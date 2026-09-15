# -*- coding: utf-8 -*-
"""
etf_metrics.py
--------------
Transforma o DataFrame vindo do Databricks (ou do mock) em ETFS_DATA:
uma lista de dicts que o dashboard consome.

CAMPOS ESPERADOS por ETF (ajuste conforme o template HTML final):
    ticker      -> codigo de negociacao (ex.: "BOVA11")
    nome        -> nome do ETF
    gestora     -> emissor / administrador
    categoria   -> "Renda Fixa" | "RV Brasil" | "RV Int" | "Multi" | ...
    pl          -> patrimonio liquido (float, R$)
    fee         -> taxa de administracao a.a. (float, % -> ex.: 0.20)
    cap12       -> captacao liquida 12m (float, R$)  [se disponivel]
    n_etfs      -> (uso em agregacao por gestora)
    cnpj        -> CNPJ do fundo/ETF (para cruzamentos)

Este arquivo tem duas funcoes principais:
    linha_para_dict(row)  -> normaliza uma linha
    montar_etfs_data(...) -> monta a lista final (ordena, ranqueia)
"""

import math


def _f(v):
    if v is None:
        return None
    try:
        x = float(v)
        return None if math.isnan(x) else x
    except (TypeError, ValueError):
        return None


def _s(v, default=""):
    return default if v is None else str(v).strip()


def limpar_cnpj(v):
    import re
    if v is None:
        return None
    d = re.sub(r"\D", "", str(v))
    return d.zfill(14) if d else None
def normalizar_gestora(valor):
    """
    Normaliza o nome bruto do fundo de índice informado pela B3
    para a marca da gestora/emissora utilizada no dashboard.

    A ordem das regras importa.
    Regras específicas devem vir antes das regras genéricas.
    """

    gestora_original = _s(valor or "N/D")
    txt = gestora_original.upper().strip()

    # ----------------------------------------------------------
    # Grandes emissores
    # ----------------------------------------------------------
    if "ISHARES" in txt:
        return "BlackRock"

    if "IT NOW" in txt:
        return "Itaú"

    if "TREND" in txt:
        return "XP"

    if "BB ETF" in txt:
        return "Banco do Brasil"

    if "BRADESCO" in txt:
        return "Bradesco"

    if "CAIXA ETF" in txt:
        return "Caixa"

    if "SAFRA" in txt:
        return "Safra"

    # ----------------------------------------------------------
    # Gestoras independentes
    # ----------------------------------------------------------
    if "INVESTO" in txt:
        return "Investo"

    if "HASHDEX" in txt:
        return "Hashdex"

    if "BUENA VISTA" in txt:
        return "Buena Vista"

    if "GALAPAGOS" in txt:
        return "Galapagos"

    if "ORANJ" in txt:
        return "Oranj"

    if "HEDGE BRASIL" in txt:
        return "Hedge Brasil"

    if "WISE" in txt:
        return "Wise"

    if "BITCOIN ETC" in txt:
        return "Bitcoin ETC"

    # ----------------------------------------------------------
    # Nu Asset
    # Exemplos encontrados:
    # NU IBOV...
    # NU RENDA...
    # NU NASDAQ...
    # ----------------------------------------------------------
    if (
        txt.startswith("NU ")
        or txt.startswith("NUIBOV")
        or txt.startswith("NU IBOV")
        or "NUBANK" in txt
        or "NU ASSET" in txt
    ):
        return "Nu Asset"

    # ----------------------------------------------------------
    # QR Asset
    # Evita usar apenas "QR", pois duas letras podem aparecer
    # no meio de outras palavras.
    # ----------------------------------------------------------
    if (
        txt.startswith("QR ")
        or txt.startswith("QR ")
        or " QR " in txt
        or "QR CAPITAL" in txt
        or "QR ASSET" in txt
        or "QR BLOOMBERG" in txt
    ):
        return "QR Asset"

    # ----------------------------------------------------------
    # B-Index e produtos Morningstar
    # ----------------------------------------------------------
    if (
        "B-INDEX" in txt
        or txt.startswith("B INDEX")
        or txt.startswith("BINDEX")
    ):
        return "B-Index"

    if "MORNINGSTAR" in txt:
        return "B-Index"

    # ----------------------------------------------------------
    # Magnetis deve ser testada ANTES da regra genérica TEVA
    # Exemplo: MAGNETIS TEVA AÇÕES AGRONEGÓCIO
    # ----------------------------------------------------------
    if "MAGNETIS" in txt:
        return "Magnetis"

    # ----------------------------------------------------------
    # BTG deve ser testado antes da regra genérica TEVA
    # Exemplo: BTG PACTUAL TEVA AUVP
    # ----------------------------------------------------------
    if "BTG PACTUAL" in txt or txt.startswith("BTG "):
        return "BTG Pactual"

    # ----------------------------------------------------------
    # Teva independente
    # Exemplo: INTER EQI TEVA ETF...
    # Não deve ser automaticamente classificada como BTG.
    # ----------------------------------------------------------
    if "TEVA" in txt:
        return "Teva"

    # ----------------------------------------------------------
    # Outros nomes identificáveis
    # ----------------------------------------------------------
    if "KARDINAL" in txt:
        return "Kardinal"

    if "INTER " in txt or txt.startswith("INTER"):
        return "Inter"

    if "EMPIRICUS" in txt:
        return "Empiricus"

    if "TRIGONO" in txt or "TRÍGONO" in txt:
        return "Trígono"

    if "JGP" in txt:
        return "JGP"

    if "SINGULARE" in txt:
        return "Singulare"

    if "GENIAL" in txt:
        return "Genial"

    if "VITREO" in txt or "VITREO" in txt:
        return "Vitreo"

    if "MERCADO BITCOIN" in txt:
        return "Mercado Bitcoin"

    # ----------------------------------------------------------
    # Não inventa uma gestora quando a regra não é conhecida.
    # Mantém o nome bruto para auditoria.
    # ----------------------------------------------------------
    return gestora_original


