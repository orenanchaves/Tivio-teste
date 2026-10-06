# -*- coding: utf-8 -*-
"""Comentários do gestor — em Markdown, Word ou Excel.

Três formatos porque o texto chega em três formatos, e obrigar a converter é
criar mais um passo manual no processo que este ambiente existe para encurtar.

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
import html as _html
import os
import re
import unicodedata
import zipfile

import pandas as pd

# "Fundo Tivio Institucional" e "Tivio Institucional" são o mesmo título; o
# prefixo varia de um fundo para outro no mesmo documento
PREFIXOS = re.compile(r'^(?:o\s+)?fundo\s+', re.I)


def _norm(s):
    s = PREFIXOS.sub('', str(s).strip())
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
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


def _do_docx(path):
    """Word: parágrafo inteiramente em negrito é título de fundo.

    É a convenção que o documento do gestor já usa — não foi preciso pedir
    nada. O resto do parágrafo segue como está, inclusive a pontuação.

    O documento começa com uma seção "Cenário" (o texto de mercado comum a
    todos). Ela vira uma entrada como qualquer outra; como não existe fundo com
    esse nome, simplesmente não é usada — e fica disponível caso um dia se
    queira montar o comentário juntando cenário + parágrafo do fundo.
    """
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8')

    def texto(trecho):
        # <w:br/> e <w:tab/> viram espaço, senão palavras colam
        trecho = re.sub(r'<w:(?:br|tab)\b[^>]*/?>', ' ', trecho)
        return re.sub(r'\s+', ' ', _html.unescape(re.sub(r'<[^>]+>', '', trecho))).strip()

    out, atual, buf = {}, None, []
    for p in re.findall(r'<w:p\b.*?</w:p>', xml, re.S):
        t = texto(p)
        if not t:
            continue
        runs = [r for r in re.findall(r'<w:r\b.*?</w:r>', p, re.S) if texto(r)]
        # <w:b/> e <w:b w:val="1"/> contam; <w:bCs/> (negrito de script
        # complexo) não — por isso o lookahead negativo
        negrito = bool(runs) and all(re.search(r'<w:b\b(?![a-zA-Z])', r) for r in runs)
        if negrito and len(t) < 80 and not t.endswith('.'):
            if atual:
                out[atual] = buf
            atual, buf = _norm(t), []
        elif atual is not None:
            buf.append(t)
        else:
            # texto antes do primeiro título em negrito: a seção de abertura
            atual, buf = _norm(t), []
    if atual:
        out[atual] = buf
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
    """Aceita um caminho ou uma lista deles (.md, .docx, .xlsx).

    Com vários, o primeiro que define um fundo vence. É o que permite manter o
    documento do gestor como fonte principal e um .md ao lado só com o que ele
    não cobre — hoje, os textos do ALT 90 e do ALT 180, que chegaram por outro
    canal.
    """
    if isinstance(caminho, (list, tuple)):
        rel, eml, origens = {}, {}, []
        for c in caminho:
            parte = carregar(c)
            if not len(parte) and not parte._email:
                continue
            origens.append(parte.origem)
            for k, v in parte._rel.items():
                rel.setdefault(k, v)
            for k, v in parte._email.items():
                eml.setdefault(k, v)
        return Comentarios(rel, eml, ' + '.join(origens) or '(nenhum arquivo de comentários)')

    if not caminho or not os.path.exists(caminho):
        # tenta os irmãos: comentarios.md <-> .docx <-> .xlsx
        if caminho:
            raiz = os.path.splitext(caminho)[0]
            for ext in ('.docx', '.md', '.xlsx'):
                if os.path.exists(raiz + ext):
                    caminho = raiz + ext
                    break
            else:
                return Comentarios(origem='(nenhum arquivo de comentários)')
        else:
            return Comentarios(origem='(nenhum arquivo de comentários)')

    if caminho.lower().endswith('.docx'):
        return Comentarios(_do_docx(caminho), {}, os.path.basename(caminho))

    if caminho.lower().endswith(('.xlsx', '.xlsm')):
        rel, eml = _do_excel(caminho)
        return Comentarios(rel, eml, os.path.basename(caminho))

    with open(caminho, encoding='utf-8') as f:
        texto = f.read()
    # nota <!-- … --> é para quem edita, não vai para o material
    texto = re.sub(r'<!--.*?-->', '', texto, flags=re.S)
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
