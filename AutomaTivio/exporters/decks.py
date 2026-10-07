# -*- coding: utf-8 -*-
"""Decks comerciais (PPTX + PDF): os PPTX do time, com os números do mês.

Os modelos ficam em templates/decks/ e a lista de decks em configs/decks.yml.
Nada de desenho novo: a automação abre o PPTX, reconhece cada número pelo texto
ao lado e troca só o número, mantendo fonte, cor e tamanho do modelo.

O que é reconhecido (por slide; o fundo do slide sai do "Por que o …?"):
  capa ............... "Junho de 2026" / "Agosto-26"  -> mês da edição
  qualquer slide ..... "Data base: dd/mm/aaaa"         -> data base
  slide do fundo ..... "Data de início: …"             -> data oficial
                       "PL: R$ …", "PL Médio: R$ …"    -> PL e PL médio (12M)
                       "12M / ANO / MÊS  x% do CDI"    -> % do CDI (Infra Plus:
                                                          retorno + "*Alfa")
                       "Carrego bruto …", "Duration …" -> carrego e duration
                       "95%" + numero-top/nome-top     -> alocação de crédito
                       "Desde o início / 12M / Mês" ao lado de "CDI + x% a.a."
                       blocos "Nome 49,1%"             -> alocação real (ALT),
                                                          redimensionados
                       gráfico de linha Fundo x CDI    -> série diária
                       "29,56%" / "22,58%"             -> fim de cada linha
Removíveis por deck: selo da XP, quadro do ROA, slide do ALT Light.
"""
import copy
import os
import re

import yaml
from lxml import etree

from calculators import formatos as fmt

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
MESES_RE = '|'.join(fmt.MESES)
NUM = r'[-−]?\d+(?:[.,]\d+)*'

# "Por que o …?" -> chave do fundo (texto sem espaços, maiúsculo)
FUNDOS_TITULO = [
    ('altlight', r'ALT\+?LIGHT'), ('alt180', r'ALT180'), ('alt90', r'ALT90'),
    ('infrapluscdi', r'INFRAPLUSCDI'), ('infraplus', r'INFRAPLUS'),
    ('inst15', r'INSTITUCIONAL15'), ('inst30', r'INSTITUCIONAL30'),
    ('institucional', r'INSTITUCIONAL'), ('banks', r'BANKS'),
]
PERIODO = {'INÍCIO': 'inicio', 'INICIO': 'inicio', '12M': '12m', 'ANO': 'ano', 'MÊS': 'mes', 'MES': 'mes', 'DESDE O INÍCIO': 'inicio',
           'DESDE O INICIO': 'inicio'}


def carregar_config():
    with open(os.path.join(RAIZ, 'configs', 'decks.yml'), encoding='utf-8') as f:
        return (yaml.safe_load(f) or {}).get('decks') or []


# ------------------------------------------------------------- utilidades
def _shapes(col, pai=None):
    """(shape, coleção-mãe) em todos os níveis de grupo."""
    for sh in col:
        yield sh, col
        if sh.shape_type == 6:
            yield from _shapes(sh.shapes, sh.shapes)


def _texto(sh):
    return sh.text_frame.text if getattr(sh, 'has_text_frame', False) and sh.has_text_frame else ''


def _troca_trecho(par, ini, fim, novo):
    """Troca os caracteres [ini, fim) do parágrafo por `novo`, run a run: o
    texto novo entra no run onde o trecho começa (mantém a formatação dele)."""
    pos, feito = 0, False
    for r in par.runs:
        t = r.text
        a, b = pos, pos + len(t)
        pos = b
        if b <= ini or a >= fim:
            continue
        i0, i1 = max(ini, a) - a, min(fim, b) - a
        if not feito:
            r.text = t[:i0] + novo + t[i1:]
            feito = True
        else:
            r.text = t[:i0] + t[i1:]
    return feito


def _troca_grupo(par, regex, valor, grupo=1, flags=re.I):
    t = ''.join(r.text for r in par.runs)
    m = re.search(regex, t, flags)
    if not m or valor is None:
        return False
    return _troca_trecho(par, m.start(grupo), m.end(grupo), valor)


def _troca_texto(slide, velho, novo):
    """Troca de texto fixa pedida no decks.yml (`textos`), parágrafo a
    parágrafo, mantendo a formatação do run onde o trecho começa."""
    for sh, _ in _shapes(slide.shapes):
        if getattr(sh, 'has_text_frame', False) and sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                t = ''.join(r.text for r in p.runs)
                i = t.find(velho)
                if i >= 0:
                    _troca_trecho(p, i, i + len(velho), novo)


def _troca_frase(par, regex, fundo, pct):
    """Troca os dois números de "X% no mês (Y% do CDI)" mantendo as casas do
    texto; o segundo antes do primeiro, para os índices não andarem."""
    if fundo is None or pct is None:
        return False
    t = ''.join(r.text for r in par.runs)
    m = re.search(regex, t, re.I)
    if not m:
        return False
    for g, v in ((2, pct), (1, fundo)):
        casas = len(m.group(g).split(',')[1]) if ',' in m.group(g) else 0
        _troca_trecho(par, m.start(g), m.end(g), fmt.num(v * 100, casas))
    return True


def _num(v, casas=2):
    return fmt.num(v, casas) if v is not None else None


def _curto(v, com_rs):
    if not v:
        return None
    if v >= 1e9:
        s = f'{fmt.num(v / 1e9, 1)} bilhões'
    else:
        s = f'{fmt.num(v / 1e6, 0)} milhões'
    return s


def _remove_elemento(el):
    pai = el.getparent()
    if pai is not None:
        pai.remove(el)


def _topo(el, sptree):
    """O ancestral de `el` que é filho direto da árvore do slide."""
    while el.getparent() is not None and el.getparent() is not sptree:
        el = el.getparent()
    return el


def _caixa(el):
    xf = el.find(f'.//{A}xfrm')
    if xf is None:
        return None
    off, ext = xf.find(f'{A}off'), xf.find(f'{A}ext')
    if off is None or ext is None:
        return None
    x, y = int(off.get('x')), int(off.get('y'))
    return x, y, x + int(ext.get('cx')), y + int(ext.get('cy'))


def _absoluta(el):
    """(x0, y0, x1, y1) do shape em EMU do slide, atravessando os grupos."""
    cx = _caixa_propria(el)
    if cx is None:
        return None
    x0, y0, x1, y1 = cx
    pai = el.getparent()
    while pai is not None and pai.tag == f'{P}grpSp':
        xf = pai.find(f'{P}grpSpPr/{A}xfrm')
        if xf is None:
            break
        off, ext = xf.find(f'{A}off'), xf.find(f'{A}ext')
        co, ce = xf.find(f'{A}chOff'), xf.find(f'{A}chExt')
        if None in (off, ext, co, ce):
            break
        # grupo de linhas tem altura 0: escala 1 nesse eixo, só translada
        sx = int(ext.get('cx')) / int(ce.get('cx')) if int(ce.get('cx')) else 1.0
        sy = int(ext.get('cy')) / int(ce.get('cy')) if int(ce.get('cy')) else 1.0
        ox, oy, cox, coy = int(off.get('x')), int(off.get('y')), int(co.get('x')), int(co.get('y'))
        x0, x1 = ox + (x0 - cox) * sx, ox + (x1 - cox) * sx
        y0, y1 = oy + (y0 - coy) * sy, oy + (y1 - coy) * sy
        pai = pai.getparent()
    return x0, y0, x1, y1


def _caixa_propria(el):
    for caminho in (f'{P}spPr/{A}xfrm', f'{P}grpSpPr/{A}xfrm', f'{P}xfrm'):
        xf = el.find(caminho)
        if xf is not None:
            off, ext = xf.find(f'{A}off'), xf.find(f'{A}ext')
            if off is not None and ext is not None:
                x, y = int(off.get('x')), int(off.get('y'))
                return x, y, x + int(ext.get('cx')), y + int(ext.get('cy'))
    return None


def _periodo(t):
    import unicodedata
    u = unicodedata.normalize('NFKD', re.sub(r'\s+', ' ', t.replace('\x0b', ' ')).strip().upper())
    u = ''.join(c for c in u if not unicodedata.combining(c))
    return {'12M': '12m', 'ANO': 'ano', 'MES': 'mes', 'DESDE O INICIO': 'inicio',
            'INICIO': 'inicio', '24M': '24m', '36M': '36m'}.get(u)


