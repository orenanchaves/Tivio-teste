# -*- coding: utf-8 -*-
"""Materiais HTML legados: injeta dados sem tocar no desenho.

Os posts, o e-mail e a Central são HTMLs feitos à mão, com carrossel, lightbox,
treemap, exportação em JPG/PDF/PPTX no próprio navegador. Reescrevê-los como
template Jinja jogaria fora o material desenhado para ganhar uniformidade de
código — troca ruim. Então aqui eles continuam sendo a fonte do layout, e só os
literais de dados (`FUNDS`, `DATA`, `HIST`, `SEED`) são reescritos.

A diferença em relação ao atualizador anterior é de onde vem o número: antes
cada função recalculava o seu; agora todas leem o mesmo `Contexto`. É o que
impede o post e o e-mail de discordarem sobre o mesmo fundo.
"""
import os
import re

import pandas as pd

from calculators import formatos as fmt
from engine.contexto import agrupar_tipos
from renderers.jsobj import replace_literal

P6 = ['mes', 'ano', '12m', '24m', '36m', 'inicio']

MENSAIS = {
    'tivio-post-credito-estruturado.html', 'tivio-post-credito-privado.html',
    'tivio-post-investment-solutions.html',
    'tivio-email-fundos-credito.html',
    'tivio-email-previdencia.html', '../landing%20page/tivio-hgd30-saiba-mais.html',
    '../landing%20page/tivio-hyd60-saiba-mais.html',
}


