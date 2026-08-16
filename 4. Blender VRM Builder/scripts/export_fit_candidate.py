from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_fit_views import apply_params


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", required=True)
    parser.add_argument("--blend", required=True)
    parser.add_argument("--vrm", required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def main():
    args = parse_args()
    params = json.loads(Path(args.params).read_text(encoding="utf-8"))
    apply_params(params)
    blend = Path(args.blend).resolve()
    vrm = Path(args.vrm).resolve()
    blend.parent.mkdir(parents=True, exist_ok=True)
    vrm.parent.mkdir(parents=True, exist_ok=True)
    if not hasattr(bpy.ops.export_scene, "vrm"):
        raise RuntimeError("VRM Add-on belum aktif. Jalankan setup_vrm_addon.ps1 dahulu.")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.vrm(filepath=str(vrm))
    print(f"Fitted candidate blend: {blend}")
    print(f"Fitted candidate VRM: {vrm}")


if __name__ == "__main__":
    main()
