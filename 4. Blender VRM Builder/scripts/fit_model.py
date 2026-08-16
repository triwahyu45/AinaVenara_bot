from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

from image_metrics import measure, save_contact_sheet, save_edge_diff, save_metrics, save_overlay


VIEW_MAP = {
    "front": "01_full_body_front.png",
    "back": "02_full_body_back.png",
    "left": "03_full_body_left.png",
    "right": "04_full_body_right.png",
    "front_left_3q": "05_full_body_front_left_3q.png",
    "front_right_3q": "06_full_body_front_right_3q.png",
    "face_front": "13_head_front.png",
    "head_top": "19_head_top.png",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", required=True)
    parser.add_argument("--reference-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--blender", default=r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe")
    parser.add_argument("--iterations", type=int, default=12)
    parser.add_argument("--resolution", type=int, default=512)
    parser.add_argument("--analysis-only", action="store_true")
    parser.add_argument("--skip-export", action="store_true")
    return parser.parse_args()


def average(metrics):
    keys = ("silhouette_iou", "edge_overlap", "landmark_error", "rgb_error", "score")
    return {key: sum(item[key] for item in metrics.values()) / len(metrics) for key in keys}


def render_views(args, params_path, render_dir):
    if args.analysis_only:
        return
    script = Path(__file__).with_name("render_fit_views.py")
    command = [
        args.blender,
        "--background",
        args.blend,
        "--python",
        str(script),
        "--",
        "--output",
        str(render_dir),
        "--params",
        str(params_path),
        "--resolution",
        str(args.resolution),
    ]
    subprocess.run(command, check=True)
    missing = [view for view in VIEW_MAP if not (render_dir / f"{view}.png").is_file()]
    if missing:
        raise RuntimeError("Blender render tidak menghasilkan view: " + ", ".join(missing))


def diagnostics(reference_root, render_dir, iteration_dir):
    metrics = {}
    overlay_images = []
    for view, reference_name in VIEW_MAP.items():
        reference = reference_root / reference_name
        render = render_dir / f"{view}.png"
        overlay = iteration_dir / f"{view}_overlay.png"
        diff = iteration_dir / f"{view}_edge_diff.png"
        metrics[view] = measure(reference, render)
        save_overlay(reference, render, overlay)
        save_edge_diff(reference, render, diff)
        overlay_images.append((view, overlay))
    summary = average(metrics)
    result = {"views": metrics, "summary": summary}
    save_metrics(result, iteration_dir / "metrics.json")
    save_contact_sheet(overlay_images, iteration_dir / "overlay_contact_sheet.png")
    return result


def clamp(value, bounds):
    return max(bounds[0], min(bounds[1], value))


def update_params(params, bounds, metrics, step):
    updated = deepcopy(params)
    front = metrics["views"]["front"]
    side = metrics["views"]["left"]
    back = metrics["views"]["back"]
    updated["body_width"] *= max(0.97, min(1.03, front["bbox_width_ratio"]))
    updated["body_height"] *= max(0.97, min(1.03, front["bbox_height_ratio"]))
    updated["body_depth"] *= max(0.98, min(1.02, side["bbox_width_ratio"]))
    # Bounded coordinate descent heuristic: correct broad silhouette first.
    if front["silhouette_iou"] < 0.90:
        updated["hoodie_width"] += step if front["landmark_error"] > 0.02 else -step / 2
        updated["hair_scale"] += step / 2 if back["edge_overlap"] < 0.85 else 0
    if side["silhouette_iou"] < 0.90:
        updated["hoodie_depth"] += step / 2
        updated["head_depth"] += step / 4
    if front["edge_overlap"] < 0.85:
        updated["bang_scale"] += step / 3
        updated["ahoge_scale"] += step / 4
    if front["rgb_error"] > 0.16:
        updated["glasses_scale"] += step / 5
        updated["hairclip_scale"] += step / 5
    for key in updated:
        updated[key] = round(clamp(updated[key], bounds[key]), 5)
    return updated


def accepted(summary):
    return (
        summary["silhouette_iou"] >= 0.90
        and summary["edge_overlap"] >= 0.85
        and summary["landmark_error"] <= 0.03
        and summary["rgb_error"] <= 0.16
    )


def export_candidate(args, output, params_path):
    if args.analysis_only or args.skip_export:
        return
    script = Path(__file__).with_name("export_fit_candidate.py")
    validator = Path(__file__).with_name("validate_output.py")
    candidate_dir = output / "candidate"
    candidate_blend = candidate_dir / "Aina_Venara_fitted.blend"
    candidate_vrm = candidate_dir / "Aina_Venara_fitted.vrm"
    stamp = candidate_dir / "validation.ok"
    subprocess.run(
        [
            args.blender,
            "--background",
            args.blend,
            "--python",
            str(script),
            "--",
            "--params",
            str(params_path),
            "--blend",
            str(candidate_blend),
            "--vrm",
            str(candidate_vrm),
        ],
        check=True,
    )
    if not candidate_blend.is_file() or not candidate_vrm.is_file() or candidate_vrm.stat().st_size == 0:
        raise RuntimeError("Blender tidak menghasilkan fitted blend atau VRM kandidat.")
    subprocess.run(
        [
            args.blender,
            "--background",
            "--python",
            str(validator),
            "--",
            "--input",
            str(candidate_vrm),
            "--stamp",
            str(stamp),
        ],
        check=True,
    )
    if not stamp.is_file():
        raise RuntimeError("Validator re-import VRM tidak menghasilkan validation stamp.")


def main():
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    reference_root = Path(args.reference_root).resolve()
    params = manifest["parameters"]
    bounds = manifest["bounds"]
    best = None
    for index in range(args.iterations):
        iteration_dir = output / f"iter_{index:02d}"
        render_dir = iteration_dir / "render"
        render_dir.mkdir(parents=True, exist_ok=True)
        params_path = iteration_dir / "params.json"
        params_path.write_text(json.dumps(params, indent=2), encoding="utf-8")
        render_views(args, params_path, render_dir)
        metrics = diagnostics(reference_root, render_dir, iteration_dir)
        score = metrics["summary"]["score"]
        if not best or score > best["score"]:
            best = {"iteration": index, "score": score, "params": deepcopy(params), "metrics": metrics["summary"]}
        if accepted(metrics["summary"]):
            break
        params = update_params(params, bounds, metrics, max(0.012, 0.055 * (1 - index / max(args.iterations, 1))))
    (output / "best_candidate.json").write_text(json.dumps(best, indent=2), encoding="utf-8")
    source = output / f"iter_{best['iteration']:02d}"
    target = output / "best"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    export_candidate(args, output, target / "params.json")
    print(json.dumps(best, indent=2))


if __name__ == "__main__":
    main()
