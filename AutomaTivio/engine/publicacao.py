# -*- coding: utf-8 -*-
"""Monta saida/_Atual/: a edição do mês organizada por área, com nome fixo.

A rodada gera a edição completa em `saida/_Historico/AAAA-MM/` (a estrutura de
trabalho: é onde a Central e os materiais interativos se enxergam por caminho
relativo). Esta etapa copia de lá só o que sai da empresa, por área:

    _Atual/
      LEIA-ME.txt
      Crédito Privado/      Relatórios/  Redes sociais/
      Crédito Estruturado/  Relatórios/  Redes sociais/  Decks/<pasta>/
      Investment Solutions/ Redes sociais/
      Previdência/          HGD30/ HYD60/  (E-mail, Informativo, Site (Saiba mais))
      Multi-área/           E-mails de Fundos de Crédito/  Decks/
      Interno/              Abrir a Central.html, Conferência.xlsx, Log da rodada.log

Os nomes de arquivo perdem o mês ("Tivio Banks - Relatório de Gestão.pdf"): o
upload substitui o arquivo do mês anterior e nenhum link precisa mudar. O mês
fica na pasta do histórico e dentro do próprio arquivo.
"""
import os
import re
import shutil
from urllib.parse import quote

from calculators import formatos as fmt

AREAS = {
    'credito_privado': 'Crédito Privado',
    'credito_estruturado': 'Crédito Estruturado',
    'investment_solutions': 'Investment Solutions',
}
MULTI = 'Multi-área'
REDES = {'credito-privado': 'Crédito Privado', 'credito-estruturado': 'Crédito Estruturado',
         'investment-solutions': 'Investment Solutions'}
EMAILS = {'agora': 'Ágora', 'btg': 'BTG', 'xp': 'XP'}
PREVIDENCIA = (('hgd30', 'HGD30'), ('hyd60', 'HYD60'))

_MES = '|'.join(fmt.MESES)
_SUFIXO_MES = re.compile(rf' - (?:{_MES}) \d{{4}}(?=\.\w+$|$)')


def sem_mes(nome):
    """'Tivio Banks - Relatório de Gestão - Setembro 2026.pdf' -> '... Gestão.pdf'."""
    return _SUFIXO_MES.sub('', nome)


class _Montador:
    def __init__(self, origem, destino):
        self.o, self.d = origem, destino
        self.n = 0
        self.faltou = []

    def _cp(self, src, *dst):
        alvo = os.path.join(self.d, *dst)
        os.makedirs(os.path.dirname(alvo), exist_ok=True)
        shutil.copy2(src, alvo)
        self.n += 1

    def arquivo(self, rel, *dst):
        src = os.path.join(self.o, *rel)
        if os.path.isfile(src):
            self._cp(src, *dst)
        else:
            self.faltou.append('/'.join(rel))

    def pasta(self, rel, *dst, renomear=None):
        """Copia a pasta inteira (e os arquivos dentro, sem o mês no nome)."""
        src = os.path.join(self.o, *rel)
        if not os.path.isdir(src):
            self.faltou.append('/'.join(rel))
            return
        for raiz, _, nomes in os.walk(src):
            sub = os.path.relpath(raiz, src)
            for nome in nomes:
                partes = [] if sub == '.' else sub.split(os.sep)
                self._cp(os.path.join(raiz, nome), *dst, *partes,
                         (renomear or sem_mes)(nome))


def _vertical_por_nome(cadastro):
    """{nome do fundo: área} a partir de configs/fundos.yml."""
    out = {}
    for f in cadastro.fundos.values():
        area = AREAS.get(f.cfg.get('vertical'))
        if area:
            out[f.nome] = area
    return out


