# -*- coding: utf-8 -*-
"""Endereço file:// que o Chromium consegue abrir, mesmo em pasta muito funda.

O Windows limita o caminho a 260 caracteres. O Python grava além disso (com
`LongPathsEnabled`), mas o Chromium não abre: o Playwright devolve
`net::ERR_FILE_NOT_FOUND` e o relatório sai sem PDF e com o PPTX "nativo".
Acontece quando o AutomaTivio está dentro de uma pasta comprida (OneDrive da
empresa + "Documentos" + subpastas + "AutomaTivio_v2 (3)"), e só nos fundos de
nome mais longo ("Tivio Infra Plus CDI - Relatório de Gestão - Setembro 2026").

A saída: abrir o arquivo por uma junção (atalho de pasta do Windows, sem
precisar de administrador) com nome curto em %TEMP%, apontando para a pasta
`saida/` ou, na falta dela, para a pasta do arquivo. A estrutura de pastas por
baixo é a mesma, então os caminhos relativos do HTML (vendor/, ../) seguem
valendo. Em pasta curta, nada muda.
"""
import atexit
import os
import subprocess
import tempfile
from urllib.parse import quote

LIMITE = 230          # folga abaixo dos 260: o caminho do arquivo + o do Chromium
_juncoes = {}         # pasta real -> junção curta


def _limpar():
    for atalho in _juncoes.values():
        try:
            os.rmdir(atalho)            # remove só a junção, nunca o destino
        except OSError:
            pass


atexit.register(_limpar)


def _juncao(pasta):
    if pasta in _juncoes and os.path.isdir(_juncoes[pasta]):
        return _juncoes[pasta]
    base = tempfile.mkdtemp(prefix='tv')
    atalho = os.path.join(base, 'a')
    r = subprocess.run(['cmd', '/c', 'mklink', '/J', atalho, pasta],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isdir(atalho):
        return None
    _juncoes[pasta] = atalho
    return atalho


def _url(caminho):
    return 'file:///' + quote(caminho.replace(os.sep, '/'), safe='/:')


def url_arquivo(origem):
    """file:// do arquivo `origem`, curto o bastante para o Chromium."""
    caminho = os.path.abspath(origem)
    if os.name != 'nt' or len(caminho) <= LIMITE:
        return _url(caminho)
    partes = caminho.split(os.sep)
    # sobe até a pasta "saida", para o HTML enxergar vendor/ e ../ como no original
    raiz = None
    for i in range(len(partes) - 1, 0, -1):
        if partes[i].lower() == 'saida':
            raiz = os.sep.join(partes[:i + 1])
            break
    raiz = raiz or os.path.dirname(caminho)
    atalho = _juncao(raiz)
    if atalho is None:
        return _url(caminho)            # sem junção: tenta o caminho cheio (vai avisar)
    return _url(os.path.join(atalho, os.path.relpath(caminho, raiz)))
