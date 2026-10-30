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
_slogan = '<h2 id="slogan">Slogan</h2><section class="destaque aprende vidro"><p class="slogan"><span>Sugestão de slogan</span>Tivio Capital,<br>somos a alternativa</p></section>'
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
_chips = '<nav class="ds-nav" aria-label="Seções de Brand">' + "".join(f'<a href="#{i}">{n}</a>' for i, n in [("slogan", "Slogan"), ("logo", "Logo"), ("cores", "Cores"), ("tipografia", "Tipografia"), ("forma", "Forma"), ("diretrizes", "Diretrizes"), ("apresentacoes", "Apresentações"), ("polo", "Polo"), ("feed", "Feed do Instagram")]) + "</nav>"
_uso = lambda ok, cl, txt, st="": f'<div class="uso"><div class="uso-a {cl}"{st}>{LOGO}</div><p class="{"ok" if ok else "nao"}">{"Certo" if ok else "Evitar"}</p><span>{txt}</span></div>'
_regras = [("Cor", ["Preto, branco e fundo escuro são a base", "Verde #C1F4D4 destaca no fundo escuro", "Verde #337F51 destaca no fundo claro", "Azul escuro #3C4A60 nos botões do tema claro", "Azul imobiliário e Agro só nesses segmentos"]),
           ("Tipografia", ["Versos em tudo", "Títulos leves, com a palavra-chave em negrito", "Corpo em Light, rótulos em SemiBold", "Rótulos curtos em maiúsculas e espaçados"]),
           ("Layout", ["Blocos de vidro com raio de 12 a 20px", "Botões em forma de pílula", "Respiro entre blocos e mínimo de 16px na borda do celular", "Nada sobreposto, sempre conferir no celular e no desktop"]),
           ("Ícones", ["SVG monocromático, em traço", "Sem emoji nas peças", "Mesma espessura em todo o conjunto"]),
           ("Texto", ["Frases curtas e pouco texto na arte", "Sem travessão", "Número sempre com fonte e data", "Falar do risco com clareza; peça passa por Compliance"])]
_ap = ["Formato 16:9, com logo oficial na capa e na assinatura", "Uma ideia por slide, com título que diz a conclusão", "Dados do mês vindos do AutomaTivio, nunca digitados à mão", "Gráfico com uma cor por função e rótulo direto no dado", "Versão sem ROA e com ROA quando a plataforma pedir", "Disclaimer e fonte no fim, com aprovação de Compliance"]
_dir = ('<h2 id="diretrizes">Diretrizes de <strong>design</strong></h2><p class="secao-sub">Proposta a partir do design system e das peças atuais da Tivio, para validar com o time.</p>'
    '<h3 class="ds-t">Uso do logo</h3><div class="usos">' + _uso(True, "escuro", "Branco no fundo escuro") + _uso(True, "claro", "Preto no fundo claro")
    + _uso(False, "claro torto", "Esticar ou distorcer") + _uso(False, "claro corfora", "Trocar a cor") + _uso(False, "semcontraste", "Fundo sem contraste") + '</div>'
    + '<div class="regras">' + "".join(f'<section class="vidro bloco"><h3>{n}</h3><ul>' + "".join(f"<li>{x}</li>" for x in l) + "</ul></section>" for n, l in _regras) + '</div>'
    + '<h2 id="apresentacoes">Apresentações</h2><p class="secao-sub">Responsável: Renan Chaves.</p><div class="subs">' + "".join(f'<div class="sub vidro"><b>{i}</b><span>{x}</span></div>' for i, x in enumerate(_ap, 1)) + '</div>')
