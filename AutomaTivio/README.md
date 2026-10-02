# Central de Materiais · plataforma de atualização mensal

Ambiente Python que atualiza **todos os materiais recorrentes** da Tivio a partir
das planilhas do mês.

O fluxo tem **dois passos**:

```
    1. python run.py          →  as telas em HTML, com os dados do mês
    2. botões na tela         →  PDF, PPTX, JPG, PNG, ZIP
```

O Python não tenta adivinhar o formato final: ele entrega a tela certa. Quem sabe
qual formato precisa é quem vai usar — e clica.

Os relatórios saem **também** em PDF e PPTX direto do `run.py`, porque são 13 por
edição e abrir 13 páginas para clicar 13 vezes não é fluxo. O botão existe para
o caso de a pessoa ajustar um texto na tela e querer reexportar aquele.

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
# 1ª vez — sem isto o run.py para e diz o que falta
python -m pip install -r requirements.txt
python -m playwright install chromium     # só para exportar PDF e PPTX

# todo mês
# 1) substituir entrada\dados_mensais.xlsx, entrada\taxas_global.xlsx
#    e entrada\tabela_spreads.xlsx
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

Três formatos aceitos, porque o texto chega em três formatos e converter seria
mais um passo manual: **`.docx`** (o documento do gestor, onde o título do fundo
é um parágrafo em negrito — a convenção que ele já usa), **`.md`** e **`.xlsx`**.

Mais de um arquivo pode ser lido junto; o primeiro que define um fundo vence.
É o que permite manter o documento do gestor como fonte principal e um `.md` ao
lado só com o que ele não cobre — hoje, os textos do ALT 90 e do ALT 180, que
chegaram por outro canal:

```yaml
# configs/edicao.yml
comentarios:
  - entrada/comentarios.docx
  - entrada/comentarios.md
```

Em Markdown, um título por fundo:

```markdown
# Relatório

## Banks

No mês, o mercado de crédito privado high grade manteve o movimento de
fechamento gradual de spreads...

O fundo rendeu {mes} ({pct_mes} do {bench}) e acumula {ano} no ano. O carrego
está em {bench} +{carrego}, com duration de {duration}.
```

O título casa pela chave **ou** pelo nome do fundo, ignorando acento e caixa.

**O texto não é alterado.** Nem pontuação, nem espaçamento, nem um número já
digitado. O sistema injeta valor onde há `{marcador}` e não toca em mais nada.
Os 13 comentários de agosto/2026 foram conferidos: saem do sistema byte a byte
iguais ao que entrou.

### Marcadores

O gestor escreve `{mes}`; o sistema põe o número. Isso serve para a lacuna que
ele deixaria em branco — o `X%` de "rentabilidade de X% no mês". E evita a
origem da divergência do Banks acima, sem obrigar ninguém a mudar o jeito de
escrever: número digitado à mão continua valendo.

O método do gerador antigo trocava o conteúdo de cada `<b>` por posição, e
errava calado quando o parágrafo ganhava um negrito a mais — o próprio código
avisava "revisar à mão" quando a contagem não batia.

| Marcador | Dá |
|---|---|
| `{mes}` `{ano}` `{12m}` `{24m}` `{36m}` `{inicio}` | retorno do fundo no período |
| `{pct_mes}` `{pct_ano}` `{pct_12m}` `{pct_inicio}` | % do benchmark |
| `{alfa_mes}` `{alfa_ano}` `{alfa_12m}` | Alfa |
| `{bench_mes}` `{bench_ano}` | retorno do benchmark |
| `{bench}` `{nome}` | nome do benchmark / do fundo |
| `{carrego}` `{duration}` `{credito}` | carteira |
| `{pl}` `{pl_medio}` | patrimônio |
| `{pct_anual_inicio}` | % do benchmark **anualizado** (≠ `{pct_inicio}`) |
| `{bench_mes}` `{bench_ano}` `{bench_inicio}` | retorno do benchmark |
| `{data_base}` `{mes_ano}` `{mes_nome}` | data da edição |

### O que a conferência faz com o texto que não muda

Não reescreve — confere. Cada percentual escrito é procurado entre os valores
que o fundo tem nesta edição; o que não aparece em lugar nenhum vira linha na aba
**Divergencias**. A tolerância é relativa (0,5%), não absoluta: uma folga fixa de
1 p.p. aceitaria 1,01% no lugar de 1,10%, que é exatamente o erro que a checagem
existe para pegar.

