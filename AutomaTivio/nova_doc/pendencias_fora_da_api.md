# Pendências e o que ainda não vem da API

Posição em 03/11/2026, branch `feat/integration_api`.

## O que ainda não vem da API

| Item | Origem atual | Observação |
|---|---|---|
| Conexão ALT 180 | `dados_mensais.xlsx` | sem `id_portfolio` em `configs/fundos.yml` |
| HGD30 e HYD60 PGBL/VGBL (classe Bradesco) | `dados_mensais.xlsx` | sem cotas da classe na planilha; a rentabilidade sai da classe principal. Ver se existe id na API |
| Taxas | `entrada/taxas_global.xlsx`, `entrada/taxas_prev.xlsx` | sem fonte na API |
| Spreads de mercado de crédito | `entrada/tabela_spreads.xlsx` | sem fonte na API |
| Ajustes manuais | `entrada/preenchimento_manual.xlsx` | overrides |
| Comentários dos gestores | `entrada/comentarios.md` | texto do gestor |
| Números institucionais (AuM, anos, fundos, profissionais, AUM por vertical) | `data/tivio_summary.json`, API pública, `configs/big_numbers.yml` | |
| Reserva | `dados_mensais.xlsx` | assume a 1ª fonte e as abas Low Vol / TOP Credit se a API falhar |

## Decisões e observações

- **Legacy:** usa o id **1123** (BV Icatu Seg Legacy Prev, CNPJ 09.166.056/0001-95). CNPJ, PL (~15 MM) e rentabilidade batem com a apresentação. O 975 (PL 155 MM) e o 2585 (sem PL) não servem.
- **Carteira expandida:** não é outro id, é o parâmetro `visao=expandida` (padrão), que o loader já usa.
- **Top Manager Global:** o benchmark é o Dólar PTAX mesmo, então o % do benchmark aparece (valores altos, como 395% desde o início). Não ocultar.

## Pendências

1. Rodada completa (PDF e PPTX) e conciliação 58/58 (`docs/conciliar_com_pptx.py`) com a API: nunca rodadas.
2. Achar o id da Conexão ALT 180.
3. Ver se a classe Bradesco do HGD30 e HYD60 existe na API.
4. Validar com o analista: `nova_doc/low_vol_and_top_credit_validar.md`.
5. Otimizar `--so`: hoje busca todos os fundos na API.
6. Logos `tivio_atuarial` e `tivio_bvp` ausentes.
7. Push da branch `feat/integration_api` (só local).
