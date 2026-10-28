-- =====================================================================
-- etf.sql
-- Base de ETFs listados na B3
--
-- Fonte:
--   marketdata.silver.b3_instrumentos_financeiros
--
-- Saída:
--   ticker, nome, gestora, categoria, pl, isin,
--   data_inicio, data_referencia, lancamento_12m
--
-- A normalização da gestora fica no etf_metrics.py.
-- O fee vem do peers_etf.csv.
-- =====================================================================

WITH parametros AS (
    SELECT
        MAX(rpt_dt) AS data_referencia
    FROM marketdata.silver.b3_instrumentos_financeiros
),

base AS (
    SELECT
        i.tckr_symb AS ticker,
        i.asst_desc AS nome,
        i.crpn_nm AS gestora,
        i.scty_ctgy_nm AS categoria_b3,
        i.mkt_cptlstn AS pl,
        i.isin_isin AS isin,
        i.tradg_start_dt AS data_inicio,
        p.data_referencia,

        CASE
            WHEN i.tradg_start_dt > add_months(p.data_referencia, -12)
             AND i.tradg_start_dt <= p.data_referencia
            THEN 1
            ELSE 0
        END AS lancamento_12m

    FROM marketdata.silver.b3_instrumentos_financeiros i
    CROSS JOIN parametros p

    WHERE i.rpt_dt = p.data_referencia

      -- Somente categorias efetivamente relacionadas a ETF.
      AND i.scty_ctgy_nm IN (
          'ETF EQUITIES',
          'ETF FOREIGN INDEX'
      )

      -- Somente ticker de negociação principal.
      -- Exclui BOVA11M, BOVA11Q e instrumentos de mercado primário.
      AND i.tckr_symb RLIKE '11$'
)

SELECT
    ticker,
    nome,
    gestora,

    CASE
        WHEN categoria_b3 = 'ETF FOREIGN INDEX'
        THEN 'RV Internacional'

        WHEN categoria_b3 = 'ETF EQUITIES'
        THEN 'RV Brasil'

        ELSE 'Outros'
    END AS categoria,

    pl,
    isin,
    data_inicio,
    data_referencia,
    lancamento_12m

FROM base

WHERE pl IS NOT NULL
  AND pl > 0

ORDER BY pl DESC