Também avisa quando o texto trata **outro mês como o mês corrente** — "Em
setembro, iniciamos posição" num relatório de agosto. Citar outro mês como
comparação ("os spreads abriram 5 bps em relação a julho") é normal e não gera
aviso.

Marcador desconhecido fica **visível no texto** (`{foo}`) e entra na conferência
— o oposto de um número errado que passa.

---

## Ajustes manuais (`entrada/preenchimento_manual.xlsx`)

É a **exceção, não a rotina** — na rodada normal do mês você não abre este
arquivo. Ele tem três abas e só uma faz alguma coisa:

| Aba | Estado |
|---|---|
| **Overrides** | **viva.** Força um valor que o cálculo não acerta, sem mexer em código |
| Mercado_Credito | reserva. Só lida se `entrada/tabela_spreads.xlsx` não existir |
| ~~Comentarios_Relatorio~~ · ~~Comentarios_Email~~ | removidas. Os comentários vêm do `.docx` |

### Overrides

Seis campos, mais `casas_taxa`:

| campo | o quê |
|---|---|
| `taxa` · `perf` | texto da taxa global e da performance |
| `carrego` · `duration` | carrego em fração (0,0823 = CDI +8,23%) e duration em anos |
| `pl` · `pl_medio` | patrimônio líquido e PL médio 12m, em reais |
| `casas_taxa` | nº de casas decimais da taxa daquele fundo |

A lista é **fechada de propósito**. Um override é uma exceção pontual — "o número
saiu errado e eu preciso publicar hoje" —, não uma segunda forma de configurar o
fundo. Abrir para qualquer campo transformaria a planilha numa config paralela,
que é exatamente o que este ambiente veio desfazer. Público-alvo, objetivo e
informações operacionais são cadastro, e ficam em `configs/fundos.yml`.

Linha que começa com `#` é exemplo e não tem efeito.

Os overrides são aplicados **no contexto**, então valem igual no relatório, no
post e no e-mail. Antes só chegavam nos materiais da Central: um override mudava
o post sem mudar o relatório — a divergência que o projeto combate, criada pela
própria ferramenta de correção.

Todo override vira linha de aviso na conferência, **com o valor que ele
substituiu**. Sem isso, no mês seguinte ninguém lembra por que aquele carrego
estava diferente do calculado.

---

## Disclaimer

Em `configs/disclaimer.md`, fora do código. É texto jurídico: muda por decisão
de quem responde por ele, não por release, e quem precisa alterá-lo não deveria
ter de abrir um `.py`.

O conteúdo foi **extraído dos relatórios publicados** de agosto/2026, onde é
idêntico nos 12 fundos — 4 parágrafos, ~3.700 caracteres. Conferido: os 13
relatórios gerados saem com o texto igual ao publicado, caractere por caractere.

Três fundos publicam ainda uma nota de rodapé própria (a regra de resgate acima
de 95% do PL): Banks, Institucional e Institucional 15. Ela vem de
`nota_rodape` em `configs/fundos.yml` e aparece antes do disclaimer.

Como o texto é longo e a faixa do rodapé é fixa, o corpo da letra é dimensionado
para caber — mesma lógica do comentário do gestor. Cortar o disclaimer de um
material distribuído a investidor não é um defeito de layout.

---

## A Central indexa a edição

A `tivio-central.html` é o índice. A cada rodada ela ganha **um card por
relatório gerado** — 13 nesta edição —, apontando para
`../relatorios/<arquivo>.html`, com a data da edição.

Sem isso a Central mostrava um único card de relatório (o gerador interativo de
5 fundos) enquanto o `run.py` produzia 13 arquivos que ninguém encontrava por
ela. Um índice que não lista o que existe não é índice.

Os cards gerados têm id `rg-<fundo>` e são refeitos a cada rodada, então não
acumulam duplicata. Card apontando para um `.html` que a edição não produziu é
removido, com aviso dizendo qual era — foi assim que o "Incentivado CDI 30",
link morto desde antes deste ambiente, saiu do índice.

Dois detalhes de ordem que custaram uma rodada cada:

- a Central é processada **por último**. Em ordem alfabética ela viria primeiro,
  olharia uma pasta de saída vazia e julgaria todos os links mortos.
- material desligado em `configs/edicao.yml` (Nordea, One Pager) é **copiado sem
  atualizar**, não pulado. "Desligado" quer dizer "não recebe os dados do mês" —
  eles têm schema próprio —, não "some da pasta". Pulado, o card da Central
  apontava para um arquivo ausente.

