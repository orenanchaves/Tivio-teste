# -*- coding: utf-8 -*-
"""
atualizar_monitor.py - Monitor de Novos Fundos - Tivio Capital

Origem do universo:
    ORIGEM=cvm     -> cadastro publico da CVM (default)
    ORIGEM=anbima  -> comportamento antigo (Databricks/ANBIMA)

Gera:
    outputs/dashboard_fundos_tivio_geral.html
    outputs/dashboard_fundos_tivio_<ano>.html
    outputs/dashboard_fundos_tivio.html

Variaveis de ambiente (.env):
    DATABRICKS_HOST / DATABRICKS_PATH / DATABRICKS_TOKEN
    DATABRICKS_CATALOG   (default marketdata)
    DATABRICKS_SCHEMA    (default silver)
    DATA_INI             (default 2024-01-01)
    LINK_CVM_BASE
    HTML_ENTRADA / SAIDA_DIR
    HTML_PRINCIPAL       recente (default) | geral
    USE_MOCK             true = dados ficticios
    PEERS                todos | planilha | gestao
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

SQL_ARQUIVO = os.getenv("MONITOR_SQL", "").strip() or "monitor_fundos.sql"

SQL_FILE = BASE / "sql" / SQL_ARQUIVO

ORIGEM = (os.getenv("ORIGEM", "").strip() or "cvm").lower()

CVM_CADASTRO = os.getenv("CVM_CADASTRO", "").strip()

USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"

CATALOG = os.getenv("DATABRICKS_CATALOG", "marketdata")
SCHEMA = os.getenv("DATABRICKS_SCHEMA", "silver")

DATA_INI = os.getenv("DATA_INI", "2024-01-01")

LINK_CVM_BASE = os.getenv(
    "LINK_CVM_BASE",
    "https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/CConsolFdo/"
    "FormBuscaConsolFdo.aspx?TpConsulta=1&CNPJNome=",
)

HTML_PRINCIPAL = os.getenv("HTML_PRINCIPAL", "recente").lower()

_MES_DIAG = int(os.getenv("MES_DIAG", "").strip() or 8)

_NOME_MES = {
    1: "JANEIRO", 2: "FEVEREIRO", 3: "MARCO", 4: "ABRIL",
    5: "MAIO", 6: "JUNHO", 7: "JULHO", 8: "AGOSTO",
    9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO",
}

# ----------------------------------------------------------- peers monitorados
# As 15 gestoras acompanhadas pela planilha historica. Itau, BTG e Bradesco
# respondem pela maior parte do volume: sem elas o total nao bate com o Excel.
PEERS_GESTAO = [
    "Augme", "Capitania", "Ibiuna", "JGP", "Kinea",
    "Patria", "Riza", "SPX", "Verde Asset", "Vinci",
]

PEERS_TODOS = PEERS_GESTAO + [
    "BTG Pactual", "Bradesco Asset", "Itau Unibanco",
    "Itau Asset", "XP Asset",
]

# default = 15 gestoras (igual a planilha). PEERS=gestao volta ao recorte menor.
PEERS_FINAL = (
    PEERS_GESTAO
    if os.getenv("PEERS", "").strip().lower() == "gestao"
    else PEERS_TODOS
)


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
                cnpj = (
                    f"{random.randint(10, 99)}."
                    f"{random.randint(100, 999)}."
                    f"{random.randint(100, 999)}/0001-"
                    f"{random.randint(10, 99)}"
                )
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
                    "data_registro":
                        f"{random.randint(1, 28):02d}/{mes:02d}/{ano}",
                    "data_constituicao":
                        f"{random.randint(1, 28):02d}/{mes:02d}/{ano}",
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
                        ["Crédito Livre", "Grau de Investimento",
                         "Soberano", ""]
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


# ------------------------------------------------------------- diagnosticos
def contagem_por_gestora(df: pd.DataFrame, titulo: str = "CONTAGEM POR GESTORA"):
    """Contagem por gestora: e o numero que se compara com a planilha."""
    print(f"\n===== {titulo} =====")

    if df.empty:
        print("  (vazio)")
        return

    tmp = (
        df.groupby("gestora")
          .size()
          .sort_values(ascending=False)
    )

    for gestora, qtd in tmp.items():
        print(f"  {str(gestora):25} {qtd}")

    print(f"  {'TOTAL':25} {len(df)}")


def detalhe_gestora(df: pd.DataFrame, nome: str = "Kinea"):
    """Lista as classes de uma gestora para conferencia linha a linha."""
    print(f"\n===== {nome.upper()} =====")

    sub = df[df["gestora"].fillna("").str.upper() == nome.upper()]

    if sub.empty:
        print("  (nenhuma classe)")
        return

    colunas = [c for c in ("data_registro", "fund_name", "cnpj", "situacao")
               if c in sub.columns]

    print(sub[colunas].to_string(index=False))


def validar_base(df: pd.DataFrame):
    """Checagens que rodam a cada execucao."""
    print("\n  validacao da base")

    dup = int(df["cnpj"].duplicated().sum())
    sem_cnpj = int((df["cnpj"].fillna("") == "").sum())
    sem_gest = int(df["gestora"].fillna("").eq("").sum())

    print(f"     duplicidades de CNPJ ... {dup}"
          f"{'  <- conferir na origem' if dup else ''}")
    print(f"     sem CNPJ ............... {sem_cnpj}")
    print(f"     sem gestora ............ {sem_gest}")

    if "situacao" in df:
        pre = int(
            df["situacao"].fillna("").str.contains("Pré-Oper|Pre-Oper").sum()
        )
        print(f"     pre-operacionais ....... {pre}"
              f"{'  <- ausentes: o LEFT JOIN virou INNER?' if not pre else ''}")

    for coluna, rotulo in (("categoria_anbima", "classificacao"),
                           ("taxa_adm", "taxa adm")):
        if coluna in df:
            ok = int((df[coluna].notna()
                      & (df[coluna].astype(str).str.strip() != "")).sum())
            print(f"     com {rotulo:<15} {ok}/{len(df)}")

    anos = pd.to_datetime(
        df["data_registro"], format="%d/%m/%Y", errors="coerce"
    ).dt.year.value_counts().sort_index()

    print("     por ano ................ "
          + " · ".join(f"{int(a)}: {int(n)}" for a, n in anos.items()))


def diagnosticar_fonte(df: pd.DataFrame):
    """Avisa quando a fonte esta defasada e o ultimo mes ficou truncado."""
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

    # contador fixo do menu: nao acompanha o dado e obrigava a reescrever
    # o numero em todos os dashboards a mao
    import sys as _s
    _s.path.insert(0, str(BASE.parent))
    from tivio_core import template as _tvtpl
    html, _ = _tvtpl.remover_badges_menu(html)

    saida.write_text(html, encoding="utf-8")
    return saida


# --------------------------------------------------------------------- main
def main():
    print("\nMonitor de Novos Fundos - atualizacao")
    print("-" * 46)
    print(f"  modo: {'DEMO (mock)' if USE_MOCK else 'DATABRICKS (real)'}")
    print(f"  origem: {ORIGEM}")
    print(f"  peers: {len(PEERS_FINAL)} gestoras")

    entrada = BASE / HTML_ENTRADA

    if not entrada.exists():
        print(f"  ! HTML nao encontrado: {entrada}")
        sys.exit(1)

    template = entrada.read_text(encoding="utf-8")

    def _query():
        bruto = SQL_FILE.read_text(encoding="utf-8")

        if "{{CVM_INI}}" in bruto:
            import sql_cvm
            bruto = sql_cvm.montar(bruto, CVM_CADASTRO or None)

        return bruto.format(
            catalog=CATALOG,
            schema=SCHEMA,
            link_base=LINK_CVM_BASE,
            data_ini=DATA_INI,
        )

    # ------------------------------------------------------------ 1. origem
    if ORIGEM == "cvm":
        # A CVM define o universo e a data. A ANBIMA so enriquece, sempre
        # por LEFT JOIN - INNER JOIN eliminaria os pre-operacionais.
        import cvm_source as cvm

        df = cvm.converter_cvm_para_dashboard(
            cvm.carregar_base_cvm(DATA_INI)
        )

        print(f"\nCVM: {len(df)} classes")

        if not USE_MOCK:
            try:
                df = cvm.enriquecer_com_anbima(df, consultar(_query()))
            except Exception as e:
                print(f"  ! enriquecimento ANBIMA falhou ({type(e).__name__}:"
                      f" {str(e)[:90]}); segue so com a CVM")
    else:
        print(f"  sql: {SQL_ARQUIVO}"
              f"{' + cadastro CVM' if CVM_CADASTRO else ''}")
        df = consultar(_query())

    print(f"Antes filtro: {len(df)}")

    contagem_por_gestora(df, "ANTES DO FILTRO")

    # ------------------------------------------------- 2. filtro de peers
    # Um unico ponto de filtro. Duas rotas porque na CVM a gestora ja vem
    # padronizada (correspondencia exata evita 'XP Asset' casar com 'SPX'),
    # enquanto na ANBIMA o nome vem juridico e precisa de substring.
    alvo = {p.strip().upper() for p in PEERS_FINAL}

    gestora_norm = df["gestora"].fillna("").astype(str).str.strip().str.upper()

    if ORIGEM == "cvm":
        df = df[gestora_norm.isin(alvo)].copy()
    else:
        df = df[
            gestora_norm.apply(lambda x: any(p in x for p in alvo))
        ].copy()

    print(f"Depois filtro: {len(df)}")

    # ------------------------------------------------- 3. diagnosticos
    contagem_por_gestora(df, "DEPOIS DO FILTRO")
    detalhe_gestora(df, "Kinea")

    if df.empty:
        print("  ! nenhuma gestora peer encontrada.")
        sys.exit(1)

    validar_base(df)
    diagnosticar_fonte(df)

    # ------------------------------------------- 4. diagnostico do mes
    try:
        _ano_diag = int(os.getenv("ANO_DIAG", "").strip() or 0)

        if not _ano_diag:
            _anos_validos = [
                a for a in df.apply(mm.ano_de, axis=1).unique() if a > 0
            ]
            _ano_diag = max(_anos_validos) if _anos_validos else 0

        mes_sel = df[
            (df["mes_ref"] == _MES_DIAG)
            & (df.apply(mm.ano_de, axis=1) == _ano_diag)
        ]

        print(f"\n=== {_NOME_MES.get(_MES_DIAG, _MES_DIAG)}/{_ano_diag} ===")
        print("Linhas:", len(mes_sel))

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

            if _outros and len(mes_sel) < 0.5 * (sum(_outros) / len(_outros)):
                print("  ! bem abaixo da media dos anos anteriores:"
                      " provavel mes incompleto na fonte")

        if not mes_sel.empty:
            print("\nPor tipo:")
            print(mes_sel["tipo"].value_counts())

            print("\nPor gestora:")
            print(mes_sel["gestora"].value_counts().head(20))

            _saida_diag = BASE / f"peers_{_ano_diag}_{_MES_DIAG:02d}.xlsx"
            mes_sel.to_excel(_saida_diag, index=False)

            print(f"Arquivo {_saida_diag.name} gerado")

    except Exception as e:
        print("Erro no diagnostico mensal:", e)

    # ------------------------------------------------- 5. geracao do HTML
    df["_ano"] = df.apply(mm.ano_de, axis=1)

    anos = sorted(
        [a for a in df["_ano"].unique() if a > 0],
        reverse=True
    )

    print(f"  {len(df)} classes · anos: {anos}")

    com_gestora = int((df["gestora"].fillna("").str.strip() != "").sum())
    com_publico = int((df["publico_alvo"].fillna("").str.strip() != "").sum())
    com_adm = int(pd.to_numeric(df["taxa_adm"], errors="coerce").notna().sum())
    com_perf = int(
        pd.to_numeric(df["taxa_perf"], errors="coerce").notna().sum()
    )
    com_link = int((df["link_cvm"].fillna("").str.strip() != "").sum())

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

    print(f"  cobertura · gestora {com_gestora}/{len(df)}"
          f" · publico-alvo {com_publico}/{len(df)}")
    print(f"             taxa adm {com_adm}/{len(df)}"
          f" · taxa perf {com_perf}/{len(df)}"
          f" · link CVM {com_link}/{len(df)}")

    destino = BASE / SAIDA_DIR
    destino.mkdir(parents=True, exist_ok=True)

    hoje = datetime.now()

    estreias_js = mm.gerar_estreias_js(df)

    arq_geral = gerar(
        template, "geral", df, mm.totais_ano(df), anos, hoje,
        destino / "dashboard_fundos_tivio_geral.html",
        estreias_js,
    )
    print(f"     OK  {arq_geral.name}  ({len(df)} classes · {len(anos)} anos)")

    for ano in anos:
        sub = df[df["_ano"] == ano]

        arq = gerar(
            template, ano, sub, mm.totais_mes(sub), anos, hoje,
            destino / f"dashboard_fundos_tivio_{ano}.html",
            estreias_js,
        )
        print(f"     OK  {arq.name}  ({len(sub)} classes)")

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
