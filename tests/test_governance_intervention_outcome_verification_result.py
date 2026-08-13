from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.governance_intervention_outcome_verification_result import (
    GOVERNANCE_INTERVENTION_OUTCOME_VERIFICATION_RESULT_ID,
    GOVERNANCE_INTERVENTION_OUTCOME_VERIFICATION_RESULT_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_OUTCOME_VERIFICATION_RESULT_VERSION,
    GovernanceInterventionOutcomeVerificationDisposition,
    GovernanceInterventionOutcomeVerificationResultBuilder,
    GovernanceInterventionOutcomeVerificationResultIntegrityError,
)
from backend.app.gagf.governance_intervention_requirement_evaluation import (
    GOVERNANCE_INTERVENTION_REQUIREMENT_EVALUATION_ID,
    GOVERNANCE_INTERVENTION_REQUIREMENT_EVALUATION_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_REQUIREMENT_EVALUATION_VERSION,
    GovernanceInterventionRequirementEvaluation,
    GovernanceInterventionRequirementEvaluationDisposition,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationOperator,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


def make_evaluation(
    *,
    disposition=(
        GovernanceInterventionRequirementEvaluationDisposition.SATISFIED
    ),
    evidence_sufficient=True,
    comparison_satisfied=True,
    observed_value=95.0,
):
    payload = {
        "evaluation_id": (
            GOVERNANCE_INTERVENTION_REQUIREMENT_EVALUATION_ID
        ),
        "version": (
            GOVERNANCE_INTERVENTION_REQUIREMENT_EVALUATION_VERSION
        ),
        "schema_version": (
            GOVERNANCE_INTERVENTION_REQUIREMENT_EVALUATION_SCHEMA_VERSION
        ),
        "tenant_id": "tenant-a",
        "contract_hash": "contract-hash-1",
        "intervention_id": "intervention-1",
        "intervention_type": "POLICY_CHANGE",
        "requirement_id": "approval-latency-rule",
        "requirement_hash": "requirement-hash-1",
        "measurement_hash": "measurement-hash-1",
        "observation_hash": "observation-hash-1",
        "execution_receipt_hash": "receipt-hash-1",
        "metric_id": "approval_latency_seconds",
        "operator": "LTE",
        "target_value": 120.0,
        "observed_value": observed_value,
        "unit": "seconds",
        "required_measurement_window_seconds": 86400,
        "actual_measurement_window_seconds": 86400,
        "minimum_record_count": 10,
        "actual_record_count": 42,
        "evidence_sufficient": evidence_sufficient,
        "comparison_satisfied": comparison_satisfied,
        "disposition": disposition.value,
    }

    return GovernanceInterventionRequirementEvaluation(
        evaluation_id=payload["evaluation_id"],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        contract_hash=payload["contract_hash"],
        intervention_id=payload["intervention_id"],
        intervention_type=payload["intervention_type"],
        requirement_id=payload["requirement_id"],
        requirement_hash=payload["requirement_hash"],
        measurement_hash=payload["measurement_hash"],
        observation_hash=payload["observation_hash"],
        execution_receipt_hash=payload["execution_receipt_hash"],
        metric_id=payload["metric_id"],
        operator=GovernanceInterventionVerificationOperator.LTE,
        target_value=payload["target_value"],
        observed_value=payload["observed_value"],
        unit=payload["unit"],
        required_measurement_window_seconds=payload[
            "required_measurement_window_seconds"
        ],
        actual_measurement_window_seconds=payload[
            "actual_measurement_window_seconds"
        ],
        minimum_record_count=payload["minimum_record_count"],
        actual_record_count=payload["actual_record_count"],
        evidence_sufficient=payload["evidence_sufficient"],
        comparison_satisfied=payload["comparison_satisfied"],
        disposition=disposition,
        evaluation_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def rebuild_evaluation_hash(evaluation):
    return replace(
        evaluation,
        evaluation_hash=sha256_hex(
            canonical_json(
                evaluation.payload()
            )
        ),
    )


def build_result(**kwargs):
    evaluation = make_evaluation(**kwargs)

    result = (
        GovernanceInterventionOutcomeVerificationResultBuilder.build(
            evaluation=evaluation
        )
    )

    return evaluation, result


def test_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_OUTCOME_VERIFICATION_RESULT_ID
        == "governance-intervention-outcome-verification-result"
    )

    assert (
        GOVERNANCE_INTERVENTION_OUTCOME_VERIFICATION_RESULT_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_OUTCOME_VERIFICATION_RESULT_SCHEMA_VERSION
        == "1.0.0"
    )


def test_satisfied_evaluation_maps_to_verified():
    evaluation, result = build_result(
        disposition=(
            GovernanceInterventionRequirementEvaluationDisposition
            .SATISFIED
        ),
        evidence_sufficient=True,
        comparison_satisfied=True,
    )

    assert evaluation.verify() is True
    assert result.verify() is True

    assert (
        result.verification_disposition
        is GovernanceInterventionOutcomeVerificationDisposition.VERIFIED
    )


def test_not_satisfied_evaluation_maps_to_not_verified():
    evaluation, result = build_result(
        disposition=(
            GovernanceInterventionRequirementEvaluationDisposition
            .NOT_SATISFIED
        ),
        evidence_sufficient=True,
        comparison_satisfied=False,
        observed_value=150.0,
    )

    assert evaluation.verify() is True
    assert result.verify() is True

    assert (
        result.verification_disposition
        is GovernanceInterventionOutcomeVerificationDisposition
        .NOT_VERIFIED
    )


def test_insufficient_evidence_maps_to_inconclusive():
    evaluation, result = build_result(
        disposition=(
            GovernanceInterventionRequirementEvaluationDisposition
            .INSUFFICIENT_EVIDENCE
        ),
        evidence_sufficient=False,
        comparison_satisfied=None,
    )

    assert evaluation.verify() is True
    assert result.verify() is True

    assert (
        result.verification_disposition
        is GovernanceInterventionOutcomeVerificationDisposition
        .INCONCLUSIVE
    )


def test_result_preserves_evaluation_lineage():
    evaluation, result = build_result()

    assert result.tenant_id == evaluation.tenant_id
    assert result.contract_hash == evaluation.contract_hash
    assert result.intervention_id == evaluation.intervention_id
    assert result.intervention_type == evaluation.intervention_type

    assert result.requirement_id == evaluation.requirement_id
    assert result.requirement_hash == evaluation.requirement_hash
    assert result.measurement_hash == evaluation.measurement_hash
    assert result.observation_hash == evaluation.observation_hash

    assert (
        result.execution_receipt_hash
        == evaluation.execution_receipt_hash
    )

    assert result.evaluation_hash == evaluation.evaluation_hash

    assert result.metric_id == evaluation.metric_id
    assert result.operator == evaluation.operator.value
    assert result.target_value == evaluation.target_value
    assert result.observed_value == evaluation.observed_value
    assert result.unit == evaluation.unit

    assert (
        result.evidence_sufficient
        is evaluation.evidence_sufficient
    )

    assert (
        result.comparison_satisfied
        is evaluation.comparison_satisfied
    )

    assert (
        result.evaluation_disposition
        == evaluation.disposition.value
    )


def test_result_is_deterministic():
    first = build_result()[-1]
    second = build_result()[-1]

    assert first == second
    assert first.verification_hash == second.verification_hash


def test_result_is_frozen():
    result = build_result()[-1]

    with pytest.raises(FrozenInstanceError):
        result.verification_disposition = (
            GovernanceInterventionOutcomeVerificationDisposition
            .NOT_VERIFIED
        )


def test_tampered_result_fails_verification():
    result = build_result()[-1]

    tampered = replace(
        result,
        observed_value=999.0,
    )

    assert tampered.verify() is False


def test_rejects_tampered_evaluation():
    evaluation = make_evaluation()

    tampered = replace(
        evaluation,
        observed_value=999.0,
    )

    assert tampered.verify() is False

    with pytest.raises(
        GovernanceInterventionOutcomeVerificationResultIntegrityError
    ):
        GovernanceInterventionOutcomeVerificationResultBuilder.build(
            evaluation=tampered
        )


@pytest.mark.parametrize(
    (
        "disposition",
        "evidence_sufficient",
        "comparison_satisfied",
    ),
    (
        (
            GovernanceInterventionRequirementEvaluationDisposition
            .SATISFIED,
            False,
            True,
        ),
        (
            GovernanceInterventionRequirementEvaluationDisposition
            .SATISFIED,
            True,
            False,
        ),
        (
            GovernanceInterventionRequirementEvaluationDisposition
            .SATISFIED,
            True,
            None,
        ),
        (
            GovernanceInterventionRequirementEvaluationDisposition
            .NOT_SATISFIED,
            False,
            False,
        ),
        (
            GovernanceInterventionRequirementEvaluationDisposition
            .NOT_SATISFIED,
            True,
            True,
        ),
        (
            GovernanceInterventionRequirementEvaluationDisposition
            .NOT_SATISFIED,
            True,
            None,
        ),
        (
            GovernanceInterventionRequirementEvaluationDisposition
            .INSUFFICIENT_EVIDENCE,
            True,
            None,
        ),
        (
            GovernanceInterventionRequirementEvaluationDisposition
            .INSUFFICIENT_EVIDENCE,
            False,
            True,
        ),
        (
            GovernanceInterventionRequirementEvaluationDisposition
            .INSUFFICIENT_EVIDENCE,
            False,
            False,
        ),
    ),
)
def test_rejects_rehashed_contradictory_evaluation(
    disposition,
    evidence_sufficient,
    comparison_satisfied,
):
    evaluation = make_evaluation(
        disposition=disposition,
        evidence_sufficient=evidence_sufficient,
        comparison_satisfied=comparison_satisfied,
    )

    assert evaluation.verify() is True

    with pytest.raises(
        GovernanceInterventionOutcomeVerificationResultIntegrityError
    ):
        GovernanceInterventionOutcomeVerificationResultBuilder.build(
            evaluation=evaluation
        )


def test_verified_requires_sufficient_evidence():
    evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionRequirementEvaluationDisposition
            .SATISFIED
        ),
        evidence_sufficient=False,
        comparison_satisfied=True,
    )

    evaluation = rebuild_evaluation_hash(evaluation)

    assert evaluation.verify() is True

    with pytest.raises(
        GovernanceInterventionOutcomeVerificationResultIntegrityError
    ):
        GovernanceInterventionOutcomeVerificationResultBuilder.build(
            evaluation=evaluation
        )


