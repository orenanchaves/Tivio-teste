# Publicação automática no SharePoint

Pedido do Renan em 10/11/2026: quando o backend terminar, os materiais já sobem
para o SharePoint. Este é o mapeamento de onde isso entra no AutomaTivio.

## Onde entra na esteira

```
Riscos aprovou os dados  +  Comercial aprovou o comentário
        ↓
Gerar material (run.py, etapas 1 a 6)
        ↓
engine/publicacao.py monta saida/_Atual/ e saida/_Historico/AAAA-MM/
        ↓
NOVA ETAPA 7: Publicar no SharePoint
        ↓
Status do fundo: Publicado no SharePoint (com link)
```

A etapa 7 roda sozinha no fim da rodada, só para os fundos que passaram pelos
dois gates. Se um fundo não tem as duas aprovações, os arquivos dele não sobem.

## O que sobe e para onde

A `saida/_Atual/` já foi desenhada para isso: nomes fixos, sem o mês
("Tivio Banks - Relatório de Gestão.pdf"), então o upload substitui o arquivo do
mês anterior e nenhum link muda.

| Local | Pasta no SharePoint | Comportamento |
|---|---|---|
| `saida/_Atual/<área>/...` | `Materiais AutomaTivio/_Atual/<área>/...` | substitui o arquivo (nova versão no histórico de versões do SharePoint) |
| `saida/_Historico/AAAA-MM/<área>/...` | `Materiais AutomaTivio/_Historico/AAAA-MM/<área>/...` | cria a pasta do mês, nunca apaga mês anterior |
| `Interno/` (Central, conferência, log) | não sobe junto | fica só na pasta interna |

Áreas: Crédito Privado, Crédito Estruturado, Investment Solutions, Previdência,
Multi-área.

## Como implementar (backend)

1. **Novo módulo** `exporters/sharepoint.py`, chamado por `engine/pipeline.py`
   depois de `engine/publicacao.py`.
2. **Acesso pela Microsoft Graph API** com um aplicativo registrado no Entra ID
   da Tivio, permissão `Sites.Selected` (acesso só ao site de Materiais, não ao
   tenant inteiro). Quem cria: TI da Tivio.
3. **Credenciais** no `entrada/.env` (já fora do Git): `SP_TENANT_ID`,
   `SP_CLIENT_ID`, `SP_CLIENT_SECRET`, `SP_SITE`, `SP_BIBLIOTECA`.
4. **Upload**: arquivos até 4 MB em uma chamada; acima disso (PDF e PPTX dos
   decks), sessão de upload em partes.
5. **Conferência**: depois de subir, ler de volta o tamanho de cada arquivo e
   comparar com o local. Diferença vira erro no log e o fundo fica com status
   "Falha no envio".
6. **Auditoria**: cada envio grava fundo, competência, arquivo, versão do
   SharePoint, data/hora e resultado na trilha de auditoria do portal.
7. **Opções do `run.py`**: `--sem-sharepoint` para rodadas de teste e
   `--conferir` nunca envia. Rodada com `--so` envia só os fundos escolhidos.

## Status no portal

| Status | Quando |
|---|---|
| Aguardando materiais | ainda não gerou |
| Enviando | etapa 7 em andamento |
| Publicado no SharePoint | todos os arquivos conferidos, com link da pasta |
| Falha no envio | algum arquivo não conferiu; botão "Reenviar" |

## O que falta para ligar

- [ ] TI da Tivio registrar o aplicativo e liberar o site de Materiais.
- [ ] Definir o nome do site e da biblioteca no SharePoint.
- [ ] Escrever `exporters/sharepoint.py` e ligar no pipeline.
