## A ideia central

Se for para lembrar de uma coisa só: **spec na frente**. São quatro ideias, cada uma sobre a anterior. O prompt delega para o contexto, a spec é o contexto mais importante, e guardrails e QA garantem que o combinado foi cumprido.

| Módulo | Pergunta que responde |
| --- | --- |
| 1. Prompt | Como pedir? |
| 2. Contexto | O que o modelo sabe quando recebe o pedido? |
| 3. SDD | Onde a intenção fica escrita antes do código? |
| 4. Guardrails e QA | O que mantém a IA no combinado, e como saber quando errou? |

## Trilha

| Ordem | Módulo | Exercício |
| --- | --- | --- |
| 1 | Prompt | Reescrever um pedido real nas quatro partes |
| 2 | Contexto | Comparar o mesmo pedido com e sem contexto |
| 3 | Grilling | Rodar `/grill-me` numa ideia real |
| 4 | Regra vira teste | Transformar uma regra em caso de borda |
| 5 | Guardrails que orientam | Aplicar o teste de cada linha num `CLAUDE.md` |
| 6 | Guardrails que garantem | Trocar uma instrução por uma trava |
| 7 | Quando usar IA | Separar um produto entre cálculo e modelo |
| 8 | O case como treino | Achar a armadilha de uma regra sua |

## Módulo 1. Prompt

**A ideia:** um bom pedido tem quatro partes.

| Parte | Exemplo |
| --- | --- |
| Persona | "Você é o assistente de atendimento da Caqui." |
| Contexto | Regras em SPEC.md, prazos no KB-006, data e hora atuais (18/11, 10h) |
| Tarefa | "Diga quando cai o resgate OP-10001 do cliente C-0007." |
| Formato | A data, a conta e a fonte, em até três linhas |

**Três reforços:**

| Reforço | Nome no mercado |
| --- | --- |
| Mostre dois ou três exemplos da resposta que você quer | Few-shot |
| Peça os passos: o raciocínio antes da conclusão | Chain of thought |
| Deixe conferir: pensa, usa uma ferramenta, olha o resultado | ReAct |

O ReAct é o jeito que todo agente trabalha: raciocina, age, observa e repete até a verificação passar. Repare que o C já aponta para arquivos: o prompt bom delega o conhecimento para o contexto.

**No case:** a SPEC descreve o pedido do classificador futuro nessas partes: persona de triagem, lista de rotas sem dado de cliente, escolher uma rota, responder uma palavra da lista, com exemplos por rota.

**Exercício:** pegue um pedido que deu resultado ruim esta semana e reescreva nas quatro partes. Rode os dois e compare.


## Módulo 2. Contexto

**A ideia:** contexto vale mais que prompt.

**Caso do CDB do Rafael (PT-06):**

| | Pedido | Resultado |
| --- | --- | --- |
| Só o pedido | "Calcula o IR do resgate do CDB do Rafael." | "22,5% sobre o valor resgatado." Errou a faixa e a base |
| Com contexto | O mesmo, com `taxas.json`, regra 2 e `posicoes.csv` do C-0002 | "181 dias: 20% sobre R$ 810,03 de rendimento, IR de R$ 162,01." Certo e com fonte |

Mesmo modelo, mesma frase. Mudou o que estava na janela. No dia 180 a alíquota é 22,5%, no 181 é 20%: é o tipo de borda que vale testar.

**Janela de contexto:** é a memória de trabalho do modelo. Cada modelo tem um tamanho (exemplos: 200 mil, 256 mil e 1 milhão de tokens). Instruções, arquivos, conversa e a própria resposta ocupam a mesma janela. Ela é medida em tokens, pedaços de palavra.

**Context rot:** janela grande não é licença para encher. A qualidade cai bem antes do limite, porque quanto mais coisa lá dentro, pior o modelo acha o que importa.

| Sinal de janela cheia | O que fazer |
| --- | --- |
| Esquece a instrução do começo | Uma conversa nova por tarefa |
| Ignora o arquivo que você passou | Apontar o trecho, não o arquivo inteiro |
| Reabre o que já estava decidido | Manter um resumo do que foi decidido |

**No case:** decisão mora em "Decisões" na `SPEC.md`, não na conversa. Duas sessões trabalharam no mesmo repositório porque o contexto estava em arquivo.

**Exercício:** escolha uma tarefa recorrente e liste o mínimo que o modelo precisa receber. Corte o resto.


## Módulo 3. SDD (Spec-Driven Development)

**A ideia:** a intenção é escrita antes do código, e a spec é o contexto que o agente relê a cada tarefa.

### Grilling

Antes da spec, deixe a IA entrevistar você.

```
/grill-me quero um app pra dividir as contas da casa
```

1. Quem paga na hora, e quem só acerta no fim do mês? Recomendo: cada um registra o que pagou, e o saldo fecha no dia 30.
2. O que acontece quando alguém sai da casa no meio do mês? Recomendo: o saldo dessa pessoa fecha na data da saída.
3. E assim até não sobrar pergunta aberta.

