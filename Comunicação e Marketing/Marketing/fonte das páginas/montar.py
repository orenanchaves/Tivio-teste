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

def cabecalho(area, abas):
    links = "".join(f'<a href="#{i}">{t}</a>' for i, t in abas)
    nome_area = f'<span class="area-nome">{area}</span>' if area else ""
    return f'''<header class="barra"><div class="barra-in">
<a class="marca" href="index.html" aria-label="Comunicação &amp; Marketing">{LOGO}{nome_area}</a>
<nav class="chips" aria-label="Seções">{links}</nav>
<div class="tema" role="group" aria-label="Tema">
<button type="button" data-tema="light" aria-label="Tema claro"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button>
<button type="button" data-tema="dark" aria-label="Tema escuro"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg></button>
</div></div></header>'''

def pagina(titulo, corpo, css_extra=""):
    return f"""<title>{titulo}</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
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

# ---------- 1. AutomaTivio ----------
URL_ZIP = "https://github.com/orenanchaves/Tivio-teste/releases/download/AutomaTivio_v2/AutomaTivio.zip"
URL_REL = "https://github.com/orenanchaves/Tivio-teste/releases/tag/AutomaTivio_v2"
cab_dl = cabecalho("", [("logica", "Como funciona"), ("ambiente", "Ambiente interno"),
                                   ("segmentos", "Segmentos"), ("fallback", "Quando falha"),
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
    corpo = (cabecalho(titulo, []) + '<div class="wrap"><section class="hero hero-time"><div>'
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
             .replace("{{IDEIAS}}", ler("mkt_ideias.html")).replace("{{CASES}}", ler("mkt_cases.html")).replace("{{PEERS}}", ler("mkt_peers.html")).replace("{{RELATORIO}}", miolo).replace("{{SUB}}", sub.group(1))
             .replace("{{SITE}}", SITE.read_text(encoding="utf-8") if SITE.exists() else "")
             .replace("{{FINMKT}}", FINMKT.read_text(encoding="utf-8") if FINMKT.exists() else ""))
cab_mkt = cabecalho("Central de Marketing", [("posicionamento", "Estruturados"), ("posts", "Posts"),
                                             ("eventos", "Eventos Itaú"), ("captacao", "Captação"), ("ideias", "Ideias"), ("cases", "Cases"), ("peers", "Peers"), ("mercados", "Outros mercados"), ("sintese", "O que fazer"),
                                             ] + ([("site", "Site")] if SITE.exists() else []) + ([("finmkt", "Finmkt")] if FINMKT.exists() else []) + [("copilot", "Copilot"), ("relatorio", "Relatório 2027")])
hero_mkt = hero("Plano de 2027", "Central de <strong>Marketing</strong>",
                "O que a Tivio vai publicar, em que segmento e com qual objetivo: posts, eventos com o Itaú, "
                "captação por landing page, SEO e GEO, a partir do relatório de marketing de 2027.")
corpo_mkt = corpo_mkt.replace("{{HEADER}}", cab_mkt).replace("{{HERO}}", hero_mkt)
(SAIDA / "marketing.html").write_text(pagina("Central de Marketing Tivio", corpo_mkt, ler("mkt.css")), encoding="utf-8")
print("ok", [(p.name, p.stat().st_size) for p in SAIDA.glob("*.html") if p.name in ("automativio.html", "marketing.html")])
