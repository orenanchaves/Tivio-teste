"""Monta as páginas da Tivio (AutomaTivio e Central de Marketing) para publicar como Artifact.
Visual da Central de Materiais: tokens de AutomaTivio/templates/estilos/_marca.css."""
import base64, re, pathlib, sys

RAIZ = pathlib.Path(sys.argv[1])
SAIDA = pathlib.Path(__file__).parent
FONTES = RAIZ / "AutomaTivio/assets/fontes"
LOGO = (RAIZ / "AutomaTivio/assets/marca/tivio.svg").read_text(encoding="utf-8")
LOGO = LOGO.replace('class="tv-brand"', 'class="logo" role="img" aria-label="Tivio Capital"')

def ler(nome):
    return (SAIDA / nome).read_text(encoding="utf-8")

def face(peso, arq):
    b = base64.b64encode((FONTES / arq).read_bytes()).decode()
    return f'@font-face{{font-family:Versos;font-weight:{peso};font-display:swap;src:url(data:font/woff2;base64,{b}) format("woff2")}}'

FACES = "\n".join([face(300, "Versos-ExtraLight.woff2"), face(400, "Versos-Regular.woff2"),
                   face(600, "Versos-SemiBold.woff2"), face(700, "Versos-Bold.woff2")])

T3D = "data:image/webp;base64," + base64.b64encode((SAIDA / "t3d.webp").read_bytes()).decode()
T3D_HTML = f'<div class="t3d" id="t3d"><img src="{T3D}" alt="" width="640" height="563"></div>'
T3D_JS = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>\n'
          '<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/SVGLoader.js"></script>\n'
          + "<script>\n" + ler("t3d.js") + "</script>\n")

BASE_CSS = ler("base.css")
BASE_JS = ler("base.js")

def hero(eyebrow, titulo, texto):
    return (f'<section class="hero"><div><p class="eyebrow"><i></i>{eyebrow}</p><h1>{titulo}</h1>'
            f'<p class="lead">{texto}</p></div>{T3D_HTML}</section>')

def cabecalho(area, abas, global_menu=True):
    links = "".join(f'<a href="{i if i.endswith(".html") else "#" + i}">{t}</a>' for i, t in abas)
    nome_area = f'<span class="area-nome">{area}</span>' if area else ""
    seta = lambda d, p: f'<button type="button" class="seta" data-dir="{d}" aria-label="{"Voltar" if d < 0 else "Avançar"} no menu"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="{p}"/></svg></button>'
    if global_menu:
        return barra_global()
    menu = (f'<div class="menu">{seta(-1, "m15 6-6 6 6 6")}<nav class="chips" aria-label="Seções">{links}</nav>{seta(1, "m9 6 6 6-6 6")}</div>'
            if abas else '<div class="menu"></div>')
    return f'''<header class="barra"><div class="barra-in">
<a class="marca" href="index.html" aria-label="Comunicação &amp; Marketing">{LOGO}{nome_area}</a>
{menu}
<div class="tema" role="group" aria-label="Tema">
<button type="button" data-tema="light" aria-label="Tema claro"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button>
<button type="button" data-tema="dark" aria-label="Tema escuro"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg></button>
</div></div></header>'''

TEMA_HTML = '''<div class="tema" role="group" aria-label="Tema">
<button type="button" data-tema="light" aria-label="Tema claro"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button>
<button type="button" data-tema="dark" aria-label="Tema escuro"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg></button>
</div>'''
SETA_DD = '<svg class="dd-seta" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>'

