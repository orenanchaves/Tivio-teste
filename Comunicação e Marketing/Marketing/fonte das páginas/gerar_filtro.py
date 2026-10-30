# -*- coding: utf-8 -*-
# Executado por último: página que busca e filtra todas as outras.
import html as _h
def _texto(arq):
    t = arq.read_text(encoding="utf-8")
    t = re.sub(r"<(style|script|header|svg)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<nav[^>]*>.*?</nav>", " ", t, flags=re.S)
    t = re.sub(r"<h[12][^>]*>.*?</h[12]>", " ", t, count=1, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", _h.unescape(t)).strip()

TIPOS = [("peer-", "Peers"), ("segmento-", "Segmentos"), ("publico-", "Públicos"), ("setor-", "Setores"), ("m-", "Central"), ("automativio", "AutomaTivio")]
SEG_T = {"Crédito Estruturado": r"cr[ée]dito estruturado|fidc|estruturados", "Crédito Privado": r"cr[ée]dito privado|high grade", "Investment Solutions": r"investment solutions|top gestor",
         "Previdência": r"previd[êe]ncia|hgd30|hyd60", "Imobiliário": r"imobili[áa]rio|\bfiis?\b"}
PUB_T = {p: p.lower().replace("á", "[áa]") for p in ("Assessor", "Gerente", "Institucional", "Originador", "Universitário", "Investidor")}
itens = []
fontes_f = sorted(EXTRA.glob("*.html")) + [SAIDA / n for n in ("marketing.html", "automativio.html", "automativio-gestao.html", "automativio-riscos.html", "automativio-marketing.html")]
for f in fontes_f:
    if f.name in ("index.html", "buscar.html"):
        continue
    tx = _texto(f)
    titulo = re.search(r"<title>(.*?)</title>", f.read_text(encoding="utf-8"), re.S).group(1)
    tipo = next((n for pre, n in TIPOS if f.name.startswith(pre)), "Central")
    baixo = tx.lower()
    # só marca quando o assunto pesa na página, não numa citação solta
    segs = [k for k, v in SEG_T.items() if len(re.findall(v, baixo)) >= 2 or k.lower() in titulo.lower()]
    pubs = [k for k, v in PUB_T.items() if len(re.findall(v, baixo)) >= 2 or k.lower() == titulo.lower()]
    itens.append({"u": f.name, "t": titulo, "k": tipo, "s": segs, "p": pubs, "x": baixo[:9000], "r": tx[:130].rsplit(" ", 1)[0] + "..."})

def _chips(grupo, vals):
    return "".join(f'<button type="button" class="fchip" data-g="{grupo}" data-v="{v}" aria-pressed="false">{v}</button>' for v in vals)
tipos_v = [n for _, n in TIPOS]
corpo_f = (cabecalho("", []) + '<div class="wrap">' + trilha(("index.html", "Início"), ("", "Pesquisar"))
  + '<section class="topo-peer"><div><p class="eyebrow"><i></i>Tudo em um lugar</p><h1>Pesquisar <strong>tudo</strong></h1></div></section>'
  + '<label class="busca" for="q"><span>Pesquisa</span><input id="q" type="search" placeholder="Escreva um nome ou assunto, como FIDC, Solis ou eventos" autocomplete="off"></label>'
  + f'<div class="fgrupo"><b>Tipo</b>{_chips("k", tipos_v)}</div>'
  + f'<div class="fgrupo"><b>Segmento</b>{_chips("s", list(SEG_T))}</div>'
  + f'<div class="fgrupo"><b>Público</b>{_chips("p", list(PUB_T))}</div>'
  + '<div class="fbarra"><span id="fconta" role="status"></span><button type="button" class="flimpa" id="flimpa">Limpar</button></div>'
  + '<div class="subs" id="fres"></div><p class="meta-txt" id="fvazio" hidden>Nada encontrado. Tire um filtro ou mude a busca.</p>'
  + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>'
  + '<script>var ITENS=' + json.dumps(itens, ensure_ascii=False).replace("</", "<\\/") + ';</script><script>' + ler("filtro.js") + '</script>')
(EXTRA / "buscar.html").write_text(pagina("Pesquisar", corpo_f, CSS_P), encoding="utf-8")
print("filtro:", len(itens))
