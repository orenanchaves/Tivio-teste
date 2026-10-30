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

// setas do menu: aparecem só quando há mais itens para aquele lado
(function(){
  var menu=document.querySelector('.menu');if(!menu)return;
  var chips=menu.querySelector('.chips');if(!chips)return;
  var volta=menu.querySelector('[data-dir="-1"]'),vai=menu.querySelector('[data-dir="1"]');
  function atualiza(){
    var fim=chips.scrollWidth-chips.clientWidth-2;
    volta.hidden=chips.scrollLeft<=2;vai.hidden=chips.scrollLeft>=fim;
  }
  [volta,vai].forEach(function(b){b.addEventListener('click',function(){
    chips.scrollBy({left:Number(b.dataset.dir)*Math.max(220,chips.clientWidth*.7),behavior:'smooth'});
  });});
  chips.addEventListener('scroll',atualiza,{passive:true});
  window.addEventListener('resize',atualiza);
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(atualiza);
  atualiza();
})();
