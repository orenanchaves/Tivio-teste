# -*- coding: utf-8 -*-
"""
patch_etf.py
------------
Prepara o dashboard_etf.html para ser alimentado pelo Databricks, aplicando
3 edicoes cirurgicas (nao reescreve o design system):

  1) da id aos KPIs "nº de ETFs" e "PL da classe" (aba Visao Geral)
  2) da id ao <tbody> da tabela de Gestoras (aba Peers & Gestoras)
  3) injeta, antes de </body>, o bloco:
        const ETFS_DATA = [];
     + a extensao JS que preenche os KPIs e reconstroi a tabela de gestoras
       a partir do ETFS_DATA (que o atualizar_etf.py substitui pelos dados
       reais do banco).

Roda uma vez sobre o TEMPLATE (e opcionalmente sobre o output ja gerado):
    python patch_etf.py

Se algum trecho ja estiver com id/injetado, o script avisa e nao duplica.
"""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent

ALVOS = [
    BASE / "templates" / "dashboard_etf.html",
    BASE / "outputs" / "dashboard_etf.html",
]

# ---------------------------------------------------------------------------
# Patch 1 · KPI numero de ETFs
# ---------------------------------------------------------------------------
KPI_N_DE = ('<div class="kpi-card"><div class="kpi-num">175</div>'
            '<div class="kpi-lbl">ETFs LISTADOS B3</div>'
            '<div class="kpi-sub">60+ lançados só em 2025</div></div>')
KPI_N_PARA = ('<div class="kpi-card"><div class="kpi-num" id="etf-kpi-n">175</div>'
              '<div class="kpi-lbl">ETFs LISTADOS B3</div>'
              '<div class="kpi-sub" id="etf-kpi-n-sub">60+ lançados só em 2025</div></div>')

# ---------------------------------------------------------------------------
# Patch 2 · KPI PL da classe
# ---------------------------------------------------------------------------
KPI_PL_DE = ('<div class="kpi-card"><div class="kpi-num">R$ 91 Bi</div>'
             '<div class="kpi-lbl">PL DA CLASSE</div>'
             '<div class="kpi-sub">+68% em 2025</div></div>')
KPI_PL_PARA = ('<div class="kpi-card"><div class="kpi-num" id="etf-kpi-pl">R$ 91 Bi</div>'
               '<div class="kpi-lbl">PL DA CLASSE</div>'
               '<div class="kpi-sub" id="etf-kpi-pl-sub">+68% em 2025</div></div>')

# ---------------------------------------------------------------------------
# Patch 3 · id no <tbody> da tabela de Gestoras (primeiro tbody apos "GESTORA")
# ---------------------------------------------------------------------------
TBODY_PAT = re.compile(r'(GESTORA.*?</thead>\s*)<tbody>', re.DOTALL)

