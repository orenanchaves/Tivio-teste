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
    def __init__(self, edicao, log):
        self.edicao = edicao
        self.log = log
        self.divergencias = []
        self.faltantes = []

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

        # 5) comentário: existe? cita o mês certo?
        if not ctx.comentario:
            self.faltantes.append([k, nome, 'comentário do gestor',
                                   'não preenchido no arquivo de comentários'])
        else:
            texto = ' '.join(ctx.comentario).lower()
            atual = MESES[self.edicao.db.month - 1].lower()
            for mes in MESES:
                if mes.lower() != atual and re.search(rf'\b{mes.lower()}\b', texto):
                    self.divergencias.append(
                        [k, nome, 'comentário',
                         f'cita "{mes}" — a data base é {atual}/{self.edicao.db.year}'])
                    break

        return len(self.divergencias) + len(self.faltantes) - antes

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
