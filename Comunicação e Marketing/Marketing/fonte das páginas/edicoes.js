// Edições da Central: guarda no KV o que o time muda nas páginas.
// Só aceita quem já passou pela senha: o navegador manda o SHA-256 da chave da trava.
const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const curto = (x, n) => String(x ?? "").slice(0, n);
const vazio = () => ({ edits: {}, novos: {}, ordem: {}, blocos: {} });

// Mesma regra do editar.js: cada mudança aplicada sobre o estado da página.
function aplica(d, o, quem, quando) {
  d.ordem = d.ordem || {}; d.blocos = d.blocos || {};
  const t = curto(o.texto, 2000);
  if (o.tipo === "editar" || o.tipo === "remover") d.edits[curto(o.chave, 120)] = { t: o.tipo === "remover" ? null : t, antes: curto(o.antes, 2000), quem, quando };
  else if (o.tipo === "restaurar") delete d.edits[curto(o.chave, 120)];
  else if (o.tipo === "novo") { const pai = curto(o.pai, 120); (d.novos[pai] = d.novos[pai] || []).push({ id: curto(o.id, 60) || crypto.randomUUID(), t, quem, quando }); }
  else if (o.tipo === "mudar-novo" || o.tipo === "apagar-novo") {
    for (const l of Object.values(d.novos)) { const i = l.findIndex(x => x.id === o.id); if (i < 0) continue; if (o.tipo === "apagar-novo") l.splice(i, 1); else Object.assign(l[i], { t, quem, quando }); break; }
  } else if (o.tipo === "novo-bloco") { const c = curto(o.cont, 120); (d.blocos[c] = d.blocos[c] || []).push({ id: curto(o.id, 60) || crypto.randomUUID(), titulo: t, dono: curto(o.dono, 300), quem, quando });
  } else if (o.tipo === "mudar-bloco" || o.tipo === "apagar-bloco") {
    for (const l of Object.values(d.blocos)) { const i = l.findIndex(x => x.id === o.id); if (i < 0) continue; if (o.tipo === "apagar-bloco") l.splice(i, 1); else l[i][o.campo === "dono" ? "dono" : "titulo"] = t; break; }
  } else if (o.tipo === "ordem") { for (const [k, v] of Object.entries(o.listas || {})) d.ordem[curto(k, 120)] = (Array.isArray(v) ? v : []).slice(0, 300).map(x => curto(x, 140)); }
  else return false;
  return true;
}

export async function onRequest({ request, env }) {
  if (request.headers.get("x-tivio") !== env.TOKEN) return json({ erro: "sem acesso" }, 401);
  const url = new URL(request.url);
  if (request.method === "GET") {
    if (url.searchParams.get("historico")) return json((await env.EDICOES.get("log", "json")) || []);
    return json((await env.EDICOES.get("ed:" + curto(url.searchParams.get("p"), 80), "json")) || vazio());
  }
  if (request.method !== "POST") return json({ erro: "método" }, 405);
  const b = await request.json().catch(() => null);
  const ops = b && (Array.isArray(b.ops) ? b.ops : b.tipo ? [b] : null);
  if (!b || !b.p || !ops || !ops.length) return json({ erro: "pedido" }, 400);
  const p = curto(b.p, 80), quem = curto(b.quem || "Sem nome", 60), quando = new Date().toISOString();
  const d = Object.assign(vazio(), (await env.EDICOES.get("ed:" + p, "json")) || {});
  const log = (await env.EDICOES.get("log", "json")) || [];
  for (const o of ops.slice(0, 200)) {
    if (!aplica(d, o, quem, quando)) continue;
    if (o.tipo !== "ordem") log.unshift({ p, tipo: o.tipo, texto: curto(o.tipo === "remover" ? o.antes : o.texto, 300), antes: curto(o.antes, 300), quem, quando });
  }
  if (ops.some(o => o.tipo === "ordem")) log.unshift({ p, tipo: "ordem", texto: "Reorganizou itens", quem, quando });
  await env.EDICOES.put("ed:" + p, JSON.stringify(d));
  await env.EDICOES.put("log", JSON.stringify(log.slice(0, 500)));
  return json(d);
}