# ------------------------------------------------------------- por slide
class Preenchedor:
    def __init__(self, edicao, contextos, cadastro, log):
        self.ed = edicao
        self.ctx = {c.key: c for c in contextos}
        self.cad = cadastro
        self.log = log
        self.trocas = 0

    def fundo_do_slide(self, slide):
        for sh, _ in _shapes(slide.shapes):
            t = _texto(sh)
            if re.search(r'Por que o', t, re.I):
                chave = re.sub(r'[^A-Z0-9+]', '', t.upper().replace('Í', 'I'))
                for k, padrao in FUNDOS_TITULO:
                    if re.search(padrao, chave):
                        return k
        return None

    # -- números do fundo
    def _inicio(self, ctx):
        """Só a data oficial de configs/fundos.yml (data_inicio); sem ela, fica
        a do modelo, que é fixa: a primeira cota da planilha nem sempre é a
        data de início que o time divulga."""
        of = ctx.f.cfg.get('data_inicio')
        return str(of) if of else None

    def _setores_top3(self, ctx):
        st = [x for x in ctx.setores_relatorio if x[0] != 'Caixa']
        return st[:3]

    # -- regras de parágrafo
    def paragrafo(self, par, ctx, capa):
        t = ''.join(r.text for r in par.runs)
        if not t.strip():
            return
        ok = False
        if capa:
            m = re.fullmatch(rf'\s*({MESES_RE})\s+de\s+\d{{4}}\s*', t, re.I)
            if m:
                ok |= _troca_trecho(par, m.start(), m.end(),
                                    f'{fmt.MESES[self.ed.db.month - 1]} de {self.ed.db.year}')
            m = re.fullmatch(rf'\s*({MESES_RE})-\d{{2}}\s*', t, re.I)
            if m:
                ok |= _troca_trecho(par, m.start(), m.end(),
                                    f'{fmt.MESES[self.ed.db.month - 1]}-{self.ed.db:%y}')
        ok |= _troca_grupo(par, r'Data ?base:\s*(\d{2}/\d{2}/\d{4})', self.ed.br)
        if ctx is not None:
            ok |= _troca_grupo(par, r'Data de in[íi]cio:\s*(\d{2}/\d{2}/\d{4})', self._inicio(ctx))
            # PL por extenso (ALT) ou curto (Crédito)
            m = re.search(r'\bPL:\s*R\$\s*([\d.,]+)(\s*(bilh|milh)\w*)?', t)
            if m and ctx.pl:
                if m.group(2):
                    ok |= _troca_trecho(par, m.start(1), m.end(2), _curto(ctx.pl, True))
                else:
                    cent = ',' in m.group(1)
                    v = fmt.brl(ctx.pl)[3:] if cent else fmt.brl(ctx.pl)[3:].split(',')[0]
                    ok |= _troca_trecho(par, m.start(1), m.end(1), v)
            m = re.search(r'PL\s+m[ée]dio(?:\s*\(12 meses\))?:\s*(?:R\$\s*)?([\d.,]+)(\s*(bilh|milh)\w*)?', t, re.I)
            if m and ctx.pl_medio:
                if m.group(2):
                    ok |= _troca_trecho(par, m.start(1), m.end(2), _curto(ctx.pl_medio, False))
                else:
                    cent = ',' in m.group(1)
                    v = fmt.brl(ctx.pl_medio)[3:] if cent else fmt.brl(ctx.pl_medio)[3:].split(',')[0]
                    ok |= _troca_trecho(par, m.start(1), m.end(1), v)
            # nota do benchmark segue o fundo ("*Benchmark: IMA-B 5." num fundo CDI)
            mb = re.search(r'Benchmark:\s*([^.]+)\.', t)
            if mb and ctx.benchmark and _sem_acento(mb.group(1)) != _sem_acento(ctx.benchmark):
                ok |= _troca_trecho(par, mb.start(1), mb.end(1), str(ctx.benchmark))
            # frase do comentário: "1,08% no mês (100% do CDI)", "14,66% em 12 meses (101% do CDI)"
            for per, txt in (('mes', r'no m[êe]s'), ('12m', r'em 12 meses'), ('ano', r'no ano'),
                             ('inicio', r'desde o in[íi]cio')):
                ok |= _troca_frase(par, r'(' + NUM + r')\s*%\s*' + txt + r'\s*\((' + NUM + r')\s*%\s*do CDI\)',
                                   ctx.valor(per, 'fundo'), ctx.valor(per, 'pct'))
            t = ''.join(r.text for r in par.runs)
            # quadros 12M / ANO / MÊS (Crédito Privado)
            m = re.match(r'\s*(12M|ANO|M[ÊE]S|IN[ÍI]CIO|Desde o in[íi]cio)\s*(' + NUM + r')\s*%', t, re.I)
            if m:
                per = PERIODO.get(m.group(1).upper())
                # fundo com menos de 12 meses: o "12M" do modelo vira desde o início
                rotulo_inicio = per == '12m' and ctx.valor('12m', 'fundo') is None
                if rotulo_inicio:
                    per = 'inicio'
                # o próprio quadro diz o formato: "% do CDI" ou retorno (+ Alfa)
                if ctx.f.retorno_absoluto or 'do CDI' not in t:
                    fv = ctx.valor(per, 'fundo')
                    v = _num(fv * 100) if fv is not None else None
                else:
                    pv = ctx.valor(per, 'pct')
                    v = fmt.num(pv * 100, 0) if pv is not None else None
                ok |= _troca_trecho(par, m.start(2), m.end(2), v) if v else False
                if rotulo_inicio and v:
                    _troca_trecho(par, m.start(1), m.end(1), 'INÍCIO')
                t = ''.join(r.text for r in par.runs)
                if 'Alfa' in t:
                    a = ctx.valor(per, 'alfa')
                    if a is not None:
                        ok |= _troca_grupo(par, r'Alfa:\s*(' + NUM + r')', fmt.num(a * 100, 2).replace('−', '-'))
        self.trocas += int(bool(ok))

    # -- regras de forma (texto + vizinhos)
    def forma(self, sh, ctx):
        t = _texto(sh)
        if not t or ctx is None:
            return
        pars = sh.text_frame.paragraphs
        if re.search(r'Carrego', t, re.I) and ctx.carrego is not None:
            for p in pars:
                if _troca_grupo(p, r'(\d+,\d+)\s*%', fmt.num(ctx.carrego * 100, 2)):
                    self.trocas += 1
                    break
            # o indexador do carrego segue o benchmark (modelo copiado de outro fundo)
            idx = 'CDI+' if str(ctx.benchmark).upper().startswith('CDI') else 'IPCA+'
            for p in pars:
                if _troca_grupo(p, r'\b(CDI\s*\+|IPCA\s*\+)', idx):
                    break
        if re.search(r'Duration', t, re.I) and ctx.duration is not None:
            for p in pars:
                if _troca_grupo(p, r'(\d+,\d+)', fmt.num(ctx.duration, 2)):
                    self.trocas += 1
                    break
            unid = 'ano' if ctx.duration < 2 else 'anos'
            for p in pars:
                if _troca_grupo(p, r'(?<![a-zà-ú])(anos?)\b', unid):
                    break
        nome = sh.name.lower()
        top = self._setores_top3(ctx)
        m = re.fullmatch(r'(numero|nome)-top([123])', nome)
        if m and len(top) >= int(m.group(2)) and not t.strip().lower().startswith('top'):
            n, _, v = top[int(m.group(2)) - 1]
            p = pars[0]
            tt = ''.join(r.text for r in p.runs)
            if m.group(1) == 'numero':
                casas = len(re.search(r'(?:,(\d+))?\s*%', tt).group(1) or '') if '%' in tt else 1
                _troca_trecho(p, 0, len(tt), f'{fmt.num(v, casas)}%')
            else:
                # o modelo escreve o setor em minúsculas ("energia elétrica"), siglas em caixa alta
                novo = n if n.isupper() else n.lower()
                _troca_trecho(p, 0, len(tt), novo)
                for extra in pars[1:]:
                    xt = ''.join(r.text for r in extra.runs)
                    _troca_trecho(extra, 0, len(xt), '')
            self.trocas += 1
        elif re.fullmatch(r'\s*\d{1,3}\s*%\s*', t) and ctx.cart:
            p = pars[0]
            if _troca_grupo(p, r'(\d{1,3})\s*%', fmt.num(ctx.cart['credito'] * 100, 0)):
                self.trocas += 1

    # -- "Desde o início / 12M / Mês" + "CDI + x% a.a." (ALT)
    def pares_cdi_mais(self, slide, ctx):
        """Cada "CDI + x% a.a." recebe o período do rótulo logo acima dele
        (Desde o início / 12M / Mês), em coordenadas do slide: rótulo e valor
        às vezes estão em grupos diferentes."""
        if ctx is None:
            return
        formas = [(sh, _absoluta(sh._element)) for sh, _ in _shapes(slide.shapes)]
        rotulos = [(b, _periodo(_texto(sh))) for sh, b in formas if b and _periodo(_texto(sh))]
        for v, bv in formas:
            if not bv or not re.fullmatch(r'\s*CDI\s*\+\s*' + NUM + r'\s*%\s*a\.a\.?\s*', _texto(v)):
                continue
            vx = (bv[0] + bv[2]) / 2
            cand = []
            for br, per in rotulos:
                rx = (br[0] + br[2]) / 2
                if br[1] > bv[1] + 12700 * 4 or abs(rx - vx) > (bv[2] - bv[0]):
                    continue
                cand.append((abs(rx - vx) + abs(bv[1] - br[3]), per))
            if not cand:
                continue
            bm = ctx.valor(min(cand)[1], 'bench_mais')
            if bm is None:
                continue
            for p in v.text_frame.paragraphs:
                if _troca_grupo(p, r'CDI\s*\+\s*(' + NUM + r')', fmt.num(bm * 100, 2)):
                    self.trocas += 1
                    break

    # -- gráfico Fundo x CDI e etiquetas do fim das linhas
    def grafico(self, slide, ctx, largura_slide):
        if ctx is None:
            return
        serie = None
        for sh, _ in _shapes(slide.shapes):
            if not (getattr(sh, 'has_chart', False) and sh.has_chart):
                continue
            if (sh.left or 0) > largura_slide:          # gráfico guardado fora do slide
                continue
            ch = sh.chart
            try:
                nomes = [s.name for s in ch.plots[0].series]
            except Exception:
                continue
            if 'LINE' not in str(ch.chart_type):      # barras ficam com Conecta.graficos
                continue
            if len(nomes) != 2 or nomes[1].strip().upper() != 'CDI':
                continue
            serie = serie or ctx.serie_diaria()
            if not serie:
                return
            _dados_grafico(sh, serie, nomes)
            self.trocas += 1
        if not serie:
            return
        # etiquetas "29,56%" / "22,58%": a de cima é a maior
        etq = [sh for sh, _ in _shapes(slide.shapes)
               if re.fullmatch(r'\s*\d+,\d{2}\s*%\s*', _texto(sh))]
        if len(etq) == 2:
            fim_f, fim_c = serie[-1][1], serie[-1][2]
            etq.sort(key=lambda s: s.top or 0)
            for sh, v in zip(etq, sorted([fim_f, fim_c], reverse=True)):
                p = sh.text_frame.paragraphs[0]
                _troca_grupo(p, r'(\d+,\d{2})', fmt.num(v * 100, 2))
            self.trocas += 1

    # -- blocos da alocação real (ALT)
    def alocacao(self, slide, ctx):
        """Treemap da alocação: rótulos "Nome 49,1%" sobre retângulos coloridos
        (no modelo, cada bloco é um retângulo preenchido, às vezes com um gêmeo
        só de contorno, e o rótulo é uma caixa de texto por cima; às vezes o
        nome e o número são duas caixas lado a lado). Os números são trocados;
        se todo rótulo tem o seu bloco, os blocos são redesenhados pelo peso do
        mês. O bloco de uma categoria que saiu da carteira passa para a
        categoria nova (com o nome trocado) ou some; categoria nova sem bloco
        para herdar ganha uma cópia do menor bloco, com cor própria."""
        if ctx is None or not ctx.cart or not ctx.key.startswith('alt'):
            return
        dados = {}
        for n, _, v in ctx.alocacao_real(self.cad):
            dados[_chave_cat(n)] = (n, v)
        conhecidas = set(dados) | _CONHECIDAS
        por_col = {}
        for sh, col in _shapes(slide.shapes):
            por_col.setdefault(id(col), (col, []))[1].append(sh)
        rotulos = []                       # (rótulo, categoria, [caixas que andam junto])
        for col, formas in por_col.values():
            so_nome, so_num = [], []
            for sh in formas:
                t = re.sub(r'\s+', ' ', _texto(sh).replace('\x0b', ' ')).strip()
                if not t:
                    continue
                m = re.fullmatch(r'(.+?),?\s*(\d+,\d{1,2})\s*%+', t)
                if m and _chave_cat(m.group(1)) in conhecidas:
                    rotulos.append((sh, _chave_cat(m.group(1)), []))
                elif _chave_cat(t) in conhecidas:
                    so_nome.append((sh, _chave_cat(t)))
                elif re.fullmatch(r'\d+,\d{1,2}\s*%', t):
                    so_num.append(sh)
            # "FIDCs Cota Mezanino" + "0,5%" em caixas separadas, lado a lado
            for sh, k in so_nome:
                viz = [n for n in so_num if abs((n.top or 0) - (sh.top or 0)) <= (sh.height or 0)
                       and (n.left or 0) >= (sh.left or 0)]
                if viz:
                    rotulos.append((sh, k, [min(viz, key=lambda n: n.left - sh.left)]))
        if len(rotulos) < 2:
            pic = _treemap_em_imagem(slide)
            if pic is not None:
                _treemap_nativo(slide, pic, [dados[k] for k in dados])
                self.trocas += 1
            return
        # o modelo já está com os números do mês (o time atualizou à mão): o
        # desenho dele fica como está
        def atual(sh, extras, k):
            t = ' '.join(_texto(x) for x in [sh] + extras)
            m = re.search(r'(\d+,(\d{1,2}))\s*%', t)
            return m and k in dados and m.group(1) == fmt.num(dados[k][1], len(m.group(2)))
        igual = {k for _, k, _ in rotulos} == set(dados) and             all(atual(sh, ex, k) for sh, k, ex in rotulos)
        for sh, k, extras in rotulos:
            if k in dados:
                _troca_pct([p for s in [sh] + extras for p in s.text_frame.paragraphs], dados[k][1])
        self.trocas += 1
        if igual:
            return
        vistas = self._redesenha(slide, rotulos, dados) or {k for _, k, _ in rotulos if k in dados}
        faltam = [dados[k][0] for k in dados if k not in vistas]
        if faltam:
            self.log.aviso(ctx.key, f'deck: categoria da alocação sem bloco no modelo (slide {self._n}): '
                                    + ', '.join(faltam))

    def _redesenha(self, slide, rotulos, dados):
        """Devolve as categorias que ganharam bloco. Tudo em coordenadas do
        slide: no modelo, os blocos podem estar soltos no slide e os rótulos
        dentro de grupos (cada um com a sua escala)."""
        todas = [sh for sh, _ in _shapes(slide.shapes) if sh.shape_type != 6]
        caixa = {id(sh): _absoluta(sh._element) for sh in todas}
        rot_ids = {id(s) for sh, _, ex in rotulos for s in [sh] + ex}
        blocos = [sh for sh in todas if id(sh) not in rot_ids and not _texto(sh).strip()
                  and caixa[id(sh)] and caixa[id(sh)][2] > caixa[id(sh)][0] and _preenchido(sh)]

        def cx(sh):
            return caixa.get(id(sh)) or _absoluta(sh._element)

        def uniao(partes):
            cs = [cx(s) for s in partes]
            return (min(c[0] for c in cs), min(c[1] for c in cs),
                    max(c[2] for c in cs), max(c[3] for c in cs))

        def area(b):
            c = cx(b)
            return (c[2] - c[0]) * (c[3] - c[1])

        par = []
        for sh, k, ex in rotulos:
            x0, y0, x1, y1 = cx(sh)                 # o nome decide o bloco
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            dentro = [b for b in blocos if cx(b)[0] <= mx <= cx(b)[2] and cx(b)[1] <= my <= cx(b)[3]]
            if not dentro:
                return set()
            par.append(([sh] + ex, k, min(dentro, key=area)))
        if len({id(b) for _, _, b in par}) != len(par):
            return set()

        def gemeos(b):
            cb = [round(v / 1000) for v in cx(b)]
            return [f for f in todas if f is b or (id(f) not in rot_ids and caixa.get(id(f))
                    and [round(v / 1000) for v in caixa[id(f)]] == cb)]

        grupo = {id(b): gemeos(b) for _, _, b in par}     # antes de mexer em qualquer bloco
        X0 = min(cx(b)[0] for *_, b in par); Y0 = min(cx(b)[1] for *_, b in par)
        X1 = max(cx(b)[2] for *_, b in par); Y1 = max(cx(b)[3] for *_, b in par)
        presentes = {k for _, k, _ in par}
        novas = sorted((k for k in dados if k not in presentes), key=lambda k: -dados[k][1])
        fica = []
        for partes, k, b in sorted(par, key=lambda a: -area(a[2])):
            if k in dados:
                fica.append((partes, k, b))
            elif novas:
                # o bloco da categoria que saiu passa para a categoria nova
                k2 = novas.pop(0)
                _renomeia(partes, dados[k2][0], dados[k2][1])
                fica.append((partes, k2, b))
            else:
                for f in grupo[id(b)] + partes:
                    _remove_elemento(f._element)
        if not fica:
            return set()
        # categoria nova sem bloco para herdar: copia o menor bloco, com cor nova
        from pptx.dml.color import RGBColor
        for k2 in novas:
            partes, _, b = min(fica, key=lambda a: area(a[2]))
            usadas = {_cor(f) for f in todas}
            cor = next((c for c in CORES_NOVAS if c not in usadas), None)
            copias = []
            for f in grupo[id(b)] + partes:
                el = copy.deepcopy(f._element)
                f._element.addnext(el)
                novo = type(f)(el, f._parent)
                caixa[id(novo)] = cx(f)
                copias.append(novo)
            n_blocos = len(grupo[id(b)])
            blocos_novos, rot_novo = copias[:n_blocos], copias[n_blocos:]
            for f in blocos_novos:
                if _preenchido(f) and cor:
                    f.fill.fore_color.rgb = RGBColor.from_string(cor)
            todas.extend(copias)
            rot_ids.update(id(s) for s in rot_novo)
            _renomeia(rot_novo, dados[k2][0], dados[k2][1])
            if cor:
                letra = '262626' if cor in CLARAS else 'FFFFFF'
                for s in rot_novo:
                    for p in s.text_frame.paragraphs:
                        for r in p.runs:
                            r.font.color.rgb = RGBColor.from_string(letra)
            grupo[id(blocos_novos[0])] = blocos_novos
            fica.append((rot_novo, k2, blocos_novos[0]))
        fica.sort(key=lambda a: -dados[a[1]][1])
        # bloco muito pequeno (0,5%) ganha área mínima (3%) para o rótulo caber; o número é o real
        rects = _squarify([max(dados[k][1], 3.0) for _, k, _ in fica], X0, Y0, X1 - X0, Y1 - Y0)
        for (partes, k, b), (x, y, w, h) in zip(fica, rects):
            bx0, by0, bx1, by1 = cx(b)
            lx0, ly0, lx1, ly1 = uniao(partes)
            # posição do rótulo no bloco original (em geral, embaixo à esquerda)
            dx, fundo = lx0 - bx0, by1 - ly1
            for g in grupo[id(b)]:
                _posiciona(g, x, y, w, h)
            lw, lh = lx1 - lx0, ly1 - ly0
            # a caixa do rótulo do modelo às vezes é menor que o texto (sem quebra)
            tw = max(lw, _largura_texto(partes))
            if len(partes) == 1 and w * 0.94 / tw < 0.75 and _quebra_antes_do_numero(partes[0]):
                # nem com a letra menor cabe numa linha: o número desce
                tw = _largura_texto(partes)
                lh = max(lh, _altura_texto(partes[0]))
            esc = min(1.0, w * 0.94 / tw, h * 0.94 / lh)
            if esc < 1:
                # encolhe a letra se o rótulo não couber no bloco novo
                esc = max(esc, 0.4)
                for s in partes:
                    for p in s.text_frame.paragraphs:
                        for r in p.runs:
                            if r.font.size:
                                r.font.size = int(r.font.size * esc)
            else:
                esc = 1.0
            if len(partes) == 1:
                # rótulo movido: alinhado à esquerda, caixa do tamanho do texto
                for p in partes[0].text_frame.paragraphs:
                    p.alignment = 1
                partes[0].text_frame.word_wrap = False
                lw = tw
            lw, lh = lw * esc, lh * esc
            dx = max(0, min(dx, w - lw))
            fundo = max(0, min(fundo, h - lh))
            nx = x + dx                             # dentro do próprio bloco
            ny = y + h - fundo - lh
            if len(partes) == 1:
                _posiciona(partes[0], nx, ny, lw, lh)
                continue
            for s in partes:                        # as caixas do rótulo andam juntas
                c = cx(s)
                _posiciona(s, nx + (c[0] - lx0) * esc, ny + (c[1] - ly0) * esc,
                           (c[2] - c[0]) * esc, (c[3] - c[1]) * esc)
        return {k for _, k, _ in fica}


