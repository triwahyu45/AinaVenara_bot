from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def open_rgb(path: str | Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    white = Image.new("RGBA", image.size, (255, 255, 255, 255))
    return Image.alpha_composite(white, image).convert("RGB")


def load_rgb(path: str | Path, size: tuple[int, int] | None = None) -> np.ndarray:
    image = open_rgb(path)
    if size and image.size != size:
        image = image.resize(size, Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.uint8)


def foreground_mask(rgb: np.ndarray, white_threshold: int = 245) -> np.ndarray:
    return np.any(rgb < white_threshold, axis=2)


def edge_mask(mask: np.ndarray) -> np.ndarray:
    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    neighbors = [
        padded[0:-2, 1:-1],
        padded[2:, 1:-1],
        padded[1:-1, 0:-2],
        padded[1:-1, 2:],
    ]
    eroded = mask.copy()
    for neighbor in neighbors:
        eroded &= neighbor
    return mask ^ eroded


def bounding_box(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return 0, 0, mask.shape[1], mask.shape[0]
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def silhouette_iou(reference: np.ndarray, render: np.ndarray) -> float:
    union = np.logical_or(reference, render).sum()
    return float(np.logical_and(reference, render).sum() / union) if union else 1.0


def edge_overlap(reference: np.ndarray, render: np.ndarray) -> float:
    ref_edge = edge_mask(reference)
    render_edge = edge_mask(render)
    # One-pixel tolerance keeps anti-aliasing from dominating the score.
    padded = np.pad(render_edge, 1, mode="constant", constant_values=False)
    dilated = np.zeros_like(render_edge)
    for y in range(3):
        for x in range(3):
            dilated |= padded[y : y + render_edge.shape[0], x : x + render_edge.shape[1]]
    denominator = ref_edge.sum()
    return float(np.logical_and(ref_edge, dilated).sum() / denominator) if denominator else 1.0


def landmark_error(reference: np.ndarray, render: np.ndarray) -> float:
    ref = bounding_box(reference)
    got = bounding_box(render)
    height, width = reference.shape
    ref_points = np.array(((ref[0], ref[1]), (ref[2], ref[3]), ((ref[0] + ref[2]) / 2, (ref[1] + ref[3]) / 2)))
    got_points = np.array(((got[0], got[1]), (got[2], got[3]), ((got[0] + got[2]) / 2, (got[1] + got[3]) / 2)))
    return float(np.linalg.norm(ref_points - got_points, axis=1).mean() / max(width, height))


def masked_rgb_error(reference_rgb: np.ndarray, render_rgb: np.ndarray) -> float:
    reference = Image.fromarray(reference_rgb)
    render = Image.fromarray(render_rgb)
    errors = []
    for size in (256, 128, 64):
        ref = np.asarray(reference.resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32)
        got = np.asarray(render.resize((size, size), Image.Resampling.BILINEAR), dtype=np.float32)
        mask = np.logical_or(foreground_mask(ref), foreground_mask(got))
        if mask.any():
            errors.append(float(np.abs(ref - got)[mask].mean() / 255.0))
    return float(np.mean(errors)) if errors else 0.0


def measure(reference_path: str | Path, render_path: str | Path) -> dict[str, float]:
    reference = load_rgb(reference_path, (512, 512))
    render = load_rgb(render_path, (512, 512))
    ref_mask = foreground_mask(reference)
    render_mask = foreground_mask(render)
    ref_box = bounding_box(ref_mask)
    render_box = bounding_box(render_mask)
    ref_width = max(1, ref_box[2] - ref_box[0])
    ref_height = max(1, ref_box[3] - ref_box[1])
    render_width = max(1, render_box[2] - render_box[0])
    render_height = max(1, render_box[3] - render_box[1])
    metrics = {
        "silhouette_iou": silhouette_iou(ref_mask, render_mask),
        "edge_overlap": edge_overlap(ref_mask, render_mask),
        "landmark_error": landmark_error(ref_mask, render_mask),
        "rgb_error": masked_rgb_error(reference, render),
        "bbox_width_ratio": ref_width / render_width,
        "bbox_height_ratio": ref_height / render_height,
    }
    metrics["score"] = (
        metrics["silhouette_iou"] * 0.42
        + metrics["edge_overlap"] * 0.28
        + (1.0 - metrics["landmark_error"]) * 0.15
        + (1.0 - metrics["rgb_error"]) * 0.15
    )
    return metrics


def save_overlay(reference_path: str | Path, render_path: str | Path, output: str | Path) -> None:
    reference = open_rgb(reference_path).resize((1024, 1024), Image.Resampling.LANCZOS)
    render = open_rgb(render_path).resize((1024, 1024), Image.Resampling.LANCZOS)
    Image.blend(reference, render, 0.5).save(output)


def save_edge_diff(reference_path: str | Path, render_path: str | Path, output: str | Path) -> None:
    reference = load_rgb(reference_path, (1024, 1024))
    render = load_rgb(render_path, (1024, 1024))
    ref_edge = edge_mask(foreground_mask(reference))
    got_edge = edge_mask(foreground_mask(render))
    canvas = np.full((1024, 1024, 3), 255, dtype=np.uint8)
    canvas[ref_edge] = (235, 72, 92)
    canvas[got_edge] = (48, 178, 120)
    canvas[np.logical_and(ref_edge, got_edge)] = (35, 60, 80)
    Image.fromarray(canvas).save(output)


def save_contact_sheet(images: list[tuple[str, Path]], output: str | Path) -> None:
    thumb = (380, 380)
    columns = min(4, max(1, len(images)))
    rows = (len(images) + columns - 1) // columns
    canvas = Image.new("RGB", (20 + columns * 395, 20 + rows * 410), "white")
    draw = ImageDraw.Draw(canvas)
    for index, (label, path) in enumerate(images):
        x = 20 + (index % columns) * 395
        y = 20 + (index // columns) * 410
        image = Image.open(path).convert("RGB")
        image.thumbnail(thumb, Image.Resampling.LANCZOS)
        canvas.paste(image, (x + (thumb[0] - image.width) // 2, y))
        draw.text((x, y + 382), label, fill=(25, 32, 42))
    canvas.save(output)


def save_metrics(metrics: dict, output: str | Path) -> None:
    Path(output).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
