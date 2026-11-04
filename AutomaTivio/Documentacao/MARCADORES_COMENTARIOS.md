# Marcadores nos comentários do gestor

No `entrada/comentarios.md`, os números que vêm da tabela de rentabilidade
entram como marcador entre chaves. O `run.py` troca cada marcador pelo número
do mês, no mesmo formato da tabela. O resto do texto (cenário, spreads em bps,
fluxos, atribuição de performance) continua escrito à mão.

Para converter um comentário que veio com os números digitados:

```bash
python scripts/marcadores_comentarios.py            # mostra o que vai mudar
python scripts/marcadores_comentarios.py --gravar   # grava (guarda comentarios.md.bak)
```

Marcador que não existe aparece no relatório como `{nome_errado}` e o log avisa.

## Os marcadores

| Marcador | O que entra | Formato (exemplo) |
|---|---|---|
| `{mes}` | rentabilidade do fundo no mês | 1,03% |
| `{pct_mes}` | % do benchmark no mês | 95% |
| `{ano}` | rentabilidade no ano | 10,44% |
| `{pct_ano}` | % do benchmark no ano | 99% |
| `{12m}` | rentabilidade em 12 meses | 13,52% |
| `{pct_12m}` | % do benchmark em 12 meses | 93,84% |
| `{inicio}` | rentabilidade desde o início | 34,10% |
| `{pct_inicio}` | % do benchmark desde o início | 130,15% |
| `{bench_inicio}` | benchmark acumulado desde o início | 26,20% |
| `{bench_mais_inicio}` | spread sobre o benchmark desde o início (CDI + X%) | 2,10% |
| `{credito}` | alocação em crédito | 75% |
| `{carrego}` | carrego da carteira (CDI + X%) | 0,25% |
| `{duration}` | duration média, com "ano" ou "anos" | 1,03 ano |
| `{mes_nome}` | mês da edição, em minúscula | setembro |
| `{nome}` | nome do fundo | Tivio Banks |
| `{bench}` | nome do benchmark | CDI |

Também existem `{24m}`, `{36m}`, `{alfa_mes}`, `{alfa_ano}`, `{alfa_12m}`,
`{bench_mes}`, `{bench_ano}`, `{bench_12m}`, `{pl}`, `{pl_medio}`,
`{data_base}` e `{mes_ano}`.

## Como fica cada fundo

Só a frase com números da tabela. O restante do comentário segue como o gestor escreveu.

**Tivio Banks**
> O Fundo Tivio Banks obteve retorno de {mes} ({pct_mes} do CDI) no mês e acumula {ano} ({pct_ano} do CDI) em 2026. A alocação em crédito era de {credito}, integralmente concentrada em emissores do setor bancário. O carrego da carteira encontra-se em CDI + {carrego}, com duration média de {duration}.

**Tivio Institucional, Legacy Prev, RF CP, BVP, Institucional 15 e Institucional 30**
> Nesse cenário, o {nome} apresentou rentabilidade de {mes} no mês ({pct_mes} do CDI), acumulando {ano} ({pct_ano} do CDI) no ano. Na parcela de corporativos, os maiores contribuidores…

**Tivio Infra Plus e Tivio Esplanada** (isentos, benchmark IPCA: sem % do benchmark)
> Nesse cenário, o {nome} apresentou rentabilidade, isenta de imposto de renda, de {mes} no mês, acumulando {ano} no ano. Na atribuição de performance…

**Tivio Atuarial**
> Nesse cenário, o Tivio Atuarial apresentou rentabilidade de {mes} no mês, acumulando {ano} no ano. Na atribuição de performance…

**Tivio Infra Plus CDI e Institucional Incentivado CDI**
> Nesse cenário, o {nome} apresentou rentabilidade, isenta de imposto de renda, de {mes} no mês ({pct_mes} do CDI), acumulando {ano} ({pct_ano} do CDI) no ano. Na atribuição de performance…

**Tivio ALT Light, ALT 180 e ALT 90** (a abertura é montada sozinha; se o gestor escrever, fica assim)
> O {nome} registrou rentabilidade de {mes} no mês, equivalente a {pct_mes} do CDI no período. Desde o início da estratégia, o fundo acumula retorno de {inicio}, frente a {bench_inicio} do CDI, o que corresponde a um desempenho anualizado de {pct_inicio} do CDI.

**Tivio Prev Top Credit**
> Nesse cenário, o Tivio Top Credit Prev apresentou rentabilidade de {mes} no mês ({pct_mes} do CDI), acumulando {12m} ({pct_12m} do CDI) em 12 meses.

**Tivio HGD30 e HYD60**: a frase de rentabilidade, carrego e duration é montada sozinha; no comentário entra só a atribuição de performance (HGD30) e os destaques da gestão (HYD60).

**Tivio Prev Low Vol**: o comentário não cita rentabilidade; não leva marcador.

**Em todos**: o mês no começo do parágrafo ("Em setembro, …") pode ser `Em {mes_nome}, …`, para não sair o mês errado quando o texto é reaproveitado.

## Cuidados

- O marcador vai sem espaço dentro das chaves: `{mes}`, não `{ mes }`.
- O `%` já vem no número: escreva `{mes}`, não `{mes}%`.
- Número que não vem da tabela (bps de alfa, spreads, R$ de fluxo) fica digitado.
- Mesmo sem marcador, o `run.py` acerta os números das frases-padrão pela tabela
  (`engine/sincroniza.py`) e registra a troca na conferência. O marcador deixa
  isso explícito no próprio texto e vale também para frases fora do padrão.
