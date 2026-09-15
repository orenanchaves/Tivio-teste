# -*- coding: utf-8 -*-
"""
captacao_metrics.py
-------------------
Transforma o DataFrame vindo do Databricks (ranking de captacao ANBIMA)
na lista de dicts que o dashboard usa em `const FUNDS_DATA = [...]`.

Cada fundo do FUNDS_DATA tem EXATAMENTE estes 17 campos (ordem livre, sao dicts):

    rank         -> posicao (1..10) DENTRO da plataforma + categoria
    nome         -> nome do fundo (str)
    cap30        -> captacao liquida 30d (float, R$)
    rent30       -> rentabilidade 30d (float, %)
    cdi30        -> % do benchmark 30d (float, %)   (rent / cdi_mes * 100)
    cap12        -> captacao liquida 12m (float, R$)
    rent12       -> rentabilidade 12m (float, %)
    cdi12        -> % do benchmark 12m (float, %)
    capytd       -> captacao liquida YTD (float, R$)
    rentytd      -> rentabilidade YTD (float, %)
    cdiytd       -> % do benchmark YTD (float, %)
    pl           -> patrimonio liquido (float, R$)
    benchmark    -> "CDI" | "IMA-B" | ... (str)
    gestor       -> nome do gestor / asset (str)
    plat         -> "XP" | "BTG" | "Itau" | "Bradesco"
    categoria    -> "Renda Fixa Ativa" | "Renda Fixa" | "Multimercado"
    rank_global  -> posicao no ranking geral (por cap30 desc, todas as linhas)

REGRAS IMPORTANTES (o dashboard depende disso):
  - `plat` precisa ser exatamente um de: XP, BTG, Itau, Bradesco
    (o rotulo bonito "BTG Pactual" / "Itau" vem do PLAT_LABELS no HTML).
  - `categoria` precisa bater com as pills do HTML:
    "Renda Fixa Ativa", "Renda Fixa", "Multimercado".
  - `cdi30/cdi12/cdiytd` sao "% do benchmark". Se o Databricks ja entrega
    isso, use direto. Se entrega so a rentabilidade, calcule aqui
    (rent / cdi_periodo * 100).
"""

import math

# Rotulos aceitos pelo dashboard -----------------------------------------
PLAT_VALIDAS = {"XP", "BTG", "Itau", "Bradesco"}
CATS_VALIDAS = {"Renda Fixa Ativa", "Renda Fixa", "Multimercado"}

# de-para para normalizar o que vier do banco -> chave do dashboard
PLAT_DEPARA = {
    "xp": "XP", "xp investimentos": "XP",
    "btg": "BTG", "btg pactual": "BTG",
    "itau": "Itau", "itaú": "Itau", "itau unibanco": "Itau",
    "bradesco": "Bradesco", "agora": "Bradesco", "ágora": "Bradesco",
}


def _f(v):
    """Converte para float seguro (None/NaN -> None)."""
    if v is None:
        return None
    try:
        x = float(v)
        if math.isnan(x):
            return None
        return x
    except (TypeError, ValueError):
        return None


def _norm_plat(p):
    if p is None:
        return None
    key = str(p).strip().lower()
    return PLAT_DEPARA.get(key, str(p).strip())


def pct_benchmark(rent, cdi_periodo):
    """Retorna % do benchmark. cdi_periodo em fracao (ex.: 0.0113 = 1.13%)."""
    rent = _f(rent)
    if rent is None or not cdi_periodo:
        return None
    return round(rent / (cdi_periodo * 100.0) * 100.0, 2)


def linha_para_dict(row, cdi):
    """
    Converte UMA linha do DataFrame (dict/Row) em um dict de fundo.
    `cdi` = {"m": 0.0113, "y": 0.1482, "ytd": 0.0572}
    Ajuste os nomes das colunas conforme o retorno real do seu SQL.
    """
    plat = _norm_plat(row.get("plataforma") or row.get("plat"))
    categoria = row.get("categoria")
    benchmark = row.get("benchmark") or "CDI"

    rent30 = _f(row.get("rent30"))
    rent12 = _f(row.get("rent12"))
    rentytd = _f(row.get("rentytd"))

    # % benchmark: usa o que veio do banco, senao calcula
    cdi30 = _f(row.get("cdi30")) if row.get("cdi30") is not None else pct_benchmark(rent30, cdi["m"])
    cdi12 = _f(row.get("cdi12")) if row.get("cdi12") is not None else pct_benchmark(rent12, cdi["y"])
    cdiytd = _f(row.get("cdiytd")) if row.get("cdiytd") is not None else pct_benchmark(rentytd, cdi["ytd"])

    return {
        "rank": None,          # preenchido depois em montar_funds_data()
        "nome": str(row.get("nome") or "").strip(),
        "cap30": _f(row.get("cap30")),
        "rent30": rent30,
        "cdi30": cdi30,
        "cap12": _f(row.get("cap12")),
        "rent12": rent12,
        "cdi12": cdi12,
        "capytd": _f(row.get("capytd")),
        "rentytd": rentytd,
        "cdiytd": cdiytd,
        "pl": _f(row.get("pl")),
        "benchmark": benchmark,
        "gestor": str(row.get("gestor") or "N/D").strip(),
        "plat": plat,
        "categoria": categoria,
        "rank_global": None,   # preenchido depois
        # guarda o CNPJ so para debug/dedupe (o dashboard ignora)
        "_cnpj": row.get("cnpj"),
    }


def montar_funds_data(linhas, cdi, top_n=10):
    """
    Recebe uma lista de dicts (saida de linha_para_dict) e devolve a
    lista final ja com:
      - top N por (plataforma, categoria), rank 1..N
      - rank_global por cap30 desc (todas as linhas do resultado final)

    `linhas` pode ser construida a partir de:
        [linha_para_dict(r, cdi) for r in df.to_dict("records")]
    """
    # 1) filtra linhas validas
    validas = [
        l for l in linhas
        if l["plat"] in PLAT_VALIDAS
        and l["categoria"] in CATS_VALIDAS
        and l["nome"]
    ]

    # 2) top N por plataforma + categoria (ordenado por cap30 desc)
    grupos = {}
    for l in validas:
        grupos.setdefault((l["plat"], l["categoria"]), []).append(l)

    final = []
    for (plat, cat), itens in grupos.items():
        itens.sort(key=lambda x: (x["cap30"] if x["cap30"] is not None else -1e18),
                   reverse=True)
        for i, l in enumerate(itens[:top_n], start=1):
            l["rank"] = i
            final.append(l)

    # 3) rank_global por cap30 desc
    final.sort(key=lambda x: (x["cap30"] if x["cap30"] is not None else -1e18),
               reverse=True)
    for i, l in enumerate(final, start=1):
        l["rank_global"] = i

    # remove campos internos (comeca com "_")
    limpos = [{k: v for k, v in l.items() if not k.startswith("_")} for l in final]
    return limpos
