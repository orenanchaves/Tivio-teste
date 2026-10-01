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


def recortar_simbolo(obj, limite_x=0.070, piso_y=0.050):
    """Mantem so o T da Tivio, descartando o resto do wordmark.

    O T sao tres contornos - braco esquerdo, haste e braco direito da
    travessa - no canto superior esquerdo. Ha folga limpa entre o fim do
    T (x 0,064) e o inicio do I (x 0,076), entao o corte por x e seguro;
    piso_y descarta a linha de CAPITAL, que comeca mais abaixo.
    """
    cur = obj.data
    manter, fora = [], []

    for i, sp in enumerate(cur.splines):
        pts = [pt.co for pt in (sp.bezier_points if sp.type == "BEZIER"
                                else sp.points)]
        if not pts:
            fora.append(sp)
            continue

        x_max = max(pt[0] for pt in pts)
        y_min = min(pt[1] for pt in pts)

        (manter if (x_max <= limite_x and y_min >= piso_y) else fora).append(sp)

    if not manter:
        sys.exit(f"  ! nenhum contorno dentro do recorte (x<={limite_x})")

    for sp in fora:
        cur.splines.remove(sp)

    print(f"  recorte do simbolo: {len(manter)} contorno(s) mantido(s), "
          f"{len(fora)} descartado(s)")

    return obj


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
    # Mede pelos pontos da curva, nao por obj.dimensions: depois de
    # recortar o simbolo o dimensions ainda devolve a caixa do wordmark
    # inteiro ate o depsgraph atualizar, e a profundidade saia metade da
    # largura do T.
    xs, ys = [], []

    for sp in obj.data.splines:
        for pt in (sp.bezier_points if sp.type == "BEZIER" else sp.points):
            xs.append(pt.co[0])
            ys.append(pt.co[1])

    largura_svg = max(max(xs) - min(xs), max(ys) - min(ys), 1e-6)
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


def material_metal(obj, cor, rugosidade=0.14, metalico=1.0, escovado=0.55):
    """Metal de verdade: Metallic em 1.0 e anisotropia no lugar do verniz.

    Metallic abaixo de 1 mistura difuso e o resultado le como plastico
    colorido. A anisotropia alonga o reflexo numa direcao, que e o que
    diferencia metal escovado de metal polido liso.
    """
    mat = bpy.data.materials.new("TivioMetal")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]

    bsdf.inputs["Base Color"].default_value = _srgb_linear(cor)
    bsdf.inputs["Metallic"].default_value = metalico
    bsdf.inputs["Roughness"].default_value = rugosidade

    if "Anisotropic" in bsdf.inputs:
        bsdf.inputs["Anisotropic"].default_value = escovado
        bsdf.inputs["Anisotropic Rotation"].default_value = 0.25

    # micro-relevo: sem ele o reflexo fica perfeito demais e artificial
    if "Roughness" in bsdf.inputs:
        ruido = nt.nodes.new("ShaderNodeTexNoise")
        ruido.inputs["Scale"].default_value = 420.0
        ruido.inputs["Detail"].default_value = 2.0
        faixa = nt.nodes.new("ShaderNodeMapRange")
        faixa.inputs["To Min"].default_value = max(rugosidade - 0.04, 0.02)
        faixa.inputs["To Max"].default_value = rugosidade + 0.05
        nt.links.new(ruido.outputs["Fac"], faixa.inputs["Value"])
        nt.links.new(faixa.outputs["Result"], bsdf.inputs["Roughness"])

    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return mat


def ambiente_estudio(forca=0.45, topo=(0.62, 0.70, 0.78), base=(0.02, 0.03, 0.04)):
    """Gradiente vertical no mundo.

    Metal nao tem cor propria: ele mostra o que esta em volta. Num mundo
    uniformemente escuro o material fica chapado, parecendo plastico
    pintado - foi o que aconteceu na primeira versao. O degrade da ao
    reflexo um "ceu" claro em cima e um "chao" escuro embaixo, que e o
    que o olho le como superficie polida.
    """
    mundo = bpy.data.worlds.new("Estudio")
    bpy.context.scene.world = mundo
    mundo.use_nodes = True
    nt = mundo.node_tree
    nt.nodes.clear()

    saida = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg_cam = nt.nodes.new("ShaderNodeBackground")
    mistura = nt.nodes.new("ShaderNodeMixShader")
    caminho = nt.nodes.new("ShaderNodeLightPath")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    tex = nt.nodes.new("ShaderNodeTexCoord")
    mapa = nt.nodes.new("ShaderNodeMapRange")

    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = _srgb_linear(base + (1.0,))
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = _srgb_linear(topo + (1.0,))

    mapa.inputs["From Min"].default_value = -1.0
    mapa.inputs["From Max"].default_value = 1.0

    bg.inputs["Strength"].default_value = forca

    nt.links.new(tex.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], mapa.inputs["Value"])
    nt.links.new(mapa.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])

    # O degrade precisa ser claro para o metal ter o que refletir, mas
    # claro tambem no fundo deixa a imagem lavada. Is Camera Ray separa
    # os dois: a camera ve o fundo escuro da marca, o reflexo ve o
    # estudio.
    bg_cam.inputs["Color"].default_value = _srgb_linear(FUNDO)
    bg_cam.inputs["Strength"].default_value = 1.0

    nt.links.new(caminho.outputs["Is Camera Ray"], mistura.inputs["Fac"])
    nt.links.new(bg.outputs["Background"], mistura.inputs[1])
    nt.links.new(bg_cam.outputs["Background"], mistura.inputs[2])
    nt.links.new(mistura.outputs["Shader"], saida.inputs["Surface"])

    return mundo


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


