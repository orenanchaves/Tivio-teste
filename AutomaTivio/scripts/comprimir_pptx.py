# -*- coding: utf-8 -*-
"""Diminui um PPTX sem mexer no desenho: só as imagens grandes.

Os decks que o time usa chegam a 194 MB, quase tudo foto salva como PNG em
resolução de impressão (uma única imagem de 69 MB). O GitHub recusa arquivo
acima de 100 MB, e o zip da automação fica pesado para baixar.

Para cada imagem acima de LIMITE:
  - reduz para no máximo LADO px no lado maior (sobra para tela cheia em 4K);
  - foto sem transparência vira JPEG (qualidade 86) e as referências a ela nos
    .rels passam a apontar para o arquivo novo;
  - imagem com transparência continua PNG, só reduzida e otimizada.

    python scripts/comprimir_pptx.py entrada.pptx saida.pptx
"""
import io
import os
import re
import sys
import zipfile

from PIL import Image

LIMITE = 600_000          # bytes
LADO = 2560               # px
Image.MAX_IMAGE_PIXELS = None


def _tem_transparencia(im):
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
        a = im.convert('RGBA').getchannel('A')
        return a.getextrema()[0] < 250
    return False


def comprimir(origem, destino, log=print):
    zin = zipfile.ZipFile(origem)
    novos, renomes = {}, {}
    for info in zin.infolist():
        nome = info.filename
        if not nome.startswith('ppt/media/') or info.file_size < LIMITE:
            continue
        ext = os.path.splitext(nome)[1].lower()
        if ext not in ('.png', '.jpg', '.jpeg'):
            continue
        try:
            im = Image.open(io.BytesIO(zin.read(nome)))
            im.load()
        except Exception:
            continue
        if max(im.size) > LADO:
            im.thumbnail((LADO, LADO), Image.LANCZOS)
        buf = io.BytesIO()
        if ext == '.png' and _tem_transparencia(im):
            im.save(buf, 'PNG', optimize=True)
            alvo = nome
        else:
            im.convert('RGB').save(buf, 'JPEG', quality=86, optimize=True, progressive=True)
            alvo = nome if ext in ('.jpg', '.jpeg') else nome[:-4] + '.jpeg'
        if buf.tell() < info.file_size:
            novos[alvo] = buf.getvalue()
            if alvo != nome:
                renomes[nome] = alvo

    with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            nome = info.filename
            if nome in renomes:
                continue                                   # sai com o nome novo
            dados = novos.get(nome, zin.read(nome))
            if nome.endswith('.rels') and renomes:
                t = dados.decode('utf-8')
                for velho, novo in renomes.items():
                    t = t.replace(os.path.basename(velho), os.path.basename(novo))
                dados = t.encode('utf-8')
            if nome == '[Content_Types].xml' and renomes and 'Extension="jpeg"' not in dados.decode('utf-8'):
                dados = dados.decode('utf-8').replace(
                    '<Default ', '<Default Extension="jpeg" ContentType="image/jpeg"/><Default ', 1).encode('utf-8')
            zout.writestr(info if nome not in novos else nome, dados)
        for velho, novo in renomes.items():
            zout.writestr(novo, novos[novo])
    a, b = os.path.getsize(origem), os.path.getsize(destino)
    log(f'{os.path.basename(origem)}: {a / 1e6:.0f} MB -> {b / 1e6:.0f} MB '
        f'({len(novos)} imagens, {len(renomes)} viraram JPEG)')
    return destino


if __name__ == '__main__':
    comprimir(sys.argv[1], sys.argv[2])
