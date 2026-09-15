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

# Primeiro, exibe as colunas para confirmarmos as chaves disponíveis
print("\n=== COLUNAS DA TABELA ===\n")

cur.execute("""
DESCRIBE marketdata.silver.anbima_prestadores_classe
""")

for r in cur.fetchall():
    print(r)

print("\n=== DISTRIBUIDORES XP / BTG / ITAU / BRADESCO ===\n")

cur.execute("""
SELECT
    codigo_tipo_prestador,
    nome_comercial,
    razao_social,
    COUNT(*) AS quantidade_registros

FROM marketdata.silver.anbima_prestadores_classe

WHERE codigo_tipo_prestador = 'DISTRIBUIDOR'
  AND (
       UPPER(COALESCE(nome_comercial, '')) LIKE '%XP%'
    OR UPPER(COALESCE(razao_social, '')) LIKE '%XP%'

    OR UPPER(COALESCE(nome_comercial, '')) LIKE '%BTG%'
    OR UPPER(COALESCE(razao_social, '')) LIKE '%BTG%'

    OR UPPER(COALESCE(nome_comercial, '')) LIKE '%ITAU%'
    OR UPPER(COALESCE(nome_comercial, '')) LIKE '%ITAÚ%'
    OR UPPER(COALESCE(razao_social, '')) LIKE '%ITAU%'
    OR UPPER(COALESCE(razao_social, '')) LIKE '%ITAÚ%'

    OR UPPER(COALESCE(nome_comercial, '')) LIKE '%BRADESCO%'
    OR UPPER(COALESCE(razao_social, '')) LIKE '%BRADESCO%'
  )

GROUP BY
    codigo_tipo_prestador,
    nome_comercial,
    razao_social

ORDER BY
    quantidade_registros DESC,
    nome_comercial
""")

for r in cur.fetchall():
    print(r)

cur.close()
conn.close()