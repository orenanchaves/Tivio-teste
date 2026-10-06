# -*- coding: utf-8 -*-
"""E-mail dos fundos de previdência (HGD30, HYD60) e os dados que ele e o
Informativo compartilham.

`dados_fundo()` junta, num dicionário só, tudo o que o e-mail e o Informativo
mostram de um fundo: textos (configs/previdencia.yml + entrada/previdencia.md)
e números (o Contexto do fundo FIFE). Os dois materiais leem esse mesmo
dicionário, e por isso nunca discordam.

O gerador de e-mail (`central/tivio-email-previdencia.html`) é o mesmo formato
do e-mail de Fundos de Crédito: cada bloco é um card que sai em PNG (é o que
vai como imagem no Mailchimp), e o botão "E-mail (HTML)" baixa o e-mail
montado, com os textos em HTML e os blocos como imagem.
"""
import base64
import json
import os

from calculators import formatos as fmt
from renderers.landing import (RenderizadorLanding, carregar_config, carregar_textos,
                               logo_svg, markdown_simples, _valor_curto)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NOMES_BLOCO = {
    'cabecalho': 'Cabeçalho', 'texto': 'Texto do gestor', 'kpis': 'Indicadores',
    'rentabilidade': 'Rentabilidade', 'alocacao': 'Alocação da carteira',
    'setorial': 'Exposição setorial', 'rating': 'Distribuição de rating',
    'composicao': 'Composição da carteira', 'historico': 'Rentabilidade histórica',
    'caracteristicas': 'Características do fundo', 'beneficios': 'Benefícios',
}
# blocos que vão como TEXTO no e-mail (o resto vai como imagem)
BLOCOS_TEXTO = ('texto', 'caracteristicas')


def _data_uri(caminho, mime):
    caminho = caminho if os.path.isabs(caminho) else os.path.join(RAIZ, caminho)
    if not os.path.exists(caminho):
        return ''
    return f'data:{mime};base64,' + base64.b64encode(open(caminho, 'rb').read()).decode()


def _pct3(v):
    return fmt.num(v * 100, 3) + '%' if v is not None else fmt.MINUS


def dados_fundo(chave, pg, ctx, edicao, textos, log=None):
    """Tudo o que o e-mail e o Informativo mostram de um fundo."""
    lp = RenderizadorLanding.__new__(RenderizadorLanding)
    lp.edicao = edicao
    texto_md, faltando = ctx.preencher(textos.get(chave, ''))
    if log:
        for k in faltando:
            log.aviso(chave, f'previdência: marcador sem valor: {{{k}}}')

    # rentabilidade: o mês com três casas, como na tabela do e-mail publicado
    # (1,085% / 1,083%); desde o início com duas
    rent = [
        ('Fundo', _pct3(ctx.valor('mes', 'fundo')), ctx.texto('inicio', 'fundo')),
        (ctx.benchmark, _pct3(ctx.valor('mes', 'bench')), ctx.texto('inicio', 'bench')),
        ('Alfa', ctx.texto('mes', 'alfa'), ctx.texto('inicio', 'alfa')),
        ('%', ctx.texto('mes', 'pct'), ctx.texto('inicio', 'pct')),
        (f'{ctx.benchmark} +', ctx.texto('mes', 'bench_mais'), ctx.texto('inicio', 'bench_mais')),
    ]
    aloc = {n: r for n, r, _ in ctx.alocacao_hghy}
    retornos = {a['nome']: a.get('retorno') for a in pg.get('previsao_alocacao') or []}
    alocacao = [{'nome': n, 'pct': r, 'retorno': retornos.get(n)}
                for n, r, _ in ctx.alocacao_hghy]

    setores = [x for x in ctx.setores_relatorio if x[0] != 'Caixa'] + \
              [x for x in ctx.setores_relatorio if x[0] == 'Caixa']
    hist = lp._historico(ctx)
    em = pg.get('email') or {}
    d = {
        'chave': chave,
        'estilo': 'hy' if pg.get('acento') == 'verde' else 'hg',
        'marca': pg.get('marca'),
        'titulo': em.get('titulo') or pg.get('nome'),
        'produto': em.get('produto', ''),
        'nota_rating': em.get('nota_rating', ''),
        'blocos': [b for b in em.get('blocos') or [] if b in NOMES_BLOCO],
        'mes': fmt.MESES[edicao.db.month - 1],
        'ano': edicao.db.year,
        'mes_ano': edicao.mes_ano,
        'data_base': edicao.br,
        'texto_html': markdown_simples(texto_md),
        'texto_md': texto_md,
        'kpis': lp._kpis(pg, ctx),
        'rent': rent,
        'alocacao': alocacao,
        'aloc_mapa': aloc,
        'setores': setores,
        'rating': list(ctx.rating_relatorio),
        'composicao': ctx.composicao(),
        'hist': hist,
        'pl_curto': _valor_curto(ctx.pl) if ctx.pl else fmt.MINUS,
        'duration': ctx.duration,
        'duration_num': fmt.num(ctx.duration, 2) if ctx.duration is not None else fmt.MINUS,
        'caracteristicas': lp._caracteristicas(pg, ctx),
        # "TIVIO HGD30" / "TIVIO HYD60", como no texto do e-mail
        'nome_curto': 'TIVIO ' + ''.join((pg.get('marca') or ['', '', ''])[1:]),
    }
    return d


