# Selos do rodapé dos relatórios

Coloque aqui os quatro arquivos que aparecem na faixa do disclaimer:

```
assets/selos/
├─ qr.png          QR Code dos fundos
├─ anbima1.png     Selo ANBIMA — Distribuição de Produtos de Investimento
├─ anbima2.png     Selo ANBIMA — Gestão de Recursos de Terceiros
└─ pri.png         Signatory of PRI
```

Aceita `.png`, `.jpg` e `.svg`.

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

Pasta vazia: o relatório usa as URLs oficiais como reserva (abaixo), e a
conferência avisa que os selos podem não sair nas exportações.

| Selo | URL oficial |
|---|---|
| qr | `https://www.tivio.com/wp-content/uploads/sites/1532/2026/08/QR-Code-scaled.png` |
| anbima1 | `https://www.tivio.com/wp-content/uploads/sites/1532/2026/07/selo-distribuicao.png` |
| anbima2 | `https://www.tivio.com/wp-content/uploads/sites/1532/2026/07/selo-02-scaled.png` |
| pri | `https://www.tivio.com/wp-content/uploads/sites/1532/2026/08/PRI.png` |

As URLs têm a data no caminho (`/2026/07/`) porque o WordPress organiza assim —
quando a área de marketing substituir um selo, a URL muda e esta tabela precisa
acompanhar. É mais um motivo para manter os arquivos aqui.
