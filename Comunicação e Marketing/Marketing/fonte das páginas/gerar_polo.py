POLOS = [("musgo", "Verde musgo escuro", "#3F5249, bordado em off-white"), ("claro", "Verde claro", "#C1F4D4, bordado escuro")]
_fig = "".join(
    f'<section class="polo-item"><img class="polo-g vidro" src="polos/{p}.webp" alt="Polo {n.lower()} com o logo da Tivio Capital bordado" width="1400" height="1738" loading="lazy">'
    f'<img class="polo-d vidro" src="polos/{p}-detalhe.webp" alt="Detalhe do bordado na polo {n.lower()}" loading="lazy"><h2>{n}</h2><p>{c}</p></section>'
    for p, n, c in POLOS)
corpo_polo = (cabecalho("Brand", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Brand"))
    + '<section class="topo-peer"><div><p class="eyebrow"><i></i>Polo Tivio Capital</p><h1>Brand</h1></div></section>'
    + f'<div class="polos">{_fig}</div><p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "brand.html").write_text(pagina("Brand", corpo_polo, CSS_P), encoding="utf-8")

corpo_est = (cabecalho("Estrutura", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Estrutura"))
    + '<section class="topo-peer"><div><p class="eyebrow"><i></i>Comunicação &amp; Marketing</p><h1>Estrutura</h1><p class="lead">Quatro frentes com responsáveis, rituais e prazos.</p></div></section>'
    + '<div class="tab"><table><tr><th>Frente</th><th>O que cobre</th></tr>'
    + '<tr><td>Direção</td><td>Prioridades e aprovação estratégica</td></tr>'
    + '<tr><td>Coordenação, performance e automação</td><td>Rituais, mensuração, dados, materiais, digital e AutomaTivio</td></tr>'
    + '<tr><td>Conteúdo e comunicação</td><td>Pauta, Tivio News, legendas, agência, aprovação e publicação</td></tr>'
    + '<tr><td>Design e creative</td><td>KVs, apresentações, e-mails, carrosséis, eventos e motion</td></tr></table></div>'
    + '<div class="analise"><div class="vidro"><h3>Fluxo</h3><ol><li>Demanda entra</li><li>Triagem e definição do responsável</li><li>Produção</li><li>Aprovação técnica e Compliance</li><li>Aprovação estratégica, quando necessária</li><li>Publicação e mensuração</li></ol></div></div>'
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "estrutura.html").write_text(pagina("Estrutura", corpo_est, CSS_P), encoding="utf-8")
