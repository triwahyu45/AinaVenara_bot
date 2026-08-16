from pathlib import Path
"""
build_v23_vroid_overlay.py — Aina Venara v23
=============================================
Fixes from v22:
  1. Glasses: Bridge/Temple pieces were at origin (0,0,0) in Master Blend
     → Force ALL glasses pieces to VRoid eye position
  2. Hair color: Use aggressive node override — clear Surface link and reconnect
     Also handle MToon Outline materials
  3. Camera: Increase ortho_scale to 1.55 and center at z=0.85 for full body view
  4. Add Outfit_Shorts back to appended list (was missing)
"""

import bpy, os, math
from mathutils import Vector, Euler

ROOT   = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
VROID  = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/VRM Draft/Aina_Venara_Base.vrm")
MASTER = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
VRM    = os.path.join(ROOT, "output", "Aina_Venara_v23.vrm")
PREV   = os.path.join(ROOT, "output", "previews", "v23")
os.makedirs(PREV, exist_ok=True)

def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_HAIR  = srgb("#7ED8F2")
C_EYE   = srgb("#2EC4B6")

# ── 1. Import VRoid ───────────────────────────────────────────────────────
print("[v23] Importing VRoid base...")
bpy.ops.import_scene.vrm(filepath=VROID)

rig = next((o for o in bpy.data.objects if o.type=='ARMATURE'), None)
bpy.context.view_layer.update()

def bone_z(name):
    b = rig.pose.bones.get(name)
    return (rig.matrix_world @ b.matrix).translation.z if b else 1.0

head_z  = bone_z("J_Bip_C_Head")
eye_z   = head_z - 0.045  # eyes are 4.5cm below head bone
eye_y   = -0.14            # nose bridge Y in VRoid space
print(f"[v23] head_z={head_z:.3f}  eye_z={eye_z:.3f}")

# ── 2. Aggressive material override for Cycles rendering ──────────────────
print("[v23] Overriding materials...")

def override_surface(mat, base_color, roughness=0.35, emit=None, emit_s=0.0):
    """Forcibly replace the Surface shader in Material Output with a Principled BSDF."""
    if not mat.use_nodes: return
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    # Find ALL output nodes
    out_nodes = [n for n in nodes if n.type in ("OUTPUT_MATERIAL", "GROUP_OUTPUT")]
    if not out_nodes:
        return
    out = out_nodes[0]
    # Remove existing Surface link
    for link in list(links):
        if link.to_node == out and link.to_socket.name in ("Surface","Color","Shader"):
            links.remove(link)
    # Add new Principled BSDF
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (out.location.x - 350, out.location.y)
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value  = roughness
    if emit and emit_s > 0:
        bsdf.inputs["Emission Color"].default_value    = emit
        bsdf.inputs["Emission Strength"].default_value = emit_s
    # Try to connect to Surface or first available shader input
    for sock_name in ("Surface", "Shader", "Color"):
        if sock_name in out.inputs:
            links.new(bsdf.outputs["BSDF"], out.inputs[sock_name])
            break

def make_transparent(mat):
    """Make material completely transparent (hide default clothes)."""
    if not mat.use_nodes: return
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    out_nodes = [n for n in nodes if n.type in ("OUTPUT_MATERIAL",)]
    if not out_nodes: return
    out = out_nodes[0]
    for link in list(links):
        if link.to_node == out:
            links.remove(link)
    transp = nodes.new("ShaderNodeBsdfTransparent")
    transp.location = (out.location.x - 200, out.location.y)
    if "Surface" in out.inputs:
        links.new(transp.outputs["BSDF"], out.inputs["Surface"])

# Apply overrides to all materials
HAIR_KEYWORDS = ["hairback", "hairfront", "hair_back", "hair_front"]
EYE_KEYWORDS  = ["eyeiris", "eye_iris"]
EYE_HI_KEYS   = ["eyehighlight", "eye_highlight"]
HIDE_KEYWORDS = ["bottoms_01_cloth", "shoes_01_cloth", "tops_01_cloth"]

for mat in bpy.data.materials:
    mn = mat.name.lower()
    if any(k in mn for k in HAIR_KEYWORDS):
        override_surface(mat, C_HAIR, roughness=0.28)
        print(f"  Hair → cyan: {mat.name}")
    elif any(k in mn for k in EYE_HI_KEYS):
        override_surface(mat, (1,1,1,1), roughness=0.02, emit=(1,1,1,1), emit_s=3.0)
        print(f"  Eye highlight: {mat.name}")
    elif any(k in mn for k in EYE_KEYWORDS):
        override_surface(mat, C_EYE, roughness=0.05, emit=C_EYE, emit_s=2.0)
        print(f"  Eye → teal: {mat.name}")
    elif any(k in mn for k in HIDE_KEYWORDS):
        make_transparent(mat)
        print(f"  Hidden: {mat.name}")

# ── 3. Arm pose (relaxed) ─────────────────────────────────────────────────
print("[v23] Setting arm pose...")
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
for side, sign in [("L", 1), ("R", -1)]:
    bone = rig.pose.bones.get(f"J_Bip_{side}_UpperArm")
    if bone:
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = Euler((0, 0, sign * math.radians(-45)), "XYZ")
bpy.ops.object.mode_set(mode="OBJECT")
bpy.context.view_layer.update()

# ── 4. Append outfit from Master Blend ───────────────────────────────────
print("[v23] Appending outfit...")
SKIP = ["body_base", "face_", "sphere.", "cube.", "cylinder.", "torus."]

