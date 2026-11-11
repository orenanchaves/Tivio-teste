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
    "infraplus": [(REL, "PDF · PPTX", f"{CP}/Relatórios/Tivio Infra Plus - Relatório de Gestão.pdf"),
                  ("Post", "JPG", f"{CP}/Redes sociais/07-tivio-infraplus.jpg")],
    "rf-cp": [(REL, "PDF · PPTX", f"{CP}/Relatórios/Tivio RF CP - Relatório de Gestão.pdf")],
    "alt-light": [(REL, "PDF · PPTX", f"{CE}/Relatórios/Tivio ALT Light - Relatório de Gestão.pdf"),
                  ("Post", "JPG", f"{CE}/Redes sociais/05-tivio-altlight.jpg")],
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

# logos oficiais dos fundos (assets/logos): versão branca para fundo escuro, preta para fundo claro
import re
LOGOS_DIR = AQUI.parent / "AutomaTivio" / "assets" / "logos"
LOGOS = {
    "banks": ("credito_privado/_Banks - Horizontal - Branco.svg", "credito_privado/_Banks - Horizontal - Preto.svg"),
    "institucional": ("credito_privado/_Institucional - Horizontal - Preto.svg", "credito_privado/_Institucional - Horizontal - Preto.svg"),
    "institucional-15": ("credito_privado/_Institucional 15 - Horizontal - Branco.svg", "credito_privado/_Institucional 15 - Horizontal - Preto.svg"),
    "institucional-30": ("credito_privado/_Institucional 30 - Horizontal - Branco.svg", "credito_privado/_Institucional 30 - Horizontal - Preto.svg"),
    "infraplus-cdi": ("credito_privado/_Infra Plus CDI - Horizontal - Branco.svg", "credito_privado/_Infra Plus CDI - Horizontal - Preto.svg"),
    "esplanada": ("credito_privado/_Esplanada - Horizontal - Branco.svg", "credito_privado/_Esplanada - Horizontal - Preto.svg"),
    "alt180": ("credito_estruturado/ALT_180_horizontal_branco_01.svg", "credito_estruturado/ALT_180_horizontal_preto_01.svg"),
    "alt90": ("credito_estruturado/ALT_90_horizontal_branco_01.svg", "credito_estruturado/ALT_90_horizontal_preto_01.svg"),
    "infraplus": ("credito_privado/_Infra Plus - Horizontal - Branco.svg", "credito_privado/_Infra Plus - Horizontal - Preto.svg"),
    "rf-cp": ("credito_privado/_RF CP - Horizontal - Branco.svg", "credito_privado/_RF CP - Horizontal - Preto.svg"),
    "alt-light": ("credito_estruturado/ALT_LIGHT_horizontal_branco.svg", "credito_estruturado/ALT_LIGHT_horizontal_preto.svg"),
    "hgd30": ("../landings/hgd30_horizontal.svg", "../landings/hgd30_horizontal.svg"),
}
# sem versão branca horizontal na pasta: a branca sai da preta, pintando de branco o que é preto
BRANCO_DA_PRETA = {"institucional", "hgd30"}
# fundos sem arquivo de logo: o nome como está na capa do deck (TIVIO / PREV LOW VOL)
LOGO_TEXTO = {"low-vol": ["PREV", "LOW VOL"], "top-credit": ["PREV", "TOP CREDIT"]}


def pinta_branco(s):
    regra = "<style>path:not([class]),polygon:not([class]),rect:not([class]),.cls-2{fill:#fff}</style>" if "#79949b" not in s else             "<style>path:not([class]),polygon:not([class]),rect:not([class]){fill:#fff}</style>"
    return s.replace("</defs>", regra + "</defs>", 1)


def svg_limpo(caminho, branco=False):
    """Tira a chapa de fundo do Illustrator (rect do tamanho do quadro, sem cor), que pinta de preto."""
    s = caminho.read_text(encoding="utf-8")
    if branco:
        s = pinta_branco(s)
    s = re.sub(r'<g id="Background">.*?</g>', "", s, flags=re.S)
    s = re.sub(r"<rect(?![^>]*\b(?:class|fill|style)=)[^>]*/>", "", s, count=1)
    # recorta o viewBox no limite do desenho (os arquivos vêm com muita margem)
    vb = re.search(r'viewBox="\s*([\d.+-]+)\s+([\d.+-]+)\s+([\d.]+)\s+([\d.]+)"', s)
    if vb:
        x0, y0, w, h = map(float, vb.groups())
        esc = 4
        pix = fitz.open(stream=s.encode("utf-8"), filetype="svg")[0].get_pixmap(matrix=fitz.Matrix(esc, esc), alpha=True)
        im = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
        caixa = im.getchannel("A").getbbox()
        if caixa:
            kx, ky = w / pix.width, h / pix.height
            a, b, c, d = caixa
            novo = f'viewBox="{x0 + a * kx - 1:.1f} {y0 + b * ky - 1:.1f} {(c - a) * kx + 2:.1f} {(d - b) * ky + 2:.1f}"'
            s = s.replace(vb.group(0), novo, 1)
    return "data:image/svg+xml;base64," + base64.b64encode(s.encode("utf-8")).decode()


logos = {}
for fundo, (branco, preto) in LOGOS.items():
    if (LOGOS_DIR / branco).exists() and (LOGOS_DIR / preto).exists():
        logos[fundo] = {"branco": svg_limpo(LOGOS_DIR / branco, fundo in BRANCO_DA_PRETA), "preto": svg_limpo(LOGOS_DIR / preto),
                        "vertical": "Vertical" in branco}
    else:
        faltou.append(branco)
for fundo, linhas in LOGO_TEXTO.items():
    logos[fundo] = {"texto": linhas}
(AQUI / "logos.json").write_text(json.dumps(logos, ensure_ascii=False), encoding="utf-8")
print("logos", len(logos))
print("peças", sum(len(v) for v in saida.values()), "tamanho", round(total / 1e6, 2), "MB")
if faltou:
    print("faltou:", *faltou, sep="\n  ")
