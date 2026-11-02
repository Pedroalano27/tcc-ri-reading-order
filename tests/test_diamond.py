"""
Testes de regressao para o Diamond (T28).

Cobre:
  - preparar_diamond.propor (pre-anotacao a partir de palavras, blocos v3 e detector Heron)
  - servidor.salvar_diamond (validacao e gravacao de anotacoes Diamond)
  - servidor._mudancas (contagem de diferencas entre proposta e anotacao)
"""
from __future__ import annotations

import os
import re
import json
import tempfile
import unittest

from src.anotacao import preparar_diamond
from src.anotacao import servidor

RE_ALFANUM = re.compile(r"[0-9A-Za-zÀ-ÿ]")


def montar_palavra(texto: str, x0: float, top: float, x1: float, bottom: float, bloco: int = 0) -> list:
    """Retorna uma palavra no formato [texto, x0, top, x1, bottom, bloco_v3]."""
    return [texto, float(x0), float(top), float(x1), float(bottom), int(bloco)]


class TestDiamondPropor(unittest.TestCase):
    def verificar_cobertura(self, palavras: list, proposta: list) -> None:
        """Verifica se nenhuma palavra com letra/digito fica sem regiao ou em duas nao-figura (item 8)."""
        for w in palavras:
            if not RE_ALFANUM.search(w[0]):
                continue
            cx, cy = (w[1] + w[3]) / 2.0, (w[2] + w[4]) / 2.0
            dentro = [r for r in proposta if r["bbox"][0] <= cx <= r["bbox"][2] and r["bbox"][1] <= cy <= r["bbox"][3]]
            self.assertGreater(len(dentro), 0, f"Palavra {w[0]!r} em ({cx}, {cy}) ficou sem regiao na proposta")
            nao_figura = [r for r in dentro if r["classe"] != "figura"]
            self.assertLessEqual(
                len(nao_figura), 1,
                f"Palavra {w[0]!r} em ({cx}, {cy}) ficou em {len(nao_figura)} regioes nao-figura: {nao_figura}"
            )

    def test_01_propor_envelope_palavras_texto(self):
        """1. Regiao de texto do detector com 3 palavras vira classe 'texto' com caixa ajustada ao envelope."""
        palavras = [
            montar_palavra("Primeira", 10.0, 10.0, 30.0, 20.0, 0),
            montar_palavra("segunda", 35.0, 10.0, 55.0, 20.0, 0),
            montar_palavra("terceira", 60.0, 10.0, 80.0, 20.0, 0),
        ]
        blocos_v3 = [{"id": "v0", "bbox": [10.0, 10.0, 80.0, 20.0]}]
        detector = [{"rotulo": "text", "score": 0.90, "bbox": [0.0, 0.0, 100.0, 50.0]}]
        prop = preparar_diamond.propor(palavras, blocos_v3, detector)

        self.assertEqual(len(prop), 1)
        self.assertEqual(prop[0]["classe"], "texto")
        self.assertEqual(prop[0]["origem"], "detector")
        self.assertEqual(prop[0]["bbox"], [10.0, 10.0, 80.0, 20.0])
        self.assertEqual(prop[0]["alertas"], [])
        self.verificar_cobertura(palavras, prop)

    def test_02_propor_score_abaixo_minimo_ignorado(self):
        """2. Regioes com score abaixo de SCORE_MIN sao ignoradas; palavras caem nas regras v3."""
        palavras = [
            montar_palavra("Palavra1", 10.0, 10.0, 30.0, 20.0, 0),
        ]
        blocos_v3 = [{"id": "v0", "bbox": [10.0, 10.0, 30.0, 20.0]}]
        detector = [{"rotulo": "text", "score": 0.40, "bbox": [0.0, 0.0, 100.0, 50.0]}]
        prop = preparar_diamond.propor(palavras, blocos_v3, detector)

        self.assertEqual(len(prop), 1)
        self.assertEqual(prop[0]["origem"], "regras")
        self.assertEqual(prop[0]["classe"], "texto")
        self.assertEqual(prop[0]["bbox"], [10.0, 10.0, 30.0, 20.0])
        self.assertIn("so_regras", prop[0]["alertas"])
        self.verificar_cobertura(palavras, prop)

    def test_03_propor_tabela_com_paragrafo_dentro(self):
        """3. Tabela com paragrafo detectado dentro: fica so a tabela com todas as palavras."""
        palavras = [
            montar_palavra("Col1", 10.0, 10.0, 30.0, 20.0, 0),
            montar_palavra("Col2", 40.0, 10.0, 60.0, 20.0, 0),
            montar_palavra("TextoInterno", 10.0, 25.0, 60.0, 35.0, 0),
        ]
        blocos_v3 = [{"id": "v0", "bbox": [10.0, 10.0, 60.0, 35.0], "tipo": "tabela"}]
        detector = [
            {"rotulo": "table", "score": 0.85, "bbox": [0.0, 0.0, 100.0, 100.0]},
            {"rotulo": "text", "score": 0.95, "bbox": [5.0, 20.0, 70.0, 40.0]},
        ]
        prop = preparar_diamond.propor(palavras, blocos_v3, detector)

        self.assertEqual(len(prop), 1)
        self.assertEqual(prop[0]["classe"], "tabela")
        self.assertEqual(prop[0]["origem"], "detector")
        self.assertEqual(prop[0]["bbox"], [10.0, 10.0, 60.0, 35.0])
        self.verificar_cobertura(palavras, prop)

    def test_04_propor_figura_nao_pega_palavra(self):
        """4. Figura nao pega palavra: palavras caem nos blocos v3 (regras) e figura mantem caixa original."""
        palavras = [
            montar_palavra("BrasaoTexto", 15.0, 15.0, 45.0, 25.0, 0),
        ]
        blocos_v3 = [{"id": "v0", "bbox": [15.0, 15.0, 45.0, 25.0]}]
        detector = [
            {"rotulo": "picture", "score": 0.90, "bbox": [0.0, 0.0, 100.0, 100.0]},
        ]
        prop = preparar_diamond.propor(palavras, blocos_v3, detector)

        self.assertEqual(len(prop), 2)
        classes = {r["classe"]: r for r in prop}
        self.assertIn("figura", classes)
        self.assertIn("texto", classes)
        self.assertEqual(classes["figura"]["bbox"], [0.0, 0.0, 100.0, 100.0])
        self.assertEqual(classes["figura"]["origem"], "detector")
        self.assertEqual(classes["texto"]["origem"], "regras")
        self.assertEqual(classes["texto"]["bbox"], [15.0, 15.0, 45.0, 25.0])
        self.verificar_cobertura(palavras, prop)

    def test_05_propor_itens_lista_mesma_coluna_e_colunas_diferentes(self):
        """5. Dois itens de lista vizinhos na mesma coluna viram uma lista; em colunas diferentes nao."""
        # Subcaso A: Mesma coluna -> unem-se em uma unica regiao lista
        palavras_mesma = [
            montar_palavra("Item1", 10.0, 10.0, 50.0, 20.0, 0),
            montar_palavra("Item2", 10.0, 25.0, 50.0, 35.0, 0),
        ]
        blocos_mesma = [{"id": "v0", "bbox": [10.0, 10.0, 50.0, 35.0]}]
        det_mesma = [
            {"rotulo": "list_item", "score": 0.90, "bbox": [5.0, 5.0, 55.0, 22.0]},
            {"rotulo": "list_item", "score": 0.88, "bbox": [5.0, 23.0, 55.0, 38.0]},
        ]
        prop_mesma = preparar_diamond.propor(palavras_mesma, blocos_mesma, det_mesma)
        self.assertEqual(len(prop_mesma), 1)
        self.assertEqual(prop_mesma[0]["classe"], "lista")
        self.assertEqual(prop_mesma[0]["bbox"], [10.0, 10.0, 50.0, 35.0])
        self.assertEqual(prop_mesma[0]["score"], 0.88)
        self.verificar_cobertura(palavras_mesma, prop_mesma)

        # Subcaso B: Colunas diferentes -> permanecem duas regioes lista separadas
        palavras_dif = [
            montar_palavra("ItemA", 10.0, 10.0, 50.0, 20.0, 0),
            montar_palavra("ItemB", 70.0, 10.0, 110.0, 20.0, 1),
        ]
        blocos_dif = [
            {"id": "v0", "bbox": [10.0, 10.0, 50.0, 20.0]},
            {"id": "v1", "bbox": [70.0, 10.0, 110.0, 20.0]},
        ]
        det_dif = [
            {"rotulo": "list_item", "score": 0.90, "bbox": [5.0, 5.0, 55.0, 25.0]},
            {"rotulo": "list_item", "score": 0.90, "bbox": [65.0, 5.0, 115.0, 25.0]},
        ]
        prop_dif = preparar_diamond.propor(palavras_dif, blocos_dif, det_dif)
        self.assertEqual(len(prop_dif), 2)
        self.assertEqual([r["classe"] for r in prop_dif], ["lista", "lista"])
        self.verificar_cobertura(palavras_dif, prop_dif)

    def test_06_propor_resolver_sobreposicoes(self):
        """6. Duas regioes que cobrem palavras uma da outra viram uma so, com classe da de mais palavras e juntou_sobrepostas."""
        # Caso A: det_A ('texto') tem 2 palavras, det_B ('titulo') tem 1 palavra -> classe vira 'texto'
        palavras_a = [
            montar_palavra("Inicio", 10.0, 10.0, 20.0, 20.0, 0),
            montar_palavra("Meio", 30.0, 10.0, 40.0, 20.0, 0),
            montar_palavra("Fim", 50.0, 10.0, 60.0, 20.0, 0),
        ]
        blocos_v3 = [{"id": "v0", "bbox": [10.0, 10.0, 60.0, 20.0]}]
        det_a = [
            {"rotulo": "text", "score": 0.90, "bbox": [5.0, 5.0, 65.0, 25.0]},
            {"rotulo": "title", "score": 0.85, "bbox": [28.0, -25.0, 42.0, 25.0]},
        ]
        prop_a = preparar_diamond.propor(palavras_a, blocos_v3, det_a)
        self.assertEqual(len(prop_a), 1)
        self.assertEqual(prop_a[0]["classe"], "texto")
        self.assertEqual(prop_a[0]["bbox"], [10.0, 10.0, 60.0, 20.0])
        self.assertIn("juntou_sobrepostas", prop_a[0]["alertas"])
        self.verificar_cobertura(palavras_a, prop_a)

        # Caso B: det_B ('titulo') tem 2 palavras, det_A ('texto') tem 1 palavra -> classe vira 'titulo'
        det_b = [
            {"rotulo": "text", "score": 0.85, "bbox": [28.0, -25.0, 42.0, 25.0]},
            {"rotulo": "title", "score": 0.90, "bbox": [5.0, 5.0, 65.0, 25.0]},
        ]
        prop_b = preparar_diamond.propor(palavras_a, blocos_v3, det_b)
        self.assertEqual(len(prop_b), 1)
        self.assertEqual(prop_b[0]["classe"], "titulo")
        self.assertEqual(prop_b[0]["bbox"], [10.0, 10.0, 60.0, 20.0])
        self.assertIn("juntou_sobrepostas", prop_b[0]["alertas"])
        self.verificar_cobertura(palavras_a, prop_b)

    def test_07_propor_alertas_so_regras_baixa_confianca_atravessa_colunas(self):
        """7. Alertas so_regras, baixa_confianca e atravessa_colunas gerados corretamente."""
        # Alerta so_regras
        palavras_regras = [montar_palavra("Regras", 10.0, 10.0, 40.0, 20.0, 0)]
        blocos_regras = [{"id": "v0", "bbox": [10.0, 10.0, 40.0, 20.0]}]
        prop_regras = preparar_diamond.propor(palavras_regras, blocos_regras, [])
        self.assertEqual(len(prop_regras), 1)
        self.assertIn("so_regras", prop_regras[0]["alertas"])
        self.verificar_cobertura(palavras_regras, prop_regras)

        # Alerta baixa_confianca (SCORE_MIN <= score < SCORE_CONFIANTE, ex.: 0.50)
        palavras_conf = [montar_palavra("Duvidoso", 10.0, 10.0, 40.0, 20.0, 0)]
        blocos_conf = [{"id": "v0", "bbox": [10.0, 10.0, 40.0, 20.0]}]
        det_conf = [{"rotulo": "text", "score": 0.50, "bbox": [5.0, 5.0, 45.0, 25.0]}]
        prop_conf = preparar_diamond.propor(palavras_conf, blocos_conf, det_conf)
        self.assertEqual(len(prop_conf), 1)
        self.assertIn("baixa_confianca", prop_conf[0]["alertas"])
        self.verificar_cobertura(palavras_conf, prop_conf)

        # Alerta atravessa_colunas (regiao do detector juntando palavras de dois blocos v3 lado a lado)
        palavras_col = [
            montar_palavra("ColunaEsq", 10.0, 10.0, 40.0, 20.0, 0),
            montar_palavra("ColunaDir", 60.0, 10.0, 90.0, 20.0, 1),
        ]
        blocos_col = [
            {"id": "v0", "bbox": [10.0, 10.0, 40.0, 20.0]},
            {"id": "v1", "bbox": [60.0, 10.0, 90.0, 20.0]},
        ]
        det_col = [{"rotulo": "text", "score": 0.90, "bbox": [5.0, 5.0, 95.0, 25.0]}]
        prop_col = preparar_diamond.propor(palavras_col, blocos_col, det_col)
        self.assertEqual(len(prop_col), 1)
        self.assertIn("atravessa_colunas", prop_col[0]["alertas"])
        self.verificar_cobertura(palavras_col, prop_col)

    def test_08_verificador_cobertura_detecta_violacoes(self):
        """8. O verificador de cobertura falha caso falte regiao ou haja duplicidade nao-figura."""
        palavras = [
            montar_palavra("Texto", 10.0, 10.0, 30.0, 20.0, 0),
            montar_palavra("***", 40.0, 10.0, 50.0, 20.0, -1),
        ]
        # Caso A: palavra alfanumerica sem regiao
        with self.assertRaises(AssertionError):
            self.verificar_cobertura(palavras, [])

        # Caso B: palavra alfanumerica em duas regioes nao-figura
        prop_duplicada = [
            {"classe": "texto", "bbox": [5.0, 5.0, 35.0, 25.0]},
            {"classe": "titulo", "bbox": [5.0, 5.0, 35.0, 25.0]},
        ]
        with self.assertRaises(AssertionError):
            self.verificar_cobertura(palavras, prop_duplicada)


