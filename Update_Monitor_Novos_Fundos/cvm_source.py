# -*- coding: utf-8 -*-
"""
cvm_source.py - CVM como origem do universo, ANBIMA como enriquecimento.

Por que existe
--------------
O monitor comecava por anbima_classes_fundo.data_inicio_atividade_classe,
que marca quando a CLASSE COMECA A OPERAR. A planilha historica marca o
REGISTRO NA CVM - evento diferente, cerca de 29 dias antes (mediana), e
que inclui os fundos em Fase Pre-Operacional. Ver DIAGNOSTICO_AGOSTO.md.

A base cadastral da CVM e publica:

    https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip

Fluxo:

    registro_fundo.csv + registro_classe.csv
        -> merge por ID_Registro_Fundo
        -> filtro por Data_Registro
        -> filtro de peers pelo gestor
        -> LEFT JOIN ANBIMA (enriquecimento)
        -> dashboard

O join com a ANBIMA e sempre a esquerda. INNER JOIN ou UNION ALL
removeriam justamente os pre-operacionais, que sao o motivo da mudanca.
"""
import os
import re
import time
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import pandas as pd

BASE = Path(__file__).resolve().parent

URL_ZIP_CVM = os.getenv(
    "URL_ZIP_CVM",
    "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip",
)

# zip local (arquivo ja baixado ou fixture de teste); vazio = baixa da CVM
CVM_ZIP_LOCAL = os.getenv("CVM_ZIP_LOCAL", "").strip()

CACHE_DIR = BASE / "data"
CACHE_ZIP = CACHE_DIR / "registro_fundo_classe.zip"

# horas antes de rebaixar o cadastro; 0 = sempre baixar
CVM_CACHE_HORAS = float(os.getenv("CVM_CACHE_HORAS", "12") or 12)

# Universo capturado na CVM. Deliberadamente mais largo que o recorte
# final: e barato trazer a mais aqui e estreitar depois em PEERS_FINAL.
GESTORAS_CVM = [
    "BTG PACTUAL", "BRADESCO ASSET", "BRAM - BRADESCO", "BRAM",
    "BANCO BRADESCO", "ITAU UNIBANCO", "ITAUBANK", "KINEA",
    "VERDE ASSET", "SPX", "JGP", "AUGME", "IBIUNA", "CAPITANIA",
    "PATRIA", "VINCI", "RIZA", "XP ALLOCATION", "XP VISTA",
]

# razao social -> nome curto usado no dashboard
GESTOR_MAP = {
    "BTG PACTUAL": "BTG Pactual",
    "BRADESCO ASSET": "Bradesco Asset",
    "BRAM - BRADESCO ASSET": "Bradesco Asset",
    "BRAM - BRADESCO": "Bradesco Asset",
    "BRAM": "Bradesco Asset",
    "BANCO BRADESCO": "Bradesco Asset",
    "ITAU UNIBANCO": "Itau Unibanco",
    "ITAUBANK": "Itau Asset",
    "KINEA": "Kinea",
    "VERDE ASSET": "Verde Asset",
    "SPX": "SPX",
    "JGP": "JGP",
    "AUGME": "Augme",
    "IBIUNA": "Ibiuna",
    "CAPITANIA": "Capitania",
    "PATRIA": "Patria",
    "VINCI": "Vinci",
    "RIZA": "Riza",
    "XP ALLOCATION": "XP Asset",
    "XP VISTA": "XP Asset",
}


def nome_gestor_curto(nome):
    """Razao social da CVM -> rotulo curto. Primeira chave que casar."""
    nome_up = str(nome or "").upper()

    for chave, label in GESTOR_MAP.items():
        if chave in nome_up:
            return label

    return str(nome or "").strip()


