# Contexto · Captação · Fundos Abertos (Tivio)

> Documento de handoff do dashboard **Captação · Fundos Abertos**.
> Objetivo: qualquer pessoa (ou outra IA) conseguir entender, rodar e evoluir o
> pipeline sem refazer toda a investigação. Última revisão: **08/2026**.

---

## 1. Visão geral

O dashboard mostra o **ranking de captação líquida de fundos abertos** por
**plataforma** (XP · BTG · Itaú · Bradesco) e **categoria** (Renda Fixa Ativa ·
Renda Fixa · Multimercado), com Top 10 por combinação.

Pipeline atual (100% automático):

```
Databricks (SQL)                 Peers_FundosAbertos.xlsx (Vivian)
      |                                    |
      v                                    v
  DataFrame  ---------- merge por CNPJ ----------
      |
      v
  FUNDS_DATA (JSON)   +   CDI real (daily_cdi_price)   +   datas do cabeçalho
      |
      v  (injeção cirúrgica via regex, sem tocar no design system)
  outputs/dashboard_captacao_fundos_abertos.html
```

Um comando por mês:

```powershell
python atualizar_captacao.py
```

---

## 2. Estrutura de pastas

```
Update_Captacao_Fundos_Abertos/
├── atualizar_captacao.py         # motor: SQL -> merge peers -> CDI -> cabeçalho -> HTML
├── captacao_metrics.py           # transforma linhas em FUNDS_DATA (17 campos/fundo)
├── preparar_peers.py             # Peers_FundosAbertos.xlsx -> peers_fundos_abertos.csv
├── remover_aviso.py              # remove banner "Em breve" e painel "Resumo destaques"
├── Peers_FundosAbertos.xlsx      # de-para CNPJ -> plataforma (mantido pela Vivian)
├── peers_fundos_abertos.csv      # gerado pelo preparar_peers.py
├── .env                          # credenciais Databricks + CDI fallback (NÃO versionar)
├── sql/
│   ├── captacao_fundos_abertos.sql   # query principal (captação/PL/rent/cadastro)
│   └── cdi_periodos.sql              # CDI acumulado 30d/12m/YTD
├── templates/
│   └── dashboard_captacao_fundos_abertos.html   # template (fonte)
└── outputs/
    └── dashboard_captacao_fundos_abertos.html   # arquivo gerado (deploy)
```

---

## 3. Fonte de cada campo (mapa de origem)

| Campo no dashboard | Origem | Observação |
|---|---|---|
| `cap30 / cap12 / capytd` | `marketdata.silver.cvm_informe_diario` | `SUM(captc_dia - resg_dia)` por janela |
| `pl` | `cvm_informe_diario` (`vl_patrim_liq`) | PL do **último registro**, não o maior histórico |
| `rent30 / rent12 / rentytd` | `cvm_informe_diario` (`vl_quota`) | variação da cota entre a data-base e a cota do início do período |
| `cotistas` | `cvm_informe_diario` (`nr_cotst`) | último registro |
| `nome` | `anbima_classes_fundo` / `anbima_fundo` | `nome_comercial_classe`, fallback `nome_comercial_fundo` |
| `categoria` | `anbima_classes_fundo` | derivada de `nivel1_categoria` + `credito_privado` + `tipo_anbima` |
| `benchmark` | `anbima_classes_fundo` | regra: `tipo_anbima` contém "INDEXADO" → Índice; senão CDI |
| `gestor` | `anbima_prestadores_classe` | `codigo_tipo_prestador = 'CO_GESTOR'` |
| `cdi30 / cdi12 / cdiytd` | `daily_cdi_price` | % do benchmark = `rent / cdi_período * 100` |
| **`plat` (plataforma)** | **`Peers_FundosAbertos.xlsx` (Vivian)** | **manual, via CNPJ — ver seção 5** |
| datas do cabeçalho | `cvm_informe_diario` (`MAX(dt_comptc)`) | competência / 12m / YTD |

### Chaves de junção (validadas)
- **CVM ↔ ANBIMA**: `cvm_informe_diario.cnpj_fundo_classe` ↔
  `anbima_classes_fundo.identificador_classe` (ambos normalizados: só dígitos).
- **Classe ↔ Fundo**: `codigo_fundo`.
- **Classe ↔ Gestor**: `codigo_classe` em `anbima_prestadores_classe`.
- **Métricas ↔ Plataforma**: `cnpj` (14 dígitos) ↔ CSV de peers.

---

## 4. Investigação do Databricks (o que existe e o que NÃO existe)

Catálogo `marketdata` tem só: `default`, `gold`, `silver`, `information_schema`.

Tabelas-chave encontradas em `silver`:
- `cvm_informe_diario` → captação, resgate, PL, cota, cotistas (fonte do fluxo).
- `anbima_classes_fundo` → nome, categorias ANBIMA, flags (crédito privado, infra, ESG, exterior).
- `anbima_fundo` → nome comercial do fundo.
- `anbima_prestadores_classe` → prestadores; **não existe `GESTOR`**, só
  `CONTROLADOR`, `CO_GESTOR`, `CUSTODIANTE`, `DISTRIBUIDOR`. Gestor real = `CO_GESTOR`.
