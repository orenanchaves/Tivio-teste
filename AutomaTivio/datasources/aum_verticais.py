# -*- coding: utf-8 -*-
"""AUM por vertical, do JSON exportado do Informativo Tivio.

O endpoint do Informativo (/api/home/summary) exige o login Microsoft
corporativo, então o AutomaTivio lê o último JSON exportado e salvo em
data/tivio_summary.json. O arquivo é interno e NÃO vai para o GitHub.

Regra dos cards:
    Investment Solutions = vertical["Investment Solutions"]
    Crédito              = vertical["Crédito High-Grade"] + vertical["Crédito Estruturado"]
    Imobiliário          = vertical["Imobiliário"]

Atenção: o AUM institucional público ("+32 bi", da API) e o AUM calculado no
Informativo (company.aum) são indicadores diferentes. Não trocar um pelo outro.
"""
import json
import os
from pathlib import Path

RAIZ = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAMINHO_PADRAO = RAIZ / "data" / "tivio_summary.json"


def formatar_bilhoes(valor):
    return f"R$ {valor / 1_000_000_000:.1f} bi".replace(".", ",")


def calcular_cards(summary):
    verticais = {
        item["name"]: float(item["aum"])
        for item in summary.get("vertical", [])
    }

    investment_solutions = verticais.get("Investment Solutions", 0)

    credito_high_grade = verticais.get("Crédito High-Grade", 0)
    credito_estruturado = verticais.get("Crédito Estruturado", 0)
    credito_total = credito_high_grade + credito_estruturado

    imobiliario = verticais.get("Imobiliário", 0)
    patrimoniais = verticais.get("Patrimoniais", 0)

    return {
        "investment_solutions": {
            "valor": investment_solutions,
            "texto": formatar_bilhoes(investment_solutions),
        },
        "credito": {
            "valor": credito_total,
            "texto": formatar_bilhoes(credito_total),
        },
        "credito_high_grade": {
            "valor": credito_high_grade,
            "texto": formatar_bilhoes(credito_high_grade),
        },
        "credito_estruturado": {
            "valor": credito_estruturado,
            "texto": formatar_bilhoes(credito_estruturado),
        },
        "imobiliario": {
            "valor": imobiliario,
            "texto": formatar_bilhoes(imobiliario),
        },
        "patrimoniais": {
            "valor": patrimoniais,
            "texto": formatar_bilhoes(patrimoniais),
        },
        "aum_informativo": {
            "valor": float(summary.get("company", {}).get("aum", 0)),
            "texto": formatar_bilhoes(
                float(summary.get("company", {}).get("aum", 0))
            ),
        },
        # todas as verticais do JSON, em R$ (a rosca dos decks usa estes)
        "_verticais": verticais,
    }


def carregar_summary(caminho=CAMINHO_PADRAO):
    caminho = Path(caminho)
    if not caminho.is_absolute():
        caminho = RAIZ / caminho

    if not caminho.exists():
        raise FileNotFoundError(
            "JSON do Informativo ausente. Atualize data/tivio_summary.json "
            f"(procurado em {caminho})."
        )

    with caminho.open(encoding="utf-8") as arquivo:
        return json.load(arquivo)


def get_aum_verticais(caminho=CAMINHO_PADRAO):
    summary = carregar_summary(caminho)
    return calcular_cards(summary)
