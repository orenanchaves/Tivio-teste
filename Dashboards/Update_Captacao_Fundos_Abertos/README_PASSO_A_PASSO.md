# Captação · Fundos Abertos → Databricks

Conecta o dashboard **Captação · Fundos Abertos** ao Databricks, no mesmo padrão do **Monitor de Novos Fundos**: `Databricks → SQL → Python → FUNDS_DATA → HTML`, com injeção cirúrgica via regex (o design system nunca é tocado).

---

## Estrutura

```
Update_Captacao_Fundos_Abertos/
├── atualizar_captacao.py      # motor: conecta, roda SQL, monta FUNDS_DATA, injeta no HTML
├── captacao_metrics.py        # transforma o DataFrame na lista de 17 campos por fundo
├── sql/
│   └── captacao_fundos_abertos.sql   # query ANBIMA (⚠️ view a confirmar)
├── templates/
│   └── dashboard_captacao_fundos_abertos.html   # <- você coloca aqui
├── outputs/                   # resultado gerado
├── .env.example               # credenciais + USE_MOCK
└── requirements.txt
```

---

## PASSO 0 — Preparar o ambiente (uma vez)

```powershell
cd "...\Update_Captacao_Fundos_Abertos"
pip install -r requirements.txt
copy .env.example .env
```

Coloque o `dashboard_captacao_fundos_abertos.html` dentro de `templates/`.

---

## PASSO 1 — Testar o pipeline SEM banco (mock)

No `.env`, deixe `USE_MOCK=true` e rode:

```powershell
python atualizar_captacao.py
```

Isso gera `outputs/dashboard_captacao_fundos_abertos.html` com 120 fundos fictícios
(4 plataformas × 3 categorias × 10). **Abra e confira** se as abas "Rankings por
Plataforma" e "Ranking Completo" preenchem. Se preencheu, a injeção funciona. ✅

---

## PASSO 2 — Descobrir a view de captação (a parte de investigação)

O SQL em `sql/captacao_fundos_abertos.sql` é um **esqueleto**. A fonte de captação
líquida (por plataforma/categoria) pode não ser a mesma do Monitor. Rode uma
sondagem no Databricks para localizar a view certa:

```python
from dotenv import load_dotenv
from databricks import sql
import os
load_dotenv()
conn = sql.connect(
    server_hostname=os.getenv("DATABRICKS_HOST"),
    http_path=os.getenv("DATABRICKS_PATH"),
    access_token=os.getenv("DATABRICKS_TOKEN"))
cur = conn.cursor()
cur.execute("SHOW TABLES IN marketdata.silver LIKE '*captac*'")
for r in cur.fetchall():
    print(r)
cur.close(); conn.close()
```

Procure algo como `anbima_captacao_fundo`, `*_ranking_captacao`, `*_fluxo_*`.
Ao achar, dê um `DESCRIBE` para ver as colunas reais:

```sql
DESCRIBE marketdata.silver.<view_que_voce_achou>
```

E ajuste os nomes de coluna no `.sql` e/ou no `captacao_metrics.py`.

> **Chaves de junção** (já confirmadas no Monitor): `codigo_classe` liga classe,
> prestadores, perfil e taxas. Gestor real vem de `anbima_prestadores_classe`
> filtrando `codigo_tipo_prestador = GESTOR` (confirme o código exato).

---

## PASSO 3 — Rodar de verdade

No `.env`, ajuste o CDI da competência e coloque `USE_MOCK=false`:

```powershell
python atualizar_captacao.py
```

Confira no terminal o resumo (quantidade de fundos, plataformas, categorias).

---

## Campos do FUNDS_DATA (contrato com o HTML)

| campo | o que é |
|---|---|
| `rank` | posição 1..10 **dentro** da plataforma+categoria |
| `nome` | nome do fundo |
| `cap30 / rent30 / cdi30` | captação 30d, rentab. 30d, % benchmark 30d |
| `cap12 / rent12 / cdi12` | idem 12 meses |
| `capytd / rentytd / cdiytd` | idem YTD |
| `pl` | patrimônio líquido |
| `benchmark` | "CDI", "IMA-B"... |
| `gestor` | asset / gestor real |
| `plat` | **exatamente** XP \| BTG \| Itau \| Bradesco |
| `categoria` | Renda Fixa Ativa \| Renda Fixa \| Multimercado |
| `rank_global` | posição no ranking geral (cap30 desc) |

`cdi30/12/ytd` = **% do benchmark**. Se o banco já entrega, usa direto; senão o
`metrics.py` calcula `rent / cdi_período * 100`.

---

## Próximos passos (fase 2 — depois que o FUNDS_DATA estiver ok)

O dashboard tem 3 blocos hoje **estáticos** que dá para automatizar em seguida:

1. **KPIs da Visão Geral** e objeto `AB.resumo` (totais 30d/12m, plataforma líder,
   maior resgate) — hoje escritos à mão no HTML.
2. **`CARTEIRAS_TOP3`** — composição CVM (CDA) dos Top 3 por plataforma/categoria.
3. **`COTIZ_MAP`** — prazo de cotização (coluna D+ da fonte).

Cada um vira uma nova injeção `const XXX = {...}` no mesmo esquema regex.
Faz o FUNDS_DATA rodar redondo primeiro; depois a gente encadeia esses três.
