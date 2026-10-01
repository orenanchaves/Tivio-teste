# Logo 3D — Tivio Capital

Logo da marca em 3D, gerado com Blender headless. A forma vem do **SVG do
próprio dashboard** (`Index/index.html`), então é exatamente o wordmark
oficial — nada foi redesenhado à mão.

## Arquivos

| Arquivo | O que é |
|---|---|
| `logo3d.py` | o script que monta a cena e renderiza |
| `tivio_logo.svg` | o wordmark extraído do dashboard |
| `tivio_T_3d.png` | **o T isolado**, 2000×2000, metálico sobre fundo escuro |
| `tivio_T_3d_alpha.png` | o T com fundo transparente, 1400×1400 |
| `tivio_T_3d.blend` | a cena do T |
| `tivio_T_girando.mp4` | **o T girando**, 72 frames · 900×900 · 30 fps · loop |
| `tivio_T_girando.gif` | o mesmo giro em GIF, 420×420 · 24 fps (para onde MP4 não entra) |
| `tivio_logo_3d.png` | wordmark completo, 1920×1080 |
| `tivio_logo_3d_alpha.png` | wordmark com fundo transparente, 1600×700 |
| `tivio_logo_3d.blend` | a cena do wordmark |

## Rodar

```powershell
pip install bpy==4.2.0
python logo3d.py --svg tivio_logo.svg --out render.png
```

Não precisa ter o Blender instalado — `bpy` é o Blender como módulo Python,
e o render roda sem interface.

### Opções

```powershell
# só o T da Tivio
python logo3d.py --svg tivio_logo.svg --out t.png --so-t

# fundo transparente
python logo3d.py --svg tivio_logo.svg --out alpha.png --transparente

# mais volume e outro ângulo
python logo3d.py --svg tivio_logo.svg --out hero.png `
    --profundidade 0.18 --azimute 22 --elevacao 9

# qualidade de apresentação
python logo3d.py --svg tivio_logo.svg --out final.png `
    --largura 3840 --altura 2160 --amostras 400

# salvar a cena para mexer no Blender
python logo3d.py --svg tivio_logo.svg --out x.png --salvar-blend cena.blend

# o T girando, em MP4
python logo3d.py --svg tivio_logo.svg --out tivio_T_girando.mp4 `
    --so-t --animar 72 --fps 30 --largura 900 --altura 900 --amostras 32

# o giro como sequência de PNG (extensão sem vídeo = PNGs numerados)
python logo3d.py --svg tivio_logo.svg --out seq/giro_ `
    --so-t --animar 48 --transparente
```

| Flag | Default | O que faz |
|---|---|---|
| `--profundidade` | 0.12 | espessura da extrusão (relativa à largura) |
| `--azimute` | 11 | giro da câmera em graus |
| `--elevacao` | 5 | altura da câmera em graus |
| `--giro` | 0 | rotação do logo no eixo Z |
| `--amostras` | 96 | qualidade do Cycles (mais = mais limpo e mais lento) |
| `--so-t` | — | só o T, descartando o resto do wordmark |
| `--transparente` | — | fundo alfa |
| `--chao` | — | adiciona piso (o padrão é a peça flutuando) |
| `--animar` | 0 | nº de frames de um giro completo (0 = imagem parada) |
| `--fps` | 30 | quadros por segundo do vídeo |
| `--eixo` | Z | eixo do giro — `Z` é mesa girante, `Y` é cambalhota |

## Cores

Saem da paleta do Design System, convertidas de sRGB para linear (o
Blender trabalha em linear; passar o hex direto deixa a cor lavada):

| Token | Hex | Uso |
|---|---|---|
| `--tv-verde` | `#C1F4D4` | cor base do metal |
| `--bg-base` | `#0A0F14` | fundo e chão |

## Como o T é isolado

O wordmark tem 19 contornos. O T são três — braço esquerdo, haste e braço
direito da travessa — no canto superior esquerdo, entre x 0,006 e 0,064.
Há folga limpa até o "I" começar em 0,076, então o corte por coordenada é
seguro, e um piso em y descarta a linha de CAPITAL.

Não é recorte de imagem: são os contornos vetoriais originais, extrudados
do mesmo jeito que o wordmark inteiro.

## O acabamento metálico

Metal não tem cor própria — ele mostra o que está em volta. Três coisas
fazem a diferença entre metal e plástico pintado:

1. **`Metallic` em 1.0.** Abaixo disso o shader mistura difuso e o
   resultado lê como plástico colorido.
2. **Placas emissivas em volta** (`estudio()`). Luz de área ilumina, mas
   o reflexo que o olho lê como metal vem de uma *superfície* visível no
   espelhamento. Elas ficam invisíveis para a câmera e aparecem só no
   reflexo.
3. **Fundo escuro para a câmera, claro para o reflexo.** Um nó
   `Is Camera Ray` separa os dois: o estúdio precisa ser claro para o
   metal ter o que refletir, mas claro no fundo deixa a imagem lavada.

Há ainda um ruído fino modulando a rugosidade — sem ele o reflexo fica
perfeito demais e artificial.

## O giro

`--animar N` keyframa uma volta completa de 2π em N frames. Dois detalhes
que não são óbvios:

**A última chave vai no frame N+1, não em N.** 0° e 360° são a mesma pose.
Fechando o range em N o loop repete um quadro e dá um tranco visível a cada
volta.

**A interpolação tem que ser linear.** O default do Blender é Bézier, que
acelera no começo e freia no fim — ótimo para um movimento que termina,
péssimo para um loop infinito, onde fica com cara de solavanco. O script
força `LINEAR` em todas as fcurves.

Sobre o GIF: ele não sai do Blender. GIF tem 1 bit de alfa, então borda
recortada fica serrilhada. O caminho é renderizar PNG transparente e
compor sobre o fundo da marca (`#0A0F14`) antes de montar o GIF — foi
assim que `tivio_T_girando.gif` foi feito.

O render roda em **Cycles em CPU** (~3 s/frame a 900×900 e 32 amostras).
EEVEE seria muito mais rápido, mas precisa de `libEGL`, que não existe
neste container — se você rodar numa máquina com GPU e EEVEE disponível,
vale trocar o engine.

## Quatro coisas que deram errado no caminho

Ficam registradas porque qualquer ajuste futuro vai esbarrar nelas.

**A ordem das operações.** Normalizar a curva e extrudar depois distorce o
wordmark — alternar `dimensions` entre 2D e 3D em volta de
`transform_apply` achatou o logo, com CAPITAL invadindo TIVIO. O caminho
que funciona é: extrudar ainda como curva (o preenchimento das faces só
acontece no modo 2D), converter para malha, e só então centralizar e
normalizar.

**A profundidade é relativa.** O SVG importa com ~0,24 unidade de largura,
então `extrude = 0.12` fazia a peça sair mais funda que larga. O script
escala a profundidade pelo tamanho importado.

**A elevação da câmera.** Acima de ~10° a espessura de TIVIO cobre o topo
de CAPITAL e o logo fica ilegível. O default é 5°.

**O chão.** Com piso espelhado o reflexo do softbox estourava e roubava a
peça; com piso difuso claro o chão tomava metade do quadro. O ambiente do
estúdio já dá o assentamento, então a peça flutua por padrão e `--chao`
traz o piso de volta.
