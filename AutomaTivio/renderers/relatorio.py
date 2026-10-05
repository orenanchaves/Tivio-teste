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
from urllib.parse import quote

import jinja2
import yaml

from calculators import formatos as fmt
from calculators import grafico
from engine.contexto import agrupar_tipos

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def carregar_disclaimer(caminho=None):
    """Texto jurídico do rodapé, de configs/disclaimer.md.

    Fora do código de propósito: é texto aprovado por quem responde por ele, e
    muda por decisão jurídica, não por release. Quem precisa alterá-lo não
    deveria ter de abrir um .py.

    O conteúdo atual foi extraído dos relatórios publicados de agosto/2026, onde
    é idêntico nos 12 fundos.
    """
    caminho = caminho or os.path.join(RAIZ, 'configs', 'disclaimer.md')
    if not os.path.exists(caminho):
        return []
    texto = open(caminho, encoding='utf-8').read()
    texto = re.sub(r'<!--.*?-->', '', texto, flags=re.S)   # fora o cabeçalho
    return [p.strip() for p in re.split(r'\n\s*\n', texto) if p.strip()]


DISCLAIMER_PADRAO = carregar_disclaimer()

# Os quatro selos da faixa do rodapé, com a URL oficial como reserva. Ordem e
# textos conferidos contra o relatório publicado.
SELOS = [
    ('qr', 'QR Code Tivio',
     'https://www.tivio.com/wp-content/uploads/sites/1532/2026/08/QR-Code-scaled.png'),
    ('anbima1', 'Selo ANBIMA — Distribuição de Produtos de Investimento',
     'https://www.tivio.com/wp-content/uploads/sites/1532/2026/07/selo-distribuicao.png'),
    ('anbima2', 'Selo ANBIMA — Gestão de Recursos de Terceiros',
     'https://www.tivio.com/wp-content/uploads/sites/1532/2026/07/selo-02-scaled.png'),
    ('pri', 'Signatory of PRI',
     'https://www.tivio.com/wp-content/uploads/sites/1532/2026/08/PRI.png'),
]

MIME = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.svg': 'image/svg+xml', '.webp': 'image/webp'}


