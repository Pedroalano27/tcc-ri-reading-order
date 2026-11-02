"""Valida o Rose offline, com PDF/API/gravacao simulados e sem anotacao em disco.

Uso: venv\\Scripts\\python.exe -m unittest tests.test_rose -v
O teste de integracao chama salvar_diamond real e intercepta apenas a leitura
das tarefas e a persistencia; suas validacoes e normalizacao continuam ativas.
"""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from src.anotacao import servidor
from src.data import gerar_rose as rose


def tarefa_exemplo():
    return {
        "page_id": "sintetica#p0", "uf": "sintetica", "arquivo": "diario.pdf", "pagina": 0,
        "dimensions": {"width": 200, "height": 200}, "imagem": "000001.jpg",
        "palavras": [["ATO", 10.12, 10.13, 30.14, 20.15, 0],
                     ["Texto", 10, 40, 30, 50, 0], ["final", 35, 40, 55, 50, 1],
                     ["2026", 10, 70, 30, 80, 2]],
        "proposta": [{"id": "p1", "classe": "texto", "bbox": [10, 10, 31, 50]},
                     {"id": "p2", "classe": "texto", "bbox": [35, 40, 55, 50]},
                     {"id": "p3", "classe": "rodape", "bbox": [10, 70, 30, 80]}],
    }


def resposta_exemplo():
    return json.dumps({"regioes": [{"classe": 1, "palavras": [0]},
                                    {"classe": 2, "palavras": [1, 2]},
                                    {"classe": 7, "palavras": [3]}]})


class TestParsingRose(unittest.TestCase):
    def setUp(self):
        self.tarefa = tarefa_exemplo()

    def test_parse_fusao_divisao_e_proveniencia(self):
        original = copy.deepcopy(self.tarefa)
        regioes = rose.parse_resposta(resposta_exemplo(), self.tarefa)
        self.assertEqual([r["classe"] for r in regioes], ["titulo", "texto", "rodape"])
        self.assertEqual([r["de"] for r in regioes], ["p1", ["p1", "p2"], "p3"])
        self.assertEqual(regioes[1]["bbox"], [10, 40, 55, 50])
        self.assertEqual(rose.verificar_cobertura(self.tarefa["palavras"], regioes), {"fora": 0, "duplas": 0})
        self.assertEqual(self.tarefa, original)

    def test_envelope_exato_e_salvar_diamond_real(self):
        regioes = rose.parse_resposta(resposta_exemplo(), self.tarefa)
        self.assertEqual(regioes[0]["bbox"], [10.12, 10.13, 30.14, 20.15])
        anotacao = rose.montar_anotacao(self.tarefa, regioes, "modelo-mock")
        with patch.object(servidor, "tarefas_diamond", return_value=[self.tarefa]), \
                patch.object(servidor, "gravar_anotacao") as gravar:
            salvo = servidor.salvar_diamond("rose_mock", anotacao)
        gravar.assert_called_once()
        self.assertEqual(salvo["anotador"], "VLM:modelo-mock")
        self.assertEqual(salvo["status"], "concluida")
        self.assertEqual(salvo["n_regioes"], 3)
        self.assertEqual(salvo["palavras_sem_caixa"], 0)
        self.assertEqual(salvo["palavras_em_duas_caixas"], 0)
        self.assertEqual(anotacao["mudancas"], salvo["mudancas"])

    def test_rejeita_json_invalido_coordenadas_e_chaves_repetidas(self):
        for resposta in ("```json\n" + resposta_exemplo() + "\n```", "{", "[]",
                         '{"regioes": [], "regioes": []}', '{"regioes": []}',
                         '{"regioes": [{"classe": 2, "palavras": [0], "bbox": [0,0,1,1]}]}'):
            with self.subTest(resposta=resposta), self.assertRaises(ValueError):
                rose.parse_resposta(resposta, self.tarefa)

    def test_rejeita_classes_e_indices_invalidos(self):
        for campo, valores in (("classe", [0, 10, True, "texto", 2.0]),
                               ("palavras", [[], [99], [-1], [True], [1.0], ["1"], [0, 0]])):
            for valor in valores:
                dados = json.loads(resposta_exemplo())
                dados["regioes"][0][campo] = valor
                with self.subTest(campo=campo, valor=valor), self.assertRaises(ValueError):
                    rose.parse_resposta(json.dumps(dados), self.tarefa)

    def test_rejeita_omissao_e_repeticao_entre_grupos(self):
        for indices in ([1], [0, 1, 2]):
            dados = json.loads(resposta_exemplo())
            dados["regioes"][1]["palavras"] = indices
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                rose.parse_resposta(json.dumps(dados), self.tarefa)

    def test_rejeita_envelope_que_captura_palavra_de_outro_grupo(self):
        dados = {"regioes": [{"classe": 2, "palavras": [0, 3]},
                              {"classe": 2, "palavras": [1, 2]}]}
        with self.assertRaisesRegex(ValueError, "duplas"):
            rose.parse_resposta(json.dumps(dados), self.tarefa)

    def test_aceita_figura_sobre_texto_sem_coordenadas_inventadas(self):
        dados = {"regioes": [{"classe": 8, "palavras": [0, 3]},
                              {"classe": 2, "palavras": [1, 2]}]}
        regioes = rose.parse_resposta(json.dumps(dados), self.tarefa)
        self.assertEqual(regioes[0]["classe"], "figura")
        self.assertEqual(rose.verificar_cobertura(self.tarefa["palavras"], regioes), {"fora": 0, "duplas": 0})

    def test_cobertura_unicode_e_pontuacao(self):
        palavras = [["漢", 0, 0, 10, 10, -1], ["***", 20, 0, 30, 10, -1]]
        self.assertEqual(rose.verificar_cobertura(palavras, []), {"fora": 1, "duplas": 0})

    def test_preserva_cobertura_exigida_pelo_regex_diamond(self):
        palavras = [["\u00d7", 0, 0, 10, 10, -1]]
        self.assertEqual(rose.verificar_cobertura(palavras, []), {"fora": 1, "duplas": 0})

    def test_rejeita_conflito_introduzido_pelo_arredondamento_diamond(self):
        self.tarefa["palavras"] = [["A", 0, 0, 1.06, 1, -1],
                                   ["B", 1.09, 0, 1.11, 1, -1],
                                   ["C", 1.5, 0, 2, 1, -1]]
        dados = {"regioes": [{"classe": 2, "palavras": [0]},
                              {"classe": 2, "palavras": [1, 2]}]}
        with self.assertRaisesRegex(ValueError, "Diamond arredondada"):
            rose.parse_resposta(json.dumps(dados), self.tarefa)

    def test_rejeita_caixas_fora_da_pagina_sem_area_e_nao_finitas(self):
        for caixa in ([-1, 0, 1, 1], [0, 0, 201, 10], [0, 0, 0.1, 1], [0, 0, float("inf"), 1]):
            with self.subTest(caixa=caixa), self.assertRaises(ValueError):
                rose.validar_regioes(self.tarefa, [{"classe": "texto", "bbox": caixa}])