class TestDiamondSalvar(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.orig_dir_diamond = servidor.DIR_DIAMOND
        servidor.DIR_DIAMOND = self.tmp_dir.name
        self.lote = "lote_teste"
        self.lote_dir = os.path.join(self.tmp_dir.name, self.lote)
        os.makedirs(self.lote_dir, exist_ok=True)

    def tearDown(self):
        servidor.DIR_DIAMOND = self.orig_dir_diamond
        self.tmp_dir.cleanup()

    def _criar_tarefa(
        self,
        page_id: str = "p01",
        width: float = 600.0,
        height: float = 800.0,
        palavras: list | None = None,
        proposta: list | None = None,
    ):
        if palavras is None:
            palavras = [
                montar_palavra("PalavraA", 20.0, 20.0, 60.0, 35.0, 0),
                montar_palavra("PalavraB", 80.0, 20.0, 120.0, 35.0, 0),
            ]
        if proposta is None:
            proposta = [
                {"id": "prop1", "classe": "texto", "bbox": [20.0, 20.0, 120.0, 35.0]}
            ]
        tarefa = {
            "page_id": page_id,
            "dimensions": {"width": width, "height": height},
            "palavras": palavras,
            "proposta": proposta,
            "extrator_sha256": "abc123sha",
        }
        with open(os.path.join(self.lote_dir, "tarefas.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(tarefa) + "\n")
        return tarefa

    def test_09_salvar_diamond_rascunho_gravado_relido_e_substituicao(self):
        """9. Rascunho valido e gravado e relido; regravar mesma pagina e anotador substitui a linha."""
        self._criar_tarefa("p01")
        reg1 = {
            "page_id": "p01",
            "anotador": "Pedro",
            "status": "rascunho",
            "nota": "Primeira versao",
            "regioes": [
                {"id": "r1", "classe": "texto", "bbox": [20.0, 20.0, 120.0, 35.0], "de": "prop1"}
            ],
        }
        res1 = servidor.salvar_diamond(self.lote, reg1)
        self.assertEqual(res1["status"], "rascunho")
        self.assertEqual(res1["nota"], "Primeira versao")

        caminho_anot = os.path.join(self.lote_dir, "anotacoes.jsonl")
        lidas1 = servidor.ler_jsonl(caminho_anot)
        self.assertEqual(len(lidas1), 1)
        self.assertEqual(lidas1[0]["nota"], "Primeira versao")
        self.assertEqual(lidas1[0]["page_id"], "p01")
        self.assertEqual(lidas1[0]["anotador"], "Pedro")

        # Regravar mesma pagina e anotador com alteracao -> substitui a linha
        reg2 = {
            "page_id": "p01",
            "anotador": "Pedro",
            "status": "rascunho",
            "nota": "Segunda versao alterada",
            "regioes": [
                {"id": "r1", "classe": "texto", "bbox": [20.0, 20.0, 120.0, 35.0], "de": "prop1"}
            ],
        }
        res2 = servidor.salvar_diamond(self.lote, reg2)
        self.assertEqual(res2["nota"], "Segunda versao alterada")

        lidas2 = servidor.ler_jsonl(caminho_anot)
        self.assertEqual(len(lidas2), 1)
        self.assertEqual(lidas2[0]["nota"], "Segunda versao alterada")

        # Regravar mesma pagina com OUTRO anotador -> acrescenta linha
        reg3 = {
            "page_id": "p01",
            "anotador": "OutroAnotador",
            "status": "rascunho",
            "nota": "Nota do outro",
            "regioes": [
                {"id": "r1", "classe": "texto", "bbox": [20.0, 20.0, 120.0, 35.0], "de": "prop1"}
            ],
        }
        servidor.salvar_diamond(self.lote, reg3)
        lidas3 = servidor.ler_jsonl(caminho_anot)
        self.assertEqual(len(lidas3), 2)

    def test_10_salvar_diamond_validacoes_value_error(self):
        """10. Classe invalida, id repetido, caixa sem area e anotador vazio levantam ValueError."""
        self._criar_tarefa("p01")
        base = {"page_id": "p01", "anotador": "Pedro", "status": "rascunho"}

        # Anotador vazio ou so espacos
        with self.assertRaises(ValueError):
            servidor.salvar_diamond(self.lote, {**base, "anotador": "   "})
        with self.assertRaises(ValueError):
            servidor.salvar_diamond(self.lote, {**base, "anotador": ""})

        # Classe invalida
        with self.assertRaises(ValueError):
            servidor.salvar_diamond(self.lote, {
                **base,
                "regioes": [{"id": "r1", "classe": "classe_inexistente", "bbox": [10.0, 10.0, 50.0, 50.0]}],
            })

        # ID repetido
        with self.assertRaises(ValueError):
            servidor.salvar_diamond(self.lote, {
                **base,
                "regioes": [
                    {"id": "r1", "classe": "texto", "bbox": [10.0, 10.0, 50.0, 50.0]},
                    {"id": "r1", "classe": "texto", "bbox": [60.0, 60.0, 90.0, 90.0]},
                ],
            })

        # ID vazio
        with self.assertRaises(ValueError):
            servidor.salvar_diamond(self.lote, {
                **base,
                "regioes": [{"id": "", "classe": "texto", "bbox": [10.0, 10.0, 50.0, 50.0]}],
            })

        # Caixa sem area (x1 - x0 < 0.5 ou y1 - y0 < 0.5)
        with self.assertRaises(ValueError):
            servidor.salvar_diamond(self.lote, {
                **base,
                "regioes": [{"id": "r1", "classe": "texto", "bbox": [10.0, 10.0, 10.3, 50.0]}],
            })
        with self.assertRaises(ValueError):
            servidor.salvar_diamond(self.lote, {
                **base,
                "regioes": [{"id": "r1", "classe": "texto", "bbox": [10.0, 10.0, 50.0, 10.2]}],
            })
        # Mas se status == 'pulada', caixa sem area deve ser ignorada sem erro
        res_pulo = servidor.salvar_diamond(self.lote, {
            **base,
            "status": "pulada",
            "motivo_pulo": "texto quebrado",
            "regioes": [{"id": "r1", "classe": "texto", "bbox": [10.0, 10.0, 10.2, 50.0]}],
        })
        self.assertEqual(res_pulo["status"], "pulada")
        self.assertEqual(len(res_pulo["regioes"]), 0)

    def test_11_salvar_diamond_recorte_caixa_limites_pagina(self):
        """11. Caixa fora da pagina e recortada aos limites da pagina."""
        self._criar_tarefa("p01", width=500.0, height=700.0)
        reg = {
            "page_id": "p01",
            "anotador": "Pedro",
            "status": "rascunho",
            "regioes": [
                # Ultrapassa todos os 4 limites da pagina [-30, -20, 550, 750]
                {"id": "r1", "classe": "texto", "bbox": [-30.0, -20.0, 550.0, 750.0], "de": "prop1"},
                # Ultrapassa borda direita [100, 100, 520, 200]
                {"id": "r2", "classe": "texto", "bbox": [100.0, 100.0, 520.0, 200.0]},
            ],
        }
        res = servidor.salvar_diamond(self.lote, reg)
        # r1 recortado para [0.0, 0.0, 500.0, 700.0]
        self.assertEqual(res["regioes"][0]["bbox"], [0.0, 0.0, 500.0, 700.0])
        # r2 recortado para [100.0, 100.0, 500.0, 200.0]
        self.assertEqual(res["regioes"][1]["bbox"], [100.0, 100.0, 500.0, 200.0])

        # Caixa completamente fora gera recorte sem area -> levanta ValueError
        reg_fora = {
            "page_id": "p01",
            "anotador": "Pedro",
            "status": "rascunho",
            "regioes": [
                {"id": "r3", "classe": "texto", "bbox": [-100.0, -100.0, -10.0, -10.0]}
            ],
        }
        with self.assertRaises(ValueError):
            servidor.salvar_diamond(self.lote, reg_fora)

    def test_12_salvar_diamond_status_concluida_cobertura(self):
        """12. Concluida com palavra sem caixa ou em duas caixas levanta ValueError; com tudo coberto grava."""
        palavras = [
            montar_palavra("Primeira", 20.0, 20.0, 60.0, 35.0, 0),
            montar_palavra("Segunda", 80.0, 20.0, 120.0, 35.0, 0),
            montar_palavra("---", 130.0, 20.0, 140.0, 35.0, -1),
        ]
        self._criar_tarefa("p01", palavras=palavras)
        base = {"page_id": "p01", "anotador": "Pedro", "status": "concluida"}

        # Subcaso 1: Palavra 'Segunda' sem caixa
        with self.assertRaises(ValueError) as ctx1:
            servidor.salvar_diamond(self.lote, {
                **base,
                "regioes": [{"id": "r1", "classe": "texto", "bbox": [10.0, 10.0, 70.0, 40.0]}],
            })
        self.assertIn("palavras sem caixa", str(ctx1.exception))

        # Subcaso 2: Palavra 'Primeira' em duas caixas nao-figura
        with self.assertRaises(ValueError) as ctx2:
            servidor.salvar_diamond(self.lote, {
                **base,
                "regioes": [
                    {"id": "r1", "classe": "texto", "bbox": [10.0, 10.0, 70.0, 40.0]},
                    {"id": "r2", "classe": "texto", "bbox": [10.0, 10.0, 130.0, 40.0]},
                ],
            })
        self.assertIn("em duas caixas", str(ctx2.exception))

        # Subcaso 3: Palavra em 'figura' e 'texto' (permitido) e segunda em 'texto' -> grava com sucesso
        res_fig = servidor.salvar_diamond(self.lote, {
            **base,
            "regioes": [
                {"id": "rf", "classe": "figura", "bbox": [0.0, 0.0, 200.0, 100.0]},
                {"id": "rt", "classe": "texto", "bbox": [10.0, 10.0, 130.0, 40.0]},
            ],
        })
        self.assertEqual(res_fig["status"], "concluida")
        self.assertEqual(res_fig["palavras_sem_caixa"], 0)
        self.assertEqual(res_fig["palavras_em_duas_caixas"], 0)

        # Subcaso 4: Ambas cobertas exatamente por caixas nao sobrepostas (separador '---' ignorado)
        res_ok = servidor.salvar_diamond(self.lote, {
            **base,
            "regioes": [
                {"id": "r1", "classe": "texto", "bbox": [10.0, 10.0, 70.0, 40.0]},
                {"id": "r2", "classe": "texto", "bbox": [75.0, 10.0, 125.0, 40.0]},
            ],
        })
        self.assertEqual(res_ok["status"], "concluida")
        self.assertEqual(res_ok["palavras_sem_caixa"], 0)
        self.assertEqual(res_ok["palavras_em_duas_caixas"], 0)

    def test_13_mudancas_contagem(self):
        """13. Mudancas: intacta, so caixa, so classe, apagada e criada contadas corretamente."""
        proposta = [
            {"id": "p1", "classe": "texto", "bbox": [10.0, 10.0, 50.0, 50.0]},
            {"id": "p2", "classe": "texto", "bbox": [10.0, 60.0, 50.0, 90.0]},
            {"id": "p3", "classe": "texto", "bbox": [10.0, 100.0, 50.0, 130.0]},
            {"id": "p4", "classe": "titulo", "bbox": [10.0, 140.0, 50.0, 170.0]},
            {"id": "p5", "classe": "texto", "bbox": [10.0, 180.0, 50.0, 210.0]},
            {"id": "p6", "classe": "texto", "bbox": [10.0, 220.0, 50.0, 250.0]},
        ]
        regioes = [
            {"id": "r1", "classe": "texto", "bbox": [10.0, 10.0, 50.0, 50.0], "de": "p1"},        # intacta
            {"id": "r2", "classe": "texto", "bbox": [10.0, 60.0, 55.0, 90.0], "de": "p2"},        # so caixa (diff 5.0 > 1.0)
            {"id": "r3", "classe": "titulo", "bbox": [10.0, 100.0, 50.0, 130.0], "de": "p3"},     # so classe
            {"id": "r4", "classe": "texto", "bbox": [10.0, 140.0, 55.0, 175.0], "de": "p4"},      # caixa_e_classe
            {"id": "r6", "classe": "texto", "bbox": [10.0, 220.5, 50.5, 250.0], "de": "p6"},      # intacta (diff 0.5 <= 1.0)
            {"id": "r7", "classe": "outro", "bbox": [10.0, 300.0, 50.0, 330.0], "de": None},       # criada
            # p5 ausente -> apagada
        ]
        m = servidor._mudancas(regioes, proposta)
        self.assertEqual(m["proposta"], 6)
        self.assertEqual(m["intactas"], 2)
        self.assertEqual(m["caixa"], 1)
        self.assertEqual(m["classe"], 1)
        self.assertEqual(m["caixa_e_classe"], 1)
        self.assertEqual(m["apagadas"], 1)
        self.assertEqual(m["criadas"], 1)


if __name__ == "__main__":
    unittest.main()
