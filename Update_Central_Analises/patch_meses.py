# -*- coding: utf-8 -*-
"""
patch_meses.py - Monitor de Novos Fundos - Tivio Capital
--------------------------------------------------------
Torna a barra de periodo DINAMICA e adiciona o SELETOR DE ANO
(Geral / 2026 / 2025 / 2024).

Dois modos:

  escopo = <ano>    -> a barra vira os 12 meses do ano (os meses sem
                       registro ficam apagados/desabilitados)

  escopo = "geral"  -> a barra vira os anos disponiveis (2024, 2025,
                       2026...) e o dashboard abre no "Periodo Completo",
                       somando todos os anos

Substituicoes cirurgicas no HTML ja existente:
  1) <div class="month-filter-bar"> ... </div>   (barra de periodo)
  2) const PERIODO_MODO = "..."                  (mes | ano)
  3) const PERIODO_KEYS = [...]                  (chaves da barra)
  4) const MES_NOMES  = {...}                    (rotulo de cada chave)
  5) const MES_TOTAIS = {...}                    (contagem de cada chave)
  6) let currentMonth = N                        (periodo inicial)
  7) a barra de referencia do topo (tv-refbar)

O seletor de ano navega entre arquivos:
  dashboard_fundos_tivio_geral.html
  dashboard_fundos_tivio_<ano>.html
"""
import re
from datetime import datetime

ABREV = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
         7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}

ARQ_GERAL = "dashboard_fundos_tivio_geral.html"
ARQ_ANO = "dashboard_fundos_tivio_"


def _geral(escopo) -> bool:
    return str(escopo).lower() == "geral"


def chaves(escopo, anos_disponiveis):
    """Chaves da barra de periodo: 1..12 (ano) ou os anos (geral)."""
    if _geral(escopo):
        return sorted(int(a) for a in anos_disponiveis)
    return list(range(1, 13))


def _rotulo(escopo, chave) -> str:
    if _geral(escopo):
        return str(chave)
    return f"{ABREV[chave]}/{str(escopo)[2:]}"


def _rotulo_completo(escopo, totais, chs) -> str:
    """Rotulo do 'Periodo Completo' (chave 0)."""
    com_dado = [c for c in chs if int(totais.get(c, 0)) > 0]
    if not com_dado:
        return "Geral" if _geral(escopo) else f"Ano {escopo}"
    if _geral(escopo):
        if com_dado[0] == com_dado[-1]:
            return str(com_dado[0])
        return f"{com_dado[0]}-{com_dado[-1]}"
    yy = str(escopo)[2:]
    return f"{ABREV[com_dado[0]]}-{ABREV[com_dado[-1]]}/{yy}"


def _seletor_html(escopo, anos_disponiveis) -> str:
    opcoes = ['<option value="geral"{}>Geral</option>'.format(
        " selected" if _geral(escopo) else ""
    )]

    for a in sorted((int(x) for x in anos_disponiveis), reverse=True):
        sel = " selected" if (not _geral(escopo) and int(escopo) == a) else ""
        opcoes.append(f'<option value="{a}"{sel}>{a}</option>')

    onchange = (
        "location.href=(this.value==='geral'"
        f"?'{ARQ_GERAL}'"
        f":'{ARQ_ANO}'+this.value+'.html')"
    )

    return (
        '<span class="mf-lbl">Ano:</span>'
        '<select class="tv-select" id="yearSel" style="margin-right:10px" '
        f'onchange="{onchange}">' + "".join(opcoes) + "</select>"
    )


def _barra_html(escopo, totais, anos_disponiveis) -> str:
    chs = chaves(escopo, anos_disponiveis)

    pills, total = [], 0
    for c in chs:
        n = int(totais.get(c, 0))
        total += n
        tem = n > 0
        cls = "month-pill" if tem else "month-pill off"
        dis = "" if tem else " disabled"
        badge = f' <span class="mp-badge">{n}</span>' if tem else ""
        pills.append(
            f'<button class="{cls}" data-month="{c}"{dis}>'
            f"{_rotulo(escopo, c)}{badge}</button>"
        )

    rot = "Periodo Completo" if _geral(escopo) else "Período Completo"
    pills.append(
        f'<button class="month-pill" data-month="0">Período Completo · {total}</button>'
    )

    return (
        '<div class="month-filter-bar">'
        + _seletor_html(escopo, anos_disponiveis)
        + '<span class="mf-lbl">Período:</span>'
        + "".join(pills)
        + "</div>"
    )


def _mes_nomes_js(escopo, totais, anos_disponiveis) -> str:
    chs = chaves(escopo, anos_disponiveis)
    partes = [f'{c}:"{_rotulo(escopo, c)}"' for c in chs]
    partes.append(f'0:"{_rotulo_completo(escopo, totais, chs)}"')
    return "const MES_NOMES = {" + ",".join(partes) + "};"


def _mes_totais_js(escopo, totais, anos_disponiveis) -> str:
    chs = chaves(escopo, anos_disponiveis)
    total = sum(int(totais.get(c, 0)) for c in chs)
    partes = [f"{c}:{int(totais.get(c, 0))}" for c in chs]
    partes.append(f"0:{total}")
    return "const MES_TOTAIS = {" + ",".join(partes) + "};"


