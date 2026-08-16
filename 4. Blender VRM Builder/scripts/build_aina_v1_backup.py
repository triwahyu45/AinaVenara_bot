import argparse
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROBOT_MARKERS = ("robo", "robot", "backpack", "armgear", "anim_logo")
AINA_PREFIX = "Aina_"
BASE_GEOMETRY_MARKERS = ("bottoms", "shoes", "tops", "hairback")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--blend", required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def hex_color(value: str) -> tuple[float, float, float, float]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) / 255 for index in (0, 2, 4)) + (1.0,)


def material(name: str, color: str, *, metallic=0.0, roughness=0.55) -> bpy.types.Material:
    found = bpy.data.materials.get(name)
    if found:
        return found
    found = bpy.data.materials.new(name)
    found.diffuse_color = hex_color(color)
    found.metallic = metallic
    found.roughness = roughness
    return found


def reject_robot_artifacts() -> None:
    names = [obj.name for obj in bpy.context.scene.objects] + [item.name for item in bpy.data.materials]
    found = sorted(name for name in names if any(marker in name.lower() for marker in ROBOT_MARKERS))
    if found:
        raise RuntimeError("Base VRM ditolak karena membawa artifact robot: " + ", ".join(found))


def armature() -> bpy.types.Object:
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if len(armatures) != 1:
        raise RuntimeError(f"Base VRM harus memiliki tepat satu armature humanoid, ditemukan {len(armatures)}.")
    return armatures[0]


def bone(rig: bpy.types.Object, *candidates: str) -> bpy.types.Bone:
    by_name = {item.name.lower(): item for item in rig.data.bones}
    for candidate in candidates:
        if candidate.lower() in by_name:
            return by_name[candidate.lower()]
    for item in rig.data.bones:
        if any(candidate.lower() in item.name.lower() for candidate in candidates):
            return item
    raise RuntimeError("Bone tidak ditemukan: " + ", ".join(candidates))


def bone_world(rig: bpy.types.Object, *candidates: str) -> Vector:
    return rig.matrix_world @ bone(rig, *candidates).head_local


def parent_bone(obj: bpy.types.Object, rig: bpy.types.Object, *candidates: str) -> None:
    target = bone(rig, *candidates)
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = target.name
    obj.matrix_world = world


def remove_old_aina_parts() -> None:
    for obj in list(bpy.context.scene.objects):
        if obj.name.startswith(AINA_PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)


def strip_base_costume_geometry() -> None:
    stripped = 0
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        forbidden_slots = {
            index
            for index, slot in enumerate(mesh.materials)
            if slot and any(marker in slot.name.lower() for marker in BASE_GEOMETRY_MARKERS)
        }
        if not forbidden_slots:
            continue
        model = bmesh.new()
        model.from_mesh(mesh)
        doomed = [face for face in model.faces if face.material_index in forbidden_slots]
        stripped += len(doomed)
        bmesh.ops.delete(model, geom=doomed, context="FACES_ONLY")
        model.to_mesh(mesh)
        model.free()
        mesh.update()
    if not stripped:
        raise RuntimeError("Base VRM tidak memiliki geometry pakaian/rambut lama yang dapat dibersihkan.")
    print(f"Base costume geometry stripped: faces={stripped}")


def apply_material(obj: bpy.types.Object, mat: bpy.types.Material) -> bpy.types.Object:
    obj.data.materials.append(mat)
    return obj


def add_uv(name: str, location: Vector, scale, mat, rig, *target_bone) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_material(obj, mat)
    parent_bone(obj, rig, *target_bone)
    return obj


def add_hair_shell(name: str, location: Vector, scale, mat, rig) -> bpy.types.Object:
    obj = add_uv(name, location, scale, mat, rig, "head")
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    bmesh.ops.delete(
        mesh,
        geom=[
            vertex
            for vertex in mesh.verts
            if (vertex.co.y < -0.035 and vertex.co.z < 0.035) or vertex.co.z < -0.075
        ],
        context="VERTS",
    )
    mesh.to_mesh(obj.data)
    mesh.free()
    return obj


