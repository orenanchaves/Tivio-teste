# -*- coding: utf-8 -*-
"""
comparar_agosto.py - Concilia o monitor novo (Python/Databricks) com a
planilha historica Monitor_Fundos_Tivio.xlsm.

USO
    python comparar_agosto.py <Monitor_Fundos_Tivio.xlsm> [--mes 8] [--ano 2026]
                              [--novo outputs/dashboard_fundos_tivio_geral.html]

A base nova pode vir de:
  * um dashboard HTML gerado (le o array FUNDS_DATA), ou
  * um .xlsx exportado pelo proprio monitor (ex.: agosto_peers.xlsx).

A planilha historica e lida da aba _DADOS (grao: 1 linha = 1 fundo/classe).
O casamento e por CNPJ de 14 digitos.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

# universo de peers usado pelo atualizar_monitor.py
PEERS = ["SPX", "IBIUNA", "VINCI", "RIZA", "JGP", "KINEA",
         "AUGME", "CAPITANIA", "VERDE", "PATRIA"]

ESTRUTURADOS = ("FIDC", "FIP", "FII", "FIAGRO", "FIIM")


def sdig(s) -> str:
    return re.sub(r"[^0-9]", "", str(s or ""))


def sem_acento(s) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(s))
        if not unicodedata.combining(c)
    )


def eh_peer(nome) -> bool:
    n = sem_acento(nome).upper()
    return any(p in n for p in PEERS)


# ------------------------------------------------------------- carga: novo
def carregar_novo(caminho: str) -> pd.DataFrame:
    """Le a base do monitor de um dashboard HTML ou de um xlsx exportado."""
    p = Path(caminho)

    if p.suffix.lower() in (".xlsx", ".xlsm"):
        df = pd.read_excel(p, dtype=str)
        ren = {"fund_name": "nome", "gestora": "gestora", "tipo": "tipo",
               "cnpj": "cnpj", "data_registro": "data"}
        df = df.rename(columns={k: v for k, v in ren.items() if k in df.columns})
    else:
        from monitor_metrics import COLS
        html = p.read_text(encoding="utf-8")
        i = html.find("const FUNDS_DATA = [")
        if i == -1:
            sys.exit(f"  ! FUNDS_DATA nao encontrado em {p}")
        j = html.find("];", i)
        arr = json.loads(html[i + len("const FUNDS_DATA = "):j + 1])
        df = pd.DataFrame(arr, columns=COLS)
        df = df.rename(columns={"fund_name": "nome", "data_registro": "data"})

    for c in ("nome", "gestora", "tipo", "cnpj", "data"):
        if c not in df.columns:
            df[c] = ""

    df["_cnpj"] = df["cnpj"].map(sdig)
    df["_dt"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
    return df


# -------------------------------------------------------- carga: historico
def carregar_hist(caminho: str) -> pd.DataFrame:
    xl = pd.ExcelFile(caminho)
    if "_DADOS" not in xl.sheet_names:
        sys.exit(f"  ! aba _DADOS ausente. Abas: {xl.sheet_names}")

    d = xl.parse("_DADOS", header=0, dtype=str).dropna(how="all")
    d["_cnpj"] = d["CNPJ_Fundo"].map(sdig)
    d["_dt"] = pd.to_datetime(d["Data_Registro"], format="%d/%m/%Y",
                              errors="coerce")
    return d


# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("historico")
    ap.add_argument("--novo", default="outputs/dashboard_fundos_tivio_geral.html")
    ap.add_argument("--mes", type=int, default=8)
    ap.add_argument("--ano", type=int, default=2026)
    a = ap.parse_args()

    d, nv = carregar_hist(a.historico), carregar_novo(a.novo)

    print("\n" + "=" * 70)
    print(f"CONCILIACAO MONITOR x PLANILHA - {a.mes:02d}/{a.ano}")
    print("=" * 70)

    print(f"\nCobertura  planilha: {d['_dt'].min().date()} -> {d['_dt'].max().date()}"
          f"  ({len(d)} linhas)")
    print(f"           monitor : {nv['_dt'].min().date()} -> {nv['_dt'].max().date()}"
          f"  ({len(nv)} linhas)")

    if nv["_dt"].max() < d["_dt"].max():
        atraso = (d["_dt"].max() - nv["_dt"].max()).days
        print(f"  ! fonte do monitor esta {atraso} dias atras da planilha")

    # ---------------------------------------------------------- 1. totais
    hm = d[(d["_dt"].dt.year == a.ano) & (d["_dt"].dt.month == a.mes)]
    nm = nv[(nv["_dt"].dt.year == a.ano) & (nv["_dt"].dt.month == a.mes)]
    hp = hm[hm["Gestor_Curto"].map(eh_peer)]

    print("\n" + "-" * 70)
    print("1. TOTAIS")
    print("-" * 70)
    print(f"  planilha historica (todas as gestoras) ... {len(hm)}")
    print(f"  planilha restrita aos PEERS do Python .... {len(hp)}")
    print(f"  monitor novo ............................. {len(nm)}")

    # ------------------------------------------------------ 2/3. so em um
    cx, cn = set(hp["_cnpj"]) - {""}, set(nm["_cnpj"]) - {""}

    print("\n" + "-" * 70)
    print(f"2. SO NO MONITOR NOVO ({len(cn - cx)})")
    print("-" * 70)
    for _, r in nm[nm["_cnpj"].isin(cn - cx)].iterrows():
        outro = d[d["_cnpj"] == r["_cnpj"]]
        onde = (f"na planilha em {outro.iloc[0]['Data_Registro']}"
                if len(outro) else "ausente da planilha")
        print(f"  [{str(r['tipo'])[:6]:<6}] {str(r['nome'])[:44]:<44} {r['data']} | {onde}")

    print("\n" + "-" * 70)
    print(f"3. SO NA PLANILHA ({len(cx - cn)})")
    print("-" * 70)
    for _, r in hp[hp["_cnpj"].isin(cx - cn)].iterrows():
        outro = nv[nv["_cnpj"] == r["_cnpj"]]
        onde = (f"no monitor em {outro.iloc[0]['data']}"
                if len(outro) else "ausente do monitor")
        print(f"  [{str(r['Situacao'])[:20]:<20}] {str(r['Denominacao_Social'])[:38]:<38}"
              f" {r['Data_Registro']} | {onde}")

    print(f"\n  CNPJs em comum: {len(cx & cn)}")

    # -------------------------------------------- 4/5. a planilha filtra?
    print("\n" + "-" * 70)
    print("5. A PLANILHA REMOVE ALGUMA CATEGORIA? (base historica inteira)")
    print("-" * 70)
    tipo = d["Tipo_Fundo"].fillna("").str.upper()
    estr = d["Tipo_Estrutura"].fillna("")
    checks = [
        ("Exclusivos", d["Exclusivo"].fillna("").str.upper().eq("S")),
        ("Mandatos", estr.str.contains("Mandato", case=False)),
        ("Estruturados", tipo.isin(ESTRUTURADOS)),
        ("Previdencia", d["Segmento_Previdencia"].fillna("").str.upper()
         .isin(["S", "SIM", "1", "TRUE"])),
        ("Feeders", d["Denominacao_Social"].fillna("").str.upper()
         .str.contains(r"EM COTAS|\bFIC\b")),
        ("Pre-operacionais", d["Situacao"].eq("Fase Pré-Operacional")),
    ]
    print(f"  {'CATEGORIA':<20} {'QTDE':>6}  VEREDITO")
    for rot, m in checks:
        q = int(m.sum())
        print(f"  {rot:<20} {q:>6}  {'REMOVIDA' if q == 0 else 'MANTIDA (nao e filtro)'}")

    # ------------------------------------------- 6. classes por fundo
    print("\n" + "-" * 70)
    print("6. MULTIPLAS CLASSES NUM MESMO FUNDO")
    print("-" * 70)
    for rot, s in (("planilha", d["_cnpj"]), ("monitor", nv["_cnpj"])):
        s = s[s != ""]
        print(f"  {rot:<9} {len(s)} linhas / {s.nunique()} CNPJs -> "
              f"{len(s) - s.nunique()} excedente(s)")

    # ------------------------------------------- 7. tabela de impacto
    print("\n" + "-" * 70)
    print("7. REGRA | IMPACTO | QTDE")
    print("-" * 70)
    fora = hm[~hm["Gestor_Curto"].map(eh_peer)]
    pre = hp[hp["Situacao"] == "Fase Pré-Operacional"]
    print(f"  {'REGRA':<46} {'IMPACTO':>8}")
    print("  " + "-" * 56)
    print(f"  {'planilha ' + f'{a.mes:02d}/{a.ano}' + ' (total)':<46} {len(hm):>8}")
    print(f"  {'(-) gestoras fora da lista PEERS':<46} {-len(fora):>+8}")
    top = fora["Gestor_Curto"].value_counts().head(5)
    print(f"  {'      ' + ', '.join(f'{k} {v}' for k, v in top.items())[:40]:<46}")
    print(f"  {'(=) universo comparavel':<46} {len(hp):>8}")
    print(f"  {'(-) ainda pre-operacionais (sem classe ativa)':<46} {-len(pre):>+8}")
    print(f"  {'(-) defasagem registro -> inicio de atividade':<46} {'ver 3':>8}")
    print(f"  {'(=) monitor novo':<46} {len(nm):>8}")

    # ------------------------------------------- 8. defasagem das datas
    m = nv.merge(d[["_cnpj", "_dt", "Situacao"]], on="_cnpj",
                 how="inner", suffixes=("_nv", "_h"))
    print("\n" + "-" * 70)
    print("8. DEFASAGEM ENTRE AS DUAS DATAS (fundos que casaram por CNPJ)")
    print("-" * 70)
    if len(m):
        lag = (m["_dt_nv"] - m["_dt_h"]).dt.days
        dif = (m["_dt_nv"].dt.to_period("M") != m["_dt_h"].dt.to_period("M"))
        print(f"  casaram ................... {len(m)}")
        print(f"  mediana ................... {lag.median():+.0f} dias")
        print(f"  monitor posterior ......... {(lag > 0).sum()}/{len(m)}"
              f" ({(lag > 0).mean() * 100:.0f}%)")
        print(f"  caem em MES diferente ..... {dif.sum()}/{len(m)}"
              f" ({dif.mean() * 100:.0f}%)")
        print("\n  => as bases medem eventos diferentes:")
        print("     planilha = registro na CVM | monitor = inicio de atividade da classe")
    else:
        print("  nenhum CNPJ em comum")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
