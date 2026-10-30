# -*- coding: utf-8 -*-
# Executado depois de gerar_paginas.py: quebra a Central em categorias e subcategorias.
CATS = [
 ("estrategia", "Estratégia", [
   ("posicionamento", "Casa de estruturados", "O foco do ano, em quatro pilares."),
   ("sintese", "O que fazer", "Plano em 6 passos e os primeiros 90 dias."),
   ("sugestoes", "Sugestões", "12 ideias com público, impacto e esforço."),
   ("ideias", "Ideias na mesa", "A lista do time e eventos x conteúdo.")]),
 ("acoes", "Canais e ações", [
   ("posts", "Posts", "Plano por segmento, semana a semana."),
   ("eventos", "Eventos Itaú", "Os 16 eventos no escritório."),
   ("captacao", "Captação", "Landing pages, orgânico, pago, SEO e GEO."),
   ("copilot", "Copilot", "Agentes para montar no Copilot Studio.")]),
 ("referencias", "Referências", [
   ("cases", "Cases", "Avenue e AUVP."),
   ("peers", "Peers no Brasil", "Nove casas, cada uma com página."),
   ("estrangeiras", "Peers no exterior", "Oito casas, cada uma com página."),
   ("mercados", "Outros mercados", "Produtos digitais, educação e B2B técnico."),
   ("setores", "Outros setores", "Consultoria, M&amp;A, farmacêutica e mais."),
   ("mundo", "Mundo", "Mercados que sonhamos e parecidos com o Brasil.")]),
 ("base", "Base", [
   ("relatorio", "Relatório 2027", "Redes da Tivio e os 12 relatórios de mercado.")]),
]
IDS = [i for _, _, it in CATS for i, _, _ in it]
partes = re.split(r'(?=<h2 id="(?:%s)">)' % "|".join(IDS), corpo_mkt)
script_abas = re.search(r"<script>\s*\(function\(\)\{\s*var abas.*?</script>", corpo_mkt, re.S).group(0)
blocos = {}
for p in partes[1:]:
    i = re.match(r'<h2 id="(\w+)">', p).group(1)
    p = p.split('<p class="rodape">')[0]
    p = re.sub(r"<script>.*?</script>", "", p, flags=re.S)
    blocos[i] = p
ordem = [(f"m-{i}.html", n) for _, _, it in CATS for i, n, _ in it]

def trilha(*itens):
    pedacos = [f'<a href="{h}">{t}</a>' if h else f"<span>{t}</span>" for h, t in itens]
    return '<nav class="trilho" aria-label="Você está em">' + '<i>/</i>'.join(pedacos) + "</nav>"

pos = 0
for cid, cnome, itens in CATS:
    irmas = [(f"m-{i}.html", n) for i, n, _ in itens]
    for i, n, _ in itens:
        corpo = (cabecalho(cnome, irmas) + '<div class="wrap">'
                 + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), (f"marketing.html#{cid}", cnome), ("", n))
                 + blocos[i] + navegar(ordem, pos, f"marketing.html#{cid}", cnome)
                 + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>'
                 + (script_abas if i == "posts" else ""))
        (EXTRA / f"m-{i}.html").write_text(pagina(n, corpo, CSS_P), encoding="utf-8")
        pos += 1

# ---- segmentos da Tivio: subcategorias por fundo, e Imobiliário
FUNDOS = {"Crédito Estruturado": ["ALT 180", "ALT 90", "ALT Light", "Conexão ALT 180"],
          "Crédito Privado": ["Banks", "Institucional", "Institucional 15", "Institucional 30", "Infra Plus", "Infra Plus CDI", "Esplanada", "Legacy Prev", "RF CP", "BVP"],
          "Investment Solutions": ["Top Gestor", "Top Gestor HY", "RF Ativo", "Macro", "Long Only", "Top Manager Global", "Prev Low Vol", "Prev Top Credit"],
          "Previdência": ["HGD30", "HYD60"], "Imobiliário": ["FIIs da vertical"]}
SEG_PEERS = {"Crédito Estruturado": ["solis", "anga", "valora", "itau-asset", "janus-henderson", "golub", "twentyfour"],
             "Crédito Privado": ["kinea", "spx", "bram", "oaktree", "pimco"],
             "Investment Solutions": ["itau-asset", "fami-capital", "kkr"],
             "Previdência": ["bram", "spx", "galapagos"],
             "Imobiliário": ["galapagos", "valora", "spx"],
             "Marca e eventos": ["bram", "solis", "ares", "apollo"]}