---

## Mercado de Crédito

A tabela setorial da ANBIMA vem de **`entrada/tabela_spreads.xlsx`** — a planilha
que a área já produz todo mês. Antes eram ~25 setores × 6 colunas digitados na
aba *Mercado_Credito*: 150 células por edição, copiadas de outra planilha, onde
um número entra errado e ninguém confere porque conferir custa o mesmo que
redigitar.

A planilha tem três características que o loader respeita, e nenhuma delas é
"uma tabela começando em A1":

1. **Duas abas, dois indexadores** — *spread mensal CDI+* e *spread mensal
   IPCA+*. Não são formatações do mesmo dado: são mercados diferentes. O fundo
   de CDI mostra a primeira; o indexado à inflação, a segunda. A escolha é pelo
   benchmark do fundo. Usar sempre a primeira aba poria no relatório do Infra
   Plus a tabela do mercado de CDI.
2. **Colunas diferentes em cada aba** — a de CDI+ tem 7 colunas; a de IPCA+ tem
   10 (Taxa Atual/anterior *e* Spread Atual/anterior, com duas colunas
   "Variação"). Por isso as colunas não são um esquema fixo no código: são
   lidas do cabeçalho da aba, na ordem em que estão.
3. **O total fica num bloco separado, acima do cabeçalho**, sem a coluna Setor.
   É lido à parte e devolvido como última linha, que é onde o relatório o mostra.

O cabeçalho é procurado pela palavra "Setor" em vez de ficar preso à linha 1, e
a aba pode ter qualquer nome.

Percentual é lido pelo **formato da célula**, não por palpite. Uma versão
anterior deste loader adivinhava ("valor menor que 1 é fração") e errava em dois
casos de toda edição: 100% guardado como `1,0` virava "1,00%", e uma coluna de
spreads inteira abaixo de 1% seria multiplicada por 100. O Excel guarda a
resposta no formato da célula — basta lê-la.

Se a planilha existir mas a tabela não for reconhecida, o relatório sai **sem** o
bloco, com aviso dizendo qual cabeçalho foi lido. Preencher um bloco de mercado
com dados meio lidos é pior do que não ter o bloco.

Enquanto a planilha não chega, a aba *Mercado_Credito* do preenchimento manual
continua funcionando como alternativa.

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

### A composição é por vertical

Não é refinamento: os relatórios de **Crédito Estruturado** publicados são outro
produto, não uma variação do high grade.

| | Crédito Privado | Crédito Estruturado |
|---|---|---|
| Páginas | 4 | **3** |
| Carteira | Principais Emissores · Setor · Rating | **Alocação Real** · **Alocação por Estratégia** |
| Mercado de Crédito | sim | **não** |

"Alocação por Estratégia" vem da coluna `Book` da Base Carteira (FIDC Sênior,
FIDC Mezanino, Caixa…) — um corte que o relatório de high grade não usa.

**Não implementado:** o bloco **Subordinação**, que aparece só no relatório do
ALT 90. A Base Carteira não tem essa coluna; o dado teria de vir de outra fonte.

### Selos

A faixa do rodapé leva QR Code, dois selos ANBIMA, o Rating S&P brAMP-1 e o selo
PRI — conferidos contra o relatório publicado.

Os arquivos vão em `assets/selos/` e são embutidos em base64. Base64, e não a
URL do site, porque o selo precisa sobreviver à **exportação**: o `html2canvas`
só desenha imagem de outro domínio se o servidor mandar cabeçalho CORS, e o
WordPress não manda. O material original contorna isso por proxies públicos — se
um cair, o selo vira um quadrado vazio no JPG e ninguém vê antes de publicar.

Pasta vazia: o relatório usa as URLs oficiais e a conferência avisa.

Cada seção é um arquivo em `templates/componentes/`. O CSS em
`templates/estilos/relatorio.css` foi **extraído do gerador HTML oficial**, para o
template reproduzir o layout publicado e não um layout parecido.

### Os gráficos — Apache ECharts

Os três blocos (linha do histórico, barras de emissores e setores, colunas de
rating) são desenhados com **Apache ECharts 5.6.0**, em `renderer: 'svg'`. SVG não
é preferência: em canvas o gráfico vira imagem rasterizada dentro de um PDF
vetorial, que é o que faz um PDF parecer impressão de tela.

