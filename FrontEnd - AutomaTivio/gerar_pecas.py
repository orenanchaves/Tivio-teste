# -*- coding: utf-8 -*-
"""Gera pecas.json: miniaturas das peças reais da última edição (saida/_Atual),
para a etapa "Materiais" do portal mostrar as peças prontas, como na Central de Materiais.

Uso: python gerar_pecas.py
"""
import base64
import io
import json
import pathlib

import fitz  # PyMuPDF
from PIL import Image

AQUI = pathlib.Path(__file__).parent
ATUAL = AQUI.parent / "AutomaTivio" / "saida" / "_Atual"
LARG = 720

CP, CE, IS, PV = "Crédito Privado", "Crédito Estruturado", "Investment Solutions", "Previdência"
REL = "Relatório de Gestão"
PECAS = {
    "banks": [(REL, "PDF · PPTX", f"{CP}/Relatórios/Tivio Banks - Relatório de Gestão.pdf"),
              ("Post", "JPG", f"{CP}/Redes sociais/03-tivio-banks.jpg")],
    "institucional": [(REL, "PDF · PPTX", f"{CP}/Relatórios/Tivio Institucional - Relatório de Gestão.pdf"),
                      ("Post", "JPG", f"{CP}/Redes sociais/04-tivio-institucional.jpg"),
                      ("Deck", "PDF · PPTX", f"{CP}/Decks/Institucional/Deck - Tivio Institucional.pdf")],
    "institucional-15": [(REL, "PDF · PPTX", f"{CP}/Relatórios/Tivio Institucional 15 - Relatório de Gestão.pdf"),
                         ("Post", "JPG", f"{CP}/Redes sociais/05-tivio-inst15.jpg"),
                         ("Deck", "PDF · PPTX", f"{CP}/Decks/Institucional 15/Deck - Tivio Institucional 15.pdf")],
    "institucional-30": [(REL, "PDF · PPTX", f"{CP}/Relatórios/Tivio Institucional 30 - Relatório de Gestão.pdf"),
                         ("Post", "JPG", f"{CP}/Redes sociais/06-tivio-inst30.jpg"),
                         ("Deck", "PDF · PPTX", f"{CP}/Decks/Institucional 30/Deck - Tivio Institucional 30.pdf")],
    "infraplus-cdi": [(REL, "PDF · PPTX", f"{CP}/Relatórios/Tivio Infra Plus CDI - Relatório de Gestão.pdf"),
                      ("Post", "JPG", f"{CP}/Redes sociais/08-tivio-infrapluscdi.jpg"),
                      ("Deck", "PDF · PPTX", f"{CP}/Decks/Infra Plus CDI/Deck - Tivio Infra Plus CDI.pdf")],
    "esplanada": [(REL, "PDF · PPTX", f"{CP}/Relatórios/Tivio Esplanada - Relatório de Gestão.pdf")],
    "alt180": [(REL, "PDF · PPTX", f"{CE}/Relatórios/Tivio ALT 180 - Relatório de Gestão.pdf"),
               ("Post", "JPG", f"{CE}/Redes sociais/03-tivio-alt180.jpg"),
               ("Deck", "PDF · PPTX", f"{CE}/Decks/ALT 180/Deck - Tivio ALT 180 - Sem ROA.pdf")],
    "alt90": [(REL, "PDF · PPTX", f"{CE}/Relatórios/Tivio ALT 90 - Relatório de Gestão.pdf"),
              ("Post", "JPG", f"{CE}/Redes sociais/04-tivio-alt90.jpg"),
              ("Deck", "PDF · PPTX", f"{CE}/Decks/ALT 90/Deck - Tivio ALT 90 - Sem ROA.pdf")],
    "hgd30": [("Informativo", "PDF · PPTX", f"{PV}/HGD30/Informativo/Informativo - HGD30.pdf"),
              ("Deck", "PDF · PPTX", f"{PV}/Decks/HGD30/Deck - Tivio HGD30.pdf")],
    "low-vol": [("Post", "JPG", f"{IS}/Redes sociais/10-tivio-prevlowvol.jpg"),
                ("Deck", "PDF · PPTX", f"{IS}/Decks/Prev Low Vol/Deck - Tivio Prev Low Vol.pdf")],
    "top-credit": [("Deck", "PDF · PPTX", f"{IS}/Decks/Prev Top Credit/Deck - Tivio Prev Top Credit.pdf")],
}


def imagem(caminho):
    if caminho.suffix.lower() == ".pdf":
        doc = fitz.open(caminho)
        pg = doc[0]
        z = LARG * 1.5 / pg.rect.width
        pix = pg.get_pixmap(matrix=fitz.Matrix(z, z))
        im = Image.open(io.BytesIO(pix.tobytes("png")))
    else:
        im = Image.open(caminho)
    im = im.convert("RGB")
    im.thumbnail((LARG, LARG * 2), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=70, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), im.size


saida, faltou, total = {}, [], 0
for fundo, itens in PECAS.items():
    for titulo, fmt, rel in itens:
        p = ATUAL / rel
        if not p.exists():
            faltou.append(rel)
            continue
        src, (w, h) = imagem(p)
        total += len(src)
        saida.setdefault(fundo, []).append({"t": titulo, "fmt": fmt, "arq": p.name, "w": w, "h": h, "img": src})

(AQUI / "pecas.json").write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")
print("peças", sum(len(v) for v in saida.values()), "tamanho", round(total / 1e6, 2), "MB")
if faltou:
    print("faltou:", *faltou, sep="\n  ")
