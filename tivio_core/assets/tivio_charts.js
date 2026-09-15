/* ==================================================================
   tivio_charts.js - graficos dos dashboards da Tivio
   ------------------------------------------------------------------
   Extraido do Monitor de Novos Fundos, que foi o primeiro a receber
   ECharts. Fica aqui para os outros dashboards usarem o mesmo modulo
   em vez de cada template repetir a implementacao - foi o que motivou
   o tivio_core no Python, e vale igual no JS.

   Injetado INLINE no HTML por template.injetar_charts(): os dashboards
   circulam como arquivo solto, entao um <script src> externo quebraria
   assim que alguem movesse so o .html.

   API:
     bars(el, items, opt)      barras horizontais
     renderEvolucao(el, items) colunas por periodo
     barsCss(el, items, opt)   fallback sem a lib

   items: [{n: rotulo, v: valor, c: cor, k?: chave de clique, sel?: bool}]
   opt:   {chip, w, h, vw, fmt, filtro}
   ================================================================== */

/* ==================================================================
   GRAFICOS EM ECHARTS
   ------------------------------------------------------------------
   Todos os paineis de barras do dashboard passam por bars(), entao a
   troca e feita aqui dentro: quem chama nao muda, e os oito paineis
   (gestoras, credito privado, top gestoras, novas, ANBIMA, publico,
   faixas de taxa, taxa por gestora) sobem juntos e consistentes.
   A evolucao mensal tem forma propria - colunas - e fica em
   renderEvolucao().

   Cores saem dos tokens do Design System, entao claro e escuro
   continuam resolvidos por CSS. Canvas nao herda CSS: por isso o
   MutationObserver no fim redesenha tudo quando o tema vira.

   Degradacao: sem a lib (offline, CDN bloqueado) cai em barsCss(),
   que e exatamente o render anterior. O painel nunca fica vazio.
   ================================================================== */
var _tvCharts = [];          /* [{el, tipo, items, opt}] para redesenhar */
var _tvEsperas = 0;

function _tok(nome, fallback){
  var v = getComputedStyle(document.documentElement)
            .getPropertyValue(nome).trim();
  return v || fallback;
}

/* "#C1F4D4" + .32 -> "rgba(193,244,212,.32)" · aceita hex de 3 ou 6 */
function _alpha(cor, a){
  var h = String(cor).trim();
  if(h.charAt(0) !== '#') return h;
  h = h.slice(1);
  if(h.length === 3) h = h[0]+h[0]+h[1]+h[1]+h[2]+h[2];
  if(h.length !== 6) return cor;
  var n = parseInt(h, 16);
  return 'rgba('+((n>>16)&255)+','+((n>>8)&255)+','+(n&255)+','+a+')';
}

/* O canvas do ECharts NAO herda CSS: sem isto os graficos saem na fonte
   padrao da lib enquanto a pagina inteira usa Versos. Le o mesmo token
   --ff, entao segue a fonte da marca sem duplicar a lista.            */
function _ff(){
  return _tok('--ff', '"Versos","Helvetica Neue",Helvetica,Arial,sans-serif');
}

/* Mede o rotulo na fonte que esta realmente valendo. Reservar espaco por
   conta fixa quebra dos dois lados: com a metrica do fallback sobra
   espaco, com a do Versos falta e o ECharts corta. containLabel tambem
   nao serve aqui - com o rotulo rich (o chip da gestora) ele reserva
   menos que o bloco desenhado e joga o texto para fora do canvas.   */
function _larguraTexto(textos, fonte){
  var cv = _larguraTexto._cv
        || (_larguraTexto._cv = document.createElement('canvas'));
  var ctx = cv.getContext('2d');
  ctx.font = fonte;
  var maior = 0;
  for(var i = 0; i < textos.length; i++){
    maior = Math.max(maior, ctx.measureText(String(textos[i])).width);
  }
  return Math.ceil(maior);
}

/* axisLabel.width + overflow:'truncate' NAO truncam quando o rotulo usa
   rich text (o chip da gestora): o bloco cresce ate o conteudo e o texto
   longo sai pela esquerda do canvas. Entao o corte e feito aqui, antes
   de montar a marcacao.                                              */
