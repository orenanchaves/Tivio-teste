#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atualiza a edição mensal inteira da Central de Materiais.

    python run.py

Fluxo do mês:
    1. trocar entrada/dados_mensais.xlsx, taxas_global.xlsx e tabela_spreads.xlsx
    2. escrever os comentários em entrada/comentarios.docx
    3. python run.py
    4. conferir saida/AAAA-MM/conferencia_AAAA-MM.xlsx
"""
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

# Pacote importado -> nome no pip. Os dois diferem com frequência, e é essa
# diferença que torna o erro padrão do Python inútil para quem não programa:
# "No module named 'yaml'" não diz que o pacote se chama PyYAML.
DEPENDENCIAS = [
    ('pandas', 'pandas'),
    ('numpy', 'numpy'),
    ('openpyxl', 'openpyxl'),
    ('yaml', 'PyYAML'),
    ('jinja2', 'Jinja2'),
    ('pptx', 'python-pptx'),
]


def conferir_dependencias():
    """Lista o que falta e diz o comando, em vez de estourar um traceback."""
    import importlib.util
    faltando = [pip for mod, pip in DEPENDENCIAS
                if importlib.util.find_spec(mod) is None]
    if not faltando:
        return
    print()
    print('  Faltam dependências para rodar:')
    print()
    for pip in faltando:
        print(f'      · {pip}')
    print()
    print('  Instale com (nesta mesma pasta):')
    print()
    print('      python -m pip install -r requirements.txt')
    print()
    print('  E, se for gerar PDF e PPTX, uma vez só:')
    print()
    print('      python -m playwright install chromium')
    print()
    sys.exit(1)


if __name__ == '__main__':
    conferir_dependencias()
    from cli.principal import main   # noqa: E402  (depois da conferência)
    sys.exit(main())
