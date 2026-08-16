from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--params", required=True)
    parser.add_argument("--resolution", type=int, default=512)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def look_at(camera, target):
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def named(prefix):
    return [obj for obj in bpy.context.scene.objects if obj.name.startswith(prefix)]


def scale_named(prefix, scale):
    if isinstance(scale, (int, float)):
        scale = (scale, scale, scale)
    for obj in named(prefix):
        obj.scale.x *= scale[0]
        obj.scale.y *= scale[1]
        obj.scale.z *= scale[2]


def corrective_shape_key(name, object_match, scale):
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or object_match not in obj.name.lower():
            continue
        if not obj.data.vertices:
            continue
        if obj.data.shape_keys is None:
            obj.shape_key_add(name="Basis")
        key = obj.data.shape_keys.key_blocks.get(name) or obj.shape_key_add(name=name)
        center = sum((vertex.co for vertex in obj.data.vertices), Vector()) / len(obj.data.vertices)
        for index, vertex in enumerate(obj.data.vertices):
            relative = vertex.co - center
            key.data[index].co = center + Vector((relative.x * scale[0], relative.y * scale[1], relative.z * scale[2]))
        key.value = 1.0


def apply_params(params):
    corrective_shape_key("Aina_FitBodyCorrective", "body", (params["body_width"], params["body_depth"], params["body_height"]))
    corrective_shape_key("Aina_FitFaceCorrective", "face", (params["head_width"], params["head_depth"], params["head_height"]))
    scale_named("Aina_Hair_", params["hair_scale"])
    scale_named("Aina_Bangs_", params["bang_scale"])
    scale_named("Aina_Ahoge", params["ahoge_scale"])
    scale_named("Aina_Hairclip", params["hairclip_scale"])
    scale_named("Aina_Glasses_", params["glasses_scale"])
    scale_named("Aina_Hoodie_", (params["hoodie_width"], params["hoodie_depth"], params["hoodie_height"]))
    scale_named("Aina_Shorts_", params["shorts_scale"])
    scale_named("Aina_Sock_", params["sock_scale"])
    scale_named("Aina_Sneaker_", params["shoe_scale"])
    # Conservative head correction: scale head-attached identity accessories together.
    for prefix in ("Aina_Hair_", "Aina_Bangs_", "Aina_Ahoge", "Aina_Hairclip", "Aina_Glasses_"):
        scale_named(prefix, (params["head_width"], params["head_depth"], params["head_height"]))


def pose_bone(rig, candidates, z_degrees):
    for item in rig.pose.bones:
        if any(candidate.lower() in item.name.lower() for candidate in candidates):
            item.rotation_mode = "XYZ"
            item.rotation_euler.z = math.radians(z_degrees)
            return


def apply_relaxed_a_pose():
    rigs = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if not rigs:
        return
    rig = rigs[0]
    pose_bone(rig, ("J_Bip_L_UpperArm", "upper_arm.L", "leftupperarm"), -55)
    pose_bone(rig, ("J_Bip_R_UpperArm", "upper_arm.R", "rightupperarm"), 55)
    pose_bone(rig, ("J_Bip_L_LowerArm", "lower_arm.L", "leftlowerarm"), -4)
    pose_bone(rig, ("J_Bip_R_LowerArm", "lower_arm.R", "rightlowerarm"), 4)


def prepare_scene(resolution):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = True
    scene.world.color = (1.0, 1.0, 1.0)
    for obj in list(scene.objects):
        if obj.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.object.camera_add()
    scene.camera = bpy.context.object
    scene.camera.data.type = "ORTHO"
    scene.camera.data.ortho_scale = 2.05
    for location, energy, size in (((-2.5, -3, 3), 280, 4), ((2, -1, 1.5), 120, 3), ((0, 2, 2.5), 180, 3)):
        bpy.ops.object.light_add(type="AREA", location=location)
        bpy.context.object.data.energy = energy
        bpy.context.object.data.shape = "DISK"
        bpy.context.object.data.size = size
    return scene


def render(scene, output, name, location, target, ortho=2.05):
    scene.camera.location = location
    scene.camera.data.ortho_scale = ortho
    look_at(scene.camera, target)
    scene.render.filepath = str(output / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def main():
    args = parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    params = json.loads(Path(args.params).read_text(encoding="utf-8"))
    apply_params(params)
    apply_relaxed_a_pose()
    scene = prepare_scene(args.resolution)
    center = Vector((0, 0, 0.85))
    render(scene, output, "front", Vector((0, -4.2, 0.95)), center)
    render(scene, output, "left", Vector((-4.2, 0, 0.95)), center)
    render(scene, output, "right", Vector((4.2, 0, 0.95)), center)
    render(scene, output, "back", Vector((0, 4.2, 0.95)), center)
    render(scene, output, "front_left_3q", Vector((-3.0, -3.0, 0.95)), center)
    render(scene, output, "front_right_3q", Vector((3.0, -3.0, 0.95)), center)
    render(scene, output, "face_front", Vector((0, -4.2, 1.45)), Vector((0, 0, 1.45)), ortho=0.72)
    render(scene, output, "head_top", Vector((0, -0.03, 4.4)), Vector((0, 0, 1.45)), ortho=0.72)


if __name__ == "__main__":
    main()
