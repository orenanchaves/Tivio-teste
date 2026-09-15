-- =====================================================================
-- captacao_fundos_abertos.sql
-- Captacao liquida de fundos abertos (CVM informe diario + cadastro ANBIMA)
--
-- FONTE REAL (validada):
--   cvm_informe_diario        -> captacao, resgate, PL, cota, cotistas
--   anbima_classes_fundo      -> nome, categoria, flags, codigo_fundo
--   anbima_fundo              -> nome comercial do fundo
--   anbima_prestadores_classe -> gestor (CO_GESTOR)
--
-- ATENCAO: a PLATAFORMA (XP/BTG/Itau/Bradesco) NAO sai daqui.
--          Ela vem do arquivo peers_fundos_abertos.csv (Vivian), via CNPJ.
--
-- Saida esperada pelo Python:
--   cnpj, nome, categoria, benchmark, gestor,
--   cap30, cap12, capytd, pl, rent30, rent12, rentytd,
--   cotistas, data_ultimo_registro
-- =====================================================================

WITH parametros AS (
    SELECT MAX(dt_comptc) AS data_referencia
    FROM marketdata.silver.cvm_informe_diario
),

fluxo AS (
    SELECT
        i.cnpj_fundo_classe,

        SUM(
            CASE
                WHEN i.dt_comptc > date_sub(p.data_referencia, 30)
                 AND i.dt_comptc <= p.data_referencia
                THEN COALESCE(i.captc_dia, 0) - COALESCE(i.resg_dia, 0)
                ELSE 0
            END
        ) AS cap30,

        SUM(
            CASE
                WHEN i.dt_comptc > add_months(p.data_referencia, -12)
                 AND i.dt_comptc <= p.data_referencia
                THEN COALESCE(i.captc_dia, 0) - COALESCE(i.resg_dia, 0)
                ELSE 0
            END
        ) AS cap12,

        SUM(
            CASE
                WHEN i.dt_comptc >= make_date(year(p.data_referencia), 1, 1)
                 AND i.dt_comptc <= p.data_referencia
                THEN COALESCE(i.captc_dia, 0) - COALESCE(i.resg_dia, 0)
                ELSE 0
            END
        ) AS capytd

    FROM marketdata.silver.cvm_informe_diario i
    CROSS JOIN parametros p
    WHERE i.dt_comptc > add_months(p.data_referencia, -12)
    GROUP BY i.cnpj_fundo_classe
),

historico_cotas AS (
    SELECT
        i.cnpj_fundo_classe,
        i.dt_comptc,
        i.vl_patrim_liq,
        i.vl_quota,
        i.nr_cotst,
        p.data_referencia,

        ROW_NUMBER() OVER (
            PARTITION BY i.cnpj_fundo_classe
            ORDER BY i.dt_comptc DESC
        ) AS rn_atual,

        ROW_NUMBER() OVER (
            PARTITION BY i.cnpj_fundo_classe
            ORDER BY
                CASE WHEN i.dt_comptc <= date_sub(p.data_referencia, 30) THEN 0 ELSE 1 END,
                CASE WHEN i.dt_comptc <= date_sub(p.data_referencia, 30) THEN i.dt_comptc END DESC
        ) AS rn_30,

        ROW_NUMBER() OVER (
            PARTITION BY i.cnpj_fundo_classe
            ORDER BY
                CASE WHEN i.dt_comptc <= add_months(p.data_referencia, -12) THEN 0 ELSE 1 END,
                CASE WHEN i.dt_comptc <= add_months(p.data_referencia, -12) THEN i.dt_comptc END DESC
        ) AS rn_12,

        ROW_NUMBER() OVER (
            PARTITION BY i.cnpj_fundo_classe
            ORDER BY
                CASE WHEN i.dt_comptc < make_date(year(p.data_referencia), 1, 1) THEN 0 ELSE 1 END,
                CASE WHEN i.dt_comptc < make_date(year(p.data_referencia), 1, 1) THEN i.dt_comptc END DESC
        ) AS rn_ytd

    FROM marketdata.silver.cvm_informe_diario i
    CROSS JOIN parametros p
),

