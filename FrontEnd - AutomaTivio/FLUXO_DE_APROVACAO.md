# Fluxo de aprovação do AutomaTivio

Especificação enviada pelo Renan em 10/11/2026. As telas desta pasta
(`index.html`) seguem este documento.

O AutomaTivio deve trabalhar com uma esteira obrigatória de aprovação.

## Fluxo principal

```
Carteira / Dados disponíveis
        ↓
Validação de dados
        ↓
Aprovação de Riscos
        ↓
Geração do comentário
        ↓
Revisão do comentário pelo Comercial
        ↓
Aprovação do Comercial
        ↓
Material liberado para geração
        ↓
Geração dos materiais
```

## Regra importante

Nenhum material final pode ser gerado enquanto os dois gates obrigatórios não
estiverem concluídos:

1. Riscos aprovou os dados.
2. Comercial aprovou o comentário.

O sistema deve deixar muito claro em qual etapa cada fundo está.

## Aprovação de dados (Riscos)

Criar uma área de validação dos dados utilizados na automação.

Riscos deve conseguir visualizar:

- Fundo
- Data-base
- Carteira utilizada
- Data/hora da última atualização
- Principais dados e indicadores utilizados
- Origem dos dados
- Eventuais alertas de validação
- Status da validação

Ações disponíveis: "Aprovar dados", "Reprovar dados", "Solicitar correção".

Status possíveis:

- Aguardando dados
- Aguardando Riscos
- Dados aprovados
- Correção solicitada
- Dados reprovados

Somente depois de Riscos aprovar os dados, o sistema deve liberar a geração do
comentário.

## Geração de comentários

Após a aprovação de Riscos, o AutomaTivio deve permitir gerar o comentário
automaticamente.

```
Dados aprovados por Riscos
        ↓
Gerar comentário
        ↓
Comentário gerado como RASCUNHO
        ↓
Enviar para aprovação Comercial
```

O sistema deve permitir dois caminhos para criação do comentário:

1. **Manual**
   - escrever diretamente;
   - colar texto;
   - importar arquivo .md;
   - editar Markdown.
2. **Automático**
   - botão "Gerar comentário";
   - futuramente conectado via MCP/IA;
   - utilizar exclusivamente dados já aprovados por Riscos;
   - considerar informações do fundo e comentários anteriores quando disponíveis;
   - gerar automaticamente o Markdown;
   - salvar sempre como rascunho.

No melhor cenário, a integração MCP deve permitir que a IA acesse as fontes
autorizadas necessárias para produzir o comentário.

## Aprovação do Comercial

Todo comentário gerado deve obrigatoriamente passar pelo Comercial.

Status:

- Não gerado
- Gerando
- Rascunho
- Aguardando Comercial
- Alterações solicitadas
- Aprovado pelo Comercial

O Comercial deve conseguir:

- visualizar o comentário;
- editar o comentário;
- comparar com a versão anterior;
- solicitar uma nova geração;
- aprovar;
- reprovar/solicitar alterações.

Adicionar botão "Aprovar comentário".

Registrar:

- usuário responsável pela aprovação;
- data e hora;
- versão aprovada.

## Regerar comentário

O sistema deve permitir gerar novamente um comentário.

```
Comentário gerado
        ↓
Comercial solicita alterações
        ↓
Gerar nova versão
        ↓
Novo rascunho
        ↓
Aprovação Comercial
```

As versões anteriores não devem ser apagadas. Manter histórico:

- v1 - Gerado por IA
- v2 - Editado manualmente
- v3 - Regenerado
- v4 - Aprovado pelo Comercial

## Geração dos materiais

A geração do material só pode ficar disponível quando:

- Carteira disponível
- Dados atualizados
- Dados aprovados por Riscos
- Comentário gerado
- Comentário aprovado pelo Comercial
- Template disponível
- Configuração válida

Quando todos os critérios forem atendidos: **STATUS: PRONTO PARA GERAR**.

Liberar "Gerar material" e "Gerar todos os materiais".

## Status na visão geral

A tela principal deve mostrar de forma muito simples:

Fundo · Data-base · Dados · Riscos · Comentário · Comercial · Materiais · Ação

Exemplos de estados:

| Fundo | Dados | Riscos | Comentário | Comercial | Materiais |
|---|---|---|---|---|---|
| Infra Plus CDI | Atualizados | Aprovado | Gerado | Aguardando aprovação | Bloqueados |
| Top Credit | Atualizados | Aprovado | Aprovado | Aprovado | Liberados |

A interface deve permitir entender rapidamente: "Por que ainda não posso gerar
este material?"

## Permissões por perfil

Preparar o frontend para trabalhar futuramente com controle de acesso por perfil.

**Riscos**
- consultar dados;
- validar dados;
- aprovar/reprovar dados;
- solicitar correções.

**Comercial**
- consultar dados aprovados;
- gerar comentário;
- editar comentário;
- regenerar comentário;
- aprovar comentário;
- gerar materiais.

**Administrador**
- acompanhar todo o fluxo;
- configurar fundos;
- configurar templates;
- consultar histórico e logs;
- administrar integrações.

## Auditoria

Toda aprovação deve possuir trilha de auditoria. Registrar:

- fundo;
- competência/data-base;
- operação;
- usuário;
- área;
- data/hora;
- versão;
- status anterior;
- novo status.

Nunca substituir silenciosamente uma aprovação anterior.