def _quebra_antes_do_numero(sh):
    """"FIDC Mez, 0,5%" -> "FIDC Mez," / "0,5%" (um <a:br> antes do número)."""
    for p in sh.text_frame.paragraphs:
        runs = list(p._p.findall(f'{A}r'))
        for i, r in enumerate(runs):
            t = r.find(f'{A}t')
            m = re.search(r'\d+,\d{1,2}\s*%', t.text or '') if t is not None else None
            if not m:
                continue
            antes = (t.text[:m.start()]).rstrip()
            if not antes and i == 0:
                return False
            ant = r.getprevious()
            if ant is not None and ant.tag == f'{A}br':
                return False                   # já está em outra linha
            br = etree.SubElement(p._p, f'{A}br')
            rpr = r.find(f'{A}rPr')
            if rpr is not None:
                br.append(copy.deepcopy(rpr))
            if antes:
                resto = t.text[m.start():]
                t.text = antes
                novo = copy.deepcopy(r)
                novo.find(f'{A}t').text = resto
                r.addnext(br)
                br.addnext(novo)
            else:
                if ant is not None and ant.find(f'{A}t') is not None:
                    at = ant.find(f'{A}t')
                    at.text = (at.text or '').rstrip()
                r.addprevious(br)
            return True
    return False


def _altura_texto(sh):
    linhas, pt = 0, 0
    for p in sh.text_frame.paragraphs:
        linhas += 1 + len(p._p.findall(f'{A}br'))
        for r in p.runs:
            if r.font.size:
                pt = max(pt, r.font.size.pt)
    return linhas * (pt or 10) * 1.2 * 12700


def _escala_do_pai(el):
    """(ax, bx, ay, by): coordenada do slide = a * coordenada do pai + b."""
    ax, bx, ay, by = 1.0, 0.0, 1.0, 0.0
    pai = el.getparent()
    while pai is not None and pai.tag == f'{P}grpSp':
        xf = pai.find(f'{P}grpSpPr/{A}xfrm')
        if xf is None:
            break
        off, ext = xf.find(f'{A}off'), xf.find(f'{A}ext')
        co, ce = xf.find(f'{A}chOff'), xf.find(f'{A}chExt')
        if None in (off, ext, co, ce):
            break
        # grupo de linhas tem altura 0: escala 1 nesse eixo, só translada
        sx = int(ext.get('cx')) / int(ce.get('cx')) if int(ce.get('cx')) else 1.0
        sy = int(ext.get('cy')) / int(ce.get('cy')) if int(ce.get('cy')) else 1.0
        # compõe: novo = s * (a*x + b - ch) + off
        ax, bx = sx * ax, sx * (bx - int(co.get('x'))) + int(off.get('x'))
        ay, by = sy * ay, sy * (by - int(co.get('y'))) + int(off.get('y'))
        pai = pai.getparent()
    return ax, bx, ay, by


def _posiciona(sh, x, y, w, h):
    """Põe o shape na caixa (x, y, w, h) dada em coordenadas do slide."""
    ax, bx, ay, by = _escala_do_pai(sh._element)
    sh.left = int(round((x - bx) / ax))
    sh.top = int(round((y - by) / ay))
    sh.width = max(int(round(w / ax)), 1)
    sh.height = max(int(round(h / ay)), 1)


def _largura_texto(partes):
    """Largura estimada do texto (EMU): caracteres x corpo x 0,58 (Versos é larga), linha a
    linha (as quebras <a:br> separam as linhas dentro do parágrafo)."""
    larg = 0
    for s in partes:
        for p in s.text_frame.paragraphs:
            linha = 0
            for el in p._p:
                tag = el.tag.split('}')[1]
                if tag == 'br':
                    larg, linha = max(larg, linha), 0
                elif tag == 'r':
                    rpr = el.find(f'{A}rPr')
                    pt = int(rpr.get('sz')) / 100 if rpr is not None and rpr.get('sz') else 10
                    t = el.find(f'{A}t')
                    linha += len(t.text or '') * pt * 0.58 * 12700 if t is not None else 0
            larg = max(larg, linha)
    return larg


