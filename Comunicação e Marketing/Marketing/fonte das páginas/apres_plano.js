/* Apresentação do Plano: monta os slides na hora, a partir da própria página (com as edições do time). */
(function () {
  var A = document.getElementById("apres"), BT = document.getElementById("ap-abrir"); if (!A || !BT) return;
  var IMG = {
    "Imprensa": [["feed/07.webp", "Na mídia", 0.8]],
    "Conteúdo|fim": [["feed/11.webp", "Carta do Gestor", 0.8], ["feed/12.webp", "Alpha DI", 0.562], ["feed/03.webp", "Global Rates", 0.798]],
    "Prêmios de melhores": [["site-tivio/desktop.webp", "Site da Tivio", 1.6]],
    "Automação": [["pecas/ce1.webp", "Crédito Estruturado", 0.75], ["pecas/cp2.webp", "Crédito Privado", 0.75], ["pecas/is1.webp", "Investment Solutions", 0.75]],
    "Eventos": [["feed/08.webp", "TheNewAgro", 0.5625]],
    "Conteúdo": [["feed/02.webp", "Carta do Gestor", 0.8], ["feed/04.webp", "Base do Raio X", 0.5625], ["feed/06.webp", "Deep Dive", 0.87]],
    "Digital com estratégia": [["site-tivio/desktop.webp", "Site hoje", 1.6], ["site-tivio/celular.webp", "No celular", 0.462]]
  };
  function t(e) { if (!e) return ""; var c = e.cloneNode(true); [].forEach.call(c.querySelectorAll(".ed-x,.ed-g,.ed-add,svg"), function (x) { x.remove() }); return c.textContent.replace(/\s+/g, " ").trim() }
  function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML }
  function vis(e) { return !e.hidden && !e.closest("[hidden]:not(.painel-pl)") }
  function itens(ul) { return ul ? [].filter.call(ul.querySelectorAll(":scope>li"), function (li) { return !li.hidden && t(li) }).map(function (li) { return "<li>" + esc(t(li)) + "</li>" }).join("") : "" }
  function capa(e, h, l) { return '<section class="sl capa"><h2>' + h + '</h2><p class="sl-l">' + esc(l) + "</p></section>" }
  function figs(l) { var r = l.reduce(function (s, x) { return s + x[2] }, 0); return '<div style="--r:' + r + '" class="sl-im">' + l.map(function (x) { return '<figure style="flex:' + x[2] + '"><img src="' + x[0] + '" alt="' + esc(x[1]) + '"><figcaption>' + esc(x[1]) + "</figcaption></figure>" }).join("") + "</div>" }
  function bloco(tit, sub, lis, imgs) {
    var card = '<div class="sl-g c1"><div><b>' + esc(tit) + "</b>" + (sub ? "<span>" + esc(sub) + "</span>" : "") + (lis ? "<ul>" + lis + "</ul>" : "") + "</div></div>";
    return '<section class="sl">' + (imgs ? '<div class="sl-2">' + card + figs(imgs) + "</div>" : '<div class="sl-1">' + card + "</div>") + "</section>";
  }
  function org(raiz, tit) {
    var n = raiz && [].filter.call(raiz.querySelectorAll(".org-n"), vis); if (!n || !n.length) return "";
    var c = n.length <= 5 ? "c" + n.length : "c4";
    return '<section class="sl"><h2 class="fr">' + tit + '</h2><div class="sl-g ' + c + '">' + n.map(function (x) { return "<div><b>" + esc(t(x.querySelector("b"))) + "</b><span>" + esc([t(x.querySelector("span")), t(x.querySelector("em"))].filter(Boolean).join(" · ")) + "</span></div>" }).join("") + "</div></section>";
  }
  function monta() {
    var F = document.getElementById("fim-do-ano"), N = document.getElementById("ano-2027"), s = "";
    s += capa(null, "Plano", "O que vamos fazer até o fim do ano e ao longo de 2027");
    s += capa(null, "Até o fim <strong>do ano</strong>", "O que fechar em novembro e dezembro para começar 2027 pronto");
    s += org(F && F.querySelector(".org"), "Estrutura até o fim <strong>do ano</strong>");
    if (F) [].forEach.call(F.querySelectorAll(".frentes section.frente"), function (f) { if (!vis(f)) return; var h = t(f.querySelector("h3")); s += bloco(h, t(f.querySelector(".dono")), itens(f.querySelector("ul")), IMG[h + "|fim"] || IMG[h]) });
    s += capa(null, "<strong>2027</strong>", "Casa de estruturados, em quatro frentes");
    s += org(N && N.querySelector(".org"), "Estrutura em <strong>2027</strong>");
    if (N) [].forEach.call(N.querySelectorAll("#frentes ~ .frentes section.frente, .frentes.f4 section.frente"), function (f) { var h = t(f.querySelector("h3")); s += bloco(h.replace(" com estratégia", ""), t(f.querySelector(".dono")), itens(f.querySelector("ul")), IMG[h]) });
    var lig = N ? [].filter.call(N.querySelectorAll(".lig-i"), vis) : [];
    if (lig.length) s += '<section class="sl"><h2 class="fr">Estratégias que se <strong>entrelaçam</strong></h2><div class="sl-g c3">' + lig.map(function (x) { return "<div><b>" + esc(t(x.querySelector(":scope>b"))) + "</b><span>" + esc(t(x.querySelector(":scope>span"))) + " · " + esc(t(x.querySelector("em"))) + "</span></div>" }).join("") + "</div></section>";
    var tri = [["Antes de começar", /nov e dez/i], ["1º trimestre", /janeiro|fevereiro|março/i], ["2º trimestre", /abril|maio|junho/i], ["3º trimestre", /julho|agosto|setembro/i], ["4º trimestre", /outubro|novembro|dezembro/i]];
    var meses = N ? [].slice.call(N.querySelectorAll("#meses .tl-m")) : [];
    tri.forEach(function (q) {
      var por = {};
      meses.filter(function (m) { return q[1].test(t(m.querySelector("h3"))) && !(q[0] !== "Antes de começar" && /nov e dez/i.test(t(m.querySelector("h3")))) }).forEach(function (m) {
        [].forEach.call(m.querySelectorAll(".tl-i"), function (i) { var f = t(i.querySelector("b")); (por[f] = por[f] || []).push("<li><em>" + esc(t(m.querySelector("h3"))) + ":</em> " + esc(t(i.querySelector("span"))) + "</li>") });
      });
      var ORD = ["Automação", "Eventos", "Conteúdo", "Digital"], ks = Object.keys(por).sort(function (x, y) { return (ORD.indexOf(x) + 9) % 9 - (ORD.indexOf(y) + 9) % 9 }); if (!ks.length) return;
      s += '<section class="sl"><h2 class="fr">' + esc(q[0]) + '</h2><div class="sl-g c' + Math.min(4, ks.length) + ' mes">' + ks.map(function (k) { return "<div><b>" + esc(k) + "</b><ul>" + por[k].join("") + "</ul></div>" }).join("") + "</div></section>";
    });
    var fu = N ? [].slice.call(N.querySelectorAll(".fu-i")) : [];
    if (fu.length) s += '<section class="sl"><h2 class="fr">O caminho do <strong>número</strong></h2><div class="sl-g c4">' + fu.map(function (x) { return "<div><b>" + esc(t(x.querySelector("b"))) + "</b><span>" + esc(t(x.querySelector("span"))) + "</span></div>" }).join("") + "</div></section>";
    s += '<section class="sl"><h2 class="fr">Onde ver <strong>tudo</strong></h2><div class="sl-g c4"><a href="estrutura.html"><b>Estrutura</b><span>Quem faz o quê</span></a><a href="imprensa.html"><b>Imprensa</b><span>Pauta, porta-vozes e filtro</span></a><a href="frente-benchmark.html"><b>Benchmark</b><span>O que vimos fora e o que fazemos</span></a><a href="visao.html"><b>Visão</b><span>O que queremos para a Tivio</span></a></div></section>';
    s += capa(null, "Casa de <strong>estruturados</strong>", "Menos, com mais qualidade.");
    [].forEach.call(A.querySelectorAll(".sl"), function (x) { x.remove() });
    A.querySelector(".ap-ctl").insertAdjacentHTML("beforebegin", s);
    return [].slice.call(A.querySelectorAll(".sl"));
  }
  var l = [], i = 0, n = document.getElementById("ap-n"); A.querySelector(".ap-logo").innerHTML = document.querySelector(".marca").innerHTML;
  function v(k) { i = Math.max(0, Math.min(l.length - 1, k)); l.forEach(function (s, j) { s.classList.toggle("ativa", j === i) }); n.textContent = (i + 1) + " / " + l.length }
  function abrir() { l = monta(); A.hidden = false; document.body.style.overflow = "hidden"; v(0); if (A.requestFullscreen) A.requestFullscreen().catch(function () {}) }
  function sair() { A.hidden = true; document.body.style.overflow = ""; if (document.fullscreenElement) document.exitFullscreen() }
  BT.onclick = abrir; document.getElementById("ap-sair").onclick = sair;
  document.getElementById("ap-ant").onclick = function () { v(i - 1) }; document.getElementById("ap-prox").onclick = function () { v(i + 1) };
  document.addEventListener("keydown", function (e) { if (A.hidden || !A.isConnected) return; if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") { e.preventDefault(); v(i + 1) } if (e.key === "ArrowLeft" || e.key === "PageUp") v(i - 1); if (e.key === "Escape") sair() });
  document.addEventListener("fullscreenchange", function () { if (!A.isConnected) return; if (!document.fullscreenElement && !A.hidden && A.dataset.fs) sair(); A.dataset.fs = document.fullscreenElement ? "1" : "" });
})();