def align_to_vector(obj: bpy.types.Object, direction: Vector) -> None:
    if direction.length > 0:
        obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()


def add_limb(name: str, start: Vector, end: Vector, radius: float, mat, rig, *target_bone) -> bpy.types.Object:
    obj = add_uv(name, (start + end) / 2, (radius, radius, max((start - end).length / 2, 0.08)), mat, rig, *target_bone)
    align_to_vector(obj, end - start)
    return obj


def add_sleeve(name: str, start: Vector, end: Vector, radius: float, mat, rig, *target_bone) -> bpy.types.Object:
    direction = end - start
    return add_tube(
        name,
        (start, start + direction * 0.52, end),
        radius,
        mat,
        rig,
        *target_bone,
        radii=(0.78, 1.0, 0.88),
    )


def add_cube(name: str, location: Vector, scale, mat, rig, *target_bone, bevel=0.025) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    modifier = obj.modifiers.new("SoftEdges", "BEVEL")
    modifier.width = bevel
    modifier.segments = 3
    apply_material(obj, mat)
    parent_bone(obj, rig, *target_bone)
    return obj


def add_tube(name: str, points, radius: float, mat, rig, *target_bone, cyclic=False, radii=None) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for index, (item, coordinate) in enumerate(zip(spline.points, points)):
        item.co = (*coordinate, 1.0)
        if radii:
            item.radius = radii[index]
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name
    apply_material(obj, mat)
    parent_bone(obj, rig, *target_bone)
    return obj


def add_ribbon(name: str, points, widths, mat, rig, *target_bone) -> bpy.types.Object:
    vertices = []
    faces = []
    for coordinate, width in zip(points, widths):
        vertices.extend(
            (
                (coordinate.x - width / 2, coordinate.y, coordinate.z),
                (coordinate.x + width / 2, coordinate.y, coordinate.z),
            )
        )
    for index in range(len(points) - 1):
        offset = index * 2
        faces.append((offset, offset + 1, offset + 3, offset + 2))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    apply_material(obj, mat)
    solidify = obj.modifiers.new("RibbonThickness", "SOLIDIFY")
    solidify.thickness = 0.004
    bevel = obj.modifiers.new("RibbonSoftEdges", "BEVEL")
    bevel.width = 0.003
    bevel.segments = 2
    parent_bone(obj, rig, *target_bone)
    return obj


def add_panel(name: str, points, mat, rig, *target_bone, thickness=0.008, bevel=0.006) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], ((0, 1, 2, 3),))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    apply_material(obj, mat)
    solidify = obj.modifiers.new("PanelThickness", "SOLIDIFY")
    solidify.thickness = thickness
    edge = obj.modifiers.new("PanelSoftEdges", "BEVEL")
    edge.width = bevel
    edge.segments = 3
    parent_bone(obj, rig, *target_bone)
    return obj


def add_torso_shell(name: str, center: Vector, top_width: float, bottom_width: float, depth: float, height: float, mat, rig, *target_bone) -> bpy.types.Object:
    top = center.z + height / 2
    bottom = center.z - height / 2
    front = center.y - depth
    back = center.y + depth
    points = (
        (-top_width + center.x, front, top),
        (top_width + center.x, front, top),
        (bottom_width + center.x, front, bottom),
        (-bottom_width + center.x, front, bottom),
        (-top_width + center.x, back, top),
        (top_width + center.x, back, top),
        (bottom_width + center.x, back, bottom),
        (-bottom_width + center.x, back, bottom),
    )
    faces = (
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (3, 2, 6, 7),
        (0, 3, 7, 4),
        (1, 5, 6, 2),
    )
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    apply_material(obj, mat)
    bevel_modifier = obj.modifiers.new("TorsoSoftEdges", "BEVEL")
    bevel_modifier.width = 0.012
    bevel_modifier.segments = 3
    parent_bone(obj, rig, *target_bone)
    return obj


