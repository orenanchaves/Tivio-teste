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
WITH distribuidores_normalizados AS (
    SELECT DISTINCT
        codigo_classe,

        CASE
            WHEN
                UPPER(COALESCE(nome_comercial, '')) LIKE '%XP%'
                OR UPPER(COALESCE(razao_social, '')) LIKE '%XP INVEST%'
                OR UPPER(COALESCE(razao_social, '')) LIKE '%XP SERVI%'
                OR UPPER(COALESCE(razao_social, '')) LIKE '%XP DISTRIB%'
            THEN 'XP'

            WHEN
                UPPER(COALESCE(nome_comercial, '')) LIKE '%BTG%'
                OR UPPER(COALESCE(razao_social, '')) LIKE '%BTG%'
                OR UPPER(COALESCE(nome_comercial, '')) LIKE '%PACTUAL%'
                OR UPPER(COALESCE(razao_social, '')) LIKE '%PACTUAL%'
            THEN 'BTG'

            WHEN
                UPPER(COALESCE(nome_comercial, '')) LIKE '%ITAU%'
                OR UPPER(COALESCE(nome_comercial, '')) LIKE '%ITAÚ%'
                OR UPPER(COALESCE(razao_social, '')) LIKE '%ITAU%'
                OR UPPER(COALESCE(razao_social, '')) LIKE '%ITAÚ%'
            THEN 'Itau'

            WHEN
                UPPER(COALESCE(nome_comercial, '')) LIKE '%BRADESCO%'
                OR UPPER(COALESCE(razao_social, '')) LIKE '%BRADESCO%'
            THEN 'Bradesco'

            ELSE NULL
        END AS plataforma

    FROM marketdata.silver.anbima_prestadores_classe

    WHERE codigo_tipo_prestador = 'DISTRIBUIDOR'
      AND (
            data_fim_vigencia IS NULL
            OR data_fim_vigencia >= current_date()
      )
),

plataformas_validas AS (
    SELECT DISTINCT
        codigo_classe,
        plataforma
    FROM distribuidores_normalizados
    WHERE plataforma IS NOT NULL
)

SELECT
    codigo_classe,
    COUNT(DISTINCT plataforma) AS quantidade_plataformas,
    CONCAT_WS(
        ', ',
        SORT_ARRAY(COLLECT_SET(plataforma))
    ) AS plataformas

FROM plataformas_validas

GROUP BY codigo_classe

HAVING COUNT(DISTINCT plataforma) > 1

ORDER BY
    quantidade_plataformas DESC,
    codigo_classe

LIMIT 50
""")

print("\n=== QUANTIDADE DE CLASSES POR PLATAFORMA ===\n")

for r in cur.fetchall():
    print(r)

cur.close()
conn.close()