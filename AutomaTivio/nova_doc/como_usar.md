# Como usar

Use sempre o Python do ambiente virtual: `.venv/bin/python` (recriar com `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`).

## 1. Rodar a edição (`run.py`)

```bash
.venv/bin/python run.py                          # a edição inteira
.venv/bin/python run.py --so legacy banks        # só estes fundos
.venv/bin/python run.py --saidas html            # pula PDF e PPTX (iterar rápido)
.venv/bin/python run.py --conferir               # calcula e valida, não escreve nada
.venv/bin/python run.py --data-base 2026-09-30   # força a data base
.venv/bin/python run.py --silencioso             # só grava o log
```

Os formatos de `--saidas`: `html`, `pdf`, `pptx`, `destaques`, `emails`, `informativos`.
As opções se combinam, por exemplo `--so legacy --saidas html --conferir`.

Saída: `saida/_Historico/AAAA-MM/` (edição completa) e `saida/_Atual/` (o que se publica).

### Configuração em `configs/edicao.yml`

| Chave | Efeito |
|---|---|
| `data_base` | data da edição (vazio = último mês fechado) |
| `entradas.fonte` | `api` (TLDR) ou `planilha`; se a API falhar, cai na `dados_mensais.xlsx` |
| `entradas.signoff` | `false` = dados da data pedida, mesmo sem aprovação do Risco (teste); `true` = só fechamento aprovado, com fallback para a última data aprovada |

Não há flag de linha de comando para o `signoff`: edite o YAML.

### Token da API

- `.env` com `TIVIO_API_TOKEN=...`: usa esse token (o log informa a origem).
- Vazio ou sem a variável: autenticação normal (`az login` / azure-identity).

## 2. Status de aprovação (sign-off) dos fundos

```bash
.venv/bin/python scripts/status_signoff.py                    # data_base do edicao.yml
.venv/bin/python scripts/status_signoff.py --data 2026-09-30
.venv/bin/python scripts/status_signoff.py -o saida/status.html
```

Gera `saida/status_signoff.html` com, para cada fundo que tem `id_portfolio` no
`configs/fundos.yml`: liberada, cota aprovada, aprovado, data/hora e quem aprovou,
última data aprovada e o último evento (aprovar ou revogar, com motivo).
Rode antes de virar `signoff: true`.

## 3. Zipar o projeto para compartilhar

```bash
.venv/bin/python scripts/zipar_projeto.py             # ../AutomaTivio_AAAA-MM-DD.zip
.venv/bin/python scripts/zipar_projeto.py -o destino.zip
```

Ignora `.git`, `.venv`, `saida`, `.env`, caches e logs.

## 4. Conferência antes de dar a edição por pronta

1. `run.py` com 0 erros no log.
2. `.venv/bin/python docs/conciliar_com_pptx.py saida/_Historico/AAAA-MM/conferencia_AAAA-MM.xlsx` (esperado 58/58).
3. PDFs em A4, com o número de páginas certo e nenhuma em branco.
