# -*- coding: utf-8 -*-
"""
atualizar_fii.py - Monitor de Novas Ofertas · FII - Tivio Capital

Segue a mesma estrutura do Update_Monitor_Novos_Fundos, que e o ambiente
de referencia: le a fonte, converte para o contrato do template, injeta
e grava em outputs/.

Fonte (FONTE no .env):
    excel      -> Excel - Guia de Base de Dados/Monitor_FII.xlsx  (default)
    databricks -> sql/ofertas_fii.sql

O default e o Excel de proposito: a tabela de ofertas no Databricks ainda
nao foi confirmada (ver ORIGEM_DOS_DADOS.md). Assim o dashboard e
regeneravel hoje, e a troca para o Databricks e so mudar a variavel.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

from tivio_core import db, template, saida, validacao   # noqa: E402

TEMPLATE = BASE / "templates" / "dashboard_ofertas_fii.html"
OUT_DIR = BASE / "outputs"
OUT_HTML = OUT_DIR / "dashboard_ofertas_fii.html"
SQL_FILE = BASE / "sql" / "ofertas_fii.sql"

EXCEL = (BASE.parent / "Excel - Guia de Base de Dados" / "Monitor_FII.xlsx")

FONTE = (os.getenv("FONTE", "").strip() or "excel").lower()
DATA_INI = os.getenv("DATA_INI", "2026-01-01")

# ordem dos campos que o template espera em OFERTAS_DATA
CAMPOS = [
    "ticker", "data", "fii", "gestora", "cnpj", "valor_mob", "nr_emissao",
    "tipo", "modalidade", "volume", "coord", "status", "processo",
    "rito", "observacao",
]

# coluna do Excel -> campo do dashboard
DE_PARA_EXCEL = {
    "Ticker": "ticker",
    "Data Requerimento": "data",
    "FII (Emissor)": "fii",
    "Gestora": "gestora",
    "CNPJ": "cnpj",
    "Valor Mobiliario": "valor_mob",
    "Nr. Emissao": "nr_emissao",
    "Tipo": "tipo",
    "Modalidade": "modalidade",
    "Volume": "volume",
    "Coordenador Lider": "coord",
    "Status": "status",
    "Processo": "processo",
    "Rito": "rito",
    "Observacao": "observacao",
}


def _texto(v, padrao=""):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return padrao
    try:
        if pd.isna(v):
            return padrao
    except (TypeError, ValueError):
        pass
    return str(v).strip()


def carregar_excel() -> pd.DataFrame:
    """Le a aba Ofertas_FII do Excel de referencia."""
    if not EXCEL.exists():
        sys.exit(f"  ! Excel nao encontrado: {EXCEL}")

    print(f"  fonte: {EXCEL.name}")

    df = pd.read_excel(EXCEL, sheet_name="Ofertas_FII", dtype=object)
    df = df.dropna(how="all")

    # o cabecalho do Excel varia em acento e espaco; casa pelo inicio
    ren = {}
    for col in df.columns:
        chave = _texto(col).lower()
        for orig, destino in DE_PARA_EXCEL.items():
            if chave.startswith(orig.split()[0].lower()[:6]) and \
               destino not in ren.values():
                ren[col] = destino
                break

    df = df.rename(columns=ren)

    print(f"  {len(df)} ofertas | {len(ren)} de {len(DE_PARA_EXCEL)} colunas mapeadas")

    return df


def carregar_databricks() -> pd.DataFrame:
    query = db.ler_sql(SQL_FILE, data_ini=DATA_INI)
    return db.consultar_ou_sair(query, mock=carregar_excel)


def para_ofertas_data(df: pd.DataFrame) -> list:
    """DataFrame -> lista de dicts no contrato de OFERTAS_DATA."""
    linhas = []

    for _, r in df.iterrows():
        item = {}

        for campo in CAMPOS:
            v = r.get(campo)

            if campo == "data":
                dt = pd.to_datetime(v, errors="coerce", dayfirst=True)
                item[campo] = "" if pd.isna(dt) else dt.strftime("%d/%m/%Y")

            elif campo == "volume":
                item[campo] = pd.to_numeric(v, errors="coerce")
                if pd.isna(item[campo]):
                    item[campo] = None
                else:
                    item[campo] = float(item[campo])

            elif campo == "nr_emissao":
                n = pd.to_numeric(v, errors="coerce")
                item[campo] = 1 if pd.isna(n) else int(n)

            elif campo == "ticker":
                item[campo] = _texto(v, "N/A") or "N/A"

            else:
                item[campo] = _texto(v)

        if item["fii"]:
            linhas.append(item)

    return linhas


def main():
    print("\nMonitor de Novas Ofertas · FII - atualizacao")
    print("-" * 48)

    if not TEMPLATE.exists():
        sys.exit(f"  ! template nao encontrado: {TEMPLATE}")

    df = carregar_excel() if FONTE == "excel" else carregar_databricks()

    ofertas = para_ofertas_data(df)

    print(f"\n  {len(ofertas)} ofertas no contrato do dashboard")

    validacao.resumo(
        pd.DataFrame(ofertas), chave="cnpj", data="data", rotulo="base de ofertas"
    )

    html = TEMPLATE.read_text(encoding="utf-8")
    html = template.injetar_array(html, "OFERTAS_DATA", ofertas)
    html = template.atualizar_data(html, datetime.now())

    # O template trazia o total escrito a mao em seis lugares ("218"),
    # que nao acompanhava o dado: o cabecalho dizia 218 enquanto o KPI
    # calculado em JS dizia 239. Cada ancora abaixo e um desses pontos.
    total = len(ofertas)

    ancoras = [
        (r'cdi-mini-lbl">OFERTAS</div><div class="cdi-mini-val">', False),
        (r'Todas as Ofertas · ', False),
        (r'id="dateFilterCount">', False),
        (r'Ofertas mapeadas</span><span class="v"><b>', False),
        (r'ofertas</span>', True),
        (r'</b> de <b>', False),
        (r'kpi-card"><div class="kpi-num">', False),
    ]

    trocas = 0

    for ancora, antes in ancoras:
        html, n = template.atualizar_contador(html, ancora, total, antes=antes)
        trocas += n

    if trocas:
        print(f"  {trocas} contador(es) fixo(s) do template atualizado(s)"
              f" para {total}")

    # o menu nao carrega mais contadores fixos; se o template vier com
    # algum, some aqui tambem
    html, n = template.remover_badges_menu(html)

    if n:
        print(f"  {n} contador(es) removido(s) do menu")

    # Apache ECharts: o modulo compartilhado troca as barras em CSS

    # ja renderizadas por graficos com animacao, tooltip e clique.

    html = template.ativar_charts(html, '.ipofo-bars, .diverging-bars')


    saida.gravar(html, OUT_HTML)

    print(f"\n     OK  {OUT_HTML.name}  ({len(ofertas)} ofertas)")
    print("-" * 48)
    print("\nConcluido.\n")


if __name__ == "__main__":
    main()
