# -*- coding: utf-8 -*-
"""Regras dos decks que entraram em outubro/2026, ao lado de exporters/decks.py.

Mesma filosofia do decks.py: abrir o PPTX do time, reconhecer cada número pelo
nome da caixa ou pelo rótulo ao lado, trocar SÓ o número e manter o desenho.

  big numbers ........ AuM, anos, profissionais, emissores, turnover
                       (configs/big_numbers.yml) e "Fonte: Anbima - Ago/2026"
  AuM por vertical ... rosca dos decks de Investment Solutions + rótulos
  retorno 12M ........ "100% do CDI" ao lado de "Retorno 12 M"
  período ............ "Mai/2025 a Set/2026 (mensal)" fecha no mês da edição
  mês nos slides ..... o selo "Setembro de 2026" em todos os slides
                       (opção `mes_em_todos` no decks.yml)
  PL nomeado ......... caixas patrimonio_liquido / patrimonio_liquido_medio_12m
  taxa (previdência) . "Taxa de Adm & Gestão" e "Taxa Global" da
                       entrada/taxas_prev.xlsx (soma dos veículos FIE + FIFE)
  comentário ......... lorem ipsum no lugar do texto do gestor
                       (opção `comentario: lorem` no decks.yml)
"""
import os
import re
import unicodedata

import yaml

from calculators import formatos as fmt
from exporters.decks import (NUM, MESES_RE, _absoluta, _shapes, _texto,
                             _troca_grupo, _troca_trecho, _sem_vinculo)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESES_CURTOS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

LOREM = [
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer posuere erat a ante '
    'venenatis dapibus posuere velit aliquet. Maecenas faucibus mollis interdum, nulla vitae '
    'elit libero, a pharetra augue. Vivamus sagittis lacus vel augue laoreet rutrum faucibus '
    'dolor auctor.',
    'Cras mattis consectetur purus sit amet fermentum. Donec ullamcorper nulla non metus '
    'auctor fringilla. Aenean lacinia bibendum nulla sed consectetur. Curabitur blandit '
    'tempus porttitor, etiam porta sem malesuada magna mollis euismod.',
    'Nullam quis risus eget urna mollis ornare vel eu leo. Sed posuere consectetur est at '
    'lobortis. Morbi leo risus, porta ac consectetur ac, vestibulum at eros. Praesent '
    'commodo cursus magna, vel scelerisque nisl consectetur et.',
    'Fusce dapibus, tellus ac cursus commodo, tortor mauris condimentum nibh, ut fermentum '
    'massa justo sit amet risus. Duis mollis, est non commodo luctus, nisi erat porttitor '
    'ligula, eget lacinia odio sem nec elit.',
]


def _sem_acento(t):
    u = unicodedata.normalize('NFKD', str(t or ''))
    return ''.join(c for c in u if not unicodedata.combining(c))


def _norm(t):
    """'Proﬁssionais\\nde Investimento' -> 'profissionais de investimento'."""
    t = _sem_acento(str(t).replace('ﬁ', 'fi').replace('\x0b', ' '))
    return re.sub(r'\s+', ' ', t).strip().lower()


def _nome_caixa(sh):
    return re.sub(r'\s+', '_', _norm(sh.name))


