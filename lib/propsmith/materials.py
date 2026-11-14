"""Palette materials: procedural, with value noise and baked-in crevice darkening (painterly, never plastic).

Every material made here carries a `propsmith_source` custom property, `palette` or `ledger:<texture id>`; `measure` reads
it back so the `materials-known` check can tell library materials from ones a prop made by hand."""
import bpy

from . import textures

_cache = {}

# Custom property naming where a material came from (read by `measure`).
SOURCE = "propsmith_source"


def material(name, color, rough=0.8, vary=0.18, scale=6.0, crevice=0.55, metal=0.0):
    """A Principled material: `color` (linear RGB) broken up by noise (`vary`, `scale` per metre) and darkened in
    crevices by an Ambient Occlusion node (`crevice` 0..1). Cached by name."""
    if name in _cache:
        return _cache[name]
    m = bpy.data.materials.new(name)
    m[SOURCE] = "palette"
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal

    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 3.0
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    lo = tuple(c * (1 - vary) for c in color)
    hi = tuple(min(1.0, c * (1 + vary * 0.6)) for c in color)
    ramp.color_ramp.elements[0].color = (*lo, 1)
    ramp.color_ramp.elements[1].color = (*hi, 1)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.65
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])

    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.25
    ao.samples = 8
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    mix.inputs[0].default_value = crevice
    nt.links.new(ramp.outputs["Color"], ao.inputs["Color"])
    nt.links.new(ramp.outputs["Color"], mix.inputs[6])
    nt.links.new(ao.outputs["AO"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    _cache[name] = m
    return m


def texture(name, texture_id, metres_per_repeat=1.0, tint=(1, 1, 1), rough=0.85, normal=0.8):
    """A material from a CC0 ledger texture (`textures.maps`): colour times `tint` and its AO map, a normal map when the
    ledger has one, box-projected on object coordinates every `metres_per_repeat`. Cached by name."""
    if name in _cache:
        return _cache[name]
    files = textures.maps(texture_id)
    m = bpy.data.materials.new(name)
    m[SOURCE] = f"ledger:{texture_id}"
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = rough
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    s = 1 / metres_per_repeat
    mapping.inputs["Scale"].default_value = (s, s, s)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])

    def image(kind, colour):
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(files[kind], check_existing=True)
        node.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        node.projection, node.projection_blend = "BOX", 0.2
        nt.links.new(mapping.outputs["Vector"], node.inputs["Vector"])
        return node

    colour = image("color", True).outputs["Color"]
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    mix.inputs[7].default_value = (*tint, 1)
    nt.links.new(colour, mix.inputs[6])
    colour = mix.outputs[2]
    if "ao" in files:
        shade = nt.nodes.new("ShaderNodeMix")
        shade.data_type, shade.blend_type = "RGBA", "MULTIPLY"
        shade.inputs[0].default_value = 1.0
        nt.links.new(colour, shade.inputs[6])
        nt.links.new(image("ao", False).outputs["Color"], shade.inputs[7])
        colour = shade.outputs[2]
    nt.links.new(colour, bsdf.inputs["Base Color"])
    if "normal" in files:
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = normal
        nt.links.new(image("normal", False).outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    _cache[name] = m
    return m


def reset():
    _cache.clear()
