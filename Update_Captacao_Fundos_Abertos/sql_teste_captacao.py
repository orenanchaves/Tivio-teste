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

WITH captacao AS (

    SELECT
        cnpj_fundo_classe,

        SUM(
            CASE
                WHEN dt_comptc >= current_date() - 30
                THEN captc_dia - resg_dia
                ELSE 0
            END
        ) AS cap30,

        MAX(vl_patrim_liq) AS pl

    FROM marketdata.silver.cvm_informe_diario

    GROUP BY cnpj_fundo_classe
)

SELECT *
FROM captacao
ORDER BY cap30 DESC
LIMIT 20

""")

for r in cur.fetchall():
    print(r)

cur.close()
conn.close()