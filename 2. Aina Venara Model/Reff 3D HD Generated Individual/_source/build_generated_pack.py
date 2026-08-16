from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "_source" / "generated"
REJECTED = ROOT / "_source" / "rejected"
QA = ROOT / "_source" / "qa"
SIZE = 2048
WHITE = (255, 255, 255)


@dataclass(frozen=True)
class Plate:
    file: str
    category: str
    view: str
    purpose: str
    camera: str = ""
    use_for_scoring: bool = False


def plate(file: str, category: str, view: str, purpose: str, camera: str = "", score: bool = False) -> Plate:
    return Plate(file, category, view, purpose, camera, score)


PLATES = [
    plate("01_full_body_front.png", "full-body", "front", "Primary silhouette fitting", "body_front", True),
    plate("02_full_body_back.png", "full-body", "back", "Back silhouette fitting", "body_back", True),
    plate("03_full_body_left.png", "full-body", "left", "Left silhouette fitting", "body_left", True),
    plate("04_full_body_right.png", "full-body", "right", "Right silhouette fitting", "body_right", True),
    plate("05_full_body_front_left_3q.png", "full-body", "front-left-3q", "Front-left depth fitting", "body_front_left_3q", True),
    plate("06_full_body_front_right_3q.png", "full-body", "front-right-3q", "Front-right depth fitting", "body_front_right_3q", True),
    plate("07_full_body_back_left_3q.png", "full-body", "back-left-3q", "Back-left volume guide"),
    plate("08_full_body_back_right_3q.png", "full-body", "back-right-3q", "Back-right volume guide"),
    plate("09_full_body_top.png", "full-body", "top", "Top footprint guide"),
    plate("10_full_body_t_pose.png", "full-body", "t-pose", "Humanoid bone placement and skinning guide"),
    plate("11_full_body_relaxed_apose.png", "full-body", "relaxed-a-pose", "Rig baseline guide"),
    plate("12_full_body_garment_silhouette.png", "full-body", "garment-silhouette", "Oversized garment silhouette guide"),
    plate("13_head_front.png", "head-face", "front", "Face fitting", "face_front", True),
    plate("14_head_back.png", "head-face", "back", "Back bob close-up"),
    plate("15_head_left.png", "head-face", "left", "Left profile guide"),
    plate("16_head_right.png", "head-face", "right", "Right profile guide"),
    plate("17_head_front_left_3q.png", "head-face", "front-left-3q", "Left cheek and glasses guide"),
    plate("18_head_front_right_3q.png", "head-face", "front-right-3q", "Right cheek and glasses guide"),
    plate("19_head_top.png", "head-face", "top-head", "Crown fitting", "head_top", True),
    plate("20_eye_pair.png", "head-face", "eye-pair", "Eye spacing and shape"),
    plate("21_iris_teal.png", "head-face", "iris", "Teal-green iris material"),
    plate("22_glasses_worn_front.png", "head-face", "glasses-worn-front", "Glasses face alignment"),
    plate("23_glasses_worn_side.png", "head-face", "glasses-worn-side", "Temple arm alignment"),
    plate("24_cheek_blush.png", "head-face", "cheek-blush", "Subtle blush placement"),
    plate("25_hair_cap.png", "hair", "hair-cap", "Base cap construction"),
    plate("26_hair_crown.png", "hair", "crown", "Crown parting"),
    plate("27_hair_bangs_center.png", "hair", "bangs-center", "Central bangs"),
    plate("28_hair_bangs_left.png", "hair", "bangs-left", "Left bang cluster"),
    plate("29_hair_bangs_right.png", "hair", "bangs-right", "Right bang cluster"),
    plate("30_hair_bangs_side.png", "hair", "bangs-side", "Bang projection"),
    plate("31_hair_side_lock_left.png", "hair", "side-lock-left", "Left side lock"),
    plate("32_hair_side_lock_right.png", "hair", "side-lock-right", "Right side lock"),
    plate("33_hair_bob_back.png", "hair", "bob-back", "Back bob layers"),
    plate("34_hair_bob_left.png", "hair", "bob-left", "Left bob layers"),
    plate("35_hair_bob_right.png", "hair", "bob-right", "Right bob layers"),
    plate("36_hair_lower_tips.png", "hair", "lower-tips", "Blue-violet tips"),
    plate("37_hair_gradient_material.png", "hair", "gradient-material", "Hair gradient material"),
    plate("38_ahoge_front.png", "hair", "ahoge-front", "Zigzag ahoge front"),
    plate("39_ahoge_side.png", "hair", "ahoge-side", "Zigzag ahoge side"),
    plate("40_ahoge_top.png", "hair", "ahoge-top", "Ahoge root top"),
    plate("41_hairclip_placement.png", "hair", "hairclip-placement", "Front-left clip placement"),
    plate("42_hairclip_attachment.png", "hair", "hairclip-attachment", "Hairclip pin attachment"),
    plate("43_hoodie_front.png", "outfit", "hoodie-front", "Hoodie front construction"),
    plate("44_hoodie_back.png", "outfit", "hoodie-back", "Hoodie back construction"),
    plate("45_hoodie_side.png", "outfit", "hoodie-side", "Hoodie side construction"),
    plate("46_hoodie_open_state.png", "outfit", "hoodie-open", "Open hoodie layering"),
    plate("47_collar_front.png", "outfit", "collar-front", "Collar front fold"),
    plate("48_cuff_charcoal.png", "outfit", "cuff", "Ribbed cuff"),
    plate("49_shorts_front.png", "outfit", "shorts-front", "Shorts front"),
    plate("50_sneaker_side.png", "outfit", "sneaker-side", "Sneaker side"),
]


