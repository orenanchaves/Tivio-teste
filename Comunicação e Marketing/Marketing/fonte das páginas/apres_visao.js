/* Apresentação da Visão: montada na hora a partir da própria página (com as edições do time). */
(function () {
  function t(e) { if (!e) return ""; var c = e.cloneNode(true); [].forEach.call(c.querySelectorAll(".ed-x,.ed-g,.ed-add,.ed-xb,svg"), function (x) { x.remove() }); return c.textContent.replace(/\s+/g, " ").trim() }
  function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML }
  function ok(e) { return e && !e.hidden && t(e) }
  function sec(txt) { var h = [].filter.call(document.querySelectorAll(".wrap h2"), function (x) { return !x.closest("#apres") && t(x).indexOf(txt) >= 0 })[0]; if (!h) return null; var l = [], n = h.nextElementSibling; while (n && n.tagName !== "H2" && !n.matches("section,.meta-txt")) { l.push(n); n = n.nextElementSibling } return l }
  function q(l, s) { var r = []; (l || []).forEach(function (e) { r = r.concat([].slice.call(e.matches(s) ? [e] : e.querySelectorAll(s))) }); return r.filter(ok) }
  function card(b, s) { return "<div><b>" + esc(b) + "</b>" + (s ? "<span>" + esc(s) + "</span>" : "") + "</div>" }
  function grade(S, h, cards, c) { if (cards.length) S.push({ sec: "Visão", h: h, html: '<div class="sl-g c' + (c || Math.min(5, cards.length)) + ' cmp">' + cards.join("") + "</div>" }) }
  window.tvDeck("Visão", function () {
    var S = [], d = document.querySelector(".wrap .destaque"), slog = d && d.querySelector(".slogan"), g = d && d.querySelector(".grande");
    S.push({ capa: true, h: "Visão", html: '<p class="sl-l">O que queremos para a Tivio Capital</p>' + (slog ? '<p class="sl-s"><span>Sugestão de slogan</span>' + esc(t(slog).replace(/^Sugestão de slogan\s*/, "")) + "</p>" : "") });
    S.push({ sec: "Sumário", h: "O que vamos <strong>ver</strong>", sum: true });
    if (g) S.push({ sec: "Visão", h: "O que <strong>queremos</strong>", html: '<div class="sl-frase"><p>' + g.innerHTML + '</p><div class="sl-im"><figure><img src="feed/02.webp" alt="Capa da Carta do Gestor"><figcaption>Carta do Gestor</figcaption></figure><figure><img src="feed/06.webp" alt="Deep Dive sobre micropensões"><figcaption>Deep Dive</figcaption></figure></div></div>' });
    grade(S, "O que <strong>concluímos</strong>", q(sec("concluímos"), "ol>li").map(function (li) { return card(t(li.querySelector("b")), t(li.querySelector("span"))) }), 5);
    var tr = q(sec("De onde saímos"), "tr").filter(function (r) { return r.querySelector("td") });
    if (tr.length) S.push({ sec: "Visão", h: "De onde saímos, para <strong>onde vamos</strong>", html: '<div class="sl-t duas">' + tr.map(function (r) { var c = r.querySelectorAll("td"); return "<p><span>" + esc(t(c[0])) + "</span><b>" + esc(t(c[1])) + "</b></p>" }).join("") + "</div>" });
    grade(S, "O que queremos que <strong>digam da Tivio</strong>", q(sec("digam da Tivio"), ".sub").map(function (a) { return card(t(a.querySelector("b")), t(a.querySelector("span"))) }), 3);
    grade(S, "Como <strong>chegamos lá</strong>", q(sec("chegamos lá"), ".sub").map(function (a) { return card(t(a.querySelector("b")), t(a.querySelector("span"))) }), 3);
    grade(S, "Como vamos <strong>saber</strong>", q(sec("vamos saber"), "li").map(function (li) { return card(t(li)) }), 3);
    [["2025: o", "2025"], ["2026: o", "2026"]].forEach(function (a) {
      var l = sec(a[0]); if (!l) return;
      var k = q(l, ".kpi").map(function (x) { return card(t(x.querySelector("b")), t(x.querySelector("span"))) });
      var m = q(l, "tr").filter(function (r) { return r.querySelector("td") }).map(function (r) { var c = r.querySelectorAll("td"); return "<p><span>" + esc(t(c[0])) + "</span><b>" + esc(t(c[1])) + "</b></p>" });
      S.push({ sec: "Os anos da Tivio", h: "<strong>" + a[1] + "</strong> em números e marcos", html: '<div class="sl-ano"><div class="sl-g c2 cmp num">' + k.join("") + '</div><div class="sl-t mini">' + m.join("") + "</div></div>" });
    });
    var mp = q(sec("uma página"), ".analise>div"); if (mp.length) S.push({ sec: "Os anos da Tivio", h: "O mercado em <strong>uma página</strong>", html: '<div class="sl-g c2 cmp">' + mp.map(function (x) { return "<div><b>" + esc(t(x.querySelector("h3"))) + "</b><ul>" + [].filter.call(x.querySelectorAll("li"), ok).map(function (li) { return "<li>" + esc(t(li)) + "</li>" }).join("") + "</ul></div>" }).join("") + "</div>" });
    S.push({ capa: true, h: "Casa de <strong>estruturados</strong>", html: '<p class="sl-l">Menos, com mais qualidade.</p>' });
    return S;
  });
})();
