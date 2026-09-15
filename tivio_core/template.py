# -*- coding: utf-8 -*-
"""Injecao de dados no template HTML e limpeza do cabecalho."""
import json
import re
from datetime import datetime


def injetar_array(html: str, nome: str, dados) -> str:
    """Troca `const <nome> = [...]` pelo array novo.

    Falha alto quando o marcador nao existe: um template sem o bloco
    geraria um dashboard silenciosamente vazio.
    """
    alvo = f"const {nome} = ["
    ini = html.find(alvo)

    if ini == -1:
        raise RuntimeError(f"bloco '{alvo}' nao encontrado no template")

    fim = html.find("];", ini)

    if fim == -1:
        raise RuntimeError(f"fim do bloco '{nome}' nao encontrado")

    js = json.dumps(dados, ensure_ascii=False)
    return html[:ini] + f"const {nome} = {js};" + html[fim + 2:]


def injetar_objeto(html: str, nome: str, dados: dict) -> str:
    """Mesma ideia de injetar_array, para `const <nome> = {...}`."""
    alvo = f"const {nome} = "
    ini = html.find(alvo)

    if ini == -1:
        return html

    fim = html.find("};", ini)

    if fim == -1:
        raise RuntimeError(f"fim do bloco '{nome}' nao encontrado")

    js = json.dumps(dados, ensure_ascii=False)
    return html[:ini] + alvo + js + ";" + html[fim + 2:]


def atualizar_data(html: str, quando: datetime = None) -> str:
    """Escreve dd/mm no selo ATUALIZADO do cabecalho."""
    quando = quando or datetime.now()

    return re.sub(
        r'(<div class="cdi-mini-lbl">ATUALIZADO</div>\s*'
        r'<div class="cdi-mini-val">)[^<]*(</div>)',
        lambda m: m.group(1) + quando.strftime("%d/%m") + m.group(2),
        html,
        count=1,
    )


# ------------------------------------------------------------------ menu
_BADGE = re.compile(
    r'\s*<span class="dash-tab-badge">[^<]*</span>'
)


def remover_badges_menu(html: str) -> tuple:
    """Tira os contadores do menu superior.

    Eram numeros fixos no HTML: cada atualizacao de qualquer dashboard
    exigia reescrever o contador em todos os outros arquivos a mao, e
    quando isso nao acontecia o menu passava a mentir. A regra CSS fica,
    para o dia em que forem preenchidos de forma automatica.
    """
    novo, n = _BADGE.subn("", html)
    return novo, n


def atualizar_contador(html: str, ancora: str, valor, antes: bool = False) -> tuple:
    """Troca o numero vizinho a um rotulo fixo do HTML.

    Existe pelo mesmo motivo de remover_badges_menu: o template traz
    totais escritos a mao ("218 ofertas") que nao acompanham o dado, e
    o dashboard passa a exibir dois numeros diferentes para a mesma
    coisa. Substituir o numero solto seria arriscado - por isso a troca
    e ancorada no texto ao lado.

    ancora  texto fixo que identifica o lugar (regex ja escapado por quem chama)
    antes   True quando o numero vem ANTES da ancora
    """
    if antes:
        padrao = re.compile(r"(\d[\d.,]*)(\s*" + ancora + ")")
        novo, n = padrao.subn(lambda m: f"{valor}{m.group(2)}", html)
    else:
        padrao = re.compile("(" + ancora + r"\s*)(\d[\d.,]*)")
        novo, n = padrao.subn(lambda m: f"{m.group(1)}{valor}", html)

    return novo, n
