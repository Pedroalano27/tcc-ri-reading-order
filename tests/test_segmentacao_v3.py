"""
Testes de regressao para a segmentacao v3 (T24).

Cobre correcoes identificadas nas revisoes do Codex:
  - extrator._juntar_letras_espacadas (titulos espacados vs texto corrido)
  - extrator._cortes_locais (calhas locais e corredores)
  - projetar_ordem.projetar_pagina (projecao de ordem e desempate)
  - layout.tabelas (limiar e desduplicacao de caixas de tabela)
  - layout.GravadorCache e layout.carregar_cache (resiliencia a linhas truncadas e falhas)
"""
from __future__ import annotations

import os
import json
import tempfile
import unittest

from src.data import extrator
from src.data import layout
from src.anotacao import projetar_ordem


def montar_linha_palavras(
    texto: str,
    x_inicio: float = 0.0,
    top: float = 100.0,
    altura: float = 9.0,
    vao: float = 2.5,
) -> list[dict]:
    """Monta lista de palavras sinteticas em uma unica linha.

    Para uma linha: cada token com largura 5 * len(t) pt, vao de 2.5 pt, top=100, altura 9.
    """
    tokens = texto.split()
    palavras = []
    x = x_inicio
    bottom = top + altura
    for s, t in enumerate(tokens):
        larg = 5.0 * len(t)
        palavras.append({
            "t": t,
            "x0": round(x, 2),
            "x1": round(x + larg, 2),
            "top": top,
            "bottom": bottom,
            "s": s,
        })
        x += larg + vao
    return palavras


def montar_faixa(
    intervalos: list[list[float] | tuple[float, float]],
    top: float = 100.0,
    altura: float = 9.0,
) -> dict:
    """Monta uma faixa com palavras sinteticas nos intervalos [a, b] dados."""
    ws = []
    bottom = top + altura
    for s, (a, b) in enumerate(intervalos):
        t = "X" * max(1, int(round((b - a) / 5.0)))
        ws.append({
            "t": t,
            "x0": float(a),
            "x1": float(b),
            "top": top,
            "bottom": bottom,
            "s": s,
        })
    return {"ws": ws, "top": top, "bottom": bottom}


