from pathlib import Path
"""
test_import.py - test importing the VRM/VRoid base
"""
import bpy, os, sys

VRM_PATH = str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/assets/akari_base.vrm")
print(f"File exists: {os.path.exists(VRM_PATH)}")
print(f"File size: {os.path.getsize(VRM_PATH) if os.path.exists(VRM_PATH) else 'N/A'}")

# Check operator poll
print(f"Has import_scene.vrm: {hasattr(bpy.ops.import_scene, 'vrm')}")

# Try VRM import using the VRM operator properly
try:
    bpy.ops.import_scene.vrm(
        filepath=VRM_PATH,
    )
    print("VRM import succeeded")
except Exception as e:
    print(f"VRM import exception: {e}")

print("Objects after import:")
for o in bpy.data.objects:
    print(f"  {o.name} - {o.type}")