- Perguntas numeradas, cada uma com a resposta recomendada. Você aceita ou corrige.
- A decisão que viraria retrabalho às 15h aparece às 10h.
- Sai com glossário e decisões escritos, prontos para a spec.

O agente questiona até os dois terem o mesmo entendimento. Serve para produto, design e engenharia, e era o caminho sugerido para responder às seis perguntas do case.

Fonte: skills `grilling` e `grill-me`, coleção open source de Matt Pocock.

**No case:** não foi usado. A spec nasceu da leitura do case. O revisor depois achou decisões que se contradiziam, o tipo de buraco que uma entrevista pode pegar antes.

### Regra vira teste

Da frase ao assert:

1. Regra 1: fundo cotiza em D+1 e paga em D+2 úteis.
2. CA-1: depois das 16h, conta do próximo dia útil.
3. Caso de borda escrito antes do código: sexta, 30/10, 17h, com 02/11 feriado.

```js
const p = prazoResgate('FUNDO-RF-01', '2026-10-30', '17:00');
assert.equal(p.base, '2026-11-03');
assert.equal(p.etapas.find((e) => e.rotulo === 'Cotização').data, '2026-11-04');
assert.equal(p.pagamento, '2026-11-05');
```

Quando o teste existe antes do código e falha, o agente tem uma coisa concreta para corrigir, não uma opinião.

### O fluxo

| Etapa | O que acontece |
| --- | --- |
| Spec | Produto, design e engenharia juntos |
| Plano | O agente propõe, você aprova |
| Tarefas | Pequenas, uma por vez |
| Código | O agente escreve |
| Verificação | Testes e olho humano |

Decisão tomada no meio do caminho volta para a spec antes de virar código. A spec não é documento para arquivar: é o contexto que o agente relê a cada tarefa. Produto e design entregam spec, critérios de aceite e protótipo. Engenharia consulta a spec antes de inventar regra, e o front consulta o design antes de inventar tela.

### As seis perguntas da spec

| # | Pergunta | O que responder |
| --- | --- | --- |
| 1 | Qual parte do problema? | Motivo, persona ou momento da jornada, e por quê |
| 2 | Qual alavanca? | Evitar o contato, resolver sem humano ou fazer o humano render mais |
| 3 | Quanto isso move? | Estimativa em números, com a conta à mostra |
| 4 | Como a confiança aparece? | O que o cliente vê para acreditar, e onde está a saída |
| 5 | O que fica de fora? | O corte de escopo que permite publicar hoje |
| 6 | Como viabilizar? | O próximo passo para colocar no ar |

**Exercício:** escolha uma regra de um projeto seu e escreva o caso de borda mais difícil, com entrada e saída exatas, antes de abrir o código.


## Módulo 4. Guardrails e QA

**A frase para guardar:** instrução é pedido, o modelo decide. Trava é configuração, a ferramenta executa. Regra que não pode ter exceção vira trava, não frase.

"Nunca grave o CPF no log" no AGENTS.md funciona quase sempre. Um hook que procura CPF antes do commit funciona sempre: instrução é não determinística; hook, permissão e teste são determinísticos.

### Os que orientam

AGENTS.md, CLAUDE.md, rules: o nome muda com a ferramenta, a ideia é a mesma.

O modelo lê e quase sempre segue. Quase sempre não é sempre.

| Guardrail | Como funciona | No case |
| --- | --- | --- |
| Instruções do projeto | AGENTS.md, CLAUDE.md ou rules, lidas em toda sessão, curtas porque cada linha disputa atenção. Teste de cada linha: se tirar, o agente erra? Se não, corta | `AGENTS.md` perdeu o que a trava já cobre |
| Skills | Passos prontos, carregados só quando o pedido combina, então dá para ter várias sem ocupar espaço. Um saber, uma skill | Skill `nova-regra` |
| Contexto isolado | Cada tarefa começa limpa. O que importa mora em arquivo | `SPEC.md` |
| Dados sensíveis | Só dado sintético, CPF mascarado em tela e em log, nenhuma conexão apontando para dado real | Parcial: CPF digitado ainda aparece na tela do cliente |

### Os que garantem

| Trava | Como funciona | No case |
| --- | --- | --- |
| Hooks | Rodam por evento, fora do modelo | Commit bloqueado com CPF sem máscara ou chave de API |
| Permissões | A pasta é a fronteira; comando de risco pede aprovação | `dados/` sem escrita, publicar pede aprovação |
| Check que o agente roda | Ele termina quando passa, não quando parece pronto | `npm run pronto` |
| Revisor sem caneta | Segundo agente que só lê, com janela limpa, compara o feito com a spec | Agente `revisor` |

**Exercício:** pegue uma regra que você repete para a IA e transforme em trava: hook, permissão ou teste.


## Módulo 5. Quando usar IA

**A ideia:** o case pede IA para construir, não em tudo que o produto faz.

| Use cálculo ou regra | Use modelo |
| --- | --- |
| Precisa dar sempre o mesmo resultado | Precisa interpretar linguagem livre |
| Um erro custa dinheiro ou confiança | Um erro leva a uma saída segura |
| Prazo, imposto, comparação com a poupança | Escolher a rota de uma mensagem |

