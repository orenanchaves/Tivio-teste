/* ===========================================================================
   Gráficos do Relatório de Gestão · Apache ECharts
   ---------------------------------------------------------------------------
   Cada bloco de gráfico chega do Python como:

       <div class="tv-chart" data-tv='{"tipo":"historico", ...}'>
         …SVG desenhado no servidor…
       </div>

   O SVG de dentro não é placeholder: é o gráfico, completo e correto. Este
   script o substitui por uma versão ECharts. Se o ECharts não carregar — CDN
   fora do ar, script bloqueado, JS desligado — o que estava lá continua lá.
   O relatório nunca sai com um retângulo vazio.

   renderer: 'svg' é obrigatório, não preferência. Em canvas o gráfico vira
   imagem rasterizada dentro de um PDF vetorial, que é o que faz um PDF
   parecer impressão de tela.
   ======================================================================== */
(function () {
  'use strict';

  var CORES = {
    azul: '#3C4A60', azulMedio: '#759DB4', cinzaClaro: '#ABC6CD',
    cinza: '#637881', grade: '#E3E9EE', texto: '#333'
  };
  var FF = 'Versos, "Helvetica Neue", Helvetica, Arial, sans-serif';

  function base() {
    return {
      animation: false,          // o PDF é um instantâneo: animar só atrasa
      textStyle: { fontFamily: FF, color: CORES.texto },
      grid: { containLabel: false }
    };
  }

  function pct(v, casas) {
    var s = Number(v).toFixed(casas === undefined ? 1 : casas);
    return s.replace('.', ',') + '%';
  }

  /* ---------------------------------------------------- linha do histórico */
  function historico(d) {
    var o = base();
    o.color = [CORES.azul, CORES.cinzaClaro];
    o.legend = {
      top: 2, left: 46, itemWidth: 26, itemHeight: 3, itemGap: 26,
      textStyle: { fontSize: 15, fontWeight: 700, color: CORES.azul, fontFamily: FF },
      data: [{ name: 'Fundo' }, { name: d.bench }]
    };
    o.grid = { left: 56, right: 76, top: 46, bottom: 46, containLabel: false };
    o.xAxis = {
      type: 'category', data: d.labels, boundaryGap: false,
      axisLine: { lineStyle: { color: CORES.grade } },
      axisTick: { show: false },
      axisLabel: {
        fontSize: 13, color: CORES.cinza, fontFamily: FF,
        // com 13+ meses os rótulos se tocam; o ECharts esconde sozinho, mas
        // escondendo do fim para o começo — e o último mês é o que importa
        interval: function (i) {
          var n = d.labels.length, passo = n <= 13 ? 1 : Math.ceil(n / 13);
          return i === n - 1 || i % passo === 0;
        }
      }
    };
    o.yAxis = {
      type: 'value', splitNumber: 4,
      axisLine: { show: false }, axisTick: { show: false },
      splitLine: { lineStyle: { color: CORES.grade } },
      axisLabel: {
        fontSize: 14, fontWeight: 600, color: CORES.cinza, fontFamily: FF,
        formatter: function (v) { return Math.round(v) + '%'; }
      }
    };
    o.tooltip = {
      trigger: 'axis',
      valueFormatter: function (v) { return pct(v, 2); },
      textStyle: { fontFamily: FF, fontSize: 13 }
    };
    var ultimo = {
      show: true, position: 'right', distance: 8, fontFamily: FF,
      formatter: function (p) {
        return p.dataIndex === d.fundo.length - 1 ? pct(p.value) : '';
      }
    };
    o.series = [
      {
        name: 'Fundo', type: 'line', data: d.fundo, smooth: false,
        symbol: 'circle', symbolSize: function (_, p) {
          return p.dataIndex === d.fundo.length - 1 ? 10 : 0;
        },
        lineStyle: { width: 3.4 }, z: 3,
        label: Object.assign({ fontSize: 15, fontWeight: 700, color: CORES.azul }, ultimo)
      },
      {
        name: d.bench, type: 'line', data: d.bench_serie, smooth: false,
        symbol: 'circle', symbolSize: function (_, p) {
          return p.dataIndex === d.bench_serie.length - 1 ? 8 : 0;
        },
        lineStyle: { width: 3, type: [7, 5] }, z: 2,
        label: Object.assign({ fontSize: 14, fontWeight: 600, color: CORES.cinza }, ultimo)
      }
    ];
    return o;
  }

  /* ------------------------------------------- barras horizontais (emissores) */
  function barras(d, larg) {
    var o = base();
    // ECharts desenha a categoria de baixo para cima; a lista chega do maior
    // para o menor, então inverte para o maior ficar no topo
    var nomes = d.itens.map(function (x) { return x[0]; }).reverse();
    var vals = d.itens.map(function (x) { return x[1]; }).reverse();

    /* A coluna do rótulo era 150px fixos. Numa folha inteira isso é folgado;
       na meia folha do ALT, não: "Comércio atacadista e varejista" saía como
       "Comércio atacadis…". O ECharts trunca em silêncio, então o nome some do
       relatório sem nenhum aviso. Agora a coluna, o corpo da fonte e o espaço
       do valor saem da largura real do bloco. */
    larg = larg || 886;
    var estreito = larg < 520;
    var colRot = Math.round(Math.max(96, Math.min(186, larg * 0.42)));
    var colVal = estreito ? 48 : 66;
    var corpo = estreito ? 12.2 : 13.4;
    o.grid = { left: colRot + 8, right: colVal, top: 4, bottom: 4,
               containLabel: false };
    o.xAxis = { type: 'value', show: true, axisLabel: { show: false },
                axisLine: { show: false }, axisTick: { show: false },
                splitLine: { show: false }, max: Math.max.apply(null, vals) * 1.02 };
    o.yAxis = {
      type: 'category', data: nomes,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: {
        fontSize: corpo, color: CORES.texto, fontFamily: FF, width: colRot,
        overflow: 'truncate', align: 'left', margin: colRot + 8
      }
    };
    // Atenção: o valor da série é a LARGURA relativa (0-100), não o
    // percentual do emissor — a barra é proporcional ao maior, senão um fundo
    // concentrado deixa todas as outras invisíveis. O número real está em
    // `rotulos`, e é ele que aparece no rótulo e no tooltip.
    o.tooltip = {
      trigger: 'item', textStyle: { fontFamily: FF },
      formatter: function (p) {
        return p.name + ': <b>' + d.rotulos[vals.length - 1 - p.dataIndex] + '</b>';
      }
    };
    o.series = [{
      type: 'bar', data: vals, barWidth: 17,
      itemStyle: {
        borderRadius: 2,
        color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
                 colorStops: [{ offset: 0, color: d.cor || CORES.azul },
                              { offset: 1, color: CORES.cinza }] }
      },
      showBackground: true,
      backgroundStyle: { color: 'rgba(212,224,230,.45)', borderRadius: 2 },
      label: {
        show: true, position: 'right', distance: 10, fontFamily: FF,
        fontSize: corpo, fontWeight: 700, color: CORES.azul,
        formatter: function (p) { return d.rotulos[vals.length - 1 - p.dataIndex]; }
      }
    }];
    return o;
  }

  /* ------------------------------------------------- colunas (rating) */
  function colunas(d) {
    var o = base();
    o.grid = { left: 8, right: 8, top: 30, bottom: 30, containLabel: false };
    o.xAxis = {
      type: 'category', data: d.itens.map(function (x) { return x[0]; }),
      axisLine: { lineStyle: { color: CORES.azul, width: 1.6 } },
      axisTick: { show: false },
      axisLabel: { fontSize: 14, color: CORES.texto, fontFamily: FF }
    };
    o.yAxis = { type: 'value', show: false,
                max: Math.max.apply(null, d.itens.map(function (x) { return x[1]; })) * 1.22 };
    // mesma observação das barras: o valor é a altura relativa, o número é o rótulo
    o.tooltip = {
      trigger: 'item', textStyle: { fontFamily: FF },
      formatter: function (p) { return p.name + ': <b>' + d.rotulos[p.dataIndex] + '</b>'; }
    };
    o.series = [{
      type: 'bar', barWidth: '58%',
      data: d.itens.map(function (x) { return x[1]; }),
      itemStyle: {
        borderRadius: [3, 3, 0, 0],
        color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                 colorStops: [{ offset: 0, color: '#9FB6C7' },
                              { offset: 0.55, color: '#7E9DB1' },
                              { offset: 1, color: '#6C8CA1' }] }
      },
      label: {
        show: true, position: 'top', fontFamily: FF, fontSize: 14.5,
        fontWeight: 700, color: CORES.azul,
        formatter: function (p) { return d.rotulos[p.dataIndex]; }
      }
    }];
    return o;
  }

  var MONTAGEM = { historico: historico, barras: barras, colunas: colunas };

  function desenhar() {
    if (typeof echarts === 'undefined') {
      // sem ECharts o SVG do servidor permanece — é o comportamento desejado
      window.__tvCharts = { ok: false, motivo: 'echarts não carregou', total: 0 };
      return;
    }
    var alvos = document.querySelectorAll('.tv-chart[data-tv]');
    var feitos = 0;
    for (var i = 0; i < alvos.length; i++) {
      var el = alvos[i];
      try {
        var d = JSON.parse(el.getAttribute('data-tv'));
        var monta = MONTAGEM[d.tipo];
        if (!monta) { continue; }
        el.innerHTML = '';
        el.style.height = (d.altura || 430) + 'px';
        var g = echarts.init(el, null, { renderer: 'svg' });
        g.setOption(monta(d, el.clientWidth || 0));
        feitos++;
      } catch (e) {
        // um gráfico com problema não derruba os outros nem apaga o fallback
        if (window.console) { console.warn('tv-chart:', e); }
      }
    }
    // o exportador de PDF espera por esta marca antes de imprimir
    window.__tvCharts = { ok: true, total: alvos.length, desenhados: feitos };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', desenhar);
  } else {
    desenhar();
  }
})();