class TestAPIRose(unittest.TestCase):
    def test_provedores_recebem_imagem_e_prompt_sem_rede(self):
        respostas = {
            "gemini": {"candidates": [{"finishReason": "STOP", "content": {
                "parts": [{"text": "pensamento", "thought": True}, {"text": resposta_exemplo()}]}}]},
            "openai": {"choices": [{"finish_reason": "stop", "message": {"content": resposta_exemplo()}}]},
        }
        for provedor, resposta in respostas.items():
            with self.subTest(provedor=provedor), patch.object(rose, "urlopen") as abrir:
                abrir.return_value.__enter__.return_value = io.StringIO(json.dumps(resposta))
                texto = rose.chamar_vlm(provedor, rose.MODELOS[provedor], "prompt", b"jpeg-mock", "segredo-mock")
                self.assertEqual(texto, resposta_exemplo())
                req = abrir.call_args.args[0]
                corpo = json.loads(req.data)
                self.assertNotIn("segredo-mock", req.full_url)
                self.assertIn("anBlZy1tb2Nr", json.dumps(corpo))
                self.assertIn("prompt", json.dumps(corpo))
                if provedor == "openai":
                    self.assertTrue(corpo["response_format"]["json_schema"]["strict"])
                else:
                    self.assertEqual(corpo["generationConfig"]["responseMimeType"], "application/json")

    def test_rejeita_truncamento_recusa_e_bloqueio(self):
        casos = [("gemini", {"candidates": [{"finishReason": "MAX_TOKENS"}]}),
                 ("gemini", {"promptFeedback": {"blockReason": "SAFETY"}}),
                 ("openai", {"choices": [{"finish_reason": "length"}]}),
                 ("openai", {"choices": [{"finish_reason": "stop", "message": {"refusal": "nao"}}]})]
        for provedor, resposta in casos:
            with self.subTest(provedor=provedor, resposta=resposta), patch.object(rose, "urlopen") as abrir:
                abrir.return_value.__enter__.return_value = io.StringIO(json.dumps(resposta))
                with self.assertRaises(ValueError):
                    rose.chamar_vlm(provedor, "mock", "prompt", b"jpeg", "segredo")

    def test_erro_http_sem_chave_ou_retentativa(self):
        with patch.object(rose, "urlopen", side_effect=HTTPError("https://mock", 429, "segredo", {}, None)) as abrir:
            with self.assertRaisesRegex(RuntimeError, "HTTP 429") as erro:
                rose.chamar_vlm("gemini", "mock", "prompt", b"jpeg", "segredo")
        abrir.assert_called_once()
        self.assertNotIn("segredo", str(erro.exception))


