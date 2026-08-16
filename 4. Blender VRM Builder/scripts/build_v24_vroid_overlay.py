from pathlib import Path
"""
build_v24_vroid_overlay.py — Aina Venara v24
=============================================
Critical fixes from v23:
  1. Hair: Completely wipe all nodes and replace with plain Principled BSDF (cyan)
     Previous partial fix didn't change rendering because MToon nodes intercepted
  2. Glasses Z position: Wrong calculation! eye_z = head_z - 0.045 = 1.341
     but glasses original z = 1.335, so z_shift was only 0.006m (6mm!)
     ACTUAL target: head_z - 0.005 = 1.381 → z_shift = 1.381 - 1.335 = 0.046m
  3. Camera center raised to z=1.05 so body renders fully in frame
  4. Include Outfit_Shorts_* objects (socks/shoes from Master Blend)
"""

import bpy, os, math
from mathutils import Vector, Euler

ROOT   = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
VROID  = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/VRM Draft/Aina_Venara_Base.vrm")
MASTER = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
VRM    = os.path.join(ROOT, "output", "Aina_Venara_v24.vrm")
PREV   = os.path.join(ROOT, "output", "previews", "v24")
os.makedirs(PREV, exist_ok=True)

def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_HAIR = srgb("#7ED8F2")  # cyan
C_EYE  = srgb("#2EC4B6")  # teal

# ── 1. Import VRoid ───────────────────────────────────────────────────────
print("[v24] Importing VRoid base...")
bpy.ops.import_scene.vrm(filepath=VROID)

rig = next((o for o in bpy.data.objects if o.type=='ARMATURE'), None)
bpy.context.view_layer.update()

def bone_z(name):
    b = rig.pose.bones.get(name)
    return (rig.matrix_world @ b.matrix).translation.z if b else 1.0

head_z = bone_z("J_Bip_C_Head")  # ~1.386
# In VRoid, the eye iris is very close to the head bone (within 1cm)
TARGET_GLASS_Z = head_z - 0.005   # ≈1.381 — put glasses AT eye level
TARGET_GLASS_Y = -0.14            # nose bridge Y  
print(f"[v24] head_z={head_z:.3f}  target_glass_z={TARGET_GLASS_Z:.3f}")

# ── 2. Completely replace hair/eye/outline material nodes ─────────────────
print("[v24] Replacing material nodes completely...")

def wipe_and_replace(mat_name_partial, rgba, roughness=0.35,
                     emit=None, emit_s=0.0, transparent=False):
    """Wipe all nodes in matching materials and replace with simple BSDF."""
    count = 0
    for mat in bpy.data.materials:
        if mat_name_partial.lower() not in mat.name.lower(): continue
        mat.use_nodes = True
        # CLEAR ALL EXISTING NODES
        mat.node_tree.nodes.clear()
        # Build new simple graph
        out  = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
        out.location = (300, 0)
        if transparent:
            tr = mat.node_tree.nodes.new("ShaderNodeBsdfTransparent")
            tr.location = (0, 0)
            mat.node_tree.links.new(tr.outputs["BSDF"], out.inputs["Surface"])
        else:
            bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
            bsdf.location = (0, 0)
            bsdf.inputs["Base Color"].default_value  = rgba
            bsdf.inputs["Roughness"].default_value   = roughness
            if emit and emit_s > 0:
                bsdf.inputs["Emission Color"].default_value    = emit
                bsdf.inputs["Emission Strength"].default_value = emit_s
            mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        mat.blend_method = "BLEND" if transparent else "OPAQUE"
        count += 1
        print(f"  Wiped & replaced: {mat.name}")
    return count

# Hair → cyan (all hair variants including outline)
wipe_and_replace("hairback", C_HAIR, roughness=0.28)
wipe_and_replace("hairfront", C_HAIR, roughness=0.28)
wipe_and_replace("hair_00_hair", C_HAIR, roughness=0.28)

# Eye iris → teal emissive
wipe_and_replace("eyeiris", C_EYE, roughness=0.05, emit=C_EYE, emit_s=2.0)

# Eye highlight → bright white
wipe_and_replace("eyehighlight", (1,1,1,1), roughness=0.02,
                 emit=(1,1,1,1), emit_s=3.0)

# Hide default clothes (transparent)
wipe_and_replace("bottoms_01_cloth", None, transparent=True)
wipe_and_replace("shoes_01_cloth",   None, transparent=True)
wipe_and_replace("tops_01_cloth",    None, transparent=True)

# ── 3. Arm pose ───────────────────────────────────────────────────────────
print("[v24] Setting arm pose (relaxed)...")
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
for side, sign in [("L", 1), ("R", -1)]:
    b = rig.pose.bones.get(f"J_Bip_{side}_UpperArm")
    if b:
        b.rotation_mode = "XYZ"
        b.rotation_euler = Euler((0, 0, sign * math.radians(-45)), "XYZ")
bpy.ops.object.mode_set(mode="OBJECT")
bpy.context.view_layer.update()

# ── 4. Append outfit from Master Blend ───────────────────────────────────
print("[v24] Appending outfit...")
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

