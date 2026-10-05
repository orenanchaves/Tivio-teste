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

  /* ---------------------------------------------------- linha do histórico
     Mesma especificação do SVG do servidor (calculators/grafico.py,
     historico_modelo): cores, espessuras, margens, degrau e topo da grade,
     rótulos visíveis do eixo X. Tudo em unidades da folha (largura 1000) e
     escalado pela largura real do gráfico, para tela, PDF e PNG baterem. */
  function historico(d, larg) {
    var k = (larg || d.largura) / d.largura;
    var px = function (v) { return v * k; };
    var o = base();
    var pad = d.pad;
    o.grid = { left: px(pad[0]), right: px(pad[1]), top: px(pad[2]), bottom: px(pad[3]),
               containLabel: false };
    if (d.estilo === 'cp') {
      o.legend = {
        top: px(pad[2] - 30), left: 'center', itemWidth: px(34), itemHeight: px(3),
        itemGap: px(40), icon: 'rect',
        textStyle: { fontSize: px(12.5), fontWeight: 600, color: '#333', fontFamily: FF },
        data: [{ name: 'Fundo' }, { name: d.bench }].concat(d.trib ? [{ name: 'Bench Tributado' }] : [])
      };
    }
    o.xAxis = {
      type: 'category', data: d.labels, boundaryGap: false,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: {
        interval: 0, rotate: -d.rot, margin: px(14),
        fontSize: px(d.estilo === 'cp' ? 12.5 : 14.5), fontWeight: 600, color: '#333',
        fontFamily: FF,
        formatter: function (_, i) { return d.rotulos[i] || ''; }
      }
    };
    o.yAxis = {
      type: 'value', min: d.base, max: d.escala_topo, interval: d.passo,
      axisLine: { show: false }, axisTick: { show: false },
      splitLine: { lineStyle: { color: '#D6D6D6', width: 1 } },
      axisLabel: {
        margin: px(12), fontSize: px(d.estilo === 'cp' ? 13 : 15.5), fontWeight: 600,
        color: '#333', fontFamily: FF,
        // a grade vai até o topo; acima dele só a linha e a etiqueta
        formatter: function (v) { return v > d.topo + 1e-9 ? '' : pct(v, d.casas); }
      }
    };
    o.tooltip = {
      trigger: 'axis', valueFormatter: function (v) { return pct(v, 2); },
      textStyle: { fontFamily: FF, fontSize: 13 }
    };
    // o acumulado no fim de cada linha, numa etiqueta da cor dela; quando as
    // duas terminam juntas, o ECharts afasta uma da outra (moveOverlap)
    var etiqueta = function (fundo, cor, tinta) {
      return {
        show: true, distance: px(6), fontFamily: FF, fontSize: px(15), fontWeight: 700,
        color: tinta, backgroundColor: cor, borderRadius: px(3),
        padding: [px(5), px(7)],
        formatter: function (p) { return pct(p.value, 2); }
      };
    };
    var linha = function (nome, dados, cor, larg, tinta, z) {
      return {
        name: nome, type: 'line', data: dados, smooth: false, symbol: 'none', z: z,
        lineStyle: { width: px(larg), color: cor, cap: 'round', join: 'round' },
        itemStyle: { color: cor },
        endLabel: etiqueta(nome === 'Fundo', cor, tinta),
        labelLayout: { moveOverlap: 'shiftY' }
      };
    };
    o.series = [
      linha(d.bench, d.bench_serie, d.cb, d.wb, d.tinta_b, 2),
      linha('Fundo', d.fundo, d.cf, d.wf, '#fff', 3)
    ];
    if (d.trib) {
      // Bench Tributado (benchmark líquido de IR): só onde o fundo pede
      var t = linha('Bench Tributado', d.trib, d.ct, 2.4, '#fff', 1);
      t.lineStyle.type = [px(6), px(4)];
      o.series.splice(1, 0, t);
    }
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
    // sem contêiner para o ECharts assumir (o desenho do servidor é o final),
    // não há o que esperar — nem motivo para avisar que ele não carregou
    if (!document.querySelector('.tv-chart[data-tv]')) {
      window.__tvCharts = { ok: true, total: 0, desenhados: 0 };
      return;
    }
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
        // a altura acompanha a largura (o desenho é feito em 1000 de largura)
        var largura = el.clientWidth || 0;
        el.innerHTML = '';
        el.style.height = (d.largura && largura ? largura * d.altura / d.largura
                                                : (d.altura || 430)) + 'px';
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
    // texto curto CRESCE até o teto (data-teto) para não sobrar vão na caixa;
    // texto longo diminui até caber. Sem data-teto, só diminui (disclaimer).
    var max = parseFloat(el.getAttribute('data-max')) || 15;
    var teto = parseFloat(el.getAttribute('data-teto')) || max;
    var cabe = function (t) {
      el.style.fontSize = t + 'px';
      return el.scrollHeight <= el.clientHeight + 1;
    };
    el.style.paddingTop = '0px';
    var lo = 8, hi = teto;
    if (cabe(hi)) {
      lo = hi;
    } else {
      while (hi - lo > 0.2) {
        var meio = (lo + hi) / 2;
        if (cabe(meio)) { lo = meio; } else { hi = meio; }
      }
    }
    el.style.fontSize = (Math.floor(lo * 4) / 4) + 'px';
    // SAC e Ouvidoria no mesmo corpo do texto do disclaimer
    var faixa = el.closest && el.closest('.disc');
    var contatos = faixa && faixa.querySelector('.contatos');
    if (contatos) { contatos.style.fontSize = el.style.fontSize; }
    // data-centro: o que sobrar de altura vai metade em cima, metade embaixo
    // (o texto fica no meio da caixa, sem um vão grande só no pé)
    if (el.hasAttribute('data-centro')) {
      var sobra = el.clientHeight - el.scrollHeight;
      if (sobra > 4) { el.style.paddingTop = (sobra / 2) + 'px'; }
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
