# Contexto · AutomaTivio (Central de Materiais)

> Documento de handoff do **AutomaTivio**, o ambiente que atualiza a edição
> mensal da Central de Materiais da Tivio Capital.
> Objetivo: qualquer pessoa (ou outra IA) conseguir entender, rodar e evoluir o
> pipeline sem refazer toda a investigação. Última revisão: **10/2026**.

---

## 1. Visão geral

Todo mês, os materiais da Central eram atualizados à mão: abrir cada PPTX,
trocar número por número, exportar PDF, recortar imagem para o post, reescrever
o e-mail, trocar as datas em cada lugar. Um fundo com dado errado só aparecia
depois de publicado.

O AutomaTivio troca isso por **um comando**. Ele lê as planilhas do mês e o
documento de comentários do gestor, calcula tudo uma vez, e publica:

- **13 relatórios de gestão** — HTML, PDF A4 vetorial e PPTX, um por fundo
  (14 fundos estão marcados com relatório; o Tivio Atuarial fica de fora
  enquanto não entrar no DePara);
- **2 páginas por vertical** (Crédito Privado e Crédito Estruturado), com os
  fundos em abas e botões de exportação — é o que o time abre;
- **posts, e-mail e a Central de Materiais** atualizados;
- **`conferencia_AAAA-MM.xlsx`** com o que mudou, o que faltou e o que não bateu;
- **log** da rodada.

```
entrada/*.xlsx + comentarios.docx
      │
      ▼
  loaders/  →  calculators/  →  engine/contexto.py  ← UM ContextoFundo por fundo
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            ▼                         ▼                         ▼
      relatórios                 posts / e-mail              Central
      (A4 · PDF · PPTX)          (HTMLs legados)             (índice)
            │                         │                         │
            └─────────────────────────┴─────────────────────────┘
                                      ▼
                              saida/AAAA-MM/
```

Um comando por mês:

```powershell
python run.py
```

---

## 2. O mês, na prática

1. Trocar em `entrada/`: `dados_mensais.xlsx`, `taxas_global.xlsx`,
   `tabela_spreads.xlsx`.
2. Colocar os comentários do gestor em `entrada/comentarios.docx`.
3. `python run.py`
4. Conferir `saida/AAAA-MM/conferencia_AAAA-MM.xlsx` (abas Mudanças, Dados
   faltantes, Fundos sem atualização, Rentabilidades, Taxas).
5. Abrir `saida/AAAA-MM/relatorios/` e exportar o que for preciso pelos botões.

A **data base** não é digitada em lugar nenhum: sai do último mês fechado da
planilha. Para forçar, `configs/edicao.yml` → `data_base: 2026-08-31`.

---

## 3. Estrutura de pastas

```
AutomaTivio/
├── run.py                    # o comando único
├── CLAUDE.md                 # guia para quem mexe no código (ou para a IA)
├── entrada/                  # o que VOCÊ coloca
│   ├── dados_mensais.xlsx    #   Base Carteira, Dados, DePara, cotas…
│   ├── taxas_global.xlsx     #   taxa de administração e performance
│   ├── tabela_spreads.xlsx   #   Mercado de Crédito (tabela setorial)
│   ├── comentarios.docx      #   texto do gestor, por fundo
│   ├── preenchimento_manual.xlsx   # overrides pontuais
│   └── imagens/              #   imagens para os materiais (nada entra sozinho)
├── configs/
│   ├── edicao.yml            # a data e o que gerar
│   ├── fundos.yml            # 22 fundos; 14 marcados com relatório
│   └── relatorio.yml         # composição das folhas, POR VERTICAL
├── engine/                   # edicao · cadastro · contexto · governança · pipeline
├── loaders/ calculators/     # leitura (com cache) e fórmulas
├── templates/                # folha A4, componentes, estilos, materiais legados
├── renderers/ exporters/     # montagem e saída (html · pdf · pptx)
├── validations/              # a conferência
├── assets/                   # logos, selos, ícones, marca, fontes, vendor
└── saida/AAAA-MM/            # o que SAI
    ├── relatorios/           #   as duas páginas por vertical ← abra estas
    ├── pdf/ pptx/ central/
    ├── conferencia_AAAA-MM.xlsx
    └── AAAA-MM-processamento.log
```

---

## 4. A decisão que sustenta o resto

**Um `ContextoFundo` por fundo, lido por todos os materiais.**

Antes, cada material tinha a sua conta. O relatório dizia que o Infra Plus
rendeu 1,26%, o post dizia outra coisa, e ninguém sabia qual estava certo sem
refazer na mão. Hoje existe um objeto por fundo
(`engine/contexto.py::ContextoFundo`) e **todo número sai dele**: relatório,
post, e-mail e Central leem o mesmo lugar.

Consequência prática para quem for evoluir: se faltar um corte de dado, ele
**nasce no Contexto**, nunca dentro de um renderizador. Uma conta feita no
renderizador volta a ser a divergência que o projeto existe para eliminar.

A segunda decisão da mesma família é a **data única** (`engine/edicao.py`): uma
variável, nove formas derivadas, e nenhuma data literal em lugar nenhum.

