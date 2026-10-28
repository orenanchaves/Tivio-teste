# -*- coding: utf-8 -*-
"""
patch_remover_abas.py · Analise · ETF · Tivio Capital

Remove do dashboard de ETF:

  1. Aba "Pipeline & Regulatorio"  (botao data-tab="5" + painel data-panel="5")
  2. Aba "Caminhos Tivio"          (botao data-tab="6" + painel data-panel="6")
  3. Na aba "Visao Geral", a linha final com os dois paineis estaticos:
        - "Timeline · Do ETF passivo ao ativo (EUA -> BR)"
        - "Destaques do mercado BR"

Tambem ajusta o subtitulo do cabecalho, que citava "Regulatorio" - secao que
deixa de existir.

O que NAO e tocado:
  - Abas 1 a 4 (Visao Geral, Peers & Gestoras, Benchmark de Taxas,
    Fluxo & Captacao)
  - Os blocos automatizados da Visao Geral (KPIs, contexto global,
    "Lancamentos & evolucao da classe", "Raio-X automatizado da base")
  - Design system, scripts, injecao de ETFS_DATA

Uso:
    python patch_remover_abas.py

Idempotente: rodar de novo apenas informa que nada resta a fazer.
Gera backup .bak na primeira execucao.
"""

import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent

# o template e a fonte; outputs/ e regerado pelo atualizar_etf.py
CANDIDATOS = [
    BASE / "templates" / "dashboard_etf.html",
    BASE / "dashboard_etf.html",
    BASE / "outputs" / "dashboard_etf.html",
]


# ----------------------------------------------------------------- utilidades
def fim_do_div(html: str, inicio: int) -> int:
    """
    Dado o indice de abertura de uma <div ...>, devolve o indice logo apos a
    </div> que a fecha, respeitando aninhamento.
    """
    i = inicio
    profundidade = 0
    n = len(html)

    while i < n:
        if html.startswith("<div", i) and (i + 4 < n) and html[i + 4] in " >\n\t":
            profundidade += 1
            i += 4
            continue
        if html.startswith("</div>", i):
            profundidade -= 1
            i += 6
            if profundidade == 0:
                return i
            continue
        i += 1

    raise ValueError("nao encontrei a </div> de fechamento")


def remover_bloco(html: str, marcador: str, rotulo: str) -> tuple:
    """Remove a div que comeca em `marcador` (string literal de abertura)."""
    pos = html.find(marcador)
    if pos == -1:
        return html, False

    fim = fim_do_div(html, pos)

    # engole espacos/quebras imediatamente anteriores, para nao deixar buraco
    ini = pos
    while ini > 0 and html[ini - 1] in " \t":
        ini -= 1
    if ini > 0 and html[ini - 1] == "\n":
        ini -= 1

    print(f"  - removido: {rotulo}")
    return html[:ini] + html[fim:], True


def remover_row_por_conteudo(html: str, texto_dentro: str, rotulo: str) -> tuple:
    """
    Remove a <div class="row two-col"> que CONTEM `texto_dentro`.
    Procura a ultima abertura de row antes da ocorrencia do texto.
    """
    alvo = html.find(texto_dentro)
    if alvo == -1:
        return html, False

    pos = html.rfind('<div class="row two-col">', 0, alvo)
    if pos == -1:
        return html, False

    fim = fim_do_div(html, pos)

    # seguranca: o bloco encontrado precisa mesmo conter o texto
    if texto_dentro not in html[pos:fim]:
        return html, False

    ini = pos
    while ini > 0 and html[ini - 1] in " \t":
        ini -= 1
    if ini > 0 and html[ini - 1] == "\n":
        ini -= 1

    print(f"  - removido: {rotulo}")
    return html[:ini] + html[fim:], True


def remover_linha(html: str, trecho: str, rotulo: str) -> tuple:
    """Remove a linha inteira que contem `trecho`."""
    pos = html.find(trecho)
    if pos == -1:
        return html, False

    ini = html.rfind("\n", 0, pos) + 1
    fim = html.find("\n", pos)
    fim = len(html) if fim == -1 else fim + 1

    print(f"  - removido: {rotulo}")
    return html[:ini] + html[fim:], True


# ---------------------------------------------------------------------- main
def aplicar(caminho: Path) -> bool:
    html = caminho.read_text(encoding="utf-8")
    original = html
    mudou = False

    print(f"\n[{caminho.name}]")

    # ---- 1. botoes das abas 5 e 6 -------------------------------------
    for tab, nome in (("5", "Pipeline & Regulatorio"), ("6", "Caminhos Tivio")):
        html, ok = remover_linha(
            html,
            f'<button class="tab-btn" data-tab="{tab}">',
            f'botao da aba "{nome}"',
        )
        mudou = mudou or ok

    # ---- 2. paineis das abas 5 e 6 ------------------------------------
    for painel, nome in (("5", "Pipeline & Regulatorio"), ("6", "Caminhos Tivio")):
        html, ok = remover_bloco(
            html,
            f'<div class="tab-panel" data-panel="{painel}">',
            f'painel da aba "{nome}"',
        )
        mudou = mudou or ok

    # ---- 3. row Timeline + Destaques, dentro da Visao Geral ------------
    html, ok = remover_row_por_conteudo(
        html,
        "Timeline · Do ETF passivo ao ativo",
        'row "Timeline" + "Destaques do mercado BR"',
    )
    mudou = mudou or ok

    # ---- 4. subtitulo do cabecalho ------------------------------------
    antigo = "Inteligência de mercado · Peers · Fluxo · Regulatório · Tivio"
    novo = "Inteligência de mercado · Peers · Fluxo · Taxas"
    if antigo in html:
        html = html.replace(antigo, novo)
        print("  - subtitulo ajustado (removida a mencao a Regulatorio)")
        mudou = True

    if not mudou:
        print("  [skip] nada a remover - o patch ja foi aplicado.")
        return False

    backup = caminho.with_suffix(".html.bak")
    if not backup.exists():
        shutil.copy2(caminho, backup)
        print(f"  [backup] {backup.name}")

    caminho.write_text(html, encoding="utf-8")

    delta = len(original) - len(html)
    print(f"  [ok] {delta:,} caracteres removidos.".replace(",", "."))
    return True


def main():
    alvos = [p for p in CANDIDATOS if p.exists()]

    if not alvos:
        print("[ERRO] nao encontrei dashboard_etf.html.")
        print("       esperado em templates/, na raiz ou em outputs/.")
        print("       rode o script dentro da pasta Update_ETF.")
        sys.exit(1)

    print("Remocao de abas · dashboard de ETF")
    print("-" * 46)

    for caminho in alvos:
        aplicar(caminho)

    print("\n" + "-" * 46)
    print("Concluido. Rode em seguida:  python atualizar_etf.py")


if __name__ == "__main__":
    main()