def test_not_verified_requires_sufficient_evidence():
    evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionRequirementEvaluationDisposition
            .NOT_SATISFIED
        ),
        evidence_sufficient=False,
        comparison_satisfied=False,
    )

    evaluation = rebuild_evaluation_hash(evaluation)

    assert evaluation.verify() is True

    with pytest.raises(
        GovernanceInterventionOutcomeVerificationResultIntegrityError
    ):
        GovernanceInterventionOutcomeVerificationResultBuilder.build(
            evaluation=evaluation
        )


def test_inconclusive_requires_null_comparison():
    evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionRequirementEvaluationDisposition
            .INSUFFICIENT_EVIDENCE
        ),
        evidence_sufficient=False,
        comparison_satisfied=True,
    )

    evaluation = rebuild_evaluation_hash(evaluation)

    assert evaluation.verify() is True

    with pytest.raises(
        GovernanceInterventionOutcomeVerificationResultIntegrityError
    ):
        GovernanceInterventionOutcomeVerificationResultBuilder.build(
            evaluation=evaluation
        )


def test_verified_serialization_is_bounded():
    result = build_result()[-1]

    serialized = result.to_dict()

    assert serialized["verification_disposition"] == "VERIFIED"
    assert serialized["evaluation_disposition"] == "SATISFIED"
    assert serialized["evidence_sufficient"] is True
    assert serialized["comparison_satisfied"] is True

    assert serialized["verification_hash"] == result.verification_hash


