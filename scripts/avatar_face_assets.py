#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


FACE_ASSET_SPECS = [
    ("happy", "closed", "开心", "眯眼笑"),
    ("happy", "open_small", "开心", "眨眼笑"),
    ("happy", "open_wide", "开心", "大笑"),
    ("thinking", "closed", "思考", None),
    ("thinking", "open_small", "思考", "开心"),
    ("thinking", "open_wide", "思考", "惊讶"),
    ("surprised", "closed", "惊讶", None),
    ("surprised", "open_small", "惊讶", "斜眼惊讶"),
    ("surprised", "open_wide", "惊讶", "惊恐"),
    ("sad", "closed", "难过", None),
    ("sad", "open_small", "难过", "委屈哭"),
    ("sad", "open_wide", "难过", "大哭"),
    ("angry", "closed", "生气", None),
    ("angry", "open_small", "生气", "不满"),
    ("angry", "open_wide", "生气", "愤怒"),
]

MOUTH_BOX_BY_SOURCE = {
    "不满": (360, 365, 575, 520),
    "大哭": (300, 320, 630, 560),
    "大笑": (305, 335, 630, 560),
    "委屈哭": (350, 360, 585, 545),
    "开心": (350, 360, 585, 535),
    "惊恐": (360, 350, 580, 550),
    "惊讶": (385, 350, 550, 550),
    "斜眼惊讶": (380, 365, 555, 555),
    "愤怒": (360, 360, 575, 555),
    "眨眼笑": (350, 350, 580, 530),
    "眯眼笑": (365, 365, 560, 520),
}


def expected_asset_filenames() -> list[str]:
    return [f"{emotion}_{mouth_shape}.png" for emotion, mouth_shape, _, _ in FACE_ASSET_SPECS]


def required_source_names() -> list[str]:
    names = set()
    for _, _, base_name, mouth_name in FACE_ASSET_SPECS:
        names.add(base_name)
        if mouth_name:
            names.add(mouth_name)
    return sorted(names)


def load_face(source_dir: Path, name: str) -> Image.Image:
    path = source_dir / f"{name}.png"
    if not path.exists():
        raise FileNotFoundError(f"Face image not found: {path}")
    return Image.open(path).convert("RGBA")


def build_mouth_mask(size: tuple[int, int], *, feather: int = 22) -> Image.Image:
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    inset = max(1, feather)
    draw.rounded_rectangle(
        (inset, inset, width - inset - 1, height - inset - 1),
        radius=max(20, min(width, height) // 3),
        fill=255,
    )
    return mask.filter(ImageFilter.GaussianBlur(feather / 2))


def blend_mouth(base: Image.Image, mouth_source: Image.Image, mouth_name: str) -> Image.Image:
    box = MOUTH_BOX_BY_SOURCE[mouth_name]
    result = base.copy()
    base_patch = result.crop(box)
    mouth_patch = mouth_source.crop(box)
    mask = build_mouth_mask(mouth_patch.size)
    result.paste(Image.composite(mouth_patch, base_patch, mask), box[:2])
    return result


def generate_avatar_face_assets(source_dir: Path, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []

    for emotion, mouth_shape, base_name, mouth_name in FACE_ASSET_SPECS:
        base = load_face(source_dir, base_name)
        if mouth_name:
            image = blend_mouth(base, load_face(source_dir, mouth_name), mouth_name)
        else:
            image = base

        output_path = output_dir / f"{emotion}_{mouth_shape}.png"
        image.save(output_path)
        generated.append(output_path)

    return generated


def write_contact_sheet(image_paths: list[Path], output_path: Path) -> None:
    if not image_paths:
        raise ValueError("No images to preview")

    thumb_size = (260, 170)
    columns = 3
    padding = 18
    label_height = 26
    rows = (len(image_paths) + columns - 1) // columns
    sheet = Image.new(
        "RGBA",
        (
            columns * (thumb_size[0] + padding) + padding,
            rows * (thumb_size[1] + label_height + padding) + padding,
        ),
        (248, 248, 248, 255),
    )
    draw = ImageDraw.Draw(sheet)
    font = load_label_font()

    for index, path in enumerate(image_paths):
        image = Image.open(path).convert("RGBA")
        image.thumbnail(thumb_size, Image.LANCZOS)
        row, col = divmod(index, columns)
        x = padding + col * (thumb_size[0] + padding)
        y = padding + row * (thumb_size[1] + label_height + padding)
        sheet.alpha_composite(image, (x + (thumb_size[0] - image.width) // 2, y))
        draw.text((x, y + thumb_size[1] + 4), path.stem, fill=(20, 20, 20, 255), font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def load_label_font() -> ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ):
        try:
            return ImageFont.truetype(path, 15)
        except OSError:
            pass
    return ImageFont.load_default()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate structured avatar face talking assets.")
    parser.add_argument("--source-dir", type=Path, default=Path("outputs/faces"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/avatar_faces"))
    parser.add_argument("--preview", type=Path, default=Path("outputs/avatar_faces_contact_sheet.png"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    generated = generate_avatar_face_assets(args.source_dir, args.output_dir)
    write_contact_sheet(generated, args.preview)
    print(args.output_dir)
    print(args.preview)


if __name__ == "__main__":
    main()
