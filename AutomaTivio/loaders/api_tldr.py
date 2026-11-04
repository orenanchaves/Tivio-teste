# -*- coding: utf-8 -*-
"""Fonte de dados de mercado pela API TLDR, no lugar da dados_mensais.xlsx.

Devolve o MESMO dicionário que `loaders.planilha.ler_dados_mensais`
(`depara`, `indices`, `fundos`, `carteira`, `feriados`) mais `rent_api`, com as
rentabilidades prontas. Assim `Calc`, `Contexto` e os renderizadores não mudam.

De onde vem cada coisa:
  fundos     configs/fundos.yml: `id_portfolio` e `mesa` de cada fundo (o fundo é
             sempre buscado por esse id, nunca por nome ou CNPJ)
  depara     visao-geral (CNPJ, benchmark, data de início)
  fundos     GET /fundos/{id}/cotas            (cota e PL, PL em R$ milhões)
  indices    GET /benchmarks                   (um por símbolo)
  carteira   GET /fundos/{id}/posicoes + /emissores (rating), traduzidas pelo
             configs/de_para_api.yml para a taxonomia da Base Carteira
  rent_api   GET /fundos/{id}/visao-geral      (mês, ano, 12m, 24m, 36m, desde o início e % do bench)
  feriados   não há fonte: são os dias úteis em que o CDI não tem valor

Token: DefaultAzureCredential (az login). `signoff=false` mostra a data pedida
mesmo sem aprovação do Risco; `true` só devolve dado aprovado.
"""
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests
import yaml

BASE = 'https://wa-tivio-tldr-brsouth.azurewebsites.net'
ESCOPO = 'api://ae37bc8e-f16d-47fb-99ab-9d3dd0cc2201/.default'

PERIODOS_API = {'mes': 'mtd', 'ano': 'ytd', '12m': '12m', '24m': '24m', '36m': '36m',
                'inicio': 'inception'}


RAIZ = Path(__file__).resolve().parent.parent


def _ler_env(chave):
    """Lê `chave` do ambiente ou do arquivo .env na raiz do projeto (sem dependência extra)."""
    valor = os.environ.get(chave, '')
    arq = RAIZ / '.env'
    if not valor.strip() and arq.exists():
        for linha in arq.read_text(encoding='utf-8').splitlines():
            linha = linha.strip()
            if linha and not linha.startswith('#') and '=' in linha:
                k, v = linha.split('=', 1)
                if k.strip() == chave:
                    valor = v.strip().strip('"').strip("'")
    return valor.strip()


def _token():
    """(token, origem). Origem: '.env', 'azure-identity' ou 'az login'."""
    # token manual no .env (TIVIO_API_TOKEN); vazio = autenticação normal
    manual = _ler_env('TIVIO_API_TOKEN')
    if manual:
        return manual.removeprefix('Bearer ').strip(), '.env (TIVIO_API_TOKEN)'
    try:
        from azure.identity import DefaultAzureCredential
        return DefaultAzureCredential().get_token(ESCOPO).token, 'autenticação normal (azure-identity)'
    except Exception:
        # mesma identidade do `az login`, sem exigir o azure-identity
        return subprocess.check_output(
            ['az', 'account', 'get-access-token', '--scope', ESCOPO,
             '--query', 'accessToken', '-o', 'tsv'], text=True).strip(), 'autenticação normal (az login)'


class ClienteApi:
    def __init__(self):
        self.s = requests.Session()
        token, self.origem_token = _token()
        self.s.headers['Authorization'] = 'Bearer ' + token

    def get(self, caminho, **params):
        for tentativa in range(3):
            r = self.s.get(BASE + caminho, params=params, timeout=90)
            if r.status_code == 503 and tentativa < 2:     # motor montando: tenta de novo
                time.sleep(3)
                continue
            r.raise_for_status()
            return r.json()


def _cnpj_fmt(d):
    d = re.sub(r'\D', '', str(d or ''))
    return f'{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}' if len(d) == 14 else d


def _serie_benchmark(api, simbolo, fundo, signoff):
    j = api.get('/v1/carteira/benchmarks', symbol=simbolo, inicio='1990-01-01',
                fundo=fundo, signoff=signoff)
    s = pd.DataFrame(j)
    if s.empty:
        return pd.DataFrame(columns=['nome', 'data', 'valor'])
    return pd.DataFrame({'nome': simbolo, 'data': pd.to_datetime(s['data_referencia']),
                         'valor': pd.to_numeric(s['valor'], errors='coerce')})


