# Bibliotecas de terceiros

## echarts.min.js — Apache ECharts 5.6.0

Motor dos gráficos do relatório. Fica aqui, versionado, em vez de ser buscado
num CDN em tempo de execução, por duas razões:

1. **O PDF é gerado sem supervisão.** Num servidor, num agendamento ou numa
   máquina com a saída restrita, o CDN pode não responder. O gráfico não
   apareceria e o PDF sairia com um retângulo vazio — e ninguém veria, porque
   ninguém abre os 12 PDFs antes de publicar.
2. **Reprodutibilidade.** Uma versão fixa gera o mesmo gráfico hoje e no ano que
   vem. "Última versão do CDN" não garante isso.

O `run.py` embute este arquivo no HTML do relatório. O HTML resultante abre e
desenha sem rede nenhuma.

Licença: Apache License 2.0 (ver `echarts-LICENSE`). Obtido de
`npm pack echarts@5.6.0`, `dist/echarts.min.js`.

### Para atualizar

```powershell
npm pack echarts@5.6.0
tar xzf echarts-5.6.0.tgz
copy package\dist\echarts.min.js assets\vendor\
```

Trocar a versão é uma decisão consciente: confira os relatórios depois.


---

## html2canvas · jszip · jspdf

As bibliotecas que os **botões de exportação** dos materiais da Central usam
(Pacote JPG, Pacote PDF, Baixar PNG, E-mail HTML).

Nos materiais originais elas vêm do `cdnjs.cloudflare.com`, **sem alternativa**:
se o CDN estiver fora, bloqueado pela rede da empresa ou simplesmente lento, os
botões não fazem nada — sem erro na tela, porque o `onclick` chama uma função que
não existe.

Isso importa mais agora do que antes: o fluxo é *o HTML sai pronto do `run.py` e
a pessoa clica no botão*. O botão virou parte do processo, e um processo não pode
depender de um CDN que ninguém controla.

O `run.py` reescreve as tags `<script>` dos materiais para **tentar a cópia local
primeiro e cair no CDN se ela não estiver lá**, e copia estes arquivos para
`saida/AAAA-MM/central/vendor/`. Assim:

| Situação | O que acontece |
|---|---|
| Pasta da edição inteira | carrega local, funciona sem rede |
| Só o HTML, por e-mail | local dá 404, cai no CDN, funciona |
| Só o HTML e sem rede | botões não funcionam (como hoje) |

Versões: html2canvas 1.4.1 · jszip 3.10.1 · jspdf 2.5.1 — as mesmas que os
materiais já pediam ao CDN, obtidas com `npm pack`.
