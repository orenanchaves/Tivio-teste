# -*- coding: utf-8 -*-
"""databricks_client.py · Central de Análises · Tivio Capital"""
import pandas as pd
import config


def _conectar():
    from databricks import sql
    return sql.connect(
        server_hostname=config.DATABRICKS["server_hostname"],
        http_path=config.DATABRICKS["http_path"],
        access_token=config.DATABRICKS["access_token"],
    )


def consultar(query: str) -> pd.DataFrame:
    if config.USE_MOCK:
        return _mock()
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            cols = [c[0] for c in cur.description]
            rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()


def carregar_sql(nome: str) -> str:
    return (config.SQL_DIR / nome).read_text(encoding="utf-8")


# ===== MOCK: espelha portfolioanalytics.gold.vw_aum =====
def _mock() -> pd.DataFrame:
    import datetime, random
    random.seed(7)
    fundos = [
        ("TIVIO VÉRTICE ITAÚ MULTIMESAS FIRF", "Investment Solutions"),
        ("TIVIO DÓLAR CAMBIAL FIF CIC CAMBIAL", "Investment Solutions"),
        ("TIVIO BANKS RF CP RL", "High Grade"),
        ("TIVIO RF ATIVO LONGO PRAZO FI", "Investment Solutions"),
        ("TIVIO INSTITUCIONAL 15 FIF CI RF CP", "High Grade"),
        ("TIVIO ALPHA DI FIF RF", "High Grade"),
        ("TIVIO LOW VOL FIM", "Multimercado"),
        ("TIVIO ZENIT AÇÕES FIA", "Renda Variável"),
        ("TIVIO GTF INFRA FI-INFRA RF", "High Grade"),
        ("TIVIO PREV RF CRÉDITO FIC", "Previdência"),
    ]
    distribuidores = ["TIVIO CAPITAL", "BRADESCO PRIVATE", "AGORA CTVM",
                      "MIRAE CCTVM", "XP INVESTIMENTOS", "BTG PACTUAL", "ITAÚ"]
    tipos = ["PF - Private", "PJ não financeira - Private", "Conta e ordem",
             "Fundos de investimento", "Institucional"]
    hoje = datetime.date(2026, 8, 27)
    linhas = []
    for cod, (nome, vert) in enumerate(fundos, start=100):
        for dist in random.sample(distribuidores, random.randint(2, 5)):
            linhas.append({
                "date": hoje,
                "fund_code": cod,
                "fund_name": nome,
                "distributor_name": dist,
                "normalized_vertical": vert,
                "client_type": random.choice(tipos),
                "aum": round(random.uniform(5, 260) * 1_000_000, 2),
            })
    return pd.DataFrame(linhas)
