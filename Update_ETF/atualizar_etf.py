# -*- coding: utf-8 -*-
"""
atualizar_etf.py
----------------
Motor de atualizacao do dashboard "Analise · ETF" (Tivio).

Fluxo:
    Databricks --SQL--> DataFrame --metrics--> ETFS_DATA (JSON)
                                                   |
                       (opcional) merge com planilha manual de fees/peers
                                                   |
                          injecao cirurgica no HTML (regex)
                                                   |
                       outputs/dashboard_etf.html

IMPORTANTE:
  O dashboard de ETF tem MUITO conteudo estatico (narrativa, timeline,
  caminhos estrategicos). Este motor automatiza apenas os BLOCOS DE DADOS
  que voce marcar com o esquema de injecao (ver README, secao 5).
  Comece pelo modo mock (USE_MOCK=true) para validar o pipeline.
"""

import os
import re
import json
import sys
import random
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import etf_metrics as em

# --------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent
TEMPLATE = BASE / "templates" / "dashboard_etf.html"
OUT_DIR = BASE / "outputs"
OUT_HTML = OUT_DIR / "dashboard_etf.html"
SQL_FILE = BASE / "sql" / "etf.sql"
PEERS_FILE = BASE / "peers_etf.csv"  # opcional: fees/peers manuais

USE_MOCK = os.getenv("USE_MOCK", "true").strip().lower() in ("1", "true", "yes", "sim")


