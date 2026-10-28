# Captação · Fundos Abertos — origem dos dados e conciliação

**Tivio Capital** · 15/09/2026

Este documento responde duas perguntas: **de onde sai o dado** do dashboard, e
**por que ele não bate** com `Captacao_Fundos_Abertos.xlsx`.

---

## 1. De onde sai o dado

O SQL está totalmente mapeado — não há origem desconhecida. `sql/captacao_fundos_abertos.sql`
(192 linhas) lê quatro tabelas do Databricks:

| Tabela | Papel |
|---|---|
| `marketdata.silver.cvm_informe_diario` | captação, resgates e PL diários — é a fonte dos valores |
| `marketdata.silver.anbima_classes_fundo` | cadastro da classe: nome, classificação, benchmark |
| `marketdata.silver.anbima_fundo` | fundo pai da classe (CNPJ, tipo) |
| `marketdata.silver.anbima_prestadores_classe` | gestor e distribuidor — é o que define a plataforma |

O CDI dos períodos vem de `sql/cdi_periodos.sql`, em query separada.

Competência atual do output: **06/2026**, CDI 30d 1,13% · 12m 14,82% · YTD 5,72% —
os mesmos valores do cabeçalho do Excel.

---

## 2. O que não bate

Comparando `outputs/dashboard_captacao_fundos_abertos.html` com as abas
`XP`, `BTG`, `Itaú` e `Bradesco` do Excel (top 30 de cada lado, 120 linhas):

| Verificação | Resultado |
|---|---|
| Fundos do Excel encontrados no dashboard | **14 de 120** |
| Desses 14, com captação 30d idêntica | **0** |
| Razão dashboard ÷ Excel | mediana 0,78 · mínimo −1,37 · máximo 2,67 |
| Top 1 de cada plataforma | **diferente nas quatro** |

**A razão não é constante**, então não é erro de unidade, de escala nem de
janela de datas — se fosse, todos os fundos errariam pelo mesmo fator. As duas
bases estão medindo coisas diferentes.

### Exemplos

| Plataforma | Fundo | Excel | Dashboard |
|---|---|---:|---:|
| XP | Mapfre Confianza FIF RF Referenciado DI | 886.462.227 | 529.325.542 |
| XP | Icatu Vanguarda Dinâmico CDI | 511.305.846 | 118.454.182 |
| BTG | Bradesco Bancos II FI Financeiro | 566.995.916 | 795.687.722 |
| BTG | BB Asset Renda Fixa Longo Prazo High | 6.804.851 | 18.145.650 |
| Bradesco | Bradesco Solaro FI Financeiro | −98.283.399 | +134.708.905 |

O último inverte o sinal: resgate líquido no Excel, captação no dashboard.

---

## 3. Hipóteses, em ordem de probabilidade

Nenhuma foi confirmada — todas exigem consultar o Databricks, o que este
ambiente de análise não alcança.

**1. Grão classe × fundo (RCVM 175).** É a mesma causa que produziu a
divergência do Monitor de Novos Fundos (ver `DIAGNOSTICO_AGOSTO.md`). Se o
Excel soma por CNPJ do fundo e o dashboard por classe — ou o contrário — o
mesmo nome aparece com valores diferentes, sem fator constante. O cabeçalho do
Excel diz explicitamente *"por CNPJ único — sem dupla contagem de fundos
multi-plataforma"*, e cita **176 fundos em mais de uma plataforma**.

**Sinal forte a favor:** no dashboard, "Mapfre Confianza" aparece com o valor
**idêntico** (529.325.542) sob XP e sob Itaú. Ou seja, o dashboard atribui a
captação inteira a cada plataforma, enquanto o Excel diz que deduplica.

**2. Janela de apuração dos 30 dias.** Ambos dizem 06/2026, mas "últimos 30
dias corridos" e "mês de junho fechado" dão números diferentes. Verificar as
datas mínima e máxima usadas em `cvm_informe_diario`.

**3. Atribuição de plataforma.** O dashboard usa `anbima_prestadores_classe`
para decidir a plataforma. Se o Excel usou distribuidor e o dashboard usa
gestor (ou vice-versa), os fundos trocam de aba — o que explica só 14 de 120
casarem por nome + plataforma.

---

## 4. Como confirmar

Rodar com acesso ao Databricks e comparar um único fundo ponta a ponta:

```sql
-- Mapfre Confianza: Excel 886.462.227 · dashboard 529.325.542
SELECT
    c.codigo_classe,
    f.identificador_fundo            AS cnpj_fundo,
    min(i.data_competencia)          AS de,
    max(i.data_competencia)          AS ate,
    sum(i.captacao - i.resgate)      AS captacao_liquida
FROM marketdata.silver.cvm_informe_diario i
JOIN marketdata.silver.anbima_classes_fundo c
    ON c.codigo_classe = i.codigo_classe
JOIN marketdata.silver.anbima_fundo f
    ON f.codigo_fundo = c.codigo_fundo
WHERE upper(c.nome_comercial_classe) LIKE '%MAPFRE CONFIANZA%'
GROUP BY c.codigo_classe, f.identificador_fundo
```

Três coisas a observar no resultado:

1. **Quantas linhas voltam.** Mais de uma classe para o mesmo CNPJ confirma a
   hipótese 1 — e a soma delas deve dar os 886 milhões do Excel.
2. **As datas `de` e `ate`.** Se não forem 01/06 a 30/06, é a hipótese 2.
3. **A plataforma.** Repetir o `JOIN` com `anbima_prestadores_classe` e conferir
   se Mapfre sai como XP, como Itaú, ou como os dois.

O script `procurar_mapfre.py`, já presente nesta pasta, faz a parte do prestador.

---

## 5. Enquanto não bate

O dashboard **não deve ser usado para número absoluto de captação** até a
conciliação fechar. O ranking relativo dentro de cada plataforma continua útil
como leitura direcional.

Vale registrar que o ranking exibido **não está ordenado por captação 30d** —
a sequência de `rank` não é monotônica em `cap30` em nenhuma das quatro
plataformas. Se a intenção é "top 30 por captação", isso é um segundo problema,
independente da divergência de valores, e está dentro do código, não na origem.
