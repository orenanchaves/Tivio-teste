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
    var nos = function (raiz) { return raiz ? [].filter.call(raiz.querySelectorAll(".org-n"), vis).map(function (x) { return { b: t(x.querySelector("b")), s: t(x.querySelector("em")) || t(x.querySelector("span")) } }) : [] };
    var hoje = nos(F && F.querySelector(".org")), novo = nos(N && N.querySelector(".org"));
    if (hoje.length && novo.length) {
      var topo = novo.slice(0, 2), nomesH = hoje.map(function (x) { return x.b }), nomesN = novo.map(function (x) { return x.b });
      var linha = hoje.slice(2).map(function (x) { return [x, nomesN.indexOf(x.b) >= 0 ? "fica" : "sai"] }).concat(novo.slice(2).filter(function (x) { return nomesH.indexOf(x.b) < 0 }).map(function (x) { return [x, "entra"] }));
      // valores: a agência sai com o custo de hoje; quem entra mostra a sua parte da diluição
      var cuN = N && N.querySelector(".cu"), kN = N ? [].slice.call(N.querySelectorAll("#custo ~ .kpis .kpi b")).map(t) : [];
      var vals = cuN ? [].map.call(cuN.querySelectorAll(".cu-i"), function (x) { return [t(x.querySelector("span")), t(x.querySelector("b"))] }) : [];  // já vem com "aprox."
      var valor = function (x, c) {
        if (c === "sai") return kN[0] ? kN[0] + " por mês" : "";
        var v = vals.filter(function (y) { return y[0].indexOf(x.b) >= 0 })[0]; return v ? v[1] : "";
      };
      var ne = 0, no = function (x, c) { var v = c === "topo" ? "" : valor(x, c); return '<div class="og-n og-' + c + '"' + (c === "entra" ? ' style="--d:' + (0.22 * ne++) + 's"' : "") + "><span>" + esc(x.s) + "</span><b>" + esc(x.b) + "</b>" + (v ? '<small class="og-r">' + esc(v) + "</small>" : "") + "</div>" };
      var livre = vals.filter(function (y) { return /^livre/i.test(y[0]) })[0];
      S.push({ sec: "Estrutura", h: "Como a área <strong>muda</strong>", html: '<div class="og"><div class="og-tg" role="group" aria-label="Estrutura"><button type="button" data-og="0" aria-pressed="true">Atual</button><button type="button" data-og="1" aria-pressed="false">Em 2027</button></div>' + no(topo[0], "topo") + '<i class="og-v"></i>' + no(topo[1], "topo") + '<i class="og-v"></i><div class="og-row og-r1">' + linha.filter(function (x) { return x[1] === "fica" }).map(function (x) { return no(x[0], x[1]) }).join("") + '</div><i class="og-v og-v2"></i><div class="og-row og-r2">' + linha.filter(function (x) { return x[1] !== "fica" }).map(function (x) { return no(x[0], x[1]) }).join("") + "</div>" + (kN[1] ? '<p class="og-nota"><b>' + esc(kN[0] || "") + "</b> por mês da agência viram <b>" + esc(kN[1]) + "</b> nas pessoas e ferramentas" + (livre ? ", e <b>" + esc(livre[1]) + "</b> ficam livres" : "") + "</p>" : "") + "</div>" });
      if (!window.__tvOg) { window.__tvOg = 1; document.addEventListener("click", function (ev) { var b = ev.target.closest && ev.target.closest(".og-tg button"); if (!b) return; ev.stopPropagation(); var og = b.closest(".og"), on = b.dataset.og === "1"; og.classList.toggle("og-27", on); [].forEach.call(og.querySelectorAll(".og-tg button"), function (x) { x.setAttribute("aria-pressed", String(x === b)) }) }, true) }
    }
    var cu = N && N.querySelector(".cu");
    if (cu) {
      var ks = [].slice.call(N.querySelectorAll("#custo ~ .kpis .kpi")).slice(0, 4);
      var conta = function (txt) { var m = txt.match(/^R\$ ([\d.]+)( mil)?$/); return m ? ' data-conta="' + m[1].replace(/\./g, "") + '" data-suf="' + (m[2] || "") + '"' : "" };
      // hoje: uma barra só da agência; 2027: a mesma barra dividida, com chave em cima e legenda alinhada embaixo
      var seg = [].slice.call(cu.querySelectorAll(".cu-bar i")), its = [].slice.call(cu.querySelectorAll(".cu-i"));
      var pc = function (x) { return parseFloat(x.getAttribute("style").replace(/[^\d.]/g, "")) || 0 };
      var usa = seg.filter(function (x) { return !x.classList.contains("cu-5") }).reduce(function (a, x) { return a + pc(x) }, 0);
      var kt = function (n) { var b = ks[n] ? t(ks[n].querySelector("b")) : ""; return "<b" + conta(b) + ">" + esc(b) + "</b> " + esc(ks[n] ? t(ks[n].querySelector("span")) : "") };
      var item = function (x) { var b = t(x.querySelector("b")).replace(/^aprox\. /, ""), ap = !x.querySelector("i.cu-5"); return '<div class="cu-i"><i class="' + x.querySelector("i").className + '"></i><span>' + esc(t(x.querySelector("span"))) + "</span>" + (ap ? '<small class="cu-ap">aprox.</small>' : "") + "<b" + conta(b) + ">" + esc(b) + "</b></div>" };
      var livre = its.filter(function (x) { return x.querySelector("i.cu-5") }), pagos = its.filter(function (x) { return !x.querySelector("i.cu-5") });
      S.push({ sec: "Estrutura", h: "O custo da agência, <strong>diluído</strong>", html: '<div class="sl-cu2">'
        + '<div class="cu-lin cu-hoje"><p class="cu-rot">Hoje</p><div class="cu-barra"><i class="cu-ag2"><b>Agência</b><span>' + kt(0) + "</span></i></div></div>"
        + '<div class="cu-lin cu-novo"><p class="cu-rot">Em 2027</p><div class="cu-col">'
        + '<div class="cu-chave"><div style="width:' + usa + '%"><p>' + kt(1) + '</p></div><div style="width:' + (100 - usa) + '%"><p>' + kt(2) + "</p></div></div>"
        + '<div class="cu-barra">' + seg.map(function (x) { return '<i class="' + x.className + '" style="width:' + pc(x) + '%"></i>' }).join("") + "</div>"
        + '<div class="cu-leg"><div style="width:' + usa + '%">' + pagos.map(item).join("") + '</div><div style="width:' + (100 - usa) + '%">' + livre.map(item).join("") + "</div></div>"
        + "</div></div>"
        + '<p class="cu-tot">' + kt(3) + "</p></div>" });
    }
    // logo depois da estrutura: o que queremos para o ano, uma meta por frente
    var qf = N ? [].slice.call(N.querySelectorAll(".fr-vis>section.frente")).filter(vis) : [];
    if (qf.length) S.push({ sec: "2027", h: "O que queremos <strong>em 2027</strong>", html: '<div class="quer"><p class="quer-f">Ser a <strong>casa de estruturados</strong> do mercado: quem explica o risco, com dado próprio e presença constante.</p><div class="sl-g c4 cmp">'
      + qf.map(function (f) { return "<div><b>" + esc(t(f.querySelector("h3")).replace(" com estratégia", "")) + "</b><span>" + esc(t(f.querySelector(".fr-m"))) + "</span></div>" }).join("") + "</div></div>" });
    var te = N ? blocos(N.querySelector(".teses")) : [];
    // por que: três teses por slide, cada uma com o que quer dizer, o que vimos e o que puxamos
    var tese = function (f, n) { var tg = function (c) { return t(f.querySelector(c)) }; return '<div class="ts" style="--n:' + n + '"><p class="ts-n">' + String(n + 1).padStart(2, "0") + "</p><h3>" + esc(tg("h3")) + '</h3><p class="ts-q">' + esc(tg(".tes-q")) + '</p><p class="ts-r">O que vimos</p><p class="ts-v">' + esc(tg(".dono")) + '</p><p class="ts-r ts-f">Por isso puxamos</p><ul>' + itens(f.querySelector("ul"), 3) + "</ul></div>" };
    // "Por que o plano é assim" saiu da apresentação (continua na página do Plano)
    var fe = blocos(F && F.querySelector(".frentes"));
    if (fe.length) S.push({ sec: "Até o fim do ano", h: "O que <strong>fechar</strong>", html: '<div class="sl-g c3 cmp">' + fe.map(function (f) { return card(f, 5) }).join("") + "</div>" });
    var nd = blocos(F && F.querySelector(".fr-nd"));
    if (nd.length) S.push({ sec: "Até o fim do ano", h: "O que já começa <strong>nas frentes</strong>", html: '<div class="sl-g c4 cmp">' + nd.map(function (f) { return card(f, 5) }).join("") + "</div>" });
    S.push({ sec: "Até o fim do ano", h: "Como o AutomaTivio <strong>funciona</strong>", html: '<div class="at"><div class="at-fluxo"><div class="at-col at-in"><p class="at-t">Entra</p><div class="at-c" style="--i:0"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4M10 12h5M10 16h5"/></svg><div><b>Comentários da Gestão</b><span>um texto por fundo</span></div></div><div class="at-c" style="--i:1"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M4 10h16M4 15h16M10 4v16"/></svg><div><b>Dados mensais</b><span>a planilha do mês</span></div></div></div><div class="at-lig at-l1"><i></i><i></i><i></i></div><div class="at-core"><span class="at-gira"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/></svg></span><b>AutomaTivio</b><code>python run.py</code><div class="at-prog"><i></i></div><small>um comando, os mesmos números em tudo</small></div><div class="at-lig at-l2"><i></i><i></i><i></i></div><div class="at-col at-out"><p class="at-t">Sai pronto</p><div class="at-c" style="--i:0"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 3h10v18H7z"/><path d="M10 15v2M13 12v5M16 9v8"/></svg><div><b>Relatórios de gestão</b><span>HTML, PDF e PPTX</span></div></div><div class="at-c" style="--i:1"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M12 16v4M8 20h8"/></svg><div><b>Decks</b><span>números trocados no modelo</span></div></div><div class="at-c" style="--i:2"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="4"/><circle cx="12" cy="12" r="3.5"/><path d="M16.5 7.5h.01"/></svg><div><b>Posts</b><span>por vertical</span></div></div><div class="at-c" style="--i:3"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg><div><b>E-mail</b><span>da edição do mês</span></div></div></div></div><div class="at-st"><div><b>84 arquivos</b><span>na rodada de setembro, em cerca de 10 minutos</span></div><div><b>0 erros</b><span>18 avisos conhecidos no log</span></div><div><b>Em 2027</b><span>Crédito e Investment Solutions totalmente automatizados; a partir de janeiro, o imobiliário</span></div></div></div>' });
    var fr = N ? blocos(N.querySelector(".fr-vis")) : [];
    if (fr.length) S.push({ sec: "2027", h: "O ano em <strong>quatro frentes</strong>", html: '<div class="sl-g c4 cmp">' + fr.map(function (f) { var im = f.querySelector(".fr-img"); return "<div>" + (im ? '<img class="th" src="' + im.getAttribute("src") + '" alt="">' : "") + "<b>" + esc(t(f.querySelector("h3")).replace(" com estratégia", "")) + "</b><span>" + esc(t(f.querySelector(".fr-m"))) + "</span><span><em>" + esc(t(f.querySelector(".dono"))) + "</em></span></div>" }).join("") + "</div>" });
    // depois do resumo, um slide por frente: imagem, meta, dono, o que fazemos e em que meses
    var meses = N ? [].slice.call(N.querySelectorAll("#meses section.tl-m")) : [];
    fr.forEach(function (f, k) {
      var im = f.querySelector(".fr-img"), nome = t(f.querySelector("h3")).replace(" com estratégia", "");
      var tira = meses.map(function (m) { var i = m.querySelector('.tl-i[data-c="' + (k + 1) + '"] span'); return '<i class="' + (i ? "on" : "") + '"' + (i ? ' title="' + esc(t(i)) + '"' : "") + "><b>" + esc(t(m.querySelector("h3")).slice(0, 3)) + "</b></i>" }).join("");
      S.push({ fora: 1, sec: "2027 · Frente " + String(k + 1).padStart(2, "0"), h: esc(nome), html: '<div class="fx">' + (im ? '<figure class="fx-im"><img src="' + im.getAttribute("src") + '" alt=""></figure>' : "")
        + '<div class="fx-t"><p class="fx-m">' + esc(t(f.querySelector(".fr-m"))) + '</p><p class="fx-d">' + esc(t(f.querySelector(".dono"))) + '</p>' + (t(f.querySelector(".fr-x")) ? '<p class="fx-x">' + esc(t(f.querySelector(".fr-x"))) + "</p>" : "") + '<ol class="fx-l">' + [].filter.call(f.querySelectorAll("ul>li"), function (li) { return !li.hidden && t(li) }).slice(0, 5).map(function (li) { var ex = li.querySelector(".fr-ex"), c = li.cloneNode(true); [].forEach.call(c.querySelectorAll(".fr-ex,.ed-x,.ed-g,.ed-r"), function (x) { x.remove() }); return "<li><div>" + esc(t(c)) + (ex ? "<small>" + esc(t(ex)) + "</small>" : "") + "</div></li>" }).join("") + "</ol>"
        + (meses.length ? '<div class="fx-tira" aria-label="Meses com entrega">' + tira + "</div>" : "") + "</div></div>" });
    });
    // gráfico: posts por mês de cada segmento
    var sg = N ? [].filter.call(N.querySelectorAll(".seg6>.sub"), vis) : [];
    if (sg.length) {
      var ps = sg.map(function (x) { var m = t(x.querySelector("em")).match(/(\d+) posts/); return m ? +m[1] : 0 }), mx = Math.max.apply(null, ps.concat([1]));
      S.push({ sec: "2027", h: "Cada segmento em <strong>uma linha</strong>", html: '<div class="sl-g c3 cmp seg">' + sg.map(function (x, k) {
        return "<div><b>" + esc(t(x.querySelector("b"))) + "</b><span>" + esc(t(x.querySelector("span"))) + '</span><div class="gb"><i style="--w:' + Math.round(ps[k] / mx * 100) + '%"></i><em>' + (ps[k] ? ps[k] + " posts por mês" : esc(t(x.querySelector("em")))) + "</em></div></div>";
      }).join("") + "</div>" });
    }

    // linha do tempo: as quatro frentes em raias, os trimestres em colunas, com o ícone de cada frente
    var mT = N ? [].slice.call(N.querySelectorAll("#meses .tl-m")).filter(function (m) { return !/nov e dez/i.test(t(m.querySelector("h3"))) }) : [];
    if (mT.length) {
      var raias = [1, 2, 3, 4].map(function (c) {
        var ex = N.querySelector('#meses .tl-i[data-c="' + c + '"]'), ic = ex && ex.querySelector("svg") ? ex.querySelector("svg").outerHTML : "", nm = ex ? t(ex.querySelector("b")) : "";
        var tri = [0, 1, 2, 3].map(function (q) { var l = []; mT.slice(q * 3, q * 3 + 3).forEach(function (m) { var s = m.querySelector('.tl-i[data-c="' + c + '"] span'); if (s) t(s).split("; ").forEach(function (x) { x = x.replace(/^\d+ eventos?: /, "Itaú: "); if (x && l.length < 3 && !/^Carta do Gestor$/.test(x)) l.push(x) }) }); return l });
        return { ic: ic, nm: nm, tri: tri };
      });
      S.push({ sec: "2027", h: "A linha do tempo <strong>de 2027</strong>", html: '<div class="lt"><div class="lt-h"><span></span>' + ["1º tri", "2º tri", "3º tri", "4º tri"].map(function (x, q) { return '<b style="--q:' + q + '">' + x + "<i></i></b>" }).join("") + "</div>"
        + raias.map(function (r, n) { return '<div class="lt-r" style="--n:' + n + '"><p class="lt-f">' + r.ic + "<span>" + esc(r.nm) + "</span></p>" + r.tri.map(function (l, q) { return '<ul style="--q:' + q + '">' + l.map(function (x) { return "<li>" + esc(x.charAt(0).toUpperCase() + x.slice(1)) + "</li>" }).join("") + "</ul>" }).join("") + "</div>" }).join("") + "</div>" });
    }
    // gráfico: eventos Itaú mês a mês, lidos da linha do tempo
    var ms = N ? [].slice.call(N.querySelectorAll("#meses .tl-m")).filter(function (m) { return !/nov e dez/i.test(t(m.querySelector("h3"))) }) : [];
    var ev = ms.map(function (m) { var e = m.querySelector('.tl-i[data-c="2"] span'), q = e && t(e).match(/^(\d+) eventos?/); return [t(m.querySelector("h3")).slice(0, 3), q ? +q[1] : 0] });
    var tot = ev.reduce(function (s, x) { return s + x[1] }, 0);
    // gráfico: caminho do número e metas das redes (hoje até a meta)
    var fu = N ? [].slice.call(N.querySelectorAll(".fu-i")) : [], mt = N ? [].slice.call(N.querySelectorAll(".mt-r")) : [];
    var ETAPA = [["Impressões, visitas ao site e novos seguidores", "Painel mensal das redes e do site", "Saber se o conteúdo chega ao assessor e ao investidor certo"],
      ["Formulários das landings, inscrições de evento e newsletter", "Formulário que guarda a origem: post, campanha ou evento", "Saber qual ação traz gente de verdade, e não só curtida"],
      ["Pedidos de conversa que o comercial aceita", "Repasse ao comercial em até 2 dias, com o histórico do contato", "Medir se o contato vira oportunidade"],
      ["Aplicações dos contatos em até 90 dias, em R$", "Cruzamento mensal com o comercial", "Mostrar quanto o marketing trouxe de dinheiro"]];
    if (fu.length) S.push({ sec: "2027", h: "Como vamos <strong>medir</strong>", html: '<p class="med-lead">Cada pessoa passa por quatro etapas. Todo mês, no painel, contamos quantas chegaram a cada uma.</p><div class="fn"><div class="fn-h"><span></span><b>O que conta</b><b>Onde medimos</b><b>Para que serve</b></div>'
      + fu.map(function (x, k) { var e = ETAPA[k] || ["", "", ""]; return '<div class="fn-r" style="--k:' + k + '"><p class="fn-e" style="--w:' + (100 - k * 13) + '%"><b>' + esc(t(x.querySelector("b"))) + "</b><span>" + esc(t(x.querySelector("span"))) + "</span></p><p>" + e[0] + "</p><p>" + e[1] + "</p><p>" + e[2] + "</p></div>" }).join("") + "</div>" });
    if (mt.length) S.push({ sec: "2027", fora: 1, h: "Metas das redes <strong>até dez/27</strong>", html: '<div class="sl-med met-2"><div class="met met-so"><b class="met-t">De hoje até a meta</b>' + mt.slice(0, 7).map(function (x) {
      var e = t(x.querySelector("em")).split(" a "), h0 = num(e[0]), m1 = num(e[1]); var pc = h0 !== null && m1 ? Math.min(100, Math.round(h0 / m1 * 100)) : 0;
      return '<div><span>' + esc(t(x.querySelector("span"))) + '</span><i style="--w:' + pc + '%"></i><em>' + esc(e[0]) + " → <strong>" + esc(e[1] || "") + "</strong></em></div>";
    }).join("") + '</div></div><p class="sl-nota">Proposta do time de Comunicação &amp; Marketing, a validar.</p>' });
    // resumo de tudo
    var rs = [];
    var kR = N ? [].slice.call(N.querySelectorAll("#custo ~ .kpis .kpi b")).map(t) : [];
    if (kR[1]) rs.push(["Estrutura", "A agência sai. " + kR[1] + " por mês vão para pessoas e ferramentas" + (kR[2] ? " e " + kR[2] + " ficam livres" : "")]);
    (N ? [].slice.call(N.querySelectorAll(".fr-vis>section.frente")).filter(vis) : []).forEach(function (f) { rs.push([t(f.querySelector("h3")).replace(" com estratégia", ""), t(f.querySelector(".fr-m"))]) });
    if (fu.length) rs.push(["Medir", fu.map(function (x) { return t(x.querySelector("b")) }).join(", ") + ", todo mês no painel"]);
    if (rs.length) S.push({ sec: "Resumo", h: "Em <strong>resumo</strong>", html: '<div class="rs">' + rs.map(function (x, n) { return '<div style="--n:' + n + '"><b>' + esc(x[0]) + "</b><span>" + esc(x[1]) + "</span></div>" }).join("") + "</div>" });
    S.push({ capa: true, h: "Casa de <strong>estruturados</strong>", html: '<p class="sl-l">Menos, com mais qualidade.</p>' });
    return S;
  });
})();
