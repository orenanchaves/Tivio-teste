// T da Tivio em 3D: extrudado do mesmo SVG do logo (assets/marca/tivio_t.svg),
// metal verde como no render do Blender (Marca_3D). Gira sozinho e pelo arraste.
// Sem WebGL, fica a imagem renderizada que já está na caixa.
(function(){
  var caixa=document.getElementById('t3d');
  if(!caixa||!window.THREE||!THREE.SVGLoader)return;
  var D='M227.02,134.16l-2.53,3.27h102.14v-26.9h-51.56c-18.94,0-36.45,8.61-48.06,23.63ZM210.25,176.57v111.2s28.51,0,28.51,0l-.02-111.2c0-13.53-4.37-26.35-12.64-37.06l-1.61-2.08-1.61,2.08c-8.27,10.71-12.64,23.52-12.64,37.06ZM173.91,110.53h-51.56v26.9h102.14l-2.53-3.27c-11.6-15.02-29.12-23.63-48.06-23.63Z';
  var renderer;
  try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});}catch(e){return;}
  if(!renderer.getContext())return;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.outputEncoding=THREE.sRGBEncoding;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=1.0;

  var cena=new THREE.Scene();
  var camera=new THREE.PerspectiveCamera(30,1,1,2000);
  camera.position.set(0,0,560);

  // reflexo: faixas claras e escuras alternadas, é o contraste que faz o metal parecer metal
  var pm=new THREE.PMREMGenerator(renderer),amb=new THREE.Scene();
  amb.background=new THREE.Color(0x05080a);
  function placa(x,y,z,l,a,p,cor,forca){
    var m=new THREE.Mesh(new THREE.BoxGeometry(l,a,p),new THREE.MeshBasicMaterial({color:new THREE.Color(cor).multiplyScalar(forca)}));
    m.position.set(x,y,z);amb.add(m);
  }
  placa(0,420,0,1200,30,500,0xffffff,5);
  placa(-520,120,260,60,700,220,0xffffff,4);
  placa(520,60,300,50,700,160,0xdff5ea,3.2);
  placa(0,-30,620,160,560,30,0xffffff,2.6);
  placa(-300,-380,200,420,30,300,0x9fd8bf,1.6);
  placa(320,240,-420,500,120,30,0xc1f4d4,2);
  cena.environment=pm.fromScene(amb,0.012,1,3000).texture;

  // forma: y invertido antes de extrudar (o SVG cresce para baixo)
  var dados=new THREE.SVGLoader().parse('<svg xmlns="http://www.w3.org/2000/svg"><path d="'+D+'"/></svg>');
  var grupo=new THREE.Group();
  var mat=new THREE.MeshPhysicalMaterial({color:0xb7d9c9,metalness:1,roughness:0.16,clearcoat:1,clearcoatRoughness:0.08,envMapIntensity:1.25});
  dados.paths.forEach(function(path){
    THREE.SVGLoader.createShapes(path).forEach(function(s){
      var pts=s.getPoints(32).map(function(v){return new THREE.Vector2(v.x,-v.y);});
      var forma=new THREE.Shape(pts);
      s.holes.forEach(function(h){forma.holes.push(new THREE.Path(h.getPoints(32).map(function(v){return new THREE.Vector2(v.x,-v.y);})));});
      var g=new THREE.ExtrudeGeometry(forma,{depth:22,bevelEnabled:true,bevelThickness:3,bevelSize:2.4,bevelSegments:6,curveSegments:32});
      grupo.add(new THREE.Mesh(g,mat));
    });
  });
  var bb=new THREE.Box3().setFromObject(grupo),c=bb.getCenter(new THREE.Vector3());
  grupo.children.forEach(function(m){m.geometry.translate(-c.x,-c.y,-c.z);});
  var pivo=new THREE.Group();pivo.add(grupo);pivo.rotation.x=-0.12;cena.add(pivo);
  var luz=new THREE.DirectionalLight(0xffffff,0.35);luz.position.set(200,300,400);cena.add(luz);
  

  caixa.appendChild(renderer.domElement);
  caixa.classList.add('vivo');

  function medir(){var w=caixa.clientWidth||200;renderer.setSize(w,w,false);camera.aspect=1;camera.updateProjectionMatrix();}
  medir();
  if(window.ResizeObserver)new ResizeObserver(medir).observe(caixa);else window.addEventListener('resize',medir);

  // giro: automático + arraste com inércia
  var parado=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var vel=parado?0:0.006,auto=vel,arr=false,ux=0,uy=0,vx=0,inclina=-0.12;
  var cv=renderer.domElement;
  cv.addEventListener('pointerdown',function(e){arr=true;ux=e.clientX;uy=e.clientY;vx=0;try{cv.setPointerCapture(e.pointerId);}catch(_){}caixa.classList.add('girando');});
  cv.addEventListener('pointermove',function(e){
    if(!arr)return;
    var dx=e.clientX-ux,dy=e.clientY-uy;ux=e.clientX;uy=e.clientY;
    vx=dx*0.01;pivo.rotation.y+=vx;
    inclina=Math.max(-0.6,Math.min(0.6,inclina+dy*0.006));
  });
  function solta(){arr=false;caixa.classList.remove('girando');}
  cv.addEventListener('pointerup',solta);cv.addEventListener('pointercancel',solta);
  cv.addEventListener('keydown',function(e){if(e.key==='ArrowLeft'){vx=-0.08;}if(e.key==='ArrowRight'){vx=0.08;}});
  cv.tabIndex=0;cv.setAttribute('role','img');cv.setAttribute('aria-label','T da Tivio em 3D');

  var visivel=true;
  if(window.IntersectionObserver)new IntersectionObserver(function(es){visivel=es[0].isIntersecting;}).observe(caixa);
  (function quadro(){
    requestAnimationFrame(quadro);
    if(!visivel)return;
    if(!arr){vx*=0.95;pivo.rotation.y+=vx+(Math.abs(vx)<0.002?auto:0);pivo.rotation.x+=(inclina*0.98-pivo.rotation.x)*0.08;inclina+=(-0.12-inclina)*0.02;}
    else pivo.rotation.x+=(inclina-pivo.rotation.x)*0.2;
    renderer.render(cena,camera);
  })();
})();
