#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atualiza a edição mensal inteira da Central de Materiais.

    python run.py

Fluxo do mês:
    1. trocar entrada/dados_mensais.xlsx e entrada/taxas_global.xlsx
    2. escrever os comentários em entrada/comentarios.md
    3. python run.py
    4. conferir reports/AAAA-MM/conferencia_AAAA-MM.xlsx
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli.principal import main   # noqa: E402

if __name__ == '__main__':
    sys.exit(main())
