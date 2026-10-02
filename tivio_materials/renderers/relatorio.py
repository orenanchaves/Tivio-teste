# -*- coding: utf-8 -*-
"""Relatório de Gestão — montagem por componentes.

O pedido: "cada relatório deve ser montado através de componentes" e "cada seção
deve poder ser ativada ou desativada sem alterar código". A composição vem de
configs/relatorio.yml; este módulo só a executa.

Um relatório = N páginas; uma página = as seções cujo `pagina` é aquele número,
na ordem do YAML. Desligar uma seção é apagar uma linha do YAML (ou listá-la em
`por_fundo.<fundo>.desligar`) — a página se refaz sozinha, e a numeração
"1 / 4" acompanha, porque é contada depois da composição, não escrita à mão.
"""
import json
import os
import re
import unicodedata

import jinja2
import yaml

from calculators import formatos as fmt
from calculators import grafico

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DISCLAIMER_PADRAO = [
    'Este material é de caráter exclusivamente informativo e não deve ser '
    'considerado como oferta de venda de cotas de fundos de investimento ou de '
    'qualquer ativo. A Tivio Capital não comercializa nem distribui cotas de '
    'fundos de investimento.',
    'Fundos de investimento não contam com garantia do administrador, do gestor, '
    'de qualquer mecanismo de seguro ou do Fundo Garantidor de Créditos — FGC. '
    'A rentabilidade obtida no passado não representa garantia de rentabilidade '
    'futura. A rentabilidade divulgada não é líquida de impostos.',
    'Leia a lâmina de informações essenciais e o regulamento antes de investir. '
    'Para avaliação da performance do fundo de investimento, é recomendável uma '
    'análise de período de, no mínimo, 12 (doze) meses.']


