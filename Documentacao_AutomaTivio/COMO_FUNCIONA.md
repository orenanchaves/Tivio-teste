# AutomaTivio · como funciona

Guia de cada processo da automação que monta a edição mensal da **Central de
Materiais da Tivio Capital**: o que entra, o que acontece em cada etapa, o que
sai e onde mexer. Escrito para quem vai rodar o mês, não para quem programa.

> O código fica em `AutomaTivio/`. Este guia fica fora dele de propósito, para
> ser lido sem abrir o projeto. O guia técnico completo continua em
> `AutomaTivio/CONTEXTO_AUTOMATIVIO.md`.

---

## 1. Em uma frase

Você troca as planilhas e o texto do gestor em `AutomaTivio/entrada/`, roda
**um comando**, e a automação devolve, numa pasta do mês, todos os materiais
prontos: relatórios de gestão (HTML, PDF e PPTX), carrosséis de Destaques (JPG e
PDF), e-mails (PNG e HTML), a Central de Materiais ligando tudo e uma planilha
que aponta o que conferir.

```bash
cd AutomaTivio
python run.py
```

Leva de 3 a 5 minutos. Também dá para dar dois cliques no `atualizar.bat`.

---

## 2. O mês na prática (passo a passo)

1. **Planilhas do mês** em `AutomaTivio/entrada/`:
   - `dados_mensais.xlsx` (cotas, carteira, DePara). **Não vai para o GitHub**:
     é grande e muda inteira todo mês. Copie a sua para essa pasta.
   - `taxas_global.xlsx` (taxa global e taxa de performance).
   - `tabela_spreads.xlsx` (Mercado de Crédito, ANBIMA).
2. **Comentários do gestor** em `AutomaTivio/entrada/comentarios.md`
   (um `## Nome do fundo` por fundo, parágrafos separados por linha em branco).
3. `python run.py`
4. Abra `saida/AAAA-MM/conferencia_AAAA-MM.xlsx` e olhe as abas
   **Divergências** e **Dados faltantes**.
5. Abra `saida/AAAA-MM/index.html`: ele abre a Central, de onde se chega a tudo.

**A data base não é digitada em lugar nenhum.** Ela sai do último mês fechado da
planilha. Para forçar: `python run.py --data-base 2026-09-30`.

---

## 3. O que sai, e onde

```
AutomaTivio/saida/AAAA-MM/
├── index.html                    ← COMECE AQUI: abre a Central
├── central/                      a Central de Materiais e os materiais interativos
│   ├── tivio-central.html        índice com todos os cards
│   ├── tivio-post-*.html         carrosséis de Destaques (editáveis na tela)
│   └── tivio-email-*.html        construtores de e-mail
├── relatorios/                   relatórios de gestão, um arquivo por vertical, fundos em abas
├── pdf/                          13 relatórios em PDF A4, texto selecionável
├── pptx/                         13 relatórios em PPTX, texto editável
├── destaques/                    carrosséis prontos para postar
│   ├── credito-privado/          01-…jpg a 08-…jpg + tivio-destaques-credito-privado.pdf
│   ├── credito-estruturado/      01-…jpg a 06-…jpg + PDF
│   └── investment-solutions/     01-…jpg a 11-…jpg + PDF
├── emails/                       e-mail de Fundos de Crédito, uma pasta por versão
│   ├── agora/  btg/  xp/  quadrado/
│   │   ├── tivio-email-<fundo>.png     um card por fundo
│   │   ├── tivio-email-completo.png    o e-mail inteiro
│   │   └── email-<versao>.html         pronto para o disparo
├── conferencia_AAAA-MM.xlsx      o que mudou, o que faltou, o que não bateu
└── AAAA-MM-processamento.log     registro completo da rodada
```

Os números dos arquivos (`01-`, `02-`…) seguem a ordem do carrossel, para o
Explorer ordenar na sequência certa.

---

## 4. Cada processo, por dentro

