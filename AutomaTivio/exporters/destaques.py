# -*- coding: utf-8 -*-
"""Posts de Destaques em JPG, direto do Python, uma pasta por vertical.

Antes cada carrossel saía só pelo botão "Pacote JPG" da página. Aqui o
Chromium abre o HTML já gerado da Central e chama a MESMA função que o botão
usa (`renderCard` + `canvasBlob`, 2160 x 2880, JPG 95%), então o arquivo sai
idêntico ao do clique — só que os três carrosséis de uma vez:

    saida/AAAA-MM/destaques/credito-privado/tivio-credito-privado-p01.jpg
    saida/AAAA-MM/destaques/credito-estruturado/...
    saida/AAAA-MM/destaques/investment-solutions/...

E um PDF por carrossel na mesma pasta, como o botão "Pacote PDF": uma página
por card, no tamanho do design (1080 x 1440 pt), renderizada em 4x (~288 DPI).
"""
import base64
import os
import re

from exporters.pdf import achar_chromium

POSTS = {
    'tivio-post-credito-privado.html': 'credito-privado',
    'tivio-post-credito-estruturado.html': 'credito-estruturado',
    'tivio-post-investment-solutions.html': 'investment-solutions',
}

# Renderiza cada .card da página pela função do próprio material e devolve
# [nome, jpg em base64]. Espera as bibliotecas e as imagens de fundo.
RENDERIZA = r"""
async (escala) => {
  if (window.__libsReady) { try { await window.__libsReady; } catch (e) {} }
  if (document.fonts && document.fonts.ready) { await document.fonts.ready; }
  const cards = [...document.querySelectorAll('.deck .card')];
  const out = [];
  for (const card of cards) {
    card.scrollIntoView();
    await new Promise(r => setTimeout(r, 250));
    const cv = await renderCard(card, escala || undefined);
    const blob = await canvasBlob(cv);
    const b64 = await new Promise(r => {
      const fr = new FileReader();
      fr.onload = () => r(String(fr.result).split(',')[1]);
      fr.readAsDataURL(blob);
    });
    out.push([card.dataset.name || card.id || 'card', b64]);
  }
  return out;
}
"""


ROTULOS = {'credito-privado': 'Crédito Privado', 'credito-estruturado': 'Crédito Estruturado',
           'investment-solutions': 'Investment Solutions'}


def exportar_destaques(pasta_central, destino, log, pasta_pdf=None, sufixo=''):
    """Grava os JPG de cada carrossel em destino/<vertical>/. Devolve a contagem.

    Com `pasta_pdf`, o pacote PDF de cada carrossel sai também lá (a pasta pdf/
    da edição, junto dos relatórios): "Destaques - Crédito Privado - Setembro 2026.pdf".
    """
    from playwright.sync_api import sync_playwright
    total = 0
    with sync_playwright() as p:
        op = {'args': ['--no-sandbox', '--font-render-hinting=none']}
        exe = achar_chromium()
        if exe:
            op['executable_path'] = exe
        nav = p.chromium.launch(**op)
        try:
            for arquivo, vertical in POSTS.items():
                origem = os.path.join(pasta_central, arquivo)
                if not os.path.exists(origem):
                    continue
                pg = nav.new_page(viewport={'width': 1440, 'height': 900})
                try:
                    pg.goto('file://' + os.path.abspath(origem), wait_until='load')
                    pg.wait_for_function("typeof renderCard === 'function'", timeout=20000)
                    pg.wait_for_timeout(800)
                    cartoes = pg.evaluate(RENDERIZA, None)
                    # o pacote PDF em 4x, como o botão (página 1080 x 1440 pt)
                    paginas_pdf = pg.evaluate(RENDERIZA, 4)
                except Exception as e:
                    log.aviso(arquivo, f'JPG dos destaques não gerado: {e!r}')
                    continue
                finally:
                    pg.close()
                pasta = os.path.join(destino, vertical)
                os.makedirs(pasta, exist_ok=True)
                for velho in os.listdir(pasta):          # só a edição atual
                    if velho.lower().endswith(('.jpg', '.pdf')):
                        os.remove(os.path.join(pasta, velho))
                for i, (nome, b64) in enumerate(cartoes, 1):
                    # posição na frente (01-, 02-…): o Explorer ordena na
                    # sequência do carrossel; o resto é o nome do card
                    nome = re.sub(r'-p\d+(-[a-z]+)?$', r'\1', nome)
                    caminho = os.path.join(pasta, f'{i:02d}-{nome}.jpg')
                    with open(caminho, 'wb') as f:
                        f.write(base64.b64decode(b64))
                    total += 1
                try:
                    import fitz
                    pdf = fitz.open()
                    for _, b64 in paginas_pdf:
                        pagina = pdf.new_page(width=1080, height=1440)
                        pagina.insert_image(pagina.rect, stream=base64.b64decode(b64))
                    pdf.save(os.path.join(pasta, f'tivio-destaques-{vertical}.pdf'), deflate=True)
                    if pasta_pdf:
                        os.makedirs(pasta_pdf, exist_ok=True)
                        nome_pdf = f'Destaques - {ROTULOS.get(vertical, vertical)}{sufixo}.pdf'
                        pdf.save(os.path.join(pasta_pdf, nome_pdf), deflate=True)
                        log.info(f'  PDF  pdf/{nome_pdf}')
                    pdf.close()
                except Exception as e:
                    log.aviso(arquivo, f'pacote PDF dos destaques não gerado: {e!r}')
                log.info(f'  JPG+PDF  destaques/{vertical}/ ({len(cartoes)} páginas)')
        finally:
            nav.close()
    return total