def create_hair(rig, cyan, blue) -> None:
    head = bone_world(rig, "head")
    add_hair_shell("Aina_Hair_Cap", head + Vector((0, 0.035, 0.075)), (0.155, 0.14, 0.16), cyan, rig)
    for index in range(17):
        angle = math.radians(-120 + index * 240 / 16)
        x = math.sin(angle) * 0.145
        y = 0.045 + math.cos(angle) * 0.108
        top = head + Vector((x * 0.58, y, 0.16))
        mid = head + Vector((x * 0.88, y - 0.006, 0.025))
        lower = head + Vector((x, y - 0.012, -0.075))
        tip = head + Vector((x * 1.03, y - 0.018, -0.12 - 0.012 * abs(math.sin(angle))))
        add_ribbon(
            f"Aina_Hair_Bob_{index:02}",
            (top, mid, lower, tip),
            (0.045, 0.052, 0.048, 0.006),
            cyan,
            rig,
            "head",
        )
        add_ribbon(
            f"Aina_Hair_Tip_{index:02}",
            (lower, tip),
            (0.046, 0.006),
            blue,
            rig,
            "head",
        )
    for index, x in enumerate((-0.105, -0.065, -0.025, 0.018, 0.058, 0.098)):
        sweep = -0.012 if index < 3 else 0.012
        add_ribbon(
            f"Aina_Bangs_{index:02}",
            (
                head + Vector((x * 0.45, -0.105, 0.16)),
                head + Vector((x * 0.8 + sweep, -0.145, 0.10)),
                head + Vector((x + sweep, -0.15, 0.045)),
                head + Vector((x * 1.05 + sweep, -0.142, -0.008)),
            ),
            (0.032, 0.038, 0.027, 0.004),
            cyan,
            rig,
            "head",
        )
    for side in (-1, 1):
        x = side * 0.12
        add_ribbon(
            f"Aina_Hair_SideLock_{'L' if side < 0 else 'R'}",
            (
                head + Vector((x * 0.55, -0.115, 0.135)),
                head + Vector((x * 0.9, -0.155, 0.04)),
                head + Vector((x, -0.158, -0.09)),
            ),
            (0.042, 0.035, 0.006),
            cyan,
            rig,
            "head",
        )
    add_tube(
        "Aina_Ahoge",
        (
            head + Vector((0.0, 0.0, 0.235)),
            head + Vector((0.014, -0.005, 0.275)),
            head + Vector((-0.02, -0.008, 0.315)),
            head + Vector((0.028, -0.01, 0.345)),
        ),
        0.005,
        cyan,
        rig,
        "head",
        radii=(0.85, 1.0, 0.8, 0.18),
    )


def create_glasses(rig, pink) -> None:
    head = bone_world(rig, "head")
    for side in (-1, 1):
        cx = side * 0.047
        points = [
            head + Vector((cx + math.cos(step * math.tau / 16) * 0.034, -0.174, 0.035 + math.sin(step * math.tau / 16) * 0.027))
            for step in range(16)
        ]
        add_tube(f"Aina_Glasses_{'L' if side < 0 else 'R'}", points, 0.004, pink, rig, "head", cyclic=True)
    add_tube("Aina_Glasses_Bridge", (head + Vector((-0.012, -0.176, 0.04)), head + Vector((0.012, -0.176, 0.04))), 0.004, pink, rig, "head")
    for side in (-1, 1):
        add_tube(
            f"Aina_Glasses_Temple_{'L' if side < 0 else 'R'}",
            (
                head + Vector((side * 0.083, -0.166, 0.04)),
                head + Vector((side * 0.138, -0.125, 0.04)),
                head + Vector((side * 0.142, -0.035, 0.032)),
            ),
            0.003,
            pink,
            rig,
            "head",
        )


def create_hairclip(rig, silver) -> None:
    head = bone_world(rig, "head")
    points = (
        head + Vector((0.092, -0.168, 0.205)),
        head + Vector((0.13, -0.168, 0.205)),
        head + Vector((0.141, -0.168, 0.19)),
        head + Vector((0.13, -0.168, 0.175)),
        head + Vector((0.105, -0.168, 0.169)),
        head + Vector((0.13, -0.168, 0.163)),
        head + Vector((0.141, -0.168, 0.148)),
        head + Vector((0.13, -0.168, 0.133)),
        head + Vector((0.092, -0.168, 0.133)),
    )
    add_tube("Aina_Hairclip_Number_3_Silver", points, 0.007, silver, rig, "head")


