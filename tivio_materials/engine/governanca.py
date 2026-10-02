# -*- coding: utf-8 -*-
"""Log da execução: o que mudou, o que faltou, o que deu erro.

O pedido era um log por edição com arquivos atualizados, campos alterados, erros
e dados faltantes. É o mesmo registro que alimenta a conferencia.xlsx, então
mora num lugar só: o `Log` acumula em memória durante a rodada, escreve o
.log no fim, e a conferência lê daqui em vez de recalcular.

Distinção que importa na prática:

    mudanca  — um campo trocou de valor. É o esperado; serve para auditar.
    aviso    — o material saiu, mas há algo a revisar (dado faltando, texto
               citando outro mês). Não impede publicar.
    erro     — o material não pôde ser gerado. Com `parar_em_erro`, a rodada
               termina sem publicar.
"""
import os
from datetime import datetime


class Log:
    def __init__(self, pasta, competencia, eco=True):
        self.pasta = pasta
        self.competencia = competencia
        self.eco = eco
        self.mudancas = []     # (arquivo, fundo, campo, antes, depois)
        self.avisos = []       # (arquivo, fundo, mensagem)
        self.erros = []        # (arquivo, fundo, mensagem)
        self.arquivos = []     # (arquivo, formato, bytes)
        self.linhas = []
        self._arquivo_atual = '—'
        self.inicio = datetime.now()
        self._p(f'=== Central de Materiais · edição {competencia} '
                f'· {self.inicio:%d/%m/%Y %H:%M:%S} ===')

    # ----------------------------------------------------------------- escrita
    def _p(self, txt, nivel=''):
        linha = f'{datetime.now():%H:%M:%S} {nivel:<5} {txt}'.rstrip()
        self.linhas.append(linha)
        if self.eco:
            print(('  ' + txt) if not nivel else f'  {nivel:<5} {txt}')

    def contexto(self, arquivo):
        """Define o arquivo ao qual os próximos registros pertencem."""
        self._arquivo_atual = arquivo
        return self

    def etapa(self, txt):
        self._p('')
        self._p(txt)

    def info(self, txt):
        self._p(txt)

    def mudanca(self, fundo, campo, antes, depois):
        self.mudancas.append((self._arquivo_atual, fundo, campo, str(antes), str(depois)))

    def aviso(self, fundo, msg):
        self.avisos.append((self._arquivo_atual, fundo, msg))
        self._p(f'[{fundo}] {msg}', 'AVISO')

    def erro(self, fundo, msg):
        self.erros.append((self._arquivo_atual, fundo, msg))
        self._p(f'[{fundo}] {msg}', 'ERRO')

    def gerado(self, caminho, formato):
        tam = os.path.getsize(caminho) if os.path.exists(caminho) else 0
        self.arquivos.append((os.path.basename(caminho), formato, tam))
        self._p(f'{formato.upper():<4} {os.path.basename(caminho)} '
                f'({tam / 1024:.0f} KB)')

    # ------------------------------------------------------------------- fecho
    @property
    def ok(self):
        return not self.erros

    def resumo(self):
        dur = (datetime.now() - self.inicio).total_seconds()
        return (f'{len(self.arquivos)} arquivos · {len(self.mudancas)} alterações · '
                f'{len(self.avisos)} avisos · {len(self.erros)} erros · {dur:.0f}s')

    def gravar(self):
        os.makedirs(self.pasta, exist_ok=True)
        self._p('')
        self._p('=== ' + self.resumo() + ' ===')
        caminho = os.path.join(self.pasta, f'{self.competencia}-processamento.log')
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.linhas) + '\n')
        return caminho
