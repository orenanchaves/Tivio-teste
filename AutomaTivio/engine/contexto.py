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


class ContextoFundo:
    """Tudo sobre um fundo nesta edição. Só leitura."""

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
        """String pt-BR. '−' quando não há valor."""
        v = self.valor(periodo, campo)
        if v is None:
            return fmt.MINUS
        return fmt.pct_cdi(v) if campo == 'pct' else fmt.pct(v)

    @property
    def linhas_rentabilidade(self):
        """A tabela do relatório e do e-mail, nas 6 colunas de período.

        Ordem das linhas igual à dos materiais: fundo, benchmark e, embaixo,
        % do benchmark — ou Alfa, nos fundos de retorno absoluto. É a mesma
        estrutura nos dois materiais porque sai daqui.
        """
        fundo = [self.texto(p, 'fundo') for p in PERIODOS]
        bench = [self.texto(p, 'bench') for p in PERIODOS]
        if self.f.retorno_absoluto:
            return {'fundo': fundo, 'bench': bench, 'abs': fundo,
                    'alfa': [self.texto(p, 'alfa') for p in PERIODOS]}
        return {'fundo': fundo, 'bench': bench,
                'pct': [self.texto(p, 'pct') for p in PERIODOS]}

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
        """Top 5 + Caixa no fim, como nos relatórios."""
        if not self.cart:
            return []
        st = self.cart['setores']
        st = pd.concat([st[st.index != 'Caixa'].head(5), st[st.index == 'Caixa']])
        return [(n, fmt.pct(v, 1), round(v * 100, 2)) for n, v in st.items()]

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
        """Resolve {marcadores} de um texto do gestor. Devolve (texto, faltando)."""
        import re as _re
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

    @property
    def comentario_preenchido(self):
        """Parágrafos do gestor com os marcadores já resolvidos."""
        out, faltas = [], []
        for p in self.comentario:
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
        hist12 = self.calc.historico(f.quantum, f.benchmark, janela_meses=12)

        taxa = self.tx.global_(key, f.cnpj, f.quantum)
        perf = self.tx.performance(key, f.cnpj, None, f.quantum)
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
