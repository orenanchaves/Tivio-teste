# -*- coding: utf-8 -*-
"""Portal de conferência: todos os dados da edição num HTML só.

Para bater o que cada material puxou antes de publicar. Sai em
saida/_Historico/AAAA-MM/Interno/Edição completa/portal_dados_AAAA-MM.html (e Interno/Portal de dados.html, no fim da rodada, junto da
conferencia_AAAA-MM.xlsx. Lê o que a rodada já calculou; não calcula nada novo:

  · cabeçalho: data base, de onde vieram os dados (API ou planilha), resumo
  · alertas: erros, avisos, divergências e dados faltantes
  · fundos: um bloco por fundo com tudo que o ContextoFundo entrega (cotas,
    rentabilidade por período, PL, taxas, carteira, comentário)
  · materiais: cada troca feita nos HTMLs (antes e depois)
  · decks: slide a slide, cada número ou data, trocado ou igual ao modelo
    (exporters/decks.py::REGISTRO). "Igual ao modelo" é onde o mês passado
    costuma ficar.
  · arquivos gerados
"""
import datetime as dt
import html
import os

from calculators import formatos as fmt

PERIODOS = [('mes', 'Mês'), ('ano', 'Ano'), ('12m', '12M'), ('24m', '24M'), ('36m', '36M'), ('inicio', 'Início')]

CSS = """
:root{--bg:#0A0F14;--sup:#12181F;--sup2:#1B2A36;--fg:#E6EDF1;--fg2:#B8C4CC;--fg3:#8A99A3;--verde:#C1F4D4;--linha:rgba(255,255,255,.10);--alerta:#F4C27A;--erro:#F49A9A}
@media (prefers-color-scheme:light){:root{--bg:#FFFFFF;--sup:#EEF2F5;--sup2:#DDE4E9;--fg:#0A0F14;--fg2:#3C4A60;--fg3:#637881;--verde:#337F51;--linha:rgba(10,15,20,.12);--alerta:#9A6200;--erro:#B3261E}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 'Versos',system-ui,-apple-system,'Segoe UI',sans-serif}
.topo{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--linha);padding:12px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.topo b{font-size:17px}.topo input{flex:1 1 220px;min-width:0;padding:8px 12px;border-radius:999px;border:1px solid var(--linha);background:var(--sup);color:var(--fg);font:inherit}
.topo nav{display:flex;flex-wrap:wrap;gap:6px}.topo nav a{padding:5px 12px;border-radius:999px;background:var(--sup);color:var(--fg);text-decoration:none;font-size:13px}
main{max-width:1280px;margin:0 auto;padding:20px 16px 60px}h1{font-weight:300;font-size:30px;margin:4px 0 6px}h1 strong{font-weight:700}
h2{font-size:21px;margin:34px 0 10px;scroll-margin-top:70px}h3{font-size:17px;margin:0}.sub{color:var(--fg2);margin:0 0 14px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}.card{background:var(--sup);border:1px solid var(--linha);border-radius:12px;padding:12px 14px}
.card span{display:block;font-size:12px;color:var(--fg3)}.card b{font-size:18px}
.fundo{background:var(--sup);border:1px solid var(--linha);border-radius:14px;padding:16px;margin:12px 0}
.fundo header{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:baseline;margin-bottom:10px}.fundo header code{color:var(--fg3)}
.selo{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;background:var(--sup2);color:var(--fg2)}
.selo.ok{color:var(--verde)}.selo.al{color:var(--alerta)}.selo.er{color:var(--erro)}
.dl{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:6px 18px;margin:10px 0}.dl div{border-bottom:1px solid var(--linha);padding:4px 0}
.dl span{color:var(--fg3);font-size:12px;display:block}
.tab{overflow-x:auto;margin:8px 0}table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--linha);vertical-align:top}th{color:var(--fg3);font-weight:600;white-space:nowrap}
td.n{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}tr.igual td{color:var(--alerta)}tr.trocado td.dep{color:var(--verde)}
details{margin:6px 0}summary{cursor:pointer;color:var(--fg2)}.coment{white-space:pre-wrap;color:var(--fg2);font-size:13.5px;max-height:240px;overflow:auto;background:var(--sup2);padding:10px;border-radius:8px}
.filtros{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px}.filtros button{padding:5px 12px;border-radius:999px;border:1px solid var(--linha);background:var(--sup);color:var(--fg);font:inherit;font-size:13px;cursor:pointer}
.filtros button[aria-pressed=true]{background:var(--verde);color:#0A0F14;border-color:var(--verde)}
.oculto,.oculto-m{display:none!important}
.lg{height:30px;max-width:220px;object-fit:contain}.lg-cla{display:none}
@media (prefers-color-scheme:light){.lg-esc{display:none}.lg-cla{display:inline}}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin:12px 0}
.kpi{background:var(--sup2);border-radius:10px;padding:10px 12px}.kpi span{display:block;font-size:12px;color:var(--fg3)}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}.kpi em{display:block;font-style:normal;font-size:12px;color:var(--fg2)}
.kpi.al b{color:var(--alerta)}.kpi.ok b{color:var(--verde)}.topo select{padding:8px 12px;border-radius:999px;border:1px solid var(--linha);background:var(--sup);color:var(--fg);font:inherit;max-width:100%}
@media (max-width:640px){h1{font-size:24px}.fundo{padding:12px}}
"""

