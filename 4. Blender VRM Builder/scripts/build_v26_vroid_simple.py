from pathlib import Path
"""
build_v26_vroid_simple.py — Aina Venara v26 (Simple VRoid Customization)
========================================================================
APPROACH:
  1. Import VRoid base (Aina_Venara_Base.vrm) which has full face, hair, body, and basic clothes.
  2. Recolor the native VRoid MToon materials directly (without breaking glTF/VRM export structure):
     - Hair -> Cyan (#7ED8F2)
     - Eye Iris -> Teal (#2EC4B6)
     - Tops (shirt/outfit) -> Cyan-Mint (#6DCFE8)
     - Bottoms (pants/skirt) -> Charcoal (#3B3F45)
  3. Append ONLY the iconic accessories from Master Blend and bone-parent them to Head bone:
     - Pink Glasses (Bridge, L/R Round Frames, L/R Temples)
     - Hairclip
     - Ahoge (lightning bolt hair style)
  4. Perform relaxed arm pose and render.
  5. Export complete, clean VRM file.
"""

import bpy, os, math
from mathutils import Vector, Euler

ROOT   = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
VROID  = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/VRM Draft/Aina_Venara_Base.vrm")
MASTER = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
VRM    = os.path.join(ROOT, "output", "Aina_Venara_v26.vrm")
PREV   = os.path.join(ROOT, "output", "previews", "v26")
os.makedirs(PREV, exist_ok=True)

def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_HAIR  = srgb("#7ED8F2")
C_HAIRS = srgb("#3B8CA0")
C_EYE   = srgb("#2EC4B6")
C_EYES  = srgb("#155A53")
C_TOPS  = srgb("#6DCFE8")
C_TOPSS = srgb("#2D6A78")
C_BOTS  = srgb("#3B3F45")
C_BOTSS = srgb("#1F2124")

# ── 1. Import VRoid ───────────────────────────────────────────────────────
print("[v26] Importing VRoid base...")
bpy.ops.import_scene.vrm(filepath=VROID)

rig = next((o for o in bpy.data.objects if o.type=='ARMATURE'), None)
bpy.context.view_layer.update()

def bone_z(name):
    b = rig.pose.bones.get(name)
    return (rig.matrix_world @ b.matrix).translation.z if b else 1.0

head_z = bone_z("J_Bip_C_Head")  # ~1.386
eye_z = head_z - 0.005
eye_y = -0.14

# ── 2. Native MToon Recolor (Safe for VRM Export) ─────────────────────────
print("[v26] Recoloring native VRoid MToon materials...")

def recolor_mtoon_node(mat_name_partial, lit_rgba, shade_rgba):
    for mat in bpy.data.materials:
        if mat_name_partial.lower() not in mat.name.lower(): continue
        if not mat.use_nodes: continue
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Find the MToon group/output node
        mtoon_node = None
        for node in nodes:
            if "Mtoon1Material.Mtoon1Output" in node.name or (node.type == 'GROUP' and "mtoon" in node.name.lower()):
                mtoon_node = node
                break
        if not mtoon_node:
            mtoon_node = next((n for n in nodes if n.type == 'GROUP'), None)
            
        if mtoon_node:
            # Disconnect texture links from base/shade color so solid color takes full effect
            for inp_name in ["Lit Color Texture Color", "Lit Color Texture", "Shade Color Texture", "Base Color Texture"]:
                if inp_name in mtoon_node.inputs:
                    inp = mtoon_node.inputs[inp_name]
                    for link in list(inp.links):
                        links.remove(link)
            
            # Set colors
            if "Lit Color" in mtoon_node.inputs:
                mtoon_node.inputs["Lit Color"].default_value = lit_rgba
            if "Shade Color" in mtoon_node.inputs:
                mtoon_node.inputs["Shade Color"].default_value = shade_rgba
            print(f"  Recolored MToon: {mat.name}")

