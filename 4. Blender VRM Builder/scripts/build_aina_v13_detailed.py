import sys
import math
from pathlib import Path

import bpy
from mathutils import Vector, Matrix

# Paths
BASE_VRM = Path(str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/VRM Draft/Aina_Venara_Base.vrm"))
GLB_SOURCE = Path(str(Path(__file__).resolve().parents[2] / "2. Aina Venara Model/Trip AI Export/Aina+Venara.glb"))
OUTPUT_VRM = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/Aina_Venara_v13.vrm"))
OUTPUT_BLEND = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/Aina_Venara_v13.blend"))
PREVIEW_DIR = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/previews/v13"))

OUTPUT_VRM.parent.mkdir(parents=True, exist_ok=True)
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

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

def hex_color(value: str) -> tuple[float, float, float, float]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) / 255 for index in (0, 2, 4)) + (1.0,)

def material(name: str, color: str, *, metallic=0.0, roughness=0.55) -> bpy.types.Material:
    found = bpy.data.materials.get(name)
    if found:
        found.diffuse_color = hex_color(color)
        found.metallic = metallic
        found.roughness = roughness
        return found
    found = bpy.data.materials.new(name)
    found.diffuse_color = hex_color(color)
    found.metallic = metallic
    found.roughness = roughness
    return found

def bone(rig: bpy.types.Object, *candidates: str) -> bpy.types.Bone:
    by_name = {item.name.lower(): item for item in rig.data.bones}
    for candidate in candidates:
        if candidate.lower() in by_name:
            return by_name[candidate.lower()]
    for item in rig.data.bones:
        if any(candidate.lower() in item.name.lower() for candidate in candidates):
            return item
    raise ValueError(f"Bone tidak ditemukan di armature. Kandidat: {candidates}")

def bone_world(rig: bpy.types.Object, *candidates: str) -> Vector:
    return rig.matrix_world @ bone(rig, *candidates).head_local

def parent_bone(obj: bpy.types.Object, rig: bpy.types.Object, *candidates: str) -> None:
    target = bone(rig, *candidates)
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = target.name
    obj.matrix_world = world

def apply_material(obj: bpy.types.Object, mat: bpy.types.Material) -> bpy.types.Object:
    obj.data.materials.append(mat)
    return obj

def add_tube(name: str, points, radius: float, mat, rig, *target_bone, cyclic=False, radii=None) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for index, (item, coordinate) in enumerate(zip(spline.points, points)):
        item.co = (*coordinate, 1.0)
        if radii:
            item.radius = radii[index]
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name
    apply_material(obj, mat)
    parent_bone(obj, rig, *target_bone)
    return obj

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
    for loc, energy, size in (((-2.5, 3, 3), 500, 4), ((2, 1, 1.5), 250, 3), ((0, -2, 2.5), 350, 3)):
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

# STEP 1: Import Base VRM for armature
print("[v13] Clearing scene...")
clear_scene()

print("[v13] Importing Base VRM for armature...")
bpy.ops.import_scene.vrm(filepath=str(BASE_VRM))

base_armature = None
for obj in list(bpy.context.scene.objects):
    if obj.type == "ARMATURE":
        base_armature = obj
        break

if base_armature is None:
    raise RuntimeError("Armature tidak ditemukan di Base VRM!")

base_armature.name = "Aina_Armature"
print(f"[v13] Armature loaded: {base_armature.name}")

# STEP 2: Import Trip AI GLB
print("[v13] Importing Trip AI GLB...")
bpy.ops.import_scene.gltf(filepath=str(GLB_SOURCE))

glb_mesh = None
for obj in bpy.context.scene.objects:
    if obj.type == "MESH" and "tripo" in obj.name:
        glb_mesh = obj
        break

if glb_mesh is None:
    raise RuntimeError("Mesh GLB tidak ditemukan!")

print(f"[v13] GLB mesh found: {glb_mesh.name}")
glb_mesh.name = "Aina_Body_GLB"

# STEP 3: Scale & Orient GLB
print("[v13] Scaling GLB mesh...")
set_active(glb_mesh)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

verts_world = [glb_mesh.matrix_world @ v.co for v in glb_mesh.data.vertices]
min_z = min(v.z for v in verts_world)
max_z = max(v.z for v in verts_world)
glb_height = max_z - min_z

target_height = 1.52
scale_factor = target_height / glb_height if glb_height > 0.01 else 1.0
print(f"[v13] Scale: height={glb_height:.3f}m -> scale={scale_factor:.4f}")

glb_mesh.scale = (scale_factor, scale_factor, scale_factor)
glb_mesh.location.z -= min_z * scale_factor

set_active(glb_mesh)
glb_mesh.rotation_euler.z = 0
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# STEP 4: Clean old meshes
print("[v13] Cleaning old meshes from Base VRM...")
for obj in list(bpy.context.scene.objects):
    if obj.type == "MESH" and obj != glb_mesh:
        bpy.data.objects.remove(obj, do_unlink=True)

# STEP 5: Parent armature
print("[v13] Parenting GLB body mesh...")
set_active(glb_mesh)
for mod in list(glb_mesh.modifiers):
    glb_mesh.modifiers.remove(mod)

