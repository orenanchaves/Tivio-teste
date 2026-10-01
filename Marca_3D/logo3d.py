# -*- coding: utf-8 -*-
"""
logo3d.py - logo da Tivio Capital em 3D, via Blender headless (modulo bpy).

    python logo3d.py --svg tivio_logo.svg --out render.png

O SVG do wordmark vem do proprio dashboard (Index/index.html), entao a
forma e exatamente a da marca - nada e redesenhado a mao.

Cores saem da paleta do Design System:
    --tv-verde            #C1F4D4
    --tv-verde-escuro     #92D3AB
    --tv-verde-light-accent #337F51
    --tv-verde-ink        #0A2415
    --bg-base (escuro)    #0A0F14
"""
import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

# ----------------------------------------------------------------- paleta
VERDE = (0.757, 0.957, 0.831, 1.0)        # #C1F4D4
VERDE_ESC = (0.573, 0.827, 0.671, 1.0)    # #92D3AB
VERDE_ACC = (0.200, 0.498, 0.318, 1.0)    # #337F51
INK = (0.039, 0.141, 0.082, 1.0)          # #0A2415
FUNDO = (0.039, 0.059, 0.078, 1.0)        # #0A0F14


def _srgb_linear(c):
    """Blender trabalha em linear; os hex da marca sao sRGB."""
    def f(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), c[3])


def limpar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def importar_svg(caminho: Path):
    """SVG -> curvas. Cada subpath vira um objeto de curva."""
    antes = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=str(caminho))
    novos = [o for o in bpy.data.objects if o not in antes]

    if not novos:
        sys.exit("  ! nenhuma curva importada do SVG")

    print(f"  {len(novos)} curva(s) importada(s)")
    return novos


def juntar(curvas):
    """Une tudo num objeto so, para extrudar e materializar de uma vez."""
    bpy.ops.object.select_all(action="DESELECT")

    for c in curvas:
        c.select_set(True)

    bpy.context.view_layer.objects.active = curvas[0]

    if len(curvas) > 1:
        bpy.ops.object.join()

    return bpy.context.view_layer.objects.active


def extrudar_e_converter(obj, profundidade=0.12, chanfro=0.012):
    """Da volume AINDA como curva e so entao converte para malha.

    A ordem importa. Tentei primeiro normalizar a curva e extrudar
    depois: alternar dimensions 2D->3D->2D em volta de transform_apply
    distorce a curva (o wordmark saiu achatado, com CAPITAL invadindo
    TIVIO). Com a malha pronta, todo transform se comporta.

    O fill so acontece no modo 2D - e por isso que a extrusao vem antes
    da conversao, e nao depois.
    """
    # A extrusao e em unidades LOCAIS, e o SVG importa com ~0,24 unidade
    # de largura: 0,12 fixo virava metade da largura do logo (a peca saia
    # mais funda que larga). Escala a profundidade pelo tamanho importado,
    # para o valor ficar relativo a largura final de 2 unidades.
    largura_svg = max(obj.dimensions.x, obj.dimensions.y, 1e-6)
    fator = largura_svg / 2.0

    print(f"  largura importada {largura_svg:.3f} -> "
          f"profundidade {profundidade * fator:.4f} em unidades locais")

    cur = obj.data
    cur.dimensions = "2D"
    cur.fill_mode = "BOTH"
    cur.extrude = profundidade * fator
    cur.bevel_depth = chanfro * fator
    cur.bevel_resolution = 4
    cur.resolution_u = 12

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")

    malha = bpy.context.view_layer.objects.active
    bpy.ops.object.shade_smooth()

    print(f"  malha: {len(malha.data.vertices)} vertices, "
          f"{len(malha.data.polygons)} faces")

    return malha


