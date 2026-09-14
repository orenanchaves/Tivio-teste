# Diagnóstico — divergência de Agosto entre o monitor novo e a planilha histórica

**Monitor de Novos Fundos · Tivio Capital**
Data da análise: 14/09/2026

Fontes confrontadas:

| | Arquivo | Grão | Período | Linhas |
|---|---|---|---|---|
| Planilha histórica | `Monitor_Fundos_Tivio.xlsm`, aba `_DADOS` | 1 fundo/classe | 02/01/2026 → 31/08/2026 | 718 |
| Monitor novo | `outputs/dashboard_fundos_tivio_geral.html` (gerado 14/09/2026 18:28) | 1 classe | 09/01/2024 → 06/08/2026 | 596 (pós-filtro peer) |

Chave de casamento: CNPJ de 14 dígitos.

---

## 1. Veredito

A hipótese de trabalho era que a planilha aplicava alguma regra de exclusão
(exclusivos, feeders, estruturados) que o Python não reproduzia.

**Ela não aplica nenhuma.** A planilha mantém todas as categorias suspeitas e as
classifica em colunas próprias. Não existe regra histórica a implementar.

A divergência vem de quatro causas independentes que se acumulam:

| # | Causa | Natureza | Impacto em Agosto |
|---|---|---|---|
| 01 | O "47" empilha três anos | bug de código | número inexistente |
| 02 | Universo de peers diferente | escopo/negócio | −89 registros |
| 03 | As bases medem eventos diferentes | conceitual | −12 registros |
| 04 | Fonte ANBIMA defasada 39 dias | dado | agosto truncado em 06/08 |

---

## 2. Causa 01 — o número 47 nunca existiu

O bloco de diagnóstico filtrava apenas `mes_ref == 8`, sem recorte de ano. Como a
base cobre 2024–2026, somava três agostos distintos:

```
ago/2024 ....... 24
ago/2025 ....... 19
ago/2026 ........ 4
              ------
soma indevida ... 47
```

A distribuição por tipo do "47" (FIF 33, FIDC 6, FIP 4, FII 3, FIAGRO 1) parecia
plausível para um mês cheio, o que fez o número passar por verossímil.

**Status: corrigido.** O recorte agora é mês *e* ano (`MES_DIAG` / `ANO_DIAG`).

---

## 3. Causa 02 — o universo de peers é outro

Agosto/2026 na planilha, por gestora:

| Gestora | Qtde | Está na lista `PEERS` do Python? |
|---|---:|---|
| Itaú Unibanco | 43 | não |
| Bradesco Asset | 17 | não |
| BTG Pactual | 16 | não |
| XP Asset | 13 | não |
| Kinea | 8 | sim |
| Ibiuna | 2 | sim |
| Capitania | 2 | sim |
| Vinci | 1 | sim |
| JGP | 1 | sim |
| Riza | 1 | sim |
| SPX | 1 | sim |
| **Total** | **105** | **16 comparáveis** |

Na direção oposta, o Python inclui **Pátria**, que não tem aba na planilha.

A planilha tem 22 abas: `Resumo`, `_DADOS`, seis por tipo de veículo
(`FI`, `FIAGRO`, `FIDC`, `FII`, `FIIM`, `FIP`), treze por gestora e `Analise`.
**Não existe aba "Agosto"** — o recorte mensal é feito filtrando `_DADOS` por
`Data_Registro`.

---

## 4. Causa 03 — registro na CVM não é início de atividade

Esta é a diferença conceitual de fundo, e a que continuará gerando ruído todo mês.

| | Planilha histórica | Monitor novo |
|---|---|---|
| Evento marcado | registro no cadastro da CVM | início de atividade da classe |
| Campo | `Data_Registro` | `data_inicio_atividade_classe` |
| Inclui pré-operacionais? | sim (194 de 718) | não — sem data, some do `WHERE` |

Cruzando os 596 registros do monitor com os 718 da planilha por CNPJ:

```
fundos que casaram ............ 69
defasagem mediana ............ +29 dias   (média +35, máx +140)
monitor posterior à planilha .. 68/69  (99%)
caem em MÊS diferente ......... 51/69  (74%)
situação na planilha .......... 69/69 "Em Funcionamento Normal"
```

Ou seja: a planilha captura o fundo no nascimento cadastral; o monitor só o vê
quando a classe começa a operar, cerca de um mês depois. Três quartos dos fundos
mudam de mês entre as duas bases.

### Efeito mês a mês (2026, apenas peers em comum)

| Mês | Planilha | Monitor |
|---|---:|---:|
| jan | 12 | 9 |
| fev | 13 | 12 |
| mar | 31 | 20 |
| abr | 13 | **25** |
| mai | 19 | 11 |
| jun | 12 | 13 |
| jul | 30 | 13 |
| ago | 16 | **4** |

Repare em **abril**: o monitor mostra 25 contra 13 da planilha. A defasagem não
derruba todo mês — ela empurra a safra para frente. Agosto é o pior caso porque
acumula a defasagem *e* o corte da fonte.

---

## 5. Causa 04 — a fonte ANBIMA está 39 dias atrasada

