/* Transição entre páginas: busca a página cifrada, abre com a chave da sessão e troca o conteúdo sem recarregar. */
(function () {
  if (window.__tvNav) return; window.__tvNav = 1;
  var Q = "tivio-chave", ocupado = false, atual = location.pathname;
  function u8(x) { return Uint8Array.from(atob(x), function (c) { return c.charCodeAt(0) }) }
  function chave() { var g = null; try { g = sessionStorage.getItem(Q) } catch (x) {} return g ? crypto.subtle.importKey("raw", u8(g), "AES-GCM", false, ["decrypt"]) : Promise.reject(0) }
  function abre(url) {
    return Promise.all([fetch(url, { credentials: "same-origin" }).then(function (r) { if (!r.ok) throw r.status; return r.text() }), chave()]).then(function (a) {
      var m = a[0].match(/var D=\{s:"([^"]+)",i:"([^"]+)",c:"([^"]+)"/); if (!m) throw 0;
      return crypto.subtle.decrypt({ name: "AES-GCM", iv: u8(m[2]) }, a[1], u8(m[3]));
    }).then(function (p) { return new DOMParser().parseFromString(new TextDecoder().decode(p), "text/html") });
  }
  function roda(scripts) {
    return scripts.reduce(function (pr, s) {
      return pr.then(function () {
        return new Promise(function (ok) {
          var n = document.createElement("script"); [].forEach.call(s.attributes, function (a) { n.setAttribute(a.name, a.value) });
          if (s.src) { n.onload = n.onerror = ok; n.async = false } n.textContent = s.textContent; s.replaceWith(n); if (!s.src) ok();
        });
      });
    }, Promise.resolve());
  }
  function troca(doc, url) {
    document.title = doc.title;
    [].forEach.call(document.head.querySelectorAll("style,link[rel=stylesheet]"), function (e) { if (e.id !== "tv-nav-css") e.remove() });
    [].forEach.call(doc.head.querySelectorAll("style,link[rel=stylesheet]"), function (e) { document.head.appendChild(document.importNode(e, true)) });
    var corpo = document.importNode(doc.body, true); document.body.replaceWith(corpo);
    window.__tvEd = 0; window.__tvPend = null;
    var h = url.hash && document.getElementById(decodeURIComponent(url.hash.slice(1)));
    if (h) h.scrollIntoView(); else scrollTo(0, 0);
    return [].slice.call(corpo.querySelectorAll("script"));
  }
  function vai(href, empurra) {
    var url = new URL(href, location.href); if (ocupado) return; ocupado = true;
    abre(url.href).then(function (doc) {
      if (empurra) history.pushState(null, "", url.href); atual = location.pathname;
      var sc, fim = function () { return roda(sc).then(function () { dispatchEvent(new HashChangeEvent("hashchange")) }) };
      if (document.startViewTransition && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
        var vt = document.startViewTransition(function () { sc = troca(doc, url) });
        return vt.updateCallbackDone.then(fim);
      }
      sc = troca(doc, url); return fim();
    }).catch(function () { location.href = url.href }).then(function () { ocupado = false });
  }
  var est = document.createElement("style"); est.id = "tv-nav-css";
  est.textContent = "header.barra{view-transition-name:barra}::view-transition-old(root){animation:220ms ease-in both tvSai}::view-transition-new(root){animation:320ms ease-out both tvEntra}@keyframes tvSai{to{opacity:0;transform:translateY(-6px)}}@keyframes tvEntra{from{opacity:0;transform:translateY(8px)}}@media (prefers-reduced-motion:reduce){::view-transition-old(root),::view-transition-new(root){animation:none}}";
  document.head.appendChild(est);
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a || e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || a.target || a.hasAttribute("download")) return;
    var u = new URL(a.href, location.href); if (u.origin !== location.origin || /\.(pdf|zip|png|jpe?g|webp|svg)$/i.test(u.pathname) || /painel-mensal/.test(u.pathname + location.pathname)) return;
    if (u.pathname.replace(/\.html$/, "") === location.pathname.replace(/\.html$/, "")) return;
    if (window.__tvPend && window.__tvPend() && !confirm("Há mudanças sem salvar. Sair mesmo assim?")) { e.preventDefault(); return }
    e.preventDefault(); var d = a.closest("details[open]"); if (d) d.open = false; vai(u.href, true);
  });
  addEventListener("popstate", function () { if (location.pathname !== atual) { atual = location.pathname; vai(location.href, false) } });
})();
