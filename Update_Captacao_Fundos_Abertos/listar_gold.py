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
SHOW TABLES IN marketdata.gold
""")

for r in cur.fetchall():
    print(r)

cur.close()
conn.close()