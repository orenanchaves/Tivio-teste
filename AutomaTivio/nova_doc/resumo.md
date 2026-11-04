
# API Carteira — Endpoints cadastrados no Bruno

> Coleção Bruno: `tivio-bruno-http-requests` → pasta `TLDR/`
> Base URL: `https://wa-tivio-tldr-brsouth.azurewebsites.net`
> Autenticação: Azure AD (token de usuário, via `refresh_tldr_token.py` → variável `access_token_tldr` nos ambientes local/homologação/produção). Client credentials **não funciona** — a API exige token delegado de usuário.
> Doc viva da API: `GET /openapi.json` (protegido por auth, mas acessível com o mesmo token).

Esta nota documenta os endpoints já testados e cadastrados no Bruno, o dado que cada um retorna e um exemplo de uso real com o fundo **Banks (código 940)**. Objetivo: servir de referência para migrar partes do relatório que hoje usam planilha para consumirem esta API diretamente.

---

## 1. Visão geral do fundo

**`GET /v1/carteira/fundos/{codigo}/visao-geral`**

Retorna metadados gerais do fundo, incluindo o **benchmark** usado para comparação de rentabilidade.

Exemplo (fundo 940 — Banks):
```
GET /v1/carteira/fundos/940/visao-geral
```
Campo relevante no retorno: `benchmark_symbol` → `"CDI"` para o fundo 940.

Uso: primeiro passo antes de buscar a série do benchmark — descobre qual símbolo usar na chamada de benchmarks (seção 4).

---

## 2. Cotas do fundo (série diária)

**`GET /v1/carteira/fundos/{codigo}/cotas?inicio=AAAA-MM-DD`**

Retorna a série histórica diária de cota do fundo a partir da data informada.

Exemplo:
```
GET /v1/carteira/fundos/940/cotas?inicio=2026-07-01
```
Retorna lista de `{data, valor}` (ou equivalente) — valores em escala de cota (ex.: ~R$5), não diretamente comparáveis ao índice de benchmark.

---

## 3. Emissores e alocação

**`GET /v1/carteira/fundos/{codigo}/emissores`** — concentração por emissor.

**`GET /v1/carteira/fundos/{codigo}/alocacao`** — alocação por tipo de ativo.

Exemplo:
```
GET /v1/carteira/fundos/940/emissores
GET /v1/carteira/fundos/940/alocacao
```

---

## 4. Série do benchmark

**`GET /v1/carteira/benchmarks?symbol={symbol}&inicio=AAAA-MM-DD&fundo={codigo}`**

Retorna a série histórica diária do índice de benchmark (ex.: CDI), no mesmo intervalo de datas do fundo.

Exemplo:
```
GET /v1/carteira/benchmarks?symbol=CDI&inicio=2026-07-01&fundo=940
```
Valores em escala de índice (ordem de grandeza bem maior que a cota do fundo — por isso não dá pra comparar bruto, precisa normalizar — ver seção 5).

---

## 5. Calculadora de retorno acumulado (genérica)

**`POST /v1/fundcalc/cum-return`**

Corpo:
```json
{
  "dates": ["2026-07-01", "2026-07-02", "..."],
  "values": [5.01, 5.02, "..."]
}
```
Retorna o retorno acumulado `(vi / v0) - 1` para cada ponto da série — é uma calculadora pura, **não consulta banco de dados**, por isso funciona igualmente bem para a cota do fundo (escala ~R$5) e para o índice de benchmark (escala ~10^11): ambos são normalizados para a mesma base comparável (retorno % desde o início).

> ⚠️ Existe também `/v1/fundcalc/by-fund/cum-return`, que busca a série do fundo direto no banco (sem precisar informar `dates`/`values`), mas retorna **403** para o usuário atual — exige acesso à tabela Databricks `fund_cadastro` que não temos. Use sempre a rota genérica acima, montando a série manualmente a partir dos passos 2 e 4.

---

## 6. Fluxo completo — série de rentabilidade Fundo x Benchmark

Para montar o gráfico de linha (fundo x benchmark), encadear:

1. `GET /v1/carteira/fundos/{codigo}/visao-geral` → pega `benchmark_symbol`
2. `GET /v1/carteira/fundos/{codigo}/cotas?inicio=...` → série bruta do fundo
3. `POST /v1/fundcalc/cum-return` com a série do passo 2 → retorno acumulado do fundo
4. `GET /v1/carteira/benchmarks?symbol={benchmark_symbol}&inicio=...&fundo={codigo}` → série bruta do benchmark
5. `POST /v1/fundcalc/cum-return` com a série do passo 4 → retorno acumulado do benchmark

Resultado final: duas séries de `(data, retorno_acumulado)` no mesmo eixo de datas, prontas para o gráfico de linha.

Testado de ponta a ponta com o fundo 940 (Banks), período 2026-07-01 a 2026-10-29 — 85 pontos diários, dados reais validados.

### Onde ver isso rodando no Bruno
- **`TLDR/get-serie-rentabilidade-fundo-x-benchmark.bru`** — versão automática: um único request que executa os 5 passos via pre-request/post-response scripts e mostra o resultado combinado (`dates`, `retorno_acumulado_fundo`, `retorno_acumulado_benchmark`) na aba Response.
- **`TLDR/Serie Rentabilidade (passo a passo)/`** — versão didática: 5 requests sequenciais (`1-visao-geral.bru` … `5-cum-return-benchmark-comparativo.bru`), cada um com sua própria resposta real visível, útil para entender/depurar cada etapa isoladamente. Variáveis padrão (`serie_codigo_fundo=940`, `serie_inicio=2026-07-01`) ficam no `folder.bru` da pasta.

---

## Observações para a migração (planilha → API)

- Tokens são **delegados de usuário** (Azure AD), não client-credentials — ok para rodar manualmente, mas é preciso confirmar com o admin da API se existe (ou pode ser criado) um modo de acesso tipo aplicação/service-principal antes de automatizar geração agendada de relatórios.
- Recomendado: ao migrar uma parte do relatório, manter a planilha como fallback temporário e comparar os dados lado a lado antes de confiar 100% na API (mesmo padrão usado neste projeto para o comparativo manual vs. live).
