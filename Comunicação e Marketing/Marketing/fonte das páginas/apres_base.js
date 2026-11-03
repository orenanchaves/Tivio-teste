/* Moldura das apresentações da Central: quadro fixo de 1920x1080 que escala para a tela,
   título no alto à esquerda, logo no alto à direita, linha e número no rodapé, menu no alto,
   transição entre slides e entrada animada do conteúdo. Cada apresentação só entrega os slides. */
window.tvDeck = function (nome, monta) {
  var A = document.getElementById("apres"), BT = document.getElementById("ap-abrir"); if (!A || !BT) return;
  function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML }
  A.innerHTML = '<div class="ap-palco"><div class="ap-logo"></div></div><nav class="ap-ctl" aria-label="Controles da apresentação"><button type="button" class="ap-menu" aria-expanded="false">Sumário</button><button type="button" class="ap-ant" aria-label="Anterior">‹</button><span class="ap-n"></span><button type="button" class="ap-prox" aria-label="Próximo">›</button><button type="button" class="ap-sair">Sair</button></nav><div class="ap-sum" hidden></div>';
  var PAL = A.querySelector(".ap-palco"), SM = A.querySelector(".ap-sum"), MB = A.querySelector(".ap-menu"), N = A.querySelector(".ap-n"), l = [], i = 0;
  var marca = document.querySelector(".marca"); if (marca) A.querySelector(".ap-logo").innerHTML = marca.innerHTML;
  function escala() { PAL.style.setProperty("--k", Math.min(innerWidth / 1920, innerHeight / 1080)) }
  function monte() {
    var S = monta(), tot = S.length, grupos = [], idx = {};
    S.forEach(function (s, k) { if (!s.sec || s.sum) return; var g = s.sec.split(" · ")[0]; if (!(g in idx)) { idx[g] = grupos.length; grupos.push([g, []]) } grupos[idx[g]][1].push([k, s.h.replace(/<[^>]+>/g, "")]) });
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
    N.textContent = String(i + 1).padStart(2, "0") + " / " + String(l.length).padStart(2, "0");
    [].forEach.call(SM.querySelectorAll("button"), function (b) { if (+b.dataset.ir === i) b.setAttribute("aria-current", "true"); else b.removeAttribute("aria-current") });
  }
  function abrir() { l = monte(); escala(); A.hidden = false; menu(false); document.body.style.overflow = "hidden"; v(0); var R = document.documentElement; if (R.requestFullscreen) R.requestFullscreen().catch(function () {}) }
  function sair() { A.hidden = true; menu(false); document.body.style.overflow = ""; if (document.fullscreenElement) document.exitFullscreen() }
  BT.onclick = abrir; A.querySelector(".ap-sair").onclick = sair; MB.onclick = function () { menu(SM.hidden) };
  A.querySelector(".ap-ant").onclick = function () { v(i - 1) }; A.querySelector(".ap-prox").onclick = function () { v(i + 1) };
  A.addEventListener("click", function (e) { var b = e.target.closest && e.target.closest("[data-ir]"); if (b) { v(+b.dataset.ir); menu(false) } });
  addEventListener("resize", function () { if (A.isConnected) escala() });
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
