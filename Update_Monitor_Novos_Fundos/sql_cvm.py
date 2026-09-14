# -*- coding: utf-8 -*-
"""
sql_cvm.py - resolve os marcadores do bloco opcional do cadastro da CVM
em sql/monitor_fundos_v2.sql.

O cadastro da CVM vive num catalogo restrito que hoje devolve
[INSUFFICIENT_PERMISSIONS]. Enquanto o acesso nao volta, a query precisa
rodar sem ele; quando voltar, basta preencher CVM_CADASTRO no .env.

Marcadores suportados:

    -- {{CVM_INI}}   trecho usado SO com o cadastro disponivel
    -- {{CVM_ELSE}}  alternativa usada sem o cadastro  (opcional)
    -- {{CVM_FIM}}

Sem CVM_ELSE o trecho e simplesmente removido quando nao ha cadastro.
"""
import re

INI = r"^[ \t]*--[ \t]*\{\{CVM_INI\}\}[ \t]*\n"
ELS = r"^[ \t]*--[ \t]*\{\{CVM_ELSE\}\}[ \t]*\n"
FIM = r"^[ \t]*--[ \t]*\{\{CVM_FIM\}\}[ \t]*\n"

_BLOCO = re.compile(
    INI + r"(?P<com>.*?)" + r"(?:" + ELS + r"(?P<sem>.*?))?" + FIM,
    re.DOTALL | re.MULTILINE,
)


def resolver(sql: str, com_cadastro: bool) -> str:
    """Escolhe o ramo de cada bloco marcado e remove os marcadores."""
    def troca(m):
        return m.group("com") if com_cadastro else (m.group("sem") or "")

    return _BLOCO.sub(troca, sql)


def montar(sql: str, cvm_tabela: str | None) -> str:
    """Resolve os blocos e injeta o nome da tabela do cadastro."""
    pronto = resolver(sql, bool(cvm_tabela))

    if cvm_tabela:
        pronto = pronto.replace("{cvm_tabela}", cvm_tabela)

    return pronto
