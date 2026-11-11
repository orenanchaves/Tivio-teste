# -*- coding: utf-8 -*-
"""Lê o Portal de dados da última rodada do AutomaTivio e grava dados.json para a tela Dados.

O Portal de dados (exporters/portal_dados.py) já traz, por fundo, tudo o que entra nos
materiais: indicadores, cadastro, rentabilidade nos 6 períodos, carteira e o que conferir.
Aqui só se traduz esse HTML para JSON, sem recalcular nada.

Uso: python gerar_dados.py   (depois: python gerar.py)
"""
import html
import json
import pathlib
import re

AQUI = pathlib.Path(__file__).parent
HIST = AQUI.parent / "AutomaTivio" / "saida" / "_Historico"

# id do fundo no portal -> chave do AutomaTivio
CHAVE = {"institucional-15": "inst15", "institucional-30": "inst30", "infraplus-cdi": "infrapluscdi",
         "rf-cp": "rfcp", "alt-light": "altlight", "low-vol": "prevlowvol", "top-credit": "prevtopcredit"}


def txt(s):
    s = re.sub(r"<br\s*/?>", "\n", s)
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def tabela(h):
    linhas = re.findall(r"<tr[^>]*>(.*?)</tr>", h, flags=re.S)
    out = [[txt(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", ln, flags=re.S)] for ln in linhas]
    return {"cab": out[0], "linhas": out[1:]} if out else None


def pares(h):
    return [[txt(k), txt(v)] for k, v in re.findall(r"<div><span>(.*?)</span>(.*?)</div>", h, flags=re.S)]


def fundo(sec):
    d = {"nome": txt(re.search(r"<h3>(.*?)</h3>", sec, flags=re.S).group(1)),
         "selos": [[c.strip(), txt(t)] for c, t in re.findall(r'<span class="selo ?([^"]*)">(.*?)</span>', sec, flags=re.S)]}
    k = re.search(r'<div class="kpis">(.*?)</div></', sec + "</", flags=re.S)
    d["kpis"] = []
    for rot, val in re.findall(r'<div class="kpi[^"]*"><span>(.*?)</span><b>(.*?)</b></div>', sec, flags=re.S):
        em = re.search(r"<em>(.*?)</em>", val, flags=re.S)
        d["kpis"].append([txt(rot), txt(re.sub(r"<em>.*?</em>", "", val, flags=re.S)), txt(em.group(1)) if em else ""])
    blocos = re.findall(r"<details[^>]*><summary>(.*?)</summary>(.*?)</details>", sec, flags=re.S)
    fora = re.sub(r"<details[^>]*>.*?</details>", "", sec, flags=re.S)
    t = re.search(r'<div class="tab">(.*?)</div>', fora, flags=re.S)
    d["rent"] = tabela(t.group(1)) if t else None
    for tit, corpo in blocos:
        tit = txt(tit)
        if tit.startswith("Cadastro"):
            d["cad"] = pares(corpo)
        elif tit.startswith("Carteira"):
            d["cart"] = [[k, [[a.strip(), b.strip()] for a, b in (x.rsplit(":", 1) for x in v.split("\n") if ":" in x)]] for k, v in pares(corpo)]
        elif tit.startswith("Últimos pontos"):
            d["hist"] = tabela(corpo)
        elif tit.startswith("O que conferir"):
            tb = tabela(corpo)
            d["conferir"] = tb["linhas"] if tb else []
    return d


def main():
    fontes = sorted(HIST.glob("*/Interno/Portal de dados.html"))
    if not fontes:
        print("sem Portal de dados em", HIST)
        return
    src = fontes[-1]
    h = src.read_text(encoding="utf-8")
    meta = re.search(r"Data base (\d\d/\d\d/\d{4}) · dados de: (.*?) · gerado em (\d\d/\d\d/\d{4} \d\d:\d\d)", txt(h))
    secoes = {m.group(1): m.group(2) for m in re.finditer(r'<section class="fundo" id="f-([^"]+)"[^>]*>(.*?)</section>', h, flags=re.S)}
    ids = ["banks", "infraplus", "rf-cp", "alt-light", "institucional", "institucional-15", "esplanada", "alt180",
           "institucional-30", "infraplus-cdi", "hgd30", "alt90", "low-vol", "top-credit"]
    out = {"_meta": {"base": meta.group(1) if meta else "", "fonte": meta.group(2) if meta else "",
                     "gerado": meta.group(3) if meta else "", "edicao": src.parts[-3]}}
    for i in ids:
        k = CHAVE.get(i, i)
        if k in secoes:
            out[i] = fundo(secoes[k])
    (AQUI / "dados.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print("dados", len(out) - 1, "fundos de", src.parts[-3], "· data base", out["_meta"]["base"])
    faltam = [i for i in ids if i not in out]
    if faltam:
        print("sem bloco no Portal de dados:", ", ".join(faltam))


if __name__ == "__main__":
    main()
