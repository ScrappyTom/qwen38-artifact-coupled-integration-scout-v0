from __future__ import annotations

import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from reactive_runtime.tokenizer import render_qwen_messages


ROOT = Path(__file__).resolve().parents[1]


class OfflineTokenizer:
    def __init__(self) -> None:
        profile = json.loads((ROOT / "MODEL_PROFILE_LOCK.json").read_text(encoding="utf-8"))
        self.executable = str(profile["tokenizer_executable"])
        self.model = str(profile["tokenizer_projection_path"])

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