recolor_mtoon_node("hairback", C_HAIR, C_HAIRS)
recolor_mtoon_node("hairfront", C_HAIR, C_HAIRS)
recolor_mtoon_node("hair_00_hair", C_HAIR, C_HAIRS)
recolor_mtoon_node("eyeiris", C_EYE, C_EYES)
recolor_mtoon_node("tops_01_cloth", C_TOPS, C_TOPSS)
recolor_mtoon_node("bottoms_01_cloth", C_BOTS, C_BOTSS)

# ── 3. Arm pose ───────────────────────────────────────────────────────────
print("[v26] Setting arm pose...")
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
for side, sign in [("L", 1), ("R", -1)]:
    b = rig.pose.bones.get(f"J_Bip_{side}_UpperArm")
    if b:
        b.rotation_mode = "XYZ"
        b.rotation_euler = Euler((0, 0, sign * math.radians(-45)), "XYZ")
bpy.ops.object.mode_set(mode="OBJECT")
bpy.context.view_layer.update()

# ── 4. Append accessories from Master Blend ──────────────────────────────
print("[v26] Appending accessories...")
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
print("[v26] Positioning and parenting accessories to Head bone...")
FRAME_ORIGINAL_Z = 1.335
z_shift = eye_z - FRAME_ORIGINAL_Z

for obj in outfit_objects:
    on = obj.name.lower()
    if "glasses" in on:
        if obj.location.z > 0.5:
            obj.location.z += z_shift
            obj.location.y  = eye_y
        else:
            if "bridge" in on:
                obj.location = Vector((0.0, eye_y, eye_z))
            elif "l_temple" in on:
                obj.location = Vector((-0.095, eye_y + 0.01, eye_z))
            elif "r_temple" in on:
                obj.location = Vector(( 0.095, eye_y + 0.01, eye_z))
            else:
                obj.location = Vector((0.0, eye_y, eye_z))
        
        bpy.context.view_layer.update()
        world_matrix = obj.matrix_world.copy()
        obj.parent = rig
        obj.parent_type = 'BONE'
        obj.parent_bone = 'J_Bip_C_Head'
        obj.matrix_world = world_matrix
        print(f"  Rigged accessory: {obj.name}")

    elif "hairclip" in on:
        obj.location.z = head_z + 0.03
        obj.location.y = -0.08
        bpy.context.view_layer.update()
        world_matrix = obj.matrix_world.copy()
        obj.parent = rig
        obj.parent_type = 'BONE'
        obj.parent_bone = 'J_Bip_C_Head'
        obj.matrix_world = world_matrix
        print(f"  Rigged accessory: {obj.name}")

    elif "ahoge" in on:
        obj.location.z = head_z + 0.06
        obj.location.x = 0.0
        obj.location.y = -0.05
        bpy.context.view_layer.update()
        world_matrix = obj.matrix_world.copy()
        obj.parent = rig
        obj.parent_type = 'BONE'
        obj.parent_bone = 'J_Bip_C_Head'
        obj.matrix_world = world_matrix
        print(f"  Rigged accessory: {obj.name}")

# ── 6. Apply Materials for Appended Accessories ──────────────────────────
print("[v26] Applying materials to accessories...")

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

# ── 7. Setup render ───────────────────────────────────────────────────────
print("[v26] Setting up renderer...")
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
print("[v26] Rendering views...")
C  = Vector((0.0, 0.0, 0.85)); HD = Vector((0.0, 0.0, head_z))

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
rv("face",  Vector(( 0,-0.5, head_z)), 0.42, HD)
rv("top",   Vector(( 0,-0.1, 5.0)),   0.90, HD)

# ── 9. Export VRM ─────────────────────────────────────────────────────────
print("[v26] Exporting VRM...")
try:
    bpy.ops.export_scene.vrm(filepath=VRM)
    print(f"[v26] VRM: {VRM}")
except Exception as e:
    print(f"[v26] VRM warning: {e}")

print("[v26] Done!")