porta = {p["slug"]: p for p in PEERS}
SEGS = list(SEGMENTOS) + [("imob", "imobiliario", "Imobiliário")]
lista_s = [(f"segmento-{s}.html", n) for _, s, n in SEGS]
base_m2 = ler("mkt_corpo.html")
for j, (k, s, n) in enumerate(SEGS):
    m_pl = re.search(rf'<section class="plano vidro" id="pl-{k}".*?</section>', base_m2, re.S)
    plano = m_pl.group(0).replace(" hidden", "", 1).replace('role="tabpanel"', "") if m_pl else ""
    plano = re.sub(r'<a class="ver-pagina".*?</a>', "", plano)
    if not m_pl:
        plano = '<section class="vidro bloco"><h2>Plano de posts</h2><p>Ainda não definido. A Central de Materiais mostra o carrossel do segmento como em produção.</p></section>'
    c_a = re.search(rf'<article class="seg vidro">\s*<p class="seg-nome"><i></i>{re.escape(n)}</p>.*?</article>', ler("segmentos.html"), re.S)
    auto = f'<h2>No <strong>AutomaTivio</strong></h2><div class="segmentos um">{c_a.group(0)}</div>' if c_a else ""
    fund = FUNDOS.get(n)
    subs = ('<h2>Fundos do <strong>segmento</strong></h2><div class="atalhos">' + "".join(f"<span>{f}</span>" for f in fund) + "</div>") if fund else ""
    ps = "".join(f'<a class="mini vidro" href="peer-{x}.html">{logo(porta[x]["nome"])}<span>{porta[x]["nome"]}</span></a>' for x in SEG_PEERS[n])
    corpo = (cabecalho(n, []) + '<div class="wrap">'
             + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("marketing.html#segmentos", "Segmentos"), ("", n))
             + f'<section class="topo-peer"><div><p class="eyebrow"><i></i>Segmento da Tivio</p><h1>{n}</h1></div></section>'
             + plano + subs + auto + f'<h2>Peers para <strong>acompanhar</strong></h2><div class="minis">{ps}</div>'
             + navegar(lista_s, j, "marketing.html#segmentos", "Segmentos")
             + '<p class="rodape">Plano em construção, para validar com o time e com Riscos.</p></div>')
    (EXTRA / f"segmento-{s}.html").write_text(pagina(n, corpo, CSS_P), encoding="utf-8")