def linha_para_dict(row):
    """Converte uma linha do Databricks em um registro padronizado de ETF."""

    g = row.get if hasattr(row, "get") else (
        lambda k, d=None: getattr(row, k, d)
    )

    gestora_bruta = (
        g("gestora")
        or g("emissor")
        or "N/D"
    )

    gestora = normalizar_gestora(gestora_bruta)

    return {
                "lancamento_12m": int(
            g("lancamento_12m") or 0
        ),

        "data_inicio": _s(
            g("data_inicio")
        ),

        "data_referencia": _s(
            g("data_referencia")
        ),
        "ticker": _s(
            g("ticker")
            or g("codigo")
        ),

        "nome": _s(
            g("nome")
            or g("nome_comercial")
        ),

        "gestora": gestora,

        "gestora_original": _s(gestora_bruta),

        "categoria": _s(
            g("categoria")
            or "N/D"
        ),

        "pl": _f(
            g("pl")
            or g("patrimonio_liquido")
        ),

        "fee": _f(
            g("fee")
            or g("taxa_administracao")
        ),

        "cap12": _f(
            g("cap12")
            or g("captacao_12m")
        ),

        "cnpj": limpar_cnpj(
            g("cnpj")
        ),
    }

def montar_etfs_data(linhas, top_n=None):
    """Lista final de ETFs, ordenada por PL desc."""

    validos = [
        l for l in linhas
        if (
            (l["ticker"] or l["nome"])
            and l["pl"] is not None
            and l["pl"] > 0
        )
    ]

    validos.sort(
        key=lambda x: (
            x["pl"]
            if x["pl"] is not None
            else -1e18
        ),
        reverse=True
    )

    if top_n:
        validos = validos[:top_n]

    for i, l in enumerate(validos, start=1):
        l["rank"] = i

    return validos



def agregar_por_gestora(etfs):
    """
    Agrega por gestora:
    - quantidade de ETFs
    - lançamentos nos últimos 12 meses
    - PL total
    - fee médio ponderado pelo PL
    - categoria dominante
    """

    grupos = {}

    for e in etfs:
        nome_gestora = e.get("gestora") or "N/D"

        g = grupos.setdefault(
            nome_gestora,
            {
                "gestora": nome_gestora,
                "n_etfs": 0,
                "lancamentos_12m": 0,
                "pl": 0.0,
                "_fee_pl": 0.0,
                "_pl_com_fee": 0.0,
                "_categorias": {},
            }
        )

        g["n_etfs"] += 1

        g["lancamentos_12m"] += int(
            e.get("lancamento_12m") or 0
        )

        pl = e.get("pl")
        fee = e.get("fee")
        categoria = e.get("categoria") or "N/D"

        if pl is not None:
            g["pl"] += pl

            g["_categorias"][categoria] = (
                g["_categorias"].get(categoria, 0.0)
                + pl
            )

            if fee is not None:
                g["_fee_pl"] += fee * pl
                g["_pl_com_fee"] += pl

    resultado = []

    for g in grupos.values():
        fee_medio = None

        if g["_pl_com_fee"] > 0:
            fee_medio = (
                g["_fee_pl"]
                / g["_pl_com_fee"]
            )

        categoria_dominante = "N/D"

        if g["_categorias"]:
            categoria_dominante = max(
                g["_categorias"],
                key=g["_categorias"].get
            )

        resultado.append(
            {
                "gestora": g["gestora"],
                "n_etfs": g["n_etfs"],
                "lancamentos_12m": g["lancamentos_12m"],
                "pl": round(g["pl"], 2),
                "fee_medio": (
                    round(fee_medio, 4)
                    if fee_medio is not None
                    else None
                ),
                "categoria_dominante": categoria_dominante,
            }
        )

    resultado.sort(
        key=lambda x: x["pl"],
        reverse=True
    )

    return resultado