def montar_atual(origem, destino, cadastro, edicao, log=None):
    """Recria `destino` a partir da edição completa em `origem`. Devolve o nº de arquivos."""
    from exporters.decks import carregar_config
    if os.path.isdir(destino):
        shutil.rmtree(destino)
    os.makedirs(destino)
    m = _Montador(origem, destino)
    area_de = _vertical_por_nome(cadastro)

    # ---- relatórios de gestão: PDF e PPTX por fundo + a página HTML da vertical
    pad = re.compile(r'^(.*) - Relatório de Gestão - .+\.(pdf|pptx)$')
    for pasta in ('pdf', 'pptx'):
        base = os.path.join(origem, pasta)
        for nome in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            mm = pad.match(nome)
            if not mm:
                continue
            area = area_de.get(mm.group(1))
            if area:
                m.arquivo((pasta, nome), area, 'Relatórios', sem_mes(nome))
            elif log:
                log.aviso(mm.group(1), 'publicação: fundo sem vertical em fundos.yml, relatório fora de _Atual')
    central = os.path.join(origem, 'central')
    for nome in sorted(os.listdir(central)) if os.path.isdir(central) else []:
        mm = re.match(r'^Relatório de Gestão - (.+?) - .+\.html$', nome)
        if mm and mm.group(1) in AREAS.values():
            m.arquivo(('central', nome), mm.group(1), 'Relatórios', sem_mes(nome))
            m.pasta(('central', 'vendor'), mm.group(1), 'Relatórios', 'vendor', renomear=lambda x: x)

    # ---- redes sociais: JPG de cada carrossel + o pacote PDF da vertical
    for slug, area in REDES.items():
        pasta = os.path.join(origem, 'destaques', slug)
        for nome in sorted(os.listdir(pasta)) if os.path.isdir(pasta) else []:
            if nome.lower().endswith('.jpg'):
                m.arquivo(('destaques', slug, nome), area, 'Redes sociais', nome)
        base = os.path.join(origem, 'pdf')
        for nome in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            if nome.startswith(f'Destaques - {area} - '):
                m.arquivo(('pdf', nome), area, 'Redes sociais', sem_mes(nome))

    # ---- e-mails de Fundos de Crédito: atravessam as áreas
    for pasta, nome in EMAILS.items():
        m.pasta(('emails', pasta), MULTI, 'E-mails de Fundos de Crédito', nome, renomear=lambda x: x)

    # ---- previdência: por fundo, com uma subpasta para cada coisa
    for chave, sigla in PREVIDENCIA:
        m.pasta(('emails', 'previdencia', chave), 'Previdência', sigla, 'E-mail', renomear=lambda x: x)
        base = os.path.join(origem, 'informativos')
        for nome in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            if nome.startswith(f'Informativo - {sigla} - '):
                m.arquivo(('informativos', nome), 'Previdência', sigla, 'Informativo', sem_mes(nome))
        m.arquivo(('landing page', f'tivio-{chave}-saiba-mais.html'),
                  'Previdência', sigla, 'Site (Saiba mais)', f'tivio-{chave}-saiba-mais.html')
        m.pasta(('landing page', 'vendor'), 'Previdência', sigla, 'Site (Saiba mais)', 'vendor',
                renomear=lambda x: x)

    # ---- decks: a área vem de configs/decks.yml (`area:`); ALT em Crédito
    # Estruturado, o que cruza áreas em Multi-área
    area_deck = {}
    for d in carregar_config():
        area_deck.setdefault(d.get('pasta', ''), d.get('area') or MULTI)
    base = os.path.join(origem, 'decks')
    for pasta in sorted(os.listdir(base)) if os.path.isdir(base) else []:
        area = area_deck.get(pasta, MULTI)
        sub = [pasta] if area != MULTI else []
        m.pasta(('decks', pasta), area, 'Decks', *sub)

    # ---- interno: não sai da empresa
    comp = edicao.competencia
    m.arquivo((f'conferencia_{comp}.xlsx',), 'Interno', 'Conferência.xlsx')
    m.arquivo((f'{comp}-processamento.log',), 'Interno', 'Log da rodada.log')
    index = os.path.join(origem, 'index.html')
    if os.path.isfile(index):
        rel = os.path.relpath(index, os.path.join(destino, 'Interno')).replace(os.sep, '/')
        href = quote(rel)
        alvo = os.path.join(destino, 'Interno', 'Abrir a Central.html')
        with open(alvo, 'w', encoding='utf-8') as f:
            f.write(
                '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
                f'<meta http-equiv="refresh" content="0; url={href}">'
                '<title>Central de Materiais</title></head><body style="font-family:Segoe UI,Arial">'
                f'<p>Abrindo a Central de Materiais de {edicao.mes_ano}...</p>'
                f'<p>Se não abrir sozinha: <a href="{href}">abrir a Central</a>.</p>'
                '</body></html>')
        m.n += 1
    _leia_me(destino, edicao, origem)
    m.n += 1
    if log and m.faltou:
        log.info(f'  _Atual: {len(m.faltou)} item(ns) não gerados nesta rodada: ' + ', '.join(m.faltou[:6])
                 + (' ...' if len(m.faltou) > 6 else ''))
    return m.n


def _leia_me(destino, edicao, origem):
    txt = f"""AUTOMATIVIO  |  EDIÇÃO {edicao.mes_ano.upper()}  |  DATA BASE {edicao.br}

Esta pasta (_Atual) é sempre a edição mais recente, no mesmo caminho. Os nomes
dos arquivos não têm o mês: ao publicar, o arquivo novo substitui o do mês
anterior e os links continuam valendo. A edição completa (Central, materiais
interativos, tudo o que foi gerado) fica em:
  {os.path.relpath(origem, os.path.dirname(destino)).replace(os.sep, '/')}/
e o histórico de meses anteriores está na pasta _Historico.

O QUE HÁ EM CADA PASTA
  Crédito Privado/        Relatórios (PDF e PPTX por fundo + página HTML com abas, com vendor/)
                          Redes sociais (Destaques em JPG + PDF)
  Crédito Estruturado/    Relatórios, Redes sociais e Decks (ALT, ALT 90, ALT 180)
  Investment Solutions/   Redes sociais (Destaques em JPG + PDF)
  Previdência/            HGD30 e HYD60: E-mail (PNG, HTML, .eml), Informativo (PPTX e PDF)
                          e Site (Saiba mais: a página HTML + vendor/)
  Multi-área/             E-mails de Fundos de Crédito (Ágora, BTG, XP) e os decks que
                          cruzam áreas (Crédito Privado e Estruturado, Tivio Conecta)
  Interno/                Abrir a Central.html, Conferência.xlsx e o log. Não sai da empresa.

ANTES DE PUBLICAR
  1. Ler Interno/Conferência.xlsx (abas Mudanças, Faltas e Avisos) e o log.
  2. Conferir o comentário do gestor e os números de cada material.
  3. A pasta "vendor" precisa seguir junto de cada HTML (gráficos).

O QUE O SISTEMA NÃO FAZ
  Subir para o site, enviar e-mail (Outlook ou Mailchimp), aprovar, escrever o
  comentário do gestor, e atualizar nos decks: AUM, equipe, ROA, Capacity, textos
  de política e os gráficos de mercado (veja o relatório de automatização).
"""
    with open(os.path.join(destino, 'LEIA-ME.txt'), 'w', encoding='utf-8') as f:
        f.write(txt)
