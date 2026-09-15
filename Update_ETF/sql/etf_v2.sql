-- =====================================================================
-- etf_v2.sql  ·  Analise · ETF · Tivio Capital
-- Base de ETFs listados na B3, enriquecida com fee da ANBIMA.
--
-- ESTRATEGIA:
--   A base B3 (b3_instrumentos_financeiros) e a espinha dorsal: garante
--   ticker, nome, data_inicio, data_referencia, lancamento_12m e o
--   universo de ~180 ETFs.
--   ANBIMA e CVM entram como LEFT JOIN, entao NUNCA reduzem o universo:
--   se nao casar, o campo vem NULL, mas o ETF continua na lista.
--
-- CHAVE DE LIGACAO:
--   B3.isin_isin  <-->  anbima_classes_fundo.isin   (normalizado)
--   ANBIMA.cnpj   <-->  cvm_informe_diario.cnpj_fundo_classe
--
-- SAIDA (aliases compativeis com etf_metrics.py):
--   ticker, nome, gestora, categoria, pl, fee, cnpj,
--   data_inicio, data_referencia, lancamento_12m
--
-- 'pl' continua vindo do market cap da B3 (mkt_cptlstn), preservando o
-- comportamento atual do dashboard. O PL regulatorio entra como coluna
-- extra (pl_cvm), apenas para validacao.
--
-- ---------------------------------------------------------------------
-- REVISAO 14/09/2026 - correcoes sobre a versao anterior:
--
--   [1] FILTRO DE NOME REMOVIDO
--       A CTE anbima filtrava  nome LIKE '%ETF%'  OR  razao LIKE '%ETF%'.
--       Boa parte dos ETFs nao tem "ETF" no nome registrado - ex.:
--         "CLASSE UNICA DE COTAS DO BTG PACTUAL IBOVESPA B3 FUNDO DE INDICE"
--         "IT NOW PIBB IBRX-50 FUNDO DE INDICE RESP LIMITADA"
--       O filtro descartaria justamente esses. Como o join ja e por ISIN
--       (chave unica e precisa), nenhum filtro de nome e necessario.
--
--   [2] COLUNA DE DATA CORRIGIDA
--       ORDER BY c.data_inicio_classe  ->  c.data_inicio_atividade_classe
--       A primeira nao existe na tabela (a segunda e a usada no
--       monitor_fundos.sql, ja validada em producao).
--
--   [3] FILTRO DE TAXA AMPLIADO
--       Antes:  WHERE perfil_taxa = 'Fixa' AND unidade_taxa = 'Percentual'
--       Agora:  WHERE valor_percentual IS NOT NULL
--       Motivos: (a) 'Escalonada' tambem tem valor valido - o filtro
--       antigo descartava 2.932 classes no Monitor; (b) a coluna
--       unidade_taxa nao foi confirmada via DESCRIBE; (c) tipo_taxa
--       nessa tabela so possui o valor 'Global' (taxa de administracao),
--       entao nao ha risco de misturar outro tipo de taxa.
--       O GROUP BY passou a ser so por codigo_classe, que e a chave
--       efetiva da tabela.
--
--   [4] FONTE DE PL TROCADA
--       cvm_cda_pl -> cvm_informe_diario (mesma fonte ja usada em
--       producao no pipeline de Captacao · Fundos Abertos).
--       Se cvm_cda_pl existir e for preferivel, basta trocar o nome na
--       CTE pl_cvm: as colunas usadas sao as mesmas.
--
--   [5] nivel3_subcategoria REMOVIDO (coluna nao confirmada).
-- =====================================================================

WITH parametros AS (
    SELECT MAX(rpt_dt) AS data_referencia
    FROM marketdata.silver.b3_instrumentos_financeiros
),

-- ---------------------------------------------------------------------
-- 1) Base B3 - define o universo de ETFs
-- ---------------------------------------------------------------------
b3 AS (
    SELECT
        i.tckr_symb        AS ticker,
        i.asst_desc        AS nome,
        i.crpn_nm          AS gestora,
        i.scty_ctgy_nm     AS categoria_b3,
        i.mkt_cptlstn      AS pl,
        i.isin_isin        AS isin,
        i.tradg_start_dt   AS data_inicio,
        p.data_referencia,

        CASE
            WHEN i.tradg_start_dt >  add_months(p.data_referencia, -12)
             AND i.tradg_start_dt <= p.data_referencia
            THEN 1 ELSE 0
        END AS lancamento_12m

    FROM marketdata.silver.b3_instrumentos_financeiros i
    CROSS JOIN parametros p
    WHERE i.rpt_dt = p.data_referencia
      AND i.scty_ctgy_nm IN ('ETF EQUITIES', 'ETF FOREIGN INDEX')
      AND i.tckr_symb RLIKE '11$'
),

