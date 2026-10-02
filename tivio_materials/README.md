# Central de Materiais · plataforma de atualização mensal

Ambiente Python que atualiza **todos os materiais recorrentes** da Tivio a partir
das planilhas do mês. Troca as planilhas, escreve os comentários, roda um comando:

```powershell
python run.py
```

Saída em `reports/AAAA-MM/`: HTML, PDF, PPTX, a `conferencia_AAAA-MM.xlsx` e o log.

---

## O problema que isto resolve

Hoje cada material guarda a sua própria cópia dos dados, dentro de um objeto
JavaScript no HTML, atualizada à mão. A consequência aparece no material
publicado — três exemplos levantados na análise da Central:

| O que saiu | Onde |
|---|---|
| Infra Plus com **1,10%** no mês no e-mail e **1,24%** no post e no relatório | 1,24% é o número do **IMA-B 5**, não do fundo |
| Banks com **1,01%** no comentário do relatório e **1,23%** no e-mail | "101% do CDI" é incompatível com 1,01% quando o CDI é 1,22% |
| Caixa do Banks **23,5%** no relatório e **23,7%** no post | mesma carteira, dois arredondamentos |

Nenhum é erro de digitação isolado: é o efeito de ter **N cópias do mesmo dado**.
A plataforma resolve pela estrutura — um `Contexto` por fundo, lido por todos os
materiais. Para divergirem, alguém precisaria escrever código que divirja.

---

## Fluxo mensal

```powershell
# 1ª vez
python -m pip install -r requirements.txt
python -m playwright install chromium     # só para exportar PDF

# todo mês
# 1) substituir entrada\dados_mensais.xlsx e entrada\taxas_global.xlsx
# 2) escrever os comentários em entrada\comentarios.md
# 3) gerar
python run.py
# 4) conferir reports\AAAA-MM\conferencia_AAAA-MM.xlsx (abas Divergencias e Dados faltantes)
```

Opções:

| Comando | Para que |
|---|---|
| `python run.py --conferir` | calcula e valida **sem escrever material** — use antes de fechar o mês |
| `python run.py --so banks infraplus` | gera só esses fundos |
| `python run.py --saidas html` | pula PDF e PPTX (mais rápido ao iterar) |
| `python run.py --data-base 2026-08-31` | força a data base |

---

## A data única

```yaml
# configs/edicao.yml
data_base: 2026-08-31     # vazio = último mês fechado disponível na planilha
```

Dela saem todas as formas em que a data aparece — e são nove:

| Forma | Onde aparece |
|---|---|
| `31/08/2026` | "Data base:" no rodapé da tabela |
| `Agosto de 2026` | cabeçalho de cada página |
| `Agosto 2026` | cards da Central, nome dos arquivos |
| `ago26` | sufixo de arquivo exportado |
| `2026-08` | pasta da edição, conferência, log |
| `agosto/2026`, `AGOSTO DE 2026` | textos no corpo dos materiais |
| `const ATUAL=7` | aba de edição ativa nos HTMLs legados |

Centralizar só o *valor* não bastaria: se cada material formatasse do seu jeito,
a divergência voltaria pela formatação. Por isso a `Edicao` (em
`engine/edicao.py`) centraliza as formas também.

---

## Comentários do gestor

`entrada/comentarios.md` — Markdown, um título por fundo:

```markdown
# Relatório

## Banks

No mês, o mercado de crédito privado high grade manteve o movimento de
fechamento gradual de spreads...

O fundo rendeu {mes} ({pct_mes} do {bench}) e acumula {ano} no ano. O carrego
está em {bench} +{carrego}, com duration de {duration}.
```

O título casa pela chave **ou** pelo nome do fundo, ignorando acento e caixa.

### Marcadores

O gestor escreve `{mes}`; o sistema põe o número. Isso existe porque a
alternativa — digitar o número no texto — é a origem da divergência do Banks
acima; e porque o método do gerador antigo (trocar o conteúdo de cada `<b>` por
posição) quebra quando o parágrafo ganha um negrito a mais, sem avisar.

| Marcador | Dá |
|---|---|
| `{mes}` `{ano}` `{12m}` `{24m}` `{36m}` `{inicio}` | retorno do fundo no período |
| `{pct_mes}` `{pct_ano}` `{pct_12m}` `{pct_inicio}` | % do benchmark |
| `{alfa_mes}` `{alfa_ano}` `{alfa_12m}` | Alfa |
| `{bench_mes}` `{bench_ano}` | retorno do benchmark |
| `{bench}` `{nome}` | nome do benchmark / do fundo |
| `{carrego}` `{duration}` `{credito}` | carteira |
| `{pl}` `{pl_medio}` | patrimônio |
| `{data_base}` `{mes_ano}` `{mes_nome}` | data da edição |

Marcador desconhecido fica **visível no texto** (`{foo}`) e entra na conferência
— o oposto de um número errado que passa.

---

## Relatório de Gestão, por componentes

O produto principal. 12 fundos × 4 páginas, montados a partir de
`configs/relatorio.yml`:

```yaml
secoes:
  - {id: objetivo,        pagina: 1, titulo: OBJETIVO DA CARTEIRA}
  - {id: rentabilidade,   pagina: 1, titulo: RENTABILIDADE}
  - {id: emissores,       pagina: 1, titulo: PRINCIPAIS EMISSORES}
  ...
por_fundo:
  altlight:
    desligar: [mercado_credito]
```

Apagar uma linha remove a seção; a página se refaz e a numeração "1 / 4" segue,
porque é contada depois da composição. Uma seção sem dado nesta edição é omitida
em vez de desenhar um bloco vazio — e o log diz qual foi omitida.

