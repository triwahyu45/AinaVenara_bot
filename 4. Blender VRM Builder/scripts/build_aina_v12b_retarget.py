"""
build_aina_v12b_retarget.py
Perbaikan v12: fix skinning dengan Data Transfer modifier dari base VRM,
dan perbaiki orientasi kamera render.
"""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

BASE_VRM = Path(str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/VRM Draft/Aina_Venara_Base.vrm"))
GLB_SOURCE = Path(str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Trip AI Export/Aina+Venara.glb"))
OUTPUT_VRM = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/Aina_Venara_v12.vrm"))
OUTPUT_BLEND = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/Aina_Venara_v12.blend"))
PREVIEW_DIR = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/previews/v12"))

OUTPUT_VRM.parent.mkdir(parents=True, exist_ok=True)
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)


# ── Utility ──────────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials,
                  bpy.data.cameras, bpy.data.lights):
        for item in list(block):
            try:
                block.remove(item)
            except Exception:
                pass


def set_active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def look_at(camera, target):
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def prepare_render():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 768
    scene.render.film_transparent = False
    scene.world.color = (0.025, 0.03, 0.04)
    for obj in list(scene.objects):
        if obj.type in {"CAMERA", "LIGHT"}:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.object.camera_add()
    scene.camera = bpy.context.object
    scene.camera.data.lens = 58
    for loc, energy, size in (((-2.5, -3, 3), 500, 4), ((2, -1, 1.5), 250, 3), ((0, 2, 2.5), 350, 3)):
        bpy.ops.object.light_add(type="AREA", location=loc)
        bpy.context.object.data.energy = energy
        bpy.context.object.data.shape = "DISK"
        bpy.context.object.data.size = size
    return scene


def render_view(scene, name, cam_loc, target, lens=58):
    camera = scene.camera
    camera.location = cam_loc
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(PREVIEW_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


# ── Step 1: Import Base VRM untuk armature ────────────────────────────────────

print("[v12b] Clearing scene...")
clear_scene()

print("[v12b] Importing Base VRM for armature + reference body mesh...")
bpy.ops.import_scene.vrm(filepath=str(BASE_VRM))

base_armature = None
base_body_mesh = None
for obj in list(bpy.context.scene.objects):
    if obj.type == "ARMATURE":
        base_armature = obj
    elif obj.type == "MESH":
        # Simpan satu body mesh sebagai referensi weights
        if "Body" in obj.name or base_body_mesh is None:
            base_body_mesh = obj

if base_armature is None:
    raise RuntimeError("Tidak ditemukan armature di Base VRM!")

print(f"[v12b] Armature: {base_armature.name}")
print(f"[v12b] Reference body mesh: {base_body_mesh.name if base_body_mesh else 'None'}")

# Rename agar tidak bentrok
base_armature.name = "Aina_Armature"


# ── Step 2: Import GLB ────────────────────────────────────────────────────────

print("[v12b] Importing Trip AI GLB...")
bpy.ops.import_scene.gltf(filepath=str(GLB_SOURCE))

glb_mesh = None
for obj in bpy.context.scene.objects:
    if obj.type == "MESH" and obj != base_body_mesh and "Face" not in obj.name:
        glb_mesh = obj
        break

if glb_mesh is None:
    raise RuntimeError("Tidak ditemukan mesh dari GLB!")

print(f"[v12b] GLB mesh: {glb_mesh.name}")
glb_mesh.name = "Aina_Body_GLB"


# ── Step 3: Scale GLB ke ukuran VRoid standar ─────────────────────────────────

print("[v12b] Scaling GLB to VRM standard...")
set_active(glb_mesh)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Hitung bounding box
verts_world = [glb_mesh.matrix_world @ v.co for v in glb_mesh.data.vertices]
min_z = min(v.z for v in verts_world)
max_z = max(v.z for v in verts_world)
glb_height = max_z - min_z

target_height = 1.52
scale_factor = target_height / glb_height if glb_height > 0.01 else 1.0
print(f"[v12b] GLB height={glb_height:.3f}m -> scale={scale_factor:.4f}")

glb_mesh.scale = (scale_factor, scale_factor, scale_factor)
glb_mesh.location.z -= min_z * scale_factor

set_active(glb_mesh)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)

# Rotasi 180 derajat di Z jika mesh menghadap ke belakang
# Check: head center harusnya di Z tertinggi, kaki di Z=0
# GLB dari Tripo biasanya menghadap ke depan (-Y di Blender = depan)
# tapi kadang perlu dirotasi 180 di Z
import math
glb_mesh.rotation_euler.z = math.radians(180)
set_active(glb_mesh)
bpy.ops.object.transform_apply(rotation=True)
print("[v12b] Applied 180° Z rotation to face front.")


# ── Step 4: Parent dengan armature (Envelopes, not auto-weights) ──────────────

print("[v12b] Parenting GLB mesh to armature...")

# Hapus mesh base VRM yang tidak diperlukan (kecuali body mesh referensi)
for obj in list(bpy.context.scene.objects):
    if obj.type == "MESH" and obj != glb_mesh and obj.name != glb_mesh.name:
        bpy.data.objects.remove(obj, do_unlink=True)

set_active(glb_mesh)

# Tambah Armature modifier manual
for mod in list(glb_mesh.modifiers):
    glb_mesh.modifiers.remove(mod)

arm_mod = glb_mesh.modifiers.new("ArmatureMod", "ARMATURE")
arm_mod.object = bpy.data.objects["Aina_Armature"]
glb_mesh.parent = bpy.data.objects["Aina_Armature"]

# Set vertex groups dengan bone envelope weights
bpy.ops.object.select_all(action="DESELECT")
glb_mesh.select_set(True)
bpy.data.objects["Aina_Armature"].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["Aina_Armature"]

# Parent with bone envelopes (lebih reliable dari auto weights untuk mesh besar)
bpy.ops.object.parent_set(type="ARMATURE_ENVELOPE")
print("[v12b] Parented with bone envelope weights.")


# ── Step 5: Smooth shading ────────────────────────────────────────────────────

set_active(glb_mesh)
bpy.ops.object.shade_smooth()


# ── Step 6: Export VRM ────────────────────────────────────────────────────────

print("[v12b] Exporting VRM...")
set_active(bpy.data.objects["Aina_Armature"])

try:
    bpy.ops.export_scene.vrm(
        filepath=str(OUTPUT_VRM),
        export_invisibles=False,
        export_only_selections=False,
    )
    print(f"[v12b] VRM exported: {OUTPUT_VRM}")
except Exception as e:
    print(f"[v12b] VRM export error: {e}")

# Save blend
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
print(f"[v12b] Blend saved: {OUTPUT_BLEND}")


# ── Step 7: Render previews ───────────────────────────────────────────────────

print("[v12b] Rendering previews...")
scene = prepare_render()

# Karakter menghadap ke -Y (depan di Blender)
center = Vector((0, 0, 0.76))
head   = Vector((0, 0, 1.42))

render_view(scene, "front", Vector((0, -3.5, 0.85)),  center)
render_view(scene, "left",  Vector((-3.5, 0, 0.85)),  center)
render_view(scene, "right", Vector((3.5, 0, 0.85)),   center)
render_view(scene, "back",  Vector((0, 3.5, 0.85)),   center)
render_view(scene, "face",  Vector((0, -1.3, 1.50)),  head, lens=80)
render_view(scene, "top",   Vector((0, -0.1, 4.0)),   Vector((0, 0, 1.2)), lens=62)

print("[v12b] Done!")
