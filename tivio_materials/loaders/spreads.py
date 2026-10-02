# -*- coding: utf-8 -*-
"""Tabela de spreads por setor (Mercado de Crédito) — entrada mensal própria.

Hoje essa tabela é digitada na aba Mercado_Credito do preenchimento_manual.xlsx.
São ~25 setores × 6 colunas, 150 células por mês, copiadas de outra planilha —
é o tipo de passo onde um número entra errado e ninguém confere, porque conferir
custa tanto quanto redigitar.

Com `entrada/tabela_spreads.xlsx` o bloco passa a ser lido direto da planilha que
já existe. A leitura é tolerante de propósito:

* o cabeçalho não precisa estar na linha 1 — é procurado pela palavra "Setor";
* as colunas são casadas por nome aproximado, não por posição, porque "Spread
  mês anterior" vira "Spread Mês Anterior" ou "Spread anterior" entre uma versão
  e outra da planilha;
* número e texto são aceitos: 0,0114 e "1,14%" chegam no mesmo lugar.

O que não é tolerante: se a planilha existir e a tabela não for reconhecida, o
loader devolve None e o relatório sai **sem** o bloco, com aviso. Preencher um
bloco de mercado com dados meio lidos é pior do que não ter o bloco.
"""
import os
import re
import unicodedata

import openpyxl
import pandas as pd

# nome exibido -> palavras que identificam a coluna na planilha
COLUNAS = [
    ('Setor',               ['setor']),
    ('Volume (R$ MM)',      ['volume']),
    ('%',                   ['%', 'part', 'peso']),
    ('Spread Atual',        ['spreadatual', 'atual']),
    ('Spread mês anterior', ['anterior']),
    ('Variação',            ['variacao', 'var']),
    ('Duration',            ['duration', 'duracao']),
]

NOTA = ('Debêntures precificadas pela ANBIMA corrigidas por CDI + spread. '
        'Desconsideramos as debêntures que começaram a ser precificadas ou que '
        'venceram ao longo do mês, para que a comparação com o mês anterior seja '
        'feita com a mesma base de ativos.')


def _norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9%]', '', s.lower())


def _br(v, casas):
    return f'{v:,.{casas}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _fmt(valor, coluna, eh_fracao):
    """Formata o valor. `eh_fracao` vem do formato da célula, não de palpite.

    A primeira versão adivinhava: "valor menor que 1 é fração". Isso erra em
    dois casos que aparecem toda edição — 100% guardado como 1,0 virava "1,00%",
    e uma coluna de spreads inteira abaixo de 1% (0,52%, 0,75%) seria
    multiplicada por 100. O Excel guarda a resposta no formato da célula: se o
    formato tem "%", o número está em fração. É isso que lemos.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ''
    if isinstance(valor, str):
        return valor.strip()

    v = float(valor)
    if coluna == 'Volume (R$ MM)':
        return _br(v, 0)
    if coluna == 'Duration':
        return _br(v, 2)
    if eh_fracao:
        v *= 100
    return _br(v, 2) + '%'


def _achar_cabecalho(df):
    """Linha que contém "Setor" e alguma coluna de spread."""
    for i in range(min(25, len(df))):
        celulas = [_norm(x) for x in df.iloc[i].tolist()]
        if any(c == 'setor' for c in celulas) and any('spread' in c for c in celulas):
            return i
    return None


def _mapear(cabecalho):
    """{nome exibido: índice da coluna}, pelo nome aproximado."""
    normalizados = [_norm(c) for c in cabecalho]
    usados, mapa = set(), {}
    for nome, pistas in COLUNAS:
        for j, c in enumerate(normalizados):
            if j in usados or not c:
                continue
            if any(p in c for p in pistas):
                mapa[nome] = j
                usados.add(j)
                break
    return mapa


def carregar(caminho, log=None):
    """Devolve o bloco pronto para o componente, ou None."""
    def avisar(msg):
        if log:
            log.aviso('mercado de crédito', msg)

    if not caminho or not os.path.exists(caminho):
        return None

    try:
        wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    except Exception as e:
        avisar(f'não consegui abrir {os.path.basename(caminho)}: {e!r}')
        return None

    try:
        abas = {}
        formatos = {}
        for ws in wb.worksheets:
            valores, fmts = [], []
            for linha in ws.iter_rows():
                valores.append([c.value for c in linha])
                fmts.append(['%' in str(c.number_format or '') for c in linha])
            if valores:
                abas[ws.title] = pd.DataFrame(valores)
                formatos[ws.title] = fmts
    finally:
        wb.close()

    for nome_aba, df in abas.items():
        if df.empty:
            continue
        i = _achar_cabecalho(df)
        if i is None:
            continue
        mapa = _mapear(df.iloc[i].tolist())
        faltam = [n for n, _ in COLUNAS if n not in mapa]
        if faltam:
            avisar(f'aba "{nome_aba}": não achei as colunas {faltam} — '
                   f'cabeçalho lido: {[str(x) for x in df.iloc[i].tolist()][:8]}')
            continue

        linhas = []
        for idx, r in df.iloc[i + 1:].iterrows():
            setor = r.iloc[mapa['Setor']]
            if setor is None or (isinstance(setor, float) and pd.isna(setor)):
                continue
            setor = str(setor).strip()
            if not setor:
                continue
            fmts = formatos[nome_aba]
            linha_fmt = fmts[idx] if idx < len(fmts) else []

            def pct_na_celula(j):
                return linha_fmt[j] if j < len(linha_fmt) else False

            celulas = [setor if n == 'Setor'
                       else _fmt(r.iloc[mapa[n]], n, pct_na_celula(mapa[n]))
                       for n, _ in COLUNAS]
            linhas.append({'celulas': celulas,
                           'total': setor.lower() in ('total', 'total geral')})

        if not linhas:
            avisar(f'aba "{nome_aba}": cabeçalho encontrado, mas nenhuma linha de setor')
            continue

        # a linha de total costuma vir em cima na planilha e embaixo no relatório
        linhas.sort(key=lambda l: l['total'])
        if log:
            log.info(f'  mercado de crédito: {len(linhas)} setores de '
                     f'{os.path.basename(caminho)} (aba "{nome_aba}")')
        return {'cabecalho': [n for n, _ in COLUNAS], 'linhas': linhas, 'nota': NOTA,
                'origem': f'{os.path.basename(caminho)} · {nome_aba}'}

    avisar(f'{os.path.basename(caminho)}: nenhuma aba tem uma tabela com "Setor" '
           f'e uma coluna de spread')
    return None
