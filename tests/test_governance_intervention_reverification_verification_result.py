from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_intervention_reverification_requirement_evaluation import (
    GovernanceInterventionReverificationRequirementEvaluation,
    GovernanceInterventionReverificationRequirementEvaluationDisposition,
)
from backend.app.gagf.governance_intervention_reverification_verification_result import (
    GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_RESULT_ID,
    GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_RESULT_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_RESULT_VERSION,
    GovernanceInterventionReverificationVerificationDisposition,
    GovernanceInterventionReverificationVerificationResultBuilder,
    GovernanceInterventionReverificationVerificationResultIntegrityError,
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
        GovernanceInterventionReverificationRequirementEvaluationDisposition
        .SATISFIED
    ),
    evidence_sufficient: bool = True,
    comparison_satisfied: bool | None = True,
) -> GovernanceInterventionReverificationRequirementEvaluation:
    payload = {
        "evaluation_id": (
            "governance-intervention-"
            "reverification-requirement-evaluation"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": "tenant-a",
        "intervention_id": "intervention-1",
        "verification_record_hash": "record-1",
        "request_hash": "request-1",
        "work_order_hash": "work-order-1",
        "attempt_id": "attempt-1",
        "attempt_execution_id": "attempt-exec-1",
        "reverification_scope": "POLICY",
        "evidence_hash": "evidence-1",
        "measurement_hash": "measurement-1",
        "actuation_contract_hash": "contract-1",
        "intervention_type": "policy-update",
        "requirement_id": "requirement-1",
        "requirement_hash": "requirement-hash-1",
        "metric_id": "metric-1",
        "operator": (
            GovernanceInterventionVerificationOperator.LTE.value
        ),
        "target_value": 100.0,
        "observed_value": 90.0,
        "unit": "ms",
        "required_measurement_window_seconds": 300,
        "actual_measurement_window_seconds": 300,
        "minimum_record_count": 10,
        "actual_record_count": 10,
        "evidence_sufficient": evidence_sufficient,
        "comparison_satisfied": comparison_satisfied,
        "disposition": disposition.value,
    }

    return GovernanceInterventionReverificationRequirementEvaluation(
        evaluation_id=payload[
            "evaluation_id"
        ],
        version=payload["version"],
        schema_version=payload[
            "schema_version"
        ],
        tenant_id=payload["tenant_id"],
        intervention_id=payload[
            "intervention_id"
        ],
        verification_record_hash=payload[
            "verification_record_hash"
        ],
        request_hash=payload[
            "request_hash"
        ],
        work_order_hash=payload[
            "work_order_hash"
        ],
        attempt_id=payload[
            "attempt_id"
        ],
        attempt_execution_id=payload[
            "attempt_execution_id"
        ],
        reverification_scope=payload[
            "reverification_scope"
        ],
        evidence_hash=payload[
            "evidence_hash"
        ],
        measurement_hash=payload[
            "measurement_hash"
        ],
        actuation_contract_hash=payload[
            "actuation_contract_hash"
        ],
        intervention_type=payload[
            "intervention_type"
        ],
        requirement_id=payload[
            "requirement_id"
        ],
        requirement_hash=payload[
            "requirement_hash"
        ],
        metric_id=payload[
            "metric_id"
        ],
        operator=(
            GovernanceInterventionVerificationOperator(
                payload["operator"]
            )
        ),
        target_value=payload[
            "target_value"
        ],
        observed_value=payload[
            "observed_value"
        ],
        unit=payload["unit"],
        required_measurement_window_seconds=payload[
            "required_measurement_window_seconds"
        ],
        actual_measurement_window_seconds=payload[
            "actual_measurement_window_seconds"
        ],
        minimum_record_count=payload[
            "minimum_record_count"
        ],
        actual_record_count=payload[
            "actual_record_count"
        ],
        evidence_sufficient=payload[
            "evidence_sufficient"
        ],
        comparison_satisfied=payload[
            "comparison_satisfied"
        ],
        disposition=disposition,
        evaluation_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def build_result(
    evaluation=None,
):
    if evaluation is None:
        evaluation = make_evaluation()

    return (
        GovernanceInterventionReverificationVerificationResultBuilder
        .build(
            evaluation=evaluation
        )
    )


def rehash_evaluation(
    evaluation,
):
    return replace(
        evaluation,
        evaluation_hash=sha256_hex(
            canonical_json(
                evaluation.payload()
            )
        ),
    )


def test_result_identity_constants_are_exact():
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_RESULT_ID
        == (
            "governance-intervention-"
            "reverification-verification-result"
        )
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_RESULT_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_VERIFICATION_RESULT_SCHEMA_VERSION
        == "1.0.0"
    )


def test_satisfied_maps_to_verified():
    evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionReverificationRequirementEvaluationDisposition
            .SATISFIED
        ),
        evidence_sufficient=True,
        comparison_satisfied=True,
    )

    result = build_result(
        evaluation
    )

    assert result.verify()

    assert (
        result.verification_disposition
        is GovernanceInterventionReverificationVerificationDisposition
        .VERIFIED
    )