A rodada tem 6 etapas. Cada uma registra o que fez no log e na conferência.

### 4.1 Leitura das entradas

- Lê a `dados_mensais.xlsx` (abas DePara, Benchmark, Base Carteira, feriados,
  Dados). Na primeira vez demora 1 a 2 minutos; depois usa um cache e fica rápido.
- Lê taxas, spreads, comentários e a planilha de ajustes manuais.
- Descobre a **data base**: o último mês fechado com cota.

### 4.2 Cálculo (um "Contexto" por fundo)

Para cada fundo, a automação calcula **uma vez** e guarda num único lugar:

- rentabilidade em Mês, Ano, 12M, 24M, 36M e Desde o início, mais o benchmark,
  o Alfa, o % do benchmark e o CDI+;
- carteira: emissores, setores, rating, alocação por classe (treemap);
- histórico mês a mês para o gráfico;
- PL, PL médio de 12 meses, carrego, duration;
- taxas e textos (razão social, público alvo, informações operacionais).

**Todos os materiais leem esse mesmo lugar.** Por isso o relatório, o post, o
e-mail e a Central nunca discordam sobre um número.

Casos especiais já configurados:
- **Esplanada:** terceira linha no gráfico, *Bench Tributado* = IMA-B 5
  acumulado × 0,85 (benchmark líquido de 15% de IR).
- **ALT 180, ALT 90 e ALT Light:** taxa e performance do relatório publicado,
  que vencem a `taxas_global.xlsx`.
- **Legacy:** o cabeçalho mostra o CNPJ 09.166.056/0001-95; o da DePara
  continua sendo usado para buscar as taxas.

### 4.3 Validação (a conferência)

Antes de publicar, compara e avisa. Não reescreve nada sozinha:
- fundo sem dado no mês, carteira sem data ou atrasada;
- número citado no comentário que não bate com o calculado;
- comentário que trata outro mês como o mês corrente;
- % do benchmark fora de faixa;
- logo ou selo faltando.

Tudo vai para a `conferencia_AAAA-MM.xlsx`. Se houver **erro grave**, a rodada
para e não publica.

### 4.4 Relatórios de gestão

- Uma folha A4 por página, desenhada sobre os relatórios publicados de agosto/2026.
- **Crédito Privado: 4 páginas.** Objetivo e rentabilidade · emissores, rating e
  setores · histórico e comentário · Mercado de Crédito · características e
  disclaimer.
- Características gerais: as duas taxas (global e performance) juntas na coluna
  da esquerda; os dois patrimônios (PL e PL médio) juntos no pé da direita.
- **Crédito Estruturado (ALT): 3 páginas.** Treemap, estratégia, colaterais,
  histórico com a caixa CDI+, comentário, características e disclaimer.
- O layout se adapta ao conteúdo:
  - lista curta de setores (o Banks tem 2) faz as barras crescerem e ocuparem a coluna;
  - Mercado de Crédito curto (IPCA) estica as linhas até a nota;
  - comentário curto aumenta a fonte e fica centralizado, comentário longo diminui até caber;
  - razão social longa diminui o corpo para caber numa linha.
- **Gráfico histórico:** desenhado em ECharts, com o acumulado no fim de cada linha.
- **Saídas:** página por vertical em `relatorios/`, com botões PDF/JPG/PNG/PPTX
  para reexportar depois de editar um texto na tela. Também gera direto em
  `pdf/`, com texto selecionável, e `pptx/`, com fundo fiel e texto editável.
- Todo PDF é **reaberto e conferido**: número de páginas, tamanho A4 e texto
  selecionável.

### 4.5 Materiais da Central

- Os posts, os e-mails e a Central são HTMLs desenhados à mão. A automação só
  troca os **números e datas** dentro deles, sem mexer no desenho.
- A Central é montada por último: ela confere se cada card aponta para um arquivo
  que existe, e tira o card que apontaria para link quebrado.