def tint_vroid_eyes(teal) -> None:
    for item in bpy.data.materials:
        if "eyeiris" in item.name.lower():
            item.diffuse_color = teal.diffuse_color


def create_outfit(rig, mint, cyan, charcoal, white, pink) -> None:
    chest = bone_world(rig, "chest", "spine")
    add_torso_shell("Aina_InnerShirt", chest + Vector((0, -0.006, -0.05)), 0.17, 0.145, 0.108, 0.37, white, rig, "chest", "spine")
    add_panel(
        "Aina_Hoodie_Back",
        (
            chest + Vector((-0.195, 0.125, 0.12)),
            chest + Vector((0.195, 0.125, 0.12)),
            chest + Vector((0.175, 0.125, -0.165)),
            chest + Vector((-0.175, 0.125, -0.165)),
        ),
        mint,
        rig,
        "chest",
        "spine",
        thickness=0.014,
    )
    for side, suffix in ((-1, "L"), (1, "R")):
        inner = side * 0.085
        outer = side * 0.195
        add_panel(
            f"Aina_Hoodie_Front_{suffix}",
            (
                chest + Vector((inner, -0.125, 0.105)),
                chest + Vector((outer, -0.105, 0.12)),
                chest + Vector((side * 0.175, -0.11, -0.165)),
                chest + Vector((side * 0.075, -0.13, -0.165)),
            ),
            mint,
            rig,
            "chest",
            "spine",
            thickness=0.014,
        )
        add_panel(
            f"Aina_Hoodie_Side_{suffix}",
            (
                chest + Vector((outer, -0.105, 0.12)),
                chest + Vector((outer, 0.125, 0.12)),
                chest + Vector((side * 0.175, 0.125, -0.165)),
                chest + Vector((side * 0.175, -0.11, -0.165)),
            ),
            mint,
            rig,
            "chest",
            "spine",
            thickness=0.014,
        )
        add_tube(
            f"Aina_CamisoleStrap_{suffix}",
            (
                chest + Vector((side * 0.092, -0.126, 0.18)),
                chest + Vector((side * 0.07, -0.132, 0.075)),
            ),
            0.006,
            pink,
            rig,
            "chest",
            "spine",
        )
    add_tube(
        "Aina_Hoodie_Collar",
        (
            chest + Vector((-0.23, -0.11, 0.145)),
            chest + Vector((-0.12, -0.14, 0.10)),
            chest + Vector((0, -0.148, 0.082)),
            chest + Vector((0.12, -0.14, 0.10)),
            chest + Vector((0.23, -0.11, 0.145)),
        ),
        0.025,
        charcoal,
        rig,
        "chest",
        "spine",
    )
    add_tube(
        "Aina_Hoodie_Collar_Back",
        (
            chest + Vector((-0.23, 0.11, 0.145)),
            chest + Vector((0, 0.145, 0.10)),
            chest + Vector((0.23, 0.11, 0.145)),
        ),
        0.025,
        charcoal,
        rig,
        "chest",
        "spine",
    )
    hips = bone_world(rig, "hips")
    add_torso_shell("Aina_Shorts_Waist", hips + Vector((0, 0, 0.035)), 0.17, 0.165, 0.105, 0.17, charcoal, rig, "hips")
    for side, suffix in ((-1, "L"), (1, "R")):
        upper_names = (f"J_Bip_{suffix}_UpperArm", f"upper_arm.{suffix}", f"upperarm_{suffix.lower()}")
        lower_names = (f"J_Bip_{suffix}_LowerArm", f"lower_arm.{suffix}", f"lowerarm_{suffix.lower()}")
        thigh_names = (f"J_Bip_{suffix}_UpperLeg", f"upper_leg.{suffix}", f"thigh.{suffix}")
        shin_names = (f"J_Bip_{suffix}_LowerLeg", f"lower_leg.{suffix}", f"shin.{suffix}")
        foot_names = (f"J_Bip_{suffix}_Foot", f"foot.{suffix}")
        upper = bone_world(rig, *upper_names)
        lower = bone_world(rig, *lower_names)
        hand_names = (f"J_Bip_{suffix}_Hand", f"hand.{suffix}")
        hand = bone_world(rig, *hand_names)
        thigh = bone_world(rig, *thigh_names)
        shin = bone_world(rig, *shin_names)
        foot = bone_world(rig, *foot_names)
        lower_arm_direction = (hand - lower).normalized()
        shoulder_start = chest + Vector((math.copysign(0.175, upper.x - chest.x), 0, 0.075))
        add_sleeve(
            f"Aina_Hoodie_Shoulder_{suffix}",
            shoulder_start,
            upper,
            0.068,
            cyan,
            rig,
            "chest",
            "spine",
        )
        add_sleeve(f"Aina_Hoodie_UpperSleeve_{suffix}", upper, lower, 0.058, cyan, rig, *upper_names)
        add_sleeve(f"Aina_Hoodie_LowerSleeve_{suffix}", lower, hand, 0.06, cyan, rig, *lower_names)
        add_sleeve(f"Aina_Hoodie_Cuff_{suffix}", hand - lower_arm_direction * 0.026, hand + lower_arm_direction * 0.026, 0.058, charcoal, rig, *hand_names)
        add_cube(f"Aina_Shorts_{suffix}", thigh + Vector((0, 0, 0.005)), (0.105, 0.09, 0.105), charcoal, rig, *thigh_names, bevel=0.035)
        sock_top = foot + (shin - foot) * 0.38
        add_limb(f"Aina_Sock_{suffix}", sock_top, foot, 0.045, white, rig, *shin_names)
        shoe = add_cube(f"Aina_Sneaker_{suffix}", foot + Vector((0, -0.065, -0.025)), (0.062, 0.12, 0.032), white, rig, *foot_names, bevel=0.024)
        shoe.rotation_euler.x = math.radians(-8)
        sole = add_cube(f"Aina_SneakerSole_{suffix}", foot + Vector((0, -0.065, -0.052)), (0.066, 0.125, 0.012), white, rig, *foot_names, bevel=0.012)
        sole.rotation_euler.x = math.radians(-8)


