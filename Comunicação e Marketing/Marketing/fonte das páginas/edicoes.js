// Edições da Central: guarda no KV o que o time muda nas páginas.
// Só aceita quem já passou pela senha: o navegador manda o SHA-256 da chave da trava.
const json = (d, s = 200) => new Response(JSON.stringify(d), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const curto = (x, n) => String(x ?? "").slice(0, n);

export async function onRequest({ request, env }) {
  if (request.headers.get("x-tivio") !== env.TOKEN) return json({ erro: "sem acesso" }, 401);
  const url = new URL(request.url);
  if (request.method === "GET") {
    if (url.searchParams.get("historico")) return json((await env.EDICOES.get("log", "json")) || []);
    const p = curto(url.searchParams.get("p"), 80);
    return json((await env.EDICOES.get("ed:" + p, "json")) || { edits: {}, novos: {} });
  }
  if (request.method !== "POST") return json({ erro: "método" }, 405);
  const b = await request.json().catch(() => null);
  if (!b || !b.p || !b.tipo) return json({ erro: "pedido" }, 400);
  const p = curto(b.p, 80), quem = curto(b.quem || "Sem nome", 60), quando = new Date().toISOString(), texto = curto(b.texto, 2000);
  const d = (await env.EDICOES.get("ed:" + p, "json")) || { edits: {}, novos: {} };
  if (b.tipo === "editar" || b.tipo === "remover") {
    d.edits[curto(b.chave, 120)] = { t: b.tipo === "remover" ? null : texto, antes: curto(b.antes, 2000), quem, quando };
  } else if (b.tipo === "restaurar") {
    delete d.edits[curto(b.chave, 120)];
  } else if (b.tipo === "novo") {
    const pai = curto(b.pai, 120); (d.novos[pai] = d.novos[pai] || []).push({ id: crypto.randomUUID(), t: texto, quem, quando });
  } else if (b.tipo === "mudar-novo" || b.tipo === "apagar-novo") {
    const l = d.novos[curto(b.pai, 120)] || []; const i = l.findIndex(x => x.id === b.id);
    if (i < 0) return json({ erro: "item" }, 404);
    if (b.tipo === "apagar-novo") l.splice(i, 1); else Object.assign(l[i], { t: texto, quem, quando });
  } else return json({ erro: "tipo" }, 400);
  await env.EDICOES.put("ed:" + p, JSON.stringify(d));
  const log = (await env.EDICOES.get("log", "json")) || [];
  log.unshift({ p, tipo: b.tipo, texto: b.tipo === "remover" ? curto(b.antes, 300) : curto(texto, 300), antes: curto(b.antes, 300), quem, quando });
  await env.EDICOES.put("log", JSON.stringify(log.slice(0, 500)));
  return json(d);
}
