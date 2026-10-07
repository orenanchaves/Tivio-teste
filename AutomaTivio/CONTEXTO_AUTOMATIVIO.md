# AutomaTivio · guia completo

> Tudo sobre o ambiente que atualiza a edição **mensal** da Central de Materiais
> da Tivio Capital: o que faz, como rodar no seu PC, como é por dentro, o que já
> foi conferido contra os relatórios publicados e o que ainda falta.
>
> Visão de processo, para quem roda o mês: `../Documentacao_AutomaTivio/COMO_FUNCIONA.md`.
>
> Documento único e autossuficiente — dá para abrir só ele e trabalhar.
> Última revisão: **10/2026**.
>
> *(O `CLAUDE.md` ao lado é o recorte curto deste documento, escrito para a IA
> que mexe no código. Se os dois divergirem, este aqui vale.)*

---

## Índice

1. [O que é e o que entrega](#1-o-que-é-e-o-que-entrega)
2. [Instalar no seu PC](#2-instalar-no-seu-pc)
3. [O mês na prática](#3-o-mês-na-prática)
4. [Onde fica cada coisa](#4-onde-fica-cada-coisa)
5. [Como funciona por dentro](#5-como-funciona-por-dentro)
6. [O relatório de gestão](#6-o-relatório-de-gestão)
7. [Fidelidade aos PPTX publicados](#7-fidelidade-aos-pptx-publicados)
8. [Onde mexer para cada coisa](#8-onde-mexer-para-cada-coisa)
9. [Armadilhas já pagas](#9-armadilhas-já-pagas)
10. [Pendências conhecidas](#10-pendências-conhecidas)
11. [Checklist antes de publicar](#11-checklist-antes-de-publicar)
12. [Segurança](#12-segurança)

---

## 1. O que é e o que entrega

Todo mês os materiais da Central eram atualizados à mão: abrir cada PPTX, trocar
número por número, exportar PDF, recortar imagem para o post, reescrever o
e-mail, trocar as datas em cada lugar. Um fundo com dado errado só aparecia
depois de publicado.

O AutomaTivio troca isso por **um comando**:

```powershell
python run.py
```

Ele lê as planilhas do mês e o documento de comentários do gestor, calcula tudo
**uma vez**, e publica:

| O que sai | Onde |
|---|---|
| **2 páginas por vertical** — fundos em abas, com botões de exportação | `saida/AAAA-MM/central/` ← **é o que você abre** (todos os HTML ficam aqui) |
| **13 relatórios em PDF A4** vetorial, um por fundo | `saida/AAAA-MM/pdf/` |
| **13 relatórios em PPTX**, um por fundo — idênticos à folha, texto editável (`exporters/pptx_fiel.py`) | `saida/AAAA-MM/pptx/` |
| Posts, e-mail e a **Central de Materiais** | `saida/AAAA-MM/central/` |
| **Carrosséis de Destaques** em JPG (2160 × 2880) + pacote PDF, uma pasta por vertical | `saida/AAAA-MM/destaques/<vertical>/` |
| **E-mails** em PNG (cards + completo) + HTML de disparo, uma pasta por versão | `saida/AAAA-MM/emails/<versao>/` |
| `index.html` que abre a Central | `saida/AAAA-MM/` |
| **`conferencia_AAAA-MM.xlsx`** — o que mudou, o que faltou, o que não bateu | `saida/AAAA-MM/` |
| Log da rodada | `saida/AAAA-MM/AAAA-MM-processamento.log` |

### Os fundos com relatório

| Fundo | Vertical |
|---|---|
| Tivio Banks · Institucional · Institucional 15 · Institucional 30 | Crédito Privado |
| Infra Plus · Infra Plus CDI · Esplanada · Legacy Prev · BVP · RF CP | Crédito Privado |
| Tivio Atuarial | Crédito Privado *(marcado, mas não sai — ver §10)* |
| ALT 180 · ALT 90 · ALT Light | Crédito Estruturado |

São **14 marcados** no `configs/fundos.yml` e **13 que saem**: o Atuarial não
está no DePara da planilha. O `configs/fundos.yml` tem outros 8 fundos (Top
Gestor, Prev Low Vol…) que entram nos posts e no e-mail, mas não têm relatório.

### Dois passos, de propósito

```
1. python run.py      →  as telas em HTML, com os dados do mês   (automático)
2. botões na tela     →  PDF · PPTX · JPG · PNG                  (você clica)
```

O Python entrega a tela certa; quem sabe qual formato precisa é quem vai usar. A
exportação pelo botão leva **só o fundo que está na aba ativa**. Os PDFs e PPTX
de todos também saem direto do `run.py`, porque são 13 por edição e abrir 13
páginas para clicar 13 vezes não é fluxo — o botão existe para quando você
ajusta um texto na tela e quer reexportar aquele.

---

## 2. Instalar no seu PC

Uma vez só:

```powershell
cd AutomaTivio
python -m pip install -r requirements.txt
python -m playwright install chromium
```

O segundo comando baixa o navegador que gera o PDF. Sem ele, o HTML sai normal e
o PDF/PPTX falham com aviso.

Se faltar alguma dependência, o `run.py` **diz qual e qual é o comando** — ele
traduz o nome do módulo para o nome no pip (`No module named 'yaml'` é o pacote
`PyYAML`, o que o erro padrão do Python não conta).

### ⚠️ Uma planilha não vem no repositório

| Arquivo em `entrada/` | Está no GitHub? |
|---|---|
| **`dados_mensais.xlsx`** | **Não** — 31 MB, trocado todo mês. Está no `.gitignore`. |
| `taxas_global.xlsx` · `tabela_spreads.xlsx` | sim (28 KB / 48 KB) |
| `comentarios.docx` · `comentarios.md` | sim |
| `preenchimento_manual.xlsx` | sim |

Depois de clonar, **copie a sua `dados_mensais.xlsx` para `entrada/`** antes de
rodar. Sem ela o `run.py` para na primeira etapa dizendo que não encontrou a
entrada — não gera material pela metade.

Ela fica de fora porque são 31 MB que mudam inteiros todo mês: doze edições
versionadas seriam ~370 MB de planilha binária, que o git não consegue
comprimir. As outras entradas são pequenas e ficam no repositório, inclusive
como exemplo do formato esperado.

### Comandos

```powershell
python run.py                       # a edição inteira
python run.py --so banks alt180     # só estes fundos
python run.py --saidas html         # pula PDF e PPTX (mais rápido ao iterar)
python run.py --conferir            # calcula e valida, não escreve nada
python run.py --data-base 2026-08-31  # força a data base
python run.py --silencioso          # não imprime; só grava o log

# qualquer HTML -> PDF A4 vetorial, texto selecionável (padrão da skill html-to-pdf)
python -m exporters.pdf "pagina.html" "pagina.pdf"
python -m exporters.pdf "pagina.html" "pagina.pdf" --paginas=4   # avisa se der outro número
```

Todo PDF gerado é reaberto e conferido: número de páginas, tamanho A4 e texto
selecionável em todas as páginas. O que não bater vira aviso no log.

E o teste que importa:

```powershell
python docs\conciliar_com_pptx.py saida\AAAA-MM\conferencia_AAAA-MM.xlsx
```

Há também `atualizar.bat` para quem prefere dar dois cliques.

---

## 3. O mês na prática

1. Trocar em `entrada/`: **`dados_mensais.xlsx`**, **`taxas_global.xlsx`**,
   **`tabela_spreads.xlsx`**. *(A `dados_mensais.xlsx` não vem no repositório —
   ver §2.)*
2. Colocar os comentários do gestor em **`entrada/comentarios.docx`**.
3. `python run.py`
4. Conferir **`saida/AAAA-MM/conferencia_AAAA-MM.xlsx`** — abas *Mudanças*,
   *Dados faltantes*, *Fundos sem atualização*, *Rentabilidades*, *Taxas*.
5. Abrir **`saida/AAAA-MM/index.html`** (abre a Central; todos os HTML ficam em `central/`) e exportar o que precisar pelos botões.

**A data base não é digitada em lugar nenhum**: sai do último mês fechado da
planilha. Para forçar, `configs/edicao.yml` → `data_base: 2026-08-31`.

**Ligar e desligar material** sem mexer em código: `configs/edicao.yml` →
`materiais:`. Material desligado é **copiado sem atualizar**, para o card da
Central não virar link morto.

**Correções pontuais** que não cabem na planilha: `entrada/preenchimento_manual.xlsx`
(taxa, performance, carrego, duration, PL, PL médio). As linhas de exemplo
começam com `#` e são ignoradas.

**Comentários:** o `.docx` do gestor é a fonte principal; o `comentarios.md` ao
lado cobre o que ele não traz. O texto é preservado **vírgula por vírgula** —
só os marcadores `X%` são preenchidos com o número calculado.

---

## 4. Onde fica cada coisa

```
AutomaTivio/
├── run.py                    # o comando único
├── atualizar.bat             # o mesmo, com dois cliques
├── CONTEXTO_AUTOMATIVIO.md   # este documento
├── CLAUDE.md                 # o recorte curto, para a IA que mexe no código
├── README.md                 # visão geral
│
├── entrada/                  # ← O QUE VOCÊ COLOCA
│   ├── dados_mensais.xlsx    #   Base Carteira, Dados, DePara, cotas, feriados
│   ├── taxas_global.xlsx     #   taxa de administração e performance
│   ├── tabela_spreads.xlsx   #   Mercado de Crédito (tabela setorial)
│   ├── comentarios.docx      #   texto do gestor, por fundo
│   ├── comentarios.md        #   complemento do .docx
│   ├── preenchimento_manual.xlsx   # correções pontuais
│   └── imagens/              #   imagens para os materiais (nada entra sozinho)
│
├── configs/
│   ├── edicao.yml            # a data e o que gerar
│   ├── fundos.yml            # 22 fundos; 14 marcados com relatório
│   ├── relatorio.yml         # composição das folhas, POR VERTICAL
│   └── disclaimer.md         # o disclaimer real, extraído do PPTX
│
├── engine/
│   ├── edicao.py             # A DATA ÚNICA e suas 9 formas derivadas
│   ├── cadastro.py           # configs ↔ DePara da planilha
│   ├── contexto.py           # O DADO ÚNICO por fundo  ← o coração
│   ├── governanca.py         # log da execução
│   └── pipeline.py           # a rodada, em 6 etapas
│
├── loaders/                  # leitura das planilhas (com cache), taxas, comentários
├── calculators/              # fórmulas, formatação pt-BR, gráficos SVG
│
├── templates/
│   ├── relatorio.html        # a folha A4 (relatório solto)
│   ├── relatorio_vertical.html   # a página por vertical, com abas
│   ├── componentes/          # uma seção do relatório por arquivo
│   ├── estilos/              # o CSS, separado por responsabilidade
│   └── materiais/            # os HTMLs legados (posts, e-mail, Central)
│
├── renderers/
│   ├── relatorio.py          # monta a folha por componentes
│   ├── legado.py             # injeta dados nos HTMLs desenhados à mão
│   └── jsobj.py              # troca literais de dados no JS sem reescrever o arquivo
│
├── exporters/                # html · pdf (Chromium) · pptx (python-pptx)
├── validations/              # a conferência
├── docs/                     # CONCILIACAO.md + o script de conciliação
│
├── assets/
│   ├── logos/                # 53 SVGs dos fundos
│   ├── selos/                # ANBIMA ×2, PRI (extraídos dos PPTX)
│   ├── icones/               # ícones de COLATERAIS (extraídos dos PPTX)
│   ├── marca/                # a marca Tivio
│   ├── fontes/               # Versos local, opcional (PDF sem rede)
│   └── vendor/               # Apache ECharts 5.6.0 e libs de exportação
│
└── saida/                    # ← O QUE SAI, uma pasta por mês
    └── AAAA-MM/
        ├── index.html        #   porta de entrada: abre a Central, que liga tudo
        ├── relatorios/       #   as duas páginas por vertical ← ABRA ESTAS
        ├── pdf/ pptx/ central/
        ├── conferencia_AAAA-MM.xlsx
        └── AAAA-MM-processamento.log
```

---

## 5. Como funciona por dentro

### O fluxo

```
entrada/*.xlsx + comentarios.docx
      │   loaders/          leem e dão cache
      ▼
  calculators/metricas.py   rentabilidade, carteira, histórico
      ▼
  engine/contexto.py        UM ContextoFundo por fundo  ◄── a fonte de verdade
      │
      ├──────────────┬──────────────┬──────────────┐
      ▼              ▼              ▼              ▼
  relatórios      posts         e-mail         Central
  (A4·PDF·PPTX)   (legados)     (legado)       (índice)
      │              │              │              │
      └──────────────┴──────────────┴──────────────┘
                     ▼
               saida/AAAA-MM/
```

`engine/pipeline.py` orquestra em 6 etapas: ler → calcular → validar →
relatórios → materiais da Central → conferência. **A Central é processada por
último de propósito**: ela confere se os arquivos que os cards apontam existem
de verdade, e remove o card se não existirem.

### A decisão que sustenta o resto

**Um `ContextoFundo` por fundo, lido por todos os materiais.**

Antes, cada material tinha a sua conta. O relatório dizia que o Infra Plus
rendeu 1,26%, o post dizia outra coisa, e ninguém sabia qual estava certo sem
refazer na mão. Hoje existe um objeto por fundo (`engine/contexto.py`) e **todo
número sai dele**: relatório, post, e-mail e Central leem o mesmo lugar.

> **Regra para quem for evoluir:** se faltar um corte de dado, ele **nasce no
> Contexto**, nunca dentro de um renderizador. Uma conta feita no renderizador
> volta a ser exatamente a divergência que o projeto existe para eliminar.

### A data única

`engine/edicao.py` é a única data do sistema, com 9 formas derivadas: `iso`
(2026-08-31), `br` (31/08/2026), `mes_ano` (Agosto de 2026), `mes_ano_curto`
(Ago 2026), `slug`, `competencia` (2026-08), `mes_nome`, `mes_indice_js`.

**Nenhuma data literal em lugar nenhum** — nem em template, nem em nome de
arquivo, nem em texto de material. Trocar o mês é trocar uma variável.

### Os materiais legados

Os posts, o e-mail e a Central continuam **HTMLs feitos à mão** — carrossel,
lightbox, treemap, exportação no próprio navegador. O `renderers/legado.py` só
reescreve os **literais de dados** dentro deles.

Reescrevê-los como template Jinja trocaria material desenhado por uniformidade
de código, o que é troca ruim. Eles seguem sendo a fonte do layout; o que mudou
é **de onde vem o número** — agora do mesmo Contexto que alimenta o relatório.

### Previdência: páginas "Saiba mais", e-mail e Informativo (HGD30, HYD60)

Configuração em `configs/previdencia.yml`. Texto do gestor montado por
`renderers/landing.py::comentario_automatico`: parágrafos de mercado do fundo
`comentario.mercado_de` (Institucional, de `entrada/comentarios.md`, até a frase
"Nesse cenário…") + `comentario.frase` com marcadores + complemento da seção
do próprio fundo em `entrada/comentarios.md` (parágrafos que repetem o mercado
ou a frase são ignorados); tudo passa por `ctx.preencher`. O loader descarta
notas `<!-- -->` do .md. No Informativo,
`exporters/previdencia.py::_cabe` reduz o corpo da caixa até o texto caber. Os fundos `hgd30` e `hyd60` de
`configs/fundos.yml` apontam para as carteiras **FIFE** (PL e carteira); a
rentabilidade, o histórico e `serie_diaria` vêm da classe FIE em
`cotas_rentabilidade` (`Contexto._quantum_rentabilidade`, por prefixo do nome na
aba de cotas; sem cotas, cai no FIFE com aviso). Cortes no Contexto: `alocacao_hghy`, `composicao()` (Bancário por
setor, sobre o total da carteira), `rating_extras()`, a partir de `hghy_tipo`,
`tipo_aj`, `tipo_setor` e `rating_book` de `Calc.carteira`.

- `renderers/landing.py` + `templates/landing.html` → `central/tivio-<chave>-saiba-mais.html`.
- `renderers/previdencia.py::dados_fundo` junta tudo o que e-mail e Informativo
  mostram; `RenderizadorEmailPrevidencia` gera `central/tivio-email-previdencia.html`
  (blocos em `templates/previdencia/blocos.html` + `blocos.css`) e o HTML de
  disparo (`templates/previdencia/email_disparo.html`).
- `exporters/previdencia.py`: `exportar_email` (Playwright fotografa cada bloco;
  grava PNG, HTML e .eml com cid:) e `exportar_informativos` (python-pptx sobre
  o PPTX de `templates/informativos/`, mapa de shapes em `MAPAS`; os gráficos
  perdem o vínculo com a planilha Excel externa e ganham uma embutida; PDF pelo
  PowerPoint via COM). O `.oft` pelo Outlook existe (`oft=True`) mas fica
  desligado: sem perfil configurado o Outlook abre a tela de boas-vindas e trava.
- Pipeline: `_landings` e `_previdencia` depois dos relatórios; `_previdencia_saidas`
  depois dos e-mails. Cards na Central: landings `l4`/`l5`, e-mail `e3`, e os
  Informativos (`inf-*`) entram por `RenderizadorLegado.central`.

### Decks comerciais (`exporters/decks.py`, `configs/decks.yml`)

- Abre o PPTX do time (`templates/decks/`) e troca só os números, run a run
  (`_troca_trecho`), reconhecendo cada um pelo texto: capa, "Data base", PL,
  12M/ANO/MÊS, carrego, duration, `numero-top*`/`nome-top*`, "CDI + x% a.a." pelo
  rótulo acima (em coordenadas do slide, `_absoluta`, porque rótulo e valor
  ficam em grupos diferentes), gráfico Fundo x CDI (`ContextoFundo.serie_diaria`,
  `replace_data` sem o externalData) e as etiquetas do fim das linhas.
- Treemap dos ALT (`Preenchedor.alocacao`/`_redesenha`): rótulos "Nome 49,1%" +
  retângulo preenchido que contém o centro do rótulo (blocos podem estar soltos
  no slide e rótulos num grupo, com escala própria: `_escala_do_pai`,
  `_posiciona`). Squarify com área mínima de 3%; rótulo encolhe até 40%, quebra
  antes do número se preciso. Imagem no lugar do treemap vira blocos nativos
  (`_treemap_nativo`).
- Remoções: `_remove_selo_xp`, `_remove_roa` (rótulo "ROA" + valor fora do grupo),
  `_remove_slide` (ALT Light) e `_remove_cartao` (coluna da Família ALT).
- Conecta (`Conecta`): tabelas (`tabelas`), PL por rótulo (`pl_rotulado`),
  gráficos de barra/rosca reconhecidos pelas categorias (`graficos`: datas →
  `ContextoFundo.mensal`; Acumulado/Ano; notas de rating; Caixa/FIDC/Bancário/
  Corporativo; setores) e os rótulos "% CDI" dentro da caixa do gráfico, da
  esquerda para a direita. `decks.yml` → `slides:` mapeia slide → fundo e opções
  (`estilo: post` = `_estilo_post`, `textos` = `_troca_texto`, `alocacao_hghy`).
- `_estilo_post`: `_alinha_post` (grade L..R, vão G) → `_fundo_post` (gradiente
  em `p:bg` via `_fundo_do_slide`, orbes/arcos atrás de tudo) → `_reflui_post`
  (linhas A/B/C, características em `_em_colunas`, painel na altura da grade,
  `_destaque_pl`) → pintura de vidro (`_pinta`, que também troca forma livre
  por roundRect). Cópias de shape ganham `cNvPr id` novo (id repetido ou
  `txBody` sem `a:p` fazem o PowerPoint recusar o arquivo).
- `Pipeline._atual` copia `saida/AAAA-MM/` para `saida/_Atual/` no fim da rodada.
- PDF pelo PowerPoint (`exporters.previdencia._pdf_powerpoint`). Etapa
  `Pipeline._decks`, ligada por `saidas.decks` em `configs/edicao.yml`.

---

## 6. O relatório de gestão

### Composição por vertical

`configs/relatorio.yml` define as seções **por vertical**, e cada seção é um
arquivo em `templates/componentes/`. **Ligar, desligar ou mover uma seção de
página é editar YAML, não código.**

**Crédito Privado — 4 folhas**

| Folha | Seções |
|---|---|
| 1 | Objetivo · Rentabilidade · Principais Emissores + Alocação por Setor · Distribuição de Rating |
| 2 | Rentabilidade Histórica · Comentário do Gestor |
| 3 | Mercado de Crédito |
| 4 | Características Gerais · Disclaimer |

**Crédito Estruturado — 3 folhas**

| Folha | Seções |
|---|---|
| 1 | Objetivo · Rentabilidade · **Alocação Real da Carteira (treemap)** · Comentário do Gestor |
| 2 | **Alocação por Estratégia** + **COLATERAIS** · Rentabilidade Histórica · **CDI+ por período** |
| 3 | Características Gerais · Disclaimer |

A composição do Crédito Estruturado é **outro produto**, não uma variação da do
high grade. Aplicar a composição do high grade neles produz um relatório que não
existe.

### A folha A4

A folha é desenhada em **1000 × 1414 px** fixos — A4 na proporção exata
(1414/1000 = 1,414 = 297/210). Quem encolhe para caber é o CSS, via `zoom`:

- **em tela:** a variável `--folha-zoom`, com degraus em media query e o valor
  exato calculado pelo JS a partir da largura disponível;
- **na impressão:** `.folhas .rcard{zoom:0.79365}` em `estilos/impressao.css`,
  que leva a folha a 793,7 × 1122,3 px — exatamente A4 a 96 dpi.

`zoom` e não `transform:scale` porque o zoom **afeta o layout**: a folha passa a
*ocupar* o tamanho reduzido, então não sobra faixa cinza nem rolagem horizontal.

> ⚠️ O seletor da impressão **precisa** ter especificidade ≥ à do enquadramento
> de tela. Escrito como `.rcard`, o zoom de tela vence e **cada folha estoura
> numa página em branco** — o PDF é gerado sem erro nenhum e o defeito só
> aparece abrindo o arquivo. O `exporters/pdf.py` mede isso antes de imprimir e
> avisa.

O PDF sai **vetorial**, com fonte incorporada, página de 210 × 297 mm e quebra
controlada. Não é impressão de navegador.

### Os gráficos

SVG e HTML desenhados no Python (`calculators/grafico.py`: `barras_modelo`,
`historico_modelo`, `treemap`) no desenho do relatório publicado de
agosto/2026. A **rentabilidade histórica** é desenhada pelo ECharts
(`renderer: 'svg'`, texto selecionável no PDF) a partir da MESMA especificação
do SVG do servidor — cores, espessuras, margens, degrau e topo da grade,
rótulos do eixo X — e com o acumulado no fim de cada linha numa etiqueta da
cor dela. Se o ECharts não carregar, fica o SVG do servidor, igual. Barras e
treemap são só do servidor (atributo `data-dados`).

O `assets/relatorio_charts.js` agora faz duas coisas na abertura da página (e
de novo ao trocar de aba): recorta o `viewBox` dos logos dos fundos pelo
contorno do desenho (os SVGs vêm com muita margem interna) e reduz o corpo do
comentário do gestor e do disclaimer até caber na caixa (`.tv-ajusta`). No
comentário, o texto curto também cresce até o teto (`data-teto`) e fica
centralizado na caixa (`data-centro`), para não sobrar vão no pé.

---

## 7. Fidelidade aos PPTX publicados

O critério de aceite do relatório é **ser igual ao PPTX publicado**, não
parecido. Os doze originais (9 de Crédito Privado + 3 de Crédito Estruturado)
foram abertos e comparados **shape a shape**.

| Bloco | Como está |
|---|---|
| Tabela de rentabilidade · CP | Fundo · CDI · **Alfa** · **%** (4 linhas) |
| Tabela de rentabilidade · CE | Fundo · CDI · % · **CDI+** (4 linhas, sem Alfa) |
| Exceções | Infra Plus CDI `sem_alfa`; Banks / Infra Plus / Legacy `casas_pct: 2` |
| Alocação **real** da carteira (CE) | **Treemap** da coluna `Tipo aj.` com os nomes de `tipo_label` — é daí que vem "Liquidez" e a ausência de "LFSN" |
| Alocação por **estratégia** (CE) | Barras dos **setores** (12 + Caixa) |
| COLATERAIS (CE) | 5 cartões fixos, com os SVGs **extraídos do próprio PPTX** |
| CDI+ por período (CE) | Caixa sob a rentabilidade histórica: Desde o início · 12M · Mês |
| Setores (CP) | Os 20 maiores, do maior para o menor, com o Caixa na posição do seu peso (como no Institucional 30 publicado) |
| Rating (CP) | Barras horizontais, todas as notas, ordenadas por peso |
| Rentabilidade histórica | Desde o início do fundo, não 12 meses |
| Cabeçalho | Preto, logo **sempre horizontal** (no ALT a variante `_03`), razão social / CNPJ, o T à direita e a faixa verde na página 1 |
| Disclaimer | Os 4 parágrafos reais, extraídos do PPTX (3.689 caracteres) |
| Selos | ANBIMA ×2, Rating S&P, PRI — extraídos do PPTX, embutidos em base64 |
| Comentário do gestor | Texto preservado vírgula por vírgula; só os `X%` preenchidos |

### Três erros que a comparação pegou

Nenhum deles apareceria de outro jeito:

1. **Faltava a linha Alfa** na tabela de Crédito Privado. O código mostrava
   Alfa *ou* %, e oito dos nove publicados têm as duas.
2. **Os títulos do ALT estavam trocados.** "Alocação real da carteira de
   crédito" é o corte por **classe** e apontava para setores; "Alocação por
   estratégia" é o corte por **setor** e apontava para classe. Número certo no
   lugar errado não parece erro.
3. **A alocação real era barras**, e no original é **treemap** — retângulos
   proporcionais, que é como o relatório mostra de relance que metade da carteira
   é cota sênior de FIDC.

### O teste que vale

```powershell
python docs\conciliar_com_pptx.py saida\AAAA-MM\conferencia_AAAA-MM.xlsx
```

Hoje em **58 de 58 rentabilidades idênticas ao relatório publicado (100%)**.
Detalhes em `docs/CONCILIACAO.md`.

---

## 8. Onde mexer para cada coisa

### O CSS, por responsabilidade

| Arquivo | O que é |
|---|---|
| `estilos/_marca.css` | design system: tokens de cor, fonte Versos, modo claro |
| **`estilos/relatorio.css`** | **a folha A4** — mexa aqui para fidelidade ao PPTX |
| `estilos/pagina.css` | a casca da página por vertical (cabeçalho, hero, rodapé) |
| `estilos/abas.css` | as abas de fundo |
| `estilos/impressao.css` | `@page` e o zoom do PDF |
| `estilos/entrega.css` | só a barra escura do relatório solto |

`pagina.css` e `abas.css` foram **extraídos sem alterar uma linha** de
`templates/referencia/tivio-relatorio-gestao-credito-privado.html`, para a página
por vertical ter o mesmo visual do gerador oficial — não um parecido. Se
precisar mexer, prefira reextrair a reescrever.

### Receitas rápidas

| Quero… | Mexo em… |
|---|---|
| Mudar o visual de uma seção do relatório | `templates/componentes/<seção>.html` |
| Mudar cor, fonte, espaçamento da folha | `templates/estilos/relatorio.css` |
| Ligar/desligar/mover uma seção de folha | `configs/relatorio.yml` |
| Mudar o texto do cabeçalho da página por vertical | `templates/relatorio_vertical.html` |
| Adicionar um fundo | `configs/fundos.yml` (`nome`, `vertical`, `carteira`) + logo em `assets/logos/` |
| Mudar quantos setores aparecem | `setores_max` no fundo, em `configs/fundos.yml` |
| Tirar a linha Alfa de um fundo | `sem_alfa: true` |
| Casas decimais do % do benchmark | `casas_pct: 2` |
| Ligar/desligar um material do mês | `configs/edicao.yml` → `materiais:` |
| Mudar o disclaimer | `configs/disclaimer.md` |
| Trocar um selo | `assets/selos/<chave>.png` |
| Trocar o logo de um fundo no e-mail | o SVG em `assets/logos/` — o e-mail usa sempre a horizontal (branca no escuro, preta no claro), via `renderers/logos.py` |
| PPTX | `exporters/pptx_fiel.py`: cada slide é a folha renderizada sem texto (fundo) + cada bloco de texto como caixa nativa editável, na posição e no estilo medidos no navegador (rota "Image to PPTX" da skill ppt-master). Sem a fonte Versos instalada, o PowerPoint troca a fonte; o layout se mantém |
| Logo com texto digitado (`<text>`) | converter em curvas: o Legacy e o Esplanada foram convertidos com a Versos Bold (10/2026) |
| Formato quadrado do e-mail | versão **Ágora** (`square:true`) no `tivio-email-fundos-credito.html` (`squareCardHTML`) |

### Adicionar um fundo novo

1. Uma entrada em `configs/fundos.yml` (`nome`, `vertical`, `carteira` ou `busca`).
2. O logo em `assets/logos/` (SVG, nome `tivio_<slug>.svg`).
3. Se tiver relatório: `relatorio: true`.
4. Rodar e conferir os avisos.

---

## 9. Armadilhas já pagas

Cada uma destas custou uma rodada. Estão aqui para não custarem outra.

- **ECharts embutido** em cada relatório dava 50 MB de saída. Fica em `vendor/`
  ao lado do HTML, com CDN só como reserva. **Toda pasta que recebe HTML precisa
  do seu `vendor/`** (`pipeline.LIBS_POR_PASTA`) — inclusive a pasta de apoio
  `relatorios/_fundos/`, de onde saem o PDF e o PPTX. Sem ela, os 13 PDFs saem
  com a versão simplificada do gráfico, sem erro nenhum.
- **`crossorigin`** em `<script>` local quebra o carregamento em `file://`
  (origem opaca). Aconteceu duas vezes.
- **`set_content()`** não tem URL base: caminho relativo não resolve. O PDF abre
  o arquivo por `file://` — e isso tem outra vantagem: o PDF sai do **mesmo
  artefato** que a pessoa abre no navegador.
- **Nome de shape no PPTX mente** sobre o conteúdo da imagem: o shape
  `anbima-distribuicao-de-produtos-de-investimento` contém o selo de *Gestão de
  Recursos*. Nomeie pelo que a imagem mostra, conferindo com o olho.
- **SVG do Illustrator** traz um `<rect>` de fundo sem fill, que vira um
  retângulo preto atrás do logo. É removido por tolerância (≥98% do viewBox),
  não por igualdade exata — os valores não batem na casa decimal.
- **Logo por prefixo** dava o logo do "Infra Plus CDI" para o "Infra Plus". O
  casamento é por variante exata.
- **O ECharts trunca rótulo em silêncio.** Qualquer largura fixa em `axisLabel`
  some com o nome do setor sem erro — foi o que escondeu "Comércio atacadista e
  varejista". Dimensione pela largura real do bloco.
- **A Central processada primeiro** (ordem alfabética) julgava todos os links
  mortos, porque os arquivos ainda não existiam. Ela é a última etapa.
- **Material desligado** virava card com link morto. Agora é copiado sem
  atualizar.
- **O comentário do gestor** varia muito de tamanho (4 parágrafos no Infra Plus,
  7 no Banks). A folha tem `overflow:hidden`: o texto que passa **some sem
  aviso**. `tamanho_comentario()` ajusta o corpo da fonte, e o exportador mede e
  avisa se ainda assim passar.

---

## 10. Pendências conhecidas

| O que falta | Por quê | Como resolver |
|---|---|---|
| **SUBORDINAÇÃO** (só no ALT 90) | A Base Carteira não tem a coluna do nível de subordinação das cotas sênior | O dado precisa vir de outra fonte |
| **QR Code** no rodapé | No PPTX ele entra por link externo, não embutido | Salvar o QR do site como `assets/selos/qr.png` |
| **Fonte Versos** no PDF | Os `.woff2` vêm do CDN da marca; sem rede o PDF usa a fonte de reserva e a métrica do texto muda | Colocar os arquivos em `assets/fontes/` |
| **Tivio Atuarial** | Não está no DePara da planilha | Incluir no DePara |
| **BVP** sem logo | Não há SVG em `assets/logos` | Adicionar `tivio_bvp.svg` |

Nenhuma delas impede a rodada: todas saem como **aviso** no log e na conferência,
não como erro.

---

## 11. Checklist antes de publicar

1. `python run.py` → **0 erros**.
   Avisos conhecidos e aceitáveis: fonte Versos sem rede, QR sem arquivo local,
   BVP sem logo, Tivio Atuarial fora do DePara.
2. `python docs\conciliar_com_pptx.py saida\AAAA-MM\conferencia_AAAA-MM.xlsx`
   → **58/58**.
3. Os PDFs: **13 arquivos**, 210 × 297 mm, número de páginas certo (4 no Crédito
   Privado, 3 no Estruturado), **nenhuma página em branco**.
4. Abrir a `conferencia_AAAA-MM.xlsx` e olhar *Dados faltantes* e *Fundos sem
   atualização*.
5. Se mexeu no CSS da folha ou da página: conferir em **390 px, 768 px e
   1440 px** sem rolagem horizontal.

---

## 12. Segurança

- **`entrada/.env`** (token Databricks) está no `.gitignore` via `**/.env` e
  **não é versionado**.
- O script legado trazia **credenciais ANBIMA escritas direto no código**. Elas
  **não** foram copiadas para cá. O acesso deve usar variável de ambiente, e o
  segredo antigo **deve ser rotacionado** antes de reusar a integração.
- As imagens em `entrada/imagens/` não entram em material nenhum sozinhas — é de
  propósito. Imagem entrando automática em relatório é como material publicado
  sai errado.
