/* Modo edição da Central: o que estiver em dúvida, ou qualquer texto, muda com um clique e salva para todos. */
(function () {
  var W = document.querySelector(".wrap"); if (!W || window.__tvEd) return; window.__tvEd = 1;
  var g = null; try { g = sessionStorage.getItem("tivio-chave") } catch (x) {} if (!g) return;
  var P = (location.pathname.split("/").pop() || "index.html").replace(/\.html$/, "") || "index";
  var SEL = "li,td,h3,p.dono,p.lead,p.meta-txt,.kpi b,.kpi span,.sub b,.sub span,.org-n b,.org-n span,.org-n em,.org-t,.tl-i span,.frente>p,.bm-i dd,.bm-i h3";
  var DUV = /a definir|definir (esse|este) m[eê]s|a medir|a confirmar|em d[uú]vida|\?\s*$/i;
  var TOKEN, D = { edits: {}, novos: {} }, ED = false;
  function hx(b) { return [].map.call(new Uint8Array(b), function (x) { return ("0" + x.toString(16)).slice(-2) }).join("") }
  function h32(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) } return (h >>> 0).toString(36) }
  function norm(s) { return (s || "").replace(/\s+/g, " ").trim() }
  function quem() { var q = ""; try { q = localStorage.getItem("tivio-quem") || "" } catch (x) {} if (!q) { q = norm(prompt("Seu nome, para o histórico de mudanças:") || ""); try { if (q) localStorage.setItem("tivio-quem", q) } catch (x) {} } return q || "Sem nome" }
  function api(m, b) { return fetch("api/edicoes" + (m === "GET" ? "?p=" + encodeURIComponent(P) + (b || "") : ""), { method: m, headers: { "x-tivio": TOKEN, "content-type": "application/json" }, body: m === "POST" ? JSON.stringify(Object.assign({ p: P, quem: quem() }, b)) : undefined }).then(function (r) { if (!r.ok) throw r.status; return r.json() }) }

  var css = document.createElement("style");
  css.textContent = ".ed-duv{outline:1.5px dashed var(--accent);outline-offset:3px;border-radius:6px;cursor:pointer}.ed-duv::after{content:'Em dúvida';display:inline-block;margin-left:8px;padding:1px 8px;border-radius:999px;background:var(--pill);color:var(--fg-2);font:600 11px var(--ff);letter-spacing:.04em;vertical-align:middle}"
    + ".ed-on [data-ed]{outline:1px dashed var(--line-strong);outline-offset:3px;border-radius:6px;cursor:text}.ed-on [data-ed]:hover,[data-ed]:focus{outline:1.5px solid var(--accent)!important;outline-offset:3px}[data-ed][contenteditable]{cursor:text}"
    + ".ed-x{display:none;margin-left:8px;width:22px;height:22px;border:1px solid var(--line-strong);border-radius:50%;background:var(--bg);color:var(--muted);font:600 13px/1 var(--ff);cursor:pointer;vertical-align:middle}.ed-on .ed-x{display:inline-block}.ed-x:hover{color:var(--fg);border-color:var(--accent)}"
    + ".ed-add{display:none;margin:8px 0 0;padding:6px 14px;border:1px dashed var(--accent);border-radius:999px;background:transparent;color:var(--fg);font:600 13px var(--ff);cursor:pointer;list-style:none}.ed-on .ed-add{display:inline-block}.ed-novo{position:relative}"
    + ".ed-bar{position:fixed;left:16px;bottom:16px;z-index:150;display:flex;gap:8px;flex-wrap:wrap}.ed-bar button{display:inline-flex;align-items:center;gap:8px;height:42px;padding:0 16px;border:1px solid var(--line-strong);border-radius:999px;background:var(--bg);color:var(--fg);font:600 14px var(--ff);cursor:pointer;box-shadow:0 4px 18px rgba(0,0,0,.18)}.ed-bar button[aria-pressed=true]{background:var(--accent);color:var(--on-accent);border-color:var(--accent)}.ed-bar svg{width:16px;height:16px}.ed-bar .ed-h{display:none}.ed-on .ed-bar .ed-h{display:inline-flex}"
    + ".ed-msg{position:fixed;left:50%;bottom:72px;z-index:160;transform:translateX(-50%);padding:10px 18px;border-radius:999px;background:var(--accent);color:var(--on-accent);font:600 14px var(--ff);pointer-events:none;opacity:0;transition:opacity .2s}.ed-msg.v{opacity:1}"
    + ".ed-hist{position:fixed;inset:0;z-index:170;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(6,10,14,.6)}.ed-hist[hidden]{display:none}.ed-hist>div{width:100%;max-width:640px;max-height:80vh;overflow:auto;padding:24px;border:1px solid var(--line);border-radius:16px;background:var(--bg);color:var(--fg)}.ed-hist h2{margin:0 0 12px;font:600 22px var(--ff)}.ed-hist ol{margin:0;padding:0;list-style:none}.ed-hist li{padding:10px 0;border-top:1px solid var(--line);font-size:14px}.ed-hist small{display:block;color:var(--muted)}.ed-hist button{float:right;height:36px;padding:0 14px;border:1px solid var(--line-strong);border-radius:999px;background:transparent;color:var(--fg);font:600 14px var(--ff);cursor:pointer}"
    + "@media (max-width:600px){.ed-bar{left:12px;bottom:12px}.ed-bar button{height:38px;padding:0 12px;font-size:13px}}";
  document.head.appendChild(css);
  var msg = document.createElement("div"); msg.className = "ed-msg"; msg.setAttribute("role", "status"); document.body.appendChild(msg);
  function aviso(t) { msg.textContent = t; msg.classList.add("v"); clearTimeout(aviso.t); aviso.t = setTimeout(function () { msg.classList.remove("v") }, 1800) }

  // chaves estáveis: texto original de cada elemento, antes de qualquer edição
  var conta = {}, els = [].filter.call(W.querySelectorAll(SEL), function (e) { return !e.closest("#apres,.gt,.ed-bar,.ed-hist,script,style,nav") && norm(e.textContent) && !e.querySelector(SEL.replace(/,/g, ",")) });
  els.forEach(function (e) { var t = norm(e.textContent), k = h32(t); conta[k] = (conta[k] || 0) + 1; e.dataset.ed = k + "." + conta[k]; e.dataset.orig = t });
  var listas = [].filter.call(W.querySelectorAll("ul"), function (u) { return !u.closest("#apres,nav,.ed-hist") && u.querySelector(":scope>li") });
  var cl = {}; listas.forEach(function (u) { var k = "ul." + h32(norm(u.textContent)); cl[k] = (cl[k] || 0) + 1; u.dataset.edl = k + "." + cl[k] });

  function marcaDuv(e) { e.classList.toggle("ed-duv", DUV.test(txt(e))) }
  function aplica() {
    els.forEach(function (e) { var x = D.edits[e.dataset.ed]; if (x) { if (x.t === null) e.hidden = true; else { e.hidden = false; e.textContent = x.t } } marcaDuv(e) });
    [].forEach.call(W.querySelectorAll("li.ed-novo"), function (n) { n.remove() });
    listas.forEach(function (u) {
      (D.novos[u.dataset.edl] || []).forEach(function (n) { var li = document.createElement("li"); li.className = "ed-novo"; li.dataset.edn = n.id; li.textContent = n.t; ponX(li); marcaDuv(li); u.insertBefore(li, u.querySelector(":scope>.ed-add")) });
      if (!u.querySelector(":scope>.ed-add")) { var b = document.createElement("button"); b.type = "button"; b.className = "ed-add"; b.textContent = "+ Adicionar item"; b.onclick = function () { novo(u) }; u.appendChild(b) }
    });
    els.forEach(function (e) { if (e.tagName === "LI" && !e.querySelector(".ed-x")) ponX(e) });
  }
  function ponX(li) { var x = document.createElement("button"); x.type = "button"; x.className = "ed-x"; x.contentEditable = "false"; x.setAttribute("aria-label", "Remover item"); x.textContent = "×"; x.onclick = function (ev) { ev.stopPropagation(); remove(li) }; li.appendChild(x) }
  function txt(e) { var c = e.cloneNode(true); [].forEach.call(c.querySelectorAll(".ed-x"), function (x) { x.remove() }); return norm(c.textContent) }
  function salva(b, ok) { return api("POST", b).then(function (d) { D = d; aplica(); aviso(ok || "Salvo para todos") }).catch(function () { aviso("Não salvou. Tente de novo.") }) }
  function remove(li) {
    if (!confirm("Remover este item para todos?")) return;
    if (li.dataset.edn) salva({ tipo: "apagar-novo", pai: li.parentNode.dataset.edl, id: li.dataset.edn }, "Removido");
    else salva({ tipo: "remover", chave: li.dataset.ed, antes: li.dataset.orig }, "Removido");
  }
  function novo(u) { var t = norm(prompt("Novo item:") || ""); if (t) salva({ tipo: "novo", pai: u.dataset.edl, texto: t }, "Item adicionado") }
  function edita(e) {
    if (e.isContentEditable) return;
    var antes = txt(e); e.contentEditable = "true"; e.focus();
    var fim = function (cancela) {
      e.removeEventListener("blur", sai); e.removeEventListener("keydown", tecla); e.removeAttribute("contenteditable");
      var t = txt(e); if (cancela || t === antes) { if (cancela) aplica(); return }
      if (!t) { aplica(); return }
      if (e.dataset.edn) salva({ tipo: "mudar-novo", pai: e.parentNode.dataset.edl, id: e.dataset.edn, texto: t });
      else salva({ tipo: "editar", chave: e.dataset.ed, antes: e.dataset.orig, texto: t });
    };
    function sai() { fim(false) }
    function tecla(ev) { if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); e.blur() } if (ev.key === "Escape") { ev.preventDefault(); fim(true); e.blur() } }
    e.addEventListener("blur", sai); e.addEventListener("keydown", tecla);
  }
  function liga() {}
  W.addEventListener("click", function (ev) {
    var e = ev.target.closest && ev.target.closest("[data-ed],li.ed-novo"); if (!e || ev.target.closest(".ed-x,.ed-add")) return;
    if (ED || e.classList.contains("ed-duv")) { ev.preventDefault(); ev.stopPropagation(); edita(e) }
  }, true);

  var bar = document.createElement("div"); bar.className = "ed-bar";
  bar.innerHTML = '<button type="button" class="ed-b" aria-pressed="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>Modo edição</button><button type="button" class="ed-h"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/></svg>Histórico</button>';
  var hist = document.createElement("div"); hist.className = "ed-hist"; hist.hidden = true; hist.setAttribute("role", "dialog"); hist.setAttribute("aria-label", "Histórico de mudanças");
  hist.onclick = function (ev) { if (ev.target === hist || ev.target.closest(".ed-fecha")) hist.hidden = true };
  bar.querySelector(".ed-b").onclick = function () { ED = !ED; this.setAttribute("aria-pressed", ED); document.body.classList.toggle("ed-on", ED); liga(ED); aviso(ED ? "Modo edição ligado: clique em qualquer texto" : "Modo edição desligado") };
  bar.querySelector(".ed-h").onclick = function () {
    api("GET", "&historico=1").then(function (l) {
      var esc = function (s) { var d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML }, nome = { editar: "Mudou", remover: "Removeu", novo: "Adicionou", "mudar-novo": "Mudou", "apagar-novo": "Removeu", restaurar: "Restaurou" };
      hist.innerHTML = '<div><button type="button" class="ed-fecha">Fechar</button><h2>Histórico</h2><ol>' + (l.length ? l.slice(0, 100).map(function (x) { return "<li>" + esc(nome[x.tipo] || x.tipo) + ": " + esc(x.texto) + (x.antes && x.tipo === "editar" ? " <small>Antes: " + esc(x.antes) + "</small>" : "") + "<small>" + esc(x.quem) + " · " + esc(x.p) + " · " + new Date(x.quando).toLocaleString("pt-BR") + "</small></li>" }).join("") : "<li>Nenhuma mudança ainda.</li>") + "</ol></div>";
      hist.hidden = false;
    }).catch(function () { aviso("Não carregou o histórico") });
  };
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && !hist.hidden) hist.hidden = true });

  crypto.subtle.digest("SHA-256", Uint8Array.from(atob(g), function (c) { return c.charCodeAt(0) })).then(function (b) {
    TOKEN = hx(b); return api("GET");
  }).then(function (d) { D = d; document.body.appendChild(bar); document.body.appendChild(hist); aplica() }).catch(function () {});
})();