function _cortar(txt, limite, fonte){
  txt = String(txt);
  if(_larguraTexto([txt], fonte) <= limite) return txt;
  var corte = txt;
  while(corte.length > 1 &&
        _larguraTexto([corte + '…'], fonte) > limite){
    corte = corte.slice(0, -1);
  }
  return corte + '…';
}

function _tvRegistra(el, tipo, items, opt){
  for(var i = 0; i < _tvCharts.length; i++){
    if(_tvCharts[i].el === el){
      _tvCharts[i] = {el:el, tipo:tipo, items:items, opt:opt};
      return;
    }
  }
  _tvCharts.push({el:el, tipo:tipo, items:items, opt:opt});
}

/* a lib pode ainda estar a caminho (o onerror do <script> baixa o
   segundo CDN). Desenha o fallback agora e tenta de novo por 5s.     */
function _tvAguardaLib(){
  if(window.echarts || _tvEsperas >= 20) return;
  _tvEsperas++;
  setTimeout(function(){
    if(window.echarts){
      _tvCharts.slice().forEach(function(c){
        c.el.innerHTML = "";
        if(c.tipo === 'evo') renderEvolucao(c.el, c.items);
        else bars(c.el, c.items, c.opt);
      });
    } else {
      _tvAguardaLib();
    }
  }, 250);
}

/* Paineis de abas inativas estao em display:none, onde o canvas nasce
   0x0 e ficaria em branco ao trocar de aba. O observador redesenha
   assim que o elemento ganha tamanho - serve para troca de aba, para
   o painel lateral e para qualquer mudanca de layout.              */
var _tvLargura = new WeakMap();

var _tvRO = (typeof ResizeObserver !== 'undefined')
  ? new ResizeObserver(function(ents){
      ents.forEach(function(e){
        var w = Math.round(e.contentRect.width);
        if(w < 1) return;
        /* so a largura dispara o resize. A altura quem define e bars(),
           e reagir a ela realimentaria o proprio observador.          */
        if(_tvLargura.get(e.target) === w) return;
        _tvLargura.set(e.target, w);
        var i = echarts.getInstanceByDom(e.target);
        if(i) i.resize();
      });
    })
  : null;

function _tvInstancia(el){
  var inst = echarts.getInstanceByDom(el);
  if(inst) return inst;
  el.innerHTML = "";
  inst = echarts.init(el, null, {renderer:'canvas'});
  if(_tvRO) _tvRO.observe(el);
  return inst;
}

/* ---------------------------------------------- barras horizontais */
function barsCss(el, items, opt){
  var max = items.length
    ? Math.max.apply(null, items.map(function(i){ return i.v; })) || 1 : 1;
  el.innerHTML = items.length ? items.map(function(i){
    return '<div class="gbar-row'+(i.k?' gbar-click':'')+'"'+(i.k?' data-gkey="'+esc(i.k)+'" data-gfiltro="'+esc(opt.filtro||'')+'" title="Ver as classes · '+esc(i.n)+'"':'')+'>' +
      (opt.chip
        ? '<div class="gbar-logo"><span style="background:'+i.c+';color:var(--text-primary);padding:6px 14px;border-radius:6px;font-weight:700;font-size:13px">'+esc(i.n)+'</span></div>'
        : '<div style="width:'+(opt.w||170)+'px;font-size:12px;color:color-mix(in srgb,var(--veil) 85%,transparent)" title="'+esc(i.n)+'">'+esc(i.n)+'</div>') +
      '<div class="gbar-track" style="height:'+(opt.h||26)+'px"><div class="gbar-fill" style="width:'+(i.v/max*100).toFixed(1)+'%;background:linear-gradient(90deg,'+i.c+','+i.c+'88)"></div></div>' +
      '<div class="gbar-value" style="font-size:14px;width:'+(opt.vw||36)+'px">'+(opt.fmt?opt.fmt(i.v):i.v)+'</div>' +
    '</div>';
  }).join('')
    : '<div style="color:var(--muted);font-size:12px">Sem registros no período.</div>';
}

