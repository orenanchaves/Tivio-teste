# Análise · ETF → Databricks (base do projeto)

Base para automatizar o dashboard **Análise · ETF** no mesmo padrão do
**Captação · Fundos Abertos**. A diferença importante está na seção 0.

---

## 0. Leia isto primeiro (o ETF é diferente!)

O dashboard de ETF é **majoritariamente estático**: timeline, contexto global,
benchmark de taxas, pipeline regulatório e "Caminhos Tivio" são **narrativa /
pesquisa** (fontes B3, CVM, ANBIMA, SEC, Morningstar). **Não** existe um
`const ETFS_DATA = [...]` dirigindo tudo, como havia no Fundos Abertos.

O que dá para automatizar (blocos de **dados**):
- **KPIs** (nº de ETFs, PL da classe, investidores, captação)
- **Peers & Gestoras** (nº ETFs, lançamentos, PL, fee médio por emissor)
- **Fluxo & Captação** por categoria (se ETF tiver informe/fluxo)
- **Cross-listed** nas plataformas

O que continua **manual** (pesquisa/estratégia):
- Timeline, contexto global, regulatório (Anexo V), Caminhos A/B/C, riscos.

> Estratégia: automatize os blocos de dados via **marcadores** no HTML
> (seção 5) e deixe a narrativa como está.

---

## 1. Estrutura

```
Update_ETF/
├── explorar_etf.py        # sondagem: descobre a base de ETFs no Databricks
├── atualizar_etf.py       # motor: SQL -> ETFS_DATA -> injeção nos blocos marcados
├── etf_metrics.py         # normaliza linhas + agrega por gestora
├── peers_etf.csv          # fees/peers manuais (fee costuma vir de lâmina)
├── sql/
│   └── etf.sql            # query (⚠️ esqueleto — ajustar após explorar)
├── templates/
│   └── dashboard_etf.html # você coloca aqui
├── outputs/               # resultado gerado
├── .env.example
└── requirements.txt
```

---

## 2. Preparar o ambiente

```powershell
cd "...\Update_ETF"
pip install -r requirements.txt
copy .env.example .env
```

Coloque o `dashboard_etf.html` em `templates/`.

---

## 3. Testar SEM banco (mock)

`.env` com `USE_MOCK=true` e:

```powershell
python atualizar_etf.py
```

Gera `outputs/dashboard_etf.html` com 40 ETFs fictícios. Valida que a
injeção funciona. ✅

---

## 4. Descobrir a base de ETFs (investigação)

Rode:

```powershell
python explorar_etf.py
```

Ele faz 3 sondagens:
1. `DESCRIBE` das tabelas B3 candidatas (`b3_instrumentos_financeiros`,
   `daily_price`, `vw_prices`...).
2. Procura colunas que classifiquem ETF (`etf`, `tipo_ativo`, `segmento`,
   `ticker`, `isin`...).
3. Lista tabelas com nome relacionado.

**Me mande os 3 resultados** — com eles a gente ajusta o `sql/etf.sql`
(nomes reais de view/coluna e o filtro que isola os ETFs).

> Heurística útil: no Brasil, tickers de ETF terminam em **11** (BOVA11,
> IMAB11, DEBB11...). Mas confirme com a coluna de tipo/segmento.

---

## 5. Marcar os blocos de dados no HTML

No `dashboard_etf.html`, envolva **cada bloco que quer automatizar** com
comentários marcadores. Exemplo para os KPIs:

```html
<!-- KPIS:START -->
<div class="kpi-card">...</div>
<div class="kpi-card">...</div>
<!-- KPIS:END -->
```

O motor (`atualizar_etf.py`, função `injetar_bloco`) troca **só** o conteúdo
entre `:START` e `:END`. Marcadores sugeridos:
- `KPIS` — os 4 KPIs da Visão Geral
- `GESTORAS` — a tabela de Peers & Gestoras
- `FLUXO` — as barras de captação por categoria

Depois, no `main()`, monte o HTML de cada bloco a partir de `etfs` /
`gestoras` e chame `injetar_bloco(html, "GESTORAS", html_da_tabela)`.

> Se preferir, dá para adicionar um `const ETFS_DATA = [...]` no template e
> deixar o JS montar as tabelas — o motor já injeta esse array se ele existir.

---

## 6. Rodar de verdade

`.env` com `USE_MOCK=false` e:

```powershell
python atualizar_etf.py
```

Confira o resumo no terminal (nº de ETFs, gestoras, PL total).

---

## 7. Campos do ETFS_DATA (contrato)

| campo | origem provável |
|---|---|
| `ticker` | B3 instrumentos |
| `nome` | B3 instrumentos |
| `gestora` | B3 / cadastro emissor |
| `categoria` | B3 segmento (ou de-para manual) |
| `pl` | informe/fluxo (se ETF tiver) ou fonte de mercado |
| `fee` | **`peers_etf.csv` (manual)** — vem de lâmina |
| `cap12` | base de fluxo (se disponível) |
| `cnpj` | B3 / cadastro |

---

## 8. Fluxo final

```
explorar_etf.py  (uma vez, para achar a base)
        |
        v
sql/etf.sql  (ajustado com nomes reais)
        |
Databricks --> etf_metrics --> ETFS_DATA
        |                         |
        +---- peers_etf.csv ------+  (fees/peers manuais)
        |
        v
injeta nos blocos marcados do HTML
        |
        v
outputs/dashboard_etf.html
```

---

## 9. Próximo passo prático

1. Rode `python explorar_etf.py` e me mande os 3 retornos.
2. Ajusto o `sql/etf.sql` com as colunas reais.
3. Você marca os blocos (`KPIS`, `GESTORAS`, `FLUXO`) no HTML.
4. `python atualizar_etf.py` com `USE_MOCK=false`.
