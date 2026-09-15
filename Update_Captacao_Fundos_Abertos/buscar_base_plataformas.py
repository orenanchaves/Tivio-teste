from dotenv import load_dotenv
from databricks import sql
import os

load_dotenv()

host = os.getenv("DATABRICKS_HOST")
http_path = os.getenv("DATABRICKS_PATH")
token = os.getenv("DATABRICKS_TOKEN")

if not host or not http_path or not token:
    raise RuntimeError(
        "Credenciais não encontradas no .env. "
        "Confira DATABRICKS_HOST, DATABRICKS_PATH e DATABRICKS_TOKEN."
    )

conn = sql.connect(
    server_hostname=host,
    http_path=http_path,
    access_token=token
)

cur = conn.cursor()

print("\n=== COLUNAS RELACIONADAS A PLATAFORMA E CAPTACAO ===\n")

cur.execute("""
SELECT
    table_schema,
    table_name,
    column_name,
    data_type

FROM marketdata.information_schema.columns

WHERE
       LOWER(column_name) LIKE '%plataforma%'
    OR LOWER(column_name) LIKE '%canal%'
    OR LOWER(column_name) LIKE '%distrib%'
    OR LOWER(column_name) LIKE '%capt%'
    OR LOWER(column_name) LIKE '%aplic%'
    OR LOWER(column_name) LIKE '%resg%'
    OR LOWER(column_name) LIKE '%flux%'
    OR LOWER(column_name) LIKE '%flow%'
    OR LOWER(column_name) LIKE '%subscription%'
    OR LOWER(column_name) LIKE '%redemption%'
    OR LOWER(column_name) LIKE '%volume%'

ORDER BY
    table_schema,
    table_name,
    column_name
""")

resultados = cur.fetchall()

print(f"Total de colunas encontradas: {len(resultados)}\n")

for r in resultados:
    print(r)

print("\n=== TABELAS COM NOMES RELACIONADOS ===\n")

cur.execute("""
SELECT DISTINCT
    table_schema,
    table_name

FROM marketdata.information_schema.tables

WHERE
       LOWER(table_name) LIKE '%plataforma%'
    OR LOWER(table_name) LIKE '%canal%'
    OR LOWER(table_name) LIKE '%distrib%'
    OR LOWER(table_name) LIKE '%capt%'
    OR LOWER(table_name) LIKE '%aplic%'
    OR LOWER(table_name) LIKE '%resg%'
    OR LOWER(table_name) LIKE '%flux%'
    OR LOWER(table_name) LIKE '%flow%'
    OR LOWER(table_name) LIKE '%subscription%'
    OR LOWER(table_name) LIKE '%redemption%'
    OR LOWER(table_name) LIKE '%ranking%'

ORDER BY
    table_schema,
    table_name
""")

tabelas = cur.fetchall()

print(f"Total de tabelas encontradas: {len(tabelas)}\n")

for r in tabelas:
    print(r)

cur.close()
conn.close()