/* Rotulo do eixo: com chip usa rich (fundo colorido por gestora), sem
   chip usa texto simples - rich sem necessidade so traz o problema de
   medicao de volta.                                                  */
function _rotuloEixo(ordem, rotulos, opt, muted){
  var base = {margin: 12, fontFamily: _ff()};

  if(!opt.chip){
    base.color = muted;
    base.fontSize = 11;
    base.formatter = function(v, n){ return rotulos[n]; };
    return base;
  }

  var rich = {};
  ordem.forEach(function(i, n){
    rich['c' + n] = {
      backgroundColor: i.c,
      color: _tok('--text-primary', '#FFF'),
      fontWeight: 700, fontSize: 12,
      padding: [4, 9, 4, 9], borderRadius: 5,
      align: 'left', fontFamily: _ff()
    };
  });

  base.rich = rich;
  base.formatter = function(v, n){ return '{c' + n + '|' + rotulos[n] + '}'; };
  return base;
}

function bars(el, items, opt){
  opt = opt || {};
  if(!el) return;

  if(!items || !items.length){
    el.style.height = "";
    el.innerHTML = '<div style="color:var(--muted);font-size:12px">Sem registros no período.</div>';
    return;
  }

  _tvRegistra(el, 'bars', items, opt);

  if(!window.echarts){
    barsCss(el, items, opt);
    _tvAguardaLib();
    return;
  }

  var muted = _tok('--text-muted', '#8A99A3');
  var linha = _tok('--line', 'rgba(255,255,255,.10)');
  var fundo = _tok('--bg-elev-1', '#11181E');
  var tinta = _tok('--text-primary', '#FFF');

  /* Altura: ocupa a folga do painel em vez de deixar um vazio embaixo
     (credito privado com 1 gestora ficava com 90px de grafico dentro de
     um painel de 498px). A folga e medida a partir do PAINEL e dos
     IRMAOS, nunca do proprio elemento - medir a si mesmo com flex:1
     realimenta o ResizeObserver e a altura dispara.                   */
  var alturaLinha = (opt.h || 26) + 14;
  var natural = Math.max(items.length * alturaLinha + 16, 90);

  el.style.flex = "";
  el.style.minHeight = "";
  el.style.gap = "";

  var pane = el.closest ? el.closest('.panel') : null;
  var alvo = natural;

  if(pane){
    var cs = getComputedStyle(pane);
    var livre = pane.clientHeight
              - parseFloat(cs.paddingTop || 0)
              - parseFloat(cs.paddingBottom || 0);

    for(var n = 0; n < pane.children.length; n++){
      var filho = pane.children[n];
      if(filho === el) continue;
      var fcs = getComputedStyle(filho);
      livre -= filho.offsetHeight
             + parseFloat(fcs.marginTop || 0)
             + parseFloat(fcs.marginBottom || 0);
    }

    if(livre > natural) alvo = Math.floor(livre);
  }

  el.style.height = alvo + "px";

  var chart = _tvInstancia(el);

  /* ECharts desenha a categoria de baixo para cima: inverte para o
     maior ficar no topo, como na lista de barras anterior          */
  var ordem = items.slice().reverse();

  var fonteRotulo = (opt.chip ? '700 12px ' : '400 11px ') + _ff();
  var limite = (opt.w || 150) - (opt.chip ? 20 : 0);

  /* o eixo mostra exatamente estes textos - ja cortados */
  var rotulos = ordem.map(function(i){
    return _cortar(i.n, limite, fonteRotulo);
  });

  var larguraRotulo = _larguraTexto(rotulos, fonteRotulo)
                    + (opt.chip ? 20 : 2);

  var textosValor = ordem.map(function(i){
    return String(opt.fmt ? opt.fmt(i.v) : i.v);
  });

  var larguraValor = Math.max(
    _larguraTexto(textosValor, '600 13px ' + _ff()),
    opt.vw || 42
  );

  chart.setOption({
    animationDuration: 380,
    textStyle: {fontFamily: _ff()},
    grid: {
      left: larguraRotulo + (opt.chip ? 26 : 16),
      /* o rotulo de valor tambem precisa caber: com fmt devolvendo
         "+R$ 4,1 Bi" a margem fixa cortava o texto na borda direita */
      right: larguraValor + 16,
      top: 4, bottom: 4
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: fundo, borderColor: linha,
      textStyle: {color: tinta, fontSize: 12},
      formatter: function(p){
        var it = ordem[p.dataIndex];
        return '<b>' + it.n + '</b><br>' +
               (opt.fmt ? opt.fmt(it.v) : it.v) +
               (it.k ? '<br><span style="color:' + muted +
                       '">clique para ver as classes</span>' : '');
      }
    },
    xAxis: {type:'value', show:false, max:'dataMax'},
    yAxis: {
      type: 'category',
      data: ordem.map(function(i){ return i.n; }),
      axisLine: {show:false}, axisTick: {show:false},
      /* triggerEvent devolve o clique ao nome/chip da gestora: antes do
         ECharts a linha inteira (.gbar-row) era o alvo, nao so a barra */
      triggerEvent: true,
      axisLabel: _rotuloEixo(ordem, rotulos, opt, muted)
    },
    series: [{
      type: 'bar',
      data: ordem.map(function(i){
        return {
          value: i.v,
          itemStyle: {
            color: {
              type: 'linear', x:0, y:0, x2:1, y2:0,
              colorStops: [{offset:0, color:i.c},
                           {offset:1, color:_alpha(i.c, .53)}]
            },
            borderRadius: [0, 4, 4, 0]
          }
        };
      }),
      barMaxWidth: opt.h || 22,
      cursor: items.some(function(i){ return !!i.k; }) ? 'pointer' : 'default',
      label: {
        show: true, position: 'right', color: tinta,
        fontSize: 13, fontWeight: 600,
        formatter: function(p){
          var it = ordem[p.dataIndex];
          return opt.fmt ? opt.fmt(it.v) : it.v;
        }
      }
    }]
  }, true);

  chart.off('click');
  chart.on('click', function(p){
    /* barra -> dataIndex · rotulo do eixo -> p.value tem o nome */
    var it = (p.componentType === 'yAxis')
      ? ordem.filter(function(i){ return i.n === p.value; })[0]
      : ordem[p.dataIndex];
    if(it && it.k) openGestoraModal(it.k, opt.filtro || "");
  });

  /* cursor de mao tambem sobre os rotulos clicaveis */
  chart.getZr().on('mousemove', function(e){
    var alvo = e.target;
    var sobreRotulo = alvo && alvo.__hoverStyle !== undefined
                      && items.some(function(i){ return !!i.k; });
    chart.getZr().setCursorStyle(sobreRotulo ? 'pointer' : 'default');
  });

  chart.resize();
}

