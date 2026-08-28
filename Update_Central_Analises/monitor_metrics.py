# -*- coding: utf-8 -*-
"""
monitor_metrics.py - Monitor de Novos Fundos - Tivio Capital

Converte o DataFrame (ANBIMA/CVM) no array FUNDS_DATA do dashboard.
Cada fundo vira uma lista com 25 posicoes, na ordem de COLS.

Posicoes que o HTML usa como chave:
    11 -> ano (campo_11)
    16 -> mes de referencia (int)
    23 -> taxa de administracao (% ao ano)
    24 -> taxa de performance (%)
"""
import json

import pandas as pd

COLS = [
    "fund_name", "gestora", "tipo", "segmento_detalhe", "categoria_anbima",
    "situacao", "data_registro", "data_constituicao", "cnpj", "publico_alvo",
    "exclusivo", "campo_11", "condominio", "subclasse", "segmentos_bitmask",
    "link_cvm", "mes_ref", "gestor_juridico", "administrador",
    "categoria_n1", "risco_credito", "duracao", "registro",
    "taxa_adm", "taxa_perf",
]

# colunas numericas: viram string com ponto decimal ("" quando nao ha valor)
COLS_NUM = {"taxa_adm", "taxa_perf"}


def _num(v) -> str:
    """Decimal/float -> string com ponto decimal; vazio quando nao ha valor."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return ""
    if f != f:                      # NaN
        return ""
    return f"{round(f, 4):g}"


def _linha(row):
    out = []
    for c in COLS:
        v = row.get(c, "")
        if isinstance(v, float) and pd.isna(v):
            v = ""
        elif v is None or (not isinstance(v, (list, tuple, dict)) and pd.isna(v)):
            v = ""

        if c == "mes_ref":
            try:
                v = int(v)
            except (ValueError, TypeError):
                v = 0
        elif c in COLS_NUM:
            v = _num(v)
        else:
            v = str(v).strip()

        out.append(v)
    return out


def gerar_funds_data(df: pd.DataFrame) -> str:
    """Array JS do FUNDS_DATA para o subconjunto recebido."""
    linhas = [_linha(r) for _, r in df.iterrows()]
    return json.dumps(linhas, ensure_ascii=False)


def ano_de(row) -> int:
    """Extrai o ano da linha (campo_11 ou da data de registro dd/mm/aaaa)."""
    a = str(row.get("campo_11", "")).strip()
    if a[:4].isdigit():
        return int(a[:4])
    d = str(row.get("data_registro", ""))
    if len(d) >= 10 and d[-4:].isdigit():
        return int(d[-4:])
    return 0


def totais_mes(df: pd.DataFrame) -> dict:
    """{1: 83, 2: 78, ...} - contagem por mes do subconjunto."""
    if df.empty or "mes_ref" not in df:
        return {}
    g = df.groupby("mes_ref").size().to_dict()
    return {
        int(k): int(v)
        for k, v in g.items()
        if str(k).isdigit() and 1 <= int(k) <= 12
    }


def totais_ano(df: pd.DataFrame) -> dict:
    """{2024: 4200, 2025: 5100, ...} - contagem por ano do subconjunto."""
    if df.empty:
        return {}
    col = df["_ano"] if "_ano" in df else df.apply(ano_de, axis=1)
    g = col.groupby(col).size().to_dict()
    return {int(k): int(v) for k, v in g.items() if int(k) > 0}
