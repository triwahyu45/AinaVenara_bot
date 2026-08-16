from pathlib import Path
"""
build_aina_v14.py  –  Aina Venara VRM v14
==========================================
Strategy:
  • Import VRoid akari_base.vrm  →  keep its armature + anime face mesh
  • Build ALL geometry ourselves in Blender (no Trip AI at all)
  • Outfit: hoodie body, inner shirt, shorts, socks, sneakers  – all procedural
  • Accessories: glasses (pink rounded rect), hairclip-3, ahoge
  • Recolour the base VRoid materials to match Aina's canonical palette
  • Correct orientation: VRoid armature faces –Y  →  all coords in –Y space
  • Export VRM  +  render 6 view previews

Canonical measurements (from Aina_Venara_Modeling_Spec.md):
  height        1.52 m
  head height   0.20 m
  glasses width 0.13 m  lens 0.052×0.036
  hairclip      0.052×0.024 m, front-left hair side
  ahoge height  0.13 m
"""

import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

# ── paths ───────────────────────────────────────────────────────────────
ROOT   = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder")
BASE   = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/VRM Draft/Aina_Venara_Base.vrm")
GLB    = str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Trip AI Export/Aina+Venara.glb")
OUT    = os.path.join(ROOT, "output", "Aina_Venara_v14.vrm")
BLEND  = os.path.join(ROOT, "output", "Aina_Venara_v14.blend")
PREV   = os.path.join(ROOT, "output", "previews", "v14")
os.makedirs(PREV, exist_ok=True)

# ── canonical colours ────────────────────────────────────────────────────
def hex_rgb(h, gamma=2.2):
    h = h.lstrip("#")
    r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return r**gamma, g**gamma, b**gamma, 1.0

C_HAIR      = hex_rgb("#7ED8F2")   # cyan bob
C_HAIR_TIP  = hex_rgb("#7E8CCF")   # blue-violet tips
C_EYE       = hex_rgb("#4FC1B3")   # teal-green iris
C_SKIN      = hex_rgb("#FFE7B0")   # warm skin
C_HOODIE    = hex_rgb("#7ED8F2")   # cyan-mint
C_HOODIE2   = hex_rgb("#5CB7E6")   # slightly darker cyan for gradient feel
C_COLLAR    = hex_rgb("#3B3F45")   # charcoal collar / cuffs
C_SHIRT     = hex_rgb("#E6E9EE")   # off-white inner shirt
C_SHORTS    = hex_rgb("#3B3F45")   # dark charcoal shorts
C_SOCK      = hex_rgb("#F0F2F5")   # white socks
C_SHOE      = hex_rgb("#EDEDEC")   # off-white sneaker
C_GLASS     = hex_rgb("#F5A4C8")   # pink glasses frame
C_CLIP      = hex_rgb("#C8C8C8")   # metallic silver hairclip
C_AHOGE     = hex_rgb("#7ED8F2")   # cyan ahoge

# ── utility ──────────────────────────────────────────────────────────────
def purge():
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

def make_mat(name, rgba, roughness=0.7, metallic=0.0, emission=None):
    mat = bpy.data.materials.get(name)
    if mat:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value  = roughness
    bsdf.inputs["Metallic"].default_value   = metallic
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = 0.3
    return mat