with bpy.data.libraries.load(MASTER, link=False) as (data_from, data_to):
    wanted = [n for n in data_from.objects
              if not any(k in n.lower() for k in SKIP)
              and any(k in n.lower() for k in ["outfit","accessory","glasses",
                                                "hairclip","ahoge"])]
    data_to.objects = wanted

outfit_objects = []
for obj in data_to.objects:
    if obj is None: continue
    bpy.context.scene.collection.objects.link(obj)
    outfit_objects.append(obj)

# ── 5. FIX glasses positions → VRoid eye level ────────────────────────────
print("[v23] Fixing all glasses positions...")
for obj in outfit_objects:
    if "glasses" not in obj.name.lower(): continue
    on = obj.name.lower()
    # Round frames are at z=1.335 → shift to eye_z
    z_shift = eye_z - 1.335  # difference from master blend head to VRoid eye
    if obj.location.z > 0.5:  # already at head level
        obj.location.z += z_shift
        obj.location.y = eye_y  # align Y to VRoid nose bridge
    else:
        # Pieces at origin (bridge, temple) — move to eye level
        if "bridge" in on:
            obj.location = Vector((0.0, eye_y, eye_z))
        elif "l_temple" in on:
            obj.location = Vector((-0.09, eye_y + 0.01, eye_z))
        elif "r_temple" in on:
            obj.location = Vector(( 0.09, eye_y + 0.01, eye_z))
        else:
            obj.location = Vector((0.0, eye_y, eye_z))
    print(f"  Glasses placed: {obj.name} → z={obj.location.z:.3f}")

# Fix hairclip too
for obj in outfit_objects:
    if "hairclip" not in obj.name.lower(): continue
    # Place hairclip at side of head, above eye level
    obj.location.z = head_z + 0.02  # slightly above head bone
    obj.location.y = -0.10          # front of head

# Ahoge already at z≈1.35+ in master blend, align to VRoid head
for obj in outfit_objects:
    if "ahoge" not in obj.name.lower(): continue
    obj.location.z = head_z + 0.05  # top of head

# ── 6. Materials + rig ───────────────────────────────────────────────────
print("[v23] Applying outfit materials and rigging...")

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
    "hoodie":   make_mat("MV_Hoodie",  srgb("#6DCFE8"), 0.72),
    "charcoal": make_mat("MV_Collar",  srgb("#3B3F45"), 0.82),
    "cuff":     make_mat("MV_Collar",  srgb("#3B3F45"), 0.82),
    "shirt":    make_mat("MV_Shirt",   srgb("#E6E9EE"), 0.80),
    "sock":     make_mat("MV_Sock",    srgb("#F0F2F5"), 0.88),
    "shoe":     make_mat("MV_ShoeW",   srgb("#F5F5F4"), 0.58),
    "glasses":  make_mat("MV_Glass",   srgb("#F5A4C8"), 0.22, metallic=0.12),
    "hairclip": make_mat("MV_Clip",    srgb("#C8C8C8"), 0.28, metallic=0.88),
    "ahoge":    make_mat("MV_HairA",   srgb("#7ED8F2"), 0.28),
    "strap":    make_mat("MV_GlassP",  srgb("#F5A4C8"), 0.22),
    "zipper":   make_mat("MV_Zip",     srgb("#3B3F45"), 0.70, metallic=0.40),
    "panel":    make_mat("MV_Hoodie",  srgb("#6DCFE8"), 0.72),
    "sleeve":   make_mat("MV_Hoodie",  srgb("#6DCFE8"), 0.72),
    "pocket":   make_mat("MV_Hoodie",  srgb("#6DCFE8"), 0.72),
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
    # Rig
    for mod in list(obj.modifiers):
        if mod.type == "ARMATURE": obj.modifiers.remove(mod)
    arm_mod = obj.modifiers.new("VRoid_Arm","ARMATURE")
    arm_mod.object = rig
    obj.parent = rig
    obj.parent_type = "OBJECT"

# ── 7. Renderer ───────────────────────────────────────────────────────────
print("[v23] Setting up renderer...")
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

# ── 8. Render 6-view ─────────────────────────────────────────────────────
print("[v23] Rendering...")
C  = Vector((0.0,0.0,0.85)); HD = Vector((0.0,0.0,head_z))

def rv(name,loc,sc_,look=None):
    look = look or C
    cam.location = loc
    cam.rotation_euler = (look-loc).to_track_quat('-Z','Y').to_euler()
    cd.ortho_scale = sc_
    sc.render.filepath = os.path.join(PREV,name+".png")
    bpy.ops.render.render(write_still=True)
    print(f"  ✓ {name}")

rv("front", Vector(( 0,-3.0, 0.85)), 1.55)
rv("left",  Vector(( 3, 0.0, 0.85)), 1.55)
rv("right", Vector((-3, 0.0, 0.85)), 1.55)
rv("back",  Vector(( 0, 3.0, 0.85)), 1.55)
rv("face",  Vector(( 0,-0.5, head_z)), 0.42, HD)
rv("top",   Vector(( 0,-0.1, 5.0 )), 0.90, HD)

# ── 9. Export VRM ─────────────────────────────────────────────────────────
print("[v23] Exporting VRM...")
try:
    bpy.ops.export_scene.vrm(filepath=VRM)
    print(f"[v23] VRM: {VRM}")
except Exception as e:
    print(f"[v23] VRM warning: {e}")
print("[v23] Done!")
