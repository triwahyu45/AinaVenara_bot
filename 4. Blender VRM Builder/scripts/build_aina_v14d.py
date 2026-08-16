from pathlib import Path
"""
build_aina_v14d.py  –  Aina Venara VRM v14d
=============================================
Strategy:
  1. Clear scene.
  2. Import VRoid base (Aina_Venara_Base.vrm).
     Keep ONLY the high-quality Face/MESH and Body/MESH.
     Delete default T-shirt, shorts, shoes vertices from Body/MESH.
  3. Append ONLY hair, accessories, and outfit meshes from Aina_Venara_Master.blend.
     Exclude proxy body parts (Body_Base_*), proxy face (Face_Eyes_*), duplicate armature, and Tripo references.
  4. Apply Subdivision Surface modifiers to outfit/hair meshes to make them smooth and organic.
  5. Weight-paint (data transfer) outfit meshes from the VRoid Body skin.
  6. Rig the hair, glasses, and hairclip 100% to the Head bone.
  7. Apply materials: cyan hair, blue-violet tips, teal eyes, pink glasses.
  8. Export VRM and render previews.
"""

import bpy, os, sys, math
from mathutils import Vector

ROOT = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
BASE = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/VRM Draft/Aina_Venara_Base.vrm")
MASTER_BLEND = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Modular Output/Aina_Venara_Master.blend")
OUT  = os.path.join(ROOT, "output", "Aina_Venara_v14d.vrm")
PREV = os.path.join(ROOT, "output", "previews", "v14d")
os.makedirs(PREV, exist_ok=True)

# Colors
def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_HAIR   = srgb("#7ED8F2")
C_HAIR_T = srgb("#7E8CCF")
C_EYE    = srgb("#4FC1B3")
C_SKIN   = srgb("#FFE7B0")
C_HOODIE = srgb("#6DCFE8")
C_COLLAR = srgb("#3B3F45")
C_SHIRT  = srgb("#E6E9EE")
C_SHORTS = srgb("#3B3F45")
C_SOCK   = srgb("#F0F2F5")
C_SHOE   = srgb("#EDEDEC")
C_GLASS  = srgb("#F5A4C8")
C_CLIP   = srgb("#C0C0C0")
C_AHOGE  = srgb("#7ED8F2")

# Helpers
def purge():
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

def make_mat(name, rgba, roughness=0.7, metallic=0.0):
    mat = bpy.data.materials.get(name)
    if mat:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value  = roughness
    bsdf.inputs["Metallic"].default_value   = metallic
    return mat

