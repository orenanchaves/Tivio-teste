# -*- coding: utf-8 -*-
"""Gravação do HTML. Fino de propósito — a inteligência está nos renderizadores."""
import os


def gravar(html, destino, log=None):
    os.makedirs(os.path.dirname(destino) or '.', exist_ok=True)
    with open(destino, 'w', encoding='utf-8') as f:
        f.write(html)
    if log:
        log.gerado(destino, 'html')
    return destino
