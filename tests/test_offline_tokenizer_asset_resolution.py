from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.offline_tokenizer import resolve_locked_tokenizer_model


class OfflineTokenizerAssetResolutionTests(unittest.TestCase):
    def profile(self, root: Path) -> dict[str, str]:
        projection = root / "projection.gguf"
        model = root / "model.gguf"
        return {
            "tokenizer_projection_path": str(projection),
            "tokenizer_projection_sha256": hashlib.sha256(b"projection").hexdigest(),
            "model_path": str(model),
            "model_sha256": hashlib.sha256(b"model").hexdigest(),
        }

    def test_prefers_verified_projection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = self.profile(root)
            (root / "projection.gguf").write_bytes(b"projection")
            (root / "model.gguf").write_bytes(b"model")
            self.assertEqual(
                root / "projection.gguf", resolve_locked_tokenizer_model(profile)
            )

    def test_falls_back_to_verified_full_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = self.profile(root)
            (root / "model.gguf").write_bytes(b"model")
            self.assertEqual(root / "model.gguf", resolve_locked_tokenizer_model(profile))

    def test_rejects_present_but_mismatched_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = self.profile(root)
            (root / "projection.gguf").write_bytes(b"wrong")
            (root / "model.gguf").write_bytes(b"also-wrong")
            with self.assertRaisesRegex(RuntimeError, "no hash-verified tokenizer asset"):
                resolve_locked_tokenizer_model(profile)


if __name__ == "__main__":
    unittest.main()
