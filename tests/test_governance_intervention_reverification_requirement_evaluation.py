from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_intervention_reverification_measurement import (
    GovernanceInterventionReverificationMeasurement,
)
from backend.app.gagf.governance_intervention_reverification_requirement_evaluation import (
    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUIREMENT_EVALUATION_ID,
    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUIREMENT_EVALUATION_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_REVERIFICATION_REQUIREMENT_EVALUATION_VERSION,
    GovernanceInterventionReverificationRequirementEvaluationDisposition,
    GovernanceInterventionReverificationRequirementEvaluationLineageError,
    GovernanceInterventionReverificationRequirementEvaluator,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationOperator,
    GovernanceInterventionVerificationRequirement,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


def make_requirement(
    *,
    tenant_id: str = "tenant-a",
    actuation_contract_hash: str = "contract-1",
    intervention_id: str = "intervention-1",
    intervention_type: str = "policy-update",
    requirement_id: str = "requirement-1",
    metric_id: str = "metric-1",
    operator: (
        GovernanceInterventionVerificationOperator
    ) = GovernanceInterventionVerificationOperator.LTE,
    target_value: float = 100.0,
    unit: str = "ms",
    measurement_window_seconds: int = 300,
    minimum_record_count: int = 10,
) -> GovernanceInterventionVerificationRequirement:
    payload = {
        "requirement_contract_id": (
            "governance-intervention-verification-requirement"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": tenant_id,
        "actuation_contract_hash": (
            actuation_contract_hash
        ),
        "intervention_id": intervention_id,
        "intervention_type": intervention_type,
        "legacy_requirement": "governed requirement",
        "requirement_id": requirement_id,
        "description": "Governed requirement.",
        "metric_id": metric_id,
        "operator": operator.value,
        "target_value": target_value,
        "unit": unit,
        "measurement_window_seconds": (
            measurement_window_seconds
        ),
        "minimum_record_count": minimum_record_count,
    }

    return GovernanceInterventionVerificationRequirement(
        requirement_contract_id=payload[
            "requirement_contract_id"
        ],
        version=payload["version"],
        schema_version=payload[
            "schema_version"
        ],
        tenant_id=payload["tenant_id"],
        actuation_contract_hash=payload[
            "actuation_contract_hash"
        ],
        intervention_id=payload[
            "intervention_id"
        ],
        intervention_type=payload[
            "intervention_type"
        ],
        legacy_requirement=payload[
            "legacy_requirement"
        ],
        requirement_id=payload[
            "requirement_id"
        ],
        description=payload[
            "description"
        ],
        metric_id=payload[
            "metric_id"
        ],
        operator=operator,
        target_value=payload[
            "target_value"
        ],
        unit=payload["unit"],
        measurement_window_seconds=payload[
            "measurement_window_seconds"
        ],
        minimum_record_count=payload[
            "minimum_record_count"
        ],
        requirement_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def make_measurement(
    *,
    requirement=None,
    tenant_id: str | None = None,
    intervention_id: str | None = None,
    intervention_type: str | None = None,
    actuation_contract_hash: str | None = None,
    requirement_id: str | None = None,
    requirement_hash: str | None = None,
    metric_id: str | None = None,
    unit: str | None = None,
    observed_value: float = 84.5,
    measurement_window_seconds: int = 300,
    record_count: int = 10,
) -> GovernanceInterventionReverificationMeasurement:
    if requirement is None:
        requirement = make_requirement()

    payload = {
        "measurement_id": (
            "governance-intervention-reverification-measurement"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": (
            requirement.tenant_id
            if tenant_id is None
            else tenant_id
        ),
        "intervention_id": (
            requirement.intervention_id
            if intervention_id is None
            else intervention_id
        ),
        "verification_record_hash": "record-1",
        "request_hash": "request-1",
        "work_order_hash": "work-order-1",
        "attempt_id": "attempt-1",
        "attempt_execution_id": "attempt-exec-1",
        "reverification_scope": "POLICY",
        "evidence_hash": "evidence-1",
        "actuation_contract_hash": (
            requirement.actuation_contract_hash
            if actuation_contract_hash is None
            else actuation_contract_hash
        ),
        "intervention_type": (
            requirement.intervention_type
            if intervention_type is None
            else intervention_type
        ),
        "requirement_id": (
            requirement.requirement_id
            if requirement_id is None
            else requirement_id
        ),
        "requirement_hash": (
            requirement.requirement_hash
            if requirement_hash is None
            else requirement_hash
        ),
        "metric_id": (
            requirement.metric_id
            if metric_id is None
            else metric_id
        ),
        "observed_value": observed_value,
        "unit": (
            requirement.unit
            if unit is None
            else unit
        ),
        "measurement_window_seconds": (
            measurement_window_seconds
        ),
        "record_count": record_count,
    }

    return GovernanceInterventionReverificationMeasurement(
        measurement_id=payload[
            "measurement_id"
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
        observed_value=payload[
            "observed_value"
        ],
        unit=payload["unit"],
        measurement_window_seconds=payload[
            "measurement_window_seconds"
        ],
        record_count=payload[
            "record_count"
        ],
        measurement_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def evaluate(
    *,
    requirement=None,
    measurement=None,
):
    if requirement is None:
        requirement = make_requirement()

    if measurement is None:
        measurement = make_measurement(
            requirement=requirement
        )

    return (
        GovernanceInterventionReverificationRequirementEvaluator.evaluate(
            requirement=requirement,
            measurement=measurement,
        )
    )


def test_evaluation_identity_constants_are_exact():
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_REQUIREMENT_EVALUATION_ID
        == (
            "governance-intervention-"
            "reverification-requirement-evaluation"
        )
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_REQUIREMENT_EVALUATION_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_REQUIREMENT_EVALUATION_SCHEMA_VERSION
        == "1.0.0"
    )


def test_sufficient_satisfied_evaluation():
    requirement = make_requirement(
        operator=(
            GovernanceInterventionVerificationOperator.LTE
        ),
        target_value=100.0,
    )

    measurement = make_measurement(
        requirement=requirement,
        observed_value=90.0,
        measurement_window_seconds=300,
        record_count=10,
    )

    result = evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    assert result.verify()
    assert result.evidence_sufficient is True
    assert result.comparison_satisfied is True
    assert (
        result.disposition
        is GovernanceInterventionReverificationRequirementEvaluationDisposition
        .SATISFIED
    )


def test_sufficient_not_satisfied_evaluation():
    requirement = make_requirement(
        operator=(
            GovernanceInterventionVerificationOperator.LTE
        ),
        target_value=100.0,
    )

    measurement = make_measurement(
        requirement=requirement,
        observed_value=101.0,
        measurement_window_seconds=300,
        record_count=10,
    )

    result = evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    assert result.evidence_sufficient is True
    assert result.comparison_satisfied is False
    assert (
        result.disposition
        is GovernanceInterventionReverificationRequirementEvaluationDisposition
        .NOT_SATISFIED
    )


def test_short_window_is_insufficient_evidence():
    requirement = make_requirement(
        measurement_window_seconds=300,
        minimum_record_count=10,
    )

    measurement = make_measurement(
        requirement=requirement,
        observed_value=999.0,
        measurement_window_seconds=299,
        record_count=10,
    )

    result = evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    assert result.evidence_sufficient is False
    assert result.comparison_satisfied is None
    assert (
        result.disposition
        is GovernanceInterventionReverificationRequirementEvaluationDisposition
        .INSUFFICIENT_EVIDENCE
    )


def test_low_record_count_is_insufficient_evidence():
    requirement = make_requirement(
        measurement_window_seconds=300,
        minimum_record_count=10,
    )

    measurement = make_measurement(
        requirement=requirement,
        observed_value=999.0,
        measurement_window_seconds=300,
        record_count=9,
    )

    result = evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    assert result.evidence_sufficient is False
    assert result.comparison_satisfied is None
    assert (
        result.disposition
        is GovernanceInterventionReverificationRequirementEvaluationDisposition
        .INSUFFICIENT_EVIDENCE
    )


def test_both_sufficiency_failures_remain_insufficient():
    requirement = make_requirement(
        measurement_window_seconds=300,
        minimum_record_count=10,
    )

    measurement = make_measurement(
        requirement=requirement,
        observed_value=999.0,
        measurement_window_seconds=1,
        record_count=1,
    )

    result = evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    assert result.evidence_sufficient is False
    assert result.comparison_satisfied is None
    assert (
        result.disposition
        is GovernanceInterventionReverificationRequirementEvaluationDisposition
        .INSUFFICIENT_EVIDENCE
    )


@pytest.mark.parametrize(
    (
        "operator",
        "observed_value",
        "target_value",
        "expected",
    ),
    [
        (
            GovernanceInterventionVerificationOperator.EQ,
            10.0,
            10.0,
            True,
        ),
        (
            GovernanceInterventionVerificationOperator.NE,
            10.0,
            11.0,
            True,
        ),
        (
            GovernanceInterventionVerificationOperator.LT,
            9.0,
            10.0,
            True,
        ),
        (
            GovernanceInterventionVerificationOperator.LTE,
            10.0,
            10.0,
            True,
        ),
        (
            GovernanceInterventionVerificationOperator.GT,
            11.0,
            10.0,
            True,
        ),
        (
            GovernanceInterventionVerificationOperator.GTE,
            10.0,
            10.0,
            True,
        ),
    ],
)
def test_all_six_operators_satisfied(
    operator,
    observed_value,
    target_value,
    expected,
):
    requirement = make_requirement(
        operator=operator,
        target_value=target_value,
    )

    measurement = make_measurement(
        requirement=requirement,
        observed_value=observed_value,
    )

    result = evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    assert (
        result.comparison_satisfied
        is expected
    )

    assert (
        result.disposition
        is GovernanceInterventionReverificationRequirementEvaluationDisposition
        .SATISFIED
    )


@pytest.mark.parametrize(
    (
        "operator",
        "observed_value",
        "target_value",
    ),
    [
        (
            GovernanceInterventionVerificationOperator.EQ,
            10.0,
            11.0,
        ),
        (
            GovernanceInterventionVerificationOperator.NE,
            10.0,
            10.0,
        ),
        (
            GovernanceInterventionVerificationOperator.LT,
            10.0,
            10.0,
        ),
        (
            GovernanceInterventionVerificationOperator.LTE,
            11.0,
            10.0,
        ),
        (
            GovernanceInterventionVerificationOperator.GT,
            10.0,
            10.0,
        ),
        (
            GovernanceInterventionVerificationOperator.GTE,
            9.0,
            10.0,
        ),
    ],
)
def test_all_six_operators_not_satisfied(
    operator,
    observed_value,
    target_value,
):
    requirement = make_requirement(
        operator=operator,
        target_value=target_value,
    )

    measurement = make_measurement(
        requirement=requirement,
        observed_value=observed_value,
    )

    result = evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    assert result.comparison_satisfied is False

    assert (
        result.disposition
        is GovernanceInterventionReverificationRequirementEvaluationDisposition
        .NOT_SATISFIED
    )


def test_exact_equality_has_no_hidden_tolerance():
    requirement = make_requirement(
        operator=(
            GovernanceInterventionVerificationOperator.EQ
        ),
        target_value=10.0,
    )

    measurement = make_measurement(
        requirement=requirement,
        observed_value=10.0000000001,
    )

    result = evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    assert result.comparison_satisfied is False


def test_same_inputs_produce_same_hash():
    requirement = make_requirement()

    measurement = make_measurement(
        requirement=requirement
    )

    first = evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    second = evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    assert (
        first.evaluation_hash
        == second.evaluation_hash
    )


def test_tampered_requirement_is_rejected():
    requirement = make_requirement()

    measurement = make_measurement(
        requirement=requirement
    )

    tampered = replace(
        requirement,
        target_value=999.0,
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequirementEvaluationLineageError,
        match=(
            "verification requirement failed "
            "deterministic verification"
        ),
    ):
        evaluate(
            requirement=tampered,
            measurement=measurement,
        )


def test_tampered_measurement_is_rejected():
    requirement = make_requirement()

    measurement = make_measurement(
        requirement=requirement
    )

    tampered = replace(
        measurement,
        record_count=999,
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequirementEvaluationLineageError,
        match=(
            "reverification measurement failed "
            "deterministic verification"
        ),
    ):
        evaluate(
            requirement=requirement,
            measurement=tampered,
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "field_value",
        "message",
    ),
    [
        (
            "tenant_id",
            "tenant-b",
            "measurement tenant",
        ),
        (
            "actuation_contract_hash",
            "contract-2",
            "measurement actuation contract hash",
        ),
        (
            "intervention_id",
            "intervention-2",
            "measurement intervention_id",
        ),
        (
            "intervention_type",
            "different-type",
            "measurement intervention_type",
        ),
        (
            "requirement_id",
            "requirement-2",
            "measurement requirement_id",
        ),
        (
            "requirement_hash",
            "different-hash",
            "measurement requirement hash",
        ),
        (
            "metric_id",
            "metric-2",
            "measurement metric_id",
        ),
        (
            "unit",
            "seconds",
            "measurement unit",
        ),
    ],
)
def test_measurement_lineage_mismatches_are_rejected(
    field_name,
    field_value,
    message,
):
    requirement = make_requirement()

    kwargs = {
        field_name: field_value
    }

    measurement = make_measurement(
        requirement=requirement,
        **kwargs,
    )

    with pytest.raises(
        GovernanceInterventionReverificationRequirementEvaluationLineageError,
        match=message,
    ):
        evaluate(
            requirement=requirement,
            measurement=measurement,
        )


def test_reverification_lineage_is_preserved():
    requirement = make_requirement()

    measurement = make_measurement(
        requirement=requirement
    )

    measurement = replace(
        measurement,
        verification_record_hash="record-42",
        request_hash="request-42",
        work_order_hash="work-order-42",
        attempt_id="attempt-42",
        attempt_execution_id="attempt-exec-42",
        reverification_scope="FULL",
        evidence_hash="evidence-42",
    )

    payload = measurement.payload()

    measurement = replace(
        measurement,
        measurement_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    result = evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    assert (
        result.verification_record_hash
        == "record-42"
    )
    assert result.request_hash == "request-42"
    assert (
        result.work_order_hash
        == "work-order-42"
    )
    assert result.attempt_id == "attempt-42"
    assert (
        result.attempt_execution_id
        == "attempt-exec-42"
    )
    assert result.reverification_scope == "FULL"
    assert result.evidence_hash == "evidence-42"


def test_evaluation_preserves_sufficiency_inputs():
    requirement = make_requirement(
        measurement_window_seconds=600,
        minimum_record_count=25,
    )

    measurement = make_measurement(
        requirement=requirement,
        measurement_window_seconds=700,
        record_count=30,
    )

    result = evaluate(
        requirement=requirement,
        measurement=measurement,
    )

    assert (
        result.required_measurement_window_seconds
        == 600
    )
    assert (
        result.actual_measurement_window_seconds
        == 700
    )
    assert result.minimum_record_count == 25
    assert result.actual_record_count == 30


def test_evaluation_contains_no_final_verification_or_action_authority():
    result = evaluate()

    payload = result.to_dict()

    forbidden = {
        "verification_disposition",
        "verified",
        "not_verified",
        "inconclusive",
        "success",
        "failure",
        "intervention_success",
        "causation",
        "causal_effect",
        "authorized",
        "recommended_action",
        "next_action",
        "lifecycle_state",
        "superseded",
        "superseded_record_hash",
    }

    assert forbidden.isdisjoint(payload)


def test_disposition_values_are_exact():
    assert {
        item.value
        for item in (
            GovernanceInterventionReverificationRequirementEvaluationDisposition
        )
    } == {
        "SATISFIED",
        "NOT_SATISFIED",
        "INSUFFICIENT_EVIDENCE",
    }