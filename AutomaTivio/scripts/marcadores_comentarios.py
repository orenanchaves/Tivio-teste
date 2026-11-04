"""Troca os números de rentabilidade digitados nos comentários pelos marcadores.

    python scripts/marcadores_comentarios.py              # só mostra o que mudaria
    python scripts/marcadores_comentarios.py --gravar     # grava (com cópia .bak)
    python scripts/marcadores_comentarios.py --arquivo outro.md

O gestor escreve "apresentou rentabilidade de 1,03% no mês (95% do CDI),
acumulando 10,44% (99% do CDI) no ano". Este script deixa a frase como

    apresentou rentabilidade de {mes} no mês ({pct_mes} do CDI),
    acumulando {ano} ({pct_ano} do CDI) no ano

e o run.py encaixa os números do mês (engine/contexto.py::preencher). O texto
do gestor não muda uma vírgula: só os números das frases-padrão viram marcador.
São as mesmas frases que engine/sincroniza.py reconhece; o que não for frase-
padrão (atribuição em bps, spreads, fluxos) fica como está, porque não vem da
tabela de rentabilidade.
"""
import argparse
import os
import re
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from engine.contexto import ContextoFundo  # noqa: E402
from engine.sincroniza import B, N, P  # noqa: E402

MESES = ('janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho',
         'agosto', 'setembro', 'outubro', 'novembro', 'dezembro')

# (regex, [(grupo, marcador)]): o grupo inteiro vira o marcador.
REGRAS = [
    # "rentabilidade [, isenta de imposto de renda,] de X% no mês (Y% do CDI)"
    (rf'(rentabilidade[^.%]{{0,45}}?\bde\s)({P})(\s+no\s+m[êe]s)(?:(\s*\()({P})(\s+do\s+{B}\)))?',
     [(2, '{mes}'), (5, '{pct_mes}')]),
    # "obteve retorno de X% (Y% do CDI) no mês"
    (rf'(retorno\s+de\s)({P})(\s*\()({P})(\s+do\s+{B}\)\s+no\s+m[êe]s)',
     [(2, '{mes}'), (4, '{pct_mes}')]),
    # "equivalente a Y% do CDI no período"
    (rf'(equivalente\s+a\s)({P})(\s+do\s+{B}\s+no\s+per[íi]odo)',
     [(2, '{pct_mes}')]),
    # "acumulando X% (Y% do CDI) no ano" / "acumula X% (Y% do CDI) em 2026"
    (rf'(acumul(?:ando|a)\s)({P})(?:(\s*\()({P})(\s+do\s+{B}\)))?(\s+(?:no\s+ano|em\s+\d{{4}}))',
     [(2, '{ano}'), (4, '{pct_ano}')]),
    # "acumulando X% (Y% do CDI) desde o início"
    (rf'(acumul(?:ando|a)\s(?:\*\*)?)({P})(\s*\()({P})(\s+do\s+{B}\)(?:\*\*)?\s+desde\s+o\s+in[íi]cio)',
     [(2, '{inicio}'), (4, '{pct_inicio}')]),
    # "acumulando X% (Y% do CDI) em 12 meses"
    (rf'(acumul(?:ando|a)\s(?:\*\*)?)({P})(\s*\()({P})(\s+do\s+{B}\)(?:\*\*)?\s+(?:em|nos)(?:\s+[úu]ltimos)?\s*12\s*meses)',
     [(2, '{12m}'), (4, '{pct_12m}')]),
    # "acumula retorno de X%, frente a B% do CDI"
    (rf'(acumula\s+retorno\s+de\s)({P})(,\s+frente\s+a\s)({P})(\s+do\s+{B})',
     [(2, '{inicio}'), (4, '{bench_inicio}')]),
    # "desempenho de CDI + Z%"
    (rf'(desempenho\s+de\s+{B}\s*\+\s*)({P})',
     [(2, '{bench_mais_inicio}')]),
    # "desempenho anualizado de W% do CDI"
    (rf'(anualizado\s+de\s)({P})(\s+do\s+{B})',
     [(2, '{pct_inicio}')]),
    # "alocação em crédito era de X%"
    (rf'(aloca[çc][ãa]o\s+em\s+cr[ée]dito\s+era\s+de\s)({P})',
     [(2, '{credito}')]),
    # "carrego da carteira encontra-se em CDI +X%"
    (rf'(carrego\s+da\s+carteira\s+encontra-se\s+em\s+{B}\s*\+\s*)({P})',
     [(2, '{carrego}')]),
    # "duration média de D anos"
    (rf'(duration\s+m[ée]dia\s+de\s)({N}\s+anos?)',
     [(2, '{duration}')]),
    # "Em setembro, ..." no começo do parágrafo: o mês corrente
    (rf'(^|\n)((?:Em|No\s+m[êe]s\s+de)\s)({"|".join(MESES)})(\b)',
     [(3, '{mes_nome}')]),
]


