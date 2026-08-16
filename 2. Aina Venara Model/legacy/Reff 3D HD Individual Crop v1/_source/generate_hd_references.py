from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


OUT = Path(__file__).resolve().parents[1]
DETAIL_ROOT = OUT.parent / "Reff 3D Detailed"
SIZE = 2048
WHITE = (255, 255, 255)


@dataclass(frozen=True)
class Reference:
    file: str
    category: str
    view: str
    source: str
    crop: tuple[int, int, int, int]
    purpose: str
    camera: str
    mask: str = "white-background"
    flip_x: bool = False


def ref(
    file: str,
    category: str,
    view: str,
    source: str,
    crop: tuple[int, int, int, int],
    purpose: str,
    camera: str,
    flip_x: bool = False,
) -> Reference:
    return Reference(file, category, view, source, crop, purpose, camera, "white-background", flip_x)


REFERENCES = [
    # Full body: eight unique modeling views.
    ref("01_full_body_front.png", "full-body", "front", "01_Aina_FullBody_Orthographic.png", (20, 150, 335, 1215), "Primary silhouette, scale, floor and A-pose alignment", "body_front"),
    ref("02_full_body_left.png", "full-body", "left", "01_Aina_FullBody_Orthographic.png", (330, 150, 620, 1215), "Left profile silhouette and garment depth", "body_left"),
    ref("03_full_body_right.png", "full-body", "right", "01_Aina_FullBody_Orthographic.png", (620, 150, 905, 1215), "Right profile silhouette and accessory placement", "body_right"),
    ref("04_full_body_back.png", "full-body", "back", "01_Aina_FullBody_Orthographic.png", (900, 150, 1190, 1215), "Back silhouette, bob and hoodie volume", "body_back"),
    ref("05_full_body_front_left_3q.png", "full-body", "front-left-3q", "01_Aina_FullBody_Orthographic.png", (1180, 150, 1475, 1215), "Three-quarter silhouette and front garment depth", "body_front_left_3q"),
    ref("06_full_body_front_right_3q.png", "full-body", "front-right-3q", "01_Aina_FullBody_Orthographic.png", (1180, 150, 1475, 1215), "Mirrored opposite three-quarter silhouette guide", "body_front_right_3q", True),
    ref("07_full_body_back_left_3q.png", "full-body", "back-left-3q", "01_Aina_FullBody_Orthographic.png", (900, 150, 1190, 1215), "Mirrored back silhouette guide for asymmetric review", "body_back_left_3q", True),
    ref("08_full_body_top.png", "full-body", "top", "01_Aina_FullBody_Orthographic.png", (1450, 150, 1780, 610), "Top-head and shoulder footprint", "body_top"),
    # Head and face.
    ref("09_head_front.png", "head-face", "front", "02_Aina_Head_Face_Detail.png", (80, 135, 500, 655), "Canonical face identity and glasses placement", "face_front"),
    ref("10_head_left.png", "head-face", "left", "02_Aina_Head_Face_Detail.png", (500, 135, 865, 655), "Head profile, nose, ear and bob depth", "face_left"),
    ref("11_head_right.png", "head-face", "right", "02_Aina_Head_Face_Detail.png", (875, 135, 1250, 655), "Opposite head profile and glasses side fit", "face_right"),
    ref("12_head_back.png", "head-face", "back", "02_Aina_Head_Face_Detail.png", (475, 655, 875, 1185), "Back bob silhouette and tip distribution", "face_back"),
    ref("13_head_front_left_3q.png", "head-face", "front-left-3q", "02_Aina_Head_Face_Detail.png", (80, 655, 485, 1185), "Cheek contour and frame perspective", "face_front_left_3q"),
    ref("14_head_top.png", "head-face", "top", "02_Aina_Head_Face_Detail.png", (875, 655, 1285, 1185), "Hair crown, parting and ahoge root", "face_top"),
    ref("15_eye_teal_closeup.png", "head-face", "eye-closeup", "02_Aina_Head_Face_Detail.png", (1300, 250, 1695, 610), "Iris color, sclera and eyelash styling", "detail_eye"),
    ref("16_glasses_worn_side.png", "head-face", "glasses-side", "02_Aina_Head_Face_Detail.png", (510, 185, 800, 585), "Temple arm and bridge alignment on face", "detail_glasses_side"),
    # Hair.
    ref("17_hair_cap_top.png", "hair", "cap-top", "06_Aina_Hair_Construction.png", (70, 625, 410, 1135), "Crown cap flow and parting", "detail_hair_top"),
    ref("18_hair_bangs_front.png", "hair", "bangs-front", "06_Aina_Hair_Construction.png", (80, 150, 420, 620), "Asymmetric bang clusters and eye clearance", "detail_hair_front"),
    ref("19_hair_bangs_side.png", "hair", "bangs-side", "06_Aina_Hair_Construction.png", (430, 150, 760, 515), "Bang projection and side-lock transition", "detail_hair_side"),
    ref("20_hair_side_lock_left.png", "hair", "side-lock-left", "06_Aina_Hair_Construction.png", (430, 280, 760, 620), "Left side-lock taper", "detail_hair_side_lock_left"),
    ref("21_hair_side_lock_right.png", "hair", "side-lock-right", "06_Aina_Hair_Construction.png", (770, 150, 1100, 620), "Right side-lock taper", "detail_hair_side_lock_right"),
    ref("22_hair_bob_back.png", "hair", "bob-back", "06_Aina_Hair_Construction.png", (1110, 150, 1450, 620), "Layered back bob silhouette", "detail_hair_back"),
    ref("23_hair_gradient_tips.png", "hair", "gradient-tips", "09_Aina_Hair_Garment_Dimensions.png", (70, 335, 760, 610), "Blue-violet lower-tip gradient depth", "detail_hair_tips"),
    ref("24_hair_ahoge_zigzag.png", "hair", "ahoge", "09_Aina_Hair_Garment_Dimensions.png", (760, 325, 1090, 615), "Signature zigzag ahoge shape", "detail_ahoge"),
    ref("25_hairclip_position.png", "hair", "hairclip-position", "02_Aina_Head_Face_Detail.png", (250, 170, 490, 430), "Number-3 hairclip placement on front-left hair", "detail_hairclip_position"),
    # Outfit.
    ref("26_hoodie_front.png", "outfit", "hoodie-front", "03_Aina_Outfit_Construction.png", (1030, 130, 1370, 580), "Open hoodie front, zipper and collar", "detail_hoodie_front"),
    ref("27_hoodie_back.png", "outfit", "hoodie-back", "03_Aina_Outfit_Construction.png", (1380, 130, 1730, 580), "Back garment volume and hem", "detail_hoodie_back"),
    ref("28_hoodie_side.png", "outfit", "hoodie-side", "03_Aina_Outfit_Construction.png", (1030, 560, 1270, 920), "Dropped shoulder, sleeve and hem depth", "detail_hoodie_side"),
    ref("29_collar_front.png", "outfit", "collar-front", "09_Aina_Hair_Garment_Dimensions.png", (520, 600, 810, 805), "Charcoal off-shoulder collar front fold", "detail_collar_front"),
    ref("30_collar_back.png", "outfit", "collar-back", "09_Aina_Hair_Garment_Dimensions.png", (810, 600, 1095, 805), "Charcoal off-shoulder collar back fold", "detail_collar_back"),
    ref("31_sleeve_volume.png", "outfit", "sleeve", "03_Aina_Outfit_Construction.png", (1040, 555, 1265, 890), "Cyan sleeve volume and gathering", "detail_sleeve"),
    ref("32_cuff_charcoal.png", "outfit", "cuff", "09_Aina_Hair_Garment_Dimensions.png", (135, 930, 310, 1080), "Charcoal ribbed cuff", "detail_cuff"),
    ref("33_zipper_detail.png", "outfit", "zipper", "09_Aina_Hair_Garment_Dimensions.png", (310, 800, 530, 1080), "Simple zipper and edge construction", "detail_zipper"),
    ref("34_pocket_detail.png", "outfit", "pocket", "09_Aina_Hair_Garment_Dimensions.png", (535, 800, 740, 1080), "Slanted charcoal pocket opening", "detail_pocket"),
    ref("35_inner_shirt_straps.png", "outfit", "inner-shirt", "09_Aina_Hair_Garment_Dimensions.png", (740, 800, 1090, 1080), "White shirt neckline and pink camisole straps", "detail_inner_shirt"),
    ref("36_shorts_dark.png", "outfit", "shorts", "03_Aina_Outfit_Construction.png", (1010, 900, 1300, 1165), "Dark shorts waist, hem and pocket construction", "detail_shorts"),
    # Accessories and extremities.
    ref("37_hairclip_number_3.png", "accessory-extremity", "hairclip-isolated", "04_Aina_Accessories_Materials.png", (70, 145, 545, 480), "Metallic number-3 clip geometry", "detail_hairclip"),
    ref("38_glasses_pink.png", "accessory-extremity", "glasses-isolated", "04_Aina_Accessories_Materials.png", (555, 145, 930, 480), "Thin rounded pink glasses frame", "detail_glasses"),
    ref("39_hand_dorsal.png", "accessory-extremity", "hand-dorsal", "10_Aina_Hands_Feet_Micro_Detail.png", (95, 260, 395, 620), "Relaxed dorsal hand topology", "detail_hand_dorsal"),
    ref("40_hand_palm.png", "accessory-extremity", "hand-palm", "10_Aina_Hands_Feet_Micro_Detail.png", (650, 260, 940, 620), "Palm and finger proportions", "detail_hand_palm"),
    ref("41_hand_side.png", "accessory-extremity", "hand-side", "10_Aina_Hands_Feet_Micro_Detail.png", (390, 260, 650, 620), "Side profile and finger taper", "detail_hand_side"),
    ref("42_socks_white.png", "accessory-extremity", "socks", "10_Aina_Hands_Feet_Micro_Detail.png", (430, 765, 870, 1105), "White ribbed crew sock shaft", "detail_socks"),
    ref("43_sneakers_front.png", "accessory-extremity", "sneaker-front", "10_Aina_Hands_Feet_Micro_Detail.png", (75, 575, 320, 850), "White sneaker toe, lacing and sole", "detail_sneaker_front"),
    ref("44_sneakers_side.png", "accessory-extremity", "sneaker-side", "10_Aina_Hands_Feet_Micro_Detail.png", (310, 575, 700, 850), "White sneaker side silhouette", "detail_sneaker_side"),
    ref("45_sneakers_back.png", "accessory-extremity", "sneaker-back", "10_Aina_Hands_Feet_Micro_Detail.png", (680, 575, 920, 850), "White sneaker heel construction", "detail_sneaker_back"),
]


