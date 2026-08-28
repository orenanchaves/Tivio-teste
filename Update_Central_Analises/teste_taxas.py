# -*- coding: utf-8 -*-
"""
teste_taxas.py - por que taxa_adm / taxa_perf voltaram vazias?

Na rodada real de 28/08 as duas colunas vieram 0 de 13.500 classes, com
publico-alvo (74%) e administrador (87%) preenchidos - ou seja, o join do
monitor funciona e o problema esta em anbima_taxas_classe.

Este script isola cada hipotese, em ordem:
  1. a tabela tem linhas?
  2. quais valores existem em tipo_taxa (o filtro '%administ%' acerta?)
  3. como e o valor_percentual (numero? string com virgula? nulo?)
  4. codigo_classe casa com anbima_classes_fundo?

Rode:  python teste_taxas.py
"""
import os

from dotenv import load_dotenv
from databricks import sql

load_dotenv()

CATALOG = os.getenv("DATABRICKS_CATALOG", "marketdata")
SCHEMA = os.getenv("DATABRICKS_SCHEMA", "silver")
T = f"{CATALOG}.{SCHEMA}.anbima_taxas_classe"
C = f"{CATALOG}.{SCHEMA}.anbima_classes_fundo"

CONSULTAS = [
    ("1. estrutura da tabela", f"DESCRIBE {T}"),

    ("2. volume total", f"SELECT COUNT(*) AS linhas FROM {T}"),

    ("3. valores de tipo_taxa", f"""
        SELECT tipo_taxa, COUNT(*) AS linhas,
               SUM(CASE WHEN valor_percentual IS NULL THEN 1 ELSE 0 END) AS sem_valor
        FROM {T}
        GROUP BY tipo_taxa
        ORDER BY linhas DESC
        LIMIT 40
    """),

    ("4. amostra de linhas", f"SELECT * FROM {T} LIMIT 15"),

    ("5. o filtro do monitor pega alguma coisa?", f"""
        SELECT
            SUM(CASE WHEN lower(tipo_taxa) LIKE '%administ%'   THEN 1 ELSE 0 END) AS bate_administ,
            SUM(CASE WHEN lower(tipo_taxa) LIKE '%performance%' THEN 1 ELSE 0 END) AS bate_performance,
            COUNT(*) AS total
        FROM {T}
    """),

    ("6. valor_percentual: da para converter em numero?", f"""
        SELECT
            COUNT(*) AS linhas,
            SUM(CASE WHEN valor_percentual IS NULL THEN 1 ELSE 0 END) AS nulos,
            SUM(CASE WHEN try_cast(valor_percentual AS DOUBLE) IS NOT NULL THEN 1 ELSE 0 END) AS cast_direto_ok,
            SUM(CASE WHEN try_cast(replace(trim(CAST(valor_percentual AS STRING)), ',', '.') AS DOUBLE) IS NOT NULL
                     THEN 1 ELSE 0 END) AS cast_com_virgula_ok
        FROM {T}
    """),

    ("7. codigo_classe casa com anbima_classes_fundo?", f"""
        SELECT
            COUNT(*) AS classes_desde_2024,
            SUM(CASE WHEN t.codigo_classe IS NOT NULL THEN 1 ELSE 0 END) AS com_taxa
        FROM {C} c
        LEFT JOIN (SELECT DISTINCT codigo_classe FROM {T}) t
            ON t.codigo_classe = c.codigo_classe
        WHERE c.data_inicio_atividade_classe >= '2024-01-01'
    """),
]


def main():
    conn = sql.connect(
        server_hostname=os.getenv("DATABRICKS_HOST"),
        http_path=os.getenv("DATABRICKS_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN"),
    )

    try:
        with conn.cursor() as cur:
            for titulo, q in CONSULTAS:
                print("\n" + "=" * 60)
                print(titulo)
                print("=" * 60)

                try:
                    cur.execute(q)
                    cols = [c[0] for c in cur.description]
                    print(" | ".join(cols))

                    for linha in cur.fetchall():
                        print(" | ".join("" if v is None else str(v) for v in linha))

                except Exception as erro:
                    print("ERRO:", erro)

    finally:
        conn.close()

    print("\n" + "-" * 60)
    print("Leitura do resultado:")
    print("  passo 5 zerado          -> tipo_taxa usa outra nomenclatura;")
    print("                             ajuste o LIKE em sql/monitor_fundos.sql")
    print("  passo 6 com cast_direto_ok = 0 e cast_com_virgula_ok > 0")
    print("                          -> ja resolvido no SQL atual")
    print("  passo 7 com com_taxa = 0 -> a taxa nao e por codigo_classe;")
    print("                             veja no passo 1 qual e a chave")
    print()


if __name__ == "__main__":
    main()