JS = """
(function(){
var q=document.getElementById('busca');
function filtra(){var t=q.value.trim().toLowerCase();
 document.querySelectorAll('[data-busca]').forEach(function(el){el.classList.toggle('oculto',t&&el.getAttribute('data-busca').indexOf(t)<0)})}
q.addEventListener('input',filtra);
var m=document.getElementById('material');
m.addEventListener('change',function(){var v=m.value;
 document.querySelectorAll('[data-mat]').forEach(function(el){var ok=!v||el.getAttribute('data-mat')===v;el.classList.toggle('oculto-m',!ok);if(ok&&v&&el.tagName==='DETAILS')el.open=true});
 document.querySelectorAll('.so-mat').forEach(function(el){el.classList.toggle('oculto-m',!!v)});
 if(v){var a=document.querySelector('[data-mat]:not(.oculto-m)');if(a)a.scrollIntoView({block:'start'})}});
document.querySelectorAll('.filtros').forEach(function(f){var alvo=document.getElementById(f.dataset.alvo);
 f.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){
  f.querySelectorAll('button').forEach(function(x){x.setAttribute('aria-pressed',x===b)});
  var e=b.dataset.estado;alvo.querySelectorAll('tr[data-estado]').forEach(function(tr){tr.classList.toggle('oculto',e&&tr.dataset.estado!==e)})})})});
})();
"""


def _e(x):
    return html.escape('' if x is None else str(x))


def _data(d):
    if d is None:
        return '−'
    try:
        return d.strftime('%d/%m/%Y')
    except Exception:
        return _e(d)


def _pct(v, casas=2):
    if v is None:
        return '−'
    try:
        return fmt.num(float(v) * 100, casas) + '%'
    except Exception:
        return _e(v)


def _tabela(cab, linhas, classes=None, attrs=None):
    h = '<div class="tab"><table><tr>' + ''.join(f'<th>{_e(c)}</th>' for c in cab) + '</tr>'
    for i, ln in enumerate(linhas):
        a = (attrs[i] if attrs else '')
        h += f'<tr{a}>' + ''.join(
            f'<td{(" class=" + chr(34) + classes[j] + chr(34)) if classes and classes[j] else ""}>{c}</td>'
            for j, c in enumerate(ln)) + '</tr>'
    return h + '</table></div>'


def _try(f, padrao=None):
    try:
        return f()
    except Exception:
        return padrao


_LOGOS = None


def _logo(ctx):
    """Logo horizontal do fundo (assets/logos), branco no escuro e preto no claro."""
    global _LOGOS
    import base64
    try:
        from renderers.logos import _indice, _achar
        if _LOGOS is None:
            _LOGOS = _indice()
        nome = ctx.f.cfg.get('logo')
        if not nome:
            return ''
        out = ''
        for cor, cls in (('branco', 'lg-esc'), ('preto', 'lg-cla')):
            arq = _achar(_LOGOS, nome, cor)
            if arq:
                b64 = base64.b64encode(open(arq, 'rb').read()).decode()
                out += f'<img class="lg {cls}" src="data:image/svg+xml;base64,{b64}" alt="{_e(ctx.nome)}">'
        return out
    except Exception:
        return ''


