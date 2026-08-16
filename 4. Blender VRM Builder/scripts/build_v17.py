from pathlib import Path
"""
build_v17.py — Aina Venara v17
==============================
Fixes from v16:
  1. Bug fix: skin material matching now uses "body_base" prefix correctly
     (covers Body_Base_L_Leg, Body_Base_R_Leg, Body_Base_L_Hand, etc.)
  2. Scale hair objects down 0.82x centered at head position to reduce puffiness
  3. Brighter, more even key light for cleaner front view
  4. Export VRM + 6-view renders
"""

import bpy, os, sys, math
from mathutils import Vector, Matrix

ROOT  = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
BLEND = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
VRM   = os.path.join(ROOT, "output", "Aina_Venara_v17.vrm")
PREV  = os.path.join(ROOT, "output", "previews", "v17")
os.makedirs(PREV, exist_ok=True)

# ── colors ────────────────────────────────────────────────────────────────
def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_SKIN   = srgb("#FFE0B2")
C_HAIR   = srgb("#7ED8F2")
C_HAIR_T = srgb("#7E8CCF")
C_HOODIE = srgb("#6DCFE8")
C_COLLAR = srgb("#3B3F45")
C_SHIRT  = srgb("#E6E9EE")
C_SHORTS = srgb("#3B3F45")
C_SOCK   = srgb("#F0F2F5")
C_SHOE_W = srgb("#F5F5F4")
C_SHOE_G = srgb("#BCBCBB")
C_GLASS  = srgb("#F5A4C8")
C_CLIP   = srgb("#C8C8C8")

