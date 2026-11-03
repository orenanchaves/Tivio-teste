/* Apresentação do Plano: resumida, montada na hora a partir da página (com as edições do time).
   Cada slide tem seção e página no topo; o Sumário leva direto a qualquer parte. */
(function () {
  var A = document.getElementById("apres"), BT = document.getElementById("ap-abrir"); if (!A || !BT) return;
  var IMG = {
    "Automação": [["pecas/ce1.webp", "Crédito Estruturado", 0.75], ["pecas/cp2.webp", "Crédito Privado", 0.75], ["pecas/is1.webp", "Investment Solutions", 0.75]],
    "Eventos": [["feed/08.webp", "TheNewAgro", 0.5625], ["feed/01.webp", "Onde encontrar os fundos", 0.8]],
    "Conteúdo": [["feed/02.webp", "Carta do Gestor", 0.8], ["feed/04.webp", "Base do Raio X", 0.5625], ["feed/06.webp", "Deep Dive", 0.87]],
    "Digital com estratégia": [["site-tivio/desktop.webp", "Site hoje", 1.6], ["site-tivio/celular.webp", "No celular", 0.462]]
  };
  function t(e) { if (!e) return ""; var c = e.cloneNode(true); [].forEach.call(c.querySelectorAll(".ed-x,.ed-g,.ed-add,.ed-xb,svg,img"), function (x) { x.remove() }); return c.textContent.replace(/\s+/g, " ").trim() }
  function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML }
  function vis(e) { return e && !e.hidden && !e.closest(".painel-pl [hidden]") }
  function itens(ul, max) { var l = ul ? [].filter.call(ul.querySelectorAll(":scope>li"), function (li) { return !li.hidden && t(li) }) : []; return l.slice(0, max || 99).map(function (li) { return "<li>" + esc(t(li)) + "</li>" }).join("") }
  function figs(l) { var r = l.reduce(function (s, x) { return s + x[2] }, 0); return '<div style="--r:' + r + '" class="sl-im">' + l.map(function (x) { return '<figure style="flex:' + x[2] + '"><img src="' + x[0] + '" alt="' + esc(x[1]) + '"><figcaption>' + esc(x[1]) + "</figcaption></figure>" }).join("") + "</div>" }
  function blocos(raiz) { return raiz ? [].filter.call(raiz.querySelectorAll("section.frente"), vis) : [] }
  var S = [];
  function sl(sec, tit, corpo, capa) { S.push({ sec: sec, tit: tit.replace(/<[^>]+>/g, ""), html: corpo, capa: capa, h: tit }) }
  function org(raiz, sec, tit) {
    var n = raiz ? [].filter.call(raiz.querySelectorAll(".org-n"), vis) : []; if (!n.length) return;
    sl(sec, tit, '<div class="sl-g ' + (n.length <= 5 ? "c" + n.length : "c4") + ' cmp">' + n.map(function (x) { return "<div><b>" + esc(t(x.querySelector("b"))) + "</b><span>" + esc([t(x.querySelector("span")), t(x.querySelector("em"))].filter(Boolean).join(" · ")) + "</span></div>" }).join("") + "</div>");
  }
  function grade(sec, tit, bl, c) { if (bl.length) sl(sec, tit, '<div class="sl-g c' + (c || Math.min(4, bl.length)) + ' cmp">' + bl.map(function (f) { return "<div><b>" + esc(t(f.querySelector("h3"))) + "</b>" + (t(f.querySelector(".dono")) ? "<span>" + esc(t(f.querySelector(".dono"))) + "</span>" : "") + "<ul>" + itens(f.querySelector("ul"), 5) + "</ul></div>" }).join("") + "</div>") }
  function monta() {
    S = [];
    var F = document.getElementById("fim-do-ano"), N = document.getElementById("ano-2027");
    sl("", "Plano", '<p class="sl-l">O que vamos fazer até o fim do ano e ao longo de 2027</p>', true);
    sl("Sumário", "O que vamos <strong>ver</strong>", "<!--SUM-->");
    var pes = function (raiz) { return raiz ? [].filter.call(raiz.querySelectorAll(".org-n"), vis).map(function (x) { return "<p><b>" + esc(t(x.querySelector("b"))) + "</b><span>" + esc(t(x.querySelector("em")) || t(x.querySelector("span"))) + "</span></p>" }).join("") : "" };
    sl("Estrutura", "Quem <strong>faz</strong>", '<div class="sl-dupla"><div><b>Até o fim do ano</b>' + pes(F && F.querySelector(".org")) + '</div><div><b>Em 2027</b>' + pes(N && N.querySelector(".org")) + "</div></div>");
    grade("Até o fim do ano", "O que <strong>fechar</strong>", blocos(F && F.querySelector(".frentes")), 3);
    var fr = N ? blocos(N.querySelector(".fr-vis")) : [];
    if (fr.length) sl("2027", "O ano em <strong>quatro frentes</strong>", '<div class="sl-g c4 cmp">' + fr.map(function (f) { var im = f.querySelector(".fr-img"); return "<div>" + (im ? '<img class="th" src="' + im.getAttribute("src") + '" alt="">' : "") + "<b>" + esc(t(f.querySelector("h3")).replace(" com estratégia", "")) + "</b><span>" + esc(t(f.querySelector(".fr-m"))) + "</span><span><em>" + esc(t(f.querySelector(".dono"))) + "</em></span></div>" }).join("") + "</div>");
    var sg = N ? [].filter.call(N.querySelectorAll(".seg6>.sub"), vis) : [];
    if (sg.length) sl("2027", "Cada segmento em <strong>uma linha</strong>", '<div class="sl-g c3 cmp">' + sg.map(function (x) { return "<div><b>" + esc(t(x.querySelector("b"))) + "</b><span>" + esc(t(x.querySelector("span"))) + "</span><span><em>" + esc(t(x.querySelector("em"))) + "</em></span></div>" }).join("") + "</div>");
    var sec = function (id) { var h = N && N.querySelector("#" + id); var n = h && h.nextElementSibling; return n && n.classList.contains("frentes") ? n : null };
    grade("2027", "O que <strong>se repete</strong>", blocos(sec("ritmo")), 3);
    grade("2027", "O ano por <strong>trimestre</strong>", blocos(sec("trimestres")), 4);
    var fu = N ? [].slice.call(N.querySelectorAll(".fu-i")) : [], mt = N ? [].slice.call(N.querySelectorAll(".mt-r")) : [];
    if (fu.length || mt.length) sl("2027", "Como vamos <strong>medir</strong>", (fu.length ? '<div class="sl-g c4 cmp">' + fu.map(function (x) { return "<div><b>" + esc(t(x.querySelector("b"))) + "</b><span>" + esc(t(x.querySelector("span"))) + "</span></div>" }).join("") + "</div>" : "")
      + (mt.length ? '<div class="sl-g c' + Math.min(5, mt.length) + ' cmp num" style="margin-top:2vh">' + mt.slice(0, 5).map(function (x) { var e = t(x.querySelector("em")).split(" a "); return "<div><b>" + esc(e[1] || e[0]) + "</b><span>" + esc(t(x.querySelector("span"))) + (e[1] ? ", hoje " + esc(e[0]) : "") + "</span></div>" }).join("") + "</div>" : ""));
    sl("", "Casa de <strong>estruturados</strong>", '<p class="sl-l">Menos, com mais qualidade.</p>', true);
    // sumário clicável: cada seção leva ao primeiro slide dela
    var grupos = {}, ordem = []; S.forEach(function (s, i) { if (!s.sec || s.sec === "Sumário") return; var gk = s.sec.split(" · ")[0]; if (!grupos[gk]) { grupos[gk] = []; ordem.push(gk) } grupos[gk].push([i, s.tit]) });
    var sum = '<div class="sl-sum">' + ordem.map(function (k) { return "<div><b>" + esc(k) + "</b>" + grupos[k].map(function (x) { return '<button type="button" data-ir="' + x[0] + '">' + esc(x[1]) + "<i>" + (x[0] + 1) + "</i></button>" }).join("") + "</div>" }).join("") + "</div>";
    var tot = S.length;
    var html = S.map(function (s, i) {
      var cab = s.capa ? "" : '<div class="sl-cab"><b>' + esc(s.sec) + "</b><i>" + (i + 1) + " / " + tot + "</i></div>";
      cab += '<div class="sl-rod"><span>Tivio Capital · Comunicação &amp; Marketing</span><span>Plano 2027</span><i><u style="width:' + Math.round((i + 1) / tot * 100) + '%"></u></i><b>' + String(i + 1).padStart(2, "0") + " / " + String(tot).padStart(2, "0") + "</b></div>";
      return '<section class="sl' + (s.capa ? " capa" : "") + '">' + cab + (s.capa ? "<h2>" + s.h + "</h2>" : '<h2 class="fr">' + s.h + "</h2>") + s.html.replace("<!--SUM-->", sum) + "</section>";
    }).join("");
    [].forEach.call(A.querySelectorAll(".sl"), function (x) { x.remove() });
    A.querySelector(".ap-sum").insertAdjacentHTML("beforebegin", html);
    A.querySelector(".ap-sum").innerHTML = ordem.map(function (k) { return "<p>" + esc(k) + "</p>" + grupos[k].map(function (x) { return '<button type="button" data-ir="' + x[0] + '">' + esc(x[1]) + "<i>" + (x[0] + 1) + "</i></button>" }).join("") }).join("");
    return [].slice.call(A.querySelectorAll(".sl"));
  }
  var l = [], i = 0, n = document.getElementById("ap-n"), SM = document.getElementById("ap-sum"), MB = document.getElementById("ap-menu");
  A.querySelector(".ap-logo").innerHTML = document.querySelector(".marca").innerHTML;
  function menu(on) { SM.hidden = !on; MB.setAttribute("aria-expanded", on) }
  function v(k) { i = Math.max(0, Math.min(l.length - 1, k)); l.forEach(function (s, j) { s.classList.toggle("ativa", j === i) }); n.textContent = (i + 1) + " / " + l.length; [].forEach.call(SM.querySelectorAll("button"), function (b) { if (+b.dataset.ir === i) b.setAttribute("aria-current", "true"); else b.removeAttribute("aria-current") }) }
  function abrir() { l = monta(); A.hidden = false; menu(false); document.body.style.overflow = "hidden"; v(0); var R = document.documentElement; if (R.requestFullscreen) R.requestFullscreen().catch(function () {}) }
  function sair() { A.hidden = true; menu(false); document.body.style.overflow = ""; if (document.fullscreenElement) document.exitFullscreen() }
  BT.onclick = abrir; document.getElementById("ap-sair").onclick = sair; MB.onclick = function () { menu(SM.hidden) };
  document.getElementById("ap-ant").onclick = function () { v(i - 1) }; document.getElementById("ap-prox").onclick = function () { v(i + 1) };
  A.addEventListener("click", function (e) { var b = e.target.closest && e.target.closest("[data-ir]"); if (b) { v(+b.dataset.ir); menu(false) } });
  document.addEventListener("keydown", function (e) { if (A.hidden || !A.isConnected) return; if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") { e.preventDefault(); v(i + 1) } if (e.key === "ArrowLeft" || e.key === "PageUp") v(i - 1); if (e.key === "Home") v(0); if (e.key === "m" || e.key === "M") menu(SM.hidden); if (e.key === "Escape") { if (!SM.hidden) menu(false); else sair() } });
  document.addEventListener("fullscreenchange", function () { if (!A.isConnected) return; if (!document.fullscreenElement && !A.hidden && A.dataset.fs) sair(); A.dataset.fs = document.fullscreenElement ? "1" : "" });
})();
