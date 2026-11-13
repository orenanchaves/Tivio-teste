# -*- coding: utf-8 -*-
# Benchmark de sites (16 gestoras lidas em 13/11/2026) e estudo de envio automático para o site (SFTP / MZ IQ).
# Executado ao fim do gerar_polo.py, com os mesmos auxiliares (cabecalho, trilha, pagina, CSS_P, EXTRA).
import html as _html

_OK = '<svg class="bm-ok" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-label="Sim"><path d="m5 12 5 5 9-10"/></svg>'
_COLS = ["Caminho por público", "Fundo com dados", "Documentos no fundo", "Newsletter", "Podcast ou vídeo", "Área do investidor"]
_MAT = [  # 1 = visto no site em 13/11/2026; vazio = não vimos
    ("Tivio", "Brasil", [0, 1, 1, 1, 1, 0]), ("Kinea", "Brasil", [1, 1, 1, 1, 1, 1]), ("BRAM", "Brasil", [1, 1, 1, 1, 1, 0]),
    ("Fami Capital", "Brasil", [0, 0, 0, 0, 1, 0]), ("Galápagos", "Brasil", [1, 0, 0, 0, 1, 1]), ("Solis", "Brasil", [1, 1, 0, 0, 0, 1]),
    ("Angá", "Brasil", [0, 0, 1, 0, 0, 0]), ("Valora", "Brasil", [0, 1, 1, 1, 0, 0]), ("SPX", "Brasil", [1, 0, 0, 1, 1, 0]),
    ("Apollo", "Exterior", [1, 1, 0, 1, 1, 1]), ("Ares", "Exterior", [1, 1, 0, 1, 1, 1]), ("KKR", "Exterior", [1, 0, 0, 1, 1, 1]),
    ("Oaktree", "Exterior", [1, 0, 0, 1, 1, 1]), ("Janus Henderson", "Exterior", [1, 0, 1, 1, 1, 0]), ("Golub", "Exterior", [1, 0, 0, 0, 1, 1]),
    ("TwentyFour", "Exterior", [1, 1, 1, 0, 1, 0])]
_PEER = [  # nome, slug das imagens, o que faz bem, o que faz mal, o que levar para a Tivio
    ("Kinea", "kinea", "No topo da página do fundo: selo de risco, taxas, público, PL e PL médio de 12 meses. Abas Sobre, Por que investir, Processo, Palavra do gestor. Onde investir e Portal do Investidor no menu.",
     "Home de 16 MB; sem título principal (H1); 40 de 93 imagens sem descrição.", "Cabeçalho de dados no fundo e a aba Palavra do gestor."),
    ("BRAM", "bram", "Escolha de público no topo (Pessoa Física, Institucional, Corporate, Internacional). Fundo com botão Relatório Mensal, CNPJ, público e rentabilidade, e vídeo explicativo. Controles de acessibilidade e simulador.",
     "Abertura em carrossel genérico; no celular a página rola para o lado.", "Botão do relatório do mês em destaque e vídeo curto por fundo."),
    ("Fami Capital", "fami-capital", "Pessoa real na abertura, com vídeo. Ofertas Públicas no menu.", "A abertura não fala de produto; aviso de cookies ocupa a tela no celular.", "Ofertas Públicas como item de menu."),
    ("Galápagos", "galapagos", "Caminhos Para empresas e Para você, Abra sua conta e botão de WhatsApp.", "26 MB e 22 segundos para carregar; abertura só com a foto do escritório.", "O caminho por público, não o peso."),
    ("Solis", "solis", "Foco em FIDC dito na abertura e números da casa logo abaixo (anos, fundos, patrimônio, prêmios). Página para tomadores.", "Sem newsletter e sem área para assessor.", "A frase de foco em estruturados na abertura."),
    ("Angá", "anga", "Controles de acessibilidade. Documentos pelo mesmo gerenciador de arquivos da MZ que a Tivio usa.", "Sem newsletter; carrossel; o link do documento baixa o arquivo direto, sem página.", "Nada novo."),
    ("Valora", "valora", "Home lista os fundos por estratégia. Fundo com CNPJ, administrador, PL, materiais e regulamento, e assinatura para receber os relatórios daquele fundo. WhatsApp.",
     "27 de 39 imagens sem descrição; listas longas.", "Receber os relatórios deste fundo, na página do fundo."),
    ("SPX", "spx", "Escolha Brasil ou Estados Unidos na entrada. Aviso contra golpes com o nome da casa. Página por estratégia e podcast.", "O aviso cobre a home inteira; sem título principal.", "Página fixa de segurança contra golpes."),
    ("Apollo", "apollo", "Seletor de público no topo. Página por estratégia, com caminho de navegação e tese. Ferramenta para assessores.", "36 MB na home.", "Página por estratégia com a tese em uma frase."),
    ("Ares", "ares", "Who We Serve separa públicos. Invest Online com um cartão por fundo e ação direta.", "Escolha de país obrigatória na entrada.", "Cartão por fundo com uma ação clara."),
    ("KKR", "kkr", "Dois caminhos: institucional e wealth. Página de crédito com quatro argumentos curtos.", "Abertura só institucional, sem produto.", "Quatro argumentos curtos por área."),
    ("Oaktree", "oaktree", "Menu Investors por tipo de investidor. Cadastro com nome, e-mail e país. Insights e podcast.", "Aviso de cookies enorme no celular.", "Cadastro com poucos campos."),
    ("Janus Henderson", "janus-henderson", "Central de assinaturas. Landing de CLO com o que é, por que a casa, time e riscos.", "Muro de aviso legal antes de entrar; 20 segundos para carregar.", "O roteiro da landing de produto complexo, para FIDC."),
    ("Golub", "golub", "Uma frase de posicionamento só (Raising the bar in private credit). Sponsors e Investors separados. Podcast em destaque. Acessibilidade.", "Pouco conteúdo de produto aberto.", "Posicionamento em uma linha."),
    ("TwentyFour", "twentyfour", "Diz na abertura que só faz renda fixa. Fundo com Preços e desempenho, Como investir e Documentos.", "Exige país e tipo de investidor antes de mostrar qualquer coisa.", "Abas Desempenho, Como investir e Documentos no fundo."),
]
_TIVIO_BOM = ["Home mais leve do grupo: 484 KB, contra 1 MB a 36 MB dos peers", "Quase todas as imagens com descrição (1 de 277 sem)", "Perguntas frequentes nas páginas de área, o que quase nenhum peer tem",
              "Onde investir em cada fundo, com as plataformas", "Carta do Gestor com versão em áudio", "Site em português e inglês"]
