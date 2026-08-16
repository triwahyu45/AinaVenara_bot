from pathlib import Path
"""
build_v16.py — Aina Venara v16
==============================
Starting from Master Blend, fix:
  1. Skin tone on all body parts (legs, arms, hands, neck, torso, head)
  2. Proper hair colors (cyan base, blue-violet tips)
  3. Better lighting — warm key, soft fill, subtle rim
  4. Better camera framing (face closeup pulled back slightly)
  5. Export VRM + 6-view renders
"""

import bpy, os, sys, math
from mathutils import Vector

ROOT  = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
BLEND = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
VRM   = os.path.join(ROOT, "output", "Aina_Venara_v16.vrm")
PREV  = os.path.join(ROOT, "output", "previews", "v16")
os.makedirs(PREV, exist_ok=True)

# ── colors ────────────────────────────────────────────────────────────────
def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_SKIN   = srgb("#FFE0B2")   # warm peach skin
C_HAIR   = srgb("#7ED8F2")   # cyan main hair
C_HAIR_T = srgb("#7E8CCF")   # blue-violet tips
C_EYE    = srgb("#4FC1B3")   # teal iris
C_HOODIE = srgb("#6DCFE8")   # cyan hoodie
C_COLLAR = srgb("#3B3F45")   # charcoal collar
C_SHIRT  = srgb("#E6E9EE")   # off-white shirt
C_SHORTS = srgb("#3B3F45")   # charcoal shorts
C_SOCK   = srgb("#F0F2F5")   # white socks
C_SHOE_W = srgb("#F5F5F4")   # white shoe
C_SHOE_G = srgb("#BCBCBB")   # gray sole
C_GLASS  = srgb("#F5A4C8")   # pink glasses
C_CLIP   = srgb("#C8C8C8")   # silver hairclip

# ── helpers ───────────────────────────────────────────────────────────────
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
print("[v16] Loading Master Blend...")
bpy.ops.wm.open_mainfile(filepath=BLEND)

# Remove Tripo blockout
for obj in list(bpy.data.objects):
    if "tripo" in obj.name.lower() or "reference" in obj.name.lower():
        bpy.data.objects.remove(obj, do_unlink=True)

# ── 2. Pre-make all materials ─────────────────────────────────────────────
print("[v16] Building material library...")
M_SKIN   = make_mat("M_Skin",   C_SKIN,   roughness=0.65)
M_HAIR   = make_mat("M_Hair",   C_HAIR,   roughness=0.35)
M_HAIR_T = make_mat("M_HairT",  C_HAIR_T, roughness=0.35)
M_HOODIE = make_mat("M_Hoodie", C_HOODIE, roughness=0.75)
M_COLLAR = make_mat("M_Collar", C_COLLAR, roughness=0.80)
M_SHIRT  = make_mat("M_Shirt",  C_SHIRT,  roughness=0.80)
M_SHORTS = make_mat("M_Shorts", C_SHORTS, roughness=0.85)
M_SOCK   = make_mat("M_Sock",   C_SOCK,   roughness=0.90)
M_SHOE_W = make_mat("M_ShoeW",  C_SHOE_W, roughness=0.60)
M_SHOE_G = make_mat("M_ShoeG",  C_SHOE_G, roughness=0.55, metallic=0.05)
M_GLASS  = make_mat("M_Glass",  C_GLASS,  roughness=0.25, metallic=0.10)
M_CLIP   = make_mat("M_Clip",   C_CLIP,   roughness=0.30, metallic=0.85)

