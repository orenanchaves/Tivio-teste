/* Modo edição da Central: muda texto, adiciona, remove e arrasta itens; o botão Salvar grava para todos. */
(function () {
  var W = document.querySelector(".wrap"); if (!W || window.__tvEd) return; window.__tvEd = 1;
  var g = null; try { g = sessionStorage.getItem("tivio-chave") } catch (x) {} if (!g) return;
  var P = (location.pathname.split("/").pop() || "index").replace(/\.html$/, "") || "index";
  var SEL = "li,td,h3,p.dono,p.lead,p.meta-txt,.kpi b,.kpi span,.sub b,.sub span,.sub em,.fr-m,.org-n b,.org-n span,.org-n em,.org-t,.tl-i span,.frente>p,.bm-i dd,.bm-i h3,ol.roteiro li>b,ol.roteiro li>span,.lig-i>b,.lig-i>span";
  var BLK = ".frentes>section.frente,.org-n,ol.roteiro>li,.subs>.sub,.kpis>.kpi,.lig>.lig-i,.bm>.bm-i";
  var DUV = /a definir|definir (esse|este) m[eê]s|a medir|a confirmar|em d[uú]vida|\?\s*$/i;
  var TOKEN, BASE = { edits: {}, novos: {}, ordem: {}, blocos: {}, resp: {} }, PEND = [], ED = false;
  function hx(b) { return [].map.call(new Uint8Array(b), function (x) { return ("0" + x.toString(16)).slice(-2) }).join("") }
  function h32(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) } return (h >>> 0).toString(36) }
  function norm(s) { return (s || "").replace(/\s+/g, " ").trim() }
  function uid() { return (crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2)) }
  function quem() { var q = ""; try { q = localStorage.getItem("tivio-quem") || "" } catch (x) {} if (!q) { q = norm(prompt("Seu nome, para o histórico de mudanças:") || ""); try { if (q) localStorage.setItem("tivio-quem", q) } catch (x) {} } return q || "Sem nome" }
  function api(m, b, extra) { return fetch("api/edicoes" + (m === "GET" ? "?p=" + encodeURIComponent(P) + (extra || "") : ""), { method: m, headers: { "x-tivio": TOKEN, "content-type": "application/json" }, body: m === "POST" ? JSON.stringify(b) : undefined }).then(function (r) { if (!r.ok) throw r.status; return r.json() }) }
  // mesma regra do servidor (functions/api/edicoes.js)
  function aplicaOp(d, o) {
    d.ordem = d.ordem || {}; d.blocos = d.blocos || {};
    if (o.tipo === "editar" || o.tipo === "remover") d.edits[o.chave] = { t: o.tipo === "remover" ? null : o.texto, antes: o.antes };
    else if (o.tipo === "novo") (d.novos[o.pai] = d.novos[o.pai] || []).push({ id: o.id, t: o.texto });
    else if (o.tipo === "mudar-novo" || o.tipo === "apagar-novo") Object.keys(d.novos).forEach(function (k) { var l = d.novos[k], i = l.findIndex(function (x) { return x.id === o.id }); if (i >= 0) { if (o.tipo === "apagar-novo") l.splice(i, 1); else l[i].t = o.texto } });
    else if (o.tipo === "novo-bloco") (d.blocos[o.cont] = d.blocos[o.cont] || []).push({ id: o.id, titulo: o.texto, dono: o.dono || "" });
    else if (o.tipo === "mudar-bloco" || o.tipo === "apagar-bloco") Object.keys(d.blocos).forEach(function (k) { var l = d.blocos[k], i = l.findIndex(function (x) { return x.id === o.id }); if (i >= 0) { if (o.tipo === "apagar-bloco") l.splice(i, 1); else l[i][o.campo === "dono" ? "dono" : "titulo"] = o.texto } });
    else if (o.tipo === "resposta") { d.resp = d.resp || {}; if (o.texto) d.resp[o.chave] = { t: o.texto, quem: "você, não salvo" }; else delete d.resp[o.chave] }
    else if (o.tipo === "ordem") Object.keys(o.listas).forEach(function (k) { d.ordem[k] = o.listas[k] });
  }
  function estado() { var d = JSON.parse(JSON.stringify(BASE)); PEND.forEach(function (o) { aplicaOp(d, o) }); return d }

  var css = document.createElement("style"); css.id = "ed-css";
  css.textContent = ".ed-duv{outline:1.5px dashed var(--accent);outline-offset:3px;border-radius:6px;cursor:pointer}.ed-duv::after{content:'Em dúvida';display:inline-block;margin-left:8px;padding:1px 8px;border-radius:999px;background:var(--pill);color:var(--fg-2);font:600 11px var(--ff);letter-spacing:.04em;vertical-align:middle}"
    + ".ed-on [data-ed],.ed-on li.ed-novo{outline:1px dashed var(--line-strong);outline-offset:3px;border-radius:6px;cursor:text}.ed-on [data-ed]:hover,.ed-on li.ed-novo:hover,[contenteditable=true]{outline:1.5px solid var(--accent)!important;outline-offset:3px}"
    + ".ed-x,.ed-g{display:none;width:22px;height:22px;border:1px solid var(--line-strong);border-radius:50%;background:var(--bg);color:var(--muted);font:600 13px/1 var(--ff);cursor:pointer;vertical-align:middle;padding:0}.ed-x{margin-left:8px}.ed-g{margin-right:6px;cursor:grab;touch-action:none;font-size:12px;letter-spacing:-1px}.ed-on .ed-x,.ed-on .ed-g{display:inline-block}.ed-x:hover,.ed-g:hover{color:var(--fg);border-color:var(--accent)}"
    + ".ed-arr{opacity:.55;outline:2px solid var(--accent)!important}.ed-arrastando,.ed-arrastando *{cursor:grabbing!important;user-select:none}.ed-alvo{outline:2px dashed var(--accent)!important;outline-offset:6px}"
    + ".ed-add{display:none;margin:8px 0 0;padding:6px 14px;border:1px dashed var(--accent);border-radius:999px;background:transparent;color:var(--fg);font:600 13px var(--ff);cursor:pointer}.ed-on .ed-add{display:inline-block}"
    + ".ed-bar{position:fixed;left:16px;bottom:16px;z-index:150;display:flex;gap:8px;flex-wrap:wrap;max-width:calc(100% - 32px)}.ed-bar button{display:inline-flex;align-items:center;gap:8px;height:42px;padding:0 16px;border:1px solid var(--line-strong);border-radius:999px;background:var(--bg);color:var(--fg);font:600 14px var(--ff);cursor:pointer;box-shadow:0 4px 18px rgba(0,0,0,.18)}.ed-bar button[aria-pressed=true],.ed-bar .ed-s{background:var(--accent);color:var(--on-accent);border-color:var(--accent)}.ed-bar svg{width:16px;height:16px}.ed-bar .ed-h{display:none}.ed-on .ed-bar .ed-h{display:inline-flex}.ed-bar [hidden]{display:none!important}"
    + ".ed-msg{position:fixed;left:50%;bottom:72px;z-index:160;transform:translateX(-50%);padding:10px 18px;border-radius:999px;background:var(--accent);color:var(--on-accent);font:600 14px var(--ff);pointer-events:none;opacity:0;transition:opacity .2s;text-align:center}.ed-msg.v{opacity:1}"
    + ".ed-hist{position:fixed;inset:0;z-index:170;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(6,10,14,.6)}.ed-hist[hidden]{display:none}.ed-hist>div{width:100%;max-width:640px;max-height:80vh;overflow:auto;padding:24px;border:1px solid var(--line);border-radius:16px;background:var(--bg);color:var(--fg)}.ed-hist h2{margin:0 0 12px;font:600 22px var(--ff)}.ed-hist ol{margin:0;padding:0;list-style:none}.ed-hist li{padding:10px 0;border-top:1px solid var(--line);font-size:14px}.ed-hist small{display:block;color:var(--muted)}.ed-hist button{float:right;height:36px;padding:0 14px;border:1px solid var(--line-strong);border-radius:999px;background:transparent;color:var(--fg);font:600 14px var(--ff);cursor:pointer}"
    + ".wrap [hidden]{display:none!important}.ed-on [data-edb],.ed-on .ed-nb{position:relative}.ed-xb{display:none;position:absolute;top:8px;right:8px;z-index:3;height:28px;padding:0 12px;border:1px solid var(--line-strong);border-radius:999px;background:var(--bg);color:var(--muted);font:600 12px var(--ff);cursor:pointer;align-items:center;gap:6px}.ed-on .ed-xb{display:inline-flex}.ed-xb:hover{color:var(--fg);border-color:var(--accent)}.ed-addb{display:none;margin:12px 0 4px;padding:9px 18px;border:1.5px dashed var(--accent);border-radius:999px;background:transparent;color:var(--fg);font:600 14px var(--ff);cursor:pointer}.ed-on .ed-addb{display:inline-block}.ed-on [data-edbc]{outline:1px dashed var(--line-strong);outline-offset:3px;border-radius:6px;cursor:text}"
    + ".perguntas ul{display:flex!important;flex-direction:column;align-items:stretch;gap:10px}.perguntas ul>li{display:flex!important;flex-wrap:wrap;align-items:center;border-radius:14px!important;padding:10px 14px!important;max-width:none!important}"
    + ".ed-r{flex:1 1 100%;display:block;margin-top:8px}.ed-r textarea{display:block;box-sizing:border-box;width:100%;min-height:38px;padding:8px 12px;border:1px dashed var(--line-strong);border-radius:10px;background:transparent;color:var(--fg);font:400 14px/1.45 var(--ff);resize:none;overflow:hidden}.ed-r textarea:focus{outline:0;border-style:solid;border-color:var(--accent)}.ed-r textarea::placeholder{color:var(--muted)}"
    + ".ed-resp-ok .ed-r textarea{border-style:solid;border-color:var(--accent)}.ed-r[data-q]:not([data-q=''])::after{content:attr(data-q);display:block;margin-top:4px;color:var(--muted);font:400 12px var(--ff)}.ed-on .perguntas .ed-x{margin-left:auto}"
    + "@media (max-width:600px){.ed-bar{left:12px;bottom:12px;gap:6px}.ed-bar button{height:38px;padding:0 12px;font-size:13px}.ed-msg{bottom:64px}}";
  var velho = document.getElementById("ed-css"); if (velho) velho.remove(); document.head.appendChild(css);
  var msg = document.createElement("div"); msg.className = "ed-msg"; msg.setAttribute("role", "status");
  function aviso(t) { msg.textContent = t; msg.classList.add("v"); clearTimeout(aviso.t); aviso.t = setTimeout(function () { msg.classList.remove("v") }, 2000) }

  // chaves estáveis a partir do texto original, antes de qualquer edição
  var conta = {}, els = [].filter.call(W.querySelectorAll(SEL), function (e) { return !e.closest("#apres,.gt,nav,.ed-bar,.ed-hist") && norm(e.textContent) && !e.querySelector(SEL) });
  els.forEach(function (e) { var t = norm(e.textContent), k = h32(t); conta[k] = (conta[k] || 0) + 1; e.dataset.ed = k + "." + conta[k]; e.dataset.orig = t });
  var listas = [].filter.call(W.querySelectorAll("ul"), function (u) { return !u.closest("#apres,nav,.ed-hist") && u.querySelector(":scope>li") });
  var cl = {}; listas.forEach(function (u) { var k = "ul." + h32(norm(u.textContent)); cl[k] = (cl[k] || 0) + 1; u.dataset.edl = k + "." + cl[k] });
  var cb = {}, blocos = [].filter.call(W.querySelectorAll(BLK), function (b) { return !b.closest("#apres,nav") });
  blocos.forEach(function (b) { var k = "b." + h32(norm(b.textContent)); cb[k] = (cb[k] || 0) + 1; b.dataset.edb = k + "." + cb[k] });
  var cc = {}, conts = [].filter.call(W.querySelectorAll(".frentes"), function (c) { return !c.closest("#apres") });
  conts.forEach(function (c) { var k = "c." + h32(norm(c.textContent)); cc[k] = (cc[k] || 0) + 1; c.dataset.edc = k + "." + cc[k] });
  function xb(b) {
    if (b.querySelector(":scope>.ed-xb")) return;
    var x = document.createElement("button"); x.type = "button"; x.className = "ed-xb"; x.contentEditable = "false"; x.textContent = "× Excluir"; x.setAttribute("aria-label", "Excluir categoria");
    x.onclick = function (ev) { ev.preventDefault(); ev.stopPropagation(); if (!confirm("Excluir esta categoria inteira?")) return; if (b.dataset.edbn) poe({ tipo: "apagar-bloco", id: b.dataset.edbn }); else poe({ tipo: "remover", chave: b.dataset.edb, antes: norm(b.textContent).replace(/× Excluir/g, "").slice(0, 300) }) };
    b.appendChild(x);
  }
  function novoBloco(c) { var t = norm(prompt("Nome da nova categoria:") || ""); if (!t) return; var d = norm(prompt("Responsável (pode deixar em branco):") || ""); poe({ tipo: "novo-bloco", cont: c.dataset.edc, id: uid(), texto: t, dono: d }) }
  function tok(li) { return li.dataset.edn ? "n:" + li.dataset.edn : "o:" + li.dataset.ed }
  function porTok(t) { return W.querySelector(t.slice(0, 2) === "n:" ? 'li[data-edn="' + t.slice(2) + '"]' : '[data-ed="' + t.slice(2) + '"]') }
  function txt(e) { var c = e.cloneNode(true); [].forEach.call(c.querySelectorAll(".ed-x,.ed-g,.ed-xb,.ed-r"), function (x) { x.remove() }); return norm(c.textContent) }
  function marcaDuv(e) { e.classList.toggle("ed-duv", DUV.test(txt(e))) }
  function botoes(li) {
    if (li.querySelector(":scope>.ed-x")) return;
    var gr = document.createElement("button"); gr.type = "button"; gr.className = "ed-g"; gr.contentEditable = "false"; gr.setAttribute("aria-label", "Arrastar item"); gr.textContent = "⋮⋮"; gr.addEventListener("pointerdown", arrasta); li.insertBefore(gr, li.firstChild);
    var x = document.createElement("button"); x.type = "button"; x.className = "ed-x"; x.contentEditable = "false"; x.setAttribute("aria-label", "Remover item"); x.textContent = "×"; x.onclick = function (ev) { ev.stopPropagation(); remove(li) }; li.appendChild(x);
  }
  function render() {
    var d = estado();
    blocos.forEach(function (b) { var x = d.edits[b.dataset.edb]; b.hidden = !!(x && x.t === null); xb(b) });
    [].forEach.call(W.querySelectorAll(".ed-nb"), function (n) { n.remove() });
    var todas = listas.slice();
    conts.forEach(function (c) {
      (d.blocos[c.dataset.edc] || []).forEach(function (nb) {
        var s = document.createElement("section"); s.className = "frente vidro ed-nb"; s.dataset.edbn = nb.id;
        var h = document.createElement("h3"); h.dataset.edbc = "titulo"; h.textContent = nb.titulo; s.appendChild(h);
        var dn = document.createElement("p"); dn.className = "dono"; dn.dataset.edbc = "dono"; dn.textContent = nb.dono || "Responsável"; s.appendChild(dn);
        var u = document.createElement("ul"); u.dataset.edl = "nb." + nb.id; s.appendChild(u); todas.push(u); xb(s); c.appendChild(s);
      });
      var nx = c.nextElementSibling; if (!nx || !nx.classList.contains("ed-addb")) { var b = document.createElement("button"); b.type = "button"; b.className = "ed-addb"; b.textContent = "+ Adicionar categoria"; b.onclick = function () { novoBloco(c) }; c.after(b) }
    });
    els.forEach(function (e) {
      var x = d.edits[e.dataset.ed], t = x ? x.t : null, kids = [].slice.call(e.querySelectorAll(":scope>.ed-x,:scope>.ed-g,:scope>.ed-r"));
      if (x && t === null) e.hidden = true; else { e.hidden = false; if (x && txt(e) !== t) { e.textContent = t; kids.forEach(function (k) { e.appendChild(k) }); var gr = e.querySelector(":scope>.ed-g"); if (gr) e.insertBefore(gr, e.firstChild) } }
      marcaDuv(e);
    });
    [].forEach.call(W.querySelectorAll("li.ed-novo"), function (n) { n.remove() });
    todas.forEach(function (u) {
      if (!u.querySelector(":scope>.ed-add")) { var b = document.createElement("button"); b.type = "button"; b.className = "ed-add"; b.textContent = "+ Adicionar item"; b.onclick = function () { novo(u) }; u.appendChild(b) }
      (d.novos[u.dataset.edl] || []).forEach(function (n) { var li = document.createElement("li"); li.className = "ed-novo"; li.dataset.edn = n.id; li.textContent = n.t; u.insertBefore(li, u.querySelector(":scope>.ed-add")) });
    });
    Object.keys(d.ordem || {}).forEach(function (k) {
      var u = W.querySelector('ul[data-edl="' + k + '"]'); if (!u) return;
      d.ordem[k].forEach(function (t) { var li = porTok(t); if (li) u.insertBefore(li, u.querySelector(":scope>.ed-add")) });
    });
    [].forEach.call(W.querySelectorAll("ul[data-edl]>li"), function (li) { botoes(li); marcaDuv(li); if (li.closest(".perguntas")) resposta(li, d) });
    barra();
  }
  // listas de perguntas: cada item tem um campo de resposta, visível sempre, que entra no Salvar
  function resposta(li, d) {
    var r = li.querySelector(":scope>.ed-r"), k = tok(li), x = (d.resp || {})[k];
    if (!r) {
      r = document.createElement("span"); r.className = "ed-r"; r.contentEditable = "false";
      var a = document.createElement("textarea"); a.rows = 1; a.placeholder = "Escreva a resposta"; a.setAttribute("aria-label", "Resposta para: " + txt(li));
      a.addEventListener("input", function () { a.style.height = "auto"; a.style.height = a.scrollHeight + "px" });
      a.addEventListener("change", function () { var v = norm(a.value), y = (estado().resp || {})[tok(li)]; if (v !== (y ? y.t : "")) poe({ tipo: "resposta", chave: tok(li), texto: v }) });
      a.addEventListener("keydown", function (ev) { if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); a.blur() } });
      r.appendChild(a); li.appendChild(r);
    }
    var t = r.querySelector("textarea"); if (document.activeElement !== t) { t.value = x ? x.t : ""; t.style.height = "auto"; if (t.value) t.style.height = t.scrollHeight + "px" }
    r.dataset.q = x && x.quem ? x.quem + (x.quando ? " · " + new Date(x.quando).toLocaleDateString("pt-BR") : "") : "";
    li.classList.toggle("ed-resp-ok", !!(x && x.t));
  }
  function poe(o) { PEND.push(o); render(); aviso("Mudança pendente: clique em Salvar") }
  function remove(li) {
    if (li.dataset.edn) poe({ tipo: "apagar-novo", id: li.dataset.edn });
    else poe({ tipo: "remover", chave: li.dataset.ed, antes: li.dataset.orig });
  }
  function novo(u) { var t = norm(prompt("Novo item:") || ""); if (t) poe({ tipo: "novo", pai: u.dataset.edl, id: uid(), texto: t }) }
  function edita(e) {
    if (e.isContentEditable) return;
    var antes = txt(e); e.contentEditable = "true"; e.focus();
    function fim(cancela) {
      e.removeEventListener("blur", sai); e.removeEventListener("keydown", tecla); e.removeAttribute("contenteditable");
      var t = txt(e); if (cancela || !t || t === antes) { render(); return }
      if (e.dataset.edbc) poe({ tipo: "mudar-bloco", id: e.closest("[data-edbn]").dataset.edbn, campo: e.dataset.edbc, texto: t });
      else if (e.dataset.edn) poe({ tipo: "mudar-novo", id: e.dataset.edn, texto: t });
      else poe({ tipo: "editar", chave: e.dataset.ed, antes: e.dataset.orig, texto: t });
    }
    function sai() { fim(false) }
    function tecla(ev) { if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); e.blur() } if (ev.key === "Escape") { ev.preventDefault(); e.removeEventListener("blur", sai); fim(true); e.blur() } }
    e.addEventListener("blur", sai); e.addEventListener("keydown", tecla);
  }
  // arrastar: segura o ⋮⋮ e solta em outra posição ou em outra lista
  function arrasta(ev) {
    ev.preventDefault(); ev.stopPropagation();
    var li = ev.currentTarget.parentNode, de = li.parentNode, alvo = null; li.classList.add("ed-arr"); document.body.classList.add("ed-arrastando");
    try { ev.currentTarget.setPointerCapture(ev.pointerId) } catch (x) {}
    function move(e) {
      li.style.pointerEvents = "none"; var sob = document.elementFromPoint(e.clientX, e.clientY); li.style.pointerEvents = "";
      if (e.clientY < 60) scrollBy(0, -12); else if (e.clientY > innerHeight - 60) scrollBy(0, 12);
      var u = sob && sob.closest && sob.closest("ul[data-edl]"); if (alvo && alvo !== u) alvo.classList.remove("ed-alvo"); alvo = u; if (!u) return; u.classList.add("ed-alvo");
      var irmao = sob.closest("ul[data-edl]>li");
      if (irmao && irmao !== li) { var r = irmao.getBoundingClientRect(), depois = (r.width > r.height * 3 ? e.clientY > r.top + r.height / 2 : e.clientX > r.left + r.width / 2); u.insertBefore(li, depois ? irmao.nextSibling : irmao) }
      else if (!irmao) u.insertBefore(li, u.querySelector(":scope>.ed-add"));
    }
    function solta() {
      document.removeEventListener("pointermove", move); document.removeEventListener("pointerup", solta); document.removeEventListener("pointercancel", solta);
      li.classList.remove("ed-arr"); document.body.classList.remove("ed-arrastando"); if (alvo) alvo.classList.remove("ed-alvo");
      var o = { tipo: "ordem", listas: {} };
      [de, li.parentNode].forEach(function (u) { o.listas[u.dataset.edl] = [].map.call(u.querySelectorAll(":scope>li"), tok) });
      poe(o);
    }
    document.addEventListener("pointermove", move); document.addEventListener("pointerup", solta); document.addEventListener("pointercancel", solta);
  }
  W.addEventListener("click", function (ev) {
    var e = ev.target.closest && ev.target.closest("[data-ed],li.ed-novo,[data-edbc]"); if (!e || ev.target.closest(".ed-x,.ed-add,.ed-g,.ed-xb,.ed-addb,.ed-r")) return;
    if (ED || e.classList.contains("ed-duv")) { ev.preventDefault(); ev.stopPropagation(); edita(e) }
  }, true);

  var bar = document.createElement("div"); bar.className = "ed-bar";
  bar.innerHTML = '<button type="button" class="ed-b" aria-pressed="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>Modo edição</button>'
    + '<button type="button" class="ed-s" hidden><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3h11l3 3v15H5z"/><path d="M8 3v5h7V3M8 21v-7h8v7"/></svg><span>Salvar</span></button>'
    + '<button type="button" class="ed-d" hidden>Descartar</button>'
    + '<button type="button" class="ed-h"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/></svg>Histórico</button>';
  function barra() { var n = PEND.length; bar.querySelector(".ed-s").hidden = !n; bar.querySelector(".ed-d").hidden = !n; bar.querySelector(".ed-s span").textContent = n ? "Salvar (" + n + ")" : "Salvar" }
  window.__tvPend = function () { return PEND.length };
  addEventListener("beforeunload", function (e) { if (PEND.length) { e.preventDefault(); e.returnValue = "" } });
  bar.querySelector(".ed-b").onclick = function () { ED = !ED; this.setAttribute("aria-pressed", ED); document.body.classList.toggle("ed-on", ED); aviso(ED ? "Modo edição: clique no texto, arraste pelo ⋮⋮ e salve no fim" : "Modo edição desligado") };
  bar.querySelector(".ed-s").onclick = function () {
    var b = this; b.disabled = true;
    api("POST", { p: P, quem: quem(), ops: PEND }).then(function (d) { BASE = d; PEND = []; render(); aviso("Salvo para todos") }).catch(function () { aviso("Não salvou. Tente de novo.") }).then(function () { b.disabled = false });
  };
  bar.querySelector(".ed-d").onclick = function () { if (confirm("Descartar as mudanças que não foram salvas?")) { PEND = []; location.reload() } };
  var hist = document.createElement("div"); hist.className = "ed-hist"; hist.hidden = true; hist.setAttribute("role", "dialog"); hist.setAttribute("aria-label", "Histórico de mudanças");
  hist.onclick = function (ev) { if (ev.target === hist || ev.target.closest(".ed-fecha")) hist.hidden = true };
  bar.querySelector(".ed-h").onclick = function () {
    api("GET", null, "&historico=1").then(function (l) {
      var esc = function (s) { var d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML }, nome = { editar: "Mudou", remover: "Removeu", novo: "Adicionou", "mudar-novo": "Mudou", "apagar-novo": "Removeu", restaurar: "Restaurou", resposta: "Respondeu", ordem: "Reorganizou", "novo-bloco": "Criou a categoria", "mudar-bloco": "Mudou a categoria", "apagar-bloco": "Excluiu a categoria" };
      hist.innerHTML = '<div><button type="button" class="ed-fecha">Fechar</button><h2>Histórico</h2><ol>' + (l.length ? l.slice(0, 100).map(function (x) { return "<li>" + esc(nome[x.tipo] || x.tipo) + (x.tipo === "ordem" ? " itens" : ": " + esc(x.texto)) + (x.antes && x.tipo === "editar" ? " <small>Antes: " + esc(x.antes) + "</small>" : "") + "<small>" + esc(x.quem) + " · " + esc(x.p) + " · " + new Date(x.quando).toLocaleString("pt-BR") + "</small></li>" }).join("") : "<li>Nenhuma mudança ainda.</li>") + "</ol></div>";
      hist.hidden = false;
    }).catch(function () { aviso("Não carregou o histórico") });
  };
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && !hist.hidden) hist.hidden = true });

  crypto.subtle.digest("SHA-256", Uint8Array.from(atob(g), function (c) { return c.charCodeAt(0) })).then(function (b) {
    TOKEN = hx(b); return api("GET");
  }).then(function (d) { BASE = Object.assign({ edits: {}, novos: {}, ordem: {}, blocos: {}, resp: {} }, d); document.body.appendChild(bar); document.body.appendChild(hist); document.body.appendChild(msg); render(); document.dispatchEvent(new Event("tv-editado")) }).catch(function () {});
})();