def _kpis(ctx, ultima, edicao):
    def k(rot, val, cls=''):
        return f'<div class="kpi {cls}"><span>{_e(rot)}</span><b>{val}</b></div>'
    b = ctx.benchmark
    itens = []
    for p, rot in (('mes', 'Mês'), ('ano', 'Ano'), ('12m', '12 meses'), ('inicio', 'Desde o início')):
        v, pc = ctx.valor(p, 'fundo'), ctx.valor(p, 'pct')
        extra = f'<em>{_pct(pc, 0 if pc and pc > 0.5 else 2)} do {_e(b)}</em>' if pc is not None and not ctx.f.retorno_absoluto else ''
        itens.append(k(rot, _pct(v) + extra))
    itens += [k('PL', _e(fmt.brl_curto(ctx.pl) if ctx.pl else '−')), k('Carrego', _e(ctx.carrego_fmt)), k('Duration', _e(ctx.duration_fmt)),
              k('Crédito', _e(ctx.credito_fmt)),
              k('Última cota', _data(ultima), 'al' if ultima is not None and ultima.date() < edicao.db.date() else 'ok')]
    return '<div class="kpis">' + ''.join(itens) + '</div>'


def _bloco_fundo(ctx, edicao, avisos_fundo, div_fundo, falt_fundo):
    f = ctx.f
    serie = _try(ctx.serie_diaria, []) or []
    primeira = serie[0][0] if serie else None
    ultima = serie[-1][0] if serie else None
    db = edicao.db
    atraso_cota = (ultima is not None and ultima.date() < db.date() if hasattr(db, 'date') else False)
    cart = ctx.cart or {}
    cart_data = cart.get('data') if cart else None

    selos = []
    if not ctx.tem_dados:
        selos.append('<span class="selo er">sem cotas</span>')
    elif atraso_cota:
        selos.append(f'<span class="selo al">última cota {_data(ultima)}, antes da data base</span>')
    else:
        selos.append('<span class="selo ok">cotas até a data base</span>')
    if div_fundo:
        selos.append(f'<span class="selo al">{len(div_fundo)} divergência(s)</span>')
    if falt_fundo:
        selos.append(f'<span class="selo al">{len(falt_fundo)} faltante(s)</span>')
    if avisos_fundo:
        selos.append(f'<span class="selo">{len(avisos_fundo)} aviso(s)</span>')

    dados = [
        ('Carteira (DePara)', _e(f.carteira)), ('CNPJ', _e(getattr(f, 'cnpj', ''))),
        ('Benchmark', _e(ctx.benchmark)), ('Data de início', _data(ctx.data_inicio)),
        ('Primeira cota', _data(primeira)), ('Última cota', _data(ultima)),
        ('PL', _e(ctx.pl_fmt)), ('PL médio 12m', _e(ctx.pl_medio_fmt)),
        ('Taxa global', _e(_try(lambda: fmt.taxa(ctx.taxa), ctx.taxa))), ('Performance', _e(ctx.perf)),
        ('Carrego', _e(ctx.carrego_fmt)), ('Duration', _e(ctx.duration_fmt)),
        ('Crédito', _e(ctx.credito_fmt)), ('Data da carteira', _data(cart_data)),
    ]
    h = (f'<section class="fundo" id="f-{_e(ctx.key)}" data-busca="{_e((ctx.nome + " " + ctx.key + " " + (f.carteira or "")).lower())}">'
         f'<header>{_logo(ctx)}<h3>{_e(ctx.nome)}</h3><code>{_e(ctx.key)}</code>{"".join(selos)}</header>'
         + (_kpis(ctx, ultima, edicao) if ctx.tem_dados else '') +
         '<details><summary>Cadastro e datas</summary><div class="dl">' + ''.join(f'<div><span>{k}</span>{v}</div>' for k, v in dados) + '</div></details>')

    if ctx.tem_dados:
        refs = ctx.rent.get('refs') or {}
        linhas = []
        for campo, rot in (('fundo', 'Fundo'), ('bench', ctx.benchmark), ('alfa', 'Alfa'),
                           ('pct', f'% do {ctx.benchmark}'), ('bench_mais', f'{ctx.benchmark}+ a.a.')):
            vals = [ctx.valor(p, campo) for p, _ in PERIODOS]
            if all(v is None for v in vals):
                continue
            linhas.append([rot] + [_pct(v) for v in vals])
        linhas.append(['Desde'] + [_data(refs.get(p)) for p, _ in PERIODOS])
        h += _tabela(['Rentabilidade'] + [r for _, r in PERIODOS], linhas, [''] + ['n'] * 6)

    listas = [('Setores', _try(lambda: ctx.setores, [])), ('Rating', _try(lambda: ctx.rating, [])),
              ('Emissores (top 5)', _try(lambda: ctx.emissores, [])),
              ('HG / HY / Caixa', _try(lambda: ctx.alocacao_hghy, [])),
              ('HG / HY Informativo', _try(lambda: ctx.alocacao_hghy_informativo, [])),
              ('Estratégia', _try(lambda: ctx.estrategia, []))]
    listas = [(t, l) for t, l in listas if l]
    if listas:
        h += '<details><summary>Carteira: ' + ', '.join(t for t, _ in listas) + '</summary><div class="dl">'
        for t, l in listas:
            h += f'<div><span>{t}</span>' + '<br>'.join(f'{_e(x[0])}: {_e(x[1])}' for x in l) + '</div>'
        h += '</div></details>'
    if serie:
        ult = serie[-5:]
        h += ('<details><summary>Últimos pontos do histórico diário (gráfico dos decks)</summary>'
              + _tabela(['Data', 'Fundo acumulado', 'Benchmark acumulado'],
                        [[_data(d), _pct(a), _pct(b)] for d, a, b in ult], ['', 'n', 'n']) + '</details>')
    if ctx.comentario:
        txt = '\n\n'.join(_try(lambda: ctx.comentario_preenchido, ctx.comentario) or [])
        h += f'<details><summary>Comentário do gestor ({len(ctx.comentario)} parágrafos)</summary><div class="coment">{_e(txt)}</div></details>'
    probs = [['divergência', _e(x[2]), _e(x[3])] for x in div_fundo] + \
            [['faltante', _e(x[2]), _e(x[3])] for x in falt_fundo] + \
            [['aviso', _e(a[0]), _e(a[2])] for a in avisos_fundo]
    if probs:
        h += '<details open><summary>O que conferir neste fundo</summary>' + _tabela(['Tipo', 'Onde', 'O quê'], probs) + '</details>'
    return h + '</section>'