def main() -> None:
    args = parse_args()
    input_vrm = Path(args.input).resolve()
    if "seed-san" in input_vrm.name.lower():
        raise RuntimeError("Seed-san ditolak sebagai base Aina.")
    if not hasattr(bpy.ops.import_scene, "vrm") or not hasattr(bpy.ops.export_scene, "vrm"):
        raise RuntimeError("VRM Add-on belum aktif. Jalankan setup_vrm_addon.ps1 dahulu.")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.vrm(filepath=str(input_vrm))
    reject_robot_artifacts()
    remove_old_aina_parts()
    strip_base_costume_geometry()
    rig = armature()

    cyan = material("Aina_Cyan", "#7ED8F2")
    blue = material("Aina_BlueTips", "#7E8CCF")
    mint = material("Aina_Mint", "#8DE6C9")
    charcoal = material("Aina_Charcoal", "#3B3F45")
    pink = material("Aina_Pink", "#F5A4C8")
    silver = material("Aina_SilverMetal", "#C8CDD5", metallic=0.78, roughness=0.28)
    teal = material("Aina_TealEyes", "#4FC1B3")
    white = material("Aina_White", "#E6E9EE")
    create_hair(rig, cyan, blue)
    create_glasses(rig, pink)
    create_hairclip(rig, silver)
    tint_vroid_eyes(teal)
    create_outfit(rig, mint, cyan, charcoal, white, pink)

    Path(args.output).resolve().parent.mkdir(parents=True, exist_ok=True)
    Path(args.blend).resolve().parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.blend).resolve()))
    bpy.ops.export_scene.vrm(filepath=str(Path(args.output).resolve()))
    print(f"Aina VRM exported: {args.output}")


if __name__ == "__main__":
    main()
