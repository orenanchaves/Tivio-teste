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

print("\n=== COBERTURA CO_GESTOR ===\n")

cur.execute("""
SELECT
    COUNT(*) AS linhas_co_gestor,
    COUNT(DISTINCT codigo_classe) AS classes_com_co_gestor,
    COUNT(DISTINCT codigo_fundo) AS fundos_com_co_gestor
FROM marketdata.silver.anbima_prestadores_classe
WHERE upper(trim(codigo_tipo_prestador)) = 'CO_GESTOR'
""")

for r in cur.fetchall():
    print(r)

print("\n=== COBERTURA DAS CLASSES DESDE 2024 ===\n")

cur.execute("""
SELECT
    COUNT(*) AS total_linhas,
    COUNT(DISTINCT codigo_classe) AS classes_distintas,
    COUNT(DISTINCT codigo_fundo) AS fundos_distintos
FROM marketdata.silver.anbima_classes_fundo
WHERE data_inicio_atividade_classe >= '2024-01-01'
""")

for r in cur.fetchall():
    print(r)

print("\n=== COBERTURA DO JOIN POR CODIGO_CLASSE ===\n")

cur.execute("""
SELECT
    COUNT(*) AS total_classes,
    SUM(
        CASE
            WHEN p.codigo_classe IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS classes_com_co_gestor,
    SUM(
        CASE
            WHEN p.codigo_classe IS NULL THEN 1
            ELSE 0
        END
    ) AS classes_sem_co_gestor
FROM marketdata.silver.anbima_classes_fundo c
LEFT JOIN (
    SELECT DISTINCT codigo_classe
    FROM marketdata.silver.anbima_prestadores_classe
    WHERE upper(trim(codigo_tipo_prestador)) = 'CO_GESTOR'
) p
    ON p.codigo_classe = c.codigo_classe
WHERE c.data_inicio_atividade_classe >= '2024-01-01'
""")

for r in cur.fetchall():
    print(r)

print("\n=== COBERTURA DO JOIN POR CODIGO_FUNDO ===\n")

cur.execute("""
SELECT
    COUNT(*) AS total_classes,
    SUM(
        CASE
            WHEN p.codigo_fundo IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS classes_com_co_gestor_via_fundo,
    SUM(
        CASE
            WHEN p.codigo_fundo IS NULL THEN 1
            ELSE 0
        END
    ) AS classes_sem_co_gestor_via_fundo
FROM marketdata.silver.anbima_classes_fundo c
LEFT JOIN (
    SELECT DISTINCT codigo_fundo
    FROM marketdata.silver.anbima_prestadores_classe
    WHERE upper(trim(codigo_tipo_prestador)) = 'CO_GESTOR'
) p
    ON p.codigo_fundo = c.codigo_fundo
WHERE c.data_inicio_atividade_classe >= '2024-01-01'
""")

for r in cur.fetchall():
    print(r)

print("\n=== CLASSES SEM CO_GESTOR COM OUTROS PRESTADORES ===\n")

cur.execute("""
SELECT
    c.codigo_fundo,
    c.codigo_classe,
    COALESCE(c.nome_comercial_classe, c.razao_social_classe) AS fundo,
    concat_ws(
        ' / ',
        sort_array(
            collect_set(p.codigo_tipo_prestador)
        )
    ) AS tipos_disponiveis,
    concat_ws(
        ' / ',
        sort_array(
            collect_set(p.nome_comercial)
        )
    ) AS prestadores_disponiveis
FROM marketdata.silver.anbima_classes_fundo c
LEFT JOIN marketdata.silver.anbima_prestadores_classe p
    ON p.codigo_classe = c.codigo_classe
WHERE c.data_inicio_atividade_classe >= '2024-01-01'
  AND NOT EXISTS (
      SELECT 1
      FROM marketdata.silver.anbima_prestadores_classe cg
      WHERE cg.codigo_classe = c.codigo_classe
        AND upper(trim(cg.codigo_tipo_prestador)) = 'CO_GESTOR'
  )
GROUP BY
    c.codigo_fundo,
    c.codigo_classe,
    COALESCE(c.nome_comercial_classe, c.razao_social_classe)
LIMIT 30
""")

for r in cur.fetchall():
    print(r)

cur.close()
conn.close()