# -*- coding: utf-8 -*-
"""Indicadores institucionais gerais, da API pública da Tivio.

    anos de história, patrimônio sob gestão, fundos, profissionais de
    investimentos e a data de referência.

Os valores vêm como a API escreve ("+25", "+32 bi", "+120", "+40"). Quem usa
decide como encaixar no material; ninguém reescreve o número.
"""
import requests

BIG_NUMBERS_URL = (
    "https://fa-publicapi-prod-brsouth-bafmhca7bhhua6h0."
    "brazilsouth-01.azurewebsites.net/big-numbers"
)


def get_big_numbers():
    response = requests.get(BIG_NUMBERS_URL, timeout=30)
    response.raise_for_status()

    dados = response.json()

    mapa = {
        item["title_en"]: item["value"]
        for item in dados
    }

    return {
        "anos_historia": mapa.get("Years of history"),
        "aum_institucional": mapa.get("Assets under management"),
        "fundos": mapa.get("Investment funds"),
        "profissionais": mapa.get("Investment professionals"),
        "data_ref": mapa.get("data_ref"),
    }
