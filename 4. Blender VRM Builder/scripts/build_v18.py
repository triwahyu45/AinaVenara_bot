from pathlib import Path
"""
build_v18.py — Aina Venara v18
==============================
Fixes from v17:
  1. Teal eyes get emissive glow so they're visible inside glasses frames
  2. Curve objects (brows, zippers, straps) get bevel radius so they render as solid
  3. Body_Base mesh objects get Subdivision Surface for smoother look
  4. Hair Crown Cap gets slightly smaller to expose more forehead
  5. Skin subsurface scattering for soft anime look
"""

import bpy, os, sys, math
from mathutils import Vector

ROOT  = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
BLEND = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
VRM   = os.path.join(ROOT, "output", "Aina_Venara_v18.vrm")
PREV  = os.path.join(ROOT, "output", "previews", "v18")
os.makedirs(PREV, exist_ok=True)

# ── colors ────────────────────────────────────────────────────────────────
def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_SKIN   = srgb("#FFE0B2")
C_HAIR   = srgb("#7ED8F2")
C_HAIR_T = srgb("#7E8CCF")
C_EYE    = srgb("#4FC1B3")   # teal iris
C_EYEHI  = (1.0, 1.0, 1.0, 1.0)  # eye highlight
C_EYELIM = srgb("#1A1A2E")   # dark limbal ring
C_BROW   = srgb("#5B3A29")   # dark brown brow
C_HOODIE = srgb("#6DCFE8")
C_COLLAR = srgb("#3B3F45")
C_SHIRT  = srgb("#E6E9EE")
C_SHORTS = srgb("#3B3F45")
C_SOCK   = srgb("#F0F2F5")
C_SHOE_W = srgb("#F5F5F4")
C_SHOE_G = srgb("#BCBCBB")
C_GLASS  = srgb("#F5A4C8")
C_CLIP   = srgb("#C8C8C8")

