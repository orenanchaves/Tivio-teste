# -*- coding: utf-8 -*-
"""
remover_aviso.py
----------------
Limpa dois elementos do dashboard Captação · Fundos Abertos:

  1) O banner  "Em breve / Público-alvo por fundo"   (bloco fixo no HTML)
  2) A seção   "Resumo · destaques do período"        (injetada por JavaScript)

Limpa OS DOIS arquivos de uma vez:
  - templates/dashboard_captacao_fundos_abertos.html  (fonte -> nunca mais volta)
  - outputs/dashboard_captacao_fundos_abertos.html     (o que voce ja gerou)

Rode:
    python remover_aviso.py
"""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent

ARQUIVOS = [
    BASE / "templates" / "dashboard_captacao_fundos_abertos.html",
    BASE / "outputs" / "dashboard_captacao_fundos_abertos.html",
]

# ------------------------------------------------------------------
# 1) Banner "Em breve / Público-alvo por fundo" (bloco fixo no HTML)
# ------------------------------------------------------------------
PADRAO_AVISO = re.compile(
    r'<div class="tv-note">\s*'
    r'<span class="tv-note-tag">Em breve</span>.*?'
    r'Público-alvo por fundo.*?'
    r'</div>\s*</div>',
    re.DOTALL,
)

# ------------------------------------------------------------------
# 2) Seção "Resumo · destaques do período" (injetada por JavaScript)
#    Neutraliza a IIFE que cria e anexa o painel na aba Visão Geral.
# ------------------------------------------------------------------
PADRAO_RESUMO = re.compile(
    r'/\*\s*-+\s*Visão Geral: destaques do Resumo\s*-+\s*\*/\s*'
    r'\(function\(\)\{.*?p1\.appendChild\(sec\);\s*\}\)\(\);',
    re.DOTALL,
)


def limpar(caminho: Path) -> None:
    if not caminho.exists():
        print(f"[skip] nao encontrado: {caminho}")
        return

    html = caminho.read_text(encoding="utf-8")

    html, n1 = PADRAO_AVISO.subn("", html)
    html, n2 = PADRAO_RESUMO.subn("", html)

    if n1 == 0 and n2 == 0:
        print(f"[ok]   nada a remover (ja limpo): {caminho.name}")
        return

    caminho.write_text(html, encoding="utf-8")
    print(f"[ok]   {caminho.name}: aviso={n1} | resumo={n2}")


if __name__ == "__main__":
    for arq in ARQUIVOS:
        limpar(arq)
    print("\nConcluido. Banner 'Em breve' e secao 'Resumo - destaques do periodo' removidos.")