-- ---------------------------------------------------------------------
-- 2) Classes ANBIMA, chaveadas por ISIN
--    Sem filtro de nome (ver nota [1]): o ISIN ja e chave precisa.
--    ROW_NUMBER resolve eventual duplicidade de ISIN, mantendo a
--    classe de inicio de atividade mais recente.
-- ---------------------------------------------------------------------
anbima AS (
    SELECT
        upper(trim(c.isin))                                  AS isin,
        regexp_replace(c.identificador_classe, '[^0-9]', '') AS cnpj,
        c.categoria_cvm,
        c.tipo_anbima,
        c.nivel1_categoria,
        c.nivel2_categoria,
        c.codigo_fundo,
        c.codigo_classe,
        ROW_NUMBER() OVER (
            PARTITION BY upper(trim(c.isin))
            ORDER BY c.data_inicio_atividade_classe DESC
        ) AS rn
    FROM marketdata.silver.anbima_classes_fundo c
    WHERE c.isin IS NOT NULL
      AND trim(c.isin) <> ''
),

-- ---------------------------------------------------------------------
-- 3) Taxa de administracao ANBIMA (Fixa + Escalonada) - ver nota [3]
-- ---------------------------------------------------------------------
taxas AS (
    SELECT
        codigo_classe,
        MAX(try_cast(valor_percentual AS DOUBLE)) AS fee
    FROM marketdata.silver.anbima_taxas_classe
    WHERE valor_percentual IS NOT NULL
    GROUP BY codigo_classe
),

-- ---------------------------------------------------------------------
-- 4) PL regulatorio CVM, registro mais recente por CNPJ - ver nota [4]
-- ---------------------------------------------------------------------
pl_cvm AS (
    SELECT
        cnpj,
        vl_patrim_liq
    FROM (
        SELECT
            regexp_replace(cnpj_fundo_classe, '[^0-9]', '') AS cnpj,
            vl_patrim_liq,
            ROW_NUMBER() OVER (
                PARTITION BY regexp_replace(cnpj_fundo_classe, '[^0-9]', '')
                ORDER BY dt_comptc DESC
            ) AS rn
        FROM marketdata.silver.cvm_informe_diario
        WHERE vl_patrim_liq IS NOT NULL
    )
    WHERE rn = 1
)

-- ---------------------------------------------------------------------
-- 5) Montagem final (aliases compativeis com etf_metrics.py)
-- ---------------------------------------------------------------------
SELECT
    b3.ticker,
    b3.nome,
    b3.gestora,

    CASE
        WHEN b3.categoria_b3 = 'ETF FOREIGN INDEX' THEN 'RV Internacional'
        WHEN b3.categoria_b3 = 'ETF EQUITIES'      THEN 'RV Brasil'
        ELSE 'Outros'
    END AS categoria,

    b3.pl,          -- market cap B3 (comportamento atual do dashboard)
    t.fee,          -- taxa de administracao ANBIMA
    a.cnpj,         -- CNPJ real, vindo da ANBIMA

    b3.data_inicio,
    b3.data_referencia,
    b3.lancamento_12m,

    -- ------- colunas extras (validacao / fases futuras) -------
    p.vl_patrim_liq AS pl_cvm,
    a.categoria_cvm,
    a.tipo_anbima,
    a.nivel1_categoria,
    a.nivel2_categoria

FROM b3

LEFT JOIN anbima a
    ON upper(trim(b3.isin)) = a.isin
   AND a.rn = 1

LEFT JOIN taxas t
    ON t.codigo_classe = a.codigo_classe

LEFT JOIN pl_cvm p
    ON p.cnpj = a.cnpj

WHERE b3.pl IS NOT NULL
  AND b3.pl > 0

ORDER BY b3.pl DESC
