from pathlib import Path
import re

BASE = Path(__file__).parent
ARQUIVO = BASE / "templates" / "dashboard_etf.html"

if not ARQUIVO.exists():
    raise SystemExit(f'[ERRO] Nao encontrei {ARQUIVO.name} na mesma pasta deste script.')

html = ARQUIVO.read_text(encoding='utf-8')
backup = ARQUIVO.with_suffix('.backup.html')
if not backup.exists():
    backup.write_text(html, encoding='utf-8')

# IDs e containers que permitem ao JS substituir os valores manuais.
replacements = {
    r'(<a class="dash-tab active" href="dashboard_etf\.html">Análise · ETF <span class="dash-tab-badge")>[^<]*(</span>)': r'\1 id="etf-nav-badge">0\2',
    r'<div class="top1-strip-lbl">[^<]*CONTEXTO GLOBAL · ETF ATIVO</div>': '<div class="top1-strip-lbl">🌍 CONTEXTO GLOBAL · ETF ATIVO</div>',
    r'<div class="diverging-bars">\s*(?=<div class="div-bar-row">)': '<div class="diverging-bars">',
}
for pattern, replacement in replacements.items():
    html = re.sub(pattern, replacement, html, count=1, flags=re.S)

# Marca blocos atualmente existentes para atualizacao dinamica sem redesenhar o dashboard.
html = html.replace('<div class="diverging-bars">', '<div class="diverging-bars" id="etf-heatmap-gestoras">', 1)
html = html.replace('<div class="hl-wrap">\n        <div class="hl-block"><div class="hl-lbl">🥇 TOP 3 EMISSORES</div>', '<div class="hl-wrap" id="etf-concentracao">\n        <div class="hl-block"><div class="hl-lbl">🥇 TOP 3 EMISSORES</div>', 1)

PATCH = r'''
<script id="etf-auto-complemento">
/* ETF: automacao complementar baseada somente nos campos existentes em ETFS_DATA. */
(function(){
  const D = (typeof ETFS_DATA !== 'undefined' && Array.isArray(ETFS_DATA)) ? ETFS_DATA : [];
  if(!D.length) return;

  const esc = s => String(s == null ? '' : s).replace(/[&<>\"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));
  const fmtBi = v => 'R$ ' + (Number(v || 0) / 1e9).toLocaleString('pt-BR', {minimumFractionDigits:1, maximumFractionDigits:1}) + ' Bi';
  const hojeRef = D.map(x => x.data_referencia).filter(Boolean).sort().at(-1) || '';
  const totalPL = D.reduce((s,x) => s + Number(x.pl || 0), 0);

  // Badge da navegacao: elimina a divergencia entre o menu e o universo carregado.
  const navBadge = document.getElementById('etf-nav-badge');
  if(navBadge) navBadge.textContent = D.length.toLocaleString('pt-BR');

  // Agregacao unica por gestora.
  const mapa = new Map();
  D.forEach(x => {
    const nome = x.gestora || 'N/D';
    if(!mapa.has(nome)) mapa.set(nome, {nome, n:0, pl:0, novos:0, cats:new Map()});
    const g = mapa.get(nome);
    g.n += 1;
    g.pl += Number(x.pl || 0);
    g.novos += Number(x.lancamento_12m || 0);
    const cat = x.categoria || 'N/D';
    g.cats.set(cat, (g.cats.get(cat) || 0) + Number(x.pl || 0));
  });
  const gestoras = [...mapa.values()].sort((a,b) => b.pl-a.pl);

  // Heatmap: lancamentos reais dos ultimos 12 meses por gestora.
  const heat = document.getElementById('etf-heatmap-gestoras');
  if(heat){
    const lista = gestoras.filter(x => x.novos > 0).sort((a,b) => b.novos-a.novos || b.pl-a.pl);
    const max = Math.max(1, ...lista.map(x => x.novos));
    heat.innerHTML = lista.map(x => {
      const w = Math.max(3, x.novos / max * 100);
      return `<div class="div-bar-row"><div class="div-bar-chip"><span class="chip g">${esc(x.nome)}</span></div><div class="div-bar-chart"><div class="div-bar-half left"></div><div class="div-bar-half right"><div class="div-bar-fill" style="width:${w.toFixed(1)}%;background:linear-gradient(90deg,var(--tivio),var(--tv-verde-escuro))"></div></div></div><div class="div-bar-value" style="color:var(--tivio)">${x.novos}</div></div>`;
    }).join('');
  }

  // Concentracao calculada a partir do PL agregado da base atual.
  const conc = document.getElementById('etf-concentracao');
  if(conc && gestoras.length){
    const top3 = gestoras.slice(0,3);
    const top3PL = top3.reduce((s,x) => s+x.pl, 0);
    const pct = totalPL ? top3PL/totalPL*100 : 0;
    const abaixo1 = gestoras.filter(x => x.pl < 1e9).length;
    const novosPlayers = gestoras.filter(x => x.novos > 0).length;
    conc.innerHTML = `
      <div class="hl-block"><div class="hl-lbl">🥇 TOP 3 EMISSORES</div><div class="hl-fund">${top3.map(x=>esc(x.nome)).join(' + ')}</div><div class="hl-val" style="color:var(--tivio)">${fmtBi(top3PL)} · ${pct.toLocaleString('pt-BR',{maximumFractionDigits:1})}% do PL</div></div>
      <div class="hl-block"><div class="hl-lbl">📉 CAUDA LONGA</div><div class="hl-fund">Gestoras com PL inferior a R$ 1 Bi</div><div class="hl-val">${abaixo1} emissores</div></div>
      <div class="hl-block"><div class="hl-lbl">🆕 EMISSORES COM LANÇAMENTOS 12m</div><div class="hl-fund">Com pelo menos um ETF marcado como lançamento</div><div class="hl-val" style="color:var(--tivio)">${novosPlayers} players</div></div>`;
  }

  // Auditoria no console. Mostra por que certos blocos nao podem ser automatizados ainda.
  const cobertura = {
    linhas: D.length,
    referencia: hojeRef,
    comPL: D.filter(x => x.pl != null).length,
    comFee: D.filter(x => x.fee != null).length,
    comCaptacao12m: D.filter(x => x.cap12 != null).length,
    comCNPJ: D.filter(x => x.cnpj != null).length,
    datasInicioInvalidas: D.filter(x => String(x.data_inicio || '').startsWith('9999-')).length
  };
  console.table(cobertura);
})();
</script>
'''

if 'id="etf-auto-complemento"' in html:
    html = re.sub(r'\s*<script id="etf-auto-complemento">.*?</script>\s*', '\n' + PATCH + '\n', html, count=1, flags=re.S)
else:
    html = html.replace('</body>', PATCH + '\n</body>')

ARQUIVO.write_text(html, encoding='utf-8')
print(f'[OK] Atualizado: {ARQUIVO}')
print(f'[OK] Backup: {backup}')
print('[INFO] Abra o HTML e pressione F12 > Console para ver a auditoria de cobertura.')