def make_mat(name, rgba, roughness=0.75, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = rgba
        b.inputs["Roughness"].default_value  = roughness
        b.inputs["Metallic"].default_value   = metallic
    return mat

def set_mat(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

# ── 1. Load blend ─────────────────────────────────────────────────────────
print("[v17] Loading Master Blend...")
bpy.ops.wm.open_mainfile(filepath=BLEND)

# Remove Tripo blockout
for obj in list(bpy.data.objects):
    if "tripo" in obj.name.lower() or "reference" in obj.name.lower():
        bpy.data.objects.remove(obj, do_unlink=True)

# ── 2. Pre-make material library ──────────────────────────────────────────
print("[v17] Building materials...")
M_SKIN   = make_mat("M_Skin",   C_SKIN,   roughness=0.65)
M_HAIR   = make_mat("M_Hair",   C_HAIR,   roughness=0.30)
M_HAIR_T = make_mat("M_HairT",  C_HAIR_T, roughness=0.30)
M_HOODIE = make_mat("M_Hoodie", C_HOODIE, roughness=0.75)
M_COLLAR = make_mat("M_Collar", C_COLLAR, roughness=0.80)
M_SHIRT  = make_mat("M_Shirt",  C_SHIRT,  roughness=0.80)
M_SHORTS = make_mat("M_Shorts", C_SHORTS, roughness=0.85)
M_SOCK   = make_mat("M_Sock",   C_SOCK,   roughness=0.90)
M_SHOE_W = make_mat("M_ShoeW",  C_SHOE_W, roughness=0.60)
M_SHOE_G = make_mat("M_ShoeG",  C_SHOE_G, roughness=0.55, metallic=0.05)
M_GLASS  = make_mat("M_Glass",  C_GLASS,  roughness=0.25, metallic=0.10)
M_CLIP   = make_mat("M_Clip",   C_CLIP,   roughness=0.30, metallic=0.85)

# ── 3. Assign materials ───────────────────────────────────────────────────
print("[v17] Assigning materials...")
for obj in bpy.data.objects:
    if obj.type not in ["MESH","CURVE"]:
        continue
    on = obj.name.lower()

    if obj.type == "MESH":
        for p in obj.data.polygons: p.use_smooth = True

    # FIX: use "body_base" prefix (covers Body_Base_L_Leg, Body_Base_R_Leg etc.)
    if "body_base" in on:
        set_mat(obj, M_SKIN)
    elif any(k in on for k in ["_tip","blueviol","blueviolet"]):
        set_mat(obj, M_HAIR_T)
    elif on.startswith("hair") or on.startswith("ahoge"):
        set_mat(obj, M_HAIR)
    elif "glasses" in on:
        set_mat(obj, M_GLASS)
    elif "hairclip" in on:
        set_mat(obj, M_CLIP)
    elif "cuff" in on or "charcoal" in on:
        set_mat(obj, M_COLLAR)
    elif "hoodie" in on:
        set_mat(obj, M_HOODIE)
    elif "strap" in on:
        set_mat(obj, M_GLASS)   # pink straps
    elif "shirt" in on:
        set_mat(obj, M_SHIRT)
    elif "shorts" in on:
        set_mat(obj, M_SHORTS)
    elif "sock" in on:
        set_mat(obj, M_SOCK)
    elif "lightgray" in on or "sole" in on:
        set_mat(obj, M_SHOE_G)
    elif "shoe" in on:
        set_mat(obj, M_SHOE_W)

    mat_name = obj.material_slots[0].material.name if obj.material_slots else "NO MAT"
    print(f"  {obj.name} → {mat_name}")

# ── 4. Scale hair down (reduce puffiness) ────────────────────────────────
print("[v17] Scaling hair objects...")
# Approximate head centre Z = 1.48 (top of head), head base Z = 1.30
# Scale hair to 85% around the head center
HEAD_CENTER = Vector((0.0, 0.0, 1.40))
HAIR_SCALE  = 0.84

hair_objs = [o for o in bpy.data.objects 
             if o.type in ["MESH","CURVE"] and 
             ("hair" in o.name.lower() or "ahoge" in o.name.lower())]

for obj in hair_objs:
    # Move to origin, scale, move back
    obj.location -= HEAD_CENTER
    obj.location  = obj.location * HAIR_SCALE
    obj.location += HEAD_CENTER
    obj.scale    *= HAIR_SCALE
    print(f"  Scaled: {obj.name}")

# ── 5. Setup render ───────────────────────────────────────────────────────
print("[v17] Setting up renderer...")
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.render.resolution_x = 512
scene.render.resolution_y = 512

cam  = bpy.data.objects.get("Camera")
cam_d = cam.data if cam else bpy.data.cameras.new("Camera")
if not cam:
    cam  = bpy.data.objects.new("Camera",cam_d)
    bpy.context.scene.collection.objects.link(cam)
scene.camera  = cam
cam_d.type = "ORTHO"

# Remove old lights, add fresh 3-point rig
for obj in list(bpy.data.objects):
    if obj.type == "LIGHT":
        bpy.data.objects.remove(obj, do_unlink=True)

def sun(name, energy, rx, rz, col=(1,1,1)):
    ld = bpy.data.lights.new(name,"SUN")
    ld.energy = energy; ld.color = col
    lo = bpy.data.objects.new(name,ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(rx),0,math.radians(rz))

sun("Key",  6.0,  45,  15, (1.00, 0.97, 0.93))   # bright warm front
sun("Fill", 2.5,  20, -55, (0.80, 0.90, 1.00))   # cool side
sun("Top",  1.8,  75,   0, (1.00, 1.00, 1.00))   # top light to lift

# World
w = scene.world or bpy.data.worlds.new("World")
scene.world = w; w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value    = (0.08,0.08,0.10,1.0)
    bg.inputs["Strength"].default_value = 0.4

# ── 6. Render 6 views ─────────────────────────────────────────────────────
print("[v17] Rendering...")
C    = Vector((0.0, 0.0, 0.82))
HEAD = Vector((0.0, 0.0, 1.40))

def rview(name, loc, scale, look=None):
    look = look or C
    cam.location = loc
    cam.rotation_euler = (look - loc).to_track_quat('-Z','Y').to_euler()
    cam_d.ortho_scale = scale
    scene.render.filepath = os.path.join(PREV, name+".png")
    bpy.ops.render.render(write_still=True)
    print(f"  ✓ {name}")

rview("front", Vector(( 0.0,-3.0, 0.82)), 1.65)
rview("left",  Vector(( 3.0, 0.0, 0.82)), 1.65)
rview("right", Vector((-3.0, 0.0, 0.82)), 1.65)
rview("back",  Vector(( 0.0, 3.0, 0.82)), 1.65)
rview("face",  Vector(( 0.0,-0.6, 1.40)), 0.48, HEAD)
rview("top",   Vector(( 0.0,-0.1, 5.0)), 1.15, HEAD)

# ── 7. Export VRM ─────────────────────────────────────────────────────────
print("[v17] Exporting VRM...")
try:
    bpy.ops.export_scene.vrm(filepath=VRM)
    print(f"[v17] VRM: {VRM}")
except Exception as e:
    print(f"[v17] VRM warning: {e}")

print("[v17] Done!")
