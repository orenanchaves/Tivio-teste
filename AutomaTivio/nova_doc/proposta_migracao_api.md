# Proposta: trocar a 1ª fonte (`dados_mensais.xlsx`) pela API TLDR

> Escopo: só a **fonte de dados de mercado** (cotas, PL, benchmark, carteira, feriados, DePara).
> Comentários, taxas, spreads, `fundos.yml` e todo o resto do fluxo ficam como estão.
> Base: `nova_doc/resumo.md`, `nova_doc/api-tldr.html` e os `.bru` de `TLDR/`.
> Ainda **não foi chamada** a API (sem token neste ambiente): o que está marcado
> "a validar" precisa ser conferido no Bruno antes de implementar.

## 1. O que a planilha entrega hoje

`loaders/planilha.py::ler_dados_mensais` devolve um dicionário que o `Calc`
(`calculators/metricas.py`) consome:

| Chave | Aba | Colunas | Quem usa |
|---|---|---|---|
| `depara` | DePara | carteira, cnpj, quantum, benchmark, mesa, cota_inicial, data_inicial | `engine/cadastro.py` |
| `indices` | Benchmark A:D | nome, data, valor | `Calc.serie_indice` (CDI, IPCA…) |
| `fundos` | Benchmark F:I | nome, data, **pl**, **cota** | `Calc.serie_fundo`, data base |
| `carteira` | Base Carteira | Carteira, Data, Emissor, Setor, Setor Aj., Tipo, Tipo aj., Rating Externo, Book, HGHY, FIDC, Taxa, duration, Exposição | `Calc.carteira` |
| `feriados` | feriados | data | `Calc.workday/du` |

Vantagem de manter esse contrato: **basta um novo loader que devolva o mesmo
dicionário**. `Calc`, `Contexto`, renderizadores e exportadores não mudam.

## 2. O que a API cobre

| Necessidade | Endpoint | Cobertura |
|---|---|---|
| Cota do fundo (série diária) | `GET /v1/carteira/fundos/{cod}/cotas?inicio=&signoff=false` | ✅ |
| Cotas de vários fundos | `POST /v1/fundcalc/by-funds/cotas` (até 100 CNPJs) | ✅ (por CNPJ) |
| Benchmark do fundo | `GET /v1/carteira/fundos/{cod}/visao-geral` → `benchmark_symbol` | ✅ |
| Série do benchmark (CDI…) | `GET /v1/carteira/benchmarks?symbol=&inicio=&fundo=` | ✅ (valor em escala de índice, igual à planilha) |
| Rentabilidade pronta (MTD, YTD, 12M…) | `GET /v1/carteira/rentabilidade/fundos?data=&ultima_cota=true` e `POST /v1/fundcalc/by-fund/period-returns` | ✅ útil como **conferência** (ver §5) |
| Alocação (setor, classe, rating, book, gestor, estratégia) | `GET /v1/carteira/fundos/{cod}/alocacao?data=&visao=expandida` | ✅ parcial |
| Emissores | `GET /v1/carteira/fundos/{cod}/emissores` | ✅ |
| Última data disponível | `GET /v1/carteira/referencia` | ✅ define a data base |
| Sign-off de risco | `GET /v1/carteira/fundos/{cod}/signoff` | ✅ governança |
| Status do motor | `GET /v1/carteira/status` | ✅ pré-checagem |
| **PL** (série) | — | ❓ **a validar**: não aparece no resumo; pode vir em `visao-geral` ou em `rentabilidade/fundos`. |
| **Feriados** | — | ❌ sem endpoint no resumo. Manter lista local ou usar `adf` `is_bizday`/`list_bizdays`. |
| **DePara** (CNPJ, cota inicial, data inicial) | — | ⚠️ parcial: `visao-geral` pode trazer CNPJ/código; `cota_inicial`/`data_inicial` a validar (senão derivar da 1ª cota da série). |
| Posição linha a linha (Taxa, duration, Exposição por ativo) | — | ❌ **gap principal**: a API devolve **agregados** (por setor/rating…), não as linhas. |

### O gap da carteira