def _troca_pct(pars, v):
    """Troca o "49,1%" do rótulo mantendo as casas do modelo (1 ou 2)."""
    for p in pars:
        t = ''.join(r.text for r in p.runs)
        m = re.search(r'(\d+,(\d{1,2}))\s*%', t)
        if m:
            return _troca_trecho(p, m.start(1), m.end(1), fmt.num(v, len(m.group(2))))
    return False


def _renomeia(partes, nome, v):
    """Rótulo de bloco reaproveitado: nome novo no lugar do antigo."""
    sh = partes[0]
    pars = sh.text_frame.paragraphs
    if len(partes) > 1:
        # nome numa caixa, número na outra
        tt = ''.join(r.text for r in pars[0].runs)
        _troca_trecho(pars[0], 0, len(tt), nome)
        for q in pars[1:]:
            _remove_elemento(q._p)
        _troca_pct([q for s in partes[1:] for q in s.text_frame.paragraphs], v)
        return
    for i, p in enumerate(pars):
        t = ''.join(r.text for r in p.runs)
        m = re.search(r'(\d+,\d{1,2})\s*%', t)
        if m and m.start() > 0:
            # nome e número no mesmo parágrafo
            tem_br = p._p.find(f'{A}br') is not None
            _troca_trecho(p, 0, m.start(), nome if tem_br else nome + ' ')
            break
        if m:
            # nome nos parágrafos de cima: o primeiro recebe o nome novo, os outros somem
            antes = [q for q in pars[:i] if ''.join(r.text for r in q.runs).strip()]
            if antes:
                tt = ''.join(r.text for r in antes[0].runs)
                _troca_trecho(antes[0], 0, len(tt), nome)
                for q in antes[1:]:
                    _remove_elemento(q._p)
            break
    _troca_pct(sh.text_frame.paragraphs, v)


_CONHECIDAS = {'fidccotasenior', 'fidccotamezanino', 'liquidez', 'creditoestruturado',
               'creditoprivado', 'fiagro', 'precatorio', 'bancario', 'fip', 'fidccotaunica',
               'debenture', 'fidcmez'}


def _cor(sh):
    try:
        return str(sh.fill.fore_color.rgb) if sh.fill.type == 1 else None
    except Exception:
        return None


def _preenchido(sh):
    try:
        return sh.fill.type == 1          # MSO_FILL.SOLID
    except Exception:
        return False


def _chave_cat(n):
    n = (n.lower().replace('ê', 'e').replace('é', 'e').replace('ó', 'o').replace('í', 'i')
         .replace('á', 'a').replace('ã', 'a').replace('ç', 'c'))
    k = ''.join(w[:-1] if w.endswith('s') and len(w) > 3 else w
                for w in re.findall(r'[a-z]+', n))
    return _APELIDOS.get(k, k)


# como o modelo escreve -> como a carteira chama
_APELIDOS = {'fidcmez': 'fidccotamezanino', 'fidccotamezsub': 'fidccotamezanino'}


# Paleta do treemap desenhado (modelo do ALT 90 em imagem): as cores do PNG
# original na ordem do peso, uma por categoria, nunca repetida.
PALETA_TREEMAP = ['262626', 'BFBFBF', '4D4D4D', 'C1F2D4', '12612F', '8FD9AE', '7A7A7A', 'E6EDF1']
# cor do bloco copiado para categoria nova: contrastes fortes, nunca repetida
CORES_NOVAS = ['12612F', '7A7A7A', '8FD9AE', '3F6073', 'ABC6CD', '4D4D4D']
CLARAS = {'ABC6CD', 'BFBFBF', 'C1F2D4', '8FD9AE', 'E6EDF1'}


def _treemap_em_imagem(slide):
    """O PNG largo logo abaixo do título "Alocação da carteira" (só o deck do
    ALT 90 tem o treemap como imagem)."""
    titulo = None
    for sh, _ in _shapes(slide.shapes):
        if 'Alocação da carteira' in ' '.join(_texto(sh).split()):
            titulo = _absoluta(sh._element)
            break
    if not titulo:
        return None
    for sh, _ in _shapes(slide.shapes):
        if sh.shape_type != 13 or not sh.width or not sh.height:
            continue
        blip = sh._element.blipFill.blip if sh._element.blipFill is not None else None
        rid = blip.rEmbed if blip is not None else None
        if not rid or not slide.part.rels[rid].target_ref.lower().endswith('.png'):
            continue
        b = _absoluta(sh._element)
        if b and (b[2] - b[0]) / (b[3] - b[1]) > 2.5 and b[1] >= titulo[1] - 12700 * 30                 and b[0] >= titulo[0] - 12700 * 20:
            return sh
    return None


def _treemap_nativo(slide, pic, itens):
    """Troca a imagem por retângulos nativos (vetor, editáveis) no mesmo lugar:
    nome em negrito, percentual maior, embaixo à esquerda, como no PNG."""
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR
    from pptx.util import Pt
    # o PNG do modelo tem uma faixa branca à direita (~1% da largura)
    b = _absoluta(pic._element)                 # a imagem pode estar dentro de um grupo
    x0, y0, w0, h0 = b[0], b[1], int((b[2] - b[0]) * 0.988), b[3] - b[1]
    itens = sorted(itens, key=lambda a: -a[1])
    rects = _squarify([max(v, 3.0) for _, v in itens], x0, y0, w0, h0)
    # textos soltos por cima da imagem (correções à mão no modelo) saem junto
    for sh, _ in list(_shapes(slide.shapes)):
        c = _absoluta(sh._element)
        if sh.shape_type != 6 and sh is not pic and _texto(sh) and c and                 c[0] >= b[0] and c[2] <= b[2] and c[1] >= b[1] and c[3] <= b[3]:
            _remove_elemento(sh._element)
    arvore = slide.shapes._spTree
    ancora = _topo(pic._element, arvore)        # os blocos entram logo acima dele
    if ancora is pic._element:
        ancora = pic._element.getprevious()
    pic._element.getparent().remove(pic._element)
    alto = h0 / 12700                        # altura do quadro em pt
    for i, ((nome, v), (x, y, w, h)) in enumerate(zip(itens, rects)):
        cor = PALETA_TREEMAP[i % len(PALETA_TREEMAP)]
        bl = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, int(x), int(y), max(int(w), 1), max(int(h), 1))
        bl.fill.solid()
        bl.fill.fore_color.rgb = RGBColor.from_string(cor)
        bl.line.fill.background()
        bl.shadow.inherit = False
        bl.name = f'treemap {nome}'
        tf = bl.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.BOTTOM
        m = int(min(w, h) * 0.08)
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = max(m, 12700 * 2)
        # letra pelo tamanho do bloco: o maior no corpo do PNG, os pequenos menores
        lado = min(w, h) / 12700
        corpo = max(5, min(alto * 0.10, lado * 0.22))
        # a palavra mais longa do nome não pode quebrar no meio ("Estrutura/do")
        util = (w - 2 * max(m, 12700 * 2)) / 12700
        maior = max(len(p) for p in nome.split()) * 0.75 * 0.58
        corpo = max(3.5, min(corpo, util / maior if maior else corpo))
        texto = '000000' if cor in CLARAS else 'FFFFFF'
        p1 = tf.paragraphs[0]
        r1 = p1.add_run()
        r1.text = nome
        r1.font.size, r1.font.bold = Pt(corpo * 0.75), True
        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        r2.text = f'{fmt.num(v, 2)}%'
        r2.font.size, r2.font.bold = Pt(corpo), True
        for r in (r1, r2):
            r.font.name = 'Versos'
            r.font.color.rgb = RGBColor.from_string('262626' if texto == '000000' else 'FFFFFF')
        for p in (p1, p2):
            p.alignment = 1          # esquerda
        # mantém a ordem de desenho da imagem original
        el = bl._element
        el.getparent().remove(el)
        ancora.addnext(el)
        ancora = el


def _squarify(vals, x, y, w, h):
    """Treemap "squarified" simples: devolve (x, y, w, h) na ordem dos valores."""
    tot = sum(vals)
    vals = [v * w * h / tot for v in vals]
    out = []

    def pior(fila, lado):
        s = sum(fila)
        return max(max(lado * lado * r / (s * s), (s * s) / (lado * lado * r)) for r in fila)

    while vals:
        lado = min(w, h)
        fila = [vals.pop(0)]
        while vals and pior(fila + [vals[0]], lado) <= pior(fila, lado):
            fila.append(vals.pop(0))
        s = sum(fila)
        if w >= h:
            larg = s / h
            yy = y
            for r in fila:
                out.append((x, yy, larg, r / larg))
                yy += r / larg
            x += larg
            w -= larg
        else:
            alt = s / w
            xx = x
            for r in fila:
                out.append((xx, y, r / alt, alt))
                xx += r / alt
            y += alt
            h -= alt
    return out


def _dados_grafico(sh, serie, nomes):
    from pptx.chart.data import CategoryChartData
    ch = sh.chart
    cs = ch._chartSpace
    ext = cs.find('{http://schemas.openxmlformats.org/drawingml/2006/chart}externalData')
    if ext is not None:
        rid = ext.get(R + 'id')
        cs.remove(ext)
        if rid and rid in ch.part.rels:
            ch.part.rels.pop(rid)
    cd = CategoryChartData(number_format='0.00%')
    cd.categories = [d.date() for d, _, _ in serie]
    cd.add_series(nomes[0] or 'Fundo', [f for _, f, _ in serie])
    cd.add_series(nomes[1] or 'CDI', [c for _, _, c in serie])
    ch.replace_data(cd)
    try:
        ca = ch.category_axis
        ca.tick_labels.number_format = '[$-416]mmm-yy;@'
        ca.tick_labels.number_format_is_linked = False
    except Exception:
        pass


# --------------------------------------------------------------- remoções
def _remove_selo_xp(slide):
    st = slide.shapes._spTree
    n = 0
    for sh, _ in list(_shapes(slide.shapes)):
        if 'plataforma da XP' in _texto(sh):
            el = _topo(sh._element, st)
            if el.getparent() is st:
                st.remove(el)
                n += 1
    return n


def _remove_roa(slide):
    st = slide.shapes._spTree
    for sh, _ in list(_shapes(slide.shapes)):
        if _texto(sh).strip() == 'ROA':
            el = _topo(sh._element, st)
            cx = _caixa(el)
            if el.getparent() is st:
                st.remove(el)
            if cx:
                x0, y0, x1, y1 = cx
                for outro in list(st):
                    c = _caixa(outro)
                    if c and x0 <= (c[0] + c[2]) / 2 <= x1 and y0 <= (c[1] + c[3]) / 2 <= y1:
                        st.remove(outro)
            return 1
    return 0


