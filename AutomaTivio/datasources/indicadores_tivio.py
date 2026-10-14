# -*- coding: utf-8 -*-
"""A fonte única dos números institucionais para todos os materiais.

    from datasources.indicadores_tivio import get_indicadores_tivio
    tivio = get_indicadores_tivio()

Chaves (as mesmas em HTML/Jinja, PDF e PPTX):
    anos_historia, aum_institucional, fundos, profissionais, data_ref,
    aum_investment_solutions, aum_credito, aum_credito_high_grade,
    aum_credito_estruturado, aum_imobiliario, aum_patrimoniais, aum_informativo

Em `aum_verticais_valores` vão os valores em R$ de cada vertical do JSON, para
gráficos (a rosca "AuM por vertical" dos decks).

Falha na API ou JSON ausente param a geração com a mensagem do motivo: a
rodada não usa número antigo sem avisar.
"""
import os

import yaml

from datasources.aum_verticais import get_aum_verticais
from datasources.big_numbers import get_big_numbers

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _forcados():
    """`forcar:` do configs/big_numbers.yml: correção manual que vence a fonte
    oficial enquanto ela está errada. Cada uso vira aviso no log da rodada."""
    caminho = os.path.join(RAIZ, 'configs', 'big_numbers.yml')
    if not os.path.exists(caminho):
        return {}
    with open(caminho, encoding='utf-8') as f:
        return (yaml.safe_load(f) or {}).get('forcar') or {}


def get_indicadores_tivio():
    try:
        gerais = get_big_numbers()
    except Exception as erro:
        raise RuntimeError(
            f"Falha ao consultar os indicadores públicos da Tivio: {erro}"
        ) from erro
    verticais = get_aum_verticais()

    ind = {
        # Indicadores públicos institucionais
        "anos_historia": gerais["anos_historia"],
        "aum_institucional": gerais["aum_institucional"],
        "fundos": gerais["fundos"],
        "profissionais": gerais["profissionais"],
        "data_ref": gerais["data_ref"],

        # AUMs por vertical do Informativo
        "aum_investment_solutions": verticais["investment_solutions"]["texto"],
        "aum_credito": verticais["credito"]["texto"],
        "aum_credito_high_grade": verticais["credito_high_grade"]["texto"],
        "aum_credito_estruturado": verticais["credito_estruturado"]["texto"],
        "aum_imobiliario": verticais["imobiliario"]["texto"],
        "aum_patrimoniais": verticais["patrimoniais"]["texto"],
        "aum_informativo": verticais["aum_informativo"]["texto"],

        # valores em R$ para gráficos
        "aum_verticais_valores": verticais["_verticais"],
        "aum_informativo_valor": verticais["aum_informativo"]["valor"],
    }

    # correções manuais: [(chave, valor da fonte, valor usado)]
    ind["_forcados"] = []
    for chave, valor in _forcados().items():
        if chave in ind and valor is not None:
            ind["_forcados"].append((chave, ind[chave], str(valor)))
            ind[chave] = str(valor)
    return ind