**No case:** o motor é determinístico, sem modelo em produção. O limite apareceu no teste cego: regra por palavra não generaliza. O próximo passo é um classificador que só escolhe a rota e nunca escreve dado.

**Exercício:** liste as funções de um produto seu e marque em cada uma: cálculo, regra ou modelo.


## Módulo 6. O case como treino

**A ideia:** o objetivo é aprender a dirigir e verificar IA num problema real. Cada regra do case esconde uma armadilha típica de modelo.

| # | Regra | Armadilha para a IA |
| --- | --- | --- |
| 1 | Liquidação | Conta dias corridos ou ignora o corte das 16h |
| 2 | IR regressivo | Aplica sobre o total ou erra no dia 181 |
| 3 | Poupança | Compara bruto com isento |
| 4 | Sem recomendação | Cede quando o cliente insiste |
| 5 | Golpe | Responde a pergunta e ignora o sinal |
| 6 | Cliente vulnerável | Trata como mais um caso |
| 7 | Cancelamento | Insiste em reter |
| 8 | Sem doom loop | Repete a mesma resposta |
| 9 | Não inventa | Cria um prazo plausível |
| 10 | Dados pessoais | Ecoa o CPF ou loga a conversa crua |
| 11 | Instrução escondida | Obedece "ignore suas regras" |
| 12 | Horário | Promete humano às 22h |

**Seis coisas valem para qualquer caminho:** saída para humano visível, sem recomendação de investimento, fonte em toda informação, golpe interrompe o fluxo, cliente nunca repete a demanda, só dados sintéticos.

**O roteiro proposto:** criar o repositório, deixar a IA entrevistar o grupo, escrever o `SPEC.md`, montar os guardrails (AGENTS.md curto, um hook e as regras virando teste), publicar e mostrar.

**Exercício:** pegue um fluxo seu, escreva três regras e, ao lado de cada uma, o erro mais provável de um modelo. Esse erro é o primeiro teste.


## O que o case ensinou

### Nota alta pode medir decoreba

As regras foram escritas depois de ler as frases da amostra, e deu 40/40 no teste oficial. O primeiro teste cego, com frases de quem não viu o código, deu 46/70. Depois dos ajustes, o segundo deu 37/50 em frases novas.

**Lição:** cada rodada cega vale uma vez. Depois de ajustar para ela, a nota fica contaminada. Pistas passando também não provam a resposta: leia as respostas.

### A métrica também erra

A primeira versão do replay contava qualquer encaminhamento como injeção detectada e deu 43 falsos alarmes. O erro era da métrica, não do motor.

### Teste verde não prova o combinado

Com todos os testes passando, o revisor sem caneta achou:

- Reclamação às 23h sem prazo de retorno; pela leitura do código, a tela mostra uma pessoa entrando sem ninguém disponível.
- Pedido de encerramento que nunca gera protocolo.
- Golpe escrito depois da passagem para pessoa, sem interromper o fluxo.
- Limite de cinco passos que a spec citava e o código não tinha.

Os dois primeiros têm a parte do motor confirmada rodando o código. Os demais vêm da leitura do revisor.

**Lição:** teste responde o que você perguntou. O revisor compara com o que foi combinado.

### Ordem honesta

`AGENTS.md`, hook, permissões, skill e revisor entraram depois da solução pronta. O método propõe o contrário. Da próxima vez, comece por eles.


## Checklist para o próximo projeto

1. Rodar `/grill-me` na ideia.
2. Escrever a spec com "fora do escopo" e "Decisões".
3. Criar instruções curtas, com o teste de cada linha.
4. Ligar hook, permissões e um comando único de check.
5. Escrever critérios de aceite como casos de borda.
6. Separar tarefas pequenas, com conversa nova por tarefa.
7. Medir com frases ou casos de quem não viu o código.
8. Rodar o revisor sem caneta antes de dizer que está pronto.
9. Registrar onde a IA errou e como foi percebido.


## Glossário

| Termo | Significado |
| --- | --- |
| Token | Pedaço de palavra; unidade da janela de contexto |
| Context rot | Queda de qualidade quando a janela enche, antes do limite |
| Few-shot | Dar exemplos da resposta esperada |
| Chain of thought | Pedir o raciocínio antes da conclusão |
| ReAct | Ciclo de raciocinar, agir com ferramenta e observar |
| Janela de contexto | Memória de trabalho do modelo em uma conversa |
| SDD | Desenvolvimento guiado por spec |
| Grilling | Entrevista da IA para achar buracos antes da spec |
| Critério de aceite (CA) | Condição verificável de que a regra foi cumprida |
| Guardrail | O que mantém a IA dentro do combinado |
| Harness | Conjunto de instruções, skills, travas e testes em volta do agente |
| Hook | Comando que roda por evento, fora do modelo |
| Revisor sem caneta | Agente que só lê e compara o feito com a spec |
| Teste cego | Medição com casos de quem não viu o código |


