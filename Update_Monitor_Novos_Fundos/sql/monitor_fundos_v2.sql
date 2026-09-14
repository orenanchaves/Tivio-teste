-- ============================================================
-- Monitor de Novos Fundos - Tivio Capital - v2
-- Fonte: ANBIMA / CVM (Databricks)
--
-- v2 = v1 + os campos que a planilha historica
-- (Monitor_Fundos_Tivio.xlsm, aba _DADOS) tem e o monitor nao tinha.
-- Ver DIAGNOSTICO_AGOSTO.md para o porque de cada um.
--
-- Placeholders preenchidos por atualizar_monitor.py:
--   {catalog}   -> marketdata
--   {schema}    -> silver
--   {link_base} -> URL base da consulta publica da CVM
--   {data_ini}  -> data inicial do recorte (AAAA-MM-DD)
--   cvm_tabela  -> catalogo.schema.tabela do cadastro da CVM
--                   (so quando CVM_CADASTRO esta definido no .env)
--
-- ------------------------------------------------------------
-- O CONTRATO DE COLUNAS DE monitor_metrics.COLS E PRESERVADO.
-- As colunas novas entram DEPOIS das 25 originais; _linha() le
-- apenas o que esta em COLS, entao o dashboard nao quebra.
--
-- ------------------------------------------------------------
-- O QUE MUDA EM RELACAO A v1
--
-- 1. data_constituicao deixa de mentir
--    v1 usava af.data_vigencia_fundo, que e a data da VERSAO VIGENTE
--    do cadastro, nao a constituicao: em 596 de 596 linhas ela e
--    posterior ou igual ao inicio da classe (mediana 178 dias depois).
--    Em v2 esse valor vai para a coluna propria data_vigencia_cadastro
--    e data_constituicao so e preenchida quando o cadastro da CVM
--    estiver disponivel. Sem ele, sai vazia - preferivel a errada.
--
-- 2. exclusivo deixa de depender so do nome
--    v1 marcava 0 de 47 classes em agosto; a planilha marca 293 de 718.
--    v2 soma tres sinais independentes (nome, razao social e a
--    combinacao condominio fechado + publico profissional/qualificado
--    sem classe irma), e ainda expone exclusivo_origem para auditar
--    qual regra disparou.
--
-- 3. Classes irmas do mesmo fundo
--    A planilha tem Existe_Classe_Prateleira e Classes_Prateleira_Irmas.
--    v2 deriva ambos por window function sobre codigo_fundo, o que
--    tambem permite auditar o grao (hoje 596 linhas / 596 CNPJs).
--
-- 4. tipo_estrutura (Prateleira / Mandato / Solucao Dedicada)
--    Aproxima Tipo_Estrutura da planilha (Prateleira 70, Mandato 33,
--    Solucao Dedicada 2 em agosto/2026). E heuristica - ver nota no
--    CASE - e vem acompanhada de tipo_estrutura_origem.
--
-- 5. ano_ref explicito
--    v1 devolvia so mes_ref, o que fez o diagnostico somar agosto de
--    2024, 2025 e 2026 num unico numero (47). Com ano_ref na mao o
--    recorte mensal fica inequivoco.
--
-- 6. Bloco opcional do cadastro da CVM
--    Delimitado pelos marcadores CVM_INI / CVM_ELSE / CVM_FIM, que
--    sql_cvm.montar() resolve conforme CVM_CADASTRO no .env, para a
--    query continuar rodando sem a permissao. Com a permissao, ele
--    traz situacao (Fase Pre-Operacional), a data de registro na CVM
--    e o exclusivo oficial - os tres campos que faltam para bater
--    com a planilha.
-- ============================================================
WITH gestores_por_fundo AS (
    SELECT
        codigo_fundo,
        concat_ws(' / ', sort_array(collect_set(nome_comercial))) AS gestora
    FROM {catalog}.{schema}.anbima_prestadores_fundo
    WHERE codigo_tipo_prestador = 'GESTOR'
    GROUP BY codigo_fundo
),
administradores_por_fundo AS (
    SELECT
        codigo_fundo,
        concat_ws(' / ', sort_array(collect_set(nome_comercial))) AS administrador
    FROM {catalog}.{schema}.anbima_prestadores_fundo
    WHERE upper(codigo_tipo_prestador) LIKE 'ADMIN%'
    GROUP BY codigo_fundo
),
perfil_por_classe AS (
    SELECT
        codigo_classe,
        concat_ws(' / ', sort_array(collect_set(trim(tipo_investidor))))
            AS tipo_investidor
    FROM {catalog}.{schema}.anbima_perfil_classe
    WHERE tipo_investidor IS NOT NULL
      AND trim(tipo_investidor) <> ''
    GROUP BY codigo_classe
),
taxa_administracao AS (
    SELECT
        codigo_classe,
        MAX(try_cast(valor_percentual AS DOUBLE)) AS valor_percentual
    FROM {catalog}.{schema}.anbima_taxas_classe
    WHERE valor_percentual IS NOT NULL
    GROUP BY codigo_classe
),
taxa_performance AS (
    SELECT
        codigo_classe,
        MAX(try_cast(valor_percentual AS DOUBLE)) AS valor_percentual,
        MAX(nullif(trim(indice_referencia), '')) AS indice_referencia
    FROM {catalog}.{schema}.anbima_detalhes_taxa_performance_classe
    WHERE valor_percentual IS NOT NULL
      AND try_cast(valor_percentual AS DOUBLE) > 0
    GROUP BY codigo_classe
),
-- ------------------------------------------------------------
-- NOVO: classes irmas do mesmo fundo
-- Reproduz Existe_Classe_Prateleira / Classes_Prateleira_Irmas.
-- Na base atual o resultado e 1 classe por fundo em 100% dos casos,
-- o que confirma que nao ha agrupamento a desfazer - mas a coluna
-- passa a provar isso a cada rodada, em vez de exigir a conferencia
-- manual que o diagnostico precisou fazer.
-- ------------------------------------------------------------
classes_por_fundo AS (
    SELECT
        codigo_fundo,
        COUNT(*) AS qtd_classes,
        concat_ws(
            ' | ',
            sort_array(collect_set(nome_comercial_classe))
        ) AS classes_irmas
    FROM {catalog}.{schema}.anbima_classes_fundo
    GROUP BY codigo_fundo
),
-- ------------------------------------------------------------
-- NOVO: exclusivo por tres sinais, nao so pelo nome
-- A regra da v1 (LIKE '%EXCLUSIV%') nao disparou em nenhuma das 47
-- linhas de agosto. Aqui cada sinal e avaliado separado e a origem
-- fica registrada, para dar para medir a cobertura de cada regra.
-- ------------------------------------------------------------
exclusivo_por_classe AS (
    SELECT
        c.codigo_classe,
        upper(COALESCE(c.nome_comercial_classe, '')) LIKE '%EXCLUSIV%'
            AS por_nome,
        upper(COALESCE(c.razao_social_classe, '')) LIKE '%EXCLUSIV%'
            AS por_razao_social,
        (
            upper(COALESCE(c.forma_condominio, '')) LIKE '%FECHADO%'
            AND upper(COALESCE(pf.tipo_investidor, '')) RLIKE
                'PROFISSIONAL|QUALIFICADO'
            AND COALESCE(cf.qtd_classes, 1) = 1
        ) AS por_estrutura
    FROM {catalog}.{schema}.anbima_classes_fundo c
    LEFT JOIN perfil_por_classe pf
        ON pf.codigo_classe = c.codigo_classe
    LEFT JOIN classes_por_fundo cf
        ON cf.codigo_fundo = c.codigo_fundo
)
-- {{CVM_INI}}
-- ------------------------------------------------------------
-- OPCIONAL: cadastro da CVM (catalogo restrito)
-- Preencher CVM_CADASTRO no .env com catalogo.schema.tabela e
-- conferir os nomes das colunas abaixo com buscar_cadastro_cvm.py.
-- Sem a variavel, atualizar_monitor.py remove este bloco inteiro.
-- ------------------------------------------------------------
, cadastro_cvm AS (
    SELECT
        regexp_replace(COALESCE(cnpj_fundo, ''), '[^0-9]', '') AS cnpj_digitos,
        cvm_status,
        data_registro_cvm,
        is_exclusive
    FROM {cvm_tabela}
)
-- {{CVM_FIM}}
SELECT
    -- ---------- as 25 colunas do contrato de monitor_metrics.COLS ----------
    COALESCE(c.nome_comercial_classe, c.razao_social_classe, '') AS fund_name,
    COALESCE(gf.gestora, '') AS gestora,
    COALESCE(af.tipo_fundo, c.categoria_cvm, '') AS tipo,
    concat_ws(
        ' | ',
        nullif(COALESCE(c.tipo_anbima, c.nivel2_categoria, ''), ''),
        nullif(COALESCE(pf.tipo_investidor, ''), ''),
        CASE WHEN ex.por_nome OR ex.por_razao_social OR ex.por_estrutura
             THEN 'Exclusivo' END
    ) AS segmento_detalhe,
    COALESCE(c.tipo_anbima, c.nivel2_categoria, '') AS categoria_anbima,

    -- situacao: vazia sem o cadastro da CVM (v1 ja se comportava assim)