def normalize(source: Path, target: Path) -> None:
    image = Image.open(source).convert("RGB")
    image = ImageOps.autocontrast(image, cutoff=0.25)
    image = ImageEnhance.Contrast(image).enhance(1.015)
    image = image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=90, threshold=3))
    image.thumbnail((1880, 1880), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (SIZE, SIZE), WHITE)
    canvas.paste(image, ((SIZE - image.width) // 2, (SIZE - image.height) // 2))
    canvas.save(target)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def white_corner_score(path: Path) -> float:
    image = Image.open(path).convert("RGB").resize((128, 128))
    pixels = [image.getpixel((x, y)) for x, y in ((0, 0), (127, 0), (0, 127), (127, 127))]
    return sum(1 for pixel in pixels if min(pixel) >= 245) / 4


def contact_sheet(items: list[Plate], output: Path, columns: int = 4) -> None:
    rows = (len(items) + columns - 1) // columns
    canvas = Image.new("RGB", (30 + columns * 440, 30 + rows * 470), "white")
    draw = ImageDraw.Draw(canvas)
    for index, item in enumerate(items):
        x = 30 + index % columns * 440
        y = 30 + index // columns * 470
        image = Image.open(ROOT / item.file).convert("RGB")
        image.thumbnail((410, 410), Image.Resampling.LANCZOS)
        canvas.paste(image, (x + (410 - image.width) // 2, y))
        draw.text((x, y + 414), item.file, fill=(25, 32, 42))
    canvas.save(output)


def main() -> None:
    for folder in (RAW, REJECTED, QA):
        folder.mkdir(parents=True, exist_ok=True)
    missing = []
    for item in PLATES:
        source = RAW / item.file
        if not source.is_file():
            missing.append(item.file)
            continue
        normalize(source, ROOT / item.file)
    if missing:
        raise RuntimeError("Raw generated plate missing: " + ", ".join(missing))
    active = [ROOT / item.file for item in PLATES]
    hashes = [sha256(path) for path in active]
    if len(hashes) != len(set(hashes)):
        raise RuntimeError("Generated pack contains byte-identical plates.")
    leakage = [path.name for path in active if white_corner_score(path) < 1.0]
    if leakage:
        raise RuntimeError("Generated plate corner QA failed: " + ", ".join(leakage))
    manifest = {
        "schema_version": 2,
        "character": "Aina Venara",
        "canonical_height_cm": 152,
        "image_size": [SIZE, SIZE],
        "background": "#FFFFFF",
        "source_strategy": "individual built-in image_gen plates normalized locally; no crop outputs",
        "references": [
            asdict(item)
            | {
                "source_kind": "generated",
                "qa_status": "approved",
                "size": [SIZE, SIZE],
            }
            for item in PLATES
        ],
    }
    (ROOT / "reference_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for category in sorted({item.category for item in PLATES}):
        contact_sheet([item for item in PLATES if item.category == category], QA / f"{category}_contact_sheet.png")
    contact_sheet(PLATES, ROOT / "Aina_Venara_Generated_HD_Index.png", columns=5)
    print(f"Generated pack ready: {len(PLATES)} plates, scoring={sum(item.use_for_scoring for item in PLATES)}")


if __name__ == "__main__":
    main()
