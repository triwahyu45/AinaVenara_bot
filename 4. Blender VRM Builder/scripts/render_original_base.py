import sys
from pathlib import Path
import bpy

# Set up paths
input_vrm = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/Aina_Venara_v0.vrm"))
output_dir = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/previews/v0_base"))
output_dir.mkdir(parents=True, exist_ok=True)

# Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Import model based on file type
if input_vrm.suffix.lower() == ".vrm":
    bpy.ops.import_scene.vrm(filepath=str(input_vrm))
else:
    bpy.ops.import_scene.gltf(filepath=str(input_vrm))

# Prepare camera and lighting
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
camera = bpy.context.object
scene.camera = camera

# Lights
for location, energy, size in (((-2.5, -3, 3), 320, 4), ((2, -1, 1.5), 140, 3), ((0, 2, 2.5), 220, 3)):
    bpy.ops.object.light_add(type="AREA", location=location)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = size

def look_at(cam, target):
    from mathutils import Vector
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()

def render_view(name, cam_loc, target, lens=58):
    from mathutils import Vector
    camera.location = cam_loc
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(output_dir / f"{name}.png")
    bpy.ops.render.render(write_still=True)

from mathutils import Vector
center = Vector((0, 0, 0.85))
render_view("front", Vector((0, -4.2, 0.95)), center)
render_view("left", Vector((-4.2, 0, 0.95)), center)
render_view("right", Vector((4.2, 0, 0.95)), center)
render_view("back", Vector((0, 4.2, 0.95)), center)
render_view("face", Vector((0, -1.55, 1.42)), Vector((0, 0, 1.42)), lens=72)
render_view("top", Vector((0, -0.15, 4.4)), Vector((0, 0, 1.25)), lens=62)

print("Original base renders completed.")
