# Captação · Previdência — origem dos dados

**Tivio Capital** · 15/09/2026

## Estado

| Item | Situação |
|---|---|
| Template | `templates/dashboard_captacao_previdencia.html` |
| Fonte hoje | `Excel - Guia de Base de Dados/Captacao_Previdencia.xlsx` |
| Fonte alvo | `sql/captacao_previdencia.sql` — **não validado** |
| Regenerável hoje | sim, `python atualizar_previdencia.py` |

## O SQL herda um problema conhecido

O `sql/captacao_previdencia.sql` foi espelhado de
`Update_Captacao_Fundos_Abertos`, que usa as mesmas quatro tabelas e já roda. A
única diferença é o recorte de previdência (PGBL/VGBL) no `WHERE`.

**Mas aquele ambiente tem divergência aberta contra a planilha de referência** —
ver `Update_Captacao_Fundos_Abertos/ORIGEM_DOS_DADOS.md`: dos 120 fundos do
Excel, só 14 aparecem no dashboard, e nenhum com o mesmo valor. É provável que
este SQL herde a mesma divergência, porque parte da mesma lógica de agregação.

**Conciliar o de Fundos Abertos primeiro.** Enquanto isso, `FONTE=databricks`
interrompe com aviso em vez de gerar número não conferido.

## O Excel é mais recente que o HTML entregue

| | Período |
|---|---|
| HTML entregue | mês fechado 29/05/2026 a 30/06/2026 |
| Excel | mês 31/07/2026 em diante |

A regeneração atualiza o dashboard para o período do Excel. O CDI do mês
derivado bate com o cabeçalho do Excel: **1,09%**.

## Duas unidades no mesmo template

O template tem dois blocos de dados, em unidades diferentes:

| Bloco | Conteúdo | Unidade |
|---|---|---|
| `FUNDS_DATA` | lista única, achatada | percentual (`1.07`, `95.78`) |
| `PREV` | por plataforma | fração (`0.0107`, `0.9578`) |

Isso vem do template, não é escolha do script — `montar_funds_data()` converte.
Mexer em um sem o outro produz rentabilidade 100× errada em metade da tela.
