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

O fluxo segue a skill html-to-pdf (github.com/aviz85/claude-skills-library):
Chrome headless, página A4 exata com escala 1 (quem encolhe a folha de
1000x1414 é o `zoom` do CSS, não o `scale` do PDF), fundo impresso, espera das
fontes, texto ajustado para caber, e o PDF gerado é CONFERIDO depois de
gravado: número de páginas esperado e texto selecionável. O comando avulso
no fim do arquivo converte qualquer HTML do mesmo jeito.

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
    def exportar(self, html, destino, largura=1000, altura=1414, origem=None,
                 esperadas=None, espera_ms=600):
        """Grava o PDF e devolve o caminho.

        `origem` é o HTML já gravado em disco. Quando existe, a página é aberta
        por `file://` em vez de `set_content`: só assim os caminhos relativos do
        documento (`vendor/echarts.min.js`) resolvem. Com `set_content` a página
        não tem URL base, e qualquer referência relativa falha — foi o que
        obrigou a embutir 1 MB de ECharts em cada relatório na primeira versão.

        Abrir o arquivo tem outra vantagem: o PDF sai do mesmo artefato que a
        pessoa abre no navegador, não de uma cópia em memória que poderia
        divergir dele.
        """
        os.makedirs(os.path.dirname(destino) or '.', exist_ok=True)
        pagina = self._browser.new_page(viewport={'width': largura, 'height': altura})
        try:
            if origem and os.path.exists(origem):
                pagina.goto('file://' + os.path.abspath(origem), wait_until='load')
            else:
                pagina.set_content(html, wait_until='load')
            if self.esperar_fonte:
                self._conferir_fonte(pagina, destino)
            self._esperar_graficos(pagina, destino)
            self._conferir_estouro(pagina, destino)
            pagina.emulate_media(media='print')
            # no modo impressão o texto que se ajusta à caixa (comentário,
            # disclaimer) é medido de novo, e só então imprime
            pagina.evaluate('window.tvAjustarTextos && window.tvAjustarTextos()')
            pagina.wait_for_timeout(espera_ms)
            self._conferir_enquadramento(pagina, destino)
            if esperadas is None:
                esperadas = pagina.evaluate("document.querySelectorAll('.rcard').length") or None
            pagina.pdf(path=destino, prefer_css_page_size=True, scale=1,
                       print_background=True, display_header_footer=False,
                       margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'})
        finally:
            pagina.close()
        self._conferir_pdf(destino, esperadas)
        return destino

    def _conferir_pdf(self, destino, esperadas):
        """Abre o PDF gravado e confere o que a skill html-to-pdf manda conferir.

        - número de páginas: uma folha a mais é página em branco, uma a menos é
          folha engolida — os dois saem sem erro nenhum do Chromium;
        - tamanho A4 (210 x 297 mm);
        - texto selecionável em todas as páginas: se uma página não tem texto,
          ela virou imagem (ou saiu em branco).
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            return   # sem pypdf a conferência fica para o olho
        nome = os.path.basename(destino)
        try:
            pdf = PdfReader(destino)
        except Exception as e:
            self.log.aviso(nome, f'não deu para reabrir o PDF gerado: {e!r}')
            return
        n = len(pdf.pages)
        if esperadas and n != esperadas:
            self.log.aviso(nome, f'{n} páginas no PDF, esperadas {esperadas} — '
                                 f'folha estourando (página a mais) ou sumindo')
        for i, pg in enumerate(pdf.pages, 1):
            w = float(pg.mediabox.width) / 72 * 25.4
            h = float(pg.mediabox.height) / 72 * 25.4
            if abs(w - 210) > 1 or abs(h - 297) > 1:
                self.log.aviso(nome, f'página {i} com {w:.0f} x {h:.0f} mm, não A4')
                break
        sem_texto = [i for i, pg in enumerate(pdf.pages, 1)
                     if len((pg.extract_text() or '').strip()) < 20]
        if sem_texto:
            self.log.aviso(nome, f'página(s) {sem_texto} sem texto selecionável — '
                                 f'saiu imagem ou em branco')

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

    # A4 a 96 dpi: 210 x 297 mm. É a caixa que o Chromium tem para imprimir.
    A4_LARGURA = 210 / 25.4 * 96      # 793,70 px
    A4_ALTURA = 297 / 25.4 * 96       # 1122,52 px

    def _conferir_enquadramento(self, pagina, destino):
        """Confere, já em modo impressão, que a folha cabe numa página A4.

        A folha é desenhada em 1000x1414 px e o CSS a reduz com `zoom`. Se essa
        regra deixar de valer — por um seletor de tela com especificidade maior,
        por exemplo — a folha volta ao tamanho cheio e cada uma estoura numa
        página em branco, ou perde a coluna da direita. O PDF continua sendo
        gerado sem erro nenhum: o defeito só aparece abrindo o arquivo. Medir
        aqui custa um `evaluate` e fecha esse buraco.
        """
        try:
            m = pagina.evaluate("""() => {
              const c = document.querySelector('.rcard');
              if (!c) { return null; }
              const r = c.getBoundingClientRect();
              return {l: r.width, a: r.height,
                      zoom: getComputedStyle(c).zoom,
                      n: document.querySelectorAll('.rcard').length};
            }""")
        except Exception:
            return
        if not m:
            return
        folga = 1.0
        if m['a'] > self.A4_ALTURA + folga or m['l'] > self.A4_LARGURA + folga:
            self.log.aviso(os.path.basename(destino),
                           f'a folha não cabe em A4 na impressão: '
                           f'{m["l"]:.0f}x{m["a"]:.0f}px contra '
                           f'{self.A4_LARGURA:.0f}x{self.A4_ALTURA:.0f}px '
                           f'(zoom {m["zoom"]}) — o PDF sai com página em branco '
                           f'entre as folhas, ou com a direita cortada')

    def _conferir_fonte(self, pagina, destino):
        """Espera a Versos e avisa se ela não chegou.

        `document.fonts.ready` resolve mesmo quando o download falhou, então ele
        sozinho não responde a pergunta. `check()` responde: ele diz se a família
        pedida está de fato disponível para desenhar.
        """
        try:
            pagina.wait_for_function('document.fonts.ready.then(()=>true)', timeout=15000)
            # 400 é o peso do corpo da folha; o 300 não é usado e nunca baixa
            ok = pagina.evaluate('document.fonts.check(\'400 16px Versos\')')
        except Exception as e:
            self.log.aviso(os.path.basename(destino), f'não deu para conferir a fonte: {e!r}')
            return
        if not ok:
            self.log.aviso(os.path.basename(destino),
                           'fonte Versos não carregou (CDN inacessível?) — o PDF sai '
                           'com a fonte de fallback e a métrica do texto muda')


# --------------------------------------------------------------------------
# Comando avulso — o equivalente do `html-to-pdf.js` da skill, para converter
# qualquer HTML no mesmo padrão (A4, sem margem, fundo, texto selecionável):
#
#   python -m exporters.pdf "relatorio.html" "relatorio.pdf"
#   python -m exporters.pdf "relatorio.html" "relatorio.pdf" --paginas=4
#
# Serve, por exemplo, para a página salva no navegador (Ctrl+S) depois de
# ajustar textos com "Editar textos".
# --------------------------------------------------------------------------
class _LogTerminal:
    def info(self, msg):
        print(msg)

    def aviso(self, onde, msg):
        print(f'AVISO [{onde}] {msg}')


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='HTML -> PDF A4 vetorial (Chromium headless)')
    ap.add_argument('entrada', help='arquivo .html')
    ap.add_argument('saida', nargs='?', help='arquivo .pdf (padrão: mesmo nome)')
    ap.add_argument('--paginas', type=int, default=None,
                    help='páginas esperadas (padrão: uma por folha .rcard)')
    ap.add_argument('--espera', type=int, default=600, help='ms de espera antes de imprimir')
    a = ap.parse_args(argv)
    saida = a.saida or os.path.splitext(a.entrada)[0] + '.pdf'
    log = _LogTerminal()
    with ExportadorPDF(log) as exp:
        exp.exportar(None, saida, origem=a.entrada, esperadas=a.paginas, espera_ms=a.espera)
    print(f'PDF: {saida}')


if __name__ == '__main__':
    main()