# ── helpers ───────────────────────────────────────────────────────────────
def make_mat(name, rgba, roughness=0.75, metallic=0.0,
             emit=None, emit_strength=0.0, sss=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value   = rgba
        bsdf.inputs["Roughness"].default_value    = roughness
        bsdf.inputs["Metallic"].default_value     = metallic
        if emit and emit_strength > 0:
            bsdf.inputs["Emission Color"].default_value    = emit
            bsdf.inputs["Emission Strength"].default_value = emit_strength
        if sss > 0:
            bsdf.inputs["Subsurface Weight"].default_value  = sss
            bsdf.inputs["Subsurface Radius"].default_value  = (0.1, 0.05, 0.03)
            bsdf.inputs["Subsurface Scale"].default_value   = 0.05
    return mat

def set_mat(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

# ── 1. Load blend ─────────────────────────────────────────────────────────
print("[v18] Loading Master Blend...")
bpy.ops.wm.open_mainfile(filepath=BLEND)

for obj in list(bpy.data.objects):
    if "tripo" in obj.name.lower() or "reference" in obj.name.lower():
        bpy.data.objects.remove(obj, do_unlink=True)

# ── 2. Build material library ─────────────────────────────────────────────
print("[v18] Building materials...")
M_SKIN   = make_mat("M_Skin",   C_SKIN,   roughness=0.65, sss=0.15)
M_HAIR   = make_mat("M_Hair",   C_HAIR,   roughness=0.28)
M_HAIR_T = make_mat("M_HairT",  C_HAIR_T, roughness=0.28)
M_EYE    = make_mat("M_Eye",    C_EYE,    roughness=0.10,
                    emit=C_EYE, emit_strength=1.5)
M_EYEHI  = make_mat("M_EyeHi", C_EYEHI,  roughness=0.05,
                    emit=C_EYEHI, emit_strength=2.0)
M_EYELIM = make_mat("M_EyeLim", C_EYELIM, roughness=0.50)
M_BROW   = make_mat("M_Brow",   C_BROW,   roughness=0.60)
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
print("[v18] Assigning materials...")
for obj in bpy.data.objects:
    if obj.type not in ["MESH","CURVE"]:
        continue
    on = obj.name.lower()

    if obj.type == "MESH":
        for p in obj.data.polygons: p.use_smooth = True

    # Body parts
    if "body_base" in on:
        set_mat(obj, M_SKIN)
    # Eyes
    elif "iris" in on:
        set_mat(obj, M_EYE)
    elif "highlight" in on:
        set_mat(obj, M_EYEHI)
    elif "dark_limbal" in on or "limbal" in on:
        set_mat(obj, M_EYELIM)
    elif "brow" in on:
        set_mat(obj, M_BROW)
    elif "mouth" in on or "smile" in on:
        set_mat(obj, M_BROW)   # dark for mouth curves
    # Hair
    elif any(k in on for k in ["_tip","blueviol","blueviolet","violet"]):
        set_mat(obj, M_HAIR_T)
    elif "hair" in on or "ahoge" in on:
        set_mat(obj, M_HAIR)
    # Accessories
    elif "glasses" in on:
        set_mat(obj, M_GLASS)
    elif "hairclip" in on:
        set_mat(obj, M_CLIP)
    # Outfit
    elif "cuff" in on or "charcoal" in on:
        set_mat(obj, M_COLLAR)
    elif "hoodie" in on:
        set_mat(obj, M_HOODIE)
    elif "strap" in on:
        set_mat(obj, M_GLASS)
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

# ── 4. Enable bevel on CURVE objects so they render as solid ─────────────
print("[v18] Enabling bevel on curves...")
for obj in bpy.data.objects:
    if obj.type != "CURVE": continue
    on = obj.name.lower()
    # Set bevel based on type
    if "brow" in on or "mouth" in on or "smile" in on:
        obj.data.bevel_depth = 0.0025   # very thin - brows/mouth
    elif "zipper" in on or "strap" in on or "pocket" in on:
        obj.data.bevel_depth = 0.0030
    elif "collar" in on:
        obj.data.bevel_depth = 0.010
    else:
        obj.data.bevel_depth = 0.005

# ── 5. Add subdiv to body parts for smoother look ─────────────────────────
print("[v18] Adding Subdivision Surface to body parts...")
body_keywords = ["body_base_leg","body_base_arm","body_base_hand",
                 "body_base_torso","body_base_neck","body_base_head"]
for obj in bpy.data.objects:
    if obj.type != "MESH": continue
    on = obj.name.lower()
    if any(k in on for k in body_keywords):
        # Only add if not already has subdiv
        has_subdiv = any(m.type == "SUBSURF" for m in obj.modifiers)
        if not has_subdiv:
            sub = obj.modifiers.new("Subdiv","SUBSURF")
            sub.levels = 2
            sub.render_levels = 2

# ── 6. Scale hair down (84%) ──────────────────────────────────────────────
print("[v18] Scaling hair...")
HEAD_CENTER = Vector((0.0, 0.0, 1.40))
HAIR_SCALE  = 0.84
for obj in bpy.data.objects:
    if obj.type not in ["MESH","CURVE"]: continue
    on = obj.name.lower()
    if "hair" in on or "ahoge" in on:
        obj.location -= HEAD_CENTER
        obj.location  = obj.location * HAIR_SCALE
        obj.location += HEAD_CENTER
        obj.scale    *= HAIR_SCALE

# ── 7. Setup renderer ─────────────────────────────────────────────────────
print("[v18] Setting up renderer...")
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.render.resolution_x = 512
scene.render.resolution_y = 512

cam = bpy.data.objects.get("Camera")
cam_d = cam.data if cam else bpy.data.cameras.new("Camera")
if not cam:
    cam = bpy.data.objects.new("Camera",cam_d)
    bpy.context.scene.collection.objects.link(cam)
scene.camera = cam; cam_d.type = "ORTHO"

for obj in list(bpy.data.objects):
    if obj.type == "LIGHT":
        bpy.data.objects.remove(obj, do_unlink=True)

def sun(name, energy, rx, rz, col=(1,1,1)):
    ld = bpy.data.lights.new(name,"SUN")
    ld.energy = energy; ld.color = col
    lo = bpy.data.objects.new(name,ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(rx),0,math.radians(rz))

sun("Key",  6.5,  45,  10, (1.00, 0.97, 0.93))
sun("Fill", 2.5,  20, -55, (0.80, 0.90, 1.00))
sun("Top",  2.0,  75,   0, (1.00, 1.00, 1.00))

w = scene.world or bpy.data.worlds.new("World")
scene.world = w; w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value    = (0.08,0.08,0.10,1.0)
    bg.inputs["Strength"].default_value = 0.4

# ── 8. Render ─────────────────────────────────────────────────────────────
print("[v18] Rendering...")
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

# ── 9. Export VRM ─────────────────────────────────────────────────────────
print("[v18] Exporting VRM...")
try:
    bpy.ops.export_scene.vrm(filepath=VRM)
    print(f"[v18] VRM: {VRM}")
except Exception as e:
    print(f"[v18] VRM warning: {e}")

print("[v18] Done!")
