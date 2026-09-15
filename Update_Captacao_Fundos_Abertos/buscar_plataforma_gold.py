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
    table_schema,
    table_name,
    column_name

FROM system.information_schema.columns

WHERE table_catalog='marketdata'
AND (
      LOWER(column_name) LIKE '%plata%'
   OR LOWER(column_name) LIKE '%canal%'
   OR LOWER(column_name) LIKE '%distrib%'
)

ORDER BY 1,2,3
""")

for r in cur.fetchall():
    print(r)

cur.close()
conn.close()