class TestSegmentacaoV3(unittest.TestCase):
    # -----------------------------------------------------------------------
    # extrator._juntar_letras_espacadas
    # -----------------------------------------------------------------------

    def test_01_juntar_letras_espacadas_juntam(self):
        """Casos onde as letras espacadas devem se juntar."""
        casos = [
            ("R E S O L V E:", ["RESOLVE:"]),
            ("PA R E C E R", ["PARECER"]),
            ("A T O S", ["ATOS"]),
            ("w w w. c o n g o", ["www.congo"]),
        ]
        for entrada, esperado in casos:
            with self.subTest(entrada=entrada):
                ws = montar_linha_palavras(entrada)
                res = extrator._juntar_letras_espacadas(ws)
                self.assertEqual([w["t"] for w in res], esperado)

    def test_02_juntar_letras_espacadas_nao_juntam(self):
        """Casos onde palavras/siglas proximas nao devem se juntar (lista sai igual)."""
        casos = [
            "e se eu me",
            "SP RJ MG ES",
            "I, II e XI do",
            "e o Sr. J.",
        ]
        for entrada in casos:
            with self.subTest(entrada=entrada):
                ws = montar_linha_palavras(entrada)
                res = extrator._juntar_letras_espacadas(ws)
                self.assertEqual([w["t"] for w in res], entrada.split())
                self.assertEqual(res, ws)

    # -----------------------------------------------------------------------
    # extrator._cortes_locais
    # -----------------------------------------------------------------------

    def test_03_cortes_locais_cinco_faixas_iguais(self):
        """Cinco faixas iguais com palavras em [0,10] e [30,60] -> ha corte (len(cortes) == 5)."""
        faixas = [
            montar_faixa([[0, 10], [30, 60]], top=100.0 + i * 15.0)
            for i in range(5)
        ]
        cortes = extrator._cortes_locais(
            faixas, vao_max=36, larg_min=3.0, n_min=4, fator_espaco=0.1
        )
        self.assertEqual(len(cortes), 5)

    def test_04_cortes_locais_corredores_incompativeis(self):
        """Corredores incompativeis: central [0,10],[30,60] com vizinhas deslocadas.

        Nenhum corte deve envolver as palavras da faixa central.
        """
        faixas = [
            montar_faixa([[0, 10], [14, 60]], top=100.0),
            montar_faixa([[0, 10], [14, 60]], top=115.0),
            montar_faixa([[0, 10], [30, 60]], top=130.0),
            montar_faixa([[0, 26], [30, 60]], top=145.0),
            montar_faixa([[0, 26], [30, 60]], top=160.0),
        ]
        cortes = extrator._cortes_locais(
            faixas, vao_max=36, larg_min=3.0, n_min=4, fator_espaco=0.1
        )
        palavras_centrais = {id(w) for w in faixas[2]["ws"]}
        for ant_id, w_id in cortes:
            self.assertNotIn(ant_id, palavras_centrais)
            self.assertNotIn(w_id, palavras_centrais)

    def test_05_cortes_locais_calha_valida_so_abaixo(self):
        """Calha valida so abaixo: o par de palavras da faixa alvo esta em cortes."""
        faixas = []
        top = 100.0
        for _ in range(5):
            faixas.append(montar_faixa([[0, 150]], top=top))
            top += 15.0

        faixas.append(montar_faixa([[0, 50], [60, 150]], top=top))
        top += 15.0

        faixa_alvo = montar_faixa([[0, 50], [90, 150]], top=top)
        faixas.append(faixa_alvo)
        top += 15.0

        for _ in range(3):
            faixas.append(montar_faixa([[0, 80], [90, 150]], top=top))
            top += 15.0

        cortes = extrator._cortes_locais(
            faixas, vao_max=36, larg_min=3.0, n_min=4, fator_espaco=0.1
        )
        ant_id = id(faixa_alvo["ws"][0])
        w_id = id(faixa_alvo["ws"][1])
        self.assertIn((ant_id, w_id), cortes)

    # -----------------------------------------------------------------------
    # projetar_ordem.projetar_pagina
    # -----------------------------------------------------------------------

    def test_06_projetar_pagina_ordens_insercao(self):
        """Mesma segmentacao, as duas ordens de insercao do dict -> 'limpa' nas duas."""
        anotacao = {"ordem": ["b0", "b1"]}
        antigas = {
            "b0": [["A", 0, 0, 1, 1], ["B", 1.1, 0, 2.1, 1]],
            "b1": [["C", 10, 0, 11, 1]],
        }
        novas_1 = {
            "b0": [["A", 0, 0, 1, 1], ["B", 1.1, 0, 2.1, 1]],
            "b1": [["C", 10, 0, 11, 1]],
        }
        novas_2 = {
            "b1": [["C", 10, 0, 11, 1]],
            "b0": [["A", 0, 0, 1, 1], ["B", 1.1, 0, 2.1, 1]],
        }
        res1 = projetar_ordem.projetar_pagina(anotacao, antigas, novas_1)
        res2 = projetar_ordem.projetar_pagina(anotacao, antigas, novas_2)

        self.assertEqual(res1["status"], "limpa")
        self.assertEqual(res1["ordem"], ["b0", "b1"])
        self.assertEqual(res2["status"], "limpa")
        self.assertEqual(res2["ordem"], ["b0", "b1"])

    def test_07_projetar_pagina_palavra_nova_sem_par(self):
        """Palavra nova sem par ('NOVA' em b0) -> 'conflito' e palavras_novas_sem_par == ['NOVA']."""
        anotacao = {"ordem": ["b0", "b1"]}
        antigas = {
            "b0": [["A", 0, 0, 1, 1], ["B", 1.1, 0, 2.1, 1]],
            "b1": [["C", 10, 0, 11, 1]],
        }
        novas = {
            "b0": [["A", 0, 0, 1, 1], ["B", 1.1, 0, 2.1, 1], ["NOVA", 30, 0, 34, 1]],
            "b1": [["C", 10, 0, 11, 1]],
        }
        res = projetar_ordem.projetar_pagina(anotacao, antigas, novas)
        self.assertEqual(res["status"], "conflito")
        self.assertEqual(res["palavras_novas_sem_par"], ["NOVA"])

    def test_08_projetar_pagina_separador_perdido(self):
        """Separador perdido ('***' em b0 ausente nas novas) -> 'limpa'."""
        anotacao = {"ordem": ["b0", "b1"]}
        antigas = {
            "b0": [["A", 0, 0, 1, 1], ["B", 1.1, 0, 2.1, 1], ["***", 5, 0, 6, 1]],
            "b1": [["C", 10, 0, 11, 1]],
        }
        novas = {
            "b0": [["A", 0, 0, 1, 1], ["B", 1.1, 0, 2.1, 1]],
            "b1": [["C", 10, 0, 11, 1]],
        }
        res = projetar_ordem.projetar_pagina(anotacao, antigas, novas)
        self.assertEqual(res["status"], "limpa")
        self.assertEqual(res["ordem"], ["b0", "b1"])

    def test_09_projetar_pagina_texto_exato_antes_de_substring(self):
        """Texto exato antes de substring: antigas com 'AA' e 'A', duas atribuicoes de ids -> 'limpa'."""
        anotacao = {"ordem": ["b0", "b1"]}
        antigas = {
            "b0": [["AA", 0, 0, 4, 4]],
            "b1": [["A", 0, 0, 4, 4]],
        }
        novas_1 = {
            "b0": [["AA", 0, 0, 4, 4]],
            "b1": [["A", 0, 0, 4, 4]],
        }
        novas_2 = {
            "b0": [["A", 0, 0, 4, 4]],
            "b1": [["AA", 0, 0, 4, 4]],
        }
        res1 = projetar_ordem.projetar_pagina(anotacao, antigas, novas_1)
        res2 = projetar_ordem.projetar_pagina(anotacao, antigas, novas_2)
        self.assertEqual(res1["status"], "limpa")
        self.assertEqual(res2["status"], "limpa")

    # -----------------------------------------------------------------------
    # layout.tabelas
    # -----------------------------------------------------------------------

    def test_10_tabelas_none(self):
        """tabelas(None) is None."""
        self.assertIsNone(layout.tabelas(None))

    def test_11_tabelas_filtragem_deduplicacao(self):
        """Deduplicacao de tabelas sobrepostas e filtragem por score."""
        regioes = [
            {"rotulo": "table", "score": 0.9, "bbox": [10.0, 20.0, 100.0, 200.0]},
            {"rotulo": "table", "score": 0.8, "bbox": [10.5, 20.5, 100.0, 200.0]},
            {"rotulo": "picture", "score": 0.95, "bbox": [10.0, 20.0, 100.0, 200.0]},
            {"rotulo": "table", "score": 0.4, "bbox": [300.0, 300.0, 400.0, 400.0]},
        ]
        res = layout.tabelas(regioes)
        self.assertEqual(res, [[10.0, 20.0, 100.0, 200.0]])

    # -----------------------------------------------------------------------
    # layout.GravadorCache e layout.carregar_cache
    # -----------------------------------------------------------------------

    def test_12_cache_recuperacao_linha_truncada(self):
        """Linha truncada sem quebra seguida de nova gravacao: dois registros validos voltam."""
        with tempfile.TemporaryDirectory() as d:
            caminho = os.path.join(d, "x.jsonl")
            reg1 = {
                "page_id": "pid_valido_1",
                "modelo": layout.MODELO,
                "revisao": layout.REVISAO,
                "dpi": layout.DPI,
                "bbox_imagem": [0.0, 0.0, 100.0, 100.0],
                "escala": 1.0,
                "regioes": [{"rotulo": "table", "score": 0.9, "bbox": [0.0, 0.0, 10.0, 10.0]}],
            }
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(json.dumps(reg1) + "\n")
                f.write('{"page_id": "pid_fragmento_sem_newline"')

            gravador = layout.GravadorCache(d)
            gravador(
                "pid_valido_2",
                "x",
                [{"rotulo": "table", "score": 0.8, "bbox": [1.0, 1.0, 9.0, 9.0]}],
                ((0.0, 0.0, 100.0, 100.0), 1.0),
            )
            gravador.fechar()

            cache = layout.carregar_cache(d)
            self.assertEqual(set(cache.keys()), {"pid_valido_1", "pid_valido_2"})

    def test_13_cache_fragmento_utf8_cortado(self):
        """Fragmento cortado no meio de byte UTF-8: sem excecao, os dois registros validos voltam."""
        with tempfile.TemporaryDirectory() as d:
            caminho = os.path.join(d, "x.jsonl")
            reg1 = {
                "page_id": "pid_valido_1",
                "modelo": layout.MODELO,
                "revisao": layout.REVISAO,
                "dpi": layout.DPI,
                "bbox_imagem": [0.0, 0.0, 100.0, 100.0],
                "escala": 1.0,
                "regioes": [{"rotulo": "table", "score": 0.9, "bbox": [0.0, 0.0, 10.0, 10.0]}],
            }
            with open(caminho, "wb") as f:
                f.write(json.dumps(reg1, ensure_ascii=False).encode("utf-8") + b"\n")
                f.write(b'{"page_id":"Edi\xc3')

            gravador = layout.GravadorCache(d)
            gravador(
                "pid_valido_2",
                "x",
                [{"rotulo": "table", "score": 0.8, "bbox": [1.0, 1.0, 9.0, 9.0]}],
                ((0.0, 0.0, 100.0, 100.0), 1.0),
            )
            gravador.fechar()

            cache = layout.carregar_cache(d)
            self.assertEqual(set(cache.keys()), {"pid_valido_1", "pid_valido_2"})

    def test_14_cache_gravador_falha(self):
        """gravador.falha grava registro que carregar_cache devolve como None."""
        with tempfile.TemporaryDirectory() as d:
            gravador = layout.GravadorCache(d)
            gravador.falha("pid_com_falha", "x", "erro simulado de renderizacao")
            gravador.fechar()

            cache = layout.carregar_cache(d)
            self.assertIn("pid_com_falha", cache)
            self.assertIsNone(cache["pid_com_falha"])


if __name__ == "__main__":
    unittest.main()
