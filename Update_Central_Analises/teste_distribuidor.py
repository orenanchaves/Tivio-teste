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
    nome_comercial
FROM marketdata.silver.anbima_prestadores_classe
WHERE codigo_tipo_prestador='DISTRIBUIDOR'
LIMIT 50
""")

for r in cur.fetchall():
    print(r)

cur.close()
conn.close()