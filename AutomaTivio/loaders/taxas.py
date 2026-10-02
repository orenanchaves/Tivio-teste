"""Taxas a partir da taxas_global.xlsx.

Regras:
- Taxa exibida = coluna 'Taxa Global' (sem custódia).
- 2 casas decimais; 3 casas quando a 3ª é significativa (0,625% · 0,695% ·
  0,995% · 0,325% · 0,277%). Para forçar: override `casas_taxa`.
- Taxa de performance vem da planilha, exceto nos fundos marcados com
  `performance_fixa: true` em configs/fundos.yml (hoje ALT 180 e ALT 90), que
  mantêm o texto atual.
"""
import re

from calculators import formatos as fmt


def _cnpj(s):
    return re.sub(r'\D', '', str(s)).zfill(14)


def _perf_texto(v):
    v = str(v or '').strip()
    if not v or v in ('-', 'nan', 'None'):
        return 'Não há'
    v = re.sub(r'\s+', ' ', v)
    v = re.sub(r'^(\d+(?:,\d+)?%)\s+exceder\s+', r'\1 do que exceder ', v)
    return v[0].upper() + v[1:]


class Taxas:
    def __init__(self, df, performance_fixa=(), overrides=None):
        self.df = df
        # quais fundos mantêm o texto de performance atual (vem de fundos.yml,
        # não mais de uma constante no código)
        self.fixa = set(performance_fixa)
        self.ov = overrides or {}

    def linha(self, cnpj, nome=None):
        r = self.df[self.df['cnpj_num'] == _cnpj(cnpj)]
        if len(r) > 1 and nome:
            r2 = r[r['Fundo'].str.upper() == nome.upper()]
            r = r2 if len(r2) else r
        if len(r) > 1:  # prefere a classe "cheia" (sem SUB/CLASSE/SEN/MEZ)
            r2 = r[~r['Fundo'].str.contains(r'\b(SUB|CLASSE|SEN|MZ|MEZ|CONS)\b', regex=True)]
            r = r2 if len(r2) else r
        return r.iloc[0] if len(r) else None

    def global_(self, key, cnpj, nome=None):
        r = self.linha(cnpj, nome)
        if r is None or r['Taxa Global'] != r['Taxa Global']:
            return None
        casas = self.ov.get(key, {}).get('casas_taxa')
        return fmt.taxa(float(r['Taxa Global']), int(casas) if casas else None)

    def performance(self, key, cnpj, atual=None, nome=None):
        if key in self.fixa:
            return atual
        r = self.linha(cnpj, nome)
        return _perf_texto(r['Taxa de Performance']) if r is not None else atual
