# -*- coding: utf-8 -*-
"""
atualizar_captacao.py
---------------------
Motor de atualizacao do dashboard "Captacao - Fundos Abertos" (Tivio).

Fluxo:
    Databricks --SQL--> DataFrame --(join plataforma via peers CSV)-->
        --metrics--> FUNDS_DATA (JSON) --> injecao cirurgica no HTML

A PLATAFORMA (XP/BTG/Itau/Bradesco) NAO vem do Databricks.
Ela vem de peers_fundos_abertos.csv (planilha da Vivian), via CNPJ.
"""

import os
import re
import json
import sys
import random
from pathlib import Path

# .env opcional
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import captacao_metrics as cm

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

from tivio_core import template as _tvtpl   # noqa: E402
TEMPLATE = BASE / "templates" / "dashboard_captacao_fundos_abertos.html"
OUT_DIR = BASE / "outputs"
OUT_HTML = OUT_DIR / "dashboard_captacao_fundos_abertos.html"
SQL_FILE = BASE / "sql" / "captacao_fundos_abertos.sql"
PEERS_FILE = BASE / "peers_fundos_abertos.csv"
CDI_SQL_FILE = BASE / "sql" / "cdi_periodos.sql"

USE_MOCK = os.getenv("USE_MOCK", "true").strip().lower() in ("1", "true", "yes", "sim")

CDI = {
    "m": float(os.getenv("CDI_MES", "0.0113")),
    "y": float(os.getenv("CDI_12M", "0.1482")),
    "ytd": float(os.getenv("CDI_YTD", "0.0572")),
}


# --------------------------------------------------------------------------
# Helper: normaliza CNPJ (14 digitos)
# --------------------------------------------------------------------------
def limpar_cnpj(valor):
    import pandas as pd
    if pd.isna(valor):
        return None
    return re.sub(r"\D", "", str(valor)).zfill(14)


# --------------------------------------------------------------------------
# 1) Fonte de dados (Databricks + join plataforma)
# --------------------------------------------------------------------------
def buscar_databricks():
    """Conecta no Databricks, roda o SQL, faz o join da plataforma pelo CNPJ."""
    import pandas as pd
    from databricks import sql  # import tardio: so precisa no modo real

    host = os.getenv("DATABRICKS_HOST")
    http_path = os.getenv("DATABRICKS_PATH")
    token = os.getenv("DATABRICKS_TOKEN")
    if not all([host, http_path, token]):
        raise RuntimeError(
            "Faltam credenciais no .env (DATABRICKS_HOST / DATABRICKS_PATH / DATABRICKS_TOKEN)."
        )

    query = SQL_FILE.read_text(encoding="utf-8")

    conn = sql.connect(server_hostname=host, http_path=http_path, access_token=token)
    try:
        cur = conn.cursor()
        cur.execute(query)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        cur.close()
    finally:
        conn.close()

    print(f"[databricks] {len(rows)} linhas retornadas.")

    # ---- join com a plataforma (planilha da Vivian) ----
    if not PEERS_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo de plataformas nao encontrado: {PEERS_FILE}\n"
            f"Rode 'python preparar_peers.py' antes."
        )

    peers = pd.read_csv(PEERS_FILE, dtype=str, encoding="utf-8-sig")

    df_sql = pd.DataFrame(rows)
    df_sql["cnpj"] = df_sql["cnpj"].apply(limpar_cnpj)
    peers["cnpj"] = peers["cnpj"].apply(limpar_cnpj)

    df_sql = df_sql.merge(
        peers[["cnpj", "plataforma"]],
        how="inner",
        on="cnpj",
    )

    rows = df_sql.to_dict("records")

    print(f"[peers] {len(rows)} linhas apos join plataforma.")

    # pega a data mais recente da consulta
    datas = [
        r.get("data_ultimo_registro")
        for r in rows
        if r.get("data_ultimo_registro")
    ]

    data_ref = max(datas) if datas else None

    return rows, data_ref


# --------------------------------------------------------------------------
# 1b) Mock (para testar o pipeline sem o banco)
# --------------------------------------------------------------------------
def gerar_mock():
    """Gera 4 plataformas x 3 categorias x 10 fundos = 120 linhas ficticias."""
    random.seed(42)
    plats = ["XP", "BTG", "Itau", "Bradesco"]
    cats = ["Renda Fixa Ativa", "Renda Fixa", "Multimercado"]
    gestores = ["ITAU UNIBANCO ASSET MANAG", "BTG PACTUAL ASSET MANAGEM",
                "XP VISTA ASSET MANAGEMENT", "BANCO BRADESCO S.A.",
                "KINEA INVESTIMENTOS LTDA.", "ARX INVESTIMENTOS LTDA",
                "KAPITALO INVESTIMENTOS LT", "TIVIO CAPITAL DISTRIBUIDO"]
    rows = []
    for plat in plats:
        for cat in cats:
            for i in range(10):
                bench = "IMA-B" if (cat == "Renda Fixa" and i % 5 == 0) else "CDI"
                rows.append({
                    "nome": f"MOCK {plat} {cat} FUNDO {i+1:02d}",
                    "cnpj": f"00.000.{random.randint(100,999)}/0001-{random.randint(10,99)}",
                    "plataforma": plat,
                    "categoria": cat,
                    "benchmark": bench,
                    "gestor": random.choice(gestores),
                    "cap30": round(random.uniform(-1.5e9, 2e9), 2),
                    "rent30": round(random.uniform(-1.5, 3.5), 2),
                    "cdi30": None,
                    "cap12": round(random.uniform(-3e9, 8e9), 2),
                    "rent12": round(random.uniform(8, 25), 2),
                    "cdi12": None,
                    "capytd": round(random.uniform(-2e8, 5e9), 2),
                    "rentytd": round(random.uniform(2, 10), 2),
                    "cdiytd": None,
                    "pl": round(random.uniform(1e7, 3e10), 2),
                })
    print(f"[mock] {len(rows)} linhas ficticias geradas.")
    return rows


