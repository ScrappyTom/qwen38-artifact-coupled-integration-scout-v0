from tools.validate_cedar_semantic_adjudication import validate


def test_cedar_semantic_adjudication_is_candidate_bound_and_consistent() -> None:
    result = validate()
    assert result["passed"], result["failures"]
    by_configuration = {
        row["configuration_id"]: row for row in result["derived_candidates"]
    }
    assert by_configuration["D0_DETACHED"]["quality_class"] == "weak_partial"
    assert by_configuration["A1_COUPLED"]["quality_class"] == "strong_partial"
    assert by_configuration["D0_DETACHED"]["closure_readiness"] == "not_ready"
    assert by_configuration["A1_COUPLED"]["closure_readiness"] == "not_ready"
    assert by_configuration["D0_DETACHED"]["useful_completion"] is False
    assert by_configuration["A1_COUPLED"]["useful_completion"] is False
