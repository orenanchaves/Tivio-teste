# -*- coding: utf-8 -*-
"""run.py · Central de Análises · Tivio Capital
    python run.py                 -> gera todos
    python run.py fundos_tivio    -> gera só um
"""
import sys
from datetime import datetime
import config, databricks_client as dbx, metrics

CALCULADORAS = {
    "fundos_tivio": metrics.kpis_fundos_tivio,
}


def gerar(nome):
    cfg = config.DASHBOARDS[nome]
    print(f"  -> {nome}: lendo {cfg['sql']} ...")
    query = dbx.carregar_sql(cfg["sql"])
    df = dbx.consultar(query)
    print(f"     {len(df)} linhas recebidas.")
    ph = CALCULADORAS[nome](df)
    ph["ATUALIZADO_EM"] = datetime.now().strftime("%d/%m/%Y as %H:%M")
    ph["FONTE"] = "Mock (demo)" if config.USE_MOCK else "Databricks - portfolioanalytics.gold.vw_aum"
    tpl = (config.TEMPLATES_DIR / cfg["template"]).read_text(encoding="utf-8")
    for k, v in ph.items():
        tpl = tpl.replace("{{" + k + "}}", str(v))
    dest = config.OUTPUTS_DIR / cfg["output"]
    dest.write_text(tpl, encoding="utf-8")
    print(f"     OK gerado: {dest.name}")


def main():
    alvos = sys.argv[1:] or list(config.DASHBOARDS.keys())
    modo = "DEMO (mock)" if config.USE_MOCK else "DATABRICKS (real)"
    print(f"\nCentral de Analises - modo {modo}\n" + "-"*44)
    for nome in alvos:
        if nome in config.DASHBOARDS:
            gerar(nome)
        else:
            print(f"  ! '{nome}' nao esta em config.DASHBOARDS")
    print("-"*44 + "\nConcluido.\n")


if __name__ == "__main__":
    main()
