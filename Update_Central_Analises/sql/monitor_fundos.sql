-- ============================================================
-- Monitor de Novos Fundos - Tivio Capital
-- Fonte: ANBIMA / CVM (Databricks)
--
-- Placeholders preenchidos por atualizar_monitor.py:
--   {catalog}   -> marketdata
--   {schema}    -> silver
--   {link_base} -> URL base da consulta publica da CVM
--   {data_ini}  -> data inicial do recorte (AAAA-MM-DD)
--
-- Gestora: {catalog}.{schema}.anbima_prestadores_fundo
--          (codigo_tipo_prestador = 'GESTOR' -> 11.5k de 11.5k fundos;
--           a antiga anbima_prestadores_classe / CO_GESTOR cobria so 205)
-- ============================================================

WITH gestores_por_fundo AS (

    SELECT
        codigo_fundo,

        concat_ws(
            ' / ',
            sort_array(
                collect_set(nome_comercial)
            )
        ) AS gestora

    FROM {catalog}.{schema}.anbima_prestadores_fundo

    WHERE codigo_tipo_prestador = 'GESTOR'

    GROUP BY codigo_fundo
),

administradores_por_fundo AS (

    SELECT
        codigo_fundo,

        concat_ws(
            ' / ',
            sort_array(
                collect_set(nome_comercial)
            )
        ) AS administrador

    FROM {catalog}.{schema}.anbima_prestadores_fundo

    WHERE upper(codigo_tipo_prestador) LIKE 'ADMIN%'

    GROUP BY codigo_fundo
),

-- Publico-alvo: {catalog}.{schema}.anbima_perfil_classe.tipo_investidor
perfil_por_classe AS (

    SELECT
        codigo_classe,

        concat_ws(
            ' / ',
            sort_array(
                collect_set(trim(tipo_investidor))
            )
        ) AS tipo_investidor

    FROM {catalog}.{schema}.anbima_perfil_classe

    WHERE tipo_investidor IS NOT NULL
      AND trim(tipo_investidor) <> ''

    GROUP BY codigo_classe
),

-- Taxa de administracao: {catalog}.{schema}.anbima_taxas_classe
taxa_administracao AS (

    SELECT
        codigo_classe,
        MAX(
            try_cast(
                replace(
                    trim(CAST(valor_percentual AS STRING)),
                    ',',
                    '.'
                ) AS DOUBLE
            )
        ) AS valor_percentual

    FROM {catalog}.{schema}.anbima_taxas_classe

    WHERE lower(tipo_taxa) LIKE '%administ%'

    GROUP BY codigo_classe
),

-- Taxa de performance: mesma tabela, outro tipo_taxa
taxa_performance AS (

    SELECT
        codigo_classe,
        MAX(
            try_cast(
                replace(
                    trim(CAST(valor_percentual AS STRING)),
                    ',',
                    '.'
                ) AS DOUBLE
            )
        ) AS valor_percentual

    FROM {catalog}.{schema}.anbima_taxas_classe

    WHERE lower(tipo_taxa) LIKE '%performance%'

    GROUP BY codigo_classe
)

