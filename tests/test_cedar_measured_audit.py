from pathlib import Path

from tools.audit_measured_interaction import audit
from tools.run_measured_interaction import RUN_ID


ROOT = Path(__file__).resolve().parents[1]


def test_cedar_measured_run_passes_post_run_audit() -> None:
    result = audit(ROOT / "runs" / RUN_ID)
    assert result["passed"], result["failures"]
    assert result["provider_calls"] == 74
    assert result["actor_calls"] == 38
    assert result["maintenance_calls"] == 36
    assert result["serialized_tokens"] == 1_026_000
    assert [row["positive_externalizations"] for row in result["cells"]] == [19, 19]
    assert [
        len(row["unmaintained_positive_externalizations"])
        for row in result["cells"]
    ] == [1, 1]