Os dashboards foram gerados em **14/09/2026 às 18:28**, numa consulta real ao
Databricks. Mesmo assim o dado mais recente é **06/08/2026**.

```
ago/2024:  24 classes | última em 30/08/2024  <- mês completo
ago/2025:  19 classes | última em 29/08/2025  <- mês completo
ago/2026:   4 classes | última em 06/08/2026  <- truncado
```

É corte seco, não maturação gradual: a semana de **27/07 a 02/08 tem zero
registros** e não há nada depois de 06/08. Se fosse comportamento real do
mercado, haveria uma cauda decrescente.

Pelo padrão histórico, agosto/2026 deve fechar em torno de **20 classes** quando
a ANBIMA publicar o restante. **Rodar de novo hoje não muda nada.**

---

## 6. A conciliação de Agosto/2026

| Regra | Impacto | Qtde |
|---|---:|---:|
| Planilha histórica — Agosto/2026 (total) | | **105** |
| (−) gestoras fora da lista `PEERS` | −89 | 16 |
| (−) ainda pré-operacionais (sem classe ativa) | −12 | 4 |
| (=) Monitor novo — Agosto/2026 | | **4** |

### Ressalva importante: a conta fecha, mas os fundos não são os mesmos

Sobram 4 de cada lado e o cruzamento por CNPJ dá **zero em comum**. O `4 = 4` é
coincidência numérica.

Os 4 do monitor existem na planilha, mas em maio e junho:

| Fundo | Tipo | No monitor | Na planilha |
|---|---|---|---|
| SPX Crédito Opportuna I Previdenciário XP Seg | FIF | 06/08/2026 | 12/06/2026 |
| SPX Crédito Opportuna I Previdenciário | FIF | 06/08/2026 | 10/06/2026 |
| Capitânia Yield Sênior | FIDC | 05/08/2026 | 04/05/2026 |
| Kinea Equity Infra II Seed Money | FIP | 03/08/2026 | 10/06/2026 |

E os 16 de agosto da planilha estão **todos ausentes** do monitor — inclusive os
4 já "Em Funcionamento Normal" (Ibiuna 28/08, Riza 24/08, Kinea 13/08 ×2), que
caíram depois do corte de 06/08 da fonte.

---

## 7. A planilha não remove nada

Verificação sobre as 718 linhas da base histórica:

| Categoria | Qtde | % da base | Veredito |
|---|---:|---:|---|
| Exclusivos (`Exclusivo = 'S'`) | 293 | 40,8% | mantida |
| Mandatos (`Tipo_Estrutura`) | 271 | 37,7% | mantida |
| Estruturados (FIDC/FIP/FII/FIAGRO/FIIM) | 181 | 25,2% | mantida |
| Pré-operacionais | 194 | 27,0% | mantida |
| Feeders (FIC / em cotas) | 54 | 7,5% | mantida |
| Previdência | 53 | 7,4% | mantida |

Em Agosto/2026 especificamente: `Tipo_Estrutura` = Prateleira 70, Mandato 33,
Solução Dedicada 2; `Exclusivo` = S 35, N 58, vazio 12.

**Consequência: nenhum filtro novo deve entrar no `atualizar_monitor.py`.**
Qualquer regra de exclusão adicionada para "aproximar" os números afastaria o
monitor da planilha, não o contrário.

---

## 8. Respostas ponto a ponto

**1. Quantidade total em Agosto em cada base**
Planilha 105 · restrita aos peers do Python 16 · monitor 4. O "47" não era um mês.

**2. Registros só no monitor novo**
Os 4 de ago/2026 — todos existem na planilha, em maio e junho.

**3. Registros só no Excel antigo**
Os 16 peers de ago/2026, todos ausentes do monitor: 12 pré-operacionais e 4
posteriores ao corte de 06/08.

**4. A diferença é classe / exclusivo / estruturado / feeder / previdência?**
Não. A composição por tipo é semelhante nas duas bases. O gap é universo de
peers (−89) e data de referência (−12).

**5. O Excel remove exclusivos, mandatos, feeders, estruturados, subclasses?**
Não remove nenhum. Ver seção 7.

**6. Há agrupamento de múltiplas classes num único fundo?**
Praticamente não. Monitor: 596 linhas / 596 CNPJs distintos. Planilha: 718 linhas
/ 711 CNPJs (7 excedentes, irrelevantes para agosto, onde os 105 CNPJs são
distintos e `Existe_Classe_Prateleira = "Nao"` em todas as linhas).
**Não há o que desagrupar.**

**7. Tabela REGRA | IMPACTO | QTDE**
Seção 6.

**8. Qual regra histórica implementar no Python?**
Nenhuma regra de exclusão. O que precisa mudar é a **data de referência** e, se a
intenção for dar continuidade ao histórico, a **lista de peers**. Ver seção 9.

---

## 9. Alterações — feitas e recomendadas

### Já aplicado e validado

**a) Escopo do bloco de diagnóstico.** O `try/except` estava alinhado à coluna 0,
fora do `main()`, quebrando o módulo no import com
`NameError: name 'df' is not defined`.