def _remove_cartao(slide, marcas):
    """Família ALT sem o ALT Light: some a coluna do cartão (fundo, logo,
    CNPJ e as linhas, que no modelo são grupos que atravessam os três
    cartões) e os outros dois se centralizam no espaço dos três."""
    if not any('Família ALT' in ' '.join(_texto(sh).split()) for sh in slide.shapes):
        return False
    pecas = [(sh, _absoluta(sh._element)) for sh, _ in _shapes(slide.shapes)
             if sh.shape_type != 6 and not sh.is_placeholder]
    pecas = [(sh, b) for sh, b in pecas if b]
    # os cartões são os fundos altos (mais de metade da altura do slide)
    alto = slide.part.package.presentation_part.presentation.slide_height
    cartoes = sorted([b for sh, b in pecas if (b[3] - b[1]) > alto * 0.6 and (b[2] - b[0]) < alto],
                     key=lambda b: b[0])
    if len(cartoes) < 2:
        return False

    def coluna(b):
        mx = (b[0] + b[2]) / 2
        for i, c in enumerate(cartoes):
            if c[0] <= mx <= c[2]:
                return i
        return None

    alvo = None
    for sh, b in pecas:
        t = ' '.join(_texto(sh).split())
        if t and any(m in t for m in marcas):
            alvo = coluna(b)
            break
    if alvo is None:
        return False
    restantes = [c for i, c in enumerate(cartoes) if i != alvo]
    esq, dir_ = cartoes[0][0], cartoes[-1][2]
    larg = sum(c[2] - c[0] for c in restantes)
    vao = (cartoes[1][0] - cartoes[0][2]) if len(cartoes) > 1 else 0
    inicio = esq + ((dir_ - esq) - (larg + vao * (len(restantes) - 1))) / 2
    destino, x = {}, inicio
    for c in restantes:
        destino[cartoes.index(c)] = x - c[0]
        x += (c[2] - c[0]) + vao
    for sh, b in pecas:
        i = coluna(b)
        if i is None:
            continue
        if i == alvo:
            _remove_elemento(sh._element)
        else:
            d = destino[i]
            _posiciona(sh, b[0] + d, b[1], b[2] - b[0], b[3] - b[1])
    return True


def _remove_slide(prs, slide):
    lst = prs.slides._sldIdLst
    for sid in list(lst):
        if prs.slides.part.related_part(sid.get(R + 'id')) is slide.part:
            prs.part.drop_rel(sid.get(R + 'id'))
            lst.remove(sid)
            return True
    return False


# ------------------------------------------------- Tivio Conecta (e afins)
# O Conecta tem layouts que os outros decks não têm: tabelas (Mês/Ano/Desde o
# início, PL em R$ MM), barras mensais Fundo x CDI com o "% CDI" em caixas de
# texto por cima, rating, setorial e a rosca da composição. Tudo reconhecido
# pelo conteúdo: as categorias do gráfico dizem o que ele é.

RATINGS = re.compile(r'^(AAA|AA[+-]?|A[+-]?|BBB[+-]?|BB[+-]?|B[+-]?|CCC|CC|C|D)$')
COMPOSICAO = {'caixa', 'fidc', 'bancário', 'corporativo'}
PERIODOS_TABELA = {'MES': 'mes', 'ANO': 'ano', '12M': '12m', '12 M': '12m',
                   'DESDE O INICIO': 'inicio', 'INICIO': 'inicio'}
ROTULO_PCT_CDI = re.compile(r'^\s*(\d+(?:,(\d+))?)\s*%\s*CDI\s*$')


def _sem_acento(t):
    import unicodedata
    t = unicodedata.normalize('NFKD', ' '.join(str(t).split()).upper())
    return ''.join(c for c in t if not unicodedata.combining(c))


def _troca_celula(cell, regex, valor):
    for p in cell.text_frame.paragraphs:
        if _troca_grupo(p, regex, valor):
            return True
    return False


def _casas(texto, padrao=2):
    m = re.search(r',(\d+)', texto)
    return len(m.group(1)) if m else (0 if re.search(r'\d', texto) else padrao)


