# Ambientes de atualização — Tivio Capital

**15/09/2026**

Cinco dashboards, um roteiro só. Cada pasta `Update_*` lê uma fonte, converte
para o contrato do seu template e grava o HTML em `outputs/`.

## Chave do Databricks — um arquivo só

Copie `.env.exemplo` para `.env` **na raiz** e preencha. Ele atende todos os
ambientes: `tivio_core/db.py` procura primeiro o `.env` da pasta do ambiente e
depois o da raiz, então rotacionar a chave é mexer em um lugar só.

Antes cada pasta precisava do seu próprio `.env` com a chave repetida — e dois
ambientes novos ficaram sem nenhum.

Confira antes de rodar qualquer coisa:

```powershell
pip install -r Update_Monitor_Novos_Fundos\requirements.txt
python testar_conexao.py
```

`testar_conexao.py` mostra host, catálogo e usuário, confirma que o token está
definido (sem imprimi-lo) e checa se as oito tabelas que os ambientes usam
existem no schema configurado.

## Como rodar

```powershell
cd Update_Monitor_Novos_Fundos ; python atualizar_monitor.py
cd Update_Monitor_FII          ; python atualizar_fii.py
cd Update_Captacao_Previdencia ; python atualizar_previdencia.py
cd Update_ETF                  ; python atualizar_etf.py
cd Update_Captacao_Fundos_Abertos ; python atualizar_captacao.py
```

Sem argumento nenhum. O que muda o comportamento fica no `.env`.

## Estado de cada ambiente

| Ambiente | Roda | Fonte | Bate com o Excel |
|---|---|---|---|
| Monitor de Novos Fundos | sim | CVM pública + ANBIMA | sim — 105 em ago/26 |
| Monitor FII | sim | Excel (SQL não confirmado) | 239 ofertas |
| Captação Previdência | sim | Excel (SQL herda pendência) | CDI 1,09% confere |
| ETF | sim | Databricks | sem Excel de referência |
| Captação Fundos Abertos | sim | Databricks | **não** — ver MD da pasta |
| Fundos Abertos | não | — | ver `LEIA_ANTES.md` |

Cada pasta tem um `ORIGEM_DOS_DADOS.md` dizendo de onde vem o dado e o que
ainda não fecha.

## `tivio_core/` — o que era copiado e colado

Os cinco ambientes repetiam o mesmo código: conectar no Databricks, ler `.sql`,
injetar array no HTML, gravar. Isso multiplicava por cinco cada correção — o bug
do recorte de ano existia em mais de um lugar.

| Módulo | Responsabilidade |
|---|---|
| `db.py` | conexão, `USE_MOCK`, leitura de `.sql` com placeholders |
| `template.py` | injeção de arrays/objetos, selo de data, contadores do menu |
| `saida.py` | gravação dos HTMLs |
| `validacao.py` | checagens que rodam a cada atualização |

Cada ambiente mantém só o que é dele: o SQL, o mapeamento para as colunas do
template e as métricas.

## Contadores do menu

Os números no menu superior (`Monitor de Novos Fundos 610`, `FII 218`…) eram
fixos no HTML. Cada atualização de qualquer dashboard exigia reescrever o
contador em **todos os outros arquivos à mão**, e quando isso não acontecia o
menu passava a mentir.

**Foram removidos dos 16 HTMLs** (118 ocorrências). A regra CSS ficou, para o
dia em que forem preenchidos automaticamente.

O mesmo problema existia dentro do FII: o total aparecia escrito à mão em dez
lugares do template, e o cabeçalho dizia 218 enquanto o KPI calculado em JS
dizia 239. `atualizar_fii.py` reescreve os dez a cada execução, ancorado no
rótulo ao lado — substituir o número solto seria arriscado.

## Ambiente de referência

`Update_Monitor_Novos_Fundos` é o mais maduro e serve de modelo:

- origem trocável (`ORIGEM=cvm|anbima`)
- validação a cada rodada (`validar_base`)
- aviso quando a fonte está defasada (`diagnosticar_fonte`)
- gráficos em ECharts com fallback para CSS quando a lib não carrega
- conciliação reprodutível contra a planilha (`comparar_agosto.py`)

Ver `DIAGNOSTICO_AGOSTO.md` nessa pasta para o raciocínio por trás de cada um.
