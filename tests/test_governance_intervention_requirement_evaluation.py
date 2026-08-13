from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_outcome_measurement import (
    GovernanceInterventionOutcomeMeasurement,
)
from backend.app.gagf.governance_intervention_requirement_evaluation import (
    GOVERNANCE_INTERVENTION_REQUIREMENT_EVALUATION_ID,
    GOVERNANCE_INTERVENTION_REQUIREMENT_EVALUATION_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_REQUIREMENT_EVALUATION_VERSION,
    GovernanceInterventionRequirementEvaluationDisposition,
    GovernanceInterventionRequirementEvaluationLineageError,
    GovernanceInterventionRequirementEvaluator,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationOperator,
    GovernanceInterventionVerificationRequirementBuilder,
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


def make_requirement(
    *,
    operator=GovernanceInterventionVerificationOperator.LTE,
    target_value=120.0,
    measurement_window_seconds=86400,
    minimum_record_count=10,
):
    contract = verified_contract()

    return GovernanceInterventionVerificationRequirementBuilder.build(
        actuation_contract=contract,
        legacy_requirement=LEGACY_REQUIREMENT,
        requirement_id="approval-latency-rule",
        description="Governed approval latency threshold.",
        metric_id="approval_latency_seconds",
        operator=operator,
        target_value=target_value,
        unit="seconds",
        measurement_window_seconds=measurement_window_seconds,
        minimum_record_count=minimum_record_count,
    )


def make_measurement(
    requirement,
    *,
    observed_value=95.0,
    measurement_window_seconds=86400,
    record_count=42,
):
    payload = {
        "measurement_id": "governance-intervention-outcome-measurement",
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": requirement.tenant_id,
        "contract_hash": requirement.actuation_contract_hash,
        "execution_receipt_hash": "receipt-hash-1",
        "observation_hash": "observation-hash-1",
        "intervention_id": requirement.intervention_id,
        "intervention_type": requirement.intervention_type,
        "requirement_id": requirement.requirement_id,
        "requirement_hash": requirement.requirement_hash,
        "metric_id": requirement.metric_id,
        "observed_value": float(observed_value),
        "unit": requirement.unit,
        "measurement_window_seconds": measurement_window_seconds,
        "record_count": record_count,
    }

    return GovernanceInterventionOutcomeMeasurement(
        **payload,
        measurement_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def evaluate(
    *,
    operator=GovernanceInterventionVerificationOperator.LTE,
    target_value=120.0,
    observed_value=95.0,
    required_window=86400,
    actual_window=86400,
    minimum_record_count=10,
    actual_record_count=42,
):
    requirement = make_requirement(
        operator=operator,
        target_value=target_value,
        measurement_window_seconds=required_window,
        minimum_record_count=minimum_record_count,
    )

    measurement = make_measurement(
        requirement,
        observed_value=observed_value,
        measurement_window_seconds=actual_window,
        record_count=actual_record_count,
    )

    result = GovernanceInterventionRequirementEvaluator.evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    return requirement, measurement, result


def test_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_REQUIREMENT_EVALUATION_ID
        == "governance-intervention-requirement-evaluation"
    )

    assert (
        GOVERNANCE_INTERVENTION_REQUIREMENT_EVALUATION_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_REQUIREMENT_EVALUATION_SCHEMA_VERSION
        == "1.0.0"
    )


@pytest.mark.parametrize(
    (
        "operator",
        "observed_value",
        "target_value",
    ),
    (
        (
            GovernanceInterventionVerificationOperator.EQ,
            120.0,
            120.0,
        ),
        (
            GovernanceInterventionVerificationOperator.NE,
            119.0,
            120.0,
        ),
        (
            GovernanceInterventionVerificationOperator.LT,
            119.0,
            120.0,
        ),
        (
            GovernanceInterventionVerificationOperator.LTE,
            120.0,
            120.0,
        ),
        (
            GovernanceInterventionVerificationOperator.GT,
            121.0,
            120.0,
        ),
        (
            GovernanceInterventionVerificationOperator.GTE,
            120.0,
            120.0,
        ),
    ),
)
def test_all_governed_operators_can_satisfy(
    operator,
    observed_value,
    target_value,
):
    _, _, result = evaluate(
        operator=operator,
        observed_value=observed_value,
        target_value=target_value,
    )

    assert result.evidence_sufficient is True
    assert result.comparison_satisfied is True
    assert (
        result.disposition
        is GovernanceInterventionRequirementEvaluationDisposition.SATISFIED
    )


@pytest.mark.parametrize(
    (
        "operator",
        "observed_value",
        "target_value",
    ),
    (
        (
            GovernanceInterventionVerificationOperator.EQ,
            119.0,
            120.0,
        ),
        (
            GovernanceInterventionVerificationOperator.NE,
            120.0,
            120.0,
        ),
        (
            GovernanceInterventionVerificationOperator.LT,
            120.0,
            120.0,
        ),
        (
            GovernanceInterventionVerificationOperator.LTE,
            121.0,
            120.0,
        ),
        (
            GovernanceInterventionVerificationOperator.GT,
            120.0,
            120.0,
        ),
        (
            GovernanceInterventionVerificationOperator.GTE,
            119.0,
            120.0,
        ),
    ),
)
def test_all_governed_operators_can_fail(
    operator,
    observed_value,
    target_value,
):
    _, _, result = evaluate(
        operator=operator,
        observed_value=observed_value,
        target_value=target_value,
    )

    assert result.evidence_sufficient is True
    assert result.comparison_satisfied is False
    assert (
        result.disposition
        is GovernanceInterventionRequirementEvaluationDisposition
        .NOT_SATISFIED
    )


def test_insufficient_window_precedes_comparison():
    _, _, result = evaluate(
        observed_value=95.0,
        target_value=120.0,
        required_window=86400,
        actual_window=60,
    )

    assert result.evidence_sufficient is False
    assert result.comparison_satisfied is None

    assert (
        result.disposition
        is GovernanceInterventionRequirementEvaluationDisposition
        .INSUFFICIENT_EVIDENCE
    )


def test_insufficient_record_count_precedes_comparison():
    _, _, result = evaluate(
        observed_value=95.0,
        target_value=120.0,
        minimum_record_count=10,
        actual_record_count=1,
    )

    assert result.evidence_sufficient is False
    assert result.comparison_satisfied is None

    assert (
        result.disposition
        is GovernanceInterventionRequirementEvaluationDisposition
        .INSUFFICIENT_EVIDENCE
    )


def test_both_evidence_thresholds_must_be_satisfied():
    _, _, result = evaluate(
        required_window=86400,
        actual_window=60,
        minimum_record_count=10,
        actual_record_count=1,
    )

    assert result.evidence_sufficient is False
    assert result.comparison_satisfied is None

    assert (
        result.disposition
        is GovernanceInterventionRequirementEvaluationDisposition
        .INSUFFICIENT_EVIDENCE
    )


def test_exact_evidence_thresholds_are_sufficient():
    _, _, result = evaluate(
        required_window=86400,
        actual_window=86400,
        minimum_record_count=10,
        actual_record_count=10,
    )

    assert result.evidence_sufficient is True


def test_evaluation_binds_rule_and_measurement_inputs():
    requirement, measurement, result = evaluate()

    assert result.verify() is True

    assert result.tenant_id == requirement.tenant_id

    assert (
        result.contract_hash
        == requirement.actuation_contract_hash
    )

    assert result.requirement_id == requirement.requirement_id
    assert result.requirement_hash == requirement.requirement_hash
    assert result.measurement_hash == measurement.measurement_hash
    assert result.observation_hash == measurement.observation_hash

    assert (
        result.execution_receipt_hash
        == measurement.execution_receipt_hash
    )

    assert result.metric_id == requirement.metric_id
    assert result.operator is requirement.operator
    assert result.target_value == requirement.target_value
    assert result.observed_value == measurement.observed_value
    assert result.unit == requirement.unit


def test_evaluation_is_deterministic():
    first = evaluate()[-1]
    second = evaluate()[-1]

    assert first == second
    assert first.evaluation_hash == second.evaluation_hash


def test_evaluation_is_frozen():
    result = evaluate()[-1]

    with pytest.raises(FrozenInstanceError):
        result.disposition = (
            GovernanceInterventionRequirementEvaluationDisposition
            .NOT_SATISFIED
        )


def test_tampered_evaluation_fails_verification():
    result = evaluate()[-1]

    tampered = replace(
        result,
        observed_value=999.0,
    )

    assert tampered.verify() is False


def test_rejects_tampered_requirement():
    requirement = make_requirement()
    measurement = make_measurement(requirement)

    tampered = replace(
        requirement,
        target_value=999.0,
    )

    assert tampered.verify() is False

    with pytest.raises(
        GovernanceInterventionRequirementEvaluationLineageError
    ):
        GovernanceInterventionRequirementEvaluator.evaluate(
            requirement=tampered,
            measurement=measurement,
        )


def test_rejects_tampered_measurement():
    requirement = make_requirement()
    measurement = make_measurement(requirement)

    tampered = replace(
        measurement,
        observed_value=999.0,
    )

    assert tampered.verify() is False

    with pytest.raises(
        GovernanceInterventionRequirementEvaluationLineageError
    ):
        GovernanceInterventionRequirementEvaluator.evaluate(
            requirement=requirement,
            measurement=tampered,
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("tenant_id", "tenant-b"),
        ("contract_hash", "wrong-contract"),
        ("intervention_id", "wrong-intervention"),
        ("intervention_type", "WRONG_TYPE"),
        ("requirement_id", "wrong-requirement"),
        ("requirement_hash", "wrong-requirement-hash"),
        ("metric_id", "wrong_metric"),
        ("unit", "milliseconds"),
    ),
)
def test_rejects_rehashed_measurement_lineage_mismatch(
    field_name,
    bad_value,
):
    requirement = make_requirement()
    measurement = make_measurement(requirement)

    mismatched = replace(
        measurement,
        **{
            field_name: bad_value,
        },
    )

    mismatched = replace(
        mismatched,
        measurement_hash=sha256_hex(
            canonical_json(
                mismatched.payload()
            )
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionRequirementEvaluationLineageError
    ):
        GovernanceInterventionRequirementEvaluator.evaluate(
            requirement=requirement,
            measurement=mismatched,
        )


def test_serialization_contains_evaluation_hash():
    result = evaluate()[-1]

    serialized = result.to_dict()

    assert serialized["evaluation_hash"] == result.evaluation_hash
    assert serialized["operator"] == "LTE"
    assert serialized["disposition"] == "SATISFIED"
    assert serialized["evidence_sufficient"] is True
    assert serialized["comparison_satisfied"] is True


def test_insufficient_evidence_serialization_preserves_null_comparison():
    result = evaluate(
        actual_record_count=1,
    )[-1]

    serialized = result.to_dict()

    assert serialized["evidence_sufficient"] is False
    assert serialized["comparison_satisfied"] is None
    assert serialized["disposition"] == "INSUFFICIENT_EVIDENCE"


def test_evaluation_contains_no_verification_or_success_judgment():
    result = evaluate()[-1]

    serialized = result.to_dict()

    forbidden_fields = {
        "verified",
        "not_verified",
        "verification_result",
        "verification_disposition",
        "success",
        "intervention_success",
        "outcome_achieved",
        "caused_by_intervention",
        "authorize",
        "authorized",
        "next_action",
        "policy_action",
    }

    assert forbidden_fields.isdisjoint(serialized)


def test_evaluator_exposes_no_execution_or_authorization_methods():
    forbidden_methods = (
        "execute",
        "dispatch",
        "actuate",
        "authorize",
        "approve",
        "rollback",
        "verify_outcome",
        "determine_success",
        "issue_verification",
    )

    for method_name in forbidden_methods:
        assert not hasattr(
            GovernanceInterventionRequirementEvaluator,
            method_name,
        )