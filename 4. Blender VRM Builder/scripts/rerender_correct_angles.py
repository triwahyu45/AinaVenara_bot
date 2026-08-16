"""
rerender_correct_angles.py - Render ulang dengan kamera yang benar.
Model menghadap +Y, jadi kamera front harus dari +Y (bukan -Y).
"""
from pathlib import Path
import bpy
from mathutils import Vector

BLEND_IN = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/Aina_Venara_v12.blend"))
PREVIEW_DIR = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/previews/v12"))
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(BLEND_IN))

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 512
scene.render.resolution_y = 768
scene.render.film_transparent = False
scene.world.color = (0.025, 0.03, 0.04)

for obj in list(scene.objects):
    if obj.type in {"CAMERA", "LIGHT"}:
        bpy.data.objects.remove(obj, do_unlink=True)

bpy.ops.object.camera_add()
scene.camera = bpy.context.object

for loc, energy, size in (((-2.5, 3, 3), 500, 4), ((2, 1, 1.5), 250, 3), ((0, -2, 2.5), 350, 3)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = size

def look_at(cam, target):
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()

center = Vector((0, 0, 0.76))
head   = Vector((0, 0, 1.42))

# Model menghadap +Y, jadi kamera front dari +Y
views = [
    ("front", Vector((0, 3.5, 0.85)),   center, 58),   # dari +Y, lihat ke -Y
    ("left",  Vector((3.5, 0, 0.85)),   center, 58),   # dari +X (kanan model)
    ("right", Vector((-3.5, 0, 0.85)),  center, 58),   # dari -X (kiri model)
    ("back",  Vector((0, -3.5, 0.85)),  center, 58),   # dari -Y (belakang)
    ("face",  Vector((0, 1.3, 1.50)),   head,   80),   # wajah dari +Y
    ("top",   Vector((0, 0.1, 4.0)),    Vector((0, 0, 1.2)), 62),
]

for name, cam_loc, target, lens in views:
    scene.camera.location = cam_loc
    scene.camera.data.lens = lens
    look_at(scene.camera, target)
    scene.render.filepath = str(PREVIEW_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {name}")

print("All renders done!")
