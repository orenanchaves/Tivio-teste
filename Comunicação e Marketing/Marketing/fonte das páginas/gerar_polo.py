import pathlib
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
    + '<section class="topo-peer"><div><h1>Brand</h1></div></section>' + _chips + _slogan + _ds + _dir
    + f'<h2 id="polo">Polo</h2><div class="polos">{_fig}</div>' + _feed_h
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>' + _lb)
(EXTRA / "brand.html").write_text(pagina("Brand", corpo_polo, CSS_P), encoding="utf-8")

FRENTES_E = [("Coordenação, Design estratégico &amp; Automação", "Renan Chaves", ["Direção de arte", "Identidade e design system", "KV de campanha", "Templates", "Decks e apresentações", "Aprovação visual final", "Prioridades", "Materiais e fechamento", "Automação", "Dados e performance", "C&amp;M Hub", "Governança", "Interface com Enrico Trotta"]),
             ("Conteúdo &amp; Comunicação", "Fernanda Acquati", ["Calendário editorial", "Redes sociais", "Dashboard de redes sociais", "Comunicação interna", "Tivio News", "Textos e legendas", "Publicação", "Moderação", "Aprovações", "Eventos, de ponta a ponta", "Imprensa", "Gestão de orçamento"]),
             ("Design operacional &amp; Produção", "Gabriel Fiorilli", ["Peças de social a partir do KV e dos templates", "Desdobramentos e formatos", "Vídeo e motion", "Ajustes e versões finais"])]
_org = ('<div class="org"><div class="org-n vidro"><span>Direção</span><b>Enrico Trotta</b></div><i class="org-l"></i>'
        '<div class="org-n vidro"><span>Coordenação, Design estratégico &amp; Automação</span><b>Renan Chaves</b></div><i class="org-l"></i>'
        '<div class="org-3 org-fim org-dois"><div class="org-n vidro"><span>Design operacional &amp; Produção</span><b>Gabriel Fiorilli</b></div><div class="org-n vidro"><span>Conteúdo &amp; Comunicação</span><b>Fernanda Acquati</b></div></div><i class="org-l"></i><div class="org-3 org-fim org-baixo org-b1"><div class="org-n org-ext"><span>Agência parceira</span><b>ColaAí</b><em>Vídeo, carrosséis e tráfego pago</em></div></div>'
        '<div class="org-t"><span>Eventos</span>Fernanda Acquati, de ponta a ponta</div></div>')
_antes = ('<div class="org"><div class="org-n vidro"><span>Direção</span><b>Enrico Trotta</b></div><i class="org-l"></i>'
          '<div class="org-n vidro org-hub"><span>Hub da área</span><b>Cesar Medeiros</b></div><i class="org-l"></i>'
          '<div class="org-3">' + "".join(f'<div class="org-n vidro"><span>{a}</span><b>{b}</b></div>' for a, b in [("Materiais, dados e automação", "Renan Chaves"), ("Conteúdo e fluxo editorial", "Fernanda Acquati"), ("Design e produção visual", "Gabriel Fiorilli")]) + '</div>'
          '<div class="org-t"><span>Agência parceira</span>ColaAí</div></div>'
          '<div class="tab"><table><tr><th>Quem</th><th>O que fazia</th></tr>'
          + "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in [("Cesar Medeiros", "Coordenação, prioridades, interface com Enrico Trotta, agência, fornecedores, aprovações e grandes eventos"), ("Renan Chaves", "Materiais, decks, relatórios, fechamento, dados, digital e automação"), ("Fernanda Acquati", "Conteúdo, pauta, redes sociais, aprovações, organização e eventos"), ("Gabriel Fiorilli", "Design, identidade visual, peças, materiais, vídeos e produção visual"), ("Agência ColaAí", "Peças, vídeo e motion, planejamento editorial, legendas, publicação, moderação, mídia paga, performance e relatório")]) + '</table></div>')
def _col(tit, sub, nos):
    return f'<section class="fase{" fase-antes" if tit == "Antes" else " fase-dest"}"><p class="fase-t">{tit}</p><p class="fase-s">{sub}</p>' + "".join(f'<div class="fase-n{" " + c if c else ""}"><span>{a}</span><b>{b}</b></div>' for a, b, c in nos) + '</section>'
_fases = '<div class="fases">' + _col("Antes", "Coordenação central", [("Direção", "Enrico Trotta", ""), ("Hub da área", "Cesar Medeiros", "hub"), ("Materiais, dados e automação", "Renan Chaves", ""), ("Conteúdo e fluxo editorial", "Fernanda Acquati", ""), ("Design e produção visual", "Gabriel Fiorilli", ""), ("Agência parceira", "ColaAí", "ext")]) \
    + _col("Agora", "Frentes com responsáveis", [("Direção", "Enrico Trotta", ""), ("Coordenação, design estratégico, dados e automação", "Renan Chaves", "hub"), ("Conteúdo &amp; Comunicação", "Fernanda Acquati", ""), ("Design operacional &amp; Produção", "Gabriel Fiorilli", ""), ("Agência parceira", "ColaAí", "ext"), ("Tráfego pago", "Ewerton", "ext")]) \
    + _col("Futuro", "Frentes consolidadas", [("Direção", "Enrico Trotta", ""), ("Coordenação, design estratégico, dados e automação", "Renan Chaves", "hub"), ("Conteúdo &amp; Comunicação", "Fernanda Acquati", ""), ("Design operacional &amp; Produção", "Gabriel Fiorilli", ""), ("Pessoa de apoio", "A definir", ""), ("Tráfego pago", "Ewerton", "ext"), ("Apoio externo", "A definir", "ext")]) + '</div>'
_fr = "".join(f'<section class="frente vidro"><h3>{n}</h3><p class="dono">{d}</p><ul>' + "".join(f"<li>{x}</li>" for x in l) + "</ul></section>" for n, d, l in FRENTES_E)
_pap = "".join(f'<div class="papel vidro"><span>{a}</span><b>{b}</b></div>' for a, b in [("Eventos de ponta a ponta", "Fernanda Acquati"), ("Aprovação estratégica", "Enrico Trotta")])
_fl = "".join(f'<li class="vidro"><b>{a}</b><span>{b}</span></li>' for a, b in [("Demanda entra", "Pedido registrado em um lugar só"), ("Triagem", "Definição do responsável"), ("Produção", "Execução pela frente dona"), ("Aprovação técnica", "Revisão e Compliance"), ("Aprovação estratégica", "Quando necessária"), ("Publicação", "Publicação e mensuração")])
_dist_p = [("r", "Renan Chaves", "Coordenação, Design estratégico &amp; Automação", ["Design estratégico", "Materiais e decks", "Dados e automação"]),
           ("f", "Fernanda Acquati", "Conteúdo &amp; Comunicação", ["Conteúdo", "Redes sociais"]),
           ("g", "Gabriel Fiorilli", "Design operacional &amp; Produção", ["Design operacional", "Peças e vídeos"])]
_dist_i = [("Coordenação", "r"), ("Prioridades", "r"), ("Interface com Enrico Trotta", "r"), ("Eventos: coordenação", "f"), ("Aprovações", "f"), ("Eventos: operação", "f"), ("Agência", "f"), ("Fornecedores", "f"), ("Eventos: peças", "f")]
_mov = ('<h2>Para onde foi <strong>cada função</strong></h2><div class="dist" id="dist"><svg class="dist-l" id="dist-l" aria-hidden="true"></svg>'
    + '<div class="dist-o vidro" id="dist-o"><span>O que o Cesar fazia</span><b>Cesar Medeiros</b><div class="dist-c" id="dist-oc">'
    + "".join(f'<i class="dist-i" data-d="{d}">{n}</i>' for n, d in _dist_i) + '</div></div><div class="dist-d">'
    + "".join(f'<div class="dist-p vidro" id="dist-{i}"><div class="dist-t"><div><span>{c}</span><b>{n}</b></div><em class="dist-n"></em></div><div class="dist-c">'
              + "".join(f'<i class="dist-i dist-b">{b}</i>' for b in bs) + '</div></div>' for i, n, c, bs in _dist_p)
    + '</div><button type="button" class="mov-b" id="dist-b">Ver de novo</button></div>'
    + """<script>(function(){var R=document.getElementById('dist');if(!R)return;
var O=document.getElementById('dist-oc'),C=document.getElementById('dist-o'),L=document.getElementById('dist-l'),I=[].slice.call(O.children),G=['r','f','g'].filter(function(i){return O.querySelector('[data-d="'+i+'"]')}),T=[],A=[],F=[],fim=false;
var parado=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
function cx(i){return document.getElementById('dist-'+i)}
function alvo(e){return cx(e.dataset.d).querySelector('.dist-c')}
function dos(i){return I.filter(function(e){return e.dataset.d===i})}
function estreito(){return getComputedStyle(R).gridTemplateColumns.split(' ').length<2}
function caixa(e){var a=e.getBoundingClientRect(),b=R.getBoundingClientRect();return{l:a.left-b.left,t:a.top-b.top,r:a.right-b.left,b:a.bottom-b.top,x:(a.left+a.right)/2-b.left,y:(a.top+a.bottom)/2-b.top}}
function curva(a,b){if(estreito())return[a,{x:6,y:a.y},{x:6,y:b.y},b];var d=Math.max(40,(b.x-a.x)*.5);return[a,{x:a.x+d,y:a.y},{x:b.x-d,y:b.y},b]}
function ponto(c,t){var u=1-t,k=[u*u*u,3*u*u*t,3*u*t*t,t*t*t];return{x:k[0]*c[0].x+k[1]*c[1].x+k[2]*c[2].x+k[3]*c[3].x,y:k[0]*c[0].y+k[1]*c[1].y+k[2]*c[2].y+k[3]*c[3].y}}
function linha(i){var o=caixa(C),p=caixa(cx(i)),a=estreito()?{x:6,y:o.b}:{x:o.r,y:o.y},b=estreito()?{x:p.l,y:p.y}:{x:p.l,y:p.y},c=curva(a,b),s=document.createElementNS('http://www.w3.org/2000/svg','path');
s.setAttribute('d','M'+c[0].x+' '+c[0].y+'C'+c[1].x+' '+c[1].y+' '+c[2].x+' '+c[2].y+' '+c[3].x+' '+c[3].y);s.dataset.g=i;L.appendChild(s);return s}
function limpa(){T.forEach(clearTimeout);T=[];A.forEach(function(a){a.cancel()});A=[];F.forEach(function(x){x.remove()});F=[];L.innerHTML='';fim=false;C.classList.remove('fim');I.forEach(function(e){O.appendChild(e);e.classList.remove('foi')});G.forEach(function(i){cx(i).classList.remove('ativo','feito');cx(i).querySelector('.dist-n').textContent=''})}
function final(){I.forEach(function(e){alvo(e).appendChild(e);e.classList.add('foi')});G.forEach(function(i){cx(i).classList.add('feito');cx(i).querySelector('.dist-n').textContent='+'+dos(i).length;linha(i).classList.add('on')});C.classList.add('fim');fim=true}
function trava(){[].forEach.call(R.querySelectorAll('.dist-p .dist-c,#dist-oc'),function(c){c.style.minHeight=''});I.forEach(function(e){alvo(e).appendChild(e)});[].forEach.call(R.querySelectorAll('.dist-p .dist-c'),function(c){c.style.minHeight=c.offsetHeight+'px'});I.forEach(function(e){O.appendChild(e)});O.style.minHeight=O.offsetHeight+'px'}
function voa(e){var f=document.createElement('i');f.className='dist-i dist-v';f.textContent=e.textContent;e.parentNode.insertBefore(f,e);F.push(f);var a=caixa(e);alvo(e).appendChild(e);e.classList.add('foi');var b=caixa(e),c=curva({x:a.x,y:a.y},{x:b.x,y:b.y}),q=[],n=28;
for(var k=0;k<=n;k++){var t=k/n,s=t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2,p=ponto(c,s);q.push({transform:'translate('+(p.x-b.x)+'px,'+(p.y-b.y)+'px) scale('+(1+.1*Math.sin(Math.PI*t))+')'})}
if(e.animate){var m=e.animate(q,{duration:850,easing:'linear'});A.push(m);m.onfinish=function(){var w=e.animate([{transform:'scale(1)'},{transform:'scale(1.08)'},{transform:'scale(1)'}],{duration:260});A.push(w)}}}
function grupo(i,t){var E=dos(i),P=cx(i),n=P.querySelector('.dist-n');T.push(setTimeout(function(){P.classList.add('ativo');var s=linha(i),z=s.getTotalLength();s.classList.add('on');if(s.animate){var d=s.animate([{strokeDasharray:z,strokeDashoffset:z},{strokeDasharray:z,strokeDashoffset:0}],{duration:520,easing:'ease-out'});A.push(d)}},t));
E.forEach(function(e,j){var u=t+320+j*280;T.push(setTimeout(function(){voa(e)},u));T.push(setTimeout(function(){n.textContent='+'+(j+1)},u+800))});
var z=t+320+(E.length-1)*280+850+260;T.push(setTimeout(function(){P.classList.remove('ativo');P.classList.add('feito')},z));return z+160}
function roda(){limpa();trava();if(parado){final();return}var t=450;G.forEach(function(i){t=grupo(i,t)});T.push(setTimeout(function(){C.classList.add('fim');fim=true},t))}
document.getElementById('dist-b').addEventListener('click',roda);
trava();final();if(!parado&&window.IntersectionObserver){var v=new IntersectionObserver(function(es){if(es[0].isIntersecting){v.disconnect();roda()}},{threshold:.3});v.observe(R)}
var r;addEventListener('resize',function(){clearTimeout(r);r=setTimeout(function(){if(fim){limpa();trava();final()}},200)})
})();</script>""")
corpo_est = (cabecalho("Estrutura", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("", "Estrutura"))
    + f'<section class="topo-peer"><div>{ICO27["Estrutura"]}<h1>Estrutura</h1><p class="lead">Quem faz o quê em Comunicação &amp; Marketing e como uma demanda anda.</p></div></section>'
    + '<h2>Como a área <strong>se organiza</strong></h2>' + _org
    + _mov
    + '<h2>O que cada frente <strong>cobre</strong></h2><div class="frentes linhas">' + _fr + '</div>'
    + '<h2>Agência <strong>parceira</strong></h2><div class="frentes linhas"><section class="frente vidro"><h3>Agência parceira</h3><p class="dono">ColaAí</p><ul><li>Vídeo</li><li>Carrosséis, inclusive o da Carta do Gestor</li><li>Tráfego pago, com Ewerton</li></ul></section><section class="frente vidro"><h3>Como pedir</h3><p class="dono">Pela Fernanda Acquati</p><ul><li>Pedido pela Fernanda Acquati</li><li>Produção na ColaAí</li><li>Revisão e Compliance</li><li>Publicação</li><li>Relatório de tráfego para o Renan Chaves</li></ul></section></div>'
    + '<h2>Como uma demanda <strong>anda</strong></h2><ol class="roteiro r6">' + _fl + '</ol>'
    + ''
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
    + '<section class="topo-peer"><div><h1>Eventos do mercado</h1><p class="lead">Onde cada segmento se encontra. A leitura serve para escolher poucos eventos e levar a mesma tese de estruturados.</p></div></section>'
    + '<div class="analise"><div class="vidro"><h3>O que a análise mostra</h3><ul><li>Assessores têm a agenda mais cheia, e é onde a Tivio fala com quem indica</li><li>Crédito privado ganhou congresso próprio da Anbima em 2026</li><li>Nenhum evento dedicado a estruturados apareceu na pesquisa, o que abre espaço para os 16 encontros com o Itaú</li></ul></div>'
    + '<div class="vidro"><h3>Sugestão para 2027</h3><ul><li>Marcar presença em poucos eventos, com porta-voz e tese definidos</li><li>Priorizar Anbima, Advisor Talks e Abrapp</li><li>Evitar choque de data com os 16 encontros</li></ul></div></div>'
    + _ev + '<p class="meta-txt">As datas são da última edição encontrada. As de 2027 ainda precisam ser confirmadas com cada organizador, e as prioridades são proposta do time. Não foram encontradas datas de eventos da Uqbar, ANFIDC, Aneprem, Abipem ou Anbima para institucionais.</p>'
    + '<p class="fontes-peer"><b>Fontes</b>' + "".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in _fontes) + '</p>'
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "eventos-mercado.html").write_text(pagina("Eventos do mercado", corpo_ev, CSS_P), encoding="utf-8")