def test_not_verified_serialization_is_bounded():
    result = build_result(
        disposition=(
            GovernanceInterventionRequirementEvaluationDisposition
            .NOT_SATISFIED
        ),
        evidence_sufficient=True,
        comparison_satisfied=False,
        observed_value=150.0,
    )[-1]

    serialized = result.to_dict()

    assert serialized["verification_disposition"] == "NOT_VERIFIED"
    assert serialized["evaluation_disposition"] == "NOT_SATISFIED"


def test_inconclusive_serialization_preserves_uncertainty():
    result = build_result(
        disposition=(
            GovernanceInterventionRequirementEvaluationDisposition
            .INSUFFICIENT_EVIDENCE
        ),
        evidence_sufficient=False,
        comparison_satisfied=None,
    )[-1]

    serialized = result.to_dict()

    assert serialized["verification_disposition"] == "INCONCLUSIVE"
    assert serialized["evidence_sufficient"] is False
    assert serialized["comparison_satisfied"] is None


def test_result_contains_no_success_causation_or_future_action_fields():
    result = build_result()[-1]

    serialized = result.to_dict()

    forbidden_fields = {
        "success",
        "failed",
        "intervention_success",
        "intervention_failure",
        "outcome_achieved",
        "caused_by_intervention",
        "causal_effect",
        "causal_attribution",
        "rollback",
        "rollback_required",
        "continue_policy",
        "continue_intervention",
        "authorize",
        "authorized",
        "authorization",
        "next_action",
        "recommended_action",
        "policy_action",
        "future_action",
    }

    assert forbidden_fields.isdisjoint(serialized)


