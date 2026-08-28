-- ============================================================
-- captacao.sql  ·  Central de Análises · Tivio Capital
-- Ajuste catalog/schema/coluna conforme as views do TI.
-- O Python injeta {catalog} e {schema} automaticamente.
-- ============================================================
SELECT
    gestora,
    captacao_liquida,
    fundos_ativos,
    fundo_destaque
FROM {catalog}.{schema}.vw_captacao
WHERE mes_ref = date_trunc('month', current_date())
ORDER BY captacao_liquida DESC