SELECT
    COALESCE(
        c.nome_comercial_classe,
        c.razao_social_classe,
        ''
    ) AS fund_name,

    COALESCE(
        gf.gestora,
        ''
    ) AS gestora,

    COALESCE(
        af.tipo_fundo,
        c.categoria_cvm,
        ''
    ) AS tipo,

    -- "Classif. ANBIMA | Publico-alvo | Exclusivo"
    concat_ws(
        ' | ',
        nullif(
            COALESCE(c.tipo_anbima, c.nivel2_categoria, ''),
            ''
        ),
        nullif(
            COALESCE(pf.tipo_investidor, ''),
            ''
        ),
        CASE
            WHEN f.is_exclusive THEN 'Exclusivo'
        END
    ) AS segmento_detalhe,

    COALESCE(
        c.tipo_anbima,
        c.nivel2_categoria,
        ''
    ) AS categoria_anbima,

    COALESCE(
        f.cvm_status,
        ''
    ) AS situacao,

    date_format(
        c.data_inicio_atividade_classe,
        'dd/MM/yyyy'
    ) AS data_registro,

    date_format(
        af.data_vigencia_fundo,
        'dd/MM/yyyy'
    ) AS data_constituicao,

    COALESCE(
        af.identificador_fundo,
        ''
    ) AS cnpj,

    COALESCE(
        pf.tipo_investidor,
        ''
    ) AS publico_alvo,

    CASE
        WHEN f.is_exclusive THEN 'S'
        ELSE 'N'
    END AS exclusivo,

    CAST(
        year(c.data_inicio_atividade_classe) AS STRING
    ) AS campo_11,

    COALESCE(
        c.forma_condominio,
        ''
    ) AS condominio,

    COALESCE(
        c.nome_comercial_classe,
        ''
    ) AS subclasse,

    concat(
        CASE
            WHEN lower(COALESCE(c.credito_privado, ''))
                 IN ('s', 'sim', 'true', '1')
            THEN '1'
            ELSE '0'
        END,
        CASE
            WHEN upper(COALESCE(af.tipo_fundo, '')) LIKE '%FIDC%'
                OR upper(COALESCE(c.categoria_cvm, '')) LIKE '%FIDC%'
            THEN '1'
            ELSE '0'
        END,
        CASE
            WHEN lower(COALESCE(c.infraestrutura, ''))
                 IN ('s', 'sim', 'true', '1')
            THEN '1'
            ELSE '0'
        END,
        CASE
            WHEN f.is_pension_fund
                OR upper(COALESCE(c.nome_comercial_classe, '')) LIKE '%PREV%'
                OR upper(COALESCE(c.nome_comercial_classe, '')) LIKE '%PGBL%'
                OR upper(COALESCE(c.nome_comercial_classe, '')) LIKE '%VGBL%'
                OR upper(COALESCE(c.nome_comercial_classe, '')) LIKE '%FLEXPREV%'
                OR upper(COALESCE(c.tipo_anbima, '')) LIKE '%PREVID%'
                OR upper(COALESCE(c.nivel1_categoria, '')) LIKE '%PREVID%'
                OR lower(COALESCE(pf.tipo_investidor, '')) LIKE '%previd%'
            THEN '1'
            ELSE '0'
        END,
        CASE
            WHEN lower(COALESCE(c.investimento_exterior, ''))
                 IN ('s', 'sim', 'true', '1')
                OR upper(COALESCE(c.nome_comercial_classe, '')) LIKE '%GLOBAL%'
                OR upper(COALESCE(c.nome_comercial_classe, '')) LIKE '%INTERNACIONAL%'
                OR upper(COALESCE(c.nome_comercial_classe, '')) LIKE '%EXTERIOR%'
                OR upper(COALESCE(c.tipo_anbima, '')) LIKE '%EXTERIOR%'
            THEN '1'
            ELSE '0'
        END,
        CASE
            WHEN lower(COALESCE(c.fundo_esg, ''))
                 IN ('s', 'sim', 'true', '1')
            THEN '1'
            ELSE '0'
        END
    ) AS segmentos_bitmask,

    -- Link CVM montado a partir do CNPJ (so quando ha 14 digitos)
    CASE
        WHEN length(
                regexp_replace(
                    COALESCE(af.identificador_fundo, ''),
                    '[^0-9]',
                    ''
                )
             ) = 14
        THEN concat(
                '{link_base}',
                regexp_replace(
                    COALESCE(af.identificador_fundo, ''),
                    '[^0-9]',
                    ''
                )
             )
        ELSE ''
    END AS link_cvm,

    month(
        c.data_inicio_atividade_classe
    ) AS mes_ref,

    COALESCE(
        gf.gestora,
        ''
    ) AS gestor_juridico,

    COALESCE(
        ad.administrador,
        ''
    ) AS administrador,

    COALESCE(
        c.nivel1_categoria,
        ''
    ) AS categoria_n1,

    COALESCE(
        f.risk_level,
        ''
    ) AS risco_credito,

    '' AS duracao,

    'Nao' AS registro,

    tx.valor_percentual  AS taxa_adm,

    tp.valor_percentual  AS taxa_perf

FROM {catalog}.{schema}.anbima_classes_fundo c

LEFT JOIN {catalog}.{schema}.anbima_fundo af
    ON af.codigo_fundo = c.codigo_fundo

LEFT JOIN masterdata.silver.fund f
    ON regexp_replace(
        COALESCE(f.taxpayer_identifier, ''),
        '[^0-9]',
        ''
    ) = regexp_replace(
        COALESCE(af.identificador_fundo, ''),
        '[^0-9]',
        ''
    )

LEFT JOIN gestores_por_fundo gf
    ON gf.codigo_fundo = c.codigo_fundo

LEFT JOIN administradores_por_fundo ad
    ON ad.codigo_fundo = c.codigo_fundo

LEFT JOIN perfil_por_classe pf
    ON pf.codigo_classe = c.codigo_classe

LEFT JOIN taxa_administracao tx
    ON tx.codigo_classe = c.codigo_classe

LEFT JOIN taxa_performance tp
    ON tp.codigo_classe = c.codigo_classe

WHERE c.data_inicio_atividade_classe >= '{data_ini}'

ORDER BY c.data_inicio_atividade_classe DESC
