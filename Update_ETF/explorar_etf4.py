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
    tckr_symb,
    crpn_nm,
    asst_desc,
    scty_ctgy_nm
FROM marketdata.silver.b3_instrumentos_financeiros
WHERE rpt_dt = (
    SELECT MAX(rpt_dt)
    FROM marketdata.silver.b3_instrumentos_financeiros
)
AND scty_ctgy_nm LIKE 'ETF%'
ORDER BY tckr_symb
LIMIT 50
""")

for r in cur.fetchall():
    print(r)

cur.close()
conn.close()