def refletor(nome, loc, rot, tam, forca, cor=(1, 1, 1)):
    """Placa emissiva: o que o metal de fato mostra.

    Luz de area ilumina, mas o reflexo que o olho le como metal vem de
    uma SUPERFICIE visivel no espelhamento. Sem estas placas o material
    reflete so o vazio e fica escuro, por mais energia que se jogue nas
    lampadas.
    """
    bpy.ops.mesh.primitive_plane_add(size=tam, location=loc, rotation=rot)
    plano = bpy.context.active_object
    plano.name = nome

    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    emis = nt.nodes.new("ShaderNodeEmission")
    emis.inputs["Color"].default_value = (*cor, 1.0)
    emis.inputs["Strength"].default_value = forca
    nt.links.new(emis.outputs["Emission"],
                 nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])

    plano.data.materials.append(mat)

    # nao aparece para a camera, so no reflexo
    plano.visible_camera = False
    plano.visible_shadow = False

    return plano


def estudio():
    """Tres placas: chave acima, preenchimento lateral e faixa atras."""
    refletor("Softbox", (1.6, -2.6, 3.4), (math.radians(52), 0, math.radians(26)),
             6.0, 9.0, cor=(1.0, 0.99, 0.97))

    refletor("Lateral", (-3.4, -1.4, 0.4), (0, math.radians(-78), 0),
             5.5, 3.2, cor=(0.70, 0.95, 0.80))

    refletor("Faixa", (0.4, 2.6, 1.2), (math.radians(-64), 0, 0),
             5.0, 6.0, cor=(0.80, 1.0, 0.88))


def iluminar():
    """Tres pontos: principal quente, preenchimento verde, contorno atras.

    O contorno e o que separa o logo do fundo escuro - sem ele a silhueta
    some, que e o erro classico de logo escuro em fundo escuro.
    """
    _luz("Principal", "AREA", 90, (2.6, -3.4, 2.6),
         cor=(1.0, 0.99, 0.96), tamanho=3.0, alvo=(0, 0, 0))

    _luz("Preenchimento", "AREA", 25, (-3.8, -2.0, 0.6),
         cor=(0.62, 0.92, 0.75), tamanho=5.0, alvo=(0, 0, 0))

    _luz("Contorno", "AREA", 110, (-1.8, 2.8, 1.4),
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

    # Piso escuro e levemente espelhado: difuso claro devolvia toda a luz
    # do estudio e o chao tomava metade do quadro, competindo com a peca.
    mat = bpy.data.materials.new("Chao")
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = _srgb_linear((0.02, 0.028, 0.035, 1))
    b.inputs["Roughness"].default_value = 0.30
    b.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.5

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
    ap.add_argument("--chao", action="store_true",
                    help="adiciona piso (fora isso a peca flutua)")
    ap.add_argument("--so-t", action="store_true",
                    help="renderiza apenas o T da Tivio")
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

    if a.so_t:
        recortar_simbolo(curva)
    logo = extrudar_e_converter(curva, profundidade=a.profundidade)
    normalizar(logo)
    material_metal(logo, VERDE)

    # o SVG chega deitado no plano XY; levanta para ficar de frente
    logo.rotation_euler = (math.radians(90), 0, math.radians(a.giro))

    ambiente_estudio(forca=0.8)
    iluminar()
    estudio()

    # Sem chao por padrao. Com piso espelhado o reflexo do softbox
    # estourava; com piso difuso claro o chao tomava metade do quadro.
    # O ambiente do estudio ja da o assentamento. --chao traz de volta.
    if a.chao and not a.transparente:
        chao(z=-0.70)
    camera(logo, azimute=a.azimute, elevacao=a.elevacao,
           folga=1.18 if a.so_t else 1.32)
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
