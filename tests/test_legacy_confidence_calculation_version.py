from backend.app.gagf.metric_adapter import (
    LEGACY_CONFIDENCE_CALCULATION_AUTHORITY,
    LEGACY_CONFIDENCE_CALCULATION_ID,
    LEGACY_CONFIDENCE_CALCULATION_STATUS,
    LEGACY_CONFIDENCE_CALCULATION_VERSION,
    MetricAdapter,
)


def test_legacy_confidence_calculation_has_stable_identity():
    assert (
        LEGACY_CONFIDENCE_CALCULATION_ID
        == "metric-adapter-evidence-confidence"
    )
    assert (
        LEGACY_CONFIDENCE_CALCULATION_VERSION
        == "0.1.0-legacy"
    )


def test_legacy_confidence_calculation_is_explicitly_legacy():
    assert (
        LEGACY_CONFIDENCE_CALCULATION_STATUS
        == "LEGACY_HEURISTIC"
    )


def test_legacy_confidence_calculation_is_non_authoritative():
    assert (
        LEGACY_CONFIDENCE_CALCULATION_AUTHORITY
        == "NON_AUTHORITATIVE"
    )


def test_metric_adapter_exposes_legacy_confidence_metadata():
    metadata = (
        MetricAdapter()
        .get_legacy_confidence_calculation_metadata()
    )

    assert metadata == {
        "calculation_id": "metric-adapter-evidence-confidence",
        "calculation_version": "0.1.0-legacy",
        "calculation_status": "LEGACY_HEURISTIC",
        "authority": "NON_AUTHORITATIVE",
    }


def test_legacy_confidence_metadata_is_deterministic():
    adapter = MetricAdapter()

    first = adapter.get_legacy_confidence_calculation_metadata()
    second = adapter.get_legacy_confidence_calculation_metadata()

    assert first == second


def test_legacy_confidence_metadata_returns_new_dictionary():
    adapter = MetricAdapter()

    first = adapter.get_legacy_confidence_calculation_metadata()
    second = adapter.get_legacy_confidence_calculation_metadata()

    assert first is not second