/* -------------------------------------------- evolucao: colunas */
function renderEvolucao(el, items){
  if(!el) return;
  _tvRegistra(el, 'evo', items, null);

  if(!window.echarts){
    var poucas = items.length <= 4;
    el.style.flex = poucas ? "1" : "";
    el.style.justifyContent = poucas ? "center" : "";
    el.style.gap = poucas ? "18px" : "";
    barsCss(el, items, {w:70, h: poucas ? 30 : 22});
    _tvAguardaLib();
    return;
  }

  el.style.flex = "1";
  el.style.minHeight = "220px";
  el.style.gap = "";

  var chart = _tvInstancia(el);

  var accent = _tok('--accent-strong', '#C1F4D4');
  var muted  = _tok('--text-muted', '#8A99A3');
  var linha  = _tok('--line', 'rgba(255,255,255,.10)');
  var fundo  = _tok('--bg-elev-1', '#11181E');
  var tinta  = _tok('--text-primary', '#FFF');

  var valores = items.map(function(i){ return i.v; });
  var total   = valores.reduce(function(a,b){ return a+b; }, 0);
  var comDado = valores.filter(function(v){ return v > 0; });
  var media   = comDado.length ? total / comDado.length : 0;

  chart.setOption({
    animationDuration: 420,
    textStyle: {fontFamily: _ff()},
    grid: {left:2, right:12, top:26, bottom:2, containLabel:true},
    tooltip: {
      trigger: 'axis', axisPointer: {type:'shadow'},
      backgroundColor: fundo, borderColor: linha,
      textStyle: {color: tinta, fontSize: 12},
      formatter: function(ps){
        var p = ps[0];
        var pct = total ? (p.value / total * 100).toFixed(1) : '0.0';
        return '<b>'+p.name+'</b><br>'+p.value+' classe'+(p.value===1?'':'s')+
               '<br><span style="color:'+muted+'">'+
               String(pct).replace('.', ',')+'% do periodo</span>';
      }
    },
    xAxis: {
      type: 'category',
      data: items.map(function(i){ return i.n; }),
      axisLine: {lineStyle:{color: linha}}, axisTick: {show:false},
      axisLabel: {color: muted, fontSize: 11, interval: 0, hideOverlap: true}
    },
    yAxis: {
      type: 'value',
      splitLine: {lineStyle:{color: linha}},
      axisLabel: {color: muted, fontSize: 11},
      minInterval: 1
    },
    series: [{
      type: 'bar',
      data: items.map(function(i){
        return {
          value: i.v,
          itemStyle: {
            color: i.sel ? accent : _alpha(accent, .32),
            borderRadius: [3, 3, 0, 0]
          }
        };
      }),
      barMaxWidth: 34,
      cursor: 'pointer',
      label: {
        show: true, position: 'top', color: muted,
        fontSize: 11, fontWeight: 600,
        formatter: function(p){ return p.value > 0 ? p.value : ''; }
      },
      markLine: media > 0 ? {
        silent: true, symbol: 'none',
        lineStyle: {color: muted, type: 'dashed', width: 1, opacity: .55},
        label: {
          color: muted, fontSize: 10, position: 'insideEndTop',
          formatter: 'media ' + media.toFixed(1).replace('.', ',')
        },
        data: [{yAxis: media}]
      } : undefined
    }]
  }, true);

  chart.off('click');
  chart.on('click', function(p){
    var it = items[p.dataIndex];
    if(!it) return;
    var alvo = document.querySelector('.month-pill[data-month="'+it.k+'"]');
    if(alvo) alvo.click();
  });

  chart.resize();
}