# ---- públicos que vamos atacar
PUBLICOS = [
 ("assessor", "Assessor", "Indica o produto ao cliente e é o maior gargalo: nos EUA, só 16% dizem conhecer bem os fundos semilíquidos.",
  "Entender estruturados o bastante para explicar ao cliente.",
  ["Hub de estruturados e glossário", "Kit com carta mensal, roteiro e convite rastreado", "Imersão FIDC em 3 aulas", "Guia \"Nem todo FIDC sênior é igual\"", "Biblioteca de objeções"],
  "Inscritos por link, presença nas aulas e pedidos de conversa.", ["kkr", "janus-henderson", "twentyfour"]),
 ("gerente", "Gerente", "Recebe a pergunta do cliente na agência, com pouco tempo. Os 16 eventos com o Itaú são a porta de entrada.",
  "Uma explicação curta e segura, sem virar especialista.",
  ["Versão de 20 minutos da trilha, com perguntas de cliente", "Eventos como módulos, com regra de marca aprovada", "Matriz Tivio para desenhar em segundos"],
  "Presença por evento, conclusão do material e pedidos de reunião.", ["bram", "itau-asset"]),
 ("institucional", "Institucional", "RPPS, fundos de pensão, seguradoras e family offices. Cada um segue uma regra própria, decide em comitê e pede dado. Os fundos de pensão somavam R$ 1,438 trilhão em junho de 2026 (Abrapp).",
  "Saber se o fundo cabe na regra dele, com tese, governança e prova de processo.",
  ["Ficha de enquadramento por fundo e por tipo de investidor, conferida por Riscos e Compliance", "Material pronto para comitê e para consultorias de investimento", "Radar trimestral de crédito estruturado", "Carta trimestral em PDF e áudio", "\"O que pode dar errado\" por fundo"],
  "Reuniões qualificadas e pedidos de due diligence.", ["valora", "bram", "itau-asset"]),
 ("originador", "Originador", "Empresas que cedem recebíveis. Quem nunca fez um FIDC decide mais pelo ranking e pela reputação.",
  "Saber se um FIDC faz sentido e como chegar lá.",
  ["Página para tomadores, com cases e formulário", "Benchmark anual do custo de captar", "Programa \"Primeiro FIDC\" com seis empresas por ano", "Dossiê de reputação"],
  "Contatos de empresas e operações iniciadas.", ["solis", "anga"]),
 ("universitario", "Universitário", "Os futuros assessores e gestores, e o caminho para atrair talentos.",
  "Aprender na prática e entrar no mercado.",
  ["Bootcamp", "Desafio de Estruturação com ligas e banca", "Residência em estruturados com universidade"],
  "Ligas participantes, inscritos e talentos contratados.", ["fami-capital"]),
 ("investidor", "Investidor", "Contas de varejo em FIDC foram de 147,3 mil para 333,7 mil em cerca de um ano. A Tivio chega a ele pelo intermediário.",
  "Entender o risco antes de investir.",
  ["Escola aberta de estruturados, sem login", "Conteúdo de risco antes do produto", "Matriz Tivio pública"],
  "Tempo nas páginas, buscas e citações em IA.", ["kinea", "galapagos"]),
]
lista_p = [(f"publico-{p[0]}.html", p[1]) for p in PUBLICOS]
CENARIO_P = {"institucional": '''<h2>Cenário <strong>brasileiro</strong></h2>
<div class="tab"><table>
  <tr><th>Quem</th><th>Regra</th><th>O que muda para nós</th></tr>
  <tr><td>RPPS</td><td>CMN 5.272, em vigor desde 02/02/2026</td><td>A certificação Pró-Gestão define limites e ativos permitidos. Cota sênior de FIDC tem teto de 20%.</td></tr>
  <tr><td>Fundos de pensão</td><td>CMN 4.994, alterada pela 5.202 em 2025</td><td>FIDC entra em renda fixa, com limite de concentração por classe de cota.</td></tr>
  <tr><td>Seguradoras</td><td>CMN 4.993</td><td>O limite de FIDC também vale por classe de cota.</td></tr>
  <tr><td>Family offices</td><td>Sem regra de alocação como as demais</td><td>A decisão segue o mandato da família e a relação com quem faz a gestão.</td></tr>
</table></div>
<p class="meta-txt">Resumo para orientar o conteúdo. Limites e enquadramento de cada fundo precisam ser confirmados com Riscos e Compliance antes de qualquer peça.</p>'''}
for j, (s, n, quem, quer, acoes, mede, refs) in enumerate(PUBLICOS):
    ac = "".join(f"<li>{a}</li>" for a in acoes)
    ps = "".join(f'<a class="mini vidro" href="peer-{x}.html">{logo(porta[x]["nome"])}<span>{porta[x]["nome"]}</span></a>' for x in refs)
    corpo = (cabecalho(n, []) + '<div class="wrap">'
             + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("marketing.html#publicos", "Públicos"), ("", n))
             + f'<section class="topo-peer"><div><p class="eyebrow"><i></i>Público que vamos atacar</p><h1>{n}</h1><p class="lead">{quem}</p></div></section>'
             + f'<section class="destaque aprende vidro"><p class="seg-nome"><i></i>O que essa pessoa precisa</p><p class="grande">{quer}</p></section>'
             + f'<div class="blocos"><section class="vidro bloco"><h2>O que vamos fazer</h2><ul>{ac}</ul></section><section class="vidro bloco"><h2>Como medir</h2><p>{mede}</p></section></div>'
             + CENARIO_P.get(s, "")
             + f'<h2>Referências para <strong>olhar</strong></h2><div class="minis">{ps}</div>'
             + navegar(lista_p, j, "marketing.html#publicos", "Públicos")
             + '<p class="rodape">Proposta para validar com o time e com Riscos.</p></div>')
    (EXTRA / f"publico-{s}.html").write_text(pagina(n, corpo, CSS_P), encoding="utf-8")

# ---- capa da Central: categorias e subcategorias
def cartoes(itens):
    return '<div class="subs">' + "".join(f'<a class="sub vidro" href="{h}"><b>{t}</b><span>{d}</span></a>' for h, t, d in itens) + "</div>"