def _carteira(api, cod, nome, mesa, db, signoff, mapas, nao_mapeados):
    pos = api.get(f'/v1/carteira/fundos/{cod}/posicoes', data=db, visao='expandida', signoff=signoff)
    p = pd.DataFrame(pos.get('positions') or [])
    if p.empty:
        return pd.DataFrame()
    try:
        em = pd.DataFrame(api.get(f'/v1/carteira/fundos/{cod}/emissores', data=db,
                                  visao='expandida', signoff=signoff))
        rating = dict(zip(em['issuer'], em['rating'])) if len(em) else {}
    except Exception:  # noqa: BLE001
        rating = {}

    def traduz(valor, mapa, onde):
        if valor in mapa:
            return mapa[valor]
        if valor is not None and str(valor) != 'nan':
            nao_mapeados.add((onde, str(valor)))
        return valor

    hg = str(mesa).upper() == 'HG'
    setor_hg, setor_aj = mapas.get('setor_hg', {}), mapas.get('setor_aj', {})
    tipo_aj, tipo_hg = mapas.get('tipo_aj', {}), mapas.get('tipo_hg', {})
    sector, classe = p['sector'], p['instrument_class']
    return pd.DataFrame({
        'Nome': p['symbol'], 'Carteira': nome, 'Data': pd.to_datetime(p['ref_date']),
        'Book': p['book_name'].fillna('').str.replace(r'^Crédito >> ', '', regex=True),
        'Quantidade': p['quantity'], 'Preço': p['price'],
        'Taxa': pd.to_numeric(p['spread'], errors='coerce').fillna(0.0) / 100,
        'duration': pd.to_numeric(p['duration'], errors='coerce').fillna(0.0) * 252,
        'Exposição': pd.to_numeric(p['exposure'], errors='coerce').fillna(0.0),
        'Tipo': [traduz(c, tipo_hg, 'tipo') if hg else c for c in classe],
        'Setor': [traduz(s, setor_hg, 'setor_hg') if hg else s for s in sector],
        'Emissor': p['issuer'],
        'Rating Externo': p['issuer'].map(rating).fillna('NA'),
        'HGHY': mapas.get('hghy_padrao', 'HG'),
        'FIDC': classe.fillna('').str.upper().str.startswith('FIDC'),
        'Setor Aj.': [traduz(s, setor_hg if hg else setor_aj, 'setor_hg' if hg else 'setor_aj')
                      for s in sector],
        'Tipo aj.': [traduz(c, tipo_aj, 'tipo_aj') for c in classe],
    })


def fundos_do_cadastro(caminho_fundos, log=print):
    """Fundos do configs/fundos.yml que têm `id_portfolio`.

    `nome` = o `carteira` do cadastro; sem ele, o nome do fundo na API (que o
    Cadastro casa pelo `busca`, como fazia com a DePara da planilha).
    """
    with open(caminho_fundos, encoding='utf-8') as f:
        cad = (yaml.safe_load(f) or {}).get('fundos') or {}
    linhas = []
    for key, cfg in cad.items():
        if not cfg.get('id_portfolio'):
            log(f'  AVISO [{key}] sem id_portfolio em configs/fundos.yml: fora da fonte API')
            continue
        linhas.append({'key': key, 'nome': cfg.get('carteira'),
                       'id_portfolio': int(cfg['id_portfolio']), 'mesa': cfg.get('mesa', 'HG')})
    return pd.DataFrame(linhas)


