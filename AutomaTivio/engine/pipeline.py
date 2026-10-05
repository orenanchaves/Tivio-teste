# -*- coding: utf-8 -*-
"""O pipeline: planilha -> cálculo -> validação -> template -> exportação.

Uma rodada inteira da edição mensal. A ordem importa e não é arbitrária:

  1. ler as entradas
  2. resolver o cadastro contra a DePara
  3. calcular o contexto de cada fundo (uma vez; todos os materiais reusam)
  4. **validar** — antes de gerar, não depois
  5. gerar HTML, PDF e PPTX
  6. gravar conferência e log

A validação vem antes da geração de propósito. Validar depois produz o pior dos
mundos: arquivos prontos, bonitos, com número errado, já salvos na pasta de onde
alguém vai pegar para publicar. Com `parar_em_erro: true`, um erro grave
interrompe antes de escrever qualquer material.
"""
import os
import shutil

import pandas as pd
import yaml

from calculators.metricas import Calc
from engine.cadastro import Cadastro
from engine.contexto import Contexto
from engine.edicao import Edicao
from engine.governanca import Log
from exporters import html as exp_html
from loaders import comentarios as loader_comentarios
from loaders import spreads as loader_spreads
from loaders.planilha import ler_dados_mensais, ler_manual, ler_taxas
from loaders.taxas import Taxas
from renderers.legado import RenderizadorLegado
from renderers.relatorio import RenderizadorRelatorio
from validations.conferencia import Conferencia

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _caminho(p):
    return p if os.path.isabs(p) else os.path.join(RAIZ, p)


