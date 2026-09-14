# Fase 1 · Fundos Tivio · Patrimônio (AUM)

Gera `outputs/dashboard_fundos_tivio_aum.html` a partir da view
`portfolioanalytics.gold.vw_aum` (a que você já tem acesso).

## Rodar em demo (não conecta)
    pip install -r requirements.txt
    python run.py

## Conectar no Databricks
1. Renomeie `.env.exemplo` para `.env` e cole seu token.
2. `python run.py`

O `USE_MOCK=false` no `.env` liga o Databricks real.

## Arquivos
- sql/fundos_tivio.sql ......... query da vw_aum
- metrics.py .................. KPIs (PL total, top fundos, distribuidores, verticais)
- templates/dashboard_fundos_tivio_aum.html ... layout Tivio + placeholders
- run.py ...................... orquestrador

## KPIs calculados
PL total · nº de fundos · maior fundo · concentração top 3 distribuidores ·
PL por vertical · Top 20 fundos · Top 20 distribuidores.

## Fase 1.2 (Ranking Gestoras) — mesma vw_aum
Basta um novo metrics.kpis_ranking + template, agrupando por distributor_name.
