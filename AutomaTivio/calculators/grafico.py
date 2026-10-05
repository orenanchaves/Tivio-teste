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


def _envelope(dados, miolo, altura=None, interativo=False):
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
    # Sem `data-tv`: o desenho do servidor é o do relatório publicado, e o
    # ECharts redesenhava por cima com outro visual (cores, eixos, rótulos).
    # Os dados ficam em `data-dados` para quem quiser religar a interação.
    attr = _json.dumps(dados, ensure_ascii=False).replace("'", '&#39;')
    # `interativo`: o ECharts assume o contêiner (data-tv) com a MESMA
    # especificação do desenho do servidor — hoje, o histórico de rentabilidade
    alvo = 'data-tv' if interativo else 'data-dados'
    return f"<div class=\"tv-chart\" {alvo}='{attr}'>{miolo}</div>"


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


# ---------------------------------------------------------------------------
# Treemap — o bloco "Alocação real da carteira de crédito" dos relatórios de
# Crédito Estruturado. No PPTX publicado ele é um conjunto de retângulos
# proporcionais com o nome e o percentual dentro, não barras: é assim que o ALT
# mostra que metade da carteira é cota sênior de FIDC. Barras horizontais dizem
# a mesma coisa com outro desenho, e o relatório deixa de parecer o original.
#
# O algoritmo é o "squarified" (Bruls, Huizing & van Wijk, 2000): vai
# empilhando itens numa faixa enquanto a pior proporção largura/altura melhora,
# e fecha a faixa quando ela começa a piorar. É o que evita as tiras compridas
# que um treemap ingênuo produz — e tira comprida não cabe o rótulo dentro.
# ---------------------------------------------------------------------------
# Na ordem do maior para o menor, como no ALT publicado: preto, gelo, azul
# escuro, verde claro, azul, cinza, verde escuro.
TREEMAP_CORES = ['#232323', '#E9EEF1', '#3C4A60', '#C6F3D6', '#7FA3B9',
                 '#9AA8B1', '#17602F', '#52B97A']


def _pior(fila, lado, escala):
    """Pior razão de aspecto de uma faixa — o critério de parada do squarified."""
    soma = sum(fila) * escala
    if soma <= 0 or lado <= 0:
        return float('inf')
    mx, mn = max(fila) * escala, min(fila) * escala
    return max(lado * lado * mx / (soma * soma), soma * soma / (lado * lado * mn))


def _squarify(valores, x, y, larg, alt, escala, saida):
    if not valores:
        return
    fila, resto = [], list(valores)
    lado = min(larg, alt)
    while resto:
        atual = _pior(fila, lado, escala) if fila else float('inf')
        if fila and _pior(fila + [resto[0]], lado, escala) > atual:
            break
        fila.append(resto.pop(0))

    soma = sum(fila) * escala
    espesso = soma / lado if lado else 0
    desloc = 0.0
    for v in fila:
        passo = (v * escala) / espesso if espesso else 0
        if larg >= alt:
            saida.append((x, y + desloc, espesso, passo))
        else:
            saida.append((x + desloc, y, passo, espesso))
        desloc += passo

    if larg >= alt:
        _squarify(resto, x + espesso, y, larg - espesso, alt, escala, saida)
    else:
        _squarify(resto, x, y + espesso, larg, alt - espesso, escala, saida)