# ── 5. Correct glasses positions ─────────────────────────────────────────
print("[v24] Positioning all glasses to VRoid eye level...")
FRAME_ORIGINAL_Z = 1.335  # z of Round Frames in Master Blend
z_shift = TARGET_GLASS_Z - FRAME_ORIGINAL_Z  # correct shift ≈ 0.046m
print(f"  z_shift = {z_shift:.4f}m")

for obj in outfit_objects:
    if "glasses" not in obj.name.lower(): continue
    on = obj.name.lower()
    if obj.location.z > 0.5:
        # Was at head level in master blend → apply correct shift
        obj.location.z += z_shift
        obj.location.y  = TARGET_GLASS_Y
    else:
        # Was at origin → place directly at target
        if "bridge" in on:
            obj.location = Vector((0.0,         TARGET_GLASS_Y, TARGET_GLASS_Z))
        elif "l_temple" in on:
            obj.location = Vector((-0.095,      TARGET_GLASS_Y + 0.01, TARGET_GLASS_Z))
        elif "r_temple" in on:
            obj.location = Vector(( 0.095,      TARGET_GLASS_Y + 0.01, TARGET_GLASS_Z))
        else:
            obj.location = Vector((0.0,         TARGET_GLASS_Y, TARGET_GLASS_Z))
    print(f"  Glasses: {obj.name} → z={obj.location.z:.3f}")

# Hairclip → top of head
for obj in outfit_objects:
    if "hairclip" in obj.name.lower():
        obj.location.z = head_z + 0.03
        obj.location.y = -0.08

# Ahoge → top-center of head
for obj in outfit_objects:
    if "ahoge" in obj.name.lower():
        obj.location.z = head_z + 0.06
        obj.location.x = 0.0
        obj.location.y = -0.05

# ── 6. Outfit materials + rig ─────────────────────────────────────────────
print("[v24] Applying outfit materials and rigging...")

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
    "hoodie":   make_mat("MV_Hoodie", srgb("#6DCFE8"), 0.72),
    "charcoal": make_mat("MV_Collar", srgb("#3B3F45"), 0.82),
    "cuff":     make_mat("MV_Collar", srgb("#3B3F45"), 0.82),
    "shirt":    make_mat("MV_Shirt",  srgb("#E6E9EE"), 0.80),
    "sock":     make_mat("MV_Sock",   srgb("#F0F2F5"), 0.88),
    "shoe":     make_mat("MV_ShoeW",  srgb("#F5F5F4"), 0.58),
    "glasses":  make_mat("MV_Glass",  srgb("#F5A4C8"), 0.22, metallic=0.12),
    "hairclip": make_mat("MV_Clip",   srgb("#C8C8C8"), 0.28, metallic=0.88),
    "ahoge":    make_mat("MV_HairA",  srgb("#7ED8F2"), 0.28),
    "strap":    make_mat("MV_GlassP", srgb("#F5A4C8"), 0.22),
    "zipper":   make_mat("MV_Zip",    srgb("#3B3F45"), 0.70, metallic=0.40),
    "panel":    make_mat("MV_Hoodie", srgb("#6DCFE8"), 0.72),
    "sleeve":   make_mat("MV_Hoodie", srgb("#6DCFE8"), 0.72),
    "pocket":   make_mat("MV_Hoodie", srgb("#6DCFE8"), 0.72),
    "shorts":   make_mat("MV_Shorts", srgb("#3B3F45"), 0.82),
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
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE": obj.modifiers.remove(mod)
    arm_mod = obj.modifiers.new("VRoid_Arm","ARMATURE")
    arm_mod.object = rig
    obj.parent = rig
    obj.parent_type = "OBJECT"

# ── 7. Renderer ───────────────────────────────────────────────────────────
print("[v24] Setting up renderer...")
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

# ── 8. Render 6-view (camera centered higher at z=1.0) ───────────────────
print("[v24] Rendering...")
# Center at z=1.0 (mid-chest), scale 1.6 shows head-to-mid-thigh
C  = Vector((0.0,0.0,1.00)); HD = Vector((0.0,0.0,head_z))

def rv(name, loc, sc_, look=None):
    look = look or C
    cam.location = loc
    cam.rotation_euler = (look-loc).to_track_quat('-Z','Y').to_euler()
    cd.ortho_scale = sc_
    sc.render.filepath = os.path.join(PREV, name+".png")
    bpy.ops.render.render(write_still=True)
    print(f"  ✓ {name}")

rv("front", Vector(( 0,-3.0, 1.00)), 1.55)
rv("left",  Vector(( 3, 0.0, 1.00)), 1.55)
rv("right", Vector((-3, 0.0, 1.00)), 1.55)
rv("back",  Vector(( 0, 3.0, 1.00)), 1.55)
rv("face",  Vector(( 0,-0.5, head_z)), 0.42, HD)
rv("top",   Vector(( 0,-0.1, 5.0)),   0.90, HD)

# ── 9. Export VRM ─────────────────────────────────────────────────────────
print("[v24] Exporting VRM...")
try:
    bpy.ops.export_scene.vrm(filepath=VRM)
    print(f"[v24] VRM: {VRM}")
except Exception as e:
    print(f"[v24] VRM warning: {e}")
print("[v24] Done!")
