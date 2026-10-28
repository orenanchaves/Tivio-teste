# -*- coding: utf-8 -*-
"""
automatizar_dashboard_etf_fase2.py

Fase 2 do dashboard ETF (Tivio).
Adiciona blocos automatizados de LANCAMENTOS, usando apenas campos ja
presentes em ETFS_DATA (data_inicio, categoria_macro, gestora, pl).

Cria na aba "Visao Geral":
  - Lancamentos por ano (barras)
  - Lancamentos por categoria_macro (barras)
  - KPIs de PL por macro-categoria (top)

Trata data_inicio == "9999-12-31" como "sem data" (nao entra no grafico por ano).

Idempotente: rodar de novo atualiza o bloco, sem duplicar.
"""

from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
ARQUIVO = BASE / "templates" / "dashboard_etf.html"

if not ARQUIVO.exists():
    raise SystemExit(f"[ERRO] Nao encontrei: {ARQUIVO}")

html = ARQUIVO.read_text(encoding="utf-8")
backup = ARQUIVO.with_name("dashboard_etf.pre_fase2.html")
if not backup.exists():
    backup.write_text(html, encoding="utf-8")

# --------------------------------------------------------------------------
# 1) Painel HTML da Fase 2 (inserido logo apos o painel da Fase 1)
# --------------------------------------------------------------------------
PAINEL = '''
  <div class="panel" id="etf-fase2-panel">
    <div class="panel-head"><h3>Lancamentos &amp; evolucao da classe</h3><span class="pill" id="etf-fase2-ref">Databricks</span></div>
    <div class="kpi-row" id="etf-macro-kpis"></div>
    <div class="row two-col">
      <div class="panel panel-lg">
        <div class="panel-head"><h3>Lancamentos por ano</h3><span class="pill" id="etf-ano-pill">todos</span></div>
        <div class="diverging-bars" id="etf-lancamentos-ano"></div>
        <div class="panel-note" id="etf-sem-data-note"></div>
      </div>
      <div class="panel panel-sm">
        <div class="panel-head"><h3>Lancamentos por categoria</h3><span class="pill">12m</span></div>
        <div class="diverging-bars" id="etf-lancamentos-cat"></div>
      </div>
    </div>
  </div>
'''

if 'id="etf-fase2-panel"' not in html:
    anchor = '<div class="panel" id="etf-fase1-panel">'
    pos = html.find(anchor)
    if pos < 0:
        raise SystemExit(
            "[ERRO] Nao encontrei o painel da Fase 1 (etf-fase1-panel). "
            "Rode antes: python automatizar_dashboard_etf_fase1.py"
        )
    # insere o painel da Fase 2 imediatamente ANTES do painel da Fase 1
    html = html[:pos] + PAINEL + html[pos:]