def carregar_selos(pasta=None, log=None):
    """{chave: {'src', 'alt', 'local'}} — base64 quando o arquivo existe.

    Base64 e não a URL porque o selo precisa sobreviver à *exportação*: o
    html2canvas só desenha imagem de outro domínio se o servidor mandar
    cabeçalho CORS, e o WordPress não manda. O material original contorna isso
    passando por proxies públicos; se um cair, o selo vira um quadrado vazio no
    JPG e ninguém vê antes de publicar.
    """
    import base64
    pasta = pasta or os.path.join(RAIZ, 'assets', 'selos')
    out, faltando = {}, []
    for chave, alt, url in SELOS:
        achou = None
        if os.path.isdir(pasta):
            for arq in sorted(os.listdir(pasta)):
                base, ext = os.path.splitext(arq.lower())
                if base == chave and ext in MIME:
                    achou = os.path.join(pasta, arq)
                    break
        if achou:
            with open(achou, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('ascii')
            mime = MIME[os.path.splitext(achou)[1].lower()]
            out[chave] = {'src': f'data:{mime};base64,{b64}', 'alt': alt, 'local': True}
        else:
            out[chave] = {'src': url, 'alt': alt, 'local': False}
            faltando.append(chave)
    if faltando and log:
        log.aviso('—', f'selos sem arquivo local em assets/selos ({", ".join(faltando)}) — '
                       f'saem pela URL do site, e podem não aparecer nas exportações. '
                       f'Ver assets/selos/LEIA-ME.md')
    return out


# ---------------------------------------------------------------------------
# COLATERAIS — bloco fixo dos relatórios de Crédito Estruturado: as garantias
# que a estratégia aceita. Igual nos três ALT publicados, na mesma ordem (as
# quatro primeiras em grade 2x2, a última na linha inteira).
COLATERAIS = [
    ('imoveis', 'AF de imóveis'),
    ('automoveis', 'AF de automóveis'),
    ('maquinario', 'AF de maquinário'),
    ('recebiveis', 'CF de recebíveis'),
    ('coobrigacao', 'Coobrigação do cedente/Avais'),
]


def _icone_limpo(svg):
    """SVG do PowerPoint -> SVG que acompanha a cor e o tamanho do bloco.

    O PowerPoint prende as cores numa <style> com classes `MsftOfcThm_…` e
    fixa `width`/`height` em pixel. Sem tratar, o ícone sai cinza #595959 num
    cartão que pode ser claro ou escuro, e com o tamanho do arquivo em vez do
    tamanho do cartão. A classe diz o papel no próprio nome — `…_Fill_v2` ou
    `…_Stroke_v2` —, então dá para traduzir cada uma no atributo certo.
    """
    svg = re.sub(r'<style>.*?</style>', '', svg, flags=re.S)

    def troca(m):
        classes = m.group(1)
        attrs = []
        if 'Fill' in classes:
            attrs.append('fill="currentColor"')
        if 'Stroke' in classes:
            attrs.append('stroke="currentColor"')
        return ' ' + ' '.join(attrs) if attrs else ''

    svg = re.sub(r'\sclass="((?:Msft[^"]*))"', troca, svg)
    # o viewBox é que manda; width/height fixos impediriam o CSS de dimensionar
    svg = re.sub(r'<svg\b([^>]*)>',
                 lambda m: '<svg' + re.sub(r'\s(?:width|height)="[^"]*"', '',
                                           m.group(1)) + ' aria-hidden="true">',
                 svg, count=1)
    return svg


def carregar_icones(pasta=None, log=None):
    """{chave: '<svg…>'} — os ícones de COLATERAIS, embutidos no HTML.

    SVG inline e não <img src>: assim o ícone herda a cor do bloco por
    `currentColor`, sobrevive à exportação em JPG (que não busca arquivo
    externo) e entra no PDF como vetor. Os arquivos saíram do próprio PPTX
    publicado — em assets/icones/colateral-<chave>.svg.
    """
    pasta = pasta or os.path.join(RAIZ, 'assets', 'icones')
    out, faltando = {}, []
    for chave, _ in COLATERAIS:
        caminho = os.path.join(pasta, f'colateral-{chave}.svg')
        if not os.path.exists(caminho):
            out[chave] = ''
            faltando.append(chave)
            continue
        out[chave] = _icone_limpo(open(caminho, encoding='utf-8').read())
    if faltando and log:
        log.aviso('—', f'ícones de colaterais sem arquivo em assets/icones '
                       f'({", ".join(faltando)}) — os cartões saem só com o texto')
    return out


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
        self.selos = carregar_selos(log=log)
        self.icones = carregar_icones(log=log)
        self.css_abas = self._ler_css('abas.css')
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
        # bloco comum da entrega (barra, folha solta, impressão)
        self.css_entrega = self._ler_css('entrega.css')
        # a casca da página por vertical (cabeçalho, hero, rodapé) e as
        # regras de impressão, que os dois formatos compartilham
        self.css_pagina = self._ler_css('pagina.css')
        self.css_impressao = self._ler_css('impressao.css')
        self._logos = self._indexar_logos()
        marca = os.path.join(RAIZ, 'assets', 'marca', 'tivio.svg')
        self.marca_svg = open(marca, encoding='utf-8').read() if os.path.exists(marca) else ''
        # o T sozinho, da caixa preta à direita do cabeçalho (subpaths do tivio.svg)
        simbolo = os.path.join(RAIZ, 'assets', 'marca', 'tivio_t.svg')
        self.t_svg = open(simbolo, encoding='utf-8').read() if os.path.exists(simbolo) else ''
        self.echarts_js, self.charts_js = self._ler_js()

    # ------------------------------------------------------------------ apoio
    @staticmethod
    def _mes_label(comp):
        """'2026-08' -> 'ago/26'."""
        return f'{fmt.MES_ABR[int(comp[5:7]) - 1]}/{comp[2:4]}'

    def _ler_css(self, nome):
        p = os.path.join(RAIZ, 'templates', 'estilos', nome)
        return open(p, encoding='utf-8').read() if os.path.exists(p) else ''

    # ECharts vem da pasta vendor/ ao lado do HTML, com o CDN como reserva — o
    # mesmo arranjo dos materiais da Central.
    #
    # A primeira versão embutia o arquivo inteiro em cada relatório, para o PDF
    # não depender de rede. Funcionava, mas cada relatório pesava 2,3 MB e os 13
    # somavam 31 MB de saída: treze cópias idênticas de 1 MB de JavaScript. O
    # problema que a embutida resolvia — o PDF é gerado sem ninguém olhando —
    # resolve-se melhor abrindo o arquivo gravado por `file://` na hora de
    # imprimir: aí o `vendor/` ao lado resolve sozinho, e o PDF sai do mesmo
    # artefato que a pessoa abre, não de uma cópia em memória.
    ECHARTS = ('vendor/echarts.min.js',
               'https://cdnjs.cloudflare.com/ajax/libs/echarts/5.6.0/echarts.min.js')

    def _ler_js(self):
        """Só o módulo de gráficos é embutido; o ECharts vem de vendor/."""
        modulo = os.path.join(RAIZ, 'assets', 'relatorio_charts.js')
        mod = open(modulo, encoding='utf-8').read() if os.path.exists(modulo) else ''
        exp = os.path.join(RAIZ, 'assets', 'relatorio_export.js')
        self.export_js = open(exp, encoding='utf-8').read() if os.path.exists(exp) else ''
        self.disclaimer = carregar_disclaimer()
        if not self.disclaimer:
            self.log.aviso('—', 'configs/disclaimer.md não encontrado — o relatório '
                                'sai sem o texto jurídico do rodapé')
        if not os.path.exists(os.path.join(RAIZ, 'assets', 'vendor', 'echarts.min.js')):
            self.log.aviso('—', 'assets/vendor/echarts.min.js não encontrado — os '
                                'gráficos ficam na versão SVG do servidor '
                                '(corretos, sem interação). Ver assets/vendor/LEIA-ME.md')
        return '', mod

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
                if not (w and h):
                    return tag
                # tolerância em vez de igualdade: o retângulo de fundo do ALT 180
                # mede 447,59 num quadro de 448,46 — cobre 99,8% e some por
                # 0,87 de diferença se a comparação for exata
                try:
                    cobre = (float(w.group(1)) / float(larg) >= 0.98
                             and float(h.group(1)) / float(alt) >= 0.98)
                except (ValueError, ZeroDivisionError):
                    return tag
                return '' if cobre else tag

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
    # Logo sempre horizontal, como nos relatórios publicados: a horizontal
    # preta vem antes de qualquer vertical (o Tivio Institucional só tem essa).
    VARIANTES = ['horizontal_branco', 'horizontal_preto',
                 'vertical_branco', 'vertical_preto']

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
                # entre as numeradas, a de maior número: no ALT a _03 é a
                # "TIVIO ALT CRÉDITO 180" numa linha só, a do relatório publicado
                num = re.search(r'_(\d+)$', chave)
                candidatos.append((ordem, -int(num.group(1)) if num else 0, chave, caminho))
        if candidatos:
            candidatos.sort()
            svg = self._preparar_svg(
                open(candidatos[0][3], encoding='utf-8').read(), fundo.key)
            if self.VARIANTES[candidatos[0][0]].endswith('preto'):
                # na versão preta o "TIVIO" vem sem cor (= preto) e some no
                # cabeçalho escuro; o que não tem classe herda branco da raiz
                svg = re.sub(r'<svg\b', '<svg fill="#fff"', svg, count=1)
            return svg
        self.log.aviso(fundo.key, f'logo não encontrado em assets/logos (procurei "{alvo}")')
        return ''

    # ------------------------------------------------------------- composição
    def secoes_do_fundo(self, key):
        """Composição do fundo: a da vertical, ajustada pelo que for do fundo.

        A vertical importa porque os relatórios de Crédito Estruturado
        publicados são outro produto, não uma variação — 3 páginas, com
        Alocação por Estratégia, sem emissores, sem rating e sem a tabela de
        Mercado de Crédito.
        """
        fundo = self.cad.get(key)
        vertical = fundo.vertical if fundo else None
        por_vert = (self.cfg.get('por_vertical') or {}).get(vertical) or {}
        secoes = por_vert.get('secoes') or self.cfg['secoes']

        ajuste = (self.cfg.get('por_fundo') or {}).get(key) or {}
        desligar = set(ajuste.get('desligar', [])) | set(por_vert.get('desligar', []))
        return [s for s in secoes if s['id'] not in desligar]

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
        if not ctx.estrategia:
            vazias.add('estrategia')
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
            # a dupla que divide a folha em duas colunas depende da vertical:
            # emissores|setores no high grade, setores|colaterais no ALT. Quem
            # decide é qual par está nesta folha.
            par = []
            for dupla in self.DUPLAS:
                achados = [s for s in lista if s['id'] in dupla]
                if len(achados) == 2:
                    par = achados
                    break
            for s in lista:
                s['primeiro_do_par'] = bool(par) and s is par[0]
                s['ultimo_do_par'] = bool(par) and s is par[-1]
                s['em_dupla'] = s in par
            paginas.append({'numero': len(paginas) + 1, 'secoes': lista})
        return paginas

    # Pares que ocupam meia folha cada, na ordem em que são procurados.
    # O high grade (emissores + rating | setores) é montado no template, porque
    # a coluna da esquerda leva dois blocos.
    DUPLAS = (('setores', 'colaterais'),)

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

    # O disclaimer tem ~3.700 caracteres e a faixa do rodapé é fixa. Mesmo
    # problema do comentário, e mesma solução: dimensionar em vez de cortar.
    # Aqui o espaço é menor e o texto é jurídico — truncar o disclaimer de um
    # material distribuído a investidor não é um defeito de layout.
    DISCLAIMER_LARGURA = 886
    DISCLAIMER_ALTURA = 404      # faixa de 664px menos título, contatos e folgas

    @classmethod
    def tamanho_disclaimer(cls, paragrafos, nota=''):
        chars = sum(len(p) for p in paragrafos) + len(nota or '')
        n = len(paragrafos) + (1 if nota else 0)
        if not chars:
            return 11.7
        altura_livre = cls.DISCLAIMER_ALTURA
        tam = 11.7
        while tam > 6.4:
            por_linha = max(30, cls.DISCLAIMER_LARGURA / (tam * 0.47))
            linhas = chars / por_linha + n
            if linhas * tam * 1.35 + n * tam * 0.4 <= altura_livre:
                break
            tam -= 0.1
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

    # ------------------------------------------------ desenho do publicado
    @staticmethod
    def ve(fundo):
        """'ce' no Crédito Estruturado (acento verde), 'cp' no resto (azul)."""
        return 'ce' if fundo.cfg.get('vertical') == 'credito_estruturado' else 'cp'

    @staticmethod
    def razao_social(fundo):
        """A linha em caixa alta sob o logo: "TIVIO INSTITUCIONAL 30 FIF CLASSE…".

        `razao_social` em configs/fundos.yml manda. Sem ela, sai do nome da
        carteira na DePara, que é a mesma denominação abreviada.
        """
        if fundo.cfg.get('razao_social'):
            return fundo.cfg['razao_social']
        base = re.sub(r'\s*-\s*Expandida\s*$', '', str(fundo.cfg.get('carteira') or fundo.nome),
                      flags=re.I)
        return re.sub(r'\bCI\b', 'CLASSE INVESTIMENTO', base).upper()

    @staticmethod
    def _inicio(ctx):
        f = ctx.f
        if f.resolvido and f.data_inicial is not None and str(f.data_inicial) != 'NaT':
            return f.data_inicial
        return ctx.data_inicio

    def caracteristicas_modelo(self, ctx):
        """As duas colunas de "Características gerais do fundo" do publicado.

        Esquerda: gestor, público, início, taxa, PL. Direita: performance,
        informações operacionais, PL médio. Sem benchmark, carrego e duration,
        que o relatório publicado não traz.
        """
        f = ctx.f
        ve = self.ve(f)
        inicio = self._inicio(ctx)
        esq = [('Gestor', 'Tivio Capital'),
               ('Público Alvo', f.cfg.get('publico', 'Investidores em geral'))]
        if inicio is not None:
            esq.append(('Data de início', f'{inicio:%d/%m/%Y}'))
        # o Estruturado publicado chama de "Taxa de administração e gestão"
        rot_taxa = 'Taxa de administração e gestão' if ve == 'ce' else self.cad.rotulo_taxa
        esq += [(rot_taxa, ctx.taxa or fmt.MINUS),
                ('Patrimônio líquido', ctx.pl_fmt)]
        dir_ = [('Taxa de performance', ctx.perf or fmt.MINUS)]
        # sem `operacional` no fundos.yml o bloco sairia só com o título
        if f.cfg.get('operacional'):
            dir_.append(('Informações Operacionais', None))
        dir_.append(('Patrimônio líquido médio ' + ('(12M)' if ve == 'ce' else '(12 meses)'),
                     ctx.pl_medio_fmt))
        return esq, dir_

    @staticmethod
    def mercado_modelo(m):
        """A tabela de Mercado de Crédito como no publicado: o total numa
        tabelinha própria em cima, e no corpo o % e a duration com uma casa."""
        if not m:
            return m

        def num(txt):
            try:
                return float(str(txt).replace('.', '').replace('%', '').replace(',', '.'))
            except ValueError:
                return None

        def uma_casa(txt, pct):
            v = num(txt)
            if v is None:
                return txt
            return fmt.num(v, 1) + ('%' if pct else '')

        cab = list(m['cabecalho'])
        i_pct = next((i for i, h in enumerate(cab) if h.strip() == '%'), None)
        i_dur = next((i for i, h in enumerate(cab) if h.lower().startswith('duration')), None)
        linhas, resumo = [], None
        for ln in m['linhas']:
            cel = list(ln['celulas'])
            if ln.get('total'):
                if i_pct is not None:
                    v = num(cel[i_pct])
                    if v is not None:
                        cel[i_pct] = fmt.num(v, 0) + '%'
                resumo = cel[1:]
                continue
            if i_pct is not None:
                cel[i_pct] = uma_casa(cel[i_pct], True)
            if i_dur is not None:
                cel[i_dur] = uma_casa(cel[i_dur], False)
            linhas.append(cel)
        # larguras do publicado (tabela CDI, 7 colunas); a do IPCA tem 10 e
        # divide o que sobra do setor em partes iguais
        if len(cab) == 7:
            larg = [270, 150, 60, 92, 155, 68, 68]
        else:
            resto = (863 - 196) / max(1, len(cab) - 1)
            larg = [196] + [round(resto, 1)] * (len(cab) - 1)
        return dict(m, cabecalho=cab, linhas=linhas, resumo=resumo, larguras=larg)

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
        # os títulos vêm da composição DESTE fundo, não da lista padrão: o
        # Crédito Estruturado chama o mesmo bloco de "Alocação Real da Carteira
        # de Crédito", e tem seções que a lista do high grade nem possui
        titulos = {s['id']: s.get('titulo', s['id'])
                   for s in self.secoes_do_fundo(f.key)}
        paginas = self.paginas(f.key, ctx)

        # setores: o contexto devolve (nome, '12,3%', valor) — a barra usa o valor
        # relativo ao maior setor, não o valor absoluto, senão a maior barra de um
        # fundo concentrado em caixa ocupa a linha toda e as outras desaparecem
        st = ctx.setores
        mx = max((v for _, _, v in st), default=1) or 1
        setores_barras = [(n, txt, round(v / mx * 100)) for n, txt, v in st]

        est = ctx.estrategia
        mxe = max((v for _, _, v in est), default=1) or 1
        estrategia_barras = [(n, txt, round(v / mxe * 100)) for n, txt, v in est]

        # "Alocação real da carteira de crédito": no PPTX do ALT é um TREEMAP
        # da coluna 'Tipo aj.' com os nomes do tipo_label — é por isso que ali
        # aparece "Liquidez" e não existe linha "LFSN". Retângulos proporcionais
        # e não barras: é assim que o relatório mostra de relance que metade da
        # carteira é cota sênior de FIDC.
        tipos = agrupar_tipos(ctx.cart['tipos'] if ctx.cart else None,
                              self.cad.tipo_label)
        estrategia_treemap = grafico.treemap(tipos)

        dados = {
            'f': f, 'c': ctx, 'edicao': self.edicao,
            'paginas': paginas,
            'periodos': ['Mês', 'Ano', '12M', '24M', '36M', 'Desde o Início'],
            'linhas': ctx.linhas_rentabilidade,
            'css_marca': self.css_marca, 'css_relatorio': self.css_relatorio,
            'css_entrega': self.css_entrega,
            'css_impressao': self.css_impressao,
            'logo_svg': self.logo(f),
            'marca_svg': self.marca_svg,
            't_svg': self.t_svg,
            'echarts_src': self.ECHARTS,
            'charts_js': self.charts_js,
            'export_js': self.export_js,
            'meta_json': json.dumps({
                'fundo': f.nome,
                'arquivo': self.edicao.nome_arquivo(
                    f'{f.nome} - Relatório de Gestão', '').rstrip('.'),
            }, ensure_ascii=False),
            'barras': grafico.barras_horizontais,
            'rating_cols': grafico.colunas_rating,
            'barras_modelo': grafico.barras_modelo,
            've': self.ve(f),
            'razao_social': self.razao_social(f),
            # desde o início, como no publicado — não a janela de 12 meses
            'grafico': grafico.historico_modelo(
                ctx.hist or ctx.hist12, ctx.benchmark, self.ve(f),
                data_inicio=self._inicio(ctx)),
            'mercado': self.mercado_modelo(self.mercado(ctx)),
            'caracteristicas': self.caracteristicas(ctx),
            'carac_colunas': self.caracteristicas_modelo(ctx),
            'operacional': self.operacional(f),
            'disclaimer': self.disclaimer,
            'selos': self.selos,
            'icones': self.icones, 'colaterais': COLATERAIS,
            'nota_rodape': (f.cfg.get('nota_rodape') or '').strip(),
            'tamanho_disclaimer': self.tamanho_disclaimer(
                self.disclaimer, (f.cfg.get('nota_rodape') or '').strip()),
            'arquivo_comentarios': 'entrada/comentarios.md',
            'setores_barras': setores_barras,
            'estrategia_barras': estrategia_barras,
            'estrategia_treemap': estrategia_treemap,
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
        ctx.estrategia_barras = estrategia_barras
        ctx.estrategia_treemap = estrategia_treemap

        titulos_por_secao = {s['id']: titulos.get(s['id'], s['id'])
                             for pagina in paginas for s in pagina['secoes']}

        # cada componente recebe seu próprio `titulo`; o include herda o contexto,
        # então o título é resolvido na hora pelo id da seção corrente
        self.env.globals['TITULOS'] = titulos_por_secao
        dados['css_abas'] = self.css_abas
        tpl = self.env.get_template(dados.pop('_template', 'relatorio.html'))
        return tpl.render(**dados, titulos=titulos_por_secao,
                          titulo_de=lambda sid: titulos_por_secao.get(sid, sid))

    # --------------------------------------------------- página por vertical
    def html_vertical(self, contextos, vertical, irmas=()):
        """Um documento com todos os fundos da vertical, em abas.

        Treze arquivos avulsos era o errado: quem abre quer "os relatórios de
        Crédito Privado", não caçar treze links. O material que o time já usa
        funciona assim — um gerador com abas de fundo —, e esta página repete
        esse controle.

        Os fundos ficam todos no documento, só um visível. Trocar de aba não
        recarrega nada, e exportar pega só o que está na tela.

        `irmas` são as outras páginas por vertical da edição, como
        (vertical, rótulo, arquivo): viram a troca de vertical no topo.
        """
        rotulo = (self.cad.verticais.get(vertical) or {}).get('rotulo', vertical)
        decks = []
        for ctx in contextos:
            corpo = self.html(ctx)
            # aproveita o corpo já montado: só as folhas, sem <head> nem scripts
            ini = corpo.index('<div class="folhas">')
            fim = corpo.index('</div>', corpo.rindex('</section>')) + len('</div>')
            decks.append({
                'key': ctx.key,
                'nome': ctx.nome,
                'arquivo': self.edicao.nome_arquivo(
                    f'{ctx.nome} - Relatório de Gestão', '').rstrip('.'),
                'paginas': len(self.paginas(ctx.f.key, ctx)),
                'html': corpo[ini:fim],
            })

        tpl = self.env.get_template('relatorio_vertical.html')
        paginas = max((b['paginas'] for b in decks), default=4)
        verticais = [{'rotulo': rot, 'href': quote(arq), 'atual': v == vertical}
                     for v, rot, arq in irmas]
        return tpl.render(
            decks=decks, vertical_rotulo=rotulo, edicao=self.edicao,
            verticais=verticais if len(verticais) > 1 else [],
            paginas_por_fundo=paginas,
            descricao_secoes=self.SECOES_HERO.get(
                vertical, self.SECOES_HERO['credito_privado']),
            marca_path=self._marca_path(),
            css_marca=self.css_marca, css_relatorio=self.css_relatorio,
            css_pagina=self.css_pagina, css_impressao=self.css_impressao,
            css_abas=self.css_abas, charts_js=self.charts_js,
            export_js=self.export_js, echarts_src=self.ECHARTS,
            meta_json=json.dumps({'fundo': rotulo,
                                  'arquivo': f'Relatório de Gestão - {rotulo}'},
                                 ensure_ascii=False))

    # O <symbol id="tv-logo"> da casca quer só o desenho, sem o <svg> em volta:
    # o viewBox do símbolo é o do gerador oficial, e repetir o de fora
    # desalinharia a marca no cabeçalho.
    def _marca_path(self):
        m = re.search(r'<svg[^>]*>(.*)</svg>', self.marca_svg, re.S)
        return m.group(1) if m else ''

    # O parágrafo do hero: o que cada vertical traz, na ordem em que aparece.
    SECOES_HERO = {
        'credito_privado':
            'São objetivo e rentabilidade em 6 períodos; principais emissores, '
            'alocação por setor e distribuição de rating; rentabilidade histórica '
            'e comentário do gestor; mercado de crédito; e características '
            'gerais + disclaimer.',
        'credito_estruturado':
            'São objetivo e rentabilidade em 6 períodos; alocação real da carteira '
            'de crédito e alocação por estratégia; rentabilidade histórica e '
            'comentário do gestor; e características gerais + disclaimer.',
    }


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