def normalizar_cnpj(valor):
    """So digitos, 14 posicoes. E a chave do merge com a ANBIMA."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""

    if pd.isna(valor):
        return ""

    digitos = re.sub(r"[^0-9]", "", str(valor))
    return digitos.zfill(14) if digitos else ""


# ------------------------------------------------------------- download
def _bytes_do_cadastro() -> bytes:
    """Le o zip do cache, de um caminho local ou baixa da CVM."""
    if CVM_ZIP_LOCAL:
        p = Path(CVM_ZIP_LOCAL)
        if not p.exists():
            raise FileNotFoundError(f"CVM_ZIP_LOCAL nao encontrado: {p}")
        print(f"  cadastro CVM: arquivo local {p.name}")
        return p.read_bytes()

    if CACHE_ZIP.exists() and CVM_CACHE_HORAS > 0:
        idade_h = (time.time() - CACHE_ZIP.stat().st_mtime) / 3600
        if idade_h < CVM_CACHE_HORAS:
            print(f"  cadastro CVM: cache de {idade_h:.1f}h")
            return CACHE_ZIP.read_bytes()

    print(f"  cadastro CVM: baixando de {URL_ZIP_CVM}")
    conteudo = urlopen(URL_ZIP_CVM, timeout=180).read()

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_ZIP.write_bytes(conteudo)
    except OSError as e:
        print(f"  ! nao deu para gravar o cache ({e}); segue sem cache")

    return conteudo


def carregar_base_cvm(data_ini: str) -> pd.DataFrame:
    """Cadastro da CVM: classes + fundo pai, so peers, a partir de data_ini."""
    print("\nBase cadastral da CVM")

    with ZipFile(BytesIO(_bytes_do_cadastro())) as zf:
        nomes = zf.namelist()

        for obrigatorio in ("registro_fundo.csv", "registro_classe.csv"):
            if obrigatorio not in nomes:
                raise RuntimeError(
                    f"{obrigatorio} ausente no zip da CVM. Conteudo: {nomes}"
                )

        ler = lambda n: pd.read_csv(
            zf.open(n), sep=";", encoding="latin1",
            dtype=str, low_memory=False,
        )

        df_fundo = ler("registro_fundo.csv")
        df_classe = ler("registro_classe.csv")

    print(f"  {len(df_fundo)} fundos | {len(df_classe)} classes")

    if "Gestor" not in df_fundo.columns:
        raise RuntimeError(
            f"coluna Gestor ausente em registro_fundo.csv. "
            f"Colunas: {list(df_fundo.columns)[:15]}"
        )

    # ------------------------------------------------ peers pelo gestor
    padrao = "|".join(re.escape(g) for g in GESTORAS_CVM)

    peer = (
        df_fundo["Gestor"].fillna("").str.upper()
        .str.contains(padrao, regex=True, na=False)
    )

    df_fundo = df_fundo[peer].copy()
    df_fundo["Gestor_Curto"] = df_fundo["Gestor"].apply(nome_gestor_curto)

    print(f"  {len(df_fundo)} fundos de gestoras peer")

    # ------------------------------------------------ merge classe+fundo
    df_fundo_merge = df_fundo.rename(columns={
        "Codigo_CVM": "Codigo_CVM_Fundo",
        "Data_Registro": "Data_Registro_Fundo",
        "Data_Constituicao": "Data_Constituicao_Fundo",
        "Denominacao_Social": "Denominacao_Social_Fundo",
        "Situacao": "Situacao_Fundo",
    })

    # o que ainda colidir ganha sufixo, para o merge nao criar _x/_y
    conflitos = (
        set(df_classe.columns) & set(df_fundo_merge.columns)
    ) - {"ID_Registro_Fundo"}

    if conflitos:
        df_fundo_merge = df_fundo_merge.rename(
            columns={c: f"{c}_FundoPai" for c in conflitos}
        )

    if "ID_Registro_Fundo" not in df_classe.columns:
        raise RuntimeError("ID_Registro_Fundo ausente em registro_classe.csv")

    df = df_classe.merge(df_fundo_merge, on="ID_Registro_Fundo", how="inner")

    print(f"  {len(df)} classes de gestoras peer")

    # ------------------------------------------------ recorte temporal
    df["Data_Registro"] = pd.to_datetime(
        df["Data_Registro"], errors="coerce", dayfirst=False
    )
    df["Data_Constituicao"] = pd.to_datetime(
        df.get("Data_Constituicao"), errors="coerce", dayfirst=False
    )

    antes = len(df)
    df = df[df["Data_Registro"] >= pd.to_datetime(data_ini)].copy()

    print(f"  {len(df)} desde {data_ini} (de {antes})")

    df = df.sort_values("Data_Registro", ascending=False)
    df["Mes_Registro_Num"] = df["Data_Registro"].dt.month
    df["Ano_Registro_Num"] = df["Data_Registro"].dt.year

    return df


# ----------------------------------------------- CVM -> contrato do HTML
def _bitmask(df: pd.DataFrame, nome: pd.Series, tipo: pd.Series,
             classif: pd.Series) -> pd.Series:
    """As 6 flags de segmento que o dashboard le em f[14].

    O conversor do plano nao gerava esta coluna nem campo_11. Sem elas o
    painel Segmentos e o de Credito Privado zeram sem erro visivel, e o
    ano teria de ser reparseado da data. Deriva-se aqui o mesmo conjunto
    do SQL: credito privado, FIDC, infraestrutura, previdencia,
    exterior e ESG.
    """
    def col(nome_col):
        if nome_col in df.columns:
            return df[nome_col].fillna("").str.upper()
        return pd.Series([""] * len(df), index=df.index)

    esg_flag = col("Classe_ESG")

    flags = [
        nome.str.contains("CRÉDITO PRIVADO|CREDITO PRIVADO", na=False)
        | classif.str.contains("CRÉDITO PRIVADO|CREDITO PRIVADO", na=False),

        tipo.str.contains("FIDC", na=False)
        | nome.str.contains("DIREITOS CREDITÓRIOS|DIREITOS CREDITORIOS", na=False),

        nome.str.contains("INFRA|INCENTIVAD|DEBÊNTURES|DEBENTURES", na=False),

        nome.str.contains("PREV|PGBL|VGBL|FLEXPREV", na=False)
        | classif.str.contains("PREVID", na=False),

        nome.str.contains("GLOBAL|INTERNACIONAL|EXTERIOR", na=False)
        | classif.str.contains("EXTERIOR", na=False),

        esg_flag.isin(["S", "SIM", "TRUE", "1"])
        | nome.str.contains("ESG|SUSTENT", na=False),
    ]

    bits = pd.DataFrame(
        {i: f.fillna(False).map(lambda v: "1" if v else "0")
         for i, f in enumerate(flags)}
    )

    return bits.apply("".join, axis=1)


def converter_cvm_para_dashboard(df_cvm: pd.DataFrame) -> pd.DataFrame:
    """DataFrame da CVM -> as 25 colunas de monitor_metrics.COLS."""
    def coluna(nome, padrao=""):
        if nome in df_cvm.columns:
            return df_cvm[nome]
        return pd.Series([padrao] * len(df_cvm), index=df_cvm.index)

    cnpj_classe = coluna("CNPJ_Classe")
    cnpj_fundo = coluna("CNPJ_Fundo")

    cnpj_final = cnpj_classe.where(
        cnpj_classe.fillna("").astype(str).str.strip() != "", cnpj_fundo
    )

    nome_up = coluna("Denominacao_Social").fillna("").astype(str).str.upper()
    tipo_up = coluna("Tipo_Fundo").fillna("").astype(str).str.upper()
    classif_up = (
        coluna("Classificacao_Anbima").fillna("").astype(str).str.upper()
    )

    dt_reg = pd.to_datetime(coluna("Data_Registro"), errors="coerce")

    df = pd.DataFrame({
        "fund_name": coluna("Denominacao_Social"),
        "gestora": coluna("Gestor_Curto"),
        "tipo": coluna("Tipo_Fundo"),
        "segmento_detalhe": "",
        "categoria_anbima": coluna("Classificacao_Anbima"),
        "situacao": coluna("Situacao"),
        "data_registro": dt_reg.dt.strftime("%d/%m/%Y"),
        "data_constituicao": pd.to_datetime(
            coluna("Data_Constituicao"), errors="coerce"
        ).dt.strftime("%d/%m/%Y"),
        "cnpj": cnpj_final.apply(normalizar_cnpj),
        "publico_alvo": coluna("Publico_Alvo"),
        "exclusivo": coluna("Exclusivo"),
        # campo_11 e lido por mm.ano_de e pelo seletor de ano do HTML
        "campo_11": dt_reg.dt.year.astype("Int64").astype(str)
                    .replace("<NA>", ""),
        "condominio": coluna("Forma_Condominio"),
        "subclasse": coluna("Denominacao_Social"),
        "segmentos_bitmask": _bitmask(df_cvm, nome_up, tipo_up, classif_up),
        "link_cvm": coluna("Link_Regulamento"),
        "mes_ref": pd.to_numeric(coluna("Mes_Registro_Num"), errors="coerce"),
        "gestor_juridico": coluna("Gestor"),
        "administrador": coluna("Administrador"),
        "categoria_n1": coluna("Classificacao_Anbima"),
        "risco_credito": "",
        "duracao": "",
        "registro": "Sim",
        "taxa_adm": coluna("taxa_adm", None),
        "taxa_perf": coluna("taxa_performance", None),
    })

    return df.reset_index(drop=True)


# -------------------------------------------- ANBIMA como enriquecimento
CAMPOS_ANBIMA = [
    "categoria_anbima", "publico_alvo", "taxa_adm", "taxa_perf",
    "segmento_detalhe", "risco_credito", "duracao", "categoria_n1",
]


def enriquecer_com_anbima(df_cvm: pd.DataFrame,
                          df_anbima: pd.DataFrame) -> pd.DataFrame:
    """LEFT JOIN por CNPJ. A CVM manda nos campos cadastrais.

    Sempre a esquerda: INNER JOIN eliminaria os pre-operacionais, que sao
    exatamente o que a mudanca de origem veio resgatar.
    """
    if df_anbima is None or df_anbima.empty:
        print("  ANBIMA indisponivel: segue so com a CVM")
        return df_cvm

    ana = df_anbima.copy()
    ana["cnpj"] = ana["cnpj"].apply(normalizar_cnpj)
    ana = ana[ana["cnpj"] != ""]
    ana = ana.drop_duplicates(subset=["cnpj"], keep="last")

    # so os campos que a ANBIMA acrescenta, para nao arrastar o cadastro
    manter = ["cnpj"] + [c for c in CAMPOS_ANBIMA if c in ana.columns]
    ana = ana[manter]

    antes = len(df_cvm)

    df = df_cvm.merge(ana, how="left", on="cnpj",
                      suffixes=("_cvm", "_anbima"))

    if len(df) != antes:
        print(f"  ! merge mudou a contagem: {antes} -> {len(df)}")

    casados = 0

    for campo in CAMPOS_ANBIMA:
        a, c = f"{campo}_anbima", f"{campo}_cvm"

        if a in df.columns and c in df.columns:
            lado_a = df[a].replace("", pd.NA)
            df[campo] = lado_a.combine_first(df[c])
            df = df.drop(columns=[a, c])
            casados = max(casados, int(lado_a.notna().sum()))
        elif a in df.columns:
            df[campo] = df[a]
            df = df.drop(columns=[a])

    print(f"  ANBIMA enriqueceu {casados} de {len(df)} classes")

    return df
