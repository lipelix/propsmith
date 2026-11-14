"""CC0 textures by ledger id (`catalog/textures.json`).

The build passes the cached files of the ledger (`configure`); `maps(id)` returns them and records the id, so
`result.json` lists the textures a variant used. An id outside the ledger fails the build. `materials.texture`
builds a material from the maps.
"""

_paths = {}
USED = set()


def configure(paths):
    """`paths`: {ledger id: {"color" | "ao" | "normal" | "roughness": file}} from the job."""
    _paths.clear()
    _paths.update(paths)
    USED.clear()


def maps(texture_id):
    if texture_id not in _paths:
        raise ValueError(f"unknown texture {texture_id!r}: not in catalog/textures.json (or not downloaded)")
    USED.add(texture_id)
    return _paths[texture_id]