/* Texto que precisa caber numa caixa fixa da folha: o comentário do gestor
   (4 parágrafos num fundo, 7 noutro) e o disclaimer. Começa no corpo do
   relatório publicado (`data-max`) e desce de 0,25 px até não sobrar nada —
   a folha tem overflow:hidden e o excedente sumiria sem aviso. Roda ao abrir
   e de novo ao trocar de aba, porque aba escondida não tem altura. */
(function () {
  function ajustar(el) {
    if (!el.clientHeight) { return; }
    var max = parseFloat(el.getAttribute('data-max')) || 15;
    var t = max;
    el.style.fontSize = t + 'px';
    while (el.scrollHeight > el.clientHeight + 1 && t > 8) {
      t -= 0.25;
      el.style.fontSize = t + 'px';
    }
  }
  function ajustarTextos() {
    var els = document.querySelectorAll('.tv-ajusta');
    for (var i = 0; i < els.length; i++) { ajustar(els[i]); }
  }
  window.tvAjustarTextos = ajustarTextos;
  /* Os SVGs dos logos dos fundos vêm com muita margem interna (no
     Institucional o desenho ocupa um quarto da altura). Recorta o viewBox
     pelo contorno real do desenho, para a altura do CSS ser a do logo. */
  function recortarLogos() {
    var svgs = document.querySelectorAll('.fund-logo svg');
    for (var i = 0; i < svgs.length; i++) {
      var s = svgs[i];
      if (s.getAttribute('data-recortado')) { continue; }
      try {
        var b = s.getBBox();
        if (b.width > 0 && b.height > 0) {
          s.setAttribute('viewBox', [b.x, b.y, b.width, b.height].join(' '));
          s.setAttribute('preserveAspectRatio', 'xMinYMid meet');
          s.setAttribute('data-recortado', '1');
        }
      } catch (e) { /* aba escondida: tenta de novo ao trocar */ }
    }
  }
  function iniciar() {
    recortarLogos();
    ajustarTextos();
    if (document.fonts && document.fonts.ready) { document.fonts.ready.then(ajustarTextos); }
    document.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('.ftab')) {
        setTimeout(function () { recortarLogos(); ajustarTextos(); }, 30);
      }
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
})();