# ---------------------------------------------------------------------------
# Patch 4 · bloco ETFS_DATA + extensao JS (injeta antes de </body>)
# ---------------------------------------------------------------------------
ETF_SCRIPT = r'''<script>
/* ====== ETF · dados do Databricks (injetado pelo atualizar_etf.py) ====== */
const ETFS_DATA = [];

/* ====== ETF · extensao: preenche KPIs + tabela de gestoras ====== */
(function(){
  const FD = (typeof ETFS_DATA !== 'undefined') ? ETFS_DATA : [];
  if(!FD.length) return; // sem dados reais, mantem os numeros manuais

  function moneyBi(v){ return 'R$ ' + (v/1e9).toLocaleString('pt-BR',{minimumFractionDigits:1,maximumFractionDigits:1}) + ' Bi'; }
  function esc(s){ return (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

  /* ---- agrega por gestora ---- */
  const g = {};
  FD.forEach(e=>{
    const k = e.gestora || 'N/D';
    g[k] = g[k] || {gestora:k, n:0, pl:0, _feePl:0, _plFee:0, cats:{}};
    g[k].n++;
    if(e.pl){ g[k].pl += e.pl; if(e.fee!=null){ g[k]._feePl += e.fee*e.pl; g[k]._plFee += e.pl; } }
    if(e.categoria){ g[k].cats[e.categoria] = (g[k].cats[e.categoria]||0) + (e.pl||0); }
  });
  const gestoras = Object.values(g).map(x=>({
    gestora:x.gestora, n:x.n, pl:x.pl,
    fee: x._plFee ? (x._feePl/x._plFee) : null,
    catDom: (Object.entries(x.cats).sort((a,b)=>b[1]-a[1])[0]||['—'])[0]
  })).sort((a,b)=>b.pl-a.pl);

  const nEtfs = FD.length;
  const plTotal = FD.reduce((s,e)=>s+(e.pl||0),0);

  /* ---- KPIs ---- */
  const kN  = document.getElementById('etf-kpi-n');
  const kPL = document.getElementById('etf-kpi-pl');
  if(kN)  kN.textContent  = String(nEtfs);
  if(kPL) kPL.textContent = moneyBi(plTotal);
  const kNsub = document.getElementById('etf-kpi-n-sub');
  const kPLsub= document.getElementById('etf-kpi-pl-sub');
  if(kNsub)  kNsub.textContent  = gestoras.length + ' emissores';
  if(kPLsub) kPLsub.textContent = 'soma capitalização B3';

  /* ---- tabela de gestoras ---- */
  const tb = document.getElementById('etf-gestoras-body');
  if(tb){
    tb.innerHTML = gestoras.map((x,i)=>{
      const medal = i===0?'🥇':i===1?'🥈':i===2?'🥉':String(i+1);
      const fee = x.fee!=null ? x.fee.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'%' : '—';
      return '<tr>'+
        '<td class="rank">'+medal+'</td>'+
        '<td class="fnome">'+esc(x.gestora)+'</td>'+
        '<td class="num">'+x.n+'</td>'+
        '<td class="num muted">—</td>'+
        '<td class="num">'+(x.pl/1e9).toLocaleString('pt-BR',{minimumFractionDigits:1,maximumFractionDigits:1})+'</td>'+
        '<td>'+esc(x.catDom)+'</td>'+
        '<td class="num">'+fee+'</td>'+
        '<td class="muted">B3</td>'+
      '</tr>';
    }).join('');
  }

  console.log('[etf] '+nEtfs+' ETFs · '+gestoras.length+' gestoras · PL '+moneyBi(plTotal));
})();
</script>
'''


def aplicar(caminho: Path) -> None:
    if not caminho.exists():
        print(f"[skip] nao encontrado: {caminho}")
        return

    html = caminho.read_text(encoding="utf-8")
    mudou = 0

    # Patch 1
    if 'id="etf-kpi-n"' in html:
        print(f"  [ok] KPI nº ETFs ja tinha id")
    elif KPI_N_DE in html:
        html = html.replace(KPI_N_DE, KPI_N_PARA, 1); mudou += 1
        print(f"  [+] KPI nº ETFs marcado")
    else:
        print(f"  [!] KPI nº ETFs nao encontrado (verifique o texto)")

    # Patch 2
    if 'id="etf-kpi-pl"' in html:
        print(f"  [ok] KPI PL ja tinha id")
    elif KPI_PL_DE in html:
        html = html.replace(KPI_PL_DE, KPI_PL_PARA, 1); mudou += 1
        print(f"  [+] KPI PL marcado")
    else:
        print(f"  [!] KPI PL nao encontrado")

    # Patch 3
    if 'id="etf-gestoras-body"' in html:
        print(f"  [ok] tbody de gestoras ja tinha id")
    else:
        html, n = TBODY_PAT.subn(r'\1<tbody id="etf-gestoras-body">', html, count=1)
        if n:
            mudou += 1
            print(f"  [+] tbody de gestoras marcado")
        else:
            print(f"  [!] tbody de gestoras nao encontrado")

    # Patch 4
    if 'const ETFS_DATA' in html:
        print(f"  [ok] ETFS_DATA + extensao ja injetados")
    elif '</body>' in html:
        html = html.replace('</body>', ETF_SCRIPT + '</body>', 1); mudou += 1
        print(f"  [+] ETFS_DATA + extensao injetados antes de </body>")
    else:
        print(f"  [!] </body> nao encontrado — nada injetado")

    if mudou:
        caminho.write_text(html, encoding="utf-8")
        print(f"[ok] {caminho.name}: {mudou} patch(es) aplicados\n")
    else:
        print(f"[ok] {caminho.name}: nada a fazer (ja estava pronto)\n")


if __name__ == "__main__":
    for arq in ALVOS:
        print(f">>> {arq}")
        aplicar(arq)
    print("Concluido. Rode 'python atualizar_etf.py' para preencher com dados reais.")
