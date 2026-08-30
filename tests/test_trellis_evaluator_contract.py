from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_t08_accepts_both_authorized_acceptance_word_orders() -> None:
    corrections = json.loads(
        (ROOT / "task_trellis" / "EVALUATOR_CORRECTIONS_V1.json").read_text(
            encoding="utf-8"
        )
    )
    pattern = corrections["corrections"]["T08_currentness.patterns[2]"]

    assert re.search(
        pattern,
        "Independent authorized acceptance is required before closure.",
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert re.search(
        pattern,
        "Independent review and acceptance by each authorized owner are required.",
        flags=re.IGNORECASE | re.DOTALL,
    )


def test_historical_evaluator_remains_frozen() -> None:
    evaluator = json.loads(
        (ROOT / "task_trellis" / "EVALUATOR.json").read_text(encoding="utf-8")
    )
    assert evaluator["evaluator_id"] == "trellis-heat-evaluator-v0"
    assert evaluator["relation_requirements"]["T08_currentness"]["patterns"][2] == (
        "independent.{0,100}(accept|acceptance).{0,100}(authorized|owner)"
    )