-- {{CVM_INI}}
    COALESCE(cv.cvm_status, '') AS situacao,
-- {{CVM_ELSE}}
    '' AS situacao,
-- {{CVM_FIM}}

    date_format(c.data_inicio_atividade_classe, 'dd/MM/yyyy') AS data_registro,

    -- MUDANCA: sem o cadastro da CVM esta coluna sai VAZIA em vez de
    -- receber a data de vigencia, que nao e a constituicao.
-- {{CVM_INI}}
    date_format(cv.data_registro_cvm, 'dd/MM/yyyy') AS data_constituicao,
-- {{CVM_ELSE}}
    '' AS data_constituicao,
-- {{CVM_FIM}}

    COALESCE(af.identificador_fundo, '') AS cnpj,
    CASE
        WHEN pf.tipo_investidor IS NULL
          OR trim(pf.tipo_investidor) = ''
          OR upper(trim(pf.tipo_investidor)) IN ('ND', 'N/D', 'NA')
        THEN 'N/D'
        ELSE trim(pf.tipo_investidor)
    END AS publico_alvo,
    CASE
-- {{CVM_INI}}
        WHEN cv.is_exclusive THEN 'S'
-- {{CVM_FIM}}
        WHEN ex.por_nome OR ex.por_razao_social OR ex.por_estrutura THEN 'S'
        ELSE 'N'
    END AS exclusivo,
    CAST(year(c.data_inicio_atividade_classe) AS STRING) AS campo_11,
    COALESCE(c.forma_condominio, '') AS condominio,
    COALESCE(c.nome_comercial_classe, '') AS subclasse,
    concat(
        CASE WHEN lower(COALESCE(c.credito_privado, ''))
                  IN ('s', 'sim', 'true', '1') THEN '1' ELSE '0' END,
        CASE WHEN upper(COALESCE(af.tipo_fundo, '')) LIKE '%FIDC%'
                  OR upper(COALESCE(c.categoria_cvm, '')) LIKE '%FIDC%'
             THEN '1' ELSE '0' END,
        CASE WHEN lower(COALESCE(c.infraestrutura, ''))
                  IN ('s', 'sim', 'true', '1') THEN '1' ELSE '0' END,
        CASE WHEN upper(COALESCE(c.nome_comercial_classe, ''))
                  RLIKE 'PREV|PGBL|VGBL|FLEXPREV'
                  OR upper(COALESCE(c.tipo_anbima, '')) LIKE '%PREVID%'
                  OR upper(COALESCE(c.nivel1_categoria, '')) LIKE '%PREVID%'
                  OR lower(COALESCE(pf.tipo_investidor, '')) LIKE '%previd%'
             THEN '1' ELSE '0' END,
        CASE WHEN lower(COALESCE(c.investimento_exterior, ''))
                  IN ('s', 'sim', 'true', '1')
                  OR upper(COALESCE(c.nome_comercial_classe, ''))
                     RLIKE 'GLOBAL|INTERNACIONAL|EXTERIOR'
                  OR upper(COALESCE(c.tipo_anbima, '')) LIKE '%EXTERIOR%'
             THEN '1' ELSE '0' END,
        CASE WHEN lower(COALESCE(c.fundo_esg, ''))
                  IN ('s', 'sim', 'true', '1') THEN '1' ELSE '0' END
    ) AS segmentos_bitmask,
    CASE
        WHEN length(regexp_replace(
                COALESCE(af.identificador_fundo, ''), '[^0-9]', '')) = 14
        THEN concat('{link_base}', regexp_replace(
                COALESCE(af.identificador_fundo, ''), '[^0-9]', ''))
        ELSE ''
    END AS link_cvm,
    month(c.data_inicio_atividade_classe) AS mes_ref,
    COALESCE(gf.gestora, '') AS gestor_juridico,
    COALESCE(ad.administrador, '') AS administrador,
    COALESCE(c.nivel1_categoria, '') AS categoria_n1,
    CASE
        WHEN upper(COALESCE(c.tipo_anbima, '')) RLIKE 'CRÉDITO LIVRE|CREDITO LIVRE'
        THEN 'Crédito Livre'
        WHEN upper(COALESCE(c.tipo_anbima, '')) LIKE '%GRAU DE INVESTIMENTO%'
        THEN 'Grau de Investimento'
        WHEN upper(COALESCE(c.tipo_anbima, '')) LIKE '%SOBERANO%'
        THEN 'Soberano'
        ELSE ''
    END AS risco_credito,
    COALESCE(c.nivel2_categoria, '') AS duracao,
    'Nao' AS registro,
    tx.valor_percentual AS taxa_adm,
    tp.valor_percentual AS taxa_perf,

    -- ---------- colunas novas da v2 (ignoradas por COLS) ----------

    -- recorte temporal inequivoco: foi a falta disso que produziu o "47"
    year(c.data_inicio_atividade_classe)  AS ano_ref,

    -- a data que a v1 chamava de constituicao, agora com o nome certo
    date_format(af.data_vigencia_fundo, 'dd/MM/yyyy') AS data_vigencia_cadastro,

    -- grao: prova a cada rodada que nao ha classes irmas a agrupar
    COALESCE(cf.qtd_classes, 1) AS qtd_classes_no_fundo,
    CASE WHEN COALESCE(cf.qtd_classes, 1) > 1 THEN 'Sim' ELSE 'Nao' END
        AS existe_classe_irma,
    COALESCE(cf.classes_irmas, '') AS classes_irmas,

    -- auditoria da flag exclusivo: qual sinal disparou
    concat_ws(
        '+',
        CASE WHEN ex.por_nome THEN 'nome' END,
        CASE WHEN ex.por_razao_social THEN 'razao' END,
        CASE WHEN ex.por_estrutura THEN 'estrutura' END
    ) AS exclusivo_origem,

    -- aproximacao de Tipo_Estrutura da planilha.
    -- HEURISTICA: a planilha classifica por regra propria que nao esta
    -- documentada no arquivo. Conferir a distribuicao contra a aba
    -- _DADOS antes de usar em decisao (agosto/2026: Prateleira 70,
    -- Mandato 33, Solucao Dedicada 2).
    CASE
        WHEN ex.por_nome OR ex.por_razao_social THEN 'Solução Dedicada'
        WHEN upper(COALESCE(c.forma_condominio, '')) LIKE '%FECHADO%'
             AND upper(COALESCE(pf.tipo_investidor, ''))
                 RLIKE 'PROFISSIONAL|QUALIFICADO'
        THEN 'Mandato'
        WHEN upper(COALESCE(pf.tipo_investidor, '')) LIKE '%GERAL%'
        THEN 'Prateleira'
        ELSE 'Mandato'
    END AS tipo_estrutura,

    -- feeder: a planilha mantem 54 de 718; aqui vira coluna propria
    CASE
        WHEN upper(COALESCE(c.nome_comercial_classe, ''))
             RLIKE 'EM COTAS|\\bFIC\\b'
        THEN 'Sim' ELSE 'Nao'
    END AS feeder,

    tp.indice_referencia AS indice_performance,
    c.codigo_classe,
    c.codigo_fundo

FROM {catalog}.{schema}.anbima_classes_fundo c
LEFT JOIN {catalog}.{schema}.anbima_fundo af
    ON af.codigo_fundo = c.codigo_fundo
LEFT JOIN exclusivo_por_classe ex
    ON ex.codigo_classe = c.codigo_classe
LEFT JOIN classes_por_fundo cf
    ON cf.codigo_fundo = c.codigo_fundo
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
-- {{CVM_INI}}
LEFT JOIN cadastro_cvm cv
    ON cv.cnpj_digitos = regexp_replace(
        COALESCE(af.identificador_fundo, ''), '[^0-9]', '')
-- {{CVM_FIM}}
WHERE c.data_inicio_atividade_classe >= '{data_ini}'
ORDER BY c.data_inicio_atividade_classe DESC
