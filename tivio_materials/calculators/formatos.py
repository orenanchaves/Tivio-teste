"""Formatação pt-BR usada nos materiais."""
import math

MINUS = '−'  # sinal de menos tipográfico usado nos materiais
MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho',
         'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
MES_ABR = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']


def _br(x, d):
    s = f'{abs(x):,.{d}f}'
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


def num(x, d=2, sinal=MINUS):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return MINUS
    return (sinal if x < 0 else '') + _br(x, d)


def pct(x, d=2):
    """0.0123 -> '1,23%'. None -> '−'."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return MINUS
    return num(x * 100, d) + '%'


def pct_cdi(x):
    """1.0123 (razão) -> '101%'."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return MINUS
    return num(x * 100, 0) + '%'


def brl(x):
    return 'R$ ' + _br(x, 2) if x is not None else MINUS


def brl_curto(x):
    if x is None:
        return MINUS
    if abs(x) >= 1e9:
        return 'R$ ' + _br(x / 1e9, 2) + ' bi'
    return 'R$ ' + _br(x / 1e6, 1) + ' mi'


def taxa(x, casas=None):
    """Taxa global: 2 casas; 3 casas quando a 3ª for significativa (ex.: 0,625%).

    `casas` força o número de casas (vem do override da planilha manual).
    """
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    v = x * 100
    if casas is None:
        casas = 2 if round(v, 2) == round(v, 6) else 3
    return _br(v, int(casas)) + '% a.a.'


def mes_ano(d):
    return f'{MESES[d.month - 1]} de {d.year}'


def slug(d):
    return f'{MES_ABR[d.month - 1]}{str(d.year)[2:]}'
