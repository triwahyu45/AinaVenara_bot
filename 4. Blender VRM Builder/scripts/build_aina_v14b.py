from pathlib import Path
"""
build_aina_v14b.py  –  Aina Venara VRM v14b
=============================================
Fixes from v14:
  • VRoid materials use MToon / custom shader nodes, not BSDF.
    -> Iterate ALL nodes looking for any color socket to tint correctly.
  • Outfit boxes were too big.  Rescaled to fit VRoid body (head ≈ 0.20m,
    full height ≈ 1.52m, head_z ≈ 1.39m).
  • Face camera was too far; zoomed in properly.
  • Hair/eye colour applied via MToon LitColor input.
"""

import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

ROOT = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
BASE = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/VRM Draft/Aina_Venara_Base.vrm")
OUT  = os.path.join(ROOT, "output", "Aina_Venara_v14b.vrm")
PREV = os.path.join(ROOT, "output", "previews", "v14b")
os.makedirs(PREV, exist_ok=True)

# ── canonical colours (linear) ────────────────────────────────────────────
def srgb(h):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return (r**2.2, g**2.2, b**2.2, 1.0)

C_HAIR   = srgb("#7ED8F2")
C_HAIR_T = srgb("#7E8CCF")
C_EYE    = srgb("#4FC1B3")
C_SKIN   = srgb("#FFE7B0")
C_HOODIE = srgb("#6DCFE8")   # slightly more saturated cyan
C_COLLAR = srgb("#3B3F45")
C_SHIRT  = srgb("#E6E9EE")
C_SHORTS = srgb("#3B3F45")
C_SOCK   = srgb("#F0F2F5")
C_SHOE   = srgb("#EDEDEC")
C_GLASS  = srgb("#F5A4C8")
C_CLIP   = srgb("#C0C0C0")
C_AHOGE  = srgb("#7ED8F2")

# ── helpers ───────────────────────────────────────────────────────────────
def purge():
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

def set_node_color(mat, rgba):
    """Set colour on any colour-input node in a material (MToon or BSDF)."""
    if not mat or not mat.use_nodes:
        return
    color_input_names = [
        "Base Color","Color","LitColor","Lit Color",
        "MainColor","Main Color","ShadeColor",
    ]
    for node in mat.node_tree.nodes:
        for inp in node.inputs:
            if inp.name in color_input_names and inp.type == "RGBA":
                inp.default_value = rgba
                return   # only tint the first color socket

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

