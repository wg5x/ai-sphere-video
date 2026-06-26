import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.virtual_person_video import (  # noqa: E402
    DEFAULT_SEQUENCE,
    build_face_mask,
    compose_expression_frame,
    parse_sequence,
    resolve_expression_path,
)


class VirtualPersonVideoTests(unittest.TestCase):
    def test_compose_preserves_background_outside_face_box(self):
        background = Image.new("RGB", (100, 80), (10, 20, 30))
        expression = Image.new("RGB", (100, 80), (220, 80, 120))

        frame = compose_expression_frame(
            background,
            expression,
            face_box=(30, 20, 70, 60),
            feather=0,
            radius=0,
        )

        self.assertEqual(frame.getpixel((5, 5)), (10, 20, 30))
        self.assertEqual(frame.getpixel((95, 75)), (10, 20, 30))
        self.assertEqual(frame.getpixel((50, 40)), (220, 80, 120))

    def test_face_mask_keeps_corners_transparent_and_center_solid(self):
        mask = build_face_mask((80, 60), feather=10, radius=18)

        self.assertEqual(mask.mode, "L")
        self.assertEqual(mask.size, (80, 60))
        self.assertEqual(mask.getpixel((0, 0)), 0)
        self.assertEqual(mask.getpixel((79, 0)), 0)
        self.assertGreater(mask.getpixel((40, 30)), 240)

    def test_parse_sequence_accepts_commas_and_newlines(self):
        self.assertEqual(
            parse_sequence("开心, 眨眼笑\n大笑"),
            ["开心", "眨眼笑", "大笑"],
        )

    def test_resolve_expression_path_finds_png_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "开心.png").write_bytes(b"fake")

            self.assertEqual(resolve_expression_path(root, "开心"), root / "开心.png")

            with self.assertRaises(FileNotFoundError):
                resolve_expression_path(root, "不存在")

    def test_default_sequence_covers_all_raw_emotions(self):
        raw_dir = ROOT / "raw" / "emo"
        expected = {path.stem for path in raw_dir.glob("*.png")}

        self.assertEqual(set(DEFAULT_SEQUENCE), expected)


if __name__ == "__main__":
    unittest.main()
