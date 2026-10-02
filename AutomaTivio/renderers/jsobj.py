"""Leitura/escrita de literais JS (objetos/arrays) embutidos nos HTMLs.

Permite localizar `const FUNDS=[...]`, converter para Python, alterar só os
campos necessários e gravar de volta — sem tocar no resto do arquivo.
"""
import json
import re


class JSParseError(Exception):
    pass


class _P:
    def __init__(self, s, i):
        self.s, self.i = s, i

    def ws(self):
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c in ' \t\r\n':
                self.i += 1
            elif s.startswith('//', self.i):
                self.i = s.find('\n', self.i) + 1 or len(s)
            elif s.startswith('/*', self.i):
                self.i = s.find('*/', self.i) + 2
            else:
                break

    def val(self):
        self.ws()
        c = self.s[self.i]
        if c == '{':
            return self.obj()
        if c == '[':
            return self.arr()
        if c in '"\'`':
            return self.string()
        m = re.compile(r'-?\d+(\.\d+)?([eE][+-]?\d+)?').match(self.s, self.i)
        if m:
            self.i = m.end()
            t = m.group(0)
            return float(t) if ('.' in t or 'e' in t.lower()) else int(t)
        m = re.compile(r'[A-Za-z_$][\w$]*').match(self.s, self.i)
        if m:
            self.i = m.end()
            w = m.group(0)
            if w in ('true', 'false'):
                return w == 'true'
            if w in ('null', 'undefined'):
                return None
            raise JSParseError('identificador inesperado: ' + w)
        raise JSParseError('caractere inesperado %r em %d' % (c, self.i))

    def string(self):
        q = self.s[self.i]
        self.i += 1
        out = []
        s = self.s
        while True:
            c = s[self.i]
            if c == '\\':
                n = s[self.i + 1]
                if n == 'u':
                    out.append(chr(int(s[self.i + 2:self.i + 6], 16)))
                    self.i += 6
                    continue
                out.append({'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f'}.get(n, n))
                self.i += 2
                continue
            if c == q:
                self.i += 1
                return ''.join(out)
            out.append(c)
            self.i += 1

    def key(self):
        self.ws()
        c = self.s[self.i]
        if c in '"\'':
            return self.string()
        m = re.compile(r'[\w$]+').match(self.s, self.i)
        if not m:
            raise JSParseError('chave inválida em %d' % self.i)
        self.i = m.end()
        return m.group(0)

    def obj(self):
        self.i += 1
        o = {}
        while True:
            self.ws()
            if self.s[self.i] == '}':
                self.i += 1
                return o
            k = self.key()
            self.ws()
            if self.s[self.i] != ':':
                raise JSParseError('esperado ":" em %d' % self.i)
            self.i += 1
            o[k] = self.val()
            self.ws()
            if self.s[self.i] == ',':
                self.i += 1

    def arr(self):
        self.i += 1
        a = []
        while True:
            self.ws()
            if self.s[self.i] == ']':
                self.i += 1
                return a
            a.append(self.val())
            self.ws()
            if self.s[self.i] == ',':
                self.i += 1


def find_literal(html, decl):
    """Acha `decl` (ex.: 'const FUNDS=') e devolve (valor, ini, fim) do literal."""
    m = re.search(re.escape(decl).replace('=', r'\s*=\s*'), html)
    if not m:
        raise JSParseError('não encontrado: ' + decl)
    p = _P(html, m.end())
    p.ws()
    ini = p.i
    v = p.val()
    return v, ini, p.i


def dump(v):
    return json.dumps(v, ensure_ascii=False, separators=(',', ':'))


def replace_literal(html, decl, fn):
    """Lê o literal, aplica fn(valor)->valor e regrava no mesmo lugar."""
    v, ini, fim = find_literal(html, decl)
    novo = fn(v)
    return html[:ini] + dump(novo) + html[fim:]
