# -*- coding: utf-8 -*-
"""A data base da edição, e todas as formas em que ela aparece nos materiais.

O pedido era explícito: *nenhuma data hardcoded*. Uma variável só — `DATA_BASE`
— e dela sai tudo. Esta classe é essa variável.

A razão de existir um objeto em vez de uma constante: a mesma data aparece nos
materiais em nove formatos diferentes ("Agosto de 2026", "ago/26", "-ago26",
"31/08/2026", "AGOSTO DE 2026", `const ATUAL=7`…). Centralizar só o valor não
resolve — tem de centralizar também as *formas*, senão cada material volta a
formatar do seu jeito e a divergência reaparece.

    >>> e = Edicao('2026-08-31')
    >>> e.mes_ano, e.slug, e.competencia
    ('Agosto de 2026', 'ago26', '2026-08')
"""
from datetime import date, datetime

import pandas as pd

MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho',
         'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
MES_ABR = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set',
           'out', 'nov', 'dez']


class Edicao:
    def __init__(self, data_base):
        if isinstance(data_base, str):
            data_base = pd.Timestamp(data_base)
        elif isinstance(data_base, (date, datetime)):
            data_base = pd.Timestamp(data_base)
        self.db = pd.Timestamp(data_base).normalize()

    # ------------------------------------------------------------- formas
    @property
    def iso(self):
        """2026-08-31 — usado em atributos de dados e nomes técnicos."""
        return self.db.strftime('%Y-%m-%d')

    @property
    def br(self):
        """31/08/2026 — "Data base:" nos materiais."""
        return self.db.strftime('%d/%m/%Y')

    @property
    def mes_ano(self):
        """Agosto de 2026 — cabeçalho das páginas."""
        return f'{MESES[self.db.month - 1]} de {self.db.year}'

    @property
    def mes_ano_curto(self):
        """Agosto 2026 — cards da Central."""
        return f'{MESES[self.db.month - 1]} {self.db.year}'

    @property
    def slug(self):
        """ago26 — nome de arquivo exportado."""
        return f'{MES_ABR[self.db.month - 1]}{str(self.db.year)[2:]}'

    @property
    def competencia(self):
        """2026-08 — chave de versão (pasta de saída, conferência, log)."""
        return self.db.strftime('%Y-%m')

    @property
    def mes_nome(self):
        return MESES[self.db.month - 1]

    @property
    def mes_indice_js(self):
        """0-based: é o que os HTMLs legados usam em `const ATUAL=`."""
        return self.db.month - 1

    # ------------------------------------------------- substituições em texto
    def substituicoes(self, antiga):
        """Pares (de, para) para trocar a data de uma edição anterior no HTML.

        Recebe a `Edicao` antiga porque os materiais legados não têm marcação —
        a data está escrita no meio do texto. Sem o valor antigo não há o que
        procurar, e varrer por regex de mês pegaria datas editoriais legítimas
        (um comentário que cita "junho" como referência histórica, por exemplo).
        """
        if antiga is None or antiga.db == self.db:
            return []
        a, n = antiga, self
        return [
            (a.br, n.br),
            (a.mes_ano, n.mes_ano),
            (a.mes_ano.lower(), n.mes_ano.lower()),
            (a.mes_ano.upper(), n.mes_ano.upper()),
            (a.mes_ano_curto, n.mes_ano_curto),
            ('-' + a.slug, '-' + n.slug),
            (f'{a.mes_nome.lower()}/{a.db.year}', f'{n.mes_nome.lower()}/{n.db.year}'),
            (f'const ATUAL={a.mes_indice_js};', f'const ATUAL={n.mes_indice_js};'),
            (f'const A={a.mes_indice_js};const track', f'const A={n.mes_indice_js};const track'),
        ]

    # ------------------------------------------------------------- utilidades
    def nome_arquivo(self, base, ext):
        """'Relatório de Gestão' -> 'Relatório de Gestão - Agosto 2026.pdf'."""
        return f'{base} - {self.mes_ano_curto}.{ext.lstrip(".")}'

    def __repr__(self):
        return f'<Edicao {self.iso} · {self.mes_ano}>'

    def __eq__(self, o):
        return isinstance(o, Edicao) and o.db == self.db
