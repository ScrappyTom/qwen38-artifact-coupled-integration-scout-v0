from __future__ import annotations

# ruff: noqa: E402

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reactive_runtime.aster_qualification import build_aster_relational_case
from reactive_runtime.canonical import (
    canonical_json_text,
    sha256_bytes,
    sha256_file,
    write_json,
)
from reactive_runtime.relational_delta import (
    SOURCE_DELTA_PROVIDER_MAX_TOKENS,
    SOURCE_DELTA_TOKEN_BUDGET,
    SOURCE_SLOT_TOKEN_BUDGET,
)
from tools.offline_tokenizer import OfflineTokenizer


OUTPUT = ROOT / "ASTER_RELATIONAL_EXPRESSION_PREFLIGHT.json"
CONTEXT_TOKENS = 25_088


def main() -> int:
    case = build_aster_relational_case(ROOT)
    tokenizer = OfflineTokenizer()
    prompt_tokens = tokenizer.count_messages(case.messages)
    value = {
        "schema": "aster-relational-expression-preflight-v0",
        "status": "passed_offline_pending_live_authorization",
        "run_id": "2026-08-26-aster-relational-expression-qualification-v0",
        "case_id": case.case_id,
        "seed": case.seed,
        "input_result_ids": list(case.input_result_ids),
        "input_source_ids": list(case.input_source_ids),
        "input_source_versions": {
            source_id: case.source_versions[source_id]
            for source_id in case.input_source_ids
        },
        "message_sha256": sha256_bytes(
            canonical_json_text(case.messages).encode("utf-8")
        ),
        "prompt_tokens": prompt_tokens,
        "provider_max_completion_tokens": SOURCE_DELTA_PROVIDER_MAX_TOKENS,
        "context_tokens": CONTEXT_TOKENS,
        "headroom_after_completion": CONTEXT_TOKENS
        - prompt_tokens
        - SOURCE_DELTA_PROVIDER_MAX_TOKENS,
        "fits": prompt_tokens + SOURCE_DELTA_PROVIDER_MAX_TOKENS <= CONTEXT_TOKENS,
        "admission_total_tokens": SOURCE_DELTA_TOKEN_BUDGET,
        "admission_per_source_tokens": SOURCE_SLOT_TOKEN_BUDGET,
        "pressure_handoff_sha256": sha256_file(
            ROOT / "ASTER_PRESSURE_BOUNDARY_HANDOFF.json"
        ),
        "pressure_audit_sha256": sha256_file(ROOT / "ASTER_PRESSURE_SCREEN_AUDIT.json"),
        "contract_sha256": sha256_file(
            ROOT / "ASTER_RELATIONAL_EXPRESSION_QUALIFICATION_CONTRACT.json"
        ),
        "safety_contract_sha256": sha256_file(
            ROOT / "ASTER_RELATIONAL_EXPRESSION_SAFETY_CONTRACT.json"
        ),
        "model_calls": 0,
        "gpu_authorized": False,
        "measured_continuation_authorized": False,
    }
    if not value["fits"]:
        raise RuntimeError("Aster relational-expression case does not fit")
    write_json(OUTPUT, value)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
