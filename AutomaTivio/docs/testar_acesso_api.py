# -*- coding: utf-8 -*-
"""Teste isolado de acesso à API TLDR (não depende do resto do AutomaTivio).

O QUE INSTALAR (uma vez só)
---------------------------
1. Python 3.9 ou mais novo
2. Bibliotecas:
       python -m pip install requests azure-identity
3. Azure CLI (é de onde sai o token):
       https://learn.microsoft.com/cli/azure/install-azure-cli
   e depois entrar com a conta da Tivio:
       az login

COMO RODAR
----------
    python testar_acesso_api.py
    python testar_acesso_api.py --data 2026-09-30 --fundo 940

Testa todas as rotas que o AutomaTivio usa (referencia, lista de fundos, benchmarks e,
por fundo: visao-geral, cotas, posicoes, emissores, alocacao, pnl/explosao, signoff).
Cada passo imprime OK ou FALHOU; em erro, mostra a resposta da própria API (status,
corpo e URL) e repete tudo num resumo no fim, para levar ao analista. Se tudo der OK,
a máquina está pronta para rodar o AutomaTivio com `fonte: api`.
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import date, timedelta

BASE = 'https://wa-tivio-tldr-brsouth.azurewebsites.net'
ESCOPO = 'api://ae37bc8e-f16d-47fb-99ab-9d3dd0cc2201/.default'


def ok(msg):
    print(f'  OK      {msg}')


def falhou(msg, dica=''):
    print(f'  FALHOU  {msg}')
    if dica:
        print(f'          -> {dica}')


def pegar_token():
    """Mesma ordem do AutomaTivio: DefaultAzureCredential, depois o az direto."""
    erro_azure = None
    try:
        from azure.identity import DefaultAzureCredential
        return DefaultAzureCredential().get_token(ESCOPO).token, 'DefaultAzureCredential'
    except ImportError:
        erro_azure = 'azure-identity não instalado'
    except Exception as e:  # noqa: BLE001
        erro_azure = str(e).splitlines()[0][:120]
    try:
        tok = subprocess.check_output(
            ['az', 'account', 'get-access-token', '--scope', ESCOPO,
             '--query', 'accessToken', '-o', 'tsv'],
            text=True, stderr=subprocess.STDOUT, shell=(sys.platform == 'win32')).strip()
        if tok:
            return tok, f'az (DefaultAzureCredential falhou: {erro_azure})'
    except FileNotFoundError:
        pass
    except subprocess.CalledProcessError as e:
        erro_azure = f'{erro_azure}; az: {e.output.strip()[:120]}'
    raise RuntimeError(erro_azure)


def main():
    ap = argparse.ArgumentParser(description='Testa o acesso à API TLDR')
    ap.add_argument('--data', default='2026-09-30', help='data base (AAAA-MM-DD)')
    ap.add_argument('--fundo', type=int, default=940, help='id_portfolio do fundo (940 = Banks)')
    ap.add_argument('--signoff', default='false', choices=['true', 'false'],
                    help='como o run.py usa (entradas.signoff do edicao.yml); padrão false')
    a = ap.parse_args()

    print(f'\nTeste de acesso à API TLDR\n{BASE}\n')
    falhas = 0

    print('1/3 Biblioteca requests')
    try:
        import requests
        ok(f'requests {requests.__version__}')
    except ImportError:
        falhou('requests não instalado', 'python -m pip install requests')
        return 1

    print('2/3 Token (login do Azure)')
    try:
        token, origem = pegar_token()
        ok(f'token obtido via {origem}')
    except Exception as e:  # noqa: BLE001
        falhou(f'não consegui o token: {e}',
               'instale o Azure CLI, rode `az login` com a conta da Tivio e tente de novo')
        return 1

    s = requests.Session()
    s.headers['Authorization'] = 'Bearer ' + token

    dicas = {401: 'token recusado: rode `az login` de novo',
             403: 'sem permissão: peça acesso à API ao time responsável',
             404: 'fundo/endpoint não encontrado: confira o --fundo',
             422: 'a API recusou os parâmetros (veja o detalhe abaixo)',
             503: 'API acordando ou motor montando: tente de novo em 1 minuto'}
    erros = []   # (nome, caminho, params, status, corpo) para o resumo final

    def chamar(nome, caminho, resumo, **params):
        """Chama a rota, como o AutomaTivio faz (503: até 3 tentativas). Em erro,
        imprime o que a própria API respondeu, para levar ao analista."""
        nonlocal falhas
        print(f'  {nome}: GET {caminho}  {params if params else ""}')
        r, t0 = None, time.time()
        try:
            for tentativa in range(3):
                r = s.get(BASE + caminho, params=params, timeout=90)
                if r.status_code == 503 and tentativa < 2:
                    time.sleep(3)
                    continue
                break
        except requests.RequestException as e:
            falhou(f'sem conexão com a API ({type(e).__name__}: {e})', 'confira a internet/VPN/proxy')
            erros.append((nome, caminho, params, 'sem conexão', f'{type(e).__name__}: {e}'))
            falhas += 1
            return None
        seg = time.time() - t0
        if r.status_code == 200:
            try:
                j = r.json()
            except ValueError:
                falhou(f'HTTP 200 mas a resposta não é JSON ({seg:.1f}s)', r.text[:500])
                erros.append((nome, caminho, params, 200, r.text[:2000]))
                falhas += 1
                return None
            ok(f'HTTP 200 em {seg:.1f}s | {resumo(j)}')
            return j
        corpo = r.text.strip()
        try:
            corpo = json.dumps(r.json(), ensure_ascii=False, indent=2)
        except ValueError:
            pass
        falhou(f'HTTP {r.status_code} {r.reason} em {seg:.1f}s', dicas.get(r.status_code, ''))
        print('          resposta da API:')
        for linha in (corpo[:3000] or '(corpo vazio)').splitlines():
            print(f'          | {linha}')
        print(f'          URL: {r.request.url}')
        erros.append((nome, caminho, params, r.status_code, corpo[:3000]))
        falhas += 1
        return None

    def tam(j):
        return f'{len(j)} itens' if isinstance(j, (list, dict)) else str(j)

    ini30 = (date.fromisoformat(a.data) - timedelta(days=30)).isoformat()
    f = f'/v1/carteira/fundos/{a.fundo}'
    print(f'3/3 Rotas usadas pelo AutomaTivio (fundo {a.fundo}, data {a.data}, signoff={a.signoff})')
    sg = a.signoff
    chamar('referencia', '/v1/carteira/referencia', lambda j: f'data de referência {j.get("data")}')
    chamar('lista de fundos', '/v1/carteira/rentabilidade/fundos',
           lambda j: f'{len(j if isinstance(j, list) else j.get("fundos", j))} fundos',
           data=a.data, ultima_cota='true', signoff=sg)
    chamar('benchmarks', '/v1/carteira/benchmarks', lambda j: f'{len(j)} pontos',
           symbol='CDI', inicio=ini30, fundo=a.fundo, signoff=sg)
    chamar('visao-geral', f + '/visao-geral',
           lambda j: (f"cnpj {j.get('cnpj')} | PL {j.get('pl_atual')} | início {j.get('official_initial_date')} "
                      f"| rent. 12m {j.get('rent_12m')}") if j else 'fundo inexistente (resposta vazia)',
           data=a.data, signoff=sg)
    chamar('cotas', f + '/cotas', lambda j: f'{len(j)} cotas', inicio=ini30, signoff=sg)
    chamar('posicoes', f + '/posicoes', lambda j: f'{len(j.get("positions") or [])} posições',
           data=a.data, visao='expandida', signoff=sg)
    chamar('emissores', f + '/emissores', tam, data=a.data, visao='expandida', signoff=sg)
    chamar('alocacao', f + '/alocacao',
           lambda j: f'exposição total {j.get("total_exposure")} | PL {j.get("pl")}',
           data=a.data, signoff=sg)
    chamar('pnl/explosao', f + '/pnl/explosao', tam, data=a.data, agrupamento='class', signoff=sg)
    chamar('signoff', f + '/signoff',
           lambda j: f'liberada={j.get("liberada")} cota_aprovada={j.get("cota_aprovada")} aprovado={j.get("aprovado")}',
           data=a.data)

    print()
    if falhas:
        print(f'RESULTADO: {falhas} rota(s) com falha. Resumo para o analista:\n')
        for nome, caminho, params, status, corpo in erros:
            print(f'- {nome}: {caminho} {params} -> {status}')
            print('  ' + corpo.replace('\n', '\n  ')[:1500])
        print()
        return 1
    print('RESULTADO: tudo OK. Esta máquina tem acesso a todas as rotas usadas.\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
