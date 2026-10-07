# -*- coding: utf-8 -*-
"""O contexto de um fundo: um dado só, consumido por todos os materiais.

Isto responde ao problema central da análise. Hoje o mesmo número aparece
diferente em três lugares — o Infra Plus saiu no e-mail com 1,10% e no post e no
relatório com 1,24%, que é o número do *benchmark*. A causa não é erro de
digitação: é que cada HTML guarda a sua própria cópia dos dados, e a cópia é
atualizada à mão, uma por vez.

A correção estrutural é ter uma fonte por fundo. `Contexto.de(fundo)` devolve um
objeto com tudo que qualquer material precisa, já calculado e já formatado em
pt-BR. Post, relatório, e-mail e PPTX leem desse objeto. Divergir passa a exigir
que alguém escreva código para divergir.

Os valores vêm em dois sabores, de propósito:
    .rent['mes']['fundo']   -> 0.011  (float, para cálculo e para o PPTX nativo)
    .fmt['mes']['fundo']    -> '1,10%' (string pt-BR, para o HTML e o PDF)
"""
import pandas as pd

from calculators import formatos as fmt

PERIODOS = ['mes', 'ano', '12m', '24m', '36m', 'inicio']
ROTULO_PERIODO = {'mes': 'Mês', 'ano': 'Ano', '12m': '12M', '24m': '24M',
                  '36m': '36M', 'inicio': 'Desde o início'}


def agrupar_tipos(serie, rotulos):
    """'Tipo aj.' -> [(rótulo, '11,4%', 11.4)], do maior para o menor.

    É a "alocação real da carteira de crédito" dos relatórios de Crédito
    Estruturado, e NÃO é o mesmo corte que a coluna Book, apesar de os dois
    parecerem a mesma coisa num relance. A diferença aparece nos rótulos do
    PPTX publicado: ali consta "Liquidez" e não existe linha "LFSN" — porque
    `tipo_label` chama Caixa de Liquidez e junta LF, LFSC, LFSN, CDB e DPGE em
    "Bancário". O corte por Book separa os dois e não reconcilia com o material.

    Mora aqui, e não dentro de cada renderizador, porque o relatório e o post
    de Crédito Estruturado mostram exatamente este mesmo agrupamento: duas
    cópias dele divergiriam no primeiro tipo novo que aparecesse na base.
    """
    if serie is None:
        return []
    junto = {}
    for t, v in serie.items():
        lb = (rotulos or {}).get(t, t)
        junto[lb] = junto.get(lb, 0) + v
    itens = sorted(((n, v) for n, v in junto.items() if v > 0.0005),
                   key=lambda x: -x[1])
    return [(n, fmt.pct(v, 1), round(v * 100, 2)) for n, v in itens]