class Conecta:
    """Preenchimentos extras por slide (tabelas, barras, rating, setores)."""

    def __init__(self, pre):
        self.pre = pre

    # -- tabelas
    def tabelas(self, slide, ctx):
        if ctx is None:
            return
        for sh, _ in _shapes(slide.shapes):
            if not (getattr(sh, 'has_table', False) and sh.has_table):
                continue
            linhas = [[c for c in r.cells] for r in sh.table.rows]
            textos = [[_sem_acento(c.text) for c in r] for r in linhas]
            # Mês / Ano / Desde o início  x  FUNDO / CDI / % CDI
            cab = next((i for i, r in enumerate(textos)
                        if sum(1 for t in r if t in PERIODOS_TABELA) >= 2), None)
            if cab is not None:
                cols = {j: PERIODOS_TABELA[t] for j, t in enumerate(textos[cab]) if t in PERIODOS_TABELA}
                for i in range(cab + 1, len(linhas)):
                    rot = textos[i][0]
                    campo = 'pct' if '%' in rot else 'fundo' if 'FUNDO' in rot else \
                        'bench' if rot in ('CDI', 'IPCA', 'IMA-B 5', 'IMA-B') else None
                    if not campo:
                        continue
                    for j, per in cols.items():
                        v = ctx.valor(per, campo)
                        if v is None:
                            continue
                        cel = linhas[i][j]
                        n = _casas(cel.text)
                        if _troca_celula(cel, r'(' + NUM + r')\s*%', fmt.num(v * 100, n)):
                            self.pre.trocas += 1
            # Patrimônio Líquido (R$ MM): ATUAL / 12 M
            for i, r in enumerate(textos):
                if 'ATUAL' in r and i + 1 < len(linhas):
                    for j, t in enumerate(r):
                        v = ctx.pl if t == 'ATUAL' else ctx.pl_medio if t in ('12 M', '12M') else None
                        if v:
                            cel = linhas[i + 1][j]
                            if _troca_celula(cel, r'(' + NUM + r')', fmt.num(v / 1e6, _casas(cel.text, 1))):
                                self.pre.trocas += 1
            # "PL" e embaixo "R$ 3,7 bilhões"
            for i, r in enumerate(textos):
                if r and r[0] == 'PL' and i + 1 < len(linhas) and ctx.pl:
                    if _troca_celula(linhas[i + 1][0], r'R\$\s*([\d.,]+\s*(?:bilh|milh)\w*)',
                                     _curto(ctx.pl, True)):
                        self.pre.trocas += 1

    # -- "Patrimônio Líquido" com o valor numa caixa logo abaixo
    def pl_rotulado(self, slide, ctx):
        if ctx is None or not ctx.pl:
            return
        formas = [(sh, _absoluta(sh._element)) for sh, _ in _shapes(slide.shapes)
                  if getattr(sh, 'has_text_frame', False) and sh.has_text_frame]
        for rot, br in formas:
            if not br or _sem_acento(_texto(rot)) != 'PATRIMONIO LIQUIDO':
                continue
            for val, bv in formas:
                if not bv or not re.fullmatch(r'\s*R\$\s*[\d.,]+\s*(bilh|milh)\w*\s*', _texto(val)):
                    continue
                if br[1] - 12700 * 20 <= bv[1] <= br[3] + 12700 * 80 and bv[0] < br[2] + 12700 * 300:
                    for p in val.text_frame.paragraphs:
                        if _troca_grupo(p, r'R\$\s*([\d.,]+\s*(?:bilh|milh)\w*)', _curto(ctx.pl, True)):
                            self.pre.trocas += 1
                            break

    # -- "Previsão de alocação" que é a alocação real (opção alocacao_hghy)
    def hghy(self, slide, ctx):
        if ctx is None:
            return
        mapa = {}
        for n, _, v in ctx.alocacao_hghy:
            mapa[n] = v
        if 'Crédito High Yield' in mapa:
            mapa['Crédito Estruturado'] = mapa['Crédito High Yield']
        formas = [(sh, _absoluta(sh._element)) for sh, _ in _shapes(slide.shapes)
                  if getattr(sh, 'has_text_frame', False) and sh.has_text_frame]
        for rot, br in formas:
            nome = ' '.join(_texto(rot).split())
            if nome not in mapa or not br:
                continue
            for val, bv in formas:
                if bv and re.fullmatch(r'\s*\d+,\d\s*%\s*', _texto(val)) and \
                        br[0] <= (bv[0] + bv[2]) / 2 <= br[2] and br[1] <= (bv[1] + bv[3]) / 2 <= br[3]:
                    if _troca_grupo(val.text_frame.paragraphs[0], r'(\d+,\d)', fmt.num(mapa[nome], 1)):
                        self.pre.trocas += 1

    # -- gráficos de barras / rosca
    def graficos(self, slide, ctx, largura):
        if ctx is None:
            return
        rotulos = [(sh, _absoluta(sh._element)) for sh, _ in _shapes(slide.shapes)
                   if getattr(sh, 'has_text_frame', False) and sh.has_text_frame
                   and ROTULO_PCT_CDI.match(_texto(sh))]
        for sh, _ in _shapes(slide.shapes):
            if not (getattr(sh, 'has_chart', False) and sh.has_chart):
                continue
            b = _absoluta(sh._element)
            if not b or b[0] > largura:
                continue
            ch = sh.chart
            try:
                pl = ch.plots[0]
                cats = [str(c) for c in pl.categories]
                series = list(pl.series)
            except Exception:
                continue
            if not cats or not series:
                continue
            meus = sorted([(r, br) for r, br in rotulos
                           if b[0] <= (br[0] + br[2]) / 2 <= b[2] and b[1] <= (br[1] + br[3]) / 2 <= b[3]],
                          key=lambda a: a[1][0])
            nomes = [_sem_acento(c) for c in cats]
            if len(series) == 2 and all(re.fullmatch(r'\d{5}(\.0)?', c) for c in cats):
                self._mensal(sh, ctx, cats, series, meus)
            elif len(series) == 2 and set(nomes) <= {'ACUMULADO DO INICIO', 'ANO', 'DESDE O INICIO', '12M', 'MES'}:
                self._acumulado(sh, ctx, cats, series, meus)
            elif len(series) == 1 and all(RATINGS.match(c.strip()) for c in cats):
                itens = [(n, v / 100) for n, _, v in ctx.rating_relatorio]
                self._uma_serie(sh, series, itens)
            elif len(series) == 1 and {c.strip().lower() for c in cats} <= COMPOSICAO:
                comp = {n.lower(): v / 100 for n, _, v in ctx.composicao()}
                self._uma_serie(sh, series, [(c, comp.get(c.strip().lower(), 0.0)) for c in cats])
            elif len(series) == 1 and ctx.cart is not None:
                st = ctx.cart.get('setores')
                if st is None:
                    continue
                st = st[st > 0].sort_values(ascending=False)
                if len({c.strip() for c in cats} & set(st.index)) < max(2, len(cats) // 2):
                    continue                        # não é setorial
                itens = [(n, float(v)) for n, v in st.head(len(cats)).items()]
                self._uma_serie(sh, series, itens)

    def _uma_serie(self, sh, series, itens):
        from pptx.chart.data import CategoryChartData
        if not itens:
            return
        fmt_v = _formato(series[0], '0.00%')
        cd = CategoryChartData(number_format=fmt_v)
        cd.categories = [n for n, _ in itens]
        cd.add_series(series[0].name or '', [v for _, v in itens])
        _sem_vinculo(sh.chart)
        sh.chart.replace_data(cd)
        self.pre.trocas += 1

    def _mensal(self, sh, ctx, cats, series, rotulos):
        from datetime import datetime, timedelta
        from pptx.chart.data import CategoryChartData
        n = len(cats)
        meses = ctx.mensal(n)
        if len(meses) < 1:
            return
        desc = float(cats[0]) > float(cats[-1])
        porcento = max(abs(v or 0) for s in series for v in s.values) > 0.5
        k = 100 if porcento else 1
        ordem = list(reversed(meses)) if desc else meses
        fmt_cat = _formato_categoria(sh.chart)
        cd = CategoryChartData(number_format=_formato(series[0], 'General'))
        # mesmo jeito do modelo: o 1º dia do mês como data do Excel
        cd.categories = [datetime(d.year, d.month, 1).date() for d, _, _ in ordem]
        cd.add_series(series[0].name or 'Fundo', [round(f * k, 2 if porcento else 4) for _, f, _ in ordem])
        cd.add_series(series[1].name or 'CDI', [round(c * k, 2 if porcento else 4) for _, _, c in ordem])
        _sem_vinculo(sh.chart)
        sh.chart.replace_data(cd)
        if fmt_cat:
            _poe_formato_categoria(sh.chart, fmt_cat)
        self.pre.trocas += 1
        # "% CDI" por cima das barras, da esquerda (mais antigo) para a direita
        crono = meses[-len(rotulos):] if rotulos else []
        for (r, _), (_, f, c) in zip(rotulos, crono):
            t = _texto(r)
            n_c = _casas(ROTULO_PCT_CDI.match(t).group(1), 0)
            if c:
                _troca_grupo(r.text_frame.paragraphs[0], r'(\d+(?:,\d+)?)\s*%', fmt.num(f / c * 100, n_c))

    def _acumulado(self, sh, ctx, cats, series, rotulos):
        from pptx.chart.data import CategoryChartData
        per = []
        for c in cats:
            u = _sem_acento(c)
            per.append('inicio' if 'INICIO' in u else 'ano' if u == 'ANO' else '12m' if u == '12M' else 'mes')
        f = [ctx.valor(p, 'fundo') for p in per]
        bch = [ctx.valor(p, 'bench') for p in per]
        if any(v is None for v in f + bch):
            return
        cd = CategoryChartData(number_format=_formato(series[0], '0.00%'))
        cd.categories = cats
        cd.add_series(series[0].name or 'Fundo', f)
        cd.add_series(series[1].name or 'CDI', bch)
        _sem_vinculo(sh.chart)
        sh.chart.replace_data(cd)
        self.pre.trocas += 1
        for (r, _), p in zip(rotulos, per):
            v = ctx.valor(p, 'pct')
            if v is not None:
                n_c = _casas(ROTULO_PCT_CDI.match(_texto(r)).group(1), 0)
                _troca_grupo(r.text_frame.paragraphs[0], r'(\d+(?:,\d+)?)\s*%', fmt.num(v * 100, n_c))


def _formato(serie, padrao):
    fc = serie._element.xpath('./c:val//c:formatCode/text()')
    return fc[0] if fc else padrao


def _formato_categoria(chart):
    fc = chart._chartSpace.xpath('.//c:ser[1]/c:cat//c:formatCode/text()')
    return fc[0] if fc else None


def _poe_formato_categoria(chart, formato):
    for el in chart._chartSpace.xpath('.//c:ser/c:cat//c:formatCode'):
        el.text = formato


def _sem_vinculo(chart):
    """replace_data não aceita gráfico com a planilha externa vinculada."""
    cs = chart._chartSpace
    ext = cs.find('{http://schemas.openxmlformats.org/drawingml/2006/chart}externalData')
    if ext is not None:
        rid = ext.get(R + 'id')
        cs.remove(ext)
        if rid and rid in chart.part.rels:
            chart.part.rels.pop(rid)


# ------------------------------------------------ estilo dos posts (vidro)
# `estilo: post` num slide do decks.yml: o slide ganha a estética dos posts de
# Destaques (templates/materiais/tivio-post-*.html): fundo navy em gradiente
# com orbes e arcos de luz, e os quadros em vidro (cantos arredondados,
# gradiente branco translúcido em diagonal, borda clara fina). Tudo nativo do
# PowerPoint: continua editável e sai igual no PDF.

def _a(tag, **attrs):
    el = etree.Element(f'{A}{tag}')
    for k, v in attrs.items():
        el.set(k, str(v))
    return el


def _rgb(hexa, alpha=None):
    c = _a('srgbClr', val=hexa)
    if alpha is not None:
        c.append(_a('alpha', val=int(alpha * 1000)))
    return c


def _gradiente(stops, ang=None, circulo=False):
    g = _a('gradFill', rotWithShape='1')
    lst = etree.SubElement(g, f'{A}gsLst')
    for pos, hexa, alpha in stops:
        gs = etree.SubElement(lst, f'{A}gs', pos=str(int(pos * 1000)))
        gs.append(_rgb(hexa, alpha))
    if circulo:
        path = etree.SubElement(g, f'{A}path', path='circle')
        etree.SubElement(path, f'{A}fillToRect', l='50000', t='50000', r='50000', b='50000')
    else:
        etree.SubElement(g, f'{A}lin', ang=str(int((ang or 0) * 60000)), scaled='0')
    return g


def _linha(hexa=None, alpha=None, pt=0.75):
    ln = _a('ln', w=int(pt * 12700))
    if hexa:
        sf = etree.SubElement(ln, f'{A}solidFill')
        sf.append(_rgb(hexa, alpha))
    else:
        etree.SubElement(ln, f'{A}noFill')
    return ln


def _pinta(el, preenchimento, linha, raio_pt=None):
    """Troca preenchimento, contorno e (opcional) geometria de um sp."""
    sppr = el.find(f'{P}spPr')
    if sppr is None:
        return
    for tag in ('noFill', 'solidFill', 'gradFill', 'blipFill', 'pattFill', 'grpFill', 'ln',
                'effectLst', 'effectDag'):
        for x in sppr.findall(f'{A}{tag}'):
            sppr.remove(x)
    geo = sppr.find(f'{A}prstGeom')
    cust = sppr.find(f'{A}custGeom')
    if raio_pt is not None and geo is None and cust is not None:
        # forma livre (cartão desenhado à mão) vira retângulo arredondado
        geo = etree.Element(f'{A}prstGeom', prst='roundRect')
        cust.addprevious(geo)
        sppr.remove(cust)
    if raio_pt is not None and geo is not None:
        cx = _caixa_propria(el)
        lado = min(cx[2] - cx[0], cx[3] - cx[1]) if cx else 0
        geo.set('prst', 'roundRect')
        for x in list(geo):
            geo.remove(x)
        av = etree.SubElement(geo, f'{A}avLst')
        adj = int(min(50000, (raio_pt * 12700) / lado * 100000)) if lado else 8000
        etree.SubElement(av, f'{A}gd', name='adj', fmla=f'val {adj}')
    # ordem do schema: xfrm, geometria, preenchimento, ln
    depois = geo if geo is not None else sppr.find(f'{A}custGeom')
    if depois is None:
        depois = sppr.find(f'{A}xfrm')
    depois.addnext(preenchimento)
    preenchimento.addnext(linha)


VIDRO = [(0, 'FFFFFF', 19), (30, 'FFFFFF', 5.5), (48, 'FFFFFF', 2), (76, 'FFFFFF', 5), (100, 'FFFFFF', 13)]
VIDRO_FORTE = [(0, 'FFFFFF', 22), (35, 'FFFFFF', 8), (60, 'C1F4D4', 4), (100, '759DB4', 9)]


def _fundo_post(slide):
    """Fundo navy dos posts, atrás de tudo: gradiente, três orbes e os arcos."""
    prs_w = slide.part.package.presentation_part.presentation.slide_width
    prs_h = slide.part.package.presentation_part.presentation.slide_height
    arvore = slide.shapes._spTree
    from pptx.enum.shapes import MSO_SHAPE
    novos = []

    def forma(tipo, x, y, w, h, preench, linha, nome):
        sh = slide.shapes.add_shape(tipo, int(x), int(y), int(w), int(h))
        sh.name = nome
        _pinta(sh._element, preench, linha)
        sh.shadow.inherit = False
        novos.append(sh._element)
        return sh

    W, H = prs_w, prs_h
    _fundo_do_slide(slide, [(0, '0D141C', None), (52, '080D13', None), (100, '03060A', None)], 68)
    # orbes (radial: centro claro que some)
    forma(MSO_SHAPE.OVAL, W * 0.50, -H * 0.55, W * 0.62, W * 0.62,
          _gradiente([(0, 'C8D7E0', 26), (48, '759DB4', 8), (70, '759DB4', 0), (100, '759DB4', 0)], circulo=True),
          _linha(), 'post orbe a')
    forma(MSO_SHAPE.OVAL, -W * 0.22, H * 0.25, W * 0.52, W * 0.52,
          _gradiente([(0, '759DB4', 22), (68, '759DB4', 0), (100, '759DB4', 0)], circulo=True),
          _linha(), 'post orbe b')
    forma(MSO_SHAPE.OVAL, W * 0.48, H * 0.55, W * 0.58, W * 0.58,
          _gradiente([(0, '3C4A60', 40), (68, '3C4A60', 0), (100, '3C4A60', 0)], circulo=True),
          _linha(), 'post orbe c')
    # arcos finos no canto superior direito
    for i, (k, a) in enumerate(((0.80, 26), (0.95, 14), (1.12, 8))):
        d = W * k
        forma(MSO_SHAPE.OVAL, W * 1.02 - d * 0.78, -d * 0.55, d, d, _a('noFill'),
              _linha('C8D7E0', a, 0.75), f'post arco {i + 1}')
    # tudo para trás, na ordem criada
    pos = 2
    for el in novos:
        arvore.remove(el)
        arvore.insert(pos, el)
        pos += 1


def _alinha_post(slide):
    """Grade do slide de fundo no estilo post: tudo entre a margem do
    "RENTABILIDADE" (L) e a borda direita do CNPJ (R), com o mesmo vão G entre
    quadros, na horizontal e na vertical. Sem a moldura escura do modelo, os
    cartões de baixo (que eram recuados dentro dela) passam a ocupar a mesma
    largura dos quadros de rentabilidade. O que está dentro de cada cartão anda
    junto com ele."""
    pecas = [(sh, _absoluta(sh._element)) for sh, _ in _shapes(slide.shapes) if sh.shape_type != 6]
    pecas = [(sh, b) for sh, b in pecas if b]
    texto = {id(sh): ' '.join(_texto(sh).split()) for sh, _ in pecas}
    rot = next((b for sh, b in pecas if texto[id(sh)] == 'RENTABILIDADE'), None)
    cnpj = next((b for sh, b in pecas if re.fullmatch(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto[id(sh)])), None)
    if not rot or not cnpj:
        return None
    L, R = rot[0], cnpj[2]
    caixas = [(sh, b) for sh, b in pecas
              if sh.shape_type == 1 and re.match(r'(12M|ANO|M[ÊE]S|IN[ÍI]CIO)\b', texto[id(sh)])]
    if len(caixas) < 2:
        return None
    caixas.sort(key=lambda a: (a[1][0], a[1][1]))
    esq = caixas[0]
    col = sorted(caixas[1:], key=lambda a: a[1][1])
    G = (col[1][1][1] - col[0][1][3]) if len(col) > 1 else 12700 * 12
    G = max(12700 * 8, min(G, 12700 * 16))
    mudou = {}

    def poe(sh, x, y, w, h):
        _posiciona(sh, x, y, w, h)
        mudou[id(sh)] = (x, y, x + w, y + h)

    # cabeçalho: o nome do fundo começa na margem
    cab = [(sh, b) for sh, b in pecas if b[3] <= rot[1] and b[2] <= cnpj[0] and b[0] < R / 2]
    if cab:
        dx = L - min(b[0] for _, b in cab)
        for sh, b in cab:
            poe(sh, b[0] + dx, b[1], b[2] - b[0], b[3] - b[1])
    # linha de rentabilidade
    we, wc = esq[1][2] - esq[1][0], col[0][1][2] - col[0][1][0]
    novo_we = (R - L - G) * we / (we + wc)
    poe(esq[0], L, esq[1][1], novo_we, esq[1][3] - esq[1][1])
    xc = L + novo_we + G
    for sh, b in col:
        poe(sh, xc, b[1], R - xc, b[3] - b[1])
    fundo_a = max(b[3] for _, b in caixas)
    for sh, b in pecas:                               # nota "*Benchmark: …" embaixo
        if texto[id(sh)].startswith('*Benchmark') and abs(b[1] - fundo_a) < 12700 * 20:
            poe(sh, L, b[1], b[2] - b[0], b[3] - b[1])
            fundo_a = max(fundo_a, b[3])
    # cartões de baixo (dentro da antiga moldura escura)
    moldura = next((b for sh, b in pecas if not texto[id(sh)] and sh.shape_type == 1
                    and (b[2] - b[0]) > (R - L) * 0.8 and b[1] > esq[1][3] - 12700 * 5), None)
    if not moldura:
        return L, R, G
    cartoes = sorted([(sh, b) for sh, b in pecas if sh.shape_type == 1 and texto[id(sh)]
                      and b[0] >= moldura[0] and b[2] <= moldura[2] and b[1] >= moldura[1]
                      and b[3] <= moldura[3] and (b[3] - b[1]) > 12700 * 60],
                     key=lambda a: a[1][0])
    if not cartoes:
        return L, R, G
    soma = sum(b[2] - b[0] for _, b in cartoes)
    livre = R - L - G * (len(cartoes) - 1)
    y0 = fundo_a + G
    x = L
    novos = []
    for sh, b in cartoes:
        w = (b[2] - b[0]) * livre / soma
        novos.append((b, x, w))
        poe(sh, x, y0, w, b[3] - b[1])
        # texto do próprio cartão quebra igual ao modelo: a largura a mais vira
        # recuo à direita
        if sh.has_text_frame:
            tf = sh.text_frame
            tf.margin_right = int((tf.margin_right or 91440) + max(0, w - (b[2] - b[0])))
        x += w + G
    ids = {id(sh) for sh, _ in cartoes}
    for sh, b in pecas:                               # conteúdo de cada cartão
        if id(sh) in ids or id(sh) in mudou or b == moldura:
            continue
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        for ob, nx, nw in novos:
            if ob[0] <= cx <= ob[2] and ob[1] <= cy <= ob[3]:
                s = nw / (ob[2] - ob[0])
                dy = y0 - ob[1]
                poe(sh, nx + (b[0] - ob[0]) * s, b[1] + dy, (b[2] - b[0]) * s, b[3] - b[1])
                break
    return L, R, G


def _fundo_do_slide(slide, stops, ang):
    """Gradiente no fundo do próprio slide (p:bg): fica embaixo do layout, então
    o logo e os filetes do layout continuam aparecendo."""
    csld = slide._element.find(f'{P}cSld')
    velho = csld.find(f'{P}bg')
    if velho is not None:
        csld.remove(velho)
    bg = etree.Element(f'{P}bg')
    pr = etree.SubElement(bg, f'{P}bgPr')
    pr.append(_gradiente(stops, ang=ang))
    etree.SubElement(pr, f'{A}effectLst')
    csld.insert(0, bg)


def _em_colunas(sh, n, x, y, w, h, vao):
    """Divide a caixa de texto em `n` caixas lado a lado, com itens inteiros em
    cada uma (a coluna do PowerPoint quebraria um item no meio)."""
    pars = [p for p in sh.text_frame.paragraphs if ''.join(r.text for r in p.runs).strip()]
    if not pars:
        return
    por = -(-len(pars) // n)
    grupos = [pars[i:i + por] for i in range(0, len(pars), por)]
    wc = (w - vao * (len(grupos) - 1)) / len(grupos)
    original = copy.deepcopy(sh._element)          # cópias saem do texto inteiro
    ids = [int(e.get('id')) for e in sh._element.getroottree().iter(f'{P}cNvPr') if e.get('id', '').isdigit()]
    prox = max(ids or [0]) + 1
    base_el = sh._element
    for i, grupo in enumerate(grupos):
        if i == 0:
            alvo = sh
        else:
            el = copy.deepcopy(original)
            el.find(f'.//{P}cNvPr').set('id', str(prox))
            prox += 1
            base_el.addnext(el)
            base_el = el
            alvo = type(sh)(el, sh._parent)
        txb = alvo.text_frame._txBody
        manter = {''.join(r.text for r in p.runs) for p in grupo}
        for p in list(alvo.text_frame.paragraphs):
            if ''.join(r.text for r in p.runs) not in manter:
                txb.remove(p._p)
        bp = txb.find(f'{A}bodyPr')
        for k in ('lIns', 'rIns', 'tIns', 'bIns'):
            bp.set(k, '0')
        _posiciona(alvo, x + i * (wc + vao), y, wc, h)


def _reflui_post(slide, grade, ctx=None):
    """Disposição do slide de fundo no estilo post:
         RENTABILIDADE
         [12M] [ANO / MÊS]                       | Por que o …? |
         [Alocação] [Carrego] [Duration]         |  (painel)    |
         [CARACTERÍSTICAS GERAIS em colunas]     |              |
    Tudo na grade L..R com o vão G; o painel tem o alto da grade."""
    if not grade:
        return
    L, R, G = grade
    prs = slide.part.package.presentation_part.presentation
    W, H = prs.slide_width, prs.slide_height
    pt = 12700
    pecas = [(sh, _absoluta(sh._element)) for sh, _ in _shapes(slide.shapes)
             if sh.shape_type != 6 and not sh.name.startswith('post ')]
    pecas = [(sh, b) for sh, b in pecas if b]
    tx = {id(sh): ' '.join(_texto(sh).split()) for sh, _ in pecas}

    def um(cond):
        return next(((sh, b) for sh, b in pecas if cond(sh, b)), (None, None))

    rot, brot = um(lambda sh, b: tx[id(sh)] == 'RENTABILIDADE')
    painel, bpai = um(lambda sh, b: sh.shape_type in (1, 17) and (b[3] - b[1]) > H * 0.8 and b[0] > W * 0.6)
    if rot is None or painel is None:
        return
    caixas = [(sh, b) for sh, b in pecas
              if sh.shape_type == 1 and re.match(r'(12M|ANO|M[ÊE]S|IN[ÍI]CIO)\b', tx[id(sh)])]
    cartoes = [(sh, b) for sh, b in pecas if sh.shape_type == 1 and
               re.match(r'(Aloca[çc][ãa]o de cr[ée]dito|Carrego|Duration)', tx[id(sh)])]
    if not caixas or not cartoes:
        return
    ya0 = min(b[1] for _, b in caixas)
    ya1 = max(b[3] for _, b in caixas)
    yb0 = min(b[1] for _, b in cartoes)
    yb1 = max(b[3] for _, b in cartoes)
    # alvos
    Y_ROT, Y_A, BASE = 64 * pt, 88 * pt, 508 * pt
    # linha da rentabilidade mais baixa (sobra para as características), menos
    # quando ANO/MÊS têm três linhas (retorno + Alfa)
    HA = 120 * pt
    HB = yb1 - yb0                      # cartões na altura do modelo (o texto deles não encolhe)
    dyA = Y_A - ya0
    nota = [(sh, b) for sh, b in pecas if tx[id(sh)].startswith('*Benchmark')]
    fim_a = Y_A + HA + (12 * pt if nota else 0)
    Y_B = fim_a + G
    Y_C = Y_B + HB + G
    sy = HB / (yb1 - yb0)
    ids_cart = {id(sh) for sh, _ in cartoes}
    mexidos = set()

    def poe(sh, x, y, w, h):
        _posiciona(sh, x, y, w, h)
        mexidos.add(id(sh))

    # título da seção e data base na mesma linha
    poe(rot, brot[0], Y_ROT, brot[2] - brot[0], brot[3] - brot[1])
    base, bb = um(lambda sh, b: tx[id(sh)].startswith('Data base') or tx[id(sh)].startswith('Database'))
    if base is not None:
        # data base no canto inferior esquerdo, embaixo do filete do rodapé
        w = bb[2] - bb[0]
        poe(base, L, H - 17 * pt, w, bb[3] - bb[1])
        for p in base.text_frame.paragraphs:
            p.alignment = 1                                 # esquerda
    # linha A: o quadro grande com a altura HA; a coluna ANO/MÊS dividida nela
    esq = min(caixas, key=lambda a: a[1][0])
    col = sorted([c for c in caixas if c is not esq], key=lambda a: a[1][1])
    poe(esq[0], esq[1][0], Y_A, esq[1][2] - esq[1][0], HA)
    hc = (HA - G * (len(col) - 1)) / max(1, len(col))
    from pptx.enum.text import MSO_ANCHOR
    for i, (sh, b) in enumerate(col):
        poe(sh, b[0], Y_A + i * (hc + G), b[2] - b[0], hc)
        # ANO/MÊS com três linhas (retorno + Alfa) cabem sem a margem interna
        tf = sh.text_frame
        tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for sh, b in nota:
        poe(sh, b[0], Y_A + HA + 2 * pt, b[2] - b[0], b[3] - b[1])
    for sh, b in nota:
        mexidos.add(id(sh))
    # linha B: cartões com a altura nova; o conteúdo acompanha, comprimido no mesmo fator
    for sh, b in cartoes:
        poe(sh, b[0], Y_B, b[2] - b[0], HB)
    for sh, b in pecas:
        if id(sh) in mexidos or id(sh) in ids_cart:
            continue
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        if L - pt <= cx <= R + pt and yb0 <= cy <= yb1:
            h = b[3] - b[1]
            ny = Y_B + ((b[1] + b[3]) / 2 - yb0) * sy - h / 2
            poe(sh, b[0], ny, b[2] - b[0], h)
    # linha C: características gerais, num quadro de vidro com colunas
    titc, btc = um(lambda sh, b: _sem_acento(tx[id(sh)]) == 'CARACTERISTICAS GERAIS')
    lista, bl = um(lambda sh, b: b[0] >= bpai[0] and tx[id(sh)].startswith('Aplica'))
    extras = sorted([(sh, b) for sh, b in pecas if b[0] >= bpai[0] and sh.shape_type == 17 and
                     re.match(r'(P[úu]blico|PL m[ée]dio)', tx[id(sh)])], key=lambda a: a[1][1])
    if titc is not None and lista is not None:
        from pptx.enum.shapes import MSO_SHAPE
        quadro = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, int(L), int(Y_C), int(R - L), int(BASE - Y_C))
        quadro.name = 'post caracteristicas'
        _pinta(quadro._element, _gradiente(VIDRO, ang=28), _linha('FFFFFF', 26), raio_pt=10)
        quadro.shadow.inherit = False
        # fica atrás dos textos
        arvore = slide.shapes._spTree
        arvore.remove(quadro._element)
        ultimo = [el for el in arvore if el.find(f'.//{P}cNvPr') is not None and
                  (el.find(f'.//{P}cNvPr').get('name') or '').startswith('post ')]
        (ultimo[-1] if ultimo else arvore[1]).addnext(quadro._element)
        pad = 14 * pt
        poe(titc, L + pad, Y_C + 8 * pt, btc[2] - btc[0], btc[3] - btc[1])
        topo = Y_C + 8 * pt + (btc[3] - btc[1]) + 4 * pt
        larg_l = (R - L - 2 * pad) * 0.72
        _em_colunas(lista, 2, L + pad, topo, larg_l, BASE - topo - 6 * pt, 16 * pt)
        mexidos.add(id(lista))
        xe = L + pad + larg_l + pad
        y = topo
        if ctx is not None and ctx.pl:
            for sh, b in extras:
                for par in list(sh.text_frame.paragraphs):
                    t = ''.join(r.text for r in par.runs).strip()
                    if re.match(r'PL\b', t) and len(sh.text_frame.paragraphs) > 1:
                        sh.text_frame._txBody.remove(par._p)
        # Público-alvo, Gestor, Data de início: numa caixa só, espaçamento uniforme
        if extras:
            prim = extras[0][0]
            for sh, b in extras[1:]:
                for par in list(sh.text_frame.paragraphs):
                    if ''.join(r.text for r in par.runs).strip():
                        prim.text_frame._txBody.append(copy.deepcopy(par._p))
                _remove_elemento(sh._element)
                mexidos.add(id(sh))
            for par in list(prim.text_frame.paragraphs):
                if not ''.join(r.text for r in par.runs).strip() and len(prim.text_frame.paragraphs) > 1:
                    prim.text_frame._txBody.remove(par._p)
            prim.text_frame.margin_top = prim.text_frame.margin_bottom = 0
            poe(prim, xe, y, R - pad - xe, BASE - y - 8 * pt)
    # painel: mesmo alto da grade (do topo da rentabilidade ao fim das características);
    # alguns modelos têm duas camadas (foto + véu), as duas descem
    x0 = R + G
    for sh, b in pecas:
        if sh.shape_type in (1, 17) and (b[3] - b[1]) > H * 0.8 and b[0] > W * 0.6:
            poe(sh, x0, Y_A, W - 10 * pt - x0, BASE - Y_A)
    # conteúdo do painel ("Por que o …?" e os tópicos), centrado na vertical
    resto = [(sh, b) for sh, b in pecas if id(sh) not in mexidos and sh is not painel
             and b[0] >= bpai[0] - pt and b[3] <= (btc[1] if titc is not None else bpai[3])]
    resto = [(sh, b) for sh, b in resto if tx[id(sh)]]
    if resto:
        t0 = min(b[1] for _, b in resto)
        t1 = max(b[3] for _, b in resto)
        tem_pl = ctx is not None and ctx.pl
        alto_pl = 74 * pt if tem_pl else 0
        vao_pl = 18 * pt if tem_pl else 0
        bloco = (t1 - t0) + vao_pl + alto_pl
        dy = Y_A + ((BASE - Y_A) - bloco) / 2 - t0
        xi, wi = x0 + 16 * pt, W - 10 * pt - x0 - 32 * pt
        for sh, b in resto:
            poe(sh, xi, b[1] + dy, min(b[2] - b[0], wi), b[3] - b[1])
        if tem_pl:
            _destaque_pl(slide, ctx, xi, t1 + dy + vao_pl, wi, alto_pl)


def _destaque_pl(slide, ctx, x, y, w, h):
    """PL e PL médio em destaque embaixo dos porquês: cartão de vidro com os
    dois valores grandes, como a linha de PL dos posts."""
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.dml.color import RGBColor
    from pptx.util import Pt
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, int(x), int(y), int(w), int(h))
    card.name = 'post pl'
    _pinta(card._element, _gradiente(VIDRO, ang=28), _linha('FFFFFF', 26), raio_pt=8)
    card.shadow.inherit = False
    itens = [('PATRIMÔNIO LÍQUIDO', ctx.pl), ('PL MÉDIO (12M)', ctx.pl_medio)]
    itens = [(r, v) for r, v in itens if v]
    pad = 10 * 12700
    wc = w - pad * 2
    for i, (rotulo, v) in enumerate(itens):
        cx = x + pad
        y0 = 9 + i * 32                                   # um embaixo do outro, valor por extenso
        for texto, corpo, negrito, cor, dy in ((rotulo, 7.5, True, 'C8D7E0', y0), (fmt.brl(v), 12.5, True, 'FFFFFF', y0 + 10)):
            tb = slide.shapes.add_textbox(int(cx), int(y + dy * 12700), int(wc), int(18 * 12700))
            tb.name = 'post pl texto'
            tf = tb.text_frame
            tf.word_wrap = False
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            r = tf.paragraphs[0].add_run()
            r.text = texto
            r.font.name = 'Versos'
            r.font.size = Pt(corpo)
            r.font.bold = negrito
            r.font.color.rgb = RGBColor.from_string(cor)
            if corpo < 8:
                r._r.get_or_add_rPr().set('spc', '120')       # rótulo espaçado, como nos posts


