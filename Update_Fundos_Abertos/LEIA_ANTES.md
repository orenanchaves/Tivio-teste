# Update_Fundos_Abertos — preciso de uma definição antes de construir

**Tivio Capital** · 15/09/2026

Este ambiente **não foi construído**, e o motivo é concreto.

## O que encontrei

O pedido diz que este ambiente tem "excel com o nome". Os dois candidatos no
`Excel - Guia de Base de Dados` são:

```
Captacao_Fundos_Abertos.xlsx        ca0b6ce83503028dbd2c973a97f8d236
relatorio_captacao_abertos (2).xlsx ca0b6ce83503028dbd2c973a97f8d236
```

**São o mesmo arquivo** — MD5 idêntico, mesmas 5 abas, mesmas 131/130/127/121
linhas. Confirmei também que a aba `XP` é igual célula a célula.

Ou seja: não existe um Excel próprio para este ambiente. O único disponível já é
a fonte do `Update_Captacao_Fundos_Abertos` (item 1).

## Por que não construí mesmo assim

Construir sobre dado idêntico produziria dois dashboards mostrando os mesmos
números com nomes diferentes — o oposto de reduzir trabalho manual. E eu estaria
adivinhando qual é o recorte pretendido.

## As três leituras possíveis

1. **É o mesmo ambiente.** "Fundos Abertos" e "Captação Fundos Abertos" são a
   mesma coisa, e o item 5 é redundante com o item 1. Nesse caso não há nada a
   fazer — basta apagar esta pasta.

2. **É o estoque, não o fluxo.** "Captação" mede entrada e saída no período;
   "Fundos Abertos" seria o universo de fundos abertos com PL, taxa e
   classificação — outra pergunta sobre a mesma base. Dá para construir, e o SQL
   sairia das mesmas quatro tabelas do item 1.

3. **É outro Excel que não veio no zip.** Nesse caso me manda o arquivo.

## O que eu faria na leitura 2

Reaproveitando o que já existe, seria rápido:

```
sql/fundos_abertos.sql          universo + PL + taxa (sem janela de captação)
atualizar_fundos_abertos.py     mesma estrutura dos outros, usando tivio_core
templates/                      precisa de um HTML — não veio nenhum para este
```

Falta o template: os outros quatro ambientes vieram com HTML pronto, este não.

**Me diz qual das três é, e eu construo.**