def _refbar_html(escopo, totais, anos_disponiveis, hoje) -> str:
    chs = chaves(escopo, anos_disponiveis)
    com_dado = [c for c in chs if int(totais.get(c, 0)) > 0]

    if _geral(escopo):
        if com_dado:
            periodo = f"01/01/{com_dado[0]} a <b>31/12/{com_dado[-1]}</b>"
        else:
            periodo = "&mdash;"
        recorte = "Geral · todos os anos"
    else:
        if com_dado:
            periodo = (
                f"01/{com_dado[0]:02d}/{escopo} a "
                f"<b>{ABREV[com_dado[-1]]}/{escopo}</b>"
            )
        else:
            periodo = "&mdash;"
        recorte = f"Ano {escopo}"

    return (
        '<div class="tv-refbar">'
        '<div class="tv-refbar-item"><span class="l">Período de referência</span>'
        f'<span class="v">{periodo}</span></div>'
        '<div class="tv-refbar-item"><span class="l">Recorte ativo</span>'
        f'<span class="v">{recorte}</span></div>'
        '<div class="tv-refbar-item"><span class="l">Base</span>'
        '<span class="v">Databricks · marketdata.silver (ANBIMA) · '
        f'atualizado em {hoje.strftime("%d/%m/%Y")}</span></div>'
        '<div class="tv-refbar-spacer"></div>'
        '<div class="tv-refbar-src">Fonte: CVM · ANBIMA · RCVM 175</div>'
        "</div>"
    )


CSS_PATCH = """<style id="tv-meses-patch">
.month-pill.off{opacity:.32;cursor:not-allowed;border-style:dashed;
  color:color-mix(in srgb,var(--veil) 30%,transparent)}
.month-pill.off:hover{transform:none;
  color:color-mix(in srgb,var(--veil) 30%,transparent);
  border-color:color-mix(in srgb,var(--veil) 10%,transparent)}
.mp-badge{font-size:9px;font-weight:700;color:var(--tivio);
  background:color-mix(in srgb,var(--accent-strong) 12%,transparent);
  border-radius:999px;padding:1px 6px;margin-left:3px}
.month-pill.active .mp-badge{background:var(--tivio);color:var(--on-accent)}
#yearSel{min-width:78px}
</style>"""


def _injetar_css(html: str) -> str:
    if 'id="tv-meses-patch"' in html:
        return html
    if "</head>" in html:
        return html.replace("</head>", CSS_PATCH + "\n</head>", 1)
    return CSS_PATCH + html


def aplicar(html: str, escopo, totais: dict, anos_disponiveis, hoje=None) -> str:
    """Aplica todas as substituicoes e devolve o HTML novo."""
    if hoje is None:
        hoje = datetime.now()

    anos_disponiveis = [int(a) for a in (anos_disponiveis or [])]
    if not anos_disponiveis and not _geral(escopo):
        anos_disponiveis = [int(escopo)]

    totais = {int(k): int(v) for k, v in (totais or {}).items()}
    chs = chaves(escopo, anos_disponiveis)

    # 1) barra de periodo (a primeira, sem tv-filter2)
    html = re.sub(
        r'<div class="month-filter-bar">.*?</div>',
        lambda m: _barra_html(escopo, totais, anos_disponiveis),
        html, count=1, flags=re.DOTALL,
    )

    # 2) modo do periodo (mes | ano)
    modo = "ano" if _geral(escopo) else "mes"
    html = re.sub(
        r'const\s+PERIODO_MODO\s*=\s*"[^"]*";',
        f'const PERIODO_MODO = "{modo}";',
        html, count=1,
    )

    # 3) chaves da barra
    html = re.sub(
        r"const\s+PERIODO_KEYS\s*=\s*\[[^\]]*\];",
        "const PERIODO_KEYS = [" + ",".join(str(c) for c in chs) + "];",
        html, count=1,
    )

    # 4) MES_NOMES
    html = re.sub(
        r"const\s+MES_NOMES\s*=\s*\{[^}]*\};",
        lambda m: _mes_nomes_js(escopo, totais, anos_disponiveis),
        html, count=1,
    )

    # 5) MES_TOTAIS
    html = re.sub(
        r"const\s+MES_TOTAIS\s*=\s*\{[^}]*\};",
        lambda m: _mes_totais_js(escopo, totais, anos_disponiveis),
        html, count=1,
    )

    # 6) periodo inicial: ultimo mes com dado (ano) ou Periodo Completo (geral)
    if _geral(escopo):
        inicial = 0
    else:
        com_dado = [c for c in chs if totais.get(c, 0) > 0]
        inicial = com_dado[-1] if com_dado else 0

    html = re.sub(
        r"let\s+currentMonth\s*=\s*\d+",
        f"let currentMonth={inicial}",
        html, count=1,
    )

    # 7) barra de referencia do topo
    html = re.sub(
        r'<div class="tv-refbar">.*?</div>\s*</div>',
        lambda m: _refbar_html(escopo, totais, anos_disponiveis, hoje),
        html, count=1, flags=re.DOTALL,
    )

    # 8) CSS do estado "apagado" + badge
    html = _injetar_css(html)

    return html