`Calc.carteira` hoje parte das linhas e agrega: carrego (`Σ Taxa×Exposição/PL`),
duration (`Σ duration×Exposição/PL/252`), cortes cruzados (`Book×Tipo aj.`,
`HGHY×Tipo aj.`, `Rating×Book×Tipo aj.`, `Tipo aj.×Setor×FIDC`).
A rota `/alocacao` entrega `exposure` (R$) e `pct` (fração do PL) por balde, mas
**cortes cruzados, carrego e duration não estão no resumo**. Precisa-se ver o
JSON real: se `/alocacao` e `/emissores` não trazem taxa/duration, esses números
(carrego, duration) e os cruzamentos usados nas páginas Saiba mais, previdência e
Crédito Estruturado ficam sem fonte.

## 3. Proposta em fases (menor risco primeiro)

**Fase 0 — Validar (1 dia).** No Bruno, com o Banks (940), baixar e guardar o JSON de
`visao-geral`, `cotas`, `benchmarks`, `alocacao`, `emissores`, `rentabilidade/fundos`.
Responder: onde está o PL? há CNPJ/cota inicial? `alocacao` tem Taxa/duration/Book/Tipo aj.?
Existe acesso tipo aplicação (service principal)? (hoje só token de usuário.)

**Fase 1 — Cotas, PL e benchmark (alto valor, baixo risco).**
- Novo `loaders/api_tldr.py` (cliente + `ler_dados_api()` que devolve `fundos` e `indices` no formato atual).
- `configs/edicao.yml`: `entradas.fonte: planilha | api` (padrão `planilha`).
- Planilha continua para `depara`, `carteira` e `feriados`; só `fundos`/`indices` vêm da API.
- Mapeamento: DePara `carteira` → código Maravi → `/cotas`; `benchmark` → `/benchmarks`.

**Fase 2 — Data base e feriados.** `GET /v1/carteira/referencia` + `signoff` definem a
data base (hoje é `max(data)` da planilha). Feriados: manter local até haver fonte.

**Fase 3 — Carteira (depende da Fase 0).** Se a API entregar o necessário:
`loaders` passa a montar a carteira a partir de `/alocacao` + `/emissores`, e `Calc.carteira`
aceita agregados prontos. Se não entregar carrego/duration/cruzamentos: pedir ao time
da API um endpoint de **posições** (linhas) ou manter a Base Carteira na planilha.

**Fase 4 — Desligar a planilha** só depois de duas edições com diferença zero.

## 4. Autenticação e execução

- Token Entra ID **delegado** (`az login` / `DefaultAzureCredential`, escopo
  `api://ae37bc8e-f16d-47fb-99ab-9d3dd0cc2201/.default`), válido ~1h. Serve para rodar manualmente;
  para agendar, pedir ao admin um modo service principal.
- Credenciais nunca no código/`.env` versionado (mesmo cuidado já adotado).
- Erros: 401 renova token; 503 tenta de novo; 422/404 → log com aviso e **cai na planilha**
  (padrão `viaApiOuReserva` do Informativo).
- Sign-off: usar o padrão (`signoff` ligado) para publicar; `signoff=false` só em teste.
  Sem sign-off o fundo vem vazio — o pipeline deve registrar aviso, não gerar relatório zerado.

## 5. Validação

`python run.py --conferir` com `fonte: api` e comparar com `fonte: planilha`:
cotas, PL e benchmark por fundo/data; rentabilidade (mês, ano, 12m, início) contra
`/rentabilidade/fundos`; depois `docs/conciliar_com_pptx.py` deve continuar **58/58**.
Atenção: o `Calc` usa janelas por dias úteis (`workday(db,-251)`); a API pode
contar de outro jeito, então comparar sempre pelo número final do relatório.

## 6. Riscos

1. Carteira (carrego/duration/cruzamentos) sem fonte equivalente — maior risco.
2. Sign-off pode atrasar a data base frente à planilha.
3. Token de usuário impede agendamento.
4. `cota_inicial`/`data_inicial` (rentabilidade desde o início) podem não existir.
5. Dependência de rede/disponibilidade → manter fallback para planilha.

## 7. Próximo passo sugerido

Rodar a Fase 0 e trazer os JSONs de `alocacao` e `visao-geral` do 940; com eles fecho
o mapeamento campo a campo e implemento a Fase 1.

---

