# -*- coding: utf-8 -*-
"""E-mail de Fundos de Crédito exportado direto do Python, uma pasta por versão.

O Chromium abre o tivio-email-fundos-credito.html já gerado e, para cada versão
(Ágora, BTG, XP, Quadrado), troca a versão e chama as MESMAS funções do botão
"Baixar tudo": `renderCard` + `canvasBlob` (PNG de cada card e do e-mail
completo) e `emailExport` (o HTML pronto para disparo).

    saida/AAAA-MM/emails/agora/tivio-email-banks.png
    saida/AAAA-MM/emails/agora/tivio-email-completo.png
    saida/AAAA-MM/emails/agora/email-agora.html
    saida/AAAA-MM/emails/btg/...   xp/...   quadrado/...

Tema escuro, todos os fundos marcados (a caixa "Incluir" da página é uma
escolha de tela, não da edição).
"""
import base64
import os

from exporters.pdf import achar_chromium

ARQUIVO = 'tivio-email-fundos-credito.html'

VERSOES = r"""() => Object.keys(VERSIONS)"""

EXPORTA = r"""
async (ver) => {
  VER = ver;
  for (const k in SEL) delete SEL[k];
  buildDeck();
  if (typeof injectLightLogos === 'function') injectLightLogos();
  await new Promise(r => setTimeout(r, 600));
  if (typeof ensureLibs === 'function') await ensureLibs();
  const out = [];
  for (const c of CARDS) {
    const cv = await renderCard(c.el, c.full ? FULL_SCALE : PNG_SCALE);
    const blob = await canvasBlob(cv);
    const b64 = await new Promise(r => {
      const fr = new FileReader();
      fr.onload = () => r(String(fr.result).split(',')[1]);
      fr.readAsDataURL(blob);
    });
    out.push([c.el.dataset.name || c.id, b64]);
  }
  return { cards: out, html: emailExport() };
}
"""


def exportar_emails(pasta_central, destino, log):
    """Grava PNGs e HTML de cada versão em destino/<versao>/. Devolve a contagem."""
    origem = os.path.join(pasta_central, ARQUIVO)
    if not os.path.exists(origem):
        return 0
    from playwright.sync_api import sync_playwright
    total = 0
    with sync_playwright() as p:
        op = {'args': ['--no-sandbox', '--font-render-hinting=none']}
        exe = achar_chromium()
        if exe:
            op['executable_path'] = exe
        nav = p.chromium.launch(**op)
        try:
            pg = nav.new_page(viewport={'width': 1440, 'height': 900})
            pg.goto('file://' + os.path.abspath(origem), wait_until='load')
            pg.wait_for_function("typeof renderCard === 'function' && typeof buildDeck === 'function'",
                                 timeout=20000)
            pg.wait_for_timeout(800)
            for ver in pg.evaluate(VERSOES):
                try:
                    r = pg.evaluate(EXPORTA, ver)
                except Exception as e:
                    log.aviso(ARQUIVO, f'versão {ver} não exportada: {e!r}')
                    continue
                pasta = os.path.join(destino, ver)
                os.makedirs(pasta, exist_ok=True)
                for velho in os.listdir(pasta):            # só a edição atual
                    if velho.lower().endswith(('.png', '.html')):
                        os.remove(os.path.join(pasta, velho))
                for nome, b64 in r['cards']:
                    with open(os.path.join(pasta, f'{nome}.png'), 'wb') as f:
                        f.write(base64.b64decode(b64))
                    total += 1
                with open(os.path.join(pasta, f'email-{ver}.html'), 'w', encoding='utf-8') as f:
                    f.write(r['html'])
                log.info(f'  PNG+HTML  emails/{ver}/ ({len(r["cards"])} imagens)')
        finally:
            nav.close()
    return total
