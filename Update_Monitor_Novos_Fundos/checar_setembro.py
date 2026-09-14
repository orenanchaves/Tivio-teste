# -*- coding: utf-8 -*-
import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from databricks import sql

load_dotenv()

BASE = Path(__file__).resolve().parent
SQL_FILE = BASE / "sql" / "monitor_fundos.sql"

CATALOG = os.getenv("DATABRICKS_CATALOG", "marketdata")
SCHEMA = os.getenv("DATABRICKS_SCHEMA", "silver")

query = SQL_FILE.read_text(encoding="utf-8").format(
    catalog=CATALOG,
    schema=SCHEMA,
    link_base="https://cvmweb.cvm.gov.br/",
    data_ini="2024-01-01",
)

conn = sql.connect(
    server_hostname=os.getenv("DATABRICKS_HOST"),
    http_path=os.getenv("DATABRICKS_PATH"),
    access_token=os.getenv("DATABRICKS_TOKEN"),
)

try:
    with conn.cursor() as cur:
        cur.execute(query)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
finally:
    conn.close()

df = pd.DataFrame(rows, columns=cols)

print(f"\ntotal de linhas: {len(df)}")

df["_dt"] = pd.to_datetime(df["data_registro"], format="%d/%m/%Y", errors="coerce")
df["_ano"] = df["_dt"].dt.year
df["_mes"] = df["_dt"].dt.month

print("\n=== contagem por ano/mes (2026) ===")
print(
    df[df["_ano"] == 2026]
    .groupby("_mes")
    .size()
    .to_string()
)

print("\n=== data mais recente ===")
print(df["_dt"].max())

print("\n=== setembro/2026 ===")
set26 = df[(df["_ano"] == 2026) & (df["_mes"] == 9)]
print(f"{len(set26)} linhas")
print(set26[["fund_name", "data_registro", "gestora"]].to_string(index=False))

print("\n=== datas nulas ===")
print(int(df["_dt"].isna().sum()))