_TIVIO_MAL = ["Sem caminho por público: assessor, institucional e investidor caem no mesmo lugar", "Abertura em carrossel, sem uma frase de posicionamento", "Crédito Estruturado fica dentro de Fundos",
              "No celular a página rola para o lado", "Nenhuma forma de receber os relatórios de um fundo específico", "Sem busca ou filtro de fundos, com mais de 40 fundos no menu"]
_PROD = [  # área da Tivio, o que levar, de quem
    ("Todas as páginas de fundo", "Cabeçalho com risco, público, taxas, PL e início; abas Sobre, Desempenho, Documentos e Onde investir; botão Relatório do mês em destaque; Receber os relatórios deste fundo; Palavra do gestor com o comentário do mês",
     "Kinea, TwentyFour, BRAM, Valora"),
    ("Crédito Estruturado", "Hub próprio fora de Fundos e landing com o que é um FIDC, por que a Tivio, time e riscos; frase de foco na abertura", "Janus Henderson, Solis"),
    ("Crédito Privado", "Quatro argumentos curtos no topo da área; rentabilidade em gráfico contra o CDI", "KKR, BRAM"),
    ("Imobiliário", "Cotação de mercado e rendimentos na página de cada FII; Ofertas Públicas visível no menu", "Kinea, Fami Capital"),
    ("Investment Solutions", "Página por estratégia, com a tese em uma frase e os fundos daquela estratégia", "Apollo"),
    ("Private Solutions", "Cartão por fundo com uma ação clara e área do investidor para quem já investe", "Ares, Golub"),
    ("Site inteiro", "Escolha de público no topo (assessor, institucional, investidor); busca e filtro de fundos; página de segurança contra golpes; cadastro curto", "BRAM, Apollo, Kinea, SPX, Oaktree"),
]
_ORDEM = [("Agora", "Rodada de 13/11: newsletter, cookies, cores das áreas, banner, rodapé e correções"),
          ("Próxima rodada", "Modelo único de página de fundo, com cabeçalho de dados, abas, relatório do mês e assinatura por fundo"),
          ("Depois", "Hub de Crédito Estruturado e escolha de público no topo"),
          ("Por fim", "Busca e filtro de fundos, página de segurança e área do investidor")]