capa = partes[0].split('<div class="wrap">', 1)[1]
kpi = re.search(r'<div class="kpis">.*?</div>\s*</div>', capa, re.S)
hero_c = re.search(r'<section class="hero">.*?</section>', capa, re.S).group(0)
kpis_c = capa[capa.index('<div class="kpis">'):capa.index('<p class="meta-txt">')]
secs = [f'<h2 id="segmentos">Segmentos da <strong>Tivio</strong></h2>' + cartoes([(f"segmento-{s}.html", n, ", ".join(FUNDOS.get(n, ["Posts, eventos e marca"])[:3])) for _, s, n in SEGS]),
        f'<h2 id="publicos">Públicos que vamos <strong>atacar</strong></h2>' + cartoes([(f"publico-{p[0]}.html", p[1], p[3]) for p in PUBLICOS])]
for cid, cnome, itens in CATS:
    extra_c = [("calendario.html", "Calendário 2027", "Feriados, datas de dinheiro e ações."), ("brand.html", "Brand", "Polo com o logo bordado."), ("estrutura.html", "Estrutura", "Frentes da área e fluxo de aprovação.")] if cid == "acoes" else []
    secs.append(f'<h2 id="{cid}">{cnome}</h2>' + cartoes(extra_c + [(f"m-{i}.html", n, d) for i, n, d in itens]))
abas_c = [("segmentos", "Segmentos"), ("publicos", "Públicos")] + [(c, n) for c, n, _ in CATS]
corpo = (cabecalho("Central de Marketing", abas_c) + '<div class="wrap">' + trilha(("index.html", "Início"), ("", "Central de Marketing"))
         + hero_c + kpis_c + "".join(secs) + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing. Planos em construção.</p></div>')
(SAIDA / "marketing.html").write_text(pagina("Central de Marketing Tivio", corpo, CSS_P), encoding="utf-8")

# ---- links antigos com âncora passam a apontar para as páginas novas
for f in list(EXTRA.glob("*.html")):
    t = f.read_text(encoding="utf-8")
    n = re.sub(r'href="marketing\.html#(%s)"' % "|".join(IDS), r'href="m-\1.html"', t)
    n = n.replace('href="#cases"', 'href="m-cases.html"')
    if n != t:
        f.write_text(n, encoding="utf-8")
print("total extras:", len(list(EXTRA.glob("*.html"))))

# ---- página inicial: o todo em um lugar
inicio = (cabecalho("", []) + '<div class="wrap">'
          + hero("Tivio Capital", "Comunicação &amp; <strong>Marketing</strong>", "Tudo do time em um lugar: a automação mensal dos materiais e o plano de marketing de 2027.")
          + cartoes([("automativio.html", "AutomaTivio", "A edição mensal em um comando, com download e como funciona."), ("marketing.html", "Central de Marketing", "Estratégia, ações e referências para 2027.")])
          + '<h2>Times do <strong>AutomaTivio</strong></h2>' + cartoes([("automativio-gestao.html", "Gestão", "Comentários e tabela de spreads."), ("automativio-riscos.html", "Riscos", "Aprovação de cada material."), ("automativio-marketing.html", "Marketing", "Dados, rodada, decks, publicação e histórico.")])
          + "".join(secs) + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "index.html").write_text(pagina("Comunicação & Marketing", inicio, CSS_P), encoding="utf-8")

# ---- Visão: a conclusão de tudo, o que queremos para a Tivio
_a = ler("analise_corpo.html")
_sec = {t: b for t, b in re.findall(r'(<h2>.*?</h2>)(.*?)(?=<h2>|<div class="parte">|<p class="rodape">)', _a, re.S)}
def _pega26(trecho):
    return next(t + b for t, b in _sec.items() if trecho in t)
visao = (cabecalho("", []) + '<div class="wrap">' + trilha(("index.html", "Início"), ("", "Visão"))
         + hero("A conclusão de tudo", "<strong>Visão</strong>", "O que queremos para a Tivio Capital.")
         + ler("visao_corpo.html").replace("{{BLOCO2025}}", '<section data-anos="2025">' + _pega26("2025: o <strong>ano") + "</section>").replace("{{BLOCO2026}}", '<section data-anos="2026">' + _pega26("o <strong>negócio</strong>") + _pega26("uma página") + "</section>") + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "visao.html").write_text(pagina("Visão", visao, CSS_P), encoding="utf-8")
