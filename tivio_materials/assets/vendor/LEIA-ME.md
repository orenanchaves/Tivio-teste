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
