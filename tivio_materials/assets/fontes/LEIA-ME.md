# Fontes locais

Coloque aqui os arquivos da **Versos** e o PDF passa a sair com a tipografia
correta **sem depender de rede**:

```
assets/fontes/
├─ Versos-ExtraLight.woff2     (peso 200/300)
├─ Versos-Regular.woff2        (400)
├─ Versos-SemiBold.woff2       (600)
└─ Versos-Bold.woff2           (700)
```

Aceita `.woff2`, `.woff`, `.ttf` e `.otf`. O nome do arquivo define o peso:
`ExtraLight`/`Light` → 200/300 · `Regular`/`Book` → 400 · `Medium` → 500 ·
`SemiBold` → 600 · `Bold` → 700.

## Por que isto existe

O `@font-face` dos materiais busca a Versos em duas fontes, nesta ordem:

1. `local("Versos Regular")` — a fonte instalada na máquina;
2. o CDN da marca (`cdn-sites-assets.mziq.com`).

Nas máquinas do time a Versos está instalada e o passo 1 resolve. Mas o PDF pode
ser gerado em outro lugar — um servidor, um agendamento, um container de CI — onde
a fonte não está instalada e o CDN pode estar bloqueado. Aí o Chromium cai para a
fonte de fallback: o PDF sai, com a métrica do texto diferente, e ninguém nota
olhando o terminal.

Com os arquivos nesta pasta, o `run.py` os embute no HTML como data URI antes de
gerar o PDF. A fonte vai **dentro** do arquivo: o resultado é idêntico em qualquer
máquina, com ou sem rede.

Se a pasta estiver vazia, nada quebra — o comportamento é o atual, e a conferência
avisa quando a fonte não carregou.
