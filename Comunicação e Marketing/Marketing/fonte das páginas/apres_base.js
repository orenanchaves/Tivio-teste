/* Moldura das apresentações da Central: quadro fixo de 1920x1080 que escala para a tela,
   título no alto à esquerda, logo no alto à direita, linha e número no rodapé, menu no alto,
   transição entre slides e entrada animada do conteúdo. Cada apresentação só entrega os slides. */
window.tvDeck = function (nome, monta) {
  var A = document.getElementById("apres"), BT = document.getElementById("ap-abrir"); if (!A || !BT) return;
  function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML }
  A.innerHTML = '<div class="ap-palco"><div class="ap-logo"></div></div><nav class="ap-ctl" aria-label="Controles da apresentação"><button type="button" class="ap-menu" aria-expanded="false">Sumário</button><button type="button" class="ap-ant" aria-label="Anterior">‹</button><span class="ap-n"></span><button type="button" class="ap-prox" aria-label="Próximo">›</button><button type="button" class="ap-sair">Sair</button></nav><div class="ap-sum" hidden></div><div class="ap-leg" aria-live="polite"></div>';
  var PAL = A.querySelector(".ap-palco"), LG = A.querySelector(".ap-leg"), SM = A.querySelector(".ap-sum"), MB = A.querySelector(".ap-menu"), N = A.querySelector(".ap-n"), l = [], i = 0;
  var marca = document.querySelector(".marca"); if (marca) A.querySelector(".ap-logo").innerHTML = marca.innerHTML;
  // celular em pé: o slide inteiro no alto, pequeno, e uma legenda legível embaixo com o mesmo conteúdo
  // celular em pé: tela cheia legível, com a mesma moldura; deitado: o quadro 16:9
  function escala() { var re = innerHeight > innerWidth; A.classList.toggle("retrato", re); PAL.classList.remove("vert"); PAL.style.setProperty("--k", Math.min(innerWidth / 1920, innerHeight / 1080)); if (re && l[i]) legenda(l[i]) }
  function legenda(s) {
    if (!A.classList.contains("retrato")) return;
    var c = s.cloneNode(true), capa = s.classList.contains("capa");
    [].forEach.call(c.querySelectorAll("svg,.cu-bar,.cu-wrap,.sl-pe,.gb i,.met i,.gc i,.sl-sec"), function (x) { x.remove() });
    var h = c.querySelector("h2"), corpo = c.querySelector(".sl-corpo"); if (h && corpo && corpo.contains(h)) h.remove();
    var n = String(l.indexOf(s) + 1).padStart(2, "0"), sec = s.querySelector(".sl-sec") ? s.querySelector(".sl-sec").textContent : "";
    var logo = A.querySelector(".ap-logo") ? A.querySelector(".ap-logo").innerHTML : "";
    LG.className = "ap-leg" + (capa ? " lg-capa" : "");
    LG.innerHTML = '<header class="lg-top"><div>' + (sec ? '<p class="lg-sec">' + esc(sec) + "</p>" : "") + (h && !capa ? "<h3>" + h.innerHTML + "</h3>" : "") + '</div><div class="lg-logo">' + logo + "</div></header>"
      + '<div class="lg-c">' + (capa && h ? "<h2>" + h.innerHTML + "</h2>" : "") + (corpo ? corpo.innerHTML : "") + "</div>"
      + '<footer class="lg-pe"><span>Tivio Capital · Comunicação &amp; Marketing · ' + esc(nome) + "</span><b>" + n + "</b></footer>";
    LG.scrollTop = 0; LG.classList.remove("entra"); void LG.offsetWidth; LG.classList.add("entra");
  }
  function monte() {
    var S = monta(), tot = S.length, grupos = [], idx = {};
    S.forEach(function (s, k) { if (!s.sec || s.sum || s.fora) return; var g = s.sec.split(" · ")[0]; if (!(g in idx)) { idx[g] = grupos.length; grupos.push([g, []]) } grupos[idx[g]][1].push([k, s.h.replace(/<[^>]+>/g, "")]) });
    var botoes = function (lst) { return lst.map(function (x) { return '<button type="button" data-ir="' + x[0] + '">' + esc(x[1]) + "<i>" + String(x[0] + 1).padStart(2, "0") + "</i></button>" }).join("") };
    var sum = '<div class="sl-sum">' + grupos.map(function (g) { return "<div><b>" + esc(g[0]) + "</b>" + botoes(g[1]) + "</div>" }).join("") + "</div>";
    SM.innerHTML = grupos.map(function (g) { return "<p>" + esc(g[0]) + "</p>" + botoes(g[1]) }).join("");
    [].forEach.call(PAL.querySelectorAll(".sl"), function (x) { x.remove() });
    PAL.insertAdjacentHTML("beforeend", S.map(function (s, k) {
      var pe = '<footer class="sl-pe"><span>Tivio Capital · Comunicação &amp; Marketing · ' + esc(nome) + "</span><b>" + String(k + 1).padStart(2, "0") + "</b></footer>";
      if (s.capa) return '<section class="sl capa"><div class="sl-corpo"><h2>' + s.h + "</h2>" + (s.html || "") + "</div>" + pe + "</section>";
      return '<section class="sl"><header class="sl-top"><span class="sl-sec">' + esc(s.sec) + '</span><h2 class="fr">' + s.h + '</h2></header><div class="sl-corpo">' + (s.sum ? sum : s.html) + "</div>" + pe + "</section>";
    }).join(""));
    return [].slice.call(PAL.querySelectorAll(".sl"));
  }
  function menu(on) { SM.hidden = !on; MB.setAttribute("aria-expanded", on) }
  function v(k) {
    i = Math.max(0, Math.min(l.length - 1, k));
    l.forEach(function (s, j) { s.classList.toggle("ativa", j === i); s.classList.toggle("antes", j < i) });
    if (l[i]) legenda(l[i]);
    // números que contam do zero quando o slide entra
    if (l[i] && !matchMedia("(prefers-reduced-motion: reduce)").matches) [].forEach.call(l[i].querySelectorAll("[data-conta]"), function (e) {
      var fim = +e.dataset.conta, suf = e.dataset.suf || "", t0 = null, atraso = e.closest(".cu-l") ? 1200 : 300;
      var fmt = function (n) { return "R$ " + Math.round(n).toLocaleString("pt-BR") + suf };
      e.textContent = fmt(0);
      setTimeout(function () { requestAnimationFrame(function passo(ts) { if (t0 === null) t0 = ts; var q = Math.min(1, (ts - t0) / 1100); e.textContent = fmt(fim * (1 - Math.pow(1 - q, 3))); if (q < 1) requestAnimationFrame(passo) }) }, atraso);
    });
    N.textContent = String(i + 1).padStart(2, "0") + " / " + String(l.length).padStart(2, "0");
    [].forEach.call(SM.querySelectorAll("button"), function (b) { if (+b.dataset.ir === i) b.setAttribute("aria-current", "true"); else b.removeAttribute("aria-current") });
  }
  function abrir() { l = monte(); escala(); A.hidden = false; menu(false); document.body.style.overflow = "hidden"; v(0); var R = document.documentElement; if (R.requestFullscreen) R.requestFullscreen().catch(function () {}) }
  function sair() { A.hidden = true; menu(false); document.body.style.overflow = ""; if (document.fullscreenElement) document.exitFullscreen() }
  BT.onclick = abrir; A.querySelector(".ap-sair").onclick = sair; MB.onclick = function () { menu(SM.hidden) };
  A.querySelector(".ap-ant").onclick = function () { v(i - 1) }; A.querySelector(".ap-prox").onclick = function () { v(i + 1) };
  A.addEventListener("click", function (e) { var b = e.target.closest && e.target.closest("[data-ir]"); if (b) { v(+b.dataset.ir); menu(false) } });
  addEventListener("resize", function () { if (A.isConnected) escala() });
  var tx = null, ty = 0;
  [PAL, LG].forEach(function (z) {
    z.addEventListener("touchstart", function (e) { tx = e.touches[0].clientX; ty = e.touches[0].clientY }, { passive: true });
    z.addEventListener("touchend", function (e) { if (tx === null) return; var dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty; tx = null; if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.3) v(i + (dx < 0 ? 1 : -1)) });
  });
  document.addEventListener("keydown", function (e) {
    if (A.hidden || !A.isConnected) return;
    if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") { e.preventDefault(); v(i + 1) }
    if (e.key === "ArrowLeft" || e.key === "PageUp") v(i - 1);
    if (e.key === "Home") v(0); if (e.key === "End") v(l.length - 1);
    if (e.key === "m" || e.key === "M") menu(SM.hidden);
    if (e.key === "Escape") { if (!SM.hidden) menu(false); else sair() }
  });
  document.addEventListener("fullscreenchange", function () { if (!A.isConnected) return; if (!document.fullscreenElement && !A.hidden && A.dataset.fs) sair(); A.dataset.fs = document.fullscreenElement ? "1" : "" });
};