def test_builder_exposes_no_execution_authorization_or_causal_methods():
    forbidden_methods = (
        "execute",
        "dispatch",
        "actuate",
        "authorize",
        "approve",
        "rollback",
        "continue_intervention",
        "determine_success",
        "determine_failure",
        "attribute_causation",
        "estimate_causal_effect",
        "recommend_action",
    )

    for method_name in forbidden_methods:
        assert not hasattr(
            GovernanceInterventionOutcomeVerificationResultBuilder,
            method_name,
        )


def test_verified_means_requirement_verification_only():
    result = build_result()[-1]

    serialized = result.to_dict()

    assert serialized["verification_disposition"] == "VERIFIED"
    assert "intervention_success" not in serialized
    assert "caused_by_intervention" not in serialized
    assert "next_action" not in serialized


@pytest.mark.parametrize(
    (
        "disposition",
        "expected_verification",
    ),
    (
        (
            GovernanceInterventionRequirementEvaluationDisposition
            .SATISFIED,
            "VERIFIED",
        ),
        (
            GovernanceInterventionRequirementEvaluationDisposition
            .NOT_SATISFIED,
            "NOT_VERIFIED",
        ),
        (
            GovernanceInterventionRequirementEvaluationDisposition
            .INSUFFICIENT_EVIDENCE,
            "INCONCLUSIVE",
        ),
    ),
)
def test_mapping_is_exact_and_closed(
    disposition,
    expected_verification,
):
    if (
        disposition
        is GovernanceInterventionRequirementEvaluationDisposition
        .SATISFIED
    ):
        evidence_sufficient = True
        comparison_satisfied = True
    elif (
        disposition
        is GovernanceInterventionRequirementEvaluationDisposition
        .NOT_SATISFIED
    ):
        evidence_sufficient = True
        comparison_satisfied = False
    else:
        evidence_sufficient = False
        comparison_satisfied = None

    result = build_result(
        disposition=disposition,
        evidence_sufficient=evidence_sufficient,
        comparison_satisfied=comparison_satisfied,
    )[-1]

    assert (
        result.verification_disposition.value
        == expected_verification
    )