arm_mod = glb_mesh.modifiers.new("ArmatureMod", "ARMATURE")
arm_mod.object = base_armature
glb_mesh.parent = base_armature

set_active(glb_mesh)
base_armature.select_set(True)
bpy.context.view_layer.objects.active = base_armature
bpy.ops.object.parent_set(type="ARMATURE_ENVELOPE")
print("[v13] Parented body mesh with envelope weights.")

# STEP 6: Generate accessories
print("[v13] Generating canonical accessories...")

pink = material("Aina_Mat_GlassesPink", "#F5A4C8", roughness=0.3)
silver = material("Aina_Mat_HairclipSilver", "#E6E9EE", metallic=0.9, roughness=0.15)
cyan = material("Aina_Mat_AhogeCyan", "#7ED8F2", roughness=0.5)

head_loc = bone_world(base_armature, "head")
print(f"[v13] Head bone world position: {head_loc}")

def map_coords(vec_offset: Vector) -> Vector:
    return Vector((-vec_offset.y, vec_offset.x, vec_offset.z))

for side in (-1, 1):
    cx = side * 0.047
    points = [
        head_loc + map_coords(Vector((cx + math.cos(step * math.tau / 16) * 0.034, -0.174, 0.035 + math.sin(step * math.tau / 16) * 0.027)))
        for step in range(16)
    ]
    add_tube(f"Aina_Glasses_{'L' if side < 0 else 'R'}", points, 0.002, pink, base_armature, "head", cyclic=True)

add_tube("Aina_Glasses_Bridge", (
    head_loc + map_coords(Vector((-0.012, -0.176, 0.04))),
    head_loc + map_coords(Vector((0.012, -0.176, 0.04)))
), 0.002, pink, base_armature, "head")

for side in (-1, 1):
    add_tube(
        f"Aina_Glasses_Temple_{'L' if side < 0 else 'R'}",
        (
            head_loc + map_coords(Vector((side * 0.083, -0.166, 0.04))),
            head_loc + map_coords(Vector((side * 0.138, -0.125, 0.04))),
            head_loc + map_coords(Vector((side * 0.142, -0.035, 0.032))),
        ),
        0.0015,
        pink,
        base_armature,
        "head",
    )
print("[v13] Canonical glasses created.")

clip_points = (
    head_loc + map_coords(Vector((0.08, -0.155, 0.11))),
    head_loc + map_coords(Vector((0.10, -0.155, 0.11))),
    head_loc + map_coords(Vector((0.105, -0.155, 0.095))),
    head_loc + map_coords(Vector((0.095, -0.155, 0.08))),
    head_loc + map_coords(Vector((0.085, -0.155, 0.08))),
    head_loc + map_coords(Vector((0.095, -0.155, 0.08))),
    head_loc + map_coords(Vector((0.105, -0.155, 0.065))),
    head_loc + map_coords(Vector((0.10, -0.155, 0.05))),
    head_loc + map_coords(Vector((0.08, -0.155, 0.05))),
)
add_tube("Aina_Hairclip_Number_3", clip_points, 0.0035, silver, base_armature, "head")
print("[v13] Silver number-3 hairclip created.")

ahoge_points = (
    head_loc + map_coords(Vector((0.0, 0.0, 0.235))),
    head_loc + map_coords(Vector((0.015, -0.01, 0.265))),
    head_loc + map_coords(Vector((-0.015, -0.015, 0.295))),
    head_loc + map_coords(Vector((0.02, -0.018, 0.325))),
)
add_tube("Aina_Ahoge", ahoge_points, 0.005, cyan, base_armature, "head", radii=(0.85, 1.0, 0.8, 0.18))
print("[v13] Zigzag ahoge created.")

# STEP 7: Export VRM & Blend
print("[v13] Exporting detailed VRM...")
set_active(base_armature)

try:
    bpy.ops.export_scene.vrm(
        filepath=str(OUTPUT_VRM),
        export_invisibles=False,
        export_only_selections=False,
    )
    print(f"[v13] VRM exported: {OUTPUT_VRM}")
except Exception as e:
    print(f"[v13] VRM export error: {e}")

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
print(f"[v13] Blend saved: {OUTPUT_BLEND}")

# STEP 8: Render Previews
print("[v13] Rendering previews...")
scene = prepare_render()

center = Vector((0, 0, 0.76))
head_target = Vector((0, 0, 1.42))

views = [
    ("front", Vector((3.5, 0, 0.85)),   center, 58),
    ("left",  Vector((0, 3.5, 0.85)),   center, 58),
    ("right", Vector((0, -3.5, 0.85)),  center, 58),
    ("back",  Vector((-3.5, 0, 0.85)),  center, 58),
    ("face",  Vector((1.3, 0, 1.48)),   head_target, 80),
    ("top",   Vector((0.1, 0, 4.0)),    Vector((0, 0, 1.2)), 62),
]

for name, cam_loc, target, lens in views:
    scene.camera.location = cam_loc
    scene.camera.data.lens = lens
    look_at(scene.camera, target)
    scene.render.filepath = str(PREVIEW_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {name}")

print("[v13] All processes completed!")