- `daily_cdi_price` → `ValorCDI` (anualizado) e `ValorDiaCDI` (fator diário).

**Não existe** no catálogo nenhuma tabela/coluna de **captação por plataforma/canal**.
Os `DISTRIBUIDOR` da ANBIMA não servem: o mesmo fundo aparece em XP+BTG+Itaú+Bradesco
ao mesmo tempo (176 fundos multi-plataforma), o que duplicaria o ranking.

Conclusão: a dimensão **plataforma** é externa (planilha manual da Vivian).

---

## 5. Plataforma = dimensão manual (Vivian Oka)

- Arquivo: **`Peers_FundosAbertos.xlsx`**, aba **`Resumo`**, cabeçalho na **linha 3**
  (`skiprows=2`). Colunas: `NOME_FUNDO`, `CNPJ`, `CLASSE_ANBIMA`, `Plataforma`,
  `Fonte`, `Atualizado`.
- `preparar_peers.py` normaliza (CNPJ com 14 dígitos, plataforma → XP/BTG/Itau/Bradesco)
  e gera `peers_fundos_abertos.csv`.
- Um mesmo **CNPJ pode estar em mais de uma plataforma** → o merge usa `inner` por CNPJ
  e cada combinação vira uma linha.

### Regras de interpretação (importante)
- A captação é a **captação total do fundo** (CVM), não a captação *originada* naquele canal.
- **Não somar** os rankings das plataformas para obter total geral (duplica fundos multi-plataforma).
- Para total geral, **deduplicar por CNPJ**.

---

## 6. Como rodar

### Mensal (rotina normal)
```powershell
# 1) se a Vivian atualizou os canais:
python preparar_peers.py
# 2) gerar o dashboard:
python atualizar_captacao.py
```

Log esperado:
```
[databricks] ~16675 linhas retornadas.
[peers] ~1070 linhas após join plataforma.
[cdi] 30d=1.xx% | 12m=14.xx% | ytd=9.xx%
[inject] FUNDS_DATA substituido (1 ocorrencia). 120 fundos.
[cabecalho] competencia=MM/AAAA | ytd=31/12/AAAA-1 a DD/MM/AAAA
OK [DATABRICKS] -> outputs\dashboard_captacao_fundos_abertos.html
```

### Modo mock (testar sem banco)
No `.env`: `USE_MOCK=true` → gera 120 fundos fictícios.

---

## 7. `.env` (modelo)

```env
USE_MOCK=false
DATABRICKS_HOST=adb-XXXX.azuredatabricks.net
DATABRICKS_PATH=/sql/1.0/warehouses/XXXX
DATABRICKS_TOKEN=coloque_seu_token
# CDI fallback (só usado se a query de CDI falhar):
CDI_MES=0.0113
CDI_12M=0.1482
CDI_YTD=0.0572
```
> Nunca versionar o `.env` nem colar o token em chat. Pode reutilizar o mesmo
> token do Monitor de Novos Fundos.

---

## 8. Detalhes técnicos que evitam retrabalho

- **Data de referência** = `MAX(dt_comptc)` da base (não `current_date()`), pra
  não distorcer janelas quando o informe tem defasagem.
- **PL** = registro mais recente por `ROW_NUMBER()`, não `MAX(vl_patrim_liq)`.
- **CNPJ** sempre normalizado (`regexp_replace('[^0-9]','')` + `zfill(14)`) antes de juntar.
- **CDI acumulado**: `EXP(SUM(LN(1 + ValorDiaCDI))) - 1` (produtório seguro em SQL),
  ancorado na mesma data de referência.
- **Injeção no HTML**: regex troca só `const FUNDS_DATA = [...]` e os 3 textos do
  cabeçalho. Design system, TiView e animações ficam intactos.
- **`~1070` vs `1136`**: a planilha tem 1.136 linhas; ~66 CNPJs não casam (FIDC/FIP/FII
  ou sem informe diário; a SQL filtra `nivel1_categoria IN ('Renda Fixa','Multimercados')`
  e `pl > 0`). Esperado.
- **120 fundos** = Top 10 × 4 plataformas × 3 categorias.

---

## 9. Fase 2 (backlog / oportunidades)

- **KPIs da Visão Geral** e `AB.resumo`: hoje ainda têm texto estático no HTML;
  dá pra calcular automaticamente a partir do `FUNDS_DATA`.
- **CARTEIRAS_TOP3**: composição CVM (CDA) dos Top 3 — automatizar via `vw_cvm_cda_carteira`.
- **COTIZ_MAP** (prazo de cotização): hoje parcial; puxar da coluna D+ da fonte.
- **Público-alvo por fundo**: existe no cadastro CVM (já aparece no Monitor de Novos
  Fundos); traria com um cruzamento por CNPJ.

---

## 10. Pessoas e responsabilidades

- **Renan Chaves** — dono do pipeline, SQL/Python/HTML, deploy do dashboard.
- **Vivian Oka** — mantém o `Peers_FundosAbertos.xlsx` (classificação de plataforma).
- **Time IT/Databricks** — acesso e permissões do SQL Warehouse.