**b) Recorte de mês + ano.** O diagnóstico agora filtra os dois, via `MES_DIAG` /
`ANO_DIAG` (ano vazio = mais recente da base). A saída virou
`peers_<ano>_<mes>.xlsx`, para não sobrescrever meses diferentes.

**c) Alerta de fonte defasada.** `diagnosticar_fonte()` imprime a última data
disponível, a defasagem em dias e avisa quando o último mês ficou truncado. O
bloco de diagnóstico ainda compara o mesmo mês nos outros anos:

```
Depois filtro: 596
  fonte ate 06/08/2026 (39 dias de defasagem)
  ! 08/2026 INCOMPLETO na fonte: faltam 25 dias do mes
    nao compare esse mes com a planilha historica ainda

=== AGOSTO/2026 ===
Linhas: 4

Mesmo mes em outros anos:
  AGOSTO/2024: 24
  AGOSTO/2025: 19
  AGOSTO/2026: 4  <- atual
  ! bem abaixo da media dos anos anteriores: provavel mes incompleto na fonte
```

Validado contra a base real: ago/2026 dispara os dois avisos; ago/2025 (19) e
abr/2026 (25, acima de abr/2025) não disparam nenhum.

### Decisão pendente 1 — restaurar o acesso ao catálogo restrito

**É o que resolve de verdade, e é pedido de permissão ao TI, não código.**

O próprio SQL documenta a perda de acesso, com data de hoje:

```
CORRECAO 1 (2026-09-14): catalogo restrito
[INSUFFICIENT_PERMISSIONS] User does not have USE CATALOG. SQLSTATE: 42501
cvm_status -> sem equivalente na ANBIMA; retorna ''
```

Esse `cvm_status` é exatamente o `Situacao` = "Fase Pré-Operacional" da planilha.
Recuperando o acesso, voltam de uma vez:

- os fundos pré-operacionais (194 de 718 na planilha);
- a data de registro na CVM, que alinha o eixo temporal das duas bases;
- a flag `is_exclusive` de verdade (hoje marca 0 de 47; a planilha marca 293 de 718).

### Decisão pendente 2 — alinhar o universo de peers

Decisão de negócio. Se a intenção é dar continuidade ao histórico, a lista
precisa incluir os grandes distribuidores:

```python
PEERS = [
    "ITAU", "BRADESCO", "BTG", "XP",       # ausentes hoje no Python
    "SPX", "IBIUNA", "VINCI", "RIZA", "JGP",
    "KINEA", "AUGME", "CAPITANIA", "VERDE",
    "PATRIA",                              # não tem aba na planilha
]
```

Se o monitor novo é deliberadamente só de peers de gestão, os totais nunca vão
bater — e isso deve estar dito no dashboard.

---

## 10. Achados secundários

| Achado | Onde | Efeito |
|---|---|---|
| `data_constituicao` é data de vigência do cadastro, não de constituição | `monitor_fundos.sql` · `af.data_vigencia_fundo` | valor errado em 596/596 linhas; é posterior ou igual ao início da classe em 100% dos casos, mediana 178 dias depois |
| Flag `exclusivo` não dispara | CTE `exclusivo_por_classe`, depende de "EXCLUSIV" no nome | 0 de 47 no monitor · 293 de 718 na planilha |
| Nomenclatura de tipo divergente | planilha usa `FI` e `FIIM`; monitor usa `FIF` | impede comparação direta por tipo |
| Atribuição duplicada de `anos` | `atualizar_monitor.py` | removida |

---

## 11. Como reproduzir

```bash
# conciliação completa de um mês
python comparar_agosto.py Monitor_Fundos_Tivio.xlsm --mes 8 --ano 2026

# outro mês, apontando a base nova explicitamente
python comparar_agosto.py Monitor_Fundos_Tivio.xlsm --mes 9 --ano 2026 \
       --novo outputs/dashboard_fundos_tivio_geral.html

# diagnóstico mensal dentro do próprio monitor
MES_DIAG=8 ANO_DIAG=2026 python atualizar_monitor.py
```

`comparar_agosto.py` aceita como base nova tanto um dashboard HTML (lê o array
`FUNDS_DATA`) quanto um `.xlsx` exportado pelo monitor.

---

## 12. Conclusão

O monitor não está errado em Agosto — ele está **incompleto e desalinhado**:

- incompleto porque a fonte ANBIMA parou em 06/08 (39 dias de defasagem);
- desalinhado porque mede início de atividade, enquanto a planilha mede registro
  na CVM, e porque acompanha um conjunto menor de gestoras.

Nenhum desses pontos se resolve com regra de filtro. Ordem de prioridade
sugerida:

1. **Restaurar o acesso ao catálogo restrito da CVM** — destrava os
   pré-operacionais, a data de registro e a flag de exclusivo de uma só vez.
2. **Decidir o universo de peers** — continuidade do histórico ou recorte novo,
   explicitado no dashboard.
3. **Corrigir `data_constituicao`** — hoje exibe a data de vigência do cadastro.
4. Só depois disso vale reavaliar a lógica do monitor.
