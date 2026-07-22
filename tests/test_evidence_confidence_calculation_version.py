from backend.app.gagf.evidence_confidence_adapter import (
    EVIDENCE_CONFIDENCE_AUTHORITY,
    EVIDENCE_CONFIDENCE_CALCULATION_ID,
    EVIDENCE_CONFIDENCE_CALCULATION_STATUS,
    EVIDENCE_CONFIDENCE_CALCULATION_VERSION,
    EvidenceConfidenceAdapter,
)


def test_evidence_confidence_calculation_has_stable_identity():
    assert EVIDENCE_CONFIDENCE_CALCULATION_ID == "evidence-confidence"
    assert (
        EVIDENCE_CONFIDENCE_CALCULATION_VERSION
        == "0.1.0-diagnostics"
    )


def test_evidence_confidence_calculation_is_provisional():
    assert (
        EVIDENCE_CONFIDENCE_CALCULATION_STATUS
        == "PROVISIONAL_HEURISTIC"
    )


def test_evidence_confidence_calculation_is_non_authoritative():
    assert EVIDENCE_CONFIDENCE_AUTHORITY == "NON_AUTHORITATIVE"


def test_adapter_exposes_calculation_metadata():
    metadata = EvidenceConfidenceAdapter().get_calculation_metadata()

    assert metadata == {
        "calculation_id": "evidence-confidence",
        "calculation_version": "0.1.0-diagnostics",
        "calculation_status": "PROVISIONAL_HEURISTIC",
        "authority": "NON_AUTHORITATIVE",
    }


def test_calculation_metadata_is_deterministic():
    adapter = EvidenceConfidenceAdapter()

    first = adapter.get_calculation_metadata()
    second = adapter.get_calculation_metadata()

    assert first == second


def test_calculation_metadata_returns_new_dictionary():
    adapter = EvidenceConfidenceAdapter()

    first = adapter.get_calculation_metadata()
    second = adapter.get_calculation_metadata()

    assert first is not second


def test_build_confidence_includes_calculation_metadata():
    result = EvidenceConfidenceAdapter().build_confidence([])

    assert result["calculation_metadata"] == {
        "calculation_id": "evidence-confidence",
        "calculation_version": "0.1.0-diagnostics",
        "calculation_status": "PROVISIONAL_HEURISTIC",
        "authority": "NON_AUTHORITATIVE",
    }


def test_versioning_does_not_change_empty_batch_score():
    result = EvidenceConfidenceAdapter().build_confidence([])

    assert result["confidence_score"] == 0.35
    assert result["confidence_band"] == "low"
