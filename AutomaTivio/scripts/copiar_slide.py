# -*- coding: utf-8 -*-
"""Copia um slide de um PPTX para outro, com imagens e gráficos.

Para montar um modelo de deck a partir de outro: o slide de rentabilidade
histórica do HYD60 nasceu do slide 10 do HGD30. O layout usado é o de um
slide do deck de destino (`--layout-de`), para o slide herdar fundo e rodapé
do deck novo, e não do deck de onde veio.

    python scripts/copiar_slide.py origem.pptx 10 destino.pptx \\
        --depois-de 9 --layout-de 9 [--saida novo.pptx]

Gráfico: o XML do gráfico e a planilha embutida são copiados como peças novas
(o gráfico continua editável no PowerPoint e o decks.py troca a série todo mês).
"""
import argparse
import copy
import io
import re

from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI

R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def _copia_parte(pacote, origem, padrao):
    """Peça nova no pacote de destino com o conteúdo da `origem` (e as peças
    que ela referencia, um nível abaixo: a planilha do gráfico)."""
    nome = pacote.next_partname(padrao)
    blob = origem.blob
    trocas = {}
    nova = Part(PackURI(nome), origem.content_type, pacote, blob)
    for rid, rel in list(origem.rels.items()):
        if rel.is_external:
            trocas[rid] = nova.rels.get_or_add_ext_rel(rel.reltype, rel.target_ref)
            continue
        # toda peça abaixo (planilha, estilo e cores do gráfico) vira cópia com
        # nome livre no destino: o mesmo nome de outro deck colide no zip
        alvo = rel.target_part
        padrao_sub = re.sub(r'\d*(\.\w+)$', r'%d\1', str(alvo.partname))
        alvo = _copia_parte(pacote, alvo, padrao_sub)
        trocas[rid] = nova.relate_to(alvo, rel.reltype)
    # o XML aponta as peças por rId: os ids novos entram no lugar dos antigos
    if trocas and nome.endswith('.xml'):
        t = blob.decode('utf-8')
        for velho, novo in trocas.items():
            t = t.replace(f'r:id="{velho}"', f'r:id="__{novo}__"')
        for novo in trocas.values():
            t = t.replace(f'r:id="__{novo}__"', f'r:id="{novo}"')
        nova._blob = t.encode('utf-8')
    return nova


def copiar(origem, n_origem, destino, depois_de, layout_de, saida=None):
    src = Presentation(origem)
    dst = Presentation(destino)
    s = src.slides[n_origem - 1]
    layout = dst.slides[layout_de - 1].slide_layout
    novo = dst.slides.add_slide(layout)
    for ph in list(novo.placeholders):
        ph._element.getparent().remove(ph._element)

    mapa = {}
    for rid, rel in s.part.rels.items():
        if rel.reltype in (RT.SLIDE_LAYOUT, RT.NOTES_SLIDE):
            continue
        if rel.is_external:
            mapa[rid] = novo.part.rels.get_or_add_ext_rel(rel.reltype, rel.target_ref)
        elif rel.reltype == RT.IMAGE:
            _, mapa[rid] = novo.part.get_or_add_image_part(io.BytesIO(rel.target_part.blob))
        elif rel.reltype == RT.CHART:
            parte = _copia_parte(dst.part.package, rel.target_part, '/ppt/charts/chart%d.xml')
            mapa[rid] = novo.part.relate_to(parte, RT.CHART)
        else:
            mapa[rid] = novo.part.relate_to(rel.target_part, rel.reltype)

    arvore = novo.shapes._spTree
    for el in s.shapes._spTree.iterchildren():
        if el.tag.endswith('}nvGrpSpPr') or el.tag.endswith('}grpSpPr'):
            continue
        el2 = copy.deepcopy(el)
        for x in el2.iter():
            for att in list(x.attrib):
                if att.startswith(R) and x.get(att) in mapa:
                    x.set(att, mapa[x.get(att)])
        arvore.append(el2)
    # fundo próprio do slide, se houver
    bg = s._element.cSld.bg
    if bg is not None:
        novo._element.cSld.insert(0, copy.deepcopy(bg))

    # posição: logo depois do slide `depois_de`
    lista = dst.slides._sldIdLst
    item = lista[-1]
    lista.remove(item)
    lista.insert(depois_de, item)
    dst.save(saida or destino)
    return depois_de + 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('origem')
    ap.add_argument('n', type=int)
    ap.add_argument('destino')
    ap.add_argument('--depois-de', type=int, required=True)
    ap.add_argument('--layout-de', type=int, required=True)
    ap.add_argument('--saida')
    a = ap.parse_args()
    n = copiar(a.origem, a.n, a.destino, a.depois_de, a.layout_de, a.saida)
    print(f'slide copiado para a posição {n}')
