-- ============================================================
-- fundos_tivio.sql  ·  Central de Análises · Tivio Capital
-- Fonte REAL confirmada: portfolioanalytics.gold.vw_aum
-- Colunas: date, fund_code, fund_name, distributor_name,
--          normalized_vertical, client_type, aum, double_count, anbima_code
--
-- Regra do double_count: a view marca posições que se contam 2x
-- (fundo que investe em outro fundo Tivio). Para o PL "de verdade"
-- da casa, filtramos double_count = false. Ajuste se o TI orientar
-- diferente.
-- ============================================================
SELECT
    date,
    fund_code,
    fund_name,
    distributor_name,
    normalized_vertical,
    client_type,
    aum
FROM portfolioanalytics.gold.vw_aum
WHERE date = (SELECT MAX(date) FROM portfolioanalytics.gold.vw_aum)
  AND double_count = false
ORDER BY aum DESC
