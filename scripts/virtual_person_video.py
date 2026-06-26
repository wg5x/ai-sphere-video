#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


DEFAULT_FACE_BOX = (900, 455, 1835, 1065)
DEFAULT_SEQUENCE = [
    "开心",
    "眨眼笑",
    "大笑",
    "大哭",
    "惊讶",
    "斜眼惊讶",
    "思考",
    "不满",
    "委屈哭",
    "难过",
    "生气",
    "愤怒",
    "惊恐",
    "比心眨眼",
    "眯眼笑",
    "嫌弃",
]


def parse_sequence(value: str) -> list[str]:
    normalized = value.replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def resolve_expression_path(raw_dir: Path, name: str) -> Path:
    path = raw_dir / f"{name}.png"
    if not path.exists():
        raise FileNotFoundError(f"Expression image not found: {path}")
    return path


def build_face_mask(
    size: tuple[int, int],
    *,
    feather: int = 28,
    radius: int = 95,
) -> Image.Image:
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)

    if feather <= 0:
        draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, fill=255)
        return mask

    inset = feather
    draw.rounded_rectangle(
        (inset, inset, width - inset - 1, height - inset - 1),
        radius=radius,
        fill=255,
    )
    return mask.filter(ImageFilter.GaussianBlur(feather / 2))


def compose_expression_frame(
    background: Image.Image,
    expression: Image.Image,
    *,
    face_box: tuple[int, int, int, int] = DEFAULT_FACE_BOX,
    feather: int = 28,
    radius: int = 95,
) -> Image.Image:
    frame = background.convert("RGB").copy()
    source = expression.convert("RGB")
    patch = source.crop(face_box)
    mask = build_face_mask(patch.size, feather=feather, radius=radius)
    frame.paste(patch, face_box[:2], mask)
    return frame


def load_expression(raw_dir: Path, name: str) -> Image.Image:
    return Image.open(resolve_expression_path(raw_dir, name)).convert("RGB")


def blended_frame(
    background: Image.Image,
    current: Image.Image,
    next_image: Image.Image | None,
    alpha: float,
    *,
    face_box: tuple[int, int, int, int],
    feather: int,
    radius: int,
) -> Image.Image:
    if next_image is None or alpha <= 0:
        return compose_expression_frame(
            background,
            current,
            face_box=face_box,
            feather=feather,
            radius=radius,
        )

    current_patch = current.crop(face_box).convert("RGB")
    next_patch = next_image.crop(face_box).convert("RGB")
    patch = Image.blend(current_patch, next_patch, alpha)
    frame = background.convert("RGB").copy()
    mask = build_face_mask(patch.size, feather=feather, radius=radius)
    frame.paste(patch, face_box[:2], mask)
    return frame


def write_video(
    frames: list[Image.Image],
    output: Path,
    *,
    fps: int,
) -> None:
    if not frames:
        raise ValueError("No frames to encode")

    width, height = frames[0].size
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        str(output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    try:
        for frame in frames:
            process.stdin.write(frame.convert("RGB").tobytes())
    finally:
        process.stdin.close()

    if process.wait() != 0:
        raise RuntimeError("ffmpeg failed to encode video")


def save_face_assets(
    raw_dir: Path,
    names: list[str],
    output_dir: Path,
    *,
    face_box: tuple[int, int, int, int],
    feather: int,
    radius: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        image = load_expression(raw_dir, name)
        patch = image.crop(face_box).convert("RGBA")
        alpha = build_face_mask(patch.size, feather=feather, radius=radius)
        patch.putalpha(alpha)
        patch.save(output_dir / f"{name}.png")


def make_frames(
    raw_dir: Path,
    sequence: list[str],
    *,
    base_name: str,
    fps: int,
    hold_seconds: float,
    transition_seconds: float,
    face_box: tuple[int, int, int, int],
    feather: int,
    radius: int,
) -> list[Image.Image]:
    background = load_expression(raw_dir, base_name)
    expressions = [load_expression(raw_dir, name) for name in sequence]
    hold_frames = max(1, round(hold_seconds * fps))
    transition_frames = max(0, round(transition_seconds * fps))

    frames: list[Image.Image] = []
    for index, expression in enumerate(expressions):
        next_expression = expressions[index + 1] if index + 1 < len(expressions) else None
        for _ in range(hold_frames):
            frames.append(
                compose_expression_frame(
                    background,
                    expression,
                    face_box=face_box,
                    feather=feather,
                    radius=radius,
                )
            )
        for step in range(transition_frames):
            alpha = (step + 1) / (transition_frames + 1)
            frames.append(
                blended_frame(
                    background,
                    expression,
                    next_expression,
                    alpha,
                    face_box=face_box,
                    feather=feather,
                    radius=radius,
                )
            )

    return frames


def parse_face_box(value: str) -> tuple[int, int, int, int]:
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("face box must be x1,y1,x2,y2")
    x1, y1, x2, y2 = parts
    if x2 <= x1 or y2 <= y1:
        raise argparse.ArgumentTypeError("face box must have x2>x1 and y2>y1")
    return x1, y1, x2, y2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Make a fixed-background virtual-person expression video.",
    )
    parser.add_argument("--raw-dir", type=Path, default=Path("raw/emo"))
    parser.add_argument("--base", default="开心")
    parser.add_argument("--sequence", default=",".join(DEFAULT_SEQUENCE))
    parser.add_argument("--output", type=Path, default=Path("outputs/virtual_person_demo.mp4"))
    parser.add_argument("--faces-dir", type=Path, default=Path("outputs/faces"))
    parser.add_argument("--preview", type=Path, default=Path("outputs/virtual_person_preview.jpg"))
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--hold-seconds", type=float, default=0.55)
    parser.add_argument("--transition-seconds", type=float, default=0.18)
    parser.add_argument("--face-box", type=parse_face_box, default=DEFAULT_FACE_BOX)
    parser.add_argument("--feather", type=int, default=28)
    parser.add_argument("--radius", type=int, default=95)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    sequence = parse_sequence(args.sequence)
    frames = make_frames(
        args.raw_dir,
        sequence,
        base_name=args.base,
        fps=args.fps,
        hold_seconds=args.hold_seconds,
        transition_seconds=args.transition_seconds,
        face_box=args.face_box,
        feather=args.feather,
        radius=args.radius,
    )
    write_video(frames, args.output, fps=args.fps)
    save_face_assets(
        args.raw_dir,
        sorted(set(sequence)),
        args.faces_dir,
        face_box=args.face_box,
        feather=args.feather,
        radius=args.radius,
    )
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    frames[min(len(frames) - 1, args.fps)].save(args.preview, quality=95)
    print(args.output)
    print(args.faces_dir)
    print(args.preview)


if __name__ == "__main__":
    main()