class ContextoFundo:
    """Tudo sobre um fundo nesta edição. Só leitura."""

    def alocacao_real(self, cadastro):
        """A "alocação real da carteira de crédito" (treemap do ALT).

        Com `book_depara` no fundo: a coluna Book (Book Maravi) passa pelo
        de-para da tabela escolhida e os percentuais de mesmo rótulo são
        somados (Caixa + LF Sênior + LFSC + LFSN = Liquidez). Book que não
        está na tabela sai com o próprio nome e vira aviso no log.
        Sem `book_depara`: o corte antigo, 'Tipo aj.' + tipo_label.
        """
        if not self.cart:
            return []
        tabela = (cadastro.book_depara or {}).get(self.f.cfg.get('book_depara') or '')
        if tabela and self.cart.get('estrategia') is not None:
            serie = self.cart['estrategia']
            bt = self.cart.get('book_tipo')
            if bt is not None:
                # "Padrão" = sem book: o tipo do ativo decide o book
                junto = {}
                for (book, tipo), v in bt.items():
                    if str(book).strip().lower() == 'padrão':
                        book = (cadastro.book_sem_book or {}).get(tipo, tipo)
                    junto[book] = junto.get(book, 0) + v
                import pandas as _pd
                serie = _pd.Series(junto)
            fora = sorted(str(b) for b in serie.index if b not in tabela and serie[b])
            if fora:
                self.avisos.append('alocação real: book sem de-para, saiu com o próprio nome: '
                                   + ', '.join(fora))
            # sobre o PL, como a planilha da gestão. Com `alocacao_100` no fundo,
            # o que passa de 100% sai SÓ da linha do Caixa: fundo alavancado
            # (ALT Light em setembro/2026, 126% do PL por um resgate grande)
            # fecha em 100% sem mexer nos outros grupos
            if self.f.cfg.get('alocacao_100') and 'Caixa' in serie.index:
                excesso = float(serie.sum()) - 1.0
                if excesso > 0:
                    serie = serie.copy()
                    serie['Caixa'] = max(0.0, serie['Caixa'] - excesso)
            return agrupar_tipos(serie, tabela)
        return agrupar_tipos(self.cart.get('tipos'), cadastro.tipo_label)

    def __init__(self, fundo, edicao, rent, cart, hist, hist12, taxa, perf,
                 comentario, avisos, calc=None):
        self.f = fundo
        self.edicao = edicao
        self.rent = rent or {}
        self.cart = cart
        self.hist = hist
        self.hist12 = hist12
        self.taxa = taxa
        self.perf = perf
        self.comentario = comentario or []
        self.avisos = avisos
        self._calc = calc

    # ------------------------------------------------------------- identidade
    @property
    def key(self):
        return self.f.key

    @property
    def nome(self):
        return self.f.nome

    @property
    def benchmark(self):
        return self.f.benchmark or 'CDI'

    @property
    def tem_dados(self):
        return bool(self.rent)

    @property
    def data_inicio(self):
        """Primeira cota do fundo.

        Cuidado com `rent['inicio']`: o cálculo grava a data ali e depois o laço
        dos períodos sobrescreve a mesma chave com o dicionário do período
        "desde o início". A data sobrevive só em `refs['inicio']`, porque para
        esse período a referência *é* a data de início.
        """
        refs = self.rent.get('refs') or {}
        return refs.get('inicio')

    # ---------------------------------------------------------- rentabilidade
    def valor(self, periodo, campo):
        """Float cru. None quando o período é maior que a vida do fundo."""
        p = self.rent.get(periodo)
        return p.get(campo) if p else None

    def texto(self, periodo, campo):
        """String pt-BR. '−' quando não há valor.

        O % do benchmark sai com 0 casas no Crédito Privado ("101% do CDI") e
        com 2 no Crédito Estruturado ("118,88%"), porque é assim nos relatórios
        publicados de cada vertical. Não é preferência de formatação: é o
        material que o investidor já recebeu.
        """
        v = self.valor(periodo, campo)
        if v is None:
            return fmt.MINUS
        if campo == 'pct':
            casas = int(self.f.cfg.get('casas_pct', 0))
            return fmt.num(v * 100, casas) + '%'
        return fmt.pct(v)

    @property
    def linhas_rentabilidade(self):
        """A tabela do relatório e do e-mail, nas 6 colunas de período.

        Ordem das linhas igual à dos relatórios publicados: Fundo, benchmark,
        Alfa e % do benchmark — e, no Crédito Estruturado, Fundo, CDI, % e CDI+
        (sem Alfa). Nos fundos de retorno absoluto só Fundo, benchmark e Alfa.
        É a mesma estrutura no relatório e no e-mail porque sai daqui.
        """
        fundo = [self.texto(p, 'fundo') for p in PERIODOS]
        bench = [self.texto(p, 'bench') for p in PERIODOS]
        if self.f.retorno_absoluto:
            return {'fundo': fundo, 'bench': bench, 'abs': fundo,
                    'alfa': [self.texto(p, 'alfa') for p in PERIODOS]}
        linhas = {'fundo': fundo, 'bench': bench,
                  'pct': [self.texto(p, 'pct') for p in PERIODOS]}
        # Alfa entra ACIMA do % do benchmark, não no lugar dele: oito dos nove
        # relatórios de Crédito Privado publicados trazem as quatro linhas
        # (Fundo, CDI, Alfa, %). A exceção é o Infra Plus CDI, que marca
        # `sem_alfa` em configs/fundos.yml.
        if not self.f.cfg.get('sem_alfa'):
            linhas['alfa'] = [self.texto(p, 'alfa') for p in PERIODOS]
        # O relatório de Crédito Estruturado publicado traz uma quarta linha,
        # "CDI+": o excesso sobre o benchmark anualizado em 252 d.u. É o número
        # que o gestor cita no comentário ("representando um desempenho de
        # CDI + 3,60%"), e sem ele a tabela do ALT não é a tabela do ALT.
        if self.f.cfg.get('linha_bench_mais'):
            linhas['bench_mais'] = [self.texto(p, 'bench_mais') for p in PERIODOS]
        return linhas

    # ------------------------------------------------------------------- PL
    @property
    def pl(self):
        return self.rent.get('pl')

    @property
    def pl_medio(self):
        return self.rent.get('pl_medio_12m')

    @property
    def pl_fmt(self):
        return fmt.brl(self.pl) if self.pl else fmt.MINUS

    @property
    def pl_medio_fmt(self):
        return fmt.brl(self.pl_medio) if self.pl_medio else fmt.MINUS

    # -------------------------------------------------------------- carteira
    @property
    def emissores(self):
        """[(nome, '12,34%', largura_barra_0_100)] — top 5."""
        if not self.cart:
            return []
        em = self.cart['emissores'].head(5)
        mx = em.max() if len(em) else 1
        return [(n, fmt.pct(v), round(v / mx * 100)) for n, v in em.items()]

    @property
    def setores(self):
        """Top N + Caixa no fim, como nos relatórios publicados.

        N é 5 no Crédito Privado — o relatório do Banks mostra duas linhas,
        Financeiro e Caixa, e nada mais. No Crédito Estruturado o publicado
        lista doze setores, então os fundos ALT marcam `setores_max: 12`.
        """
        if not self.cart:
            return []
        st = self.cart['setores']
        n = int(self.f.cfg.get('setores_max', 5))
        st = pd.concat([st[st.index != 'Caixa'].head(n), st[st.index == 'Caixa']])
        return [(n_, fmt.pct(v, 1), round(v * 100, 2)) for n_, v in st.items()]

    @property
    def setores_relatorio(self):
        """Setores como no relatório publicado: do maior para o menor, com o
        Caixa na posição do seu peso (no Institucional 30 ele é o 2º), duas
        casas. O Crédito Privado lista os 20 maiores; o ALT, `setores_max` (12).

        Corte separado de `setores` porque posts e e-mail usam o top 5 + Caixa.
        """
        if not self.cart:
            return []
        st = self.cart['setores']
        st = st[st > 0].sort_values(ascending=False)
        # o Institucional 30 publicado para nos 20 maiores (Têxtil e Calçados)
        n = self.f.cfg.get('setores_max_relatorio') or self.f.cfg.get('setores_max') or 20
        st = st.head(int(n))
        return [(n_, fmt.pct(v, 2), round(v * 100, 4)) for n_, v in st.items()]

    @property
    def rating_relatorio(self):
        """Rating do maior para o menor peso, todas as notas, duas casas."""
        if not self.cart:
            return []
        rt = self.cart['rating']
        rt = rt[rt > 0].sort_values(ascending=False)
        return [(n, fmt.pct(v, 2), round(v * 100, 4)) for n, v in rt.items()]

    @property
    def emissores_relatorio(self):
        """Top 5 emissores; '6,00%' sai '6%', como no publicado."""
        if not self.cart:
            return []
        em = self.cart['emissores'].head(5)
        return [(n, fmt.pct(v, 2).replace(',00%', '%'), round(v * 100, 4))
                for n, v in em.items()]

    @property
    def rating(self):
        if not self.cart:
            return []
        rt = self.cart['rating']
        rt = rt[rt > 0].head(6)
        mx = rt.max() if len(rt) else 1
        return [(n, fmt.pct(v, 1), max(1, round(v / mx * 100))) for n, v in rt.items()]

    @property
    def estrategia(self):
        """Alocação por estratégia (coluna Book) — usada no Crédito Estruturado."""
        if not self.cart or self.cart.get('estrategia') is None:
            return []
        e = self.cart['estrategia']
        return [(n, fmt.pct(v, 1), round(v * 100, 2)) for n, v in e.head(8).items()]

    def serie_diaria(self):
        """[(data, fundo, bench)] acumulados desde a primeira cota até a data
        base, em fração (0,2956 = 29,56%): o gráfico de rentabilidade
        histórica dos decks, que é diário."""
        c = getattr(self, '_calc', None)
        if c is None:
            return []
        sf = c.serie_fundo(self.f.quantum)
        if sf.empty:
            return []
        cota = sf['cota'][sf.index <= c.db].dropna()
        if cota.empty:
            return []
        idx = c.serie_indice(self.benchmark)
        idx = idx[~idx.index.duplicated()].sort_index()
        base_i = c.asof(idx, cota.index[0])
        ind = idx.reindex(idx.index.union(cota.index)).ffill().reindex(cota.index)
        c0 = float(cota.iloc[0])
        return [(d.to_pydatetime(), float(v) / c0 - 1, float(i) / base_i - 1)
                for (d, v), i in zip(cota.items(), ind.values)]

    @property
    def alocacao_hghy(self):
        """High Grade / High Yield / Caixa sobre o PL (páginas Saiba mais).

        O caixa vem marcado como HG na coluna HGHY; aqui ele sai do HG e vira
        linha própria, como na página publicada do HGD30.
        """
        bt = self.cart.get('hghy_tipo') if self.cart else None
        if bt is None:
            return []
        junto = {'Crédito High Grade': 0.0, 'Crédito High Yield': 0.0, 'Caixa': 0.0}
        for (hghy, tipo), v in bt.items():
            if str(tipo).strip().lower() == 'caixa':
                junto['Caixa'] += v
            elif str(hghy).strip().upper() == 'HY':
                junto['Crédito High Yield'] += v
            else:
                junto['Crédito High Grade'] += v
        return [(n, fmt.pct(v, 1), round(v * 100, 2)) for n, v in junto.items() if v > 0.0005]

    def rating_extras(self):
        """Fora das notas: Título Público (Book TPF) e S/rating (sem nota,
        fora o caixa). [(rótulo, '1,23%', 1.23)], só os que existem."""
        rb = self.cart.get('rating_book') if self.cart else None
        if rb is None:
            return []
        tp = sr = 0.0
        for (nota, book, tipo), v in rb.items():
            nota, book = str(nota).strip(), str(book).strip().upper()
            if book == 'TPF':
                tp += v
            elif nota.upper() in ('NA', 'NAN', 'N/A', '', 'S/RATING') and                     str(tipo).strip().lower() != 'caixa':
                sr += v
        return [(n, fmt.pct(v, 2), round(v * 100, 4))
                for n, v in (('Título Público', tp), ('S/rating', sr)) if v > 0.00005]

    def composicao(self, setores_bancarios=('Financeiro', 'Financeiro Corp')):
        """Composição da carteira dos materiais de previdência, na ordem do
        Informativo: Corporativo, Bancário, FIDC, Caixa.

        Caixa = tipo Caixa; FIDC = cota de FIDC; Bancário = emissor do setor
        financeiro (LF, LFSC, LFSN, CDB e também debênture de banco); o resto é
        Corporativo. Percentual sobre o total da carteira. Conferido com o
        Informativo do HGD30 de setembro/2026:
        28,3% / 36,1% / 7,2% / 28,4%.
        """
        ts = self.cart.get('tipo_setor') if self.cart else None
        if ts is None:
            return []
        junto = {'Corporativo': 0.0, 'Bancário': 0.0, 'FIDC': 0.0, 'Caixa': 0.0}
        for (tipo, setor, fidc), v in ts.items():
            tipo = str(tipo).strip()
            if tipo.lower() == 'caixa' or str(setor).strip() == 'Caixa':
                junto['Caixa'] += v
            elif bool(fidc) is True or tipo.upper().startswith('FIDC'):
                junto['FIDC'] += v
            elif str(setor).strip() in setores_bancarios:
                junto['Bancário'] += v
            else:
                junto['Corporativo'] += v
        # sobre o total da carteira (fecha 100%), não sobre o PL, como no Informativo
        tot = sum(junto.values()) or 1.0
        junto = {n: v / tot for n, v in junto.items()}
        return [(n, fmt.pct(v, 1), round(v * 100, 2)) for n, v in junto.items() if v > 0.0005]

    @property
    def carrego(self):
        return self.cart['carrego'] if self.cart else None

    @property
    def duration(self):
        return self.cart['duration'] if self.cart else None

    @property
    def carrego_fmt(self):
        return fmt.num(self.carrego * 100, 2) + '%' if self.carrego is not None else fmt.MINUS

    @property
    def duration_fmt(self):
        if self.duration is None:
            return fmt.MINUS
        return f'{fmt.num(self.duration, 2)} {"ano" if self.duration < 2 else "anos"}'

    @property
    def credito_fmt(self):
        return fmt.num(self.cart['credito'] * 100, 0) + '%' if self.cart else fmt.MINUS

    # --------------------------------------------------- texto com marcadores
    # O comentário do gestor cita números: "rendeu 1,10% no mês (100% do CDI)".
    # No processo atual esses números são digitados à mão no texto, e é por isso
    # que o relatório do Banks saiu dizendo 1,01% enquanto o e-mail dizia 1,23% —
    # dois textos, duas digitações, uma desatualizada.
    #
    # A alternativa que o gerador antigo usava era trocar o conteúdo de cada
    # <b>…</b> por posição. Funciona até o gestor acrescentar um negrito: aí os
    # valores entram no lugar errado, silenciosamente. (O próprio código avisava
    # "revisar à mão" quando a contagem não batia.)
    #
    # Aqui o gestor escreve o marcador e o sistema resolve. Posição não importa,
    # quantidade não importa, e um marcador inexistente aparece no texto como
    # {marcador_desconhecido} — visível na revisão, em vez de um número errado.
    MARCADORES = {
        'mes': ('mes', 'fundo'), 'ano': ('ano', 'fundo'),
        '12m': ('12m', 'fundo'), '24m': ('24m', 'fundo'),
        '36m': ('36m', 'fundo'), 'inicio': ('inicio', 'fundo'),
        'pct_mes': ('mes', 'pct'), 'pct_ano': ('ano', 'pct'),
        'pct_12m': ('12m', 'pct'), 'pct_inicio': ('inicio', 'pct'),
        'alfa_mes': ('mes', 'alfa'), 'alfa_ano': ('ano', 'alfa'),
        'alfa_12m': ('12m', 'alfa'),
        'bench_mes': ('mes', 'bench'), 'bench_ano': ('ano', 'bench'),
        'bench_12m': ('12m', 'bench'), 'bench_24m': ('24m', 'bench'),
        'bench_36m': ('36m', 'bench'), 'bench_inicio': ('inicio', 'bench'),
        'bench_mais_inicio': ('inicio', 'bench_mais'),
        'bench_mais_12m': ('12m', 'bench_mais'),
    }

    def pct_anualizado(self, periodo='inicio'):
        """% do benchmark em base anualizada.

        Não é o mesmo que `pct`. `pct` divide os retornos acumulados; sobre vários
        anos isso não é o número que o gestor chama de "desempenho anualizado de
        122% do CDI" — esse divide os retornos *anualizados*. Em período longo os
        dois divergem bastante, e usar um pelo outro põe no relatório um número
        que não se reproduz.
        """
        p = self.rent.get(periodo)
        refs = self.rent.get('refs') or {}
        if not p or periodo not in refs:
            return None
        f, b = p.get('fundo'), p.get('bench')
        if f is None or b is None:
            return None
        import numpy as _np
        if _np.isnan(f) or _np.isnan(b):
            return None
        n = self._du_do_periodo(periodo)
        if not n or n <= 0:
            return None
        fa = (1 + f) ** (252 / n) - 1
        ba = (1 + b) ** (252 / n) - 1
        return (fa / ba) if ba else None

    def _du_do_periodo(self, periodo):
        """Dias úteis entre a referência do período e a data base."""
        refs = self.rent.get('refs') or {}
        ref = refs.get(periodo)
        if ref is None or self._calc is None:
            return None
        try:
            return self._calc.du(ref, self.edicao.db)
        except Exception:
            return None

    def preencher(self, texto):
        """Resolve {marcadores} de um texto do gestor. Devolve (texto, faltando).

        Antes, os números das frases-padrão ("rentabilidade de X% no mês (Y% do
        CDI)…") são trocados pelos da tabela (engine/sincroniza.py), para o
        comentário nunca contradizer a rentabilidade publicada.
        """
        import re as _re
        from engine.sincroniza import sincronizar
        texto, trocas = sincronizar(self, texto)
        for antes, depois in trocas:
            msg = f'comentário ajustado à tabela: {antes} → {depois}'
            if msg not in self.avisos:
                self.avisos.append(msg)
        faltando = []

        def troca(m):
            chave = m.group(1).strip()
            if chave in self.MARCADORES:
                per, campo = self.MARCADORES[chave]
                return self.texto(per, campo)
            if chave.startswith('pct_anual'):
                per = chave.replace('pct_anual_', '') or 'inicio'
                v = self.pct_anualizado(per if per != 'pct_anual' else 'inicio')
                return fmt.pct_cdi(v) if v is not None else fmt.MINUS
            fixos = {
                'bench': self.benchmark,
                'nome': self.nome,
                'carrego': self.carrego_fmt,
                'duration': self.duration_fmt,
                'credito': self.credito_fmt,
                'pl': self.pl_fmt,
                'pl_medio': self.pl_medio_fmt,
                'data_base': self.edicao.br,
                'mes_ano': self.edicao.mes_ano,
                'mes_nome': self.edicao.mes_nome.lower(),
            }
            if chave in fixos:
                return str(fixos[chave])
            faltando.append(chave)
            return m.group(0)

        saida = _re.sub(r'\{([a-z_0-9]{2,24})\}', troca, texto or '')
        return saida, faltando

    # Abertura padrão dos ALT: a mesma frase todo mês, só os números mudam.
    # `abertura: alt` no fundo (configs/fundos.yml) liga.
    ABERTURA_ALT = ('O {nome} registrou rentabilidade de {mes} no mês, equivalente a '
                    '{pct_mes} do {bench} no período. Desde o início da estratégia, o '
                    'fundo acumula retorno de {inicio}, frente a {bench_inicio} do {bench}, '
                    'o que corresponde a um desempenho anualizado de {pct_inicio} do {bench}.')

    def _abertura(self):
        if self.f.cfg.get('abertura') != 'alt':
            return None
        return self.ABERTURA_ALT

    @property
    def comentario_preenchido(self):
        """Parágrafos do gestor com os marcadores já resolvidos.

        Nos fundos com `abertura: alt`, o primeiro parágrafo é a abertura
        padrão com os números da tabela: substitui a do gestor quando ela
        existe ("O Tivio ALT … registrou rentabilidade…") e entra no topo
        quando não existe.
        """
        import re as _re
        paragrafos = list(self.comentario)
        modelo = self._abertura()
        if modelo:
            if paragrafos and _re.match(r'\s*O\s+Tivio\s+ALT\b.*registrou\s+rentabilidade',
                                        paragrafos[0], _re.I | _re.S):
                paragrafos[0] = modelo
            else:
                paragrafos.insert(0, modelo)
        out, faltas = [], []
        for p in paragrafos:
            txt, falta = self.preencher(p)
            out.append(txt)
            faltas += falta
        if faltas:
            self.avisos.append('marcadores desconhecidos no comentário: '
                               + ', '.join('{%s}' % f for f in sorted(set(faltas))))
        return out

    # ------------------------------------------------------------- utilidades
    def __repr__(self):
        return f'<Contexto {self.key} {"com dados" if self.tem_dados else "SEM dados"}>'


