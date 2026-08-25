from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.canonical import canonical_json_text, sha256_bytes, sha256_file, write_json  # noqa: E402
from reactive_runtime.meridian_qualification import build_meridian_delta_case  # noqa: E402
from reactive_runtime.source_delta import (  # noqa: E402
    DELTA_PROVIDER_MAX_TOKENS,
    DELTA_TOKEN_BUDGET,
    SLOT_TOKEN_BUDGET,
)
from tools.offline_tokenizer import OfflineTokenizer  # noqa: E402


OUTPUT = ROOT / "MERIDIAN_SOURCE_DELTA_QUALIFICATION_PREFLIGHT.json"
CONTEXT_TOKENS = 25_088


def main() -> int:
    case = build_meridian_delta_case(ROOT)
    tokenizer = OfflineTokenizer()
    prompt_tokens = tokenizer.count_messages(case.messages)
    value = {
        "schema": "meridian-source-delta-expression-preflight-v0",
        "status": "passed_offline_pending_live_authorization",
        "run_id": "2026-08-25-meridian-source-delta-expression-qualification-v0",
        "case_id": case.case_id,
        "seed": case.seed,
        "input_result_ids": list(case.input_result_ids),
        "allowed_source_versions": case.allowed_source_versions,
        "message_sha256": sha256_bytes(
            canonical_json_text(case.messages).encode("utf-8")
        ),
        "prompt_tokens": prompt_tokens,
        "provider_max_completion_tokens": DELTA_PROVIDER_MAX_TOKENS,
        "context_tokens": CONTEXT_TOKENS,
        "headroom_after_completion": CONTEXT_TOKENS
        - prompt_tokens
        - DELTA_PROVIDER_MAX_TOKENS,
        "fits": prompt_tokens + DELTA_PROVIDER_MAX_TOKENS <= CONTEXT_TOKENS,
        "admission_total_tokens": DELTA_TOKEN_BUDGET,
        "admission_per_source_tokens": SLOT_TOKEN_BUDGET,
        "pressure_handoff_sha256": sha256_file(
            ROOT / "MERIDIAN_PRESSURE_BOUNDARY_HANDOFF.json"
        ),
        "pressure_audit_sha256": sha256_file(ROOT / "MERIDIAN_PRESSURE_SCREEN_AUDIT.json"),
        "contract_sha256": sha256_file(
            ROOT / "MERIDIAN_SOURCE_DELTA_QUALIFICATION_CONTRACT.json"
        ),
        "model_calls": 0,
        "gpu_authorized": False,
        "measured_continuation_authorized": False,
    }
    if not value["fits"]:
        raise RuntimeError("Meridian source-delta expression case does not fit")
    write_json(OUTPUT, value)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