# Atualização (29/10) — testes reais com o Banks (940), data base 2026-09-30

Token obtido pelo `az` (mesma identidade do `DefaultAzureCredential`): **funciona**. Todas as rotas abaixo responderam 200.

## Decisões acordadas
- **DePara novo** (`nome`, `id_portfolio`): o código Maravi é a única chave da API. CNPJ, benchmark e data de início passam a vir de `visao-geral`.
- **Data base dinâmica** (parâmetro `--data-base`, ou o último fechamento de mês): a edição é sempre o fechamento do mês.
- **`signoff` parametrizável** (`edicao.yml` → `api.signoff: true|false`). Futuro: só gerar quando `GET /fundos/{cod}/signoff` disser `aprovado: true`.
- **Feriados saem**: não há mais conta de dias úteis para a rentabilidade.

## O que `visao-geral?data=&signoff=` entrega (confirmado)
`cnpj`, `fund_name`, `benchmark_symbol`, `official_initial_date` (2009-04-30), `cota_atual`, `pl_atual`, `last_date`,
`rent_{dia,mtd,ytd,6m,12m,24m,inception}`, `pct_bench_{dia,mtd,ytd,6m,12m,24m,inception}`,
`captacao_liq_*`, `peer_rank_*`, `vol_aa`, `var_95_bps`, `var_99_*`, `sharpe_12m`, `max_drawdown_12m`.

## Conferência contra a planilha (Banks)
| Métrica | Planilha | API | |
|---|---|---|---|
| Mês | 1,0830% / 100,042% CDI | 1,0830% / 100,042% | ✅ idêntico |
| Ano | 10,541% / 100,283% | 10,541% / 100,283% | ✅ idêntico |
| 12m | 14,529% / 100,346% | 14,529% / 100,346% | ✅ idêntico |
| 24m | 30,06% / 100,85% | 29,95% / 100,846% | ⚠️ difere ~0,1 p.p. (janela diferente: a planilha usa 503 dias úteis) |
| 36m | 45,38% / 102,56% | **não existe** | ❌ |
| Desde o início | 450,56% / 108,72% | `rent_inception = null` | ❌ vem nulo |
| PL | 1.826.931.618,96 | 1.828.531.134,42 | ⚠️ difere (conferir qual data/cota a planilha usou) |
| PL médio 12m / desde o início | calculado | **não existe** | ❌ |

## Pontos de atenção descobertos
1. **Nem tudo some do cálculo**: o `visao-geral` não traz 36m, `inception` (nulo) nem PL médio. Para o relatório continuar igual, ainda
   precisamos da **série de cotas e PL** (`/cotas?inicio=`). Ela existe desde a data inicial (4.396 pontos, cota inicial 1,0 em 2009-04-30)
   e permite calcular `inception`, 36m e PL médio localmente. O PL na série vem **em R$ milhões** (1829,02), no `visao-geral` em reais.
2. **O gráfico de histórico** (`Calc.historico`, `Contexto` linhas 287-320) precisa da série de cotas **e** do CDI — continua usando série.
3. **Série vai além da data base** (até hoje, 29/10): sempre cortar em `<= data_base`.
4. **`/benchmarks` volta `[]` se `signoff` não for passado `false`** em fundo sem aprovação (testado: sem o parâmetro = vazio; com `signoff=false` = série). O loader deve sempre mandar `signoff` explícito.
5. `/signoff?data=2026-09-30` hoje: `aprovado: false`, `cota_aprovada: true`, `liberada: true` — ou seja, setembro ainda **não** tem sign-off do Banks; com `signoff=true` o relatório sairia vazio.
6. 24m diverge da planilha: decidir se o relatório adota o número da API (recomendado, é a fonte oficial) e se a conciliação 58/58 aceita essa diferença.
7. Rentabilidade por classe diferente (`cotas_rentabilidade` do HGD30/HYD60) precisa do código Maravi da outra classe no DePara novo.

