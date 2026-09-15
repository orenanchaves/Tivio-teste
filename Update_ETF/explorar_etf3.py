from dotenv import load_dotenv
from databricks import sql
import os
load_dotenv()
conn = sql.connect(
    server_hostname=os.getenv("DATABRICKS_HOST"),
    http_path=os.getenv("DATABRICKS_PATH"),
    access_token=os.getenv("DATABRICKS_TOKEN"))
cur = conn.cursor()

print("\n=== 1) QUANTOS ETFs (categoria ETF%) ===")
cur.execute("""
SELECT scty_ctgy_nm, COUNT(*) n
FROM marketdata.silver.b3_instrumentos_financeiros
WHERE rpt_dt=(SELECT MAX(rpt_dt) FROM marketdata.silver.b3_instrumentos_financeiros)
  AND scty_ctgy_nm LIKE 'ETF%'
GROUP BY scty_ctgy_nm
""")
for r in cur.fetchall(): print(r)

print("\n=== 2) ETFs reais com mkt_cptlstn (tamanho) ===")
cur.execute("""
SELECT tckr_symb, asst_desc, scty_ctgy_nm, crpn_nm, mkt_cptlstn
FROM marketdata.silver.b3_instrumentos_financeiros
WHERE rpt_dt=(SELECT MAX(rpt_dt) FROM marketdata.silver.b3_instrumentos_financeiros)
  AND scty_ctgy_nm LIKE 'ETF%'
ORDER BY mkt_cptlstn DESC NULLS LAST
LIMIT 30
""")
for r in cur.fetchall(): print(r)

print("\n=== 3) quantos ETFs tem mkt_cptlstn preenchido ===")
cur.execute("""
SELECT COUNT(*) total,
       COUNT(mkt_cptlstn) com_mktcap,
       COUNT(CASE WHEN mkt_cptlstn>0 THEN 1 END) com_valor
FROM marketdata.silver.b3_instrumentos_financeiros
WHERE rpt_dt=(SELECT MAX(rpt_dt) FROM marketdata.silver.b3_instrumentos_financeiros)
  AND scty_ctgy_nm LIKE 'ETF%'
""")
for r in cur.fetchall(): print(r)

cur.close(); conn.close()