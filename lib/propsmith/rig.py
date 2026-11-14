"""The light rig and camera of a render, driven by a style (`tools/blender/style.json` for the review snapshots; a
game passes its own).

Camera: orthographic, by default 30 deg elevation and 45 deg yaw (a 2:1 isometric view), scaled so `tileMetres`
metres on the ground span `pxPerTile` px across the diamond.

Grid to world (for games on a tile grid): grid +x runs screen right-down and grid +y screen left-down. With the camera
looking along world +x+y, that is grid (gx, gy) -> world (-gy, -gx) tiles. Screen top-left is world +y.

Light: one warm sun from the screen's top-left, a cool sky, ambient occlusion (EEVEE horizon scan plus the crevice
term in every palette material), AgX. Post: an optional Kuwahara pass, saturation and a warm gain, in the compositor.
"""
import math

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def grid_to_world(style, gx, gy, z=0.0):
    t = style["tileMetres"]
    return Vector((-gy * t, -gx * t, z))


def new_scene(style):
    """Empties the file and sets render, colour management, sky, sun and ambient occlusion from `style`."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = style["samples"]
    scene.render.filter_size = 1.2
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = style["look"]
    scene.view_settings.exposure = style["exposure"]

    ao = style["ao"]
    scene.eevee.use_raytracing = True
    scene.eevee.ray_tracing_method = "SCREEN"
    scene.eevee.use_fast_gi = True
    scene.eevee.fast_gi_method = "AMBIENT_OCCLUSION_ONLY"
    scene.eevee.fast_gi_distance = ao["distance"]
    scene.eevee.use_shadows = True
    scene.eevee.shadow_ray_count = 2
    scene.eevee.shadow_step_count = 8

    sky = style["sky"]
    world = bpy.data.worlds.new("sky")
    scene.world = world
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (*sky["color"], 1)
    bg.inputs["Strength"].default_value = sky["strength"]

    sun = style["sun"]
    light = bpy.data.lights.new("sun", "SUN")
    light.energy, light.color, light.angle = sun["energy"], sun["color"], math.radians(sun["angleDeg"])
    obj = bpy.data.objects.new("sun", light)
    scene.collection.objects.link(obj)
    # Screen up on the ground is world (1, 1), screen right (1, -1); `fromScreenDeg` turns clockwise from up.
    a, e = math.radians(sun["fromScreenDeg"]), math.radians(sun["elevationDeg"])
    up, right = Vector((1, 1, 0)).normalized(), Vector((1, -1, 0)).normalized()
    toward = (up * math.cos(a) + right * math.sin(a)) * math.cos(e) + Vector((0, 0, math.sin(e)))
    obj.rotation_euler = (-toward).to_track_quat("-Z", "Y").to_euler()

    _compositor(scene, style["post"])
    return scene


def _compositor(scene, post):
    tree = bpy.data.node_groups.new("post", "CompositorNodeTree")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    scene.compositing_node_group = tree
    scene.render.use_compositing = True
    rl = tree.nodes.new("CompositorNodeRLayers")
    out = tree.nodes.new("NodeGroupOutput")
    image = rl.outputs["Image"]
    k = post.get("kuwahara")
    if k:
        node = tree.nodes.new("CompositorNodeKuwahara")
        node.inputs["Type"].default_value = "Anisotropic"
        node.inputs["Size"].default_value = k["size"]
        node.inputs["Uniformity"].default_value = k["uniformity"]
        node.inputs["Sharpness"].default_value = k["sharpness"]
        node.inputs["Eccentricity"].default_value = k["eccentricity"]
        node.inputs["High Precision"].default_value = True
        tree.links.new(image, node.inputs["Image"])
        image = node.outputs["Image"]
    hs = tree.nodes.new("CompositorNodeHueSat")
    hs.inputs["Saturation"].default_value = post["saturation"]
    hs.inputs["Value"].default_value = post["value"]
    tree.links.new(image, hs.inputs["Image"])
    image = hs.outputs["Image"]
    warm = tree.nodes.new("CompositorNodeColorBalance")
    warm.inputs["Type"].default_value = "Lift/Gamma/Gain"
    gain = next(s for s in warm.inputs if s.name == "Gain" and s.type == "RGBA")
    gain.default_value = (*post["gain"], 1)
    tree.links.new(image, warm.inputs["Image"])
    # Keep the render's own alpha: a Kuwahara pass would otherwise smear the transparent border.
    alpha = tree.nodes.new("CompositorNodeSetAlpha")
    alpha.inputs["Type"].default_value = "Replace Alpha"
    tree.links.new(warm.outputs["Image"], alpha.inputs["Image"])
    tree.links.new(rl.outputs["Alpha"], alpha.inputs["Alpha"])
    tree.links.new(alpha.outputs["Image"], out.inputs[0])


def camera(scene, style, width, height, target, target_px):
    """The actor camera, `width` x `height` px, framed so world point `target` lands on pixel `target_px` (x, y from
    the top-left)."""
    cam = style["camera"]
    data = bpy.data.cameras.new("cam")
    data.type = "ORTHO"
    obj = bpy.data.objects.new("cam", data)
    scene.collection.objects.link(obj)
    scene.camera = obj
    elev, yaw = math.radians(cam["elevationDeg"]), math.radians(cam["yawDeg"])
    view = Vector((-math.cos(elev) * math.sin(yaw), -math.cos(elev) * math.cos(yaw), math.sin(elev)))
    obj.location = Vector(target) + view * 40
    obj.rotation_euler = (-view).to_track_quat("-Z", "Y").to_euler()
    t = style["tileMetres"]
    data.ortho_scale = max(width, height) / style["pxPerTile"] * t * math.sqrt(2)
    data.clip_end = 100
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    bpy.context.view_layer.update()
    px, py = project(scene, target)
    big = max(width, height)
    data.shift_x = (px - target_px[0]) / big
    data.shift_y = (target_px[1] - py) / big
    bpy.context.view_layer.update()
    return obj


def project(scene, point):
    """World point -> image pixel (x, y from the top-left)."""
    ndc = world_to_camera_view(scene, scene.camera, Vector(point))
    return ndc.x * scene.render.resolution_x, (1 - ndc.y) * scene.render.resolution_y


def ground(style, tiles, textures):
    """A `tiles` x `tiles` patch of the CC0 ground texture from grid (0, 0), so shadows have something to fall on."""
    g = style["ground"]
    t = style["tileMetres"]
    size = tiles * t
    bpy.ops.mesh.primitive_plane_add(size=size, location=(-size / 2, -size / 2, 0))
    plane = bpy.context.active_object
    plane.name = "ground"
    mat = bpy.data.materials.new("ground")
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.9
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    s = 1 / g["metresPerRepeat"]
    mapping.inputs["Scale"].default_value = (s, s, s)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])

    def image(kind, colour):
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(textures[kind])
        node.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        nt.links.new(mapping.outputs["Vector"], node.inputs["Vector"])
        return node

    col, ao, nor = image("color", True), image("ao", False), image("normal", False)
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type, tint.blend_type = "RGBA", "MULTIPLY"
    tint.inputs[0].default_value = 1.0
    tint.inputs[7].default_value = (*g["tint"], 1)
    nt.links.new(col.outputs["Color"], tint.inputs[6])
    shade = nt.nodes.new("ShaderNodeMix")
    shade.data_type, shade.blend_type = "RGBA", "MULTIPLY"
    shade.inputs[0].default_value = 1.0
    nt.links.new(tint.outputs[2], shade.inputs[6])
    nt.links.new(ao.outputs["Color"], shade.inputs[7])
    nt.links.new(shade.outputs[2], bsdf.inputs["Base Color"])
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = g["normalStrength"]
    nt.links.new(nor.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    plane.data.materials.append(mat)
    return plane


def render(scene, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def sun_direction(scene):
    """The direction sunlight travels (unit vector, pointing down)."""
    sun = scene.objects["sun"]
    return (sun.matrix_world.to_quaternion() @ Vector((0, 0, -1))).normalized()


def shadow_catcher(style, size):
    """A ground plane `size` metres square that renders only the shadow falling on it, as black with alpha, so a prop
    sprite carries its own shadow on a transparent film (EEVEE has no shadow catcher of its own).

    A white diffuse plane through Shader to RGB gives the light arriving at each point; divided by the light arriving in
    the open (the sun at its elevation plus the sky, computed from `style`) it is 1 in full light and the sky's share in
    full shadow. That range maps to alpha 0 .. `spriteShadow.opacity`. Ambient occlusion near the feet darkens it too."""
    sun, sky = style["sun"], style["sky"]
    open_light = [
        sun["energy"] * math.sin(math.radians(sun["elevationDeg"])) / math.pi * c + sky["strength"] * s
        for c, s in zip(sun["color"], sky["color"])
    ]
    lum = (0.2126, 0.7152, 0.0722)
    shade = sum(w * sky["strength"] * s for w, s in zip(lum, sky["color"])) / sum(w * o for w, o in zip(lum, open_light))

    mat = bpy.data.materials.new("shadow_catcher")
    mat.surface_render_method = "BLENDED"
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    diffuse = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.inputs["Color"].default_value = (1, 1, 1, 1)
    to_rgb = nt.nodes.new("ShaderNodeShaderToRGB")
    nt.links.new(diffuse.outputs["BSDF"], to_rgb.inputs["Shader"])
    divide = nt.nodes.new("ShaderNodeVectorMath")
    divide.operation = "DIVIDE"
    divide.inputs[1].default_value = open_light
    nt.links.new(to_rgb.outputs["Color"], divide.inputs[0])
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(divide.outputs["Vector"], bw.inputs["Color"])
    alpha = nt.nodes.new("ShaderNodeMapRange")
    alpha.clamp = True
    alpha.inputs["From Min"].default_value = shade
    alpha.inputs["From Max"].default_value = 0.98
    alpha.inputs["To Min"].default_value = style["spriteShadow"]["opacity"]
    alpha.inputs["To Max"].default_value = 0.0
    nt.links.new(bw.outputs["Val"], alpha.inputs["Value"])
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    black = nt.nodes.new("ShaderNodeEmission")
    black.inputs["Color"].default_value = (0, 0, 0, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(alpha.outputs["Result"], mix.inputs["Fac"])
    nt.links.new(clear.outputs["BSDF"], mix.inputs[1])
    nt.links.new(black.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.name = "shadow_catcher"
    plane.data.materials.append(mat)
    plane.visible_shadow = False
    return plane