def _li(xs): return "<ul>" + "".join(f"<li>{x}</li>" for x in xs) + "</ul>"
_mat = ('<div class="tab bm-mat"><table><tr><th>Gestora</th>' + "".join(f"<th>{c}</th>" for c in _COLS) + "</tr>"
        + "".join(f'<tr{" class=bm-tv" if n == "Tivio" else ""}><td>{n}<small>{g}</small></td>' + "".join(f'<td data-r="{c}">{_OK if v else "<span class=bm-no>não vimos</span>"}</td>' for c, v in zip(_COLS, vs)) + "</tr>" for n, g, vs in _MAT)
        + "</table></div>")
_cards = '<div class="bm-peers">' + "".join(
    f'<section class="bm-p vidro"><a class="bm-img" href="bench/{s}-d-home.webp" target="_blank" rel="noopener"><img src="bench/{s}-d-home.webp" alt="Abertura do site da {n} no desktop" loading="lazy"></a>'
    f'<div class="bm-t"><h3>{n}</h3><dl><dt>Faz bem</dt><dd>{b}</dd><dt>Faz mal</dt><dd>{m}</dd><dt>Levar para a Tivio</dt><dd>{l}</dd></dl></div></section>' for n, s, b, m, l in _PEER) + "</div>"
_fundos = '<div class="bm-gal">' + "".join(f'<figure><a href="bench/{s}-d-produto.webp" target="_blank" rel="noopener"><img src="bench/{s}-d-produto.webp" alt="Página de produto da {n}" loading="lazy"></a><figcaption>{n}</figcaption></figure>'
                                         for n, s in [("Tivio", "tivio"), ("Kinea", "kinea"), ("BRAM", "bram"), ("Valora", "valora"), ("TwentyFour", "twentyfour"), ("Ares", "ares")]) + "</div>"
_cel = '<div class="bm-cel">' + "".join(f'<figure><img src="bench/{s}-m-home.webp" alt="Abertura do site da {n} no celular" loading="lazy"><figcaption>{n}</figcaption></figure>'
                                      for n, s in [("Tivio", "tivio"), ("Kinea", "kinea"), ("BRAM", "bram"), ("Valora", "valora"), ("Solis", "solis"), ("Golub", "golub")]) + "</div>"