cotas AS (
    SELECT
        cnpj_fundo_classe,
        MAX(CASE WHEN rn_atual = 1 THEN vl_patrim_liq END) AS pl,
        MAX(CASE WHEN rn_atual = 1 THEN vl_quota      END) AS cota_atual,
        MAX(CASE WHEN rn_atual = 1 THEN nr_cotst      END) AS cotistas,
        MAX(CASE WHEN rn_atual = 1 THEN dt_comptc     END) AS data_ultimo_registro,
        MAX(CASE WHEN rn_30    = 1 THEN vl_quota      END) AS cota_30,
        MAX(CASE WHEN rn_12    = 1 THEN vl_quota      END) AS cota_12,
        MAX(CASE WHEN rn_ytd   = 1 THEN vl_quota      END) AS cota_ytd
    FROM historico_cotas
    GROUP BY cnpj_fundo_classe
),

classes AS (
    SELECT
        identificador_classe,
        codigo_classe,
        codigo_fundo,
        nome_comercial_classe,
        tipo_anbima,
        nivel1_categoria,
        credito_privado
    FROM marketdata.silver.anbima_classes_fundo
),

gestores AS (
    SELECT
        codigo_classe,
        MAX(nome_comercial) AS gestor
    FROM marketdata.silver.anbima_prestadores_classe
    WHERE codigo_tipo_prestador = 'CO_GESTOR'
      AND (data_fim_vigencia IS NULL OR data_fim_vigencia >= current_date())
    GROUP BY codigo_classe
)

SELECT
    fluxo.cnpj_fundo_classe AS cnpj,

    COALESCE(c.nome_comercial_classe, f.nome_comercial_fundo) AS nome,

    CASE
        WHEN c.nivel1_categoria = 'Multimercados' THEN 'Multimercado'
        WHEN c.nivel1_categoria = 'Renda Fixa'
         AND (c.credito_privado = 'S'
              OR upper(COALESCE(c.tipo_anbima, '')) LIKE '%CRÉDITO%'
              OR upper(COALESCE(c.tipo_anbima, '')) LIKE '%CREDITO%')
        THEN 'Renda Fixa Ativa'
        WHEN c.nivel1_categoria = 'Renda Fixa' THEN 'Renda Fixa'
        ELSE NULL
    END AS categoria,

    CASE
        WHEN upper(COALESCE(c.tipo_anbima, '')) LIKE '%INDEXADO%' THEN 'Índice'
        ELSE 'CDI'
    END AS benchmark,

    COALESCE(g.gestor, 'N/D') AS gestor,

    fluxo.cap30,
    fluxo.cap12,
    fluxo.capytd,

    cotas.pl,

    CASE WHEN cotas.cota_30  IS NOT NULL AND cotas.cota_30  <> 0
         THEN ((cotas.cota_atual / cotas.cota_30)  - 1) * 100 END AS rent30,
    CASE WHEN cotas.cota_12  IS NOT NULL AND cotas.cota_12  <> 0
         THEN ((cotas.cota_atual / cotas.cota_12)  - 1) * 100 END AS rent12,
    CASE WHEN cotas.cota_ytd IS NOT NULL AND cotas.cota_ytd <> 0
         THEN ((cotas.cota_atual / cotas.cota_ytd) - 1) * 100 END AS rentytd,

    cotas.cotistas,
    cotas.data_ultimo_registro

FROM fluxo

INNER JOIN classes c
    ON regexp_replace(fluxo.cnpj_fundo_classe, '[^0-9]', '')
     = regexp_replace(c.identificador_classe, '[^0-9]', '')

LEFT JOIN marketdata.silver.anbima_fundo f
    ON c.codigo_fundo = f.codigo_fundo

LEFT JOIN gestores g
    ON c.codigo_classe = g.codigo_classe

LEFT JOIN cotas
    ON fluxo.cnpj_fundo_classe = cotas.cnpj_fundo_classe

WHERE COALESCE(c.nome_comercial_classe, f.nome_comercial_fundo) IS NOT NULL
  AND c.nivel1_categoria IN ('Renda Fixa', 'Multimercados')
  AND cotas.pl > 0