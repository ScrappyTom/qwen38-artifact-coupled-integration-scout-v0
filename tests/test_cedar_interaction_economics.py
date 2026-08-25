from __future__ import annotations

import json
from pathlib import Path

from tools import audit_cedar_interaction_economics as audit


ROOT = Path(__file__).resolve().parents[1]


def test_offline_interaction_economics_receipt() -> None:
    assert audit.main() == 0
    value = json.loads(
        (ROOT / "CEDAR_INTERACTION_ECONOMICS_AUDIT.json").read_text(encoding="utf-8")
    )
    assert value["schema"] == "cedar-interaction-economics-audit-v0"
    assert value["status"] == "offline_design_evidence_only"
    assert [row["configuration_id"] for row in value["cells"]] == [
        "D0_DETACHED",
        "A1_COUPLED",
    ]
    for row in value["cells"]:
        assert row["actor_calls"] == 19
        assert row["maintenance_calls"] == 18
        assert row["provider_calls"] == 37
        assert row["accepted_maintenance_calls"] == [2, 8, 9, 10, 14]
        assert len(row["rejected_maintenance_calls"]) == 13
        assert row["terminal_disposition"] == "maintenance_call_budget_exhausted"
        assert row["check_currency"]["final_check_status"] == "stale"
        assert row["capacity_only_cadence_accounting"][
            "batch_every_three_externalizations"
        ]["maintenance_calls_if_every_externalization_is_integrated"] == 7


def test_a1_known_errors_entered_through_actor_work() -> None:
    value = json.loads(
        (ROOT / "CEDAR_INTERACTION_ECONOMICS_AUDIT.json").read_text(encoding="utf-8")
    )
    a1 = next(row for row in value["cells"] if row["configuration_id"] == "A1_COUPLED")
    for lineage in a1["known_semantic_error_lineage"].values():
        assert lineage["first_admitted_origin"] == "ordinary_actor_work"
    assert a1["known_semantic_error_lineage"]["revision_binding_as_permitted_count"][
        "first_actor_occurrence"
    ]["actor_call"] == 12
    for marker_id in (
        "arrival_hours_as_wind_speed",
        "wind_shift_probability_as_humidity",
        "survey_coverage_as_uncertainty",
    ):
        lineage = a1["known_semantic_error_lineage"][marker_id]
        assert lineage["first_actor_occurrence"]["actor_call"] == 15
        assert lineage["first_maintenance_occurrence"] is None
    assert a1["final_effect_crossed_actor_boundary"] is False


def test_d0_final_effect_and_resource_accounting() -> None:
    value = json.loads(
        (ROOT / "CEDAR_INTERACTION_ECONOMICS_AUDIT.json").read_text(encoding="utf-8")
    )
    d0 = next(row for row in value["cells"] if row["configuration_id"] == "D0_DETACHED")
    assert d0["final_effect_crossed_actor_boundary"] is True
    assert d0["maintenance_serialized_tokens"] > 100_000
    assert d0["remaining_declared_actor_calls_at_terminal"] == 7
