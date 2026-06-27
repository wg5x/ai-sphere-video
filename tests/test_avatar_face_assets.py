import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.avatar_face_assets import (  # noqa: E402
    FACE_ASSET_SPECS,
    expected_asset_filenames,
    generate_avatar_face_assets,
    required_source_names,
)


class AvatarFaceAssetsTests(unittest.TestCase):
    def test_expected_asset_filenames_match_runtime_contract(self):
        self.assertEqual(
            expected_asset_filenames(),
            [
                "happy_closed.png",
                "happy_open_small.png",
                "happy_open_wide.png",
                "thinking_closed.png",
                "thinking_open_small.png",
                "thinking_open_wide.png",
                "surprised_closed.png",
                "surprised_open_small.png",
                "surprised_open_wide.png",
                "sad_closed.png",
                "sad_open_small.png",
                "sad_open_wide.png",
                "angry_closed.png",
                "angry_open_small.png",
                "angry_open_wide.png",
            ],
        )

    def test_generate_avatar_face_assets_writes_expected_pngs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "faces"
            output_dir = root / "avatar_faces"
            source_dir.mkdir()

            for index, name in enumerate(required_source_names()):
                image = Image.new("RGBA", (935, 610), (20 + index, 40, 80, 255))
                image.save(source_dir / f"{name}.png")

            generated = generate_avatar_face_assets(source_dir, output_dir)

            self.assertEqual(
                [path.name for path in generated],
                expected_asset_filenames(),
            )
            self.assertEqual(len(generated), len(FACE_ASSET_SPECS))
            for path in generated:
                with Image.open(path) as image:
                    self.assertEqual(image.mode, "RGBA")
                    self.assertEqual(image.size, (935, 610))


if __name__ == "__main__":
    unittest.main()
