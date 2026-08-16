"""
build_aina_v12_glb_retarget.py
Strategi baru: Ambil mesh berkualitas tinggi dari Aina+Venara.glb (Trip AI),
gabungkan dengan armature humanoid dari Aina_Venara_Base.vrm,
lalu export sebagai VRM v12.

Langkah:
1. Import Base.vrm -> ambil armature + face mesh (bola mata/bibir/kulit)
2. Import Aina+Venara.glb -> ambil semua mesh berkualitas tinggi
3. Transfer bone weights dari Base.vrm ke semua mesh GLB
4. Export sebagai VRM.
"""

import sys
from pathlib import Path

import bpy
from mathutils import Vector, Matrix

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
            block.remove(item)


def set_active(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)


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
    for loc, energy, size in (((-2.5, -3, 3), 400, 4), ((2, -1, 1.5), 200, 3), ((0, 2, 2.5), 300, 3)):
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


# ── Step 1: Import Base VRM untuk ambil armature ─────────────────────────────

print("[v12] Clearing scene...")
clear_scene()

print("[v12] Importing Base VRM for armature...")
bpy.ops.import_scene.vrm(filepath=str(BASE_VRM))

# Ambil armature dari Base VRM
base_armature = None
base_meshes = []
for obj in bpy.context.scene.objects:
    if obj.type == "ARMATURE":
        base_armature = obj
    elif obj.type == "MESH":
        base_meshes.append(obj)

if base_armature is None:
    raise RuntimeError("Tidak ditemukan armature di Base VRM!")

print(f"[v12] Armature ditemukan: {base_armature.name}")
print(f"[v12] Bones: {[b.name for b in base_armature.data.bones[:10]]}...")

# Hapus semua mesh dari base VRM (kita pakai mesh dari GLB)
for mesh_obj in base_meshes:
    bpy.data.objects.remove(mesh_obj, do_unlink=True)

print("[v12] Base meshes removed, armature kept.")


# ── Step 2: Import GLB dan scale/posisikan ───────────────────────────────────

print("[v12] Importing Trip AI GLB...")
bpy.ops.import_scene.gltf(filepath=str(GLB_SOURCE))

# Kumpulkan semua mesh yang baru diimport (bukan armature)
glb_meshes = [obj for obj in bpy.context.scene.objects
              if obj.type == "MESH" and obj not in base_meshes]

print(f"[v12] GLB meshes: {[m.name for m in glb_meshes]}")

# Cari bounding box karakter GLB untuk menentukan scale
all_verts = []
for mesh_obj in glb_meshes:
    mat = mesh_obj.matrix_world
    for v in mesh_obj.data.vertices:
        all_verts.append(mat @ v.co)

if all_verts:
    min_z = min(v.z for v in all_verts)
    max_z = max(v.z for v in all_verts)
    glb_height = max_z - min_z
    print(f"[v12] GLB height: {glb_height:.3f}m, min_z={min_z:.3f}, max_z={max_z:.3f}")

    # Target: karakter VRoid standar ~1.52m
    target_height = 1.52
    scale_factor = target_height / glb_height if glb_height > 0.01 else 1.0
    print(f"[v12] Scale factor: {scale_factor:.4f}")

    # Scale dan posisikan semua mesh GLB
    for mesh_obj in glb_meshes:
        mesh_obj.scale = (scale_factor, scale_factor, scale_factor)
        # Ground model at z=0
        mesh_obj.location.z -= min_z * scale_factor
        bpy.ops.object.select_all(action="DESELECT")
        mesh_obj.select_set(True)
        bpy.context.view_layer.objects.active = mesh_obj
        bpy.ops.object.transform_apply(scale=True, location=True, rotation=False)

print("[v12] GLB meshes scaled to VRM standard height.")


# ── Step 3: Join semua mesh GLB menjadi satu ─────────────────────────────────

print("[v12] Joining GLB meshes...")
bpy.ops.object.select_all(action="DESELECT")
for mesh_obj in glb_meshes:
    mesh_obj.select_set(True)

if glb_meshes:
    bpy.context.view_layer.objects.active = glb_meshes[0]
    bpy.ops.object.join()
    combined_mesh = bpy.context.view_layer.objects.active
    combined_mesh.name = "Aina_Body_Combined"
    print(f"[v12] Combined mesh: {combined_mesh.name}")
else:
    raise RuntimeError("Tidak ada mesh dari GLB!")


# ── Step 4: Assign armature modifier + automatic weight paint ─────────────────

print("[v12] Assigning armature modifier to GLB mesh...")
bpy.ops.object.select_all(action="DESELECT")
combined_mesh.select_set(True)
bpy.context.view_layer.objects.active = combined_mesh

# Tambah Armature modifier
arm_mod = combined_mesh.modifiers.new("Armature", "ARMATURE")
arm_mod.object = base_armature

# Parent mesh ke armature dengan automatic weights
bpy.ops.object.select_all(action="DESELECT")
combined_mesh.select_set(True)
base_armature.select_set(True)
bpy.context.view_layer.objects.active = base_armature

bpy.ops.object.parent_set(type="ARMATURE_AUTO")
print("[v12] Automatic bone weights assigned.")


# ── Step 5: Smooth normals ────────────────────────────────────────────────────

bpy.ops.object.select_all(action="DESELECT")
combined_mesh.select_set(True)
bpy.context.view_layer.objects.active = combined_mesh
bpy.ops.object.shade_smooth()
print("[v12] Smooth shading applied.")


# ── Step 6: Export VRM ────────────────────────────────────────────────────────

print("[v12] Exporting VRM...")
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = base_armature

bpy.ops.export_scene.vrm(
    filepath=str(OUTPUT_VRM),
    export_invisibles=False,
    export_only_selections=False,
)
print(f"[v12] VRM exported to: {OUTPUT_VRM}")

# Save blend file
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
print(f"[v12] Blend saved to: {OUTPUT_BLEND}")


# ── Step 7: Render previews ───────────────────────────────────────────────────

print("[v12] Rendering previews...")
scene = prepare_render()
center = Vector((0, 0, 0.76))
render_view(scene, "front", Vector((0, -4.2, 0.85)), center)
render_view(scene, "left",  Vector((-4.2, 0, 0.85)), center)
render_view(scene, "right", Vector((4.2, 0, 0.85)), center)
render_view(scene, "back",  Vector((0, 4.2, 0.85)), center)
render_view(scene, "face",  Vector((0, -1.55, 1.42)), Vector((0, 0, 1.42)), lens=72)
render_view(scene, "top",   Vector((0, -0.15, 4.4)), Vector((0, 0, 1.25)), lens=62)

print("[v12] Done! Aina Venara v12 build complete.")
