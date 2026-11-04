# -*- coding: utf-8 -*-
"""Compara a dados_mensais.xlsx com a API TLDR e grava um Excel com o que a API
cobre, o que falta e a diferença numérica, fundo a fundo.

    python docs/comparar_api_planilha.py [--data-base 2026-09-30] [--signoff false]
                                         [--saida nova_doc/comparativo_api_vs_planilha.xlsx]

Token: DefaultAzureCredential (se o azure-identity estiver instalado) ou
`az account get-access-token` — a mesma identidade do `az login`.
"""
import argparse
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd
import requests

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from calculators.metricas import Calc  # noqa: E402
from engine.cadastro import Cadastro  # noqa: E402
from loaders.planilha import ler_dados_mensais  # noqa: E402

BASE = 'https://wa-tivio-tldr-brsouth.azurewebsites.net'
ESCOPO = 'api://ae37bc8e-f16d-47fb-99ab-9d3dd0cc2201/.default'


def token():
    try:
        from azure.identity import DefaultAzureCredential
        return DefaultAzureCredential().get_token(ESCOPO).token
    except Exception:
        return subprocess.check_output(
            ['az', 'account', 'get-access-token', '--scope', ESCOPO,
             '--query', 'accessToken', '-o', 'tsv'], text=True).strip()


class Api:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers['Authorization'] = 'Bearer ' + token()

    def get(self, caminho, **q):
        r = self.s.get(BASE + caminho, params=q, timeout=90)
        r.raise_for_status()
        return r.json()


def digitos(x):
    return re.sub(r'\D', '', str(x or ''))


def pct(v):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v)


def dif(a, b):
    a, b = pct(a), pct(b)
    return None if a is None or b is None else a - b


# ---------------------------------------------------------------- planilha
def rent_planilha(calc, f):
    r = calc.rentabilidade(f.quantum, f.benchmark)
    if not r:
        return None
    return r