def _slug_logo(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


class RenderizadorRelatorio:
    def __init__(self, edicao, cadastro, manual, log, config=None, spreads=None):
        self.edicao = edicao
        self.cad = cadastro
        self.manual = manual or {}
        self.log = log
        self.spreads = spreads
        cfg_path = config or os.path.join(RAIZ, 'configs', 'relatorio.yml')
        with open(cfg_path, encoding='utf-8') as f:
            self.cfg = yaml.safe_load(f)
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.join(RAIZ, 'templates')),
            autoescape=jinja2.select_autoescape(['html']),
            trim_blocks=True, lstrip_blocks=True)
        self.env.filters['mes_label'] = self._mes_label
        self.css_marca = self._ler_css('_marca.css')
        local = css_fontes_locais()
        if local:
            # As regras do CDN precisam SAIR, não perder por cascata: o navegador
            # casa @font-face por peso exato, então uma regra de peso 300
            # apontando para o CDN continuaria sendo escolhida para o texto de
            # peso 300 — e, sem rede, cairia na fallback. Com as duas presentes o
            # PDF sai metade na fonte certa e metade na errada.
            self.css_marca = re.sub(r'@font-face\{[^}]*Versos[^}]*\}', '', self.css_marca)
            self.css_marca = ('/* fontes de assets/fontes — PDF sem dependência de rede */\n'
                              + local + '\n' + self.css_marca)
            self.fontes_locais = True
        else:
            self.fontes_locais = False
        self.css_relatorio = self._ler_css('relatorio.css')
        self._logos = self._indexar_logos()
        marca = os.path.join(RAIZ, 'assets', 'marca', 'tivio.svg')
        self.marca_svg = open(marca, encoding='utf-8').read() if os.path.exists(marca) else ''
        self.echarts_js, self.charts_js = self._ler_js()

    # ------------------------------------------------------------------ apoio
    @staticmethod
    def _mes_label(comp):
        """'2026-08' -> 'ago/26'."""
        return f'{fmt.MES_ABR[int(comp[5:7]) - 1]}/{comp[2:4]}'

    def _ler_css(self, nome):
        p = os.path.join(RAIZ, 'templates', 'estilos', nome)
        return open(p, encoding='utf-8').read() if os.path.exists(p) else ''

    def _ler_js(self):
        """ECharts e o módulo de gráficos, embutidos no HTML.

        Embutido, e não via <script src> para o CDN: o PDF é gerado sem ninguém
        olhando, e um CDN fora do ar produziria 12 relatórios com o gráfico
        faltando, descobertos depois de publicados. Embutido, o HTML abre e
        desenha sem rede.
        """
        vendor = os.path.join(RAIZ, 'assets', 'vendor', 'echarts.min.js')
        modulo = os.path.join(RAIZ, 'assets', 'relatorio_charts.js')
        ec = open(vendor, encoding='utf-8').read() if os.path.exists(vendor) else ''
        mod = open(modulo, encoding='utf-8').read() if os.path.exists(modulo) else ''
        exp = os.path.join(RAIZ, 'assets', 'relatorio_export.js')
        self.export_js = open(exp, encoding='utf-8').read() if os.path.exists(exp) else ''
        if not ec:
            self.log.aviso('—', 'assets/vendor/echarts.min.js não encontrado — os '
                                'gráficos ficam na versão SVG do servidor '
                                '(corretos, sem interação). Ver assets/vendor/LEIA-ME.md')
        return ec, mod

    def _indexar_logos(self):
        """Mapa slug -> caminho do SVG, nas duas pastas de logo."""
        idx = {}
        base = os.path.join(RAIZ, 'assets', 'logos')
        for vert in os.listdir(base) if os.path.isdir(base) else []:
            d = os.path.join(base, vert)
            if not os.path.isdir(d):
                continue
            for arq in os.listdir(d):
                if not arq.lower().endswith('.svg'):
                    continue
                # "_Banks - Horizontal - Branco.svg" -> banks|horizontal|branco
                idx.setdefault(_slug_logo(os.path.splitext(arq)[0]), os.path.join(d, arq))
        return idx

    @staticmethod
    def _preparar_svg(svg, prefixo):
        """Deixa o SVG exportado do Illustrator utilizável dentro da página.

        Três coisas vêm do exportador e atrapalham:

        1. um `<rect>` em `#Background` **sem fill**, que o SVG pinta de preto —
           sobre a faixa azul do cabeçalho vira um retângulo preto cobrindo o logo;
        2. nenhum `width`/`height` na raiz, só `viewBox` — sem altura explícita o
           SVG inline não ocupa o espaço do contêiner;
        3. classes genéricas (`.cls-1`, `.cls-2`) num `<style>` global — dois logos
           na mesma página disputam a mesma regra e um pinta o outro.
        """
        # 1: fora a chapa de fundo.
        # O exportador do Illustrator põe um retângulo do tamanho do quadro,
        # sem `fill` — e SVG sem fill pinta de preto. Sobre a faixa azul do
        # cabeçalho isso vira um bloco preto cobrindo o logo. O marcador varia:
        # às vezes é `<g id="Background">`, às vezes o id está no próprio <svg>
        # e o retângulo é filho direto. Então o critério não é o nome do grupo,
        # é a forma: retângulo do tamanho do viewBox e sem cor própria.
        svg = re.sub(r'<g id="Background">.*?</g>', '', svg, flags=re.S)
        vb = re.search(r'viewBox="\s*[\d.+-]+\s+[\d.+-]+\s+([\d.]+)\s+([\d.]+)', svg)
        if vb:
            larg, alt = vb.group(1), vb.group(2)

            def chapa(m):
                tag = m.group(0)
                if re.search(r'\b(fill|class|style)\s*=', tag):
                    return tag
                w = re.search(r'\bwidth="([\d.]+)"', tag)
                h = re.search(r'\bheight="([\d.]+)"', tag)
                if w and h and w.group(1) == larg and h.group(1) == alt:
                    return ''
                return tag

            svg = re.sub(r'<rect\b[^>]*/?>', chapa, svg)
        # 2: altura do contêiner. Por CSS, não por atributo: o atributo `width`
        # do SVG é um comprimento, não aceita "auto" — o navegador rejeita e
        # loga um erro por página.
        svg = re.sub(r'<svg\b',
                     '<svg style="height:100%;width:auto;display:block" '
                     'preserveAspectRatio="xMinYMid meet"', svg, count=1)
        # 3: classes com escopo
        classes = set(re.findall(r'\.(cls-[\w-]+)', svg))
        for c in classes:
            svg = svg.replace(f'.{c}', f'.{prefixo}-{c}')
            svg = re.sub(rf'class="{re.escape(c)}"', f'class="{prefixo}-{c}"', svg)
        return svg.replace('<?xml version="1.0" encoding="UTF-8"?>', '').strip()

    # variantes, em ordem de preferência (a faixa do cabeçalho é escura)
    VARIANTES = ['horizontal_branco', 'vertical_branco',
                 'horizontal_preto', 'vertical_preto']

    @staticmethod
    def _casa_logo(chave, alvo):
        """O arquivo é deste fundo, e não de um fundo de nome mais longo?

        "Infra Plus" é prefixo de "Infra Plus CDI": casar por prefixo simples
        põe a marca do Infra Plus CDI no relatório do Infra Plus. O que
        distingue é o que vem logo depois do nome — num arquivo deste fundo,
        só a variante.
        """
        chave = chave.strip('_')
        if not chave.startswith(alvo):
            return None
        resto = chave[len(alvo):].strip('_')
        for i, variante in enumerate(RenderizadorRelatorio.VARIANTES):
            # aceita o sufixo numerado do Crédito Estruturado (…_branco_01)
            if resto == variante or re.fullmatch(rf'{variante}_\d+', resto):
                return i
        return None

    def logo(self, fundo):
        """SVG do fundo, na variante que melhor assenta sobre a faixa escura."""
        alvo = _slug_logo(fundo.cfg.get('logo') or fundo.nome)
        candidatos = []
        for chave, caminho in sorted(self._logos.items()):
            ordem = self._casa_logo(chave, alvo)
            if ordem is not None:
                candidatos.append((ordem, chave, caminho))
        if candidatos:
            candidatos.sort()
            return self._preparar_svg(
                open(candidatos[0][2], encoding='utf-8').read(), fundo.key)
        self.log.aviso(fundo.key, f'logo não encontrado em assets/logos (procurei "{alvo}")')
        return ''

    # ------------------------------------------------------------- composição
    def secoes_do_fundo(self, key):
        desligar = set((self.cfg.get('por_fundo', {}).get(key) or {}).get('desligar', []))
        return [s for s in self.cfg['secoes'] if s['id'] not in desligar]

    def paginas(self, key, ctx):
        """Agrupa as seções em páginas e resolve o par de duas colunas."""
        secoes = self.secoes_do_fundo(key)
        # uma seção sem dado nenhum não deve abrir um bloco vazio no relatório
        vazias = set()
        if not ctx.emissores:
            vazias.add('emissores')
        if not ctx.setores:
            vazias.add('setores')
        if not ctx.rating:
            vazias.add('rating')
        if not ctx.hist12:
            vazias.add('historico')
        if not self.mercado(ctx):
            vazias.add('mercado_credito')
        secoes = [s for s in secoes if s['id'] not in vazias]
        if vazias:
            self.log.aviso(key, 'seções sem dado nesta edição, omitidas: '
                                + ', '.join(sorted(vazias)))

        por_pag = {}
        for s in secoes:
            por_pag.setdefault(int(s.get('pagina', 1)), []).append(dict(s))

        paginas = []
        for numero in sorted(por_pag):
            lista = por_pag[numero]
            par = [s for s in lista if s['id'] in ('emissores', 'setores')]
            for s in lista:
                s['primeiro_do_par'] = bool(par) and s is par[0]
                s['ultimo_do_par'] = bool(par) and s is par[-1]
            paginas.append({'numero': len(paginas) + 1, 'secoes': lista})
        return paginas

    # --------------------------------------------------- ajuste do comentário
    # O comentário do gestor varia muito de tamanho: o do Infra Plus tem 4
    # parágrafos, o do Banks tem 7 e passa de 4.000 caracteres. A folha é fixa
    # (1000x1414) e o CSS corta o que sobra — ou seja, o texto excedente some do
    # relatório sem erro, sem aviso e sem ninguém perceber.
    #
    # Em vez de cortar, o corpo do comentário é dimensionado para caber. A conta
    # é uma estimativa (o navegador é quem decide de verdade), por isso o
    # exportador de PDF confere depois e avisa se ainda assim estourou.
    COMENTARIO_LARGURA = 886     # px úteis dentro da caixa
    COMENTARIO_MIN = 10.5
    COMENTARIO_MAX = 15.5

    @classmethod
    def tamanho_comentario(cls, paragrafos, altura_livre):
        if not paragrafos:
            return cls.COMENTARIO_MAX
        chars = sum(len(p) for p in paragrafos)
        n = len(paragrafos)
        tam = cls.COMENTARIO_MAX
        while tam > cls.COMENTARIO_MIN:
            # ~0,5 em de largura média por caractere nesta fonte
            por_linha = max(20, cls.COMENTARIO_LARGURA / (tam * 0.5))
            linhas = chars / por_linha + n          # +1 linha órfã por parágrafo
            altura = linhas * tam * 1.45 + n * tam * 0.55   # + espaço entre eles
            if altura <= altura_livre:
                break
            tam -= 0.25
        return round(tam, 2)

    # ----------------------------------------------------------------- blocos
    def mercado(self, ctx=None):
        """Tabela setorial ANBIMA — a do mercado em que o fundo opera.

        A planilha traz duas: CDI+ e IPCA+. Não são formatações diferentes do
        mesmo dado, são mercados diferentes, com colunas diferentes. O fundo de
        CDI mostra a primeira; o indexado à inflação, a segunda. Escolher pela
        primeira aba poria no relatório do Infra Plus a tabela do mercado de CDI.

        Se a planilha não existir, cai na aba Mercado_Credito do preenchimento
        manual — a mesma tabela digitada à mão, que existe só para a transição.
        """
        if self.spreads:
            from loaders.spreads import para_fundo
            bench = ctx.benchmark if ctx is not None else 'CDI'
            return para_fundo(self.spreads, bench)
        df = self.manual.get('Mercado_Credito')
        if df is None or not len(df):
            return None
        cab = ['Setor', 'Volume (R$ MM)', '%', 'Spread Atual',
               'Spread mês anterior', 'Variação', 'Duration']
        linhas = []
        for _, r in df.iterrows():
            celulas = [str(r.iloc[c]).strip() for c in range(min(7, len(r)))]
            if not celulas or not celulas[0]:
                continue
            linhas.append({'celulas': celulas,
                           'total': celulas[0].strip().lower() == 'total'})
        if not linhas:
            return None
        return {'cabecalho': cab, 'linhas': linhas,
                'nota': 'Debêntures precificadas pela ANBIMA corrigidas por CDI + spread. '
                        'Desconsideramos as debêntures que começaram a ser precificadas ou '
                        'que venceram ao longo do mês, para que a comparação com o mês '
                        'anterior seja feita com a mesma base de ativos.'}

    def caracteristicas(self, ctx):
        f = ctx.f
        itens = [('Gestor', 'Tivio Capital'),
                 ('Público alvo', f.cfg.get('publico', 'Investidores em geral'))]
        if ctx.benchmark:
            itens.append(('Benchmark', ctx.benchmark))

        # Data de início: a coluna da DePara vem vazia nesta base, então o valor
        # confiável é a primeira cota da série — que é, por definição, quando o
        # fundo começou a ser cotado. Confere com os relatórios publicados
        # (Banks 30/04/2009, Institucional 13/05/2005).
        inicio = None
        if f.resolvido and f.data_inicial is not None and str(f.data_inicial) != 'NaT':
            inicio = f.data_inicial
        elif ctx.data_inicio is not None:
            inicio = ctx.data_inicio
        if inicio is not None:
            itens.append(('Data de início', f'{inicio:%d/%m/%Y}'))
        itens += [('Patrimônio líquido', ctx.pl_fmt),
                  ('Patrimônio líquido médio (12 meses)', ctx.pl_medio_fmt),
                  (self.cad.rotulo_taxa, ctx.taxa or fmt.MINUS),
                  ('Taxa de performance', ctx.perf or fmt.MINUS)]
        if ctx.carrego is not None:
            itens.append(('Carrego da carteira', f'{ctx.benchmark} +{ctx.carrego_fmt}'))
        if ctx.duration is not None:
            itens.append(('Duration média', ctx.duration_fmt))
        return itens

    @staticmethod
    def operacional(fundo):
        rot = {'aplicacao': 'Aplicação', 'resgate': 'Resgate',
               'pagamento_resgate': 'Pagamento do Resgate',
               'aplicacao_minima': 'Aplicação mínima inicial',
               'movimentacao_minima': 'Movimentação mínima'}
        op = fundo.cfg.get('operacional') or {}
        return [(rot.get(k, k), v) for k, v in op.items()]

    # ------------------------------------------------------------- renderiza
    def html(self, ctx):
        f = ctx.f
        titulos = {s['id']: s.get('titulo', s['id']) for s in self.cfg['secoes']}
        paginas = self.paginas(f.key, ctx)

        # setores: o contexto devolve (nome, '12,3%', valor) — a barra usa o valor
        # relativo ao maior setor, não o valor absoluto, senão a maior barra de um
        # fundo concentrado em caixa ocupa a linha toda e as outras desaparecem
        st = ctx.setores
        mx = max((v for _, _, v in st), default=1) or 1
        setores_barras = [(n, txt, round(v / mx * 100)) for n, txt, v in st]

        dados = {
            'f': f, 'c': ctx, 'edicao': self.edicao,
            'paginas': paginas,
            'periodos': ['Mês', 'Ano', '12M', '24M', '36M', 'Desde o início'],
            'linhas': ctx.linhas_rentabilidade,
            'css_marca': self.css_marca, 'css_relatorio': self.css_relatorio,
            'logo_svg': self.logo(f),
            'marca_svg': self.marca_svg,
            'echarts_js': self.echarts_js,
            'charts_js': self.charts_js,
            'export_js': self.export_js,
            'meta_json': json.dumps({
                'fundo': f.nome,
                'arquivo': self.edicao.nome_arquivo(
                    f'{f.nome} - Relatório de Gestão', '').rstrip('.'),
            }, ensure_ascii=False),
            'barras': grafico.barras_horizontais,
            'rating_cols': grafico.colunas_rating,
            'grafico': grafico.linha_historica(ctx.hist12, ctx.benchmark),
            'mercado': self.mercado(ctx),
            'caracteristicas': self.caracteristicas(ctx),
            'operacional': self.operacional(f),
            'disclaimer': DISCLAIMER_PADRAO,
            'arquivo_comentarios': 'entrada/comentarios.md',
            'setores_barras': setores_barras,
        }

        # espaço livre na página do comentário: a folha, menos o cabeçalho fino,
        # menos o gráfico quando ele divide a página, menos as margens
        ids_pagina = {s['id'] for pg in paginas for s in pg['secoes']
                      if any(x['id'] == 'comentario' for x in pg['secoes'])}
        livre = 1414 - 118 - 150
        if 'historico' in ids_pagina:
            livre -= 560
        dados['tamanho_comentario'] = self.tamanho_comentario(
            ctx.comentario_preenchido, livre)
        # o componente de setores lê c.setores_barras; injeta sem mexer no contexto
        ctx.setores_barras = setores_barras

        titulos_por_secao = {}
        for pagina in paginas:
            for s in pagina['secoes']:
                titulos_por_secao[s['id']] = titulos.get(s['id'], s['id'])

        # cada componente recebe seu próprio `titulo`; o include herda o contexto,
        # então o título é resolvido na hora pelo id da seção corrente
        self.env.globals['TITULOS'] = titulos_por_secao
        tpl = self.env.get_template('relatorio.html')
        return tpl.render(**dados, titulos=titulos_por_secao,
                          titulo_de=lambda sid: titulos_por_secao.get(sid, sid))


