from pathlib import Path
import pandas as pd
import re

BASE_DIR = Path(__file__).resolve().parent

ARQUIVO_ENTRADA = BASE_DIR / "Peers_FundosAbertos.xlsx"
ARQUIVO_SAIDA = BASE_DIR / "peers_fundos_abertos.csv"


def normalizar_cnpj(valor):

    if pd.isna(valor):
        return None

    digitos = re.sub(r"\D", "", str(valor))

    if not digitos:
        return None

    return digitos.zfill(14)


def normalizar_plataforma(valor):

    if pd.isna(valor):
        return None

    mapa = {
        "xp": "XP",
        "btg": "BTG",
        "itaú": "Itau",
        "itau": "Itau",
        "bradesco": "Bradesco"
    }

    return mapa.get(
        str(valor).strip().lower()
    )


df = pd.read_excel(
    ARQUIVO_ENTRADA,
    sheet_name="Resumo",
    skiprows=2,
    engine="openpyxl",
    dtype=str
)

df.columns = [
    str(c).strip().upper()
    for c in df.columns
]

df = df.rename(
    columns={
        "NOME_FUNDO": "nome_fundo",
        "CNPJ": "cnpj",
        "CLASSE_ANBIMA": "classe_anbima",
        "PLATAFORMA": "plataforma",
        "FONTE": "fonte",
        "ATUALIZADO": "atualizado"
    }
)

df["cnpj"] = df["cnpj"].apply(
    normalizar_cnpj
)

df["plataforma"] = df["plataforma"].apply(
    normalizar_plataforma
)

df = df[
    [
        "cnpj",
        "plataforma",
        "nome_fundo",
        "classe_anbima",
        "fonte",
        "atualizado"
    ]
]

df = df.dropna(
    subset=["cnpj", "plataforma"]
)

df = df.drop_duplicates(
    subset=["cnpj", "plataforma"]
)

df.to_csv(
    ARQUIVO_SAIDA,
    index=False,
    encoding="utf-8-sig"
)

print("\nArquivo criado:")
print(ARQUIVO_SAIDA)

print("\nQuantidade por plataforma:")
print(
    df.groupby("plataforma")
      .size()
      .sort_values(ascending=False)
)

print("\nPrimeiras linhas:")
print(df.head())