def apply_mat(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

# ── 1. Clear scene ────────────────────────────────────────────────────────
print("[v14d] Clearing scene...")
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
purge()

# ── 2. Import VRoid base ──────────────────────────────────────────────────
print("[v14d] Importing VRoid base...")
bpy.ops.import_scene.vrm(filepath=BASE)
for o in bpy.data.objects:
    if o.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(o)

rig = next((o for o in bpy.data.objects if o.type=="ARMATURE"), None)
if not rig:
    print("ERROR: no armature"); sys.exit(1)
rig.name = "Aina_Armature"

# Get body mesh and delete default clothes vertices
# Body Material Slots:
# Slot 0: Body skin (KEEP)
# Slot 1: Bottoms (DELETE)
# Slot 2: Shoes (DELETE)
# Slot 3: Tops (DELETE)
# Slot 4: HairBack (DELETE)
body = bpy.data.objects.get("Body")
if body:
    print("[v14d] Deleting clothes vertices from VRoid Body...")
    import bmesh
    me = body.data
    bm = bmesh.new()
    bm.from_mesh(me)
    # Delete faces associated with clothes materials (slots 1, 2, 3, 4)
    faces_to_delete = [f for f in bm.faces if f.material_index in [1, 2, 3, 4]]
    bmesh.ops.delete(bm, geom=faces_to_delete, context="FACES")
    bm.to_mesh(me)
    bm.free()
    me.update()

# ── 3. Append meshes from Master Blend with exclusion filters ─────────────
print("[v14d] Appending objects from Master Blend...")

exclude_prefixes = [
    "Body_Base_",
    "Face_Eyes_",
    "Reference_Tripo_",
    "Aina_Venara_Humanoid_",
    "Camera",
    "Light",
    "QA_Area_"
]

with bpy.data.libraries.load(MASTER_BLEND) as (data_from, data_to):
    # Only import objects that do not start with any of the excluded prefixes
    data_to.objects = [
        name for name in data_from.objects 
        if not any(name.startswith(p) for p in exclude_prefixes)
    ]

# Link imported objects to scene
imported_objects = []
for obj in data_to.objects:
    if obj:
        bpy.context.scene.collection.objects.link(obj)
        imported_objects.append(obj)
        print(f"  Appended: {obj.name} ({obj.type})")

# Determine head bone name
head_bone = "J_Bip_C_Head" if rig.data.bones.get("J_Bip_C_Head") else "head"

# ── 4. Apply materials and subdiv to imported meshes ─────────────────────
print("[v14d] Configuring materials and subdivisions...")
M_HOODIE = make_mat("M_Hoodie", C_HOODIE, roughness=0.75)
M_COLLAR = make_mat("M_Collar", C_COLLAR, roughness=0.80)
M_SHIRT  = make_mat("M_Shirt",  C_SHIRT,  roughness=0.80)
M_SHORTS = make_mat("M_Shorts", C_SHORTS, roughness=0.85)
M_SOCK   = make_mat("M_Sock",   C_SOCK,   roughness=0.90)
M_SHOE   = make_mat("M_Shoe",   C_SHOE,   roughness=0.60)
M_GLASS  = make_mat("M_Glass",  C_GLASS,  roughness=0.25, metallic=0.1)
M_CLIP   = make_mat("M_Clip",   C_CLIP,   roughness=0.30, metallic=0.85)
M_AHOGE  = make_mat("M_Ahoge",  C_AHOGE,  roughness=0.35)

# Rigging and smoothing loop
for obj in imported_objects:
    if obj.type not in ["MESH", "CURVE"]:
        continue
    
    # Smooth shading
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True
            
        # Add Subdivision Surface modifier to make meshes smooth
        # Exclude flat/thin accessories
        if "Hairclip" not in obj.name and "Glasses" not in obj.name:
            sub = obj.modifiers.new("Subdiv", "SUBSURF")
            sub.levels = 2
            sub.render_levels = 2
            
    # Assign materials based on name matching
    on = obj.name.lower()
    if "hoodie" in on:
        if "collar" in on or "cuff" in on:
            apply_mat(obj, M_COLLAR)
        else:
            apply_mat(obj, M_HOODIE)
    elif "shirt" in on:
        if "strap" in on:
            apply_mat(obj, M_GLASS) # pink straps
        else:
            apply_mat(obj, M_SHIRT)
    elif "shorts" in on:
        apply_mat(obj, M_SHORTS)
    elif "sock" in on:
        apply_mat(obj, M_SOCK)
    elif "shoe" in on:
        apply_mat(obj, M_SHOE)
    elif "glass" in on:
        apply_mat(obj, M_GLASS)
    elif "hairclip" in on:
        apply_mat(obj, M_CLIP)
    elif "ahoge" in on or "hair_base" in on:
        if "violet" in on or "tip" in on:
            apply_mat(obj, make_mat(obj.name+"_tip", C_HAIR_T, roughness=0.35))
        else:
            apply_mat(obj, make_mat(obj.name+"_base", C_HAIR, roughness=0.35))

# Recolour VRoid face/eyes
for mat in bpy.data.materials:
    mn = mat.name.lower()
    if not mat.use_nodes:
        continue
    # Set eye color
    if any(x in mn for x in ["eye","iris"]):
        for node in mat.node_tree.nodes:
            for inp in node.inputs:
                if inp.name in ["Base Color", "LitColor", "MainColor"] and inp.type == "RGBA":
                    inp.default_value = C_EYE

# ── 5. Rigging and Vertex Weights ─────────────────────────────────────────
print("[v14d] Rigging imported meshes to VRoid Armature...")
for obj in imported_objects:
    if obj.type not in ["MESH", "CURVE"]:
        continue
    
    # 1. Clean parent and modifier
    obj.parent = None
    for mod in list(obj.modifiers):
        if mod.type in ["ARMATURE", "DATA_TRANSFER"]:
            obj.modifiers.remove(mod)
            
    on = obj.name.lower()
    
    # 2. Setup vertex weights / data transfer first (for meshes only)
    if obj.type == "MESH":
        if "hair" in on or "glass" in on or "ahoge" in on:
            # Rig head objects 100% to head bone
            obj.vertex_groups.clear()
            vg = obj.vertex_groups.new(name=head_bone)
            vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
        else:
            # Rig body/outfit objects by transferring weights from base Body skin
            if body:
                print(f"  Transferring weights to {obj.name}...")
                obj.vertex_groups.clear()
                dt_mod = obj.modifiers.new(name="WeightTransfer", type="DATA_TRANSFER")
                dt_mod.object = body
                dt_mod.use_vert_data = True
                dt_mod.data_types_verts = {'VGROUP_WEIGHTS'}
                dt_mod.vert_mapping = 'NEAREST'
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=dt_mod.name)

    # 3. Parent to Aina_Armature and add Armature modifier
    obj.parent = rig
    obj.parent_type = "OBJECT"
    arm_mod = obj.modifiers.new("Armature", "ARMATURE")
    arm_mod.object = rig

