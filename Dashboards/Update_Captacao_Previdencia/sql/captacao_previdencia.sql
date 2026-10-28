-- ============================================================
-- Captacao · Previdencia - Tivio Capital
--
-- STATUS: NAO VALIDADO CONTRA O DATABRICKS.
-- Ver ORIGEM_DOS_DADOS.md nesta pasta.
--
-- Estrutura espelhada de Update_Captacao_Fundos_Abertos, que usa as
-- mesmas quatro tabelas e ja roda. A diferenca de escopo e o recorte
-- de previdencia (PGBL/VGBL), aplicado no WHERE.
--
-- ATENCAO: o ambiente de Fundos Abertos tem divergencia aberta contra a
-- planilha de referencia (ver ORIGEM_DOS_DADOS.md de la). Como este SQL
-- parte da mesma logica, e provavel que herde a mesma divergencia -
-- conciliar aquele primeiro.
--
-- Placeholders: {catalog} {schema} {data_ini}
-- ============================================================
WITH prestador AS (
    SELECT
        codigo_classe,
        MAX(CASE WHEN codigo_tipo_prestador = 'GESTOR'
                 THEN nome_comercial END) AS gestora,
        MAX(CASE WHEN upper(codigo_tipo_prestador) LIKE 'DISTRIB%'
                 THEN nome_comercial END) AS distribuidor
    FROM {catalog}.{schema}.anbima_prestadores_classe
    GROUP BY codigo_classe
),
movimento AS (
    SELECT
        codigo_classe,
        SUM(captacao)                  AS captacao,
        SUM(resgate)                   AS resgate,
        SUM(captacao) - SUM(resgate)   AS captacao_liquida,
        MAX(patrimonio_liquido)        AS pl,
        MIN(data_competencia)          AS de,
        MAX(data_competencia)          AS ate
    FROM {catalog}.{schema}.cvm_informe_diario
    WHERE data_competencia >= '{data_ini}'
    GROUP BY codigo_classe
)
SELECT
    c.nome_comercial_classe          AS nome,
    p.gestora                        AS gestora,
    p.distribuidor                   AS plataforma,
    m.captacao_liquida               AS cap,
    m.resgate                        AS resg,
    m.pl                             AS pl,
    c.tipo_anbima                    AS estrategia,
    m.de                             AS periodo_de,
    m.ate                            AS periodo_ate
FROM {catalog}.{schema}.anbima_classes_fundo c
JOIN movimento m  ON m.codigo_classe = c.codigo_classe
LEFT JOIN prestador p ON p.codigo_classe = c.codigo_classe
-- recorte de previdencia
WHERE upper(COALESCE(c.nome_comercial_classe, '')) RLIKE 'PREV|PGBL|VGBL'
   OR upper(COALESCE(c.tipo_anbima, '')) LIKE '%PREVID%'
   OR upper(COALESCE(c.nivel1_categoria, '')) LIKE '%PREVID%'
ORDER BY m.captacao_liquida DESC