def test_not_satisfied_maps_to_not_verified():
    evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionReverificationRequirementEvaluationDisposition
            .NOT_SATISFIED
        ),
        evidence_sufficient=True,
        comparison_satisfied=False,
    )

    result = build_result(
        evaluation
    )

    assert (
        result.verification_disposition
        is GovernanceInterventionReverificationVerificationDisposition
        .NOT_VERIFIED
    )


def test_insufficient_evidence_maps_to_inconclusive():
    evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionReverificationRequirementEvaluationDisposition
            .INSUFFICIENT_EVIDENCE
        ),
        evidence_sufficient=False,
        comparison_satisfied=None,
    )

    result = build_result(
        evaluation
    )

    assert (
        result.verification_disposition
        is GovernanceInterventionReverificationVerificationDisposition
        .INCONCLUSIVE
    )


def test_same_inputs_produce_same_verification_hash():
    evaluation = make_evaluation()

    first = build_result(
        evaluation
    )

    second = build_result(
        evaluation
    )

    assert (
        first.verification_hash
        == second.verification_hash
    )


def test_different_evaluation_changes_verification_hash():
    first_evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionReverificationRequirementEvaluationDisposition
            .SATISFIED
        ),
        evidence_sufficient=True,
        comparison_satisfied=True,
    )

    second_evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionReverificationRequirementEvaluationDisposition
            .NOT_SATISFIED
        ),
        evidence_sufficient=True,
        comparison_satisfied=False,
    )

    first = build_result(
        first_evaluation
    )

    second = build_result(
        second_evaluation
    )

    assert (
        first.verification_hash
        != second.verification_hash
    )


def test_tampered_evaluation_is_rejected():
    evaluation = make_evaluation()

    tampered = replace(
        evaluation,
        observed_value=999.0,
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationResultIntegrityError,
        match=(
            "reverification requirement evaluation "
            "failed deterministic verification"
        ),
    ):
        build_result(
            tampered
        )


def test_verified_rejects_insufficient_evidence():
    evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionReverificationRequirementEvaluationDisposition
            .SATISFIED
        ),
        evidence_sufficient=False,
        comparison_satisfied=True,
    )

    evaluation = rehash_evaluation(
        evaluation
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationResultIntegrityError,
        match="VERIFIED requires sufficient evidence",
    ):
        build_result(
            evaluation
        )


def test_verified_rejects_unsatisfied_comparison():
    evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionReverificationRequirementEvaluationDisposition
            .SATISFIED
        ),
        evidence_sufficient=True,
        comparison_satisfied=False,
    )

    evaluation = rehash_evaluation(
        evaluation
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationResultIntegrityError,
        match=(
            "VERIFIED requires a satisfied comparison"
        ),
    ):
        build_result(
            evaluation
        )


def test_not_verified_rejects_insufficient_evidence():
    evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionReverificationRequirementEvaluationDisposition
            .NOT_SATISFIED
        ),
        evidence_sufficient=False,
        comparison_satisfied=False,
    )

    evaluation = rehash_evaluation(
        evaluation
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationResultIntegrityError,
        match=(
            "NOT_VERIFIED requires sufficient evidence"
        ),
    ):
        build_result(
            evaluation
        )


def test_not_verified_rejects_satisfied_comparison():
    evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionReverificationRequirementEvaluationDisposition
            .NOT_SATISFIED
        ),
        evidence_sufficient=True,
        comparison_satisfied=True,
    )

    evaluation = rehash_evaluation(
        evaluation
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationResultIntegrityError,
        match=(
            "NOT_VERIFIED requires an unsatisfied comparison"
        ),
    ):
        build_result(
            evaluation
        )


