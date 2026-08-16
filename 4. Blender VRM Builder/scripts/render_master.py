from pathlib import Path
"""
render_master.py - Render the master blend file to inspect its visual quality.
"""
import bpy, os, math

ROOT = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
MASTER_BLEND = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
OUT_DIR = os.path.join(ROOT, "output", "previews", "master_check")
os.makedirs(OUT_DIR, exist_ok=True)

# Load master blend file
bpy.ops.wm.open_mainfile(filepath=MASTER_BLEND)

# Configure renderer
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 64
scene.render.resolution_x = 512
scene.render.resolution_y = 512

# Find or create camera
cam = bpy.data.objects.get("Camera")
if not cam:
    cam_d = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_d)
    bpy.context.scene.collection.objects.link(cam)
scene.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 1.9

# Move camera to view the model frontally
cam.location = (0.0, -3.5, 0.9)
cam.rotation_euler = (math.radians(90), 0, 0)

# Set rendering filepath
scene.render.filepath = os.path.join(OUT_DIR, "front.png")
bpy.ops.render.render(write_still=True)
print("Rendered master front view!")

# Render closeup face view
cam.location = (0.0, -1.2, 1.45)
cam.data.ortho_scale = 0.5
scene.render.filepath = os.path.join(OUT_DIR, "face.png")
bpy.ops.render.render(write_still=True)
print("Rendered master face view!")
