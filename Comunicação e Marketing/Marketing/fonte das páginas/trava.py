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
*{box-sizing:border-box}html,body{margin:0;min-height:100%}body{min-height:100dvh;display:flex;align-items:center;justify-content:center;padding:24px 16px;background:var(--bg-radial),var(--bg);background-attachment:fixed;color:var(--fg);font:400 16px/1.5 var(--ff)}
.ent{width:100%;max-width:420px;padding:32px 24px;border:1px solid var(--line);border-radius:16px;background:var(--bg-elev)}.ent[hidden]{display:none}
.ent svg{display:block;width:176px;height:auto;margin-bottom:32px}.ent svg *{fill:currentColor}
.ent h1{margin:0 0 4px;font:600 26px/1.2 var(--ff)}.ent>p{margin:0 0 24px;color:var(--muted)}
.ent label{display:block;margin-bottom:8px;font-weight:600}.ent input{display:block;width:100%;height:48px;padding:0 16px;border:1px solid var(--line-strong);border-radius:999px;background:transparent;color:var(--fg);font:400 16px var(--ff)}
.ent button{display:block;width:100%;height:48px;margin-top:12px;border:0;border-radius:999px;background:#3C4A60;color:#FFF;font:600 16px var(--ff);cursor:pointer}.ent button:disabled{opacity:.7;cursor:wait}
.ent #e{margin:12px 0 0}
"""
(OUT/"entrar.css").write_text(css, encoding="utf-8")
JS = """(function(){try{var t=localStorage.getItem('tivio-tema');if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}catch(x){}
var Q='tivio-chave',F=document.getElementById('f'),E=document.getElementById('e');function u(x){return Uint8Array.from(atob(x),function(c){return c.charCodeAt(0)})}
async function abre(k){var p=await crypto.subtle.decrypt({name:'AES-GCM',iv:u(D.i)},k,u(D.c));var h=new TextDecoder().decode(p);document.open();document.write(h);document.close()}
async function chave(){var g=null;try{g=sessionStorage.getItem(Q)}catch(x){}if(!g)return null;try{return await crypto.subtle.importKey('raw',u(g),'AES-GCM',false,['decrypt'])}catch(x){return null}}
(async function(){var k=await chave();if(k){try{await abre(k);return}catch(x){try{sessionStorage.removeItem(Q)}catch(y){}}}F.hidden=false;document.getElementById('s').focus()})();
document.getElementById('l').addEventListener('submit',async function(e){e.preventDefault();E.hidden=true;var B=this.querySelector('button');B.disabled=true;try{var kb=await crypto.subtle.importKey('raw',new TextEncoder().encode(document.getElementById('s').value),'PBKDF2',false,['deriveKey']);
var k=await crypto.subtle.deriveKey({name:'PBKDF2',salt:u(D.s),iterations:D.n,hash:'SHA-256'},kb,{name:'AES-GCM',length:256},true,['decrypt']);var r=new Uint8Array(await crypto.subtle.exportKey('raw',k));try{sessionStorage.setItem(Q,btoa(String.fromCharCode.apply(null,r)))}catch(x){}await abre(k)}catch(x){try{sessionStorage.removeItem(Q)}catch(y){}E.hidden=false;B.disabled=false}})})();"""
def casca(iv, ct):
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Comunicação &amp; Marketing</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex,nofollow">
<meta name="tivio-trava" content="1">
<link rel="stylesheet" href="entrar.css">
</head>
<body>
<main class="ent" id="f" hidden>{logo}<h1>Comunicação &amp; Marketing</h1><p>Área restrita da Tivio Capital.</p><form id="l"><label for="s">Senha</label><input id="s" type="password" autocomplete="current-password" required><button type="submit">Entrar</button><p id="e" role="alert" hidden>Senha incorreta.</p></form></main>
<script>var D={{s:"{b(sal)}",i:"{b(iv)}",c:"{b(ct)}",n:{ITER}}};{JS}</script>
</body>
</html>
"""
for f in sorted(ORIG.glob("*.html")):
    h = f.read_text(encoding="utf-8")
    if f.name == "orcamento.html":
        i = h.index('<div class="wrap">'); j = h.rindex('<p class="rodape">'); j = h.index("</div>", j) + 6
        h = h[:i] + (S/"orc_frag.html").read_text(encoding="utf-8") + h[j:]
    iv = os.urandom(12)
    (OUT/f.name).write_text(casca(iv, AESGCM(k).encrypt(iv, h.encode("utf-8"), None)), encoding="utf-8")
print("cifradas", len(list(OUT.glob("*.html"))))
