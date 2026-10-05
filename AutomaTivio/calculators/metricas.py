"""Cálculos por fundo — réplica das fórmulas da aba 'Tabela e Gráficos Carteira'
e da aba 'Dados' da dados_mensais.xlsx.

Referências (planilha):
  C6  mês    = WORKDAY(1º dia do mês, -1)
  D6  ano    = WORKDAY(1º de janeiro, -1)
  E6  12M    = WORKDAY(data base, -251)      F6 24M = -503   G6 36M = -755
  H6  início = primeira cota do fundo         (cada data = MAX(data, H6))
  C8  fundo  = cota(data base) / cota(ref) - 1
  C9  bench  = índice(data base) / índice(ref) - 1
  C10 alfa = fundo - bench | C11 % = fundo/bench | C12 bench+ = anualizado (252)
  B15 carrego = Σ(taxa·exposição)/PL | C15 duration = Σ(dur·exp)/PL/252
  D15 % crédito = exposição sem Caixa/DAP / PL | E15 PL médio 12M | F15 PL
"""
import numpy as np
import pandas as pd

RATINGS = ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-', 'B+', 'B', 'B-']
PERIODOS = ['mes', 'ano', '12m', '24m', '36m', 'inicio']


class Calc:
    def __init__(self, dados, data_base=None):
        self.d = dados
        self.hol = np.array(dados['feriados'].dt.date.values, dtype='datetime64[D]')
        self.db = pd.Timestamp(data_base) if data_base else self.ultimo_fechamento(dados['fundos']['data'].max())

    def ultimo_fechamento(self, d):
        """Último dia útil do último mês completo disponível."""
        fim = self.workday(pd.Timestamp(d.year, d.month, 1) + pd.offsets.MonthEnd(0) + pd.Timedelta(days=1), -1)
        return d if d >= fim else self.workday(pd.Timestamp(d.year, d.month, 1), -1)

    # ---------- calendário ----------
    def workday(self, d, n):
        return pd.Timestamp(np.busday_offset(np.datetime64(d.date()), n, roll='forward', holidays=self.hol))

    def du(self, a, b):
        return int(np.busday_count(np.datetime64(a.date()), np.datetime64(b.date()) + 1, holidays=self.hol)) - 1

    # ---------- séries ----------
    def serie_fundo(self, quantum):
        f = self.d['fundos']
        s = f[(f['nome'] == quantum) & (f['data'] <= self.db)].set_index('data')
        return s[~s.index.duplicated(keep='last')]

    def serie_indice(self, nome):
        i = self.d['indices']
        s = i[i['nome'] == nome].set_index('data')['valor']
        return s[~s.index.duplicated(keep='last')]

    @staticmethod
    def asof(s, d):
        s = s[s.index <= d]
        return float(s.iloc[-1]) if len(s) else np.nan

    # ---------- rentabilidade ----------
    def refs(self, inicio):
        db = self.db
        r = {
            'mes': self.workday(pd.Timestamp(db.year, db.month, 1), -1),
            'ano': self.workday(pd.Timestamp(db.year, 1, 1), -1),
            '12m': self.workday(db, -251),
            '24m': self.workday(db, -503),
            '36m': self.workday(db, -755),
            'inicio': inicio,
        }
        trunc = {k: (v < inicio) for k, v in r.items()}
        return {k: max(v, inicio) for k, v in r.items()}, trunc

    def rentabilidade(self, quantum, bench):
        sf = self.serie_fundo(quantum)
        if sf.empty:
            return None
        cota = sf['cota']
        idx = self.serie_indice(bench)
        inicio = sf.index.min()
        refs, trunc = self.refs(inicio)
        c_db, i_db = self.asof(cota, self.db), self.asof(idx, self.db)
        out = {'inicio': inicio, 'refs': refs}
        for p in PERIODOS:
            ref = refs[p]
            f = c_db / self.asof(cota, ref) - 1
            b = i_db / self.asof(idx, ref) - 1 if len(idx) else np.nan
            n = self.du(ref, self.db)
            # período maior que a vida do fundo -> '−' (exceto 'desde o início')
            vazio = trunc[p] and p != 'inicio'
            out[p] = None if vazio else {
                'fundo': f, 'bench': b, 'alfa': f - b,
                'pct': (f / b) if b else np.nan,
                'bench_mais': ((1 + f) ** (252 / n) / (1 + b) ** (252 / n) - 1) if n > 0 else np.nan,
            }
        # PL
        pl = sf['pl']
        out['pl'] = self.asof(pl, self.db)
        out['pl_medio_12m'] = float(pl[pl.index >= refs['12m']].mean())
        out['pl_medio_inicio'] = float(pl.mean())
        return out

    # ---------- histórico mensal (aba Dados W:Y) ----------
    def historico(self, quantum, bench, cota_inicial=1.0, data_inicial=None, janela_meses=None):
        sf = self.serie_fundo(quantum)
        if sf.empty:
            return None
        ini = max(pd.Timestamp(data_inicial) if pd.notna(data_inicial) else sf.index.min(), sf.index.min())
        cota = sf['cota'][sf.index >= ini]
        idx = self.serie_indice(bench)
        fim_mes = cota.groupby([cota.index.year, cota.index.month]).tail(1)
        if janela_meses:
            fim_mes = fim_mes.iloc[-(janela_meses + 1):]
            base_c = float(fim_mes.iloc[0])
            base_d = fim_mes.index[0]
        else:
            base_c = cota_inicial if pd.notna(data_inicial) else float(cota.iloc[0])
            base_d = ini
        base_i = self.asof(idx, base_d)
        l, f, c = [], [], []
        for d, v in fim_mes.items():
            l.append(d.strftime('%Y-%m'))
            f.append(round((v / base_c - 1) * 100, 2))
            c.append(round((self.asof(idx, d) / base_i - 1) * 100, 2))
        return {'b': bench, 'l': l, 'f': f, 'c': c}

    # ---------- carteira (aba Dados B:U) ----------
    def carteira(self, nome_carteira, mesa, pl):
        c = self.d['carteira']
        todas = c[c['Carteira'] == nome_carteira]
        ultima = todas['Data'].max()
        if pd.isna(ultima):
            # carteira sem data na planilha: usa todas as linhas do fundo e
            # devolve data=None, para quem consome saber que não há como
            # confirmar de que mês é a posição
            c, ultima = todas, None
        else:
            # posição sem data na Base Carteira também é da carteira atual
            # (setembro/2026: no ALT 90, duas cotas sênior e um caixa vinham
            # sem data e o FIDC Sênior saía 66,7% em vez de 76,7%)
            c = todas[(todas['Data'] == ultima) | todas['Data'].isna()]
        if c.empty or not pl:
            return None
        hg = str(mesa).upper() == 'HG'
        exp = c['Exposição']

        def grupo(col, base):
            g = base.groupby(col)['Exposição'].sum() / pl
            return g[g != 0].sort_values(ascending=False)

        # emissores: HG exclui FIDC; ordena; remove Caixa
        base_em = c[~c['FIDC']] if hg else c
        emissores = grupo('Emissor', base_em)
        emissores = emissores[emissores.index != 'Caixa']
        # setores: HG = Setor (sem FIDC) + linha 'FIDC' ; HY/IS = Setor Aj.
        if hg:
            setores = grupo('Setor', c[~c['FIDC']])
            fidc = c[c['FIDC']]['Exposição'].sum() / pl
            if fidc:
                setores = pd.concat([setores, pd.Series({'FIDC': fidc})]).sort_values(ascending=False)
            tipos = grupo('Tipo', c)
        else:
            setores = grupo('Setor Aj.', c)
            tipos = grupo('Tipo aj.', c)
        rating = (c.groupby('Rating Externo')['Exposição'].sum() / pl).reindex(RATINGS).fillna(0)
        # 'Book' é a estratégia da posição (FIDC Sênior, FIDC Mezanino, Caixa…).
        # É o que os relatórios de Crédito Estruturado chamam de "Alocação por
        # Estratégia" — um corte que o relatório de high grade não usa.
        estrategia = grupo('Book', c) if 'Book' in c.columns else None
        # (Book, Tipo aj.): o "Padrão" do Book é posição SEM book; o tipo do
        # ativo na mesma linha decide para onde ela vai (engine/contexto.py)
        book_tipo = None
        if 'Book' in c.columns and 'Tipo aj.' in c.columns:
            book_tipo = c.groupby(['Book', 'Tipo aj.'])['Exposição'].sum() / pl
        credito = c[~c['Setor'].isin(['Caixa', 'DAP'])]['Exposição'].sum() / pl
        return {
            'emissores': emissores, 'setores': setores, 'tipos': tipos, 'rating': rating,
            'estrategia': estrategia, 'book_tipo': book_tipo,
            'carrego': float((c['Taxa'] * exp).sum() / pl),
            'duration': float((c['duration'] * exp).sum() / pl / 252),
            'credito': float(credito),
            'data': ultima,
        }
