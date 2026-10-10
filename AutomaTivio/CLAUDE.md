# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> O código, os comentários e a documentação deste projeto são em **português**.
> Mantenha assim — quem lê e mantém isto é o time de Marketing e Produtos da
> Tivio, não um time de engenharia.

> **`CONTEXTO_AUTOMATIVIO.md` é o guia completo e a fonte de verdade.** Este
> arquivo é o recorte curto dele, com o que importa para mexer no código. Em
> caso de divergência, vale o guia.

---

## O que é

`AutomaTivio` automatiza a edição **mensal** da Central de Materiais da Tivio
Capital. Um comando lê as planilhas do mês e publica: 13 relatórios de gestão
(HTML + PDF A4 + PPTX — 14 fundos marcados, menos o Atuarial, que não está no
DePara), as duas páginas por vertical, os posts, o e-mail, a Central e uma
planilha de conferência.

O produto principal é o **relatório de gestão**, e o critério de aceite dele é
**fidelidade aos PPTX publicados** — não "parecido". Os originais que serviram
de referência estão descritos em `docs/CONCILIACAO.md`.

---

## Comandos

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium        # uma vez só, para PDF e PPTX

python run.py                                # a edição inteira
python run.py --so banks alt180              # só estes fundos
python run.py --saidas html                  # pula PDF e PPTX (iterar rápido)
python run.py --conferir                     # calcula e valida, não escreve nada
python run.py --data-base 2026-08-31         # força a data base
python run.py --silencioso                   # só grava o log

