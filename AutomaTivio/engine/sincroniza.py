# -*- coding: utf-8 -*-
"""O comentário do gestor sempre bate com a tabela de rentabilidade.

O gestor escreve os números à mão ("apresentou rentabilidade de 1,03% no mês
(95% do CDI), acumulando 10,44% (99% do CDI) no ano"). Se o texto vem de outro
mês, ou um número é digitado errado, o relatório publica uma frase que
contradiz a tabela logo acima dela.

Aqui, nas frases-padrão desses comentários, cada número é trocado pelo valor
calculado — no MESMO formato da tabela (`ContextoFundo.texto`). O resto do
texto não muda uma vírgula. Cada troca é devolvida para o log e a
conferência registrarem o que mudou.

Frases reconhecidas (o benchmark pode ser CDI, IMA-B 5, Ibovespa…):
  rentabilidade [, isenta de imposto de renda,] de X% no mês (Y% do CDI)
  obteve retorno de X% (Y% do CDI) no mês
  equivalente a Y% do CDI no período
  acumulando / acumula X% (Y% do CDI) no ano | em 2026
  acumula retorno de X%, frente a B% do CDI          (desde o início)
  desempenho de CDI + Z%                             (CDI+ desde o início)
  desempenho anualizado de W% do CDI
  alocação em crédito era de X%
  carrego da carteira encontra-se em CDI +X%, com duration média de D ano(s)
"""
import re

P = r'[-−]?\d{1,3}(?:\.\d{3})*(?:,\d+)?%'      # número com %
N = r'\d+(?:,\d+)?'                              # número sem %
B = r'(?:CDI|IMA-B\s?5|IPCA|Ibovespa|benchmark)'  # nome do benchmark


def _regras(ctx):
    """(regex, [(grupo, valor)]) — o grupo é trocado pelo valor."""
    t = ctx.texto
    anual = None
    try:
        from calculators import formatos as fmt
        v = ctx.pct_anualizado('inicio')
        anual = fmt.pct_cdi(v) if v is not None else None
    except Exception:
        pass
    r = [
        # "rentabilidade, isenta de imposto de renda, de X% no mês (Y% do CDI)"
        (rf'(rentabilidade[^.%]{{0,45}}?\bde\s)({P})(\s+no\s+m[êe]s)(?:(\s*\()({P})(\s+do\s+{B}\)))?',
         [(2, t('mes', 'fundo')), (5, t('mes', 'pct'))]),
        # "obteve retorno de X% (Y% do CDI) no mês"
        (rf'(retorno\s+de\s)({P})(\s*\()({P})(\s+do\s+{B}\)\s+no\s+m[êe]s)',
         [(2, t('mes', 'fundo')), (4, t('mes', 'pct'))]),
        # "equivalente a Y% do CDI no período"
        (rf'(equivalente\s+a\s)({P})(\s+do\s+{B}\s+no\s+per[íi]odo)',
         [(2, t('mes', 'pct'))]),
        # "acumulando X% (Y% do CDI) no ano" / "acumula X% (Y% do CDI) em 2026"
        (rf'(acumul(?:ando|a)\s)({P})(?:(\s*\()({P})(\s+do\s+{B}\)))?(\s+(?:no\s+ano|em\s+\d{{4}}))',
         [(2, t('ano', 'fundo')), (4, t('ano', 'pct'))]),
        # "acumula retorno de X%, frente a B% do CDI"
        (rf'(acumula\s+retorno\s+de\s)({P})(,\s+frente\s+a\s)({P})(\s+do\s+{B})',
         [(2, t('inicio', 'fundo')), (4, t('inicio', 'bench'))]),
        # "desempenho de CDI + Z%"
        (rf'(desempenho\s+de\s+{B}\s*\+\s*)({P})',
         [(2, t('inicio', 'bench_mais'))]),
        # "desempenho anualizado de W% do CDI"
        (rf'(anualizado\s+de\s)({P})(\s+do\s+{B})',
         [(2, anual)]),
    ]
    if getattr(ctx, 'cart', None):
        r += [
            (rf'(aloca[çc][ãa]o\s+em\s+cr[ée]dito\s+era\s+de\s)({P})',
             [(2, ctx.credito_fmt)]),
            (rf'(carrego\s+da\s+carteira\s+encontra-se\s+em\s+{B}\s*\+\s*)({P})',
             [(2, ctx.carrego_fmt)]),
            (rf'(duration\s+m[ée]dia\s+de\s)({N})(\s+anos?)',
             [(2, ctx.duration_fmt.split(' ')[0] if ctx.duration_fmt else None)]),
        ]
    return r


def _vazio(v):
    return v is None or str(v).strip() in ('', '-', '–', '—', '−')


def sincronizar(ctx, texto):
    """Devolve (texto, [(antes, depois)]) com os números das frases-padrão
    trocados pelos da tabela. Número sem valor calculado fica como está."""
    trocas = []
    if not texto:
        return texto, trocas
    for padrao, alvos in _regras(ctx):
        def troca(m):
            partes = list(m.groups())
            for g, valor in alvos:
                atual = partes[g - 1]
                if atual is None or _vazio(valor):
                    continue
                if atual != valor:
                    trocas.append((atual, valor))
                partes[g - 1] = valor
            return ''.join(x or '' for x in partes)
        texto = re.sub(padrao, troca, texto, flags=re.I)
    return texto, trocas
