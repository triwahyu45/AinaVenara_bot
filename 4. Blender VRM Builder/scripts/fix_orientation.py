"""
fix_orientation.py  - Quick fix: rotasi mesh 180° di Y supaya wajah menghadap kamera front.
Jalankan setelah v12b build. Load blend, fix, re-export, re-render.
"""
import math
from pathlib import Path
import bpy
from mathutils import Vector

BLEND_IN  = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/Aina_Venara_v12.blend"))
OUTPUT_VRM = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/Aina_Venara_v12.vrm"))
PREVIEW_DIR = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/previews/v12"))
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

# Load existing blend
bpy.ops.wm.open_mainfile(filepath=str(BLEND_IN))

# Find GLB mesh
glb_mesh = None
armature = None
for obj in bpy.context.scene.objects:
    if obj.type == "MESH":
        glb_mesh = obj
    elif obj.type == "ARMATURE":
        armature = obj

if glb_mesh is None:
    raise RuntimeError("No mesh found!")

print(f"Mesh: {glb_mesh.name}, Armature: {armature.name if armature else 'None'}")

# Check current rotation
print(f"Current rotation: {[math.degrees(r) for r in glb_mesh.rotation_euler]}")

# Unparent, fix rotation, reparent
bpy.ops.object.select_all(action="DESELECT")
glb_mesh.select_set(True)
bpy.context.view_layer.objects.active = glb_mesh

# Clear parent keeping transform
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")

# Add 180 deg Z rotation to face -Y (Blender front direction)
# If current Z rot is 180 (from v12b), set to 0 to face +Y, which means back in Blender
# Actually in Blender: camera at (0, -distance, h) looks toward +Y
# Character should face +Y for "front" view from (0, -d, h)
# Set rotation Z to 0
glb_mesh.rotation_euler.z = 0
bpy.ops.object.select_all(action="DESELECT")
glb_mesh.select_set(True)
bpy.context.view_layer.objects.active = glb_mesh
bpy.ops.object.transform_apply(rotation=True)
print("Reset Z rotation to 0 (face +Y = Blender front)")

# Reparent with envelope weights
bpy.ops.object.select_all(action="DESELECT")
glb_mesh.select_set(True)
armature.select_set(True)
bpy.context.view_layer.objects.active = armature
bpy.ops.object.parent_set(type="ARMATURE_ENVELOPE")
print("Reparented.")

# Smooth shading
bpy.ops.object.select_all(action="DESELECT")
glb_mesh.select_set(True)
bpy.context.view_layer.objects.active = glb_mesh
bpy.ops.object.shade_smooth()

# Export VRM
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = armature
bpy.ops.export_scene.vrm(filepath=str(OUTPUT_VRM))
print(f"VRM exported: {OUTPUT_VRM}")

# Render
def look_at(cam, target):
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()

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
for loc, energy, size in (((-2.5, -3, 3), 500, 4), ((2, -1, 1.5), 250, 3), ((0, 2, 2.5), 350, 3)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = size

center = Vector((0, 0, 0.76))
head   = Vector((0, 0, 1.42))

views = [
    ("front", Vector((0, -3.5, 0.85)),  center, 58),
    ("left",  Vector((-3.5, 0, 0.85)),  center, 58),
    ("right", Vector((3.5, 0, 0.85)),   center, 58),
    ("back",  Vector((0, 3.5, 0.85)),   center, 58),
    ("face",  Vector((0, -1.3, 1.50)),  head, 80),
    ("top",   Vector((0, -0.1, 4.0)),   Vector((0, 0, 1.2)), 62),
]

for name, cam_loc, target, lens in views:
    scene.camera.location = cam_loc
    scene.camera.data.lens = lens
    look_at(scene.camera, target)
    scene.render.filepath = str(PREVIEW_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {name}")

print("Done!")
