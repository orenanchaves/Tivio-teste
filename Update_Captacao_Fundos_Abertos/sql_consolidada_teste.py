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
WITH parametros AS (
    SELECT
        MAX(dt_comptc) AS data_referencia
    FROM marketdata.silver.cvm_informe_diario
),

fluxo AS (
    SELECT
        i.cnpj_fundo_classe,

        SUM(
            CASE
                WHEN i.dt_comptc > date_sub(p.data_referencia, 30)
                 AND i.dt_comptc <= p.data_referencia
                THEN COALESCE(i.captc_dia, 0)
                   - COALESCE(i.resg_dia, 0)
                ELSE 0
            END
        ) AS cap30,

        SUM(
            CASE
                WHEN i.dt_comptc > add_months(p.data_referencia, -12)
                 AND i.dt_comptc <= p.data_referencia
                THEN COALESCE(i.captc_dia, 0)
                   - COALESCE(i.resg_dia, 0)
                ELSE 0
            END
        ) AS cap12,

        SUM(
            CASE
                WHEN i.dt_comptc >= make_date(year(p.data_referencia), 1, 1)
                 AND i.dt_comptc <= p.data_referencia
                THEN COALESCE(i.captc_dia, 0)
                   - COALESCE(i.resg_dia, 0)
                ELSE 0
            END
        ) AS capytd,

        MAX(p.data_referencia) AS data_referencia

    FROM marketdata.silver.cvm_informe_diario i
    CROSS JOIN parametros p

    WHERE i.dt_comptc > add_months(p.data_referencia, -12)

    GROUP BY
        i.cnpj_fundo_classe
),

ultimo_registro AS (
    SELECT
        cnpj_fundo_classe,
        dt_comptc,
        vl_patrim_liq,
        vl_quota,
        nr_cotst,

        ROW_NUMBER() OVER (
            PARTITION BY cnpj_fundo_classe
            ORDER BY dt_comptc DESC
        ) AS rn

    FROM marketdata.silver.cvm_informe_diario
),

classes AS (
    SELECT
        identificador_classe,
        codigo_classe,
        codigo_fundo,
        nome_comercial_classe,
        tipo_anbima,
        nivel1_categoria,
        nivel2_categoria,
        nivel3_subcategoria,
        credito_privado,
        infraestrutura,
        investimento_exterior,
        fundo_esg

    FROM marketdata.silver.anbima_classes_fundo
),

fundos AS (
    SELECT
        codigo_fundo,
        nome_comercial_fundo,
        tipo_fundo

    FROM marketdata.silver.anbima_fundo
)

SELECT
    fluxo.cnpj_fundo_classe AS cnpj,

    COALESCE(
        c.nome_comercial_classe,
        f.nome_comercial_fundo
    ) AS nome,

    f.nome_comercial_fundo,
    c.nome_comercial_classe,

    c.codigo_classe,
    c.codigo_fundo,

    c.tipo_anbima,
    c.nivel1_categoria,
    c.nivel2_categoria,
    c.nivel3_subcategoria,

    c.credito_privado,
    c.infraestrutura,
    c.investimento_exterior,
    c.fundo_esg,

    fluxo.cap30,
    fluxo.cap12,
    fluxo.capytd,

    u.vl_patrim_liq AS pl,
    u.vl_quota AS cota_atual,
    u.nr_cotst AS cotistas,
    u.dt_comptc AS data_ultimo_registro,

    fluxo.data_referencia

FROM fluxo

LEFT JOIN ultimo_registro u
    ON fluxo.cnpj_fundo_classe = u.cnpj_fundo_classe
   AND u.rn = 1

LEFT JOIN classes c
    ON regexp_replace(fluxo.cnpj_fundo_classe, '[^0-9]', '')
     = regexp_replace(c.identificador_classe, '[^0-9]', '')

LEFT JOIN fundos f
    ON c.codigo_fundo = f.codigo_fundo

WHERE COALESCE(
    c.nome_comercial_classe,
    f.nome_comercial_fundo
) IS NOT NULL

ORDER BY fluxo.cap30 DESC

LIMIT 50
""")

for r in cur.fetchall():
    print(r)

cur.close()
conn.close()