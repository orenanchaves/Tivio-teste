"""Status de liberação e aprovação (sign-off) dos fundos mapeados na API TLDR.

    python scripts/status_signoff.py                      # data base do edicao.yml
    python scripts/status_signoff.py --data 2026-09-30
    python scripts/status_signoff.py -o saida/status.html

Lê os fundos com `id_portfolio` em configs/fundos.yml e consulta, um a um,
GET /v1/carteira/fundos/{id}/signoff?data=AAAA-MM-DD. Grava o relatório em
saida/status_signoff.html (token: o mesmo do run.py, .env ou autenticação normal).
"""
import argparse
import html
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

import yaml

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from loaders.api_tldr import ClienteApi  # noqa: E402

BRASILIA = timezone(timedelta(hours=-3))


def _data_base(arg):
    if arg:
        return arg
    with open(os.path.join(RAIZ, 'configs', 'edicao.yml'), encoding='utf-8') as f:
        db = (yaml.safe_load(f) or {}).get('data_base')
    if db:
        return str(db)
    return (date.today().replace(day=1) - timedelta(days=1)).isoformat()


def _fundos():
    with open(os.path.join(RAIZ, 'configs', 'fundos.yml'), encoding='utf-8') as f:
        cad = (yaml.safe_load(f) or {}).get('fundos') or {}
    return [(k, c.get('nome') or k, int(c['id_portfolio'])) for k, c in cad.items() if c.get('id_portfolio')]


def _brasilia(texto):
    """'2026-10-29 18:33:33.336862+00' -> '29/10/2026 15:33'."""
    if not texto:
        return ''
    try:
        d = datetime.fromisoformat(str(texto).replace(' ', 'T'))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(BRASILIA).strftime('%d/%m/%Y %H:%M')
    except ValueError:
        return str(texto)


def _data_br(iso):
    try:
        return datetime.strptime(str(iso)[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
    except ValueError:
        return str(iso or '')


def _consulta(api, data, fundo):
    chave, nome, cod = fundo
    linha = {'chave': chave, 'nome': nome, 'id': cod, 'erro': None}
    try:
        s = api.get(f'/v1/carteira/fundos/{cod}/signoff', data=data)
    except Exception as e:
        linha['erro'] = repr(e)
        return linha
    eventos = s.get('eventos') or []
    vigente = eventos[0] if eventos else None        # o mais recente da data
    linha.update(
        liberada=bool(s.get('liberada')), cota=bool(s.get('cota_aprovada')),
        aprovado=bool(s.get('aprovado')), ultima=s.get('ultima_aprovada'),
        quando=_brasilia(vigente['created_at']) if vigente and s.get('aprovado') else '',
        quem=(vigente or {}).get('usuario') or '',
        ultimo_evento=(f"{vigente['acao']} em {_brasilia(vigente['created_at'])}"
                       + (f" — {vigente['motivo']}" if vigente.get('motivo') else '')) if vigente else '')
    return linha


def _selo(ok, sim='sim', nao='não'):
    return f'<span class="selo {"ok" if ok else "nao"}">{sim if ok else nao}</span>'


def _html(data, linhas, gerado):
    cab = ('Fundo', 'Id', 'Liberada', 'Cota aprovada', 'Aprovado', 'Aprovado em', 'Por', 'Última aprovada', 'Último evento')
    corpo = []
    for l in linhas:
        if l['erro']:
            corpo.append(f'<tr><td>{html.escape(l["nome"])}</td><td>{l["id"]}</td>'
                         f'<td colspan="7" class="erro">erro na API: {html.escape(l["erro"])}</td></tr>')
            continue
        corpo.append(
            f'<tr><td>{html.escape(l["nome"])}</td><td>{l["id"]}</td>'
            f'<td>{_selo(l["liberada"])}</td><td>{_selo(l["cota"])}</td>'
            f'<td>{_selo(l["aprovado"])}</td><td>{html.escape(l["quando"] or "—")}</td>'
            f'<td>{html.escape(l["quem"] or "—")}</td><td>{html.escape(_data_br(l["ultima"]) if l["ultima"] else "—")}</td>'
            f'<td>{html.escape(l["ultimo_evento"] or "—")}</td></tr>')
    ok = [l for l in linhas if not l['erro']]
    resumo = (f'{sum(l["liberada"] for l in ok)} liberados · {sum(l["aprovado"] for l in ok)} aprovados '
              f'· {len(linhas)} fundos' + (f' · {len(linhas) - len(ok)} com erro' if len(ok) != len(linhas) else ''))
    return f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Status de sign-off {_data_br(data)}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:24px;color:#1B3A36}}
h1{{font-size:20px;margin:0}} p{{color:#555;margin:4px 0 16px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left}}
th{{background:#1B3A36;color:#fff}} tr:hover td{{background:#f3faf6}}
.selo{{padding:2px 8px;border-radius:10px;font-weight:600;font-size:12px}}
.ok{{background:#d8f1e3;color:#1c6b3d}} .nao{{background:#fde2e2;color:#a12626}}
.erro{{color:#a12626}}
</style></head><body>
<h1>Status de sign-off — data base {_data_br(data)}</h1>
<p>{resumo} · gerado em {gerado}</p>
<table><thead><tr>{''.join(f'<th>{c}</th>' for c in cab)}</tr></thead>
<tbody>{''.join(corpo)}</tbody></table>
</body></html>'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', help='AAAA-MM-DD (padrão: data_base do configs/edicao.yml)')
    ap.add_argument('-o', '--saida', default=os.path.join(RAIZ, 'saida', 'status_signoff.html'))
    args = ap.parse_args()

    data = _data_base(args.data)
    api = ClienteApi()
    print(f'sign-off em {data} (token via {api.origem_token})')
    with ThreadPoolExecutor(max_workers=6) as ex:
        linhas = list(ex.map(lambda f: _consulta(api, data, f), _fundos()))
    for l in linhas:
        estado = 'ERRO' if l['erro'] else f"liberada={'S' if l['liberada'] else 'N'} aprovado={'S' if l['aprovado'] else 'N'}"
        print(f"  {l['id']:>5}  {l['nome'][:40]:<40} {estado}")

    os.makedirs(os.path.dirname(args.saida), exist_ok=True)
    with open(args.saida, 'w', encoding='utf-8') as f:
        f.write(_html(data, linhas, datetime.now(BRASILIA).strftime('%d/%m/%Y %H:%M')))
    print(f'gravado: {args.saida}')


if __name__ == '__main__':
    main()
