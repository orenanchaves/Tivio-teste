# -*- coding: utf-8 -*-
"""
explorar_etf.py
---------------
Sondagem do Databricks para descobrir a base de ETFs.
Roda 3 investigacoes:
  1) DESCRIBE das tabelas B3 candidatas
  2) Busca colunas que possam classificar ETF (etf/tipo/segmento/especie)
  3) Busca tabelas com nome relacionado a ETF/instrumento/fundo

O aviso do pyarrow pode ser ignorado (usamos fetchall()).
"""

import os
from dotenv import load_dotenv
from databricks import sql

load_dotenv()

conn = sql.connect(
    server_hostname=os.getenv("DATABRICKS_HOST"),
    http_path=os.getenv("DATABRICKS_PATH"),
    access_token=os.getenv("DATABRICKS_TOKEN"),
)
cur = conn.cursor()


def secao(titulo):
    print("\n" + "=" * 60)
    print(titulo)
    print("=" * 60)


# 1) DESCRIBE das tabelas B3 candidatas ----------------------------------
CANDIDATAS = [
    "marketdata.silver.b3_instrumentos_financeiros",
    "marketdata.silver.b3_negocios_consolidado",
    "marketdata.silver.daily_price",
    "marketdata.gold.vw_prices",
    "marketdata.gold.vw_b3_instrumentos_financeiro",
]
for tab in CANDIDATAS:
    secao(f"DESCRIBE {tab}")
    try:
        cur.execute(f"DESCRIBE {tab}")
        for r in cur.fetchall():
            print(r)
    except Exception as e:
        print(f"[erro] {e}")


# 2) Colunas que possam classificar ETF ----------------------------------
secao("COLUNAS COM etf / tipo / segmento / especie / classe")
try:
    cur.execute(
        """
        SELECT table_schema, table_name, column_name, data_type
        FROM system.information_schema.columns
        WHERE table_catalog = 'marketdata'
          AND (
                LOWER(column_name) LIKE '%etf%'
             OR LOWER(column_name) LIKE '%segmento%'
             OR LOWER(column_name) LIKE '%especie%'
             OR LOWER(column_name) LIKE '%tipo_ativo%'
             OR LOWER(column_name) LIKE '%tipo_instrumento%'
             OR LOWER(column_name) LIKE '%security_type%'
             OR LOWER(column_name) LIKE '%ticker%'
             OR LOWER(column_name) LIKE '%isin%'
          )
        ORDER BY table_schema, table_name, column_name
        """
    )
    linhas = cur.fetchall()
    print(f"Total: {len(linhas)}\n")
    for r in linhas:
        print(r)
except Exception as e:
    print(f"[erro] {e}")


# 3) Tabelas com nome relacionado ----------------------------------------
secao("TABELAS COM NOME etf / instrumento / fundo / cotacao")
try:
    cur.execute(
        """
        SELECT table_schema, table_name
        FROM system.information_schema.tables
        WHERE table_catalog = 'marketdata'
        ORDER BY table_schema, table_name
        """
    )
    for r in cur.fetchall():
        txt = f"{r.table_schema}.{r.table_name}".lower()
        if any(k in txt for k in ("etf", "instrument", "fund", "cota", "price", "b3")):
            print(r)
except Exception as e:
    print(f"[erro] {e}")


cur.close()
conn.close()
print("\nConcluido. Mande os 3 resultados para montarmos o SQL do ETF.")