# --------------------------------------------------------------------------
# 2) Injecao cirurgica no HTML
# --------------------------------------------------------------------------
def injetar_funds_data(html, funds):
    """Troca o bloco const FUNDS_DATA = [ ... ]; pelo novo array."""
    novo_json = json.dumps(funds, ensure_ascii=False)
    novo_bloco = f"const FUNDS_DATA = {novo_json};"

    padrao = re.compile(r"const\s+FUNDS_DATA\s*=\s*\[.*?\]\s*;", re.DOTALL)
    if not padrao.search(html):
        raise RuntimeError(
            "Nao encontrei 'const FUNDS_DATA = [...]' no template. "
            "Confirme que o HTML correto esta em templates/."
        )
    html2, n = padrao.subn(lambda _: novo_bloco, html, count=1)
    print(f"[inject] FUNDS_DATA substituido ({n} ocorrencia). {len(funds)} fundos.")
    return html2


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def buscar_cdi():
    """
    Busca CDI acumulado 30d / 12m / YTD.
    """

    from databricks import sql

    host = os.getenv("DATABRICKS_HOST")
    http_path = os.getenv("DATABRICKS_PATH")
    token = os.getenv("DATABRICKS_TOKEN")

    query = CDI_SQL_FILE.read_text(
        encoding="utf-8"
    )

    conn = sql.connect(
        server_hostname=host,
        http_path=http_path,
        access_token=token
    )

    try:
        cur = conn.cursor()

        cur.execute(query)

        row = cur.fetchone()

        cur.close()

    finally:
        conn.close()

    cdi = {
        "m": float(row[0]) if row[0] is not None else CDI["m"],
        "y": float(row[1]) if row[1] is not None else CDI["y"],
        "ytd": float(row[2]) if row[2] is not None else CDI["ytd"],
    }

    print(
        f"[cdi] "
        f"30d={cdi['m']*100:.2f}% | "
        f"12m={cdi['y']*100:.2f}% | "
        f"ytd={cdi['ytd']*100:.2f}%"
    )

    return cdi
from datetime import date


def _to_date(v):

    if v is None:
        return None

    if isinstance(v, date):
        return v

    try:
        s = str(v)[:10]
        y, m, d = s.split("-")
        return date(
            int(y),
            int(m),
            int(d)
        )

    except Exception:
        return None


def injetar_cabecalho(html, data_ref):

    data_ref = _to_date(data_ref)

    if not data_ref:
        return html

    competencia = f"{data_ref.month:02d}/{data_ref.year}"

    inicio_ytd = date(
        data_ref.year - 1,
        12,
        31
    )

    ytd = (
        f"{inicio_ytd.strftime('%d/%m/%Y')} "
        f"a "
        f"{data_ref.strftime('%d/%m/%Y')}"
    )

    html = re.sub(
        r'(<span class="l">Competência</span><span class="v"><b>)[^<]*(</b>)',
        lambda m: (
            m.group(1)
            + competencia
            + m.group(2)
        ),
        html
    )

    html = re.sub(
        r'(<span class="l">12 meses</span><span class="v">)12m móveis até [^<]*(</span>)',
        lambda m: (
            m.group(1)
            + f"12m móveis até {competencia}"
            + m.group(2)
        ),
        html
    )

    html = re.sub(
        r'(<span class="l">YTD</span><span class="v">)[^<]*(</span>)',
        lambda m: (
            m.group(1)
            + ytd
            + m.group(2)
        ),
        html
    )

    print(
        f"[cabecalho] "
        f"competencia={competencia} | "
        f"ytd={ytd}"
    )

    return html
def main():
    if not TEMPLATE.exists():
        sys.exit(
            f"[erro] Template nao encontrado: {TEMPLATE}\n"
            f"       Coloque o dashboard_captacao_fundos_abertos.html em templates/."
        )

    # 1) dados
    if USE_MOCK:
        records = gerar_mock()
        data_ref = None
        cdi = CDI
    else:
        records, data_ref = buscar_databricks()
        cdi = buscar_cdi()

    # 2) transforma -> FUNDS_DATA
    linhas = [cm.linha_para_dict(r, cdi) for r in records]

    funds = cm.montar_funds_data(
        linhas,
        cdi,
        top_n=10
    )

    # 3) injeta no HTML e grava
    html = TEMPLATE.read_text(encoding="utf-8")

    html = injetar_funds_data(
        html,
        funds
    )

    html = injetar_cabecalho(
        html,
        data_ref
    )

    OUT_DIR.mkdir(exist_ok=True)

    # Apache ECharts: o modulo compartilhado troca as barras em CSS

    # ja renderizadas por graficos com animacao, tooltip e clique.

    html = _tvtpl.ativar_charts(html, '.diverging-bars')


    OUT_HTML.write_text(
        html,
        encoding="utf-8"
    )

    modo = "MOCK" if USE_MOCK else "DATABRICKS"
    print(f"\nOK [{modo}] -> {OUT_HTML}")
    print(f"   {len(funds)} fundos | "
          f"plataformas: {sorted({f['plat'] for f in funds})} | "
          f"categorias: {sorted({f['categoria'] for f in funds})}")


if __name__ == "__main__":
    main()
