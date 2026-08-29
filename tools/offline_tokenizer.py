from __future__ import annotations

import hashlib
import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from reactive_runtime.tokenizer import render_qwen_messages


ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=8)
def _verified_sha256(path_text: str, size: int, mtime_ns: int) -> str:
    """Hash one immutable runtime asset once per process and file identity."""

    del size, mtime_ns
    digest = hashlib.sha256()
    with Path(path_text).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _matches_locked_asset(path: Path, expected_sha256: str) -> bool:
    if not path.is_file():
        return False
    stat = path.stat()
    return (
        _verified_sha256(str(path), stat.st_size, stat.st_mtime_ns)
        == expected_sha256.lower()
    )


def resolve_locked_tokenizer_model(profile: dict[str, Any]) -> Path:
    """Select only a hash-verified tokenizer-bearing asset from the model lock.

    The historical sparse tokenizer projection was a convenience, not a live
    inference asset.  If it is unavailable, the immutable full model declared
    by the same lock is an exact tokenizer source and is the durable fallback.
    """

    candidates = (
        (
            Path(str(profile["tokenizer_projection_path"])),
            str(profile["tokenizer_projection_sha256"]),
        ),
        (Path(str(profile["model_path"])), str(profile["model_sha256"])),
    )
    for path, expected_sha256 in candidates:
        if _matches_locked_asset(path, expected_sha256):
            return path
    rendered = ", ".join(str(path) for path, _ in candidates)
    raise RuntimeError(f"no hash-verified tokenizer asset is available: {rendered}")


class OfflineTokenizer:
    def __init__(self) -> None:
        profile = json.loads((ROOT / "MODEL_PROFILE_LOCK.json").read_text(encoding="utf-8"))
        self.executable = str(profile["tokenizer_executable"])
        self.model = str(resolve_locked_tokenizer_model(profile))

    @lru_cache(maxsize=256)
    def count_text(self, text: str) -> int:
        run = subprocess.run(
            [
                self.executable,
                "-m",
                self.model,
                "--stdin",
                "--show-count",
                "--no-bos",
            ],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=180,
            check=False,
        )
        stdout = run.stdout.decode("utf-8", errors="replace")
        stderr = run.stderr.decode("utf-8", errors="replace")
        match = re.search(r"Total number of tokens:\s*(\d+)", stdout)
        if run.returncode != 0 or match is None:
            raise RuntimeError(f"offline tokenizer failed: {stderr[-1000:]}")
        return int(match.group(1))

    def count_messages(self, messages: list[dict[str, Any]]) -> int:
        return self.count_text(render_qwen_messages(messages))

    def bounded_repetition(self, label: str, maximum_tokens: int) -> str:
        if maximum_tokens < 1:
            raise ValueError("maximum_tokens must be positive")
        low = 1
        high = maximum_tokens * 4 + 16
        best = label
        while low <= high:
            middle = (low + high) // 2
            candidate = (label + " ") * middle
            count = self.count_text(candidate)
            if count <= maximum_tokens:
                best = candidate
                low = middle + 1
            else:
                high = middle - 1
        return best.rstrip()
