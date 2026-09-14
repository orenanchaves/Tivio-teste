# -*- coding: utf-8 -*-
"""
buscar_cadastro_cvm.py - localiza a tabela de cadastro da CVM no Databricks.

Por que existe
--------------
O SQL do monitor dependia de uma tabela de cadastro num catalogo restrito,
que passou a devolver:

    [INSUFFICIENT_PERMISSIONS] User does not have USE CATALOG. SQLSTATE: 42501

A dependencia foi removida em 14/09/2026 e o nome da tabela nao ficou
registrado em lugar nenhum do projeto. Sao dessa tabela os tres campos
que faltam para o monitor bater com a planilha historica:

    cvm_status      -> Situacao ("Fase Pre-Operacional")
    data de registro na CVM -> Data_Registro da planilha
    is_exclusive    -> Exclusivo (293 de 718 na planilha; 0 de 47 no monitor)

Este script varre o catalogo de metadados e imprime os candidatos, junto
com a linha pronta para colar no .env.

Uso
---
    python buscar_cadastro_cvm.py

Se o catalogo continuar bloqueado, a varredura devolve zero linhas para
ele - o que ja e a resposta: a permissao ainda nao foi concedida.
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from databricks import sql

# colunas que caracterizam o cadastro procurado
PISTAS_COLUNA = [
    "cvm_status", "situacao", "situacao_cvm", "status_cvm",
    "is_exclusive", "exclusivo",
    "data_registro", "dt_registro", "data_registro_cvm",
    "is_pension_fund", "previdencia",
]

# nomes de tabela que costumam carregar esse cadastro
PISTAS_TABELA = ["cadastro", "cvm", "fundo", "registro"]


def consultar(cur, query, titulo):
    print(f"\n{'=' * 70}\n{titulo}\n{'=' * 70}")
    try:
        cur.execute(query)
        linhas = cur.fetchall()
    except Exception as e:
        print(f"  ! falhou: {type(e).__name__}: {str(e)[:160]}")
        return []

    if not linhas:
        print("  (nenhum resultado)")
    return linhas


def main():
    faltando = [v for v in ("DATABRICKS_HOST", "DATABRICKS_PATH",
                            "DATABRICKS_TOKEN") if not os.getenv(v)]
    if faltando:
        sys.exit(f"  ! defina no .env: {', '.join(faltando)}")

    conn = sql.connect(
        server_hostname=os.getenv("DATABRICKS_HOST"),
        http_path=os.getenv("DATABRICKS_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN"),
    )

    try:
        cur = conn.cursor()

        # ---------------------------------------------- 1. catalogos visiveis
        cats = consultar(
            cur,
            "SELECT catalog_name FROM system.information_schema.catalogs "
            "ORDER BY catalog_name",
            "1. CATALOGOS VISIVEIS PARA ESTE TOKEN",
        )
        for c in cats:
            print(f"  {c[0]}")

        # ------------------------------------- 2. tabelas com cara de cadastro
        cond_tab = " OR ".join(
            f"lower(table_name) LIKE '%{p}%'" for p in PISTAS_TABELA
        )
        tabs = consultar(
            cur,
            f"""
            SELECT table_catalog, table_schema, table_name
            FROM system.information_schema.tables
            WHERE ({cond_tab})
            ORDER BY table_catalog, table_schema, table_name
            """,
            "2. TABELAS COM NOME DE CADASTRO / CVM / FUNDO",
        )
        for t in tabs[:60]:
            print(f"  {t[0]}.{t[1]}.{t[2]}")
        if len(tabs) > 60:
            print(f"  ... e mais {len(tabs) - 60}")

        # ------------------------------- 3. o que realmente identifica: colunas
        cond_col = " OR ".join(
            f"lower(column_name) LIKE '%{p}%'" for p in PISTAS_COLUNA
        )
        cols = consultar(
            cur,
            f"""
            SELECT table_catalog, table_schema, table_name,
                   collect_set(column_name) AS colunas,
                   count(*) AS n
            FROM system.information_schema.columns
            WHERE ({cond_col})
            GROUP BY table_catalog, table_schema, table_name
            ORDER BY n DESC
            LIMIT 40
            """,
            "3. TABELAS QUE TEM AS COLUNAS PROCURADAS  <- o que importa",
        )

        melhor = None
        for r in cols:
            nome = f"{r[0]}.{r[1]}.{r[2]}"
            print(f"\n  {nome}   ({r[4]} colunas casadas)")
            print(f"     {sorted(r[3])}")
            if melhor is None:
                melhor = nome

        # ---------------------------------------------------- 4. o que fazer
        print(f"\n{'=' * 70}\n4. PROXIMO PASSO\n{'=' * 70}")
        if melhor:
            print("  Candidata mais provavel:\n")
            print(f"      CVM_CADASTRO={melhor}\n")
            print("  Cole a linha acima no .env, confira os nomes reais das")
            print("  colunas na CTE cadastro_cvm de sql/monitor_fundos_v2.sql")
            print("  (cnpj_fundo, cvm_status, data_registro_cvm, is_exclusive)")
            print("  e rode:\n")
            print("      MONITOR_SQL=monitor_fundos_v2.sql python atualizar_monitor.py")
        else:
            print("  Nenhuma tabela com essas colunas esta visivel para este")
            print("  token. O catalogo restrito continua sem permissao - e")
            print("  isso e um pedido ao TI, nao algo que o codigo resolva.")
            print("\n  Enquanto isso o monitor roda com a v1 ou com a v2 sem")
            print("  o bloco do cadastro, e agosto seguira sem os fundos")
            print("  pre-operacionais (12 dos 16 peers de ago/2026).")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
