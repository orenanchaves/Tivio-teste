# -*- coding: utf-8 -*-
"""Cadastro de fundos: junta configs/fundos.yml com a aba DePara da planilha.

O vínculo entre os dois é o nome da carteira — e esse nome é instável. A
planilha troca o sufixo " - Expandida" de um mês para o outro, e um fundo novo
entra com a grafia que o Quantum devolveu. Casar só por igualdade exata faz o
fundo desaparecer silenciosamente do material.

Então o resolvedor tem três degraus:

1. `carteira` exata (quando a config a conhece);
2. `carteira` ignorando o sufixo " - Expandida" e caixa/acento;
3. `busca`: todas as palavras-chave presentes no nome.

O que não resolve em nenhum degrau não é inventado — vira uma linha na aba
"Fundos sem atualização" da conferência, com os candidatos mais próximos.
"""
import re
import unicodedata

import yaml


def _norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    s = re.sub(r'\s*-\s*expandida\s*$', '', s.strip().lower())
    return re.sub(r'\s+', ' ', s)


class Fundo:
    """Um fundo com config e cadastro já resolvidos."""

    def __init__(self, key, cfg, linha_depara=None, carteira=None):
        self.key = key
        self.cfg = cfg
        self.carteira = carteira
        self.dp = linha_depara

    # --------------------------------------------------------------- config
    @property
    def nome(self):
        return self.cfg.get('nome', self.key)

    @property
    def vertical(self):
        return self.cfg.get('vertical', 'credito_privado')

    @property
    def apelidos(self):
        """Outros nomes pelos quais o fundo aparece (comentários, planilhas)."""
        return list(self.cfg.get('apelidos') or [])

    @property
    def objetivo(self):
        return (self.cfg.get('objetivo') or '').strip()

    @property
    def retorno_absoluto(self):
        """Mostra retorno do fundo + Alfa em vez de % do benchmark."""
        return self.cfg.get('retorno') == 'absoluto'

    @property
    def performance_fixa(self):
        return bool(self.cfg.get('performance_fixa'))

    @property
    def tem_relatorio(self):
        return bool(self.cfg.get('relatorio'))

    # ------------------------------------------------------------- cadastro
    @property
    def resolvido(self):
        return self.dp is not None

    @property
    def cnpj(self):
        return self.dp['cnpj'] if self.resolvido else None

    @property
    def quantum(self):
        return self.dp['quantum'] if self.resolvido else None

    @property
    def benchmark(self):
        return self.dp['benchmark'] if self.resolvido else None

    @property
    def mesa(self):
        return str(self.dp['mesa']).upper() if self.resolvido else None

    @property
    def cota_inicial(self):
        return self.dp['cota_inicial'] if self.resolvido else 1.0

    @property
    def data_inicial(self):
        return self.dp['data_inicial'] if self.resolvido else None

    def __repr__(self):
        return f'<Fundo {self.key} {"ok" if self.resolvido else "NAO RESOLVIDO"}>'


class Cadastro:
    def __init__(self, caminho_yml, depara):
        with open(caminho_yml, encoding='utf-8') as f:
            self.cfg = yaml.safe_load(f)
        self.depara = depara
        self.alias = self.cfg.get('alias', {})
        self.rotulo_taxa = self.cfg.get('rotulo_taxa', 'Taxa global')
        self.tipo_label = self.cfg.get('tipo_label', {})
        self.book_depara = self.cfg.get('book_depara', {})
        self.verticais = self.cfg.get('verticais', {})
        self._idx = {_norm(r['carteira']): r for _, r in depara.iterrows()}
        self.fundos = {}
        self.nao_resolvidos = []
        self._tomadas = set()     # carteiras já atribuídas a um fundo

        # Dois passos, e a ordem é o que corrige um erro real: "RF CP" como
        # palavra-chave casa com nove carteiras, entre elas a do Banks
        # ("TIVIO BANKS RF CP RL"). Resolvendo primeiro quem declara a carteira
        # exata, essa linha já está tomada quando a busca por palavra-chave roda,
        # e o Tivio RF CP encontra a carteira que é dele.
        itens = list((self.cfg.get('fundos') or {}).items())
        for key, c in itens:
            if (c or {}).get('carteira'):
                self.fundos[key] = self._resolver(key, c or {})
        for key, c in itens:
            if key not in self.fundos:
                self.fundos[key] = self._resolver(key, c or {})

    # ------------------------------------------------------------ resolução
    def _resolver(self, key, c):
        alvo = c.get('carteira')
        # 1 e 2: pelo nome da carteira
        if alvo:
            exata = self.depara[self.depara['carteira'] == alvo]
            if len(exata):
                return self._tomar(key, c, exata.iloc[0], alvo)
            linha = self._idx.get(_norm(alvo))
            if linha is not None:
                return self._tomar(key, c, linha, linha['carteira'])
        # 3: pelas palavras-chave
        termos = [_norm(t) for t in (c.get('busca') or [])]
        if termos:
            cand = [(n, r) for n, r in self._idx.items()
                    if all(t in n for t in termos)
                    and r['carteira'] not in self._tomadas]
            if len(cand) == 1:
                return self._tomar(key, c, cand[0][1], cand[0][1]['carteira'])
            if len(cand) > 1:
                # ainda ambíguo: prefere o nome que começa pelo nome do fundo
                # ("Tivio RF CP" -> "TIVIO RF CP …"), depois o mais curto, que é
                # o fundo cheio e não uma classe derivada (SUB/SEN/MEZ/CLASSE)
                esperado = _norm('tivio ' + (c.get('nome') or key).replace('Tivio ', ''))
                cand.sort(key=lambda x: (not x[0].startswith(esperado), len(x[0]))) 
                escolhida = cand[0][1]['carteira']
                self.nao_resolvidos.append(
                    (key, f'{len(cand)} carteiras casaram com {c.get("busca")}; '
                          f'usando "{escolhida}". Se estiver errada, escreva a '
                          f'carteira exata em configs/fundos.yml. '
                          f'Outras: {[c2[1]["carteira"] for c2 in cand[1:4]]}'))
                return self._tomar(key, c, cand[0][1], escolhida)
        # nada: registra com os candidatos mais próximos para o humano decidir
        pista = c.get('carteira') or ' '.join(c.get('busca') or [])
        prox = [r['carteira'] for n, r in self._idx.items()
                if pista and _norm(pista).split()[0] in n][:5]
        self.nao_resolvidos.append(
            (key, f'não encontrado na DePara (procurei por {pista!r}). '
                  f'Candidatos: {prox or "nenhum"}'))
        return Fundo(key, c, None, None)

    def _tomar(self, key, c, linha, carteira):
        self._tomadas.add(linha['carteira'])
        return Fundo(key, c, linha, carteira)

    # -------------------------------------------------------------- acesso
    def get(self, key):
        return self.fundos.get(self.alias.get(key, key))

    def __getitem__(self, key):
        f = self.get(key)
        if f is None:
            raise KeyError(key)
        return f

    def __contains__(self, key):
        return self.get(key) is not None

    def __iter__(self):
        return iter(self.fundos.values())

    def com_relatorio(self):
        return [f for f in self.fundos.values() if f.tem_relatorio]

    def da_vertical(self, vertical):
        return [f for f in self.fundos.values() if f.vertical == vertical]

    @property
    def performance_fixa(self):
        return {k for k, f in self.fundos.items() if f.performance_fixa}
