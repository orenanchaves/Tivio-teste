# -*- coding: utf-8 -*-
"""Páginas "Saiba mais sobre o fundo" (previdência): HGD30 e HYD60.

Uma página por entrada de `configs/previdencia.yml`, no design system da Central
(casca escura, Versos, tokens de _marca.css). Os números saem do Contexto do
fundo FIFE de cada uma (configs/fundos.yml): rentabilidade, alocação HG/HY/
Caixa, setores, rating, composição, histórico, PL, duration e carrego. O texto
do gestor vem de `entrada/comentarios.md`, com os números das frases-padrão
trocados pelos da tabela (engine/sincroniza.py), como no comentário do
relatório.

Saída: saida/AAAA-MM/central/tivio-<chave>-saiba-mais.html
"""
import html as _html
import json
import os
import re

import yaml

from calculators import formatos as fmt

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TITULOS = {
    'texto': 'Início',
    'kpis': None,
    'rentabilidade': 'Rentabilidade',
    'alocacao_real': 'Alocação da Carteira',
    'previsao_alocacao': 'Alocação da Carteira',
    'setorial': 'Exposição Setorial',
    'rating': 'Rating',
    'composicao': 'Composição da Carteira',
    'historico': 'Rentabilidade Histórica',
    'beneficios': 'Benefícios',
    'caracteristicas': 'Características do Fundo',
}


