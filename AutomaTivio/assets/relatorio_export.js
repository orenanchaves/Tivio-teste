/* ===========================================================================
   Barra de exportação do Relatório de Gestão
   ---------------------------------------------------------------------------
   O modelo do ambiente é de dois passos: o Python gera a tela em HTML, e os
   botões exportam. Os materiais da Central já funcionavam assim; os relatórios
   gerados não tinham botão nenhum — saíam só pelo `run.py`. Esta barra fecha
   isso: o mesmo HTML que o Python entrega vira PDF, JPG, PNG ou PPTX no clique.

   Por que continuar gerando PDF e PPTX também no servidor: são 13 fundos. O
   `run.py` entrega os 13 de uma vez, sem ninguém abrir nada, e o PDF de lá é
   vetorial. O botão serve ao caso em que a pessoa editou um texto na tela e
   quer reexportar aquele relatório — algo que o servidor não tem como saber.

   As bibliotecas carregam sob demanda (local primeiro, CDN como reserva):
   quem só abre para ler não paga 1,8 MB de download.
   ======================================================================== */
(function () {
  'use strict';

  var LIBS = {
    html2canvas: ['vendor/html2canvas.min.js',
                  'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'],
    jszip: ['vendor/jszip.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js'],
    jspdf: ['vendor/jspdf.umd.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'],
    pptxgen: ['vendor/pptxgen.min.js',
              'https://cdnjs.cloudflare.com/ajax/libs/pptxgenjs/3.12.0/pptxgen.min.js'],
  };
  var PRONTO = {
    html2canvas: function () { return typeof html2canvas !== 'undefined'; },
    jszip: function () { return typeof JSZip !== 'undefined'; },
    jspdf: function () { return typeof window.jspdf !== 'undefined'; },
    pptxgen: function () { return typeof PptxGenJS !== 'undefined'; },
  };

  function carregarUm(src) {
    return new Promise(function (ok, erro) {
      var s = document.createElement('script');
      s.src = src;
      // crossOrigin só faz sentido em URL absoluta: numa página aberta por
      // file:// ele transforma o arquivo local numa requisição CORS de origem
      // opaca, que o navegador recusa com o arquivo ali do lado
      if (/^https?:/i.test(src)) { s.crossOrigin = 'anonymous'; }
      s.onload = function () { ok(true); };
      s.onerror = function () { erro(new Error(src)); };
      document.head.appendChild(s);
    });
  }

  function garantir(nome) {
    if (PRONTO[nome]()) { return Promise.resolve(true); }
    var fontes = LIBS[nome].slice();
    return (function tenta() {
      if (!fontes.length) {
        return Promise.reject(new Error('não consegui carregar ' + nome));
      }
      return carregarUm(fontes.shift()).then(function () {
        return PRONTO[nome]() ? true : tenta();
      }, tenta);
    })();
  }

  // ------------------------------------------------------------------ apoio
  var META = (window.TV_RELATORIO || {});

  /* O documento pode conter vários fundos (a página por vertical). Exportar
     tem de pegar SÓ o que está na tela — senão o PDF do Banks sai com as 40
     folhas dos dez fundos. Quando não há abas, o documento inteiro é o deck. */
  function deckAtivo() {
    return document.querySelector('.deck.ativo') || document;
  }

  var folhas = function () {
    return [].slice.call(deckAtivo().querySelectorAll('.rcard'));
  };

  /* ------------------------------------------------- enquadramento da folha
     A folha tem 1000 px de largura fixa — é um A4. Em tela menor que isso ela
     transbordava pela direita, e no celular isso aparecia como título cortado
     no meio da palavra e disclaimer saindo da borda.

     O CSS já traz degraus de --folha-zoom para o primeiro quadro; aqui o valor
     fica exato, medido na largura que a página realmente tem. `zoom` não muda
     clientWidth, então medir não entra em laço com o que a medida provoca. */
  var LARGURA_FOLHA = 1000;

  function enquadrar() {
    var host = deckAtivo().querySelector('.folhas') ||
               document.querySelector('.folhas');
    if (!host) { return; }
    var cs = getComputedStyle(host);
    var disp = host.clientWidth -
               (parseFloat(cs.paddingLeft) || 0) - (parseFloat(cs.paddingRight) || 0);
    if (!(disp > 0)) { return; }
    var z = Math.min(1, disp / LARGURA_FOLHA);
    document.documentElement.style.setProperty(
      '--folha-zoom', String(Math.floor(z * 1e4) / 1e4));
  }

  function ligarEnquadramento() {
    enquadrar();
    var t;
    var refaz = function () { clearTimeout(t); t = setTimeout(enquadrar, 120); };
    window.addEventListener('resize', refaz);
    window.addEventListener('orientationchange', refaz);
  }

  function nomeArquivo(sufixo, ext) {
    var d = document.querySelector('.deck.ativo');
    var base = (d && d.getAttribute('data-arquivo')) ||
               META.arquivo || document.title || 'relatorio';
    base = base.replace(/[\\/:*?"<>|]+/g, '-');
    return base + (sufixo ? ' - ' + sufixo : '') + '.' + ext;
  }

  function baixar(blob, nome) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = nome;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 4000);
  }

  /* A página por vertical veste a casca do gerador oficial e já traz o seu
     `#toast`; o relatório solto não tem casca nenhuma, e aí a bolha é criada
     aqui. Um aviso só, duas molduras. */
  function aviso(txt, erro) {
    var t = document.getElementById('toast');
    if (t) {
      t.textContent = txt;
      t.classList.add('show');
      clearTimeout(t._x);
      t._x = setTimeout(function () { t.classList.remove('show'); }, erro ? 7000 : 3000);
      return;
    }
    t = document.getElementById('tv-toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'tv-toast';
      document.body.appendChild(t);
    }
    t.textContent = txt;
    t.className = 'tv-toast mostra' + (erro ? ' erro' : '');
    clearTimeout(t._t);
    t._t = setTimeout(function () { t.className = 'tv-toast'; }, erro ? 7000 : 2600);
  }

  /* Captura uma folha em bitmap.

     escala 3 dá ~3000x4242 px numa folha A4 — suficiente para impressão e para
     slide em tela cheia. Acima disso o html2canvas começa a estourar memória em
     máquina modesta, e o ganho não aparece. */
  function capturar(folha, escala) {
    return html2canvas(folha, {
      scale: escala || 3,
      backgroundColor: '#ffffff',
      useCORS: true,
      allowTaint: false,
      logging: false,
      windowWidth: 1000,
      windowHeight: 1414,
    });
  }

  function comBarraEscondida(fn) {
    // a própria barra não pode aparecer no que for exportado
    document.body.classList.add('tv-exportando');
    return Promise.resolve()
      .then(fn)
      .then(function (r) { document.body.classList.remove('tv-exportando'); return r; },
            function (e) { document.body.classList.remove('tv-exportando'); throw e; });
  }

  function emSerie(itens, fn) {
    // uma folha por vez: capturar as quatro em paralelo multiplica o pico de
    // memória por quatro e trava a aba em máquina modesta
    return itens.reduce(function (fila, item, i) {
      return fila.then(function (acc) {
        return Promise.resolve(fn(item, i)).then(function (r) {
          acc.push(r);
          return acc;
        });
      });
    }, Promise.resolve([]));
  }

  // --------------------------------------------------------------- formatos
  function exportarImagem(tipo) {
    var ext = tipo === 'png' ? 'png' : 'jpg';
    var mime = tipo === 'png' ? 'image/png' : 'image/jpeg';
    return garantir('html2canvas').then(function () {
      return garantir('jszip');
    }).then(function () {
      aviso('Gerando ' + ext.toUpperCase() + '…');
      return comBarraEscondida(function () {
        return emSerie(folhas(), function (folha, i) {
          return capturar(folha).then(function (cv) {
            return new Promise(function (ok) {
              cv.toBlob(function (b) { ok({ i: i + 1, blob: b }); }, mime, 0.95);
            });
          });
        });
      });
    }).then(function (paginas) {
      if (paginas.length === 1) {
        baixar(paginas[0].blob, nomeArquivo('', ext));
        return;
      }
      var zip = new JSZip();
      paginas.forEach(function (p) {
        zip.file(nomeArquivo('p' + p.i, ext), p.blob);
      });
      return zip.generateAsync({ type: 'blob' }).then(function (b) {
        baixar(b, nomeArquivo(ext.toUpperCase(), 'zip'));
      });
    });
  }

  /* Camada de texto do PDF baixado.

     O PDF do botão é a foto da folha (html2canvas), e foto não tem texto: não
     dá para selecionar, copiar nem buscar. Por cima da foto vai cada palavra
     da folha, invisível, na posição e na largura exatas em que aparece — o
     mesmo truque de um PDF escaneado com OCR. O visual não muda; a seleção, a
     cópia e o Ctrl+F passam a funcionar.

     Medido com a folha em zoom 1 (durante a exportação), em mm de A4. Rótulos
     girados dos gráficos ficam de fora: a caixa deles é horizontal e a
     seleção sairia torta. */
  function camadaTexto(folha) {
    var base = folha.getBoundingClientRect();
    var k = 210 / base.width;
    var out = [];
    var andar = document.createTreeWalker(folha, NodeFilter.SHOW_TEXT, null);
    var faixa = document.createRange();
    var palavra = /\S+/g;
    var no, m, r;
    while ((no = andar.nextNode())) {
      var txt = no.nodeValue;
      if (!txt || !txt.trim() || !no.parentElement) { continue; }
      if (no.parentElement.closest('[transform*="rotate"], script, style')) { continue; }
      palavra.lastIndex = 0;
      while ((m = palavra.exec(txt))) {
        faixa.setStart(no, m.index);
        faixa.setEnd(no, m.index + m[0].length);
        r = faixa.getBoundingClientRect();
        if (r.width < 0.5 || r.height < 0.5) { continue; }
        if (r.bottom < base.top || r.top > base.bottom ||
            r.right < base.left || r.left > base.right) { continue; }
        out.push({ t: m[0], x: (r.left - base.left) * k, y: (r.top - base.top) * k,
                   w: r.width * k, h: r.height * k });
      }
    }
    return out;
  }

  function escreverCamada(pdf, palavras) {
    pdf.setFont('helvetica', 'normal');
    palavras.forEach(function (p) {
      // a caixa da linha inclui o entrelinha; o corpo é ~78% dela
      var corpo = p.h * 0.78;
      pdf.setFontSize(corpo * 72 / 25.4);
      var natural = pdf.getTextWidth(p.t.replace(/[−‒–—]/g, '-')) || p.w;
      var opc = { renderingMode: 'invisible', baseline: 'alphabetic',
                  horizontalScale: p.w / natural };
      // o sinal de menos tipográfico não existe na fonte padrão do PDF; o
      // espaço no fim separa palavras que vêm de elementos diferentes na cópia
      var t = p.t.replace(/[−‒–—]/g, '-') + ' ';
      try {
        pdf.text(t, p.x, p.y + p.h * 0.8, opc);
      } catch (e) {
        // caractere fora da fonte padrão do PDF: a palavra fica só na imagem
      }
    });
  }

  function exportarPDF() {
    return garantir('html2canvas').then(function () {
      return garantir('jspdf');
    }).then(function () {
      aviso('Gerando PDF…');
      return comBarraEscondida(function () {
        return emSerie(folhas(), function (folha) {
          return capturar(folha).then(function (cv) {
            return { cv: cv, texto: camadaTexto(folha) };
          });
        });
      });
    }).then(function (paginas) {
      var jsPDF = window.jspdf.jsPDF;
      var pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4',
                            compress: true });
      paginas.forEach(function (pg, i) {
        if (i) { pdf.addPage(); }
        pdf.addImage(pg.cv.toDataURL('image/jpeg', 0.95), 'JPEG', 0, 0, 210, 297);
        escreverCamada(pdf, pg.texto);
      });
      pdf.save(nomeArquivo('', 'pdf'));
    });
  }

  function exportarPPTX() {
    return garantir('html2canvas').then(function () {
      return garantir('pptxgen');
    }).then(function () {
      aviso('Gerando PPTX…');
      return comBarraEscondida(function () {
        return emSerie(folhas(), function (folha) { return capturar(folha); });
      });
    }).then(function (canvases) {
      var pptx = new PptxGenJS();
      // A4 retrato, igual à folha — o slide não reescala no PowerPoint
      pptx.defineLayout({ name: 'A4', width: 8.27, height: 11.69 });
      pptx.layout = 'A4';
      canvases.forEach(function (cv) {
        var s = pptx.addSlide();
        s.addImage({ data: cv.toDataURL('image/jpeg', 0.95),
                     x: 0, y: 0, w: 8.27, h: 11.69 });
      });
      return pptx.write({ outputType: 'blob' }).then(function (b) {
        baixar(b, nomeArquivo('', 'pptx'));
      });
    });
  }

  function imprimir() {
    // o navegador imprime o documento inteiro; sem isto, o PDF do fundo
    // ativo sairia seguido das folhas de todos os outros
    var estilo = document.getElementById('tv-print-escopo');
    if (!estilo) {
      estilo = document.createElement('style');
      estilo.id = 'tv-print-escopo';
      estilo.textContent = '@media print{.deck:not(.ativo){display:none!important}}';
      document.head.appendChild(estilo);
    }
    // O caminho vetorial: o @page do template já define A4 sem margem, então a
    // impressão do navegador sai idêntica ao PDF do run.py, com texto
    // selecionável. É melhor que o PDF por imagem — por isso vem primeiro.
    window.print();
  }

  function editar(botao) {
    var ligado = document.body.classList.toggle('tv-editando');
    folhas().forEach(function (f) {
      f.querySelectorAll('p, h2, h3, td, th, .fv, .fk, .bk, .bv, .rk, .rv')
        .forEach(function (e) { e.contentEditable = ligado ? 'true' : 'false'; });
    });
    // na casca o botão tem ícone + <span>; trocar o textContent inteiro
    // apagaria o ícone, então só o rótulo muda
    var rotulo = botao.querySelector('span') || botao;
    rotulo.textContent = ligado ? 'Terminar edição' : 'Editar textos';
    botao.setAttribute('aria-pressed', String(ligado));
    botao.classList.toggle('ativo', ligado);
    if (botao.classList.contains('btn')) {
      botao.classList.toggle('btn-primary', ligado);
      botao.classList.toggle('btn-glass', !ligado);
    }
    aviso(ligado ? 'Edição ligada — clique no texto para alterar'
                 : 'Edição desligada');
  }

  // ----------------------------------------------------------------- barra
  var BOTOES = [
    ['PDF (vetor)', imprimir, 'principal'],
    ['PDF (baixar)', exportarPDF],
    ['JPG', function () { return exportarImagem('jpg'); }],
    ['PNG', function () { return exportarImagem('png'); }],
    ['PPTX', exportarPPTX],
  ];

  /* ------------------------------------------------------------- abas */
  function ligarAbas(titulo) {
    var abas = [].slice.call(document.querySelectorAll('.ftab[data-deck]'));
    if (!abas.length) { return; }
    abas.forEach(function (aba) {
      aba.addEventListener('click', function () {
        var alvo = aba.getAttribute('data-deck');
        abas.forEach(function (o) {
          o.setAttribute('aria-selected', String(o === aba));
        });
        [].slice.call(document.querySelectorAll('.deck')).forEach(function (d) {
          d.classList.toggle('ativo', d.getAttribute('data-deck') === alvo);
        });
        var d = document.querySelector('.deck.ativo');
        if (titulo && d) { titulo.textContent = d.getAttribute('data-nome') || ''; }
        // o ECharts não desenha em elemento com display:none — o gráfico do
        // fundo que estava escondido sai com 0x0 até alguém redimensionar
        if (typeof echarts !== 'undefined' && d) {
          [].slice.call(d.querySelectorAll('.tv-chart')).forEach(function (el) {
            var g = echarts.getInstanceByDom(el);
            if (g) { g.resize(); }
          });
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    });
  }

  /* ------------------------------------------------------------- ícones
     Os mesmos traços do gerador oficial — é o que faz o botão parecer da casa
     e não um <button> cru. */
  var ICONE = {
    baixar: '<path d="M12 3v12M7 12l5 5 5-5M5 21h14"/>',
    arquivo: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>'
           + '<path d="M14 3v5h5"/>',
    lapis: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
  };

  function svg(d) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
         + 'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
         + d + '</svg>';
  }

  /* ------------------------------------------------------------- tema
     Claro/escuro, guardado no navegador de quem usa. Só liga se a página
     tiver os botões — o relatório solto não tem. */
  function ligarTema() {
    var botoes = [].slice.call(document.querySelectorAll('[data-theme-set]'));
    if (!botoes.length) { return; }
    var raiz = document.documentElement, CHAVE = 'tivio-relgestao-theme';
    function aplicar(t) {
      raiz.setAttribute('data-theme', t);
      botoes.forEach(function (b) {
        b.setAttribute('aria-pressed', String(b.dataset.themeSet === t));
      });
      try { localStorage.setItem(CHAVE, t); } catch (e) {}
    }
    var salvo = null;
    try { salvo = localStorage.getItem(CHAVE); } catch (e) {}
    aplicar(salvo || 'dark');
    botoes.forEach(function (b) {
      b.addEventListener('click', function () { aplicar(b.dataset.themeSet); });
    });
  }

  function ligarVoltarAoTopo() {
    var b = document.getElementById('backtop');
    if (!b) { return; }
    window.addEventListener('scroll', function () {
      b.classList.toggle('show', window.scrollY > 420);
    }, { passive: true });
    b.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  function aoClicar(el, fn) {
    el.addEventListener('click', function () {
      el.disabled = true;
      el.classList.add('is-loading');
      Promise.resolve()
        .then(fn)
        .catch(function (e) {
          aviso('Não consegui exportar: ' + (e && e.message ? e.message : e), true);
        })
        .then(function () { el.disabled = false; el.classList.remove('is-loading'); });
    });
  }

  /* ------------------------------------------------------------- montagem
     Dois destinos possíveis:

     - `#tv-acoes` existe → a página já tem a casca do gerador oficial
       (cabeçalho, hero, abas, rodapé). Os botões entram nela com as classes
       da casa e nada mais é criado.
     - não existe → é o relatório solto, que não tem casca nenhuma. Aí sim a
       barra escura é montada no topo.

     Era isso que faltava: a página por vertical nascia com a barra crua em
     cima de um layout que já tinha cabeçalho desenhado. */
  function montarNaCasca(destino) {
    BOTOES.forEach(function (b) {
      var el = document.createElement('button');
      el.type = 'button';
      el.className = 'btn btn-sm ' + (b[2] === 'principal' ? 'btn-primary' : 'btn-glass');
      el.innerHTML = svg(b[0].indexOf('PDF') === 0 ? ICONE.arquivo : ICONE.baixar)
                   + '<span>' + b[0] + '</span>';
      el.title = 'Exporta só o fundo que está na tela';
      aoClicar(el, b[1]);
      destino.appendChild(el);
    });
    var ed = document.createElement('button');
    ed.type = 'button';
    ed.className = 'btn btn-glass btn-sm';
    ed.setAttribute('aria-pressed', 'false');
    ed.innerHTML = svg(ICONE.lapis) + '<span>Editar textos</span>';
    ed.addEventListener('click', function () { editar(ed); });
    destino.appendChild(ed);
  }

  function montarBarra() {
    var barra = document.createElement('div');
    barra.className = 'tv-bar';
    var titulo = document.createElement('span');
    titulo.className = 'tv-bar-tit';
    var ativo = document.querySelector('.deck.ativo');
    titulo.textContent = (ativo && ativo.getAttribute('data-nome')) ||
                         META.fundo || 'Relatório de Gestão';
    barra.appendChild(titulo);

    BOTOES.forEach(function (b) {
      var el = document.createElement('button');
      el.type = 'button';
      el.className = 'tv-btn' + (b[2] ? ' ' + b[2] : '');
      el.textContent = b[0];
      aoClicar(el, b[1]);
      barra.appendChild(el);
    });
    var ed = document.createElement('button');
    ed.type = 'button';
    ed.className = 'tv-btn fantasma';
    ed.textContent = 'Editar textos';
    ed.addEventListener('click', function () { editar(ed); });
    barra.appendChild(ed);

    document.body.insertBefore(barra, document.body.firstChild);
    return titulo;
  }

  function montar() {
    if (!document.querySelectorAll('.rcard').length) { return; }
    var casca = document.getElementById('tv-acoes');
    var titulo = null;
    if (casca) {
      montarNaCasca(casca);
      ligarTema();
      ligarVoltarAoTopo();
    } else {
      titulo = montarBarra();
    }
    ligarAbas(titulo);
    ligarEnquadramento();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', montar);
  } else {
    montar();
  }
})();
