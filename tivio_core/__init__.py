# -*- coding: utf-8 -*-
"""
tivio_core - o que todo ambiente de dashboard da Tivio repete.

Cada pasta Update_* seguia o mesmo roteiro copiado e colado: conectar no
Databricks, ler um .sql, injetar um array JS no template, gravar o HTML.
Isso multiplicava por cinco cada correcao - o bug do recorte de ano, por
exemplo, existia em mais de um lugar.

Aqui fica a parte comum. Cada ambiente mantem so o que e proprio dele:
o SQL, o mapeamento para as colunas do template e as metricas.

Uso tipico:

    from tivio_core import db, template, saida

    df = db.consultar(sql, mock=meu_mock)
    html = template.injetar(base, "FUNDS_DATA", linhas)
    saida.gravar(html, Path("outputs/dashboard.html"))
"""
from . import db, template, saida, validacao   # noqa: F401

__all__ = ["db", "template", "saida", "validacao"]
