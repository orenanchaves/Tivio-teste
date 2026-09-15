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

print("\n=== COLUNAS ===\n")
cur.execute("DESCRIBE marketdata.silver.daily_cdi_price")
for r in cur.fetchall():
    print(r)

print("\n=== 10 LINHAS ===\n")
cur.execute("""
SELECT *
FROM marketdata.silver.daily_cdi_price
ORDER BY 1 DESC
LIMIT 10
""")
for r in cur.fetchall():
    print(r)

cur.close()
conn.close()