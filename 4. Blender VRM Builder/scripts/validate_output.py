import argparse
import sys
from pathlib import Path

import bpy

ROBOT_MARKERS = ("robo", "robot", "backpack", "armgear", "anim_logo")
FORBIDDEN_BASE_MATERIALS = ("bottoms", "shoes", "tops", "hairback")
REQUIRED_AINA_PARTS = (
    "hairclip",
    "glasses",
    "hair_cap",
    "hair_bob",
    "hair_tip",
    "hoodie_",
    "innershirt",
    "camisolestrap",
    "shorts",
    "sock",
    "sneaker",
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--stamp")
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def main() -> None:
    args = parse_args()
    input_vrm = Path(args.input).resolve()
    if not input_vrm.is_file() or input_vrm.stat().st_size == 0:
        raise RuntimeError(f"VRM tidak ditemukan atau kosong: {input_vrm}")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.vrm(filepath=str(input_vrm))

    objects = list(bpy.context.scene.objects)
    armatures = [obj for obj in objects if obj.type == "ARMATURE"]
    names = [obj.name.lower() for obj in objects] + [item.name.lower() for item in bpy.data.materials]
    robot_artifacts = [name for name in names if any(marker in name for marker in ROBOT_MARKERS)]
    missing_parts = [part for part in REQUIRED_AINA_PARTS if not any(part in name for name in names)]
    forbidden_geometry = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        materials = obj.data.materials
        for polygon in obj.data.polygons:
            if polygon.material_index >= len(materials) or not materials[polygon.material_index]:
                continue
            material_name = materials[polygon.material_index].name.lower()
            if any(marker in material_name for marker in FORBIDDEN_BASE_MATERIALS):
                forbidden_geometry.append(f"{obj.name}:{materials[polygon.material_index].name}")
                break
    expression_keys = [
        key.name
        for obj in objects
        if obj.type == "MESH" and obj.data.shape_keys
        for key in obj.data.shape_keys.key_blocks
    ]
    if not armatures:
        raise RuntimeError("VRM hasil export tidak memiliki armature.")
    if robot_artifacts:
        raise RuntimeError("VRM hasil export masih membawa artifact robot: " + ", ".join(robot_artifacts))
    if missing_parts:
        raise RuntimeError("VRM hasil export kehilangan bagian Aina: " + ", ".join(missing_parts))
    if forbidden_geometry:
        raise RuntimeError("VRM hasil export masih memakai geometry base lama: " + ", ".join(forbidden_geometry))
    if len(expression_keys) < 3:
        raise RuntimeError("VRM hasil export kehilangan expression keys wajah.")

    print(
        f"VRM re-import valid: armatures={len(armatures)}, "
        f"required_parts={len(REQUIRED_AINA_PARTS)}, expressions={len(expression_keys)}, objects={len(objects)}"
    )
    if args.stamp:
        Path(args.stamp).write_text("ok", encoding="ascii")


if __name__ == "__main__":
    main()
