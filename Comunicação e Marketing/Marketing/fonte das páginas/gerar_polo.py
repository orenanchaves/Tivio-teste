POLOS = [("musgo", "Verde musgo escuro", "#3F5249, bordado em off-white"), ("claro", "Verde claro", "#C1F4D4, bordado escuro")]
_fig = "".join(
    f'<section class="polo-item"><img class="polo-g vidro" src="polos/{p}.webp" alt="Polo {n.lower()} com o logo da Tivio Capital bordado" width="1400" height="1738" loading="lazy">'
    f'<img class="polo-d vidro" src="polos/{p}-detalhe.webp" alt="Detalhe do bordado na polo {n.lower()}" loading="lazy"><h2>{n}</h2><p>{c}</p></section>'
    for p, n, c in POLOS)
corpo_polo = (cabecalho("Polo", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Polo"))
    + '<section class="topo-peer"><div><p class="eyebrow"><i></i>Mockup</p><h1>Polo Tivio Capital</h1></div></section>'
    + f'<div class="polos">{_fig}</div><p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "polo.html").write_text(pagina("Polo", corpo_polo, CSS_P), encoding="utf-8")