def carregar_config(caminho=None):
    caminho = caminho or os.path.join(RAIZ, 'configs', 'previdencia.yml')
    if not os.path.exists(caminho):
        return {}
    with open(caminho, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def carregar_textos(caminho=None):
    """entrada/previdencia.md -> {chave: texto markdown}."""
    caminho = caminho or os.path.join(RAIZ, 'entrada', 'previdencia.md')
    if not os.path.exists(caminho):
        return {}
    txt = open(caminho, encoding='utf-8').read()
    txt = re.sub(r'<!--.*?-->', '', txt, flags=re.S)
    partes = re.split(r'^##\s+(\S+)\s*$', txt, flags=re.M)
    return {partes[i].strip().lower(): partes[i + 1].strip()
            for i in range(1, len(partes) - 1, 2)}


TITULO_MERCADO = re.compile(r'Vis[ãa]o de Mercado\s*\|\s*[A-Za-zÀ-ú]+', re.I)
TITULO_DESTAQUES = re.compile(r'Destaques da atua[çc][ãa]o da gest[ãa]o em\s+[A-Za-zÀ-ú]+', re.I)


def html_para_markdown(texto):
    """Texto colado de editor de texto rico (site, e-mail) vira Markdown simples.

    <strong>/<b> viram **negrito**, <br>/<p>/<li> viram quebra de parágrafo, o
    resto das tags sai e as entidades (&amp;, &nbsp;) voltam a ser caracteres.
    Texto sem HTML passa intacto.
    """
    if '<' not in (texto or ''):
        return texto
    t = re.sub(r'<\s*(strong|b)\b[^>]*>', '**', texto, flags=re.I)
    t = re.sub(r'<\s*/\s*(strong|b)\s*>', '**', t, flags=re.I)
    t = re.sub(r'<\s*li\b[^>]*>', '\n\n- ', t, flags=re.I)
    t = re.sub(r'<\s*(br|/p|p|/li|/ul|ul|/div|div)\b[^>]*>', '\n\n', t, flags=re.I)
    t = re.sub(r'<[^>]+>', '', t)
    t = _html.unescape(t).replace('\xa0', ' ')
    t = re.sub(r'\*\*(\s*)\*\*', r'\1', t)            # dois negritos seguidos: fica o espaço
    # espaço dentro do negrito vai para fora ("de** CDI**" -> "de **CDI**")
    t = re.sub(r'\*\*(.+?)\*\*', lambda m: (' ' if m.group(1)[:1].isspace() else '') + '**' + m.group(1).strip() + '**'
               + (' ' if m.group(1)[-1:].isspace() else ''), t)
    t = re.sub(r'[ \t]+', ' ', t)
    return '\n\n'.join(x.strip() for x in re.split(r'\n\s*\n', t) if x.strip())


def _secoes_proprias(texto):
    """Separa o texto do fundo em (título do mercado, mercado, título dos
    destaques, destaques), pelos títulos "Visão de Mercado | <mês>" e
    "Destaques da atuação da gestão em <mês>", mesmo colados no meio do
    parágrafo. Sem "Visão de Mercado", tudo antes dos Destaques é o mercado.
    O que vem antes do "Visão de Mercado" (texto de outro mês esquecido) sai.
    Sem nenhum dos dois títulos: (None, None, None, texto)."""
    m = TITULO_MERCADO.search(texto)
    d = TITULO_DESTAQUES.search(texto, m.end() if m else 0)
    if not m and not d:
        return None, None, None, texto
    limpa = lambda x: x.strip(' *\n:|')
    ini = m.end() if m else 0
    mercado = limpa(texto[ini:d.start() if d else len(texto)])
    destaques = limpa(texto[d.end():]) if d else ''
    descartado = limpa(texto[:m.start()]) if m else ''
    return (limpa(m.group(0)) if m else None, mercado or None,
            limpa(d.group(0)) if d else None, destaques, descartado)[:4] + (descartado,)


def _paragrafos(t):
    return [p.strip() for p in re.split(r'\n\s*\n', t or '') if p.strip()]


def _topicos(ps):
    """Cada frase-parágrafo vira tópico (o texto vem de um editor com lista)."""
    return [p if p.startswith(('- ', '**')) else '- ' + p for p in ps]


FRASE_RENT = re.compile(r'apresentou rentabilidade|obteve retorno|acumula retorno', re.I)


def comentario_automatico(chave, pg, por_key, textos, edicao, log=None):
    """O texto do gestor dos fundos de previdência, montado sozinho.

    Ordem: "Sobre o Fundo" (fixo, configs/previdencia.yml) · Visão de Mercado ·
    frase de rentabilidade · Destaques da gestão.

    - Mercado: o que o gestor escreveu na seção do próprio fundo em
      entrada/comentarios.md ("## Tivio HGD30"); sem isso, os parágrafos de
      mercado do fundo de referência (comentario.mercado_de, o Institucional).
    - Frase de rentabilidade: a do gestor, onde ele pôs (os números são
      conferidos pela tabela); se ele não escreveu, a de comentario.frase.
    - Destaques: o que vem depois de "Destaques da atuação da gestão em <mês>"
      (ou, sem títulos, o texto do fundo inteiro).
    Texto colado com HTML é convertido (html_para_markdown).
    """
    cfg = pg.get('comentario') or {}
    proprio = por_key.get(pg.get('fundo') or chave)
    paragrafos = [p.strip() for p in (proprio.comentario if proprio is not None else []) if p.strip()]
    if not paragrafos and textos.get(chave):            # legado: entrada/previdencia.md
        paragrafos = _paragrafos(textos[chave])
    veio_html = any('<' in p for p in paragrafos)
    # texto comum antes de um bloco colado com HTML: o colado é o mais recente
    antigo = []
    if veio_html:
        primeiro = next(i for i, p in enumerate(paragrafos) if '<' in p)
        antigo, paragrafos = paragrafos[:primeiro], paragrafos[primeiro:]
    if antigo and log:
        log.aviso(chave, 'comentário: o texto antes do bloco colado (com HTML) foi ignorado '
                         '(parece de outro mês): ' + antigo[0][:80] + '…')
    bruto = html_para_markdown('\n\n'.join(paragrafos))
    secoes = _secoes_proprias(bruto)
    tit_m, mercado_proprio, tit_d, destaques = secoes[:4]
    descartado = secoes[4] if len(secoes) > 4 else ''
    if descartado and log:
        log.aviso(chave, 'comentário: o texto antes de "Visão de Mercado" foi ignorado '
                         '(parece de outro mês): ' + descartado[:80] + '…')
    if not cfg:
        return '\n\n'.join(_paragrafos(bruto))
    mes = fmt.MESES[edicao.db.month - 1]

    def m(t):
        return str(t).replace('{Mes}', mes).replace('{mes_minusculo}', mes.lower())

    partes = []
    if cfg.get('sobre'):
        partes += ['**Sobre o Fundo**', '\n'.join('- ' + m(x) for x in cfg['sobre'])]

    # mercado
    if mercado_proprio:
        mercado = _paragrafos(mercado_proprio)
        if veio_html:
            mercado = _topicos(mercado)
    else:
        mercado = []
        ref = por_key.get(cfg.get('mercado_de'))
        for p in (ref.comentario if ref is not None else []) or []:
            if re.search(r'Nesse cen[áa]rio', p) or FRASE_RENT.search(p):
                break
            if p.strip():
                mercado.append(p.strip())
    if mercado:
        titulo = tit_m or (m(cfg['titulo_mercado']) if cfg.get('titulo_mercado') else None)
        if titulo:
            partes.append('**' + titulo + '**')
        partes += mercado

    # destaques (o texto do fundo sem títulos conta como destaques)
    if tit_m is None and tit_d is None:
        resto = [p for p in _paragrafos(bruto) if p not in mercado]
    else:
        resto = _paragrafos(destaques)
    if veio_html:
        resto = _topicos(resto)
    tem_frase = any(FRASE_RENT.search(p) for p in resto)
    if cfg.get('frase') and not tem_frase:
        partes.append(m(cfg['frase']))
    if resto:
        titulo = tit_d or (m(cfg['titulo_destaques']) if cfg.get('titulo_destaques') else None)
        if titulo:
            partes.append('**' + titulo + '**')
        partes += resto
    return '\n\n'.join(partes)


def _inline(s):
    s = _html.escape(s, quote=False)
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)


