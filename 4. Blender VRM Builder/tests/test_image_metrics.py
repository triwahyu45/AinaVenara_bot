import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from image_metrics import measure, save_contact_sheet, save_edge_diff, save_overlay  # noqa: E402


def fixture(path: Path, offset: int = 0):
    image = Image.new("RGB", (256, 256), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((70 + offset, 35, 185 + offset, 225), fill=(126, 216, 242))
    image.save(path)


def test_identical_images_score_better_than_shifted_images(tmp_path):
    reference = tmp_path / "reference.png"
    same = tmp_path / "same.png"
    shifted = tmp_path / "shifted.png"
    fixture(reference)
    fixture(same)
    fixture(shifted, 24)
    assert measure(reference, same)["score"] > measure(reference, shifted)["score"]


def test_overlay_and_edge_diff_are_written(tmp_path):
    reference = tmp_path / "reference.png"
    shifted = tmp_path / "shifted.png"
    overlay = tmp_path / "overlay.png"
    diff = tmp_path / "edge_diff.png"
    fixture(reference)
    fixture(shifted, 12)
    save_overlay(reference, shifted, overlay)
    save_edge_diff(reference, shifted, diff)
    assert overlay.is_file()
    assert diff.is_file()


def test_contact_sheet_keeps_all_scoring_views(tmp_path):
    images = []
    for index in range(8):
        path = tmp_path / f"view_{index}.png"
        fixture(path, index)
        images.append((f"view_{index}", path))
    output = tmp_path / "contact_sheet.png"
    save_contact_sheet(images, output)
    with Image.open(output) as image:
        assert image.size == (1600, 840)


def test_fit_manifest_has_bounded_face_parameters():
    manifest = json.loads((ROOT / "fit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["iterations"] == 12
    for key in ("head_width", "head_depth", "head_height"):
        low, high = manifest["bounds"][key]
        assert 0.9 <= low < 1.0 < high <= 1.1
    for key in ("body_width", "body_depth", "body_height"):
        assert key in manifest["bounds"]