class TestFluxoRose(unittest.TestCase):
    def test_le_arquivo_ou_diretorio_com_tarefas(self):
        fonte = Path("colecao_mock")
        for diretorio in (False, True):
            with self.subTest(diretorio=diretorio), \
                    patch.object(Path, "is_dir", return_value=diretorio), \
                    patch.object(Path, "is_file", return_value=True), \
                    patch.object(Path, "open") as abrir:
                abrir.return_value.__enter__.return_value = io.StringIO(json.dumps(tarefa_exemplo()) + "\n")
                self.assertEqual(list(rose.ler_colecao(fonte)), [tarefa_exemplo()])

    def test_le_diretorio_de_blocos_e_rejeita_duplicatas_e_json_invalido(self):
        fonte = Path("colecao_mock")
        with patch.object(Path, "is_dir", return_value=True), \
                patch.object(Path, "is_file", return_value=False), \
                patch.object(Path, "glob", return_value=[fonte / "uf.jsonl"]), \
                patch.object(Path, "open") as abrir:
            for texto, erro in ((json.dumps(tarefa_exemplo()) + "\n", False),
                                ((json.dumps(tarefa_exemplo()) + "\n") * 2, True),
                                ("{\n", True), ('{"page_id": "sem_metadados"}\n', True)):
                with self.subTest(texto=texto):
                    abrir.return_value.__enter__.return_value = io.StringIO(texto)
                    if erro:
                        with self.assertRaises(ValueError):
                            list(rose.ler_colecao(fonte))
                    else:
                        self.assertEqual(len(list(rose.ler_colecao(fonte))), 1)

    def test_chaves_ausentes_e_alternativa_google(self):
        with patch.dict(rose.os.environ, {}, clear=True), patch.object(rose, "ler_chave_env", return_value=None):
            for provedor in rose.MODELOS:
                with self.subTest(provedor=provedor), self.assertRaises(ValueError):
                    rose.chave_api(provedor)
            with patch.dict(rose.os.environ, {"GOOGLE_API_KEY": "mock"}):
                self.assertEqual(rose.chave_api("gemini"), "mock")

    def test_dry_run_uma_pagina_sem_rede_chave_ou_gravacao(self):
        for provedor in rose.MODELOS:
            with self.subTest(provedor=provedor), \
                    patch.object(rose, "ler_colecao", return_value=iter([tarefa_exemplo()] * 2)), \
                    patch.object(rose, "preparar_pagina", return_value=(tarefa_exemplo(), b"jpeg")) as preparar, \
                    patch.object(rose, "chamar_vlm") as chamar, patch.object(rose, "chave_api") as chave, \
                    patch.object(Path, "mkdir") as mkdir, patch.object(Path, "open") as abrir, \
                    patch("sys.stdout", new_callable=io.StringIO) as console:
                codigo = rose.main(["--colecao", "mock", "--dry-run", "--limite", "10", "--provedor", provedor])
                resumo = json.loads(console.getvalue().splitlines()[-1])
            self.assertEqual(codigo, 0)
            self.assertEqual(resumo["paginas"], 1)
            self.assertEqual(resumo["modelo"], rose.MODELOS[provedor])
            preparar.assert_called_once()
            for mock in (chamar, chave, mkdir, abrir):
                mock.assert_not_called()

    def test_saida_protegida_e_lote_existente(self):
        for saida in (rose.RAIZ / "data/raw/rose", rose.RAIZ / "data/golden/rose", rose.RAIZ / "tests"):
            with self.subTest(saida=saida), self.assertRaises(ValueError):
                rose.validar_saida(saida, rose.RAIZ / "src/data/entrada_mock.jsonl")
        with self.assertRaisesRegex(ValueError, "origem"):
            rose.validar_saida(rose.RAIZ / "src/data/rose", rose.RAIZ / "src/data/entrada_mock.jsonl")

    def test_preparar_pdf_congela_palavras_e_renderiza_110_dpi(self):
        tarefa = tarefa_exemplo()
        original = copy.deepcopy(tarefa)
        with patch("pdfplumber.open") as abrir:
            pagina = abrir.return_value.__enter__.return_value.pages.__getitem__.return_value
            pagina.bbox = (0, 0, 200, 200)
            pagina.width = pagina.height = 200
            imagem = pagina.to_image.return_value.original.convert.return_value
            imagem.save.side_effect = lambda buffer, **kw: buffer.write(b"jpeg-mock")
            pronta, jpeg = rose.preparar_pagina(tarefa, 1)
            pagina.to_image.assert_called_once_with(resolution=110, force_mediabox=True)
        self.assertEqual(pronta["palavras"], tarefa["palavras"])
        self.assertEqual(jpeg, b"jpeg-mock")
        self.assertEqual(tarefa, original)

    def test_fluxo_grava_formato_diamond_e_respeita_limite_em_memoria(self):
        with patch.object(rose, "validar_saida"), patch.object(rose, "chave_api", return_value="mock"), \
                patch.object(rose, "ler_colecao", return_value=iter([tarefa_exemplo()] * 2)), \
                patch.object(rose, "preparar_pagina", return_value=(tarefa_exemplo(), b"jpeg")), \
                patch.object(rose, "chamar_vlm", return_value=resposta_exemplo()) as chamar, \
                patch.object(Path, "mkdir"), patch.object(Path, "open") as abrir, \
                patch("sys.stdout", new_callable=io.StringIO):
            codigo = rose.main(["--colecao", "mock", "--limite", "1"])
            escritas = abrir.return_value.__enter__.return_value.write.call_args_list
        self.assertEqual(codigo, 0)
        chamar.assert_called_once()
        self.assertEqual(len(escritas), 3)
        tarefa, anotacao = (json.loads(c.args[0]) for c in escritas[1:])
        self.assertIn("resposta_vlm", tarefa["rose"])
        self.assertEqual(anotacao["anotador"], f"VLM:{rose.MODELOS['gemini']}")
        self.assertEqual(anotacao["palavras_sem_caixa"], 0)
        self.assertEqual(anotacao["palavras_em_duas_caixas"], 0)

    def test_resposta_invalida_nao_cria_lote(self):
        with patch.object(rose, "validar_saida"), patch.object(rose, "chave_api", return_value="mock"), \
                patch.object(rose, "ler_colecao", return_value=iter([tarefa_exemplo()])), \
                patch.object(rose, "preparar_pagina", return_value=(tarefa_exemplo(), b"jpeg")), \
                patch.object(rose, "chamar_vlm", return_value='{"regioes": []}'), \
                patch.object(Path, "mkdir") as mkdir, patch.object(Path, "open") as abrir, \
                patch("sys.stderr", new_callable=io.StringIO):
            codigo = rose.main(["--colecao", "mock"])
        self.assertEqual(codigo, 1)
        mkdir.assert_not_called()
        abrir.assert_not_called()