_passos = "".join(f'<li class="vidro"><b>{a}</b><span>{b}</span></li>' for a, b in [("Oferta aprovada", "Riscos e Compliance liberam o que pode ser dito"), ("Peça curta", "Gabriel Fiorilli monta o card no padrão do canal"), ("Publicação", "Fernanda Acquati publica pelo número da Tivio"), ("Link rastreado", "Renan Chaves mede cliques e pedidos de material"), ("Assessor age", "Abre o material aprovado e fala com a Tivio")])
_fontes_c = [("Canal e comunidade", "https://canaltech.com.br/apps/qual-a-diferenca-entre-canal-e-comunidade-no-whatsapp/"), ("Comunidades", "https://tecnoblog.net/responde/comunidade-do-whatsapp-o-que-e-e-como-funciona-a-ferramenta-que-reune-grupos/"), ("Canais para empresas", "https://www.infobip.com/pt/blog/canais-do-whatsapp"), ("Resolução CVM 160", "https://lefosse.com/noticias/resolucao-cvm-160-novo-arcabouco-regulatorio-de-ofertas-publicas/"), ("Período de silêncio", "https://renovainvest.com.br/blog/periodo-de-silencio-o-que-e-e-como-ele-funciona-no-mercado-financeiro/")]
corpo_canal = (cabecalho("Canal de ofertas", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Canal de ofertas"))
    + '<section class="topo-peer"><div><h1>Canal de ofertas</h1><p class="lead">Um canal de WhatsApp para assessores, no estilo dos canais de desconto: aviso curto, prazo claro e um link. Operado dentro da Tivio Capital.</p></div></section>'
    + '<div class="canal"><div class="zap vidro"><p class="zap-t">Tivio Ofertas</p><div class="zap-m"><span>Oferta aberta</span><b>[Nome do fundo]</b><p>Para [público da oferta]. Reservas até [data].</p><p>Material aprovado no link.</p><em>[link rastreado]</em></div><p class="zap-p">Exemplo de formato, sem oferta real</p></div>'
    + '<div class="analise canal-d"><div class="vidro"><h3>Por que funciona</h3><ul><li>O aviso chega onde o assessor já está</li><li>Mensagem curta, com prazo e uma ação só</li><li>Só entra quando existe oferta, então não vira ruído</li></ul></div><div class="vidro"><h3>Como medir</h3><ul><li>Assessores no canal</li><li>Cliques por oferta</li><li>Pedidos de material e de conversa</li><li>Reservas originadas, quando houver dado</li></ul></div></div></div>'
    + '<h2>Como <strong>anda</strong></h2><ol class="roteiro r5 canal-p">' + _passos + '</ol>'
    + '<h2>Canal ou <strong>comunidade</strong></h2><div class="tab"><table><tr><th></th><th>Canal do WhatsApp</th><th>Comunidade com grupo de avisos</th></tr>'
    + '<tr><td>Quem entra</td><td>Qualquer pessoa com acesso ao canal</td><td>Só com convite</td></tr><tr><td>Quem fala</td><td>Só a Tivio; seguidores leem e reagem</td><td>Só a Tivio no grupo de avisos</td></tr><tr><td>Tamanho</td><td>Sem limite de seguidores</td><td>Limite por comunidade, a confirmar no WhatsApp</td></tr><tr><td>Serve para</td><td>Aviso geral, sem detalhe de oferta</td><td>Assessores credenciados</td></tr></table></div>'
    + '<p class="nota"><b>Recomendação:</b> comunidade fechada, com grupo de avisos, porque controla quem recebe. Tem a mesma cara de canal de desconto, e o canal aberto pode ficar para conteúdo geral.</p>'
    + '<h2>Regras antes de <strong>ligar</strong></h2><div class="analise"><div class="vidro"><ul><li>Publicar só material aprovado por Compliance</li><li>Respeitar o período de silêncio de cada oferta</li><li>Manter o texto coerente com os documentos da oferta</li></ul></div><div class="vidro"><ul><li>Linguagem serena, sem promessa de retorno</li><li>Definir se assessor pode repassar a mensagem ao cliente</li><li>Confirmar com o Jurídico a regra para cada tipo de oferta</li></ul></div></div>'
    + '<p class="meta-txt">Proposta para validar com Riscos, Compliance e Jurídico. A pesquisa não encontrou regra específica para WhatsApp; a análise precisa partir do texto da Resolução CVM 160.</p>'
    + '<p class="fontes-peer"><b>Fontes</b>' + "".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in _fontes_c) + '</p>'
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "canal-ofertas.html").write_text(pagina("Canal de ofertas", corpo_canal, CSS_P), encoding="utf-8")

