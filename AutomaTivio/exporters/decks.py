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
PERIODO = {'12M': '12m', 'ANO': 'ano', 'MÊS': 'mes', 'MES': 'mes', 'DESDE O INÍCIO': 'inicio',
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
        ok |= _troca_grupo(par, r'Data base:\s*(\d{2}/\d{2}/\d{4})', self.ed.br)
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
            # quadros 12M / ANO / MÊS (Crédito Privado)
            m = re.match(r'\s*(12M|ANO|M[ÊE]S|Desde o in[íi]cio)\s*(' + NUM + r')\s*%', t, re.I)
            if m:
                per = PERIODO.get(m.group(1).upper())
                if ctx.f.retorno_absoluto:
                    v = _num((ctx.valor(per, 'fundo') or 0) * 100)
                else:
                    pv = ctx.valor(per, 'pct')
                    v = fmt.num(pv * 100, 0) if pv is not None else None
                ok |= _troca_trecho(par, m.start(2), m.end(2), v) if v else False
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
        for sh, k, extras in rotulos:
            if k in dados:
                _troca_pct([p for s in [sh] + extras for p in s.text_frame.paragraphs], dados[k][1])
        self.trocas += 1
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
        remover = set(d.get('remover') or [])
        largura = prs.slide_width
        for i, slide in enumerate(list(prs.slides)):
            k = pre.fundo_do_slide(slide)
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
