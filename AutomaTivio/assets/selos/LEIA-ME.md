# Selos do rodapé dos relatórios

```
assets/selos/
├─ anbima1.png     Selo ANBIMA — Distribuição de Produtos de Investimento
├─ anbima2.png     Selo ANBIMA — Gestão de Recursos de Terceiros
├─ pri.png         Signatory of PRI
└─ qr.png          QR Code dos fundos        (FALTANDO — ver abaixo)
```

Os três primeiros foram **extraídos dos relatórios PPTX publicados**, onde vêm
embutidos no arquivo. Aceita `.png`, `.jpg` e `.svg`.

## O QR Code

É o único que não veio dos PPTX: ali ele entra por link externo, não embutido.
Enquanto o arquivo não estiver nesta pasta, o relatório usa a URL do site
(`tivio.com/wp-content/uploads/sites/1532/2026/08/QR-Code-scaled.png`) e a
conferência avisa.

Para resolver: salve o QR Code do site como `qr.png` aqui.

## Por que local, e não a URL

Os materiais da Central referenciam os selos em `tivio.com/wp-content/uploads/…`.
Para ver na tela funciona. Para **exportar**, não: o `html2canvas` precisa que o
servidor da imagem responda com cabeçalho CORS, e o WordPress não responde. O
material original contorna isso buscando a imagem por proxies públicos
(`corsproxy.io`, `allorigins`) e convertendo em dataURL — se um deles cair, o
selo vira um quadrado vazio no JPG exportado, e isso só aparece depois.

Com os arquivos nesta pasta, o `run.py` os embute no HTML em base64. O selo vai
dentro do documento: aparece na tela, no PDF, no JPG e no PPTX, sem rede e sem
proxy de terceiro.

## Uma armadilha na extração

No PPTX, o **nome do shape não corresponde ao conteúdo da imagem**: o shape
chamado `anbima-distribuicao-de-produtos-de-investimento` contém o selo de
*Gestão de Recursos*, e vice-versa. Os arquivos aqui foram nomeados pelo que a
imagem mostra, não pelo nome do shape. Se for reextrair, confira olhando.

## URLs oficiais (reserva)

| Selo | URL |
|---|---|
| qr | `https://www.tivio.com/wp-content/uploads/sites/1532/2026/08/QR-Code-scaled.png` |
| anbima1 | `https://www.tivio.com/wp-content/uploads/sites/1532/2026/07/selo-distribuicao.png` |
| anbima2 | `https://www.tivio.com/wp-content/uploads/sites/1532/2026/07/selo-02-scaled.png` |
| pri | `https://www.tivio.com/wp-content/uploads/sites/1532/2026/08/PRI.png` |

As URLs têm a data no caminho (`/2026/07/`) porque o WordPress organiza assim —
quando marketing substituir um selo, a URL muda. É mais um motivo para manter os
arquivos aqui.
