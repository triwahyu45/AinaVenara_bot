from pathlib import Path
"""
build_v21_vroid_overlay.py — Aina Venara v21
=============================================
APPROACH:
  1. Import VRoid base (Aina_Venara_Base.vrm) → keeps proper anime face, MToon, springs
  2. Recolor VRoid MToon hair → cyan #7ED8F2
  3. Recolor VRoid MToon eye → teal #2EC4B6
  4. Make default VRoid clothes (Bottoms/Tops/Shoes) transparent/hidden
  5. Append custom outfit + accessories from Master Blend
     (skip Body_Base_* since VRoid already has skin mesh)
  6. Add Armature modifier to outfit pieces → VRoid armature
  7. Render 6-view + export VRM
"""

import bpy, os, math
from mathutils import Vector

ROOT   = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
VROID  = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/VRM Draft/Aina_Venara_Base.vrm")
MASTER = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
VRM    = os.path.join(ROOT, "output", "Aina_Venara_v21.vrm")
PREV   = os.path.join(ROOT, "output", "previews", "v21")
os.makedirs(PREV, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Import VRoid base
# ─────────────────────────────────────────────────────────────────────────────
print("[v21] Importing VRoid base...")
bpy.ops.import_scene.vrm(filepath=VROID)

rig = next((o for o in bpy.data.objects if o.type=='ARMATURE'), None)
print(f"[v21] Armature: {rig.name}")

# Head bone world Z for outfit alignment reference
head_z = 1.386
chest_z = 1.073
hip_z = 0.908
b_head = rig.pose.bones.get("J_Bip_C_Head")
if b_head:
    head_z = (rig.matrix_world @ b_head.matrix).translation.z
    print(f"[v21] Head z={head_z:.3f}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Recolor VRoid MToon materials
# ─────────────────────────────────────────────────────────────────────────────
print("[v21] Recoloring VRoid MToon materials...")

def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_HAIR  = srgb("#7ED8F2")   # cyan hair
C_HAIRT = srgb("#7E8CCF")   # blue-violet tips (for dark nodes)
C_EYE   = srgb("#2EC4B6")   # teal iris

def recolor_mtoon(mat_name_partial, new_color):
    """Find material by partial name, change all RGBA color inputs."""
    for mat in bpy.data.materials:
        if mat_name_partial.lower() in mat.name.lower():
            if not mat.use_nodes: continue
            for node in mat.node_tree.nodes:
                # Change BSDF base color
                if node.type == "BSDF_PRINCIPLED":
                    node.inputs["Base Color"].default_value = new_color
                # Change any node that has "Lit Color" or "Shade Color" input
                for inp in node.inputs:
                    low = inp.name.lower()
                    if inp.type == "RGBA" and any(k in low for k in ["lit","shade","color","base"]):
                        inp.default_value = new_color
            print(f"  Recolored: {mat.name}")

recolor_mtoon("HairBack_00_HAIR", C_HAIR)
recolor_mtoon("EyeIris_00_EYE",  C_EYE)

# Disconnect texture from hair to force solid color
for mat in bpy.data.materials:
    if "HairBack" in mat.name and mat.use_nodes:
        to_remove = []
        for link in mat.node_tree.links:
            if link.from_node.type == "TEX_IMAGE":
                to_remove.append(link)
        for link in to_remove:
            mat.node_tree.links.remove(link)
        print(f"  Disconnected texture from: {mat.name}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Hide/transparent default VRoid clothes
# ─────────────────────────────────────────────────────────────────────────────
print("[v21] Hiding default VRoid clothes...")

HIDE_MATS = ["Bottoms_01_CLOTH", "Shoes_01_CLOTH", "Tops_01_CLOTH"]

def hide_material(mat_name_partial):
    for mat in bpy.data.materials:
        if mat_name_partial.lower() in mat.name.lower():
            mat.blend_method = "BLEND"
            if mat.use_nodes:
                # Set alpha to 0 on principled BSDF
                for node in mat.node_tree.nodes:
                    if node.type == "BSDF_PRINCIPLED":
                        node.inputs["Alpha"].default_value = 0.0
                    # Also set any Alpha input
                    for inp in node.inputs:
                        if inp.name == "Alpha" and inp.type == "VALUE":
                            inp.default_value = 0.0
            print(f"  Hidden: {mat.name}")

for name in HIDE_MATS:
    hide_material(name)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Append outfit + accessories from Master Blend
# ─────────────────────────────────────────────────────────────────────────────
print("[v21] Appending outfit from Master Blend...")

# Which objects to skip (VRoid provides body/face/hair)
SKIP_KEYWORDS = ["body_base", "face_", "sphere.", "cube.", "cylinder.", "torus."]

with bpy.data.libraries.load(MASTER, link=False) as (data_from, data_to):
    wanted = []
    for name in data_from.objects:
        low = name.lower()
        # Skip: body skin, generic primitives, and face (VRoid has these)
        if any(k in low for k in SKIP_KEYWORDS):
            continue
        # Keep: outfit, hair accessories, glasses, hairclip
        if any(k in low for k in ["outfit", "accessory", "glasses", "hairclip",
                                   "ahoge", "hair_ahoge"]):
            wanted.append(name)
    data_to.objects = wanted
    print(f"  Will append: {wanted}")

# Link appended objects into scene
outfit_objects = []
for obj in data_to.objects:
    if obj is None: continue
    bpy.context.scene.collection.objects.link(obj)
    outfit_objects.append(obj)
    print(f"  Appended: {obj.name}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Adjust outfit position to match VRoid proportions
# ─────────────────────────────────────────────────────────────────────────────
print("[v21] Aligning outfit to VRoid body...")

# Master Blend reference points (from inspection):
# - Head/face at z≈1.38, body center ≈ 0.9
# - VRoid: head z=1.386, hips z=0.908 → essentially same scale!
# So just minor Y-offset: Master Blend body is at Y=0, VRoid also Y=0
# No rescaling needed, only verify positions

# Add Armature modifier so outfit follows VRoid rig
for obj in outfit_objects:
    if obj.type not in ["MESH","CURVE"]: continue
    # Remove existing armature modifiers
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE":
            obj.modifiers.remove(mod)
    # Add VRoid armature
    arm_mod = obj.modifiers.new("VRoid_Arm","ARMATURE")
    arm_mod.object = rig
    # Parent to armature object
    obj.parent = rig
    obj.parent_type = "OBJECT"
    print(f"  Rigged: {obj.name}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Apply materials to outfit pieces
# ─────────────────────────────────────────────────────────────────────────────
print("[v21] Applying outfit materials...")

def make_mat(name, rgba, roughness=0.75, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = rgba
        b.inputs["Roughness"].default_value  = roughness
        b.inputs["Metallic"].default_value   = metallic
    return mat

C_HOODIE = srgb("#6DCFE8")
C_COLLAR = srgb("#3B3F45")
C_SHIRT  = srgb("#E6E9EE")
C_SHORTS = srgb("#3B3F45")
C_SOCK   = srgb("#F0F2F5")
C_SHOE_W = srgb("#F5F5F4")
C_SHOE_G = srgb("#BCBCBB")
C_GLASS  = srgb("#F5A4C8")
C_CLIP   = srgb("#C8C8C8")
C_HAIR_A = srgb("#7ED8F2")

M = {
    "hoodie": make_mat("MV_Hoodie", C_HOODIE, 0.72),
    "charcoal": make_mat("MV_Collar", C_COLLAR, 0.82),
    "cuff":     make_mat("MV_Collar", C_COLLAR, 0.82),
    "shirt":    make_mat("MV_Shirt",  C_SHIRT,  0.80),
    "sock":     make_mat("MV_Sock",   C_SOCK,   0.88),
    "shoe":     make_mat("MV_ShoeW",  C_SHOE_W, 0.58),
    "glasses":  make_mat("MV_Glass",  C_GLASS,  0.22, metallic=0.12),
    "hairclip": make_mat("MV_Clip",   C_CLIP,   0.28, metallic=0.88),
    "ahoge":    make_mat("MV_Hair",   C_HAIR_A, 0.28),
    "strap":    make_mat("MV_Glass",  C_GLASS,  0.22, metallic=0.12),
}

for obj in outfit_objects:
    if obj.type not in ["MESH","CURVE"]: continue
    on = obj.name.lower()
    # Smooth shade
    if obj.type == "MESH":
        for p in obj.data.polygons: p.use_smooth = True
    # Assign material
    for key, mat in M.items():
        if key in on:
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            break
    # Bevel curves
    if obj.type == "CURVE":
        obj.data.bevel_depth = 0.003

# ─────────────────────────────────────────────────────────────────────────────
# 7. Setup render
# ─────────────────────────────────────────────────────────────────────────────
print("[v21] Setting up renderer...")
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 128
sc.render.resolution_x = 512
sc.render.resolution_y = 512

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

sun("Key",  6.5, 45, 10,  (1.00,0.98,0.95))
sun("Fill", 2.5, 20, -50, (0.80,0.90,1.00))
sun("Top",  2.0, 75,  0,  (1.00,1.00,1.00))

w = sc.world or bpy.data.worlds.new("World")
sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value    = (0.08,0.08,0.10,1.0)
    bg.inputs["Strength"].default_value = 0.4

# ─────────────────────────────────────────────────────────────────────────────
# 8. Render 6-view
# ─────────────────────────────────────────────────────────────────────────────
print("[v21] Rendering...")
C  = Vector((0.0,0.0,0.82)); HD = Vector((0.0,0.0,head_z))

def rv(name,loc,sc_,look=None):
    look = look or C
    cam.location = loc
    cam.rotation_euler = (look-loc).to_track_quat('-Z','Y').to_euler()
    cd.ortho_scale = sc_
    sc.render.filepath = os.path.join(PREV,name+".png")
    bpy.ops.render.render(write_still=True)
    print(f"  ✓ {name}")

rv("front", Vector(( 0,-3.0, 0.82)), 1.65)
rv("left",  Vector(( 3, 0.0, 0.82)), 1.65)
rv("right", Vector((-3, 0.0, 0.82)), 1.65)
rv("back",  Vector(( 0, 3.0, 0.82)), 1.65)
rv("face",  Vector(( 0,-0.6, head_z)), 0.48, HD)
rv("top",   Vector(( 0,-0.1, 5.0)),  1.15, HD)

# ─────────────────────────────────────────────────────────────────────────────
# 9. Export VRM
# ─────────────────────────────────────────────────────────────────────────────
print("[v21] Exporting VRM...")
try:
    bpy.ops.export_scene.vrm(filepath=VRM)
    print(f"[v21] VRM: {VRM}")
except Exception as e:
    print(f"[v21] VRM warning: {e}")

print("[v21] Done!")