def gerar_portal(contextos, conf, log, edicao, cfg, destino):
    from exporters.decks import REGISTRO
    ent = (cfg.get('entradas') or {})
    fonte = str(ent.get('fonte', 'planilha')).lower()
    caiu = any(a[1] == 'api' for a in log.avisos)
    fonte_txt = 'API TLDR' if fonte == 'api' and not caiu else ('Planilha (a API não respondeu)' if fonte == 'api' else 'Planilha')
    agora = dt.datetime.now().strftime('%d/%m/%Y %H:%M')

    com_dados = [c for c in contextos if c.tem_dados]
    atrasados = []
    for c in com_dados:
        s = _try(c.serie_diaria, []) or []
        if s and s[-1][0].date() < edicao.db.date():
            atrasados.append(c)
    deck_igual = [r for r in REGISTRO if r['estado'] == 'igual ao modelo']

    h = ['<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>Portal de dados · {_e(edicao.mes_ano)}</title><style>{CSS}</style></head><body>'
         '<div class="topo"><b>Portal de dados</b><input id="busca" type="search" placeholder="Buscar fundo, deck, campo ou valor">'
         '<select id="material" aria-label="Material"><option value="">Todos os materiais</option>' + ''.join(
             f'<option value="{_e(m)}">{_e(m)}</option>' for m in sorted({str(x[0]) for x in log.mudancas} | {r["deck"] for r in REGISTRO})) + '</select>'
         '<nav><a href="#resumo">Resumo</a><a href="#alertas">Alertas</a><a href="#fundos">Fundos</a>'
         '<a href="#materiais">Materiais</a><a href="#decks">Decks</a><a href="#arquivos">Arquivos</a></nav></div><main>']
    h.append(f'<h1 id="resumo">Edição de <strong>{_e(edicao.mes_ano)}</strong></h1>'
             f'<p class="sub">Data base {_e(edicao.br)} · dados de: {_e(fonte_txt)} · gerado em {agora}. '
             'Tudo aqui é o que a rodada calculou e escreveu nos materiais.</p>')
    cards = [('Fundos com dados', f'{len(com_dados)} de {len(contextos)}'),
             ('Cotas antes da data base', str(len(atrasados))),
             ('Erros', str(len(log.erros))), ('Avisos', str(len(log.avisos))),
             ('Divergências', str(len(conf.divergencias))), ('Dados faltantes', str(len(conf.faltantes))),
             ('Trocas nos materiais', str(len(log.mudancas))),
             ('Números de deck iguais ao modelo', str(len(deck_igual))),
             ('Arquivos gerados', str(len(log.arquivos)))]
    h.append('<div class="cards">' + ''.join(f'<div class="card"><span>{k}</span><b>{v}</b></div>' for k, v in cards) + '</div>')

    # alertas
    h.append('<h2 id="alertas">Alertas</h2>')
    lin = [['erro', _e(x[1]), _e(x[2])] for x in log.erros] + \
          [['divergência', _e(f'{x[1]} · {x[2]}'), _e(x[3])] for x in conf.divergencias] + \
          [['faltante', _e(f'{x[1]} · {x[2]}'), _e(x[3])] for x in conf.faltantes] + \
          [['cota atrasada', _e(c.nome), f'última cota {_data((_try(c.serie_diaria, []) or [[None]])[-1][0])}'] for c in atrasados] + \
          [['aviso', _e(a[1]), _e(a[2])] for a in log.avisos]
    h.append(_tabela(['Tipo', 'Onde', 'O quê'], lin, attrs=[f' data-busca="{_e((" ".join(map(str, x))).lower())}"' for x in lin])
             if lin else '<p class="sub">Nada a conferir.</p>')

    # fundos
    h.append('<h2 id="fundos">Fundos</h2><p class="sub">Um bloco por fundo, na ordem do cadastro.</p>')
    for ctx in contextos:
        av = [a for a in log.avisos if a[1] == ctx.key]
        dv = [x for x in conf.divergencias if x[0] == ctx.key]
        fl = [x for x in conf.faltantes if x[0] == ctx.key]
        h.append(_bloco_fundo(ctx, edicao, av, dv, fl))

    # materiais (HTMLs legados)
    h.append('<h2 id="materiais">Materiais</h2><p class="sub">Cada número trocado nos posts, e-mails e Central.</p>')
    mud = log.mudancas
    h.append(_tabela(['Arquivo', 'Fundo', 'Campo', 'Antes', 'Depois'],
                     [[_e(a), _e(b), _e(c), _e(d), _e(e)] for a, b, c, d, e in mud],
                     attrs=[f' data-mat="{_e(m[0])}" data-busca="{_e(" ".join(map(str, m)).lower())}"' for m in mud])
             if mud else '<p class="sub">Nenhuma troca registrada.</p>')

    # decks
    h.append('<h2 id="decks">Decks</h2><p class="sub">Cada caixa com número ou data, slide a slide. '
             'Em amarelo o que ficou igual ao modelo: é onde o mês passado costuma ficar.</p>')
    decks = []
    for r in REGISTRO:
        if r['deck'] not in decks:
            decks.append(r['deck'])
    for i, nome in enumerate(decks):
        rs = [r for r in REGISTRO if r['deck'] == nome]
        n_ig = sum(r['estado'] == 'igual ao modelo' for r in rs)
        tid = f'dk{i}'
        h.append(f'<details class="fundo" data-mat="{_e(nome)}" data-busca="{_e(nome.lower())}"><summary><b>{_e(nome)}</b> · '
                 f'{len(rs) - n_ig} trocados · {n_ig} iguais ao modelo</summary>'
                 f'<div class="filtros" data-alvo="{tid}"><button type="button" aria-pressed="true" data-estado="">Tudo</button>'
                 '<button type="button" aria-pressed="false" data-estado="igual ao modelo">Iguais ao modelo</button>'
                 '<button type="button" aria-pressed="false" data-estado="trocado">Trocados</button></div><div id="' + tid + '">'
                 + _tabela(['Slide', 'Onde', 'No modelo', 'No deck'],
                           [[str(r['slide']), _e(r['onde']), _e(r['antes']), _e(r['depois'])] for r in rs],
                           ['n', '', '', 'dep'],
                           [f' class="{"igual" if r["estado"] == "igual ao modelo" else "trocado"}" data-estado="{r["estado"]}"' for r in rs])
                 + '</div></details>')
    if not decks:
        h.append('<p class="sub">Nenhum deck nesta rodada.</p>')

    # arquivos
    h.append('<h2 id="arquivos">Arquivos gerados</h2>')
    h.append(_tabela(['Arquivo', 'Formato', 'Tamanho'],
                     [[_e(os.path.relpath(a, os.path.dirname(destino)) if os.path.isabs(str(a)) else a), _e(f), _e(fmt.num((b or 0) / 1024, 0) + ' KB')]
                      for a, f, b in log.arquivos], ['', '', 'n']))
    h.append(f'</main><script>{JS}</script></body></html>')
    os.makedirs(os.path.dirname(destino) or '.', exist_ok=True)
    with open(destino, 'w', encoding='utf-8') as fh:
        fh.write(''.join(h))
    return destino