def tarefa_regioes_exemplo():
    return {
        "page_id": "regioes#p0", "uf": "sintetica", "arquivo": "diario.pdf", "pagina": 0,
        "dimensions": {"width": 200, "height": 200}, "imagem": "000001.jpg",
        "palavras": [
            ["TITULO", 10, 10, 50, 20, 0],
            ["Linha", 10, 30, 40, 40, 1], ["um", 45, 30, 60, 40, 1],
            ["Linha", 10, 50, 40, 60, 2], ["dois", 45, 50, 70, 60, 2],
            ["Linha", 10, 70, 40, 80, 3], ["tres", 45, 70, 70, 80, 3],
        ],
        "proposta": [
            {"id": "p1", "classe": "titulo", "bbox": [10, 10, 50, 20]},
            {"id": "p2", "classe": "texto", "bbox": [10, 30, 60, 40]},
            {"id": "p3", "classe": "texto", "bbox": [10, 50, 70, 60]},
            {"id": "p4", "classe": "texto", "bbox": [10, 70, 70, 80]},
        ],
    }


class TestModoRegioes(unittest.TestCase):
    def setUp(self):
        self.tarefa = tarefa_regioes_exemplo()

    def test_parse_regioes_unir_cadeia(self):
        resp = json.dumps({
            "regioes": [
                {"id": "p1", "classe": 1, "unir_com": None, "quebras": []},
                {"id": "p2", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p3", "classe": 2, "unir_com": "p2", "quebras": []},
                {"id": "p4", "classe": 2, "unir_com": "p3", "quebras": []},
            ]
        })
        regioes = rose.parse_resposta(resp, self.tarefa, modo="regioes")
        self.assertEqual(len(regioes), 2)
        self.assertEqual([r["classe"] for r in regioes], ["titulo", "texto"])
        self.assertEqual(regioes[0]["de"], "p1")
        self.assertEqual(regioes[0]["origem"], "vlm")
        self.assertEqual(regioes[1]["de"], ["p2", "p3", "p4"])
        self.assertEqual(regioes[1]["origem"], "vlm")
        self.assertEqual(regioes[1]["bbox"], [10, 30, 70, 80])
        self.assertEqual(rose.verificar_cobertura(self.tarefa["palavras"], regioes), {"fora": 0, "duplas": 0})

    def test_parse_regioes_quebra(self):
        t = {
            "page_id": "quebra#p0", "uf": "sintetica", "arquivo": "diario.pdf", "pagina": 0,
            "dimensions": {"width": 200, "height": 200}, "imagem": "000001.jpg",
            "palavras": [
                ["ACORDANTE:", 10, 10, 40, 20, 0], ["Ver.", 45, 10, 70, 20, 0],
                ["OBJETO:", 10, 30, 40, 40, 0], ["Termo", 45, 30, 70, 40, 0],
            ],
            "proposta": [
                {"id": "p1", "classe": "texto", "bbox": [10, 10, 70, 40]},
            ],
        }
        resp = json.dumps({
            "regioes": [
                {"id": "p1", "classe": 2, "unir_com": None, "quebras": [1]},   # linha 1: "OBJETO: Termo"
            ]
        })
        regioes = rose.parse_resposta(resp, t, modo="regioes")
        self.assertEqual(len(regioes), 2)
        self.assertEqual(regioes[0]["de"], "p1")
        self.assertEqual(regioes[1]["de"], "p1")
        self.assertEqual(regioes[0]["origem"], "vlm")
        self.assertEqual(regioes[1]["origem"], "vlm")
        self.assertEqual(regioes[0]["bbox"], [10, 10, 70, 20])
        self.assertEqual(regioes[1]["bbox"], [10, 30, 70, 40])
        self.assertEqual(rose.verificar_cobertura(t["palavras"], regioes), {"fora": 0, "duplas": 0})

    def test_parse_regioes_figura_sem_palavras(self):
        t = {
            "page_id": "figura#p0", "uf": "sintetica", "arquivo": "diario.pdf", "pagina": 0,
            "dimensions": {"width": 200, "height": 200}, "imagem": "000001.jpg",
            "palavras": [
                ["Texto", 10, 80, 50, 90, 0],
            ],
            "proposta": [
                {"id": "p1", "classe": "figura", "bbox": [10, 10, 60, 60]},
                {"id": "p2", "classe": "texto", "bbox": [10, 80, 50, 90]},
            ],
        }
        resp = json.dumps({
            "regioes": [
                {"id": "p1", "classe": 8, "unir_com": None, "quebras": []},
                {"id": "p2", "classe": 2, "unir_com": None, "quebras": []},
            ]
        })
        regioes = rose.parse_resposta(resp, t, modo="regioes")
        self.assertEqual(len(regioes), 2)
        self.assertEqual(regioes[0]["classe"], "figura")
        self.assertEqual(regioes[0]["bbox"], [10, 10, 60, 60])
        self.assertEqual(regioes[0]["de"], "p1")
        self.assertEqual(regioes[0]["origem"], "vlm")
        self.assertEqual(rose.verificar_cobertura(t["palavras"], regioes), {"fora": 0, "duplas": 0})

    def test_parse_regioes_recusa_ciclo(self):
        resp_ciclo = json.dumps({
            "regioes": [
                {"id": "p1", "classe": 1, "unir_com": None, "quebras": []},
                {"id": "p2", "classe": 2, "unir_com": "p3", "quebras": []},
                {"id": "p3", "classe": 2, "unir_com": "p2", "quebras": []},
                {"id": "p4", "classe": 2, "unir_com": None, "quebras": []},
            ]
        })
        with self.assertRaisesRegex(ValueError, "ciclo"):
            rose.parse_resposta(resp_ciclo, self.tarefa, modo="regioes")

        resp_autociclo = json.dumps({
            "regioes": [
                {"id": "p1", "classe": 1, "unir_com": "p1", "quebras": []},
                {"id": "p2", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p3", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p4", "classe": 2, "unir_com": None, "quebras": []},
            ]
        })
        with self.assertRaisesRegex(ValueError, "ciclo"):
            rose.parse_resposta(resp_autociclo, self.tarefa, modo="regioes")

    def test_parse_regioes_recusa_uniao_com_figura(self):
        t = {
            "page_id": "fig_uniao#p0", "uf": "sintetica", "arquivo": "diario.pdf", "pagina": 0,
            "dimensions": {"width": 200, "height": 200}, "imagem": "000001.jpg",
            "palavras": [["A", 10, 10, 20, 20, 0], ["B", 10, 30, 20, 40, 1]],
            "proposta": [
                {"id": "p1", "classe": "figura", "bbox": [10, 10, 20, 20]},
                {"id": "p2", "classe": "texto", "bbox": [10, 30, 20, 40]},
            ],
        }
        resp = json.dumps({
            "regioes": [
                {"id": "p1", "classe": 8, "unir_com": None, "quebras": []},
                {"id": "p2", "classe": 2, "unir_com": "p1", "quebras": []},
            ]
        })
        with self.assertRaisesRegex(ValueError, "figura"):
            rose.parse_resposta(resp, t, modo="regioes")

    def test_parse_regioes_preenche_faltando_e_recusa_repetido(self):
        resp_faltando = json.dumps({
            "regioes": [
                {"id": "p1", "classe": 1, "unir_com": None, "quebras": []},
                {"id": "p2", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p3", "classe": 2, "unir_com": None, "quebras": []},
            ]
        })
        # regiao esquecida pelo VLM fica como na proposta, marcada com origem "proposta"
        regioes = rose.parse_resposta(resp_faltando, self.tarefa, modo="regioes")
        self.assertEqual([r["origem"] for r in regioes], ["vlm", "vlm", "vlm", "proposta"])
        self.assertEqual(regioes[3]["de"], "p4")

        resp_repetido = json.dumps({
            "regioes": [
                {"id": "p1", "classe": 1, "unir_com": None, "quebras": []},
                {"id": "p1", "classe": 1, "unir_com": None, "quebras": []},
                {"id": "p2", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p3", "classe": 2, "unir_com": None, "quebras": []},
            ]
        })
        with self.assertRaises(ValueError):
            rose.parse_resposta(resp_repetido, self.tarefa, modo="regioes")

        resp_desconhecido = json.dumps({
            "regioes": [
                {"id": "p1", "classe": 1, "unir_com": None, "quebras": []},
                {"id": "p2", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p3", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p99", "classe": 2, "unir_com": None, "quebras": []},
            ]
        })
        with self.assertRaises(ValueError):
            rose.parse_resposta(resp_desconhecido, self.tarefa, modo="regioes")

    def test_parse_regioes_recusa_indice_fora_da_regiao(self):
        for q in (99, -1):
            resp = json.dumps({
                "regioes": [
                    {"id": "p1", "classe": 1, "unir_com": None, "quebras": [q]},
                    {"id": "p2", "classe": 2, "unir_com": None, "quebras": []},
                    {"id": "p3", "classe": 2, "unir_com": None, "quebras": []},
                    {"id": "p4", "classe": 2, "unir_com": None, "quebras": []},
                ]
            })
            with self.subTest(q=q), self.assertRaisesRegex(ValueError, "fora da regiao"):
                rose.parse_resposta(resp, self.tarefa, modo="regioes")

    def test_parse_regioes_cobertura(self):
        t_invalida = copy.deepcopy(self.tarefa)
        t_invalida["palavras"].append(["ORFA", 150, 150, 180, 160, -1])
        resp = json.dumps({
            "regioes": [
                {"id": "p1", "classe": 1, "unir_com": None, "quebras": []},
                {"id": "p2", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p3", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p4", "classe": 2, "unir_com": None, "quebras": []},
            ]
        })
        with self.assertRaisesRegex(ValueError, "cobertura"):
            rose.parse_resposta(resp, t_invalida, modo="regioes")


class TestNovosRecursosRose(unittest.TestCase):
    def test_erros_jsonl_gravado_ao_pular(self):
        t1 = tarefa_regioes_exemplo()
        t2 = copy.deepcopy(t1)
        t2["page_id"] = "regioes#p1"
        t2["imagem"] = "000002.jpg"
        resp_valida = json.dumps({
            "regioes": [
                {"id": "p1", "classe": 1, "unir_com": None, "quebras": []},
                {"id": "p2", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p3", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p4", "classe": 2, "unir_com": None, "quebras": []},
            ]
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            saida = Path(tmpdir) / "lote_erros"
            chamadas = [RuntimeError("API gemini: falha de conexao")] * 5 + [resp_valida]
            def fake_vlm(*args, **kwargs):
                r = chamadas.pop(0)
                if isinstance(r, Exception):
                    raise r
                return r

            with patch.object(rose, "validar_saida"), \
                    patch.object(rose, "chave_api", return_value="mock"), \
                    patch.object(rose, "ler_colecao", return_value=iter([t1, t2])), \
                    patch.object(rose, "preparar_pagina", side_effect=[(t1, b"jpeg1"), (t2, b"jpeg2")]), \
                    patch.object(rose, "chamar_vlm", side_effect=fake_vlm), \
                    patch.object(rose.time, "sleep"), \
                    patch("sys.stdout", new_callable=io.StringIO) as console:
                codigo = rose.main(["--colecao", "mock", "--saida", str(saida),
                                    "--modo", "regioes", "--pular-erros"])
            self.assertEqual(codigo, 0)
            erros_arq = saida / "erros.jsonl"
            self.assertTrue(erros_arq.is_file())
            linhas = [json.loads(l) for l in erros_arq.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(linhas), 1)
            self.assertEqual(linhas[0]["page_id"], "regioes#p0")
            self.assertIn("falha de conexao", linhas[0]["erro"])
            self.assertEqual(linhas[0]["tentativas"], 5)
            self.assertIn("momento", linhas[0])
            self.assertIn("1 paginas puladas", console.getvalue())

    def test_parada_limpa_cota_diaria(self):
        t1 = tarefa_regioes_exemplo()
        with tempfile.TemporaryDirectory() as tmpdir:
            saida = Path(tmpdir) / "lote_cota"
            msg_cota = "API gemini: HTTP 429: Quota exceeded for quota metric 'GenerateContent requests' and limit 'GenerateContent requests per day' of service 'generativelanguage.googleapis.com'"
            with patch.object(rose, "validar_saida"), \
                    patch.object(rose, "chave_api", return_value="mock"), \
                    patch.object(rose, "ler_colecao", return_value=iter([t1])), \
                    patch.object(rose, "preparar_pagina", return_value=(t1, b"jpeg")), \
                    patch.object(rose, "chamar_vlm", side_effect=RuntimeError(msg_cota)), \
                    patch("sys.stdout", new_callable=io.StringIO) as console:
                codigo = rose.main(["--colecao", "mock", "--saida", str(saida), "--modo", "regioes"])
            self.assertEqual(codigo, 0)
            self.assertIn("Cota diaria esgotada", console.getvalue())

    def test_espacamento_rpm(self):
        t1 = tarefa_regioes_exemplo()
        t2 = copy.deepcopy(t1)
        t2["page_id"] = "regioes#p1"
        t2["imagem"] = "000002.jpg"
        resp = json.dumps({
            "regioes": [
                {"id": "p1", "classe": 1, "unir_com": None, "quebras": []},
                {"id": "p2", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p3", "classe": 2, "unir_com": None, "quebras": []},
                {"id": "p4", "classe": 2, "unir_com": None, "quebras": []},
            ]
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            saida = Path(tmpdir) / "lote_rpm"
            with patch.object(rose, "validar_saida"), \
                    patch.object(rose, "chave_api", return_value="mock"), \
                    patch.object(rose, "ler_colecao", return_value=iter([t1, t2])), \
                    patch.object(rose, "preparar_pagina", side_effect=[(t1, b"jpeg1"), (t2, b"jpeg2")]), \
                    patch.object(rose, "chamar_vlm", return_value=resp), \
                    patch.object(rose.time, "sleep") as mock_sleep, \
                    patch("sys.stdout", new_callable=io.StringIO):
                codigo = rose.main(["--colecao", "mock", "--saida", str(saida),
                                    "--modo", "regioes", "--rpm", "30"])
            self.assertEqual(codigo, 0)
            mock_sleep.assert_called()
            espera = mock_sleep.call_args[0][0]
            self.assertAlmostEqual(espera, 2.0, delta=0.5)

    def test_leitura_chave_env_diretorio_temporario(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("# Arquivo de configuracao\nOUTRA_VAR=123\nGEMINI_API_KEY=chave-secreta-temp\n", encoding="utf-8")
            with patch.dict(rose.os.environ, {}, clear=True):
                chave = rose.chave_api("gemini", raiz=tmpdir)
                self.assertEqual(chave, "chave-secreta-temp")

    def test_filtro_paginas_ids(self):
        t1 = tarefa_regioes_exemplo()
        t2 = copy.deepcopy(t1)
        t2["page_id"] = "regioes#p1"
        with tempfile.TemporaryDirectory() as tmpdir:
            filtro_file = Path(tmpdir) / "ids.txt"
            filtro_file.write_text("regioes#p1\n", encoding="utf-8")
            with patch.object(rose, "ler_colecao", return_value=iter([t1, t2])), \
                    patch.object(rose, "preparar_pagina", return_value=(t2, b"jpeg")) as prep, \
                    patch("sys.stdout", new_callable=io.StringIO):
                codigo = rose.main(["--colecao", "mock", "--paginas-ids", str(filtro_file), "--dry-run"])
            self.assertEqual(codigo, 0)
            self.assertEqual(prep.call_args[0][0]["page_id"], "regioes#p1")


if __name__ == "__main__":
    unittest.main()



class TestQuebrasValidas(unittest.TestCase):
    def test_quebra_so_antes_de_campo(self):
        t = {
            "page_id": "paragrafo#p0", "uf": "sintetica", "arquivo": "diario.pdf", "pagina": 0,
            "dimensions": {"width": 200, "height": 200}, "imagem": "000001.jpg",
            "palavras": [
                ["Considerando", 10, 10, 60, 20, 0], ["que", 65, 10, 80, 20, 0],
                ["a", 10, 30, 15, 40, 0], ["lei", 20, 30, 40, 40, 0],
                ["OBJETO:", 10, 50, 40, 60, 0], ["Termo", 45, 50, 70, 60, 0],
            ],
            "proposta": [{"id": "p1", "classe": "texto", "bbox": [10, 10, 80, 60]}],
        }
        resp = json.dumps({"regioes": [{"id": "p1", "classe": 2, "unir_com": None, "quebras": [1, 2]}]})
        regioes = rose.parse_resposta(resp, t, modo="regioes")
        # a quebra na linha 1 (continuacao de paragrafo) e ignorada; a da linha 2 ("OBJETO:") vale
        self.assertEqual([r["bbox"] for r in regioes], [[10, 10, 80, 40], [10, 50, 70, 60]])


class TestBordaDaPagina(unittest.TestCase):
    def test_palavra_cortada_na_borda_e_recortada(self):
        t = {
            "page_id": "borda#p0", "uf": "sintetica", "arquivo": "diario.pdf", "pagina": 0,
            "dimensions": {"width": 100, "height": 100}, "imagem": "000001.jpg",
            "palavras": [["Estadual,", -13.8, 10, 14.6, 20, 0], ["nada", 20, 10, 40, 20, 0]],
            "proposta": [{"id": "p1", "classe": "texto", "bbox": [0, 10, 40, 20]}],
        }
        resp = json.dumps({"regioes": [{"id": "p1", "classe": 2, "unir_com": None, "quebras": []}]})
        regioes = rose.parse_resposta(resp, t, modo="regioes")
        self.assertEqual(regioes[0]["bbox"], [0.0, 10.0, 40.0, 20.0])

    def test_caixa_sem_area_ganha_meio_ponto_no_lugar(self):
        t = {"dimensions": {"width": 100, "height": 100}, "palavras": [["|", 50, 10, 50, 20, 0]]}
        regioes = [{"id": "r1", "classe": "outro", "bbox": [50.0, 10.0, 50.0, 20.0]}]
        rose.validar_regioes(t, regioes)
        self.assertEqual(regioes[0]["bbox"], [50.0, 10.0, 50.5, 20.0])


class TestUnioesTolerantes(unittest.TestCase):
    def test_uniao_que_cobre_outra_regiao_e_desfeita(self):
        # p1 e p3 em colunas empilhadas com p2 no meio, em outra coluna: unir p1 e p3 cobriria p2
        t = {
            "page_id": "uniao#p0", "uf": "sintetica", "arquivo": "diario.pdf", "pagina": 0,
            "dimensions": {"width": 200, "height": 200}, "imagem": "000001.jpg",
            "palavras": [["Nome", 10, 10, 90, 20, 0], ["meio", 40, 30, 60, 40, 1], ["Cargo", 10, 50, 90, 60, 2]],
            "proposta": [
                {"id": "p1", "classe": "texto", "bbox": [10, 10, 90, 20]},
                {"id": "p2", "classe": "texto", "bbox": [40, 30, 60, 40]},
                {"id": "p3", "classe": "texto", "bbox": [10, 50, 90, 60]},
            ],
        }
        resp = json.dumps({"regioes": [
            {"id": "p1", "classe": 5, "unir_com": None, "quebras": []},
            {"id": "p2", "classe": 2, "unir_com": None, "quebras": []},
            {"id": "p3", "classe": 5, "unir_com": "p1", "quebras": [1]},
        ]})
        regioes = rose.parse_resposta(resp, t, modo="regioes")
        self.assertEqual(len(regioes), 3)
        self.assertEqual(rose.verificar_cobertura(t["palavras"], regioes), {"fora": 0, "duplas": 0})

    def test_quebra_em_regiao_unida_e_ignorada(self):
        t = tarefa_regioes_exemplo()
        resp = json.dumps({"regioes": [
            {"id": "p1", "classe": 1, "unir_com": None, "quebras": []},
            {"id": "p2", "classe": 2, "unir_com": None, "quebras": [1]},
            {"id": "p3", "classe": 2, "unir_com": "p2", "quebras": []},
            {"id": "p4", "classe": 2, "unir_com": None, "quebras": []},
        ]})
        regioes = rose.parse_resposta(resp, t, modo="regioes")
        self.assertEqual(len(regioes), 3)
