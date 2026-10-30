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

// menu com dropdown: abre um por vez, por clique ou passando o mouse; no celular vira lista
(function(){
  var dds=[].slice.call(document.querySelectorAll('.dd'));if(!dds.length)return;
  var nav=document.getElementById('nav-global'),btn=document.querySelector('.menu-btn');
  var mouse=window.matchMedia('(hover: hover) and (min-width: 1000px)');
  function fecha(menos){dds.forEach(function(d){if(d!==menos)d.open=false;});}
  dds.forEach(function(d){
    d.addEventListener('toggle',function(){if(d.open)fecha(d);});
    d.querySelector('summary').addEventListener('click',function(e){if(mouse.matches){e.preventDefault();d.open=true;fecha(d);}});
    d.addEventListener('mouseenter',function(){if(mouse.matches){d.open=true;}});
    d.addEventListener('mouseleave',function(){if(mouse.matches){d.open=false;}});
  });
  document.addEventListener('click',function(e){if(!e.target.closest('.nav-global')&&!e.target.closest('.menu-btn')){fecha();}});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'){fecha();nav.classList.remove('aberto');btn.setAttribute('aria-expanded','false');}});
  btn.addEventListener('click',function(){var a=nav.classList.toggle('aberto');btn.setAttribute('aria-expanded',a);});
})();

// campo de pesquisa nas listas de fichas
document.querySelectorAll('.fichas').forEach(function(g,n){
  var cards=[].slice.call(g.children);if(cards.length<4)return;
  function sem(t){return t.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();}
  var w=document.createElement('label');w.className='busca mini-busca';w.htmlFor='ff'+n;
  var s=document.createElement('span');s.textContent='Pesquisar';
  var i=document.createElement('input');i.id='ff'+n;i.type='search';i.placeholder='Nome ou assunto';i.autocomplete='off';
  w.appendChild(s);w.appendChild(i);g.parentNode.insertBefore(w,g);
  i.addEventListener('input',function(){var t=sem(i.value).split(/\s+/).filter(Boolean);
    cards.forEach(function(c){var b=sem(c.textContent);c.hidden=!t.every(function(x){return b.indexOf(x)>=0;});});});
});

// filtro por ano na Visão
(function(){
  var bts=[].slice.call(document.querySelectorAll('.anos button'));if(!bts.length)return;
  var secs=[].slice.call(document.querySelectorAll('[data-anos]'));
  bts.forEach(function(b){b.addEventListener('click',function(){
    var a=b.dataset.ano;
    bts.forEach(function(x){x.setAttribute('aria-pressed',x===b);});
    secs.forEach(function(s){s.hidden=a!=='todos'&&s.dataset.anos.split(' ').indexOf(a)<0;});
  });});
})();
