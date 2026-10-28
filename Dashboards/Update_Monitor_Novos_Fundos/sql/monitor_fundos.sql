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
--
-- ------------------------------------------------------------
-- CORRECAO 1 (2026-09-14): catalogo restrito
-- Removida a dependencia da tabela de cadastro do catalogo restrito
-- (alias f), que causava:
--   [INSUFFICIENT_PERMISSIONS] User does not have USE CATALOG. SQLSTATE: 42501
-- Tratamento dos 3 campos que vinham de la:
--   is_exclusive    -> CTE exclusivo_por_classe (nome / razao social / condominio)
--   cvm_status      -> sem equivalente na ANBIMA; retorna '' (ver nota)
--   is_pension_fund -> ja havia varias regras por nome/categoria no bitmask
--
-- NOTA: a coluna c.situacao NAO existe em anbima_classes_fundo.
-- Enquanto o acesso a tabela de cadastro nao for liberado, o campo sai
-- vazio para nao quebrar o contrato de colunas do monitor_metrics.py.
--
-- ------------------------------------------------------------
-- CORRECAO 2 (2026-09-14): taxa de administracao
-- O filtro perfil_taxa = 'Fixa' descartava 2.932 classes com perfil
-- 'Escalonada'. Como tipo_taxa so possui o valor 'Global' nessa tabela,
-- nao ha risco de misturar outro tipo de taxa. Filtro trocado por
-- valor_percentual IS NOT NULL.
--   Fixa ........ 29.610 classes | media 1,4759
--   Escalonada ... 2.932 classes | media 0,4709
-- Obs.: para as escalonadas o valor_percentual e a faixa base; o
-- detalhamento por faixa esta em anbima_faixas_escalonamento_classe.
--
-- ------------------------------------------------------------
-- CORRECAO 3 (2026-09-14): taxa de performance (estava 0/11733)
-- A performance NAO esta em anbima_taxas_classe (que so tem taxa
-- global de administracao, tipo_taxa = 'Global'). O filtro antigo
--   WHERE lower(tipo_taxa) LIKE '%performance%'
-- nunca casava, zerando o campo.
-- Fonte correta: anbima_detalhes_taxa_performance_classe
--   valor_percentual .............. % de performance (ex.: 20, 15)
--   indice_referencia ............. CDI / IPCA / IBOVESPA / OUTROS
--   valor_percentual_indice_ref ... % do indice (ex.: 100)
--   -> 13.024 linhas / 13.020 classes distintas
-- A tabela anbima_taxa_performance_classe so indica SE ha cobranca
-- (perfil/periodicidade), sem valor - por isso nao e usada aqui.
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
-- Taxa de administracao (taxa global): Fixa + Escalonada
taxa_administracao AS (
    SELECT
        codigo_classe,
        MAX(
            try_cast(valor_percentual AS DOUBLE)
        ) AS valor_percentual
    FROM {catalog}.{schema}.anbima_taxas_classe
    WHERE valor_percentual IS NOT NULL
    GROUP BY codigo_classe
),
-- Taxa de performance: tabela propria de detalhes
taxa_performance AS (
    SELECT
        codigo_classe,
        MAX(
            try_cast(valor_percentual AS DOUBLE)
        ) AS valor_percentual,
        max(
            nullif(trim(indice_referencia), '')
        ) AS indice_referencia
    FROM {catalog}.{schema}.anbima_detalhes_taxa_performance_classe
    WHERE valor_percentual IS NOT NULL
      AND try_cast(valor_percentual AS DOUBLE) > 0
    GROUP BY codigo_classe
),
-- Substituto do antigo campo is_exclusive (catalogo restrito)
exclusivo_por_classe AS (
    SELECT
        codigo_classe,
        CASE
            WHEN upper(COALESCE(forma_condominio, '')) LIKE '%FECHADO%'
                 AND upper(COALESCE(nome_comercial_classe, '')) LIKE '%EXCLUSIV%'
            THEN TRUE
            WHEN upper(COALESCE(nome_comercial_classe, '')) LIKE '%EXCLUSIV%'
            THEN TRUE
            WHEN upper(COALESCE(razao_social_classe, '')) LIKE '%EXCLUSIV%'
            THEN TRUE
            ELSE FALSE
        END AS is_exclusive
    FROM {catalog}.{schema}.anbima_classes_fundo
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
            WHEN ex.is_exclusive THEN 'Exclusivo'
        END
    ) AS segmento_detalhe,
    COALESCE(
        c.tipo_anbima,
        c.nivel2_categoria,
        ''
    ) AS categoria_anbima,
    -- cvm_status vinha do catalogo restrito; sem equivalente na ANBIMA
    '' AS situacao,
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
    CASE
        WHEN pf.tipo_investidor IS NULL
          OR trim(pf.tipo_investidor) = ''
          OR upper(trim(pf.tipo_investidor)) IN ('ND','N/D','NA')
        THEN 'N/D'
        ELSE trim(pf.tipo_investidor)
    END AS publico_alvo,
    CASE
        WHEN ex.is_exclusive THEN 'S'
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
            WHEN upper(COALESCE(c.nome_comercial_classe, '')) LIKE '%PREV%'
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
    CASE
        WHEN upper(COALESCE(c.tipo_anbima,'')) LIKE '%CRÉDITO LIVRE%'
          OR upper(COALESCE(c.tipo_anbima,'')) LIKE '%CREDITO LIVRE%'
        THEN 'Crédito Livre'
        WHEN upper(COALESCE(c.tipo_anbima,'')) LIKE '%GRAU DE INVESTIMENTO%'
        THEN 'Grau de Investimento'
        WHEN upper(COALESCE(c.tipo_anbima,'')) LIKE '%SOBERANO%'
        THEN 'Soberano'
        ELSE ''
    END AS risco_credito,
    COALESCE(
        c.nivel2_categoria,
        ''
    ) AS duracao,
    'Nao' AS registro,
    tx.valor_percentual  AS taxa_adm,
    tp.valor_percentual  AS taxa_perf
FROM {catalog}.{schema}.anbima_classes_fundo c
LEFT JOIN {catalog}.{schema}.anbima_fundo af
    ON af.codigo_fundo = c.codigo_fundo
LEFT JOIN exclusivo_por_classe ex
    ON ex.codigo_classe = c.codigo_classe
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
