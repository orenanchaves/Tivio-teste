# -*- coding: utf-8 -*-
"""Abas de Investment Solutions ("Low Vol", "TOP Credit") montadas pela API TLDR.

Devolve a MESMA grade que `loaders/abas_is.ler_abas` lê da planilha, com os
blocos nas mesmas células. Assim os gráficos, as cascatas e a tabela de PnL dos
decks (que guardam a fórmula `'Low Vol'!$T$6:$T$13`) seguem funcionando sem
mudança.

De onde vem cada bloco:
  PL (E2) e volatilidade 12m (H2)   visao-geral        (pl_atual, vol_aa)
  PnL por estratégia (B:E, G:H...)  pnl/explosao       Alpha da planilha = Alpha + Trade da API
  Low Vol: macro-estratégia         agrupamento=book   o 1º/2º nível do book vira a macro
  TOP Credit: classe do ativo       agrupamento=class
  TOP Credit: PnL por emissor       agrupamento=economic_group
  Low Vol: exposição (R$ M, % PL)   alocacao (by_book)
  TOP Credit: emissores (% PL)      emissores
  TOP Credit: tipo                  alocacao (by_class)  -- ATENÇÃO: a base difere da planilha
                                    (Caixa 37% na API x 44% na planilha); sai com aviso
"""
import collections

_MAX_LIN, _MAX_COL = 30, 30


def _col(letras):
    n = 0
    for ch in letras.upper():
        n = n * 26 + (ord(ch) - 64)
    return n - 1


class _Grade:
    def __init__(self):
        self.g = [[None] * _MAX_COL for _ in range(_MAX_LIN)]

    def put(self, col, lin, valor):
        self.g[lin - 1][_col(col)] = valor

    def bloco(self, col0, lin0, linhas):
        """Escreve `linhas` (listas) a partir de (col0, lin0)."""
        c0 = _col(col0)
        for i, linha in enumerate(linhas):
            for j, v in enumerate(linha):
                self.g[lin0 - 1 + i][c0 + j] = v


def _macro_book(book):
    """Book do Risco -> macro-estratégia da aba Low Vol."""
    seg = [s.strip() for s in str(book).split('>>')]
    if seg[0] == 'Juros' and len(seg) > 1:
        return 'Juros ' + seg[1]
    if seg[0] in ('FX', 'Termo', 'IBOV', 'Offshore', 'Provisões'):
        return seg[0]
    if seg[0] in ('Padrão', 'Caixa'):
        return 'Caixa'
    return 'Crédito'


def _pnl_mes(api, cod, agrupamento, chave=lambda x: x):
    """{grupo: (alpha, bench)}; alpha da planilha = Alpha + Trade da API."""
    linhas = api.get(f'/v1/carteira/fundos/{cod}/pnl/explosao', agrupamento=agrupamento, **api._q)
    acc = collections.defaultdict(lambda: [0.0, 0.0])
    for x in linhas:
        if x['period'] != 'month':
            continue
        a = acc[chave(x['group_name'])]
        if x['attribution_type'] == 'Bench':
            a[1] += x['bps']
        else:
            a[0] += x['bps']
    return {k: tuple(v) for k, v in acc.items() if abs(v[0]) + abs(v[1]) > 1e-9}


def _ordenado(pnl, excluir=()):
    """[(nome, alpha, bench)] por alpha decrescente (empate: ordem original)."""
    itens = [(k, a, b) for k, (a, b) in pnl.items() if k not in excluir]
    return sorted(itens, key=lambda t: -t[1])


def _cabecalho(gr):
    gr.put('B', 4, 'PnL (bps)')
    gr.bloco('B', 5, [['Estratégia', 'Alpha', 'Bench', 'Total']])
    gr.bloco('G', 5, [['Estratégia', 'PnL']])
    gr.put('M', 3, 'TOP 5 contribuições de performance attiribution (bps)')
    gr.put('M', 27, 'Maiores Exposições do portfólio')
    gr.put('G', 2, 'Vol')


def _tabela_pnl(gr, itens, cascata_crescente):
    """B:E (tabela), G:H (cascata) e a linha Total."""
    linhas = [[n, a, b, a + b] for n, a, b in itens]
    ta, tb = sum(a for _, a, _ in itens), sum(b for _, _, b in itens)
    linhas.append(['Total', ta, tb, ta + tb])
    gr.bloco('B', 6, linhas)
    casc = sorted(itens, key=lambda t: t[1], reverse=not cascata_crescente)
    gr.bloco('G', 6, [['CDI', tb]] + [[n, a] for n, a, _ in casc])


