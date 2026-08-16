from pathlib import Path
"""
build_v28_vroid_perfect.py — Aina Venara v28 (Perfect VRoid Customization)
==========================================================================
APPROACH:
  1. Import VRoid base (Aina_Venara_Base.vrm).
  2. Wipe and replace VRoid material nodes for Cycles rendering:
     - N00_000_00_HairBack_00_HAIR -> Cyan (#7ED8F2)
     - N00_000_00_EyeIris_00_EYE -> Teal (#2EC4B6)
     - N00_000_00_EyeHighlight_00_EYE -> Bright Emissive White
     - N00_004_01_Tops_01_CLOTH -> Cyan-Mint (#6DCFE8)
     - N00_001_01_Bottoms_01_CLOTH -> Charcoal (#3B3F45)
     - N00_004_01_Shoes_01_CLOTH -> White (#F5F5F4)
  3. Append accessories (Glasses, Hairclip, Ahoge) from Master Blend:
     - Clear parent first to ensure clean world coords.
     - Calculate perfect head shifts:
       * z_shift = +0.114m (shifts from Master eye Z 1.335 to VRoid eye Z 1.449)
       * y_shift = +0.047m (shifts from Master nose bridge Y -0.135 to VRoid nose bridge Y -0.088)
     - Position using these shifts.
     - Use the robust `parent_set(type='BONE')` operator to parent to Head bone.
  4. Perform relaxed arm pose, render 6-view preview, and export clean VRM.
"""

import bpy, os, math
from mathutils import Vector, Euler

ROOT   = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
VROID  = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/VRM Draft/Aina_Venara_Base.vrm")
MASTER = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
VRM    = os.path.join(ROOT, "output", "Aina_Venara_v28.vrm")
PREV   = os.path.join(ROOT, "output", "previews", "v28")
os.makedirs(PREV, exist_ok=True)

def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_HAIR  = srgb("#7ED8F2")
C_EYE   = srgb("#2EC4B6")
C_TOPS  = srgb("#6DCFE8")
C_BOTS  = srgb("#3B3F45")
C_SHOE  = srgb("#F5F5F4")

# ── 1. Import VRoid ───────────────────────────────────────────────────────
print("[v28] Importing VRoid base...")
bpy.ops.import_scene.vrm(filepath=VROID)

rig = next((o for o in bpy.data.objects if o.type=='ARMATURE'), None)
bpy.context.view_layer.update()

def bone_z(name):
    b = rig.pose.bones.get(name)
    return (rig.matrix_world @ b.matrix).translation.z if b else 1.0

head_z = bone_z("J_Bip_C_Head")  # ~1.386
eye_z = 1.449                     # VRoid eye height
print(f"[v28] head_z={head_z:.3f} eye_z={eye_z:.3f}")

# ── 2. Override materials completely ─────────────────────────────────────
print("[v28] Overriding material nodes...")

def wipe_and_replace(mat_name_partial, rgba, roughness=0.35, emit=None, emit_s=0.0):
    count = 0
    for mat in bpy.data.materials:
        if mat_name_partial.lower() not in mat.name.lower(): continue
        mat.use_nodes = True
        mat.node_tree.nodes.clear()
        out  = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
        out.location = (300, 0)
        
        bsdf = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        bsdf.inputs["Base Color"].default_value  = rgba
        bsdf.inputs["Roughness"].default_value   = roughness
        if emit and emit_s > 0:
            bsdf.inputs["Emission Color"].default_value    = emit
            bsdf.inputs["Emission Strength"].default_value = emit_s
        mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        print(f"  Overrode: {mat.name}")
        count += 1
    return count

wipe_and_replace("hairback", C_HAIR, roughness=0.28)
wipe_and_replace("hairfront", C_HAIR, roughness=0.28)
wipe_and_replace("hair_00_hair", C_HAIR, roughness=0.28)
wipe_and_replace("eyeiris", C_EYE, roughness=0.05, emit=C_EYE, emit_s=2.0)
wipe_and_replace("eyehighlight", (1,1,1,1), roughness=0.02, emit=(1,1,1,1), emit_s=3.0)
wipe_and_replace("tops_01_cloth", C_TOPS, roughness=0.75)
wipe_and_replace("bottoms_01_cloth", C_BOTS, roughness=0.82)
wipe_and_replace("shoes_01_cloth", C_SHOE, roughness=0.60)

# ── 3. Arm pose ───────────────────────────────────────────────────────────
print("[v28] Setting arm pose...")
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
for side, sign in [("L", 1), ("R", -1)]:
    b = rig.pose.bones.get(f"J_Bip_{side}_UpperArm")
    if b:
        b.rotation_mode = "XYZ"
        b.rotation_euler = Euler((0, 0, sign * math.radians(-45)), "XYZ")