_lb = """<div id="lb" hidden><button type="button" aria-label="Fechar"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg></button><img alt=""></div>
<script>(function(){var l=document.getElementById('lb'),i=l.querySelector('img');function f(){l.hidden=true;i.removeAttribute('src')}
[].forEach.call(document.querySelectorAll('a.zoom'),function(a){a.addEventListener('click',function(e){e.preventDefault();i.src=a.getAttribute('href');i.alt=a.querySelector('img').alt;l.hidden=false})});
l.addEventListener('click',f);document.addEventListener('keydown',function(e){if(e.key==='Escape')f()})})();</script>"""
corpo_polo = (cabecalho("Brand", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Brand"))
    + '<section class="topo-peer"><div><p class="eyebrow"><i></i>Tivio Capital</p><h1>Brand</h1></div></section>' + _chips + _slogan + _ds + _dir
    + f'<h2 id="polo">Polo</h2><div class="polos">{_fig}</div>' + _feed_h
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>' + _lb)
(EXTRA / "brand.html").write_text(pagina("Brand", corpo_polo, CSS_P), encoding="utf-8")

FRENTES_E = [("Coordenação, Performance &amp; Automação", "Renan Chaves", ["Prioridades", "Materiais e fechamento", "Automação", "Dados e performance", "C&amp;M Hub", "Governança", "Interface com Enrico Trotta", "Apresentações e decks"]),
             ("Conteúdo &amp; Comunicação", "Fernanda Acquati", ["Calendário editorial", "Redes sociais", "Tivio News", "Textos e legendas", "Publicação", "Moderação", "Aprovações", "Operação dos eventos"]),
             ("Design &amp; Produção", "Gabriel Fiorilli", ["Identidade visual", "KVs", "Social", "Materiais de eventos", "Vídeo e motion", "Templates"]),
             ("Agência parceira", "ColaAí", ["Tráfego pago"])]
_org = ('<div class="org"><div class="org-n vidro"><span>Direção</span><b>Enrico Trotta</b></div><i class="org-l"></i>'
        '<div class="org-n vidro"><span>Coordenação de C&amp;M</span><b>Renan Chaves</b></div><i class="org-l"></i>'
        '<div class="org-3"><div class="org-n vidro"><span>Conteúdo &amp; Comunicação</span><b>Fernanda Acquati</b></div><div class="org-n vidro"><span>Design &amp; Produção</span><b>Gabriel Fiorilli</b></div><div class="org-n vidro"><span>Performance, Dados &amp; Automação</span><b>Renan Chaves</b></div></div>'
        '<div class="org-t"><span>Eventos</span>Frente transversal, com as três áreas</div>'
        '<div class="org-t"><span>Agência parceira</span>ColaAí, tráfego pago</div></div>')
_fr = "".join(f'<section class="frente vidro"><h3>{n}</h3><p class="dono">{d}</p><ul>' + "".join(f"<li>{x}</li>" for x in l) + "</ul></section>" for n, d, l in FRENTES_E)
_pap = "".join(f'<div class="papel vidro"><span>{a}</span><b>{b}</b></div>' for a, b in [("Coordenação", "Renan Chaves"), ("Operação", "Fernanda Acquati"), ("Peças", "Gabriel Fiorilli"), ("Aprovação estratégica", "Enrico Trotta")])
_fl = "".join(f'<li class="vidro"><b>{a}</b><span>{b}</span></li>' for a, b in [("Demanda entra", "Pedido registrado em um lugar só"), ("Triagem", "Definição do responsável"), ("Produção", "Execução pela frente dona"), ("Aprovação técnica", "Revisão e Compliance"), ("Aprovação estratégica", "Quando necessária"), ("Publicação", "Publicação e mensuração")])
corpo_est = (cabecalho("Estrutura", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Estrutura"))
    + '<section class="topo-peer"><div><p class="eyebrow"><i></i>Comunicação &amp; Marketing</p><h1>Estrutura</h1><p class="lead">Direção, coordenação, três pilares operacionais e Eventos como frente transversal.</p></div></section>'
    + '<h2>Quem responde <strong>por quê</strong></h2>' + _org
    + '<h2>O que cada frente <strong>cobre</strong></h2><div class="frentes">' + _fr + '</div>'
    + '<h2>Eventos, frente <strong>transversal</strong></h2><div class="papeis">' + _pap + '</div>'
    + '<h2>Como uma demanda <strong>anda</strong></h2><ol class="roteiro r6">' + _fl + '</ol>'
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "estrutura.html").write_text(pagina("Estrutura", corpo_est, CSS_P), encoding="utf-8")

EV = [("Crédito Estruturado e Crédito Privado", "Quem aloca, estrutura e distribui crédito", [
        ("I Congresso Brasileiro de Crédito Privado (Anbima)", "10/09/2026, São Paulo", "Alta: é o palco mais próximo da tese"),
        ("Money Week", "27 e 28/08/2026, Balneário Camboriú", "Média: gestoras de crédito estruturado já participam")]),
      ("Assessores e gerentes", "Quem indica o produto", [
        ("Anbima Global Insights", "11/11/2026, São Paulo, gratuito", "Alta: feito para assessores, gerentes e consultores"),
        ("Advisor Talks", "17/09/2026, WTC, São Paulo", "Alta: reguladores, instituições e assessores no mesmo lugar"),
        ("BTG Summit", "25 e 26/02/2026, São Paulo", "Média: depende da relação com a plataforma"),
        ("Expert XP", "Julho em 2025; data de 2026 não confirmada", "Alta: a Tivio já esteve lá em 2025")]),
      ("Previdência e institucional", "Fundos de pensão e entidades", [
        ("Congresso Brasileiro de Previdência Privada (Abrapp)", "22 a 24/10/2025, São Paulo; edição de 2026 não confirmada", "Alta: principal encontro do setor"),
        ("Encontros regionais da Abrapp", "Março e abril de 2026: São Paulo, Rio e Brasília", "Média: conversa menor, com lideranças das entidades")]),
      ("Imobiliário", "Gestoras, investidores e cotistas de FII", [
        ("FII Experience (Suno)", "26/03/2026, São Paulo", "Média: público de varejo em FII"),
        ("GRI Fundos Imobiliários", "Data não confirmada", "Alta: gestores e institucionais"),
        ("Money Week", "27 e 28/08/2026, Balneário Camboriú", "Média: grandes gestoras de FII presentes")]),
      ("Agro", "Crédito, Fiagro e CRA", [
        ("Agri 360 Breakfast (Mayer Brown)", "23/04/2026, São Paulo", "Média: Fiagro, CRA, CPR e PPE"),
        ("Conecta Agro", "24 e 25/11/2026, São Paulo", "A avaliar: confirmar se trata de crédito")])]
_ev = "".join(f'<h2>{s}</h2><p class="secao-sub">{q}</p><div class="tab"><table><tr><th>Evento</th><th>Última data encontrada</th><th>Prioridade sugerida</th></tr>'
              + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in l) + "</table></div>" for s, q, l in EV)
_fontes = [("Anbima, crédito privado", "https://www.anbima.com.br/pt_br/noticias/congresso-discute-avancos-necessarios-para-o-desenvolvimento-do-credito-privado.htm"),
           ("Anbima Global Insights", "https://www.anbima.com.br/pt_br/noticias/inscricoes-abertas-para-o-anbima-global-insights-2026.htm"),
           ("Advisor Talks", "https://legismap.com.br/conteudos/artigos-e-noticias/abrapp-sera-uma-das-apoiadoras-do-advisor-talks-2026"),
           ("Agenda do Gorila", "https://gorila.com.br/blog/agenda-do-wealth-management-principais-eventos-do-primeiro-semestre-de-2026/"),
           ("Abrapp 2025", "https://altss.com/conferences/46-congresso-brasileiro-de-previd-ncia-privada-abrapp"),
           ("Encontros Abrapp", "https://legismap.com.br/conteudos/artigos-e-noticias/encontros-regionais-da-abrapp-iniciam-em-marco-pela-regional-sudoeste"),
           ("FII Experience", "https://fiis.com.br/?p=417523"), ("Money Week", "https://euqueroinvestir.com/money-week/money-week-2026-reune-grandes-gestoras-de-fiis-veja-quem-estara-no-evento"),
           ("GRI FII", "https://borainvestir.b3.com.br/eventos/gri-fundos-imobiliarios-2026/"),
           ("Agri 360", "https://www.mayerbrown.com/pt/insights/events/2026/04/agri-360-breakfast-tendencias-e-evolucao-das-estruturas-de-financiamento-no-agronegocio-para-2026-fiagro-cra-cpr-e-ppe"),
           ("Conecta Agro", "https://visitesaopaulo.com/evento/conecta-agro-2026-2026/")]
corpo_ev = (cabecalho("Eventos do mercado", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Eventos do mercado"))
    + '<section class="topo-peer"><div><p class="eyebrow"><i></i>Eventos</p><h1>Eventos do mercado</h1><p class="lead">Onde cada segmento se encontra. A leitura serve para escolher poucos eventos e levar a mesma tese de estruturados.</p></div></section>'
    + '<div class="analise"><div class="vidro"><h3>O que a análise mostra</h3><ul><li>Assessores têm a agenda mais cheia, e é onde a Tivio fala com quem indica</li><li>Crédito privado ganhou congresso próprio da Anbima em 2026</li><li>Nenhum evento dedicado a estruturados apareceu na pesquisa, o que abre espaço para os 16 encontros com o Itaú</li></ul></div>'
    + '<div class="vidro"><h3>Sugestão para 2027</h3><ul><li>Marcar presença em poucos eventos, com porta-voz e tese definidos</li><li>Priorizar Anbima, Advisor Talks e Abrapp</li><li>Evitar choque de data com os 16 encontros</li></ul></div></div>'
    + _ev + '<p class="meta-txt">As datas são da última edição encontrada. As de 2027 ainda precisam ser confirmadas com cada organizador, e as prioridades são proposta do time. Não foram encontradas datas de eventos da Uqbar, ANFIDC, Aneprem, Abipem ou Anbima para institucionais.</p>'
    + '<p class="fontes-peer"><b>Fontes</b>' + "".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in _fontes) + '</p>'
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "eventos-mercado.html").write_text(pagina("Eventos do mercado", corpo_ev, CSS_P), encoding="utf-8")