def normalizar(obj, largura_alvo=2.0):
    """Centra na origem e normaliza a largura. Sempre depois da malha."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    obj.location = (0, 0, 0)

    maior = max(obj.dimensions.x, obj.dimensions.y, obj.dimensions.z, 1e-6)
    k = largura_alvo / maior
    obj.scale = (k, k, k)

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # recentra: escalar em torno da origem desloca quando ela nao e o centro
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    obj.location = (0, 0, 0)

    d = obj.dimensions
    print(f"  normalizado: {d.x:.2f} x {d.y:.2f} x {d.z:.2f}")

    return obj


def material_metal(obj, cor, rugosidade=0.25, metalico=0.9):
    """Verde da marca em acabamento metalico escovado."""
    mat = bpy.data.materials.new("TivioVerde")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]

    bsdf.inputs["Base Color"].default_value = _srgb_linear(cor)
    bsdf.inputs["Metallic"].default_value = metalico
    bsdf.inputs["Roughness"].default_value = rugosidade

    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.3
        bsdf.inputs["Coat Roughness"].default_value = 0.1

    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return mat


def fundo(cor, forca=0.08):
    """Mundo escuro: o contraste vem das luzes, nao do ambiente."""
    mundo = bpy.data.worlds.new("Mundo")
    bpy.context.scene.world = mundo
    mundo.use_nodes = True
    bg = mundo.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = _srgb_linear(cor)
    bg.inputs["Strength"].default_value = forca


def _luz(nome, tipo, energia, loc, cor=(1, 1, 1), tamanho=2.0, alvo=None):
    dados = bpy.data.lights.new(nome, type=tipo)
    dados.energy = energia
    dados.color = cor

    if tipo == "AREA":
        dados.size = tamanho

    obj = bpy.data.objects.new(nome, dados)
    bpy.context.collection.objects.link(obj)
    obj.location = loc

    if alvo is not None:
        direcao = Vector(alvo) - Vector(loc)
        obj.rotation_euler = direcao.to_track_quat("-Z", "Y").to_euler()

    return obj


def iluminar():
    """Tres pontos: principal quente, preenchimento verde, contorno atras.

    O contorno e o que separa o logo do fundo escuro - sem ele a silhueta
    some, que e o erro classico de logo escuro em fundo escuro.
    """
    _luz("Principal", "AREA", 220, (2.6, -3.4, 2.6),
         cor=(1.0, 0.99, 0.96), tamanho=3.0, alvo=(0, 0, 0))

    _luz("Preenchimento", "AREA", 45, (-3.8, -2.0, 0.6),
         cor=(0.62, 0.92, 0.75), tamanho=5.0, alvo=(0, 0, 0))

    _luz("Contorno", "AREA", 260, (-1.8, 2.8, 1.4),
         cor=(0.72, 1.0, 0.84), tamanho=2.2, alvo=(0, 0, 0))


def camera(obj, lente=95, folga=1.32, azimute=11.0, elevacao=5.0):
    """Enquadra pela caixa real do objeto, nao por distancia fixa.

    Distancia chutada enquadrava o vazio ou cortava o logo: o wordmark e
    muito mais largo que alto, entao a conta tem de partir da largura e
    respeitar tambem a altura do sensor.
    """
    cam_dados = bpy.data.cameras.new("Camera")
    cam_dados.lens = lente
    cam = bpy.data.objects.new("Camera", cam_dados)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    bpy.context.view_layer.update()

    cantos = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    centro = sum(cantos, Vector()) / 8
    larg = max(c.x for c in cantos) - min(c.x for c in cantos)
    alt = max(c.z for c in cantos) - min(c.z for c in cantos)

    cena = bpy.context.scene
    aspecto = cena.render.resolution_x / max(cena.render.resolution_y, 1)

    sensor = cam_dados.sensor_width
    fov_h = 2 * math.atan(sensor / (2 * lente))
    fov_v = 2 * math.atan((sensor / aspecto) / (2 * lente))

    d_larg = (larg / 2) / math.tan(fov_h / 2)
    d_alt = (alt / 2) / math.tan(fov_v / 2)
    dist = max(d_larg, d_alt) * folga

    az, el = math.radians(azimute), math.radians(elevacao)

    cam.location = centro + Vector((
        dist * math.sin(az) * math.cos(el),
        -dist * math.cos(az) * math.cos(el),
        dist * math.sin(el),
    ))

    cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()

    print(f"  enquadramento: caixa {larg:.2f} x {alt:.2f} | distancia {dist:.2f}")
    return cam


def chao(z=-0.9):
    """Plano de apoio: segura a sombra e ancora o logo no espaco."""
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, z))
    plano = bpy.context.active_object

    mat = bpy.data.materials.new("Chao")
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = _srgb_linear(FUNDO)
    b.inputs["Roughness"].default_value = 0.72
    b.inputs["Metallic"].default_value = 0.05

    plano.data.materials.append(mat)
    return plano


def configurar_render(saida: Path, largura, altura, amostras, motor,
                      transparente=False):
    cena = bpy.context.scene
    cena.render.engine = motor
    cena.render.resolution_x = largura
    cena.render.resolution_y = altura
    cena.render.resolution_percentage = 100
    cena.render.film_transparent = bool(transparente)
    cena.render.filepath = str(saida)
    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_depth = "8"

    if transparente:
        cena.render.image_settings.color_mode = "RGBA"

    if motor == "CYCLES":
        cena.cycles.samples = amostras
        cena.cycles.use_denoising = True
        cena.cycles.device = "CPU"
        # caustica off: metal + area light gera ruido que o denoiser nao limpa
        cena.cycles.caustics_reflective = False
        cena.cycles.caustics_refractive = False

    cena.view_settings.view_transform = "Filmic" \
        if "Filmic" in [v.name for v in
                        bpy.types.ColorManagedViewSettings.bl_rna
                        .properties["view_transform"].enum_items] else "Standard"
    cena.view_settings.look = "None"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--svg", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--largura", type=int, default=1600)
    ap.add_argument("--altura", type=int, default=900)
    ap.add_argument("--amostras", type=int, default=96)
    ap.add_argument("--motor", default="CYCLES")
    ap.add_argument("--profundidade", type=float, default=0.12)
    ap.add_argument("--salvar-blend", default="")
    ap.add_argument("--azimute", type=float, default=11.0)
    ap.add_argument("--elevacao", type=float, default=5.0)
    ap.add_argument("--transparente", action="store_true",
                    help="fundo alfa e sem chao: para deck e dashboard")
    ap.add_argument("--giro", type=float, default=0.0,
                    help="graus de rotacao no eixo Z (para sequencias)")
    a = ap.parse_args()

    svg = Path(a.svg)

    if not svg.exists():
        sys.exit(f"  ! SVG nao encontrado: {svg}")

    print(f"\nLogo 3D - Tivio Capital")
    print(f"  Blender {bpy.app.version_string} | motor {a.motor}")

    limpar()

    curva = juntar(importar_svg(svg))
    logo = extrudar_e_converter(curva, profundidade=a.profundidade)
    normalizar(logo)
    material_metal(logo, VERDE)

    # o SVG chega deitado no plano XY; levanta para ficar de frente
    logo.rotation_euler = (math.radians(90), 0, math.radians(a.giro))

    fundo(FUNDO)
    iluminar()

    if not a.transparente:
        chao(z=-0.70)
    camera(logo, azimute=a.azimute, elevacao=a.elevacao)
    configurar_render(Path(a.out), a.largura, a.altura, a.amostras, a.motor,
                      transparente=a.transparente)

    if a.salvar_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.salvar_blend).resolve()))
        print(f"  cena salva em {a.salvar_blend}")

    print(f"  renderizando {a.largura}x{a.altura} ({a.amostras} amostras)...")
    bpy.ops.render.render(write_still=True)
    print(f"  OK  {a.out}\n")


if __name__ == "__main__":
    main()
