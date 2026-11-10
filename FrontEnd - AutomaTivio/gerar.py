# -*- coding: utf-8 -*-
"""Monta o portal a partir de portal_fonte.html.

- index.html: versão local, abre com dois cliques (fontes em fontes/).
- portal(...): a mesma página para a Central (tivio-central.pages.dev); o montar.py
  da Central chama esta função com as fontes embutidas e o link de volta da Central.

Uso: python gerar.py   (antes, se as peças mudaram: python gerar_pecas.py)
"""
import json
import pathlib

AQUI = pathlib.Path(__file__).parent
RAIZ = AQUI.parent


def portal(faces, casa, logo=None):
    s = (AQUI / "portal_fonte.html").read_text(encoding="utf-8")
    if logo is None:
        logo = (RAIZ / "AutomaTivio/assets/marca/tivio.svg").read_text(encoding="utf-8").strip()
        logo = logo.replace('class="tv-brand"', 'role="img" aria-label="Tivio Capital"', 1)
    pecas = (AQUI / "pecas.json").read_text(encoding="utf-8") if (AQUI / "pecas.json").exists() else "{}"
    return (s.replace("{{FACES}}", faces).replace("{{CASA}}", casa).replace("{{LOGO}}", logo)
             .replace("/*PECAS*/{}", pecas.replace("</", "<\\/")))


if __name__ == "__main__":
    faces = "\n".join(
        f'@font-face{{font-family:Versos;font-weight:{p};font-display:swap;src:url(fontes/Versos-{n}.woff2) format("woff2")}}'
        for p, n in ((300, "ExtraLight"), (400, "Regular"), (600, "SemiBold"), (700, "Bold")))
    html = '<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n' + portal(faces, "#inicio") + "\n</html>\n"
    (AQUI / "index.html").write_text(html, encoding="utf-8")
    print("index.html", round(len(html) / 1e6, 2), "MB")
