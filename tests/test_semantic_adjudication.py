from tools.validate_semantic_adjudication import validate


def test_semantic_adjudication_is_exactly_bound_and_internally_consistent() -> None:
    result = validate()
    assert result["passed"], result["failures"]
    assert len(result["derived_candidates"]) == 2
    assert all(
        row["closure_readiness"] == "not_ready"
        for row in result["derived_candidates"]
    )
