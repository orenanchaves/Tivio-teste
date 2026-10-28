# -*- coding: utf-8 -*-
"""
patch_cobertura.py · Monitor de Novos Fundos · Tivio Capital

Insere no atualizar_monitor.py um bloco de cobertura SEGMENTADA de taxas,
separando fundos tradicionais de veiculos estruturados.

Motivacao (diagnostico 14/09/2026):
    A linha "taxa adm 3794/11733" dava impressao de falha no pipeline, mas a
    lacuna e de cadastro da ANBIMA e se concentra em estruturados:

        Acoes ......... 499/984   = 51%
        Previdencia ... 492/779   = 63%
        ETF ........... 96/129    = 74%
        Renda Fixa .... 1062/3156 = 34%
        Multimercados . 1078/2956 = 36%
        FIDC .......... 264/2252  = 12%   <- estruturado
        FIP ........... 129/778   = 17%   <- estruturado
        FIAGRO ........ 23/177    = 13%   <- estruturado

    FIDC + FIP + FIAGRO = 3.207 classes com apenas 416 taxas informadas.
    Nesses veiculos a remuneracao costuma estar no regulamento, nao no
    cadastro padrao - portanto a ausencia e esperada, nao um erro.

Uso:
    python patch_cobertura.py

O script e idempotente: rodar varias vezes nao duplica o bloco.
Gera backup atualizar_monitor.py.bak na primeira execucao.
"""

import re
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ALVO = BASE / "atualizar_monitor.py"

MARCADOR = "# --- cobertura segmentada (patch_cobertura.py) ---"

ANCORA = 'com_link = int((df["link_cvm"].fillna("").str.strip() != "").sum())'

BLOCO = '''
    # --- cobertura segmentada (patch_cobertura.py) ---
    # Estruturados (FIDC/FIP/FIAGRO) raramente informam taxa no cadastro
    # ANBIMA: a remuneracao fica no regulamento. Medir os dois grupos
    # juntos subestima a qualidade do dado dos fundos tradicionais.
    ESTRUTURADOS = ("FIDC", "FIP", "FIAGRO")

    _cat = df["categoria_n1"].fillna("").str.upper().str.strip()
    _eh_estrut = _cat.isin([s.upper() for s in ESTRUTURADOS])

    _trad = df[~_eh_estrut]
    _estr = df[_eh_estrut]

    def _cob(sub, coluna):
        """(preenchidos, total, percentual) para uma coluna numerica."""
        tot = len(sub)
        if tot == 0:
            return 0, 0, 0.0
        ok = int(pd.to_numeric(sub[coluna], errors="coerce").notna().sum())
        return ok, tot, (ok / tot * 100)

    _ta_t, _tt_t, _tp_t = _cob(_trad, "taxa_adm")
    _pa_t, _pt_t, _pp_t = _cob(_trad, "taxa_perf")
    _ta_e, _tt_e, _tp_e = _cob(_estr, "taxa_adm")
    _pa_e, _pt_e, _pp_e = _cob(_estr, "taxa_perf")

    print("  cobertura de taxas por perfil de veiculo")
    print(
        f"     tradicionais  ({_tt_t:>5} classes) "
        f"adm {_ta_t:>5} ({_tp_t:4.1f}%) | "
        f"perf {_pa_t:>5} ({_pp_t:4.1f}%)"
    )
    print(
        f"     estruturados  ({_tt_e:>5} classes) "
        f"adm {_ta_e:>5} ({_tp_e:4.1f}%) | "
        f"perf {_pa_e:>5} ({_pp_e:4.1f}%)"
    )
    print(
        "     obs: baixa cobertura em FIDC/FIP/FIAGRO e esperada "
        "(taxa no regulamento)"
    )

    # detalhe por categoria, ordenado pelo tamanho da base
    print("  cobertura de taxa adm por categoria")
    for _categoria, _sub in sorted(
        df.groupby(_cat),
        key=lambda kv: len(kv[1]),
        reverse=True,
    ):
        if not _categoria:
            _categoria = "(sem categoria)"
        _ok, _tot, _pct = _cob(_sub, "taxa_adm")
        _flag = " *" if _categoria in [s.upper() for s in ESTRUTURADOS] else ""
        print(f"     {_categoria:<16} {_ok:>5}/{_tot:<5} ({_pct:5.1f}%){_flag}")
    print("     * veiculo estruturado - ausencia esperada")
    # --- fim cobertura segmentada ---
'''


def main():
    if not ALVO.exists():
        print(f"[ERRO] nao encontrei {ALVO.name} nesta pasta.")
        print(f"       rode o script dentro de Update_Monitor_Novos_Fundos.")
        sys.exit(1)

    codigo = ALVO.read_text(encoding="utf-8")

    if MARCADOR in codigo:
        print("[skip] o patch ja foi aplicado anteriormente. Nada a fazer.")
        return

    if ANCORA not in codigo:
        print("[ERRO] nao encontrei a linha de ancora esperada:")
        print(f"       {ANCORA}")
        print("       o arquivo pode ter sido alterado. Nada foi modificado.")
        sys.exit(1)

    backup = ALVO.with_suffix(".py.bak")
    if not backup.exists():
        shutil.copy2(ALVO, backup)
        print(f"[backup] {backup.name} criado.")

    # descobre a indentacao real da linha de ancora
    match = re.search(r"^([ \t]*)" + re.escape(ANCORA), codigo, flags=re.M)
    indent = match.group(1)

    linha_ancora = indent + ANCORA
    codigo = codigo.replace(linha_ancora, linha_ancora + "\n" + BLOCO.rstrip(), 1)

    ALVO.write_text(codigo, encoding="utf-8")
    print(f"[ok] bloco inserido em {ALVO.name}.")
    print("     rode: python atualizar_monitor.py")


if __name__ == "__main__":
    main()
