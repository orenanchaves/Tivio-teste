# Validar com o analista — abas Low Vol e TOP Credit via API

Data base conferida: 30/09/2026. Origem: `loaders/abas_is_api.py`.

## TOP Credit
1. **Quadro "Tipo"**: a API (`alocacao.by_class`) dá Caixa 37,0% e LF 14,2%; a planilha tinha Caixa 43,9% e LF 10,2%. Qual é a base correta (% do PL, % da exposição, outra)?
2. **Top 5 de emissores**: pela API entraria o **C6** (PnL 3,19 / 2,8% do PL), que a planilha omitia. Foi exclusão proposital?

## Low Vol
3. **Regra book → macro-estratégia** (inferida dos números, bate com a planilha):
   - `Juros >> X` → "Juros X"; FX, Termo, IBOV, Offshore e Provisões ficam como estão;
   - `Padrão` e `Caixa` → Caixa;
   - todo o resto (LF Sênior, Crédito, LFSC, LFSN, FIDC Sênior, Deb, CDB, DPGE...) → Crédito.
   Confirmar se está certo.

## Ambos
4. **Alpha** = `Alpha` + `Trade` da API; a diferença para a planilha é de 0,1 a 0,3 bps (Debênture, Provisões, FIDC Sr). Aceitável?
5. **Vol 12m**: 0,94% na API contra 0,93% na planilha. Aceitável?
