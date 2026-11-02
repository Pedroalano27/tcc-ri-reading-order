"""Testes do exportador Diamond -> YOLO (src/data/exportar_deteccao.py). Sem I/O de dados reais."""
from __future__ import annotations

import unittest

from src.data.exportar_deteccao import rotulos_yolo, IDX
from src.data.regioes import CLASSES


class TestRotulosYolo(unittest.TestCase):
    def test_caixa_cheia_normaliza_ao_centro(self):
        linhas = rotulos_yolo([{"classe": "texto", "bbox": [0, 0, 600, 800]}], 600, 800)
        self.assertEqual(linhas, [f"{IDX['texto']} 0.500000 0.500000 1.000000 1.000000"])

    def test_indice_da_classe(self):
        # a ordem dos indices segue CLASSES
        linha = rotulos_yolo([{"classe": "figura", "bbox": [0, 0, 60, 80]}], 600, 800)[0]
        self.assertTrue(linha.startswith(str(CLASSES.index("figura")) + " "))

    def test_coordenadas_invertidas_sao_ordenadas(self):
        # x0>x1 e y0>y1 nao devem gerar largura/altura negativas
        linha = rotulos_yolo([{"classe": "texto", "bbox": [300, 400, 100, 200]}], 600, 800)[0]
        _, cx, cy, w, h = linha.split()
        self.assertAlmostEqual(float(w), 200 / 600, places=5)
        self.assertAlmostEqual(float(h), 200 / 800, places=5)
        self.assertGreater(float(w), 0)

    def test_area_zero_e_descartada(self):
        self.assertEqual(rotulos_yolo([{"classe": "texto", "bbox": [10, 10, 10, 50]}], 600, 800), [])

    def test_classe_desconhecida_e_descartada(self):
        self.assertEqual(rotulos_yolo([{"classe": "xxx", "bbox": [0, 0, 60, 80]}], 600, 800), [])

    def test_coordenadas_fora_da_pagina_sao_limitadas(self):
        linha = rotulos_yolo([{"classe": "texto", "bbox": [-50, -50, 900, 1200]}], 600, 800)[0]
        _, cx, cy, w, h = linha.split()
        for v in (cx, cy, w, h):
            self.assertGreaterEqual(float(v), 0.0)
            self.assertLessEqual(float(v), 1.0)


if __name__ == "__main__":
    unittest.main()
