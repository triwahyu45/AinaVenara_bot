from pathlib import Path
"""
build_v19.py — Aina Venara v19
==============================
Critical fix from v18:
  - Dark_Limbal is at Y=-0.121, Teal_Iris at Y=-0.118 → limbal COVERS iris
  - Fix: move iris Y-location -0.006 (forward), making it visible in front of limbal
  - Also: push highlight forward too to keep stacking order correct
  - Hair re-scaled 84% (same as v18)
  - Body subdiv 2 (same)
  - All materials same but iris more saturated teal
"""

import bpy, os, sys, math
from mathutils import Vector

ROOT  = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
BLEND = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
VRM   = os.path.join(ROOT, "output", "Aina_Venara_v19.vrm")
PREV  = os.path.join(ROOT, "output", "previews", "v19")
os.makedirs(PREV, exist_ok=True)

def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_SKIN   = srgb("#FFE0B2")
C_HAIR   = srgb("#7ED8F2")
C_HAIR_T = srgb("#7E8CCF")
C_EYE    = srgb("#2EC4B6")   # more saturated teal
C_EYEHI  = (1.0, 1.0, 1.0, 1.0)
C_EYELIM = srgb("#1A1A2E")
C_BROW   = srgb("#5B3A29")
C_HOODIE = srgb("#6DCFE8")
C_COLLAR = srgb("#3B3F45")
C_SHIRT  = srgb("#E6E9EE")
C_SHORTS = srgb("#3B3F45")
C_SOCK   = srgb("#F0F2F5")
C_SHOE_W = srgb("#F5F5F4")
C_SHOE_G = srgb("#BCBCBB")
C_GLASS  = srgb("#F5A4C8")
C_CLIP   = srgb("#C8C8C8")

