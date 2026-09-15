-- Acumula o CDI (fator diario) em 30d, 12m e YTD,
-- ancorado na mesma data de referencia do informe diario.
WITH parametros AS (
    SELECT MAX(dt_comptc) AS data_referencia
    FROM marketdata.silver.cvm_informe_diario
)
SELECT
    EXP(SUM(CASE
        WHEN c.Data > date_sub(p.data_referencia, 30)
         AND c.Data <= p.data_referencia
        THEN LN(1 + c.ValorDiaCDI) ELSE 0 END)) - 1 AS cdi30,

    EXP(SUM(CASE
        WHEN c.Data > add_months(p.data_referencia, -12)
         AND c.Data <= p.data_referencia
        THEN LN(1 + c.ValorDiaCDI) ELSE 0 END)) - 1 AS cdi12,

    EXP(SUM(CASE
        WHEN c.Data >= make_date(year(p.data_referencia), 1, 1)
         AND c.Data <= p.data_referencia
        THEN LN(1 + c.ValorDiaCDI) ELSE 0 END)) - 1 AS cdiytd

FROM marketdata.silver.daily_cdi_price c
CROSS JOIN parametros p
WHERE c.Data > add_months(p.data_referencia, -12)