_BM_CSS = """
.bm-mat td small{display:block;font-size:12px;color:var(--muted)}.bm-mat td{vertical-align:middle}.bm-mat .bm-tv td{font-weight:600}
.bm-mat{overflow-x:auto}.bm-mat table{min-width:640px}.bm-mat th,.bm-mat td{text-align:center}.bm-mat th:first-child,.bm-mat td:first-child{text-align:left;position:sticky;left:0;background:var(--bg-elev-1,var(--bg));z-index:1}
.bm-ok{width:20px;height:20px;color:var(--accent)}.bm-no{font-size:12px;color:var(--muted)}
.bm-peers{display:grid;gap:16px}.bm-p{display:grid;grid-template-columns:minmax(0,420px) minmax(0,1fr);gap:24px;padding:16px;align-items:start}
.bm-img img{width:100%;height:auto;display:block;border-radius:10px;border:1px solid var(--line)}
.bm-t h3{margin:4px 0 10px}.bm-t dl{margin:0;display:grid;gap:4px}.bm-t dt{font-weight:600;font-size:14px;margin-top:6px}.bm-t dd{margin:0;color:var(--muted);line-height:1.5}
.bm-gal{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.bm-gal img,.bm-cel img{width:100%;height:auto;display:block;border-radius:10px;border:1px solid var(--line)}
.bm-gal figcaption,.bm-cel figcaption{font-size:14px;color:var(--muted);margin-top:6px}.bm-gal figure,.bm-cel figure{margin:0}
.bm-cel{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px}
.bm-dois{display:grid;grid-template-columns:1fr 1fr;gap:16px}.bm-dois section{padding:20px}.bm-dois h3{margin:0 0 8px}.bm-dois ul{margin:0;padding-left:18px;line-height:1.6}
@media (max-width:820px){.bm-p{grid-template-columns:1fr}.bm-gal{grid-template-columns:1fr 1fr}.bm-cel{grid-template-columns:repeat(3,minmax(0,1fr))}.bm-dois{grid-template-columns:1fr}}
"""
corpo_bm = (cabecalho("Benchmark de sites", []) + '<div class="wrap">' + trilha(("index.html", "Início"), ("frente-digital.html", "Digital"), ("", "Benchmark de sites"))
    + '<section class="topo-peer"><div><h1>Benchmark de sites</h1><p class="lead">Os sites dos peers do portal, lidos em 13/11/2026: o que fazem bem, o que fazem mal e o que levar para cada produto da Tivio.</p></div></section>'
    + '<p class="secao-sub">16 gestoras lidas, 8 no Brasil e 8 lá fora, na home e numa página de produto, no computador e no celular. O site do Itaú Asset bloqueou a leitura automática, o que também afasta as IAs; o da PIMCO não respondeu.</p>'
    + '<h2 id="tivio">Onde a Tivio <strong>está</strong></h2><div class="bm-dois"><section class="vidro"><h3>Já fazemos melhor</h3>' + _li(_TIVIO_BOM) + '</section><section class="vidro"><h3>Ficamos para trás</h3>' + _li(_TIVIO_MAL) + "</section></div>"
    + '<h2 id="quem">Quem faz <strong>o quê</strong></h2><p class="secao-sub">O que estava visível sem login. "Não vimos" não quer dizer que o recurso não exista em outra parte do site.</p>' + _mat
    + '<h2 id="produtos">O que levar para <strong>cada produto</strong></h2><div class="tab tab-pilha"><table><tr><th>Na Tivio</th><th>O que levar</th><th>De quem</th></tr>'
    + "".join(f'<tr><td>{a}</td><td data-r="O que levar">{b}</td><td data-r="De quem">{c}</td></tr>' for a, b, c in _PROD) + "</table></div>"
    + '<h2 id="ordem">Ordem para <strong>aprovar</strong></h2><ol class="roteiro r6 as-o">' + "".join(f'<li class="vidro"><b>{a}</b><span>{b}</span></li>' for a, b in _ORDEM) + "</ol>"
    + '<p class="meta-txt">A rodada de agora está no <a href="site-espelho/revisoes/rodada-2026-11-13" target="_blank" rel="noopener">pedido de 13/11</a> e pode ser vista funcionando no <a href="site-espelho/" target="_blank" rel="noopener">site espelho</a>.</p>'
    + '<h2 id="paginas-fundo">Páginas de <strong>fundo</strong></h2>' + _fundos
    + '<h2 id="peers">Peer a <strong>peer</strong></h2>' + _cards
    + '<h2 id="celular">No <strong>celular</strong></h2><p class="secao-sub">Em quase todos, o aviso de cookies cobre metade da primeira tela.</p>' + _cel
    + '<p class="meta-txt">Leitura automática das páginas públicas em 13/11/2026, sem login. Peso da página medido no primeiro carregamento.</p><p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "benchmark-sites.html").write_text(pagina("Benchmark de sites", corpo_bm, CSS_P + _BM_CSS), encoding="utf-8")

# Estudo de envio automático para o site (SFTP / MZ IQ), a partir do relatório em Marketing/Estudos
try:
    import markdown as _md, pathlib as _pl
    _f = RAIZ / "Comunicação e Marketing" / "Marketing" / "Estudos" / "Estudo SFTP MZ IQ.md"
    _t = _f.read_text(encoding="utf-8").split("\n", 1)[1]
    _h = _md.markdown(_t, extensions=["tables", "fenced_code"])
    _h = _h.replace("<table>", '<div class="tab"><table>').replace("</table>", "</table></div>")
    _SF_CSS = ".sftp .tab{overflow-x:auto;max-width:100%}.sftp table{width:100%;table-layout:auto}.sftp td,.sftp th{word-break:break-word;overflow-wrap:anywhere;min-width:110px}.sftp a,.sftp :not(pre)>code{overflow-wrap:anywhere;word-break:break-word}.sftp h2{margin-top:44px}.sftp h3{margin:28px 0 10px}.sftp p,.sftp li{line-height:1.6;overflow-wrap:anywhere}.sftp pre{background:var(--card,rgba(127,127,127,.08));border:1px solid var(--line);border-radius:10px;padding:14px;overflow:auto;font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere;max-width:100%}.sftp pre code{white-space:pre-wrap;overflow-wrap:anywhere}.sftp code{font-size:.92em}"
    corpo_sf = (cabecalho("Envio automático para o site", []) + '<div class="wrap">' + trilha(("index.html", "Início"), ("frente-automacao.html", "Automação"), ("", "Envio automático para o site"))
        + '<section class="topo-peer"><div><h1>Envio automático para o site</h1><p class="lead">Estudo para o AutomaTivio publicar relatórios e o Resumo do Mês no site da MZ (MZ IQ), por SFTP ou API, com aprovação antes.</p></div></section>'
        + '<div class="sftp">' + _h + '</div><p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
    (EXTRA / "estudo-sftp.html").write_text(pagina("Envio automático para o site", corpo_sf, CSS_P + _SF_CSS), encoding="utf-8")
except Exception as _e:
    print("estudo sftp:", _e)
