# -*- coding: utf-8 -*-
"""Gravacao dos HTMLs gerados."""
from pathlib import Path


def gravar(html: str, destino: Path) -> Path:
    """Grava o HTML criando a pasta se precisar."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino


def copiar(origem: Path, destino: Path) -> Path:
    """Duplica um dashboard ja gerado (o principal costuma ser copia)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(origem.read_text(encoding="utf-8"), encoding="utf-8")
    return destino