def ler_dados_api(caminho_fundos, caminho_mapas, data_base=None, signoff=False, log=print):
    signoff = 'true' if signoff in (True, 'true', 'True') else 'false'
    api = ClienteApi()
    log(f'  API TLDR: token via {api.origem_token}')
    dep = fundos_do_cadastro(caminho_fundos, log)
    with open(caminho_mapas, encoding='utf-8') as f:
        mapas = yaml.safe_load(f) or {}
    log(f'  API TLDR: {len(dep)} fundos (signoff={signoff})')

    cdi = _serie_benchmark(api, 'CDI', int(dep['id_portfolio'].iloc[0]), signoff)
    if cdi.empty:
        raise RuntimeError('a API não devolveu a série do CDI')
    if not data_base:
        # último dia com CDI antes do mês corrente: o fechamento do mês anterior
        ref = pd.Timestamp(api.get('/v1/carteira/referencia')['data'])
        data_base = cdi.loc[cdi['data'] < ref.replace(day=1), 'data'].max()
    db = pd.Timestamp(data_base)
    dbs = db.strftime('%Y-%m-%d')

    nao_mapeados, avisos = set(), []

    def um(linha):
        cod, mesa = int(linha['id_portfolio']), linha['mesa']
        vg = api.get(f'/v1/carteira/fundos/{cod}/visao-geral', data=dbs, signoff=signoff)
        if not vg:
            log(f"  AVISO [{linha['key']}] id_portfolio {cod} não existe na API: fundo fora desta edição")
            return None
        ini = vg.get('official_initial_date') or '1990-01-01'
        cot = pd.DataFrame(api.get(f'/v1/carteira/fundos/{cod}/cotas', inicio=ini, signoff=signoff))
        if not cot.empty:
            cot['data'] = pd.to_datetime(cot['data_referencia'])
            cot = cot[cot['data'] <= db]
        nome = linha['nome'] if isinstance(linha['nome'], str) and linha['nome'] \
            else (str(cot['nome_fundo_maravi'].iloc[-1]) if len(cot) else linha['key'])
        cart = _carteira(api, cod, nome, mesa, dbs, signoff, mapas, nao_mapeados)
        return cod, nome, mesa, vg, cot, cart

    with ThreadPoolExecutor(max_workers=6) as ex:
        resultados = [r for r in ex.map(um, [r for _, r in dep.iterrows()]) if r]

    depara, fundos, carteiras, rent_api, bench = [], [], [], {}, {}
    for cod, nome, mesa, vg, cot, cart in resultados:
        if cot.empty:
            avisos.append((nome, 'a API não devolveu cotas até a data base'))
            continue
        simbolo = vg.get('benchmark_symbol') or 'CDI'
        # a API corta o benchmark na data de início do fundo informado: usa o mais antigo
        ini = pd.Timestamp(vg['official_initial_date']) if vg.get('official_initial_date') else pd.Timestamp.max
        for sim in {simbolo, 'CDI'}:
            if sim not in bench or ini < bench[sim][0]:
                bench[sim] = (ini, cod)
        depara.append({'carteira': nome, 'cnpj': _cnpj_fmt(vg.get('cnpj')), 'quantum': nome,
                       'quantum2': nome, 'benchmark': simbolo, 'mesa': mesa,
                       # a 1ª cota da série é a base do histórico desde o início
                       'cota_inicial': float(cot['cota'].iloc[0]),
                       'data_inicial': pd.Timestamp(vg['official_initial_date'])
                       if vg.get('official_initial_date') else pd.NaT})
        fundos.append(pd.DataFrame({'nome': nome, 'data': cot['data'],
                                    'pl': pd.to_numeric(cot['pl'], errors='coerce') * 1e6,
                                    'cota': pd.to_numeric(cot['cota'], errors='coerce')}))
        if not cart.empty:
            carteiras.append(cart)
        else:
            avisos.append((nome, 'a API não devolveu posições'))
        rent_api[nome] = {p: {'fundo': vg.get(f'rent_{k}'), 'pct': vg.get(f'pct_bench_{k}')}
                          for p, k in PERIODOS_API.items()}
        rent_api[nome]['ultima_cota'] = vg.get('last_date')

    indices = [_serie_benchmark(api, simbolo, cod, signoff) for simbolo, (_, cod) in bench.items()]
    indices = pd.concat(indices, ignore_index=True)
    cdi = indices[indices['nome'] == 'CDI']

    # feriado = dia útil em que o CDI não tem valor (a API não entrega calendário)
    uteis = pd.bdate_range(cdi['data'].min(), cdi['data'].max())
    feriados = pd.Series(uteis.difference(pd.DatetimeIndex(cdi['data'])))

    for onde, valor in sorted(nao_mapeados):
        avisos.append(('de_para_api', f'{onde}: "{valor}" sem tradução em configs/de_para_api.yml'))
    for nome, msg in avisos:
        log(f'  AVISO [{nome}] {msg}')

    return {
        'depara': pd.DataFrame(depara),
        'indices': indices.sort_values('data'),
        'fundos': pd.concat(fundos, ignore_index=True).sort_values('data'),
        'carteira': pd.concat(carteiras, ignore_index=True) if carteiras else pd.DataFrame(),
        'feriados': feriados,
        'rent_api': rent_api,
        'data_base': db,
        'avisos': avisos,
    }