## Design resultante
```
DePara novo (id_portfolio)  ─►  GET visao-geral (data base, signoff)  ─► rent_*, pct_bench_*, cnpj, benchmark, data inicial, pl_atual
                            ─►  GET cotas       (desde a data inicial, corta na data base) ─► histórico, inception, 36m, PL médio
                            ─►  GET benchmarks  (symbol do visao-geral, signoff explícito) ─► histórico do CDI
                            ─►  GET alocacao / emissores ─► carteira (a validar, Fase 3)
```
Autenticação: `azure-identity` (`DefaultAzureCredential`), escopo `api://ae37bc8e-f16d-47fb-99ab-9d3dd0cc2201/.default`; renovar o token a cada ~50 min.

## Atualização 2 — `/posicoes` resolve o gap da carteira
`GET /v1/carteira/fundos/{cod}/posicoes?data=&visao=expandida&signoff=` devolve a **posição linha a linha**
(`issuer`, `sector`, `instrument_class`, `book_name`, `exposure`, `pct_nav`, `spread` (em %), `duration` (anos), `ref_date`).
Carrego e duration batem com a planilha. Não vêm: `Rating Externo` por linha, `Tipo aj.`, `Setor Aj.`, `HGHY`, `FIDC`;
e a taxonomia de setor é outra (Banco de Varejo… × Financeiro). O mapeamento `portfolio_id` sai de
`GET /v1/carteira/rentabilidade/fundos` casando por CNPJ (24/24 fundos casaram).
Detalhe fundo a fundo: `nova_doc/comparativo_api_vs_planilha.xlsx` (gerado por `python docs/comparar_api_planilha.py`).

## Divergências conhecidas (mantidas de propósito, com ciência do time) — dados de 30/09/2026
| Fundo | Tema | Planilha | API |
|---|---|---|---|
| Top Manager Global | Benchmark | MSCI ACWI | MSCI + Dólar 2D (rentabilidade ~1 p.p. diferente) |
| Esplanada | Benchmark | IMA-B 5 | IMA-B (% do benchmark: mês 50,0% × 31,9%) |
| Legacy | PL | — | ≈ −90% de diferença; cotas e carteira praticamente iguais |
| Todos | Rent. 36m e desde o início | calculada | agora vêm da API (`rent_36m`, `rent_inception`); nulos só se o fundo for mais novo que o período |
| Todos | Sign-off | — | `signoff=false` (Risco ainda não aprovou; em teste) |

Também registradas na aba **Divergências conhecidas** do `comparativo_api_vs_planilha.xlsx`.

## Implementação (Fase 1)

- `loaders/api_tldr.py` devolve o mesmo dicionário da planilha (+ `rent_api`).
- Liga em `configs/edicao.yml`: `entradas.fonte: api` (padrão `planilha`), `signoff`, `de_para_taxonomia`. Se a API falhar, cai na planilha com aviso. Os fundos e ids vêm de `configs/fundos.yml` (`id_portfolio`, `mesa`, `id_carteira_expandida`); sem id, o fundo fica fora da API com aviso.
- Data base: `--data-base` ou o último fechamento do mês anterior à data de `/referencia`.
- `Calc.rentabilidade` usa os valores da API (mês, ano, 12m, 24m, 36m e desde o início).
- Feriados reconstruídos pelos dias úteis sem CDI na API.
- `HGHY` usa `hghy_padrao` do `de_para_api.yml` (a API não traz).

**Decisão (29/10/2026):** vale o `configs/de_para_api.yml` como está (gerado pelo cruzamento API × Base Carteira de 30/09/2026, valor mais frequente). Sem revisão da analista por enquanto; ajustes entram como novas linhas no arquivo.

## Abas de Investment Solutions (Low Vol e TOP Credit) via API

`loaders/abas_is_api.py` monta, a partir da API, a mesma grade de células que a
aba da planilha tinha (os gráficos do PPTX apontam para essas células). Usa
`visao-geral` (PL e vol), `pnl/explosao` (agrupado por `book` e `economic_group`)
e `alocacao`. Se a API falhar, cai na `dados_mensais.xlsx`, por aba.

Diferenças a confirmar com a gestão:
- quadro "Tipo" do TOP Credit: vem de `by_class` (Caixa 37% na API x 44% na planilha);
- top 5 de emissores: a API inclui o C6, que a planilha omitia;
- Low Vol: regra book→macro-estratégia inferida dos números;
- alpha = `Alpha` + `Trade` da API (diferenças de 0,1 a 0,3 bps).