# ── 6. Export VRM ─────────────────────────────────────────────────────────
print("[v14d] Exporting final VRM...")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.vrm(filepath=OUT)
print(f"[v14d] Export completed: {OUT}")
bpy.ops.wm.save_as_mainfile(filepath=OUT.replace(".vrm", ".blend"))

# ── 7. Render previews ───────────────────────────────────────────────────
print("[v14d] Rendering preview views...")
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 80
scene.render.resolution_x = 512
scene.render.resolution_y = 512

cam_d = bpy.data.cameras.new("PreviewCam")
cam = bpy.data.objects.new("PreviewCam", cam_d)
bpy.context.scene.collection.objects.link(cam)
scene.camera = cam
cam_d.type = "ORTHO"

# Lights
world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.06, 0.06, 0.08, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = world

def add_sun(n, loc, energy, col=(1,1,1)):
    ld = bpy.data.lights.new(n, "SUN")
    ld.energy = energy
    ld.color = col
    lo = bpy.data.objects.new(n, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (math.radians(40), 0, math.radians(20))

add_sun("Key",  ( 2,-2, 5), 4.5)
add_sun("Fill", (-2, 2, 3), 2.0, (0.7, 0.85, 1.0))
add_sun("Rim",  ( 0, 4, 3), 2.0, (0.6, 0.4, 1.0))

# Head bone position is roughly Z = 1.39
head_z = 1.39

def rview(name, cam_loc, ortho_scale, look_at):
    cam.location = cam_loc
    d = look_at - cam_loc
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam_d.ortho_scale = ortho_scale
    scene.render.filepath = os.path.join(PREV, name + ".png")
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {name}")

rview("front", Vector((0.0, -3.5, 0.85)), 1.85, Vector((0.0, 0.0, 0.85)))
rview("left",  Vector((3.5, 0.0, 0.85)),  1.85, Vector((0.0, 0.0, 0.85)))
rview("right", Vector((-3.5, 0.0, 0.85)), 1.85, Vector((0.0, 0.0, 0.85)))
rview("back",  Vector((0.0, 3.5, 0.85)),  1.85, Vector((0.0, 0.0, 0.85)))
rview("face",  Vector((0.0, -0.6, head_z + 0.05)), 0.40, Vector((0.0, 0.0, head_z + 0.05)))
rview("top",   Vector((0.0, -0.1, 5.0)),  1.10, Vector((0.0, 0.0, head_z)))

print("[v14d] All processes completed!")
