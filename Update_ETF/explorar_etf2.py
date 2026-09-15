# explorar_etf2.py
from dotenv import load_dotenv
from databricks import sql
import os
load_dotenv()
conn = sql.connect(
    server_hostname=os.getenv("DATABRICKS_HOST"),
    http_path=os.getenv("DATABRICKS_PATH"),
    access_token=os.getenv("DATABRICKS_TOKEN"))
cur = conn.cursor()

print("\n=== 1) CATEGORIAS DISTINTAS (scty_ctgy_nm) ===")
cur.execute("""
SELECT scty_ctgy_nm, COUNT(*) n
FROM marketdata.silver.b3_instrumentos_financeiros
WHERE rpt_dt = (SELECT MAX(rpt_dt) FROM marketdata.silver.b3_instrumentos_financeiros)
GROUP BY scty_ctgy_nm ORDER BY n DESC
""")
for r in cur.fetchall(): print(r)

print("\n=== 2) AMOSTRA DE ETFs (ticker terminando em 11) ===")
cur.execute("""
SELECT tckr_symb, asst_desc, scty_ctgy_nm, sgmt_nm, mkt_nm, crpn_nm, isin_isin
FROM marketdata.silver.b3_instrumentos_financeiros
WHERE rpt_dt = (SELECT MAX(rpt_dt) FROM marketdata.silver.b3_instrumentos_financeiros)
  AND tckr_symb RLIKE '11$'
ORDER BY tckr_symb LIMIT 30
""")
for r in cur.fetchall(): print(r)

print("\n=== 3) daily_price: amostra com etf_navps preenchido ===")
cur.execute("""
SELECT date, instrument_id, contract_identifier, etf_navps, fund_pl,
       outstanding_shares, financial_traded_volume
FROM marketdata.silver.daily_price
WHERE etf_navps IS NOT NULL
ORDER BY date DESC LIMIT 15
""")
for r in cur.fetchall(): print(r)

cur.close(); conn.close()