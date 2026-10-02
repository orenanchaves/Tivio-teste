# -*- coding: utf-8 -*-
"""Comentários do gestor — em Markdown ou Excel.

O formato pedido é Markdown, que é o que um gestor consegue editar sem abrir
planilha:

    # Banks

    Primeiro parágrafo.

    Segundo parágrafo.

    # Institucional

    ...

O título (`# Banks`) casa com a chave do fundo OU com o `nome` em fundos.yml,
sem distinguir caixa nem acento — "# Infra Plus CDI", "# infrapluscdi" e
"# INFRA PLUS CDI" chegam todos no mesmo fundo.

Também aceita a planilha antiga (abas Comentarios_Relatorio / Comentarios_Email
com colunas chave, p1..p4) para não obrigar a migrar tudo de uma vez.
"""
import os
import re
import unicodedata

import pandas as pd


def _norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', s.lower())


class Comentarios:
    """Acesso uniforme: `.relatorio(key)` -> lista de parágrafos."""

    def __init__(self, por_fundo=None, email=None, origem=''):
        self._rel = por_fundo or {}
        self._email = email or {}
        self.origem = origem

    # ------------------------------------------------------------- consulta
    def relatorio(self, key, nome=None):
        for k in (key, nome):
            if k and _norm(k) in self._rel:
                return self._rel[_norm(k)]
        return []

    def email(self, key, nome=None):
        for k in (key, nome):
            if k and _norm(k) in self._email:
                return self._email[_norm(k)]
        return ''

    @property
    def fundos(self):
        return list(self._rel)

    def __len__(self):
        return len(self._rel)


def _do_markdown(texto):
    """Divide por `# Título` e devolve {chave_normalizada: [parágrafos]}."""
    out, atual = {}, None
    buf = []
    for linha in texto.splitlines():
        m = re.match(r'^#{1,3}\s+(.+?)\s*$', linha)
        if m:
            if atual:
                out[atual] = [p for p in buf if p]
            atual, buf = _norm(m.group(1)), []
            continue
        if atual is None:
            continue
        if linha.strip():
            buf.append(linha.strip()) if not buf or buf[-1] == '' else buf.__setitem__(
                -1, (buf[-1] + ' ' + linha.strip()).strip())
        else:
            buf.append('')
    if atual:
        out[atual] = [p for p in buf if p]
    return out


def _do_excel(path):
    xl = pd.read_excel(path, sheet_name=None, dtype=str)
    rel, eml = {}, {}
    df = xl.get('Comentarios_Relatorio')
    if df is not None:
        for _, r in df.fillna('').iterrows():
            k = _norm(r.get('chave', ''))
            if not k:
                continue
            rel[k] = [str(r.get(f'p{i}', '')).strip()
                      for i in range(1, 6) if str(r.get(f'p{i}', '')).strip()]
    df = xl.get('Comentarios_Email')
    if df is not None:
        for _, r in df.fillna('').iterrows():
            k = _norm(r.get('chave', ''))
            if k:
                eml[k] = str(r.get('comentario', '')).strip()
    return rel, eml


def carregar(caminho):
    """Aceita .md, .xlsx ou caminho inexistente (devolve vazio)."""
    if not caminho or not os.path.exists(caminho):
        # tenta o par: comentarios.md <-> comentarios.xlsx
        if caminho:
            alt = os.path.splitext(caminho)[0] + ('.xlsx' if caminho.endswith('.md') else '.md')
            if os.path.exists(alt):
                caminho = alt
            else:
                return Comentarios(origem='(nenhum arquivo de comentários)')
        else:
            return Comentarios(origem='(nenhum arquivo de comentários)')

    if caminho.lower().endswith(('.xlsx', '.xlsm')):
        rel, eml = _do_excel(caminho)
        return Comentarios(rel, eml, os.path.basename(caminho))

    with open(caminho, encoding='utf-8') as f:
        texto = f.read()
    # o .md pode ter duas seções de nível 1 separando relatório de e-mail
    partes = re.split(r'(?im)^#\s*(relat[óo]rio|e-?mail)\s*$', texto)
    if len(partes) >= 3:
        blocos, i = {}, 1
        while i < len(partes) - 1:
            blocos[_norm(partes[i])] = partes[i + 1]
            i += 2
        rel = _do_markdown(blocos.get('relatorio', ''))
        eml = {k: ' '.join(v) for k, v in _do_markdown(blocos.get('email', '')).items()}
        return Comentarios(rel, eml, os.path.basename(caminho))
    return Comentarios(_do_markdown(texto), {}, os.path.basename(caminho))
