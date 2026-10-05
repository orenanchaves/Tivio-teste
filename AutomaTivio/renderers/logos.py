# -*- coding: utf-8 -*-
"""Logos dos fundos para os materiais legados (e-mail), sempre na versão HORIZONTAL.

O e-mail trazia os logos embutidos à mão, na versão empilhada (TIVIO em cima,
BANKS embaixo) e, no ALT, na variante _01. Os relatórios publicados usam o logo
horizontal, então o e-mail passa a sair dos mesmos arquivos de assets/logos:

- modo escuro: horizontal branca (a horizontal preta com o "TIVIO" em branco
  quando não existe branca — é o caso do Tivio Institucional);
- modo claro: horizontal preta (ou a branca escurecida, se não houver preta).

O formato devolvido é o que o e-mail já usa: {'vb': viewBox, 'p': miolo do SVG}
com a cor em `fill` no próprio elemento (o CSS do modo claro do e-mail troca
cor por atributo, não por classe). O viewBox é recortado pelo contorno real do
desenho, medido no Chromium: os SVGs vêm com muita margem interna.
"""
import json
import os
import re
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, 'assets', 'logos')

# chave do e-mail -> nome do logo em assets/logos
LOGO_DO_EMAIL = {
    'banks': 'Banks', 'institucional': 'Institucional', 'inst15': 'Institucional 15',
    'inst30': 'Institucional 30', 'infra': 'Infra Plus', 'infracdi': 'Infra Plus CDI',
    'esplanada': 'Esplanada', 'legacy': 'Legacy', 'rfcp': 'RF CP',
    'altlight': 'ALT_LIGHT', 'alt180': 'ALT_180', 'alt90': 'ALT_90',
    # chaves usadas nos posts de Destaques
    'infraplus': 'Infra Plus', 'infrapluscdi': 'Infra Plus CDI', 'legacy': 'Legacy',
}


def _slug(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


def _indice():
    idx = {}
    for raiz, _, arqs in os.walk(PASTA):
        for a in arqs:
            if a.lower().endswith('.svg'):
                idx[_slug(os.path.splitext(a)[0])] = os.path.join(raiz, a)
    return idx


def _achar(idx, nome, cor):
    """O arquivo horizontal na cor pedida; numeradas, a de maior número (_03)."""
    alvo = _slug(nome)
    melhor = None
    for chave, caminho in idx.items():
        if not chave.startswith(alvo):
            continue
        resto = chave[len(alvo):].strip('_')
        m = re.fullmatch(rf'horizontal_{cor}(?:_(\d+))?', resto)
        if m:
            n = int(m.group(1) or 0)
            if melhor is None or n > melhor[0]:
                melhor = (n, caminho)
    return melhor[1] if melhor else None


def _miolo(svg, padrao):
    """SVG do Illustrator -> (viewBox, miolo com fill por elemento)."""
    vb = re.search(r'viewBox="([^"]+)"', svg)
    vb = vb.group(1) if vb else '0 0 100 100'
    vw, vh = [float(x) for x in vb.split()[2:4]]
    cores = {m.group(1): m.group(2) for m in
             re.finditer(r'\.(cls-\d+)\s*\{[^}]*?fill:\s*(#[0-9a-fA-F]{3,6})', svg)}
    corpo = re.search(r'<svg[^>]*>(.*)</svg>', svg, re.S).group(1)
    corpo = re.sub(r'<defs>.*?</defs>', '', corpo, flags=re.S)
    corpo = re.sub(r'<title>.*?</title>', '', corpo, flags=re.S)

    # retângulo de fundo (>= 98% do viewBox): vira um bloco atrás do logo
    def fundo(m):
        tag = m.group(0)
        w = re.search(r'\bwidth="([\d.]+)"', tag)
        h = re.search(r'\bheight="([\d.]+)"', tag)
        if w and h and float(w.group(1)) >= vw * .98 and float(h.group(1)) >= vh * .98:
            return ''
        return tag
    corpo = re.sub(r'<rect\b[^>]*/>', fundo, corpo)

    def pinta(m):
        tag, nome = m.group(0), m.group(1)
        cls = re.search(r'\bclass="([^"]+)"', tag)
        cor = None
        if cls:
            for c in cls.group(1).split():
                cor = cores.get(c, cor)
            tag = re.sub(r'\s*\bclass="[^"]+"', '', tag)
        if 'fill=' not in tag:
            tag = tag.replace(f'<{nome}', f'<{nome} fill="{cor or padrao}"', 1)
        return tag
    corpo = re.sub(r'<(path|rect|polygon|circle|ellipse|polyline)\b[^>]*>', pinta, corpo)
    corpo = re.sub(r'\s+id="[^"]*"', '', corpo)
    corpo = re.sub(r'>\s+<', '><', corpo).strip()
    return vb, corpo


def _recortar(logos):
    """Mede o contorno de cada logo no Chromium e devolve o viewBox justo."""
    try:
        from playwright.sync_api import sync_playwright
        from exporters.pdf import achar_chromium
    except Exception:
        return logos
    itens = list(logos.items())
    html = ''.join(f'<svg id="l{i}" viewBox="{v["vb"]}" width="400" height="200" '
                   f'xmlns="http://www.w3.org/2000/svg">{v["p"]}</svg>'
                   for i, (_, v) in enumerate(itens))
    try:
        with sync_playwright() as p:
            op = {'args': ['--no-sandbox']}
            exe = achar_chromium()
            if exe:
                op['executable_path'] = exe
            b = p.chromium.launch(**op)
            pg = b.new_page()
            pg.set_content('<body>' + html + '</body>')
            caixas = pg.evaluate("""n => [...Array(n).keys()].map(i => {
                const b = document.getElementById('l' + i).getBBox();
                return [b.x, b.y, b.width, b.height]; })""", len(itens))
            b.close()
    except Exception:
        return logos
    for (k, v), (x, y, w, h) in zip(itens, caixas):
        if w > 0 and h > 0:
            v['vb'] = f'{x:.2f} {y:.2f} {w:.2f} {h:.2f}'
    return logos


def logos_horizontais(chaves, log=None):
    """{chave: {'vb','p'}} para o modo escuro e para o modo claro."""
    idx = _indice()
    escuro, claro = {}, {}
    for k in chaves:
        nome = LOGO_DO_EMAIL.get(k)
        if not nome:
            continue
        br, pr = _achar(idx, nome, 'branco'), _achar(idx, nome, 'preto')
        if not (br or pr):
            if log:
                log.aviso(k, f'logo horizontal não encontrado em assets/logos ("{nome}")')
            continue
        # escuro: branca; sem branca, a preta com o que não tem cor em branco
        # (o que vem sem cor no arquivo é preto pelo padrão do SVG — o "15" do
        # Institucional 15 na caixa branca; só vira branco quando a preta
        # faz as vezes da branca)
        f = br or pr
        vb, p = _miolo(open(f, encoding='utf-8').read(), '#000' if br else '#fff')
        escuro[k] = {'vb': vb, 'p': p}
        # claro: preta; sem preta, a branca (o CSS do e-mail escurece o branco)
        f = pr or br
        vb, p = _miolo(open(f, encoding='utf-8').read(), '#0A0F14')
        claro[k] = {'vb': vb, 'p': p}
    _recortar(escuro)
    _recortar(claro)
    return escuro, claro


def como_js(nome, logos):
    return f'const {nome}={json.dumps(logos, ensure_ascii=False)};'