def _estilo_post(slide, ctx=None):
    prs = slide.part.package.presentation_part.presentation
    W = prs.slide_width
    grade = _alinha_post(slide)
    _fundo_post(slide)
    _reflui_post(slide, grade, ctx)
    for sh, _ in list(_shapes(slide.shapes)):
        if sh.shape_type == 6 or sh.name.startswith('post '):
            continue
        el = sh._element
        if el.tag != f'{P}sp':
            continue
        b = _absoluta(el)
        if not b:
            continue
        w, h = b[2] - b[0], b[3] - b[1]
        t = ' '.join(_texto(sh).split())
        sppr = el.find(f'{P}spPr')
        x = etree.tostring(sppr).decode() if sppr is not None else ''
        foto = 'blipFill' in x
        # painel lateral com foto ("Por que o …"): vira um painel de vidro
        if foto and h > prs.slide_height * 0.6 and b[0] > W * 0.6 and grade:
            _pinta(el, _gradiente(VIDRO_FORTE, ang=28), _linha('FFFFFF', 26), raio_pt=14)
            continue
        # cartões com foto (comparativo de fundos): cartão de vidro
        if foto and h > prs.slide_height * 0.5 and not t:
            _pinta(el, _gradiente(VIDRO, ang=28), _linha('FFFFFF', 26), raio_pt=12)
            continue
        # quadros (com contorno) e a moldura de fundo dos cartões
        tem_linha = '<a:ln' in x and 'noFill' not in x.split('<a:ln', 1)[1][:200]
        caixa_texto = sh.shape_type == 17
        if not caixa_texto and w > 12700 * 60 and h > 12700 * 40 and (tem_linha or 'solidFill' in x):
            if not t and 'solidFill' in x and w > W * 0.5:
                _pinta(el, _a('noFill'), _linha())          # moldura escura atrás dos cartões
            else:
                _pinta(el, _gradiente(VIDRO, ang=28), _linha('FFFFFF', 26), raio_pt=10)
            continue
        # CNPJ (caixinha preenchida no cabeçalho) vira pílula de vidro
        if re.fullmatch(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', t) and 'solidFill' in x:
            _pinta(el, _gradiente(VIDRO, ang=28), _linha('FFFFFF', 30), raio_pt=40)
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    from pptx.dml.color import RGBColor
                    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)


