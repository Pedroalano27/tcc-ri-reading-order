"""Testa contrato, margens e cortes do corpo sem PDF, modelo ou arquivos de dados.

Uso: venv/Scripts/python.exe -B -m unittest tests.test_politica_margens -v
"""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.eval.politica_margens import aplicar_margens, xycut_margens

DIMENSOES = {"width": 600, "height": 1000}


def bloco(bid, x0=10, y0=200, x1=200, y1=300, texto="Conteudo", classe=None):
    b = {"id": bid, "bbox": [x0, y0, x1, y1], "text": texto}
    if classe is not None:
        b["classe"] = classe
    return b


class TestPoliticaMargens(unittest.TestCase):
    def test_pagina_sem_cabecalho_preserva_corpo_arbitrario(self):
        bs = [bloco("a"), bloco("b", y0=400, y1=500), bloco("c", x0=350, x1=550)]
        self.assertEqual(aplicar_margens(bs, ["b", "c", "a"], DIMENSOES), ["b", "c", "a"])

    def test_cabecalho_dois_campos_lado_a_lado(self):
        bs = [bloco("direita", x0=400, x1=550, y0=20, y1=35),
              bloco("corpo"), bloco("esquerda", y0=20, y1=35)]
        self.assertEqual(aplicar_margens(bs, ["corpo", "direita", "esquerda"], DIMENSOES),
                         ["esquerda", "direita", "corpo"])

    def test_rodape_multilinha_e_marcas_antes_dele(self):
        bs = [bloco("r2", y0=980, y1=995), bloco("corpo"),
              bloco("r1", y0=955, y1=975), bloco("m", y0=998, y1=999, texto="<@fim> contPageBreak2")]
        self.assertEqual(aplicar_margens(bs, ["r2", "r1", "m", "corpo"], DIMENSOES),
                         ["corpo", "m", "r1", "r2"])

    def test_pagina_so_com_tabela_nao_parte_caixa(self):
        bs = [bloco("t", y0=10, y1=995, classe="tabela")]
        p = {"page_id": "tabela#p0", "bounding_boxes": bs, "dimensions": DIMENSOES}
        self.assertEqual(aplicar_margens(bs, ["t"], DIMENSOES), ["t"])
        self.assertEqual(xycut_margens(p), ["t"])

    def test_ordem_invalida_rejeitada(self):
        bs = [bloco("a"), bloco("b")]
        for ordem in (["a"], ["a", "a"], ["a", "desconhecido"], ["a", "b", "extra"]):
            with self.subTest(ordem=ordem), self.assertRaises(ValueError):
                aplicar_margens(bs, ordem, DIMENSOES)
        with self.assertRaises(ValueError):
            aplicar_margens([bloco("a"), bloco("a")], ["a", "a"], DIMENSOES)

    def test_classes_substituem_geometria_sem_fallback(self):
        bs = [bloco("titulo", y0=10, y1=25, classe="titulo"),
              bloco("c", y0=150, y1=170, classe="cabecalho"),
              bloco("r", y0=500, y1=600, classe="rodape"), bloco("sem", y0=970, y1=990)]
        self.assertEqual(aplicar_margens(bs, ["r", "sem", "titulo", "c"], DIMENSOES, variante="classe"),
                         ["c", "sem", "titulo", "r"])

    def test_limites_estritos_e_base_do_topo(self):
        bs = [bloco("centro70", y0=50, y1=90), bloco("base100", y0=0, y1=100),
              bloco("centro950", y0=940, y1=960), bloco("dentro", y0=20, y1=30)]
        self.assertEqual(aplicar_margens(bs, ["centro950", "base100", "centro70", "dentro"], DIMENSOES),
                         ["dentro", "centro950", "base100", "centro70"])

    def test_marca_mista_e_texto_ausente_nao_sao_marcas(self):
        bs = [bloco("misto", texto="<@inicio> texto"), bloco("vazio", texto=None), bloco("m", texto="<#fim>")]
        self.assertEqual(aplicar_margens(bs, ["m", "misto", "vazio"], DIMENSOES), ["misto", "vazio", "m"])
        self.assertEqual(aplicar_margens(bs, ["m", "misto", "vazio"], DIMENSOES, padrao_marcacao=None),
                         ["m", "misto", "vazio"])

    def test_idempotencia_pureza_e_desempate_indice(self):
        bs = [bloco("z", y0=10, y1=20), bloco("a", y0=10, y1=20), bloco("c")]
        ordem = ["c", "a", "z"]
        antes = copy.deepcopy((bs, ordem, DIMENSOES))
        nova = aplicar_margens(bs, ordem, DIMENSOES)
        self.assertEqual(nova, ["z", "a", "c"])
        self.assertEqual(aplicar_margens(bs, nova, DIMENSOES), nova)
        self.assertEqual((bs, ordem, DIMENSOES), antes)
        self.assertIsNot(nova, ordem)

    def test_dimensoes_caixas_e_parametros_invalidos(self):
        for dim in ({"width": 0, "height": 1000}, {"width": 600, "height": float("nan")}, {}):
            with self.subTest(dim=dim), self.assertRaises(ValueError):
                aplicar_margens([bloco("a")], ["a"], dim)
        for bbox in ([0, 20, 10, 10], [0, 0, float("inf"), 20], [0, 1, 2]):
            with self.subTest(bbox=bbox), self.assertRaises(ValueError):
                aplicar_margens([{"id": "a", "bbox": bbox}], ["a"], DIMENSOES)
        with self.assertRaises(ValueError):
            aplicar_margens([], [], DIMENSOES, variante="inexistente")
        with self.assertRaises(ValueError):
            aplicar_margens([], [], DIMENSOES, limiar_topo=0.2)

    def test_pagina_vazia(self):
        p = {"page_id": "vazia", "bounding_boxes": [], "dimensions": DIMENSOES}
        self.assertEqual(aplicar_margens([], [], DIMENSOES), [])
        self.assertEqual(xycut_margens(p), [])

    def test_xycut_recorta_corpo_antes_dos_cortes(self):
        # Corpo multicoluna preservado depois de separar o cabecalho.
        bs = [bloco("c", x0=0, y0=30, x1=600, y1=50),
              bloco("l1", y0=60, y1=80), bloco("l2", y0=300, y1=320),
              bloco("r1", x0=400, x1=550, y0=60, y1=80),
              bloco("r2", x0=400, x1=550, y0=300, y1=320)]
        p = {"page_id": "colunas", "bounding_boxes": bs, "dimensions": DIMENSOES}
        antes = copy.deepcopy(p)
        self.assertEqual(xycut_margens(p), ["c", "l1", "l2", "r1", "r2"])
        self.assertEqual(p, antes)


    def test_recorte_e_pos_processamento_nao_sao_equivalentes(self):
        bs = [bloco("m", x0=0, y0=400, x1=600, y1=410, texto="<@fim>"),
              bloco("l1", y0=200, y1=220), bloco("l2", y0=600, y1=620),
              bloco("r1", x0=400, x1=550, y0=200, y1=220),
              bloco("r2", x0=400, x1=550, y0=600, y1=620)]
        p = {"page_id": "marca_larga", "bounding_boxes": bs, "dimensions": DIMENSOES}
        from src.data.extrator import xycut
        from src.eval.baselines import caixas
        from src.eval.protocolo import ordem_entrada
        ids = [b["id"] for b in bs]
        pura = [ids[i] for i in xycut(ordem_entrada(p), caixas(p))]
        self.assertEqual(aplicar_margens(bs, pura, DIMENSOES), ["l1", "r1", "l2", "r2", "m"])
        self.assertEqual(xycut_margens(p), ["l1", "l2", "r1", "r2", "m"])


