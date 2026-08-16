from pathlib import Path
from PIL import Image, ImageDraw

output_dir = Path(str(Path(__file__).resolve().parents[2] / "4. Blender VRM Builder/output/previews/v13"))
images = [
    ("front", output_dir / "front.png"),
    ("left", output_dir / "left.png"),
    ("right", output_dir / "right.png"),
    ("back", output_dir / "back.png"),
    ("face", output_dir / "face.png"),
    ("top", output_dir / "top.png"),
]

thumb = (380, 380)
columns = 3
rows = 2
canvas = Image.new("RGB", (20 + columns * 395, 20 + rows * 410), "white")
draw = ImageDraw.Draw(canvas)

for index, (label, path) in enumerate(images):
    x = 20 + (index % columns) * 395
    y = 20 + (index // columns) * 410
    image = Image.open(path).convert("RGB")
    image.thumbnail(thumb, Image.Resampling.LANCZOS)
    canvas.paste(image, (x + (thumb[0] - image.width) // 2, y))
    draw.text((x, y + 382), label, fill=(25, 32, 42))

canvas.save(output_dir / "base_contact_sheet.png")
print("Base contact sheet saved.")