/* As webfonts chegam depois do primeiro render: sem isto a largura dos
   rotulos fica medida na fonte de fallback e o eixo sai desalinhado
   quando o Versos entra. */
if(document.fonts && document.fonts.ready){
  document.fonts.ready.then(function(){
    if(!window.echarts) return;
    _tvCharts.forEach(function(c){
      if(c.tipo === 'evo') renderEvolucao(c.el, c.items);
      else bars(c.el, c.items, c.opt);
    });
  });
}

/* canvas nao herda CSS: redesenha tudo quando o tema vira */
new MutationObserver(function(){
  if(!window.echarts) return;
  _tvCharts.forEach(function(c){
    if(c.tipo === 'evo') renderEvolucao(c.el, c.items);
    else bars(c.el, c.items, c.opt);
  });
}).observe(document.documentElement,
           {attributes:true, attributeFilter:['data-theme']});

window.addEventListener('resize', function(){
  if(!window.echarts) return;
  _tvCharts.forEach(function(c){
    var i = echarts.getInstanceByDom(c.el);
    if(i) i.resize();
  });
});


/* ==================================================================
   tvUpgrade - troca barras em CSS ja renderizadas por ECharts
   ------------------------------------------------------------------
   Cada dashboard monta suas barras de um jeito: uns por template
   literal no JS, outros com o HTML escrito direto no arquivo. Reescrever
   quatro implementacoes diferentes seria arriscado e nao sobreviveria a
   proxima alteracao de qualquer um deles.

   Aqui a leitura e do DOM ja pronto: pega rotulo, valor e cor de cada
   linha que o proprio dashboard desenhou e redesenha o conjunto com
   ECharts. Funciona igual nos quatro, e se a lib nao carregar o painel
   simplesmente fica como estava.
   ================================================================== */

