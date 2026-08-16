import bpy


def has_operator(path: str) -> bool:
    current = bpy.ops
    for part in path.split("."):
        current = getattr(current, part, None)
        if current is None:
            return False
    return True


required = ("import_scene.vrm", "export_scene.vrm")
missing = [operator for operator in required if not has_operator(operator)]
if missing:
    raise RuntimeError(
        "VRM Add-on belum aktif. Jalankan setup_vrm_addon.ps1. "
        f"Operator hilang: {', '.join(missing)}"
    )

print("VRM Add-on siap: import_scene.vrm dan export_scene.vrm tersedia.")

