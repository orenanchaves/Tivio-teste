# -*- coding: utf-8 -*-
"""
testar_conexao.py - confere a chave do Databricks antes de rodar qualquer
ambiente.

Rode da raiz ou de dentro de qualquer pasta Update_*:

    python testar_conexao.py
    python ..\testar_conexao.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tivio_core import db   # noqa: E402


def main():
    print("\nTeste de conexao - Databricks")
    print("-" * 46)

    import os

    for v in ("DATABRICKS_HOST", "DATABRICKS_PATH", "DATABRICKS_CATALOG",
              "DATABRICKS_SCHEMA"):
        print(f"  {v:<20} {os.getenv(v) or '(vazio)'}")

    # o token nunca e impresso, so confirmado
    tok = os.getenv("DATABRICKS_TOKEN") or ""
    print(f"  {'DATABRICKS_TOKEN':<20} "
          f"{'definido (' + str(len(tok)) + ' chars)' if tok else '(vazio)'}")

    if not tok:
        print(f"\n  ! preencha {db.RAIZ / '.env'} (modelo em .env.exemplo)")
        sys.exit(1)

    print("\n  conectando...")

    try:
        df = db.consultar("SELECT current_catalog() AS cat, current_user() AS quem")
    except Exception as e:
        print(f"  ! falhou: {type(e).__name__}: {str(e)[:160]}")
        sys.exit(1)

    print(f"  OK  catalogo={df.iloc[0, 0]}  usuario={df.iloc[0, 1]}")

    cat = os.getenv("DATABRICKS_CATALOG", "marketdata")
    sch = os.getenv("DATABRICKS_SCHEMA", "silver")

    print(f"\n  tabelas que os ambientes usam em {cat}.{sch}:")

    usadas = [
        "anbima_classes_fundo", "anbima_fundo", "anbima_prestadores_fundo",
        "anbima_prestadores_classe", "anbima_perfil_classe",
        "anbima_taxas_classe", "anbima_detalhes_taxa_performance_classe",
        "cvm_informe_diario",
    ]

    try:
        achadas = set(db.consultar(
            f"SELECT table_name FROM {cat}.information_schema.tables "
            f"WHERE table_schema = '{sch}'"
        )["table_name"])
    except Exception as e:
        print(f"  ! nao deu para listar: {str(e)[:110]}")
        sys.exit(0)

    for t in usadas:
        print(f"     {'OK ' if t in achadas else '!! '} {t}")

    faltando = [t for t in usadas if t not in achadas]

    if faltando:
        print(f"\n  {len(faltando)} tabela(s) ausente(s) neste schema - "
              f"conferir DATABRICKS_SCHEMA")

    print("-" * 46 + "\n")


if __name__ == "__main__":
    main()