# O conteúdo do Orçamento entra só cifrado, a partir de orc_frag.html, fora do Git.
(EXTRA / "orcamento.html").write_text(pagina("Orçamento", cabecalho("Orçamento", []) + '<div class="wrap"><p class="rodape">Tivio Capital</p></div>', CSS_P), encoding="utf-8")

_rows = lambda L: "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in L)
_vis = [("Primeira dobra no celular", "Faixa do WhatsApp, aviso de cookies e aba da newsletter cobrem a abertura", "Reduzir os avisos e soltar a primeira dobra"),
        ("Rolagem lateral no celular", "A home passa da largura da tela", "Corrigir o elemento que estoura"),
        ("Abertura", "Carrossel troca de assunto e arte a cada peça, sem uma mensagem fixa", "Abertura fixa com a ideia da casa e peças em segundo plano"),
        ("Cartões de fundos", "Alturas e textos desiguais; títulos longos quebram de formas diferentes", "Mesmo tamanho, texto curto e dados no mesmo lugar"),
        ("Repetição de botão", "Conhecer Fundo repetido em todos os cartões", "Botão secundário e uma ação principal por seção"),
        ("Linguagem visual", "Cada peça do carrossel e das notícias segue uma direção de arte", "Molde de capa com a mesma família visual")]
_est = [("Posicionamento", "Título e descrição falam de crédito, imobiliário e alternativos; estruturados não aparece como tema da casa", "Levar casa de estruturados ao título, à abertura e ao menu"),
        ("Menu", "Crédito Estruturado fica dentro de Fundos", "Criar um hub próprio de estruturados"),
        ("Públicos", "A home fala com um visitante genérico", "Caminhos para assessor, institucional, originador e investidor"),
        ("Captação", "Newsletter pede perfil em uma lista longa", "Formulário curto e oferta clara por público"),
        ("Prova", "Patrimônio, anos, fundos e equipe aparecem bem", "Manter e somar dado próprio de estruturados"),
        ("Onde investir", "Bloco das plataformas é útil, mas fica no fim da página", "Subir o bloco e ligar cada fundo à plataforma")]
