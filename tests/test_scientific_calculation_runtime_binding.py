from backend.app.gagf.evidence_confidence_adapter import (
    EVIDENCE_CONFIDENCE_AUTHORITY,
    EVIDENCE_CONFIDENCE_CALCULATION_ID,
    EVIDENCE_CONFIDENCE_CALCULATION_STATUS,
    EVIDENCE_CONFIDENCE_CALCULATION_VERSION,
    EvidenceConfidenceAdapter,
)
from backend.app.gagf.metric_adapter import (
    LEGACY_CONFIDENCE_CALCULATION_AUTHORITY,
    LEGACY_CONFIDENCE_CALCULATION_ID,
    LEGACY_CONFIDENCE_CALCULATION_STATUS,
    LEGACY_CONFIDENCE_CALCULATION_VERSION,
    NORMALIZATION_RULESET_AUTHORITY,
    NORMALIZATION_RULESET_ID,
    NORMALIZATION_RULESET_STATUS,
    NORMALIZATION_RULESET_VERSION,
    MetricAdapter,
)
from backend.app.gagf.scientific_calculation_contract import (
    ADAPTIVE_STATE_NORMALIZATION_CONTRACT,
    EVIDENCE_CONFIDENCE_CONTRACT,
    LEGACY_METRIC_CONFIDENCE_CONTRACT,
)


def test_evidence_confidence_constants_match_registry():
    assert EVIDENCE_CONFIDENCE_CALCULATION_ID == (
        EVIDENCE_CONFIDENCE_CONTRACT.calculation_id
    )
    assert EVIDENCE_CONFIDENCE_CALCULATION_VERSION == (
        EVIDENCE_CONFIDENCE_CONTRACT.calculation_version
    )
    assert EVIDENCE_CONFIDENCE_CALCULATION_STATUS == (
        EVIDENCE_CONFIDENCE_CONTRACT.calculation_status.value
    )
    assert EVIDENCE_CONFIDENCE_AUTHORITY == (
        EVIDENCE_CONFIDENCE_CONTRACT.authority.value
    )


def test_evidence_confidence_metadata_matches_registry():
    metadata = EvidenceConfidenceAdapter().get_calculation_metadata()

    assert metadata == EVIDENCE_CONFIDENCE_CONTRACT.to_metadata()


def test_evidence_confidence_metadata_is_not_registry_shared_state():
    metadata = EvidenceConfidenceAdapter().get_calculation_metadata()
    metadata["calculation_version"] = "changed"

    assert EVIDENCE_CONFIDENCE_CONTRACT.calculation_version == (
        "0.1.0-diagnostics"
    )


def test_legacy_confidence_constants_match_registry():
    assert LEGACY_CONFIDENCE_CALCULATION_ID == (
        LEGACY_METRIC_CONFIDENCE_CONTRACT.calculation_id
    )
    assert LEGACY_CONFIDENCE_CALCULATION_VERSION == (
        LEGACY_METRIC_CONFIDENCE_CONTRACT.calculation_version
    )
    assert LEGACY_CONFIDENCE_CALCULATION_STATUS == (
        LEGACY_METRIC_CONFIDENCE_CONTRACT.calculation_status.value
    )
    assert LEGACY_CONFIDENCE_CALCULATION_AUTHORITY == (
        LEGACY_METRIC_CONFIDENCE_CONTRACT.authority.value
    )


def test_legacy_confidence_metadata_matches_registry():
    metadata = (
        MetricAdapter()
        .get_legacy_confidence_calculation_metadata()
    )

    assert metadata == (
        LEGACY_METRIC_CONFIDENCE_CONTRACT.to_metadata()
    )


def test_legacy_confidence_metadata_is_not_registry_shared_state():
    metadata = (
        MetricAdapter()
        .get_legacy_confidence_calculation_metadata()
    )
    metadata["calculation_version"] = "changed"

    assert LEGACY_METRIC_CONFIDENCE_CONTRACT.calculation_version == (
        "0.1.0-legacy"
    )


def test_normalization_constants_match_registry():
    assert NORMALIZATION_RULESET_ID == (
        ADAPTIVE_STATE_NORMALIZATION_CONTRACT.calculation_id
    )
    assert NORMALIZATION_RULESET_VERSION == (
        ADAPTIVE_STATE_NORMALIZATION_CONTRACT.calculation_version
    )
    assert NORMALIZATION_RULESET_STATUS == (
        ADAPTIVE_STATE_NORMALIZATION_CONTRACT
        .calculation_status
        .value
    )
    assert NORMALIZATION_RULESET_AUTHORITY == (
        ADAPTIVE_STATE_NORMALIZATION_CONTRACT.authority.value
    )


def test_normalization_metadata_maps_registry_contract_keys():
    metadata = MetricAdapter().get_normalization_ruleset_metadata()

    assert metadata == {
        "ruleset_id": (
            ADAPTIVE_STATE_NORMALIZATION_CONTRACT.calculation_id
        ),
        "ruleset_version": (
            ADAPTIVE_STATE_NORMALIZATION_CONTRACT
            .calculation_version
        ),
        "ruleset_status": (
            ADAPTIVE_STATE_NORMALIZATION_CONTRACT
            .calculation_status
            .value
        ),
        "authority": (
            ADAPTIVE_STATE_NORMALIZATION_CONTRACT
            .authority
            .value
        ),
    }


def test_normalization_metadata_is_not_registry_shared_state():
    metadata = MetricAdapter().get_normalization_ruleset_metadata()
    metadata["ruleset_version"] = "changed"

    assert (
        ADAPTIVE_STATE_NORMALIZATION_CONTRACT
        .calculation_version
        == "0.1.0-legacy"
    )


def test_all_runtime_contracts_remain_non_authoritative():
    assert (
        EvidenceConfidenceAdapter()
        .get_calculation_metadata()["authority"]
        == "NON_AUTHORITATIVE"
    )
    assert (
        MetricAdapter()
        .get_legacy_confidence_calculation_metadata()["authority"]
        == "NON_AUTHORITATIVE"
    )
    assert (
        MetricAdapter()
        .get_normalization_ruleset_metadata()["authority"]
        == "NON_AUTHORITATIVE"
    )
