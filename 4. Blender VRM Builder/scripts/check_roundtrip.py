from __future__ import annotations

import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path

import bmesh
import bpy


BASE_GEOMETRY_MARKERS = ("bottoms", "shoes", "tops", "hairback")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--strip-base", action="store_true")
    parser.add_argument(
        "--feature-group",
        choices=("none", "material", "primitive", "parented", "hair", "glasses", "hairclip", "outfit", "all"),
        default="none",
    )
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def expression_count() -> int:
    return sum(
        len(obj.data.shape_keys.key_blocks)
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and obj.data.shape_keys
    )


def strip_base_costume_geometry() -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        forbidden_slots = {
            index
            for index, slot in enumerate(obj.data.materials)
            if slot and any(marker in slot.name.lower() for marker in BASE_GEOMETRY_MARKERS)
        }
        if not forbidden_slots:
            continue
        model = bmesh.new()
        model.from_mesh(obj.data)
        bmesh.ops.delete(
            model,
            geom=[face for face in model.faces if face.material_index in forbidden_slots],
            context="FACES_ONLY",
        )
        model.to_mesh(obj.data)
        model.free()
        obj.data.update()


def add_feature_group(name: str) -> None:
    if name == "none":
        return
    module_path = Path(__file__).with_name("build_aina_v1.py")
    spec = importlib.util.spec_from_file_location("aina_builder", module_path)
    builder = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(builder)
    rig = builder.armature()
    cyan = builder.material("Aina_Cyan", "#7ED8F2")
    if name == "material":
        return
    if name == "primitive":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, location=(0.0, 0.0, 1.0))
        sphere = bpy.context.object
        sphere.name = "Aina_TestPrimitive"
        sphere.data.name = sphere.name
        sphere.data.materials.append(cyan)
        return
    if name == "parented":
        builder.add_uv("Aina_TestParented", (0.0, 0.0, 1.0), (0.1, 0.1, 0.1), cyan, rig, "head")
        return
    blue = builder.material("Aina_BlueTips", "#7E8CCF")
    mint = builder.material("Aina_Mint", "#8DE6C9")
    charcoal = builder.material("Aina_Charcoal", "#3B3F45")
    pink = builder.material("Aina_Pink", "#F5A4C8")
    silver = builder.material("Aina_SilverMetal", "#C8CDD5", metallic=0.78, roughness=0.28)
    white = builder.material("Aina_White", "#E6E9EE")
    if name in {"hair", "all"}:
        builder.create_hair(rig, cyan, blue)
    if name in {"glasses", "all"}:
        builder.create_glasses(rig, pink)
    if name in {"hairclip", "all"}:
        builder.create_hairclip(rig, silver)
    if name in {"outfit", "all"}:
        builder.create_outfit(rig, mint, cyan, charcoal, white, pink)


def main() -> None:
    args = parse_args()
    input_vrm = Path(args.input).resolve()
    output_vrm = Path(tempfile.gettempdir()) / "aina_roundtrip_check.vrm"
    bpy.ops.import_scene.vrm(filepath=str(input_vrm))
    before = expression_count()
    if args.strip_base:
        strip_base_costume_geometry()
    add_feature_group(args.feature_group)
    bpy.ops.export_scene.vrm(filepath=str(output_vrm))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.vrm(filepath=str(output_vrm))
    after = expression_count()
    output_vrm.unlink(missing_ok=True)
    print(
        f"ROUNDTRIP_EXPRESSIONS before={before} after={after} "
        f"strip_base={args.strip_base} feature_group={args.feature_group}"
    )
    if before != after:
        raise RuntimeError("Round-trip VRM mengubah jumlah expression shape keys.")


if __name__ == "__main__":
    main()