def test_inconclusive_rejects_sufficient_evidence():
    evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionReverificationRequirementEvaluationDisposition
            .INSUFFICIENT_EVIDENCE
        ),
        evidence_sufficient=True,
        comparison_satisfied=None,
    )

    evaluation = rehash_evaluation(
        evaluation
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationResultIntegrityError,
        match=(
            "INCONCLUSIVE requires insufficient evidence"
        ),
    ):
        build_result(
            evaluation
        )


def test_inconclusive_rejects_comparison_result():
    evaluation = make_evaluation(
        disposition=(
            GovernanceInterventionReverificationRequirementEvaluationDisposition
            .INSUFFICIENT_EVIDENCE
        ),
        evidence_sufficient=False,
        comparison_satisfied=False,
    )

    evaluation = rehash_evaluation(
        evaluation
    )

    with pytest.raises(
        GovernanceInterventionReverificationVerificationResultIntegrityError,
        match=(
            "INCONCLUSIVE requires no comparison result"
        ),
    ):
        build_result(
            evaluation
        )


def test_full_reverification_lineage_is_preserved():
    evaluation = make_evaluation()

    evaluation = replace(
        evaluation,
        tenant_id="tenant-42",
        intervention_id="intervention-42",
        verification_record_hash="record-42",
        request_hash="request-42",
        work_order_hash="work-order-42",
        attempt_id="attempt-42",
        attempt_execution_id="attempt-exec-42",
        reverification_scope="FULL",
        evidence_hash="evidence-42",
        measurement_hash="measurement-42",
        actuation_contract_hash="contract-42",
        intervention_type="configuration-change",
        requirement_id="requirement-42",
        requirement_hash="requirement-hash-42",
        metric_id="metric-42",
    )

    evaluation = rehash_evaluation(
        evaluation
    )

    result = build_result(
        evaluation
    )

    assert result.tenant_id == "tenant-42"
    assert (
        result.intervention_id
        == "intervention-42"
    )
    assert (
        result.verification_record_hash
        == "record-42"
    )
    assert (
        result.request_hash
        == "request-42"
    )
    assert (
        result.work_order_hash
        == "work-order-42"
    )
    assert (
        result.attempt_id
        == "attempt-42"
    )
    assert (
        result.attempt_execution_id
        == "attempt-exec-42"
    )
    assert (
        result.reverification_scope
        == "FULL"
    )
    assert (
        result.evidence_hash
        == "evidence-42"
    )
    assert (
        result.measurement_hash
        == "measurement-42"
    )
    assert (
        result.evaluation_hash
        == evaluation.evaluation_hash
    )
    assert (
        result.actuation_contract_hash
        == "contract-42"
    )
    assert (
        result.intervention_type
        == "configuration-change"
    )
    assert (
        result.requirement_id
        == "requirement-42"
    )
    assert (
        result.requirement_hash
        == "requirement-hash-42"
    )
    assert (
        result.metric_id
        == "metric-42"
    )


def test_result_preserves_governed_evaluation_values():
    evaluation = make_evaluation()

    result = build_result(
        evaluation
    )

    assert (
        result.operator
        == evaluation.operator.value
    )
    assert (
        result.target_value
        == evaluation.target_value
    )
    assert (
        result.observed_value
        == evaluation.observed_value
    )
    assert (
        result.unit
        == evaluation.unit
    )
    assert (
        result.evidence_sufficient
        == evaluation.evidence_sufficient
    )
    assert (
        result.comparison_satisfied
        == evaluation.comparison_satisfied
    )
    assert (
        result.evaluation_disposition
        == evaluation.disposition.value
    )


def test_result_contains_no_original_execution_lineage_fields():
    result = build_result()

    payload = result.to_dict()

    forbidden = {
        "observation_hash",
        "execution_receipt_hash",
        "execution_result_hash",
        "actuation_id",
        "adapter_id",
        "adapter_name",
    }

    assert forbidden.isdisjoint(
        payload
    )


def test_result_contains_no_success_causation_or_action_authority():
    result = build_result()

    payload = result.to_dict()

    forbidden = {
        "success",
        "failure",
        "intervention_success",
        "intervention_failure",
        "causation",
        "causal_effect",
        "authorized",
        "recommended_action",
        "next_action",
        "continue",
        "rollback",
        "remediate",
        "remediation",
        "lifecycle_state",
        "superseded",
        "superseded_record_hash",
    }

    assert forbidden.isdisjoint(
        payload
    )


def test_verification_disposition_values_are_exact():
    assert {
        item.value
        for item in (
            GovernanceInterventionReverificationVerificationDisposition
        )
    } == {
        "VERIFIED",
        "NOT_VERIFIED",
        "INCONCLUSIVE",
    }