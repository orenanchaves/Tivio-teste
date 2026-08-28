# -*- coding: utf-8 -*-
"""metrics.py · Central de Análises · Tivio Capital
Cálculo dos KPIs do dashboard de AUM (vw_aum)."""
import pandas as pd


def fmt(v: float) -> str:
    if v >= 1_000_000_000:
        return f"R$ {v/1_000_000_000:.2f} Bi".replace(".", ",")
    if v >= 1_000_000:
        return f"R$ {v/1_000_000:.1f} MM".replace(".", ",")
    if v >= 1_000:
        return f"R$ {v/1_000:.0f} mil"
    return f"R$ {v:.0f}"


def _linhas_rank(serie, total, unidade="fundo"):
    maior = float(serie.max()) if len(serie) else 1
    out = []
    for i, (nome, val) in enumerate(serie.items(), 1):
        pct = (val / total * 100) if total else 0
        larg = (val / maior * 100) if maior else 0
        destaque = " style='color:var(--tivio);font-weight:700'" if "TIVIO" in str(nome).upper() and unidade == "dist" else ""
        out.append(f"""
        <tr>
          <td class="rank">{i}</td>
          <td class="fnome"{destaque}>{nome}</td>
          <td class="fcap">{fmt(float(val))}</td>
          <td class="fpct">{pct:.1f}%</td>
          <td><div class="bar-track"><div class="bar-fill" style="width:{larg:.0f}%"></div></div></td>
        </tr>""")
    return "".join(out)


def _cards_vertical(df, total):
    g = df.groupby("normalized_vertical")["aum"].sum().sort_values(ascending=False)
    cores = ["var(--tivio)", "var(--tv-info)", "var(--tv-warn)", "var(--tv-roxo)", "var(--tv-pos)", "var(--tv-neg)"]
    out = []
    for i, (vert, val) in enumerate(g.items()):
        pct = (val / total * 100) if total else 0
        c = cores[i % len(cores)]
        out.append(f"""
        <div class="vcard">
          <div class="vcard-top" style="background:{c}"></div>
          <div class="vcard-num" style="color:{c}">{fmt(float(val))}</div>
          <div class="vcard-name">{vert}</div>
          <div class="vcard-bar"><div style="width:{pct:.0f}%;background:{c}"></div></div>
          <div class="vcard-pct">{pct:.1f}% do PL</div>
        </div>""")
    return "".join(out)


def kpis_fundos_tivio(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["aum"] = df["aum"].astype(float)
    total = float(df["aum"].sum())

    por_fundo = df.groupby("fund_name")["aum"].sum().sort_values(ascending=False)
    por_dist  = df.groupby("distributor_name")["aum"].sum().sort_values(ascending=False)
    por_cli   = df.groupby("client_type")["aum"].sum().sort_values(ascending=False)

    top_fundo = por_fundo.index[0]
    top_dist  = por_dist.index[0]
    top3_dist_pct = (por_dist.head(3).sum() / total * 100) if total else 0

    return {
        "PL_TOTAL":        fmt(total),
        "QTD_FUNDOS":      str(df["fund_code"].nunique()),
        "QTD_DIST":        str(df["distributor_name"].nunique()),
        "TOP_FUNDO":       str(top_fundo),
        "TOP_FUNDO_VAL":   fmt(float(por_fundo.iloc[0])),
        "TOP_DIST":        str(top_dist),
        "TOP_DIST_VAL":    fmt(float(por_dist.iloc[0])),
        "TOP3_DIST_PCT":   f"{top3_dist_pct:.0f}%",
        "TABELA_FUNDOS":   _linhas_rank(por_fundo.head(20), total, "fundo"),
        "TABELA_DIST":     _linhas_rank(por_dist.head(20), total, "dist"),
        "CARDS_VERTICAL":  _cards_vertical(df, total),
    }
