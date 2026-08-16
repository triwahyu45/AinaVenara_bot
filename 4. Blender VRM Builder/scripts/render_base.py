from pathlib import Path
"""
render_base.py - Render the base model directly to see what it looks like.
"""
import bpy, os

ROOT = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
BASE = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/VRM Draft/Aina_Venara_Base.vrm")
OUT_DIR = os.path.join(ROOT, "output", "previews", "base_check")
os.makedirs(OUT_DIR, exist_ok=True)

# Clear
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

# Import
bpy.ops.import_scene.vrm(filepath=BASE)
for o in bpy.data.objects:
    if o.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(o)

# Render front view
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 64
scene.render.resolution_x = 512
scene.render.resolution_y = 512

cam_d = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_d)
bpy.context.scene.collection.objects.link(cam)
scene.camera = cam
cam_d.type = "ORTHO"
cam_d.ortho_scale = 1.9

world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.1, 0.1, 0.12, 1.0)
scene.world = world

def add_sun(n, loc, energy):
    ld = bpy.data.lights.new(n, "SUN")
    ld.energy = energy
    lo = bpy.data.objects.new(n, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (0.7, 0, 0.5)

add_sun("Sun", (2, -2, 5), 4.0)

cam.location = (0.0, -3.5, 0.85)
import math
cam.rotation_euler = (math.radians(90), 0, 0)

scene.render.filepath = os.path.join(OUT_DIR, "front.png")
bpy.ops.render.render(write_still=True)
print("Rendered base model front view!")
