from __future__ import annotations

# ruff: noqa: E402

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from host_refactor.live_smoke import EXPECTED_PENDING_RESULT_ID, build_live_smoke_system
from reactive_runtime.canonical import sha256_bytes, write_json
from reactive_runtime.tokenizer import render_qwen_messages
from tools.live_common import LiveTokenizer, start_server, stop_server
from tools.offline_tokenizer import OfflineTokenizer


RUN_ROOT = ROOT / "diagnostic_runs" / "2026-08-28-live-tokenizer-parity-v1"


def offline_ids(tokenizer: OfflineTokenizer, text: str) -> list[int]:
    run = subprocess.run(
        [
            tokenizer.executable,
            "-m",
            tokenizer.model,
            "--stdin",
            "--ids",
            "--no-bos",
        ],
        input=text.encode("utf-8"),
        capture_output=True,
        timeout=180,
        check=False,
    )
    output = run.stdout.decode("utf-8", errors="replace")
    matches = re.findall(r"\[[0-9,\s]+\]", output)
    if run.returncode != 0 or not matches:
        raise RuntimeError(run.stderr.decode("utf-8", errors="replace")[-2000:])
    value = json.loads(matches[-1])
    if not isinstance(value, list) or not all(isinstance(item, int) for item in value):
        raise RuntimeError("offline tokenizer did not return integer ids")
    return value


def compare(label: str, messages: list[dict[str, str]], live: LiveTokenizer, offline: OfflineTokenizer) -> dict[str, object]:
    manual = render_qwen_messages(messages)
    server = live.render(messages)
    live_tokens = live.tokenize(server)
    offline_tokens = offline_ids(offline, manual)
    first_difference = next(
        (
            index
            for index, (left, right) in enumerate(zip(offline_tokens, live_tokens))
            if left != right
        ),
        None,
    )
    if first_difference is None and len(offline_tokens) != len(live_tokens):
        first_difference = min(len(offline_tokens), len(live_tokens))
    window_start = 0 if first_difference is None else max(0, first_difference - 12)
    window_end = 0 if first_difference is None else first_difference + 20
    return {
        "first_token_difference": first_difference,
        "label": label,
        "live_count": len(live_tokens),
        "live_tail": live_tokens[-12:],
        "live_window": live_tokens[window_start:window_end],
        "manual_bytes": len(manual.encode("utf-8")),
        "manual_sha256": sha256_bytes(manual.encode("utf-8")),
        "offline_count": len(offline_tokens),
        "offline_tail": offline_tokens[-12:],
        "offline_window": offline_tokens[window_start:window_end],
        "render_equal": manual == server,
        "server_bytes": len(server.encode("utf-8")),
        "server_sha256": sha256_bytes(server.encode("utf-8")),
    }


def main() -> int:
    if RUN_ROOT.exists():
        raise FileExistsError(RUN_ROOT)
    RUN_ROOT.mkdir(parents=True)
    process = stdout = stderr = None
    release = None
    try:
        process, stdout, stderr, gate = start_server(RUN_ROOT / "model")
        live = LiveTokenizer()
        offline = OfflineTokenizer()
        host, _, kernel, _ = build_live_smoke_system(
            repository_root=ROOT,
            trajectory_root=RUN_ROOT / "trajectory",
            count_messages=offline.count_messages,
            count_text=offline.count_text,
        )
        ordinary = host.composer.compose(kernel).message_list()
        outcome = host.capacity.ensure_feasible(
            kernel,
            protected_result_ids=(EXPECTED_PENDING_RESULT_ID,),
        )
        write_json(
            RUN_ROOT / "TOKENIZER_PARITY.json",
            {
                "ordinary": compare("ordinary", ordinary, live, offline),
                "relieved": compare(
                    "relieved", outcome.packet.message_list(), live, offline
                ),
                "runtime_gate_passed": gate["passed"],
                "schema": "live-tokenizer-parity-diagnostic-v0",
            },
        )
    finally:
        if process is not None:
            release = stop_server(process, stdout, stderr, RUN_ROOT / "model")
        write_json(RUN_ROOT / "FINALIZATION.json", {"release": release})
    if release is None or release.get("released") is not True:
        raise RuntimeError("diagnostic runtime did not release")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
