# -*- coding: utf-8 -*-
"""Gráficos em SVG, desenhados no Python.

Por que SVG e não uma biblioteca de gráficos: o relatório vira PDF, e o pedido
era PDF vetorial com fonte incorporada, não impressão de navegador. SVG passa
pelo Chromium como vetor e sai vetor no PDF — texto selecionável, linha sem
pixel. Um PNG de matplotlib viraria imagem rasterizada no meio de uma página
vetorial, e é exatamente isso que faz um PDF parecer impresso.

Por que desenhado aqui e não no JS do material: o gerador HTML atual *inventa* a
série histórica — `histSVG()` interpola uma reta do zero até o valor final, com
um ruidinho para parecer orgânico. O gráfico do relatório publicado não é o
histórico do fundo. Aqui a série é a real, vinda das cotas.
"""
from calculators import formatos as fmt

AZUL = '#3C4A60'
CINZA = '#ABC6CD'
GRID = '#E3E9EE'
ROTULO = '#637881'


def _esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def _envelope(dados, miolo, altura=None):
    """Contêiner que o ECharts assume, com o desenho do servidor dentro.

    Aprimoramento progressivo, e não por elegância: o PDF é gerado sem ninguém
    olhando. Se o ECharts falhar e o bloco for um `<div>` vazio esperando JS, os
    12 PDFs saem com um retângulo branco no meio e isso só aparece depois de
    publicado. Com o desenho do servidor dentro, o pior caso é o gráfico de
    antes — correto, só sem tooltip.
    """
    import json as _json
    if altura:
        dados = dict(dados, altura=altura)
    attr = _json.dumps(dados, ensure_ascii=False).replace("'", '&#39;')
    return f"<div class=\"tv-chart\" data-tv='{attr}'>{miolo}</div>"


def linha_historica(hist, nome_bench, largura=900, altura=430):
    """Duas séries acumuladas (fundo e benchmark) a partir de `Calc.historico`.

    `hist` = {'l': ['2025-08', …], 'f': [0.0, 1.2, …], 'c': [...]} em pontos
    percentuais. Devolve o SVG como string.
    """
    if not hist or not hist.get('l'):
        return '<div class="histvazio">sem série histórica</div>'

    labels = [f'{fmt.MES_ABR[int(l[5:7]) - 1]}-{l[2:4]}' for l in hist['l']]
    fundo, bench = hist['f'], hist['c']
    n = len(labels)
    if n < 2:
        return '<div class="histvazio">série com um ponto só</div>'

    padL, padR, padT, padB = 52, 64, 42, 54
    todos = fundo + bench + [0]
    maxv, minv = max(todos), min(0, min(todos))
    rng = (maxv - minv) or 1
    maxv += rng * 0.12
    # eixo negativo acontece: Infra Plus em IMA-B 5 fecha mês no vermelho. Sem
    # abrir o mínimo a linha sai cortada embaixo do eixo.
    if minv < 0:
        minv -= rng * 0.08
    rng = maxv - minv

    def X(i):
        return padL + (largura - padL - padR) * (i / (n - 1))

    def Y(v):
        return padT + (altura - padT - padB) * (1 - (v - minv) / rng)

    s = [f'<svg viewBox="0 0 {largura} {altura}" xmlns="http://www.w3.org/2000/svg" '
         f'font-family="Versos,Arial,sans-serif" class="histsvg">']

    # legenda
    s.append(f'<g transform="translate({padL},22)" font-size="15" font-weight="700">'
             f'<line x1="0" y1="-5" x2="26" y2="-5" stroke="{AZUL}" stroke-width="3"/>'
             f'<text x="32" y="0" fill="{AZUL}">Fundo</text>'
             f'<line x1="120" y1="-5" x2="146" y2="-5" stroke="{CINZA}" stroke-width="3" '
             f'stroke-dasharray="7 5"/>'
             f'<text x="152" y="0" fill="{AZUL}">{_esc(nome_bench)}</text></g>')

    # grade + eixo Y
    for g in range(5):
        gv = minv + rng * g / 4
        gy = Y(gv)
        s.append(f'<line x1="{padL}" y1="{gy:.1f}" x2="{largura - padR}" y2="{gy:.1f}" '
                 f'stroke="{GRID}" stroke-width="1"/>')
        s.append(f'<text x="{padL - 9}" y="{gy + 4:.1f}" fill="{ROTULO}" font-size="14" '
                 f'font-weight="600" text-anchor="end">{gv:.0f}%</text>')

    pts = lambda serie: ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, v in enumerate(serie))
    s.append(f'<polyline points="{pts(bench)}" fill="none" stroke="{CINZA}" stroke-width="3" '
             f'stroke-dasharray="7 5" stroke-linejoin="round" stroke-linecap="round"/>')
    s.append(f'<polyline points="{pts(fundo)}" fill="none" stroke="{AZUL}" stroke-width="3.4" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')

    lx = X(n - 1)
    s.append(f'<circle cx="{lx:.1f}" cy="{Y(bench[-1]):.1f}" r="4" fill="{CINZA}"/>'
             f'<circle cx="{lx:.1f}" cy="{Y(fundo[-1]):.1f}" r="5" fill="{AZUL}"/>')

    # rótulos do eixo X: com 13+ meses eles se tocam, então rareia
    passo = 1 if n <= 13 else (n + 12) // 13
    for i, lb in enumerate(labels):
        if i % passo and i != n - 1:
            continue
        s.append(f'<text x="{X(i):.1f}" y="{altura - padB + 22}" fill="{ROTULO}" '
                 f'font-size="13" text-anchor="middle">{lb}</text>')

    # Valor final de cada série, à direita. Num fundo que roda colado no
    # benchmark — e os de crédito high grade rodam — as duas linhas terminam a
    # menos de um pixel de distância e os dois rótulos se sobrepõem, virando um
    # borrão. Quando isso acontece, afasta-os na vertical.
    yf, yb = Y(fundo[-1]), Y(bench[-1])
    if abs(yf - yb) < 17:
        meio = (yf + yb) / 2
        yf, yb = meio - 9, meio + 9
    s.append(f'<text x="{lx + 10:.1f}" y="{yf + 5:.1f}" fill="{AZUL}" font-size="15" '
             f'font-weight="700">{fmt.num(fundo[-1], 1)}%</text>')
    s.append(f'<text x="{lx + 10:.1f}" y="{yb + 5:.1f}" fill="{ROTULO}" font-size="14" '
             f'font-weight="600">{fmt.num(bench[-1], 1)}%</text>')

    s.append('</svg>')

    return _envelope({
        'tipo': 'historico',
        'labels': labels,
        'fundo': [round(v, 4) for v in fundo],
        'bench_serie': [round(v, 4) for v in bench],
        'bench': nome_bench,
    }, ''.join(s), altura=altura)


