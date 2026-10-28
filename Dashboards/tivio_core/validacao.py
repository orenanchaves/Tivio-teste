# -*- coding: utf-8 -*-
"""Checagens que rodam a cada atualizacao.

Existe porque erro de dado aqui nao levanta excecao: aparece semanas
depois como numero errado no dashboard. Ver DIAGNOSTICO_AGOSTO.md, onde
um recorte sem ano somou tres anos num numero que passou por plausivel.
"""
import pandas as pd


def resumo(df: pd.DataFrame, chave: str = None, data: str = None,
           rotulo: str = "base") -> dict:
    """Imprime e devolve os indicadores basicos da base."""
    print(f"\n  validacao da {rotulo}")
    print(f"     linhas ................. {len(df)}")

    achados = {"linhas": len(df)}

    if chave and chave in df:
        dup = int(df[chave].duplicated().sum())
        vazio = int(df[chave].fillna("").astype(str).str.strip().eq("").sum())
        achados.update(duplicados=dup, sem_chave=vazio)

        print(f"     {chave} duplicado{'':<8} {dup}"
              f"{'  <- conferir na origem' if dup else ''}")
        print(f"     {chave} vazio{'':<12} {vazio}")

    if data and data in df:
        dt = pd.to_datetime(df[data], errors="coerce", dayfirst=True)
        validas = dt.notna().sum()
        achados["datas_invalidas"] = int(len(df) - validas)

        print(f"     datas invalidas ........ {len(df) - validas}")

        if validas:
            print(f"     periodo ................ "
                  f"{dt.min():%d/%m/%Y} a {dt.max():%d/%m/%Y}")
            porano = dt.dt.year.value_counts().sort_index()
            print("     por ano ................ "
                  + " · ".join(f"{int(a)}: {int(n)}" for a, n in porano.items()))

    return achados


def conferir_contra(esperado: dict, obtido: dict, rotulo: str) -> bool:
    """Compara numeros do dashboard com os da planilha de referencia."""
    print(f"\n  conferencia contra {rotulo}")
    print(f"     {'METRICA':<28}{'PLANILHA':>12}{'DASHBOARD':>12}  ")
    print("     " + "-" * 56)

    tudo_ok = True

    for k, v_esp in esperado.items():
        v_obt = obtido.get(k)
        ok = (v_obt is not None
              and abs(float(v_obt) - float(v_esp)) < max(1, abs(float(v_esp)) * 0.005))
        tudo_ok = tudo_ok and ok

        print(f"     {k:<28}{v_esp:>12}{str(v_obt):>12}  "
              f"{'ok' if ok else '<- DIVERGE'}")

    return tudo_ok