def carregar_big_numbers():
    caminho = os.path.join(RAIZ, 'configs', 'big_numbers.yml')
    if not os.path.exists(caminho):
        return {}
    with open(caminho, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


# rótulo da caixa vizinha -> chave do big_numbers.yml
ROTULOS = [
    (r'^ativos sob gestao$', 'ativos_sob_gestao'),
    (r'^aum captado nos ultimos 12 meses$', 'ativos_sob_gestao_credito_12'),
    (r'^profissionais dedicados ao credito$', 'profissionais_credito'),
    (r'^profissionais de investimento$', 'profissionais_investimento'),
    (r'^profissionais$', 'profissionais'),
    (r'^anos de historia$', 'anos_historia'),
    (r'^fundos de investimento desde a criacao$', 'fundos_criacao'),
    (r'^turnover$', 'turnover'),
]
# o nome da caixa no PPTX (sem acento) -> chave, quando difere
NOMES = {'ativos_sob_gestao': 'ativos_sob_gestao'}
VALOR = re.compile(r'^\s*\+?\s*(R\$\s*)?' + NUM + r'\s*(%|bi|mi)?\s*$', re.I)


def _formata(v, modelo):
    """Número no formato do modelo: as casas decimais do texto atual."""
    if isinstance(v, str):
        return v
    m = re.search(r'\d+(?:,(\d+))?', modelo)
    casas = len(m.group(1)) if m and m.group(1) else 0
    return fmt.num(float(v), casas)


def _troca_numero(sh, valor):
    """Troca o primeiro número da caixa, mantendo "+R$" e "bi" do modelo."""
    for p in sh.text_frame.paragraphs:
        t = ''.join(r.text for r in p.runs)
        m = re.search(r'\d+(?:[.,]\d+)*', t)
        if m:
            return _troca_trecho(p, m.start(), m.end(), _formata(valor, m.group(0)))
    return False


class Extras:
    def __init__(self, edicao, log, taxas_prev=None, big=None):
        self.ed = edicao
        self.log = log
        self.prev = taxas_prev
        self.big = big if big is not None else carregar_big_numbers()
        self.num = self.big.get('numeros') or {}
        self.trocas = 0

    # ------------------------------------------------------------ big numbers
    def big_numbers(self, slide):
        texto_slide = _norm(' '.join(_texto(sh) for sh, _ in _shapes(slide.shapes)))
        de_credito = 'profissionais dedicados' in texto_slide or 'emissores em carteira' in texto_slide
        formas = [(sh, _absoluta(sh._element)) for sh, _ in _shapes(slide.shapes)
                  if getattr(sh, 'has_text_frame', False) and sh.has_text_frame]
        feitas = set()
        # 1) pelo nome da caixa
        for sh, _ in formas:
            k = _nome_caixa(sh)
            k = NOMES.get(k, k)
            if k == 'ativos_sob_gestao' and de_credito:
                k = 'ativos_sob_gestao_credito'
            if k in self.num and VALOR.match(_texto(sh)):
                if _troca_numero(sh, self.num[k]):
                    feitas.add(id(sh))
                    self.trocas += 1
        # 2) pelo rótulo vizinho (caixa sem nome)
        for rot, br in formas:
            nr = _norm(_texto(rot))
            chave = next((k for rx, k in ROTULOS if re.match(rx, nr)), None)
            if not chave or not br:
                continue
            if chave == 'ativos_sob_gestao' and de_credito:
                chave = 'ativos_sob_gestao_credito'
            if chave not in self.num:
                continue
            cand = []
            for val, bv in formas:
                if val is rot or not bv or id(val) in feitas or not VALOR.match(_texto(val)):
                    continue
                cx, cy = (bv[0] + bv[2]) / 2, (bv[1] + bv[3]) / 2
                rx, ry = (br[0] + br[2]) / 2, (br[1] + br[3]) / 2
                d = abs(cx - rx) + abs(cy - ry)
                # o valor fica dentro do cartão do rótulo ou logo acima/abaixo dele
                if d < 12700 * 180:
                    cand.append((d, val))
            if cand:
                val = min(cand, key=lambda a: a[0])[1]
                if _troca_numero(val, self.num[chave]):
                    feitas.add(id(val))
                    self.trocas += 1
        # 3) emissores num texto só: "+30 Bancários / +100 Corporativos"
        for sh, _ in formas:
            if id(sh) in feitas:
                continue
            for p in sh.text_frame.paragraphs:
                for chave, rx in (('emissores_bancarios', r'\+?\s*(\d+)\s*Banc[áa]rios'),
                                  ('emissores_corporativos', r'\+?\s*(\d+)\s*Corporativos')):
                    if chave in self.num and _troca_grupo(p, rx, _formata(self.num[chave], '0')):
                        self.trocas += 1
        self._fonte(slide)

    def _fonte(self, slide):
        f = self.big.get('fonte') or {}
        if not f.get('mes'):
            return
        ano, mes = str(f['mes']).split('-')[:2]
        novo = f'Fonte: {f.get("texto", "Anbima")} - {MESES_CURTOS[int(mes) - 1]}/{ano}'
        for sh, _ in _shapes(slide.shapes):
            if getattr(sh, 'has_text_frame', False) and sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    t = ''.join(r.text for r in p.runs)
                    # aceita os erros que já saíram ("Agp/2026", "-Ago", "–")
                    m = re.search(r'Fonte:\s*Anbima\s*[-–]\s*\w{3}/\d{4}', t, re.I)
                    if m and _troca_trecho(p, m.start(), m.end(), novo):
                        self.trocas += 1

    # -------------------------------------------------------- AuM por vertical
    def aum_vertical(self, slide):
        aum = self.big.get('aum_vertical') or {}
        if not aum:
            return
        total = sum(float(v) for v in aum.values())
        achou = False
        for sh, _ in _shapes(slide.shapes):
            if not (getattr(sh, 'has_chart', False) and sh.has_chart):
                continue
            ch = sh.chart
            try:
                pl = ch.plots[0]
                cats = [str(c) for c in pl.categories]
            except Exception:
                continue
            if 'DOUGHNUT' not in str(ch.chart_type) and 'PIE' not in str(ch.chart_type):
                continue
            if not set(cats) & set(aum):
                continue
            achou = True
            serie = pl.series[0]
            # valores no cache do gráfico (mantém os rótulos personalizados)
            C = '{http://schemas.openxmlformats.org/drawingml/2006/chart}'
            for pt in serie._element.findall(f'{C}val/{C}numRef/{C}numCache/{C}pt'):
                i = int(pt.get('idx'))
                if i < len(cats) and cats[i] in aum:
                    pt.find(f'{C}v').text = repr(float(aum[cats[i]]))
            _sem_vinculo(ch)
            # rótulos "R$ 9,2 bi Crédito Privado"
            for i, ptl in enumerate(serie.points):
                if i >= len(cats) or cats[i] not in aum:
                    continue
                try:
                    tf = ptl.data_label.text_frame
                except Exception:
                    continue
                for p in tf.paragraphs:
                    if _troca_grupo(p, r'R\$\s*(' + NUM + r')\s*bi',
                                    fmt.num(float(aum[cats[i]]) / 1e9, 1)):
                        break
            self.trocas += 1
        if not achou:
            return
        # o total no centro ("R$31 bi"), que é uma caixa solta sobre a rosca
        for sh, _ in _shapes(slide.shapes):
            t = _texto(sh)
            if re.fullmatch(r'\s*R\$\s*\d+\s*bi\s*', t):
                _troca_grupo(sh.text_frame.paragraphs[0], r'R\$\s*(\d+)', fmt.num(total / 1e9, 0))

    # ------------------------------------- alocação HG / HY / Caixa lado a lado
    def alocacao_lado(self, slide, ctx):
        """"High Grade  66,5%" com rótulo e valor em caixas vizinhas (HGD30) e
        as tabelas "Carteira HGD / 66,5%". Só nos slides com `alocacao_hghy`:
        no HYD60 a "Previsão de alocação" é meta e fica como está."""
        if ctx is None:
            return
        real = {n: v for n, _, v in ctx.alocacao_hghy}
        hg, hy, cx = real.get('Crédito High Grade'), real.get('Crédito High Yield'), real.get('Caixa')
        mapa = {'high grade': hg, 'credito high grade': hg, 'carteira hgd': hg, 'carteira hg': hg,
                'credito estruturado': hy, 'high yield': hy, 'credito high yield': hy,
                'carteira hyd': hy, 'carteira hy': hy, 'caixa': cx}
        formas = [(sh, _absoluta(sh._element)) for sh, _ in _shapes(slide.shapes)
                  if getattr(sh, 'has_text_frame', False) and sh.has_text_frame]
        for rot, br in formas:
            v = mapa.get(_norm(_texto(rot)))
            if v is None or not br:
                continue
            cy = (br[1] + br[3]) / 2
            cand = [(bv[0] - br[0], val) for val, bv in formas
                    if bv and val is not rot and re.fullmatch(r'\s*\d+,\d\s*%\s*', _texto(val))
                    and abs((bv[1] + bv[3]) / 2 - cy) < 12700 * 20 and bv[0] >= br[0]]
            if cand:
                val = min(cand, key=lambda a: a[0])[1]
                if _troca_grupo(val.text_frame.paragraphs[0], r'(\d+,\d)', fmt.num(v, 1)):
                    self.trocas += 1
        # tabelas de uma coluna: "Carteira HGD" e o valor na linha de baixo
        for sh, _ in _shapes(slide.shapes):
            if not (getattr(sh, 'has_table', False) and sh.has_table):
                continue
            linhas = list(sh.table.rows)
            for i, r in enumerate(linhas[:-1]):
                v = mapa.get(_norm(r.cells[0].text))
                if v is None:
                    continue
                cel = linhas[i + 1].cells[0]
                for p in cel.text_frame.paragraphs:
                    if _troca_grupo(p, r'(\d+,\d)\s*%', fmt.num(v, 1)):
                        self.trocas += 1
                        break

    # ------------------------------------------------ "Principais emissores"
    def emissores(self, slide, ctx):
        """O gráfico de barras logo abaixo do título "Principais emissores"
        recebe o top 5 da carteira, na mesma ordem (maior em cima) do modelo."""
        if ctx is None:
            return
        try:
            itens = [(n, v / 100) for n, _, v in ctx.emissores_relatorio]
        except Exception:
            return
        if not itens:
            return
        formas = [(sh, _absoluta(sh._element)) for sh, _ in _shapes(slide.shapes)]
        titulos = [b for sh, b in formas if b and _norm(_texto(sh)) == 'principais emissores']
        if not titulos:
            return
        tb = titulos[0]
        # o gráfico logo abaixo do título, na mesma coluna. A moldura do gráfico
        # costuma começar um pouco ACIMA do título; o que conta é o centro.
        cy_t = (tb[1] + tb[3]) / 2
        graficos = [(sh, b) for sh, b in formas if b and getattr(sh, 'has_chart', False) and sh.has_chart
                    and (b[1] + b[3]) / 2 > cy_t and b[0] < tb[2] and b[2] > tb[0]]
        if not graficos:
            return
        sh = min(graficos, key=lambda a: abs(a[1][1] - tb[3]))[0]
        from pptx.chart.data import CategoryChartData
        pl = sh.chart.plots[0]
        serie = pl.series[0]
        vals = list(serie.values)
        # barras horizontais: a 1ª categoria fica embaixo; o modelo diz a ordem
        if vals and vals[0] is not None and vals[-1] is not None and vals[0] < vals[-1]:
            itens = list(reversed(itens))
        fc = serie._element.xpath('./c:val//c:formatCode/text()')
        cd = CategoryChartData(number_format=fc[0] if fc else '0.00%')
        cd.categories = [n for n, _ in itens]
        cd.add_series(serie.name or '', [v for _, v in itens])
        _sem_vinculo(sh.chart)
        sh.chart.replace_data(cd)
        self.trocas += 1

    # ------------------------------------------------- fundo: números nomeados
    def nomeados(self, slide, ctx):
        if ctx is None:
            return
        valores = {'patrimonio_liquido': ctx.pl, 'patrimonio_liquido_medio_12m': ctx.pl_medio}
        for sh, _ in _shapes(slide.shapes):
            k = _nome_caixa(sh)
            if k in valores and valores[k] and re.search(r'R\$', _texto(sh)):
                p = sh.text_frame.paragraphs[0]
                t = ''.join(r.text for r in p.runs)
                m = re.search(r'R\$\s*[\d.,]+', t)
                if m and _troca_trecho(p, m.start(), m.end(), fmt.brl(valores[k])):
                    self.trocas += 1

    # -------------------------------------------- "100% do CDI" + "Retorno 12 M"
    def retorno_12m(self, slide, ctx):
        if ctx is None:
            return
        formas = [(sh, _absoluta(sh._element)) for sh, _ in _shapes(slide.shapes)
                  if getattr(sh, 'has_text_frame', False) and sh.has_text_frame]
        rotulos = [b for sh, b in formas if b and re.fullmatch(r'retorno 12 ?m', _norm(_texto(sh)))]
        if not rotulos:
            return
        pct = ctx.valor('12m', 'pct')
        if pct is None:
            pct, inicio = ctx.valor('inicio', 'pct'), True
        else:
            inicio = False
        if pct is None:
            return
        for sh, b in formas:
            if not b or not re.fullmatch(r'\s*\d+\s*%\s*do CDI\s*', _texto(sh)):
                continue
            perto = any(abs(b[1] - r[1]) < 12700 * 80 and abs(b[0] - r[0]) < 12700 * 200 for r in rotulos)
            if perto and _troca_grupo(sh.text_frame.paragraphs[0], r'(\d+)\s*%', fmt.num(pct * 100, 0)):
                self.trocas += 1
        if inicio:                      # fundo com menos de 12 meses
            for sh, b in formas:
                if b and re.fullmatch(r'retorno 12 ?m', _norm(_texto(sh))):
                    p = sh.text_frame.paragraphs[0]
                    t = ''.join(r.text for r in p.runs)
                    _troca_trecho(p, 0, len(t), 'Retorno desde o início')

    # --------------------------------------------- "Mai/2025 a Set/2026 (mensal)"
    def periodo(self, slide, ctx=None):
        """O fim é o mês da edição; o início, o mês da primeira cota do fundo
        (a mesma série do gráfico). Sem série, o início do modelo fica."""
        fim = f'{MESES_CURTOS[self.ed.db.month - 1]}/{self.ed.db.year}'
        ini = None
        if ctx is not None:
            try:
                serie = ctx.serie_diaria()
            except Exception:
                serie = None
            if serie:
                d0 = serie[0][0]
                ini = f'{MESES_CURTOS[d0.month - 1]}/{d0.year}'
        rx = r'\b([A-Z][a-z]{2}/\d{4})\s+a\s+([A-Z][a-z]{2}/\d{4})'
        for sh, _ in _shapes(slide.shapes):
            if getattr(sh, 'has_text_frame', False) and sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    # só o rótulo do gráfico: "… (mensal)" / "… (diário)"
                    if not re.search(r'\((mensal|di[áa]rio)\)', ''.join(r.text for r in p.runs)):
                        continue
                    if _troca_grupo(p, rx, fim, grupo=2):
                        self.trocas += 1
                        if ini:
                            _troca_grupo(p, rx, ini, grupo=1)

    # --------------------------------------------- "Setembro de 2026" em todo slide
    def mes(self, slide):
        novo = f'{fmt.MESES[self.ed.db.month - 1]} de {self.ed.db.year}'
        for sh, _ in _shapes(slide.shapes):
            if getattr(sh, 'has_text_frame', False) and sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    t = ''.join(r.text for r in p.runs)
                    m = re.fullmatch(rf'\s*({MESES_RE})\s+de\s+\d{{4}}\s*', t, re.I)
                    if m and _troca_trecho(p, m.start(), m.end(), novo):
                        self.trocas += 1

    # ---------------------------------------------------------- taxa (previdência)
    def taxa_prev(self, slide, ctx):
        if ctx is None or self.prev is None:
            return
        tx = self.prev.taxa_final(ctx.f.cfg.get('bloco_taxas_prev'))
        if tx is None:
            return
        formas = [(sh, _absoluta(sh._element)) for sh, _ in _shapes(slide.shapes)
                  if getattr(sh, 'has_text_frame', False) and sh.has_text_frame]
        for rot, br in formas:
            nr = _norm(_texto(rot))
            if not br or not (nr.startswith('taxa de adm') or nr == 'taxa global'):
                continue
            cand = []
            for val, bv in formas:
                if val is rot or not bv or not re.fullmatch(r'\s*' + NUM + r'\s*%\s*(a\.\s*a\.?)?\s*', _texto(val)):
                    continue
                d = abs((bv[0] + bv[2]) / 2 - (br[0] + br[2]) / 2) + abs((bv[1] + bv[3]) / 2 - (br[1] + br[3]) / 2)
                if d < 12700 * 200:
                    cand.append((d, val))
            if not cand:
                continue
            val = min(cand, key=lambda a: a[0])[1]
            p = val.text_frame.paragraphs[0]
            t = ''.join(r.text for r in p.runs)
            m = re.search(NUM, t)
            casas = len(m.group(0).split(',')[1]) if ',' in m.group(0) else 0
            # as casas do modelo, a não ser que elas escondam parte da taxa (1,127%)
            if round(tx * 100, casas) != round(tx * 100, 3):
                casas = 2 if round(tx * 100, 2) == round(tx * 100, 3) else 3
            if _troca_trecho(p, m.start(), m.end(), fmt.num(tx * 100, casas)):
                self.trocas += 1

    # ---------------------------------------------------------------- comentário
    def lorem(self, slide):
        """O texto do gestor (caixa longa num slide de "Comentário do Gestor")
        vira lorem ipsum, com a formatação do primeiro parágrafo do modelo."""
        textos = _norm(' '.join(_texto(sh) for sh, _ in _shapes(slide.shapes)))
        if 'comentario do gestor' not in textos:
            return
        import copy
        for sh, _ in _shapes(slide.shapes):
            if not (getattr(sh, 'has_text_frame', False) and sh.has_text_frame):
                continue
            if len(_texto(sh)) < 300:
                continue
            tf = sh.text_frame
            pars = [p for p in tf.paragraphs if p.runs and ''.join(r.text for r in p.runs).strip()]
            if not pars:
                continue
            modelo = copy.deepcopy(pars[0]._p)
            corpo = tf._txBody
            for p in list(corpo.findall('{http://schemas.openxmlformats.org/drawingml/2006/main}p')):
                corpo.remove(p)
            A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
            n = max(2, min(len(LOREM), len(pars)))
            for i in range(n):
                p = copy.deepcopy(modelo)
                runs = p.findall(f'{A}r')
                for r in runs[1:]:
                    p.remove(r)
                for x in p.findall(f'{A}br'):
                    p.remove(x)
                runs[0].find(f'{A}t').text = LOREM[i]
                corpo.append(p)
                if i < n - 1:                      # linha em branco entre parágrafos
                    vazio = copy.deepcopy(modelo)
                    for x in vazio.findall(f'{A}r') + vazio.findall(f'{A}br'):
                        vazio.remove(x)
                    corpo.append(vazio)
            self.trocas += 1
