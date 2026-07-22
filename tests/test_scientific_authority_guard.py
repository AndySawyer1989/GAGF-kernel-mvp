from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.scientific_authority_guard import (
    AUTHORITY_POLICY_ID,
    AUTHORITY_POLICY_VERSION,
    AuthorityEscalationEvidence,
    ScientificAuthorityEscalationGuard,
)
from backend.app.gagf.scientific_calculation_contract import (
    EVIDENCE_CONFIDENCE_CONTRACT,
    LEGACY_METRIC_CONFIDENCE_CONTRACT,
    CalculationAuthority,
    CalculationStatus,
    ScientificCalculationContract,
)


def complete_evidence() -> AuthorityEscalationEvidence:
    return AuthorityEscalationEvidence(
        deterministic_replay_verified=True,
        canonical_input_binding_verified=True,
        calculation_version_frozen=True,
        regression_suite_passed=True,
        validation_report_present=True,
        constitutional_approval_present=True,
    )


def validated_contract() -> ScientificCalculationContract:
    return ScientificCalculationContract(
        calculation_id="validated-test-calculation",
        calculation_version="1.0.0",
        calculation_status=CalculationStatus.VALIDATED,
        authority=CalculationAuthority.NON_AUTHORITATIVE,
        description="Validated calculation used by policy tests.",
    )


def test_authority_policy_has_stable_identity():
    assert AUTHORITY_POLICY_ID == "scientific-authority-escalation"
    assert AUTHORITY_POLICY_VERSION == "0.1.0"


def test_authority_evidence_is_immutable():
    evidence = complete_evidence()

    with pytest.raises(FrozenInstanceError):
        evidence.regression_suite_passed = False


def test_missing_requirements_are_deterministic():
    evidence = AuthorityEscalationEvidence(
        deterministic_replay_verified=False,
        canonical_input_binding_verified=True,
        calculation_version_frozen=False,
        regression_suite_passed=True,
        validation_report_present=False,
        constitutional_approval_present=True,
    )

    assert evidence.missing_requirements() == (
        "deterministic_replay_verified",
        "calculation_version_frozen",
        "validation_report_present",
    )


def test_same_authority_is_allowed():
    decision = ScientificAuthorityEscalationGuard().evaluate(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.NON_AUTHORITATIVE,
        evidence=complete_evidence(),
    )

    assert decision.allowed is True
    assert decision.missing_requirements == ()


def test_authority_reduction_is_allowed():
    authoritative_contract = ScientificCalculationContract(
        calculation_id="authoritative-test",
        calculation_version="1.0.0",
        calculation_status=CalculationStatus.VALIDATED,
        authority=CalculationAuthority.AUTHORITATIVE,
        description="Authoritative test contract.",
    )

    decision = ScientificAuthorityEscalationGuard().evaluate(
        contract=authoritative_contract,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert decision.allowed is True


def test_legacy_calculation_cannot_become_advisory():
    decision = ScientificAuthorityEscalationGuard().evaluate(
        contract=LEGACY_METRIC_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert decision.allowed is False
    assert "Legacy or deprecated" in decision.reason


def test_provisional_calculation_requires_advisory_evidence():
    evidence = AuthorityEscalationEvidence(
        deterministic_replay_verified=False,
        canonical_input_binding_verified=False,
        calculation_version_frozen=True,
        regression_suite_passed=False,
        validation_report_present=False,
        constitutional_approval_present=False,
    )

    decision = ScientificAuthorityEscalationGuard().evaluate(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=evidence,
    )

    assert decision.allowed is False
    assert decision.missing_requirements == (
        "deterministic_replay_verified",
        "regression_suite_passed",
    )


def test_provisional_calculation_may_become_advisory():
    decision = ScientificAuthorityEscalationGuard().evaluate(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    assert decision.allowed is True


def test_provisional_calculation_cannot_become_authoritative():
    decision = ScientificAuthorityEscalationGuard().evaluate(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.AUTHORITATIVE,
        evidence=complete_evidence(),
    )

    assert decision.allowed is False
    assert decision.reason == (
        "Only validated calculations may become authoritative."
    )


def test_validated_calculation_requires_all_authoritative_evidence():
    evidence = AuthorityEscalationEvidence(
        deterministic_replay_verified=True,
        canonical_input_binding_verified=False,
        calculation_version_frozen=True,
        regression_suite_passed=True,
        validation_report_present=True,
        constitutional_approval_present=False,
    )

    decision = ScientificAuthorityEscalationGuard().evaluate(
        contract=validated_contract(),
        requested_authority=CalculationAuthority.AUTHORITATIVE,
        evidence=evidence,
    )

    assert decision.allowed is False
    assert decision.missing_requirements == (
        "canonical_input_binding_verified",
        "constitutional_approval_present",
    )


def test_validated_calculation_may_become_authoritative():
    decision = ScientificAuthorityEscalationGuard().evaluate(
        contract=validated_contract(),
        requested_authority=CalculationAuthority.AUTHORITATIVE,
        evidence=complete_evidence(),
    )

    assert decision.allowed is True
    assert decision.missing_requirements == ()


def test_decision_serialization_uses_string_enum_values():
    decision = ScientificAuthorityEscalationGuard().evaluate(
        contract=validated_contract(),
        requested_authority=CalculationAuthority.AUTHORITATIVE,
        evidence=complete_evidence(),
    )

    assert decision.to_dict() == {
        "allowed": True,
        "policy_id": "scientific-authority-escalation",
        "policy_version": "0.1.0",
        "calculation_id": "validated-test-calculation",
        "calculation_version": "1.0.0",
        "current_authority": "NON_AUTHORITATIVE",
        "requested_authority": "AUTHORITATIVE",
        "reason": (
            "Authoritative escalation requirements are satisfied."
        ),
        "missing_requirements": [],
    }


def test_decision_is_immutable():
    decision = ScientificAuthorityEscalationGuard().evaluate(
        contract=validated_contract(),
        requested_authority=CalculationAuthority.AUTHORITATIVE,
        evidence=complete_evidence(),
    )

    with pytest.raises(FrozenInstanceError):
        decision.allowed = False