# conciliação com os relatórios publicados (o teste que importa)
python docs/conciliar_com_pptx.py saida/_Historico/AAAA-MM/conferencia_AAAA-MM.xlsx
```

Não há suíte de testes unitários. **A verificação é a rodada completa**: zero
erros no log, o relatório de conciliação em 58/58 e os PDFs conferidos (A4,
número de páginas certo, nenhuma em branco).

Em ambiente headless, o Chromium costuma estar em
`/opt/pw-browsers/chromium-*/chrome-linux/chrome`; `exporters/pdf.py` procura
sozinho e aceita `TIVIO_CHROMIUM` como override.

---

## Arquitetura

### A regra central: um Contexto por fundo

`engine/contexto.py::ContextoFundo` é o **único** lugar de onde sai qualquer
número de um fundo. Relatório, post, e-mail e Central leem o mesmo objeto, e é
só por isso que o Infra Plus lê 1,26% nos quatro materiais. **Nunca** calcule um
número dentro de um renderizador: se falta um corte, ele nasce no Contexto (ou
numa função livre ao lado dele, como `agrupar_tipos`).

### O fluxo

```
entrada/*.xlsx + comentarios.docx
   │  loaders/          leem e dão cache
   ▼
calculators/metricas.py  rentabilidade, carteira, histórico
   ▼
engine/contexto.py       UM ContextoFundo por fundo  ◄── a fonte de verdade
   ▼
renderers/relatorio.py   monta a folha A4 por componentes Jinja
renderers/legado.py      injeta dados nos HTMLs desenhados à mão
   ▼
exporters/              html · pdf (Chromium) · pptx (python-pptx)
   ▼
saida/_Historico/AAAA-MM/        a edição completa (Central e materiais interativos)
   ▼  engine/publicacao.py
saida/_Atual/                    por área, nome fixo sem o mês: o que se publica
```

`engine/pipeline.py` orquestra em 6 etapas (ler → calcular → validar →
relatórios → materiais da Central → conferência). A Central é processada por
último de propósito: ela confere se os arquivos que os cards apontam existem.

### A data única

`engine/edicao.py` é a única data do sistema, com 9 formas derivadas (`iso`,
`br`, `mes_ano`, `slug`, `competencia`…). **Nenhuma data literal em lugar
nenhum** — nem em template, nem em nome de arquivo, nem em comentário de
material.

### Composição do relatório

`configs/relatorio.yml` define as seções **por vertical**, e cada seção é um
arquivo em `templates/componentes/`. Ligar, desligar ou mover uma seção de
página é editar YAML, não código. A composição do Crédito Estruturado é outro
produto (3 folhas, com treemap e colaterais), não uma variação da do high grade.

A folha é desenhada em **1000×1414 px** fixos (A4 na proporção 1,414). Quem
encolhe para caber é o CSS, via `zoom`:

- em tela: `--folha-zoom`, com degraus em media query e o valor exato vindo do JS;
- na impressão: `.folhas .rcard{zoom:0.79365}` em `templates/estilos/impressao.css`.

O seletor da impressão **precisa** ter especificidade ≥ à do enquadramento de
tela. Escrito como `.rcard`, o zoom de tela vence e cada folha estoura numa
página em branco. `exporters/pdf.py::_conferir_enquadramento` mede isso antes de
imprimir — se você mexer no CSS da folha e o aviso aparecer, é isso.

### CSS por responsabilidade

| arquivo | o que é |
|---|---|
| `_marca.css` | design system (tokens, fonte Versos, modo claro) |
| `relatorio.css` | **a folha A4** — mexa aqui para fidelidade ao PPTX |
| `pagina.css` | a casca da página por vertical (cabeçalho, hero, rodapé) |
| `abas.css` | as abas de fundo |
| `impressao.css` | `@page` e o zoom do PDF |
| `entrega.css` | só a barra escura do relatório solto |

`pagina.css` e `abas.css` foram **extraídos sem alterar uma linha** de
`templates/referencia/tivio-relatorio-gestao-credito-privado.html`, para a página
por vertical ter o mesmo visual do gerador oficial. Se precisar mexer, prefira
reextrair a reescrever.

### Materiais legados

Os posts, o e-mail e a Central continuam HTMLs feitos à mão (carrossel,
lightbox, treemap, exportação no navegador). `renderers/legado.py` só reescreve
os **literais de dados** via `renderers/jsobj.py::replace_literal`. Reescrevê-los
como Jinja trocaria material desenhado por uniformidade de código.

### Gráficos

SVG/HTML desenhado no Python (`calculators/grafico.py`: `barras_modelo`,
`historico_modelo`, `treemap`) no desenho do relatório publicado, e esse é o
desenho do servidor; só o histórico é redesenhado pelo ECharts, com a mesma
especificação (`data-tv`) e o acumulado no fim das linhas. `assets/relatorio_charts.js`
recorta o viewBox dos logos dos fundos e encolhe o texto `.tv-ajusta`
(comentário, disclaimer) até caber. A referência visual está em
`../_revisao/modelo/` (PDFs de agosto/2026 do Institucional 30 e do ALT 180).

---

## Armadilhas já pagas

- **ECharts embutido** em cada relatório dava 50 MB de saída. Fica em `vendor/`
  ao lado do HTML, com CDN só como reserva. Toda pasta que recebe HTML precisa
  do seu `vendor/` (`pipeline.LIBS_POR_PASTA`) — inclusive `relatorios/_fundos/`,
  de onde saem o PDF e o PPTX.
- **`crossorigin`** em `<script>` local quebra o carregamento em `file://`
  (origem opaca). Já aconteceu duas vezes.
- **`set_content()`** não tem URL base: caminho relativo não resolve. O PDF abre
  o arquivo por `file://`.
- **Nome de shape no PPTX mente** sobre o conteúdo da imagem: o shape
  `anbima-distribuicao…` contém o selo de *Gestão*. Nomeie pelo que a imagem
  mostra.
- **SVG do Illustrator** traz um `<rect>` de fundo sem fill; `_preparar_svg()`
  remove por tolerância (≥98% do viewBox), não por igualdade exata.
- **Comentário do gestor**: o texto é preservado **vírgula por vírgula**; só os
  marcadores `X%` são preenchidos. `tamanho_comentario()` ajusta o corpo da
  fonte para caber — a folha tem `overflow:hidden` e o que passa some sem aviso.
- **Credenciais**: `entrada/.env` está no `.gitignore` (`**/.env`). O código
  legado tinha credenciais ANBIMA escritas no fonte; não as replique — e o
  segredo antigo deve ser rotacionado antes de reusar a integração.

---

## Antes de considerar pronto

1. `python run.py` → **0 erros** (avisos conhecidos: fonte Versos sem rede, QR
   sem arquivo local, BVP sem logo, Tivio Atuarial fora do DePara).
2. `python docs/conciliar_com_pptx.py saida/_Historico/AAAA-MM/conferencia_AAAA-MM.xlsx`
   → **58/58**.
3. PDFs: 13 arquivos, 210×297 mm, páginas certas, **nenhuma em branco**.
4. Se mexeu no CSS da folha ou da página: conferir 390 px, 768 px e 1440 px sem
   rolagem horizontal.