# ---------------------------------------------------------------------------
# Fontes locais: tornam o PDF reprodutível sem rede.
#
# O @font-face da marca aponta para `local("Versos …")` e, como segunda opção,
# para o CDN. Isso funciona na máquina de quem tem a fonte instalada. Num
# servidor ou container não tem nem uma nem outra, e o Chromium cai para a
# fallback silenciosamente — o PDF sai com outra métrica de texto.
#
# Com os arquivos em assets/fontes/, eles entram no HTML como data URI e a fonte
# viaja dentro do documento.
# ---------------------------------------------------------------------------
import base64   # noqa: E402

PESOS = [('extralight', 200), ('thin', 200), ('light', 300), ('regular', 400),
         ('book', 400), ('medium', 500), ('semibold', 600), ('demibold', 600),
         ('bold', 700), ('black', 900)]
FORMATOS = {'.woff2': 'woff2', '.woff': 'woff', '.ttf': 'truetype', '.otf': 'opentype'}


# pesos que os materiais da marca usam; todos precisam ter uma regra, senão o
# peso sem regra local cai na regra do CDN e, sem rede, na fonte de fallback
PESOS_USADOS = [200, 300, 400, 500, 600, 700]


def css_fontes_locais(pasta=None, familia='Versos'):
    """@font-face com os arquivos de assets/fontes/ embutidos. '' se não houver.

    Todo peso usado pelos materiais recebe uma regra. Para um peso sem arquivo
    próprio, aponta o arquivo de peso mais próximo: é melhor o Chromium engordar
    um Regular do que trocar a família inteira pela fallback — a família errada
    muda a métrica de cada linha, o peso aproximado não.
    """
    pasta = pasta or os.path.join(RAIZ, 'assets', 'fontes')
    if not os.path.isdir(pasta):
        return ''

    arquivos = {}
    for arq in sorted(os.listdir(pasta)):
        ext = os.path.splitext(arq)[1].lower()
        if ext not in FORMATOS:
            continue
        base = os.path.splitext(arq)[0].lower().replace('-', '').replace('_', '')
        peso = next((p for sufixo, p in PESOS if base.endswith(sufixo)), 400)
        with open(os.path.join(pasta, arq), 'rb') as f:
            arquivos[peso] = (base64.b64encode(f.read()).decode('ascii'), FORMATOS[ext])
    if not arquivos:
        return ''

    regras = []
    for peso in PESOS_USADOS:
        mais_proximo = min(arquivos, key=lambda p: (abs(p - peso), p))
        b64, formato = arquivos[mais_proximo]
        regras.append(
            f"@font-face{{font-family:{familia};"
            f"src:url(data:font/{formato};base64,{b64}) format('{formato}');"
            f"font-weight:{peso};font-style:normal;font-display:block}}")
    return '\n'.join(regras)
