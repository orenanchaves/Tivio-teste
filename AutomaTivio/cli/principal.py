# -*- coding: utf-8 -*-
"""Linha de comando. O caminho normal é `python run.py`, sem argumento."""
import argparse
import sys


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog='run.py',
        description='Atualiza a edição mensal da Central de Materiais Tivio.')
    ap.add_argument('--data-base', metavar='AAAA-MM-DD',
                    help='força a data base (padrão: último mês fechado na planilha)')
    ap.add_argument('--so', metavar='FUNDO', nargs='+',
                    help='gera só estes fundos (ex.: --so banks infraplus)')
    ap.add_argument('--saidas', metavar='FORMATO', nargs='+',
                    choices=['html', 'pdf', 'pptx'],
                    help='limita os formatos desta rodada')
    ap.add_argument('--config', default='configs/edicao.yml')
    ap.add_argument('--silencioso', action='store_true',
                    help='não imprime no terminal; só grava o log')
    ap.add_argument('--conferir', action='store_true',
                    help='calcula e valida, mas não escreve material nenhum')
    a = ap.parse_args(argv)

    from engine.pipeline import Pipeline
    p = Pipeline(config=a.config, data_base=a.data_base, saidas=a.saidas,
                 so_fundos=a.so, eco=not a.silencioso)
    if a.conferir:
        p.cfg['saidas'] = {'html': False, 'pdf': False, 'pptx': False}
        p.cfg['materiais'] = {k: False for k in p.cfg.get('materiais', {})}

    print()
    ok = p.rodar()
    print()
    print('  ' + p.log.resumo())
    print(f'  saída: saida/{p.edicao.competencia}/')
    if not ok:
        print('  ! houve erros — ver a aba Avisos da conferência e o log')
    print()
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
