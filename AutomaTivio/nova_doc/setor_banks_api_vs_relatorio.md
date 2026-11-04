# Banks: setor na API x setor no relatório

Fundo Banks (código 940), data base 30/09/2026, `signoff=false`.
Fonte: `GET /v1/carteira/fundos/940/posicoes?data=2026-09-30&visao=expandida&signoff=false`
(campo `sector`), traduzido pelo bloco `setor_hg` de `configs/de_para_api.yml`.

| Setor na API | Vira, no relatório | % do fundo |
|---|---|---:|
| Banco de Varejo | Financeiro | 22,3% |
| Banco de Atacado | Financeiro | 18,1% |
| Banco de Montadora | Financeiro | 13,5% |
| Banco Completo | Financeiro | 12,1% |
| Banco Público | Financeiro | 4,8% |
| Banco de Cooperativa | Financeiro | 2,1% |
| Banco de Controle Estrangeiro | Financeiro | 1,7% |
| Governo | Caixa | 17,0% |
| Caixa | Caixa | 8,4% |
| **Total Financeiro** | | **74,6%** |
| **Total Caixa** | | **25,4%** |

Conferência: a Base Carteira da planilha dá Financeiro 74,6% e Caixa 25,4%, com o mesmo total (R$ 1.829.026.095,73).