def barra_global():
    def dd(nome, itens, grande=False):
        links = "".join(f'<a href="{h}">{t}</a>' if h else f'<p class="dd-tit">{t}</p>' for h, t in itens)
        return f'<details class="dd"><summary>{nome}{SETA_DD}</summary><div class="dd-painel{" grande" if grande else ""}">{links}</div></details>'
    peers = [("", "Brasil")] + [(f'peer-{p["slug"]}.html', p["nome"]) for p in PEERS if p["grupo"] == "Brasil"]
    peers += [("", "Exterior")] + [(f'peer-{p["slug"]}.html', p["nome"]) for p in PEERS if p["grupo"] != "Brasil"]
    segs = [(f"segmento-{s}.html", n) for _, s, n in SEGMENTOS] + [("segmento-imobiliario.html", "Imobiliário")]
    pubs = [("publico-assessor.html", "Assessor"), ("publico-gerente.html", "Gerente"), ("publico-institucional.html", "Institucional"),
            ("publico-originador.html", "Originador"), ("publico-universitario.html", "Universitário"), ("publico-investidor.html", "Investidor")]
    nav = "".join([
        '<a class="nav-top" href="estrutura.html">Estrutura</a>',
        dd("Automação", [("frente-automacao.html", "Visão geral"), ("automativio.html", "AutomaTivio"), ("automativio.html#baixar", "Como baixar"), ("", "Times"), ("automativio-gestao.html", "Gestão"), ("automativio-riscos.html", "Riscos"), ("automativio-marketing.html", "Marketing"), ("", "IA"), ("m-copilot.html", "Copilot"), ("metodos-ia.html", "Como usar IA")]),
        dd("Eventos", [("frente-eventos.html", "Visão geral"), ("m-eventos.html", "Eventos Itaú"), ("eventos-mercado.html", "Eventos do mercado"), ("calendario.html", "Calendário 2027")]),
        dd("Conteúdo", [("frente-conteudo.html", "Visão geral"), ("m-posts.html", "Posts"), ("analise-postagens.html", "Análise das postagens"), ("painel-mensal.html", "Painel mensal"), ("imprensa.html", "Imprensa"), ("canal-ofertas.html", "Canal de ofertas")] + [("", "Segmentos")] + segs + [("", "Públicos")] + pubs, True),
        '<a class="nav-top" href="imprensa.html">Imprensa</a>',
        dd("Digital", [("frente-digital.html", "Visão geral"), ("analise-site.html", "Site"), ("frente-digital.html#artigos", "Artigos para o Google"), ("m-captacao.html", "Captação")]),
        dd("Benchmark", [("frente-benchmark.html", "Visão geral"), ("m-peers.html", "Peers no Brasil"), ("m-estrangeiras.html", "Peers no exterior"), ("m-cases.html", "Cases"), ("m-mundo.html", "Mundo"), ("m-mercados.html", "Outros mercados"), ("m-setores.html", "Outros setores"), ("m-relatorio.html", "Relatório 2027")]),
        dd("Base", [("", "Estratégia"), ("visao.html", "Visão"), ("m-posicionamento.html", "Casa de estruturados"), ("m-sintese.html", "O que fazer"), ("m-sugestoes.html", "Sugestões"), ("m-ideias.html", "Ideias na mesa"), ("", "Área"), ("plano-2027.html#fim-do-ano", "Fim de 2026"), ("transicao.html", "Transição"), ("orcamento.html", "Orçamento 2027"), ("brand.html", "Brand"), ("", "Tudo"), ("marketing.html", "Central completa")], True),
    ])
    return f'''<header class="barra"><div class="barra-in">
<a class="marca" href="index.html" aria-label="Comunicação &amp; Marketing">{LOGO}</a>
<button type="button" class="menu-btn" aria-expanded="false" aria-controls="nav-global" aria-label="Menu"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
<nav class="nav-global" id="nav-global" aria-label="Principal">{nav}</nav>
<a class="btn-filtro" href="buscar.html"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/></svg>Pesquisar</a>
<a class="btn-visao" href="plano-2027.html">Plano</a>
{TEMA_HTML}</div></header>'''

_ic = lambda d: f'<svg class="ic-rede" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>'
ICONES = {"LinkedIn": _ic('<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 10v7M8 7v.01M12 17v-4a2.5 2.5 0 0 1 5 0v4M12 10v7"/>'),
          "Instagram": _ic('<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><path d="M17.5 6.5v.01"/>'),
          "YouTube": _ic('<rect x="2.5" y="5" width="19" height="14" rx="4"/><path d="m10 9 5 3-5 3z"/>')}
def com_icones(html):
    for nome, svg in ICONES.items():
        html = html.replace(f">{nome}<", f">{svg}{nome}<")
        html = re.sub(rf"(>(?:seguidores no|inscritos no) ){nome}", lambda x: ">" + svg + x.group(1)[1:] + nome, html)
    return html