class RenderizadorLegado:
    ARQUIVOS = {
        'tivio-post-credito-privado.html': 'post_credito_privado',
        'tivio-post-credito-estruturado.html': 'post_credito_estruturado',
        'tivio-post-investment-solutions.html': 'post_investment_solutions',
        'tivio-email-fundos-credito.html': 'email_fundos_credito',
        'tivio-central.html': 'central',
    }

    def __init__(self, contexto, cadastro, edicao, comentarios, manual, log,
                 relatorios=None, pasta_saida=None):
        self.ctx = contexto
        self.cad = cadastro
        self.edicao = edicao
        self.com = comentarios
        self.manual = manual or {}
        self.log = log
        # [(contexto, nome do arquivo)] dos relatórios gerados nesta edição —
        # é o que a Central precisa listar
        self.relatorios = relatorios or []
        self.pasta_saida = pasta_saida or ''
        self.rotulo_taxa = cadastro.rotulo_taxa
        self.ov = {}
        for _, r in self.manual.get('Overrides', pd.DataFrame()).iterrows():
            chave = str(r.get('chave') or '').strip()
            campo = str(r.get('campo') or '').strip()
            if not chave or not campo or chave.startswith('#'):
                continue   # '#' marca linha de exemplo
            self.ov.setdefault(chave, {})[campo] = r['valor']

    # ------------------------------------------------------------------- util
    def set(self, fundo, obj, campo, novo):
        if novo is None:
            return
        antes = obj.get(campo)
        if antes != novo:
            self.log.mudanca(fundo, campo, antes, novo)
            obj[campo] = novo

    def overrides(self, key, obj):
        for campo, valor in self.ov.get(self.cad.alias.get(key, key), {}).items():
            if campo == 'casas_taxa':
                continue
            alvo, partes = obj, campo.split('.')
            for p in partes[:-1]:
                alvo = alvo.get(p) if isinstance(alvo, dict) else None
                if alvo is None:
                    break
            if isinstance(alvo, dict):
                self.set(key, alvo, partes[-1], valor)

    def c(self, key):
        """Contexto do fundo, ou None com aviso já registrado."""
        ctx = self.ctx.de(key)
        if ctx is None:
            self.log.aviso(key, 'fundo não está em configs/fundos.yml — mantido como estava')
            return None
        if not ctx.tem_dados:
            return None
        return ctx

    def troca_taxas(self, txt, taxa, perf):
        if taxa:
            txt = re.sub(r'(Taxa de administração(?: e gestão)?|Taxa global):\s*[^.]*?a\.a\.(?: \([^)]*\))?',
                         f'{self.rotulo_taxa}: {taxa}', txt)
        if perf and re.search(r'Taxa de performance:', txt):
            p = perf[0].lower() + perf[1:] if perf.startswith('Não') else perf
            txt = re.sub(r'Taxa de performance:\s*.*?(?=\.\s|\.$)',
                         f'Taxa de performance: {p}', txt)
        return txt

    # --------------------------------------------------------------- datas
    @staticmethod
    def data_antiga(html):
        m = re.search(r'[Dd]ata base:?\s*(\d{2}/\d{2}/\d{4})', html)
        if not m:
            return None
        from engine.edicao import Edicao
        return Edicao(pd.to_datetime(m.group(1), dayfirst=True))

    def trocar_datas(self, html, antiga):
        for de, para in self.edicao.substituicoes(antiga):
            if de in html:
                self.log.mudanca('—', 'data', de, para)
                html = html.replace(de, para)
        return html

    # ============================================================== POSTS
    # Posts de Destaques: os boxes de Rentabilidade saem sem casa decimal
    # ("100%"); os Infra mantêm as casas (pedido de 05/10/2026)
    COM_CASAS_NO_POST = ('infraplus', 'infrapluscdi')

    def rent_post(self, ctx, per, campo):
        if ctx.key in self.COM_CASAS_NO_POST:
            return ctx.texto(per, campo)
        v = ctx.valor(per, campo)
        if v is None:
            return fmt.MINUS
        return fmt.num(v * 100, 0) + '%'

    def post_credito_privado(self, html):
        # bug do material publicado: buildPages() usa f.tw e f.hl, que não existem
        # em FUNDS, e as páginas 3-7 saem com "undefined undefined" no cabeçalho
        html = html.replace("const n=idx+3, nome=(f.tw+' '+f.hl+(f.num?' '+f.num:''));",
                            "const n=idx+3, nome=f.nome;")

        def fn(funds):
            for f in funds:
                k = f['key']
                ctx = self.c(k)
                if not ctx:
                    self.log.aviso(k, 'sem dados — mantido como estava')
                    continue
                sem_12m = ctx.texto('12m', 'pct' if not ctx.f.retorno_absoluto else 'fundo') in ('-', '–', '—', '', fmt.MINUS)
                for i, per in ((1, 'inicio' if sem_12m else '12m'), (2, 'ano'), (3, 'mes')):
                    if i == 1:
                        self.set(k, f, 'k1', 'Desde o início' if sem_12m else '12M')
                    if ctx.f.retorno_absoluto:
                        self.set(k, f, f'v{i}', self.rent_post(ctx, per, 'fundo'))
                        self.set(k, f, f'a{i}', '*Alfa: ' + ctx.texto(per, 'alfa'))
                    else:
                        self.set(k, f, f'v{i}', self.rent_post(ctx, per, 'pct'))
                self.set(k, f, 'pl', ctx.pl_fmt)
                self.set(k, f, 'plm', ctx.pl_medio_fmt)
                if ctx.cart:
                    st = ctx.cart['setores']
                    top = st[st.index != 'Caixa'].head(3)
                    self.set(k, f, 'alloc', {
                        'total': ctx.credito_fmt.rstrip('%'),
                        'top': [{'p': fmt.num(v * 100, 0) + '%',
                                 'n': n if n == 'FIDC' else str(n).lower()}
                                for n, v in top.items()]})
                    f['carrego'] = dict(f.get('carrego') or {})
                    self.set(k, f['carrego'], 'val', fmt.num(ctx.carrego * 100, 2))
                    f['duration'] = dict(f.get('duration') or {})
                    self.set(k, f['duration'], 'val', fmt.num(ctx.duration, 2))
                    self.set(k, f['duration'], 'unit', 'ano' if ctx.duration < 2 else 'anos')
                if f.get('taxas'):
                    self.set(k, f, 'taxas', self.troca_taxas(f['taxas'], ctx.taxa, ctx.perf))
                self.overrides(k, f)
            return funds
        html = replace_literal(html, 'const FUNDS=', fn)
        return self.logos_horizontais_no_html(html, 'p', extras=('infrapluscdi',))

    def post_credito_estruturado(self, html):
        def fn(funds):
            for f in funds:
                k = f['key']
                ctx = self.c(k)
                if not ctx:
                    self.log.aviso(k, 'sem dados — mantido')
                    continue
                self.set(k, f, 'b1val', ctx.pl_fmt)
                desde = 'início' in (f.get('b2lab') or '')
                pl_medio = ctx.rent.get('pl_medio_inicio') if desde else ctx.pl_medio
                self.set(k, f, 'b2val', fmt.brl(pl_medio) if pl_medio else fmt.MINUS)
                p1 = 'inicio' if f.get('k1') == 'Desde o início' else '12m'
                if p1 == '12m' and not ctx.rent.get('12m'):
                    # fundo com menos de 12 meses: o rótulo vira "Desde o início"
                    # em vez de mostrar um traço onde deveria haver número
                    self.set(k, f, 'k1', 'Desde o início')
                    p1 = 'inicio'
                for i, per in ((1, p1), (2, 'ano'), (3, 'mes')):
                    self.set(k, f, f'v{i}', self.rent_post(ctx, per, 'pct'))
                if ctx.cart:
                    # o mesmo agrupamento do treemap do relatório — uma
                    # implementação só, em engine/contexto.py
                    self.set(k, f, 'alloc',
                             [{'n': n, 'p': round(v, 1)} for n, _, v in
                              ctx.alocacao_real(self.cad)])
                    faltam = [t for t in ctx.cart['tipos'].index
                              if t not in self.cad.tipo_label]
                    if faltam:
                        self.log.aviso(k, f'tipos sem nome amigável em fundos.yml '
                                          f'(tipo_label): {faltam}')
                if f.get('taxas'):
                    self.set(k, f, 'taxas', self.troca_taxas(f['taxas'], ctx.taxa, ctx.perf))
                self.overrides(k, f)
            return funds
        html = replace_literal(html, 'const FUNDS=', fn)
        return self.logos_horizontais_no_html(html, 'path')

    def post_investment_solutions(self, html):
        html = html.replace('<span contenteditable="true">Taxa de administração</span>',
                            f'<span contenteditable="true">{self.rotulo_taxa}</span>')

        def fn(funds):
            for f in funds:
                k = f['key']
                ctx = self.ctx.de(k)
                if ctx and ctx.taxa:
                    self.set(k, f, 'adm', ctx.taxa)
                    self.set(k, f, 'perf', ctx.perf or f.get('perf'))
                ctx = self.c(k)
                if not ctx:
                    self.log.aviso(k, 'sem dados — rentabilidade e PL mantidos')
                    continue
                for i, per in ((1, 'mes'), (2, 'ano'), (3, '12m')):
                    if ctx.f.retorno_absoluto:
                        self.set(k, f, f'v{i}', self.rent_post(ctx, per, 'fundo'))
                        self.set(k, f, f'a{i}', '*Alfa: ' + ctx.texto(per, 'alfa'))
                    else:
                        self.set(k, f, f'v{i}', self.rent_post(ctx, per, 'pct'))
                self.set(k, f, 'plm', fmt.brl_curto(ctx.pl_medio) if ctx.pl_medio else fmt.MINUS)
                self.overrides(k, f)
            return funds
        return replace_literal(html, 'const FUNDS=', fn)

    # ============================================================== E-MAIL
    def email_fundos_credito(self, html):
        def fn(funds):
            for f in funds:
                k = f['key']
                ctx = self.c(k)
                if not ctx:
                    self.log.aviso(k, 'sem dados — mantido')
                    continue
                rows = [list(x) for x in f['rows']]
                for row in rows:
                    lb = row[0]
                    if lb == 'Fundo':
                        campo = 'fundo'
                    elif lb == '%':
                        campo = 'pct'
                    elif lb == 'Alfa':
                        campo = 'alfa'
                    elif str(lb).endswith('+'):
                        campo = 'bench_mais'
                    else:
                        campo = 'bench'
                    row[1:7] = [ctx.texto(p, campo) for p in P6]
                self.set(k, f, 'rows', rows)

                meta = [list(x) for x in f['meta']]
                for it in meta:
                    lb = str(it[0])
                    if lb.startswith(('Taxa de Administração', 'Taxa Global')) or lb == self.rotulo_taxa:
                        it[0], it[1] = self.rotulo_taxa, ctx.taxa or it[1]
                    elif lb == 'Taxa de Performance':
                        it[1] = ctx.perf or it[1]
                    elif lb.startswith('PL Médio'):
                        it[1] = fmt.brl_curto(ctx.pl_medio) if ctx.pl_medio else it[1]
                    elif lb.startswith('PL (desde'):
                        it[1] = fmt.brl_curto(ctx.pl) if ctx.pl else it[1]
                self.set(k, f, 'meta', meta)

                frase = self.frase_abertura(ctx, f.get('name') or ctx.nome)
                resto, _ = ctx.preencher(self.com.email(k, ctx.nome))
                if not resto:
                    partes = re.split(r'(?<=\.)\s+(?=[A-ZÁÉÍÓÚ])', f.get('comment', ''), maxsplit=1)
                    resto = partes[-1] if len(partes) > 1 else ''
                self.checar_mes(k, resto)
                self.set(k, f, 'comment', (frase + ' ' + resto).strip())
                self.overrides(k, f)
            return funds
        html = replace_literal(html, 'const FUNDS=', fn)

        def fh(hist):
            for k in list(hist):
                ctx = self.ctx.de(k)
                if ctx and ctx.hist:
                    if hist[k] == ctx.hist:
                        continue
                    antes = hist[k]['l'][-1] if hist[k].get('l') else '?'
                    self.log.mudanca(k, 'HIST', f'até {antes}',
                                     f'até {ctx.hist["l"][-1]} ({len(ctx.hist["l"])} meses)')
                    hist[k] = ctx.hist
                else:
                    self.log.aviso(k, 'histórico não recalculado (sem cotas)')
            return hist
        html = replace_literal(html, 'const HIST=', fh)
        return self.logos_email(html)

    def logos_horizontais_no_html(self, html, campo='p', extras=()):
        """Troca o literal FUND_LOGOS do material pelos logos HORIZONTAIS de
        assets/logos (versão branca). `campo` é o nome da chave do desenho no
        material: 'p' no post de Crédito Privado, 'path' no de Estruturado.
        `extras`: chaves que o material ainda não tem e passam a ter logo."""
        from renderers.logos import logos_horizontais
        import json as _json
        i = html.find('const FUND_LOGOS=')
        if i < 0:
            return html
        k = html.find('const fundLogoSVG', i)
        if k < 0:
            k = html.find('const FUNDS=', i)
        j = html.rfind('}', i, k) + 1 if k > 0 else -1
        if j <= 0:
            return html
        chaves = re.findall(r"'(\w+)':\{vb:", html[i:j])
        chaves += [c for c in extras if c not in chaves]
        escuro, _ = logos_horizontais(chaves, log=self.log)
        faltam = [c for c in chaves if c not in escuro]
        if faltam:
            self.log.aviso('logos', 'sem logo horizontal, mantido o antigo: ' + ', '.join(faltam))
            return html
        novo = {c: {'vb': v['vb'], campo: v['p']} for c, v in escuro.items()}
        return html[:i] + 'const FUND_LOGOS=' + _json.dumps(novo, ensure_ascii=False) + html[j:]

    def logos_email(self, html):
        """Troca os logos embutidos no e-mail pelas versões HORIZONTAIS de
        assets/logos (escuro: branca; claro: preta) — renderers/logos.py."""
        from renderers.logos import logos_horizontais, como_js
        i = html.find('const FUND_LOGOS=')
        # o literal termina na última chave antes da função que desenha o logo
        # (que vem na linha seguinte) — ou antes de FUNDS, se ela não existir
        k = html.find('const fundLogoSVG', i)
        if k < 0:
            k = html.find('const FUNDS=', i)
        j = html.rfind('}', i, k) + 1 if k > 0 else -1
        if i < 0 or j < 0:
            self.log.aviso('e-mail', 'FUND_LOGOS não encontrado — logos mantidos')
            return html
        chaves = re.findall(r"'(\w+)':\{vb:", html[i:j])
        # fundos que entraram no e-mail depois do desenho original (só Ágora)
        chaves += [c for c in ('inst30', 'infrapluscdi') if c not in chaves]
        escuro, claro = logos_horizontais(chaves, log=self.log)
        if not escuro:
            return html
        antigos = dict.fromkeys(chaves)
        faltam = [k for k in antigos if k not in escuro]
        if faltam:
            self.log.aviso('e-mail', 'sem logo horizontal, mantido o antigo: ' + ', '.join(faltam))
            return html
        novo = como_js('FUND_LOGOS', escuro)[:-1] + ';' + como_js('FUND_LOGOS_LIGHT', claro)[:-1]
        return html[:i] + novo + html[j:]

    def frase_abertura(self, ctx, nome):
        """A primeira frase do comentário do e-mail, montada dos números."""
        b = ctx.benchmark
        if ctx.f.retorno_absoluto:
            return (f'O {nome} apresentou rentabilidade, isenta de imposto de renda, de '
                    f'{ctx.texto("mes", "fundo")} no mês, acumulando '
                    f'{ctx.texto("ano", "fundo")} no ano.')
        if ctx.f.mesa == 'HY':
            return (f'O {nome} rendeu {ctx.texto("mes", "fundo")} no mês '
                    f'({ctx.texto("mes", "pct")} do {b}), acumulando '
                    f'{ctx.texto("ano", "fundo")} no ano e {ctx.texto("inicio", "fundo")} '
                    f'desde o início ({b}+{ctx.texto("inicio", "bench_mais")} ao ano).')
        return (f'O {nome} apresentou rentabilidade de {ctx.texto("mes", "fundo")} no mês '
                f'({ctx.texto("mes", "pct")} do {b}), acumulando '
                f'{ctx.texto("ano", "fundo")} no ano.')

    def checar_mes(self, k, texto):
        """Mesma regra da conferência: só avisa quando o texto trata outro mês
        como o mês corrente, não quando cita outro mês como comparação."""
        from validations.conferencia import Conferencia
        from engine.edicao import MESES
        atual = MESES[self.edicao.db.month - 1].lower()
        citado = Conferencia._mes_de_referencia(self, texto)
        if citado and citado != atual:
            self.log.aviso(k, f'o texto se refere a "{citado}" como o mês corrente '
                              f'— a data base é {atual}')

    # ========================================================== RELATÓRIO
    def relatorio_legado(self, html):
        """O gerador HTML de relatórios continua funcionando, com os dados novos.

        O relatório componentizado (renderers/relatorio.py) é o caminho principal
        e cobre os 12 fundos. Este aqui mantém o gerador interativo de 5 fundos
        vivo para quem usa a edição na tela — mesmos números, mesma fonte.
        """
        html = html.replace("['Taxa de administração',f.adm]",
                            f"['{self.rotulo_taxa}',f.adm]")
        # gráfico: a série real substitui a interpolação sintética do histSVG
        html = html.replace(
            "const fundo=series(fundoEnd),bench=series(benchEnd);",
            "const fundo=(f.hist12?f.hist12.f:series(fundoEnd)),"
            "bench=(f.hist12?f.hist12.c:series(benchEnd));")
        html = html.replace("let maxV=Math.max.apply(null,all),minV=0,",
                            "let maxV=Math.max.apply(null,all),"
                            "minV=Math.min(0,Math.min.apply(null,all)),")

        mercado = self.manual.get('Mercado_Credito')

        def fn(data):
            if mercado is not None and len(mercado):
                linhas = []
                for _, r in mercado.iterrows():
                    if not str(r.iloc[0]).strip():
                        continue
                    linhas.append([str(r.iloc[c]) for c in range(min(7, len(r)))]
                                  + [str(r.iloc[0]).strip().lower() == 'total'])
                if linhas:
                    self.set('mercado', data, 'MARKET', linhas)
            for f in data.get('FUNDS', []):
                k = f['key']
                ctx = self.c(k)
                if not ctx:
                    self.log.aviso(k, 'sem dados — mantido')
                    continue
                self.set(k, f, 'adm', ctx.taxa)
                self.set(k, f, 'perf', ctx.perf or f.get('perf'))
                self.set(k, f, 'pl', ctx.pl_fmt)
                self.set(k, f, 'plm', ctx.pl_medio_fmt)
                self.set(k, f, 'perfrows', ctx.linhas_rentabilidade)
                if ctx.cart:
                    self.set(k, f, 'emissores', [[n, v, l] for n, v, l in ctx.emissores])
                    self.set(k, f, 'setores', [[n, v] for n, v, _ in ctx.setores])
                    self.set(k, f, 'rating', [[n, v, l] for n, v, l in ctx.rating])
                    f['carrego'] = dict(f.get('carrego') or {})
                    self.set(k, f['carrego'], 'val', ctx.carrego_fmt)
                    f['duration'] = dict(f.get('duration') or {})
                    self.set(k, f['duration'], 'val', fmt.num(ctx.duration, 2))
                    self.set(k, f['duration'], 'unit', 'ano' if ctx.duration < 2 else 'anos')
                if ctx.hist12:
                    self.set(k, f, 'hist12', ctx.hist12)
                    self.set(k, f, 'histEnd',
                             [ctx.hist12['f'][-1], ctx.hist12['c'][-1], ctx.benchmark])
                if ctx.comentario:
                    paras = ctx.comentario_preenchido
                    self.set(k, f, 'comentario', paras)
                    self.checar_mes(k, ' '.join(paras))
                self.overrides(k, f)
            return data
        return replace_literal(html, 'const DATA=', fn)

    # ============================================================= CENTRAL
    CENTRAL_JS = """
/* ===== DATA AUTOMÁTICA · materiais recorrentes (gerado por run.py) ===== */
const DATA_BASE='%DB%';
const RECORRENTES=%REC%;
(function(){
  const M=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];
  const d=new Date(DATA_BASE+'T12:00:00'),lb=M[d.getMonth()]+' '+d.getFullYear();
  const rec=i=>RECORRENTES.indexOf(i.link)>-1&&['destaques','relatorios','emails'].indexOf(i.kind)>-1;
  SEED.forEach(i=>{if(rec(i))i.date=lb});
  items.forEach(i=>{if(rec(i))i.date=lb});
})();
/* ===== fim data automática ===== */"""

    ANCORA = ("items=items.filter(i=>!(i.kind==='emails'&&!i.link&&"
              "(i.id==='s4'||i.id==='s5'||i.id==='s7')));")

    # Descrição dos cards de relatório, por vertical. Fica aqui e não no YAML
    # porque é texto de vitrine da Central, não configuração do fundo.
    DESC_RELATORIO = {
        'credito_privado':
            'Relatório de gestão mensal, 4 páginas (A4): objetivo e rentabilidade '
            'em 6 períodos; principais emissores, alocação por setor e distribuição '
            'de rating; rentabilidade histórica e comentário do gestor; mercado de '
            'crédito; características e disclaimer. Exporta em PDF, JPG, PNG e PPTX.',
        'credito_estruturado':
            'Relatório de gestão mensal, 3 páginas (A4): objetivo e rentabilidade '
            'em 6 períodos; alocação real da carteira de crédito e alocação por '
            'estratégia; rentabilidade histórica e comentário do gestor; '
            'características e disclaimer. Exporta em PDF, JPG, PNG e PPTX.',
    }
    VERT_CENTRAL = {'credito_privado': 'credito-privado',
                    'credito_estruturado': 'credito-estruturado',
                    'investment_solutions': 'solutions'}

    def central(self, html):
        """Atualiza a data dos cards e registra os relatórios desta edição.

        Sem isto a Central continua mostrando um único card de relatório — o do
        gerador interativo de 5 fundos — enquanto o `run.py` produz 13 arquivos
        que ninguém encontra pela Central. O índice tem de listar o que existe.
        """
        rotulo = self.edicao.mes_ano_curto
        novos = self._cards_de_relatorio()

        def existe(link):
            """O card aponta para um arquivo que saiu desta edição?

            Só vale para link local terminado em .html — URL externa, PDF no
            SharePoint e landing no ar não dá para conferir daqui, e some do
            índice se eu tentar.
            """
            if not link or '://' in link or not link.lower().endswith('.html'):
                return True
            from urllib.parse import unquote
            return os.path.exists(os.path.normpath(
                os.path.join(self.pasta_saida, 'central', unquote(link))))

        def fn(seed):
            for it in seed:
                if it.get('link') in MENSAIS and it.get('kind') in ('destaques', 'relatorios', 'emails', 'landings'):
                    self.set(it.get('id', '?'), it, 'date', rotulo)

            if not novos:
                return seed

            # fora os cards de relatório gerados numa edição anterior (os ids
            # começam com 'rg-'), para não acumular duplicata a cada rodada
            seed = [it for it in seed if not str(it.get('id', '')).startswith('rg-')]

            # o card do gerador interativo continua, mas depois dos relatórios
            # prontos: hoje ele cobre 5 fundos, e os prontos cobrem 13
            pos = next((i for i, it in enumerate(seed)
                        if it.get('kind') == 'relatorios'), len(seed))
            seed[pos:pos] = novos

            # ...e passa a se chamar pelo que é. Com o título antigo ficavam
            # dois cards "Relatórios de Gestão · Crédito Privado" lado a lado,
            # um indo para o relatório pronto e outro para o construtor.
            for it in seed:
                if (it.get('kind') != 'relatorios'
                        or str(it.get('id', '')).startswith('rg-')
                        or str(it.get('title', '')).startswith('Gerador')):
                    continue
                cauda = str(it.get('title', '')).split('·')[-1].strip()
                self.set(it.get('id', '?'), it, 'title',
                         f'Gerador de Relatório de Gestão · {cauda}')
                self.set(it.get('id', '?'), it, 'desc',
                         'Construtor interativo, folha a folha. Os relatórios '
                         'prontos do mês estão no card acima. '
                         + str(it.get('desc', '')))

            # Informativos de previdência (PPTX + PDF) desta edição: saem em
            # ../informativos/, depois da Central; o nome é previsível
            from urllib.parse import quote
            seed = [it for it in seed if not str(it.get('id', '')).startswith('inf-')]
            mes = f'{fmt.MESES[self.edicao.db.month - 1]} {self.edicao.db.year}'
            infs = []
            for sigla, nome in (('HGD30', 'Tivio HGD30'), ('HYD60', 'Bradesco Tivio HYD60')):
                base = '../informativos/' + quote(f'Informativo - {sigla} - {mes}')
                infs.append({'id': f'inf-{sigla.lower()}', 'kind': 'apresentacoes',
                             'vert': 'previdencia', 'title': f'Informativo · {nome}',
                             'desc': 'Informativo mensal que vai para os clientes, com os '
                                     'números da carteira do mês. PPT editável e PDF.',
                             'date': rotulo, 'status': 'pronto',
                             'link': base + '.pptx', 'pdf': base + '.pdf'})
            pos = next((i for i, it in enumerate(seed) if it.get('kind') == 'apresentacoes'), len(seed))
            seed[pos:pos] = infs

            # card apontando para HTML que não existe é link morto no índice —
            # alguém clica e não acontece nada
            mortos = [it for it in seed if not existe(it.get('link'))]
            for it in mortos:
                self.log.aviso('tivio-central.html',
                               f'card "{it.get("title", it.get("id"))}" removido: '
                               f'aponta para "{it.get("link")}", que não existe '
                               f'nesta edição')
            seed = [it for it in seed if it not in mortos]

            self.log.mudanca('—', 'Central', 'cards de relatório',
                             f'{len(novos)} registrados para {rotulo}')
            return seed
        html = replace_literal(html, 'const SEED=', fn)

        bloco = (self.CENTRAL_JS.replace('%DB%', self.edicao.iso)
                 .replace('%REC%', '[' + ','.join(f"'{r}'" for r in sorted(MENSAIS)) + ']'))
        ini = html.find('/* ===== DATA AUTOMÁTICA')
        if ini >= 0:
            marca = '/* ===== fim data automática ===== */'
            fim = html.find(marca) + len(marca)
            html = html[:ini - 1] + bloco + html[fim:]
        elif self.ANCORA in html:
            html = html.replace(self.ANCORA, self.ANCORA + bloco, 1)
            self.log.mudanca('—', 'data automática', '', f'DATA_BASE={self.edicao.iso}')
        else:
            self.log.aviso('—', 'âncora do localStorage não encontrada — a data dos '
                                'cards só muda para quem limpar o cache do navegador')
        return html

    # ===================================================== libs de exportação
    # Os botões (Pacote JPG, Pacote PDF, Baixar PNG, E-mail HTML) dependem de
    # html2canvas, jszip e jspdf, que os materiais buscam no cdnjs — sem
    # alternativa. CDN fora, bloqueado pela rede da empresa ou lento e o botão
    # não faz nada: o onclick chama uma função que não existe, e não aparece
    # erro na tela.
    #
    # Como o fluxo é "o HTML sai pronto e a pessoa clica no botão", o botão é
    # parte do processo. Aqui a ordem é invertida: tenta a cópia local, cai no
    # CDN se ela não estiver lá. Mandar só o HTML por e-mail continua
    # funcionando (o local dá 404 e o CDN assume); a pasta inteira funciona sem
    # rede nenhuma.
    LIBS = {
        'html2canvas': 'html2canvas.min.js',
        'jszip': 'jszip.min.js',
        'jspdf': 'jspdf.umd.min.js',
        'echarts': 'echarts.min.js',
    }

    def libs_locais(self, html):
        trocas = 0
        for chave, arquivo in self.LIBS.items():
            padrao = re.compile(
                r'<script\s+src="(https://[^"]*' + chave + r'[^"]*)"([^>]*)></script>',
                re.I)

            def troca(m):
                nonlocal trocas
                trocas += 1
                cdn, resto = m.group(1), m.group(2)
                # `crossorigin` e `integrity` são do CDN e atrapalham no local:
                # numa página aberta por file://, crossorigin="anonymous" faz o
                # navegador tratar o script como requisição CORS de origem
                # opaca e recusá-lo — o arquivo está lá e não carrega.
                resto = re.sub(r'\s*(crossorigin|integrity)="[^"]*"', '', resto)
                # o onerror roda só quando o arquivo local não existe; aí
                # injeta a tag do CDN no lugar, de forma síncrona o bastante
                # para o resto da página ainda encontrar a biblioteca
                return (f'<script src="vendor/{arquivo}"{resto} '
                        f'onerror="this.onerror=null;'
                        f'document.write(\'&lt;script src=&quot;{cdn}&quot;&gt;'
                        f'&lt;/script&gt;\'.replace(/&lt;/g,String.fromCharCode(60))'
                        f'.replace(/&gt;/g,String.fromCharCode(62))'
                        f'.replace(/&quot;/g,String.fromCharCode(34)))"></script>')
            html = padrao.sub(troca, html)

            # O e-mail não usa <script src>: carrega em JS, percorrendo uma
            # lista de CDNs até um responder. Aí não há tag para reescrever —
            # basta o caminho local entrar como primeiro candidato da lista, e a
            # cascata de CDNs que já existe continua valendo como reserva.
            lista = re.compile(
                r"\['(https://cdnjs[^']*" + chave + r"[^']*)'", re.I)

            def primeiro(m):
                nonlocal trocas
                trocas += 1
                return f"['vendor/{arquivo}','{m.group(1)}'"
            html = lista.sub(primeiro, html)

        # O carregador dinâmico marca `crossOrigin='anonymous'` em toda URL.
        # Para o CDN é correto; para o arquivo local é fatal: numa página aberta
        # por file:// o navegador trata o script como requisição CORS de origem
        # opaca e recusa — o arquivo está ali e não carrega. Passa a marcar só
        # quando a URL é absoluta.
        antes = html
        html = html.replace(
            "s.src=src;s.crossOrigin='anonymous';",
            "s.src=src;if(/^https?:/i.test(src))s.crossOrigin='anonymous';")
        if html != antes:
            trocas += 1

        if trocas:
            self.log.mudanca('—', 'libs de exportação', 'CDN',
                             f'{trocas} referências → vendor/ local (CDN como reserva)')
        return html

    def _cards_de_relatorio(self):
        """Um card por VERTICAL, não por fundo.

        Treze cards de relatório afogavam a aba. O material que o time já usa é
        um gerador por vertical com abas de fundo dentro, e é esse o card: um
        link para a página, com os fundos nomeados na descrição.
        """
        cards = []
        for rotulo, ctxs, arquivo in self.relatorios:
            vert = ctxs[0].f.vertical if ctxs else 'credito_privado'
            nomes = ', '.join(c.nome.replace('Tivio ', '') for c in ctxs)
            cards.append({
                'id': f'rg-{vert}',
                'kind': 'relatorios',
                'vert': self.VERT_CENTRAL.get(vert, 'credito-privado'),
                'title': f'Relatórios de Gestão · {rotulo}',
                'desc': f'{len(ctxs)} fundos em abas — {nomes}. '
                        + self.DESC_RELATORIO.get(vert, self.DESC_RELATORIO['credito_privado']),
                'date': self.edicao.mes_ano_curto,
                'status': 'pronto',
                # todos os HTML ficam em central/, ao lado da Central
                'link': arquivo,
            })
        return cards

    # ========================================================== orquestração
    def processar(self, nome, html):
        metodo = self.ARQUIVOS.get(nome)
        if not metodo:
            return html
        antiga = self.data_antiga(html)
        html = getattr(self, metodo)(html)
        if nome in MENSAIS:
            html = self.trocar_datas(html, antiga)
        return self.libs_locais(html)
