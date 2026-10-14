# -*- coding: utf-8 -*-
"""Taxas dos fundos de previdência a partir da entrada/taxas_prev.xlsx.

A planilha tem um bloco por fundo, um embaixo do outro:

    HGD30:                                   <- título do bloco (coluna B)
                       Taxas a.a.
    Gestor | Fundo | Tipo | CNPJ | Administração | Gestão | Distribuição |
        Estruturação | Taxa Global Máxima | Performance | Custódia
    BRAM   | BRADESCO TIVIO HGD 30 ... | FIE I | 59.888.171/0001-41 | ...
    ...
                                    Taxa Final | 0,8%    <- soma dos veículos

O que sai daqui, por bloco:
  - `taxa_final`  a "Taxa Final" do bloco: a soma da Taxa Global Máxima dos
                  veículos (FIE I + FIE II + FIFE), que é a taxa global máxima
                  do fundo de previdência para o investidor. É a taxa dos decks
                  ("Taxa de Adm & Gestão", "Taxa Global"). A leitura confere a
                  soma e avisa se a célula "Taxa Final" não bate com ela.
  - `veiculos`    uma linha por veículo (FIE I, FIE II, FIFE), com as taxas
                  e a performance como texto.

Qual bloco é de qual fundo fica em configs/fundos.yml (`bloco_taxas_prev`).
A planilha muda pouco; quando um bloco novo entra (ex.: ZENIT), ele já aparece
aqui sem mexer no código.
"""
import re
import unicodedata

COLUNAS = {
    'gestor': 'Gestor', 'fundo': 'Fundo', 'tipo': 'Tipo', 'cnpj': 'CNPJ',
    'administracao': 'Administração', 'gestao': 'Gestão',
    'distribuicao': 'Distribuição', 'estruturacao': 'Estruturação',
    'taxa_global_maxima': 'Taxa Global Máxima', 'performance': 'Performance',
    'custodia': 'Custódia',
}


def _chave(t):
    """'TOP CREDIT:' -> 'TOPCREDIT'; 'Prev Imob' -> 'PREVIMOB'."""
    u = unicodedata.normalize('NFKD', str(t or '')).upper()
    u = ''.join(c for c in u if not unicodedata.combining(c))
    return re.sub(r'[^A-Z0-9]', '', u)


def _num(v):
    if isinstance(v, (int, float)):
        return float(v)
    return None


def ler_taxas_prev(caminho):
    """{CHAVE_DO_BLOCO: {'titulo', 'taxa_final', 'veiculos': [...]}}.

    Valor fora do padrão (ex.: custódia em reais no meio de percentuais) vira
    aviso em `avisos` do bloco, em vez de ser escondido.
    """
    import openpyxl
    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.worksheets[0]
    blocos, atual, cab = {}, None, None
    for linha in ws.iter_rows(values_only=True):
        cel = [c for c in linha]
        textos = [str(c).strip() if c is not None else '' for c in cel]
        if not any(textos):
            continue
        # título do bloco: um único texto na linha, terminado (ou não) em ':'
        preenchidas = [t for t in textos if t]
        if len(preenchidas) == 1 and not re.search(r'taxas', preenchidas[0], re.I) \
                and isinstance(next(c for c in cel if c is not None and str(c).strip()), str):
            titulo = preenchidas[0].rstrip(':').strip()
            atual = {'titulo': titulo, 'taxa_final': None, 'veiculos': [], 'avisos': []}
            blocos[_chave(titulo)] = atual
            cab = None
            continue
        if atual is None:
            continue
        if 'Gestor' in textos and 'Fundo' in textos:
            cab = {t: i for i, t in enumerate(textos) if t}
            continue
        # "Taxa Final" / "Taxa final" com o valor na célula ao lado
        for i, t in enumerate(textos):
            if re.fullmatch(r'taxa final', t, re.I) and i + 1 < len(cel):
                atual['taxa_final'] = _num(cel[i + 1])
        if cab and textos[cab.get('Fundo', 0)] and not any(
                re.fullmatch(r'taxa final', t, re.I) for t in textos):
            v = {}
            for k, rotulo in COLUNAS.items():
                i = cab.get(rotulo)
                v[k] = cel[i] if i is not None and i < len(cel) else None
            for k in ('administracao', 'gestao', 'distribuicao', 'estruturacao',
                      'taxa_global_maxima', 'custodia'):
                n = _num(v[k])
                if n is not None and n > 0.2:            # 20% a.a. não é taxa
                    atual['avisos'].append(
                        f'{v["tipo"]}: {COLUNAS[k]} = {v[k]} (fora do padrão de percentual)')
            atual['veiculos'].append(v)
    for b in blocos.values():
        soma = sum(_num(v['taxa_global_maxima']) or 0 for v in b['veiculos'])
        if b['taxa_final'] is None and soma:
            b['taxa_final'] = soma
        elif b['taxa_final'] is not None and abs(b['taxa_final'] - soma) > 0.00005:
            b['avisos'].append(f'Taxa Final {b["taxa_final"]:.4%} diferente da soma da '
                               f'Taxa Global Máxima dos veículos ({soma:.4%})')
    return blocos


class TaxasPrev:
    """Consulta pelo nome do bloco (`bloco_taxas_prev` do fundo em
    configs/fundos.yml: "HGD30", "LOW VOL", "TOP CREDIT"...)."""

    def __init__(self, blocos):
        self.blocos = blocos or {}

    def bloco(self, nome):
        return self.blocos.get(_chave(nome)) if nome else None

    def taxa_final(self, nome):
        b = self.bloco(nome)
        return b['taxa_final'] if b else None

    def avisos(self):
        return [(t, a) for t, b in self.blocos.items() for a in b['avisos']]