# ── 3. Assign materials to every object by name ───────────────────────────
print("[v16] Assigning materials...")
for obj in bpy.data.objects:
    if obj.type not in ["MESH","CURVE"]:
        continue
    on = obj.name.lower()
    
    # Smooth shading for meshes
    if obj.type == "MESH":
        for p in obj.data.polygons:
            p.use_smooth = True

    # Match by prefix / keyword
    if any(k in on for k in ["body_base_leg","body_base_hand",
                              "body_base_arm","body_base_torso",
                              "body_base_neck","body_base_head"]):
        set_mat(obj, M_SKIN)
    elif any(k in on for k in ["hair_base_back_bluev","hair_base_l_side_tip",
                                "hair_base_r_side_tip","blueviol","_tip"]):
        set_mat(obj, M_HAIR_T)
    elif "hair" in on or "ahoge" in on:
        set_mat(obj, M_HAIR)
    elif "glasses_pink_bridge" in on or "glasses_pink_l" in on or "glasses_pink_r" in on:
        set_mat(obj, M_GLASS)
    elif "hairclip" in on:
        set_mat(obj, M_CLIP)
    elif "hoodie_charcoal" in on or "cuff" in on:
        set_mat(obj, M_COLLAR)
    elif "hoodie" in on:
        set_mat(obj, M_HOODIE)
    elif "shirt_pink" in on or "strap" in on:
        set_mat(obj, M_GLASS)  # pink strap
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

    print(f"  {obj.name}: {obj.material_slots[0].material.name if obj.material_slots else 'NO MAT'}")

# ── 4. Setup render ───────────────────────────────────────────────────────
print("[v16] Setting up render...")
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.render.resolution_x = 512
scene.render.resolution_y = 512

cam_d = bpy.data.cameras.get("Camera")
cam   = bpy.data.objects.get("Camera")
if not cam:
    cam_d = bpy.data.cameras.new("Camera")
    cam   = bpy.data.objects.new("Camera", cam_d)
    bpy.context.scene.collection.objects.link(cam)
else:
    cam_d = cam.data
scene.camera  = cam
cam_d.type = "ORTHO"

# Remove ALL old lights and add fresh studio rig
for obj in list(bpy.data.objects):
    if obj.type == "LIGHT":
        bpy.data.objects.remove(obj, do_unlink=True)

def sun(name, energy, rx, rz, col=(1,1,1)):
    ld = bpy.data.lights.new(name,"SUN")
    ld.energy = energy; ld.color = col
    lo = bpy.data.objects.new(name,ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(rx),0,math.radians(rz))

sun("Key",  5.5,  50,  20, (1.00, 0.97, 0.93))   # warm front
sun("Fill", 2.0,  25, -60, (0.75, 0.88, 1.00))   # cool side fill
sun("Rim",  1.5,  30, 160, (0.85, 0.70, 1.00))   # subtle lavender rim

# Better world
w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = w
w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value   = (0.07, 0.07, 0.09, 1.0)
    bg.inputs["Strength"].default_value = 0.3

# ── 5. Render 6 views ─────────────────────────────────────────────────────
print("[v16] Rendering...")
C   = Vector((0.0, 0.0, 0.82))
HEAD = Vector((0.0, 0.0, 1.42))

def rview(name, loc, scale, look=None):
    look = look or C
    cam.location = loc
    d = look - loc
    cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
    cam_d.ortho_scale = scale
    scene.render.filepath = os.path.join(PREV, name+".png")
    bpy.ops.render.render(write_still=True)
    print(f"  ✓ {name}")

rview("front", Vector(( 0.0,-3.0, 0.82)), 1.65)
rview("left",  Vector(( 3.0, 0.0, 0.82)), 1.65)
rview("right", Vector((-3.0, 0.0, 0.82)), 1.65)
rview("back",  Vector(( 0.0, 3.0, 0.82)), 1.65)
rview("face",  Vector(( 0.0,-0.65, 1.42)), 0.46, HEAD)
rview("top",   Vector(( 0.0,-0.1,  5.0 )), 1.15, HEAD)

# ── 6. Export VRM ─────────────────────────────────────────────────────────
print("[v16] Exporting VRM...")
try:
    bpy.ops.export_scene.vrm(filepath=VRM)
    print(f"[v16] VRM: {VRM}")
except Exception as e:
    print(f"[v16] VRM warning: {e}")

print("[v16] Done!")
