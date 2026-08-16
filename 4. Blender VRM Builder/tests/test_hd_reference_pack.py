import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).parents[1]
REFERENCES = ROOT.parent / "2. Aina Venara Model" / "Reff 3D HD Generated Individual"


def test_reference_manifest_has_exactly_50_individual_images():
    manifest = json.loads((REFERENCES / "reference_manifest.json").read_text(encoding="utf-8"))
    items = manifest["references"]
    names = {item["file"] for item in items}
    assert manifest["schema_version"] == 2
    assert len(items) == 50
    assert len(names) == 50
    assert "10_full_body_t_pose.png" in names
    assert "11_full_body_relaxed_apose.png" in names
    assert sum(item["use_for_scoring"] for item in items) == 8
    assert {item["file"] for item in items if item["use_for_scoring"]} == {
        "01_full_body_front.png",
        "02_full_body_back.png",
        "03_full_body_left.png",
        "04_full_body_right.png",
        "05_full_body_front_left_3q.png",
        "06_full_body_front_right_3q.png",
        "13_head_front.png",
        "19_head_top.png",
    }


def test_reference_images_exist_and_are_2048_square():
    manifest = json.loads((REFERENCES / "reference_manifest.json").read_text(encoding="utf-8"))
    for item in manifest["references"]:
        with Image.open(REFERENCES / item["file"]) as image:
            assert image.size == (2048, 2048)


def test_reference_images_are_not_byte_duplicates():
    files = sorted(REFERENCES.glob("*.png"))
    hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in files]
    assert len(hashes) == len(set(hashes))
