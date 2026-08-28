# -*- coding: utf-8 -*-

from dotenv import load_dotenv
from databricks import sql
import os

load_dotenv()

conn = sql.connect(
    server_hostname=os.getenv("DATABRICKS_HOST"),
    http_path=os.getenv("DATABRICKS_PATH"),
    access_token=os.getenv("DATABRICKS_TOKEN")
)

cur = conn.cursor()

try:
    print("\n=== COLUNAS RELACIONADAS A GESTORA ===\n")

    cur.execute("""
    SELECT
        table_catalog,
        table_schema,
        table_name,
        column_name,
        data_type
    FROM system.information_schema.columns
    WHERE
        lower(column_name) LIKE '%gestor%'
        OR lower(column_name) LIKE '%gestora%'
        OR lower(column_name) LIKE '%manager%'
        OR lower(column_name) LIKE '%asset%'
        OR lower(column_name) LIKE '%administrador%'
        OR lower(column_name) LIKE '%prestador%'
        OR lower(column_name) LIKE '%instituicao%'
        OR lower(column_name) LIKE '%instituição%'
    ORDER BY
        table_catalog,
        table_schema,
        table_name,
        ordinal_position
    """)

    resultados = cur.fetchall()

    print(f"Colunas encontradas: {len(resultados)}\n")

    for r in resultados:
        print(
            f"{r.table_catalog}."
            f"{r.table_schema}."
            f"{r.table_name}"
            f" | {r.column_name}"
            f" | {r.data_type}"
        )

    print("\n=== TABELAS COM NOMES RELACIONADOS ===\n")

    cur.execute("""
    SELECT
        table_catalog,
        table_schema,
        table_name,
        table_type
    FROM system.information_schema.tables
    WHERE
        lower(table_name) LIKE '%gestor%'
        OR lower(table_name) LIKE '%gestora%'
        OR lower(table_name) LIKE '%manager%'
        OR lower(table_name) LIKE '%asset%'
        OR lower(table_name) LIKE '%administrador%'
        OR lower(table_name) LIKE '%prestador%'
        OR lower(table_name) LIKE '%instituicao%'
        OR lower(table_name) LIKE '%instituição%'
        OR lower(table_name) LIKE '%participante%'
        OR lower(table_name) LIKE '%empresa%'
    ORDER BY
        table_catalog,
        table_schema,
        table_name
    """)

    tabelas = cur.fetchall()

    print(f"Tabelas encontradas: {len(tabelas)}\n")

    for r in tabelas:
        print(
            f"{r.table_catalog}."
            f"{r.table_schema}."
            f"{r.table_name}"
            f" | {r.table_type}"
        )

except Exception as erro:
    print("\nERRO NA BUSCA:")
    print(erro)

finally:
    cur.close()
    conn.close()

print("\nBusca concluida.\n")