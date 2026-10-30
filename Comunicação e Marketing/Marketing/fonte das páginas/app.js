// abas genéricas: cada botão role=tab mostra o painel do aria-controls, dentro do mesmo grupo
function ligarAbas(seletor){
  var abas=[].slice.call(document.querySelectorAll(seletor));
  abas.forEach(function(a){a.addEventListener('click',function(){
    abas.forEach(function(x){var on=x===a;x.setAttribute('aria-selected',on);document.getElementById(x.getAttribute('aria-controls')).hidden=!on;});
  });});
}
ligarAbas('.perfis [role="tab"]');
ligarAbas('.app-nav [role="tab"]');

// Marketing: OK de dados
(function(){
  var b=document.getElementById('ok-dados'),m=document.getElementById('ok-dados-msg');
  if(!b)return;
  b.addEventListener('click',function(){
    var dado=b.dataset.dado==='1';
    b.dataset.dado=dado?'0':'1';
    b.textContent=dado?'Dar OK nos dados':'Desfazer o OK';
    m.textContent=dado?'Aguardando o OK de quem confere os dados.':'OK dado. A Gestão já pode enviar os comentários e a rodada está liberada.';
    m.classList.toggle('ok-txt',!dado);
  });
})();

// Gestão: comentários por segmento -> comentarios.md
(function(){
  var SEG={
    cp:['Tivio Banks','Tivio Institucional','Tivio Institucional 15','Tivio Institucional 30','Tivio Infra Plus','Tivio Infra Plus CDI','Tivio Esplanada','Tivio Legacy Prev','Tivio RF CP','Tivio BVP','Institucional Incentivado CDI','Tivio HGD30','Tivio HYD60'],
    ce:['Tivio ALT 180','Tivio ALT 90','Tivio ALT Light'],
    is:['Tivio Prev Low Vol','Tivio Prev Top Credit']
  };
  var NOTA={'Tivio HGD30':'Previdência: só o complemento do mês. O mercado vem do Tivio Institucional e a frase de rentabilidade sai da tabela.','Tivio HYD60':'Previdência: só o complemento do mês, como no HGD30.'};
  var texto={'Tivio ALT 180':'O Tivio ALT 180 registrou rentabilidade de {mes} no mês, equivalente a {pct_mes} do CDI no período. Desde o início da estratégia, o fundo acumula retorno de {inicio}.\n\nEm {mes_nome}, iniciamos posição em uma cota sênior de FIDC com exposição ao setor de telecomunicações.'};
  if(!document.getElementById('coment-form'))return;
  var form=document.getElementById('coment-form'),md=document.getElementById('md'),prog=document.getElementById('progresso'),atual='cp';
  var todos=[].concat(SEG.cp,SEG.ce,SEG.is);
  function idDe(n){return 'f-'+n.toLowerCase().replace(/[^a-z0-9]+/g,'-');}
  function cheio(n){return !!(texto[n]||'').trim();}
  function progresso(){
    var f=todos.filter(cheio).length;
    prog.innerHTML='<i></i>'+f+' de '+todos.length+' fundos';
    prog.className='pill '+(f===todos.length?'ok':'aviso');
  }
  function montarMd(){
    var out=['# Relatório',''];
    todos.forEach(function(n){
      if(!cheio(n))return;
      var pars=texto[n].trim().split(/\n\s*\n/).map(function(p){return p.trim().replace(/\s*\n\s*/g,' ');}).filter(Boolean);
      out.push('## '+n,'');pars.forEach(function(p){out.push(p,'');});
    });
    if(out.length===2)out.push('(nenhum comentário preenchido)');
    md.textContent=out.join('\n');progresso();
  }
  function desenhar(){
    form.innerHTML='';
    SEG[atual].forEach(function(n){
      var w=document.createElement('div');w.className='campo';
      var l=document.createElement('label');l.htmlFor=idDe(n);l.textContent=n;
      var st=document.createElement('span');st.className='campo-st';
      var t=document.createElement('textarea');t.id=idDe(n);t.rows=3;t.value=texto[n]||'';
      t.placeholder='Comentário do mês. Parágrafos separados por uma linha em branco.';
      function marca(){var ok=!!t.value.trim();st.textContent=ok?'Preenchido':'Falta';st.classList.toggle('ok-txt',ok);}
      t.addEventListener('input',function(){texto[n]=t.value;marca();montarMd();});
      marca();
      var cab=document.createElement('div');cab.className='campo-cab';cab.appendChild(l);cab.appendChild(st);
      w.appendChild(cab);
      if(NOTA[n]){var p=document.createElement('p');p.className='meta-txt';p.textContent=NOTA[n];w.appendChild(p);}
      w.appendChild(t);form.appendChild(w);
    });
  }
  var botoes=[].slice.call(document.querySelectorAll('.segs button'));
  botoes.forEach(function(b){b.addEventListener('click',function(){
    atual=b.dataset.seg;botoes.forEach(function(x){x.setAttribute('aria-pressed',x===b);});desenhar();
  });});
  var c=document.getElementById('copiar-md');
  c.addEventListener('click',function(){
    function sel(){var r=document.createRange();r.selectNodeContents(md);var s=getSelection();s.removeAllRanges();s.addRange(r);}
    try{navigator.clipboard.writeText(md.textContent).then(function(){c.textContent='Copiado';setTimeout(function(){c.textContent='Copiar'},1600)},sel)}catch(e){sel()}
  });
  var env=document.getElementById('enviar-coment'),em=document.getElementById('enviar-msg');
  env.addEventListener('click',function(){
    var falta=todos.filter(function(n){return !cheio(n);}).length;
    em.textContent=falta?('Enviado (simulação). '+falta+' fundos sem comentário saem com texto provisório e entram como aviso para Riscos.'):'Enviado (simulação). Todos os fundos com comentário.';
    em.classList.toggle('ok-txt',!falta);
  });
  desenhar();montarMd();
})();