def pagina(titulo, corpo, css_extra=""):
    corpo = com_icones(corpo)
    return f"""<title>{titulo}</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex">
<meta name="claude:viewport-fit-sides" content="cover">
<style>
{BASE_CSS}
{css_extra}
{FACES}
</style>
{corpo}
<script>
{BASE_JS}
</script>
{T3D_JS}"""

import json
_idx = json.loads((SAIDA / "logos/indice.json").read_text(encoding="utf-8"))
_url = json.loads(ler("sites.json"))
def logo(nome):
    f = _idx.get(nome)
    if f:
        b = base64.b64encode((SAIDA / "logos" / f).read_bytes()).decode()
        return f'<span class="lg"><img src="data:image/png;base64,{b}" alt="" width="28" height="28"></span>'
    iniciais = "".join(p[0] for p in nome.split()[:2]).upper()
    return f'<span class="lg lg-m">{iniciais}</span>'

def _celulas(tr):
    return re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)

def fichas(html):
    """<div class="tab"> de marcas vira grade de fichas; a primeira coluna (ou Case) é o nome."""
    def troca(mt):
        linhas = re.findall(r"<tr[^>]*>.*?</tr>", mt.group(0), re.S)
        cab = _celulas(linhas[0])
        if cab[0] not in ("Casa", "Case", "Setor"):
            return mt.group(0)
        chave = cab.index("Case") if "Case" in cab else 0
        out = ['<div class="fichas">']
        for tr in linhas[1:]:
            c = _celulas(tr)
            nome = c[chave]
            tag = f'<small>{c[0]}</small>' if chave else ""
            url = _url.get(nome)
            link = f'<a class="ver-site" href="{url}" target="_blank" rel="noopener">Ver o original</a>' if url else ""
            dl = "".join(f"<dt>{cab[i]}</dt><dd>{c[i]}</dd>" for i in range(len(c)) if i != chave and not (chave and i == 0))
            classe = "ficha vidro tv" if 'class="tv"' in tr else "ficha vidro"
            nome_vis = "Tivio" if nome == "Tivio" else nome
            alvo = _paginas.get(nome)
            abre = f'<a class="ver-pagina" href="{alvo}">Abrir página</a>' if alvo else ""
            out.append(f'<article class="{classe}"><header>{logo(nome)}<span><b>{nome_vis}</b>{tag}</span></header><dl>{dl}</dl><div class="ficha-pe">{abre}{link}</div></article>')
        out.append("</div>")
        return "".join(out)
    return re.sub(r'<div class="tab"><table>.*?</table></div>', troca, html, flags=re.S)

def _ic27(d):
    return f'<svg class="ic27" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>'
ICO27 = {"Automação": _ic27('<path d="M4 12a8 8 0 0 1 14-5.3L20 9M20 4v5h-5M20 12a8 8 0 0 1-14 5.3L4 15M4 20v-5h5"/>'),
         "Eventos": _ic27('<rect x="3.5" y="5" width="17" height="15.5" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/>'),
         "Conteúdo": _ic27('<path d="M6 3.5h8l4.5 4.5v12.5H6z"/><path d="M14 3.5V8h4.5M9 12.5h6M9 16h6"/>'),
         "Digital com estratégia": _ic27('<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.4 2.4 3.6 5.2 3.6 8.5s-1.2 6.1-3.6 8.5c-2.4-2.4-3.6-5.2-3.6-8.5s1.2-6.1 3.6-8.5z"/>'),
         "Estrutura": _ic27('<circle cx="9" cy="8" r="3.5"/><path d="M3 20c0-3.5 2.7-6 6-6s6 2.5 6 6M16 4.8a3.5 3.5 0 0 1 0 6.4M18 14.4c1.9.8 3 2.8 3 5.6"/>'),
         "Plano 2027": _ic27('<path d="M5 21V4M5 4.5c4-2.5 7 2 14 0v9c-7 2-10-2.500-14 0"/>'),
         "Benchmark": _ic27('<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><path d="M12 11.9h.01"/>')}
def _num_br(v):
    return f"{v:g}".replace(".", ",")