/* O canvas nao entende var(--x) nem color-mix(): as barras em CSS usam
   os dois, e passar direto para o ECharts derruba o gradiente com
   "could not be parsed as a color". Resolve para um valor concreto. */
function _corConcreta(el){
  var bruto = el.style.background || el.style.backgroundColor || "";

  var mv = bruto.match(/var\((--[a-z0-9-]+)/i);

  if(mv){
    var v = _tok(mv[1], "");
    /* o token pode apontar para outro token */
    for(var i = 0; i < 3 && /^var\(/.test(v); i++){
      var m2 = v.match(/var\((--[a-z0-9-]+)/i);
      v = m2 ? _tok(m2[1], "") : "";
    }
    if(v && !/var\(|color-mix/.test(v)) return v.trim();
  }

  var mh = bruto.match(/#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)/);
  if(mh) return mh[0];

  /* ultimo recurso: o que o browser calculou para o elemento */
  var comp = getComputedStyle(el).backgroundColor;
  if(comp && comp !== "rgba(0, 0, 0, 0)") return comp;

  return _tok("--accent-strong", "#C1F4D4");
}


function _tvLinhas(cont, selFill){
  /* cada linha e o ancestral comum entre o preenchimento e o rotulo */
  var fills = cont.querySelectorAll(selFill);
  var itens = [];

  for(var i = 0; i < fills.length; i++){
    var fill = fills[i];
    var linha = fill.closest('[class*="row"], li, tr') || fill.parentElement;

    if(!linha) continue;

    /* largura ja calculada pelo dashboard = o valor relativo */
    var largura = parseFloat(fill.style.width) || 0;

    /* graficos divergentes tem eixo zero no meio: o lado esquerdo e
       negativo. Sem isto "-R$ 2,3 Bi" desenhava barra para a direita,
       igual a um valor positivo - o grafico dizia o contrario do rotulo. */
    var metade = fill.closest('[class*="half"]');

    if(metade && /\bleft\b/.test(metade.className)) largura = -largura;

    /* rotulo: o primeiro texto da linha que nao esteja dentro da barra */
    var texto = "";
    var valor = "";

    for(var n = 0; n < linha.children.length; n++){
      var c = linha.children[n];
      if(c.contains(fill)) continue;
      var t = (c.textContent || "").trim();
      if(!t) continue;
      if(!texto) texto = t; else if(!valor) valor = t;
    }

    if(!texto) continue;

    itens.push({
      n: texto.replace(/\s+/g, " ").slice(0, 46),
      v: largura,
      c: _corConcreta(fill),
      rotuloValor: valor,
    });
  }

  return itens;
}

function tvUpgrade(cont, opt){
  opt = opt || {};

  if(!window.echarts || !cont) return false;

  var itens = _tvLinhas(cont, opt.fill || '[class*="fill"]:not([class*="scroll"])');

  if(itens.length < 2) return false;          /* 1 barra nao e grafico */

  /* o rotulo de valor que o dashboard ja formatou vale mais que o
     numero cru: mantem "R$ 45,3 Bi" em vez de virar a largura em % */
  var comRotulo = itens.filter(function(i){ return i.rotuloValor; }).length;

  if(comRotulo === itens.length){
    opt.fmt = function(v){
      for(var i = 0; i < itens.length; i++){
        if(itens[i].v === v) return itens[i].rotuloValor;
      }
      return v;
    };
  }

  cont.setAttribute("data-tv-upgraded", "1");
  bars(cont, itens, opt);

  return true;
}

function tvUpgradeTodos(sel, opt){
  var alvos = document.querySelectorAll(sel);
  var n = 0;

  for(var i = 0; i < alvos.length; i++){
    if(alvos[i].getAttribute("data-tv-upgraded")) continue;
    if(tvUpgrade(alvos[i], opt)) n++;
  }

  return n;
}