def apply_mat(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

def link(obj):
    if obj.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(obj)

def bone_world(rig, name):
    b = rig.pose.bones.get(name)
    if b:
        return (rig.matrix_world @ b.matrix).translation.copy()
    return Vector((0, 0, 1.4))

def parent_to_bone(child, rig, bone_name):
    child.parent      = rig
    child.parent_type = "BONE"
    child.parent_bone = bone_name
    child.matrix_parent_inverse = Matrix.Identity(4)

# ── 1.  clear scene ──────────────────────────────────────────────────────
print("[v14] Clearing scene...")
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
purge()

# ── 2.  import VRoid base (armature + face mesh) ─────────────────────────
print("[v14] Importing VRoid base...")
result = bpy.ops.import_scene.vrm(filepath=BASE)
print(f"[v14] Import result: {result}")
print(f"[v14] Objects in scene: {[o.name+'/'+o.type for o in bpy.context.scene.objects]}")
print(f"[v14] Objects in data:  {[o.name+'/'+o.type for o in bpy.data.objects]}")

# Link any unlinked objects to scene
for o in bpy.data.objects:
    if o.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(o)

rig = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
if not rig:
    print("ERROR: no armature found in data.objects")
    sys.exit(1)
rig.name = "Aina_Armature"
print(f"[v14] Armature: {rig.name}")

# ── 3.  recolour base VRoid materials to Aina palette ────────────────────
print("[v14] Recolouring VRoid materials...")
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    for slot in obj.material_slots:
        if not slot.material:
            continue
        mn = slot.material.name.lower()
        bsdf = None
        if slot.material.use_nodes:
            for n in slot.material.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    bsdf = n; break
        if not bsdf:
            continue
        # hair
        if "hair" in mn and "tip" not in mn:
            bsdf.inputs["Base Color"].default_value = C_HAIR
            bsdf.inputs["Roughness"].default_value  = 0.35
        elif "tip" in mn or "bv" in mn:
            bsdf.inputs["Base Color"].default_value = C_HAIR_TIP
        # eye / iris
        elif "eye" in mn or "iris" in mn:
            bsdf.inputs["Base Color"].default_value = C_EYE
            bsdf.inputs["Roughness"].default_value  = 0.2
        # skin / face
        elif "skin" in mn or "face" in mn or "body" in mn:
            bsdf.inputs["Base Color"].default_value = C_SKIN
            bsdf.inputs["Roughness"].default_value  = 0.6

# ── 4.  probe head bone position ─────────────────────────────────────────
# VRoid armature faces –Y.  Head bone tip is roughly at (0, 0, 1.43)
bpy.context.view_layer.update()
head_pos = bone_world(rig, "J_Bip_C_Head")
if head_pos.length < 0.1:
    head_pos = bone_world(rig, "head")
if head_pos.length < 0.1:
    head_pos = Vector((0.0, 0.0, 1.43))
print(f"[v14] Head bone world pos: {head_pos}")

# Centre X/Y at 0; Z is the chin-ish level of the head bone origin
# face centre (eye level) is approximately head_pos.z + 0.07
eye_z  = head_pos.z + 0.07
nose_z = head_pos.z - 0.01
# –Y direction is front of face in VRoid Blender space
FRONT  = -0.175   # Y offset for items in front of face
FRONT2 = -0.17    # slightly closer

# ── 5.  build outfit geometry ────────────────────────────────────────────
def add_mesh(verts, edges, faces, name):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, edges, faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def box_mesh(name, sx, sy, sz, ox=0, oy=0, oz=0):
    """Create a simple box mesh centred at (ox,oy,oz)."""
    hx,hy,hz = sx/2, sy/2, sz/2
    verts = [
        (ox-hx, oy-hy, oz-hz), (ox+hx, oy-hy, oz-hz),
        (ox+hx, oy+hy, oz-hz), (ox-hx, oy+hy, oz-hz),
        (ox-hx, oy-hy, oz+hz), (ox+hx, oy-hy, oz+hz),
        (ox+hx, oy+hy, oz+hz), (ox-hx, oy+hy, oz+hz),
    ]
    faces = [
        (0,1,2,3),(4,5,6,7),(0,4,7,3),(1,5,6,2),(0,1,5,4),(3,2,6,7)
    ]
    return add_mesh(verts, [], faces, name)

def parent_to_armature(obj, rig):
    obj.parent = rig
    obj.parent_type = "OBJECT"
    mod = obj.modifiers.new("Armature","ARMATURE")
    mod.object = rig
    # simple uniform weight to root bone
    root = rig.data.bones[0].name
    vg = obj.vertex_groups.new(name=root)
    vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")

print("[v14] Building outfit geometry...")

# --- hoodie body (torso + oversized volume) ---
# torso: –Y facing, centred on origin, sitting on top of feet
# approximate dimensions scaled to 1.52m character
SCALE = 1.0   # already in metres matching the VRoid base at 1.52m

# Hoodie outer
hoodie = box_mesh("Aina_Hoodie",
    sx=0.40, sy=0.20, sz=0.42,
    ox=0.0, oy=0.0, oz=0.95)
apply_mat(hoodie, make_mat("M_Hoodie", C_HOODIE, roughness=0.75))

# Charcoal off-shoulder collar
collar = box_mesh("Aina_Collar",
    sx=0.42, sy=0.21, sz=0.09,
    ox=0.0, oy=0.0, oz=1.19)
apply_mat(collar, make_mat("M_Collar", C_COLLAR, roughness=0.8))

# Sleeve L  (our model faces –Y, so arm extends in +X direction)
sleeve_l = box_mesh("Aina_Sleeve_L",
    sx=0.14, sy=0.14, sz=0.40,
    ox=0.30, oy=0.0, oz=1.0)
apply_mat(sleeve_l, make_mat("M_Sleeve_L", C_HOODIE, roughness=0.75))

# Sleeve cuff L charcoal
cuff_l = box_mesh("Aina_Cuff_L",
    sx=0.115, sy=0.115, sz=0.065,
    ox=0.30, oy=0.0, oz=0.79)
apply_mat(cuff_l, make_mat("M_Cuff_L", C_COLLAR, roughness=0.8))

# Sleeve R
sleeve_r = box_mesh("Aina_Sleeve_R",
    sx=0.14, sy=0.14, sz=0.40,
    ox=-0.30, oy=0.0, oz=1.0)
apply_mat(sleeve_r, make_mat("M_Sleeve_R", C_HOODIE, roughness=0.75))

cuff_r = box_mesh("Aina_Cuff_R",
    sx=0.115, sy=0.115, sz=0.065,
    ox=-0.30, oy=0.0, oz=0.79)
apply_mat(cuff_r, make_mat("M_Cuff_R", C_COLLAR, roughness=0.8))

# Inner white shirt (visible at torso opening)
shirt = box_mesh("Aina_Shirt",
    sx=0.22, sy=0.14, sz=0.40,
    ox=0.0, oy=-0.05, oz=0.93)
apply_mat(shirt, make_mat("M_Shirt", C_SHIRT, roughness=0.8))

# Shorts
shorts = box_mesh("Aina_Shorts",
    sx=0.28, sy=0.18, sz=0.18,
    ox=0.0, oy=0.0, oz=0.72)
apply_mat(shorts, make_mat("M_Shorts", C_SHORTS, roughness=0.85))

# Left leg
leg_l = box_mesh("Aina_Leg_L",
    sx=0.095, sy=0.10, sz=0.40,
    ox=0.085, oy=0.0, oz=0.47)
apply_mat(leg_l, make_mat("M_Leg_L", C_SKIN, roughness=0.65))

# Right leg
leg_r = box_mesh("Aina_Leg_R",
    sx=0.095, sy=0.10, sz=0.40,
    ox=-0.085, oy=0.0, oz=0.47)
apply_mat(leg_r, make_mat("M_Leg_R", C_SKIN, roughness=0.65))

# Socks L & R
sock_l = box_mesh("Aina_Sock_L", sx=0.09, sy=0.09, sz=0.14, ox=0.085, oy=0.0, oz=0.20)
apply_mat(sock_l, make_mat("M_Sock_L", C_SOCK, roughness=0.9))

sock_r = box_mesh("Aina_Sock_R", sx=0.09, sy=0.09, sz=0.14, ox=-0.085, oy=0.0, oz=0.20)
apply_mat(sock_r, make_mat("M_Sock_R", C_SOCK, roughness=0.9))

# Sneakers L & R (slightly wider/longer, sole)
shoe_l = box_mesh("Aina_Shoe_L", sx=0.11, sy=0.20, sz=0.09, ox=0.085, oy=-0.02, oz=0.048)
apply_mat(shoe_l, make_mat("M_Shoe_L", C_SHOE, roughness=0.6))

shoe_r = box_mesh("Aina_Shoe_R", sx=0.11, sy=0.20, sz=0.09, ox=-0.085, oy=-0.02, oz=0.048)
apply_mat(shoe_r, make_mat("M_Shoe_R", C_SHOE, roughness=0.6))

# Arms (visible at wrist beyond cuff)
arm_l = box_mesh("Aina_Arm_L", sx=0.08, sy=0.08, sz=0.09, ox=0.30, oy=0.0, oz=0.72)
apply_mat(arm_l, make_mat("M_Arm_L", C_SKIN, roughness=0.65))

arm_r = box_mesh("Aina_Arm_R", sx=0.08, sy=0.08, sz=0.09, ox=-0.30, oy=0.0, oz=0.72)
apply_mat(arm_r, make_mat("M_Arm_R", C_SKIN, roughness=0.65))

# Parent all outfit pieces to armature
outfit_objs = [hoodie, collar, sleeve_l, cuff_l, sleeve_r, cuff_r,
               shirt, shorts, leg_l, leg_r, sock_l, sock_r,
               shoe_l, shoe_r, arm_l, arm_r]
for ob in outfit_objs:
    parent_to_armature(ob, rig)

# ── 6.  accessories ──────────────────────────────────────────────────────
# All coords in Blender –Y facing (VRoid standard)
# head_pos is head bone world position; front of face = –Y
print("[v14] Building accessories...")
mat_glass = make_mat("M_Glass_Frame", C_GLASS, roughness=0.25, metallic=0.1)
mat_clip  = make_mat("M_Hairclip",    C_CLIP,  roughness=0.3,  metallic=0.8)
mat_ahoge = make_mat("M_Ahoge",       C_AHOGE, roughness=0.35)

# --- Glasses ---
# total width 0.13m, lens 0.052×0.036, bridge 0.014m
# Position: eye level, FRONT = –0.175 in Y
GL_W  = 0.052   # lens width
GL_H  = 0.036   # lens height
GL_T  = 0.003   # frame tube thickness
GL_CX = 0.034   # lens centre X offset from face centre
GL_BW = 0.014   # bridge half-width
GL_Y  = FRONT
GL_Z  = eye_z - 0.005
GL_X  = head_pos.x

def make_glass_ring(name, cx, cy, cz, rw, rh, t):
    """Create a rounded-rect frame as thin torus-ish box ring."""
    verts = []
    faces = []
    segs = 16
    # outer rect verts
    for i in range(segs):
        a = 2*math.pi*i/segs
        # map circle to squircle
        ca, sa = math.cos(a), math.sin(a)
        x = cx + (rw/2+t)*ca
        z = cz + (rh/2+t)*sa
        verts.append((x, cy-t/2, z))
        verts.append((x, cy+t/2, z))
    # inner
    for i in range(segs):
        a = 2*math.pi*i/segs
        ca, sa = math.cos(a), math.sin(a)
        x = cx + (rw/2)*ca
        z = cz + (rh/2)*sa
        verts.append((x, cy-t/2, z))
        verts.append((x, cy+t/2, z))
    # faces: connect outer ring
    n = segs
    for i in range(n):
        i2 = (i+1) % n
        o0,o1 = i*2,   i2*2
        i0,i1 = i*2+2*n, i2*2+2*n
        faces.append((o0, o1, i1, i0))
        o0f,o1f = i*2+1, i2*2+1
        i0f,i1f = i*2+1+2*n, i2*2+1+2*n
        faces.append((o0f, o1f, i1f, i0f))
        faces.append((o0, o0f, i0f, i0))
        faces.append((o1, o1f, i1f, i1))
    return add_mesh(verts, [], faces, name)

# Use simpler torus approach for lens frames
def add_torus_ring(name, cx, cy, cz, rx, ry, t=0.003, segs=12, rings=8):
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bm = bmesh.new()
    for ri in range(rings):
        a = 2*math.pi*ri/rings
        ca, sa = math.cos(a), math.sin(a)
        cent_x = cx + rx*ca
        cent_z = cz + ry*sa
        for si in range(segs):
            b = 2*math.pi*si/segs
            cb, sb = math.cos(b), math.sin(b)
            # tube direction: mix of tangential (a direction) and Y
            dx = -math.sin(a)*cb*t
            dy = sb*t
            dz = math.cos(a)*cb*t
            bm.verts.new((cent_x+dx, cy+dy, cent_z+dz))
    bm.verts.ensure_lookup_table()
    for ri in range(rings):
        for si in range(segs):
            v00 = bm.verts[ri*segs + si]
            v01 = bm.verts[ri*segs + (si+1)%segs]
            v10 = bm.verts[((ri+1)%rings)*segs + si]
            v11 = bm.verts[((ri+1)%rings)*segs + (si+1)%segs]
            bm.faces.new([v00, v01, v11, v10])
    bm.to_mesh(me); bm.free()
    me.update()
    return ob

# Lens frame L (left from character's view = +X in Blender)
lens_l = add_torus_ring("Aina_Lens_L",
    cx=GL_X + GL_CX, cy=GL_Y, cz=GL_Z,
    rx=GL_W/2, ry=GL_H/2, t=GL_T, segs=10, rings=16)
apply_mat(lens_l, mat_glass)

# Lens frame R
lens_r = add_torus_ring("Aina_Lens_R",
    cx=GL_X - GL_CX, cy=GL_Y, cz=GL_Z,
    rx=GL_W/2, ry=GL_H/2, t=GL_T, segs=10, rings=16)
apply_mat(lens_r, mat_glass)

# Bridge (horizontal bar connecting lenses)
bridge = box_mesh("Aina_Bridge",
    sx=GL_BW*2+0.002, sy=GL_T*2, sz=GL_T*2,
    ox=GL_X, oy=GL_Y, oz=GL_Z)
apply_mat(bridge, mat_glass)

# Temples (arms going back over ears) – thin bars in Y direction
def temple(name, cx):
    verts = [
        (cx-GL_T, GL_Y,      GL_Z-GL_T),
        (cx+GL_T, GL_Y,      GL_Z-GL_T),
        (cx+GL_T, GL_Y,      GL_Z+GL_T),
        (cx-GL_T, GL_Y,      GL_Z+GL_T),
        (cx-GL_T, GL_Y+0.14, GL_Z-GL_T-0.01),
        (cx+GL_T, GL_Y+0.14, GL_Z-GL_T-0.01),
        (cx+GL_T, GL_Y+0.14, GL_Z+GL_T-0.01),
        (cx-GL_T, GL_Y+0.14, GL_Z+GL_T-0.01),
    ]
    faces = [(0,1,2,3),(4,5,6,7),(0,4,7,3),(1,5,6,2),(0,1,5,4),(3,2,6,7)]
    return add_mesh(verts,[],faces,name)

tmpl_l = temple("Aina_Temple_L", cx=GL_X + GL_CX + GL_W/2)
apply_mat(tmpl_l, mat_glass)
tmpl_r = temple("Aina_Temple_R", cx=GL_X - GL_CX - GL_W/2)
apply_mat(tmpl_r, mat_glass)

# Parent glasses to head bone
head_bone = "J_Bip_C_Head" if rig.data.bones.get("J_Bip_C_Head") else "head"
for g in [lens_l, lens_r, bridge, tmpl_l, tmpl_r]:
    parent_to_armature(g, rig)

# --- Hairclip "3" (front-left hair side = +X, slightly forward -Y) ---
# size 0.052 × 0.024 m, depth 0.004m
# "3" shape: two horizontal bars + vertical connector on right side
HC_X  = head_pos.x + 0.065   # front-left (char's left = Blender +X)
HC_Y  = head_pos.y - 0.12    # front of hair
HC_Z  = head_pos.z + 0.06    # mid-upper head
HC_W, HC_H, HC_D = 0.052, 0.024, 0.004

def hairclip_3(name):
    t = 0.006   # bar thickness
    h = HC_H/2
    w = HC_W
    ox, oy, oz = HC_X, HC_Y, HC_Z
    # top bar
    verts, faces = [], []
    def add_box(ax, ay, az, bx, by_=None, bz=None):
        if by_ is None: by_ = oy
        n = len(verts)
        hvx = bx/2; hvz = bz/2
        dx, dz = t/2, t/2
        v = [
            (ax-hvx, by_-HC_D/2, az-hvz),(ax+hvx, by_-HC_D/2, az-hvz),
            (ax+hvx, by_+HC_D/2, az-hvz),(ax-hvx, by_+HC_D/2, az-hvz),
            (ax-hvx, by_-HC_D/2, az+hvz),(ax+hvx, by_-HC_D/2, az+hvz),
            (ax+hvx, by_+HC_D/2, az+hvz),(ax-hvx, by_+HC_D/2, az+hvz),
        ]
        verts.extend(v)
        f = [(n,n+1,n+2,n+3),(n+4,n+5,n+6,n+7),(n,n+4,n+7,n+3),
             (n+1,n+5,n+6,n+2),(n,n+1,n+5,n+4),(n+3,n+2,n+6,n+7)]
        faces.extend(f)
    # "3" = top bar, middle bar, bottom bar, right vertical stem
    add_box(ox, oy, oz + h - t/2, w, bz=t)          # top horizontal
    add_box(ox, oy, oz,           w, bz=t)           # middle horizontal
    add_box(ox, oy, oz - h + t/2, w, bz=t)          # bottom horizontal
    add_box(ox + w/2 - t/2, oy, oz,  t, bz=HC_H)    # right vertical spine
    return add_mesh(verts, [], faces, name)

hc = hairclip_3("Aina_Hairclip_3")
apply_mat(hc, mat_clip)
parent_to_armature(hc, rig)

# --- Ahoge (zigzag cyan strand above head) ---
# height 0.13m, starts at crown centre
AH_X = head_pos.x
AH_Y = head_pos.y
AH_BASE_Z = head_pos.z + 0.10   # just above crown

def ahoge(name):
    r = 0.004   # strand radius
    # zigzag control points (dx, dy, dz from base)
    pts = [
        (AH_X,       AH_Y,       AH_BASE_Z),
        (AH_X+0.015, AH_Y,       AH_BASE_Z+0.04),
        (AH_X-0.012, AH_Y,       AH_BASE_Z+0.08),
        (AH_X+0.008, AH_Y,       AH_BASE_Z+0.115),
        (AH_X,       AH_Y,       AH_BASE_Z+0.135),
    ]
    verts, faces = [], []
    segs = 6
    for i, (px, py, pz) in enumerate(pts):
        for s in range(segs):
            a = 2*math.pi*s/segs
            verts.append((px+r*math.cos(a), py+r*math.sin(a), pz))
    # connect rings
    for i in range(len(pts)-1):
        for s in range(segs):
            s2 = (s+1)%segs
            a = i*segs+s; b = i*segs+s2
            c = (i+1)*segs+s2; d = (i+1)*segs+s
            faces.append((a,b,c,d))
    return add_mesh(verts, [], faces, name)

ah = ahoge("Aina_Ahoge")
apply_mat(ah, mat_ahoge)
parent_to_armature(ah, rig)

# ── 7.  export VRM ───────────────────────────────────────────────────────
print("[v14] Exporting VRM...")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.vrm(filepath=OUT)
print(f"[v14] VRM saved: {OUT}")

# Save blend
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print(f"[v14] Blend saved: {BLEND}")

# ── 8.  render previews ──────────────────────────────────────────────────
print("[v14] Rendering previews...")
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 64
scene.render.resolution_x = 512
scene.render.resolution_y = 512

# Camera
cam_data = bpy.data.cameras.new("PreviewCam")
cam = bpy.data.objects.new("PreviewCam", cam_data)
bpy.context.scene.collection.objects.link(cam)
scene.camera = cam
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.0

# World / lighting
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value  = (0.07, 0.07, 0.07, 1)
bg.inputs["Strength"].default_value = 0.5
scene.world = world

# Key light
def add_sun(name, x, y, z, energy=4.0, col=(1,1,1)):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = energy
    ld.color  = col
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = (x, y, z)
    lo.rotation_euler = (math.radians(45), 0, math.radians(30))
    return lo

add_sun("Key",  3, -3, 5, energy=5.0)
add_sun("Fill", -2, 2, 3, energy=2.0, col=(0.7,0.85,1.0))
add_sun("Rim",  0, 5, 4,  energy=2.5, col=(0.6,0.4,1.0))

LOOK_AT = Vector((0.0, 0.0, 0.9))

def render_view(name, cam_loc, fov_scale=2.0):
    cam.location = cam_loc
    # point camera at look-at
    direction = LOOK_AT - cam_loc
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam_data.ortho_scale = fov_scale
    scene.render.filepath = os.path.join(PREV, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {name}")

render_view("front",  Vector((0.0, -4.0, 0.9)), 1.9)
render_view("left",   Vector((4.0,  0.0, 0.9)), 1.9)
render_view("right",  Vector((-4.0, 0.0, 0.9)), 1.9)
render_view("back",   Vector((0.0,  4.0, 0.9)), 1.9)
render_view("face",   Vector((0.0, -2.5, 1.42)), 0.55)
render_view("top",    Vector((0.0, -0.1, 5.0)), 1.2)

print("[v14] Done!")