# O markup abaixo não é escolha de estilo: é o que o CSS do relatório (extraído
# do gerador oficial) espera. `.bar` é um grid de três colunas — rótulo, trilho,
# valor; `.bt` é o trilho e `.bf` o preenchimento. Inventar nomes de classe aqui
# produz exatamente o que apareceu no primeiro teste: o texto certo, sem barra.


def barras_horizontais(itens, cor=None):
    """[(nome, '12,34%', largura 0-100)] -> linhas do bloco de emissores/setores.

    A largura mínima de 6% existe porque um emissor de 0,2% desenharia uma barra
    de um pixel, que o olho lê como ausência de barra, não como valor pequeno.
    """
    linhas = []
    for nome, valor, larg in itens:
        larg = max(6, min(100, int(round(larg))))
        linhas.append(
            f'<div class="bar"><span class="bk">{_esc(nome)}</span>'
            f'<span class="bt"><span class="bf" style="width:{larg}%"></span></span>'
            f'<span class="bv">{_esc(valor)}</span></div>')
    if not linhas:
        return '<div class="histvazio">sem carteira nesta edição</div>'

    return _envelope({
        'tipo': 'barras',
        'itens': [[n, round(float(larg), 2)] for n, _, larg in itens],
        'rotulos': [v for _, v, _ in itens],
        'cor': cor or AZUL,
    }, ''.join(linhas), altura=max(120, 34 * len(itens)))


def colunas_rating(itens, colunas=6):
    """[(rating, '46,2%', altura 0-100)] -> colunas verticais + eixo.

    `.ratebars` é um grid de 6 colunas de largura fixa. Com menos de 6 ratings as
    colunas existentes ficariam largas e desalinhadas dos rótulos, então o bloco
    é completado com células vazias.
    """
    if not itens:
        return '<div class="histvazio">sem rating nesta edição</div>'
    itens = list(itens[:colunas])
    vazias = colunas - len(itens)

    barras = ''.join(
        f'<div class="rbar"><span class="rv">{_esc(v)}</span>'
        f'<span class="rfill" style="height:{max(1, min(100, int(round(h))))}%"></span></div>'
        for _, v, h in itens) + '<div class="rbar"></div>' * vazias
    rotulos = ''.join(f'<span class="rk">{_esc(k)}</span>' for k, _, _ in itens) \
        + '<span class="rk"></span>' * vazias
    return _envelope({
        'tipo': 'colunas',
        'itens': [[k, round(float(h), 2)] for k, _, h in itens],
        'rotulos': [v for _, v, _ in itens],
    }, f'<div class="ratebars">{barras}</div>'
       f'<div class="ratelabels">{rotulos}</div>', altura=232)
