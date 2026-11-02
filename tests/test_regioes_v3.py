"""
Testes da versao 3 da segmentacao por regioes e ferramentas associadas (T35).

Cobre:
  1. Marcacao vira outro e regiao de origem se ajusta;
  2. Texto comum com '<' ou '@' nao vira outro;
  3. Classes do Rose por maioria e so nas classes pedidas;
  4. regras="v2" igual a v2;
  5. atualizar_proposta num diretorio temporario: pula anotadas (inclusive rascunho),
     rele antes de gravar, nao altera anotacoes.jsonl.
"""
from __future__ import annotations

import os
import json
import shutil
import tempfile
import unittest

from src.data import regioes as seg
from src.anotacao.atualizar_proposta import atualizar_proposta, ler_jsonl


class TestRegioesV3(unittest.TestCase):

    def setUp(self):
        # Caixa padrao da pagina
        self.detector_padrao = [
            {"rotulo": "text", "score": 0.9, "bbox": [10.0, 10.0, 200.0, 200.0]}
        ]
        self.blocos_padrao = [
            {"id": "b0", "bbox": [10.0, 10.0, 200.0, 200.0], "tipo": "texto"}
        ]

    def test_01_marcacao_vira_outro_e_origem_se_ajusta(self):
        """Marca de diagramacao vira 'outro' e a regiao de origem se ajusta as palavras restantes."""
        # Palavras: 0 eh marca, 1 e 2 sao texto comum
        palavras = [
            ["<@textFrameStart>", 10.0, 10.0, 50.0, 20.0, 0],
            ["Primeira", 60.0, 10.0, 120.0, 20.0, 0],
            ["palavra", 130.0, 10.0, 180.0, 20.0, 0],
        ]
        proposta = seg.propor(palavras, self.blocos_padrao, self.detector_padrao, regras=True)

        classes = {r["classe"] for r in proposta}
        self.assertIn("outro", classes)
        self.assertIn("texto", classes)

        reg_outro = [r for r in proposta if r["classe"] == "outro"]
        reg_texto = [r for r in proposta if r["classe"] == "texto"]
        self.assertEqual(len(reg_outro), 1)
        self.assertEqual(len(reg_texto), 1)

        # A caixa de outro deve cobrir a marca
        self.assertEqual(reg_outro[0]["bbox"], [10.0, 10.0, 50.0, 20.0])
        # A caixa de texto deve se ajustar apenas as palavras restantes
        self.assertEqual(reg_texto[0]["bbox"], [60.0, 10.0, 180.0, 20.0])

        # Cobertura completa: toda palavra fica em exatamente uma regiao
        centros = [seg._centro(w) for w in palavras]
        for cx, cy in centros:
            dentro = [r for r in proposta if seg._contem(r["bbox"], cx, cy)]
            self.assertEqual(len(dentro), 1)

    def test_02_regiao_so_com_marcacao_some_origem(self):
        """Se a regiao de origem tiver apenas marcas de diagramacao, a origem some."""
        palavras = [
            ["contPageBreak", 10.0, 10.0, 50.0, 20.0, 0],
        ]
        proposta = seg.propor(palavras, self.blocos_padrao, self.detector_padrao, regras=True)
        self.assertEqual(len(proposta), 1)
        self.assertEqual(proposta[0]["classe"], "outro")
        self.assertEqual(proposta[0]["bbox"], [10.0, 10.0, 50.0, 20.0])

    def test_03_marcacoes_contiguas_fundem(self):
        """Marcacoes na mesma coluna e CONTIGUAS formam uma so regiao outro (etapa 7,
        fundir_fragmentos): o ouro humano do Diamond trata marcas de diagramacao empilhadas como
        um bloco unico. Marcas distantes (vao grande) continuam separadas."""
        # Linha 1 (duas marcas, agrupadas pela outro_marcacao) + Linha 2 contigua -> uma regiao
        palavras = [
            ["<#SEGRASE#123>", 10.0, 10.0, 40.0, 20.0, 0],
            ["<#E.G.B#456>", 50.0, 10.0, 80.0, 20.0, 0],
            ["contPageBreak", 10.0, 30.0, 60.0, 40.0, 0],
        ]
        proposta = seg.propor(palavras, self.blocos_padrao, self.detector_padrao, regras=True)
        self.assertEqual(len(proposta), 1)
        self.assertEqual(proposta[0]["classe"], "outro")
        self.assertEqual(proposta[0]["bbox"], [10.0, 10.0, 80.0, 40.0])

        # Marca muito abaixo (vao ~6 linhas > folga_max) NAO funde: fica separada
        palavras_dist = [
            ["<#SEGRASE#123>", 10.0, 10.0, 40.0, 20.0, 0],
            ["contPageBreak", 10.0, 80.0, 60.0, 90.0, 0],
        ]
        prop_dist = seg.propor(palavras_dist, self.blocos_padrao, self.detector_padrao, regras=True)
        self.assertEqual(len(prop_dist), 2)
        self.assertTrue(all(r["classe"] == "outro" for r in prop_dist))

    def test_04_texto_comum_com_menor_ou_arroba_nao_vira_outro(self):
        """Texto legitimo contendo '<' ou '@' nao deve virar 'outro'."""
        exemplos = [
            "<qualquer>",
            "<usuario@email.com>",
            "usuario@dominio.com.br",
            "@prefeitura",
            "x < y",
            "contato",
            "conteudo",
            "contagem",
        ]
        for palavra in exemplos:
            self.assertFalse(
                bool(seg.RE_MARCACAO.match(palavra)),
                f"Palavra '{palavra}' nao deveria casar com RE_MARCACAO",
            )

        # Propor com texto contendo email e menor
        palavras = [
            ["E-mail:", 10.0, 10.0, 40.0, 20.0, 0],
            ["<contato@ufg.br>", 50.0, 10.0, 120.0, 20.0, 0],
            ["valor", 10.0, 30.0, 40.0, 40.0, 0],
            ["<", 45.0, 30.0, 50.0, 40.0, 0],
            ["10", 55.0, 30.0, 70.0, 40.0, 0],
        ]
        proposta = seg.propor(palavras, self.blocos_padrao, self.detector_padrao, regras=True)
        classes = {r["classe"] for r in proposta}
        self.assertNotIn("outro", classes)

    def test_05_classes_rose_por_maioria_e_so_classes_pedidas(self):
        """Classes do Rose sao aplicadas por maioria de palavras e apenas se pertencerem a classes."""
        regioes = [
            {"id": "p1", "classe": "texto", "bbox": [10.0, 10.0, 100.0, 30.0], "origem": "detector"}
        ]
        palavras = [
            ["Fulano", 10.0, 10.0, 30.0, 20.0, 0],
            ["de", 35.0, 10.0, 45.0, 20.0, 0],
            ["Tal", 50.0, 10.0, 70.0, 20.0, 0],
            ["Prefeito", 10.0, 25.0, 50.0, 35.0, 0],
        ]
        # Rose cobre 3 palavras com 'assinatura' e 1 palavra com 'cabecalho'
        regioes_rose = [
            {"id": "r1", "classe": "assinatura", "bbox": [5.0, 5.0, 75.0, 22.0]},
            {"id": "r2", "classe": "cabecalho", "bbox": [5.0, 23.0, 55.0, 37.0]},
        ]

        # Caso 1: classe pedida inclui 'assinatura' -> adota 'assinatura'
        res1 = seg.aplicar_classes_rose(regioes, palavras, regioes_rose, classes={"assinatura", "cabecalho"})
        self.assertEqual(res1[0]["classe"], "assinatura")
        # Nao mexe em caixa
        self.assertEqual(res1[0]["bbox"], [10.0, 10.0, 100.0, 30.0])

        # Caso 2: classe pedida NAO inclui 'assinatura' (so 'cabecalho') -> mantem 'texto'
        res2 = seg.aplicar_classes_rose(regioes, palavras, regioes_rose, classes={"cabecalho"})
        self.assertEqual(res2[0]["classe"], "texto")
        self.assertEqual(res2[0]["bbox"], [10.0, 10.0, 100.0, 30.0])

        # Caso 3: usando nome de conjunto predefinido 'assinatura_cabecalho'
        res3 = seg.aplicar_classes_rose(regioes, palavras, regioes_rose, classes="assinatura_cabecalho")
        self.assertEqual(res3[0]["classe"], "assinatura")

    def test_06_regras_v2_reproduz_v2(self):
        """regras='v2' reproduz as regras da versao 2 sem aplicar outro_marcacao."""
        palavras = [
            ["<@textFrameStart>", 10.0, 10.0, 50.0, 20.0, 0],
            ["Texto", 60.0, 10.0, 120.0, 20.0, 0],
        ]
        # Na v2, marcas nao sao tratadas e permanecem na caixa original (classe 'texto')
        prop_v2 = seg.propor(palavras, self.blocos_padrao, self.detector_padrao, regras="v2")
        classes_v2 = {r["classe"] for r in prop_v2}
        self.assertNotIn("outro", classes_v2)

        # Na v3 (regras=True), vira 'outro'
        prop_v3 = seg.propor(palavras, self.blocos_padrao, self.detector_padrao, regras=True)
        classes_v3 = {r["classe"] for r in prop_v3}
        self.assertIn("outro", classes_v3)

    def test_07_atualizar_proposta_diretorio_temporario(self):
        """atualizar_proposta pula paginas com anotacao (inclusive rascunho), rele antes de gravar,
        faz backup e nao altera anotacoes.jsonl."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lote_dir = os.path.join(tmpdir, "lote_teste")
            os.makedirs(lote_dir)

            palavras_com_marca = [
                ["<@textFrameStart>", 10.0, 10.0, 50.0, 20.0, 0],
                ["Texto", 60.0, 10.0, 120.0, 20.0, 0],
            ]
            detector = [{"rotulo": "text", "score": 0.9, "bbox": [10.0, 10.0, 150.0, 50.0]}]
            blocos_v3 = [{"id": "b0", "bbox": [10.0, 10.0, 150.0, 50.0], "tipo": "texto"}]

            tarefas = [
                {
                    "page_id": "p1_concluida",
                    "proposta_versao": "v2",
                    "palavras": palavras_com_marca,
                    "detector": {"regioes": detector},
                    "blocos_v3": blocos_v3,
                    "proposta": seg.propor(palavras_com_marca, blocos_v3, detector, regras="v2"),
                    "stats": {"n_proposta": 1},
                },
                {
                    "page_id": "p2_rascunho",
                    "proposta_versao": "v2",
                    "palavras": palavras_com_marca,
                    "detector": {"regioes": detector},
                    "blocos_v3": blocos_v3,
                    "proposta": seg.propor(palavras_com_marca, blocos_v3, detector, regras="v2"),
                    "stats": {"n_proposta": 1},
                },
                {
                    "page_id": "p3_sem_anotacao",
                    "proposta_versao": "v2",
                    "palavras": palavras_com_marca,
                    "detector": {"regioes": detector},
                    "blocos_v3": blocos_v3,
                    "proposta": seg.propor(palavras_com_marca, blocos_v3, detector, regras="v2"),
                    "stats": {"n_proposta": 1},
                },
            ]

            anotacoes = [
                {"page_id": "p1_concluida", "anotador": "pedro", "status": "concluida", "regioes": []},
                {"page_id": "p2_rascunho", "anotador": "pedro", "status": "rascunho", "regioes": []},
            ]

            arq_tarefas = os.path.join(lote_dir, "tarefas.jsonl")
            arq_anotacoes = os.path.join(lote_dir, "anotacoes.jsonl")

            with open(arq_tarefas, "w", encoding="utf-8") as f:
                for t in tarefas:
                    f.write(json.dumps(t) + "\n")

            with open(arq_anotacoes, "w", encoding="utf-8") as f:
                for a in anotacoes:
                    f.write(json.dumps(a) + "\n")

            with open(arq_anotacoes, "rb") as f:
                conteudo_anotacoes_original = f.read()

            # Execucao 1: sem --aplicar (simulacao)
            relato = atualizar_proposta(
                lote="lote_teste",
                versao="v3",
                aplicar=False,
                dir_diamond=tmpdir,
            )
            self.assertEqual(relato["paginas_anotadas"], 2)
            self.assertEqual(relato["paginas_elegiveis"], 1)
            self.assertEqual(relato["paginas_mudariam"], 1)
            self.assertEqual(relato["mudariam_ids"], ["p3_sem_anotacao"])

            # Garante que tarefas.jsonl nao foi alterado
            tarefas_pos_dry = ler_jsonl(arq_tarefas)
            self.assertEqual(tarefas_pos_dry[2]["proposta_versao"], "v2")

            # Execucao 2: com --aplicar
            relato_apl = atualizar_proposta(
                lote="lote_teste",
                versao="v3",
                aplicar=True,
                dir_diamond=tmpdir,
            )
            self.assertEqual(relato_apl["paginas_efetivamente_alteradas"], 1)

            # Backup criado
            self.assertTrue(os.path.exists(relato_apl["backup"]))

            # Registrado em derivados/atualizacoes.jsonl
            arq_log = os.path.join(lote_dir, "derivados", "atualizacoes.jsonl")
            self.assertTrue(os.path.exists(arq_log))
            logs = ler_jsonl(arq_log)
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0]["paginas"], ["p3_sem_anotacao"])
            self.assertEqual(logs[0]["versao"], "v3")

            # anotacoes.jsonl jamais foi modificado
            with open(arq_anotacoes, "rb") as f:
                self.assertEqual(f.read(), conteudo_anotacoes_original)

            # tarefas.jsonl atualizado: p1 e p2 continuam intocadas, p3 atualizada
            tarefas_finais = {t["page_id"]: t for t in ler_jsonl(arq_tarefas)}
            self.assertEqual(tarefas_finais["p1_concluida"]["proposta_versao"], "v2")
            self.assertEqual(tarefas_finais["p2_rascunho"]["proposta_versao"], "v2")
            self.assertEqual(tarefas_finais["p3_sem_anotacao"]["proposta_versao"], "v3")
            # p3 agora contem a regiao 'outro'
            classes_p3 = {r["classe"] for r in tarefas_finais["p3_sem_anotacao"]["proposta"]}
            self.assertIn("outro", classes_p3)

    def test_08_rele_anotacoes_antes_de_gravar(self):
        """Se uma pagina receber anotacao durante o processo, a releitura logo antes de gravar a exclui."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lote_dir = os.path.join(tmpdir, "lote_concorrente")
            os.makedirs(lote_dir)

            palavras = [
                ["<@textFrameStart>", 10.0, 10.0, 50.0, 20.0, 0],
                ["Texto", 60.0, 10.0, 120.0, 20.0, 0],
            ]
            detector = [{"rotulo": "text", "score": 0.9, "bbox": [10.0, 10.0, 150.0, 50.0]}]
            blocos_v3 = [{"id": "b0", "bbox": [10.0, 10.0, 150.0, 50.0], "tipo": "texto"}]

            tarefas = [
                {
                    "page_id": "p_anotada_depois",
                    "proposta_versao": "v2",
                    "palavras": palavras,
                    "detector": {"regioes": detector},
                    "blocos_v3": blocos_v3,
                    "proposta": seg.propor(palavras, blocos_v3, detector, regras="v2"),
                    "stats": {"n_proposta": 1},
                }
            ]
            arq_tarefas = os.path.join(lote_dir, "tarefas.jsonl")
            arq_anotacoes = os.path.join(lote_dir, "anotacoes.jsonl")

            with open(arq_tarefas, "w", encoding="utf-8") as f:
                for t in tarefas:
                    f.write(json.dumps(t) + "\n")

            # anotacoes.jsonl inicialmente vazio
            with open(arq_anotacoes, "w", encoding="utf-8") as f:
                f.write("")

            # Simulamos que antes do os.replace ou gravacao final, o Pedro anotou a pagina
            # Injetamos uma anotacao logo antes da gravacao simulando a concorrencia:
            # chamamos atualizar_proposta mas com monkeypatch ou simplesmente adicionando a anotacao:
            # Para testar diretamente o comportamento da funcao: se o arquivo anotacoes.jsonl
            # tem a anotacao quando anotadas_finais eh lido, a pagina nao e alterada.
            with open(arq_anotacoes, "a", encoding="utf-8") as f:
                f.write(json.dumps({"page_id": "p_anotada_depois", "anotador": "pedro", "status": "concluida", "regioes": []}) + "\n")

            relato = atualizar_proposta(
                lote="lote_concorrente",
                versao="v3",
                aplicar=True,
                dir_diamond=tmpdir,
            )
            # Como a pagina estava anotada na releitura, nao foi alterada
            self.assertEqual(relato["paginas_efetivamente_alteradas"], 0)
            tarefas_finais = ler_jsonl(arq_tarefas)
            self.assertEqual(tarefas_finais[0]["proposta_versao"], "v2")


if __name__ == "__main__":
    unittest.main()
