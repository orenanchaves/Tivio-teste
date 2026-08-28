# Monitor de Novos Fundos · v3 (Geral + público-alvo + taxas + link CVM)

## Novidades desta versão
- **Seletor de ano com "Geral"**: `Geral · 2026 · 2025 · 2024`.
  No modo Geral a barra de período vira **os anos** (2024/2025/2026) e o
  dashboard abre no *Período Completo* — todos os anos somados.
  Nos arquivos por ano a barra continua sendo os **12 meses** (os meses sem
  dado ficam apagados).
- **Público-alvo** vindo de `marketdata.silver.anbima_perfil_classe`
  (campo `tipo_investidor`), agregado por classe.
- **Taxa de administração e taxa de performance** vindas de
  `marketdata.silver.anbima_taxas_classe` (`valor_percentual`, filtrando
  `tipo_taxa` por `%administ%` e `%performance%`), com duas colunas novas na
  tabela e uma **aba "Taxas"** (mediana, média, cobertura, faixas e mediana
  por gestora).
- **Link CVM** gerado automaticamente a partir do CNPJ (base configurável em
  `LINK_CVM_BASE`).
- **Administrador** vindo de `anbima_prestadores_fundo`
  (`codigo_tipo_prestador LIKE 'ADMIN%'`) — a coluna vinha vazia.

## Rodar

    pip install -r requirements.txt
    cp .env.exemplo .env      # cole o token
    python atualizar_monitor.py

Saída em `outputs/`:

    dashboard_fundos_tivio_geral.html   2024 + 2025 + 2026
    dashboard_fundos_tivio_2026.html
    dashboard_fundos_tivio_2025.html
    dashboard_fundos_tivio_2024.html
    dashboard_fundos_tivio.html         cópia do principal

O principal é o **ano mais recente**; para abrir no Geral use
`HTML_PRINCIPAL=geral` no `.env`.

Teste sem Databricks: `USE_MOCK=true python atualizar_monitor.py`
(gera ~1.000 classes fictícias em 2024/2025/2026, útil para conferir layout).

## Recorte de anos
O SQL traz tudo a partir de `DATA_INI` (default `2024-01-01`). Um arquivo é
gerado por ano encontrado e o seletor navega entre eles.

## Arquivos
- `atualizar_monitor.py` .. conecta, gera FUNDS_DATA, separa por ano, grava
- `monitor_metrics.py` ... df -> array de 25 posições (pos 11 = ano)
- `patch_meses.py` ....... barra de período (meses ou anos) + seletor de ano
- `sql/monitor_fundos.sql`  query ANBIMA/CVM
- `templates/dashboard_fundos_tivio.html` .. template (não editar o outputs/)
