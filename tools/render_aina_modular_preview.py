from pathlib import Path
import math

import bpy


ROOT = Path(str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model"))
OUT_DIR = ROOT / "Modular Output"
MASTER_BLEND = OUT_DIR / "Aina_Venara_Master.blend"
PREVIEW = OUT_DIR / "Aina_Venara_Modular_Preview.png"


def hide_reference():
    for obj in bpy.data.objects:
        if obj.name.startswith("Reference_Tripo_Blockout"):
            obj.hide_render = True
            obj.hide_viewport = True


def set_camera(name, loc, rot):
    bpy.ops.object.camera_add(location=loc, rotation=rot)
    cam = bpy.context.object
    cam.name = name
    cam.data.lens = 70
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 1.75
    bpy.context.scene.camera = cam
    return cam


def render_to(path, camera):
    bpy.context.scene.camera = camera
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(MASTER_BLEND))
    hide_reference()
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    bpy.context.scene.eevee.taa_render_samples = 32
    bpy.context.scene.render.resolution_x = 768
    bpy.context.scene.render.resolution_y = 1024
    bpy.context.scene.world.color = (1, 1, 1)
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            obj.hide_render = True
    bpy.ops.object.light_add(type="AREA", location=(0, -3, 3))
    light = bpy.context.object
    light.data.energy = 600
    light.data.size = 4
    cameras = [
        set_camera("QA_Front", (0, -3.0, 0.85), (math.radians(90), 0, 0)),
        set_camera("QA_Left", (-3.0, 0, 0.85), (math.radians(90), 0, math.radians(-90))),
        set_camera("QA_Back", (0, 3.0, 0.85), (math.radians(90), 0, math.radians(180))),
    ]
    temp_paths = []
    for camera in cameras:
        path = OUT_DIR / f"{camera.name}.png"
        temp_paths.append(path)
        render_to(path, camera)

    print(f"Rendered QA views to {OUT_DIR}")


if __name__ == "__main__":
    main()
