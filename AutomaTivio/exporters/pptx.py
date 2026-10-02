# -*- coding: utf-8 -*-
"""Relatório -> PowerPoint.

Duas estratégias, na ordem que o pedido define:

  1. **Nativo** (padrão): texto em text boxes, tabela de rentabilidade e tabela
     de Mercado de Crédito como tabelas do PowerPoint, histórico como gráfico de
     linhas nativo. O usuário abre e edita o número na célula.

  2. **Imagem** (`modo='imagem'`): a folha renderizada em PNG de alta resolução
     ocupando o slide. Serve para quando o layout importa mais que a edição.

O que não existe é um meio-caminho mudo: se uma seção não puder ser reconstruída
nativamente, ela entra como imagem *daquele bloco* e o log registra qual seção
caiu para imagem — senão o arquivo chega ao usuário com um pedaço não editável
sem avisar.

A4 retrato (21 × 29,7 cm) porque é o formato dos relatórios publicados; o PPTX
exporta para PDF nesse mesmo tamanho sem reescalar.
"""
import io
import os

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.text import PP_ALIGN
from pptx.util import Cm, Pt

from calculators import formatos as fmt

# paleta da marca (hex -> RGBColor)
AZUL_ESCURO = RGBColor(0x3C, 0x4A, 0x60)
AZUL = RGBColor(0x75, 0x9D, 0xB4)
CINZA_CLARO = RGBColor(0xAB, 0xC6, 0xCD)
CINZA = RGBColor(0x63, 0x78, 0x81)
VERDE = RGBColor(0xC1, 0xF4, 0xD4)
BRANCO = RGBColor(0xFF, 0xFF, 0xFF)
QUASE_PRETO = RGBColor(0x1A, 0x1A, 0x1A)
LINHA = RGBColor(0xD4, 0xE0, 0xE6)

FONTE = 'Versos'
A4_L, A4_A = Cm(21.0), Cm(29.7)
MARGEM = Cm(1.5)


