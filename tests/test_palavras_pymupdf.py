"""
Testes do adaptador PyMuPDF com PDFs sinteticos gerados em memoria.

Compara o contrato e a geometria com o caminho original, incluindo CropBox,
rotacao, fluxo contrario a geometria, fontes e desduplicacao. Verifica tambem
os blocos e as ordens em um exemplo multicoluna sem depender do acervo.

Uso: venv/Scripts/python.exe -B -m unittest tests.test_palavras_pymupdf -v
     venv/Scripts/python.exe -B -m unittest discover -s tests -v
"""
from __future__ import annotations

import io
import unittest

import pdfplumber
import pymupdf

from src.data.extrator import palavras_da_pagina, segmentar, xycut
from src.data.palavras_pymupdf import palavras_da_pagina_pymupdf


class TestPalavrasPyMuPDF(unittest.TestCase):
    def setUp(self):
        self.doc = pymupdf.open()
        self.page = self.doc.new_page(width=400, height=500)

    def tearDown(self):
        self.doc.close()

    def comparar(self, tolerancia=0.003):
        with pdfplumber.open(io.BytesIO(self.doc.tobytes())) as pdf:
            original = palavras_da_pagina(pdf.pages[0])
        novo = palavras_da_pagina_pymupdf(self.page)
        self.assertEqual([w['t'] for w in original], [w['t'] for w in novo])
        self.assertEqual([w['s'] for w in original], [w['s'] for w in novo])
        for a, b in zip(original, novo):
            self.assertEqual(set(b), {'t', 'x0', 'x1', 'top', 'bottom', 's'})
            for k in ('x0', 'x1', 'top', 'bottom'):
                self.assertAlmostEqual(a[k], b[k], delta=tolerancia, msg=f'{a["t"]}: {k}')
        return original, novo

    def test_pagina_vazia(self):
        self.assertEqual(self.comparar(), ([], []))

    def test_contrato_fontes_e_pontuacao(self):
        for j, fonte in enumerate(('helv', 'hebo', 'heit', 'tiro', 'tibo', 'cour')):
            self.page.insert_text((35, 55 + 35 * j), 'Art. 1: resolucao, 2026.',
                                  fontname=fonte, fontsize=9 + j)
        self.comparar()

    def test_cropbox_deslocada_inclui_texto_fora_do_recorte(self):
        self.page.insert_text((10, 20), 'FORA')
        self.page.insert_text((100, 120), 'DENTRO')
        self.page.set_cropbox(pymupdf.Rect(40, 50, 350, 450))
        _, novo = self.comparar()
        self.assertEqual([w['t'] for w in novo], ['FORA', 'DENTRO'])
        self.assertEqual(novo[0]['x0'], 10)

    def test_rotacao_da_pagina(self):
        self.page.insert_text((100, 120), 'ABC texto')
        for rotacao in (0, 90, 180, 270):
            with self.subTest(rotacao=rotacao):
                self.page.set_rotation(rotacao)
                self.comparar()

    def test_rotacao_com_cropbox(self):
        self.page.insert_text((100, 120), 'ABC texto')
        self.page.set_cropbox(pymupdf.Rect(40, 50, 350, 450))
        for rotacao in (0, 90, 180, 270):
            with self.subTest(rotacao=rotacao):
                self.page.set_rotation(rotacao)
                self.comparar()

    def test_texto_vertical_descartado(self):
        self.page.insert_text((100, 220), 'VERTICAL', rotate=90)
        self.page.insert_text((80, 80), 'HORIZONTAL')
        _, novo = self.comparar()
        self.assertEqual([w['t'] for w in novo], ['HORIZONTAL'])

    def test_texto_vertical_fica_horizontal_apos_rotacao(self):
        self.page.insert_text((100, 220), 'VERTICAL', rotate=90)
        self.page.set_rotation(90)
        self.comparar()

    def test_origem_mediabox_nao_nula(self):
        self.doc.xref_set_key(self.page.xref, 'MediaBox', '[20 30 420 530]')
        self.page = self.doc.reload_page(self.page)
        self.page.insert_text((100, 120), 'Texto')
        for rotacao in (0, 90, 180, 270):
            with self.subTest(rotacao=rotacao):
                self.page.set_rotation(rotacao)
                self.comparar()

    def test_fluxo_diferente_da_ordem_geometrica(self):
        self.page.insert_text((240, 200), 'Primeiro')
        self.page.insert_text((40, 60), 'Segundo')
        _, novo = self.comparar()
        self.assertEqual([w['t'] for w in novo], ['Primeiro', 'Segundo'])

    def test_negrito_falso(self):
        self.page.insert_text((50, 80), 'Texto duplicado')
        self.page.insert_text((50.3, 80.3), 'Texto duplicado')
        diag = {}
        novo = palavras_da_pagina_pymupdf(self.page, diagnostico=diag)
        self.assertEqual([w['t'] for w in novo], ['Texto', 'duplicado'])
        self.assertGreater(diag['caracteres_desduplicados'], 0)
        self.comparar()

    def test_preenchimento_e_contorno(self):
        self.page.insert_text((50, 80), 'Texto', render_mode=2)
        _, novo = self.comparar()
        self.assertEqual([w['t'] for w in novo], ['Texto'])

    def test_mesmo_texto_em_posicoes_diferentes(self):
        for x, y in ((40, 80), (200, 80), (40, 160)):
            self.page.insert_text((x, y), 'Texto')
        _, novo = self.comparar()
        self.assertEqual(len(novo), 3)

    def test_letras_espacadas(self):
        self.page.insert_text((40, 80), 'R E S O L V E:', fontsize=12)
        _, novo = self.comparar()
        self.assertEqual([w['t'] for w in novo], ['RESOLVE:'])

    def test_tokens_em_operadores_separados(self):
        self.page.insert_text((40, 80), 'Texto', fontsize=12)
        largura = pymupdf.get_text_length('Texto', fontsize=12)
        self.page.insert_text((40 + largura + 1, 80), 'junto', fontsize=12)
        _, novo = self.comparar()
        self.assertEqual([w['t'] for w in novo], ['Textojunto'])

    def test_fontdescriptor_embutido(self):
        fonte = pymupdf.Font('cjk')
        self.page.insert_font(fontname='embutida', fontbuffer=fonte.buffer)
        self.page.insert_text((40, 80), 'Texto com fonte embutida', fontname='embutida')
        # Fontes embutidas podem ter larguras PDF arredondadas a 1/1000 em.
        self.comparar(tolerancia=0.02)

    def test_ligadura_nao_cria_corte_no_meio_da_palavra(self):
        fonte = pymupdf.Font('cjk')
        self.assertGreater(fonte.has_glyph(0xfb01), 0)
        xref = self.page.insert_font(fontname='embutida', fontbuffer=fonte.buffer)
        # ToUnicode multicaractere faz o trace devolver componentes com glifo -1.
        # A mudanca e somente no PDF sintetico em memoria, sem tocar no acervo.
        _, referencia = self.doc.xref_get_key(xref, 'ToUnicode')
        cmap_xref = int(referencia.split()[0])
        cmap = self.doc.xref_stream(cmap_xref)
        cmap = cmap.replace(b'<83fe> <83ff> <fb01>',
                            b'<83fe> <83ff> [<00660069> <0066006c>]')
        cmap = cmap.replace(b'<8400> <8401> <fb03>',
                            b'<8400> <8401> [<006600660069> <00660066006c>]')
        self.doc.update_stream(cmap_xref, cmap)
        self.page.insert_text((40, 80), 'O\ufb01cial a\ufb03nidade', fontname='embutida')
        _, novo = self.comparar(tolerancia=0.02)
        self.assertEqual([w['t'] for w in novo], ['Oficial', 'affinidade'])
        diag = {}
        palavras_da_pagina_pymupdf(self.page, diagnostico=diag)
        self.assertGreater(diag.get('componentes_ligadura_unidos', 0), 0)

    def test_nao_modifica_pagina(self):
        self.page.insert_text((40, 80), 'Texto')
        self.page.set_cropbox(pymupdf.Rect(20, 30, 380, 480))
        antes = (tuple(self.page.cropbox), self.page.rotation,
                 self.doc.xref_object(self.page.xref), self.page.read_contents())
        palavras_da_pagina_pymupdf(self.page)
        depois = (tuple(self.page.cropbox), self.page.rotation,
                  self.doc.xref_object(self.page.xref), self.page.read_contents())
        self.assertEqual(antes, depois)

    def test_segmentacao_e_ordens_multicoluna(self):
        for x in (220, 30):
            for j in range(5):
                self.page.insert_text((x, 70 + 13 * j), f'Linha {j} da coluna {x}', fontsize=10)
        a, b = self.comparar()
        tabelas = [[210, 55, 390, 130]]
        for tab in (None, tabelas):
            with self.subTest(tabelas=tab):
                ba, bb = segmentar(a, tab), segmentar(b, tab)
                self.assertEqual([v['texto'] for v in ba], [v['texto'] for v in bb])
                for chave in ('s', 'top'):
                    self.assertEqual(sorted(range(len(ba)), key=lambda i: ba[i][chave]),
                                     sorted(range(len(bb)), key=lambda i: bb[i][chave]))
                self.assertEqual(xycut(list(range(len(ba))), ba), xycut(list(range(len(bb))), bb))

    def test_pareamento_maximo_nao_conta_um_bloco_duas_vezes(self):
        from orquestracao.analises.extrator_pymupdf_paridade import casar
        def caixa(x):
            return {'t': 'igual', 'x0': x, 'x1': x + 10, 'top': 0, 'bottom': 10}
        # O primeiro bloco tem dois candidatos; o segundo so tem o primeiro.
        pares = casar([caixa(0), caixa(5)], [caixa(2), caixa(-2)], limiar=0.4)
        self.assertEqual(len(pares), 2)
        self.assertEqual(len({j for _, j in pares}), 2)

    def test_tau_usa_identidade_casada_e_nao_indice_local(self):
        from orquestracao.analises.extrator_pymupdf_paridade import comparar_blocos
        def bloco(texto, x, s):
            return {'texto': texto, 'x0': x, 'x1': x + 30, 'top': 20, 'bottom': 40, 's': s}
        a = [bloco('esquerda', 10, 0), bloco('direita', 100, 1)]
        b = [bloco('direita', 100, 0), bloco('esquerda', 10, 1)]
        r = comparar_blocos(a, b)
        self.assertTrue(r['mesma'])
        self.assertEqual(r['tau'], {'stream': -1, 'naive': 1, 'xycut': 1})
        self.assertFalse(r['ordem_total_igual']['stream'])

    def test_tau_indisponivel_para_menos_de_dois_pares(self):
        from orquestracao.analises.extrator_pymupdf_paridade import tau_ordens
        self.assertIsNone(tau_ordens([], []))
        self.assertIsNone(tau_ordens([0], [0]))


if __name__ == '__main__':
    unittest.main()