def markdown_simples(texto):
    """**negrito**, '- ' item de lista, linha em branco entre parágrafos.
    Itens seguidos (mesmo separados por linha em branco) viram uma lista só."""
    blocos = [b.strip() for b in re.split(r'\n\s*\n', texto or '') if b.strip()]
    saida, lista = [], []

    def fecha():
        if lista:
            saida.append('<ul>' + ''.join(f'<li>{x}</li>' for x in lista) + '</ul>')
            lista.clear()

    for b in blocos:
        linhas = [l.strip() for l in b.splitlines() if l.strip()]
        if all(l.startswith('- ') for l in linhas):
            lista.extend(_inline(l[2:]) for l in linhas)
            continue
        fecha()
        corpo = _inline(' '.join(linhas))
        # parágrafo que é só um negrito vira subtítulo do bloco
        if re.fullmatch(r'<strong>[^<]+</strong>', corpo):
            saida.append(f'<h3>{corpo[8:-9]}</h3>')
        else:
            saida.append(f'<p>{corpo}</p>')
    fecha()
    return '\n'.join(saida)


def logo_svg(caminho, classe):
    """SVG do fundo pronto para entrar no HTML, nas duas cores de tema.

    Os arquivos de assets/landings/ vêm do Illustrator com <style> e classes
    cls-1, cls-2… Inline no HTML, esse <style> vira CSS da página inteira (e o
    .cls-1 de um logo pintaria o outro). Por isso cada classe vira atributo no
    próprio elemento, e o preto do desenho (sem fill) passa a ser currentColor:
    branco no modo escuro, preto no claro. A cor de destaque (HG, HY) fica a do
    arquivo oficial.
    """
    if not caminho:
        return ''
    caminho = caminho if os.path.isabs(caminho) else os.path.join(RAIZ, caminho)
    if not os.path.exists(caminho):
        return ''
    svg = open(caminho, encoding='utf-8').read()
    svg = re.sub(r'<\?xml[^>]*\?>', '', svg).strip()
    regras = {}
    for m in re.finditer(r'([^{}]+)\{([^}]*)\}', ''.join(re.findall(r'<style>(.*?)</style>', svg, re.S))):
        props = dict((k.strip(), v.strip()) for k, v in
                     (x.split(':', 1) for x in m.group(2).split(';') if ':' in x))
        for sel in m.group(1).split(','):
            regras.setdefault(sel.strip().lstrip('.'), {}).update(props)
    svg = re.sub(r'<defs>.*?</defs>', '', svg, flags=re.S)

    def troca(m):
        attrs = {}
        for c in m.group(1).split():
            attrs.update(regras.get(c, {}))
        return ' '.join(f'{k}="{v}"' for k, v in attrs.items())
    svg = re.sub(r'class="([^"]*)"', troca, svg)
    svg = re.sub(r'<svg\b[^>]*?(viewBox="[^"]*")[^>]*>',
                 lambda m: f'<svg class="{classe}" {m.group(1)} fill="currentColor" '
                           f'role="img" xmlns="http://www.w3.org/2000/svg">', svg, count=1)
    return svg


