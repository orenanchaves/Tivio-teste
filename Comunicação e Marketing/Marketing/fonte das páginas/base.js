// botão de tema: claro ou escuro; sem escolha, segue o sistema
(function(){
  var raiz=document.documentElement,bts=[].slice.call(document.querySelectorAll('.tema button'));
  function atual(){var t=raiz.getAttribute('data-theme');if(t)return t;return window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';}
  function marca(){var t=atual();bts.forEach(function(b){b.setAttribute('aria-pressed',b.dataset.tema===t);});}
  try{var s=localStorage.getItem('tivio-tema');if(s)raiz.setAttribute('data-theme',s);}catch(e){}
  bts.forEach(function(b){b.addEventListener('click',function(){
    raiz.setAttribute('data-theme',b.dataset.tema);try{localStorage.setItem('tivio-tema',b.dataset.tema);}catch(e){}
    marca();window.dispatchEvent(new Event('tivio-tema'));
  });});
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change',marca);
  marca();
})();
// botões de copiar
document.querySelectorAll('[data-copiar]').forEach(function(b){
  b.addEventListener('click',function(){
    var el=document.getElementById(b.dataset.copiar),txt=b.textContent;
    function sel(){var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r);}
    try{navigator.clipboard.writeText(el.textContent).then(function(){b.textContent='Copiado';setTimeout(function(){b.textContent=txt},1600)},sel)}catch(e){sel()}
  });
});