def make_mat(name, rgba, roughness=0.75, metallic=0.0,
             emit=None, emit_s=0.0, sss=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value  = rgba
        b.inputs["Roughness"].default_value   = roughness
        b.inputs["Metallic"].default_value    = metallic
        if emit and emit_s > 0:
            b.inputs["Emission Color"].default_value    = emit
            b.inputs["Emission Strength"].default_value = emit_s
        if sss > 0:
            b.inputs["Subsurface Weight"].default_value = sss
            b.inputs["Subsurface Radius"].default_value = (0.1, 0.05, 0.03)
            b.inputs["Subsurface Scale"].default_value  = 0.05
    return mat

def set_mat(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

# ── 1. Load ───────────────────────────────────────────────────────────────
print("[v19] Loading...")
bpy.ops.wm.open_mainfile(filepath=BLEND)
for obj in list(bpy.data.objects):
    if "tripo" in obj.name.lower() or "reference" in obj.name.lower():
        bpy.data.objects.remove(obj, do_unlink=True)

# ── 2. Materials ──────────────────────────────────────────────────────────
print("[v19] Materials...")
M_SKIN   = make_mat("M_Skin",   C_SKIN,   0.65, sss=0.15)
M_HAIR   = make_mat("M_Hair",   C_HAIR,   0.28)
M_HAIR_T = make_mat("M_HairT",  C_HAIR_T, 0.28)
M_EYE    = make_mat("M_Eye",    C_EYE,    0.05, emit=C_EYE, emit_s=3.0)
M_EYEHI  = make_mat("M_EyeHi", C_EYEHI,  0.02, emit=C_EYEHI, emit_s=4.0)
M_EYELIM = make_mat("M_EyeLim", C_EYELIM, 0.50)
M_BROW   = make_mat("M_Brow",   C_BROW,   0.60)
M_HOODIE = make_mat("M_Hoodie", C_HOODIE, 0.75)
M_COLLAR = make_mat("M_Collar", C_COLLAR, 0.80)
M_SHIRT  = make_mat("M_Shirt",  C_SHIRT,  0.80)
M_SHORTS = make_mat("M_Shorts", C_SHORTS, 0.85)
M_SOCK   = make_mat("M_Sock",   C_SOCK,   0.90)
M_SHOE_W = make_mat("M_ShoeW",  C_SHOE_W, 0.60)
M_SHOE_G = make_mat("M_ShoeG",  C_SHOE_G, 0.55, metallic=0.05)
M_GLASS  = make_mat("M_Glass",  C_GLASS,  0.25, metallic=0.10)
M_CLIP   = make_mat("M_Clip",   C_CLIP,   0.30, metallic=0.85)

# ── 3. Assign materials ───────────────────────────────────────────────────
print("[v19] Assigning...")
for obj in bpy.data.objects:
    if obj.type not in ["MESH","CURVE"]: continue
    on = obj.name.lower()
    if obj.type == "MESH":
        for p in obj.data.polygons: p.use_smooth = True
    if "body_base" in on:         set_mat(obj, M_SKIN)
    elif "teal_iris" in on:       set_mat(obj, M_EYE)
    elif "highlight" in on:       set_mat(obj, M_EYEHI)
    elif "dark_limbal" in on:     set_mat(obj, M_EYELIM)
    elif "brow" in on:            set_mat(obj, M_BROW)
    elif "mouth" in on or "smile" in on: set_mat(obj, M_BROW)
    elif any(k in on for k in ["_tip","blueviol","violet"]):
        set_mat(obj, M_HAIR_T)
    elif "hair" in on or "ahoge" in on: set_mat(obj, M_HAIR)
    elif "glasses" in on:         set_mat(obj, M_GLASS)
    elif "hairclip" in on:        set_mat(obj, M_CLIP)
    elif "cuff" in on or "charcoal" in on: set_mat(obj, M_COLLAR)
    elif "hoodie" in on:          set_mat(obj, M_HOODIE)
    elif "strap" in on:           set_mat(obj, M_GLASS)
    elif "shirt" in on:           set_mat(obj, M_SHIRT)
    elif "shorts" in on:          set_mat(obj, M_SHORTS)
    elif "sock" in on:            set_mat(obj, M_SOCK)
    elif "lightgray" in on or "sole" in on: set_mat(obj, M_SHOE_G)
    elif "shoe" in on:            set_mat(obj, M_SHOE_W)

# ── 4. FIX: move iris in front of dark limbal ring ────────────────────────
print("[v19] Fixing iris Z-order (moving iris forward -0.006 Y)...")
for name in ["Face_Eyes_L_Teal_Iris","Face_Eyes_R_Teal_Iris"]:
    o = bpy.data.objects.get(name)
    if o:
        o.location.y -= 0.006   # push iris toward camera (more negative Y)
        print(f"  Moved {name} to Y={o.location.y:.4f}")

# Highlight is already in front, push a tiny bit more
for name in ["Face_Eyes_L_Highlight","Face_Eyes_R_Highlight"]:
    o = bpy.data.objects.get(name)
    if o:
        o.location.y -= 0.003
        print(f"  Moved {name} to Y={o.location.y:.4f}")

# ── 5. Bevel on curves ────────────────────────────────────────────────────
print("[v19] Bevel on curves...")
for obj in bpy.data.objects:
    if obj.type != "CURVE": continue
    on = obj.name.lower()
    if "brow" in on:         obj.data.bevel_depth = 0.0020
    elif "mouth" in on or "smile" in on: obj.data.bevel_depth = 0.0025
    elif "zipper" in on:     obj.data.bevel_depth = 0.0030
    elif "strap" in on:      obj.data.bevel_depth = 0.0030
    elif "pocket" in on:     obj.data.bevel_depth = 0.0025
    else:                    obj.data.bevel_depth = 0.004

# ── 6. Subdiv on body ────────────────────────────────────────────────────
print("[v19] Subdiv on body parts...")
kws = ["body_base_leg","body_base_arm","body_base_hand",
       "body_base_torso","body_base_neck","body_base_head"]
for obj in bpy.data.objects:
    if obj.type != "MESH": continue
    on = obj.name.lower()
    if any(k in on for k in kws):
        if not any(m.type=="SUBSURF" for m in obj.modifiers):
            s = obj.modifiers.new("Subdiv","SUBSURF")
            s.levels = 2; s.render_levels = 2

# ── 7. Scale hair 84% ────────────────────────────────────────────────────
print("[v19] Scaling hair...")
H = Vector((0.0, 0.0, 1.40))
SH = 0.84
for obj in bpy.data.objects:
    if obj.type not in ["MESH","CURVE"]: continue
    on = obj.name.lower()
    if "hair" in on or "ahoge" in on:
        obj.location -= H
        obj.location  = obj.location * SH
        obj.location += H
        obj.scale    *= SH

# ── 8. Renderer ───────────────────────────────────────────────────────────
print("[v19] Renderer setup...")
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 128
sc.render.resolution_x = 512; sc.render.resolution_y = 512

cam = bpy.data.objects.get("Camera")
cd  = cam.data if cam else bpy.data.cameras.new("Camera")
if not cam:
    cam = bpy.data.objects.new("Camera",cd)
    bpy.context.scene.collection.objects.link(cam)
sc.camera = cam; cd.type = "ORTHO"

for obj in list(bpy.data.objects):
    if obj.type == "LIGHT": bpy.data.objects.remove(obj, do_unlink=True)

def sun(name, e, rx, rz, col=(1,1,1)):
    ld = bpy.data.lights.new(name,"SUN"); ld.energy=e; ld.color=col
    lo = bpy.data.objects.new(name,ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(rx),0,math.radians(rz))

sun("Key",  6.5, 45,  10, (1.00,0.97,0.93))
sun("Fill", 2.5, 20, -55, (0.80,0.90,1.00))
sun("Top",  2.0, 75,   0, (1.00,1.00,1.00))

w = sc.world or bpy.data.worlds.new("World")
sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value    = (0.08,0.08,0.10,1.0)
    bg.inputs["Strength"].default_value = 0.4

# ── 9. Render 6-view ─────────────────────────────────────────────────────
print("[v19] Rendering...")
C = Vector((0.0,0.0,0.82)); HD = Vector((0.0,0.0,1.40))

def rv(name,loc,sc_,look=None):
    look = look or C
    cam.location = loc
    cam.rotation_euler = (look-loc).to_track_quat('-Z','Y').to_euler()
    cd.ortho_scale = sc_
    sc.render.filepath = os.path.join(PREV, name+".png")
    bpy.ops.render.render(write_still=True)
    print(f"  ✓ {name}")

rv("front", Vector(( 0,-3.0, 0.82)), 1.65)
rv("left",  Vector(( 3, 0.0, 0.82)), 1.65)
rv("right", Vector((-3, 0.0, 0.82)), 1.65)
rv("back",  Vector(( 0, 3.0, 0.82)), 1.65)
rv("face",  Vector(( 0,-0.6, 1.40)), 0.48, HD)
rv("top",   Vector(( 0,-0.1, 5.0 )), 1.15, HD)

# ── 10. Export VRM ────────────────────────────────────────────────────────
print("[v19] Exporting VRM...")
try:
    bpy.ops.export_scene.vrm(filepath=VRM)
    print(f"[v19] VRM: {VRM}")
except Exception as e:
    print(f"[v19] VRM warning: {e}")
print("[v19] Done!")