# --------------------------------------------------------------------------
# 1) Fonte de dados
# --------------------------------------------------------------------------
def buscar_databricks():
    """Conecta no Databricks, roda o SQL e devolve lista de dicts (records)."""
    from databricks import sql

    server_hostname = os.getenv("DATABRICKS_HOST")
    http_path = os.getenv("DATABRICKS_PATH")
    access_token = os.getenv("DATABRICKS_TOKEN")

    if not all([server_hostname, http_path, access_token]):
        raise RuntimeError(
            "[databricks] Variaveis ausentes: "
            "DATABRICKS_HOST / DATABRICKS_PATH / DATABRICKS_TOKEN"
        )

    if not SQL_FILE.exists():
        raise FileNotFoundError(f"[databricks] SQL nao encontrado: {SQL_FILE}")

    query = SQL_FILE.read_text(encoding="utf-8")

    with sql.connect(
        server_hostname=server_hostname,
        http_path=http_path,
        access_token=access_token,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            cols = [c[0] for c in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    print(f"[databricks] {len(rows)} linhas retornadas.")
    return rows


# --------------------------------------------------------------------------
# 1b) Mock
# --------------------------------------------------------------------------
def categoria_macro(ticker, categoria=""):
    t = (ticker or "").upper()

    if any(x in t for x in [
        "BTC","BIT","ETH","HASH","CRPT","DEFI",
        "QBTC","QETH","ETHE","BITH"
    ]):
        return "Cripto"

    if any(x in t for x in [
        "IMAB","IRFM","B5P","DEBB",
        "LFTS","USDB","AGGX"
    ]):
        return "Renda Fixa"

    if any(x in t for x in [
        "GOLD","OURO","SLVR",
        "PRAF","OROF"
    ]):
        return "Commodities"

    if any(x in t for x in [
        "SPX","IVVB","NASD",
        "ACWI","VWRA","WRLD"
    ]):
        return "EUA"

    if any(x in t for x in [
        "AGRI","AGRO","CORN"
    ]):
        return "Agro"

    if any(x in t for x in [
        "SMAL","SMAC","SCVB"
    ]):
        return "Small Caps"

    if any(x in t for x in [
        "DIVO","DIVD","NDIV"
    ]):
        return "Dividendos"

    if any(x in t for x in [
        "TECK","UTEC","XTEC",
        "SEMI","CHIP"
    ]):
        return "Tecnologia"

    return categoria or "Outros"
    

def aplicar_categoria_macro(etfs):
    """Anexa o campo categoria_macro em cada ETF (idempotente)."""
    for etf in etfs:
        etf["categoria_macro"] = categoria_macro(
            etf.get("ticker"),
            etf.get("categoria"),
        )
    return etfs

def aplicar_peers(etfs):
    import csv
    caminho = BASE / "peers_etf.csv"
    if not caminho.exists():
        print("[peers] peers_etf.csv nao encontrado - pulando.")
        return etfs
    mapa = {}
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            tk = (row.get("ticker") or "").strip().upper()
            if tk:
                mapa[tk] = row
    aplicados = 0
    for etf in etfs:
        tk = (etf.get("ticker") or "").strip().upper()
        info = mapa.get(tk)
        if not info:
            continue
        fee = (info.get("fee") or "").strip()
        cnpj = (info.get("cnpj") or "").strip()
        if fee:
            try:
                etf["fee"] = float(fee.replace(",", "."))
            except ValueError:
                pass
        if cnpj:
            etf["cnpj"] = cnpj
        aplicados += 1

    print(f"[peers] fee/cnpj aplicados em {aplicados} ETFs.")
    return etfs



def gerar_mock():
    random.seed(42)

    gestoras = [
        "BTG Pactual",
        "iShares",
        "XP/Trend",
        "Itau",
        "Bradesco",
        "Banco do Brasil",
        "Investo",
        "Nu Asset",
        "Teva",
        "Buena Vista",
    ]

    cats = [
        "Renda Fixa",
        "RV Brasil",
        "RV Int",
        "Multi",
        "Cripto",
    ]

    rows = []

    for i in range(40):
        cat = random.choice(cats)

        rows.append({
            "ticker": f"MOCK{i:02d}11",
            "nome": f"MOCK ETF {cat} {i+1:02d}",
            "gestora": random.choice(gestoras),
            "categoria": cat,
            "pl": round(random.uniform(1e8, 2.2e10), 2),
            "fee": round(random.uniform(0.15, 0.80), 2),
            "cap12": round(random.uniform(-1e9, 4e9), 2),
            "cnpj": f"00.000.{random.randint(100,999)}/0001-{random.randint(10,99)}",
        })

    print(f"[mock] {len(rows)} ETFs ficticios gerados.")
    return rows

# --------------------------------------------------------------------------
# 2) Injecao cirurgica no HTML
# --------------------------------------------------------------------------
def injetar_bloco(html, marcador, conteudo):
    """
    Substitui o trecho entre:
        <!-- {marcador}:START --> ... <!-- {marcador}:END -->
    pelo `conteudo`. Assim voce marca no HTML SO os blocos de dados.
    Retorna (html, n_substituicoes).
    """
    padrao = re.compile(
        rf"(<!--\s*{re.escape(marcador)}:START\s*-->).*?(<!--\s*{re.escape(marcador)}:END\s*-->)",
        re.DOTALL,
    )
    novo, n = padrao.subn(lambda m: m.group(1) + conteudo + m.group(2), html)
    return novo, n


def injetar_etfs_data(html, etfs):
    """Injeta um const ETFS_DATA = [...] se o template tiver o marcador."""
    etfs = aplicar_categoria_macro(etfs)
    novo_json = json.dumps(etfs, ensure_ascii=False)
    bloco = f"const ETFS_DATA = {novo_json};"
    padrao = re.compile(r"const\s+ETFS_DATA\s*=\s*\[.*?\]\s*;", re.DOTALL)
    if padrao.search(html):
        html, n = padrao.subn(lambda _: bloco, html, count=1)
        print(f"[inject] ETFS_DATA substituido ({n}).")
    else:
        print("[inject] (sem const ETFS_DATA no template — pulando)")
    return html


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    if not TEMPLATE.exists():
        sys.exit(
            f"[erro] Template nao encontrado: {TEMPLATE}\n"
            f"       Coloque dashboard_etf.html em templates/."
        )

    records = gerar_mock() if USE_MOCK else buscar_databricks()

    linhas = [em.linha_para_dict(r) for r in records]
    etfs = em.montar_etfs_data(linhas)

    # Corrige datas placeholder da B3
    for etf in etfs:
        if str(etf.get("data_inicio")) == "9999-12-31":
            etf["data_inicio"] = None

        if etf.get("fee") in ("", "-", "null"):
            etf["fee"] = None

    etfs = aplicar_peers(etfs)

    com_fee = sum(
        1
        for etf in etfs
        if etf.get("fee") is not None
    )

    # sem_data era usada logo abaixo sem nunca ter sido atribuida: o
    # script quebrava com UnboundLocalError em toda execucao, antes de
    # gravar o HTML.
    sem_data = sum(
        1
        for etf in etfs
        if not etf.get("data_inicio")
    )

    print(
        f"[validacao] Cobertura fee: "
        f"{(com_fee/len(etfs))*100:.1f}%"
    )

    print(
        f"[validacao] Cobertura data_inicio: "
        f"{((len(etfs)-sem_data)/len(etfs))*100:.1f}%"
    )
    

    sem_fee = [
        etf["ticker"]
        for etf in etfs
        if etf.get("fee") is None
    ]

    print(
        f"[validacao] ETFs sem fee: {len(sem_fee)}"
    )

    print(
        "[validacao] Sem fee: "
        + ", ".join(sem_fee[:20])
    )

    sem_data = sum(
        1
        for etf in etfs
        if not etf.get("data_inicio")
    )

    print(f"[validacao] ETFs sem data_inicio: {sem_data}")

    sem_data_tickers = [
        etf["ticker"]
        for etf in etfs
        if not etf.get("data_inicio")
    ]

    print(
        "[validacao] Sem data: "
        + ", ".join(sem_data_tickers)
    )

    gestoras = em.agregar_por_gestora(etfs)

    html = TEMPLATE.read_text(encoding="utf-8")

    # 1) se existir um const ETFS_DATA, injeta o array completo
    html = injetar_etfs_data(html, etfs)

    # 2) injeta blocos marcados (exemplos). Marque no HTML com:
    #    <!-- KPIS:START --> ... <!-- KPIS:END -->
    total_pl = sum(e["pl"] for e in etfs if e["pl"])
    kpis_html = (
        f'<div class="kpi-num">{len(etfs)}</div>'  # exemplo simples
    )
    html, n = injetar_bloco(html, "KPIS", kpis_html)
    if n:
        print(f"[inject] bloco KPIS atualizado ({n}).")

    OUT_DIR.mkdir(exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")

    modo = "MOCK" if USE_MOCK else "DATABRICKS"
    print(f"\nOK [{modo}] -> {OUT_HTML}")
    print(f"   {len(etfs)} ETFs | gestoras: {len(gestoras)} | PL total: R$ {total_pl/1e9:.1f} Bi")


if __name__ == "__main__":
    main()