# ------------------------------------------------------------------ geral
def exportar_decks(contextos, cadastro, edicao, destino, log, so=None, pdf=True):
    from pptx import Presentation
    from exporters.previdencia import _pdf_powerpoint, instalar_versos
    instalar_versos(log)
    feitos = 0
    for d in carregar_config():
        if so and d['nome'] not in so:
            continue
        modelo = os.path.join(RAIZ, 'templates', 'decks', d['modelo'])
        if not os.path.exists(modelo):
            log.aviso('decks', f'modelo não encontrado: {d["modelo"]}')
            continue
        prs = Presentation(modelo)
        pre = Preenchedor(edicao, contextos, cadastro, log)
        con = Conecta(pre)
        remover = set(d.get('remover') or [])
        # slide -> fundo (e opções) quando o título não diz de quem é o slide
        por_slide = {int(n): (v if isinstance(v, dict) else {'fundo': v})
                     for n, v in (d.get('slides') or {}).items()}
        largura = prs.slide_width
        for i, slide in enumerate(list(prs.slides)):
            opc = por_slide.get(i + 1) or {}
            k = opc.get('fundo') or pre.fundo_do_slide(slide)
            if 'altlight' in remover and k == 'altlight':
                _remove_slide(prs, slide)
                continue
            if 'altlight' in remover:
                al = pre.ctx.get('altlight')
                marcas = ['Previdência'] + ([str(al.f.cnpj)] if al is not None and al.f.cnpj else [])
                _remove_cartao(slide, marcas)
            ctx = pre.ctx.get(k) if k else None
            pre._n = i + 1
            if 'selo_xp' in remover:
                _remove_selo_xp(slide)
            if 'roa' in remover:
                _remove_roa(slide)
            for sh, _ in list(_shapes(slide.shapes)):
                if getattr(sh, 'has_text_frame', False) and sh.has_text_frame:
                    for p in sh.text_frame.paragraphs:
                        pre.paragrafo(p, ctx, capa=(i == 0))
                    pre.forma(sh, ctx)
            pre.pares_cdi_mais(slide, ctx)
            pre.alocacao(slide, ctx)
            pre.grafico(slide, ctx, largura)
            con.tabelas(slide, ctx)
            con.pl_rotulado(slide, ctx)
            con.graficos(slide, ctx, largura)
            if opc.get('alocacao_hghy'):
                con.hghy(slide, ctx)
            for velho, novo in (opc.get('textos') or {}).items():
                _troca_texto(slide, velho, novo)
            if opc.get('estilo') == 'post':
                _estilo_post(slide, ctx)
        pasta = os.path.join(destino, d.get('pasta', ''))
        os.makedirs(pasta, exist_ok=True)
        base = f'{d["nome"]} - {fmt.MESES[edicao.db.month - 1]} {edicao.db.year}'
        pptx = os.path.join(pasta, base + '.pptx')
        prs.save(pptx)
        log.gerado(pptx, 'pptx')
        arq_pdf = os.path.join(pasta, base + '.pdf')
        if pdf and _pdf_powerpoint(os.path.abspath(pptx), os.path.abspath(arq_pdf), log):
            log.gerado(arq_pdf, 'pdf')
        log.info(f'  deck {d["nome"]}: {pre.trocas} trocas')
        feitos += 1
    return feitos