- Todas as páginas têm o botão **Central de Materiais** para voltar.

### 4.6 Exportação dos carrosséis e dos e-mails

O Python abre cada material no navegador e usa **a mesma função do botão** da
página, então o arquivo sai idêntico ao que sairia clicando:
- **Destaques:** JPG 2160 × 2880 de cada página e um PDF por carrossel
  (1080 × 1440 pt, renderizado em 4×).
- **E-mails:** as quatro versões (Ágora, BTG, XP e Quadrado), PNG de cada card,
  PNG do e-mail completo e o HTML de disparo.

Para desligar algum formato: `AutomaTivio/configs/edicao.yml` → `saidas:`.

---

## 5. Onde mexer em cada coisa

| Quero… | Mexo em… |
|---|---|
| Texto do comentário do gestor | `entrada/comentarios.md` (`## Fundo`). Marcadores como `{mes}` e `{pct_mes}` viram o número do mês |
| Corrigir um número pontual (taxa, PL, carrego) | `entrada/preenchimento_manual.xlsx`, aba Overrides |
| Razão social, CNPJ exibido, público alvo, aplicação/resgate | `configs/fundos.yml`, no bloco do fundo |
| Taxa ou performance diferente da planilha | `configs/fundos.yml` → `taxa:` / `performance:` |
| Linha de benchmark tributado em outro fundo | `configs/fundos.yml` → `bench_tributado: 0.85` |
| Ligar/desligar um material ou um formato | `configs/edicao.yml` → `materiais:` / `saidas:` |
| Ordem e seções das páginas do relatório | `configs/relatorio.yml` |
| Visual da folha (cores, tamanhos) | `templates/estilos/relatorio.css` |
| Logo de um fundo | o SVG em `assets/logos/`, sempre **horizontal** e com o texto em curvas |
| Texto jurídico do rodapé | `configs/disclaimer.md` |

---

## 6. Comandos úteis

```bash
python run.py                          # a edição inteira
python run.py --so banks alt180        # só estes fundos (mais rápido)
python run.py --saidas html            # só os HTML, sem PDF/PPTX/JPG (para iterar)
python run.py --conferir               # calcula e confere, não grava nada
python run.py --data-base 2026-09-30   # força a data base
python -m exporters.pdf "x.html" "x.pdf"   # converte qualquer HTML em PDF A4
```

Para instalar no PC (uma vez só):

```bash
python -m pip install -r AutomaTivio/requirements.txt
python -m playwright install chromium
```

---

## 7. Antes de publicar (checklist)

1. A rodada termina com **0 erros**. Avisos conhecidos e aceitáveis: Atuarial fora
   da DePara, BVP sem logo, QR sem arquivo local, carteira sem data no Infra Plus
   e no Esplanada.
2. Na `conferencia_AAAA-MM.xlsx`, a aba **Divergências** não tem número do
   comentário diferente do calculado nem mês errado.
3. Abrir um PDF de cada vertical: 4 páginas no Crédito Privado, 3 no
   Estruturado, nenhuma em branco.
4. Abrir `destaques/` e `emails/` e conferir uma imagem de cada pasta.

---

## 8. O que ainda depende de você

- **`dados_mensais.xlsx`** de cada mês: não vem no GitHub.
- **Comentários de setembro:** já estão em `entrada/comentarios.md`. Os de agosto
  ficaram guardados em `entrada/comentarios_2026-08.md`.
- **BVP:** sem logo em `assets/logos/`.
- **Tivio Atuarial:** fora da DePara da planilha, então não gera relatório.
- **Botão "Voltar ao C&M Hub"** da Central: aponta para uma página que não existe
  no projeto.

---

## 9. Download

O pacote completo (código + saída de agosto) fica na Release **AutomaTivio v2**:
<https://github.com/orenanchaves/Tivio-teste/releases/download/AutomaTivio_v2/AutomaTivio_v2.zip>
