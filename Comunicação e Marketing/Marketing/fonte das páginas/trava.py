import base64, os, pathlib, re, shutil, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
S = pathlib.Path(sys.argv[1]); R = pathlib.Path(sys.argv[2]); SENHA = sys.argv[3]
ORIG = S/"ghpages"; OUT = S/"ghpages-trava"
shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir()
ITER = 600000
fsal = S/"trava_sal.bin"
if not fsal.exists(): fsal.write_bytes(os.urandom(16))
sal = fsal.read_bytes()
k = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=sal, iterations=ITER).derive(SENHA.encode())
b = lambda x: base64.b64encode(x).decode()
logo = (R/"AutomaTivio/assets/marca/tivio.svg").read_text(encoding="utf-8")
logo = logo[logo.index("<svg"):]
idx = (ORIG/"index.html").read_text(encoding="utf-8")
fontes = "".join(re.findall(r"@font-face\{font-family:Versos;font-weight:(?:400|600);.*?\}", idx, flags=re.S))
assert fontes.count("@font-face") == 2
claro = "--bg:#EEF3F6;--bg-elev:linear-gradient(135deg,rgba(255,255,255,.92),rgba(255,255,255,.70));--bg-radial:radial-gradient(1200px 800px at 15% -10%,rgba(60,74,96,.14),transparent 60%),radial-gradient(900px 700px at 110% 10%,rgba(117,157,180,.12),transparent 60%);--fg:#0A0F14;--muted:#4a5a66;--line:rgba(10,15,20,.08);--line-strong:rgba(10,15,20,.18);color-scheme:light"
css = fontes + """:root{--bg:#0A0F14;--bg-elev:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.015));--bg-radial:radial-gradient(1200px 800px at 15% -10%,rgba(117,157,180,.14),transparent 60%),radial-gradient(900px 700px at 110% 10%,rgba(200,215,224,.08),transparent 60%);--fg:#FFFFFF;--muted:#8A99A3;--line:rgba(255,255,255,.10);--line-strong:rgba(255,255,255,.18);--ff:"Versos","Helvetica Neue",Helvetica,Arial,sans-serif;color-scheme:dark}
@media (prefers-color-scheme:light){:root:not([data-theme="dark"]){""" + claro + """}}
:root[data-theme="light"]{""" + claro + """}
.trv,.trv *{box-sizing:border-box}.trv{margin:0;min-height:100dvh;display:flex;align-items:center;justify-content:center;padding:24px 16px;background:var(--bg-radial),var(--bg);background-attachment:fixed;color:var(--fg);font:400 16px/1.5 var(--ff)}
.ent{width:100%;max-width:420px;padding:32px 24px;text-align:center;border:1px solid var(--line);border-radius:16px;background:var(--bg-elev)}.ent[hidden]{display:none}
.ent svg{display:block;width:176px;height:auto;margin:0 auto 32px}.ent svg *{fill:currentColor}
.ent h1{margin:0 0 4px;font:600 26px/1.2 var(--ff)}.ent>p{margin:0 0 24px;color:var(--muted)}
.ent label{display:block;margin-bottom:8px;font-weight:600}.ent input{display:block;width:100%;height:48px;padding:0 16px;border:1px solid var(--line-strong);border-radius:999px;background:transparent;color:var(--fg);font:400 16px var(--ff);text-align:center}
.ent button{display:block;width:100%;height:48px;margin-top:12px;border:0;border-radius:999px;background:#3C4A60;color:#FFF;font:600 16px var(--ff);cursor:pointer}.ent button:disabled{opacity:.7;cursor:wait}
.ent #e{margin:12px 0 0}
.car{display:flex;align-items:center;justify-content:center}.car[hidden]{display:none}.car svg{display:block;width:96px;height:auto}.car path{fill:currentColor;opacity:.15;animation:carT 1.5s ease-in-out infinite}.car path:nth-child(2){animation-delay:.18s}.car path:nth-child(3){animation-delay:.36s}
@keyframes carT{0%,100%{opacity:.15}35%,65%{opacity:1}}
@media (prefers-reduced-motion:reduce){.car path{animation:none;opacity:1}}
"""
(OUT/"entrar.css").write_text(css, encoding="utf-8")
shutil.copy(S/"favicon.ico", OUT/"favicon.ico")
JS = """(function(){try{var t=localStorage.getItem('tivio-tema');if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}catch(x){}
var Q='tivio-chave',F=document.getElementById('f'),E=document.getElementById('e'),C=document.getElementById('c');function u(x){return Uint8Array.from(atob(x),function(c){return c.charCodeAt(0)})}
async function abre(k,m){var p=await crypto.subtle.decrypt({name:'AES-GCM',iv:u(D.i)},k,u(D.c));var h=new TextDecoder().decode(p);if(m)await new Promise(function(r){setTimeout(r,Math.max(0,m-Date.now()))});if(document.readyState!=='complete')await new Promise(function(r){addEventListener('load',r)});document.open();document.write(h);document.close()}
async function chave(){var g=null;try{g=sessionStorage.getItem(Q)}catch(x){}if(!g)return null;try{return await crypto.subtle.importKey('raw',u(g),'AES-GCM',false,['decrypt'])}catch(x){return null}}
(async function(){var k=await chave();if(k){try{await abre(k);return}catch(x){try{sessionStorage.removeItem(Q)}catch(y){}}}F.hidden=false;document.getElementById('s').focus()})();
document.getElementById('l').addEventListener('submit',async function(e){e.preventDefault();E.hidden=true;var B=this.querySelector('button'),M=Date.now()+1500;B.disabled=true;F.hidden=true;C.hidden=false;try{var kb=await crypto.subtle.importKey('raw',new TextEncoder().encode(document.getElementById('s').value),'PBKDF2',false,['deriveKey']);
var k=await crypto.subtle.deriveKey({name:'PBKDF2',salt:u(D.s),iterations:D.n,hash:'SHA-256'},kb,{name:'AES-GCM',length:256},true,['decrypt']);var r=new Uint8Array(await crypto.subtle.exportKey('raw',k));try{sessionStorage.setItem(Q,btoa(String.fromCharCode.apply(null,r)))}catch(x){}await abre(k,M)}catch(x){try{sessionStorage.removeItem(Q)}catch(y){}C.hidden=true;F.hidden=false;E.hidden=false;B.disabled=false;document.getElementById('s').focus()}})})();"""
TRANS = """<style>@keyframes tvIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}.wrap{animation:tvIn .32s ease-out}.wrap.tv-sai{opacity:0;transition:opacity .16s ease-in}@media (prefers-reduced-motion:reduce){.wrap{animation:none}.wrap.tv-sai{transition:none}}</style><script>document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href]');if(!a||e.defaultPrevented||e.button||e.metaKey||e.ctrlKey||e.shiftKey||a.target||a.hasAttribute('download'))return;var u=new URL(a.href,location.href);if(u.origin!==location.origin||u.pathname===location.pathname)return;var w=document.querySelector('.wrap');if(!w||matchMedia('(prefers-reduced-motion: reduce)').matches)return;e.preventDefault();w.classList.add('tv-sai');setTimeout(function(){location.href=a.href},160)});addEventListener('pageshow',function(e){if(e.persisted){var w=document.querySelector('.wrap');if(w)w.classList.remove('tv-sai')}})</script>"""
def casca(iv, ct):
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Comunicação &amp; Marketing</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex,nofollow">
<meta name="tivio-trava" content="1">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="stylesheet" href="entrar.css">
</head>
<body class="trv">
<main class="ent" id="f" hidden>{logo}<h1>Comunicação &amp; Marketing</h1><p>Área restrita da Tivio Capital.</p><form id="l"><label for="s">Senha</label><input id="s" type="password" autocomplete="current-password" required><button type="submit">Entrar</button><p id="e" role="alert" hidden>Senha incorreta.</p></form></main>
<div class="car" id="c" role="status" aria-label="Carregando" hidden><svg viewBox="118 106 213 186" aria-hidden="true"><path d="M173.91,110.53h-51.56v26.9h102.14l-2.53-3.27c-11.6-15.02-29.12-23.63-48.06-23.63Z"/><path d="M227.02,134.16l-2.53,3.27h102.14v-26.9h-51.56c-18.94,0-36.45,8.61-48.06,23.63Z"/><path d="M210.25,176.57v111.2s28.51,0,28.51,0l-.02-111.2c0-13.53-4.37-26.35-12.64-37.06l-1.61-2.08-1.61,2.08c-8.27,10.71-12.64,23.52-12.64,37.06Z"/></svg></div>
<script>var D={{s:"{b(sal)}",i:"{b(iv)}",c:"{b(ct)}",n:{ITER}}};{JS}</script>
</body>
</html>
"""
for f in sorted(ORIG.glob("*.html")):
    h = f.read_text(encoding="utf-8")
    fr = {"orcamento.html": "orc_frag.html", "transicao.html": "transicao_frag.html"}.get(f.name)
    if fr:
        i = h.index('<div class="wrap">'); j = h.rindex('<p class="rodape">'); j = h.index("</div>", j) + 6
        h = h[:i] + (S/fr).read_text(encoding="utf-8") + h[j:]
    h = h.replace("</head>", TRANS + "</head>", 1)
    h = h.replace("<!--METAS-->", (S/"metas_frag.html").read_text(encoding="utf-8"))
    h = h.replace("<!--REF-TIME-->", (S/"ref_time_frag.html").read_text(encoding="utf-8"))
    h, n = re.subn(r'<p class="(?:eyebrow|sl-e)"[^>]*>.*?</p>', "", h, flags=re.S)
    if "favicon.ico" not in h: h = h.replace("</title>", '</title>\n<link rel="icon" href="favicon.ico" sizes="any">', 1)
    assert 'class="eyebrow' not in h and 'class="sl-e' not in h, f.name
    iv = os.urandom(12)
    (OUT/f.name).write_text(casca(iv, AESGCM(k).encrypt(iv, h.encode("utf-8"), None)), encoding="utf-8")
print("cifradas", len(list(OUT.glob("*.html"))))
