#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont


CANVAS_SIZE = (935, 610)
OUTPUT_DIR = Path("outputs/avatar_faces_v2_sample")
CONTACT_SHEET = Path("outputs/avatar_faces_v2_sample_contact_sheet.png")

EXPRESSIONS = ("开心", "思考", "生气")

MOUTH_SHAPES = (
    ("mouth_00_closed", 0.0),
    ("mouth_01_tiny", 0.18),
    ("mouth_02_small", 0.34),
    ("mouth_03_medium", 0.52),
    ("mouth_04_large", 0.72),
    ("mouth_05_wide", 1.0),
)


@dataclass(frozen=True)
class ExpressionStyle:
    brow: str
    eye: str
    cheek: tuple[int, int, int, int]
    accent: tuple[int, int, int, int]


EXPRESSION_STYLES = {
    "开心": ExpressionStyle("soft", "happy", (255, 104, 153, 210), (255, 69, 136, 255)),
    "思考": ExpressionStyle("curious", "side", (255, 123, 168, 190), (75, 151, 255, 255)),
    "生气": ExpressionStyle("angry", "angry", (255, 89, 112, 210), (255, 75, 72, 255)),
}


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rounded_polygon_mask(size: tuple[int, int], points: list[tuple[int, int]], blur: int = 0) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(points, fill=255)
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return mask


