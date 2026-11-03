/* Apresentação do Plano: resumida, montada na hora a partir da página (com as edições do time). */
(function () {
  function t(e) { if (!e) return ""; var c = e.cloneNode(true); [].forEach.call(c.querySelectorAll(".ed-x,.ed-g,.ed-add,.ed-xb,svg,img"), function (x) { x.remove() }); return c.textContent.replace(/\s+/g, " ").trim() }
  function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML }
  function vis(e) { return e && !e.hidden && !e.closest(".painel-pl [hidden]") }
  function itens(ul, max) { var l = ul ? [].filter.call(ul.querySelectorAll(":scope>li"), function (li) { return !li.hidden && t(li) }) : []; return l.slice(0, max || 99).map(function (li) { return "<li>" + esc(t(li)) + "</li>" }).join("") }
  function blocos(raiz) { return raiz ? [].filter.call(raiz.querySelectorAll("section.frente"), vis) : [] }
  function card(f, max) { return "<div><b>" + esc(t(f.querySelector("h3"))) + "</b>" + (t(f.querySelector(".dono")) ? "<span>" + esc(t(f.querySelector(".dono"))) + "</span>" : "") + "<ul>" + itens(f.querySelector("ul"), max) + "</ul></div>" }
  function num(s) { var m = String(s).replace(/\./g, "").replace(",", ".").match(/-?\d+(\.\d+)?/); return m ? parseFloat(m[0]) : null }
  window.tvDeck("Plano 2027", function () {
    var F = document.getElementById("fim-do-ano"), N = document.getElementById("ano-2027"), S = [];
    var sec = function (id) { var h = N && N.querySelector("#" + id); var n = h && h.nextElementSibling; return n && n.classList.contains("frentes") ? n : null };
    S.push({ capa: true, h: "Plano <strong>2027</strong>", html: '<p class="sl-l">O que vamos fazer até o fim do ano e ao longo de 2027</p>' });
    S.push({ sec: "Sumário", h: "O que vamos <strong>ver</strong>", sum: true });
    var pes = function (raiz) { return raiz ? [].filter.call(raiz.querySelectorAll(".org-n"), vis).map(function (x) { return "<p><b>" + esc(t(x.querySelector("b"))) + "</b><span>" + esc(t(x.querySelector("em")) || t(x.querySelector("span"))) + "</span></p>" }).join("") : "" };
    S.push({ sec: "Estrutura", h: "Quem <strong>faz</strong>", html: '<div class="sl-dupla"><div><b>Até o fim do ano</b>' + pes(F && F.querySelector(".org")) + '</div><div><b>Em 2027</b>' + pes(N && N.querySelector(".org")) + "</div></div>" });
    var cu = N && N.querySelector(".cu");
    if (cu) { var ks = [].slice.call(N.querySelectorAll("#custo ~ .kpis .kpi")).slice(0, 4);
      S.push({ sec: "Estrutura", h: "O custo da agência, <strong>diluído</strong>", html: '<div class="sl-cu"><div class="sl-g c4 cmp num">' + ks.map(function (k) { return "<div><b>" + esc(t(k.querySelector("b"))) + "</b><span>" + esc(t(k.querySelector("span"))) + "</span></div>" }).join("") + '</div><div class="cu-bar">' + [].map.call(cu.querySelectorAll(".cu-bar i"), function (i) { return '<i class="' + i.className + '" style="' + i.getAttribute("style") + '"></i>' }).join("") + '</div><div class="cu-l">' + [].map.call(cu.querySelectorAll(".cu-i"), function (x) { return '<div class="cu-i"><i class="' + x.querySelector("i").className + '"></i><span>' + esc(t(x.querySelector("span"))) + "</span><b>" + esc(t(x.querySelector("b"))) + "</b></div>" }).join("") + "</div></div>" }); }
    var te = N ? blocos(N.querySelector(".teses")) : [];
    if (te.length) S.push({ sec: "Por que", h: "Por que <strong>assim</strong>", html: '<div class="sl-g c3 cmp tes">' + te.map(function (f) { return "<div><b>" + esc(t(f.querySelector("h3"))) + "</b><span>" + esc(t(f.querySelector(".dono"))) + "</span><ul>" + itens(f.querySelector("ul"), 3) + "</ul></div>" }).join("") + "</div>" });
    var fe = blocos(F && F.querySelector(".frentes"));
    if (fe.length) S.push({ sec: "Até o fim do ano", h: "O que <strong>fechar</strong>", html: '<div class="sl-g c3 cmp">' + fe.map(function (f) { return card(f, 5) }).join("") + "</div>" });
    var fr = N ? blocos(N.querySelector(".fr-vis")) : [];
    if (fr.length) S.push({ sec: "2027", h: "O ano em <strong>quatro frentes</strong>", html: '<div class="sl-g c4 cmp">' + fr.map(function (f) { var im = f.querySelector(".fr-img"); return "<div>" + (im ? '<img class="th" src="' + im.getAttribute("src") + '" alt="">' : "") + "<b>" + esc(t(f.querySelector("h3")).replace(" com estratégia", "")) + "</b><span>" + esc(t(f.querySelector(".fr-m"))) + "</span><span><em>" + esc(t(f.querySelector(".dono"))) + "</em></span></div>" }).join("") + "</div>" });
    // gráfico: posts por mês de cada segmento
    var sg = N ? [].filter.call(N.querySelectorAll(".seg6>.sub"), vis) : [];
    if (sg.length) {
      var ps = sg.map(function (x) { var m = t(x.querySelector("em")).match(/(\d+) posts/); return m ? +m[1] : 0 }), mx = Math.max.apply(null, ps.concat([1]));
      S.push({ sec: "2027", h: "Cada segmento em <strong>uma linha</strong>", html: '<div class="sl-g c3 cmp seg">' + sg.map(function (x, k) {
        return "<div><b>" + esc(t(x.querySelector("b"))) + "</b><span>" + esc(t(x.querySelector("span"))) + '</span><div class="gb"><i style="--w:' + Math.round(ps[k] / mx * 100) + '%"></i><em>' + (ps[k] ? ps[k] + " posts por mês" : esc(t(x.querySelector("em")))) + "</em></div></div>";
      }).join("") + "</div>" });
    }
    var ri = blocos(sec("ritmo")); if (ri.length) S.push({ sec: "2027", h: "O que <strong>se repete</strong>", html: '<div class="sl-g c3 cmp">' + ri.map(function (f) { return card(f) }).join("") + "</div>" });
    var tr = blocos(sec("trimestres")); if (tr.length) S.push({ sec: "2027", h: "O ano por <strong>trimestre</strong>", html: '<div class="sl-g c4 cmp">' + tr.map(function (f) { return card(f, 5) }).join("") + "</div>" });
    // gráfico: eventos Itaú mês a mês, lidos da linha do tempo
    var ms = N ? [].slice.call(N.querySelectorAll("#meses .tl-m")).filter(function (m) { return !/nov e dez/i.test(t(m.querySelector("h3"))) }) : [];
    var ev = ms.map(function (m) { var e = m.querySelector('.tl-i[data-c="2"] span'), q = e && t(e).match(/^(\d+) eventos?/); return [t(m.querySelector("h3")).slice(0, 3), q ? +q[1] : 0] });
    var tot = ev.reduce(function (s, x) { return s + x[1] }, 0);
    if (tot) S.push({ sec: "2027 · Eventos", h: tot + " eventos Itaú <strong>no ano</strong>", html: '<div class="gc" role="img" aria-label="Eventos Itaú por mês">' + ev.map(function (x) { return '<div><b>' + (x[1] || "") + '</b><i style="height:' + Math.round(x[1] / 2 * 330) + 'px"></i><span>' + esc(x[0]) + "</span></div>" }).join("") + '</div><p class="sl-nota">No escritório da Tivio, quatro por trimestre, além de Summit BTG, Expert XP e Congresso Abrapp.</p>' });
    // gráfico: caminho do número e metas das redes (hoje até a meta)
    var fu = N ? [].slice.call(N.querySelectorAll(".fu-i")) : [], mt = N ? [].slice.call(N.querySelectorAll(".mt-r")) : [];
    if (fu.length || mt.length) S.push({ sec: "2027", h: "Como vamos <strong>medir</strong>", html: '<div class="sl-med"><div class="fun">' + fu.map(function (x, k) { return '<div style="--w:' + (100 - k * 14) + '%"><b>' + esc(t(x.querySelector("b"))) + "</b><span>" + esc(t(x.querySelector("span"))) + "</span></div>" }).join("") + '</div><div class="met"><b class="met-t">Metas das redes até dez/27</b>' + mt.slice(0, 5).map(function (x) {
      var e = t(x.querySelector("em")).split(" a "), h0 = num(e[0]), m1 = num(e[1]); var pc = h0 !== null && m1 ? Math.min(100, Math.round(h0 / m1 * 100)) : 0;
      return '<div><span>' + esc(t(x.querySelector("span"))) + '</span><i style="--w:' + pc + '%"></i><em>' + esc(e[0]) + " → <strong>" + esc(e[1] || "") + "</strong></em></div>";
    }).join("") + "</div></div>" });
    S.push({ capa: true, h: "Casa de <strong>estruturados</strong>", html: '<p class="sl-l">Menos, com mais qualidade.</p>' });
    return S;
  });
})();
