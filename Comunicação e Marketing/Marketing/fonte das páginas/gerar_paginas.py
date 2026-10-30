# -*- coding: utf-8 -*-
# Executado no fim do montar.py: uma página por peer, por segmento da Tivio e por setor.
exec(ler("dados_peers.py"))
EXTRA = SAIDA / "extra"
EXTRA.mkdir(exist_ok=True)
CSS_P = ler("mkt.css") + "\n" + ler("paginas.css")
SETA_E = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 6-6 6 6 6"/></svg>'
SETA_D = SETA_E.replace("m15 6-6 6 6 6", "m9 6 6 6-6 6")

def navegar(lista, i, volta, volta_txt):
    """Setas para a anterior e a próxima da mesma lista, e o caminho de volta."""
    a_arq, a_nome = lista[i - 1]
    p_arq, p_nome = lista[(i + 1) % len(lista)]
    return (f'<nav class="passa" aria-label="Navegar"><a class="passa-seta" href="{a_arq}">{SETA_E}<span>{a_nome}</span></a>'
            f'<a class="passa-volta" href="{volta}">{volta_txt}</a>'
            f'<a class="passa-seta dir" href="{p_arq}"><span>{p_nome}</span>{SETA_D}</a></nav>')

def escreve(arq, titulo, area, corpo):
    (EXTRA / arq).write_text(pagina(titulo, cabecalho(area, []) + corpo, CSS_P), encoding="utf-8")

# ---- peers
lista = [(f'peer-{p["slug"]}.html', p["nome"]) for p in PEERS]
for i, p in enumerate(PEERS):
    k = "".join(f'<div class="kpi vidro"><span>{a}</span><b>{b}</b></div>' for a, b in p["kpis"])
    blocos = [("Em estruturados", p["estr"]), ("Site", p["site"]), ("Redes e porta-vozes", p["redes"]), ("Conteúdo próprio", p["conteudo"])]
    cards = "".join(f'<section class="vidro bloco"><h2>{t}</h2><p>{x}</p></section>' for t, x in blocos)
    fontes = "".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in p["fontes"])
    nome_g = "Peers no Brasil" if p["grupo"] == "Brasil" else "Peers no exterior"
    ancora = "peers" if p["grupo"] == "Brasil" else "estrangeiras"
    corpo = f'''<div class="wrap">{navegar(lista, i, f"marketing.html#{ancora}", nome_g)}
<section class="topo-peer">{logo(p["nome"])}<div><p class="eyebrow"><i></i>{nome_g}</p><h1>{p["nome"]}</h1><p class="lead">{p["frase"]}</p></div></section>
<div class="kpis peer">{k}</div>
<section class="destaque vidro"><p class="seg-nome"><i></i>O que faz muito bem</p><p class="grande">{p["bem"]}</p></section>
<div class="blocos">{cards}</div>
<section class="destaque aprende vidro"><p class="seg-nome"><i></i>O que a Tivio pode aprender</p><p class="grande">{p["aprender"]}</p></section>
<p class="fontes-peer"><b>Fontes</b>{fontes}</p>
<p class="rodape">Fontes públicas, lidas em 30/10/2026. Sugestões para validar com Riscos.</p></div>'''
    escreve(f'peer-{p["slug"]}.html', p["nome"], "Peers", corpo)

# ---- segmentos da Tivio: o plano de posts e o que vem do AutomaTivio
base_m = ler("mkt_corpo.html")
base_s = ler("segmentos.html")
lista = [(f"segmento-{s}.html", n) for _, s, n in SEGMENTOS]
for i, (k, s, n) in enumerate(SEGMENTOS):
    plano = re.search(rf'<section class="plano vidro" id="pl-{k}".*?</section>', base_m, re.S).group(0)
    plano = plano.replace(" hidden", "", 1).replace('role="tabpanel"', "")
    cartao = re.search(rf'<article class="seg vidro">\s*<p class="seg-nome"><i></i>{re.escape(n)}</p>.*?</article>', base_s, re.S)
    auto = f'<h2>No <strong>AutomaTivio</strong></h2><div class="segmentos um">{cartao.group(0)}</div>' if cartao else ""
    corpo = f'''<div class="wrap">{navegar(lista, i, "marketing.html#posts", "Plano de posts")}
<section class="topo-peer"><div><p class="eyebrow"><i></i>Segmento da Tivio</p><h1>{n}</h1></div></section>
{plano}{auto}
<p class="rodape">Plano em construção, para validar com o time e com Riscos.</p></div>'''
    escreve(f"segmento-{s}.html", n, "Segmentos", corpo)

# ---- setores: as fichas de cada case, tiradas das tabelas da Central
html_tab = ler("mkt_peers.html") + ler("mkt_mundo.html")
linhas = {}
for t in re.findall(r'<table>.*?</table>', html_tab, re.S):
    trs = re.findall(r"<tr[^>]*>.*?</tr>", t, re.S)
    cab = _celulas(trs[0])
    if "Case" not in cab:
        continue
    c_i = cab.index("Case")
    for tr in trs[1:]:
        c = _celulas(tr)
        linhas[c[c_i]] = (cab, c, c_i)
lista = [(f"setor-{s}.html", n) for s, n, _, _ in SETORES]
for i, (s, n, frase, cases) in enumerate(SETORES):
    fs = []
    for nome in cases:
        cab, c, c_i = linhas[nome]
        dl = "".join(f"<dt>{cab[j]}</dt><dd>{c[j]}</dd>" for j in range(len(c)) if j != c_i and cab[j] != "Setor")
        url = _url.get(nome)
        link = f'<a class="ver-site" href="{url}" target="_blank" rel="noopener">Ver o original</a>' if url else ""
        fs.append(f'<article class="ficha vidro"><header>{logo(nome)}<span><b>{nome}</b></span></header><dl>{dl}</dl>{link}</article>')
    corpo = f'''<div class="wrap">{navegar(lista, i, "marketing.html#setores", "Outros setores")}
<section class="topo-peer"><div><p class="eyebrow"><i></i>Outros mercados</p><h1>{n}</h1><p class="lead">{frase}</p></div></section>
<div class="fichas setor">{"".join(fs)}</div>
<p class="rodape">Fontes públicas, lidas em 30/10/2026. Sugestões para validar com Riscos.</p></div>'''
    escreve(f"setor-{s}.html", n, "Setores", corpo)
print("extras:", len(list(EXTRA.glob("*.html"))))