def box_mesh(name, sx, sy, sz, ox=0.0, oy=0.0, oz=0.0):
    hx,hy,hz = sx/2, sy/2, sz/2
    verts = [
        (ox-hx,oy-hy,oz-hz),(ox+hx,oy-hy,oz-hz),
        (ox+hx,oy+hy,oz-hz),(ox-hx,oy+hy,oz-hz),
        (ox-hx,oy-hy,oz+hz),(ox+hx,oy-hy,oz+hz),
        (ox+hx,oy+hy,oz+hz),(ox-hx,oy+hy,oz+hz),
    ]
    faces = [(0,1,2,3),(4,5,6,7),(0,4,7,3),(1,5,6,2),(0,1,5,4),(3,2,6,7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts,[],faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def parent_to_armature(obj, rig):
    obj.parent      = rig
    obj.parent_type = "OBJECT"
    mod = obj.modifiers.new("Armature","ARMATURE")
    mod.object = rig
    # weight entire mesh to root bone
    root = rig.data.bones[0].name
    vg = obj.vertex_groups.new(name=root)
    vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")

def bone_world(rig, *names):
    bpy.context.view_layer.update()
    for name in names:
        b = rig.pose.bones.get(name)
        if b:
            return (rig.matrix_world @ b.matrix).translation.copy()
    return Vector((0.0, 0.0, 1.39))

# ── 1. Clear scene ────────────────────────────────────────────────────────
print("[v14b] Clearing scene...")
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
purge()

# ── 2. Import VRoid base ──────────────────────────────────────────────────
print("[v14b] Importing VRoid base...")
bpy.ops.import_scene.vrm(filepath=BASE)
for o in bpy.data.objects:
    if o.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(o)

rig = next((o for o in bpy.data.objects if o.type=="ARMATURE"), None)
if not rig:
    print("ERROR: no armature"); sys.exit(1)
rig.name = "Aina_Armature"
print(f"[v14b] Armature: {rig.name}")
print(f"[v14b] Bones: {[b.name for b in rig.data.bones][:10]}")

# ── 3. Recolour VRoid MToon materials ─────────────────────────────────────
print("[v14b] Recolouring MToon materials...")
for mat in bpy.data.materials:
    mn = mat.name.lower()
    if not mat.use_nodes:
        continue
    # Print material names to see what we have
    print(f"  Material: {mat.name}")
    if any(x in mn for x in ["hair","_01_"]):
        set_node_color(mat, C_HAIR)
        print(f"    -> cyan hair")
    elif any(x in mn for x in ["eye","iris","_13_","_12_"]):
        set_node_color(mat, C_EYE)
        print(f"    -> teal eye")
    elif any(x in mn for x in ["skin","face","_00_"]):
        set_node_color(mat, C_SKIN)
        print(f"    -> skin")

# ── 4. Probe head bone ────────────────────────────────────────────────────
head_pos = bone_world(rig,
    "J_Bip_C_Head", "head", "Head",
    "J_Bip_C_Neck",
)
print(f"[v14b] Head pos: {head_pos}")

# VRoid body reference points (matched to 1.52m character, head at ~1.39):
# Chest centre ≈ 1.05, waist ≈ 0.85, hip ≈ 0.72, knee ≈ 0.42, ankle ≈ 0.09
# Shoulder X  ≈ ±0.175  (half of 35cm shoulder span)
# Arm length  ≈ 0.52m  → hand at ±(0.175+0.52) = ±0.695 from centre X
# But armature arm extends horizontally so X span ≈ ±0.60

# ── 5. Build outfit ───────────────────────────────────────────────────────
print("[v14b] Building outfit...")

M_HOODIE  = make_mat("M_Hoodie",  C_HOODIE,  roughness=0.75)
M_COLLAR  = make_mat("M_Collar",  C_COLLAR,  roughness=0.80)
M_SHIRT   = make_mat("M_Shirt",   C_SHIRT,   roughness=0.80)
M_SHORTS  = make_mat("M_Shorts",  C_SHORTS,  roughness=0.85)
M_SOCK    = make_mat("M_Sock",    C_SOCK,    roughness=0.90)
M_SHOE    = make_mat("M_Shoe",    C_SHOE,    roughness=0.60)
M_SKIN    = make_mat("M_Skin",    C_SKIN,    roughness=0.65)
M_GLASS   = make_mat("M_Glass",   C_GLASS,   roughness=0.25, metallic=0.1)
M_CLIP    = make_mat("M_Clip",    C_CLIP,    roughness=0.30, metallic=0.85)
M_AHOGE   = make_mat("M_Ahoge",   C_AHOGE,   roughness=0.35)

# --- Hoodie outer body ---
# VRoid chest is about 0.78cm wide at shoulder, torso height 0.38m (0.84→1.22)
hoodie = box_mesh("Aina_Hoodie",
    sx=0.31, sy=0.165, sz=0.37,
    ox=0.0, oy=0.0, oz=1.03)
apply_mat(hoodie, M_HOODIE)

# Collar strip (off-shoulder, charcoal, sitting on top of hoodie)
collar = box_mesh("Aina_Collar",
    sx=0.33, sy=0.17, sz=0.075,
    ox=0.0, oy=0.0, oz=1.22)
apply_mat(collar, M_COLLAR)

# Sleeve L (+X direction for VRoid T-pose)
sleeve_l = box_mesh("Aina_Sleeve_L",
    sx=0.40, sy=0.095, sz=0.095,
    ox=0.305, oy=0.0, oz=1.13)
apply_mat(sleeve_l, M_HOODIE)

cuff_l = box_mesh("Aina_Cuff_L",
    sx=0.06, sy=0.09, sz=0.09,
    ox=0.505, oy=0.0, oz=1.13)
apply_mat(cuff_l, M_COLLAR)

# Sleeve R (–X)
sleeve_r = box_mesh("Aina_Sleeve_R",
    sx=0.40, sy=0.095, sz=0.095,
    ox=-0.305, oy=0.0, oz=1.13)
apply_mat(sleeve_r, M_HOODIE)

cuff_r = box_mesh("Aina_Cuff_R",
    sx=0.06, sy=0.09, sz=0.09,
    ox=-0.505, oy=0.0, oz=1.13)
apply_mat(cuff_r, M_COLLAR)

# Inner white shirt strip (visible at collar opening)
shirt = box_mesh("Aina_Shirt",
    sx=0.17, sy=0.12, sz=0.30,
    ox=0.0, oy=-0.04, oz=1.00)
apply_mat(shirt, M_SHIRT)

# Shorts
shorts = box_mesh("Aina_Shorts",
    sx=0.23, sy=0.15, sz=0.15,
    ox=0.0, oy=0.0, oz=0.745)
apply_mat(shorts, M_SHORTS)

# Hands (wrists, flesh coloured)
hand_l = box_mesh("Aina_Hand_L",
    sx=0.075, sy=0.055, sz=0.075,
    ox=0.560, oy=0.0, oz=1.13)
apply_mat(hand_l, M_SKIN)

hand_r = box_mesh("Aina_Hand_R",
    sx=0.075, sy=0.055, sz=0.075,
    ox=-0.560, oy=0.0, oz=1.13)
apply_mat(hand_r, M_SKIN)

# Socks
sock_l = box_mesh("Aina_Sock_L",
    sx=0.075, sy=0.082, sz=0.115,
    ox=0.075, oy=0.0, oz=0.18)
apply_mat(sock_l, M_SOCK)

sock_r = box_mesh("Aina_Sock_R",
    sx=0.075, sy=0.082, sz=0.115,
    ox=-0.075, oy=0.0, oz=0.18)
apply_mat(sock_r, M_SOCK)

# Sneakers
shoe_l = box_mesh("Aina_Shoe_L",
    sx=0.09, sy=0.175, sz=0.075,
    ox=0.075, oy=-0.012, oz=0.040)
apply_mat(shoe_l, M_SHOE)

shoe_r = box_mesh("Aina_Shoe_R",
    sx=0.09, sy=0.175, sz=0.075,
    ox=-0.075, oy=-0.012, oz=0.040)
apply_mat(shoe_r, M_SHOE)

outfit_objs = [hoodie, collar, sleeve_l, cuff_l, sleeve_r, cuff_r,
               shirt, shorts, hand_l, hand_r, sock_l, sock_r,
               shoe_l, shoe_r]
for ob in outfit_objs:
    parent_to_armature(ob, rig)

# ── 6. Glasses ────────────────────────────────────────────────────────────
# From spec: total width 13cm, lens 5.2×3.6cm, bridge 1.4cm
# VRoid faces –Y.  In front of face: Y decreases (more negative).
# head_pos.z is head bone origin (approx chin level).
# eye level ≈ head_pos.z + 0.065

eye_z   = head_pos.z + 0.068
gl_y    = head_pos.y - 0.158   # in front of face (–Y direction)
gl_cx   = 0.034                # half interocular / lens centre X
gl_rw   = 0.026                # lens half-width (52mm/2)
gl_rh   = 0.018                # lens half-height (36mm/2)
T       = 0.003                # frame tube radius

def torus_ring(name, cx, cy, cz, rw, rh, t=0.003, rings=20, segs=8):
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    verts_list = []
    for ri in range(rings):
        a = 2*math.pi * ri / rings
        ca, sa = math.cos(a), math.sin(a)
        px = cx + rw * ca
        pz = cz + rh * sa
        for si in range(segs):
            b = 2*math.pi * si / segs
            cb, sb = math.cos(b), math.sin(b)
            # tangent along ring
            tx = -math.sin(a)
            tz =  math.cos(a) * (rh/rw)
            tn = math.sqrt(tx*tx + tz*tz + 1e-9)
            tx /= tn; tz /= tn
            bm.verts.new((px + t*(cb*tx), cy + t*sb, pz + t*(cb*tz)))
    bm.verts.ensure_lookup_table()
    for ri in range(rings):
        for si in range(segs):
            v00 = bm.verts[ri*segs + si]
            v01 = bm.verts[ri*segs + (si+1)%segs]
            v10 = bm.verts[((ri+1)%rings)*segs + si]
            v11 = bm.verts[((ri+1)%rings)*segs + (si+1)%segs]
            bm.faces.new([v00, v01, v11, v10])
    bm.to_mesh(me); bm.free(); me.update()
    return ob

lens_l = torus_ring("Aina_Lens_L",
    cx=head_pos.x + gl_cx, cy=gl_y, cz=eye_z,
    rw=gl_rw, rh=gl_rh, t=T, rings=20, segs=8)
apply_mat(lens_l, M_GLASS)

lens_r = torus_ring("Aina_Lens_R",
    cx=head_pos.x - gl_cx, cy=gl_y, cz=eye_z,
    rw=gl_rw, rh=gl_rh, t=T, rings=20, segs=8)
apply_mat(lens_r, M_GLASS)

# Bridge
bridge = box_mesh("Aina_Bridge",
    sx=0.020, sy=T*2, sz=T*2,
    ox=head_pos.x, oy=gl_y, oz=eye_z)
apply_mat(bridge, M_GLASS)

# Temples (bar going back along Y+)
def temple_bar(name, cx):
    verts = [
        (cx-T, gl_y,      eye_z-T),
        (cx+T, gl_y,      eye_z-T),
        (cx+T, gl_y,      eye_z+T),
        (cx-T, gl_y,      eye_z+T),
        (cx-T, gl_y+0.12, eye_z-T*0.5),
        (cx+T, gl_y+0.12, eye_z-T*0.5),
        (cx+T, gl_y+0.12, eye_z+T*0.5),
        (cx-T, gl_y+0.12, eye_z+T*0.5),
    ]
    faces = [(0,1,2,3),(4,5,6,7),(0,4,7,3),(1,5,6,2),(0,1,5,4),(3,2,6,7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts,[],faces); me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

tmpl_l = temple_bar("Aina_Temple_L", head_pos.x + gl_cx + gl_rw)
apply_mat(tmpl_l, M_GLASS)
tmpl_r = temple_bar("Aina_Temple_R", head_pos.x - gl_cx - gl_rw)
apply_mat(tmpl_r, M_GLASS)

for g in [lens_l, lens_r, bridge, tmpl_l, tmpl_r]:
    parent_to_armature(g, rig)

# ── 7. Hairclip "3" ───────────────────────────────────────────────────────
# front-left hair side = +X and slightly –Y from head centre
# size 52×24mm, depth 4mm
HC_X = head_pos.x + 0.060
HC_Y = head_pos.y - 0.105
HC_Z = head_pos.z + 0.065
HW, HH, HD = 0.052, 0.024, 0.004
t = 0.006   # bar thickness

def clip3():
    """Number '3' shape from horizontal bars + right spine."""
    verts, faces = [], []
    def bar(ax, ay, az, lx, lz):
        n = len(verts)
        hvx, hvz = lx/2, lz/2
        v = [(ax-hvx,ay-HD/2,az-hvz),(ax+hvx,ay-HD/2,az-hvz),
             (ax+hvx,ay+HD/2,az-hvz),(ax-hvx,ay+HD/2,az-hvz),
             (ax-hvx,ay-HD/2,az+hvz),(ax+hvx,ay-HD/2,az+hvz),
             (ax+hvx,ay+HD/2,az+hvz),(ax-hvx,ay+HD/2,az+hvz)]
        verts.extend(v)
        faces.extend([(n,n+1,n+2,n+3),(n+4,n+5,n+6,n+7),
                      (n,n+4,n+7,n+3),(n+1,n+5,n+6,n+2),
                      (n,n+1,n+5,n+4),(n+3,n+2,n+6,n+7)])
    bar(HC_X, HC_Y, HC_Z + HH/2 - t/2, HW, t)        # top bar
    bar(HC_X, HC_Y, HC_Z,              HW, t)          # middle bar
    bar(HC_X, HC_Y, HC_Z - HH/2 + t/2, HW, t)        # bottom bar
    bar(HC_X + HW/2 - t/2, HC_Y, HC_Z, t, HH)        # right spine
    me = bpy.data.meshes.new("Aina_Hairclip_3")
    me.from_pydata(verts,[],faces); me.update()
    ob = bpy.data.objects.new("Aina_Hairclip_3", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

hc = clip3()
apply_mat(hc, M_CLIP)
parent_to_armature(hc, rig)

# ── 8. Ahoge ─────────────────────────────────────────────────────────────
# zigzag strand, 13cm height, cyan
AH_BASE = Vector((head_pos.x, head_pos.y, head_pos.z + 0.10))
AH_PTS = [
    AH_BASE + Vector((0,      0, 0)),
    AH_BASE + Vector((0.012,  0, 0.035)),
    AH_BASE + Vector((-0.010, 0, 0.072)),
    AH_BASE + Vector((0.007,  0, 0.108)),
    AH_BASE + Vector((0,      0, 0.132)),
]
r_strand = 0.004

def strand(pts, r, name):
    verts, faces = [], []
    segs = 6
    for p in pts:
        for s in range(segs):
            a = 2*math.pi*s/segs
            verts.append((p.x+r*math.cos(a), p.y+r*math.sin(a), p.z))
    for i in range(len(pts)-1):
        for s in range(segs):
            s2 = (s+1)%segs
            a = i*segs+s; b = i*segs+s2
            c = (i+1)*segs+s2; d = (i+1)*segs+s
            faces.append((a,b,c,d))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts,[],faces); me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

ah = strand(AH_PTS, r_strand, "Aina_Ahoge")
apply_mat(ah, M_AHOGE)
parent_to_armature(ah, rig)

# ── 9. Export VRM ─────────────────────────────────────────────────────────
print("[v14b] Exporting VRM...")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.vrm(filepath=OUT)
print(f"[v14b] Saved: {OUT}")
bpy.ops.wm.save_as_mainfile(filepath=OUT.replace(".vrm",".blend"))

# ── 10. Render previews ───────────────────────────────────────────────────
print("[v14b] Rendering...")
scene = bpy.context.scene
scene.render.engine     = "CYCLES"
scene.cycles.samples    = 80
scene.render.resolution_x = 512
scene.render.resolution_y = 512

cam_d = bpy.data.cameras.new("Cam")
cam   = bpy.data.objects.new("Cam", cam_d)
bpy.context.scene.collection.objects.link(cam)
scene.camera  = cam
cam_d.type    = "ORTHO"

world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.06,0.06,0.08,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = world

def add_sun(n, loc, energy, col=(1,1,1)):
    ld = bpy.data.lights.new(n,"SUN")
    ld.energy = energy; ld.color = col
    lo = bpy.data.objects.new(n, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (math.radians(40),0,math.radians(20))
    return lo

add_sun("Key",  ( 2,-2, 5), 4.5)
add_sun("Fill", (-2, 2, 3), 2.0, (0.7,0.85,1.0))
add_sun("Rim",  ( 0, 4, 3), 2.0, (0.6,0.4,1.0))

LOOK = Vector((0, 0, 0.9))

def rview(name, loc, scale):
    cam.location = loc
    d = LOOK - loc; cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
    cam_d.ortho_scale = scale
    scene.render.filepath = os.path.join(PREV, name+".png")
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered {name}")

rview("front", Vector(( 0.0, -3.5, 0.85)), 1.85)
rview("left",  Vector(( 3.5,  0.0, 0.85)), 1.85)
rview("right", Vector((-3.5,  0.0, 0.85)), 1.85)
rview("back",  Vector(( 0.0,  3.5, 0.85)), 1.85)
rview("face",  Vector(( 0.0, -1.8, 1.44)), 0.42)
rview("top",   Vector(( 0.0, -0.1, 5.0 )), 1.10)

print("[v14b] Done!")
