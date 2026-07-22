from pathlib import Path


CONTRACT_PATH = Path("docs/EVIDENCE_CONFIDENCE_CONTRACTS.md")


def read_contract() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8-sig")


def test_evidence_confidence_contract_document_exists():
    assert CONTRACT_PATH.is_file()


def test_contract_identifies_diagnostics_calculation():
    content = read_contract()

    assert "evidence-confidence" in content
    assert "0.1.0-diagnostics" in content
    assert "PROVISIONAL_HEURISTIC" in content
    assert "NON_AUTHORITATIVE" in content


def test_contract_identifies_legacy_calculation():
    content = read_contract()

    assert "metric-adapter-evidence-confidence" in content
    assert "0.1.0-legacy" in content
    assert "LEGACY_HEURISTIC" in content


def test_contract_documents_precision_difference():
    content = read_contract()

    assert "four decimal places" in content.lower()
    assert "three decimal places" in content.lower()


def test_contract_prohibits_silent_calculator_substitution():
    content = read_contract()

    assert "No silent calculator substitution" in content
    assert "explicit migration story" in content


def test_contract_preserves_additive_response_compatibility():
    content = read_contract()

    assert "Additive response evolution" in content
    assert "must remain stable" in content


def test_contract_requires_replay_for_consolidation():
    content = read_contract()

    assert "Replay requirement" in content
    assert "deterministic replay" in content


def test_contract_preserves_non_authoritative_status():
    content = read_contract()

    assert "No authority escalation" in content
    assert "constitutional contract" in content


def test_contract_documents_diagnostics_output_keys():
    content = read_contract()

    expected_keys = {
        "event_count",
        "diagnostic_score",
        "confidence_score",
        "confidence_band",
        "evidence_confidence",
        "calculation_metadata",
    }

    for key in expected_keys:
        assert f"`{key}`" in content


def test_contract_documents_legacy_factor_keys():
    content = read_contract()

    expected_factors = {
        "timestamp_quality",
        "sensor_reliability",
        "cross_source_agreement",
        "telemetry_completeness",
    }

    for factor in expected_factors:
        assert f"`{factor}`" in content
