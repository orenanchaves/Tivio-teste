# -*- coding: utf-8 -*-
"""config.py · Central de Análises · Tivio Capital"""
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()  # carrega o .env automaticamente, se existir
except Exception:
    pass

DATABRICKS = {
    "server_hostname": os.getenv("DATABRICKS_HOST", "adb-2905561991608053.13.azuredatabricks.net"),
    "http_path":       os.getenv("DATABRICKS_PATH", "/sql/1.0/warehouses/9636f7bb0ab55ff6"),
    "access_token":    os.getenv("DATABRICKS_TOKEN", "COLE_NO_.env"),
}

BASE_DIR      = Path(__file__).resolve().parent
SQL_DIR       = BASE_DIR / "sql"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUTS_DIR   = BASE_DIR / "outputs"

DASHBOARDS = {
    "fundos_tivio": {
        "sql":      "fundos_tivio.sql",
        "template": "dashboard_fundos_tivio_aum.html",
        "output":   "dashboard_fundos_tivio_aum.html",
    },
    # Fase 1.2 (mesma vw_aum, só muda o metrics/template):
    # "ranking_gestoras": {...}
}

# True = dados fictícios (não conecta) · False = Databricks real
USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"
