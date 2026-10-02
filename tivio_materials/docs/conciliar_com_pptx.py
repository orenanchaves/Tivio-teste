# -*- coding: utf-8 -*-
"""Confere a rentabilidade calculada contra os PPTX publicados de agosto/2026.

Como ler o slide 1: a tabela de rentabilidade é feita de text boxes soltas, uma
por valor. Agrupando por posição x (coluna = período) e ordenando por y, a ordem
dentro da coluna é sempre: fundo · benchmark · Alfa · % do benchmark.

Fundo novo tem colunas vazias (o Institucional 30 começou em 12/2024, então 24M
e 36M não existem) — por isso o mapeamento é pela posição da coluna, com a última
sempre sendo "desde o início", e não pela ordem em que as caixas aparecem.
"""
import glob, os, re, sys, unicodedata
import pandas as pd
from pptx import Presentation

PERIODOS = ['mes', 'ano', '12m', '24m', '36m', 'inicio']


def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', s.lower())


def num(t):
    return float(t.strip().replace('%', '').replace('−', '-')
                 .replace('.', '').replace(',', '.'))


def ler_pptx(path):
    """{periodo: (fundo, bench)} lido do slide 1."""
    p = Presentation(path)
    caixas = []

    def anda(shapes):
        for sh in shapes:
            if sh.shape_type is not None and str(sh.shape_type).startswith('GROUP'):
                anda(sh.shapes)
                continue
            if sh.has_text_frame:
                t = sh.text_frame.text.strip()
                if re.fullmatch(r'-?[\d.]*,\d+%', t):
                    caixas.append((sh.left, sh.top, num(t)))
    anda(p.slides[0].shapes)
    if not caixas:
        return {}

    # agrupa em colunas (tolerância de meia polegada)
    caixas.sort(key=lambda c: c[0])
    colunas, atual = [], [caixas[0]]
    for c in caixas[1:]:
        if c[0] - atual[-1][0] > 457200 // 2:
            colunas.append(atual); atual = [c]
        else:
            atual.append(c)
    colunas.append(atual)

    out = {}
    n = len(colunas)
    for i, col in enumerate(colunas):
        col.sort(key=lambda c: c[1])          # y crescente: fundo primeiro
        if len(col) < 2:
            continue
        per = 'inicio' if i == n - 1 else (PERIODOS[i] if i < 5 else None)
        if per:
            out[per] = (col[0][2], col[1][2])
    return out


ALVO = {'banks': 'Banks', 'institucional': 'Institucional', 'inst15': 'Institucional_15',
        'inst30': 'Institucional_30', 'infraplus': 'Infra_Plus', 'infrapluscdi': 'Infra_Plus_CDI',
        'esplanada': 'Esplanada', 'legacy': 'Legacy', 'rfcp': 'RF_CP',
        'alt180': 'ALT 180', 'alt90': 'ALT 90', 'altlight': 'ALT Light'}

conf = pd.read_excel(sys.argv[1], sheet_name='Rentabilidades')
base = '/tmp/claude-0/-home-user-Tivio-teste/63fdd8dd-91bd-552b-af1b-f3216a209a3e/scratchpad/novos'
pptxs = (glob.glob(base + '/relatorios_privado/*.pptx')
         + glob.glob(base + '/relatorios_estruturado/*.pptx'))

print(f"{'fundo':<14}{'período':<8}{'calculado':>11}{'PPTX':>10}{'dif':>9}   {'bench calc':>11}{'PPTX':>10}")
print('-' * 76)
tot = ok = 0
divergem = []
for key, pedaco in ALVO.items():
    cam = [p for p in pptxs if norm(pedaco) in norm(os.path.basename(p))]
    # "Institucional" casa também com "Institucional_15"; pega o nome mais curto
    cam.sort(key=lambda p: len(os.path.basename(p)))
    if not cam:
        print(f'{key:<14}(sem PPTX)')
        continue
    pub = ler_pptx(cam[0])
    sub = conf[conf['fundo'] == key].set_index('periodo')
    for per in PERIODOS:
        if per not in pub or per not in sub.index:
            continue
        calc_f, calc_b = sub.loc[per, 'fundo_pct'], sub.loc[per, 'bench_pct']
        if pd.isna(calc_f):
            continue
        calc_f, calc_b = calc_f * 100, (calc_b * 100 if pd.notna(calc_b) else None)
        pub_f, pub_b = pub[per]
        dif = calc_f - pub_f
        tot += 1
        bate = abs(dif) < 0.015
        ok += bate
        marca = '' if bate else '   <-- DIVERGE'
        if not bate:
            divergem.append((key, per, calc_f, pub_f))
        print(f'{key:<14}{per:<8}{calc_f:>10.2f}%{pub_f:>9.2f}%{dif:>8.2f}   '
              f'{(f"{calc_b:>10.2f}%" if calc_b is not None else "         —")}'
              f'{pub_b:>9.2f}%{marca}')
print('-' * 76)
print(f'{ok} de {tot} rentabilidades idênticas ao relatório publicado '
      f'({ok / tot * 100:.0f}%)' if tot else 'nada comparado')
if divergem:
    print('\nDivergem:')
    for k, p, c, pb in divergem:
        print(f'  {k} {p}: calculado {c:.2f}% · publicado {pb:.2f}%')