Cada seção é um arquivo em `templates/componentes/`. O CSS em
`templates/estilos/relatorio.css` foi **extraído do gerador HTML oficial**, para o
template reproduzir o layout publicado e não um layout parecido.

### O gráfico histórico

O relatório publicado hoje mostra uma curva que **não é o histórico do fundo**:
`histSVG()` interpola uma reta do zero até o valor final, com um ruído para
parecer orgânico. Aqui a série é a real, apurada pelas cotas de fechamento de cada
mês (`calculators/grafico.py`), em SVG — que no PDF sai vetor.

---

## Exportação

### PDF

Chromium headless, com a configuração que separa PDF institucional de impressão
de navegador:

| Sintoma de "impressão de navegador" | O que evita |
|---|---|
| cabeçalho/rodapé do navegador | `display_header_footer=False` |
| margem de 1 cm em volta | `margin=0` + `@page{margin:0}` |
| fundo branco onde devia ter faixa | `print_background=True` |
| página fora do A4 | `@page{size:210mm 297mm}` + `prefer_css_page_size` |
| conteúdo cortado no meio | `break-after:page` por folha |

O texto sai como texto (selecionável, fonte incorporada) e as linhas do gráfico
como vetor. Se a fonte Versos não carregar do CDN, o PDF é gerado **com aviso** —
a métrica do texto muda e isso precisa aparecer na conferência, não passar.

### PPTX

Nativo por padrão: texto em text boxes, rentabilidade e Mercado de Crédito como
**tabelas do PowerPoint**, histórico como **gráfico de linhas nativo** — tudo
editável. Se um bloco não se reconstruir, cai para slide-imagem em alta resolução
e **o log diz qual caiu**, para ninguém receber um arquivo meio-editável sem saber.

---

## Conferência

`reports/AAAA-MM/conferencia_AAAA-MM.xlsx`:

| Aba | Conteúdo |
|---|---|
| **Divergencias** | o que não faz sentido e precisa de olho humano |
| **Dados faltantes** | campo que o material mostra e esta edição não calculou |
| Mudancas | todo campo que trocou de valor, com antes e depois |
| Fundos sem atualizacao | fundo da config que não casou com a DePara |
| Rentabilidades | os 6 períodos × todos os fundos, em número cru |
| Taxas | taxa global e performance por CNPJ |
| Avisos · Arquivos | o log e o que foi gerado |

As checagens são de sanidade: fundo idêntico ao benchmark em todos os períodos
(coluna trocada), % do CDI fora de 0–300% (unidade errada), carteira defasada mais
de 45 dias ou **sem data**, comentário citando outro mês.

A validação roda **antes** de gerar. Validar depois produz o pior caso: arquivos
prontos e com número errado, já na pasta de onde alguém vai publicar. Com
`parar_em_erro: true`, um erro grave interrompe antes de escrever qualquer coisa.

---

## Estrutura

```
tivio_materials/
├─ run.py                     ← o comando
├─ configs/
│   ├─ edicao.yml             ← DATA_BASE e o que gerar
│   ├─ fundos.yml             ← 20 fundos; 12 com relatório
│   └─ relatorio.yml          ← composição por seções
├─ entrada/                   ← planilhas do mês + comentarios.md
├─ engine/
│   ├─ edicao.py              ← a data única e suas formas
│   ├─ cadastro.py            ← config ↔ DePara
│   ├─ contexto.py            ← o dado único por fundo
│   ├─ governanca.py          ← log da execução
│   └─ pipeline.py            ← a rodada
├─ loaders/                   ← planilha (com cache), taxas, comentários
├─ calculators/               ← fórmulas, formatação pt-BR, gráficos SVG
├─ templates/
│   ├─ relatorio.html         ← folha A4
│   ├─ componentes/           ← uma seção por arquivo
│   ├─ estilos/               ← CSS da marca e do relatório
│   └─ materiais/             ← HTMLs legados (posts, e-mail, Central)
├─ renderers/
│   ├─ relatorio.py           ← monta o relatório por componentes
│   └─ legado.py              ← injeta dados nos HTMLs desenhados à mão
├─ exporters/                 ← html · pdf · pptx
├─ validations/               ← conferência
├─ assets/logos/              ← 53 SVGs dos fundos
├─ reports/AAAA-MM/           ← saída
└─ logs/
```

### Por que os materiais legados continuam HTML

Os posts, o e-mail e a Central são HTMLs feitos à mão, com carrossel, lightbox,
treemap e exportação no próprio navegador. Reescrevê-los como template Jinja
trocaria material desenhado por uniformidade de código — troca ruim. Então eles
seguem sendo a fonte do layout, e o `renderers/legado.py` só reescreve os
literais de dados. O que mudou é **de onde vem o número**: agora do mesmo
`Contexto` que alimenta o relatório.

---

## Fundo novo

1. Uma entrada em `configs/fundos.yml` (`nome`, `vertical`, `carteira` ou `busca`,
   `logo`, `objetivo`, `operacional`).
2. O logo em `assets/logos/<vertical>/`.
3. `python run.py --so <chave>`.

Não precisa mexer em código. Se a `carteira` não casar com a DePara, o fundo
aparece na aba **Fundos sem atualizacao** com os candidatos próximos — em vez de
sair do material em silêncio.

---

## Escala

A arquitetura separa origem, cálculo, template e exportação, então o que vem
depois entra sem reescrever:

- **banco de dados** no lugar da planilha → um módulo novo em `loaders/`, mesmo
  contrato de saída (é o que o `Update_Monitor_Novos_Fundos` já faz com o Databricks)
- **Airflow / agendamento** → `Pipeline().rodar()` é uma chamada, sem estado global
- **SharePoint / WordPress** → um exportador novo em `exporters/`
- **material novo** → um template em `templates/` e uma linha em `configs/edicao.yml`
