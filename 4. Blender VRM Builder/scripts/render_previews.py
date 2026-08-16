import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def look_at(camera, target):
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def prepare_scene():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.025, 0.03, 0.04)
    for obj in list(scene.objects):
        if obj.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.object.camera_add()
    scene.camera = bpy.context.object
    scene.camera.data.lens = 58
    for location, energy, size in (((-2.5, -3, 3), 320, 4), ((2, -1, 1.5), 140, 3), ((0, 2, 2.5), 220, 3)):
        bpy.ops.object.light_add(type="AREA", location=location)
        bpy.context.object.data.energy = energy
        bpy.context.object.data.shape = "DISK"
        bpy.context.object.data.size = size
    return scene


def render(scene, output, name, location, target, lens=58):
    scene.camera.location = location
    scene.camera.data.lens = lens
    look_at(scene.camera, target)
    scene.render.filepath = str(output / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def main():
    args = parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    scene = prepare_scene()
    center = Vector((0, 0, 0.85))
    render(scene, output, "front", Vector((0, -4.2, 0.95)), center)
    render(scene, output, "left", Vector((-4.2, 0, 0.95)), center)
    render(scene, output, "right", Vector((4.2, 0, 0.95)), center)
    render(scene, output, "back", Vector((0, 4.2, 0.95)), center)
    render(scene, output, "face", Vector((0, -1.55, 1.42)), Vector((0, 0, 1.42)), lens=72)
    render(scene, output, "top", Vector((0, -0.15, 4.4)), Vector((0, 0, 1.25)), lens=62)


if __name__ == "__main__":
    main()