// Riscos decide; Publicar, na página do Marketing, lê a decisão (exemplo: fica neste navegador)
function lerRev(){try{return JSON.parse(localStorage.getItem('tivio-revisao')||'{}');}catch(e){return {};}}
function gravarRev(r){try{localStorage.setItem('tivio-revisao',JSON.stringify(r));}catch(e){}}
(function(){
  var lista=document.getElementById('revisao');if(!lista)return;
  var cont=document.getElementById('aprov-cont'),itens=[].slice.call(lista.querySelectorAll('li')),rev=lerRev();
  function contar(){
    var a=itens.filter(function(li){return li.dataset.estado==='aprovado';}).length;
    cont.innerHTML='<i></i>'+a+' de '+itens.length+' aprovados';cont.className='pill '+(a===itens.length?'ok':'aviso');
  }
  function aplicar(li,novo){
    li.dataset.estado=novo;rev[li.dataset.id]=novo;gravarRev(rev);
    var motivo=li.querySelector('.motivo');
    if(novo==='ajuste'&&!motivo){
      motivo=document.createElement('div');motivo.className='motivo';
      var id='m-'+li.dataset.id;
      motivo.innerHTML='<label for="'+id+'">O que precisa mudar</label><textarea id="'+id+'" rows="2"></textarea>';
      li.appendChild(motivo);
    } else if(novo!=='ajuste'&&motivo){motivo.remove();}
    li.querySelector('[data-acao="aprovar"]').textContent=novo==='aprovado'?'Aprovado':'Aprovar';
    contar();
  }
  itens.forEach(function(li){
    if(rev[li.dataset.id])aplicar(li,rev[li.dataset.id]);
    li.querySelectorAll('[data-acao]').forEach(function(b){b.addEventListener('click',function(){
      var alvo=b.dataset.acao==='aprovar'?'aprovado':'ajuste';
      aplicar(li,li.dataset.estado===alvo?'':alvo);
    });});
  });
  contar();
})();
(function(){
  var pub=document.getElementById('pub');if(!pub)return;
  var rev=lerRev(),mapa={aprovado:['ok','Liberado para baixar'],ajuste:['aviso','Ajuste pedido']};
  [].forEach.call(pub.querySelectorAll('li'),function(li){
    var e=mapa[rev[li.dataset.id]];if(!e)return;
    var p=li.querySelector('.pill');p.className='pill '+e[0];p.innerHTML='<i></i>'+e[1];
  });
})();

// Marketing > Rodada: simulação das etapas
(function(){
  var btn=document.getElementById('simular');if(!btn)return;
  var itens=[].slice.call(document.querySelectorAll('#etapas li')),rodando=false;
  var lento=!window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  btn.addEventListener('click',function(){
    if(rodando)return;rodando=true;btn.disabled=true;btn.textContent='Rodando…';
    itens.forEach(function(li){li.dataset.st='espera'});
    var i=0;
    (function passo(){
      if(i>0)itens[i-1].dataset.st=itens[i-1].dataset.fim;
      if(i===itens.length){btn.disabled=false;btn.textContent='Simular uma rodada';rodando=false;return;}
      itens[i].dataset.st='rodando';i++;setTimeout(passo,lento?700:50);
    })();
  });
})();