def _valor_curto(x):
    """R$ 3,8 bilhões / R$ 453,5 milhões — como no cartão da página publicada."""
    if not x:
        return fmt.MINUS
    if abs(x) >= 1e9:
        return f'R$ {fmt.num(x / 1e9, 1)} bilhões'
    return f'R$ {fmt.num(x / 1e6, 1)} milhões'


class RenderizadorLanding:
    def __init__(self, rend_relatorio, edicao, log):
        self.r = rend_relatorio          # reaproveita CSS, marca, disclaimer
        self.edicao = edicao
        self.log = log
        self.cfg = carregar_config()
        self.textos = carregar_textos()

    @property
    def paginas(self):
        return self.cfg.get('paginas') or {}

    @staticmethod
    def arquivo(chave):
        return f'tivio-{chave}-saiba-mais.html'

    # ------------------------------------------------------------- dados
    def _kpis(self, pg, ctx):
        dados = {
            'duration': (ctx.duration_fmt.split(' ')[0],
                         ctx.duration_fmt.split(' ')[1] if ' ' in ctx.duration_fmt else ''),
            'pl_curto': tuple(_valor_curto(ctx.pl).rsplit(' ', 1)) if ctx.pl else (fmt.MINUS, ''),
            'carrego': (f'CDI + {ctx.carrego_fmt}', 'a.a.'),
        }
        saida = []
        for k in pg.get('kpis') or []:
            if k.get('dado'):
                v, u = dados.get(k['dado'], (fmt.MINUS, ''))
            else:
                v, u = str(k.get('valor') or ''), ''
                # "20% do que exceder 100% do CDI": número grande, resto pequeno
                m = re.match(r'^(\S+%|\S+)\s+(.+)$', v) if v and not v.startswith(('R$', 'CDI')) else None
                if m:
                    v, u = m.group(1), m.group(2)
            saida.append({'rotulo': k.get('rotulo', '').replace('{mes_ano}', f'{fmt.MESES[self.edicao.db.month - 1]} {self.edicao.db.year}'), 'valor': v, 'unidade': u,
                          'destaque': not v})
        return saida

    def _rent(self, ctx):
        per = [('mes', 'Mês'), ('inicio', 'Desde o Início')]
        linhas = [('Fundo', 'fundo'), (ctx.benchmark, 'bench'), ('Alfa', 'alfa'),
                  ('%', 'pct'), (f'{ctx.benchmark} +', 'bench_mais')]
        return {'periodos': [p[1] for p in per],
                'linhas': [(rot, [ctx.texto(p, campo) for p, _ in per])
                           for rot, campo in linhas]}

    @staticmethod
    def _barras(itens):
        """[(nome, '12,3%', 12.3)] -> [(nome, rótulo, largura 0-100, é_caixa)]."""
        if not itens:
            return []
        mx = max(v for _, _, v in itens) or 1
        return [(n, r, max(0.8, v / mx * 100), n == 'Caixa') for n, r, v in itens]

    def _caracteristicas(self, pg, ctx):
        mapa = {
            'nome': ('Nome', pg.get('nome_caracteristicas') or pg.get('nome')),
            'cnpj': ('CNPJ', pg.get('cnpj')),
            'inicio': ('Data de início do fundo', pg.get('data_inicio') or (
                f'{ctx.data_inicio:%d/%m/%Y}' if ctx.data_inicio is not None
                and str(ctx.data_inicio) != 'NaT' else None)),
            'pl': ('Patrimônio líquido', ctx.pl_fmt.split(',')[0] if ctx.pl else None),
            'pl_medio': ('PL médio (12M)', ctx.pl_medio_fmt.split(',')[0] if ctx.pl_medio else None),
            'publico': ('Público alvo', pg.get('publico')),
            'taxas': ('Taxas', pg.get('taxas')),
        }
        return [mapa[c] for c in pg.get('caracteristicas') or ['nome', 'cnpj']
                if c in mapa and mapa[c][1]]

    def _ec(self, ctx, previsao):
        """Dados dos gráficos ECharts da página: [nome, valor, rótulo]."""
        def lista(itens):
            return [[n, round(float(v), 4), r] for n, r, v in itens]
        setores = [x for x in ctx.setores_relatorio if x[0] != 'Caixa'] + \
                  [x for x in ctx.setores_relatorio if x[0] == 'Caixa']
        aloc = ctx.alocacao_hghy
        hg = next((r for n, r, _ in aloc if 'High Grade' in n), '')
        comp = ctx.composicao()
        maior = max(comp, key=lambda x: x[2]) if comp else None
        return {
            'alocacao': {'tipo': 'meia', 'itens': lista(aloc), 'centro': hg, 'sub': 'HIGH GRADE'},
            'previsao': {'tipo': 'meia', 'itens': lista(aloc), 'centro': hg, 'sub': 'HIGH GRADE'},
            # treemap: maior para o menor (o Caixa na posição do seu peso)
            'setorial': {'tipo': 'blocos', 'itens': lista(sorted(ctx.setores_relatorio, key=lambda x: -x[2]))},
            'rating': {'tipo': 'colunas', 'itens': lista(ctx.rating_relatorio)},
            'composicao': {'tipo': 'rosca', 'itens': lista(comp),
                           'centro': maior[1] if maior else '', 'sub': maior[0].upper() if maior else ''},
        }

    def _historico(self, ctx):
        h = ctx.hist or ctx.hist12
        if not h or not h.get('l') or len(h['l']) < 2:
            return None
        meses, f, c = list(h['l']), list(h['f']), list(h['c'])
        ini = ctx.data_inicio
        if f[0] != 0 and ini is not None and str(ini) != 'NaT' and f'{ini:%Y-%m}' < meses[0]:
            meses.insert(0, f'{ini:%Y-%m}'); f.insert(0, 0.0); c.insert(0, 0.0)
        rot = [f'{fmt.MES_ABR[int(m[5:7]) - 1]}/{m[2:4]}' for m in meses]
        return {'l': rot, 'f': f, 'c': c, 'bench': ctx.benchmark}

    # ------------------------------------------------------------- página
    def html(self, chave, ctx, por_key=None):
        pg = self.paginas[chave]
        bruto = comentario_automatico(chave, pg, por_key or {}, self.textos, self.edicao, self.log)
        texto, faltando = ctx.preencher(bruto)
        if not bruto:
            self.log.aviso(chave, 'previdência sem texto do gestor em entrada/comentarios.md')
        for k in faltando:
            self.log.aviso(chave, f'landing: marcador sem valor: {{{k}}}')

        # previsão de alocação (HYD60): o % de cada linha é o da carteira do mês
        aloc = {n: r for n, r, _ in ctx.alocacao_hghy}
        previsao = [dict(a, alocacao=aloc.get(a.get('nome'), a.get('alocacao')))
                    for a in pg.get('previsao_alocacao') or []]
        rating = list(ctx.rating_relatorio)
        if pg.get('rating_extras'):
            rating += ctx.rating_extras()
        secoes = [s for s in pg.get('secoes') or [] if s in TITULOS]
        nav = []
        for s in secoes:
            t = TITULOS[s]
            if t and t not in [n[1] for n in nav]:
                nav.append((s, t))

        tpl = self.r.env.get_template('landing.html')
        return tpl.render(
            chave=chave, pg=pg, ctx=ctx, edicao=self.edicao,
            mes_ref=f'{fmt.MESES[self.edicao.db.month - 1]} de {self.edicao.db.year}',
            secoes=secoes, nav=nav,
            texto_html=markdown_simples(texto),
            kpis=self._kpis(pg, ctx),
            rent=self._rent(ctx),
            alocacao=self._barras(ctx.alocacao_hghy),
            # Caixa no pé da lista, como na página publicada
            setores=self._barras([x for x in ctx.setores_relatorio if x[0] != 'Caixa']
                                 + [x for x in ctx.setores_relatorio if x[0] == 'Caixa']),
            rating=self._barras(rating),
            composicao=self._barras(ctx.composicao()),
            previsao=previsao,
            historico=json.dumps(self._historico(ctx), ensure_ascii=False),
            caracteristicas=self._caracteristicas(pg, ctx),
            disclaimer=self.r.disclaimer,
            marca_path=self.r._marca_path(),
            logo_empilhado=logo_svg((pg.get('logo') or {}).get('empilhado'), 'lp-logo'),
            logo_horizontal=logo_svg((pg.get('logo') or {}).get('horizontal'), 'lp-logo-h'),
            logo_horizontal_hero=logo_svg((pg.get('logo') or {}).get('horizontal'), 'lp-logo'),
            ec=self._ec(ctx, previsao),
            css_marca=self.r.css_marca, css_pagina=self.r.css_pagina,
            echarts_src=self.r.ECHARTS)
