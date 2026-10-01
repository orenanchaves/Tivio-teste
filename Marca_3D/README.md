# Logo 3D — Tivio Capital

Logo da marca em 3D, gerado com Blender headless. A forma vem do **SVG do
próprio dashboard** (`Index/index.html`), então é exatamente o wordmark
oficial — nada foi redesenhado à mão.

## Arquivos

| Arquivo | O que é |
|---|---|
| `logo3d.py` | o script que monta a cena e renderiza |
| `tivio_logo.svg` | o wordmark extraído do dashboard |
| `tivio_logo_3d.png` | render 1920×1080 com fundo e chão |
| `tivio_logo_3d_alpha.png` | 1600×700 com fundo transparente, para deck e dashboard |
| `tivio_logo_3d.blend` | a cena, para abrir no Blender e ajustar à mão |

## Rodar

```powershell
pip install bpy==4.2.0
python logo3d.py --svg tivio_logo.svg --out render.png
```

Não precisa ter o Blender instalado — `bpy` é o Blender como módulo Python,
e o render roda sem interface.

### Opções

```powershell
# fundo transparente, sem chão
python logo3d.py --svg tivio_logo.svg --out alpha.png --transparente

# mais volume e outro ângulo
python logo3d.py --svg tivio_logo.svg --out hero.png `
    --profundidade 0.18 --azimute 22 --elevacao 9

# qualidade de apresentação
python logo3d.py --svg tivio_logo.svg --out final.png `
    --largura 3840 --altura 2160 --amostras 400

# salvar a cena para mexer no Blender
python logo3d.py --svg tivio_logo.svg --out x.png --salvar-blend cena.blend
```

| Flag | Default | O que faz |
|---|---|---|
| `--profundidade` | 0.12 | espessura da extrusão (relativa à largura) |
| `--azimute` | 11 | giro da câmera em graus |
| `--elevacao` | 5 | altura da câmera em graus |
| `--giro` | 0 | rotação do logo no eixo Z |
| `--amostras` | 96 | qualidade do Cycles (mais = mais limpo e mais lento) |
| `--transparente` | — | alfa e sem chão |

## Cores

Saem da paleta do Design System, convertidas de sRGB para linear (o
Blender trabalha em linear; passar o hex direto deixa a cor lavada):

| Token | Hex | Uso |
|---|---|---|
| `--tv-verde` | `#C1F4D4` | cor base do metal |
| `--bg-base` | `#0A0F14` | fundo e chão |

## Três coisas que deram errado no caminho

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