def _claro(hexcor):
    """Luminância relativa > 0,55 -> o texto branco some em cima."""
    r, g, b = (int(hexcor[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) > 0.55


def _rotulo_tm(nome):
    """'FIDCs Cotas Sênior' -> 'FIDCs' leve + 'Cotas Sênior' em negrito, como no ALT."""
    partes = str(nome).split(' ', 1)
    if len(partes) == 1:
        return _esc(nome)
    return f'{_esc(partes[0])}<br><b>{_esc(partes[1])}</b>'


def treemap(itens, largura=1000, altura=192, cores=None):
    """[(nome, '49,1%', valor)] -> blocos proporcionais, do maior para o menor.

    A proporção (1000x190) é a do PPTX publicado, onde o bloco tem 712x137 px
    numa folha de 794 — uma faixa larga e baixa, não um quadrado. Em quadrado
    ele empurraria o comentário do gestor para fora da folha 1.

    Os retângulos saem posicionados em porcentagem, então o bloco acompanha a
    largura da folha (e do PDF) sem recalcular nada. O corpo do texto, porém,
    é dimensionado em pixel a partir do tamanho de CADA caixa: num bloco de
    2,2% da carteira o rótulo de 13px não cabe, e um rótulo que não cabe vira
    um borrão cortado — foi o que aconteceu com "Crédito Estruturado".
    """
    # a paleta segue a ordem do maior para o menor; o ALT Light publicado usa
    # outra (configs/fundos.yml -> treemap_cores)
    paleta = list(cores) if cores else TREEMAP_CORES
    itens = [i for i in itens if i[2] and i[2] > 0]
    itens.sort(key=lambda i: -i[2])
    if not itens:
        return '<div class="histvazio">sem carteira nesta edição</div>'

    valores = [i[2] for i in itens]
    escala = (largura * altura) / sum(valores)
    caixas = []
    _squarify(valores, 0.0, 0.0, float(largura), float(altura), escala, caixas)

    def limites(v, lo, hi):
        return max(lo, min(hi, v))

    blocos = []
    for i, ((nome, rotulo, _), (bx, by, bl, ba)) in enumerate(zip(itens, caixas)):
        cor = paleta[min(i, len(paleta) - 1)]
        tinta = '#2B3744' if _claro(cor) else '#fff'

        fv = limites(min(bl / 5.2, ba / 3.2), 9.5, 21.0)
        fn = limites(min(bl / 8.0, ba / 5.2), 8.0, 17.0)
        # o nome só entra se couber em duas linhas de verdade: largura para uns
        # 9 caracteres por linha, e altura para as duas linhas mais o valor
        pad = limites(bl / 14, 5.0, 13.0)
        # nome em duas linhas + valor + respiro, senão o nome sobe por cima do valor
        cabe = bl >= fn * 7 and ba >= fn * 2.3 + fv * 1.15 + 2 * pad + 4
        pad = limites(bl / 14, 5.0, 13.0)

        blocos.append(
            f'<div class="tmbox" style="left:{bx / largura * 100:.4f}%;'
            f'top:{by / altura * 100:.4f}%;width:{bl / largura * 100:.4f}%;'
            f'height:{ba / altura * 100:.4f}%;background:{cor};color:{tinta};'
            f'padding:{pad:.1f}px" '
            f'title="{_esc(nome)} · {_esc(rotulo)}">'
            + (f'<span class="tmn" style="font-size:{fn:.1f}px">{_rotulo_tm(nome)}</span>'
               if cabe else '')
            + f'<span class="tmv" style="font-size:{fv:.1f}px">{_esc(rotulo)}</span>'
            + '</div>')

    # Legenda embaixo, com todos os itens: nas caixas pequenas o nome não
    # cabe, e sem ela o leitor fica com um "2,6%" sem dizer de quê.
    legenda = ''.join(
        f'<span class="tmleg"><i style="background:'
        f'{paleta[min(i, len(paleta) - 1)]}"></i>{_esc(n)} '
        f'<b>{_esc(r)}</b></span>'
        for i, (n, r, _) in enumerate(itens))
    return (f'<div class="tmwrap" style="aspect-ratio:{largura}/{altura}">'
            + ''.join(blocos) + '</div>'
            + f'<div class="tmlegs">{legenda}</div>')


# ---------------------------------------------------------------------------
# Desenho dos relatórios publicados (PDF de agosto/2026, Institucional 30 e
# ALT 180). Barra horizontal com o rótulo alinhado à direita, um eixo fino e o
# valor logo depois do fim da barra — não numa coluna à parte. A espessura e a
# cor mudam por bloco: emissores em barra grossa azul, setores e rating em
# barra fina azul-clara, a estratégia do ALT em verde.
# ---------------------------------------------------------------------------
def barras_modelo(itens, estilo, altura, espessura=None):
    """[(nome, '12,34%', valor)] -> linhas proporcionais ao maior valor.

    `altura` é a do bloco em px na folha: as linhas se distribuem nela, como no
    PPTX, onde a lista de setores desce até o rodapé.
    """
    itens = [i for i in itens if i[2] is not None]
    if not itens:
        return '<div class="histvazio">sem carteira nesta edição</div>'
    mx = max(float(v) for _, _, v in itens) or 1
    linhas = []
    for nome, rotulo, v in itens:
        # a barra ocupa até 80% do trilho: o resto é do valor escrito depois dela
        larg = max(0.6, float(v) / mx * 80)
        linhas.append(
            f'<div class="hb"><span class="hbk">{_esc(nome)}</span>'
            f'<span class="hbt"><span class="hbf" style="width:{larg:.2f}%"></span>'
            f'<span class="hbv">{_esc(rotulo)}</span></span></div>')
    # lista curta: barra mais grossa (a linha também fica mais alta)
    esp = f'--hb-h:{espessura:.1f}px;' if espessura else ''
    return (f'<div class="hbars hb-{estilo}" style="height:{altura}px;{esp}'
            f'--hb-n:{len(itens)}">' + ''.join(linhas) + '</div>')


def _passo_eixo(maxv):
    """Degrau redondo do eixo Y: 5 em 5 até 30%, 10 em 10 acima."""
    for p in (1, 2, 2.5, 5, 10, 20, 25, 50):
        if maxv / p <= 7:
            return p
    return 100


def historico_modelo(hist, nome_bench, estilo, data_inicio=None,
                     largura=1000, altura=None):
    """Rentabilidade acumulada desde o início, no desenho do relatório publicado.

    cp: Fundo azul e CDI verde-claro, eixo em 0,00%, meses inclinados (dez-24).
    ce: Fundo verde e CDI preto, eixo em 0,0%, meses na vertical (jan/25) e o
        valor final de cada linha numa etiqueta da cor dela.
    """
    if not hist or not hist.get('l') or len(hist['l']) < 2:
        return '<div class="histvazio">sem série histórica</div>'
    meses, fundo, bench = list(hist['l']), list(hist['f']), list(hist['c'])
    trib = list(hist['t']) if hist.get('t') else None
    # a curva publicada nasce em 0% no mês de início do fundo
    inserido = False
    if fundo[0] != 0 and data_inicio is not None and str(data_inicio) != 'NaT':
        ini = f'{data_inicio:%Y-%m}'
        if ini < meses[0]:
            meses.insert(0, ini); fundo.insert(0, 0.0); bench.insert(0, 0.0)
            if trib is not None: trib.insert(0, 0.0)
            inserido = True
        elif estilo == 'ce' and ini == meses[0]:
            # começou no meio do mês: a linha nasce em 0 e o mês parcial fica
            # sem rótulo — o primeiro rótulo é o mês seguinte, como no publicado
            meses.insert(0, ini); fundo.insert(0, 0.0); bench.insert(0, 0.0)
            if trib is not None: trib.insert(0, 0.0)
            inserido = 'parcial'
    sep = '-' if estilo == 'cp' else '/'
    labels = [f'{fmt.MES_ABR[int(m[5:7]) - 1]}{sep}{m[2:4]}' for m in meses]
    n = len(labels)

    # o do ALT é mais alto: divide a folha só com a estratégia e os colaterais
    altura = altura or (360 if estilo == 'cp' else 470)
    if estilo == 'cp':
        cf, cb, wf, wb, casas = '#5B8299', '#A9EBC4', 2.6, 2.6, 2
        padL, padR, padT, padB, rot = 78, 112, 46, 62, -45
    else:
        cf, cb, wf, wb, casas = '#26B663', '#1F1F1F', 3.6, 3.6, 1
        padL, padR, padT, padB, rot = 84, 112, 26, 82, -90

    ct = '#3C4A60'                    # Bench Tributado: azul escuro, tracejado
    maxv = max(fundo + bench + (trib or []) + [0])
    passo = _passo_eixo(maxv)
    topo = passo * (int(maxv / passo) + 1)
    if estilo == 'ce':
        # o Estruturado publicado para a grade no degrau ABAIXO do valor final
        # (30% para um acumulado de 33%; 12% para 12,6%) e a linha passa dela
        topo = max(passo, passo * int(maxv / passo))
    # a escala vai até o valor final (com folga para a etiqueta); a grade, só até o topo
    escala_topo = max(topo, maxv * 1.06)
    minv = min(fundo + bench + (trib or []) + [0])
    base = 0 if minv >= 0 else -passo * (int(-minv / passo) + 1)

    def X(i):
        return padL + (largura - padL - padR) * i / (n - 1)

    def Y(v):
        return padT + (altura - padT - padB) * (1 - (v - base) / (escala_topo - base))

    s = [f'<svg viewBox="0 0 {largura} {altura}" xmlns="http://www.w3.org/2000/svg" '
         f'font-family="Versos,Arial,sans-serif" class="histsvg hs-{estilo}">']
    if estilo == 'cp':
        meio = largura / 2
        s.append(f'<g font-size="12.5" fill="#333" font-weight="600">'
                 f'<line x1="{meio - 118 - (70 if trib else 0)}" y1="{padT - 20}" x2="{meio - 84 - (70 if trib else 0)}" y2="{padT - 20}" '
                 f'stroke="{cf}" stroke-width="3"/>'
                 f'<text x="{meio - 80 - (70 if trib else 0)}" y="{padT - 16}">Fundo</text>'
                 f'<line x1="{meio - 16 - (70 if trib else 0)}" y1="{padT - 20}" x2="{meio + 18 - (70 if trib else 0)}" y2="{padT - 20}" '
                 f'stroke="{cb}" stroke-width="3"/>'
                 f'<text x="{meio + 22 - (70 if trib else 0)}" y="{padT - 16}">{_esc(nome_bench)}</text>'
                 + (f'<line x1="{meio + 110}" y1="{padT - 20}" x2="{meio + 144}" y2="{padT - 20}" '
                    f'stroke="{ct}" stroke-width="2.4" stroke-dasharray="6 4"/>'
                    f'<text x="{meio + 148}" y="{padT - 16}">Bench Tributado</text>' if trib else '')
                 + '</g>')
    v = base
    while v <= topo + 1e-9:
        gy = Y(v)
        s.append(f'<line x1="{padL}" y1="{gy:.1f}" x2="{largura - padR}" y2="{gy:.1f}" '
                 f'stroke="#D6D6D6" stroke-width="1"/>')
        s.append(f'<text x="{padL - 12}" y="{gy + 4.5:.1f}" fill="#333" font-size="'
                 f'{13 if estilo == "cp" else 15.5}" font-weight="600" text-anchor="end">'
                 f'{fmt.num(v, casas)}%</text>')
        v += passo
    # Um rótulo por mês, como no publicado, enquanto couber (~24 meses). O
    # Institucional tem série desde 2005: mês a mês vira uma mancha no eixo,
    # então rareia mantendo o último mês.
    passo_eixo = passo
    passo = max(1, -(-n // 24)) if n <= 30 else max(2, -(-n // 18))
    visiveis = []
    for i, lb in enumerate(labels):
        mostra = not ((n - 1 - i) % passo)
        # no Estruturado o mês de início (parcial) não leva rótulo
        if estilo == 'ce' and inserido and (i == 0 or (inserido == 'parcial' and i == 1)):
            mostra = False
        visiveis.append(lb if mostra else '')
    for i, lb in enumerate(visiveis):
        if not lb:
            continue
        x, y = X(i), altura - padB + 14
        anc = 'end'
        s.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="#333" font-size="'
                 f'{12.5 if estilo == "cp" else 14.5}" font-weight="600" text-anchor="{anc}" '
                 f'transform="rotate({rot} {x:.1f} {y:.1f})" '
                 f'dominant-baseline="middle">{lb}</text>')
    pts = lambda serie: ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, v in enumerate(serie))
    s.append(f'<polyline points="{pts(bench)}" fill="none" stroke="{cb}" stroke-width="{wb}" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')
    if trib:
        s.append(f'<polyline points="{pts(trib)}" fill="none" stroke="{ct}" stroke-width="2.4" '
                 f'stroke-dasharray="6 4" stroke-linejoin="round" stroke-linecap="round"/>')
    s.append(f'<polyline points="{pts(fundo)}" fill="none" stroke="{cf}" stroke-width="{wf}" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')
    # o acumulado no fim de cada linha, numa etiqueta da cor dela (as duas
    # verticais); quando as linhas terminam juntas, as etiquetas se afastam
    lx = X(n - 1)
    yf, yb = Y(fundo[-1]), Y(bench[-1])
    if abs(yf - yb) < 30:
        m = (yf + yb) / 2
        yf, yb = (m - 15, m + 15) if fundo[-1] >= bench[-1] else (m + 15, m - 15)
    tinta_b = '#fff' if not _claro(cb) else '#1F1F1F'
    larg_et = 74 if max(abs(fundo[-1]), abs(bench[-1])) >= 100 else 64
    etiquetas = [(yf, cf, '#fff', fundo[-1]), (yb, cb, tinta_b, bench[-1])]
    if trib:
        yt = Y(trib[-1])
        for outro in (yf, yb):
            if abs(yt - outro) < 30:
                yt = outro + (30 if yt >= outro else -30)
        etiquetas.append((yt, ct, '#fff', trib[-1]))
    for yy, cor, tinta, val in etiquetas:
        s.append(f'<rect x="{lx + 4:.1f}" y="{yy - 14:.1f}" width="{larg_et}" height="28" '
                 f'rx="3" fill="{cor}"/><text x="{lx + 4 + larg_et / 2:.1f}" y="{yy + 5:.1f}" '
                 f'fill="{tinta}" font-size="15" font-weight="700" text-anchor="middle">'
                 f'{fmt.num(val, 2)}%</text>')
    s.append('</svg>')
    return _envelope({
        'tipo': 'historico', 'estilo': estilo, 'labels': labels, 'rotulos': visiveis,
        'fundo': fundo, 'bench_serie': bench, 'bench': nome_bench,
        'trib': trib, 'ct': ct,
        'cf': cf, 'cb': cb, 'tinta_b': tinta_b, 'wf': wf, 'wb': wb, 'casas': casas,
        'pad': [padL, padR, padT, padB], 'rot': rot, 'largura': largura,
        'base': base, 'topo': topo, 'escala_topo': escala_topo, 'passo': passo_eixo,
    }, ''.join(s), altura=altura, interativo=True)