bpy.ops.object.mode_set(mode="OBJECT")
bpy.context.view_layer.update()

# ── 4. Append accessories ────────────────────────────────────────────────
print("[v28] Appending accessories...")
with bpy.data.libraries.load(MASTER, link=False) as (data_from, data_to):
    wanted = [n for n in data_from.objects
              if any(k in n.lower() for k in ["glasses", "hairclip", "ahoge"])]
    data_to.objects = wanted

outfit_objects = []
for obj in data_to.objects:
    if obj is None: continue
    bpy.context.scene.collection.objects.link(obj)
    outfit_objects.append(obj)

# ── 5. Position and bone-parent accessories ──────────────────────────────
print("[v28] Position shift and parenting to Head bone...")
# shifts to translate from master coordinates to VRoid head coordinates:
z_shift = 1.449 - 1.335   # +0.114m
y_shift = -0.088 - (-0.135) # +0.047m

for obj in outfit_objects:
    # Clear old parenting
    obj.parent = None
    on = obj.name.lower()
    
    # If the accessory coordinates were at origin in Master, set them relative to local eye level first
    if obj.location.z < 0.5:
        if "bridge" in on:
            obj.location = Vector((0.0, -0.135, 1.335))
        elif "l_temple" in on:
            obj.location = Vector((-0.095, -0.125, 1.335))
        elif "r_temple" in on:
            obj.location = Vector(( 0.095, -0.125, 1.335))
        else:
            obj.location = Vector((0.0, -0.135, 1.335))
            
    # Apply head shift
    obj.location.z += z_shift
    obj.location.y += y_shift
    
    # For curves, convert to mesh first (so VRM exporter handles them correctly)
    if obj.type == 'CURVE':
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.convert(target='MESH')
        obj = bpy.context.active_object
        
    bpy.context.view_layer.update()
    
    # Bone parenting using parent_set operator
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    rig.data.bones.active = rig.data.bones['J_Bip_C_Head']
    
    bpy.ops.object.parent_set(type='BONE')
    print(f"  Parented {obj.name} to J_Bip_C_Head at world z={obj.matrix_world.translation.z:.3f}")

# ── 6. Apply Materials to Accessories ─────────────────────────────────────
print("[v28] Applying materials to accessories...")

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
    "glasses":  make_mat("MV_Glass",  srgb("#F5A4C8"), 0.22, metallic=0.12),
    "hairclip": make_mat("MV_Clip",   srgb("#C8C8C8"), 0.28, metallic=0.88),
    "ahoge":    make_mat("MV_HairA",  srgb("#7ED8F2"), 0.28),
    "strap":    make_mat("MV_GlassP", srgb("#F5A4C8"), 0.22),
}

for obj in outfit_objects:
    if obj.type != 'MESH': continue
    on = obj.name.lower()
    for p in obj.data.polygons: p.use_smooth = True
    for key, mat in M.items():
        if key in on:
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            break

# ── 7. Setup render ───────────────────────────────────────────────────────
print("[v28] Setting up renderer...")
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

# ── 8. Render ─────────────────────────────────────────────────────────────
print("[v28] Rendering views...")
C  = Vector((0.0, 0.0, 0.85)); HD = Vector((0.0, 0.0, eye_z))

def rv(name, loc, sc_, look=None):
    look = look or C
    cam.location = loc
    cam.rotation_euler = (look-loc).to_track_quat('-Z','Y').to_euler()
    cd.ortho_scale = sc_
    sc.render.filepath = os.path.join(PREV, name+".png")
    bpy.ops.render.render(write_still=True)
    print(f"  ✓ {name}")

rv("front", Vector(( 0,-3.0, 0.85)), 1.55)
rv("left",  Vector(( 3, 0.0, 0.85)), 1.55)
rv("right", Vector((-3, 0.0, 0.85)), 1.55)
rv("back",  Vector(( 0, 3.0, 0.85)), 1.55)
rv("face",  Vector(( 0,-0.5, eye_z)), 0.42, HD)
rv("top",   Vector(( 0,-0.1, 5.0)),   0.90, HD)

# ── 9. Export VRM ─────────────────────────────────────────────────────────
print("[v28] Exporting VRM...")
try:
    bpy.ops.export_scene.vrm(filepath=VRM)
    print(f"[v28] VRM: {VRM}")
except Exception as e:
    print(f"[v28] VRM warning: {e}")

print("[v28] Done!")
