# -*- coding: utf-8 -*-
"""
atualizar_previdencia.py - Captacao · Previdencia - Tivio Capital

Mesma estrutura do Update_Monitor_Novos_Fundos (ambiente de referencia).

Fonte (FONTE no .env):
    excel      -> Excel - Guia de Base de Dados/Captacao_Previdencia.xlsx
    databricks -> sql/captacao_previdencia.sql

Default no Excel porque o SQL ainda nao foi conferido contra o Databricks
(ver ORIGEM_DOS_DADOS.md). O dashboard segue regeneravel hoje.

O template tem dois blocos de dados:
    FUNDS_DATA - lista unica, achatada, com rentabilidade em PERCENTUAL
    PREV       - por plataforma, com rentabilidade em FRACAO
As duas unidades sao do template, nao escolha nossa: montar_* converte.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

from tivio_core import db, template, saida, validacao   # noqa: E402

TEMPLATE = BASE / "templates" / "dashboard_captacao_previdencia.html"
OUT_HTML = BASE / "outputs" / "dashboard_captacao_previdencia.html"
SQL_FILE = BASE / "sql" / "captacao_previdencia.sql"

EXCEL = BASE.parent / "Excel - Guia de Base de Dados" / "Captacao_Previdencia.xlsx"

FONTE = (os.getenv("FONTE", "").strip() or "excel").lower()
DATA_INI = os.getenv("DATA_INI", "2025-07-01")

# aba do Excel -> chave usada no bloco PREV do template
ABAS = {"XP": "XP", "BTG": "BTG", "Itaú": "Itaú", "Bradesco": "Bradesco"}

# a aba tem tres blocos de tres colunas: mes, 12m e YTD
COLS_PERIODO = [
    ("m", "Capt.Líq.(R$)", "Rentab.", "% CDI"),
    ("y", "Capt.Líq.(R$).1", "Rentab..1", "% CDI.1"),
    ("ytd", "Capt.Líq.(R$).2", "Rentab..2", "% CDI.2"),
]


def _num(v, padrao=0.0):
    n = pd.to_numeric(v, errors="coerce")
    return padrao if pd.isna(n) else float(n)


def _texto(v, padrao=""):
    if v is None:
        return padrao
    try:
        if pd.isna(v):
            return padrao
    except (TypeError, ValueError):
        pass
    return str(v).strip()


def ler_aba(aba: str) -> pd.DataFrame:
    """Le uma aba de plataforma; o cabecalho fica na linha 5."""
    df = pd.read_excel(EXCEL, sheet_name=aba, header=5).dropna(how="all")

    # so as linhas numeradas (1..10) sao fundos
    col_rank = df.columns[1]
    df = df[df[col_rank].astype(str).str.strip().str.isdigit()]

    return df


def montar_prev(por_aba: dict) -> dict:
    """Bloco PREV: por plataforma, rentabilidade em FRACAO (como no template)."""
    gestoras = {}

    for aba, df in por_aba.items():
        fundos = []

        for _, r in df.iterrows():
            f = {
                "rank": int(_num(r[df.columns[1]], 0)),
                "nome": _texto(r[df.columns[2]]),
            }

            for pref, c_cap, c_rent, c_cdi in COLS_PERIODO:
                f[f"{pref}_cap"] = _num(r.get(c_cap))
                f[f"{pref}_rent"] = _num(r.get(c_rent))
                f[f"{pref}_cdi"] = _num(r.get(c_cdi))

            f["pl"] = _num(r.get("PL (R$)"))
            f["resg"] = _num(r.get("Resgates(R$)"))
            f["cotiz"] = _texto(r.get("D+"), "D+0")

            fundos.append(f)

        total = {
            "m_cap": sum(f["m_cap"] for f in fundos),
            "y_cap": sum(f["y_cap"] for f in fundos),
            "ytd_cap": sum(f["ytd_cap"] for f in fundos),
            "pl": sum(f["pl"] for f in fundos),
            "resg": sum(f["resg"] for f in fundos),
        }

        gestoras[ABAS[aba]] = {
            "funds": fundos,
            "total": total,
            "top3": [f["nome"] for f in fundos[:3]],
        }

    # CDI: a media do %CDI nao serve; o CDI do periodo sai da rentabilidade
    # dividida pelo %CDI de cada fundo. Usa a mediana para nao pegar outlier.
    cdi = {}

    todos = [f for g in gestoras.values() for f in g["funds"]]

    for pref in ("m", "y", "ytd"):
        razoes = [
            f[f"{pref}_rent"] / f[f"{pref}_cdi"]
            for f in todos
            if f[f"{pref}_cdi"]
        ]
        cdi[pref] = round(pd.Series(razoes).median(), 6) if razoes else 0.0

    return {
        "gestoras": gestoras,
        "cdi": cdi,
        "resumo": {
            "titulo": "RANKING CAPTAÇÃO & RENTABILIDADE — PREVIDÊNCIA",
            "periodo": (
                f"CDI mês: {cdi['m'] * 100:.2f}%"
                f"   |   CDI 12m: {cdi['y'] * 100:.2f}%"
                f"   |   CDI YTD: {cdi['ytd'] * 100:.2f}%"
            ),
            "atualizado": datetime.now().strftime("%d/%m/%Y"),
        },
        "vg": {},
    }


def montar_funds_data(prev: dict) -> list:
    """Bloco FUNDS_DATA: lista unica, rentabilidade em PERCENTUAL."""
    linhas = []

    for plat_html, dados in prev["gestoras"].items():
        # o FUNDS_DATA usa a chave sem acento
        plat = "Itau" if plat_html == "Itaú" else plat_html

        for f in dados["funds"]:
            linhas.append({
                "rank": f["rank"],
                "nome": f["nome"],
                "cap": f["m_cap"],
                "rent": round(f["m_rent"] * 100, 4),
                "cdi": round(f["m_cdi"] * 100, 2),
                "pl": f["pl"],
                "prazo": f["cotiz"],
                "estrategia": "",
                "carteira": "",
                "plat": plat,
                "rank_global": 0,
            })

    linhas.sort(key=lambda x: x["cap"], reverse=True)

    for i, l in enumerate(linhas, 1):
        l["rank_global"] = i

    return linhas


def main():
    print("\nCaptacao · Previdencia - atualizacao")
    print("-" * 46)

    if not TEMPLATE.exists():
        sys.exit(f"  ! template nao encontrado: {TEMPLATE}")

    if FONTE == "excel":
        if not EXCEL.exists():
            sys.exit(f"  ! Excel nao encontrado: {EXCEL}")

        print(f"  fonte: {EXCEL.name}")
        por_aba = {aba: ler_aba(aba) for aba in ABAS}

        for aba, df in por_aba.items():
            print(f"     {aba:<10} {len(df)} fundos")
    else:
        # O SQL roda, mas o agrupamento por plataforma ainda nao foi
        # conferido contra a planilha. Em vez de recusar a conexao,
        # mostra o que voltou - da para iterar no SQL - e para antes de
        # gravar, que e onde um numero nao conferido viraria decisao.
        print("  fonte: Databricks")

        query = db.ler_sql(SQL_FILE, data_ini=DATA_INI)
        bruto = db.consultar_ou_sair(query)

        print(f"\n  {len(bruto)} linhas | colunas: {list(bruto.columns)}")

        if len(bruto):
            print("\n  amostra:")
            print(bruto.head(5).to_string(index=False, max_colwidth=34))

            if "plataforma" in bruto.columns:
                print("\n  por plataforma:")
                print(bruto["plataforma"].value_counts().head(10).to_string())

        sys.exit(
            "\n  ! parando aqui de proposito: o agrupamento por plataforma "
            "nao foi\n    conferido contra a planilha, e o ambiente de "
            "Fundos Abertos - que usa\n    a mesma logica - tem divergencia "
            "aberta. Ver ORIGEM_DOS_DADOS.md.\n    Para gerar o dashboard "
            "hoje: FONTE=excel"
        )

    prev = montar_prev(por_aba)
    funds = montar_funds_data(prev)

    print(f"\n  {len(funds)} fundos | CDI mes {prev['cdi']['m'] * 100:.2f}%"
          f" · 12m {prev['cdi']['y'] * 100:.2f}%"
          f" · YTD {prev['cdi']['ytd'] * 100:.2f}%")

    validacao.resumo(pd.DataFrame(funds), chave="nome", rotulo="base de fundos")

    html = TEMPLATE.read_text(encoding="utf-8")
    html = template.injetar_array(html, "FUNDS_DATA", funds)
    html = template.injetar_objeto(html, "PREV", prev)
    html = template.atualizar_data(html, datetime.now())
    html, n = template.remover_badges_menu(html)

    if n:
        print(f"  {n} contador(es) removido(s) do menu")

    saida.gravar(html, OUT_HTML)

    print(f"\n     OK  {OUT_HTML.name}  ({len(funds)} fundos)")
    print("-" * 46)
    print("\nConcluido.\n")


if __name__ == "__main__":
    main()
