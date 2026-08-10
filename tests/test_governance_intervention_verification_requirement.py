from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from math import inf, nan

import pytest

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GOVERNANCE_INTERVENTION_VERIFICATION_REQUIREMENT_ID,
    GOVERNANCE_INTERVENTION_VERIFICATION_REQUIREMENT_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_VERIFICATION_REQUIREMENT_VERSION,
    GovernanceInterventionVerificationOperator,
    GovernanceInterventionVerificationRequirementBuilder,
    GovernanceInterventionVerificationRequirementLineageError,
    GovernanceInterventionVerificationRequirementValueError,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


LEGACY_REQUIREMENT = "Verify approval latency."


def make_contract() -> GovernanceInterventionActuationContract:
    return GovernanceInterventionActuationContract(
        contract_id="governance-intervention-actuation-contract",
        contract_version="0.1.0",
        schema_version="1.0.0",
        tenant_id="tenant-a",
        binding_hash="binding-hash",
        authorization_receipt_hash="authorization-hash",
        execution_context_hash="context-hash",
        intervention_id="intervention-1",
        intervention_type="POLICY_CHANGE",
        requested_effect="reduce approval delay",
        effect_boundary="approval workflow only",
        preconditions=("approval system reachable",),
        abort_criteria=("error budget exceeded",),
        rollback_strategy="restore prior approval policy",
        max_attempts=3,
        timeout_seconds=30,
        verification_requirements=(
            LEGACY_REQUIREMENT,
            "Verify audit evidence continuity.",
        ),
        contract_hash="",
    )


def verified_contract() -> GovernanceInterventionActuationContract:
    contract = make_contract()

    payload = contract.to_dict()
    payload.pop("contract_hash")

    return replace(
        contract,
        contract_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def build_requirement(
    *,
    operator=GovernanceInterventionVerificationOperator.LTE,
    target_value=120.0,
    measurement_window_seconds=86400,
    minimum_record_count=10,
):
    return GovernanceInterventionVerificationRequirementBuilder.build(
        actuation_contract=verified_contract(),
        legacy_requirement=LEGACY_REQUIREMENT,
        requirement_id="approval-latency-lte-120",
        description=(
            "Approval latency must be no greater than "
            "120 seconds after intervention."
        ),
        metric_id="approval_latency_seconds",
        operator=operator,
        target_value=target_value,
        unit="seconds",
        measurement_window_seconds=measurement_window_seconds,
        minimum_record_count=minimum_record_count,
    )


def test_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_REQUIREMENT_ID
        == "governance-intervention-verification-requirement"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_REQUIREMENT_VERSION
        == "0.1.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_VERIFICATION_REQUIREMENT_SCHEMA_VERSION
        == "1.0.0"
    )


@pytest.mark.parametrize(
    ("operator", "expected_value"),
    (
        (GovernanceInterventionVerificationOperator.EQ, "EQ"),
        (GovernanceInterventionVerificationOperator.NE, "NE"),
        (GovernanceInterventionVerificationOperator.LT, "LT"),
        (GovernanceInterventionVerificationOperator.LTE, "LTE"),
        (GovernanceInterventionVerificationOperator.GT, "GT"),
        (GovernanceInterventionVerificationOperator.GTE, "GTE"),
    ),
)
def test_supports_governed_operator_vocabulary(
    operator,
    expected_value,
):
    requirement = build_requirement(
        operator=operator
    )

    assert requirement.operator is operator
    assert requirement.to_dict()["operator"] == expected_value
    assert requirement.verify() is True


def test_builds_structured_requirement_from_verified_contract():
    contract = verified_contract()

    requirement = (
        GovernanceInterventionVerificationRequirementBuilder.build(
            actuation_contract=contract,
            legacy_requirement=LEGACY_REQUIREMENT,
            requirement_id="approval-latency-lte-120",
            description=(
                "Approval latency must be no greater "
                "than 120 seconds."
            ),
            metric_id="approval_latency_seconds",
            operator=GovernanceInterventionVerificationOperator.LTE,
            target_value=120,
            unit="seconds",
            measurement_window_seconds=86400,
            minimum_record_count=10,
        )
    )

    assert requirement.verify() is True
    assert requirement.tenant_id == contract.tenant_id
    assert (
        requirement.actuation_contract_hash
        == contract.contract_hash
    )
    assert requirement.intervention_id == contract.intervention_id
    assert requirement.intervention_type == contract.intervention_type
    assert requirement.legacy_requirement == LEGACY_REQUIREMENT
    assert requirement.metric_id == "approval_latency_seconds"
    assert requirement.target_value == 120.0
    assert requirement.unit == "seconds"
    assert requirement.measurement_window_seconds == 86400
    assert requirement.minimum_record_count == 10


def test_requirement_hash_is_deterministic():
    first = build_requirement()
    second = build_requirement()

    assert first == second
    assert first.requirement_hash == second.requirement_hash


def test_serialization_contains_requirement_hash():
    requirement = build_requirement()

    serialized = requirement.to_dict()

    assert (
        serialized["requirement_hash"]
        == requirement.requirement_hash
    )
    assert serialized["metric_id"] == "approval_latency_seconds"
    assert serialized["operator"] == "LTE"
    assert serialized["target_value"] == 120.0


