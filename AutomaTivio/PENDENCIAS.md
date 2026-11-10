# AutomaTivio · o que falta (outubro/2026)

Situação em 15/10/2026. O código está no GitHub (`orenanchaves/tivio-teste`),
com os 8 decks novos, os números institucionais pelas fontes oficiais e as
taxas de previdência. Este arquivo lista só o que ainda não está fechado.

---

## 1. Para rodar o mês no seu PC

- [ ] Baixar a versão nova pelo link do release (`AutomaTivio_v2.zip`, atualizado em
      15/10/2026) ou pelo repositório (botão verde **Code** > **Download ZIP**).
- [ ] `pip install -r requirements.txt` (entrou o pacote `requests`, para a API).
- [ ] Copiar a `dados_mensais.xlsx` para `AutomaTivio\entrada\`.
- [ ] Copiar o `tivio_summary.json` do Informativo para `AutomaTivio\data\`
      (opcional: sem ele a rodada segue e avisa no log).
- [ ] `python run.py` e conferir no fim:
  - decks em `saida\_Historico\AAAA-MM\decks\` e `saida\_Atual\<área>\Decks\`;
  - no log, as linhas de `deck` e `indicadores`.

---

## 1b. Atualizar todos os PPTs

- [ ] Conferir o sign-off: `python ./scripts/status_signoff.py --data 2026-10-30`
- [ ] Gerar o material: `python run.py --data-base 2026-10-30`
- [ ] Rodar a edição completa (`python run.py`) e conferir **todos os PPTs** do mês:
      os 18 decks, os 13 relatórios de gestão em PPTX e os Informativos do HGD30 e do HYD60.
- [ ] Tivio Conecta e Conexão ALT 180: puxar a rentabilidade pelas cotas diárias da
      CVM (CNPJ 60.173.255/0001-88); hoje o slide mantém os números do modelo.
- [ ] Deck do Conexão Bradesco (HGD30 PGBL/VGBL, CNPJ 59.888.171/0001-41): mesma fonte.
- [ ] Trocar o texto provisório (lorem ipsum) do `comentarios.md` antes de publicar:
      a rodada avisa no log quais fundos estão com ele.

## 2. Dados que ainda não chegam na automação

| O que | Onde aparece | O que falta |
|---|---|---|
| JSON do Informativo (`tivio_summary.json`) | Rosca "AuM por vertical" (Prev Low Vol e Top Credit) e "Ativos sob gestão" do slide de crédito | Exportar com o login corporativo a cada mês. Sem ele, esses números ficam como no modelo |
| Comentário do gestor do Prev Low Vol e do Top Credit | Slide "Comentário do Gestor" | Escrever as seções `## Tivio Prev Low Vol` e `## Tivio Prev Top Credit` no `entrada/comentarios.md`. Sem elas, os slides do comentário saem do deck e a rodada acusa erro |

---

## 3. Números que seguem manuais

Ficam em `configs/big_numbers.yml` porque ainda não têm fonte oficial:

| Número | Valor hoje |
|---|---|
| AuM captado nos últimos 12 meses (crédito) | R$ 3,5 bi |
| Emissores em carteira | +30 bancários, +100 corporativos |
| Profissionais dedicados ao crédito | 11 |
| Turnover (decks de IS) | 3,3% |

E um número forçado, que vence a API:

| Número | API diz | Material usa | Quando tirar |
|---|---|---|---|
| Anos de história | +25 | +27 | Quando o site for corrigido, apagar a linha em `forcar:` |

---

## 4. Decisões pendentes

- [ ] **Rótulo "Profissionais"** nos decks de crédito: o número agora é o da
      API (+40, profissionais de **investimento**). Antes era +75. Vale trocar o
      rótulo do cartão para "Profissionais de investimento"?
- [ ] **Anos de história**: confirmar com quem cuida do site se o oficial é
      +25 ou 27, e corrigir a API.

---

## 5. Correções nas planilhas

- [ ] `taxas_prev.xlsx`, bloco **ALT LIGHT**: a custódia do FIE I está como
      **1720,46**, um valor em reais na coluna de percentual. A automação avisa
      no log, mas o dado precisa ser corrigido na planilha.
- [ ] **Tivio Atuarial** não está na DePara (aviso antigo, não impede a rodada).

---

## 6. Para conferir na primeira rodada real

Os decks foram testados com números fictícios. Na primeira rodada com dados
reais, vale abrir e olhar:

- [ ] **HYD60, slide 10** (rentabilidade histórica, novo): série da classe FIE,
      período "Mar/2026 a Set/2026", etiquetas no fim das linhas.
- [ ] **HGD30, slides 8 e 9**: alocação High Grade / Crédito Estruturado / Caixa
      e "Carteira HGD / HYD".
- [ ] **Infra Plus CDI, slide 8**: gráfico de principais emissores.
- [ ] **Institucional 15**: "Retorno 12M" em % do CDI.
- [ ] **Prev Low Vol e Top Credit, slide 3**: tabela com 24M, 36M e Alfa.
- [ ] **Prev Low Vol e Top Credit, slides 3 a 5**: volatilidade, tabela PnL, cascata,
      pizza de alocação e top 5 vêm agora das abas `Low Vol` e `TOP Credit`
      (testado com setembro, que já batia com o modelo, e com números alterados).
- [ ] Cartões de AuM com decimal ("+R$ 11,3 bi", "+R$ 3,5 bi") quebram linha
      no modelo: se incomodar, aumentar a largura da caixa no PPTX.

---

## 7. Próximo passo: comentário mensal gerado por IA

Ideia registrada em 10/11/2026. Hoje o comentário de cada fundo vem escrito pelo
gestor (`comentarios.docx` / `comentarios.md`), e a automação só preenche os
marcadores `X%`. A ideia é os comentários mensais passarem a ser gerados por IA:

- [ ] **Começo: a rentabilidade do fundo no mês.**
- [ ] **Restante: a carteira, comparada com o mês anterior.**
- [ ] **Num portal:** o portal gera o relatório com os números e gera o
      comentário com base na carteira e nas análises anteriores.
- [ ] **Telas do portal e fluxo de aprovação** (Riscos aprova os dados, Comercial
      aprova o comentário, só então gera os materiais) e **envio automático ao
      SharePoint** no fim do backend: na pasta `../FrontEnd - AutomaTivio/`
      (`index.html`, `FLUXO_DE_APROVACAO.md`, `SHAREPOINT.md`).

---

## Resolvido em 15/10/2026

- Abas de Investment Solutions mapeadas: os gráficos dos decks do Prev Low Vol e
  do Top Credit leem o intervalo que o próprio modelo guarda; PnL e
  volatilidade pelo rótulo (`loaders/abas_is.py`, `aba_is` em `fundos.yml`).
- Prev Top Credit na DePara: o nome é o mesmo do `fundos.yml` com
  " - Expandida" no fim, que o cadastro já ignora. Nada a mudar.
- Fiagro Sr e Fiagro Mz (ALT 180 e ALT 90) ganharam nome amigável ("Fiagro").
- Release `AutomaTivio_v2.zip` substituído pela versão nova.