O ECharts fica **versionado** em `assets/vendor/` e é copiado para
`reports/AAAA-MM/relatorios/vendor/`, ao lado dos HTMLs — com o CDN só como
reserva. Razão prática: o PDF é gerado sem ninguém olhando, e um CDN fora do ar
produziria 13 relatórios com o gráfico faltando, descobertos depois de
publicados.

A primeira versão **embutia** o arquivo em cada relatório. Funcionava, mas eram
13 cópias idênticas de 1 MB: cada relatório pesava 2,3 MB e a saída do mês somava
50 MB. Referenciar a pasta ao lado resolve o mesmo problema — desde que o PDF
seja tirado do **arquivo gravado**, aberto por `file://`, e não de uma cópia em
memória: com `set_content` a página não tem URL base e nenhum caminho relativo
resolve. Hoje a saída inteira dá **14 MB**, e o PDF sai do mesmo artefato que a
pessoa abre no navegador.

**Aprimoramento progressivo.** O Python desenha o gráfico em SVG e o entrega
dentro do contêiner; o ECharts o substitui ao carregar. Se o ECharts falhar, o
que estava lá continua lá — o relatório nunca sai com um retângulo vazio. Antes
de imprimir, o exportador espera `window.__tvCharts` e avisa se algum gráfico
não desenhou.

A série é a real, apurada pelas cotas de fechamento de cada mês. O relatório
publicado hoje mostra uma curva que **não é o histórico do fundo**: `histSVG()`
interpola uma reta do zero até o valor final, com um ruído para parecer orgânico.

---

## Os botões

Toda tela gerada tem a sua barra de exportação.

| Tela | Botões |
|---|---|
| Relatório de Gestão (13) | PDF (vetor) · PDF (imagem) · JPG · PNG · PPTX · Editar textos |
| Posts (Estruturado, Privado, IS) | Baixar JPG · Pacote JPG · Pacote PDF · Editar textos |
| E-mail de Crédito | Baixar PNG · Por partes · Baixar tudo · E-mail (HTML) |
| Relatório interativo | JPG do fundo · Pacote JPG · Pacote PDF |

**PDF (vetor)** usa a impressão do navegador: como o `@page` do template já
define A4 sem margem, sai idêntico ao PDF do `run.py`, com texto selecionável.
**PDF (imagem)** captura as folhas em bitmap — serve quando o destino não lida
bem com vetor. Por isso o vetor vem primeiro na barra.

As folhas são capturadas **uma por vez**: as quatro em paralelo multiplicam o
pico de memória por quatro e travam a aba em máquina modesta. A escala é 3×
(3000×4242 px numa A4) — acima disso o html2canvas estoura a memória sem ganho
visível.

Para que o clique funcione, as bibliotecas (`html2canvas`, `jszip`, `jspdf`,
`echarts`) são servidas de `central/vendor/`, copiadas junto com os HTMLs. Nos
materiais originais elas vêm do cdnjs **sem alternativa**: CDN fora, bloqueado
pela rede da empresa ou lento e o botão não faz nada — sem erro na tela, porque
o `onclick` chama uma função que não existe.

A ordem agora é local primeiro, CDN como reserva:

| Situação | O que acontece |
|---|---|
| Pasta da edição inteira | carrega local, funciona sem rede |
| Só o HTML, por e-mail | local dá 404, cai no CDN, funciona |

Duas armadilhas resolvidas no caminho, as duas pelo mesmo motivo — `crossorigin`
em arquivo local: numa página aberta por `file://` o navegador trata o script
como requisição CORS de origem opaca e o recusa, com o arquivo ali do lado. O
atributo é removido das tags reescritas, e o carregador dinâmico do e-mail passa
a marcá-lo só quando a URL é absoluta.

Verificado com a rede bloqueada: os cinco materiais com export carregam as
bibliotecas, e o botão "Baixar JPG" produz o arquivo de 2160×2880.

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
AutomaTivio/
├─ run.py                     ← o comando
├─ configs/
│   ├─ edicao.yml             ← DATA_BASE e o que gerar
│   ├─ fundos.yml             ← 22 fundos; 14 com relatório
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
├─ assets/
│   ├─ logos/                 ← 53 SVGs dos fundos
│   ├─ vendor/                ← Apache ECharts 5.6.0 (versionado)
│   ├─ fontes/                ← Versos local, opcional (PDF sem rede)
│   └─ relatorio_charts.js    ← monta os gráficos ECharts
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
