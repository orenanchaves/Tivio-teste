"""Leitura das planilhas de entrada.

A dados_mensais.xlsx tem ~32 MB e quatro abas largas; abrir custa 1-2 min. O
cache em `.cache/` é indexado por (caminho, tamanho, mtime), então trocar a
planilha do mês invalida sozinho — não há passo manual de limpar cache.
"""
import hashlib
import os
import pickle
from datetime import datetime, timedelta

import openpyxl
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.cache')

ABAS = {
    'DePara': 13,
    'Benchmark': 9,
    'Base Carteira': 18,
    'feriados': 3,
}


def _excel_serial(v):
    if isinstance(v, datetime):
        return pd.Timestamp(v)
    if isinstance(v, (int, float)) and not pd.isna(v):
        return pd.Timestamp(datetime(1899, 12, 30) + timedelta(days=float(v)))
    return pd.NaT


def _ler_aba(ws, max_col):
    linhas, vazias = [], 0
    for r in ws.iter_rows(values_only=True, max_col=max_col):
        if all(v is None for v in r):
            vazias += 1
            if vazias > 2000:  # aba com formatação até a linha 1.048.576
                break
            continue
        vazias = 0
        linhas.append(r)
    cab = [str(c) if c is not None else f'_c{i}' for i, c in enumerate(linhas[0])]
    return pd.DataFrame(linhas[1:], columns=cab)


def _hash(path):
    st = os.stat(path)
    return hashlib.md5(f'{path}{st.st_size}{st.st_mtime}'.encode()).hexdigest()


def ler_dados_mensais(path, log=print):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = os.path.join(CACHE_DIR, _hash(path) + '.pkl')
    if os.path.exists(cache):
        log('  usando cache de ' + os.path.basename(path))
        with open(cache, 'rb') as f:
            return pickle.load(f)

    log('  lendo ' + os.path.basename(path) + ' (primeira vez demora ~1-2 min)…')
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    raw = {}
    for aba, mc in ABAS.items():
        log(f'    · {aba}')
        raw[aba] = _ler_aba(wb[aba], mc)
    wb.close()

    # ---- DePara (B:I) ----
    dp = raw['DePara'].iloc[:, 1:9].copy()
    dp.columns = ['carteira', 'cnpj', 'quantum', 'quantum2', 'benchmark', 'mesa', 'cota_inicial', 'data_inicial']
    dp = dp[dp['cnpj'].astype(str).str.match(r'\d{2}\.\d{3}')]
    dp['data_inicial'] = dp['data_inicial'].map(_excel_serial)
    dp['cota_inicial'] = pd.to_numeric(dp['cota_inicial'], errors='coerce').fillna(1.0)

    # ---- Benchmark: A:D índices / F:I fundos ----
    b = raw['Benchmark']
    idx = b.iloc[:, [1, 2, 3]].dropna()
    idx.columns = ['nome', 'data', 'valor']
    idx['data'] = idx['data'].map(_excel_serial)
    idx['valor'] = pd.to_numeric(idx['valor'], errors='coerce')
    fun = b.iloc[:, [5, 6, 7, 8]].dropna(subset=[b.columns[5], b.columns[6]])
    fun.columns = ['nome', 'data', 'pl', 'cota']
    fun['data'] = fun['data'].map(_excel_serial)
    fun[['pl', 'cota']] = fun[['pl', 'cota']].apply(pd.to_numeric, errors='coerce')

    # ---- Base Carteira ----
    c = raw['Base Carteira']
    c = c[c['Carteira'].notna()].copy()
    c['Data'] = pd.to_datetime(c['Data'], errors='coerce')
    # Célula de data vazia ou zerada vira 1970-01-01 (o epoch), não NaT — e aí o
    # dado passa por válido. Na base de agosto/2026 são 394 das 2.666 linhas,
    # entre elas as carteiras inteiras do Infra Plus e do Esplanada. Marcamos
    # como ausente para a conferência poder dizer "sem data" em vez de calcular
    # 20.695 dias de atraso.
    c.loc[c['Data'] < pd.Timestamp('1990-01-01'), 'Data'] = pd.NaT
    for col in ('Taxa', 'duration', 'Exposição'):
        c[col] = pd.to_numeric(c[col], errors='coerce').fillna(0.0)
    c['FIDC'] = c['FIDC'].astype(str).str.upper().eq('TRUE')

    fer = pd.to_datetime(raw['feriados'].iloc[:, 0], errors='coerce').dropna()

    dados = {'depara': dp, 'indices': idx.sort_values('data'), 'fundos': fun.sort_values('data'),
             'carteira': c, 'feriados': fer}
    with open(cache, 'wb') as f:
        pickle.dump(dados, f)
    return dados


def ler_taxas(path):
    t = pd.read_excel(path)
    t['cnpj_num'] = t['CNPJ'].astype('Int64').astype(str).str.zfill(14)
    return t


def ler_manual(path):
    """Planilha de preenchimento manual (textos, cadastro, overrides)."""
    if not path or not os.path.exists(path):
        return {}
    xl = pd.read_excel(path, sheet_name=None, dtype=str)
    return {k: v.fillna('') for k, v in xl.items()}