def _low_vol(api, cod, gr):
    itens = _ordenado(_pnl_mes(api, cod, 'book', chave=_macro_book))
    _tabela_pnl(gr, itens, cascata_crescente=True)
    gr.bloco('J', 5, [['Estratégia', 'PnL']])
    gr.bloco('J', 6, [[n, a] for n, a, _ in itens])

    aloc = api.get(f'/v1/carteira/fundos/{cod}/alocacao', **api._q)
    pl = aloc['pl'] or 0
    exp = collections.defaultdict(float)
    for b in aloc['by_book']:
        exp[_macro_book(b['label'])] += b['exposure']
    expo = sorted(((k, v) for k, v in exp.items() if k != 'Provisões'), key=lambda t: -t[1])
    gr.bloco('T', 5, [['Estratégia', 'Exp (R$ M)', '% PL']])
    gr.bloco('T', 6, [[k, v / 1e6, v / pl if pl else None] for k, v in expo])
    gr.bloco('X', 5, [['Estratégia', 'PnL']])
    gr.bloco('X', 6, [[n, a] for n, a, _ in itens if n != 'Caixa'])
    gr.bloco('AA', 5, [['Estratégia', '% PL']])
    gr.bloco('AA', 6, [[k, v / pl if pl else None] for k, v in expo if k != 'Caixa'])


_TIPOS_TOP_CREDIT = ['Caixa', 'FIDC Sr', 'CDB', 'Debênture', 'LF', 'LFSC', 'LFSN']
_NAO_EMISSOR = {'Caixa', 'Provisões', 'NC', ''}


def _top_credit(api, cod, gr, log):
    itens = _ordenado(_pnl_mes(api, cod, 'class'), excluir={'NC'})
    _tabela_pnl(gr, itens, cascata_crescente=False)

    emis = _pnl_mes(api, cod, 'economic_group')
    top = sorted(((k, a + b) for k, (a, b) in emis.items() if k not in _NAO_EMISSOR),
                 key=lambda t: -t[1])[:5]
    gr.bloco('J', 5, [['Emissor', 'PnL']])
    gr.bloco('J', 6, [[k, v] for k, v in top])

    em = api.get(f'/v1/carteira/fundos/{cod}/emissores', **api._q)
    pct = sorted(((x['issuer'], x['exposure_pct'] / 100) for x in em
                  if x['issuer'] not in _NAO_EMISSOR), key=lambda t: -t[1])[:5]
    gr.bloco('T', 5, [['Emissor', '% PL']])
    gr.bloco('T', 6, [[k, v] for k, v in pct])

    por_classe = {b['label']: b['pct'] / 100
                  for b in api.get(f'/v1/carteira/fundos/{cod}/alocacao', **api._q)['by_class']}
    gr.bloco('W', 5, [['Tipo', '%']])
    gr.bloco('W', 6, [[t, por_classe[t]] for t in _TIPOS_TOP_CREDIT if t in por_classe])
    log.aviso('abas_is', 'TOP Credit: o quadro "Tipo" vem da alocação da API (% da exposição); '
                         'a planilha usava outra base (ex.: Caixa 44% x 37%). Conferir com a gestão.')


_MONTADORES = {'Low Vol': _low_vol, 'TOP Credit': _top_credit}


def ler_abas_api(api, abas, data_base, signoff, log):
    """{aba: grade} para `abas` = {nome_da_aba: id_portfolio}; o que a API não monta fica de fora."""
    out = {}
    api._q = {'data': data_base, 'signoff': 'true' if signoff in (True, 'true', 'True') else 'false'}
    for nome, cod in abas.items():
        montar = _MONTADORES.get(nome)
        if not montar:
            continue
        try:
            vg = api.get(f'/v1/carteira/fundos/{cod}/visao-geral', **api._q) or {}
            if not vg:
                log.aviso('abas_is', f'aba "{nome}": o id {cod} não existe na API')
                continue
            gr = _Grade()
            _cabecalho(gr)
            gr.put('E', 2, (vg.get('pl_atual') or 0) / 1e6)
            gr.put('H', 2, vg.get('vol_aa'))
            if montar is _top_credit:
                montar(api, cod, gr, log)
            else:
                montar(api, cod, gr)
            out[nome] = gr.g
            log.info(f'  aba "{nome}" montada pela API (fundo {cod})')
        except Exception as e:  # noqa: BLE001
            log.aviso('abas_is', f'aba "{nome}" não montada pela API ({e!r}); usa a planilha')
    return out