---

## 5. Fidelidade aos relatórios publicados

O critério de aceite do relatório é **ser igual ao PPTX publicado**, não
parecido. Os doze originais (9 de Crédito Privado + 3 de Crédito Estruturado)
foram abertos e comparados shape a shape. O que valeu:

| Bloco | Como está |
|---|---|
| Tabela de rentabilidade · CP | Fundo · CDI · **Alfa** · **%** (4 linhas) |
| Tabela de rentabilidade · CE | Fundo · CDI · % · **CDI+** (4 linhas, sem Alfa) |
| Exceções | Infra Plus CDI `sem_alfa`; Banks/Infra Plus/Legacy `casas_pct: 2` |
| Alocação **real** da carteira (CE) | **Treemap** da coluna `Tipo aj.` com os nomes de `tipo_label` — é daí que vem "Liquidez" e a ausência de "LFSN" |
| Alocação por **estratégia** (CE) | Barras dos **setores** (12 + Caixa) |
| COLATERAIS (CE) | 5 cartões fixos, com os SVGs **extraídos do próprio PPTX** |
| CDI+ por período (CE) | Caixa sob a rentabilidade histórica: Desde o início · 12M · Mês |
| Setores (CP) | Top 5 + Caixa (o Banks publicado mostra só Financeiro e Caixa) |
| Disclaimer | Os 4 parágrafos reais, extraídos do PPTX (3.689 caracteres) |
| Selos | ANBIMA ×2, Rating S&P, PRI — extraídos do PPTX, embutidos em base64 |
| Comentário do gestor | Texto preservado **vírgula por vírgula**; só os `X%` preenchidos |

**Dois erros que isso pegou** e que não apareceriam de outro jeito:

1. Faltava a linha **Alfa** na tabela de Crédito Privado — o código mostrava
   Alfa *ou* %, e o publicado tem as duas.
2. Os títulos do ALT estavam **trocados**: "Alocação real da carteira de
   crédito" é o corte por classe e apontava para setores; "Alocação por
   estratégia" é o corte por setor e apontava para classe. Número certo no lugar
   errado não parece erro.

**O teste que vale:**

```powershell
python docs\conciliar_com_pptx.py saida\AAAA-MM\conferencia_AAAA-MM.xlsx
```

Hoje em **58 de 58 rentabilidades idênticas ao relatório publicado (100%)**.
Detalhes em `docs/CONCILIACAO.md`.

---

## 6. Dois passos: o HTML sai pronto, o resto é botão

A automação vai até o HTML — ele sai correto, sem ninguém clicar em nada. **A
exportação é botão**, de propósito: PDF (vetor), PDF (imagem), JPG, PNG e PPTX,
e a exportação leva **só o fundo que está na aba ativa**.

Isso mantém a pessoa no controle do que publica, e evita gerar 13 PPTX quando
só um mudou. O `run.py` também gera PDF e PPTX de todos, para quem quiser o
pacote pronto.

A folha é A4 de verdade: **210 × 297 mm**, vetorial, fonte incorporada, quebra
de página controlada. Não é impressão de navegador.

---

## 7. Pendências conhecidas

| O que falta | Por quê | Como resolver |
|---|---|---|
| **SUBORDINAÇÃO** (só no ALT 90) | A Base Carteira não tem a coluna do nível de subordinação | O dado precisa vir de outra fonte |
| **QR Code** no rodapé | No PPTX ele entra por link externo, não embutido | Salvar o QR do site como `assets/selos/qr.png` |
| **Fonte Versos** no PDF | Os `.woff2` vêm do CDN da marca; sem rede o PDF usa a fonte de reserva e a métrica do texto muda | Colocar os arquivos em `assets/fontes/` |
| **Tivio Atuarial** | Não está no DePara da planilha | Incluir no DePara |
| **BVP** sem logo | Não há SVG em `assets/logos` | Adicionar `tivio_bvp.svg` |

Nenhuma delas impede a rodada: todas saem como **aviso** no log e na
conferência, não como erro.

---

## 8. Segurança

- `entrada/.env` (token Databricks) está no `.gitignore` via `**/.env` e **não
  é versionado**.
- O script legado trazia **credenciais ANBIMA escritas no código**. Elas não
  foram copiadas para cá; o acesso deve usar variável de ambiente, e o segredo
  antigo **deve ser rotacionado** antes de reusar a integração.

---

## 9. Para mexer no visual

- **A folha A4** (o que precisa ser fiel ao PPTX): `templates/estilos/relatorio.css`
  e um arquivo por seção em `templates/componentes/`.
- **A casca da página** (cabeçalho, hero, abas, rodapé):
  `templates/estilos/pagina.css` e `abas.css` — extraídos sem alterar uma linha
  do gerador oficial.
- **Ligar, desligar ou mover uma seção de folha**: `configs/relatorio.yml`. Não
  precisa tocar em código.

Depois de qualquer mexida no CSS da folha, conferir: `python run.py` sem erros,
a conciliação em 58/58, e os PDFs em A4 sem página em branco. O exportador mede
o enquadramento sozinho e avisa se a folha deixar de caber.
