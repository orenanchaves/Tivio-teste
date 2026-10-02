# -*- coding: utf-8 -*-
"""HTML -> PDF vetorial, via Chromium headless.

"Não quero PDFs parecendo impressão de navegador." O que faz um PDF *parecer*
impressão de navegador não é o motor — é a configuração:

    cabeçalho e rodapé do navegador   -> display_header_footer=False
    margem padrão de 1 cm             -> margin=0 e @page{margin:0} no template
    fundo não impresso                -> print_background=True
    página no tamanho errado          -> @page{size:210mm 297mm} + prefer_css_page_size
    conteúdo cortado no meio          -> break-after:page por folha
    texto virando imagem              -> nenhuma rasterização: o texto do
                                         Chromium sai como texto no PDF, com a
                                         fonte incorporada

Com isso o PDF sai com texto selecionável, Versos embutida, vetor nas linhas do
gráfico e uma folha A4 por página — que é o que "qualidade institucional"
significa na prática.

A fonte vem de CDN. Sem rede, o Chromium cai para a fallback e o PDF sai com a
métrica errada — então esperamos a fonte carregar e avisamos quando ela não vem,
em vez de publicar um PDF com a tipografia trocada sem ninguém notar.
"""
import glob
import os

# O Playwright procura o Chromium por uma revisão fixa, embutida na versão do
# pacote. Quando o navegador já está instalado no sistema com outra revisão, o
# launch falha pedindo `playwright install` — mesmo havendo um Chromium
# perfeitamente utilizável ao lado. Em ambiente controlado (CI, container, a
# máquina do time) reinstalar não é opção, então apontamos o executável.
PADROES_CHROMIUM = [
    '/opt/pw-browsers/chromium-*/chrome-linux/chrome',
    '/opt/pw-browsers/chromium/chrome-linux/chrome',
    '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome',
    os.path.expanduser('~/.cache/ms-playwright/chromium-*/chrome-linux/chrome'),
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
]


def achar_chromium():
    """Primeiro executável existente, ou None para deixar o Playwright decidir."""
    if os.environ.get('TIVIO_CHROMIUM'):
        return os.environ['TIVIO_CHROMIUM']
    for padrao in PADROES_CHROMIUM:
        for caminho in sorted(glob.glob(padrao), reverse=True):
            if os.path.exists(caminho):
                return caminho
    return None


class ExportadorPDF:
    def __init__(self, log, esperar_fonte=True):
        self.log = log
        self.esperar_fonte = esperar_fonte
        self._pw = None
        self._browser = None

    # ----------------------------------------------------------- ciclo de vida
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        exe = achar_chromium()
        opcoes = {'args': ['--no-sandbox', '--font-render-hinting=none']}
        if exe:
            opcoes['executable_path'] = exe
            self.log.info(f'Chromium: {exe}')
        try:
            self._browser = self._pw.chromium.launch(**opcoes)
        except Exception as e:
            raise RuntimeError(
                f'não foi possível abrir o Chromium ({e}). Instale com '
                f'"python -m playwright install chromium" ou aponte o executável '
                f'na variável de ambiente TIVIO_CHROMIUM.') from e
        return self

    def __exit__(self, *e):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    # -------------------------------------------------------------- exportação
    def exportar(self, html, destino, largura=1000, altura=1414):
        """Grava o PDF e devolve o caminho. `html` é a string, não um arquivo."""
        os.makedirs(os.path.dirname(destino) or '.', exist_ok=True)
        pagina = self._browser.new_page(viewport={'width': largura, 'height': altura})
        try:
            pagina.set_content(html, wait_until='load')
            if self.esperar_fonte:
                self._conferir_fonte(pagina, destino)
            self._esperar_graficos(pagina, destino)
            self._conferir_estouro(pagina, destino)
            pagina.emulate_media(media='print')
            pagina.pdf(path=destino, prefer_css_page_size=True,
                       print_background=True, display_header_footer=False,
                       margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'})
        finally:
            pagina.close()
        return destino

    def _esperar_graficos(self, pagina, destino):
        """Só imprime depois que os gráficos desenharam.

        Sem isso o PDF pode sair com o gráfico pela metade — o Chromium imprime
        o DOM do instante, e o ECharts desenha depois do `load`.
        """
        try:
            pagina.wait_for_function('window.__tvCharts !== undefined', timeout=10000)
            estado = pagina.evaluate('window.__tvCharts')
        except Exception:
            return   # relatório sem gráfico nenhum
        if estado and not estado.get('ok'):
            self.log.aviso(os.path.basename(destino),
                           f'gráficos não renderizados ({estado.get("motivo")}) — '
                           f'o PDF sai com a versão SVG do servidor')
        elif estado and estado.get('desenhados', 0) < estado.get('total', 0):
            self.log.aviso(os.path.basename(destino),
                           f'{estado["total"] - estado["desenhados"]} de '
                           f'{estado["total"]} gráficos não desenharam')

    def _conferir_estouro(self, pagina, destino):
        """Avisa quando algum conteúdo passa do limite da folha.

        A folha tem `overflow:hidden`: o que passa some. É a pior falha
        possível num relatório — o texto do gestor truncado no meio, sem erro,
        sem aviso, e descoberto só depois de publicado. Então medimos.
        """
        try:
            sobras = pagina.evaluate("""() => {
              const out = [];
              document.querySelectorAll('.rcard').forEach((folha, i) => {
                const lim = folha.getBoundingClientRect();
                folha.querySelectorAll('.rc-body, .commentbox, .mkt, .featgrid, p')
                  .forEach(el => {
                    const r = el.getBoundingClientRect();
                    if (r.height > 0 && r.bottom > lim.bottom + 2) {
                      out.push({pagina: i + 1,
                                onde: (el.className || el.tagName).toString().slice(0, 40),
                                sobra: Math.round(r.bottom - lim.bottom)});
                    }
                  });
              });
              return out;
            }""")
        except Exception:
            return
        if not sobras:
            return
        pior = max(sobras, key=lambda s: s['sobra'])
        self.log.aviso(os.path.basename(destino),
                       f'conteúdo passa do fim da folha {pior["pagina"]} em '
                       f'{pior["sobra"]}px ({pior["onde"]}) — o PDF corta o excedente; '
                       f'reduzir o texto ou mover a seção de página')

    def _conferir_fonte(self, pagina, destino):
        """Espera a Versos e avisa se ela não chegou.

        `document.fonts.ready` resolve mesmo quando o download falhou, então ele
        sozinho não responde a pergunta. `check()` responde: ele diz se a família
        pedida está de fato disponível para desenhar.
        """
        try:
            pagina.wait_for_function('document.fonts.ready.then(()=>true)', timeout=15000)
            ok = pagina.evaluate('document.fonts.check(\'300 16px Versos\')')
        except Exception as e:
            self.log.aviso(os.path.basename(destino), f'não deu para conferir a fonte: {e!r}')
            return
        if not ok:
            self.log.aviso(os.path.basename(destino),
                           'fonte Versos não carregou (CDN inacessível?) — o PDF sai '
                           'com a fonte de fallback e a métrica do texto muda')
