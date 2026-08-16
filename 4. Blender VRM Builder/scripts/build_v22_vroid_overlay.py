from pathlib import Path
"""
build_v22_vroid_overlay.py — Aina Venara v22
=============================================
Fixes from v21:
  1. Hair: Don't disconnect texture. Instead add new Principled BSDF with cyan
     connected directly to Material Output (Cycles only, MToon untouched for export)
  2. Eyes: Same approach - force teal Principled BSDF to Material Output
  3. Glasses: Move up +0.08m Z to align with VRoid eye position
  4. Arms: Apply a slight downward rotation on UpperArm bones for render pose
  5. Camera: center at 0.9 (body center excluding arms spread)
"""

import bpy, os, math
from mathutils import Vector, Euler

ROOT   = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
VROID  = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/VRM Draft/Aina_Venara_Base.vrm")
MASTER = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
VRM    = os.path.join(ROOT, "output", "Aina_Venara_v22.vrm")
PREV   = os.path.join(ROOT, "output", "previews", "v22")
os.makedirs(PREV, exist_ok=True)

def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_HAIR  = srgb("#7ED8F2")
C_HAIRT = srgb("#7E8CCF")
C_EYE   = srgb("#2EC4B6")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Import VRoid base
# ─────────────────────────────────────────────────────────────────────────────
print("[v22] Importing VRoid base...")
bpy.ops.import_scene.vrm(filepath=VROID)

rig = next((o for o in bpy.data.objects if o.type=='ARMATURE'), None)
bpy.context.view_layer.update()

# Get key bone Z heights
def bone_z(name):
    b = rig.pose.bones.get(name)
    return (rig.matrix_world @ b.matrix).translation.z if b else 1.0