def draw_glow(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    for offset, alpha in ((22, 28), (14, 44), (7, 72)):
        glow = (*color[:3], alpha)
        draw.rounded_rectangle((x1 - offset, y1 - offset, x2 + offset, y2 + offset), radius=125, outline=glow, width=7)


def draw_helmet(base: Image.Image) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    visor = (112, 82, 823, 542)
    draw_glow(draw, visor, (0, 210, 255, 255))
    draw.rounded_rectangle(visor, radius=120, fill=(7, 13, 39, 245), outline=(20, 232, 255, 230), width=9)
    draw.rounded_rectangle((140, 115, 795, 512), radius=96, fill=(22, 18, 57, 255), outline=(118, 66, 255, 210), width=5)

    for x in range(170, 775, 44):
        y = 132 + int(10 * math.sin(x * 0.05))
        draw.ellipse((x, y, x + 4, y + 4), fill=(255, 255, 255, 150))

    draw.arc((122, 68, 812, 355), 190, 350, fill=(255, 73, 179, 220), width=11)
    draw.arc((146, 79, 789, 340), 194, 346, fill=(255, 210, 74, 210), width=4)
    draw.arc((164, 92, 770, 334), 195, 345, fill=(26, 115, 255, 230), width=5)

    ornament_x = 468
    draw.line((ornament_x, 73, ornament_x, 143), fill=(255, 219, 103, 240), width=3)
    draw.ellipse((ornament_x - 17, 124, ornament_x + 17, 158), fill=(255, 60, 85, 245), outline=(255, 230, 138, 240), width=3)
    draw.ellipse((ornament_x - 7, 112, ornament_x + 7, 128), fill=(45, 223, 245, 255))


def draw_face_base(base: Image.Image) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    face_box = (250, 136, 685, 532)
    draw.ellipse((230, 118, 705, 560), fill=(255, 202, 215, 255))
    draw.ellipse(face_box, fill=(255, 214, 224, 255))
    draw.rectangle((305, 108, 630, 220), fill=(28, 16, 45, 255))
    for x in range(320, 612, 24):
        draw.line((x, 116, x - 13, 210), fill=(12, 8, 31, 255), width=13)
    draw.arc((249, 116, 685, 360), 190, 350, fill=(35, 20, 50, 255), width=28)


def draw_cheeks(draw: ImageDraw.ImageDraw, color: tuple[int, int, int, int]) -> None:
    draw.ellipse((265, 343, 350, 418), fill=color)
    draw.ellipse((585, 343, 670, 418), fill=color)
    draw.ellipse((287, 365, 332, 404), fill=(255, 143, 186, 70))
    draw.ellipse((607, 365, 652, 404), fill=(255, 143, 186, 70))


def draw_eye(draw: ImageDraw.ImageDraw, cx: int, cy: int, *, scale: float = 1.0, angry: bool = False, side: int = 0) -> None:
    width = int(82 * scale)
    height = int(96 * scale)
    draw.ellipse((cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2), fill=(16, 17, 46, 255))
    draw.ellipse((cx - width // 2 + 7, cy - height // 2 + 7, cx + width // 2 - 7, cy + height // 2 - 7), fill=(61, 50, 142, 255))
    iris_x = cx + side * 9
    draw.ellipse((iris_x - 26, cy - 29, iris_x + 26, cy + 32), fill=(48, 154, 255, 255))
    draw.ellipse((iris_x - 17, cy - 19, iris_x + 17, cy + 21), fill=(146, 61, 244, 255))
    draw.ellipse((iris_x - 8, cy - 8, iris_x + 8, cy + 10), fill=(17, 17, 49, 255))
    draw.ellipse((cx - 23, cy - 33, cx - 4, cy - 14), fill=(255, 255, 255, 235))
    draw.ellipse((cx + 10, cy - 12, cx + 20, cy - 2), fill=(255, 255, 255, 190))
    if angry:
        if cx < 470:
            draw.line((cx - 51, cy - 64, cx + 42, cy - 35), fill=(31, 14, 42, 255), width=13)
        else:
            draw.line((cx - 42, cy - 35, cx + 51, cy - 64), fill=(31, 14, 42, 255), width=13)


def draw_closed_happy_eye(draw: ImageDraw.ImageDraw, cx: int, cy: int) -> None:
    draw.arc((cx - 50, cy - 20, cx + 50, cy + 58), 198, 342, fill=(28, 18, 48, 255), width=13)
    draw.line((cx - 52, cy + 10, cx - 65, cy - 2), fill=(28, 18, 48, 255), width=5)
    draw.line((cx + 52, cy + 10, cx + 65, cy - 2), fill=(28, 18, 48, 255), width=5)


def draw_brows(draw: ImageDraw.ImageDraw, style: str) -> None:
    if style == "angry":
        draw.line((330, 236, 421, 264), fill=(28, 16, 45, 255), width=10)
        draw.line((515, 264, 606, 236), fill=(28, 16, 45, 255), width=10)
    elif style == "curious":
        draw.arc((318, 214, 420, 256), 200, 340, fill=(28, 16, 45, 255), width=8)
        draw.arc((512, 198, 620, 246), 205, 335, fill=(28, 16, 45, 255), width=8)
    else:
        draw.arc((318, 218, 420, 262), 200, 340, fill=(28, 16, 45, 255), width=8)
        draw.arc((516, 218, 618, 262), 200, 340, fill=(28, 16, 45, 255), width=8)


def draw_expression_marks(draw: ImageDraw.ImageDraw, expression: str, accent: tuple[int, int, int, int]) -> None:
    if expression == "思考":
        font = load_font(46)
        draw.text((638, 208), "?", font=font, fill=accent)
        draw.ellipse((390, 219, 399, 228), fill=(255, 78, 116, 210))
    elif expression == "生气":
        draw.line((286, 198, 319, 225), fill=accent, width=8)
        draw.line((322, 196, 292, 228), fill=accent, width=8)
        draw.line((615, 198, 648, 225), fill=accent, width=8)
        draw.line((651, 196, 621, 228), fill=accent, width=8)
        draw.ellipse((465, 218, 476, 229), fill=(255, 58, 86, 230))
    else:
        draw.ellipse((453, 217, 464, 228), fill=(255, 78, 116, 210))


def mouth_box(openness: float, expression: str) -> tuple[int, int, int, int]:
    base_width = {
        "开心": 104,
        "思考": 84,
        "生气": 90,
    }[expression]
    max_extra = {
        "开心": 70,
        "思考": 46,
        "生气": 48,
    }[expression]
    width = int(base_width + max_extra * openness)
    height = int(7 + 112 * openness)
    center_x = 468
    top = int(415 - 17 * openness)
    return (center_x - width // 2, top, center_x + width // 2, top + height)


def draw_mouth(draw: ImageDraw.ImageDraw, expression: str, openness: float) -> None:
    box = mouth_box(openness, expression)
    x1, y1, x2, y2 = box

    if openness <= 0.02:
        if expression == "生气":
            draw.arc((x1 - 6, y1 - 4, x2 + 6, y1 + 36), 205, 335, fill=(89, 24, 46, 255), width=8)
        elif expression == "思考":
            draw.arc((x1, y1 - 5, x2, y1 + 28), 195, 330, fill=(103, 38, 63, 255), width=7)
        else:
            draw.arc((x1, y1 - 22, x2, y1 + 34), 20, 160, fill=(116, 39, 62, 255), width=7)
        return

    radius = max(14, min((x2 - x1) // 2, (y2 - y1) // 2 + 12))
    draw.rounded_rectangle(box, radius=radius, fill=(82, 21, 45, 255), outline=(109, 28, 53, 255), width=6)

    inner_pad_x = max(9, int(11 + 5 * openness))
    inner_pad_y = max(7, int(7 + 4 * openness))
    draw.rounded_rectangle(
        (x1 + inner_pad_x, y1 + inner_pad_y, x2 - inner_pad_x, y2 - inner_pad_y),
        radius=max(9, radius - 12),
        fill=(49, 14, 36, 255),
    )

    if openness > 0.2:
        tooth_h = int(12 + 15 * openness)
        draw.rounded_rectangle((x1 + 18, y1 + 6, x2 - 18, y1 + tooth_h), radius=8, fill=(255, 248, 242, 255))

    tongue_h = int(11 + 31 * openness)
    draw.ellipse((x1 + 24, y2 - tongue_h - 8, x2 - 24, y2 + 12), fill=(255, 105, 151, 230))

    if expression == "生气":
        draw.line((x1 + 15, y1 + 8, x1 + 30, y1 + 28), fill=(255, 248, 242, 255), width=5)
        draw.line((x2 - 15, y1 + 8, x2 - 30, y1 + 28), fill=(255, 248, 242, 255), width=5)


def draw_face(expression: str, mouth_name: str, openness: float) -> Image.Image:
    style = EXPRESSION_STYLES[expression]
    image = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    shadow = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow, "RGBA")
    sdraw.rounded_rectangle((112, 82, 823, 542), radius=120, fill=(0, 0, 0, 115))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)), (0, 12))

    draw_helmet(image)
    draw_face_base(image)

    draw = ImageDraw.Draw(image, "RGBA")
    draw_cheeks(draw, style.cheek)
    draw_brows(draw, style.brow)

    if style.eye == "happy":
        draw_closed_happy_eye(draw, 372, 300)
        draw_closed_happy_eye(draw, 565, 300)
    elif style.eye == "side":
        draw_eye(draw, 373, 301, scale=0.95, side=1)
        draw_eye(draw, 565, 301, scale=0.95, side=1)
    else:
        draw_eye(draw, 373, 301, scale=0.97, angry=True)
        draw_eye(draw, 565, 301, scale=0.97, angry=True)

    draw_expression_marks(draw, expression, style.accent)
    draw_mouth(draw, expression, openness)

    font = load_font(17)
    draw.text((34, 562), f"{expression} / {mouth_name}", font=font, fill=(255, 255, 255, 0))
    return image


def make_contact_sheet(files: list[Path]) -> None:
    thumb_size = (214, 140)
    label_h = 34
    pad = 18
    cols = 6
    rows = math.ceil(len(files) / cols)
    sheet = Image.new("RGBA", (cols * (thumb_size[0] + pad) + pad, rows * (thumb_size[1] + label_h + pad) + pad), (248, 248, 248, 255))
    draw = ImageDraw.Draw(sheet, "RGBA")
    font = load_font(15)

    for index, path in enumerate(files):
        row, col = divmod(index, cols)
        x = pad + col * (thumb_size[0] + pad)
        y = pad + row * (thumb_size[1] + label_h + pad)
        image = Image.open(path).convert("RGBA")
        image.thumbnail(thumb_size, Image.LANCZOS)
        sheet.alpha_composite(image, (x + (thumb_size[0] - image.width) // 2, y))
        label = f"{path.parent.name}/{path.stem.replace('mouth_', '')}"
        draw.text((x, y + thumb_size[1] + 8), label, font=font, fill=(32, 32, 32, 255))

    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(CONTACT_SHEET)


def main() -> None:
    generated: list[Path] = []
    for expression in EXPRESSIONS:
        expression_dir = OUTPUT_DIR / expression
        expression_dir.mkdir(parents=True, exist_ok=True)
        for mouth_name, openness in MOUTH_SHAPES:
            image = draw_face(expression, mouth_name, openness)
            output = expression_dir / f"{mouth_name}.png"
            image.save(output)
            generated.append(output)

    make_contact_sheet(generated)
    print(f"generated {len(generated)} images in {OUTPUT_DIR}")
    print(CONTACT_SHEET)


if __name__ == "__main__":
    main()