_pri = [("Agora", "Corrigir celular e avisos da primeira dobra"), ("Em seguida", "Abertura fixa e revisão dos textos institucionais"), ("Depois", "Hub de estruturados e caminhos por público"), ("Por fim", "Moldes de capa e cartões padronizados")]
corpo_as = (cabecalho("Análise do site", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Análise do site"))
    + '<section class="topo-peer"><div><h1>Análise do site</h1><p class="lead">O que melhorar no visual e na estratégia.</p></div></section>'
    + '<div class="as-prints"><figure><img src="site-tivio/desktop.webp" alt="Abertura da home da Tivio Capital no desktop" loading="lazy"><figcaption>Desktop, 1440px</figcaption></figure><figure><img src="site-tivio/celular.webp" alt="Abertura da home da Tivio Capital no celular com avisos sobre a tela" loading="lazy"><figcaption>Celular, 375px</figcaption></figure></div>'
    + '<h2 id="visual">Melhorias <strong>visuais</strong></h2><div class="tab"><table><tr><th>Ponto</th><th>O que vimos</th><th>O que fazer</th></tr>' + _rows(_vis) + '</table></div>'
    + '<h2 id="estrategia">Melhorias de <strong>estratégia</strong></h2><div class="tab"><table><tr><th>Ponto</th><th>O que vimos</th><th>O que fazer</th></tr>' + _rows(_est) + '</table></div>'
    + '<h2 id="ordem">Por onde <strong>começar</strong></h2><ol class="roteiro r6 as-o">' + "".join(f'<li class="vidro"><b>{a}</b><span>{b}</span></li>' for a, b in _pri) + '</ol>'
    + '<p class="meta-txt">Leitura da home em telas de 1440px e 375px. A home carregou cerca de 500 KB e 277 imagens; desempenho e conversão precisam de dados do Analytics e do Search Console.</p>'
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "analise-site.html").write_text(pagina("Análise do site", corpo_as, CSS_P), encoding="utf-8")

import markdown as _md
_txt = (pathlib.Path(__file__).parent / "metodos_ia.md").read_text(encoding="utf-8")
_h = _md.markdown(_txt, extensions=["tables", "fenced_code"])
_h = _h.replace("<table>", '<div class="tab"><table>').replace("</table>", "</table></div>").replace(' align="left"', "")
_mi = re.sub(r"<h2>(.*?)</h2>", lambda m: "<h2>" + re.sub(r"^(Módulo \\d\\.) (.*)$", r"\\1 <strong>\\2</strong>", m.group(1)) + "</h2>", _h)
corpo_mi = (cabecalho("Como usar IA", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Como usar IA"))
    + '<section class="topo-peer"><div><h1>Como usar IA</h1><p class="lead">Os melhores métodos para pedir, dar contexto, escrever a spec e conferir o resultado, com o case da Caqui Invest, empresa fictícia com dados sintéticos.</p></div></section>'
    + '<div class="mi">' + _mi + '</div><p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "metodos-ia.html").write_text(pagina("Como usar IA", corpo_mi, CSS_P), encoding="utf-8")

_ser = [("Tivio Visita", "Irregular: 5 episódios em 2026", "49 e 4 comentários", "Melhor resultado do mês"),
        ("Carta do Gestor", "Todo mês: 10 edições em 10 meses de 2026", "13 e 23", "A série mais confiável"),
        ("Dividendos de FIIs", "Mensal, no fim do mês", "16", "Serviço para quem já é cotista"),
        ("Resumo mensal em Reels", "Mensal, um de crédito e um de imobiliário", "13 e 17", "Saem por volta do dia 15"),
        ("Desempenho em card", "Mensal, nos primeiros dias", "5 e 10", "O pior resultado do feed"),
        ("Deep Dive", "Irregular: nov/2025 e depois out/2026", "15", "Bom, mas 11 meses de intervalo"),
        ("Tivio ao Quadrado", "Parada: só a 1ª edição, em mar/2026, e 4 cortes", "Sem post no período", "Manter e retomar"),
        ("Cortes da Carta", "Pararam em mar/2026", "Sem post no período", "Série abandonada"),
        ("Tivio Think", "Uma edição, em jun/2025", "Sem post no período", "Série abandonada")]
_atn = [("Foco", "3 dos 14 posts de outubro falam de crédito estruturado, e 1 das 10 Cartas de 2026 tem esse tema central, pelos títulos e resumos", "Uma edição de crédito estruturado por trimestre na Carta ou no Deep Dive"),
        ("Bio do Instagram", "Ainda diz gestora de recursos independente; o site já mostra uma empresa Bradesco", "Corrigir primeiro"),
        ("LinkedIn", "27.288 seguidores contra 3.432 no Instagram, com reações quase iguais: mediana de 12,5 contra 14 curtidas", "Levar o texto pronto dos gestores para o LinkedIn pessoal"),
        ("Calendário", "3 posts em 30/10, depois de nenhum entre 23 e 29/10", "Distribuir as publicações no mês"),
        ("Página de vídeos", "A lista do site para em 17/08/2026, embora os resumos de setembro estejam no Instagram", "Atualizar a página"),
        ("Formato", "Tivio Visita rendeu de 2 a 10 vezes mais que os cards de tabela e de produto", "Dar calendário fixo ao Tivio Visita, mensal ou bimestral")]
_fora = [("Encerramento da oferta do Tivio Malls", "22"), ("Evento The New Agro", "15"), ("Produto: Global Rates", "12"), ("Na Mídia: Eco Invest", "12"), ("Produto: Alpha DI", "10")]
_ord = [("Agora", "Corrigir a bio do Instagram"), ("Em seguida", "Juntar os cards de desempenho em um só, ou deixá-los apenas no site"), ("Depois", "Dar calendário fixo ao Tivio Visita e firmar a casa de estruturados na Carta e no Deep Dive"), ("Por fim", "Retomar o Tivio ao Quadrado; encerrar ou retomar de vez os cortes e o Tivio Think")]
corpo_ap = (cabecalho("Análise das postagens", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("marketing.html", "Central de Marketing"), ("", "Análise das postagens"))
    + '<section class="topo-peer"><div><h1>Análise das postagens</h1><p class="lead">O que a Tivio publica com frequência e o que funciona. A constância é boa, mas o foco em estruturados aparece pouco.</p></div></section>'
    + '<h2 id="series">Séries <strong>recorrentes</strong></h2><div class="tab tab-pilha"><table><tr><th>Série</th><th>Frequência real</th><th>Curtidas em outubro</th><th>Leitura</th></tr>'
    + "".join(f'<tr><td>{a}</td><td data-r="Frequência real">{b}</td><td data-r="Curtidas em outubro">{c}</td><td data-r="Leitura">{d}</td></tr>' for a, b, c, d in _ser) + '</table></div>'
    + '<h2 id="grafico">Curtidas por <strong>tipo de post</strong></h2><p class="secao-sub">Média em outubro de 2026, no Instagram.</p>' + _bh(_curt)
    + '<h2 id="avulsos">Fora das <strong>séries</strong></h2><div class="tab"><table><tr><th>Post</th><th>Curtidas em outubro</th></tr>'
    + "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in _fora) + '</table></div>'
    + '<h2 id="pontos">O que <strong>chama atenção</strong></h2><div class="tab tab-pilha"><table><tr><th>Ponto</th><th>O que vimos</th><th>O que fazer</th></tr>' + "".join(f'<tr><td>{a}</td><td data-r="O que vimos">{b}</td><td data-r="O que fazer">{c}</td></tr>' for a, b, c in _atn) + '</table></div>'
    + '<h2 id="ordem">Por onde <strong>começar</strong></h2><ol class="roteiro r6 as-o">' + "".join(f'<li class="vidro"><b>{a}</b><span>{b}</span></li>' for a, b in _ord) + '</ol>'
    + '<p class="meta-txt">Leitura de 01/11/2026. No Instagram, sem login, entram só os 15 posts mais recentes dos 456: outubro e o fixado. Alcance, salvamentos e compartilhamentos não são públicos, e não dá para saber se algum post foi impulsionado. Os posts de 30/10 tinham 2 dias e ainda podem crescer. No LinkedIn, as reações são das 10 últimas publicações. Os vídeos vêm da página do site, porque o canal do YouTube não pôde ser lido.</p>'
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "analise-postagens.html").write_text(pagina("Análise das postagens", corpo_ap, CSS_P), encoding="utf-8")

_fr27 = [("Automação", "frente-automacao.html", "Facilitar o operacional para o time gastar tempo no que muda resultado.",
          ["Crédito e Investment Solutions já totalmente automatizados", "Imobiliário: começa em janeiro, com meta de concluir até abril pela complexidade", "Portal com os dados de fechamento de todas as áreas até o meio do ano", "Janelas específicas de crédito geradas no portal", "IA no dia a dia do time, com trilha de aprendizado e Claude Max"]),
         ("Eventos", "frente-eventos.html", "Transformar presença em contato e reunião.",
          ["16 encontros com o Itaú no ano", "Summit BTG, Conexão Bradesco e Expert XP", "Abrapp, Previpar, APEP e ASCPrev", "Convites a partir dos alocadores mapeados pela fnmk", "Contato quente para o comercial em até 2 dias"]),
         ("Conteúdo", "frente-conteudo.html", "Ser mais engajado nos posts: menos, com mais qualidade, para um nicho.",
          ["Eventos da Carta do Gestor sobre assuntos específicos", "Eventos internos com especialista e com convidados", "Casa de estruturados em toda série", "Executivos postando e compartilhando no LinkedIn", "Colaboradores, Teams e WhatsApp", "Newsletter como base própria", "Raio X do Mercado e Tivio ao Quadrado", "Imprensa com pauta por trimestre", "Kit do assessor"]),
         ("Digital com estratégia", "frente-digital.html", "Otimizar o site, ranquear no Google e aparecer nas IAs.",
          ["Landing pages por demanda específica, com tráfego pago", "Tráfego para atrair gente aos eventos", "Fundos da Tivio espalhados no mercado, para varejo e assessores", "GEO e SEO: a Tivio nas IAs e nas buscas do Google", "Plano de otimizar o site, com subida e atualização de arquivos automatizada", "Gráfico interativo de rentabilidade e perguntas em acordeão nos artigos", "Metas das redes"])]
_FX27 = {"Automação": "Até o fim do ano, tudo automatizado em código. No começo de 2027, isso vira um portal: até o meio do ano, os dados de fechamento de todas as áreas, e, quem sabe, janelas específicas de crédito. O imobiliário começa em janeiro, com meta de concluir até abril.",
         "Eventos": "16 encontros com o Itaú no ano, um tema de estruturados por vez, e os grandes eventos de plataforma e previdência. Todo evento segue o mesmo roteiro: convite 3 semanas antes, post do executivo, cobertura no dia, resumo em até 2 dias, artigo e cortes em até 2 semanas e balanço no fim do mês.",
         "Conteúdo": "A visão para 2027 é ser mais engajado nos posts. A Carta do Gestor vira também evento, um assunto específico por vez, além de eventos internos com especialista e até com convidados. Todo mês, Carta e newsletter; todo trimestre, Raio X do Mercado, filmagem e pauta de imprensa.",
         "Digital com estratégia": "Trazer demandas específicas: landing pages direcionadas, com tráfego pago, para levar gente aos eventos e espalhar os fundos da Tivio no mercado, possivelmente para varejo e assessores. E estar em todas as IAs, com GEO, e nas buscas, com SEO. Temos também o plano de otimizar o site e automatizar a subida e a atualização dos arquivos."}
_EX27 = {"Landing pages por demanda específica, com tráfego pago": "Página só de FIDC para assessores, com anúncio no LinkedIn para quem trabalha com renda fixa",
         "Tráfego para atrair gente aos eventos": "Anúncio do encontro com o Itaú para assessores da região, levando para a inscrição",
         "Fundos da Tivio espalhados no mercado, para varejo e assessores": "Página do HGD30 e do HYD60 com material pronto para o assessor mandar ao cliente",
         "GEO e SEO: a Tivio nas IAs e nas buscas do Google": "O ChatGPT citar a Tivio sobre crédito estruturado e a Tivio no topo do Google para o que é FIDC",
         "Plano de otimizar o site, com subida e atualização de arquivos automatizada": "Relatórios, lâminas e materiais do mês sobem para o site direto do AutomaTivio, sem envio manual"}
_num27 = [("Automação", "Horas do time por edição", "A medir"), ("Automação", "Materiais gerados por rodada", "81, em set/2026"), ("Automação", "Correções depois de publicar", "A medir"),
          ("Eventos", "Eventos realizados", "23 no orçamento de 2027"), ("Eventos", "Inscritos, presentes e pedidos de contato", "A medir"), ("Eventos", "Captação de presentes em até 90 dias", "A medir"),
          ("Conteúdo", "Posts sobre estruturados", "3 de 14, em out/2026"), ("Conteúdo", "Contatos vindos de cada série", "A medir"), ("Conteúdo", "Executivos ativos no LinkedIn", "A medir"), ("Conteúdo", "Colaboradores que engajam nos posts", "A medir"), ("Conteúdo", "Cliques do WhatsApp até um contato", "A medir"), ("Conteúdo", "Inscritos, abertura e cliques da newsletter", "A medir"), ("Conteúdo", "Menções na imprensa com porta-voz da Tivio", "A medir"),
          ("Digital com estratégia", "Contatos por landing e por origem", "A medir"), ("Digital com estratégia", "Custo por contato", "A medir"), ("Digital com estratégia", "Reuniões qualificadas", "A medir"), ("Digital com estratégia", "Posição no Google nos termos de estruturados", "A medir"), ("Digital com estratégia", "Visitas orgânicas ao site", "A medir"), ("Digital com estratégia", "Citações da Tivio nas respostas de IAs sobre estruturados", "A medir")]
_ano27 = [("Nov e dez/26", "Medir horas por edição; corrigir as falhas dos decks", "", "Regra de aprovação com Riscos; kit do assessor piloto; planejamento de conteúdo de 2027, olhando cada frente do comercial e do institucional", "Melhorias de SEO e GEO no site, já iniciadas; plano de otimização do site; formulário curto da newsletter"),
          ("Janeiro", "Começar a automatizar o imobiliário; crédito e Investment Solutions já automatizados", "1 evento: panorama de estruturados", "1º Raio X do Mercado, quadro fixo de vídeo; newsletter no novo formato", "3 templates indexáveis; landing do evento"),
          ("Fevereiro", "Decks sem ajuste manual", "1 evento: como ler um FIDC; Summit BTG", "Executivos no LinkedIn; colaboradores e canal do Teams", "Otimização do site; subida de arquivos automatizada"),
          ("Março", "Imobiliário: primeiros materiais automatizados; balanço de horas e erros", "2 eventos: estruturados e FIDC", "Rotina semanal no WhatsApp", "Primeiros artigos: FIDC e crédito estruturado; SEO dos termos de estruturados"),
          ("Abril", "Imobiliário automatizado por completo; relatórios e destaques do mês; convite e balanço de evento em modelo", "1 evento: Família ALT", "2º Raio X do Mercado; Gráfico da Semana", "Site otimizado no ar, com gráfico interativo de rentabilidade"),
          ("Maio", "Imobiliário na edição mensal em um comando", "1 evento: crédito privado e juros", "Tivio ao Quadrado", "Hub de estruturados; GEO: perguntas e respostas para as IAs citarem"),
          ("Junho", "Portal com os dados de fechamento de todas as áreas", "2 eventos: Família ALT e juros", "Balanço das séries no semestre", "Artigos de crédito privado e previdência"),
          ("Julho", "Números do mês nas páginas de fundo", "1 evento: previdência; Expert XP", "3º Raio X do Mercado", "Panorama de Estruturados, em troca do contato"),
          ("Agosto", "", "1 evento: curadoria de gestores", "Carta do Gestor em PDF e áudio", "Novos artigos por termo"),
          ("Setembro", "Rever horas e erros do ano", "2 eventos: previdência e curadoria", "", "Rever posições no Google e citações nas IAs"),
          ("Outubro", "", "2 eventos: balanço de estruturados; Congresso Abrapp", "4º Raio X do Mercado", "Novos artigos por termo"),
          ("Novembro", "", "2 eventos: perspectivas para 2028", "", "Simulador de cascata com carteira fictícia"),
          ("Dezembro", "Fechar o painel de números do ano", "Balanço dos eventos do ano", "Balanço das séries: manter, ajustar ou parar", "Balanço de site, artigos, SEO e GEO")]
_ano27 = [(r[0], r[1], r[2], r[3] if "Carta do Gestor" in r[3] else "Carta do Gestor" + (f"; {r[3]}" if r[3] else ""), r[4]) for r in _ano27]
_imp_mes = {"Nov e dez/26": "plano de imprensa", "Janeiro": "pauta de imprensa do 1º tri", "Abril": "pauta de imprensa do 2º tri", "Julho": "Panorama de Estruturados na imprensa", "Outubro": "pauta de imprensa do 4º tri"}
_ano27 = [(r[0], r[1], r[2], r[3] + (f"; {_imp_mes[r[0]]}" if r[0] in _imp_mes else ""), r[4]) for r in _ano27]
_ano27 = [(r[0], r[1], r[2], r[3] + ("; <!--FILM-->" if r[0] in ("Janeiro", "Abril", "Julho", "Outubro") else ""), r[4]) for r in _ano27]
_bm = [("Automação", "Constância vale mais que audiência", "Kinea e Apollo", "Carta do Gestor todo mês; 81 materiais por rodada no AutomaTivio", "Edição mensal em dia, sem esforço manual"),
       ("Eventos", "O gargalo é quem indica", "PIMCO e Ares", "16 eventos Itaú no orçamento de 2027; o site ainda fala com um visitante genérico", "Trilha para assessores e gerentes"),
       ("Conteúdo", "Gente pesa mais que marca", "Solis e Ares", "Tivio Visita teve o melhor resultado de outubro, com 49 curtidas; executivos ativos no LinkedIn ainda a medir", "Gestores no LinkedIn pessoal"),
       ("Conteúdo", "Quem explica o risco ganha", "Oaktree e Janus Henderson", "Deep Dive com 15 curtidas, mas 11 meses de intervalo; 1 das 10 Cartas de 2026 tem crédito estruturado como tema central", "Séries que mostram a estrutura e o que pode dar errado"),
       ("Digital com estratégia", "Estruturados ainda não tem dona", "Solis, só em FIDC", "3 de 14 posts sobre estruturados em out/26; no site, Crédito Estruturado fica dentro de Fundos", "Site, hub e artigos para disputar o termo"),
       ("Digital com estratégia", "Dado próprio cria autoridade", "Valora e Golub", "O site prova patrimônio, anos, fundos e equipe; ainda sem dado próprio de estruturados", "Panorama de Estruturados para imprensa e IAs citarem")]
_bm_vis = '<div class="bm">' + "".join(f'<section class="bm-i vidro"><p class="bm-f">{ICO27[a]}{a.replace(" com estratégia", "")}</p><h3>{b}</h3><dl><dt>Quem faz bem</dt><dd>{q}</dd><dt class="bm-t">O que fazemos hoje</dt><dd class="bm-t">{h}</dd><dt>Como entra no plano</dt><dd>{d}</dd></dl></section>' for a, b, q, h, d in _bm) + '</div>'
_lig = [("Automação + Conteúdo", {"Automação", "Conteúdo"}, "Já hoje", "A rodada do mês entrega posts e destaques prontos"),
        ("Evento + Digital", {"Eventos", "Digital com estratégia"}, "1º tri", "Landing de inscrição, replay em artigo e remarketing de quem veio"),
        ("Evento + Conteúdo", {"Eventos", "Conteúdo"}, "1º tri", "Executivo anuncia no LinkedIn, e os cortes viram posts e WhatsApp"),
        ("Conteúdo + Digital", {"Conteúdo", "Digital com estratégia"}, "2º tri", "Artigo ranqueia no Google, e LinkedIn e WhatsApp levam tráfego"),
        ("Automação + Eventos", {"Automação", "Eventos"}, "2º tri", "Convite, lembrete e balanço do evento em modelo pronto"),
        ("Automação + Digital", {"Automação", "Digital com estratégia"}, "3º tri", "Números do mês atualizam as páginas de fundo")]
def _lig_tab(n=None):
    return '<div class="tab tab-pilha"><table><tr><th>Estratégia</th><th>Quando</th><th>Como funciona</th></tr>' + "".join(f'<tr><td>{a}</td><td data-r="Quando">{q}</td><td data-r="Como funciona">{d}</td></tr>' for a, s, q, d in _lig if n is None or n in s) + '</table></div>'
_G_M = ["N/D", "J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
def _gantt(so=None):
    nomes = [(1, "Automação"), (2, "Eventos"), (3, "Conteúdo"), (4, "Digital com estratégia")]
    h = '<div class="gt-r gt-h"><span></span>' + "".join((f'<span><a href="#m{i}">{x}</a></span>' if not so else f"<span>{x}</span>") for i, x in enumerate(_G_M)) + '</div>'
    for i, n in nomes:
        if so and n != so:
            continue
        cel = ""
        for r in _ano27:
            t = r[i]
            q = re.match(r"(\d+) eventos?:", t) if i == 2 else None
            cel += f'<span class="gt-c{" on" if t else ""}" title="{r[0]}: {t}">{q.group(1) if q else ""}</span>'
        h += f'<div class="gt-r"><b>{ICO27[n]}{n.replace(" com estratégia", "")}</b>{cel}</div>'
    return f'<div class="gt vidro" role="img" aria-label="Calendário de implementações por frente">{h}</div>'
def _tl(col):
    nomes = {1: "Automação", 2: "Eventos", 3: "Conteúdo", 4: "Digital com estratégia"}
    h = ""
    for m, r in enumerate(_ano27):
        itens = [i for i in nomes if r[i] and (col is None or i == col)]
        if not itens:
            continue
        h += f'<section class="tl-m" id="m{m}"><h3>{r[0]}</h3><div class="tl-c{" um" if col else ""}">' + "".join(f'<div class="tl-i vidro" data-c="{i}">{ICO27[nomes[i]]}<div><b>{nomes[i].replace(" com estratégia", "")}</b><span>{r[i]}</span></div></div>' for i in itens) + '</div></section>'
    return f'<div class="tl" id="{"meses" if col is None else "linha"}">{h}</div>'
def _lig_vis():
    def ic(t):
        return ICO27["Eventos" if t == "Evento" else "Digital com estratégia" if t == "Digital" else t]
    return '<div class="lig">' + "".join(f'<div class="lig-i vidro"><div class="lig-t">{ic(a.split(" + ")[0])}<i>+</i>{ic(a.split(" + ")[1])}<em>{q}</em></div><b>{a}</b><span>{d}</span></div>' for a, s, q, d in _lig) + '</div>'
_IMG27 = {"Automação": ("pecas/ce1.webp", "Destaque de Crédito Estruturado gerado pelo AutomaTivio"), "Eventos": ("feed/evento.webp", "Plateia assistindo a uma palestra"),
          "Conteúdo": ("feed/02.webp", "Capa da Carta do Gestor O Cálculo de Tolstói"), "Digital com estratégia": ("site-tivio/desktop.webp", "Site da Tivio Capital no desktop")}
_DONO27 = {"Automação": "Renan Chaves", "Eventos": "Fernanda Acquati", "Conteúdo": "Fernanda Acquati e Gabriel Fiorilli", "Digital com estratégia": "Renan Chaves"}
_RITMO = [("Todo mês", "Ritmo mensal", ["Carta do Gestor", "Newsletter", "Edição mensal em um comando", "Pauta do mês com a assessoria"]),
          ("Todo trimestre", "Ritmo trimestral", ["Raio X do Mercado", "<!--FILMC-->", "Pauta de imprensa do trimestre", "4 eventos Itaú no escritório"]),
          ("No ano", "Marcos fixos", ["Summit BTG, Conexão Bradesco e Expert XP", "Congresso Abrapp", "Balanço: manter, ajustar ou parar"])]
_TRI = [("1º trimestre", "Janeiro a março", ["4 eventos Itaú e Summit BTG", "1º Raio X do Mercado", "Executivos no LinkedIn", "Otimização do site e primeiros artigos", "Automação do imobiliário a partir de janeiro"]),
        ("2º trimestre", "Abril a junho", ["4 eventos Itaú, com a Família ALT", "2º Raio X, Gráfico da Semana e Tivio ao Quadrado", "Site otimizado no ar", "Hub de estruturados e GEO", "Imobiliário na edição mensal"]),
        ("3º trimestre", "Julho a setembro", ["4 eventos Itaú e Expert XP", "3º Raio X do Mercado", "Carta do Gestor em PDF e áudio", "Panorama de Estruturados", "Números do mês nas páginas de fundo"]),
        ("4º trimestre", "Outubro a dezembro", ["4 eventos Itaú e Congresso Abrapp", "4º Raio X do Mercado", "Simulador de cascata", "Balanço do ano: manter, ajustar ou parar"])]
_SEG = [("Crédito Estruturado", "credito-estruturado", "Mostrar como a casa estrutura, não só quanto rendeu", "Foco do ano · 8 posts por mês"),
        ("Crédito Privado", "credito-privado", "Leitura de mercado com cara de gente", "5 posts por mês"),
        ("Imobiliário", "imobiliario", "Automatizar a partir de janeiro, com o carrossel dos FIIs", "A partir de janeiro"),
        ("Investment Solutions", "investment-solutions", "Curadoria de gestores explicada", "4 posts por mês"),
        ("Previdência", "previdencia", "HGD30 e HYD60 para quem planeja o longo prazo", "3 posts por mês"),
        ("Marca e eventos", "marca-e-eventos", "A Tivio como lugar de encontro do mercado de estruturados", "4 posts por mês")]
_TESES = [("O espaço existe", "Ninguém é dono do tema crédito estruturado na cabeça do assessor e do investidor. Quem ocupar primeiro vira a referência.",
           "Só 3 de 14 posts de outubro falaram de estruturados; no nosso site o tema fica escondido dentro de Fundos", ["Estruturados como foco do ano", "Hub de estruturados no site", "SEO e GEO para disputar o termo"]),
          ("Quem explica o risco ganha", "Estruturado assusta porque parece complexo. Quem explica o risco com clareza ganha a confiança antes de falar de retorno.",
           "Oaktree e Janus Henderson abrem pelo risco; o nosso Deep Dive foi bem, com 15 curtidas, mas ficou 11 meses sem nova edição; só 1 das 10 Cartas de 2026 falou de estruturados", ["Raio X do Mercado a cada trimestre", "Deep Dive e Tivio Explica em calendário", "Simulador de cascata com carteira fictícia"]),
          ("O gargalo é quem indica", "O investidor chega pelo assessor e pelo gerente. Se eles não entendem o fundo, não indicam.",
           "PIMCO e Ares educam primeiro quem distribui; o Not Listed mapeou 1.202 casas de wealth; o nosso site fala com um visitante genérico", ["16 encontros com o Itaú no ano", "Convites a partir dos alocadores da fnmk", "Kit do assessor e canal de ofertas no WhatsApp"]),
          ("Gente pesa mais que marca", "As pessoas confiam em pessoas. Post com rosto da casa rende mais do que card de produto.",
           "O Tivio Visita, com gente da Tivio, foi o melhor post de outubro, com 49 curtidas e de 2 a 10 vezes mais que os cards; Solis e Ares põem o gestor na frente", ["Executivos postando e compartilhando no LinkedIn", "Porta-vozes com pauta por trimestre", "Gestor no vídeo do Raio X do Mercado"]),
          ("Dado próprio cria autoridade", "Quem publica o número vira a fonte que a imprensa, o assessor e as IAs citam.",
           "Valora e Golub viraram referência com números próprios; o Not Listed ganhou espaço só organizando dado público da CVM e da ANBIMA", ["Panorama de Estruturados em troca do contato", "Raio X como número recorrente", "Pauta de imprensa com dado"]),
          ("Constância vale mais que audiência", "Aparecer sempre, no mesmo ritmo, constrói lembrança. Pico de audiência passa.",
           "Kinea e Apollo publicam sempre no mesmo ritmo; a nossa Carta do Gestor saiu em 10 dos 10 meses de 2026; o AutomaTivio já gera 81 materiais por rodada", ["Edição mensal em um comando", "Ritmo fixo: Carta todo mês, Raio X e eventos todo trimestre", "Imobiliário automatizado a partir de janeiro"])]
_AP_BTN = '<button type="button" id="ap-abrir" class="ap-b"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M12 16v4M8 20h8"/></svg>Modo apresentação</button>'
_AP_JS = """<script>(function(){var a=document.getElementById('apres');if(!a)return;var l=[].slice.call(a.querySelectorAll('.sl')),i=0,n=document.getElementById('ap-n');a.querySelector('.ap-logo').innerHTML=document.querySelector('.marca').innerHTML;
function v(k){i=Math.max(0,Math.min(l.length-1,k));l.forEach(function(s,j){s.classList.toggle('ativa',j===i)});n.textContent=(i+1)+' / '+l.length}
function abrir(){a.hidden=false;document.body.style.overflow='hidden';v(0);if(a.requestFullscreen)a.requestFullscreen().catch(function(){})}
function sair(){a.hidden=true;document.body.style.overflow='';if(document.fullscreenElement)document.exitFullscreen()}
document.getElementById('ap-abrir').onclick=abrir;document.getElementById('ap-sair').onclick=sair;document.getElementById('ap-ant').onclick=function(){v(i-1)};document.getElementById('ap-prox').onclick=function(){v(i+1)};
document.addEventListener('keydown',function(e){if(a.hidden)return;if(e.key==='ArrowRight'||e.key===' '||e.key==='PageDown'){e.preventDefault();v(i+1)}if(e.key==='ArrowLeft'||e.key==='PageUp')v(i-1);if(e.key==='Escape')sair()});
document.addEventListener('fullscreenchange',function(){if(!document.fullscreenElement&&!a.hidden&&a.dataset.fs)sair();a.dataset.fs=document.fullscreenElement?'1':''})})();</script>"""
_ABAS_JS = """<script>(function(){var B=[].slice.call(document.querySelectorAll('.abas-pl button'));function sel(id){B.forEach(function(x){x.setAttribute('aria-selected',x.dataset.aba===id)});[].forEach.call(document.querySelectorAll('.painel-pl'),function(p){p.hidden=p.id!==id})}
B.forEach(function(b){b.addEventListener('click',function(){sel(b.dataset.aba);history.replaceState(null,'','#'+b.dataset.aba)})});sel(location.hash==='#ano-2027'?'ano-2027':'fim-do-ano')})();</script>"""
corpo_p27 = (cabecalho("Plano", []) + '<div class="wrap">'
    + trilha(("index.html", "Início"), ("", "Plano"))
    + '<section class="topo-peer"><div><h1>Plano</h1><p class="lead">O que fechar até o fim do ano e o que fazer em 2027 para ser a casa de estruturados.</p></div></section>'
    + _AP_BTN + '<div class="abas abas-pl" role="tablist"><button type="button" role="tab" data-aba="fim-do-ano" aria-selected="true">Até o fim do ano</button><button type="button" role="tab" data-aba="ano-2027" aria-selected="false">2027</button></div>'
    + '<section class="painel-pl" id="fim-do-ano"><h2 id="estrutura-fim">Estrutura até o fim <strong>do ano</strong></h2>' + _org + '<!--FIMANO-->' + '<h2 id="frentes-fim">O que já começa <strong>nas frentes</strong></h2><div class="frentes linhas fr-nd">' + "".join(f'<section class="frente vidro"><h3>{n}</h3><p class="dono">Novembro e dezembro</p><ul>' + "".join(f"<li>{x[:1].upper() + x[1:]}</li>" for x in _ano27[0][k].split("; ") if x) + "</ul></section>" for k, n in ((1, "Automação"), (2, "Eventos"), (3, "Conteúdo"), (4, "Digital")) if _ano27[0][k]) + '</div></section><section class="painel-pl" id="ano-2027" hidden>'
    + '<h2 id="estrutura">Estrutura em <strong>2027</strong></h2><!--ORG27-->' + '<a class="tp tp-b" href="estrutura.html">' + ICO27["Estrutura"] + 'Ver a estrutura completa</a>' + '<!--CUSTO27-->'
    + '<h2 id="porque">Por que <strong>assim</strong></h2><p class="secao-sub">Cada tese, a evidência que temos e o que o plano faz com ela.</p><div class="frentes linhas teses">'
    + "".join(f'<section class="frente vidro"><h3>{a}</h3><p class="tes-q">{q}</p><p class="tes-r">O que vimos</p><p class="dono">{b}</p><p class="tes-r tes-f">Por isso puxamos</p><ul>' + "".join(f"<li>{x}</li>" for x in l) + "</ul></section>" for a, q, b, l in _TESES) + '</div>'
    + '<h2 id="frentes">O ano em <strong>quatro frentes</strong></h2><div class="frentes f4 fr-vis">'
    + "".join(f'<section class="frente vidro"><img class="fr-img" src="{_IMG27[n][0]}" alt="{_IMG27[n][1]}" loading="lazy">{ICO27[n]}<h3><a href="{h}">{n}</a></h3><p class="dono">{_DONO27[n]}</p><p class="fr-m">{d}</p><p class="fr-x">{_FX27[n]}</p><ul>' + "".join(f'<li>{x}' + (f'<em class="fr-ex">Ex.: {_EX27[x]}</em>' if x in _EX27 else "") + "</li>" for x in l) + "</ul></section>" for n, h, d, l in _fr27) + '</div>'
    + '<h2 id="segmentos">Cada segmento em <strong>uma linha</strong></h2><div class="subs seg6">' + "".join(f'<a class="sub vidro" href="segmento-{h}.html"><b>{n}</b><span>{d}</span><em>{q}</em></a>' for n, h, d, q in _SEG) + '</div>'
    + '<h2 id="ritmo">O que <strong>se repete</strong></h2><div class="frentes linhas">'
    + "".join(f'<section class="frente vidro"><h3>{a}</h3><p class="dono">{b}</p><ul>' + "".join(f"<li>{x}</li>" for x in l) + "</ul></section>" for a, b, l in _RITMO) + '</div>'
    + '<h2 id="trimestres">O ano por <strong>trimestre</strong></h2><div class="frentes linhas">'
    + "".join(f'<section class="frente vidro"><h3>{a}</h3><p class="dono">{b}</p><ul>' + "".join(f"<li>{x}</li>" for x in l) + "</ul></section>" for a, b, l in _TRI) + '</div>'
    + '<h2 id="juntas">Estratégias que se <strong>entrelaçam</strong></h2>' + _lig_vis()
    + '<h2 id="medir">Como vamos <strong>medir</strong></h2><div class="fu">'
    + "".join(f'<div class="fu-i vidro" style="width:{w}%"><b>{a}</b><span>{b}</span></div>' for w, a, b in [(100, "Alcance", "Quem viu a Tivio"), (88, "Contato", "Quem deixou nome e origem"), (76, "Reunião", "Quem pediu conversa qualificada"), (64, "Captação", "Quanto veio, em R$")]) + '</div>'
    + '<!--METAS--><div class="acc" id="numeros">'
    + "".join(f'<details><summary><b>{x[0]}</b><span>{sum(1 for n in _num27 if n[0] == x[0])} números</span></summary><div class="tab tab-pilha"><table><tr><th>Número</th><th>Hoje</th></tr>' + "".join(f'<tr><td>{b}</td><td data-r="Hoje">{d}</td></tr>' for a, b, d in _num27 if a == x[0]) + '</table></div></details>' for i, x in enumerate(_fr27)) + '</div>'
    + '<details class="det-ano" id="ano"><summary>Ver o ano <strong>mês a mês</strong></summary>' + _gantt() + '<div class="pil" id="pil" role="group" aria-label="Filtrar por frente">'
    + "".join(f'<button type="button" data-c="{i}" aria-pressed="{"true" if i == 0 else "false"}">{n}</button>' for i, n in enumerate(["Todas", "Automação", "Eventos", "Conteúdo", "Digital"]))
    + '</div>' + _tl(None) + """</details><script>(function(){var B=[].slice.call(document.querySelectorAll('#pil button')),T=document.getElementById('meses');
B.forEach(function(b){b.addEventListener('click',function(){var c=b.dataset.c;B.forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false')});
[].forEach.call(T.querySelectorAll('.tl-i'),function(e){e.hidden=c!=='0'&&e.dataset.c!==c});
[].forEach.call(T.querySelectorAll('.tl-m'),function(m){m.hidden=!m.querySelector('.tl-i:not([hidden])')})})})})();</script>"""
    + '<h2 id="bases">Onde o plano <strong>se apoia</strong></h2><div class="pl-base">' + cartoes([("frente-benchmark.html", "Benchmark", "O que vimos fora e o que fazemos."), ("analise-postagens.html", "Análise das postagens", "O que funciona hoje."), ("imprensa.html", "Imprensa", "Pauta, porta-vozes e filtro."), ("analise-site.html", "Análise do site", "O que melhorar."), ("orcamento.html", "Orçamento 2027", "Com o que contamos.")]) + '</div>'
    + '<p class="meta-txt">Proposta do time de Comunicação &amp; Marketing. As metas de negócio ficam para definir depois de medir a base, e a captação por origem depende de registrar a origem do contato até o comercial.</p></section>'
    + '<div id="apres" hidden role="dialog" aria-label="Modo apresentação"><div class="ap-logo"></div><div class="ap-sum" id="ap-sum" hidden></div><div class="ap-ctl"><button type="button" id="ap-menu" aria-label="Sumário" aria-expanded="false">Sumário</button><button type="button" id="ap-ant" aria-label="Anterior">‹</button><span id="ap-n"></span><button type="button" id="ap-prox" aria-label="Próximo">›</button><button type="button" id="ap-sair" aria-label="Sair">Sair</button></div></div>'
    + '<script>' + (pathlib.Path(__file__).parent / "apres_base.js").read_text(encoding="utf-8") + (pathlib.Path(__file__).parent / "apres_plano.js").read_text(encoding="utf-8") + '</script>' + _ABAS_JS
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "plano-2027.html").write_text(pagina("Plano", corpo_p27, CSS_P), encoding="utf-8")

_ver = {"Automação": [("automativio.html", "AutomaTivio", "A edição mensal em um comando."), ("automativio-marketing.html", "Times", "Dados, rodada, decks e publicação."), ("m-copilot.html", "Copilot", "Uso no dia a dia do time."), ("metodos-ia.html", "Como usar IA", "Métodos para pedir e conferir.")],
        "Eventos": [("m-eventos.html", "Eventos Itaú", "Roteiro e temas dos 16 eventos."), ("eventos-mercado.html", "Eventos do mercado", "Onde cada segmento se encontra."), ("calendario.html", "Calendário 2027", "Feriados, datas de dinheiro e ações.")],
        "Conteúdo": [("painel-mensal.html", "Painel mensal", "Instagram, LinkedIn, YouTube e e-mail, até 31/10/2026."), ("https://tiviocapital.docsend.com/view/jjy2v9nsd7qejnjm", "Painel no DocSend", "O arquivo para baixar e enviar."), ("m-posts.html", "Posts", "Plano por segmento."), ("analise-postagens.html", "Análise das postagens", "O que funciona hoje."), ("canal-ofertas.html", "Canal de ofertas", "WhatsApp para assessores."), ("marketing.html#segmentos", "Segmentos e públicos", "Para quem falamos.")],
        "Digital com estratégia": [("analise-site.html", "Site", "O que melhorar no visual e na estratégia."), ("m-captacao.html", "Captação", "Landing, orgânico, pago, SEO e GEO.")]}
_site = ('<h2 id="site">Site e <strong>artigos</strong></h2><div class="tab tab-pilha"><table><tr><th>Remodelar</th><th>O que muda</th></tr>'
    + "".join(f'<tr><td>{a}</td><td data-r="O que muda">{b}</td></tr>' for a, b in [("Abertura", "Casa de estruturados no título e no menu"), ("Hub", "Área própria de estruturados, fora de Fundos"), ("Fundos", "Uma página por fundo, com documentos em texto"), ("Google", "Liberar no robots.txt a pasta de lâminas e relatórios")])
    + '</table></div><!--METAS--><h2 id="artigos">Artigos para <strong>ranquear no Google</strong></h2><div class="tab tab-pilha"><table><tr><th>Termo</th><th>Artigo</th></tr>'
    + "".join(f'<tr><td>{a}</td><td data-r="Artigo">{b}</td></tr>' for a, b in [("FIDC", "O que é um FIDC"), ("Crédito estruturado", "Como funciona o crédito estruturado"), ("Fundo de crédito privado", "Como escolher um fundo de crédito privado"), ("Previdência crédito privado", "Previdência com crédito privado: como funciona")]) + '</table></div>')
_evt_l = [("Eventos Íon / Itaú", "Plataforma", "16 no ano, no escritório", "No orçamento"), ("Summit BTG", "Plataforma", "Fevereiro, na última edição", "No orçamento"), ("Conexão Bradesco", "Plataforma", "A confirmar", "No orçamento"), ("Expert XP", "Plataforma", "Julho, na última edição confirmada", "No orçamento, 5 ingressos"),
          ("Seminário Abrapp e Congresso", "Previdência", "Congresso em outubro, na última edição", "No orçamento, com 2 convites"), ("Previpar", "Previdência", "A confirmar", "No orçamento"), ("APEP", "Previdência", "A confirmar", "No orçamento"), ("ASCPrev", "Previdência", "A confirmar", "No orçamento"),
          ("WEW 2027", "Fora do orçamento", "A confirmar", "A aprovar"), ("Roadshow de oferta pública", "Fora do orçamento", "A confirmar", "A aprovar"), ("Roadshow em escritórios do Bradesco e plataformas", "Fora do orçamento", "A confirmar", "A aprovar"), ("FFA", "Fora do orçamento", "A confirmar", "A aprovar"), ("Eco Invest / Climate Week", "Fora do orçamento", "A confirmar", "A aprovar"), ("LAVCA", "Fora do orçamento", "A confirmar", "A aprovar"), ("GIIN Impact Forum", "Fora do orçamento", "A confirmar", "A aprovar")]
_edit = [("3 semanas antes", "Tema do encontro e convite com inscrição", "Landing, e-mail e WhatsApp", "Fernanda Acquati"), ("1 semana antes", "Post do executivo com a tese do evento", "LinkedIn pessoal", "Executivo, com texto de Fernanda Acquati"), ("1 semana antes", "Lembrete e post para colaboradores engajarem", "E-mail e canal do Teams", "Fernanda Acquati"),
         ("No dia", "Fotos, vídeo curto e entrevista rápida com o porta-voz", "Stories e LinkedIn", "Fernanda Acquati"), ("No dia", "Material do tema, com QR para assinar a newsletter", "Presencial", "Fernanda Acquati"), ("Até 2 dias", "Resumo com 3 aprendizados e o material", "E-mail, newsletter e post", "Fernanda Acquati"),
         ("Até 2 semanas", "Artigo a partir da palestra", "Site, para o Google", "Fernanda Acquati"), ("Até 2 semanas", "Cortes do evento", "Reels, LinkedIn e WhatsApp", "Fernanda Acquati"), ("No fim do mês", "Balanço: inscritos, presentes e pedidos de contato", "Plano 2027", "Fernanda Acquati")]
_ang = [("Eventos Itaú", "Assessores e investidores da base Itaú", "Trilha de estruturados, um tema por encontro"), ("Summit BTG, Conexão Bradesco e Expert XP", "Assessores e plataformas", "O que levar ao cliente e como explicar o risco"), ("Abrapp, Previpar, APEP e ASCPrev", "Fundos de pensão e regimes próprios", "Processo, governança e fundos já enquadrados")]
_evt = ('<h2 id="mix">Os 23 eventos <strong>por tipo</strong></h2>' + _st([("Itaú", 16), ("Previdência", 4), ("Plataformas", 3)])
    + '<h2 id="meses">Eventos Itaú <strong>por mês</strong></h2>' + _bc([(r[0][:3], int(re.match(r"(\d+) evento", r[2]).group(1)) if re.match(r"\d+ evento", r[2]) else 0) for r in _ano27[1:]])
    + '<h2 id="todos">Todos os eventos <strong>de 2027</strong></h2><div class="tab tab-pilha"><table><tr><th>Evento</th><th>Tipo</th><th>Quando</th><th>Situação</th></tr>'
    + "".join(f'<tr><td>{a}</td><td data-r="Tipo">{b}</td><td data-r="Quando">{d}</td><td data-r="Situação">{e}</td></tr>' for a, b, d, e in _evt_l) + '</table></div><p class="meta-txt">Datas de 2027 a confirmar com cada organizador. Para achar mais eventos e alocadores por segmento, usar também a agenda curada e o mapeamento da <a href="https://www.fnmkhub.com/" target="_blank" rel="noopener">fnmk</a>.</p>'
    + '<h2 id="editorial">Conteúdo editorial dos <strong>eventos presenciais</strong></h2><div class="tab tab-pilha"><table><tr><th>Quando</th><th>Peça</th><th>Canal</th><th>Dono</th></tr>'
    + "".join(f'<tr><td>{a}</td><td data-r="Peça">{b}</td><td data-r="Canal">{d}</td><td data-r="Dono">{e}</td></tr>' for a, b, d, e in _edit)
    + '</table></div><h3>O ângulo de cada evento</h3><div class="tab tab-pilha"><table><tr><th>Eventos</th><th>Para quem</th><th>Ângulo editorial</th></tr>'
    + "".join(f'<tr><td>{a}</td><td data-r="Para quem">{b}</td><td data-r="Ângulo editorial">{d}</td></tr>' for a, b, d in _ang) + '</table></div><p class="meta-txt">Todas as peças passam pela aprovação de Riscos antes de publicar.</p>')
_exec = [("Bruno Franco", "<!--CEO2-->Infra e energia", "<!--CEO3-->Ilíquidos de infraestrutura e energia"), ("Sami Karlik", "CIO de Crédito", "Crédito privado e estruturado"), ("Huang Seen", "Head de renda fixa", "Juros globais e renda fixa"), ("Vitor Engelmann", "Imobiliário", "Fundos imobiliários e aquisições")]
_acoes = [("Colaboradores", "Post da semana com sugestão de comentário, para quem quiser participar"), ("Canal do Teams", "Cada post novo no canal, com link direto e sugestão de comentário"),
          ("Canal de WhatsApp", "Mensagem curta com gráfico ou vídeo, enquete e aviso antecipado de carta e evento"),
          ("Raio X do Mercado", "Quadro fixo de vídeo, uma edição por trimestre: o mercado de crédito como um todo, com a Vivi e o pessoal de crédito, sempre na mesma estrutura; imobiliário no mesmo formato"), ("Tivio ao Quadrado", "Série mantida, com nova edição no 2º tri")]
_imp_v = [("Bruno Franco", "<!--CEO1-->Infraestrutura e energia"), ("Sami Karlik", "Crédito privado e estruturado"), ("Huang Seen", "Juros e renda fixa"), ("Vitor Engelmann", "Imobiliário")]
_imp_t = [("1º tri", "Perspectivas de estruturados para 2027", "Panorama do evento de janeiro e o Raio X do Mercado"), ("2º tri", "FIDC chega ao varejo: o que olhar antes de investir", "Contas de varejo em FIDC de 147,3 mil para 333,7 mil em cerca de um ano"),
          ("3º tri", "Panorama de Estruturados", "Dado próprio, lançado para a imprensa antes do site"), ("4º tri", "Balanço de estruturados e o que vem em 2028", "Evento de outubro e balanço do ano")]
_imp_r = [("Pauta do mês", "Reunião mensal com a assessoria, a partir da Carta do Gestor e do Raio X do Mercado"), ("Release", "Só com dado novo, lançamento ou evento"), ("Porta-voz pronto", "Uma página de apoio por tema"),
          ("Aprovação", "Revisão e Compliance antes de qualquer resposta escrita"), ("Na Mídia", "Toda matéria volta como post, LinkedIn do porta-voz e newsletter"), ("Clipping por gestor", "Cada gestor recebe só as matérias do tema dele"), ("Medição", "Clipping mensal com menções, porta-voz citado e tema")]
_imp_m = ["Valor Econômico", "Pipeline", "NeoFeed", "Bloomberg Línea", "InfoMoney", "Estadão E-Investidor", "Investidor Institucional"]
_imp = ('<h2 id="porta-vozes">Quem fala <strong>de quê</strong></h2><div class="papeis">' + "".join(f'<div class="papel vidro"><span>{b}</span><b>{a}</b></div>' for a, b in _imp_v) + '</div>'
    + '<h2 id="filtro">Filtro antes dos <strong>gestores</strong></h2><div class="frentes linhas"><section class="frente vidro"><h3>Pedido de imprensa</h3><p class="dono">Fernanda Acquati filtra antes</p><ul><li>Veículo e jornalista</li><li>Tema ligado a estruturados ou a um fundo da casa</li><li>Prazo que o gestor consegue cumprir</li><li>Risco de falar de fundo em oferta</li><li>Só então vai ao gestor, com briefing de uma página</li></ul></section></div>'
    + '<h2 id="pauta">Uma pauta por <strong>trimestre</strong></h2><div class="tab tab-pilha"><table><tr><th>Quando</th><th>Pauta</th><th>Gancho</th></tr>' + "".join(f'<tr><td>{a}</td><td data-r="Pauta">{b}</td><td data-r="Gancho">{d}</td></tr>' for a, b, d in _imp_t) + '</table></div>'
    + '<h2 id="rotina">A <strong>rotina</strong></h2><div class="tab tab-pilha"><table><tr><th>O quê</th><th>Como funciona</th></tr>' + "".join(f'<tr><td>{a}</td><td data-r="Como funciona">{b}</td></tr>' for a, b in _imp_r) + '</table></div>'
    + '<h2 id="veiculos">Onde <strong>aparecer</strong></h2><div class="frentes linhas"><section class="frente vidro"><h3>Veículos</h3><p class="dono">Economia, mercado e previdência</p><ul>' + "".join(f"<li>{x}</li>" for x in _imp_m) + '</ul></section></div>')
corpo_imp = (cabecalho("Imprensa", []) + '<div class="wrap">' + trilha(("index.html", "Início"), ("", "Imprensa"))
    + '<section class="topo-peer"><div><h1>Imprensa</h1><p class="lead">A Tivio como fonte de estruturados na imprensa econômica. Com Fernanda Acquati e a assessoria de imprensa.</p></div></section>' + _imp
    + '<p class="meta-txt">Todas as respostas passam por Revisão e Compliance antes de sair.</p><p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "imprensa.html").write_text(pagina("Imprensa", corpo_imp, CSS_P), encoding="utf-8")
_cont = ('<h2 id="foco">O que publicamos <strong>hoje</strong></h2><p class="secao-sub">14 posts em outubro de 2026, no Instagram.</p>' + _st([("Crédito estruturado", 3), ("Outros temas", 11)])
    + '<h2 id="curtidas">O que mais <strong>engaja</strong></h2><p class="secao-sub">Curtidas por tipo de post, média de outubro.</p>' + _bh(_curt[:6])
    + '<h2 id="executivos">Executivos nas <strong>conversas do LinkedIn</strong></h2><div class="tab tab-pilha"><table><tr><th>Executivo</th><th>Papel</th><th>Conversas para entrar</th></tr>'
    + "".join(f'<tr><td>{a}</td><td data-r="Papel">{b}</td><td data-r="Conversas para entrar">{d}</td></tr>' for a, b, d in _exec) + '</table></div>'
    + '<h2 id="newsletter">Newsletter como <strong>base própria</strong></h2><p class="secao-sub">É o canal que não depende de algoritmo: cada inscrito vira um contato com perfil conhecido.</p><div class="tab tab-pilha"><table><tr><th>Ação</th><th>Como funciona</th></tr>'
    + "".join(f'<tr><td>{a}</td><td data-r="Como funciona">{b}</td></tr>' for a, b in [("Formulário curto", "De 6 campos para nome, e-mail e perfil"), ("Promessa clara", "O que muda em estruturados, uma vez por mês"), ("Edição", "Carta do mês, Gráfico da Semana, um vídeo e o próximo evento"), ("Por público", "Assessor, institucional e investidor recebem o destaque certo"), ("Onde convidar", "Bio do Instagram, LinkedIn, fim dos artigos, QR nos eventos, landings e WhatsApp"), ("Motivo para assinar", "Panorama de Estruturados e convites de evento primeiro para quem assina")]) + '</table></div>'
    + '<h2 id="engajar">Mais <strong>engajamento</strong></h2><div class="tab tab-pilha"><table><tr><th>Ação</th><th>Como funciona</th></tr>'
    + "".join(f'<tr><td>{a}</td><td data-r="Como funciona">{b}</td></tr>' for a, b in _acoes) + '</table></div>')
for _i, (_n, _s, _o, _l) in enumerate([(x[0], x[1], x[2], x[3]) for x in _fr27]):
    _col = {"Automação": 1, "Eventos": 2, "Conteúdo": 3}.get(_n, 4)
    _c = (cabecalho(_n, []) + '<div class="wrap">' + trilha(("index.html", "Início"), ("plano-2027.html", "Plano"), ("", _n))
        + f'<section class="topo-peer"><div>{ICO27[_n]}<h1>{_n}</h1><p class="lead">{_o}</p></div></section>'
        + '<h2>O que vamos <strong>fazer</strong></h2><ol class="roteiro r6' + (' as-o' if len(_l) == 4 else '') + '">' + "".join(f'<li class="vidro"><b>{x}</b></li>' for x in _l) + '</ol>'
        + (_site if _n.startswith("Digital") else _cont if _n == "Conteúdo" else _evt if _n == "Eventos" else "")
        + '<h2>Como se encaixa <strong>no todo</strong></h2>' + _lig_tab(_n)
        + '<h2>Os <strong>números</strong></h2><div class="tab tab-pilha"><table><tr><th>Número</th><th>Hoje</th></tr>' + "".join(f'<tr><td>{b}</td><td data-r="Hoje">{d}</td></tr>' for a, b, d in _num27 if a == _n) + '</table></div>' + '<p class="meta-txt">Dashboard de redes sociais com Fernanda Acquati.</p>'
        + '<h2>O <strong>ano</strong></h2>' + _gantt(_n) + _tl(_col)
        + '<h2>O que veio do <strong>benchmark</strong></h2><div class="tab tab-pilha"><table><tr><th>O que aprendemos</th><th>O que fazemos hoje</th><th>Como entra</th></tr>' + "".join(f'<tr><td><a href="frente-benchmark.html">{b}</a></td><td data-r="O que fazemos hoje">{h}</td><td data-r="Como entra">{d}</td></tr>' for a, b, q, h, d in _bm if a == _n) + '</table></div>'
        + '<h2>Onde <strong>ver</strong></h2>' + cartoes(_ver[_n])
        + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
    (EXTRA / _s).write_text(pagina(_n, _c, CSS_P), encoding="utf-8")
_c = (cabecalho("Benchmark", []) + '<div class="wrap">' + trilha(("index.html", "Início"), ("plano-2027.html", "Plano"), ("", "Benchmark"))
    + '<section class="topo-peer"><div><h1>Benchmark</h1><p class="lead">O que estudamos fora da Tivio, o que já fazemos e como isso entra nas quatro frentes.</p></div></section>'
    + '<h2>O que vimos fora e o que <strong>fazemos</strong></h2>' + _bm_vis
    + '<h2>Bases <strong>externas</strong></h2><div class="frentes linhas"><section class="frente vidro"><h3><a href="https://www.fnmkhub.com/" target="_blank" rel="noopener">fnmk</a></h3><p class="dono">Inteligência para o mercado de capitais</p><ul><li>Alocadores por segmento: assets, wealth, family offices e fundos de pensão</li><li>Insights e benchmarks para o discurso</li><li>Agenda curada de eventos e encontros</li><li>Entra em Eventos, Conteúdo e Benchmark</li></ul></section><section class="frente vidro"><h3><a href="https://www.notlistedclub.com/pt" target="_blank" rel="noopener">Not Listed</a></h3><p class="dono">Estudo de wealth da fnmk, 2ª edição</p><ul><li>1.202 casas de gestão e consultoria de patrimônio mapeadas, em 129 cidades</li><li>Dado público organizado: 555 formulários da CVM e ANBIMA</li><li>Entrevistas com UBS, Hamilton Lane e Christie&#39;s</li><li>Edição anual com cinco matérias e e-mail profissional para receber</li><li>Na Tivio: modelo para o Panorama de Estruturados</li></ul></section></div>'
    + '<h2>Onde <strong>ver</strong></h2>' + cartoes([("m-peers.html", "Peers no Brasil", "Gestoras brasileiras."), ("m-estrangeiras.html", "Peers no exterior", "Gestoras de fora."), ("m-cases.html", "Cases", "O que outros fizeram."), ("m-mundo.html", "Mundo", "Tendências lá fora."), ("m-mercados.html", "Outros mercados", "Referências de outros países."), ("m-setores.html", "Outros setores", "O que copiar de fora das finanças."), ("m-relatorio.html", "Relatório 2027", "Estudos de marketing para 2027.")])
    + '<p class="rodape">Tivio Capital · Comunicação &amp; Marketing</p></div>')
(EXTRA / "frente-benchmark.html").write_text(pagina("Benchmark", _c, CSS_P), encoding="utf-8")

(EXTRA / "fim-de-ano.html").write_text(pagina("Plano", cabecalho("Plano", []) + '<div class="wrap"><p><a href="plano-2027.html#fim-do-ano">Abrir o Plano, até o fim do ano</a></p><script>location.replace("plano-2027.html#fim-do-ano")</script></div>', CSS_P), encoding="utf-8")
(EXTRA / "transicao.html").write_text(pagina("Transição", cabecalho("Transição", []) + '<div class="wrap"><p class="rodape">Tivio Capital</p></div>', CSS_P), encoding="utf-8")
