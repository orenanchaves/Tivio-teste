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
    print("\n=== DESCRIBE marketdata.gold.vw_anbima_gestor ===\n")

    cur.execute("""
        DESCRIBE marketdata.gold.vw_anbima_gestor
    """)

    colunas = cur.fetchall()

    for r in colunas:
        print(r)

    print("\n=== AMOSTRA marketdata.gold.vw_anbima_gestor ===\n")

    cur.execute("""
        SELECT *
        FROM marketdata.gold.vw_anbima_gestor
        LIMIT 30
    """)

    nomes_colunas = [c[0] for c in cur.description]

    print("COLUNAS:")
    print(nomes_colunas)
    print()

    for r in cur.fetchall():
        print(r)

except Exception as erro:
    print("\nERRO:")
    print(erro)

finally:
    cur.close()
    conn.close()

print("\nTeste concluido.\n")