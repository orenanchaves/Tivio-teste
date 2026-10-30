(function(){
  var q=document.getElementById('q'),res=document.getElementById('fres'),conta=document.getElementById('fconta'),vazio=document.getElementById('fvazio');
  var chips=[].slice.call(document.querySelectorAll('.fchip')),sel={k:[],s:[],p:[]};
  function sem(t){return t.normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();}
  ITENS.forEach(function(i){i.b=sem(i.t+' '+i.x);});
  function passa(i,termos){
    if(sel.k.length&&sel.k.indexOf(i.k)<0)return false;
    if(sel.s.length&&!sel.s.some(function(v){return i.s.indexOf(v)>=0;}))return false;
    if(sel.p.length&&!sel.p.some(function(v){return i.p.indexOf(v)>=0;}))return false;
    return termos.every(function(t){return i.b.indexOf(t)>=0;});
  }
  function desenha(){
    var termos=sem(q.value).split(/\s+/).filter(Boolean),r=ITENS.filter(function(i){return passa(i,termos);});
    res.textContent='';
    r.forEach(function(i){
      var a=document.createElement('a');a.className='sub vidro';a.href=i.u;
      var k=document.createElement('small');k.textContent=i.k;
      var b=document.createElement('b');b.textContent=i.t;
      var s=document.createElement('span');s.textContent=i.r;
      a.appendChild(k);a.appendChild(b);a.appendChild(s);res.appendChild(a);
    });
    conta.textContent=r.length+(r.length===1?' página':' páginas');
    vazio.hidden=r.length>0;
  }
  chips.forEach(function(c){c.addEventListener('click',function(){
    var l=sel[c.dataset.g],i=l.indexOf(c.dataset.v),on=i<0;
    if(on)l.push(c.dataset.v);else l.splice(i,1);
    c.setAttribute('aria-pressed',on);desenha();
  });});
  q.addEventListener('input',desenha);
  document.getElementById('flimpa').addEventListener('click',function(){
    q.value='';sel={k:[],s:[],p:[]};chips.forEach(function(c){c.setAttribute('aria-pressed','false');});desenha();
  });
  desenha();
})();
