from pathlib import Path
"""
render_and_export_master.py
============================
Use the Aina_Venara_Master.blend directly - no mixing with VRoid base.
Just render proper 6-view contact sheet + export VRM from the master armature.
"""

import bpy, os, sys, math
from mathutils import Vector

ROOT = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
MASTER_BLEND = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
OUT_VRM  = os.path.join(ROOT, "output", "Aina_Venara_v15.vrm")
PREV = os.path.join(ROOT, "output", "previews", "v15")
os.makedirs(PREV, exist_ok=True)

# ── 1. Load master blend ──────────────────────────────────────────────────
print("[v15] Loading Master Blend...")
bpy.ops.wm.open_mainfile(filepath=MASTER_BLEND)

# Remove Reference_Tripo blockout object (not needed for final)
for obj in list(bpy.data.objects):
    if obj.name.startswith("Reference_Tripo"):
        bpy.data.objects.remove(obj, do_unlink=True)

# ── 2. Inspect armature and print bone info ───────────────────────────────
rig = next((o for o in bpy.data.objects if o.type=="ARMATURE"), None)
if not rig:
    print("ERROR: no armature found!"); sys.exit(1)
print(f"[v15] Using armature: {rig.name}")

# Find head bone position in world space
bpy.context.view_layer.update()
head_z = 1.39   # default
for bone_name in ["Head", "head", "J_Bip_C_Head", "Bip_Head"]:
    b = rig.pose.bones.get(bone_name)
    if b:
        pos = (rig.matrix_world @ b.matrix).translation
        head_z = pos.z
        print(f"[v15] Head bone: {bone_name} at z={head_z:.3f}")
        break

# ── 3. Setup proper materials for all objects ─────────────────────────────
print("[v15] Ensuring materials are properly assigned...")

def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_HAIR   = srgb("#7ED8F2")
C_HAIR_T = srgb("#7E8CCF")
C_GLASS  = srgb("#F5A4C8")
C_CLIP   = srgb("#C0C0C0")

def make_mat(name, rgba, roughness=0.7, metallic=0.0):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat

# Fix any missing material assignments
for obj in bpy.data.objects:
    if obj.type not in ["MESH","CURVE"]: continue
    on = obj.name.lower()
    # Only fix objects with no material
    if not obj.material_slots or not obj.material_slots[0].material:
        if "hair" in on and "violet" not in on and "tip" not in on:
            mat = make_mat("M_Hair_Cyan", C_HAIR, roughness=0.35)
            if len(obj.material_slots) == 0:
                obj.data.materials.append(mat)
            else:
                obj.material_slots[0].material = mat

# ── 4. Setup renderer ─────────────────────────────────────────────────────
print("[v15] Setting up renderer...")
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.render.resolution_x = 512
scene.render.resolution_y = 512

# Set up camera - reuse existing or create new
cam_obj = bpy.data.objects.get("Camera")
if cam_obj:
    cam_d = cam_obj.data
else:
    cam_d = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_d)
    bpy.context.scene.collection.objects.link(cam_obj)
scene.camera = cam_obj
cam_d.type = "ORTHO"

# World background
if scene.world:
    world = scene.world
else:
    world = bpy.data.worlds.new("World")
    scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.07, 1.0)
    bg.inputs["Strength"].default_value = 0.4

# Remove existing lights, add 3-point studio lighting
for obj in list(bpy.data.objects):
    if obj.type == "LIGHT" and obj.name.startswith("QA_Area"):
        bpy.data.objects.remove(obj, do_unlink=True)

def add_sun(n, energy, angle_h, angle_v, col=(1,1,1)):
    ld = bpy.data.lights.new(n, "SUN")
    ld.energy = energy
    ld.color = col
    ld.angle = math.radians(15)
    lo = bpy.data.objects.new(n, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(angle_v), 0, math.radians(angle_h))
    return lo

add_sun("Key",  5.0,  30, 50, (1.0, 0.97, 0.95))    # warm key light
add_sun("Fill", 2.5, -30, 30, (0.7, 0.85, 1.0))      # cool fill light
add_sun("Rim",  3.0, 160, 40, (0.6, 0.4, 1.0))       # purple rim light

# ── 5. Render 6-view contact sheet ───────────────────────────────────────
print("[v15] Rendering 6 views...")

CENTER     = Vector((0.0, 0.0, 0.85))   # character centre
HEAD_PT    = Vector((0.0, 0.0, head_z))

def rview(name, cam_loc, ortho_scale, look_at=CENTER):
    cam_obj.location = cam_loc
    d = look_at - cam_loc
    cam_obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam_d.ortho_scale = ortho_scale
    scene.render.filepath = os.path.join(PREV, name + ".png")
    bpy.ops.render.render(write_still=True)
    print(f"  ✓ {name}")

rview("front", Vector((0.0, -3.0, 0.85)), 1.60)
rview("left",  Vector((3.0,  0.0, 0.85)), 1.60)
rview("right", Vector((-3.0, 0.0, 0.85)), 1.60)
rview("back",  Vector((0.0,  3.0, 0.85)), 1.60)
rview("face",  Vector((0.0, -0.5, head_z + 0.04)), 0.38, HEAD_PT)
rview("top",   Vector((0.0, -0.1, 5.0)),  1.10, HEAD_PT)

# ── 6. Export VRM ─────────────────────────────────────────────────────────
print("[v15] Exporting VRM...")
try:
    bpy.ops.export_scene.vrm(filepath=OUT_VRM)
    print(f"[v15] VRM saved: {OUT_VRM}")
except Exception as e:
    print(f"[v15] VRM export warning: {e}")

# Also save blend
blend_out = OUT_VRM.replace(".vrm", ".blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_out)
print(f"[v15] BLEND saved: {blend_out}")
print("[v15] Done!")
