# Monitor de Novas Ofertas · FII — origem dos dados

**Tivio Capital** · 15/09/2026

## Estado

| Item | Situação |
|---|---|
| Template | `templates/dashboard_ofertas_fii.html` |
| Fonte hoje | `Excel - Guia de Base de Dados/Monitor_FII.xlsx`, aba `Ofertas_FII` |
| Fonte alvo | `sql/ofertas_fii.sql` — **não validado** |
| Regenerável hoje | sim, `python atualizar_fii.py` |

## O SQL não está confirmado

A tabela de ofertas públicas **não aparece em nenhum SQL existente** do projeto.
Os ambientes que já rodam usam `anbima_*` e `cvm_informe_diario`, que são
cadastro e movimentação — não trazem oferta pública.

O `sql/ofertas_fii.sql` foi escrito por analogia (nomes de coluna no padrão dos
outros SQLs) e aponta para `{catalog}.{schema}.cvm_ofertas_publicas`, **que é um
palpite**. Por isso o default é `FONTE=excel`.

Para descobrir a tabela real, rodar o `buscar_cadastro_cvm.py` do Monitor de
Novos Fundos apontando para outras pistas:

```sql
SELECT table_catalog, table_schema, table_name
FROM system.information_schema.tables
WHERE lower(table_name) RLIKE 'oferta|emissao|distribuicao|rcvm160'
```

Confirmada a tabela, ajustar o `FROM` e as colunas do SQL e rodar com
`FONTE=databricks`.

## Conferência contra o Excel

O Excel tem **239 ofertas**; o HTML entregue tinha **218**. A regeneração
atualiza para 239 — período de 02/02/2026 a 31/07/2026.

A validação reporta **24 CNPJs repetidos**. São emissões diferentes do mesmo
FII (`Nr. Emissao` 1, 2, 3…), não duplicidade de dado — o CNPJ não é chave única
aqui, a chave é CNPJ + número da emissão.

## Contadores fixos do template

O template trazia o total escrito à mão em **dez lugares** (`218`), que não
acompanhava o dado: o cabeçalho dizia 218 enquanto o KPI calculado em JS dizia
239. `atualizar_fii.py` agora reescreve os dez a cada execução.
