# -*- coding: utf-8 -*-
"""
atualizar_monitor.py - Monitor de Novos Fundos - Tivio Capital

Le o SQL de sql/monitor_fundos.sql, consulta o Databricks e gera:

    outputs/dashboard_fundos_tivio_geral.html   (todos os anos somados)
    outputs/dashboard_fundos_tivio_<ano>.html   (um por ano com dado)
    outputs/dashboard_fundos_tivio.html         (copia do dashboard principal)

O seletor "Ano" no topo do dashboard navega entre esses arquivos
(Geral / 2026 / 2025 / 2024).

Variaveis de ambiente (.env):
    DATABRICKS_HOST / DATABRICKS_PATH / DATABRICKS_TOKEN
    DATABRICKS_CATALOG   (default marketdata)
    DATABRICKS_SCHEMA    (default silver)
    DATA_INI             (default 2024-01-01)
    LINK_CVM_BASE        (base da consulta publica da CVM)
    HTML_ENTRADA / SAIDA_DIR
    HTML_PRINCIPAL       recente (default) | geral
    USE_MOCK             true = dados ficticios, nao conecta
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import pandas as pd

import monitor_metrics as mm
import patch_meses as pm

BASE = Path(__file__).resolve().parent

_in_templates = BASE / "templates" / "dashboard_fundos_tivio.html"

_default_in = (
    "templates/dashboard_fundos_tivio.html"
    if _in_templates.exists()
    else "dashboard_fundos_tivio.html"
)

HTML_ENTRADA = os.getenv("HTML_ENTRADA", _default_in)

SAIDA_DIR = Path(os.getenv("SAIDA_DIR", "outputs"))

# monitor_fundos.sql (v1, default) | monitor_fundos_v2.sql (campos da planilha)
SQL_ARQUIVO = os.getenv("MONITOR_SQL", "").strip() or "monitor_fundos.sql"

SQL_FILE = BASE / "sql" / SQL_ARQUIVO

# catalogo.schema.tabela do cadastro da CVM; vazio = roda sem ele.
# Descobrir o nome com: python buscar_cadastro_cvm.py
CVM_CADASTRO = os.getenv("CVM_CADASTRO", "").strip()

USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"

CATALOG = os.getenv("DATABRICKS_CATALOG", "marketdata")
SCHEMA = os.getenv("DATABRICKS_SCHEMA", "silver")

DATA_INI = os.getenv("DATA_INI", "2024-01-01")

# Consulta publica de fundos da CVM: a base recebe o CNPJ so com digitos.
LINK_CVM_BASE = os.getenv(
    "LINK_CVM_BASE",
    "https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/CConsolFdo/"
    "FormBuscaConsolFdo.aspx?TpConsulta=1&CNPJNome=",
)

# qual arquivo vira o dashboard_fundos_tivio.html: "recente" ou "geral"
HTML_PRINCIPAL = os.getenv("HTML_PRINCIPAL", "recente").lower()

# mes/ano do bloco de diagnostico (ANO_DIAG vazio = ano mais recente da base)
_MES_DIAG = int(os.getenv("MES_DIAG", "").strip() or 8)

_NOME_MES = {
    1: "JANEIRO", 2: "FEVEREIRO", 3: "MARCO", 4: "ABRIL",
    5: "MAIO", 6: "JUNHO", 7: "JULHO", 8: "AGOSTO",
    9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO",
}


# ----------------------------------------------------------------- consulta
def consultar(query: str) -> pd.DataFrame:
    if USE_MOCK:
        return _mock()

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


def _mock() -> pd.DataFrame:
    """Dados ficticios com o mesmo formato do SELECT (USE_MOCK=true)."""
    import random

    random.seed(7)

    gestoras = [
        "ITAU ASSET", "BTG PACTUAL", "BRADESCO ASSET", "XP ASSET",
        "KINEA", "VINCI", "SPX", "IBIUNA", "RIZA", "CAPITANIA",
        "VERDE ASSET", "JGP", "AUGME", "PATRIA", "OPPORTUNITY GESTORA",
    ]
    tipos = ["FI", "FIDC", "FII", "FIP", "FIAGRO"]
    anbima = ["Renda Fixa Duracao Livre", "Multimercados Livre",
              "Acoes Livre", "Previdencia Multimercado Livre"]
    n1 = ["Renda Fixa", "Multimercados", "Ações", "Previdência"]
    publico = ["Publico Geral", "Qualificado", "Profissional"]

    linhas = []
    for ano in (2024, 2025, 2026):
        meses = range(1, 13) if ano < 2026 else range(1, 9)
        for mes in meses:
            for i in range(random.randint(20, 40)):
                cnpj = f"{random.randint(10, 99)}.{random.randint(100, 999)}." \
                       f"{random.randint(100, 999)}/0001-{random.randint(10, 99)}"
                dig = re.sub(r"[^0-9]", "", cnpj)
                cat = random.choice(anbima)
                pub = random.choice(publico)
                exc = "S" if random.random() < 0.25 else "N"
                gest = random.choice(gestoras)
                linhas.append({
                    "fund_name": f"FUNDO {gest} {ano}-{mes:02d}-{i:02d}",
                    "gestora": gest,
                    "tipo": random.choice(tipos),
                    "segmento_detalhe": " | ".join(
                        [cat, pub] + (["Exclusivo"] if exc == "S" else [])
                    ),
                    "categoria_anbima": cat,
                    "situacao": "Fase Pre-Operacional",
                    "data_registro": f"{random.randint(1, 28):02d}/{mes:02d}/{ano}",
                    "data_constituicao": f"{random.randint(1, 28):02d}/{mes:02d}/{ano}",
                    "cnpj": cnpj,
                    "publico_alvo": pub,
                    "exclusivo": exc,
                    "campo_11": str(ano),
                    "condominio": random.choice(["Aberto", "Fechado"]),
                    "subclasse": f"FUNDO {gest} {ano}-{mes:02d}-{i:02d}",
                    "segmentos_bitmask": "".join(
                        random.choice("01") for _ in range(6)
                    ),
                    "link_cvm": LINK_CVM_BASE + dig,
                    "mes_ref": mes,
                    "gestor_juridico": gest + " GESTAO DE RECURSOS LTDA.",
                    "administrador": "BEM DTVM LTDA.",
                    "categoria_n1": random.choice(n1),
                    "risco_credito": random.choice(
                        ["Crédito Livre", "Grau de Investimento", "Soberano", ""]
                    ),
                    "duracao": "",
                    "registro": "Nao",
                    "taxa_adm": round(random.uniform(0.2, 2.5), 2)
                    if random.random() < 0.7 else None,
                    "taxa_perf": round(random.uniform(10, 20), 2)
                    if random.random() < 0.35 else None,
                })

    return pd.DataFrame(linhas)


# -------------------------------------------------------------- injecao HTML
def injetar_funds(html: str, funds_js: str) -> str:
    inicio = html.find("const FUNDS_DATA = [")

    if inicio == -1:
        raise RuntimeError("Bloco FUNDS_DATA nao encontrado no template.")

    fim = html.find("];", inicio)

    if fim == -1:
        raise RuntimeError("Fim do bloco FUNDS_DATA nao encontrado.")

    return html[:inicio] + f"const FUNDS_DATA = {funds_js};" + html[fim + 2:]


def injetar_estreias(html: str, estreias_js: str) -> str:
    """Mapa de estreia por gestora, para o painel de novas gestoras."""
    alvo = "const GESTORA_ESTREIA = "

    inicio = html.find(alvo)

    if inicio == -1:
        return html

    fim = html.find("};", inicio)

    if fim == -1:
        raise RuntimeError("Fim do bloco GESTORA_ESTREIA nao encontrado.")

    return html[:inicio] + alvo + estreias_js + ";" + html[fim + 2:]


def atualizar_badge(html: str) -> str:
    hoje = datetime.now().strftime("%d/%m")

    return re.sub(
        r'(<div class="cdi-mini-lbl">ATUALIZADO</div>\s*'
        r'<div class="cdi-mini-val">)[^<]*(</div>)',
        lambda m: m.group(1) + hoje + m.group(2),
        html,
        count=1,
    )



def diagnosticar_fonte(df: pd.DataFrame):
    """Avisa quando a fonte esta defasada e o ultimo mes ficou truncado.

    A ANBIMA publica o inicio de atividade das classes com semanas de
    atraso. Sem esse aviso o mes corrente aparece no dashboard com uma
    contagem baixa que parece real - foi o que fez agosto/2026 exibir 4
    classes quando os agostos anteriores tiveram 24 e 19.
    """
    dt = pd.to_datetime(df["data_registro"], format="%d/%m/%Y",
                        errors="coerce")

    ultima = dt.max()

    if pd.isna(ultima):
        print("  ! nenhuma data valida em data_registro")
        return None

    hoje = pd.Timestamp.today().normalize()
    atraso = (hoje - ultima).days

    print(f"  fonte ate {ultima:%d/%m/%Y} ({atraso} dias de defasagem)")

    fim_do_mes = ultima + pd.offsets.MonthEnd(0)

    if ultima < fim_do_mes:
        faltam = (fim_do_mes - ultima).days
        print(f"  ! {ultima:%m/%Y} INCOMPLETO na fonte:"
              f" faltam {faltam} dias do mes")
        print("    nao compare esse mes com a planilha historica ainda")

    return ultima


def gerar(template, escopo, sub, totais, anos, hoje, saida: Path,
          estreias_js: str = "{}") -> Path:
    html = injetar_funds(template, mm.gerar_funds_data(sub))
    html = injetar_estreias(html, estreias_js)
    html = pm.aplicar(html, escopo, totais, anos, hoje)
    html = atualizar_badge(html)

    saida.write_text(html, encoding="utf-8")
    return saida


# --------------------------------------------------------------------- main
def main():
    print("\nMonitor de Novos Fundos - atualizacao")
    print("-" * 46)
    print(f"  modo: {'DEMO (mock)' if USE_MOCK else 'DATABRICKS (real)'}")

    entrada = BASE / HTML_ENTRADA

    if not entrada.exists():
        print(f"  ! HTML nao encontrado: {entrada}")
        sys.exit(1)

    template = entrada.read_text(encoding="utf-8")

    bruto = SQL_FILE.read_text(encoding="utf-8")

    # v2 traz o bloco opcional do cadastro da CVM entre marcadores;
    # resolver() escolhe o ramo antes do .format() para nao sobrar chave.
    if "{{CVM_INI}}" in bruto:
        import sql_cvm
        bruto = sql_cvm.montar(bruto, CVM_CADASTRO or None)

    query = bruto.format(
        catalog=CATALOG,
        schema=SCHEMA,
        link_base=LINK_CVM_BASE,
        data_ini=DATA_INI,
    )

    print(f"  sql: {SQL_ARQUIVO}"
          f"{' + cadastro CVM' if CVM_CADASTRO else ''}")

    df = consultar(query)

    print(f"Antes filtro: {len(df)}")

    PEERS = [
        "SPX",
        "IBIUNA",
        "VINCI",
        "RIZA",
        "JGP",
        "KINEA",
        "AUGME",
        "CAPITANIA",
        "VERDE",
        "PATRIA"
    ]

    df = df[
        df["gestora"]
            .fillna("")
            .str.upper()
            .apply(lambda x: any(peer in x for peer in PEERS))
    ].copy()

    print(f"Depois filtro: {len(df)}")

    diagnosticar_fonte(df)

    try:
        # ATENCAO: mes_ref sozinho nao distingue o ano. Sem o recorte de
        # ano abaixo, "agosto" somaria ago/2024 + ago/2025 + ago/2026
        # (47 linhas), numero que nao existe em nenhum mes real e que nao
        # e comparavel com a aba do Excel historico (um unico ano).
        _ano_diag = int(os.getenv("ANO_DIAG", "").strip() or 0)

        if not _ano_diag:
            _anos_validos = [
                a for a in df.apply(mm.ano_de, axis=1).unique() if a > 0
            ]
            _ano_diag = max(_anos_validos) if _anos_validos else 0

        agosto = df[
            (df["mes_ref"] == _MES_DIAG)
            & (df.apply(mm.ano_de, axis=1) == _ano_diag)
        ]

        print(f"\n=== {_NOME_MES.get(_MES_DIAG, _MES_DIAG)}/{_ano_diag} ===")
        print("Linhas:", len(agosto))

        # o mesmo mes nos anos anteriores: mostra se a safra amadureceu
        _hist = (
            df[df["mes_ref"] == _MES_DIAG]
            .assign(_a=lambda x: x.apply(mm.ano_de, axis=1))
            .groupby("_a")
            .size()
        )

        if len(_hist) > 1:
            print("\nMesmo mes em outros anos:")
            for _a, _n in _hist.items():
                _marca = "  <- atual" if _a == _ano_diag else ""
                print(f"  {_NOME_MES.get(_MES_DIAG, '')}/{_a}: {_n}{_marca}")

            _outros = [n for a, n in _hist.items() if a != _ano_diag]

            if _outros and len(agosto) < 0.5 * (sum(_outros) / len(_outros)):
                print("  ! bem abaixo da media dos anos anteriores:"
                      " provavel mes incompleto na fonte")

        print("\nPor tipo:")
        print(agosto["tipo"].value_counts())

        print("\nTop gestoras:")
        print(agosto["gestora"].value_counts().head(20))

        agosto[
            [
                "fund_name",
                "gestora",
                "tipo",
                "exclusivo"
            ]
        ]

        _saida_diag = BASE / f"peers_{_ano_diag}_{_MES_DIAG:02d}.xlsx"
        agosto.to_excel(_saida_diag, index=False)

        print(f"Arquivo {_saida_diag.name} gerado")

    except Exception as e:
        print("Erro no diagnostico mensal:", e)

    if df.empty:
        print("  ! nenhuma gestora peer encontrada.")
        sys.exit(1)

    df["_ano"] = df.apply(mm.ano_de, axis=1)

    anos = sorted(
        [a for a in df["_ano"].unique() if a > 0],
        reverse=True
    )

    print(f"  {len(df)} classes · anos: {anos}")

    com_gestora = int((df["gestora"].fillna("").str.strip() != "").sum())
    com_publico = int((df["publico_alvo"].fillna("").str.strip() != "").sum())
    com_adm = int(pd.to_numeric(df["taxa_adm"], errors="coerce").notna().sum())
    com_perf = int(pd.to_numeric(df["taxa_perf"], errors="coerce").notna().sum())
    com_link = int((df["link_cvm"].fillna("").str.strip() != "").sum())

    # --- cobertura segmentada (patch_cobertura.py) ---
    # Estruturados (FIDC/FIP/FIAGRO) raramente informam taxa no cadastro
    # ANBIMA: a remuneracao fica no regulamento. Medir os dois grupos
    # juntos subestima a qualidade do dado dos fundos tradicionais.
    ESTRUTURADOS = ("FIDC", "FIP", "FIAGRO")

    _cat = df["categoria_n1"].fillna("").str.upper().str.strip()
    _eh_estrut = _cat.isin([s.upper() for s in ESTRUTURADOS])

    _trad = df[~_eh_estrut]
    _estr = df[_eh_estrut]

    def _cob(sub, coluna):
        """(preenchidos, total, percentual) para uma coluna numerica."""
        tot = len(sub)
        if tot == 0:
            return 0, 0, 0.0
        ok = int(pd.to_numeric(sub[coluna], errors="coerce").notna().sum())
        return ok, tot, (ok / tot * 100)

    _ta_t, _tt_t, _tp_t = _cob(_trad, "taxa_adm")
    _pa_t, _pt_t, _pp_t = _cob(_trad, "taxa_perf")
    _ta_e, _tt_e, _tp_e = _cob(_estr, "taxa_adm")
    _pa_e, _pt_e, _pp_e = _cob(_estr, "taxa_perf")

    print("  cobertura de taxas por perfil de veiculo")
    print(
        f"     tradicionais  ({_tt_t:>5} classes) "
        f"adm {_ta_t:>5} ({_tp_t:4.1f}%) | "
        f"perf {_pa_t:>5} ({_pp_t:4.1f}%)"
    )
    print(
        f"     estruturados  ({_tt_e:>5} classes) "
        f"adm {_ta_e:>5} ({_tp_e:4.1f}%) | "
        f"perf {_pa_e:>5} ({_pp_e:4.1f}%)"
    )
    print(
        "     obs: baixa cobertura em FIDC/FIP/FIAGRO e esperada "
        "(taxa no regulamento)"
    )

    # detalhe por categoria, ordenado pelo tamanho da base
    print("  cobertura de taxa adm por categoria")
    for _categoria, _sub in sorted(
        df.groupby(_cat),
        key=lambda kv: len(kv[1]),
        reverse=True,
    ):
        if not _categoria:
            _categoria = "(sem categoria)"
        _ok, _tot, _pct = _cob(_sub, "taxa_adm")
        _flag = " *" if _categoria in [s.upper() for s in ESTRUTURADOS] else ""
        print(f"     {_categoria:<16} {_ok:>5}/{_tot:<5} ({_pct:5.1f}%){_flag}")
    print("     * veiculo estruturado - ausencia esperada")
    # --- fim cobertura segmentada ---

    print(f"  cobertura · gestora {com_gestora}/{len(df)}"
          f" · publico-alvo {com_publico}/{len(df)}")
    print(f"             taxa adm {com_adm}/{len(df)}"
          f" · taxa perf {com_perf}/{len(df)}"
          f" · link CVM {com_link}/{len(df)}")

    destino = BASE / SAIDA_DIR
    destino.mkdir(parents=True, exist_ok=True)

    hoje = datetime.now()

    # estreia de cada gestora na base inteira (usado pelo painel de novas)
    estreias_js = mm.gerar_estreias_js(df)

    # --- Geral: todos os anos, barra de periodo por ano ---
    arq_geral = gerar(
        template, "geral", df, mm.totais_ano(df), anos, hoje,
        destino / "dashboard_fundos_tivio_geral.html",
        estreias_js,
    )
    print(f"     OK  {arq_geral.name}  ({len(df)} classes · {len(anos)} anos)")

    # --- um arquivo por ano ---
    for ano in anos:
        sub = df[df["_ano"] == ano]

        arq = gerar(
            template, ano, sub, mm.totais_mes(sub), anos, hoje,
            destino / f"dashboard_fundos_tivio_{ano}.html",
            estreias_js,
        )
        print(f"     OK  {arq.name}  ({len(sub)} classes)")

    # --- dashboard principal ---
    if HTML_PRINCIPAL == "geral":
        origem, rotulo = arq_geral, "geral"
    else:
        origem, rotulo = (
            destino / f"dashboard_fundos_tivio_{anos[0]}.html",
            str(anos[0]),
        )

    principal = destino / "dashboard_fundos_tivio.html"
    principal.write_text(origem.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"     OK  {principal.name}  (= {rotulo})")

    print("-" * 46)
    print("\nConcluido.\n")


if __name__ == "__main__":
    main()
