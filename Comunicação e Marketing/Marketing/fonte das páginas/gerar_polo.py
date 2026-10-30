POLOS = [("musgo", "Verde musgo escuro", "#3F5249, bordado em off-white"), ("claro", "Verde claro", "#C1F4D4, bordado escuro"),
         ("clarinho", "Verde clarinho", "#B3BFBB, bordado escuro"), ("preta", "Preta", "Bordado branco")]
_fig = "".join(
    f'<section class="polo-item"><a class="zoom" href="polos/{p}.webp"><img class="vidro" src="polos/{p}.webp" alt="Polo {n.lower()} com o logo da Tivio Capital bordado" width="1400" height="1738" loading="lazy"></a>'
    f'<a class="zoom" href="polos/{p}-detalhe.webp"><img class="vidro" src="polos/{p}-detalhe.webp" alt="Detalhe do bordado na polo {n.lower()}" loading="lazy"></a><h3>{n}</h3><p>{c}</p></section>'
    for p, n, c in POLOS)

CORES = [("Verde", "#C1F4D4"), ("Verde escuro", "#92D3AB"), ("Verde destaque", "#337F51"), ("Agro", "#52B97A"),
         ("Azul escuro", "#3C4A60"), ("Azul", "#759DB4"), ("Azul imobiliário", "#C8D7E0"), ("Cinza", "#637881"),
         ("Cinza claro", "#ABC6CD"), ("Linha", "#D4E0E6"), ("Off-white", "#E6EDF1"), ("Fundo escuro", "#0A0F14"),
         ("Preto", "#000000"), ("Branco", "#FFFFFF"), ("Bradesco", "#CC092F")]
_cores = "".join(f'<div class="cor vidro"><i style="background:{h}"></i><b>{n}</b><span>{h}</span></div>' for n, h in CORES)
PESOS = [(200, "ExtraLight"), (300, "Light"), (400, "Regular"), (600, "SemiBold"), (700, "Bold")]
_pesos = "".join(f'<div class="peso vidro"><b style="font-weight:{w}">Casa de estruturados</b><span>Versos {n}, {w}</span></div>' for w, n in PESOS)
RAIOS = [("8", "sm"), ("12", "md"), ("20", "lg"), ("28", "xl"), ("999", "full")]
_raios = "".join(f'<div class="raio"><i style="border-radius:{r}px"></i><span>{n}, {r}px</span></div>' for r, n in RAIOS)
_t = (RAIZ / "AutomaTivio/assets/marca/tivio_t.svg").read_text(encoding="utf-8")
_ds = ('<h2 id="design-system">Design <strong>system</strong></h2>'
    f'<h3 class="ds-t" id="logo">Logo</h3><div class="ds-logos"><div class="ds-logo escuro">{LOGO}</div><div class="ds-logo claro">{LOGO}</div><div class="ds-logo escuro simbolo">{_t}</div><div class="ds-logo claro simbolo">{_t}</div></div>'
    f'<h3 class="ds-t" id="cores">Cores</h3><div class="ds-cores">{_cores}</div>'
    f'<h3 class="ds-t" id="tipografia">Tipografia</h3><div class="ds-pesos">{_pesos}</div>'
    f'<h3 class="ds-t" id="forma">Forma</h3><div class="ds-raios">{_raios}</div>')
import json as _json, datetime as _dt
def _data(d):
    try: return _dt.datetime.strptime(d, "%B %d, %Y").strftime("%d/%m/%Y")
    except ValueError: return ""
_feed = _json.loads((pathlib.Path("feed") / "feed.json").read_text(encoding="utf-8"))
_grade = "".join(f'<a class="feed-item vidro" href="{x["h"]}" target="_blank" rel="noopener"><img src="feed/{x["f"]}" alt="{"Reel" if x["t"] == "Video" else "Post"} da Tivio Capital de {_data(x["d"])}" loading="lazy"><span>{"Reel" if x["t"] == "Video" else "Post"} · {_data(x["d"])}</span></a>' for x in _feed)
_feed_h = f'<h2 id="feed">Feed do <strong>Instagram</strong></h2><p class="secao-sub">12 publicações mais recentes de @tiviocapital, copiadas em 30/10/2026. A primeira é a fixada no perfil.</p><div class="feed">{_grade}</div>'
_chips = '<nav class="ds-nav" aria-label="Seções de Brand">' + "".join(f'<a href="#{i}">{n}</a>' for i, n in [("logo", "Logo"), ("cores", "Cores"), ("tipografia", "Tipografia"), ("forma", "Forma"), ("polo", "Polo"), ("feed", "Feed do Instagram")]) + "</nav>"
_lb = """<div id="lb" hidden><button type="button" aria-label="Fechar"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg></button><img alt=""></div>
<script>(function(){var l=document.getElementById('lb'),i=l.querySelector('img');function f(){l.hidden=true;i.removeAttribute('src')}
[].forEach.call(document.querySelectorAll('a.zoom'),function(a){a.addEventListener('click',function(e){e.preventDefault();i.src=a.getAttribute('href');i.alt=a.querySelector('img').alt;l.hidden=false})});
l.addEventListener('click',f);document.addEventListener('keydown',function(e){if(e.key==='Escape')f()})})();</script>"""
corpo_polo = (cabecalho("Brand", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Brand"))
    + '<section class="topo-peer"><div><p class="eyebrow"><i></i>Tivio Capital</p><h1>Brand</h1></div></section>' + _chips + _ds
    + f'<h2 id="polo">Polo</h2><div class="polos">{_fig}</div>' + _feed_h
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>' + _lb)
(EXTRA / "brand.html").write_text(pagina("Brand", corpo_polo, CSS_P), encoding="utf-8")

corpo_est = (cabecalho("Estrutura", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Estrutura"))
    + '<section class="topo-peer"><div><p class="eyebrow"><i></i>Comunicação &amp; Marketing</p><h1>Estrutura</h1><p class="lead">Direção, coordenação, três pilares operacionais e Eventos como frente transversal.</p></div></section>'
    + '<div class="tab"><table><tr><th>Frente</th><th>O que cobre</th></tr>'
    + '<tr><td>Direção</td><td>Prioridades e aprovação estratégica</td></tr>'
    + '<tr><td>Coordenação de C&amp;M</td><td>Prioridades, governança e ligação entre as frentes</td></tr>'
    + '<tr><td>Conteúdo &amp; Comunicação</td><td>Calendário editorial, redes sociais, Tivio News, textos, legendas e publicação</td></tr>'
    + '<tr><td>Design &amp; Produção</td><td>Identidade visual, KVs, apresentações, social, vídeo, motion e templates</td></tr>'
    + '<tr><td>Performance, Dados &amp; Automação</td><td>Materiais, fechamento, dados, performance, mídia paga e automação</td></tr>'
    + '<tr><td>Eventos</td><td>Frente transversal: coordenação, operação, peças e aprovação estratégica</td></tr></table></div>'
    + '<div class="analise"><div class="vidro"><h3>Fluxo</h3><ol><li>Demanda entra</li><li>Triagem e definição do responsável</li><li>Produção</li><li>Aprovação técnica e Compliance</li><li>Aprovação estratégica, quando necessária</li><li>Publicação e mensuração</li></ol></div></div>'
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "estrutura.html").write_text(pagina("Estrutura", corpo_est, CSS_P), encoding="utf-8")
