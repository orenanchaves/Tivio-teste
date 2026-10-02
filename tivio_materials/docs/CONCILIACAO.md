# Conciliação com os relatórios publicados · agosto/2026

Antes de confiar na automação, a pergunta certa é: **ela reproduz o que já foi
publicado?** Esta conciliação responde comparando a rentabilidade calculada pela
plataforma com a dos 12 PPTX de Relatório de Gestão de agosto/2026.

## Resultado

```
58 de 58 rentabilidades idênticas ao relatório publicado (100%)
```

Seis períodos (mês, ano, 12M, 24M, 36M, desde o início) × 12 fundos, descontados
os períodos que não existem em fundo novo. Tolerância de 0,015 p.p. — abaixo da
casa decimal exibida.

| Fundo | Mês | Ano | 12M | 24M | 36M | Desde o início |
|---|---|---|---|---|---|---|
| Banks | 1,10% | 9,36% | 14,63% | 29,82% | 45,41% | 444,67% |
| Institucional | 1,09% | 9,31% | 14,58% | 29,93% | 47,60% | 825,45% |
| Institucional 15 | 1,11% | 9,53% | 14,94% | 30,92% | 51,22% | 1.644,37% |
| Institucional 30 | 1,12% | 9,45% | 14,68% | — | — | 25,93% |
| Infra Plus | 1,26% | 5,98% | 9,91% | 19,03% | 29,49% | 77,41% |
| Infra Plus CDI | 0,97% | 8,80% | — | — | — | 12,11% |
| Esplanada | 1,28% | 6,11% | 10,04% | — | — | 20,15% |
| Legacy | 1,07% | 8,91% | 14,07% | 28,79% | 46,53% | 435,43% |
| RF CP | 1,12% | 8,59% | 13,99% | 28,43% | 46,57% | 154,64% |
| ALT 180 | 1,30% | 11,19% | 18,11% | — | — | 33,14% |
| ALT 90 | 1,22% | 10,40% | 16,49% | — | — | 21,25% |
| ALT Light | 0,72% | 9,51% | — | — | — | 12,60% |

Todos os valores acima são, ao mesmo tempo, o que a plataforma calculou e o que
está no PPTX publicado.

As datas de início também conferem: Banks 30/04/2009, Institucional 13/05/2005,
Institucional 30 11/12/2024 — iguais à ficha de cada relatório.

## O que isso cobre (e o que não cobre)

**Cobre** toda a cadeia de cálculo: leitura das cotas, calendário de dias úteis
com feriados, as seis datas de referência, o truncamento de período em fundo
novo, a série do benchmark e a formatação pt-BR. Se qualquer elo estivesse
errado, os 58 valores não fechariam.

**Cobre também a resolução de cadastro** dos quatro fundos que nunca estiveram na
automação anterior — Esplanada, Infra Plus CDI, Legacy e RF CP. O RF CP é o caso
instrutivo: a palavra-chave "RF CP" casa com cinco carteiras da DePara, entre elas
a do próprio Banks (`TIVIO BANKS RF CP RL`). O fato de os seis períodos baterem
confirma que a carteira escolhida (`TIVIO FI CI RF CP RL`) é a certa.

**Não cobre** carteira (emissores, setores, rating, carrego, duration) nem a
tabela de Mercado de Crédito, que no PPTX são formas desenhadas e não texto
legível por máquina. Esses números continuam na conferência mensal.

## Uma diferença encontrada

| Fundo | Período | Benchmark calculado | No PPTX |
|---|---|---|---|
| Institucional 15 | 24M | 29,49% | 29,38% |

Só o **benchmark**; o retorno do fundo bate. Os outros onze fundos têm 29,49%
para o CDI de 24 meses no mesmo mês — o que aponta para um ajuste manual na
célula daquele relatório, não para divergência de cálculo. Vale conferir na
próxima edição.

## Como repetir

```powershell
python docs\conciliar_com_pptx.py reports\2026-08\conferencia_2026-08.xlsx
```

O script lê a aba *Rentabilidades* da conferência e os PPTX de referência. Ele
documenta, no próprio código, como a tabela é extraída do slide: as caixas de
texto agrupadas por posição x (coluna = período) e ordenadas por y, onde a ordem
é sempre fundo · benchmark · Alfa · % do benchmark.