class TestAvaliacaoPareada(unittest.TestCase):
    def test_recorte_classe_compara_com_xycut_sem_margens(self):
        # Evita parear a classe com o recorte geometrico por engano de sufixo.
        from orquestracao.analises.politica_margens_avaliacao import resumir
        from src.eval.metrics import avaliar
        gt = ["a", "b", "c"]
        rows = [{"metricas": {"xycut_recalculada": avaliar(gt, gt),
                              "xycut_margens": avaliar(gt[::-1], gt),
                              "xycut_margens_classe": avaliar(gt, gt)}}]
        s = resumir(rows, nboot=100, seed=7)["xycut_margens_classe"]
        self.assertEqual(s["contra"], "xycut_recalculada")
        self.assertEqual(s["diferenca"]["kendall_tau"]["media"], 0)
        self.assertEqual(s["diferenca"]["kendall_tau"]["p_pratt"], 1)

    def test_pratt_empates_e_numeros_pequenos(self):
        from orquestracao.analises.politica_margens_avaliacao import pratt, ptexto
        self.assertEqual(pratt([0, 0, 0]), 1)
        self.assertNotEqual(ptexto(1e-8), "0,000000")


    def test_retomada_ignora_checkpoint_truncado_e_corrompido(self):
        from orquestracao.analises import politica_margens_avaliacao as a
        with tempfile.TemporaryDirectory() as tmp, patch.object(a, "SAIDA", Path(tmp) / "relatorio.md"):
            r1, r2 = {"paginas": [1]}, {"paginas": [1, 2]}
            a.SAIDA.write_text(a.checkpoint(r1) + a.checkpoint(r2)
                              + f"\n<!-- {a.MARCADOR}\nAAAA\n-->\n"
                              + f"\n<!-- {a.MARCADOR}\nQUEDA", encoding="utf-8")
            self.assertEqual(a.ler_cache(), r2)

    def test_diario_compacta_sem_deixar_resultados_antigos(self):
        from orquestracao.analises import politica_margens_avaliacao as a
        with tempfile.TemporaryDirectory() as tmp, patch.object(a, "SAIDA", Path(tmp) / "relatorio.md"), \
                patch.object(a, "renderizar", return_value="Número calculado: 7\n"):
            r = {"paginas": [1], "completo": False}
            a.gravar(r)
            r["paginas"].append(2)
            a.gravar(r)
            self.assertEqual(a.ler_cache(), r)
            self.assertEqual(a.SAIDA.read_text(encoding="utf-8").count(a.MARCADOR), 2)
            r["completo"] = True
            a.gravar(r)
            self.assertEqual(a.SAIDA.read_text(encoding="utf-8"), a.documento(r))
            self.assertEqual(a.ler_cache(), r)


    def test_checkpoint_preserva_ordem_das_tabelas_ao_recarregar(self):
        from orquestracao.analises import politica_margens_avaliacao as a
        with tempfile.TemporaryDirectory() as tmp, patch.object(a, "SAIDA", Path(tmp) / "relatorio.md"), \
                patch.object(a, "renderizar", side_effect=lambda r: "\n".join(r["metodos"])):
            r = {"completo": True, "metodos": {"xycut": 1, "naive": 2, "layoutlm_sucessor": 3}}
            a.gravar(r)
            self.assertEqual(a.documento(a.ler_cache()), a.SAIDA.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