class Pipeline:
    def __init__(self, config='configs/edicao.yml', data_base=None, saidas=None,
                 so_fundos=None, eco=True):
        with open(_caminho(config), encoding='utf-8') as f:
            self.cfg = yaml.safe_load(f)
        self.data_base_forcada = data_base or self.cfg.get('data_base')
        if saidas:
            for k in self.cfg['saidas']:
                self.cfg['saidas'][k] = k in saidas
        self.so_fundos = set(so_fundos) if so_fundos else None
        self.eco = eco

    # --------------------------------------------------------------- entradas
    def _ler(self):
        ent = self.cfg['entradas']
        dados = ler_dados_mensais(_caminho(ent['dados']), log=self.log.info)
        calc = Calc(dados, self.data_base_forcada)
        self.edicao = Edicao(calc.db)
        self.log.competencia = self.edicao.competencia
        self.calc = calc

        self.cadastro = Cadastro(_caminho('configs/fundos.yml'), dados['depara'])
        self.manual = ler_manual(_caminho(ent.get('manual', '')))
        overrides = {}
        for _, r in self.manual.get('Overrides', pd.DataFrame()).iterrows():
            chave = str(r.get('chave') or '').strip()
            campo = str(r.get('campo') or '').strip()
            # linha começando com '#' é exemplo/comentário, não override. Sem
            # isso os exemplos da planilha entram como ajuste de verdade — e o
            # relatório sai com o carrego do exemplo.
            if not chave or not campo or chave.startswith('#'):
                continue
            overrides.setdefault(chave, {})[campo] = r['valor']
        self.taxas = Taxas(ler_taxas(_caminho(ent['taxas'])),
                           performance_fixa=self.cadastro.performance_fixa,
                           overrides=overrides)
        fontes = ent.get('comentarios', '')
        if isinstance(fontes, (list, tuple)):
            fontes = [_caminho(f) for f in fontes]
        else:
            fontes = _caminho(fontes)
        self.comentarios = loader_comentarios.carregar(fontes)
        self.log.contexto('mercado de crédito')
        self.spreads = loader_spreads.carregar(_caminho(ent.get('spreads', '')), self.log)
        self.log.contexto('—')

        self.log.info(f'data base: {self.edicao.br} ({self.edicao.mes_ano})')
        self.log.info(f'cadastro: {len(self.cadastro.fundos)} fundos, '
                      f'{sum(1 for f in self.cadastro if f.resolvido)} resolvidos na DePara')
        self.log.info(f'comentários: {len(self.comentarios)} fundos em '
                      f'{self.comentarios.origem}')
        for key, msg in self.cadastro.nao_resolvidos:
            self.log.aviso(key, msg)

        self.contexto = Contexto(calc, self.cadastro, self.taxas, self.comentarios,
                                 self.edicao, self.log, overrides)

    # ------------------------------------------------------------------ saída
    @property
    def pasta_saida(self):
        return os.path.join(RAIZ, 'saida', self.edicao.competencia)

    def _destino(self, *partes):
        return os.path.join(self.pasta_saida, *partes)

    # ------------------------------------------------------------------ etapas
    def _validar(self, contextos):
        self.log.etapa('3/6 Validando')
        self.conf = Conferencia(self.edicao, self.log, self.spreads)
        for ctx in contextos:
            self.conf.checar(ctx)
        self.log.info(self.conf.resumo)
        return self.conf

    def _relatorios(self, contextos):
        """O produto principal: um relatório por fundo, nos três formatos."""
        self.log.etapa('4/6 Relatórios de Gestão')
        rend = RenderizadorRelatorio(self.edicao, self.cadastro, self.manual, self.log,
                                     spreads=self.spreads)
        alvo = [c for c in contextos if c.f.tem_relatorio]
        if self.so_fundos:
            alvo = [c for c in alvo if c.key in self.so_fundos]

        htmls = {}
        for ctx in alvo:
            self.log.contexto(f'relatorio/{ctx.key}')
            if not ctx.tem_dados:
                self.log.aviso(ctx.key, 'relatório não gerado: sem dados nesta edição')
                continue
            try:
                html = rend.html(ctx)
            except Exception as e:
                self.log.erro(ctx.key, f'falha ao montar o relatório: {e!r}')
                continue
            # O HTML de um fundo é gravado numa pasta de apoio: o PDF e o PPTX
            # saem dele (por file://, para o vendor/ resolver), mas o que é
            # entregue são as páginas por vertical, logo abaixo.
            destino = self._destino('relatorios', '_fundos',
                                    self.edicao.nome_arquivo(
                                        f'{ctx.nome} - Relatório de Gestão', 'html'))
            exp_html.gravar(html, destino, None)
            htmls[ctx.key] = (ctx, html, destino, False)

        self._pdf_e_pptx(htmls, rend)
        self._paginas_por_vertical(htmls, rend)

        # a pasta de apoio existiu só para o PDF sair de um arquivo
        apoio = self._destino('relatorios', '_fundos')
        if os.path.isdir(apoio):
            shutil.rmtree(apoio, ignore_errors=True)
        return htmls

    def _paginas_por_vertical(self, htmls, rend):
        """Uma página por vertical, com os fundos em abas — o que é entregue."""
        self.relatorios_gerados = []
        if not self.cfg['saidas'].get('html'):
            return

        por_vert = {}
        for ctx, _, _, _ in htmls.values():
            por_vert.setdefault(ctx.f.vertical, []).append(ctx)

        # as páginas se apontam umas às outras: a troca de vertical no topo
        # leva de Crédito Privado para Crédito Estruturado sem voltar à Central
        ordem = list(self.cadastro.verticais)
        irmas = []
        for v in sorted(por_vert, key=lambda v: ordem.index(v) if v in ordem else len(ordem)):
            rot = (self.cadastro.verticais.get(v) or {}).get('rotulo', v)
            irmas.append((v, rot, self.edicao.nome_arquivo(f'Relatório de Gestão - {rot}', 'html')))

        for vertical, ctxs in por_vert.items():
            rotulo = (self.cadastro.verticais.get(vertical) or {}).get('rotulo', vertical)
            self.log.contexto(f'relatorio/{vertical}')
            try:
                html = rend.html_vertical(ctxs, vertical, irmas)
            except Exception as e:
                self.log.erro(vertical, f'falha ao montar a página da vertical: {e!r}')
                continue
            nome = self.edicao.nome_arquivo(f'Relatório de Gestão - {rotulo}', 'html')
            destino = self._destino('relatorios', nome)
            exp_html.gravar(html, destino, self.log)
            self.relatorios_gerados.append((rotulo, ctxs, nome))

    def _pdf_e_pptx(self, htmls, rend):
        if not htmls:
            return
        quer_pdf = self.cfg['saidas'].get('pdf')
        quer_pptx = self.cfg['saidas'].get('pptx')
        if not (quer_pdf or quer_pptx):
            return

        from exporters.pdf import ExportadorPDF
        from exporters.pptx import ExportadorPPTX

        # o vendor/ precisa existir antes de abrir o HTML por file://
        self._copiar_libs()

        pptx = ExportadorPPTX(self.log)
        with ExportadorPDF(self.log) as pdf:
            for key, (ctx, html, arquivo, _) in htmls.items():
                self.log.contexto(f'relatorio/{key}')
                base = f'{ctx.nome} - Relatório de Gestão'
                if quer_pdf:
                    try:
                        destino = self._destino('pdf', self.edicao.nome_arquivo(base, 'pdf'))
                        pdf.exportar(html, destino, origem=arquivo)
                        self.log.gerado(destino, 'pdf')
                    except Exception as e:
                        self.log.erro(key, f'PDF não gerado: {e!r}')
                if quer_pptx:
                    try:
                        destino = self._destino('pptx', self.edicao.nome_arquivo(base, 'pptx'))
                        pptx.nativo(ctx, rend, destino)
                        self.log.gerado(destino, 'pptx')
                    except Exception as e:
                        # o nativo é o desejado; a imagem garante que o usuário
                        # recebe o arquivo mesmo quando um bloco não se reconstrói
                        self.log.aviso(key, f'PPTX nativo falhou ({e!r}) — caindo '
                                            f'para slide-imagem')
                        try:
                            destino = self._destino('pptx',
                                                    self.edicao.nome_arquivo(base, 'pptx'))
                            pptx.imagem(html, destino, pdf._browser, origem=arquivo)
                            self.log.gerado(destino, 'pptx')
                        except Exception as e2:
                            self.log.erro(key, f'PPTX não gerado: {e2!r}')

    # bibliotecas que cada pasta de saída precisa ter ao lado dos HTMLs
    LIBS_POR_PASTA = {
        ('central',): ('html2canvas.min.js', 'jszip.min.js', 'jspdf.umd.min.js',
                       'echarts.min.js'),
        # echarts entra aqui desde que o relatório deixou de embuti-lo: sem ele
        # na pasta, o <script src="vendor/echarts.min.js"> do HTML dá 404 e o
        # gráfico cai na versão SVG do servidor
        ('relatorios',): ('echarts.min.js', 'html2canvas.min.js', 'jszip.min.js',
                          'jspdf.umd.min.js', 'pptxgen.min.js'),
        # o HTML de apoio de cada fundo (de onde saem o PDF e o PPTX) fica um
        # nível abaixo, e `vendor/…` é relativo ao arquivo: sem um vendor/ ao
        # lado dele o Chromium não acha o echarts e o PDF sai com a versão SVG
        # do servidor em vez do gráfico desenhado
        ('relatorios', '_fundos'): ('echarts.min.js',),
    }

    def _copiar_libs(self):
        """Leva as bibliotecas dos botões para junto dos HTMLs.

        Sem isso o `vendor/…` que o HTML referencia daria 404 e tudo cairia no
        CDN — ou seja, a correção não valeria nada. São duas pastas porque os
        relatórios e os materiais da Central ficam separados, e cada um precisa
        do `vendor/` ao seu lado.
        """
        origem = os.path.join(RAIZ, 'assets', 'vendor')
        if not os.path.isdir(origem):
            self.log.aviso('—', 'assets/vendor não existe — os botões dependerão do CDN')
            return
        for partes, arquivos in self.LIBS_POR_PASTA.items():
            pasta = '/'.join(partes)
            alvo = self._destino(*partes)
            if not os.path.isdir(alvo):
                continue     # material desligado nesta edição
            destino = os.path.join(alvo, 'vendor')
            os.makedirs(destino, exist_ok=True)
            copiados = 0
            for arq in arquivos:
                caminho = os.path.join(origem, arq)
                if os.path.exists(caminho):
                    shutil.copy2(caminho, os.path.join(destino, arq))
                    copiados += 1
            faltam = [a for a in arquivos
                      if not os.path.exists(os.path.join(origem, a))]
            if faltam:
                self.log.aviso('—', f'{pasta}/: faltam em assets/vendor {faltam} — '
                                    f'esses botões dependerão do CDN')
            if copiados:
                self.log.info(f'  {copiados} bibliotecas copiadas para {pasta}/vendor/')

    def _materiais_legados(self):
        self.log.etapa('5/6 Materiais da Central')
        quais = self.cfg.get('materiais', {})
        mapa = {
            'tivio-post-credito-estruturado.html': 'post_credito_estruturado',
            'tivio-post-credito-privado.html': 'post_credito_privado',
            'tivio-post-investment-solutions.html': 'post_investment_solutions',
            'tivio-email-fundos-credito.html': 'email_fundos_credito',
            'tivio-central.html': 'central',
            'tivio-relatorio-gestao-credito-privado.html': 'relatorio_gestao',
            'tivio-email-nordea-studio.html': 'email_nordea',
            'tivio-construtor-one-pager.html': 'one_pager',
        }
        rend = RenderizadorLegado(self.contexto, self.cadastro, self.edicao,
                                  self.comentarios, self.manual, self.log,
                                  relatorios=getattr(self, 'relatorios_gerados', []),
                                  pasta_saida=self.pasta_saida)
        pasta = os.path.join(RAIZ, 'templates', 'materiais')
        if not os.path.isdir(pasta):
            self.log.aviso('—', f'templates/materiais não existe — nada a atualizar')
            return
        # A Central é processada POR ÚLTIMO: ela confere quais arquivos a
        # edição produziu para montar o índice, e em ordem alfabética viria
        # primeiro — olharia uma pasta vazia e julgaria todos os links mortos.
        arquivos = sorted(n for n in os.listdir(pasta) if n.endswith('.html'))
        arquivos.sort(key=lambda n: n == 'tivio-central.html')

        for nome in arquivos:
            chave = mapa.get(nome)
            # Material desligado nesta edição é COPIADO sem atualizar, não
            # pulado: a Central aponta para ele, e um arquivo ausente vira link
            # morto no índice. "Desligado" quer dizer "não recebe os dados do
            # mês" (o Nordea e o One Pager têm schema próprio), não "some".
            atualiza = not (chave and not quais.get(chave, True))
            self.log.contexto(nome)
            original = open(os.path.join(pasta, nome), encoding='utf-8').read()
            if not atualiza:
                novo = original
                self.log.info(f'  {nome} copiado sem atualizar (desligado em '
                              f'configs/edicao.yml)')
            else:
                try:
                    novo = rend.processar(nome, original)
                except Exception as e:
                    self.log.erro(nome, f'{e!r} — copiado sem alteração')
                    novo = original
            destino = self._destino('central', nome)
            exp_html.gravar(novo, destino, self.log)
            if atualiza and novo == original and chave:
                self.log.aviso(nome, 'nenhuma alteração aplicada — conferir se as '
                                     'chaves do material batem com configs/fundos.yml')

    # ------------------------------------------------------------------ rodada
    def rodar(self):
        self.log = Log(os.path.join(RAIZ, 'logs'), 'edicao', eco=self.eco)
        self.log.etapa('1/6 Lendo entradas')
        self._ler()

        self.log.etapa('2/6 Calculando')
        keys = [f.key for f in self.cadastro]
        contextos = self.contexto.todos(keys)
        com_dados = [c for c in contextos if c.tem_dados]
        self.log.info(f'{len(com_dados)} de {len(contextos)} fundos com dados nesta edição')

        self._validar(contextos)

        if self.cfg.get('parar_em_erro') and not self.log.ok:
            self.log.etapa('PARADO: há erros; nada foi publicado')
            self._fechar(contextos)
            return False

        if self.cfg.get('materiais', {}).get('relatorio_gestao', True):
            self._relatorios(contextos)
        self._materiais_legados()
        self._copiar_libs()
        self._fechar(contextos)
        return self.log.ok

    def _fechar(self, contextos):
        self.log.etapa('6/6 Conferência e log')
        self.log.contexto('—')
        destino = self._destino(f'conferencia_{self.edicao.competencia}.xlsx')
        self.conf.gravar(contextos, self.cadastro, self.taxas, destino)
        self.log.gerado(destino, 'xlsx')
        caminho = self.log.gravar()
        # o log também vai para a pasta da edição, junto do material
        try:
            shutil.copy2(caminho, self._destino(os.path.basename(caminho)))
        except Exception:
            pass
