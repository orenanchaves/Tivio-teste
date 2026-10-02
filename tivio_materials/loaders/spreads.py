# -*- coding: utf-8 -*-
"""Tabela de spreads por setor (Mercado de Crédito) — entrada mensal própria.

Antes essa tabela era digitada na aba Mercado_Credito do preenchimento manual:
~25 setores × 6 colunas, 150 células por edição copiadas de outra planilha. É o
tipo de passo onde um número entra errado e ninguém confere, porque conferir
custa tanto quanto redigitar.

A planilha real (`tabela_spreads.xlsx`) tem três características que o loader
precisa respeitar, e nenhuma delas é "uma tabela começando em A1":

1. **Duas abas, dois indexadores.** "spread mensal CDI+" e "spread mensal
   IPCA+". Não são variações de formatação: são mercados diferentes. O fundo de
   CDI mostra a primeira, o indexado a inflação mostra a segunda. Usar a errada
   põe no relatório do Infra Plus a tabela do mercado de CDI.

2. **Colunas diferentes em cada aba.** A de CDI+ tem Spread Atual/anterior; a de
   IPCA+ tem Taxa Atual/anterior *e* Spread Atual/anterior, com duas colunas
   "Variação". Por isso as colunas não são um esquema fixo no código: são lidas
   do cabeçalho da aba, na ordem em que estão.

3. **O total fica num bloco separado, acima do cabeçalho**, sem a coluna Setor.
   Lido à parte e devolvido como última linha, que é onde o relatório o mostra.

Percentual é decidido pelo **formato da célula**. A primeira versão deste loader
adivinhava ("valor menor que 1 é fração") e errava em dois casos de toda edição:
100% guardado como 1,0 virava "1,00%", e uma coluna de spreads inteira abaixo de
1% seria multiplicada por 100. O Excel guarda a resposta no number_format.
"""
import os
import re
import unicodedata

import openpyxl

NOTA = ('Debêntures precificadas pela ANBIMA corrigidas por CDI + spread. '
        'Desconsideramos as debêntures que começaram a ser precificadas ou que '
        'venceram ao longo do mês, para que a comparação com o mês anterior seja '
        'feita com a mesma base de ativos.')

NOTA_IPCA = ('Debêntures incentivadas precificadas pela ANBIMA. Desconsideramos as '
             'debêntures que começaram a ser precificadas ou que venceram ao longo '
             'do mês, para que a comparação com o mês anterior seja feita com a '
             'mesma base de ativos.')

# nome da aba -> indexador do mercado
INDEXADORES = [('ipca', 'IPCA'), ('ima-b', 'IPCA'), ('inflac', 'IPCA'), ('cdi', 'CDI')]

# colunas que são quantidade, não percentual (decidido pelo nome)
NAO_PERCENTUAL = ('volume', 'duration', 'duracao', 'setor')


def _norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9%+]', '', s.lower())


def _br(v, casas):
    # -0,00% é ruído de arredondamento: a variação de -7,5e-06 do setor de
    # energia vira "menos zero", que lê como erro. Zero arredondado é zero.
    if round(v, casas) == 0:
        v = abs(v)
    return f'{v:,.{casas}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _indexador_da_aba(titulo):
    t = _norm(titulo)
    for pista, nome in INDEXADORES:
        if _norm(pista) in t:
            return nome
    return None


def _fmt(valor, coluna, formato):
    """Formata uma célula. `formato` é o number_format do Excel."""
    if valor is None:
        return ''
    if isinstance(valor, str):
        return valor.strip()
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return str(valor).strip()

    nome = _norm(coluna)
    if any(p in nome for p in NAO_PERCENTUAL):
        return _br(v, 0) if 'volume' in nome else _br(v, 2)
    if '%' in str(formato or ''):
        v *= 100
    return _br(v, 2) + '%'


