from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.scientific_calculation_contract import (
    ADAPTIVE_STATE_NORMALIZATION_CONTRACT,
    CALCULATION_CONTRACTS,
    EVIDENCE_CONFIDENCE_CONTRACT,
    LEGACY_METRIC_CONFIDENCE_CONTRACT,
    CalculationAuthority,
    CalculationStatus,
    ScientificCalculationContract,
    get_calculation_contract,
    list_calculation_contracts,
)


def test_registry_contains_current_calculation_contracts():
    assert set(CALCULATION_CONTRACTS) == {
        "adaptive-state-normalization",
        "evidence-confidence",
        "metric-adapter-evidence-confidence",
    }


def test_evidence_confidence_contract_matches_runtime_identity():
    assert EVIDENCE_CONFIDENCE_CONTRACT.to_metadata() == {
        "calculation_id": "evidence-confidence",
        "calculation_version": "0.1.0-diagnostics",
        "calculation_status": "PROVISIONAL_HEURISTIC",
        "authority": "NON_AUTHORITATIVE",
    }


def test_legacy_confidence_contract_matches_runtime_identity():
    assert LEGACY_METRIC_CONFIDENCE_CONTRACT.to_metadata() == {
        "calculation_id": "metric-adapter-evidence-confidence",
        "calculation_version": "0.1.0-legacy",
        "calculation_status": "LEGACY_HEURISTIC",
        "authority": "NON_AUTHORITATIVE",
    }


def test_normalization_contract_matches_runtime_identity():
    assert ADAPTIVE_STATE_NORMALIZATION_CONTRACT.to_metadata() == {
        "calculation_id": "adaptive-state-normalization",
        "calculation_version": "0.1.0-legacy",
        "calculation_status": "LEGACY_HEURISTIC",
        "authority": "NON_AUTHORITATIVE",
    }


def test_contract_is_immutable():
    with pytest.raises(FrozenInstanceError):
        EVIDENCE_CONFIDENCE_CONTRACT.calculation_version = "changed"


def test_registry_is_read_only():
    with pytest.raises(TypeError):
        CALCULATION_CONTRACTS["new-calculation"] = (
            EVIDENCE_CONFIDENCE_CONTRACT
        )


def test_get_calculation_contract_returns_registered_contract():
    contract = get_calculation_contract("evidence-confidence")

    assert contract is EVIDENCE_CONFIDENCE_CONTRACT


def test_get_calculation_contract_rejects_unknown_identity():
    with pytest.raises(
        KeyError,
        match="Unknown scientific calculation",
    ):
        get_calculation_contract("unknown-calculation")


def test_list_contracts_is_deterministically_sorted():
    contracts = list_calculation_contracts()
    identifiers = [
        contract.calculation_id
        for contract in contracts
    ]

    assert identifiers == sorted(identifiers)


def test_list_contracts_filters_by_status():
    contracts = list_calculation_contracts(
        status=CalculationStatus.LEGACY_HEURISTIC
    )

    assert {
        contract.calculation_id
        for contract in contracts
    } == {
        "adaptive-state-normalization",
        "metric-adapter-evidence-confidence",
    }


def test_list_contracts_filters_by_authority():
    contracts = list_calculation_contracts(
        authority=CalculationAuthority.NON_AUTHORITATIVE
    )

    assert len(contracts) == 3


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("calculation_id", ""),
        ("calculation_version", " "),
        ("description", ""),
    ],
)
def test_contract_rejects_empty_required_text(
    field_name,
    field_value,
):
    values = {
        "calculation_id": "test-calculation",
        "calculation_version": "1.0.0",
        "calculation_status": CalculationStatus.RESEARCH_CONSTRUCT,
        "authority": CalculationAuthority.NON_AUTHORITATIVE,
        "description": "Test calculation.",
    }
    values[field_name] = field_value

    with pytest.raises(
        ValueError,
        match=f"{field_name} must be a non-empty string",
    ):
        ScientificCalculationContract(**values)


def test_metadata_returns_new_dictionary():
    first = EVIDENCE_CONFIDENCE_CONTRACT.to_metadata()
    second = EVIDENCE_CONFIDENCE_CONTRACT.to_metadata()

    assert first == second
    assert first is not second