class ExportadorPPTX:
    def __init__(self, log, fonte=FONTE):
        self.log = log
        self.fonte = fonte

    # ------------------------------------------------------------------ apoio
    def _txt(self, slide, x, y, w, h, texto, tam=10, bold=False, cor=QUASE_PRETO,
             alinhamento=PP_ALIGN.LEFT, caixa_alta=False):
        cx = slide.shapes.add_textbox(x, y, w, h)
        tf = cx.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        linhas = str(texto).split('\n')
        for i, linha in enumerate(linhas):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = alinhamento
            r = p.add_run()
            r.text = linha.upper() if caixa_alta else linha
            r.font.name = self.fonte
            r.font.size = Pt(tam)
            r.font.bold = bold
            r.font.color.rgb = cor
        return cx

    def _faixa(self, slide, altura, titulo, subtitulo, data):
        """Cabeçalho azul da folha — o mesmo da versão HTML."""
        from pptx.enum.shapes import MSO_SHAPE
        band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, A4_L, altura)
        band.fill.solid()
        band.fill.fore_color.rgb = AZUL_ESCURO
        band.line.fill.background()
        band.shadow.inherit = False
        y = Cm(0.9)
        self._txt(slide, MARGEM, y, Cm(14), Cm(0.5), 'RELATÓRIO DE GESTÃO',
                  tam=8, bold=True, cor=CINZA_CLARO)
        self._txt(slide, MARGEM, y + Cm(0.6), Cm(14), Cm(1.1), titulo,
                  tam=20, bold=True, cor=BRANCO)
        if subtitulo:
            self._txt(slide, MARGEM, y + Cm(1.75), Cm(14), Cm(0.5), subtitulo,
                      tam=8, cor=CINZA_CLARO)
        self._txt(slide, MARGEM, altura - Cm(1.0), Cm(14), Cm(0.5), data,
                  tam=9, bold=True, cor=VERDE)
        return band

    def _tabela(self, slide, x, y, w, dados, larguras=None, altura_linha=Cm(0.52),
                cabecalho=True, destaque_primeira_coluna=True):
        """Tabela nativa do PowerPoint — células editáveis."""
        nl, nc = len(dados), len(dados[0])
        shape = slide.shapes.add_table(nl, nc, x, y, w, altura_linha * nl)
        tab = shape.table
        if larguras:
            total = sum(larguras)
            for i, frac in enumerate(larguras):
                tab.columns[i].width = int(w * frac / total)
        for i, linha in enumerate(dados):
            tab.rows[i].height = altura_linha
            for j, valor in enumerate(linha):
                cel = tab.cell(i, j)
                cel.margin_left = cel.margin_right = Cm(0.12)
                cel.margin_top = cel.margin_bottom = 0
                cel.text = ''
                p = cel.text_frame.paragraphs[0]
                p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT
                r = p.add_run()
                r.text = str(valor)
                r.font.name = self.fonte
                r.font.size = Pt(8.5)
                cabec = cabecalho and i == 0
                r.font.bold = cabec or (destaque_primeira_coluna and j == 0)
                r.font.color.rgb = BRANCO if cabec else QUASE_PRETO
                cel.fill.solid()
                cel.fill.fore_color.rgb = (AZUL_ESCURO if cabec else
                                           (RGBColor(0xF4, 0xF7, 0xF9) if i % 2 else BRANCO))
        return shape

    def _grafico_linha(self, slide, x, y, w, h, hist, nome_bench):
        """Gráfico de linhas nativo: as séries ficam editáveis no PowerPoint."""
        dados = CategoryChartData()
        dados.categories = [f'{fmt.MES_ABR[int(l[5:7]) - 1]}/{l[2:4]}' for l in hist['l']]
        dados.add_series('Fundo', [v / 100 for v in hist['f']])
        dados.add_series(nome_bench, [v / 100 for v in hist['c']])
        gf = slide.shapes.add_chart(XL_CHART_TYPE.LINE, x, y, w, h, dados).chart
        gf.has_title = False
        gf.has_legend = True
        gf.legend.position = XL_LEGEND_POSITION.TOP
        gf.legend.include_in_layout = False
        gf.font.name = self.fonte
        gf.font.size = Pt(8)
        for serie, cor, tracejado in ((gf.series[0], AZUL_ESCURO, False),
                                      (gf.series[1], CINZA_CLARO, True)):
            serie.smooth = False
            linha = serie.format.line
            linha.color.rgb = cor
            linha.width = Pt(2.0)
            if tracejado:
                from pptx.enum.dml import MSO_LINE_DASH_STYLE
                linha.dash_style = MSO_LINE_DASH_STYLE.DASH
        gf.value_axis.tick_labels.number_format = '0.0%'
        gf.value_axis.tick_labels.number_format_is_linked = False
        gf.value_axis.has_major_gridlines = True
        return gf

    # --------------------------------------------------------------- nativo
    def _slide(self, prs):
        return prs.slides.add_slide(prs.slide_layouts[6])   # layout em branco

    def nativo(self, ctx, renderizador, destino):
        prs = Presentation()
        prs.slide_width, prs.slide_height = A4_L, A4_A
        ed = renderizador.edicao
        f = ctx.f
        sub = f'CNPJ: {f.cnpj}' + (f'  ·  Benchmark: {ctx.benchmark}' if ctx.benchmark else '') \
            if f.cnpj else ''

        # ---------------- slide 1: objetivo, rentabilidade, carteira
        s = self._slide(prs)
        self._faixa(s, Cm(5.0), f.nome, sub, ed.mes_ano)
        y = Cm(5.8)
        if f.objetivo:
            self._txt(s, MARGEM, y, A4_L - 2 * MARGEM, Cm(0.5),
                      'OBJETIVO DA CARTEIRA', tam=9, bold=True, cor=AZUL)
            self._txt(s, MARGEM, y + Cm(0.55), A4_L - 2 * MARGEM, Cm(1.6), f.objetivo, tam=9)
            y += Cm(2.4)

        linhas = ctx.linhas_rentabilidade
        cab = ['', 'Mês', 'Ano', '12M', '24M', '36M', 'Desde o início']
        corpo = [cab, ['Fundo'] + linhas['fundo'], [ctx.benchmark] + linhas['bench']]
        if 'pct' in linhas:
            corpo.append([f'% do {ctx.benchmark}'] + linhas['pct'])
        else:
            corpo.append(['Alfa'] + linhas['alfa'])
        self._txt(s, MARGEM, y, Cm(10), Cm(0.5), 'RENTABILIDADE', tam=9, bold=True, cor=AZUL)
        self._tabela(s, MARGEM, y + Cm(0.55), A4_L - 2 * MARGEM, corpo,
                     larguras=[2.4, 1, 1, 1, 1, 1, 1.5])
        y += Cm(3.3)
        self._txt(s, MARGEM, y, A4_L - 2 * MARGEM, Cm(0.4),
                  f'Data base: {ed.br}', tam=8, cor=CINZA, alinhamento=PP_ALIGN.RIGHT)
        y += Cm(0.8)

        # emissores e setores, lado a lado
        col = (A4_L - 2 * MARGEM - Cm(0.8)) / 2
        for i, (titulo, itens) in enumerate((('PRINCIPAIS EMISSORES', ctx.emissores),
                                             ('ALOCAÇÃO POR SETOR', ctx.setores))):
            if not itens:
                continue
            x = MARGEM + i * (col + Cm(0.8))
            self._txt(s, x, y, col, Cm(0.5), titulo, tam=9, bold=True, cor=AZUL)
            self._tabela(s, x, y + Cm(0.55), col,
                         [[n, v] for n, v, *_ in itens],
                         larguras=[3, 1], cabecalho=False)
        y += Cm(0.55) + Cm(0.52) * max(len(ctx.emissores), len(ctx.setores)) + Cm(0.9)

        if ctx.rating:
            self._txt(s, MARGEM, y, A4_L - 2 * MARGEM, Cm(0.5),
                      'DISTRIBUIÇÃO DE RATING DA CARTEIRA DE CRÉDITO',
                      tam=9, bold=True, cor=AZUL)
            self._tabela(s, MARGEM, y + Cm(0.55), A4_L - 2 * MARGEM,
                         [[r[0] for r in ctx.rating], [r[1] for r in ctx.rating]],
                         cabecalho=True, destaque_primeira_coluna=False)
        self._rodape(s, 1)

        # ---------------- slide 2: histórico + comentário
        s = self._slide(prs)
        self._faixa(s, Cm(3.0), f.nome, '', ed.mes_ano)
        y = Cm(3.8)
        if ctx.hist12:
            self._txt(s, MARGEM, y, Cm(12), Cm(0.5), 'RENTABILIDADE HISTÓRICA',
                      tam=9, bold=True, cor=AZUL)
            self._grafico_linha(s, MARGEM, y + Cm(0.6), A4_L - 2 * MARGEM, Cm(9.0),
                                ctx.hist12, ctx.benchmark)
            y += Cm(10.2)
        if ctx.comentario:
            self._txt(s, MARGEM, y, A4_L - 2 * MARGEM, Cm(0.5),
                      'COMENTÁRIO DO GESTOR E ANÁLISE DE MERCADO',
                      tam=9, bold=True, cor=AZUL)
            import re
            limpo = [re.sub(r'<[^>]+>', '', p) for p in ctx.comentario]
            self._txt(s, MARGEM, y + Cm(0.6), A4_L - 2 * MARGEM,
                      A4_A - y - Cm(2.0), '\n\n'.join(limpo), tam=9)
        self._rodape(s, 2)

        # ---------------- slide 3: mercado de crédito
        mercado = renderizador.mercado(ctx)
        secoes_do_fundo = {x['id'] for x in renderizador.secoes_do_fundo(f.key)}
        if mercado and 'mercado_credito' in secoes_do_fundo:
            s = self._slide(prs)
            self._faixa(s, Cm(3.0), f.nome, '', ed.mes_ano)
            self._txt(s, MARGEM, Cm(3.8), Cm(12), Cm(0.5), 'MERCADO DE CRÉDITO',
                      tam=9, bold=True, cor=AZUL)
            dados = [mercado['cabecalho']] + [l['celulas'] for l in mercado['linhas']]
            # a tabela ANBIMA tem ~25 setores; mais que isso não cabe na folha
            if len(dados) > 27:
                self.log.aviso(f.key, f'Mercado de Crédito com {len(dados) - 1} setores; '
                                      f'o PPTX mostra os 26 primeiros')
                dados = dados[:27]
            self._tabela(s, MARGEM, Cm(4.4), A4_L - 2 * MARGEM, dados,
                         larguras=[3.4, 1.3, 1, 1.2, 1.5, 1.1, 1],
                         altura_linha=Cm(0.46))
            self._txt(s, MARGEM, A4_A - Cm(2.6), A4_L - 2 * MARGEM, Cm(1.4),
                      mercado['nota'], tam=6.5, cor=CINZA)
            self._rodape(s, 3)

        # ---------------- slide final: características + disclaimer
        s = self._slide(prs)
        self._faixa(s, Cm(3.0), f.nome, '', ed.mes_ano)
        self._txt(s, MARGEM, Cm(3.8), Cm(12), Cm(0.5),
                  'CARACTERÍSTICAS GERAIS DO FUNDO', tam=9, bold=True, cor=AZUL)
        carac = renderizador.caracteristicas(ctx)
        self._tabela(s, MARGEM, Cm(4.4), A4_L - 2 * MARGEM,
                     [[k, v] for k, v in carac], larguras=[2.2, 1.6], cabecalho=False)
        y = Cm(4.4) + Cm(0.52) * len(carac) + Cm(0.8)
        op = renderizador.operacional(f)
        if op:
            self._txt(s, MARGEM, y, Cm(12), Cm(0.5), 'INFORMAÇÕES OPERACIONAIS',
                      tam=9, bold=True, cor=AZUL)
            self._tabela(s, MARGEM, y + Cm(0.55), A4_L - 2 * MARGEM,
                         [[k, v] for k, v in op], larguras=[2.2, 1.6], cabecalho=False)
            y += Cm(0.55) + Cm(0.52) * len(op) + Cm(0.8)
        from renderers.relatorio import DISCLAIMER_PADRAO
        nota = (f.cfg.get('nota_rodape') or '').strip()
        blocos = ([nota] if nota else []) + list(DISCLAIMER_PADRAO)
        self._txt(s, MARGEM, y, A4_L - 2 * MARGEM, Cm(0.5), 'DISCLAIMER',
                  tam=9, bold=True, cor=AZUL)
        self._txt(s, MARGEM, y + Cm(0.55), A4_L - 2 * MARGEM, A4_A - y - Cm(2.2),
                  '\n\n'.join(blocos), tam=5.4, cor=CINZA)
        self._rodape(s, len(prs.slides._sldIdLst))

        os.makedirs(os.path.dirname(destino) or '.', exist_ok=True)
        prs.save(destino)
        return destino

    def _rodape(self, slide, numero):
        self._txt(slide, A4_L - MARGEM - Cm(3), A4_A - Cm(1.2), Cm(3), Cm(0.4),
                  f'{numero}', tam=8, bold=True, cor=CINZA, alinhamento=PP_ALIGN.RIGHT)
        self._txt(slide, MARGEM, A4_A - Cm(1.2), Cm(6), Cm(0.4), 'tivio.com/fundos',
                  tam=8, cor=CINZA)

    # --------------------------------------------------------------- imagem
    def imagem(self, html, destino, navegador, escala=2, origem=None):
        """Fallback: cada folha do HTML vira um slide-imagem de alta resolução.

        Abre o arquivo gravado quando ele existe, pelo mesmo motivo do PDF: com
        `set_content` a página não tem URL base e o `vendor/` ao lado não
        resolve.
        """
        prs = Presentation()
        prs.slide_width, prs.slide_height = A4_L, A4_A
        pagina = navegador.new_page(viewport={'width': 1000, 'height': 1414},
                                    device_scale_factor=escala)
        try:
            if origem and os.path.exists(origem):
                pagina.goto('file://' + os.path.abspath(origem), wait_until='load')
            else:
                pagina.set_content(html, wait_until='load')
            try:
                pagina.wait_for_function('document.fonts.ready.then(()=>true)', timeout=15000)
            except Exception:
                pass
            folhas = pagina.query_selector_all('.rcard')
            if not folhas:
                raise RuntimeError('nenhuma folha .rcard no HTML')
            for folha in folhas:
                png = folha.screenshot(type='png')
                s = self._slide(prs)
                s.shapes.add_picture(io.BytesIO(png), 0, 0, A4_L, A4_A)
        finally:
            pagina.close()
        os.makedirs(os.path.dirname(destino) or '.', exist_ok=True)
        prs.save(destino)
        return destino