head_z  = bone_z("J_Bip_C_Head")   # ~1.386
chest_z = bone_z("J_Bip_C_Chest")  # ~1.073
eye_z   = head_z - 0.04            # eyes are slightly below head bone
print(f"[v22] head_z={head_z:.3f} eye_z={eye_z:.3f}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Recolor materials: Force Principled BSDF → Material Output (Cycles only)
#    MToon nodes left intact → VRM export still works
# ─────────────────────────────────────────────────────────────────────────────
print("[v22] Overriding material colors for Cycles rendering...")

def force_cycles_color(mat_name_partial, base_color, roughness=0.35,
                       emit=None, emit_s=0.0):
    for mat in bpy.data.materials:
        if mat_name_partial.lower() not in mat.name.lower(): continue
        if not mat.use_nodes: continue
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        # Find Material Output node
        out = next((n for n in nodes if n.type=="OUTPUT_MATERIAL"), None)
        if not out: continue
        # Create new Principled BSDF
        new_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        new_bsdf.location = (out.location.x - 300, out.location.y)
        new_bsdf.inputs["Base Color"].default_value  = base_color
        new_bsdf.inputs["Roughness"].default_value   = roughness
        if emit and emit_s > 0:
            new_bsdf.inputs["Emission Color"].default_value    = emit
            new_bsdf.inputs["Emission Strength"].default_value = emit_s
        # Connect to Material Output Surface
        links.new(new_bsdf.outputs["BSDF"], out.inputs["Surface"])
        print(f"  Overridden: {mat.name}")

# Hair → cyan (all hair material slots)
force_cycles_color("HairBack_00_HAIR",  C_HAIR, roughness=0.28)
force_cycles_color("HairFront",         C_HAIR, roughness=0.28)

# Eye iris → teal emissive
force_cycles_color("EyeIris_00_EYE", C_EYE, roughness=0.05,
                   emit=C_EYE, emit_s=2.0)
# Eye highlight → bright white emissive
force_cycles_color("EyeHighlight_00_EYE",
                   (1,1,1,1), roughness=0.02, emit=(1,1,1,1), emit_s=3.0)

# Hide default VRoid clothes (transparent BSDF)
HIDE = ["Bottoms_01_CLOTH","Shoes_01_CLOTH","Tops_01_CLOTH"]
for name in HIDE:
    for mat in bpy.data.materials:
        if name.lower() not in mat.name.lower(): continue
        if not mat.use_nodes: continue
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        out = next((n for n in nodes if n.type=="OUTPUT_MATERIAL"), None)
        if not out: continue
        transp = nodes.new("ShaderNodeBsdfTransparent")
        links.new(transp.outputs["BSDF"], out.inputs["Surface"])
        print(f"  Transparent: {mat.name}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Arm pose — rotate upper arms down for render (looks natural, not T-pose)
# ─────────────────────────────────────────────────────────────────────────────
print("[v22] Setting arm pose (relaxed)...")
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")

# Rotate L UpperArm: rotate toward body (-Z axis in bone space, ~40° down)
for side, sign in [("L", 1), ("R", -1)]:
    bone = rig.pose.bones.get(f"J_Bip_{side}_UpperArm")
    if bone:
        # Clear existing rotation first
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = Euler((0, 0, sign * math.radians(-45)), "XYZ")
        print(f"  Posed: J_Bip_{side}_UpperArm")

bpy.ops.object.mode_set(mode="OBJECT")
bpy.context.view_layer.update()

# ─────────────────────────────────────────────────────────────────────────────
# 4. Append outfit from Master Blend
# ─────────────────────────────────────────────────────────────────────────────
print("[v22] Appending outfit from Master Blend...")
SKIP = ["body_base", "face_", "sphere.", "cube.", "cylinder.", "torus."]

with bpy.data.libraries.load(MASTER, link=False) as (data_from, data_to):
    wanted = [n for n in data_from.objects
              if not any(k in n.lower() for k in SKIP)
              and any(k in n.lower() for k in ["outfit","accessory","glasses",
                                                "hairclip","ahoge"])]
    data_to.objects = wanted
    print(f"  Appending {len(wanted)} objects")

outfit_objects = []
for obj in data_to.objects:
    if obj is None: continue
    bpy.context.scene.collection.objects.link(obj)
    outfit_objects.append(obj)

# ─────────────────────────────────────────────────────────────────────────────
# 5. Adjust glasses position to VRoid eye level
# ─────────────────────────────────────────────────────────────────────────────
print("[v22] Adjusting glasses position...")

# VRoid eye Z ≈ head_z - 0.04  
# Master Blend glasses were designed at head_z ≈ 1.38, eye ≈ 1.33
# VRoid eye_z = head_z - 0.04 = same! So glasses should already align.
# But the glasses seem too low — let's check and nudge up if needed
GLASSES_OFFSET_Z = 0.04   # nudge up 4cm to sit on nose bridge

for obj in outfit_objects:
    if "glasses" in obj.name.lower():
        obj.location.z += GLASSES_OFFSET_Z
        print(f"  Nudged glasses up: {obj.name} → z={obj.location.z:.3f}")

# Hairclip position — nudge up to match VRoid head
HAIRCLIP_OFFSET_Z = 0.04
for obj in outfit_objects:
    if "hairclip" in obj.name.lower():
        obj.location.z += HAIRCLIP_OFFSET_Z

# ─────────────────────────────────────────────────────────────────────────────
# 6. Apply materials + rig outfit to VRoid armature
# ─────────────────────────────────────────────────────────────────────────────
print("[v22] Applying outfit materials and rigging...")

def make_mat(name, rgba, roughness=0.75, metallic=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = rgba
        b.inputs["Roughness"].default_value  = roughness
        b.inputs["Metallic"].default_value   = metallic
    return mat

M = {
    "hoodie":    make_mat("MV_Hoodie",  srgb("#6DCFE8"), 0.72),
    "charcoal":  make_mat("MV_Collar",  srgb("#3B3F45"), 0.82),
    "cuff":      make_mat("MV_Collar",  srgb("#3B3F45"), 0.82),
    "shirt":     make_mat("MV_Shirt",   srgb("#E6E9EE"), 0.80),
    "sock":      make_mat("MV_Sock",    srgb("#F0F2F5"), 0.88),
    "shoe":      make_mat("MV_ShoeW",   srgb("#F5F5F4"), 0.58),
    "glasses":   make_mat("MV_Glass",   srgb("#F5A4C8"), 0.22, metallic=0.12),
    "hairclip":  make_mat("MV_Clip",    srgb("#C8C8C8"), 0.28, metallic=0.88),
    "ahoge":     make_mat("MV_Hair",    srgb("#7ED8F2"), 0.28),
    "strap":     make_mat("MV_Glass",   srgb("#F5A4C8"), 0.22, metallic=0.12),
    "zipper":    make_mat("MV_Collar",  srgb("#3B3F45"), 0.70, metallic=0.40),
    "panel":     make_mat("MV_Hoodie",  srgb("#6DCFE8"), 0.72),
    "sleeve":    make_mat("MV_Hoodie",  srgb("#6DCFE8"), 0.72),
    "pocket":    make_mat("MV_Hoodie",  srgb("#6DCFE8"), 0.72),
}

for obj in outfit_objects:
    if obj.type not in ["MESH","CURVE"]: continue
    on = obj.name.lower()
    if obj.type == "MESH":
        for p in obj.data.polygons: p.use_smooth = True
    for key, mat in M.items():
        if key in on:
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            break
    if obj.type == "CURVE":
        obj.data.bevel_depth = 0.003
    # Rig to VRoid armature
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE": obj.modifiers.remove(mod)
    arm_mod = obj.modifiers.new("VRoid_Arm","ARMATURE")
    arm_mod.object = rig
    obj.parent = rig
    obj.parent_type = "OBJECT"

# ─────────────────────────────────────────────────────────────────────────────
# 7. Renderer setup
# ─────────────────────────────────────────────────────────────────────────────
print("[v22] Setting up renderer...")
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
print("[v22] Rendering...")
C  = Vector((0.0,0.0,0.90)); HD = Vector((0.0,0.0,head_z))

def rv(name,loc,sc_,look=None):
    look = look or C
    cam.location = loc
    cam.rotation_euler = (look-loc).to_track_quat('-Z','Y').to_euler()
    cd.ortho_scale = sc_
    sc.render.filepath = os.path.join(PREV,name+".png")
    bpy.ops.render.render(write_still=True)
    print(f"  ✓ {name}")

rv("front", Vector(( 0,-3.0, 0.90)), 1.30)
rv("left",  Vector(( 3, 0.0, 0.90)), 1.30)
rv("right", Vector((-3, 0.0, 0.90)), 1.30)
rv("back",  Vector(( 0, 3.0, 0.90)), 1.30)
rv("face",  Vector(( 0,-0.6, head_z)), 0.45, HD)
rv("top",   Vector(( 0,-0.1, 5.0)),  0.95, HD)

# ─────────────────────────────────────────────────────────────────────────────
# 9. Export VRM
# ─────────────────────────────────────────────────────────────────────────────
print("[v22] Exporting VRM...")
try:
    bpy.ops.export_scene.vrm(filepath=VRM)
    print(f"[v22] VRM: {VRM}")
except Exception as e:
    print(f"[v22] VRM warning: {e}")
print("[v22] Done!")
