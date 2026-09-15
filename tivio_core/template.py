# -*- coding: utf-8 -*-
"""Injecao de dados no template HTML e limpeza do cabecalho."""
import json
import re
from pathlib import Path
from datetime import datetime


def injetar_array(html: str, nome: str, dados) -> str:
    """Troca `const <nome> = [...]` pelo array novo.

    Falha alto quando o marcador nao existe: um template sem o bloco
    geraria um dashboard silenciosamente vazio.
    """
    alvo = f"const {nome} = ["
    ini = html.find(alvo)

    if ini == -1:
        raise RuntimeError(f"bloco '{alvo}' nao encontrado no template")

    fim = html.find("];", ini)

    if fim == -1:
        raise RuntimeError(f"fim do bloco '{nome}' nao encontrado")

    js = json.dumps(dados, ensure_ascii=False)
    return html[:ini] + f"const {nome} = {js};" + html[fim + 2:]


def injetar_objeto(html: str, nome: str, dados: dict) -> str:
    """Mesma ideia de injetar_array, para `const <nome> = {...}`."""
    alvo = f"const {nome} = "
    ini = html.find(alvo)

    if ini == -1:
        return html

    fim = html.find("};", ini)

    if fim == -1:
        raise RuntimeError(f"fim do bloco '{nome}' nao encontrado")

    js = json.dumps(dados, ensure_ascii=False)
    return html[:ini] + alvo + js + ";" + html[fim + 2:]


def atualizar_data(html: str, quando: datetime = None) -> str:
    """Escreve dd/mm no selo ATUALIZADO do cabecalho."""
    quando = quando or datetime.now()

    return re.sub(
        r'(<div class="cdi-mini-lbl">ATUALIZADO</div>\s*'
        r'<div class="cdi-mini-val">)[^<]*(</div>)',
        lambda m: m.group(1) + quando.strftime("%d/%m") + m.group(2),
        html,
        count=1,
    )


# ------------------------------------------------------------------ menu
# aceita atributos extras: o ETF usa <span class="dash-tab-badge"
# id="etf-nav-badge">, que a versao anterior do padrao deixava passar
_BADGE = re.compile(
    r'\s*<span[^>]*class="[^"]*dash-tab-badge[^"]*"[^>]*>[^<]*</span>'
)


def remover_badges_menu(html: str) -> tuple:
    """Tira os contadores do menu superior.

    Eram numeros fixos no HTML: cada atualizacao de qualquer dashboard
    exigia reescrever o contador em todos os outros arquivos a mao, e
    quando isso nao acontecia o menu passava a mentir. A regra CSS fica,
    para o dia em que forem preenchidos de forma automatica.
    """
    novo, n = _BADGE.subn("", html)
    return novo, n


def atualizar_contador(html: str, ancora: str, valor, antes: bool = False) -> tuple:
    """Troca o numero vizinho a um rotulo fixo do HTML.

    Existe pelo mesmo motivo de remover_badges_menu: o template traz
    totais escritos a mao ("218 ofertas") que nao acompanham o dado, e
    o dashboard passa a exibir dois numeros diferentes para a mesma
    coisa. Substituir o numero solto seria arriscado - por isso a troca
    e ancorada no texto ao lado.

    ancora  texto fixo que identifica o lugar (regex ja escapado por quem chama)
    antes   True quando o numero vem ANTES da ancora
    """
    if antes:
        padrao = re.compile(r"(\d[\d.,]*)(\s*" + ancora + ")")
        novo, n = padrao.subn(lambda m: f"{valor}{m.group(2)}", html)
    else:
        padrao = re.compile("(" + ancora + r"\s*)(\d[\d.,]*)")
        novo, n = padrao.subn(lambda m: f"{m.group(1)}{valor}", html)

    return novo, n


# ---------------------------------------------------------------- graficos
ECHARTS_VER = "5.6.0"

_LOADER = (
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/'
    + ECHARTS_VER + '/echarts.min.js" '
    'onerror="(function(t){t.remove();var s=document.createElement(\'script\');'
    "s.src='https://cdn.jsdelivr.net/npm/echarts@" + ECHARTS_VER
    + "/dist/echarts.min.js';"
    'document.head.appendChild(s);})(this)"></script>'
)

_MARCA = "<!-- tivio-charts -->"


def injetar_charts(html: str, assets_dir=None) -> tuple:
    """Inline o loader do ECharts e o tivio_charts.js no HTML.

    Inline, e nao <script src>, porque os dashboards circulam como
    arquivo solto: um caminho externo quebraria assim que alguem movesse
    so o .html. O custo e ~16 KB por arquivo.

    O loader tenta cdnjs e cai para o jsDelivr; sem os dois, o proprio
    modulo cai para barras em CSS. Devolve (html, injetou).
    """
    if _MARCA in html:
        return html, False

    if assets_dir is None:
        assets_dir = Path(__file__).resolve().parent / "assets"

    js = (Path(assets_dir) / "tivio_charts.js").read_text(encoding="utf-8")

    bloco = (
        f"\n{_MARCA}\n{_LOADER}\n"
        f"<script>\n{js}\n</script>\n{_MARCA}\n"
    )

    if "</body>" in html:
        return html.replace("</body>", bloco + "</body>", 1), True

    return html + bloco, True


def ativar_charts(html: str, seletor: str, espera_ms: int = 300) -> str:
    """Injeta o modulo e dispara tvUpgradeTodos() sobre um seletor.

    O upgrade roda DEPOIS do render do proprio dashboard - por isso o
    timeout e o MutationObserver: varios paineis so existem quando a
    pessoa troca de aba, e ai precisam ser convertidos tambem.
    """
    html, _ = injetar_charts(html)

    gatilho = f"""
<!-- tivio-charts-ativar -->
<script>
(function(){{
  var SEL = {seletor!r};

  function subir(){{
    if(!window.echarts || typeof tvUpgradeTodos !== 'function') return;
    try {{ tvUpgradeTodos(SEL); }} catch(e) {{ /* painel sem barras */ }}
  }}

  function tentar(n){{
    subir();
    if(n > 0) setTimeout(function(){{ tentar(n - 1); }}, {espera_ms});
  }}

  if(document.readyState === 'loading'){{
    document.addEventListener('DOMContentLoaded', function(){{ tentar(12); }});
  }} else {{
    tentar(12);
  }}

  /* paineis de abas inativas so aparecem depois; converte quando surgirem */
  new MutationObserver(function(){{ subir(); }})
    .observe(document.body, {{childList: true, subtree: true}});
}})();
</script>
<!-- tivio-charts-ativar -->
"""

    if "</body>" in html:
        return html.replace("</body>", gatilho + "</body>", 1)

    return html + gatilho
