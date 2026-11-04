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

Cada passo imprime OK ou FALHOU e, no segundo caso, o que fazer. Se tudo der OK,
a máquina está pronta para rodar o AutomaTivio com `fonte: api`.
"""
import argparse
import subprocess
import sys

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
    a = ap.parse_args()

    print(f'\nTeste de acesso à API TLDR\n{BASE}\n')
    falhas = 0

    print('1/4 Biblioteca requests')
    try:
        import requests
        ok(f'requests {requests.__version__}')
    except ImportError:
        falhou('requests não instalado', 'python -m pip install requests')
        return 1

    print('2/4 Token (login do Azure)')
    try:
        token, origem = pegar_token()
        ok(f'token obtido via {origem}')
    except Exception as e:  # noqa: BLE001
        falhou(f'não consegui o token: {e}',
               'instale o Azure CLI, rode `az login` com a conta da Tivio e tente de novo')
        return 1

    s = requests.Session()
    s.headers['Authorization'] = 'Bearer ' + token

    def chamar(passo, caminho, **params):
        nonlocal falhas
        print(passo)
        try:
            r = s.get(BASE + caminho, params=params, timeout=90)
        except requests.RequestException as e:
            falhou(f'sem conexão com a API ({type(e).__name__})', 'confira a internet/VPN/proxy')
            falhas += 1
            return None
        if r.status_code == 200:
            return r.json()
        dicas = {401: 'token recusado: rode `az login` de novo',
                 403: 'sem permissão: peça acesso à API ao time responsável',
                 404: 'fundo/endpoint não encontrado: confira o --fundo',
                 503: 'API acordando: tente de novo em 1 minuto'}
        falhou(f'{caminho} -> HTTP {r.status_code}', dicas.get(r.status_code, r.text[:150]))
        falhas += 1
        return None

    j = chamar('3/4 Endpoint simples (/v1/carteira/referencia)', '/v1/carteira/referencia')
    if j is not None:
        ok(f'resposta: {j}')

    j = chamar(f'4/4 Dados do fundo {a.fundo} em {a.data} (visao-geral)',
               f'/v1/carteira/fundos/{a.fundo}/visao-geral', data=a.data, signoff='false')
    if j is not None:
        ok(f"cnpj {j.get('cnpj')} | cota {j.get('cota_atual')} | PL {j.get('pl_atual')} | "
           f"início {j.get('official_initial_date')} | rent. 12m {j.get('rent_12m')}")

    print()
    if falhas:
        print('RESULTADO: há falhas acima. Corrija e rode de novo.\n')
        return 1
    print('RESULTADO: tudo OK. Esta máquina tem acesso à API.\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
