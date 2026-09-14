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
    print("\n=== DESCRIBE anbima_prestadores_fundo ===\n")

    cur.execute("""
        DESCRIBE marketdata.silver.anbima_prestadores_fundo
    """)

    for r in cur.fetchall():
        print(r)

    print("\n=== TIPOS DE PRESTADOR NO FUNDO ===\n")

    cur.execute("""
        SELECT
            codigo_tipo_prestador,
            COUNT(*) AS quantidade
        FROM marketdata.silver.anbima_prestadores_fundo
        GROUP BY codigo_tipo_prestador
        ORDER BY quantidade DESC
    """)

    for r in cur.fetchall():
        print(r)

    print("\n=== AMOSTRA DE PRESTADORES DO FUNDO ===\n")

    cur.execute("""
        SELECT *
        FROM marketdata.silver.anbima_prestadores_fundo
        LIMIT 30
    """)

    colunas = [c[0] for c in cur.description]

    print("COLUNAS:")
    print(colunas)
    print()

    for r in cur.fetchall():
        print(r)

    print("\n=== COBERTURA DESDE 2024 ===\n")

    cur.execute("""
        SELECT
            COUNT(*) AS total_classes,

            SUM(
                CASE
                    WHEN pf.codigo_fundo IS NOT NULL THEN 1
                    ELSE 0
                END
            ) AS classes_com_prestador_fundo,

            SUM(
                CASE
                    WHEN pf.codigo_fundo IS NULL THEN 1
                    ELSE 0
                END
            ) AS classes_sem_prestador_fundo

        FROM marketdata.silver.anbima_classes_fundo c

        LEFT JOIN (
            SELECT DISTINCT codigo_fundo
            FROM marketdata.silver.anbima_prestadores_fundo
        ) pf
            ON pf.codigo_fundo = c.codigo_fundo

        WHERE c.data_inicio_atividade_classe >= '2024-01-01'
    """)

    for r in cur.fetchall():
        print(r)

except Exception as erro:
    print("\nERRO:")
    print(erro)

finally:
    cur.close()
    conn.close()

print("\nTeste concluido.\n")