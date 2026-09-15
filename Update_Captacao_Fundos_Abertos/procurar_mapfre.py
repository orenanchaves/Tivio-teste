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

cur.execute("""
SELECT
    codigo_classe,
    codigo_tipo_prestador,
    nome_comercial,
    razao_social
FROM marketdata.silver.anbima_prestadores_classe
WHERE UPPER(nome_comercial) LIKE '%MAPFRE%'
   OR UPPER(razao_social) LIKE '%MAPFRE%'
""")


for r in cur.fetchall():
    print(r)

cur.close()
conn.close()