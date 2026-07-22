from backend.app.gagf.metric_adapter import (
    NORMALIZATION_DELTAS,
    NORMALIZATION_RULESET_AUTHORITY,
    NORMALIZATION_RULESET_ID,
    NORMALIZATION_RULESET_STATUS,
    NORMALIZATION_RULESET_VERSION,
    MetricAdapter,
)


def test_normalization_ruleset_has_stable_identity():
    assert NORMALIZATION_RULESET_ID == "adaptive-state-normalization"
    assert NORMALIZATION_RULESET_VERSION == "0.1.0-legacy"


def test_normalization_ruleset_is_explicitly_legacy():
    assert NORMALIZATION_RULESET_STATUS == "LEGACY_HEURISTIC"


def test_normalization_ruleset_is_explicitly_non_authoritative():
    assert NORMALIZATION_RULESET_AUTHORITY == "NON_AUTHORITATIVE"


def test_metric_adapter_exposes_normalization_ruleset_metadata():
    metadata = MetricAdapter().get_normalization_ruleset_metadata()

    assert metadata == {
        "ruleset_id": "adaptive-state-normalization",
        "ruleset_version": "0.1.0-legacy",
        "ruleset_status": "LEGACY_HEURISTIC",
        "authority": "NON_AUTHORITATIVE",
    }


def test_normalization_rules_remain_available():
    assert isinstance(NORMALIZATION_DELTAS, dict)
    assert len(NORMALIZATION_DELTAS) > 0


def test_normalization_rules_target_supported_adaptive_state_fields():
    supported_fields = {
        "risk_index",
        "uncertainty",
        "coherence_psi",
        "revision_pressure",
        "governance_momentum",
    }

    for indicator, delta in NORMALIZATION_DELTAS.values():
        assert indicator in supported_fields
        assert isinstance(delta, float)


def test_normalization_ruleset_metadata_is_deterministic():
    adapter = MetricAdapter()

    first = adapter.get_normalization_ruleset_metadata()
    second = adapter.get_normalization_ruleset_metadata()

    assert first == second


def test_normalization_ruleset_metadata_returns_new_dictionary():
    adapter = MetricAdapter()

    first = adapter.get_normalization_ruleset_metadata()
    second = adapter.get_normalization_ruleset_metadata()

    assert first is not second