def _bh(itens, suf=""):
    m = max(v for _, v in itens)
    return '<div class="fig vidro">' + "".join(f'<div class="bh-r" title="{n}: {_num_br(v)}{suf}"><span>{n}</span><i><b style="width:{v / m * 100:.1f}%"></b></i><em>{_num_br(v)}{suf}</em></div>' for n, v in itens) + '</div>'
def _bc(itens):
    m = max(v for _, v in itens)
    return '<div class="fig vidro bc">' + "".join(f'<div title="{n}: {v}"><em>{v or ""}</em><i><b style="height:{v / m * 100:.0f}%"></b></i><span>{n}</span></div>' for n, v in itens) + '</div>'
def _st(itens):
    t = sum(v for _, v in itens)
    return '<div class="fig vidro"><div class="st">' + "".join(f'<i class="c{i}" style="width:{v / t * 100:.1f}%" title="{n}: {v}"></i>' for i, (n, v) in enumerate(itens)) + '</div><div class="st-l">' + "".join(f'<span><i class="c{i}"></i>{n}: <b>{v}</b></span>' for i, (n, v) in enumerate(itens)) + '</div></div>'
_curt = [("Tivio Visita", 49), ("Oferta do Tivio Malls", 22), ("Carta do Gestor", 18), ("Dividendos de FIIs", 16), ("Resumo mensal em Reels", 15), ("Deep Dive", 15), ("Evento The New Agro", 15), ("Na Mídia", 12), ("Produto", 11), ("Desempenho em card", 7.5)]
exec(ler("dados_peers.py"))
_paginas = {p["nome"]: f'peer-{p["slug"]}.html' for p in PEERS}
for _s, _n, _f, _cs in SETORES:
    for _c in _cs:
        _paginas[_c] = f"setor-{_s}.html"

def logos_inline(html):
    return re.sub(r"\{\{lg:([^}]+)\}\}", lambda x: logo(x.group(1)), html)

# ---------- 1. AutomaTivio ----------
URL_ZIP = "https://github.com/orenanchaves/Tivio-teste/releases/download/AutomaTivio_v2/AutomaTivio.zip"
URL_REL = "https://github.com/orenanchaves/Tivio-teste/releases/tag/AutomaTivio_v2"
cab_dl = cabecalho("", [("logica", "Como funciona"), ("ambiente", "Ambiente interno"),
                                   ("segmentos", "Segmentos"), ("status", "Decks"), ("fallback", "Quando falha"),
                                   ("baixar", "Como baixar"), ("comecar", "Começar")])
hero_dl = hero("Versão de 28/10/2026", "Automa<strong>Tivio</strong>",
               "A edição mensal da Central de Materiais em um comando: lê as planilhas do mês e gera os "
               "relatórios de gestão, as páginas por vertical, os posts, o e-mail e a Central, com os mesmos números em todos.")
corpo_dl = (ler("dl_corpo.html").replace("{{HEADER}}", cab_dl).replace("{{HERO}}", hero_dl)
            .replace("{{URL_ZIP}}", URL_ZIP).replace("{{URL_REL}}", URL_REL)
            .replace("{{AMBIENTE}}", ler("p_ambiente.html")).replace("{{SEGMENTOS}}", ler("segmentos.html")))
(SAIDA / "automativio.html").write_text(pagina("AutomaTivio", corpo_dl, ler("dl.css")), encoding="utf-8")

# páginas de cada time: públicos diferentes, cada uma só com o que aquele time usa
def pagina_time(arq, titulo, h1, texto, parte):
    corpo = (cabecalho(titulo, [], False) + '<div class="wrap"><section class="hero hero-time"><div>'
             f'<h1>{h1}</h1><p class="lead">{texto}</p></div></section>' + ler(parte)
             + '</div><script>\n' + ler("app.js") + '</script>')
    (SAIDA / arq).write_text(pagina(titulo, corpo, ler("dl.css")), encoding="utf-8")
pagina_time("automativio-gestao.html", "Gestão", "Comentários da <strong>Gestão</strong>",
            "Os comentários que vão nos relatórios do mês, por segmento.", "p_gestao.html")
pagina_time("automativio-riscos.html", "Riscos", "Aprovação de <strong>Riscos</strong>",
            "Cada material da edição, com os avisos da conferência ao lado.", "p_riscos.html")