def render(reference: Reference) -> None:
    source = DETAIL_ROOT / reference.source
    with Image.open(source).convert("RGB") as image:
        crop = image.crop(reference.crop)
        if reference.flip_x:
            crop = crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        # Mild clarity enhancement only; preserve canonical geometry.
        crop = ImageEnhance.Contrast(crop).enhance(1.025)
        crop = crop.filter(ImageFilter.UnsharpMask(radius=1.1, percent=105, threshold=3))
        max_side = 1840
        scale = min(max_side / crop.width, max_side / crop.height)
        resized = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (SIZE, SIZE), WHITE)
        canvas.paste(resized, ((SIZE - resized.width) // 2, (SIZE - resized.height) // 2))
        canvas.save(OUT / reference.file, quality=100)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for item in REFERENCES:
        render(item)
    manifest = {
        "schema_version": 1,
        "character": "Aina Venara",
        "canonical_height_cm": 152,
        "image_size": [SIZE, SIZE],
        "background": "#FFFFFF",
        "source_strategy": "canonical-sheet crop and LANCZOS upscale; no identity drift",
        "references": [asdict(item) | {"size": [SIZE, SIZE]} for item in REFERENCES],
    }
    (OUT / "reference_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated {len(REFERENCES)} HD references at {OUT}")


if __name__ == "__main__":
    main()