class RenderizadorEmailPrevidencia:
    """central/tivio-email-previdencia.html: o gerador, um fundo por aba."""

    ARQUIVO = 'tivio-email-previdencia.html'

    def __init__(self, rend_relatorio, edicao, log):
        self.r = rend_relatorio
        self.edicao = edicao
        self.log = log
        self.cfg = carregar_config()
        self.textos = carregar_textos()

    def fundos(self, contextos):
        por_key = {c.key: c for c in contextos}
        saida = []
        for chave, pg in (self.cfg.get('paginas') or {}).items():
            ctx = por_key.get(pg.get('fundo') or chave)
            if ctx is None or not ctx.tem_dados:
                self.log.aviso(chave, 'e-mail de previdência sem este fundo: sem dados nesta edição')
                continue
            saida.append((dados_fundo(chave, pg, ctx, self.edicao, self.textos, self.log), pg))
        return saida

    @staticmethod
    def arquivos(d):
        """bloco -> nome do PNG ('01-cabecalho.png'…), só os que vão como imagem."""
        out, i = {}, 0
        for b in d['blocos']:
            if b not in BLOCOS_TEXTO:
                i += 1
                out[b] = f'{i:02d}-{b}.png'
        return out

    def disparo(self, d, arquivos=None):
        """O e-mail pronto para o disparo: texto em HTML, blocos como imagem."""
        tpl = self.r.env.get_template('previdencia/email_disparo.html')
        return tpl.render(d=d, arquivos=arquivos or self.arquivos(d),
                          nomes_bloco=NOMES_BLOCO, disclaimer=self.r.disclaimer)

    def html(self, contextos):
        fundos = self.fundos(contextos)
        self.ultimos = fundos
        tpl = self.r.env.get_template('previdencia/email.html')
        imagens = {
            'hgd30_capa': _data_uri('assets/previdencia/hgd30_capa.jpg', 'image/jpeg'),
            'hyd60_capa': _data_uri('assets/previdencia/hyd60_capa.jpg', 'image/jpeg'),
            'hyd60_beneficios': _data_uri('assets/previdencia/hyd60_beneficios.png', 'image/png'),
        }
        logos = {d['chave']: {
            'empilhado': logo_svg((pg.get('logo') or {}).get('empilhado'), 'flogo'),
            'horizontal': logo_svg((pg.get('logo') or {}).get('horizontal'), 'flogo-h')}
            for d, pg in fundos}
        return tpl.render(
            fundos=[d for d, _ in fundos], logos=logos, imagens=imagens,
            nomes_bloco=NOMES_BLOCO, blocos_texto=BLOCOS_TEXTO,
            edicao=self.edicao, disclaimer=self.r.disclaimer,
            selos=self.r.selos, marca_path=self.r._marca_path(), t_svg=self.r.t_svg,
            css_marca=self.r.css_marca, css_pagina=self.r.css_pagina,
            css_blocos=open(os.path.join(RAIZ, 'templates', 'previdencia', 'blocos.css'),
                            encoding='utf-8').read(),
            dados_json=json.dumps({d['chave']: {'hist': d['hist'], 'estilo': d['estilo'],
                                                'blocos': d['blocos'], 'titulo': d['titulo'],
                                                'disparo': self.disparo(d)}
                                   for d, _ in fundos}, ensure_ascii=False).replace('</', '<' + chr(92) + '/'))