class Contexto:
    """Fábrica de contextos. Calcula uma vez por fundo e guarda."""

    # Campos que a aba Overrides pode forçar. A lista é fechada de propósito:
    # um override é uma exceção pontual ("o número saiu errado e eu preciso
    # publicar hoje"), não uma segunda forma de configurar o fundo. Abrir para
    # qualquer campo transformaria a planilha numa config paralela, que é
    # exatamente o que este ambiente veio desfazer.
    #
    # Aplicados no CONTEXTO, não no material: assim valem igual no relatório, no
    # post e no e-mail. Antes só chegavam nos materiais da Central, e um override
    # mudava o post sem mudar o relatório — a divergência que o projeto combate,
    # criada pela própria ferramenta de correção.
    OVERRIDES = {
        'taxa': str, 'perf': str,
        'carrego': float, 'duration': float,
        'pl': float, 'pl_medio': float,
    }

    def __init__(self, calc, cadastro, taxas, comentarios, edicao, log=None,
                 overrides=None):
        self.calc = calc
        self.cad = cadastro
        self.tx = taxas
        self.com = comentarios
        self.edicao = edicao
        self.log = log
        self.ov = overrides or {}
        self._cache = {}

    def de(self, key):
        key = self.cad.alias.get(key, key)
        if key in self._cache:
            return self._cache[key]
        f = self.cad.get(key)
        if f is None:
            self._cache[key] = None
            return None

        avisos = []
        if not f.resolvido:
            avisos.append('fundo não encontrado na DePara — material mantido como estava')
            ctx = ContextoFundo(f, self.edicao, None, None, None, None, None, None, [], avisos, self.calc)
            self._cache[key] = ctx
            return ctx

        rent = self.calc.rentabilidade(f.quantum, f.benchmark)
        if not rent:
            avisos.append(f'sem cotas para "{f.quantum}" na dados_mensais — material mantido')
            ctx = ContextoFundo(f, self.edicao, None, None, None, None, None, None, [], avisos, self.calc)
            self._cache[key] = ctx
            return ctx

        cart = self.calc.carteira(f.carteira, f.mesa, rent['pl'])
        if cart is None:
            avisos.append('sem carteira na Base Carteira — alocação, carrego e duration mantidos')
        elif cart['data'] is None:
            avisos.append('carteira sem data na Base Carteira — os números saem, mas '
                          'não há como confirmar que a posição é a do mês')
        else:
            # a carteira pode estar atrasada em relação à cota; é um erro comum
            # e silencioso, porque o número aparece, só está do mês errado
            atraso = (self.edicao.db - pd.Timestamp(cart['data'])).days
            if atraso > 45:
                avisos.append(f'carteira de {pd.Timestamp(cart["data"]):%d/%m/%Y} — '
                              f'{atraso} dias antes da data base')

        hist = self.calc.historico(f.quantum, f.benchmark, f.cota_inicial, f.data_inicial)
        fator = f.cfg.get('bench_tributado')
        if hist and fator:
            hist = dict(hist, t=[round(v * float(fator), 2) for v in hist['c']])
        hist12 = self.calc.historico(f.quantum, f.benchmark, janela_meses=12)

        # o CNPJ do relatório publicado (cnpj_exibido) vence o da DePara também
        # na busca da taxa: no Legacy o da DePara é outra classe, com taxa 0%
        cnpj_tx = f.cfg.get('cnpj_exibido') or f.cnpj
        taxa = self.tx.global_(key, cnpj_tx, f.quantum)
        perf = self.tx.performance(key, cnpj_tx, None, f.quantum)
        # O texto publicado em configs/fundos.yml (`taxa`, `performance`) vence
        # a taxas_global.xlsx: nos ALT a planilha diverge do relatório
        # publicado (ALT 90 2,43% x 1,25%; ALT Light 0,65% x 1,15%).
        if f.cfg.get('taxa'):
            taxa = str(f.cfg['taxa'])
        if f.cfg.get('performance'):
            perf = str(f.cfg['performance'])
        if taxa is None:
            avisos.append('taxa global não encontrada na taxas_global.xlsx')

        coment = self.com.relatorio(key, f.nome)
        for apelido in f.apelidos:
            if coment:
                break
            coment = self.com.relatorio(key, apelido)

        ctx = ContextoFundo(f, self.edicao, rent, cart, hist, hist12, taxa, perf,
                            coment, avisos, self.calc)
        self._aplicar_overrides(key, ctx)
        if self.log:
            for a in avisos:
                self.log.aviso(f.key, a)
        self._cache[key] = ctx
        return ctx

    def _aplicar_overrides(self, key, ctx):
        """Força os valores da aba Overrides, com registro no log.

        Um valor forçado some do rastro se ninguém anotar: no mês seguinte
        ninguém lembra por que aquele carrego estava diferente do calculado.
        Por isso cada override vira linha de aviso, com o valor que ele
        substituiu.
        """
        for campo, valor in (self.ov.get(key) or {}).items():
            if campo == 'casas_taxa':
                continue      # tratado em loaders/taxas.py
            tipo = self.OVERRIDES.get(campo)
            if tipo is None:
                ctx.avisos.append(f'override de "{campo}" ignorado — campos aceitos: '
                                  + ', '.join(sorted(self.OVERRIDES)))
                continue
            try:
                novo = tipo(str(valor).replace('%', '').replace(',', '.')
                            if tipo is float else valor)
            except (TypeError, ValueError):
                ctx.avisos.append(f'override de "{campo}": não consegui ler {valor!r} '
                                  f'como {tipo.__name__}')
                continue
            if campo in ('taxa', 'perf'):
                antes = getattr(ctx, campo)
                setattr(ctx, campo, novo)
            elif campo in ('carrego', 'duration'):
                if not ctx.cart:
                    ctx.avisos.append(f'override de "{campo}" ignorado — o fundo não '
                                      f'tem carteira nesta edição')
                    continue
                antes = ctx.cart.get(campo)
                ctx.cart[campo] = novo
            else:
                chave = {'pl': 'pl', 'pl_medio': 'pl_medio_12m'}[campo]
                antes = ctx.rent.get(chave)
                ctx.rent[chave] = novo
            ctx.avisos.append(f'override: {campo} forçado para {novo!r} '
                              f'(calculado: {antes!r})')

    def todos(self, keys=None):
        keys = keys or [f.key for f in self.cad]
        return [c for c in (self.de(k) for k in keys) if c is not None]