def marcar(texto):
    """Devolve (texto com marcadores, [(antes, marcador)])."""
    trocas = []
    for padrao, alvos in REGRAS:
        def troca(m):
            partes = list(m.groups())
            for g, marcador in alvos:
                atual = partes[g - 1]
                if atual is None or atual.startswith('{'):
                    continue
                trocas.append((atual, marcador))
                partes[g - 1] = marcador
            return ''.join(x or '' for x in partes)
        texto = re.sub(padrao, troca, texto, flags=re.I)
    return texto, trocas


def _secoes(texto):
    """[(título da seção, início, fim)] pelos cabeçalhos ## e ###."""
    marcas = [(m.group(2).strip(), m.start()) for m in re.finditer(r'(?m)^(#{2,3})\s+(.+)$', texto)]
    return [(t, ini, marcas[i + 1][1] if i + 1 < len(marcas) else len(texto)) for i, (t, ini) in enumerate(marcas)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--arquivo', default=os.path.join(RAIZ, 'entrada', 'comentarios.md'))
    ap.add_argument('--gravar', action='store_true', help='grava no arquivo (guarda uma cópia .bak)')
    a = ap.parse_args()
    original = open(a.arquivo, encoding='utf-8').read()

    novo, total = [], 0
    pos = 0
    for titulo, ini, fim in _secoes(original) or [('', 0, len(original))]:
        novo.append(original[pos:ini])
        bloco, trocas = marcar(original[ini:fim])
        novo.append(bloco)
        pos = fim
        if trocas:
            total += len(trocas)
            print(f'\n{titulo}')
            for antes, marcador in trocas:
                print(f'  {antes:>10}  ->  {marcador}')
    novo.append(original[pos:])
    novo = ''.join(novo)

    conhecidos = set(ContextoFundo.MARCADORES) | {'bench', 'nome', 'carrego', 'duration', 'credito', 'pl',
                                                  'pl_medio', 'data_base', 'mes_ano', 'mes_nome'}
    usados = set(re.findall(r'\{([a-z_0-9]{2,24})\}', novo))
    estranhos = sorted(u for u in usados if u not in conhecidos and not u.startswith('pct_anual'))
    if estranhos:
        print('\nATENÇÃO: marcadores que o run.py não conhece: ' + ', '.join('{%s}' % e for e in estranhos))

    if not total:
        print('Nada a trocar: os números das frases-padrão já estão como marcador.')
        return
    print(f'\n{total} número(s) viram marcador.')
    if not a.gravar:
        print('Nada foi gravado. Para gravar: python scripts/marcadores_comentarios.py --gravar')
        return
    shutil.copy2(a.arquivo, a.arquivo + '.bak')
    with open(a.arquivo, 'w', encoding='utf-8', newline='') as f:
        f.write(novo)
    print(f'Gravado em {os.path.relpath(a.arquivo, RAIZ)} (cópia em {os.path.relpath(a.arquivo, RAIZ)}.bak).')
    print('Rode python run.py e confira os comentários: o log avisa marcador sem valor.')


if __name__ == '__main__':
    main()