# --------------------------------------------------------------------------
# 2) Script JS da Fase 2
# --------------------------------------------------------------------------
JS = r'''<script id="etf-fase2-auto">
(function(){
  const D = (typeof ETFS_DATA !== 'undefined' && Array.isArray(ETFS_DATA)) ? ETFS_DATA : [];
  if(!D.length) return;

  const esc = s => String(s == null ? '' : s).replace(/[&<>\"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));
  const n = v => Number(v || 0);
  const bi = v => (n(v)/1e9).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
  const ref = D.map(x=>x.data_referencia).filter(Boolean).sort().at(-1) || '';
  const totalPL = D.reduce((s,x)=>s+n(x.pl),0);

  const refPill = document.getElementById('etf-fase2-ref');
  if(refPill && ref) refPill.textContent = ref.slice(8,10)+'/'+ref.slice(5,7)+'/'+ref.slice(0,4);

  // ---- KPIs de PL por categoria_macro (top 5) ----
  const macroMap = new Map();
  D.forEach(x=>{
    const k = x.categoria_macro || x.categoria || 'Outros';
    macroMap.set(k, (macroMap.get(k)||0) + n(x.pl));
  });
  const macro = [...macroMap.entries()].map(([nome,pl])=>({nome,pl})).sort((a,b)=>b.pl-a.pl);
  const kpis = document.getElementById('etf-macro-kpis');
  if(kpis){
    kpis.innerHTML = macro.slice(0,5).map(x=>{
      const share = totalPL ? (x.pl/totalPL*100) : 0;
      return `<div class="kpi-card"><div class="kpi-num">R$ ${bi(x.pl)} Bi</div><div class="kpi-lbl">${esc(x.nome).toUpperCase()}</div><div class="kpi-sub">${share.toLocaleString('pt-BR',{maximumFractionDigits:1})}% do PL</div></div>`;
    }).join('');
  }

  // ---- Lancamentos por ANO (data_inicio, ignorando 9999) ----
  const anoMap = new Map();
  let semData = 0;
  D.forEach(x=>{
    const di = String(x.data_inicio || '');
    const ano = di.slice(0,4);
    if(!ano || ano === '9999'){ semData++; return; }
    anoMap.set(ano, (anoMap.get(ano)||0) + 1);
  });
  const anos = [...anoMap.entries()].map(([ano,q])=>({ano,q})).sort((a,b)=>a.ano.localeCompare(b.ano));
  const elAno = document.getElementById('etf-lancamentos-ano');
  if(elAno){
    const max = Math.max(1,...anos.map(x=>x.q));
    elAno.innerHTML = anos.map(x=>{
      const w = Math.max(3, x.q/max*100);
      return `<div class="div-bar-row"><div class="div-bar-chip"><span class="chip g">${esc(x.ano)}</span></div><div class="div-bar-chart"><div class="div-bar-half left"></div><div class="div-bar-half right"><div class="div-bar-fill" style="width:${w.toFixed(1)}%;background:linear-gradient(90deg,var(--tivio),var(--tv-verde-escuro))"></div></div></div><div class="div-bar-value" style="color:var(--tivio)">${x.q}</div></div>`;
    }).join('');
  }
  const anoPill = document.getElementById('etf-ano-pill');
  if(anoPill && anos.length) anoPill.textContent = anos[0].ano + '-' + anos[anos.length-1].ano;
  const semNote = document.getElementById('etf-sem-data-note');
  if(semNote) semNote.innerHTML = semData ? `<b>${semData}</b> ETFs sem data de inicio valida (9999) ficaram fora do grafico por ano.` : '';

  // ---- Lancamentos por CATEGORIA (lancamento_12m) ----
  const catMap = new Map();
  D.forEach(x=>{
    if(n(x.lancamento_12m) <= 0) return;
    const k = x.categoria_macro || x.categoria || 'Outros';
    catMap.set(k, (catMap.get(k)||0) + 1);
  });
  const cats = [...catMap.entries()].map(([nome,q])=>({nome,q})).sort((a,b)=>b.q-a.q);
  const elCat = document.getElementById('etf-lancamentos-cat');
  if(elCat){
    const max = Math.max(1,...cats.map(x=>x.q));
    elCat.innerHTML = cats.map(x=>{
      const w = Math.max(3, x.q/max*100);
      return `<div class="div-bar-row"><div class="div-bar-chip"><span class="chip g">${esc(x.nome)}</span></div><div class="div-bar-chart"><div class="div-bar-half left"></div><div class="div-bar-half right"><div class="div-bar-fill" style="width:${w.toFixed(1)}%;background:linear-gradient(90deg,var(--tivio),var(--tv-verde-escuro))"></div></div></div><div class="div-bar-value" style="color:var(--tivio)">${x.q}</div></div>`;
    }).join('');
  }

  console.log('[ETF Fase 2]', {anos:anos.length, semData, categorias:cats.length, macro:macro.length});
})();
</script>'''

# remove versao anterior (idempotente) e reinsere antes de </body>
html = re.sub(r'\s*<script id="etf-fase2-auto">.*?</script>\s*', '\n', html, flags=re.S)
html = html.replace('</body>', JS + '\n</body>')

ARQUIVO.write_text(html, encoding="utf-8")
print(f"[OK] Fase 2 aplicada no template: {ARQUIVO}")
print(f"[OK] Backup pre-Fase 2: {backup}")
print("[PROXIMO] Rode: python atualizar_etf.py")
