/* Apresentação da Visão: monta os slides na hora, a partir da própria página (com as edições do time). */
(function () {
  var A = document.getElementById("apres"), BT = document.getElementById("ap-abrir"); if (!A || !BT) return;
  function t(e) { if (!e) return ""; var c = e.cloneNode(true); [].forEach.call(c.querySelectorAll(".ed-x,.ed-g,.ed-add,svg"), function (x) { x.remove() }); return c.textContent.replace(/\s+/g, " ").trim() }
  function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML }
  function ok(e) { return e && !e.hidden && t(e) }
  function sec(txt) { var h = [].filter.call(document.querySelectorAll(".wrap h2"), function (x) { return !x.closest("#apres") && t(x).indexOf(txt) >= 0 })[0]; if (!h) return null; var l = [], n = h.nextElementSibling; while (n && n.tagName !== "H2" && !n.matches("section,.meta-txt")) { l.push(n); n = n.nextElementSibling } return l }
  function q(l, s) { var r = []; (l || []).forEach(function (e) { r = r.concat([].slice.call(e.matches(s) ? [e] : e.querySelectorAll(s))) }); return r.filter(ok) }
  function figs(l) { var r = l.reduce(function (s, x) { return s + x[2] }, 0); return '<div style="--r:' + r + '" class="sl-im">' + l.map(function (x) { return '<figure style="flex:' + x[2] + '"><img src="' + x[0] + '" alt="' + esc(x[1]) + '"><figcaption>' + esc(x[1]) + "</figcaption></figure>" }).join("") + "</div>" }
  function grade(tit, cards, c) { return cards.length ? '<section class="sl"><h2 class="fr">' + tit + '</h2><div class="sl-g c' + (c || Math.min(5, cards.length)) + '">' + cards.join("") + "</div></section>" : "" }
  function card(b, s) { return "<div><b>" + esc(b) + "</b>" + (s ? "<span>" + esc(s) + "</span>" : "") + "</div>" }
  function monta() {
    var s = "", d = document.querySelector(".wrap .destaque"), slog = d && d.querySelector(".slogan");
    s += '<section class="sl capa"><h2>Visão</h2><p class="sl-l">O que queremos para a Tivio Capital</p>' + (slog ? '<p class="sl-s"><span>Sugestão de slogan</span>' + esc(t(slog).replace(/^Sugestão de slogan\s*/, "")) + "</p>" : "") + "</section>";
    var g = d && d.querySelector(".grande"); if (g) s += '<section class="sl"><div class="sl-2"><h2 class="fr">' + g.innerHTML + "</h2>" + figs([["feed/02.webp", "Carta do Gestor", 0.8], ["feed/06.webp", "Deep Dive", 0.87]]) + "</div></section>";
    s += grade("O que <strong>concluímos</strong>", q(sec("concluímos"), "ol>li").map(function (li) { return card(t(li.querySelector("b")), t(li.querySelector("span"))) }), 5);
    var tr = q(sec("De onde saímos"), "tr").filter(function (r) { return r.querySelector("td") });
    if (tr.length) s += '<section class="sl"><h2 class="fr">De onde saímos, para <strong>onde vamos</strong></h2><div class="sl-t">' + tr.map(function (r) { var c = r.querySelectorAll("td"); return "<p><span>" + esc(t(c[0])) + "</span><b>" + esc(t(c[1])) + "</b></p>" }).join("") + "</div></section>";
    s += grade("O que queremos que <strong>digam da Tivio</strong>", q(sec("digam da Tivio"), ".sub").map(function (a) { return card(t(a.querySelector("b")), t(a.querySelector("span"))) }), 3);
    var ch = q(sec("chegamos lá"), ".sub"); if (ch.length) s += '<section class="sl"><h2 class="fr">Como <strong>chegamos lá</strong></h2><div class="sl-g c' + Math.min(4, ch.length) + '">' + ch.map(function (a) { return '<a href="' + a.getAttribute("href") + '"><b>' + esc(t(a.querySelector("b"))) + "</b><span>" + esc(t(a.querySelector("span"))) + "</span></a>" }).join("") + "</div></section>";
    s += grade("Como vamos <strong>saber</strong>", q(sec("vamos saber"), "li").map(function (li) { return card(t(li)) }), 3);
    [["2025: o", "2025"], ["2026: o", "2026"]].forEach(function (a) {
      var l = sec(a[0]); if (!l) return;
      var k = q(l, ".kpi").map(function (x) { return card(t(x.querySelector("b")), t(x.querySelector("span"))) });
      var m = q(l, "tr").filter(function (r) { return r.querySelector("td") }).map(function (r) { var c = r.querySelectorAll("td"); return "<p><span>" + esc(t(c[0])) + "</span><b>" + esc(t(c[1])) + "</b></p>" });
      s += '<section class="sl"><h2 class="fr"><strong>' + a[1] + '</strong> em números</h2><div class="sl-g c4 num">' + k.join("") + "</div></section>";
      if (m.length) s += '<section class="sl"><h2 class="fr"><strong>' + a[1] + '</strong> mês a mês</h2><div class="sl-t mini">' + m.join("") + "</div></section>";
    });
    var mp = q(sec("uma página"), ".analise>div"); if (mp.length) s += '<section class="sl"><h2 class="fr">O mercado em <strong>uma página</strong></h2><div class="sl-g c2">' + mp.map(function (x) { return "<div><b>" + esc(t(x.querySelector("h3"))) + "</b><ul>" + [].filter.call(x.querySelectorAll("li"), ok).map(function (li) { return "<li>" + esc(t(li)) + "</li>" }).join("") + "</ul></div>" }).join("") + "</div></section>";
    s += '<section class="sl"><h2 class="fr">Onde ver <strong>o plano</strong></h2><div class="sl-g c2"><a href="plano-2027.html#fim-do-ano"><b>Até o fim do ano</b><span>O que fechar em novembro e dezembro</span></a><a href="plano-2027.html#ano-2027"><b>2027</b><span>Quatro frentes, os números e cada mês</span></a></div></section>';
    s += '<section class="sl capa"><h2>Casa de <strong>estruturados</strong></h2><p class="sl-l">Menos, com mais qualidade.</p></section>';
    [].forEach.call(A.querySelectorAll(".sl"), function (x) { x.remove() });
    A.querySelector(".ap-ctl").insertAdjacentHTML("beforebegin", s);
    var ls = [].slice.call(A.querySelectorAll(".sl")), tot = ls.length;
    ls.forEach(function (x, k) { x.insertAdjacentHTML("beforeend", '<div class="sl-rod"><span>Tivio Capital · Comunicação &amp; Marketing</span><span>Visão</span><i><u style="width:' + Math.round((k + 1) / tot * 100) + '%"></u></i><b>' + String(k + 1).padStart(2, "0") + " / " + String(tot).padStart(2, "0") + "</b></div>") });
    return ls;
  }
  var l = [], i = 0, n = document.getElementById("ap-n"); A.querySelector(".ap-logo").innerHTML = document.querySelector(".marca").innerHTML;
  function v(k) { i = Math.max(0, Math.min(l.length - 1, k)); l.forEach(function (s, j) { s.classList.toggle("ativa", j === i) }); n.textContent = (i + 1) + " / " + l.length }
  function abrir() { l = monta(); A.hidden = false; document.body.style.overflow = "hidden"; v(0); var R = document.documentElement; if (R.requestFullscreen) R.requestFullscreen().catch(function () {}) }
  function sair() { A.hidden = true; document.body.style.overflow = ""; if (document.fullscreenElement) document.exitFullscreen() }
  BT.onclick = abrir; document.getElementById("ap-sair").onclick = sair;
  document.getElementById("ap-ant").onclick = function () { v(i - 1) }; document.getElementById("ap-prox").onclick = function () { v(i + 1) };
  document.addEventListener("keydown", function (e) { if (A.hidden || !A.isConnected) return; if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") { e.preventDefault(); v(i + 1) } if (e.key === "ArrowLeft" || e.key === "PageUp") v(i - 1); if (e.key === "Escape") sair() });
  document.addEventListener("fullscreenchange", function () { if (!A.isConnected) return; if (!document.fullscreenElement && !A.hidden && A.dataset.fs) sair(); A.dataset.fs = document.fullscreenElement ? "1" : "" });
})();