def test_requirement_is_frozen():
    requirement = build_requirement()

    with pytest.raises(FrozenInstanceError):
        requirement.metric_id = "tampered_metric"


def test_tampered_requirement_fails_verification():
    requirement = build_requirement()

    tampered = replace(
        requirement,
        target_value=999.0,
    )

    assert tampered.verify() is False


def test_rejects_tampered_actuation_contract():
    contract = verified_contract()

    tampered = replace(
        contract,
        requested_effect="tampered requested effect",
    )

    assert tampered.verify() is False

    with pytest.raises(
        GovernanceInterventionVerificationRequirementLineageError
    ):
        GovernanceInterventionVerificationRequirementBuilder.build(
            actuation_contract=tampered,
            legacy_requirement=LEGACY_REQUIREMENT,
            requirement_id="approval-latency-lte-120",
            description="description",
            metric_id="approval_latency_seconds",
            operator=GovernanceInterventionVerificationOperator.LTE,
            target_value=120,
            unit="seconds",
            measurement_window_seconds=86400,
            minimum_record_count=10,
        )


def test_rejects_requirement_not_present_in_actuation_contract():
    contract = verified_contract()

    with pytest.raises(
        GovernanceInterventionVerificationRequirementLineageError
    ):
        GovernanceInterventionVerificationRequirementBuilder.build(
            actuation_contract=contract,
            legacy_requirement="Invented after execution.",
            requirement_id="invented-rule",
            description="invented rule",
            metric_id="invented_metric",
            operator=GovernanceInterventionVerificationOperator.EQ,
            target_value=1,
            unit="count",
            measurement_window_seconds=60,
            minimum_record_count=1,
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("legacy_requirement", " "),
        ("requirement_id", ""),
        ("description", "   "),
        ("metric_id", ""),
        ("unit", " "),
    ),
)
def test_rejects_blank_required_text(
    field_name,
    bad_value,
):
    kwargs = {
        "actuation_contract": verified_contract(),
        "legacy_requirement": LEGACY_REQUIREMENT,
        "requirement_id": "approval-latency-lte-120",
        "description": "description",
        "metric_id": "approval_latency_seconds",
        "operator": GovernanceInterventionVerificationOperator.LTE,
        "target_value": 120,
        "unit": "seconds",
        "measurement_window_seconds": 86400,
        "minimum_record_count": 10,
    }

    kwargs[field_name] = bad_value

    with pytest.raises(
        GovernanceInterventionVerificationRequirementValueError
    ):
        GovernanceInterventionVerificationRequirementBuilder.build(
            **kwargs
        )


def test_rejects_uncontrolled_operator_value():
    with pytest.raises(
        GovernanceInterventionVerificationRequirementValueError
    ):
        GovernanceInterventionVerificationRequirementBuilder.build(
            actuation_contract=verified_contract(),
            legacy_requirement=LEGACY_REQUIREMENT,
            requirement_id="approval-latency-rule",
            description="description",
            metric_id="approval_latency_seconds",
            operator="LTE",
            target_value=120,
            unit="seconds",
            measurement_window_seconds=86400,
            minimum_record_count=10,
        )


@pytest.mark.parametrize(
    "target_value",
    (
        nan,
        inf,
        -inf,
    ),
)
def test_rejects_nonfinite_target_value(
    target_value,
):
    with pytest.raises(
        GovernanceInterventionVerificationRequirementValueError
    ):
        build_requirement(
            target_value=target_value
        )


@pytest.mark.parametrize(
    "measurement_window_seconds",
    (
        0,
        -1,
        -86400,
    ),
)
def test_rejects_invalid_measurement_window(
    measurement_window_seconds,
):
    with pytest.raises(
        GovernanceInterventionVerificationRequirementValueError
    ):
        build_requirement(
            measurement_window_seconds=measurement_window_seconds
        )


@pytest.mark.parametrize(
    "minimum_record_count",
    (
        0,
        -1,
        -100,
    ),
)
def test_rejects_invalid_minimum_record_count(
    minimum_record_count,
):
    with pytest.raises(
        GovernanceInterventionVerificationRequirementValueError
    ):
        build_requirement(
            minimum_record_count=minimum_record_count
        )


def test_structured_rule_retains_exact_legacy_requirement():
    requirement = build_requirement()

    assert requirement.legacy_requirement == LEGACY_REQUIREMENT


def test_requirement_contains_no_observation_or_judgment():
    requirement = build_requirement()

    serialized = requirement.to_dict()

    forbidden_fields = {
        "observed_value",
        "observation_hash",
        "observation_result",
        "verified",
        "success",
        "outcome_achieved",
        "verification_result",
        "verification_disposition",
        "evaluation_result",
    }

    assert forbidden_fields.isdisjoint(serialized)


def test_builder_has_no_evaluation_execution_or_commitment_methods():
    forbidden_methods = (
        "execute",
        "dispatch",
        "actuate",
        "observe",
        "evaluate",
        "verify_outcome",
        "determine_success",
        "commit",
        "authorize",
        "rollback",
    )

    for method_name in forbidden_methods:
        assert not hasattr(
            GovernanceInterventionVerificationRequirementBuilder,
            method_name,
        )