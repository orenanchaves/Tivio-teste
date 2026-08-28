# Monitor de Novos Fundos · atualização automática

Atualiza o **dashboard_fundos_tivio.html** com os dados novos da CVM/ANBIMA
vindos do Databricks, **sem tocar no layout**: substitui cirurgicamente só o
bloco `const FUNDS_DATA = [ ... ]`.

## Como usar
1. Copie o **dashboard_fundos_tivio.html** para esta pasta.
2. Ajuste `sql/monitor_fundos.sql` com o nome real da view CVM/ANBIMA e colunas (com o TI).
3. Renomeie `.env.exemplo` para `.env` e cole seu token.
4. Rode:

       pip install -r requirements.txt
       python atualizar_monitor.py

O HTML é regravado com os fundos atualizados e a data "ATUALIZADO" do topo.

## Arquivos
- sql/monitor_fundos.sql ...... query da view CVM/ANBIMA (25 colunas)
- monitor_metrics.py ......... converte o df no array FUNDS_DATA (escape correto)
- atualizar_monitor.py ....... conecta, gera e injeta no HTML (regex cirúrgica)

## Teste sem Databricks
`USE_MOCK=true` roda com ~1.000 classes fictícias (2024/2025/2026) só para validar layout e injeção.
Confirme que o dashboard abre e mostra os fundos mock; depois vire `USE_MOCK=false`.

## As 25 posições do FUNDS_DATA (ordem)
0 nome · 1 gestora · 2 tipo · 3 seg_detalhe · 4 categ_anbima · 5 situacao ·
6 data_reg · 7 data_const · 8 cnpj · 9 publico · 10 exclusivo · 11 ano ·
12 condominio · 13 subclasse · 14 seg_bitmask(6) · 15 link_cvm · 16 mes(1-12) ·
17 gestor_juridico · 18 administrador · 19 categoria_n1 · 20 risco_credito ·
21 duracao · 22 registro · 23 taxa_adm · 24 taxa_perf

## Fontes por campo
| campo | tabela |
|---|---|
| gestora / administrador | `marketdata.silver.anbima_prestadores_fundo` (`GESTOR` / `ADMIN%`) |
| público-alvo | `marketdata.silver.anbima_perfil_classe` (`tipo_investidor`) |
| taxa de administração | `marketdata.silver.anbima_taxas_classe` (`tipo_taxa LIKE '%administ%'`) |
| taxa de performance | `marketdata.silver.anbima_taxas_classe` (`tipo_taxa LIKE '%performance%'`) |
| link CVM | montado do CNPJ com `LINK_CVM_BASE` |

## Nome das gestoras
A ANBIMA devolve a razão social. O dashboard resolve um **nome curto** por
classe (`nomeCurto`, no template), em três passos:
1. `GESTORA_REGRAS` — as 15 monitoradas (mesma chave do `GESTORA_META`);
2. `GESTORA_ALIAS` — casas conhecidas fora da lista (Safra, Santander, BB,
   Caixa, Opportunity, Franklin Templeton, UBS, Icatu, ...);
3. regra geral — as duas primeiras palavras, sem forma jurídica
   ("Rio das Pedras Gestora" -> "Rio das Pedras").

Para incluir uma gestora nova no recorte peer, basta adicioná-la ao
`GESTORA_META` e ao `GESTORA_REGRAS`; para só encurtar o nome, ao
`GESTORA_ALIAS`.

> O `mes_ref` (16) precisa ser NÚMERO 1..12 — é o que alimenta o filtro de meses.
