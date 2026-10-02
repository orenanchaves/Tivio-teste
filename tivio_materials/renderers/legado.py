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
import re

import pandas as pd

from calculators import formatos as fmt
from renderers.jsobj import replace_literal

P6 = ['mes', 'ano', '12m', '24m', '36m', 'inicio']

MENSAIS = {
    'tivio-post-credito-estruturado.html', 'tivio-post-credito-privado.html',
    'tivio-post-investment-solutions.html',
    'tivio-relatorio-gestao-credito-privado.html',
    'tivio-email-fundos-credito.html',
}


class RenderizadorLegado:
    ARQUIVOS = {
        'tivio-post-credito-privado.html': 'post_credito_privado',
        'tivio-post-credito-estruturado.html': 'post_credito_estruturado',
        'tivio-post-investment-solutions.html': 'post_investment_solutions',
        'tivio-email-fundos-credito.html': 'email_fundos_credito',
        'tivio-central.html': 'central',
        'tivio-relatorio-gestao-credito-privado.html': 'relatorio_legado',
    }

    def __init__(self, contexto, cadastro, edicao, comentarios, manual, log):
        self.ctx = contexto
        self.cad = cadastro
        self.edicao = edicao
        self.com = comentarios
        self.manual = manual or {}
        self.log = log
        self.rotulo_taxa = cadastro.rotulo_taxa
        self.ov = {}
        for _, r in self.manual.get('Overrides', pd.DataFrame()).iterrows():
            if r.get('chave') and r.get('campo'):
                self.ov.setdefault(str(r['chave']).strip(), {})[str(r['campo']).strip()] = r['valor']

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
                for i, per in ((1, '12m'), (2, 'ano'), (3, 'mes')):
                    if ctx.f.retorno_absoluto:
                        self.set(k, f, f'v{i}', ctx.texto(per, 'fundo'))
                        self.set(k, f, f'a{i}', '*Alfa: ' + ctx.texto(per, 'alfa'))
                    else:
                        self.set(k, f, f'v{i}', ctx.texto(per, 'pct'))
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
        return replace_literal(html, 'const FUNDS=', fn)

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
                    self.set(k, f, f'v{i}', ctx.texto(per, 'pct'))
                if ctx.cart:
                    g = {}
                    for t, v in ctx.cart['tipos'].items():
                        lb = self.cad.tipo_label.get(t, t)
                        g[lb] = g.get(lb, 0) + v
                    self.set(k, f, 'alloc', [{'n': n, 'p': round(v * 100, 1)}
                                             for n, v in sorted(g.items(), key=lambda x: -x[1])
                                             if v > 0.0005])
                    faltam = [t for t in ctx.cart['tipos'].index
                              if t not in self.cad.tipo_label]
                    if faltam:
                        self.log.aviso(k, f'tipos sem nome amigável em fundos.yml '
                                          f'(tipo_label): {faltam}')
                if f.get('taxas'):
                    self.set(k, f, 'taxas', self.troca_taxas(f['taxas'], ctx.taxa, ctx.perf))
                self.overrides(k, f)
            return funds
        return replace_literal(html, 'const FUNDS=', fn)

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
                        self.set(k, f, f'v{i}', ctx.texto(per, 'fundo'))
                        self.set(k, f, f'a{i}', '*Alfa: ' + ctx.texto(per, 'alfa'))
                    else:
                        self.set(k, f, f'v{i}', ctx.texto(per, 'pct'))
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
        return replace_literal(html, 'const HIST=', fh)

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
        from engine.edicao import MESES
        atual = MESES[self.edicao.db.month - 1].lower()
        for mes in MESES:
            if mes.lower() != atual and re.search(rf'\b{mes.lower()}\b', (texto or '').lower()):
                self.log.aviso(k, f'texto cita "{mes}" — a data base é {atual}')
                return

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

    def central(self, html):
        rotulo = self.edicao.mes_ano_curto

        def fn(seed):
            for it in seed:
                if it.get('link') in MENSAIS and it.get('kind') in ('destaques', 'relatorios', 'emails'):
                    self.set(it.get('id', '?'), it, 'date', rotulo)
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

    # ========================================================== orquestração
    def processar(self, nome, html):
        metodo = self.ARQUIVOS.get(nome)
        if not metodo:
            return html
        antiga = self.data_antiga(html)
        html = getattr(self, metodo)(html)
        if nome in MENSAIS:
            html = self.trocar_datas(html, antiga)
        return html
