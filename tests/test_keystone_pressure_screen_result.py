from __future__ import annotations

from tools.audit_keystone_pressure_screen import audit


def test_keystone_nonqualifying_pressure_screen_audits_cleanly() -> None:
    result = audit(write_outputs=False)
    assert result["passed"] is True
    assert result["pressure_reached"] is True
    assert result["interaction_trigger_qualified"] is False
    assert result["actor_calls"] == 9
    assert result["delivered_qualifying_sources"] == 8
    assert result["delivered_qualifying_domains"] == 8
    assert result["frozen_minimum_qualifying_sources"] == 10
    assert result["frozen_minimum_qualifying_domains"] == 10
    assert result["positive_relief_result_ids"] == ["RESULT-001"]
    assert result["positive_relief_after_tokens"] == 20_648
    assert result["measured_fork_authorized"] is False
