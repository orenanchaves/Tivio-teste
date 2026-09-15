# -*- coding: utf-8 -*-
"""Conexao com o Databricks, igual para todos os ambientes."""
import os

import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def usar_mock() -> bool:
    return os.getenv("USE_MOCK", "false").strip().lower() in (
        "1", "true", "yes", "sim"
    )


def consultar(query: str, mock=None) -> pd.DataFrame:
    """Roda a query. Com USE_MOCK=true devolve mock() sem conectar.

    mock e uma funcao sem argumentos que devolve o DataFrame ficticio -
    cada ambiente tem o seu, com o mesmo formato do SELECT real.
    """
    if usar_mock():
        if mock is None:
            raise RuntimeError("USE_MOCK=true mas o ambiente nao tem mock")
        print("  modo DEMO (mock): nao conecta no Databricks")
        return mock()

    faltando = [v for v in ("DATABRICKS_HOST", "DATABRICKS_PATH",
                            "DATABRICKS_TOKEN") if not os.getenv(v)]
    if faltando:
        raise RuntimeError(
            f"defina no .env: {', '.join(faltando)} "
            f"(ou rode com USE_MOCK=true)"
        )

    from databricks import sql

    conn = sql.connect(
        server_hostname=os.getenv("DATABRICKS_HOST"),
        http_path=os.getenv("DATABRICKS_PATH"),
        access_token=os.getenv("DATABRICKS_TOKEN"),
    )

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            cols = [c[0] for c in cur.description]
            rows = cur.fetchall()

        return pd.DataFrame(rows, columns=cols)

    finally:
        conn.close()


def ler_sql(caminho, **placeholders) -> str:
    """Le o .sql e preenche {catalog}, {schema}, {data_ini}..."""
    bruto = caminho.read_text(encoding="utf-8")

    padrao = {
        "catalog": os.getenv("DATABRICKS_CATALOG", "marketdata"),
        "schema": os.getenv("DATABRICKS_SCHEMA", "silver"),
    }
    padrao.update(placeholders)

    return bruto.format(**padrao)