def _ler_aba(ws):
    """(cabecalho, linhas de setor, linha de total) ou None."""
    grade = []
    for linha in ws.iter_rows():
        grade.append([(c.value, c.number_format) for c in linha])

    # cabeçalho = linha que tem "Setor" e alguma coluna de spread, taxa ou volume
    i_cab = None
    for i, linha in enumerate(grade[:40]):
        nomes = [_norm(v) for v, _ in linha]
        if 'setor' in nomes and any(p in n for n in nomes for p in ('spread', 'taxa', 'volume')):
            i_cab = i
            break
    if i_cab is None:
        return None

    cab_bruto = [(j, v) for j, (v, _) in enumerate(grade[i_cab]) if v is not None]
    if not cab_bruto:
        return None
    colunas = [(j, str(v).strip()) for j, v in cab_bruto]
    j_setor = next((j for j, n in colunas if _norm(n) == 'setor'), None)

    linhas = []
    for linha in grade[i_cab + 1:]:
        setor = linha[j_setor][0] if j_setor is not None and j_setor < len(linha) else None
        if setor is None or not str(setor).strip():
            continue
        celulas = []
        for j, nome in colunas:
            v, f = linha[j] if j < len(linha) else (None, None)
            celulas.append(str(setor).strip() if j == j_setor else _fmt(v, nome, f))
        linhas.append({'celulas': celulas, 'total': False})

    # O total vive num bloco acima, com o mesmo cabeçalho menos a coluna Setor.
    # Procuramos de trás para frente a partir do cabeçalho principal.
    total = None
    for i in range(i_cab - 1, max(-1, i_cab - 8), -1):
        nomes = [_norm(v) for v, _ in grade[i]]
        if not any('volume' in n for n in nomes):
            continue
        valores = grade[i + 1] if i + 1 < len(grade) else []
        if not any(v is not None and not isinstance(v, str) for v, _ in valores):
            continue
        por_nome = {_norm(v): j for j, (v, _) in enumerate(grade[i]) if v is not None}
        celulas = []
        for j, nome in colunas:
            if j == j_setor:
                celulas.append('Total')
                continue
            k = por_nome.get(_norm(nome))
            v, f = valores[k] if k is not None and k < len(valores) else (None, None)
            celulas.append(_fmt(v, nome, f))
        if any(c for c in celulas if c and c != 'Total'):
            total = {'celulas': celulas, 'total': True}
        break

    return [n for _, n in colunas], linhas, total


def carregar(caminho, log=None):
    """{'CDI': tabela, 'IPCA': tabela} — ou None se nada for reconhecido."""
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

    tabelas = {}
    try:
        for ws in wb.worksheets:
            lido = _ler_aba(ws)
            if not lido:
                continue
            cabecalho, linhas, total = lido
            if not linhas:
                avisar(f'aba "{ws.title}": cabeçalho encontrado, nenhuma linha de setor')
                continue
            if total:
                linhas.append(total)
            else:
                avisar(f'aba "{ws.title}": não achei a linha de total')
            idx = _indexador_da_aba(ws.title) or ('CDI' if 'CDI' not in tabelas else ws.title)
            tabelas[idx] = {
                'cabecalho': cabecalho,
                'linhas': linhas,
                'nota': NOTA_IPCA if idx == 'IPCA' else NOTA,
                'origem': f'{os.path.basename(caminho)} · {ws.title}',
                'indexador': idx,
            }
            if log:
                log.info(f'  mercado de crédito {idx}: {len(linhas)} linhas, '
                         f'{len(cabecalho)} colunas (aba "{ws.title}")')
    finally:
        wb.close()

    if not tabelas:
        avisar(f'{os.path.basename(caminho)}: nenhuma aba tem uma tabela com "Setor" '
               f'e colunas de spread, taxa ou volume')
        return None
    return tabelas


def para_fundo(tabelas, benchmark):
    """A tabela do mercado em que o fundo opera, escolhida pelo benchmark."""
    if not tabelas:
        return None
    b = _norm(benchmark)
    alvo = 'IPCA' if ('ima' in b or 'ipca' in b or 'inflac' in b) else 'CDI'
    return tabelas.get(alvo) or next(iter(tabelas.values()))