pagina_time("automativio-marketing.html", "Marketing", "Edição do <strong>mês</strong>",
            "Dados, rodada, decks, publicação e histórico.", "p_mkt.html")

# ---------- 2. Central de Marketing ----------
fonte = (RAIZ / "Comunicação e Marketing/Marketing/Relatório geral de marketing 2027.html").read_text(encoding="utf-8")
miolo = re.search(r"<main>(.*)</main>", fonte, re.S).group(1)
miolo = re.sub(r"<h1>.*?</h1>", "", miolo, count=1, flags=re.S)
sub = re.search(r'<p class="sub">(.*?)</p>', miolo, re.S)
miolo = miolo.replace(sub.group(0), "", 1)
# os h2 do relatório ganham âncora para o menu
ids = {"1.": "resumo", "2.": "redes", "3.": "relatorios", "4.": "fazer", "5.": "lidos"}
miolo = re.sub(r"<h2>(\d\.)", lambda m: f'<h2 id="r-{ids.get(m.group(1), "x")}">{m.group(1)}', miolo)
SITE = SAIDA / "mkt_site.html"
FINMKT = SAIDA / "mkt_finmkt.html"
corpo_mkt = (ler("mkt_corpo.html")
             .replace("{{GESTORES}}", ler("mkt_gestores.html")).replace("{{VIDEO}}", ler("mkt_video.html")).replace("{{IDEIAS}}", ler("mkt_ideias.html")).replace("{{CASES}}", ler("mkt_cases.html")).replace("{{PEERS}}", ler("mkt_peers.html").replace("{{MUNDO}}", ler("mkt_mundo.html"))).replace("{{RELATORIO}}", miolo).replace("{{SUB}}", sub.group(1))
             .replace("{{SITE}}", SITE.read_text(encoding="utf-8") if SITE.exists() else "")
             .replace("{{FINMKT}}", FINMKT.read_text(encoding="utf-8") if FINMKT.exists() else ""))
cab_mkt = cabecalho("Central de Marketing", [("posicionamento", "Estruturados"), ("posts", "Posts"),
                                             ("eventos", "Eventos Itaú"), ("captacao", "Captação"), ("ideias", "Ideias"), ("cases", "Cases"), ("peers", "Peers"), ("mercados", "Outros mercados"), ("setores", "Setores"), ("mundo", "Mundo"), ("sugestoes", "Sugestões"), ("sintese", "O que fazer"),
                                             ] + ([("site", "Site")] if SITE.exists() else []) + ([("finmkt", "Finmkt")] if FINMKT.exists() else []) + [("copilot", "Copilot"), ("relatorio", "Relatório 2027")])
hero_mkt = hero("Plano de 2027", "Central de <strong>Marketing</strong>",
                "O que a Tivio vai publicar, em que segmento e com qual objetivo: posts, eventos com o Itaú, "
                "captação por landing page, SEO e GEO, a partir do relatório de marketing de 2027.")
corpo_mkt = corpo_mkt.replace("{{HEADER}}", cab_mkt).replace("{{HERO}}", hero_mkt)
corpo_mkt = logos_inline(fichas(corpo_mkt))
(SAIDA / "marketing.html").write_text(pagina("Central de Marketing Tivio", corpo_mkt, ler("mkt.css")), encoding="utf-8")
exec(ler("gerar_paginas.py"))
exec(ler("gerar_categorias.py"))
exec(ler("gerar_polo.py"))
exec(ler("gerar_calendario.py"))
exec(ler("gerar_sitenovo.py"))
exec(ler("gerar_filtro.py"))
_an = '<header class="barra"><div class="barra-in"><span class="marca">' + LOGO + '</span></div></header>' + ler("analise_corpo.html")
(SAIDA / "analise.html").write_text('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">' + pagina("Tivio 2026 e 2027", _an, CSS_P + "@media print{.barra{position:static}.vidro,.tab,tr,.kpi{break-inside:avoid}h2{break-after:avoid}}") + "</html>", encoding="utf-8")
print("ok", [(p.name, p.stat().st_size) for p in SAIDA.glob("*.html") if p.name in ("automativio.html", "marketing.html")])
