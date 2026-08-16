import json
import math
import os
import struct
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model"))
OUT_DIR = ROOT / "Modular Output"
TRIPO_GLB = ROOT / "Trip AI Export" / "Aina+Venara.glb"
MASTER_BLEND = OUT_DIR / "Aina_Venara_Master.blend"
MODULAR_GLB = OUT_DIR / "Aina_Venara_Modular.glb"
MODULAR_VRM = OUT_DIR / "Aina_Venara_Modular.vrm"
REPORT = OUT_DIR / "Aina_Venara_Modular_Report.json"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def mat(name, color, roughness=0.85, metallic=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return material


def add_uv_sphere(name, loc, scale, material, segments=48, rings=24, collection=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    if collection:
        link_to_collection(obj, collection)
    return obj


def add_cube(name, loc, scale, material, collection=None):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("soft bevel", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 3
    obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    if collection:
        link_to_collection(obj, collection)
    return obj


def add_cylinder(name, loc, radius, depth, material, vertices=32, rotation=(0, 0, 0), scale=(1, 1, 1), collection=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    if collection:
        link_to_collection(obj, collection)
    return obj


def add_torus(name, loc, major_radius, minor_radius, material, rotation=(0, 0, 0), collection=None):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=72,
        minor_segments=10,
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=loc,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    if collection:
        link_to_collection(obj, collection)
    return obj


def add_curve(name, points, material, bevel_depth=0.01, resolution=4, collection=None):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 4
    poly = curve.splines.new("POLY")
    poly.points.add(len(points) - 1)
    for p, co in zip(poly.points, points):
        p.co = (co[0], co[1], co[2], 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    if collection:
        link_to_collection(obj, collection)
    return obj


def link_to_collection(obj, collection):
    if obj.name not in collection.objects:
        collection.objects.link(obj)
    for coll in list(obj.users_collection):
        if coll != collection and coll.name != "Scene Collection":
            try:
                coll.objects.unlink(obj)
            except RuntimeError:
                pass


def collection(name):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def add_shape_keys(obj, names):
    obj.shape_key_add(name="Basis")
    for name in names:
        obj.shape_key_add(name=name)


def create_armature():
    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm = bpy.context.object
    arm.name = "Aina_Venara_Humanoid_Armature"
    arm.data.name = "Aina_Venara_Humanoid_Skeleton"
    arm.show_in_front = True
    bpy.ops.object.mode_set(mode="EDIT")
    bones = arm.data.edit_bones
    root = bones[0]
    root.name = "hips"
    root.head = (0, 0, 0.78)
    root.tail = (0, 0, 0.92)

    def bone(name, head, tail, parent=None):
        b = bones.new(name)
        b.head = head
        b.tail = tail
        if parent:
            b.parent = bones[parent]
        return b

    bone("spine", (0, 0, 0.90), (0, 0, 1.08), "hips")
    bone("chest", (0, 0, 1.08), (0, 0, 1.22), "spine")
    bone("neck", (0, 0, 1.22), (0, 0, 1.29), "chest")
    bone("head", (0, 0, 1.29), (0, 0, 1.52), "neck")
    bone("leftUpperArm", (-0.12, 0, 1.18), (-0.38, 0, 1.08), "chest")
    bone("leftLowerArm", (-0.38, 0, 1.08), (-0.56, 0, 0.98), "leftUpperArm")
    bone("leftHand", (-0.56, 0, 0.98), (-0.64, 0, 0.95), "leftLowerArm")
    bone("rightUpperArm", (0.12, 0, 1.18), (0.38, 0, 1.08), "chest")
    bone("rightLowerArm", (0.38, 0, 1.08), (0.56, 0, 0.98), "rightUpperArm")
    bone("rightHand", (0.56, 0, 0.98), (0.64, 0, 0.95), "rightLowerArm")
    bone("leftUpperLeg", (-0.07, 0, 0.78), (-0.10, 0, 0.47), "hips")
    bone("leftLowerLeg", (-0.10, 0, 0.47), (-0.10, 0, 0.16), "leftUpperLeg")
    bone("leftFoot", (-0.10, 0, 0.16), (-0.10, -0.12, 0.05), "leftLowerLeg")
    bone("rightUpperLeg", (0.07, 0, 0.78), (0.10, 0, 0.47), "hips")
    bone("rightLowerLeg", (0.10, 0, 0.47), (0.10, 0, 0.16), "rightUpperLeg")
    bone("rightFoot", (0.10, 0, 0.16), (0.10, -0.12, 0.05), "rightLowerLeg")
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def assign_parent(obj, armature):
    obj.parent = armature
    obj["modular_part"] = obj.name


def create_character():
    OUT_DIR.mkdir(exist_ok=True)
    clear_scene()

    mats = {
        "skin": mat("MAT_Skin_soft_peach", (1.0, 0.79, 0.68, 1)),
        "hair": mat("MAT_Hair_cyan", (0.48, 0.86, 0.95, 1)),
        "hair_tip": mat("MAT_Hair_blue_violet_tips", (0.43, 0.50, 0.82, 1)),
        "eye": mat("MAT_Eye_teal", (0.02, 0.72, 0.78, 1)),
        "eye_dark": mat("MAT_Eye_dark_limbal", (0.02, 0.11, 0.14, 1)),
        "highlight": mat("MAT_Eye_highlight", (1, 1, 1, 1)),
        "glasses": mat("MAT_Glasses_pink_plastic", (0.96, 0.29, 0.55, 1), 0.45),
        "metal": mat("MAT_Hairclip_3_silver", (0.78, 0.76, 0.70, 1), 0.35, 0.5),
        "hoodie": mat("MAT_Hoodie_cyan_mint", (0.23, 0.82, 0.78, 1)),
        "hoodie_blue": mat("MAT_Hoodie_cyan_blue_sleeves", (0.15, 0.69, 0.92, 1)),
        "rib": mat("MAT_Hoodie_charcoal_rib_collar", (0.05, 0.07, 0.10, 1)),
        "shirt": mat("MAT_Shirt_off_white", (0.96, 0.96, 0.93, 1)),
        "strap": mat("MAT_Understrap_pink", (0.95, 0.39, 0.58, 1)),
        "shorts": mat("MAT_Shorts_charcoal", (0.04, 0.06, 0.10, 1)),
        "sock": mat("MAT_Socks_white_rib", (0.95, 0.96, 0.96, 1)),
        "shoe": mat("MAT_Sneakers_off_white", (0.90, 0.91, 0.91, 1)),
        "sole": mat("MAT_Shoe_sole_light_gray", (0.72, 0.74, 0.76, 1)),
        "mouth": mat("MAT_Mouth_soft_line", (0.35, 0.11, 0.12, 1)),
    }

    coll_body = collection("Body_Base")
    coll_face = collection("Face_Eyes")
    coll_hair = collection("Hair_Base")
    coll_ahoge = collection("Hair_Ahoge")
    coll_glasses = collection("Accessory_Glasses_Pink")
    coll_clip = collection("Accessory_Hairclip_3")
    coll_outfit = collection("Outfit_Modular")
    coll_ref = collection("Reference_Tripo_Blockout")
    coll_ref.hide_viewport = True
    coll_ref.hide_render = True

    arm = create_armature()

    # Body proportions: 1.52 m tall, anime head-heavy silhouette.
    parts = []
    parts.append(add_uv_sphere("Body_Base_Head", (0, -0.02, 1.31), (0.135, 0.115, 0.16), mats["skin"], collection=coll_body))
    parts.append(add_uv_sphere("Body_Base_Neck", (0, -0.005, 1.14), (0.045, 0.035, 0.055), mats["skin"], 32, 16, coll_body))
    parts.append(add_uv_sphere("Body_Base_Torso", (0, 0, 0.91), (0.135, 0.075, 0.22), mats["skin"], 40, 20, coll_body))
    for side, sx in [("L", -1), ("R", 1)]:
        parts.append(add_cylinder(f"Body_Base_{side}_UpperArm", (sx * 0.245, 0, 0.86), 0.034, 0.34, mats["skin"], scale=(0.85, 0.75, 1), collection=coll_body))
        parts.append(add_uv_sphere(f"Body_Base_{side}_Hand", (sx * 0.245, -0.010, 0.665), (0.038, 0.024, 0.052), mats["skin"], 28, 14, coll_body))
        parts.append(add_cylinder(f"Body_Base_{side}_Leg", (sx * 0.07, 0, 0.43), 0.04, 0.55, mats["skin"], vertices=36, collection=coll_body))

    # Face.
    for side, sx in [("L", -1), ("R", 1)]:
        eye = add_uv_sphere(f"Face_Eyes_{side}_Teal_Iris", (sx * 0.055, -0.118, 1.335), (0.030, 0.006, 0.042), mats["eye"], 32, 16, coll_face)
        parts.append(eye)
        parts.append(add_uv_sphere(f"Face_Eyes_{side}_Dark_Limbal", (sx * 0.055, -0.121, 1.335), (0.034, 0.003, 0.046), mats["eye_dark"], 32, 12, coll_face))
        parts.append(add_uv_sphere(f"Face_Eyes_{side}_Highlight", (sx * 0.043, -0.124, 1.355), (0.009, 0.002, 0.012), mats["highlight"], 16, 8, coll_face))
        parts.append(add_curve(f"Face_Eyes_{side}_Brow", [(sx * 0.028, -0.126, 1.398), (sx * 0.055, -0.130, 1.405), (sx * 0.088, -0.126, 1.400)], mats["hair"], 0.004, collection=coll_face))
    mouth = add_curve("Face_Eyes_Mouth_Smile_ShapeKeyHost", [(-0.025, -0.128, 1.275), (0, -0.134, 1.268), (0.025, -0.128, 1.275)], mats["mouth"], 0.003, collection=coll_face)
    mouth["shape_key_presets"] = "A,I,U,E,O,Smile,Sad,Angry,Surprised"
    parts.append(mouth)

    # Hair: layered bob, bangs, blue-violet lower tips.
    parts.append(add_uv_sphere("Hair_Base_Crown_Cap", (0, 0.0, 1.40), (0.155, 0.135, 0.13), mats["hair"], 56, 24, coll_hair))
    parts.append(add_uv_sphere("Hair_Base_Back_Bob_Mass", (0, 0.055, 1.28), (0.155, 0.105, 0.15), mats["hair"], 56, 24, coll_hair))
    parts.append(add_uv_sphere("Hair_Base_Back_BlueViolet_Tips", (0, 0.078, 1.16), (0.145, 0.075, 0.035), mats["hair_tip"], 48, 12, coll_hair))
    for i, x in enumerate([-0.09, -0.045, 0, 0.045, 0.09]):
        parts.append(add_uv_sphere(f"Hair_Base_Front_Bang_{i+1:02d}", (x, -0.115, 1.34 - abs(x) * 0.25), (0.04, 0.025, 0.115), mats["hair"], 28, 14, coll_hair))
    for side, sx in [("L", -1), ("R", 1)]:
        parts.append(add_uv_sphere(f"Hair_Base_{side}_Side_Lock", (sx * 0.13, -0.045, 1.24), (0.04, 0.035, 0.13), mats["hair"], 28, 14, coll_hair))
        parts.append(add_uv_sphere(f"Hair_Base_{side}_Side_Tip_BlueViolet", (sx * 0.13, -0.043, 1.12), (0.035, 0.027, 0.035), mats["hair_tip"], 24, 10, coll_hair))
    ahoge_points = [(0.00, -0.01, 1.515), (0.035, -0.01, 1.60), (-0.020, -0.01, 1.585), (0.030, -0.01, 1.665)]
    parts.append(add_curve("Hair_Ahoge_ZigZag_Replaceable", ahoge_points, mats["hair"], 0.012, collection=coll_ahoge))

    # Accessories.
    for side, sx in [("L", -1), ("R", 1)]:
        frame = add_torus(f"Accessory_Glasses_Pink_{side}_Round_Frame", (sx * 0.055, -0.135, 1.335), 0.040, 0.0045, mats["glasses"], rotation=(math.radians(90), 0, 0), collection=coll_glasses)
        frame.scale.x = 1.18
        frame.scale.z = 0.82
        parts.append(frame)
        parts.append(add_curve(f"Accessory_Glasses_Pink_{side}_Temple", [(sx * 0.095, -0.135, 1.338), (sx * 0.145, -0.08, 1.338), (sx * 0.150, 0.015, 1.315)], mats["glasses"], 0.004, collection=coll_glasses))
    parts.append(add_curve("Accessory_Glasses_Pink_Bridge", [(-0.018, -0.137, 1.336), (0, -0.141, 1.333), (0.018, -0.137, 1.336)], mats["glasses"], 0.004, collection=coll_glasses))
    parts.append(add_curve("Accessory_Hairclip_3_Silver", [(-0.055, -0.122, 1.43), (-0.020, -0.124, 1.43), (-0.048, -0.124, 1.395), (-0.015, -0.126, 1.395), (-0.050, -0.126, 1.36)], mats["metal"], 0.008, collection=coll_clip))

    # Outfit.
    parts.append(add_uv_sphere("Outfit_Shirt_OffWhite", (0, -0.035, 1.00), (0.14, 0.055, 0.23), mats["shirt"], 40, 18, coll_outfit))
    parts.append(add_curve("Outfit_Shirt_Pink_Left_Strap", [(-0.075, -0.065, 1.22), (-0.09, -0.02, 1.06)], mats["strap"], 0.008, collection=coll_outfit))
    parts.append(add_curve("Outfit_Shirt_Pink_Right_Strap", [(0.075, -0.065, 1.22), (0.09, -0.02, 1.06)], mats["strap"], 0.008, collection=coll_outfit))
    parts.append(add_uv_sphere("Outfit_Hoodie_CyanMint_Body", (0, 0.015, 0.89), (0.205, 0.095, 0.225), mats["hoodie"], 48, 20, coll_outfit))
    parts.append(add_curve("Outfit_Hoodie_Charcoal_OffShoulder_Collar_Front", [(-0.205, -0.098, 1.115), (-0.095, -0.132, 1.085), (0.0, -0.138, 1.078), (0.095, -0.132, 1.085), (0.205, -0.098, 1.115)], mats["rib"], 0.026, collection=coll_outfit))
    parts.append(add_curve("Outfit_Hoodie_Charcoal_OffShoulder_Collar_Back", [(-0.205, 0.075, 1.130), (-0.095, 0.105, 1.118), (0.0, 0.115, 1.112), (0.095, 0.105, 1.118), (0.205, 0.075, 1.130)], mats["rib"], 0.026, collection=coll_outfit))
    parts.append(add_cube("Outfit_Hoodie_Left_Open_Panel", (-0.072, -0.102, 0.98), (0.018, 0.008, 0.205), mats["shirt"], coll_outfit))
    parts.append(add_cube("Outfit_Hoodie_Right_Open_Panel", (0.072, -0.102, 0.98), (0.018, 0.008, 0.205), mats["shirt"], coll_outfit))
    parts.append(add_curve("Outfit_Hoodie_Zipper_Left", [(-0.047, -0.122, 1.14), (-0.060, -0.126, 0.78)], mats["metal"], 0.0035, collection=coll_outfit))
    parts.append(add_curve("Outfit_Hoodie_Zipper_Right", [(0.047, -0.122, 1.14), (0.060, -0.126, 0.78)], mats["metal"], 0.0035, collection=coll_outfit))
    for side, sx in [("L", -1), ("R", 1)]:
        sleeve = add_cylinder(f"Outfit_Hoodie_{side}_Sleeve_CyanBlue", (sx * 0.245, -0.005, 0.875), 0.066, 0.43, mats["hoodie_blue"], vertices=40, scale=(1.10, 0.82, 1), collection=coll_outfit)
        sleeve.rotation_euler[1] = math.radians(8 * -sx)
        parts.append(sleeve)
        parts.append(add_torus(f"Outfit_Hoodie_{side}_Cuff_Charcoal", (sx * 0.245, -0.01, 0.650), 0.043, 0.012, mats["rib"], collection=coll_outfit))
        parts.append(add_curve(f"Outfit_Hoodie_{side}_Pocket_Slit", [(sx * 0.135, -0.114, 0.89), (sx * 0.165, -0.116, 0.80)], mats["rib"], 0.006, collection=coll_outfit))
    parts.append(add_cube("Outfit_Shorts_Charcoal", (0, -0.006, 0.705), (0.145, 0.07, 0.075), mats["shorts"], coll_outfit))
    for side, sx in [("L", -1), ("R", 1)]:
        parts.append(add_cylinder(f"Outfit_Socks_{side}_White_Rib", (sx * 0.10, 0, 0.22), 0.043, 0.22, mats["sock"], vertices=36, collection=coll_outfit))
        shoe = add_cube(f"Outfit_Shoes_{side}_White_LowTop", (sx * 0.10, -0.055, 0.055), (0.055, 0.115, 0.035), mats["shoe"], coll_outfit)
        parts.append(shoe)
        parts.append(add_cube(f"Outfit_Shoes_{side}_LightGray_Sole", (sx * 0.10, -0.06, 0.023), (0.06, 0.125, 0.012), mats["sole"], coll_outfit))

    for obj in parts:
        assign_parent(obj, arm)

    # Shape-key hosts for downstream VRM authoring.
    for obj in [o for o in parts if o.type == "MESH" and o.name.startswith("Face_Eyes_")]:
        add_shape_keys(obj, ["Blink_L", "Blink_R", "Smile", "Sad", "Angry", "Surprised", "Look_Left", "Look_Right", "Look_Up", "Look_Down"])
    head = bpy.data.objects.get("Body_Base_Head")
    if head:
        add_shape_keys(head, ["A", "I", "U", "E", "O", "Smile", "Sad", "Angry", "Surprised"])

    # Keep the raw Tripo model as hidden blockout reference in the .blend only.
    if TRIPO_GLB.exists():
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(TRIPO_GLB))
        imported = [o for o in bpy.data.objects if o not in before]
        for obj in imported:
            obj.name = f"Reference_Tripo_Blockout_{obj.name}"
            link_to_collection(obj, coll_ref)
            obj.hide_viewport = True
            obj.hide_render = True

    # Camera and lights for quick visual QA.
    bpy.ops.object.light_add(type="AREA", location=(0, -3, 2.2))
    bpy.context.object.name = "QA_Area_Key_Light"
    bpy.context.object.data.energy = 500
    bpy.context.object.data.size = 4
    bpy.ops.object.camera_add(location=(0, -3.0, 1.1), rotation=(math.radians(75), 0, 0))
    bpy.context.scene.camera = bpy.context.object

    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.context.scene["Aina_Target_Height_Meters"] = 1.52
    bpy.context.scene["Aina_Modular_Output"] = "VRM-ready modular GLB; VRM metadata is post-processed into .vrm."
    bpy.context.scene["Aina_Reference_Notes"] = (
        "cyan bob hair, blue-violet tips, zigzag ahoge, silver number-3 hairclip, pink glasses, "
        "teal eyes, oversized cyan/mint off-shoulder hoodie, white shirt, charcoal shorts, white socks and sneakers"
    )

    bpy.ops.wm.save_as_mainfile(filepath=str(MASTER_BLEND))
    export_glb()
    write_vrm_from_glb()
    write_report()


def export_glb():
    for obj in bpy.data.objects:
        obj.select_set(False)
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "CURVE", "ARMATURE"} and not obj.name.startswith("Reference_Tripo_Blockout"):
            obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(MODULAR_GLB),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_materials="EXPORT",
        export_yup=True,
        export_animations=True,
        export_morph=True,
        export_skins=True,
    )


def read_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF":
        raise ValueError("Not a GLB file")
    offset = 12
    json_chunk = None
    bin_chunk = b""
    while offset < len(data):
        clen, ctype = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + clen]
        offset += clen
        if ctype == 0x4E4F534A:
            json_chunk = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            bin_chunk = chunk
    return json_chunk, bin_chunk


def write_glb(path, gltf, bin_chunk):
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_pad = (4 - len(json_bytes) % 4) % 4
    json_bytes += b" " * json_pad
    chunks = [(0x4E4F534A, json_bytes)]
    if bin_chunk:
        bin_pad = (4 - len(bin_chunk) % 4) % 4
        chunks.append((0x004E4942, bin_chunk + b"\x00" * bin_pad))
    total = 12 + sum(8 + len(chunk) for _, chunk in chunks)
    out = bytearray(struct.pack("<4sII", b"glTF", 2, total))
    for ctype, chunk in chunks:
        out += struct.pack("<II", len(chunk), ctype)
        out += chunk
    path.write_bytes(bytes(out))


def write_vrm_from_glb():
    gltf, bin_chunk = read_glb(MODULAR_GLB)
    node_index = {node.get("name"): i for i, node in enumerate(gltf.get("nodes", []))}
    bone_map = [
        ("hips", "hips"),
        ("spine", "spine"),
        ("chest", "chest"),
        ("neck", "neck"),
        ("head", "head"),
        ("leftUpperArm", "leftUpperArm"),
        ("leftLowerArm", "leftLowerArm"),
        ("leftHand", "leftHand"),
        ("rightUpperArm", "rightUpperArm"),
        ("rightLowerArm", "rightLowerArm"),
        ("rightHand", "rightHand"),
        ("leftUpperLeg", "leftUpperLeg"),
        ("leftLowerLeg", "leftLowerLeg"),
        ("leftFoot", "leftFoot"),
        ("rightUpperLeg", "rightUpperLeg"),
        ("rightLowerLeg", "rightLowerLeg"),
        ("rightFoot", "rightFoot"),
    ]
    human_bones = []
    for vrm_name, node_name in bone_map:
        if node_name in node_index:
            human_bones.append({"bone": vrm_name, "node": node_index[node_name], "useDefaultValues": True})

    gltf.setdefault("extensionsUsed", [])
    if "VRM" not in gltf["extensionsUsed"]:
        gltf["extensionsUsed"].append("VRM")
    gltf.setdefault("extensions", {})
    gltf["extensions"]["VRM"] = {
        "exporterVersion": "Codex modular postprocess 1.0",
        "specVersion": "0.0",
        "meta": {
            "title": "Aina Venara Modular",
            "version": "0.1",
            "author": "Tri Wahyu + Codex",
            "contactInformation": "",
            "reference": "Aina Venara reference sheets in Reff 3D Detailed",
            "allowedUserName": "OnlyAuthor",
            "violentUssageName": "Disallow",
            "sexualUssageName": "Disallow",
            "commercialUssageName": "Allow",
            "otherPermissionUrl": "",
            "licenseName": "Other",
            "otherLicenseUrl": "",
        },
        "humanoid": {
            "humanBones": human_bones,
            "armStretch": 0.05,
            "legStretch": 0.05,
            "upperArmTwist": 0.5,
            "lowerArmTwist": 0.5,
            "upperLegTwist": 0.5,
            "lowerLegTwist": 0.5,
            "feetSpacing": 0.0,
            "hasTranslationDoF": False,
        },
        "firstPerson": {
            "firstPersonBone": node_index.get("head", 0),
            "firstPersonBoneOffset": {"x": 0, "y": 0.06, "z": 0},
            "meshAnnotations": [],
            "lookAtTypeName": "Bone",
            "lookAtHorizontalInner": {"curve": [0, 0, 0, 0, 0, 0, 0, 0], "xRange": 90, "yRange": 10},
            "lookAtHorizontalOuter": {"curve": [0, 0, 0, 0, 0, 0, 0, 0], "xRange": 90, "yRange": 10},
            "lookAtVerticalDown": {"curve": [0, 0, 0, 0, 0, 0, 0, 0], "xRange": 90, "yRange": 10},
            "lookAtVerticalUp": {"curve": [0, 0, 0, 0, 0, 0, 0, 0], "xRange": 90, "yRange": 10},
        },
        "blendShapeMaster": {
            "blendShapeGroups": [
                {"name": "Blink", "presetName": "blink", "binds": [], "materialValues": [], "isBinary": False},
                {"name": "A", "presetName": "a", "binds": [], "materialValues": [], "isBinary": False},
                {"name": "I", "presetName": "i", "binds": [], "materialValues": [], "isBinary": False},
                {"name": "U", "presetName": "u", "binds": [], "materialValues": [], "isBinary": False},
                {"name": "E", "presetName": "e", "binds": [], "materialValues": [], "isBinary": False},
                {"name": "O", "presetName": "o", "binds": [], "materialValues": [], "isBinary": False},
                {"name": "Joy", "presetName": "joy", "binds": [], "materialValues": [], "isBinary": False},
                {"name": "Angry", "presetName": "angry", "binds": [], "materialValues": [], "isBinary": False},
                {"name": "Sorrow", "presetName": "sorrow", "binds": [], "materialValues": [], "isBinary": False},
                {"name": "Surprised", "presetName": "surprised", "binds": [], "materialValues": [], "isBinary": False},
            ]
        },
        "secondaryAnimation": {"boneGroups": [], "colliderGroups": []},
        "materialProperties": [],
    }
    write_glb(MODULAR_VRM, gltf, bin_chunk)


def mesh_stats():
    tris = 0
    verts = 0
    for obj in bpy.data.objects:
        if obj.type == "MESH" and not obj.name.startswith("Reference_Tripo_Blockout"):
            deps = bpy.context.evaluated_depsgraph_get()
            mesh = obj.evaluated_get(deps).to_mesh()
            tris += sum(max(1, len(poly.vertices) - 2) for poly in mesh.polygons)
            verts += len(mesh.vertices)
            obj.evaluated_get(deps).to_mesh_clear()
    return verts, tris


def write_report():
    verts, tris = mesh_stats()
    report = {
        "outputs": {
            "blend": str(MASTER_BLEND),
            "glb": str(MODULAR_GLB),
            "vrm": str(MODULAR_VRM),
        },
        "target_height_m": 1.52,
        "mesh_stats": {"vertices": verts, "triangles": tris},
        "modular_collections": [
            "Body_Base",
            "Face_Eyes",
            "Hair_Base",
            "Hair_Ahoge",
            "Accessory_Glasses_Pink",
            "Accessory_Hairclip_3",
            "Outfit_Modular",
        ],
        "materials": [m.name for m in bpy.data.materials if m.name.startswith("MAT_")],
        "notes": [
            "Tripo raw atlas is kept only as hidden blockout reference inside the blend.",
            "VRM file is GLB post-processed with VRM 0.x metadata and humanoid node mapping.",
            "For production tracking, bind meshes to armature weights and tune VRM blendshape binds in a VRM viewer/add-on.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    create_character()