PERIODOS = [('mes', 'rent_mtd', 'pct_bench_mtd'), ('ano', 'rent_ytd', 'pct_bench_ytd'),
            ('12m', 'rent_12m', 'pct_bench_12m'), ('24m', 'rent_24m', 'pct_bench_24m'),
            ('36m', None, None), ('inicio', 'rent_inception', 'pct_bench_inception')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-base')
    ap.add_argument('--signoff', default='false')
    ap.add_argument('--saida', default=os.path.join(RAIZ, 'nova_doc', 'comparativo_api_vs_planilha.xlsx'))
    a = ap.parse_args()

    print('lendo planilha (cache)…')
    dados = ler_dados_mensais(os.path.join(RAIZ, 'entrada', 'dados_mensais.xlsx'), log=lambda *x: None)
    calc = Calc(dados, a.data_base)
    db = calc.db.strftime('%Y-%m-%d')
    cad = Cadastro(os.path.join(RAIZ, 'configs', 'fundos.yml'), dados['depara'])
    api = Api()
    sg = a.signoff.lower()
    print(f'data base {db} · signoff={sg}')

    lista = api.get('/v1/carteira/rentabilidade/fundos', data=db, ultima_cota='true', signoff=sg)
    por_cnpj = {digitos(x['cnpj']): x for x in lista if x.get('cnpj')}

    match, rent, serie, cart, cart_cortes = [], [], [], [], []
    for f in cad:
        lin = {'chave': f.key, 'fundo': f.nome, 'carteira (planilha)': f.carteira if f.resolvido else None,
               'cnpj (planilha)': f.cnpj, 'benchmark (planilha)': f.benchmark}
        item = por_cnpj.get(digitos(f.cnpj)) if f.resolvido else None
        if not item:
            lin.update({'id_portfolio (API)': None, 'nome (API)': None, 'situação': 'SEM MATCH POR CNPJ'})
            match.append(lin)
            continue
        cod = int(item['portfolio_id'])
        lin.update({'id_portfolio (API)': cod, 'nome (API)': item['fund_name'],
                    'benchmark (API)': item['benchmark_symbol'],
                    'desk (API)': item['desk_label'],
                    'benchmark igual?': 'sim' if str(f.benchmark).upper() == str(item['benchmark_symbol']).upper() else 'NÃO',
                    'situação': 'ok'})
        try:
            vg = api.get(f'/v1/carteira/fundos/{cod}/visao-geral', data=db, signoff=sg)
        except Exception as e:  # noqa: BLE001
            lin['situação'] = f'visao-geral falhou: {e}'
            match.append(lin)
            continue
        match.append(lin)

        # ---- rentabilidade
        rp = rent_planilha(calc, f)
        if rp:
            for p, kr, kp in PERIODOS:
                x = rp.get(p)
                pl_f = x['fundo'] if x else None
                pl_p = x['pct'] if x else None
                ap_f = vg.get(kr) if kr else None
                ap_p = vg.get(kp) if kp else None
                if p == 'inicio' and ap_f is None:
                    ap_f = 'nulo na API'
                rent.append({
                    'chave': f.key, 'período': p,
                    'rent planilha': pct(pl_f), 'rent API': ap_f if isinstance(ap_f, str) else pct(ap_f),
                    'dif (p.p.)': dif(pl_f, ap_f) * 100 if not isinstance(ap_f, str) and dif(pl_f, ap_f) is not None else None,
                    '% bench planilha': pct(pl_p), '% bench API': pct(ap_p),
                    'dif % bench (p.p.)': dif(pl_p, ap_p) * 100 if dif(pl_p, ap_p) is not None else None,
                    'situação': ('não existe na API' if kr is None else
                                 'nulo na API' if ap_f is None or isinstance(ap_f, str) else 'ok'),
                })

        # ---- cota / PL / benchmark / data inicial
        cotas = pd.DataFrame(api.get(f'/v1/carteira/fundos/{cod}/cotas',
                                     inicio=(vg.get('official_initial_date') or '2000-01-01'), signoff=sg))
        if not cotas.empty:
            cotas['data'] = pd.to_datetime(cotas['data_referencia'])
            cotas = cotas[cotas['data'] <= calc.db].set_index('data')
        sf = calc.serie_fundo(f.quantum)
        comum = sf.index.intersection(cotas.index) if len(cotas) else []
        dc = (sf.loc[comum, 'cota'] - cotas.loc[comum, 'cota']).abs() if len(comum) else pd.Series(dtype=float)
        dpl = ((sf.loc[comum, 'pl'] - cotas.loc[comum, 'pl'] * 1e6).abs() / sf.loc[comum, 'pl']) if len(comum) else pd.Series(dtype=float)
        idx_p = calc.serie_indice(f.benchmark)
        try:
            bm = pd.DataFrame(api.get('/v1/carteira/benchmarks', symbol=item['benchmark_symbol'],
                                      inicio=db[:4] + '-01-01', fundo=cod, signoff=sg))
            bm['data'] = pd.to_datetime(bm['data_referencia'])
            bm = bm[bm['data'] <= calc.db].set_index('data')['valor']
        except Exception:  # noqa: BLE001
            bm = pd.Series(dtype=float)
        ci = idx_p.index.intersection(bm.index)
        dbm = (((idx_p.loc[ci] / idx_p.loc[ci].iloc[0]) / (bm.loc[ci] / bm.loc[ci].iloc[0])) - 1).abs() if len(ci) else pd.Series(dtype=float)
        serie.append({
            'chave': f.key, 'data base': db, 'última cota API': vg.get('last_date'),
            'data inicial (planilha)': f.data_inicial if pd.notna(f.data_inicial) else None,
            'data inicial (API official_initial_date)': vg.get('official_initial_date'),
            'cota inicial (planilha)': f.cota_inicial,
            'primeira cota da série API': float(cotas['cota'].iloc[0]) if len(cotas) else None,
            'cota final planilha': float(sf['cota'].iloc[-1]) if len(sf) else None,
            'cota final API (visao-geral)': vg.get('cota_atual'),
            'pontos de cota planilha': len(sf), 'pontos de cota API (≤ data base)': len(cotas),
            'dias em comum': len(comum),
            'maior dif. de cota nos dias em comum': pct(dc.max()) if len(dc) else None,
            'PL planilha (R$)': rp['pl'] if rp else None, 'PL API visao-geral (R$)': vg.get('pl_atual'),
            'dif PL (%)': (rp['pl'] / vg['pl_atual'] - 1) * 100 if rp and vg.get('pl_atual') else None,
            'maior dif. relativa de PL (série, %)': pct(dpl.max() * 100) if len(dpl) else None,
            'PL médio 12m planilha': rp['pl_medio_12m'] if rp else None,
            'PL médio 12m (calc. na série API)': float(cotas['pl'][cotas.index >= rp['refs']['12m']].mean() * 1e6) if rp and len(cotas) else None,
            'PL médio 12m na API pronto?': 'não',
            'dias do benchmark em comum (ano corrente)': len(ci),
            'maior dif. relativa do índice (normalizado no 1º dia comum)': pct(dbm.max()) if len(dbm) else None,
            'obs. benchmark': 'API devolveu vazio' if bm.empty else '',
        })

        # ---- carteira
        pos = api.get(f'/v1/carteira/fundos/{cod}/posicoes', data=db, visao='expandida', signoff=sg)
        pp = pd.DataFrame(pos.get('positions') or [])
        pl_ref = rp['pl'] if rp else vg.get('pl_atual')
        cp = calc.carteira(f.carteira, f.mesa, pl_ref) if rp else None
        c = dados['carteira']
        c = c[c['Carteira'] == f.carteira]
        c = c[c['Data'] == c['Data'].max()] if c['Data'].notna().any() else c
        reg = {'chave': f.key, 'linhas planilha': len(c), 'linhas API': len(pp),
               'data carteira planilha': cp['data'].strftime('%Y-%m-%d') if cp and cp['data'] is not None else None}
        if len(pp):
            exp = pp['exposure'].astype(float)
            reg.update({
                'exposição total planilha (R$)': float(c['Exposição'].sum()),
                'exposição total API (R$)': float(exp.sum()),
                'carrego planilha': cp['carrego'] if cp else None,
                'carrego API (Σspread/100×exposição/PL)': float((pp['spread'].fillna(0) / 100 * exp).sum() / pl_ref) if pl_ref else None,
                'duration planilha (anos)': cp['duration'] if cp else None,
                'duration API (Σduration×exposição/PL)': float((pp['duration'].fillna(0) * exp).sum() / pl_ref) if pl_ref else None,
                'crédito planilha (%PL)': cp['credito'] if cp else None,
                'avisos API': '; '.join(map(str, pos.get('avisos') or [])),
            })
            for col in ('issuer', 'sector', 'instrument_class', 'book_name'):
                reg[f'API distintos {col}'] = int(pp[col].nunique())
            # cortes: planilha x API em % do PL
            pares = [('Emissor', 'issuer', 'emissores'), ('Setor', 'sector', 'setores'),
                     ('Tipo', 'instrument_class', 'tipos'), ('Book', 'book_name', 'estrategia')]
            for col_p, col_a, chave in pares:
                gp = (c.groupby(col_p)['Exposição'].sum() / pl_ref) if col_p in c.columns else pd.Series(dtype=float)
                ga = pp.groupby(col_a)['exposure'].sum() / pl_ref
                nomes = sorted(set(gp.index) | set(ga.index), key=lambda n: -max(abs(gp.get(n, 0)), abs(ga.get(n, 0))))
                for n in nomes[:40]:
                    cart_cortes.append({'chave': f.key, 'corte': col_p, 'rótulo': n,
                                        '% PL planilha': float(gp.get(n, np.nan)) if n in gp.index else None,
                                        '% PL API': float(ga.get(n, np.nan)) if n in ga.index else None,
                                        'dif (p.p.)': (float(gp.get(n, 0)) - float(ga.get(n, 0))) * 100,
                                        'só em': 'planilha' if n not in ga.index else 'API' if n not in gp.index else 'ambos'})
            reg['colunas da posição API'] = ', '.join(pp.columns)
        cart.append(reg)
        print(f'  {f.key}: ok (id {cod})')

    # ---- campos
    campos = pd.DataFrame(CAMPOS, columns=['dado usado no relatório', 'planilha hoje', 'API', 'situação', 'observação'])

    os.makedirs(os.path.dirname(a.saida), exist_ok=True)
    with pd.ExcelWriter(a.saida, engine='openpyxl') as w:
        pd.DataFrame(DIVERGENCIAS, columns=['fundo', 'tema', 'planilha', 'API', 'situação'])\
            .to_excel(w, sheet_name='Divergências conhecidas', index=False)
        campos.to_excel(w, sheet_name='O que falta', index=False)
        pd.DataFrame(match).to_excel(w, sheet_name='Fundos x id_portfolio', index=False)
        pd.DataFrame(rent).to_excel(w, sheet_name='Rentabilidade', index=False)
        pd.DataFrame(serie).to_excel(w, sheet_name='Cota, PL e benchmark', index=False)
        pd.DataFrame(cart).to_excel(w, sheet_name='Carteira (resumo)', index=False)
        pd.DataFrame(cart_cortes).to_excel(w, sheet_name='Carteira (cortes)', index=False)
        for ws in w.book.worksheets:
            ws.freeze_panes = 'B2'
            for col in ws.columns:
                tam = max(len(str(cel.value)) if cel.value is not None else 0 for cel in col[:60])
                ws.column_dimensions[col[0].column_letter].width = min(max(12, tam + 2), 60)
    print('gravado:', a.saida)


# Divergências já conhecidas e mantidas de propósito, para o time ter ciência.
# Valores de 30/09/2026; conferir de novo quando a API ou a planilha mudar.
DIVERGENCIAS = [
    ('topgestorlongonly', 'Benchmark errado', 'Ibovespa', 'IBOV', 'Mantido: nomes diferentes para o mesmo índice, conferir a série'),
    ('topmanagerglobal', 'Benchmark errado', 'MSCI ACWI', 'MSCI + Dólar 2D', 'Mantido: rentabilidade difere ~1 p.p. no mês, ano e 12m'),
    ('esplanada', 'Benchmark errado', 'IMA-B 5', 'IMA-B', 'Mantido: % do benchmark difere (mês 50,0% na planilha, 31,9% na API)'),
    ('legacy', 'PL diverge', 'ver aba Cota, PL e benchmark', 'ver aba Cota, PL e benchmark', 'Mantido: diferença de cerca de −90% no PL; carteira e cotas praticamente iguais'),
    ('todos', 'Rentabilidade 36m', 'calculada', 'não existe', 'Nulo até a API entregar (solicitado ao time da API)'),
    ('todos', 'Rentabilidade desde o início', 'calculada', 'rent_inception nulo', 'Nulo até a API entregar (solicitado ao time da API)'),
    ('todos', 'Sign-off', '—', 'signoff=false', 'Mantido false: o Risco ainda não aprovou a data; testes em andamento'),
]

CAMPOS = [
    ('Cota diária do fundo', 'Benchmark F:I (cota)', 'GET /cotas (cota, cota_ajustada)', '✅ tem', 'Série desde official_initial_date; cortar na data base'),
    ('PL diário', 'Benchmark F:I (pl)', 'GET /cotas (pl, em R$ milhões) e visao-geral.pl_atual (R$)', '✅ tem', 'Atenção à unidade (milhões na série)'),
    ('Índice do benchmark (CDI…)', 'Benchmark A:D', 'GET /benchmarks', '✅ tem', 'Mandar signoff explícito, senão volta vazio em fundo sem aprovação'),
    ('CNPJ', 'DePara', 'visao-geral.cnpj', '✅ tem', 'Subclasses podem vir sem CNPJ'),
    ('Benchmark do fundo', 'DePara', 'visao-geral.benchmark_symbol', '✅ tem', ''),
    ('Data de início', 'DePara (data_inicial)', 'visao-geral.official_initial_date', '✅ tem', 'Na planilha costuma estar vazia'),
    ('Cota inicial', 'DePara (cota_inicial)', 'primeira cota da série /cotas', '⚠️ derivável', 'Ver coluna "primeira cota da série API"'),
    ('Rentabilidade mês/ano/12m + % do benchmark', 'calculado (Calc.rentabilidade)', 'visao-geral.rent_mtd/ytd/12m e pct_bench_*', '✅ tem', 'Comparar na aba Rentabilidade'),
    ('Rentabilidade 24m', 'calculado', 'visao-geral.rent_24m', '⚠️ tem, número pode diferir', 'Janela diferente da planilha (503 dias úteis)'),
    ('Rentabilidade 36m', 'calculado', '— (só 6m e 24m)', '❌ falta', 'Calcular na série de cotas ou /fundcalc/by-fund/period-returns'),
    ('Rentabilidade desde o início', 'calculado', 'visao-geral.rent_inception', '❌ vem nulo', 'Calcular: cota final / cota inicial − 1'),
    ('PL médio 12m e desde o início', 'calculado', '—', '❌ falta', 'Calcular na série de PL da API'),
    ('Histórico mensal do gráfico (fundo × bench)', 'calculado (Calc.historico)', 'séries /cotas e /benchmarks (+ POST /fundcalc/monthly-returns)', '⚠️ derivável', 'Precisa da série'),
    ('Feriados / dias úteis', 'aba feriados', '—', '✅ dispensável', 'Rentabilidades vêm prontas; só o histórico usa fim de mês'),
    ('Posição linha a linha (exposição, taxa, duration)', 'Base Carteira', 'GET /fundos/{cod}/posicoes (exposure, rate, duration, pct_nav…)', '✅ tem', 'Ver aba Carteira (resumo)'),
    ('Emissor', 'Base Carteira (Emissor)', 'posicoes.issuer / GET /emissores', '✅ tem', 'Nomes podem divergir'),
    ('Setor / Setor Aj.', 'Base Carteira', 'posicoes.sector / alocacao.by_sector', '⚠️ taxonomia diferente', 'Planilha: Financeiro, Industrial…; API: Banco de Varejo, Banco de Atacado, Governo… Não há "Setor Aj." (HY/IS)'),
    ('Tipo / Tipo aj.', 'Base Carteira', 'posicoes.instrument_class / alocacao.by_class', '⚠️ parcial', 'Não há "Tipo aj."'),
    ('Rating Externo', 'Base Carteira', 'alocacao.by_rating (agregado); emissores.rating', '⚠️ parcial', 'Não vem na posição'),
    ('Book', 'Base Carteira', 'posicoes.book_name / alocacao.by_book', '✅ tem', 'Nomes a conferir'),
    ('HGHY', 'Base Carteira', '—', '❌ não achei', 'Usado nas páginas Saiba mais HGD30/HYD60'),
    ('FIDC (flag)', 'Base Carteira', '—', '❌ não achei', 'Pode ser derivável do book/instrument_class'),
    ('Taxa (carrego) e duration', 'Base Carteira', 'posicoes.spread (em %, ÷100 = Taxa da planilha) e duration (já em anos)', '✅ tem', 'Planilha: Taxa em fração e duration em dias úteis ÷ 252'),
    ('Data da carteira', 'Base Carteira (Data)', 'posicoes.ref_date', '✅ tem', ''),
    ('Data base da edição', 'último fechamento da planilha', 'GET /referencia (hoje) + parâmetro', '✅ tem', 'Parâmetro --data-base'),
    ('Sign-off', '—', 'GET /fundos/{cod}/signoff; parâmetro signoff', '✅ tem', 'Futuro: só gerar com aprovado = true'),
    ('Código do fundo (id_portfolio)', '—', 'rentabilidade/fundos (portfolio_id + cnpj)', '✅ tem', 'Casamento por CNPJ — aba Fundos x id_portfolio'),
]

if __name__ == '__main__':
    main()
