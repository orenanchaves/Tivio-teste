-- ============================================================
-- Monitor de Novas Ofertas · FII - Tivio Capital
--
-- STATUS: NAO VALIDADO CONTRA O DATABRICKS.
-- Ver ORIGEM_DOS_DADOS.md nesta pasta. Os nomes de tabela e coluna
-- abaixo seguem o padrao dos ambientes que ja rodam (Monitor de Novos
-- Fundos e Captacao), mas a tabela de ofertas em si nao aparece em
-- nenhum SQL existente do projeto - precisa ser confirmada.
--
-- Enquanto nao for confirmada, atualizar_fii.py roda com FONTE=excel,
-- lendo Monitor_FII.xlsx, e o dashboard e regenerado normalmente.
--
-- Placeholders: {catalog} {schema} {data_ini}
-- ============================================================
SELECT
    COALESCE(o.ticker, 'N/A')                      AS ticker,
    date_format(o.data_requerimento, 'dd/MM/yyyy') AS data,
    o.nome_fundo                                   AS fii,
    COALESCE(o.gestora, '')                        AS gestora,
    COALESCE(o.cnpj, '')                           AS cnpj,
    COALESCE(o.valor_mobiliario, 'Cotas de FII')   AS valor_mob,
    COALESCE(o.numero_emissao, 1)                  AS nr_emissao,
    COALESCE(o.tipo_oferta, '')                    AS tipo,
    COALESCE(o.modalidade, '')                     AS modalidade,
    try_cast(o.volume_ofertado AS DOUBLE)          AS volume,
    COALESCE(o.coordenador_lider, '')              AS coord,
    COALESCE(o.status, '')                         AS status,
    COALESCE(o.numero_processo, '')                AS processo,
    COALESCE(o.rito, '')                           AS rito,
    COALESCE(o.observacao, '')                     AS observacao
FROM {catalog}.{schema}.cvm_ofertas_publicas o
WHERE upper(COALESCE(o.valor_mobiliario, '')) LIKE '%FII%'
   OR upper(COALESCE(o.valor_mobiliario, '')) LIKE '%IMOBILI%'
  AND o.data_requerimento >= '{data_ini}'
ORDER BY o.data_requerimento DESC
