# -*- coding: utf-8 -*-
"""conferencia.xlsx — a revisão humana antes de publicar.

Abas pedidas: Mudanças · Dados faltantes · Fundos sem atualização ·
Rentabilidades · Taxas. Mais duas que a prática exige: Arquivos (o que saiu, em
que formato, com que tamanho) e Divergências.

A aba Divergências é a que justifica o projeto. A análise apontou o Infra Plus
saindo no e-mail com 1,10% e no post com 1,24% — o número do benchmark no lugar
do fundo. Como agora os três materiais leem o mesmo contexto, esse erro não pode
nascer; mas o mesmo teste continua rodando, contra o material *publicado*, para
pegar o caso em que alguém editou o HTML à mão depois de gerar.

As checagens são de sanidade, não de gosto:
  · fundo e benchmark idênticos em todos os períodos -> provável troca de coluna
  · % do CDI fora de 0-300% -> provável unidade errada
  · carteira mais velha que 45 dias -> dado do mês anterior
  · comentário citando outro mês -> texto não revisado
"""
import os
import re

import pandas as pd

from calculators import formatos as fmt
from engine.edicao import MESES

PERIODOS = ['mes', 'ano', '12m', '24m', '36m', 'inicio']


class Conferencia:
    def __init__(self, edicao, log, spreads=None):
        self.edicao = edicao
        self.log = log
        self.divergencias = []
        self.faltantes = []
        # Percentuais da tabela de Mercado de Crédito. O comentário do gestor
        # cita os spreads do mercado ("passando de CDI + 1,19% para CDI +
        # 1,22%"), que não são valores do fundo — sem esta lista eles viravam
        # divergência toda edição, e um aviso que sempre aparece é um aviso que
        # ninguém lê.
        self.do_mercado = self._percentuais_do_mercado(spreads)

    @staticmethod
    def _percentuais_do_mercado(spreads):
        valores = set()
        for tabela in (spreads or {}).values():
            for linha in tabela.get('linhas', []):
                for celula in linha.get('celulas', []):
                    m = re.fullmatch(r'-?(\d{1,3}(?:,\d{1,2})?)%', str(celula).strip())
                    if m:
                        valores.add(round(float(m.group(1).replace(',', '.')), 2))
        return valores

    # ------------------------------------------------------------- checagens
    def checar(self, ctx):
        """Roda todas as checagens de um fundo. Devolve nº de problemas."""
        antes = len(self.divergencias) + len(self.faltantes)
        k, nome = ctx.key, ctx.nome

        if not ctx.tem_dados:
            self.faltantes.append([k, nome, 'rentabilidade', 'sem cotas na dados_mensais'])
            return 1

        # 1) fundo == benchmark em todos os períodos: coluna trocada
        pares = [(ctx.valor(p, 'fundo'), ctx.valor(p, 'bench')) for p in PERIODOS]
        pares = [(a, b) for a, b in pares if a is not None and b is not None]
        if len(pares) >= 3 and all(abs(a - b) < 1e-9 for a, b in pares):
            self.divergencias.append(
                [k, nome, 'rentabilidade', 'fundo idêntico ao benchmark em todos os '
                 'períodos — conferir se a coluna de cota não é a do índice'])

        # 2) % do benchmark fora da faixa plausível
        for p in PERIODOS:
            pct = ctx.valor(p, 'pct')
            if pct is None or pd.isna(pct):
                continue
            if not (0 < pct < 3.0):
                self.divergencias.append(
                    [k, nome, f'% do benchmark ({p})',
                     f'{fmt.pct_cdi(pct)} fora da faixa 0–300% — conferir unidade '
                     f'ou sinal do benchmark'])

        # 3) carteira defasada
        if ctx.cart and ctx.cart.get('data') is None:
            self.divergencias.append(
                [k, nome, 'carteira', 'linhas sem data na Base Carteira — a alocação '
                 'exibida pode ser de outro mês; conferir a coluna Data da planilha'])
        elif ctx.cart and ctx.cart.get('data') is not None:
            atraso = (self.edicao.db - pd.Timestamp(ctx.cart['data'])).days
            if atraso > 45:
                self.divergencias.append(
                    [k, nome, 'carteira',
                     f'posição de {pd.Timestamp(ctx.cart["data"]):%d/%m/%Y}, '
                     f'{atraso} dias antes da data base'])
        elif not ctx.cart:
            self.faltantes.append([k, nome, 'carteira', 'sem linhas na Base Carteira'])

        # 4) dados que o material mostra e que podem vir vazios
        for campo, valor in (('PL', ctx.pl), ('PL médio 12m', ctx.pl_medio),
                             ('taxa global', ctx.taxa), ('carrego', ctx.carrego),
                             ('duration', ctx.duration)):
            if valor is None:
                self.faltantes.append([k, nome, campo, 'não calculado nesta edição'])

        # 5) números digitados no comentário × números calculados
        self._conferir_numeros_do_comentario(ctx)

        # 6) comentário: existe? cita o mês certo?
        if not ctx.comentario:
            self.faltantes.append([k, nome, 'comentário do gestor',
                                   'não preenchido no arquivo de comentários'])
        else:
            atual = MESES[self.edicao.db.month - 1].lower()
            citado = self._mes_de_referencia(' '.join(ctx.comentario))
            if citado and citado != atual:
                self.divergencias.append(
                    [k, nome, 'comentário',
                     f'o texto se refere a "{citado}" como o mês corrente — a data '
                     f'base é {atual}/{self.edicao.db.year}. Conferir se o comentário '
                     f'é o desta edição.'])

        return len(self.divergencias) + len(self.faltantes) - antes

    def _mes_de_referencia(self, texto):
        """Mês que o texto trata como o mês da edição, ou None.

        Distinção que evita avisar à toa: um comentário de agosto diz
        legitimamente "os spreads abriram 5 bps **em relação a julho**" — citar
        outro mês como comparação é normal. O que não é normal é abrir o
        parágrafo com "**Em setembro**, iniciamos posição" num relatório de
        agosto: aí o texto é de outra edição.

        Então procuramos a construção que marca o mês corrente ("Em <mês>,",
        "No mês de <mês>"), e não qualquer aparição do nome do mês.
        """
        nomes = '|'.join(m.lower() for m in MESES)
        padrao = (rf'(?:^|[.!?]\s+|\n)\s*(?:em|no mês de|durante|ao longo de)\s+'
                  rf'({nomes})\b')
        for m in re.finditer(padrao, (texto or '').lower()):
            # "em relação a julho" / "em comparação com julho" não contam
            antes = texto.lower()[max(0, m.start() - 40):m.start(1)]
            if re.search(r'rela[çc][ãa]o|compara|frente|versus|ante\b|contra\b', antes):
                continue
            return m.group(1)
        return None

    # ----------------------------------------------- números dentro do texto
    # O texto do gestor é intocável — nem uma vírgula muda. Mas um percentual
    # digitado ali é uma afirmação sobre o fundo, e foi assim que o relatório
    # saiu dizendo 1,01% enquanto o e-mail dizia 1,23%. Então o texto não é
    # reescrito: é conferido. O que não bater vira linha na aba Divergencias.
    #
    # A comparação é por conjunto, não por posição: procuramos cada percentual
    # escrito entre os valores que o fundo tem nesta edição (retorno, benchmark,
    # % do benchmark, carrego, alocação em crédito, nos períodos todos). Um
    # número que não aparece em lugar nenhum é o suspeito.
    def _conferir_numeros_do_comentario(self, ctx):
        if not ctx.comentario or not ctx.tem_dados:
            return
        # o texto como sai publicado: depois da sincronização com a tabela
        texto = ' '.join(ctx.comentario_preenchido)
        escritos = re.findall(r'(?<![\w,.])(\d{1,3}(?:,\d{1,2})?)%', texto)
        if not escritos:
            return

        plausiveis = set()
        for per in PERIODOS:
            for campo in ('fundo', 'bench', 'alfa', 'pct', 'bench_mais'):
                v = ctx.valor(per, campo)
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    continue
                plausiveis.add(round(abs(v) * 100, 2))
            a = ctx.pct_anualizado(per)
            if a:
                plausiveis.add(round(a * 100, 2))
        for v in (ctx.carrego, ctx.duration):
            if v is not None:
                plausiveis.add(round(abs(v) * 100, 2))
        if ctx.cart:
            plausiveis.add(round(ctx.cart['credito'] * 100, 2))
            for serie in ('setores', 'rating'):
                for x in ctx.cart[serie]:
                    plausiveis.add(round(abs(x) * 100, 2))
        plausiveis |= self.do_mercado

        # Tolerância relativa, não absoluta — e a diferença importa. Uma folga
        # fixa de 1 p.p. aceitaria 1,01% no lugar de 1,10%, que é exatamente o
        # erro que esta checagem existe para pegar. Com folga relativa de 0,5%,
        # 101% passa por 100,59% (arredondamento legítimo) e 1,01% não passa por
        # 1,10%. Também aceitamos o valor truncado, porque escrever "75%" para
        # 75,7% é escolha editorial corrente, não erro.
        def perto(n):
            for p in plausiveis:
                if abs(n - p) <= max(0.005 * p, 0.051):
                    return True
                if round(p) == n or int(p) == n:
                    return True
            return False

        suspeitos = []
        for s in set(escritos):
            n = float(s.replace(',', '.'))
            # números pequenos e redondos são do texto de mercado (spreads de
            # 0,03%, overcollateral de 25%, alocação mínima de 15%), não do fundo
            if n in (0.0, 1.0, 5.0, 15.0, 25.0) or n > 2000:
                continue
            if not perto(n):
                suspeitos.append(s + '%')

        if suspeitos:
            self.divergencias.append(
                [ctx.key, ctx.nome, 'números no comentário',
                 'o texto cita ' + ', '.join(sorted(suspeitos)) +
                 ' — nenhum bate com um valor calculado deste fundo nesta edição. '
                 'Conferir se o texto é do mês certo (o sistema não altera o texto).'])

    # ---------------------------------------------------------------- planilha
    def gravar(self, contextos, cadastro, taxas, destino):
        rent, tx = [], []
        for ctx in contextos:
            if not ctx.tem_dados:
                continue
            for p in PERIODOS:
                v = ctx.rent.get(p) or {}
                rent.append([ctx.key, ctx.nome, ctx.f.carteira, ctx.benchmark, p,
                             ctx.rent['refs'][p].date() if ctx.rent.get('refs') else None,
                             v.get('fundo'), v.get('bench'), v.get('alfa'),
                             v.get('pct'), v.get('bench_mais')])
            tx.append([ctx.key, ctx.nome, ctx.f.cnpj, ctx.taxa, ctx.perf,
                       'sim' if ctx.f.performance_fixa else 'não'])

        sem_atualizacao = [[k, '', msg] for k, msg in cadastro.nao_resolvidos]
        for ctx in contextos:
            if not ctx.tem_dados and ctx.f.resolvido:
                sem_atualizacao.append([ctx.key, ctx.f.carteira or '',
                                        'resolvido na DePara, mas sem cotas no período'])

        abas = {
            'Mudancas': pd.DataFrame(self.log.mudancas,
                                     columns=['arquivo', 'fundo', 'campo', 'antes', 'depois']),
            'Divergencias': pd.DataFrame(self.divergencias,
                                         columns=['fundo', 'nome', 'onde', 'o_que_conferir']),
            'Dados faltantes': pd.DataFrame(self.faltantes,
                                            columns=['fundo', 'nome', 'campo', 'motivo']),
            'Fundos sem atualizacao': pd.DataFrame(sem_atualizacao,
                                                   columns=['fundo', 'carteira', 'motivo']),
            'Rentabilidades': pd.DataFrame(rent, columns=[
                'fundo', 'nome', 'carteira', 'benchmark', 'periodo', 'data_ref',
                'fundo_pct', 'bench_pct', 'alfa', 'pct_bench', 'bench_mais_aa']),
            'Taxas': pd.DataFrame(tx, columns=[
                'fundo', 'nome', 'cnpj', 'taxa_global', 'performance', 'performance_fixa']),
            'Avisos': pd.DataFrame(self.log.avisos,
                                   columns=['arquivo', 'fundo', 'aviso']),
            'Arquivos': pd.DataFrame(self.log.arquivos,
                                     columns=['arquivo', 'formato', 'bytes']),
        }
        os.makedirs(os.path.dirname(destino) or '.', exist_ok=True)
        with pd.ExcelWriter(destino, engine='openpyxl') as w:
            for nome, df in abas.items():
                if df.empty:
                    df = pd.DataFrame({'(nada nesta edição)': []})
                df.to_excel(w, sheet_name=nome[:31], index=False)
                ws = w.sheets[nome[:31]]
                for col in ws.columns:
                    largura = max((len(str(c.value or '')) for c in col), default=10)
                    ws.column_dimensions[col[0].column_letter].width = min(58, max(11, largura + 2))
        return destino

    @property
    def resumo(self):
        return (f'{len(self.divergencias)} divergências · '
                f'{len(self.faltantes)} dados faltantes')
