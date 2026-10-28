# -*- coding: utf-8 -*-
"""Conexao com o Databricks, igual para todos os ambientes."""
import os
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent


def carregar_env():
    """Procura o .env na pasta do ambiente e depois na raiz.

    Antes cada pasta Update_* precisava do seu proprio .env com a chave
    do Databricks repetida. Alem do trabalho de copiar, rotacionar a
    chave exigia lembrar de todos os lugares - e dois ambientes novos
    ficaram sem nenhum.

    Agora um unico .env na raiz atende todos. Um .env na pasta do
    ambiente ainda vence, para o caso de um deles precisar de outro
    workspace: o primeiro a definir a variavel ganha, porque
    load_dotenv() nao sobrescreve o que ja existe.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        # falhar em silencio aqui produz o pior erro possivel: o script
        # diz "faltando no .env" com o .env na frente da pessoa
        achou = [c for c in (Path.cwd() / ".env", RAIZ / ".env") if c.exists()]

        if achou:
            print("  ! python-dotenv nao instalado: o .env encontrado em "
                  f"{achou[0]} sera IGNORADO")
            print("    pip install python-dotenv")

        return

    for caminho in (Path.cwd() / ".env", RAIZ / ".env"):
        if caminho.exists():
            load_dotenv(caminho)


carregar_env()


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
            f"faltando no .env: {', '.join(faltando)}\n"
            f"     ponha em {RAIZ / '.env'} (serve todos os ambientes)\n"
            f"     ou rode com USE_MOCK=true para nao conectar"
        )

    try:
        from databricks import sql
    except ImportError:
        raise RuntimeError(
            "databricks-sql-connector nao instalado.\n"
            "     pip install -r requirements.txt\n"
            "     (ou rode com USE_MOCK=true para nao conectar)"
        ) from None

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


def consultar_ou_sair(query: str, mock=None):
    """consultar() que termina com mensagem limpa em vez de traceback.

    Falta de credencial ou de dependencia sao erros de configuracao, nao
    defeito: quem roda precisa ler o que fazer, nao a pilha de chamadas.
    """
    import sys

    try:
        return consultar(query, mock=mock)
    except RuntimeError as e:
        sys.exit(f"\n  ! {e}\n")
