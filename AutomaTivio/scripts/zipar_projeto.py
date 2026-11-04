"""Gera um .zip do projeto para compartilhar com outra pessoa.

    python scripts/zipar_projeto.py              # ../AutomaTivio_AAAA-MM-DD.zip
    python scripts/zipar_projeto.py -o destino.zip

Ficam de fora: .git, .venv e saida (a saída é regenerada por `python run.py`).
Também ficam de fora, por segurança ou por serem lixo: o `.env` (pode ter o
token da API; o `.env.example` vai no lugar), __pycache__, .cache e logs.
"""
import argparse
import os
import zipfile
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTAS_FORA = {'.git', '.venv', 'saida', '__pycache__', '.cache', 'logs'}
ARQUIVOS_FORA = {'.env'}


def _fora(nome_arquivo):
    return (nome_arquivo in ARQUIVOS_FORA or nome_arquivo.endswith('.pyc')
            or 'Zone.Identifier' in nome_arquivo or nome_arquivo.endswith('sec.endpointdlp'))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-o', '--saida', help='caminho do .zip (padrão: pasta acima do projeto)')
    args = ap.parse_args()

    destino = Path(args.saida) if args.saida else RAIZ.parent / f'AutomaTivio_{date.today():%Y-%m-%d}.zip'
    destino = destino.resolve()
    pasta_zip = 'AutomaTivio'     # nome da pasta dentro do zip, ao descompactar

    n = 0
    with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as z:
        for pasta, subpastas, arquivos in os.walk(RAIZ):
            subpastas[:] = [d for d in subpastas if d not in PASTAS_FORA]
            for nome in arquivos:
                caminho = Path(pasta) / nome
                if _fora(nome) or caminho == destino:
                    continue
                z.write(caminho, Path(pasta_zip) / caminho.relative_to(RAIZ))
                n += 1
    print(f'{n} arquivos -> {destino} ({destino.stat().st_size / 1e6:.1f} MB)')


if __name__ == '__main__':
    main()
