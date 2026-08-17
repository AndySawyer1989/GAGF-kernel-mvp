from __future__ import annotations

from dataclasses import replace
from math import inf, nan

import pytest

from backend.app.gagf.governance_intervention_reverification_evidence import (
    GovernanceInterventionReverificationEvidence,
)
from backend.app.gagf.governance_intervention_reverification_measurement import (
    GOVERNANCE_INTERVENTION_REVERIFICATION_MEASUREMENT_ID,
    GOVERNANCE_INTERVENTION_REVERIFICATION_MEASUREMENT_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_REVERIFICATION_MEASUREMENT_VERSION,
    GovernanceInterventionReverificationMeasurementBuilder,
    GovernanceInterventionReverificationMeasurementLineageError,
    GovernanceInterventionReverificationMeasurementValueError,
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
    legacy_requirement: str = "latency <= 100",
    requirement_id: str = "requirement-1",
    metric_id: str = "metric-1",
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
        "legacy_requirement": legacy_requirement,
        "requirement_id": requirement_id,
        "description": "Latency remains bounded.",
        "metric_id": metric_id,
        "operator": (
            GovernanceInterventionVerificationOperator.LTE.value
        ),
        "target_value": 100.0,
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
        schema_version=payload["schema_version"],
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
        description=payload["description"],
        metric_id=payload["metric_id"],
        operator=(
            GovernanceInterventionVerificationOperator(
                payload["operator"]
            )
        ),
        target_value=payload["target_value"],
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


def make_evidence(
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
    verification_record_hash: str = "record-1",
    request_hash: str = "request-1",
    work_order_hash: str = "work-order-1",
    attempt_id: str = "attempt-1",
    attempt_execution_id: str = "attempt-exec-1",
    reverification_scope: str = "POLICY",
    requirement_id: str = "requirement-1",
    requirement_hash: str | None = None,
    metric_id: str = "metric-1",
    record_count: int = 5,
) -> GovernanceInterventionReverificationEvidence:
    requirement = make_requirement(
        tenant_id=tenant_id,
        intervention_id=intervention_id,
        requirement_id=requirement_id,
        metric_id=metric_id,
    )

    if requirement_hash is None:
        requirement_hash = requirement.requirement_hash

    payload = {
        "evidence_id": (
            "governance-intervention-reverification-evidence"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": tenant_id,
        "intervention_id": intervention_id,
        "verification_record_hash": (
            verification_record_hash
        ),
        "request_hash": request_hash,
        "work_order_hash": work_order_hash,
        "attempt_id": attempt_id,
        "attempt_execution_id": (
            attempt_execution_id
        ),
        "reverification_scope": (
            reverification_scope
        ),
        "requirement_id": requirement_id,
        "requirement_hash": requirement_hash,
        "metric_id": metric_id,
        "source_id": "source-1",
        "source_kind": "telemetry",
        "acquired_at": "2026-08-17T16:00:00Z",
        "evidence_summary": "Fresh telemetry.",
        "evidence_references": [
            "ref-1"
        ],
        "record_count": record_count,
    }

    return GovernanceInterventionReverificationEvidence(
        evidence_id=payload["evidence_id"],
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
        request_hash=payload["request_hash"],
        work_order_hash=payload[
            "work_order_hash"
        ],
        attempt_id=payload["attempt_id"],
        attempt_execution_id=payload[
            "attempt_execution_id"
        ],
        reverification_scope=payload[
            "reverification_scope"
        ],
        requirement_id=payload[
            "requirement_id"
        ],
        requirement_hash=payload[
            "requirement_hash"
        ],
        metric_id=payload["metric_id"],
        source_id=payload["source_id"],
        source_kind=payload["source_kind"],
        acquired_at=payload["acquired_at"],
        evidence_summary=payload[
            "evidence_summary"
        ],
        evidence_references=tuple(
            payload["evidence_references"]
        ),
        record_count=payload["record_count"],
        evidence_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def build_measurement(
    *,
    requirement=None,
    evidence=None,
    observed_value=84.5,
    unit="ms",
    measurement_window_seconds=300,
):
    if requirement is None:
        requirement = make_requirement()

    if evidence is None:
        evidence = make_evidence(
            requirement_hash=(
                requirement.requirement_hash
            )
        )

    return (
        GovernanceInterventionReverificationMeasurementBuilder.build(
            requirement=requirement,
            evidence=evidence,
            observed_value=observed_value,
            unit=unit,
            measurement_window_seconds=(
                measurement_window_seconds
            ),
        )
    )


def test_measurement_identity_constants_are_exact():
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_MEASUREMENT_ID
        == "governance-intervention-reverification-measurement"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_MEASUREMENT_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_MEASUREMENT_SCHEMA_VERSION
        == "1.0.0"
    )


def test_builds_valid_deterministic_measurement():
    requirement = make_requirement()

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    measurement = build_measurement(
        requirement=requirement,
        evidence=evidence,
    )

    assert measurement.verify()

    assert (
        measurement.tenant_id
        == evidence.tenant_id
    )

    assert (
        measurement.intervention_id
        == evidence.intervention_id
    )

    assert (
        measurement.verification_record_hash
        == evidence.verification_record_hash
    )

    assert (
        measurement.evidence_hash
        == evidence.evidence_hash
    )

    assert (
        measurement.requirement_hash
        == requirement.requirement_hash
    )


def test_same_inputs_produce_same_measurement_hash():
    requirement = make_requirement()

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    first = build_measurement(
        requirement=requirement,
        evidence=evidence,
    )

    second = build_measurement(
        requirement=requirement,
        evidence=evidence,
    )

    assert (
        first.measurement_hash
        == second.measurement_hash
    )


def test_different_observed_value_changes_hash():
    requirement = make_requirement()

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    first = build_measurement(
        requirement=requirement,
        evidence=evidence,
        observed_value=84.5,
    )

    second = build_measurement(
        requirement=requirement,
        evidence=evidence,
        observed_value=85.5,
    )

    assert (
        first.measurement_hash
        != second.measurement_hash
    )


def test_tampered_requirement_is_rejected():
    requirement = make_requirement()

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    tampered = replace(
        requirement,
        metric_id="tampered-metric",
    )

    with pytest.raises(
        GovernanceInterventionReverificationMeasurementLineageError,
        match=(
            "verification requirement failed "
            "deterministic verification"
        ),
    ):
        build_measurement(
            requirement=tampered,
            evidence=evidence,
        )


def test_tampered_evidence_is_rejected():
    requirement = make_requirement()

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    tampered = replace(
        evidence,
        record_count=999,
    )

    with pytest.raises(
        GovernanceInterventionReverificationMeasurementLineageError,
        match=(
            "reverification evidence failed "
            "deterministic verification"
        ),
    ):
        build_measurement(
            requirement=requirement,
            evidence=tampered,
        )


def test_tenant_mismatch_is_rejected():
    requirement = make_requirement(
        tenant_id="tenant-a"
    )

    evidence = make_evidence(
        tenant_id="tenant-b",
        requirement_hash=(
            requirement.requirement_hash
        ),
    )

    with pytest.raises(
        GovernanceInterventionReverificationMeasurementLineageError,
        match="evidence tenant does not match",
    ):
        build_measurement(
            requirement=requirement,
            evidence=evidence,
        )


def test_intervention_mismatch_is_rejected():
    requirement = make_requirement(
        intervention_id="intervention-1"
    )

    evidence = make_evidence(
        intervention_id="intervention-2",
        requirement_hash=(
            requirement.requirement_hash
        ),
    )

    with pytest.raises(
        GovernanceInterventionReverificationMeasurementLineageError,
        match="evidence intervention_id",
    ):
        build_measurement(
            requirement=requirement,
            evidence=evidence,
        )


def test_requirement_id_mismatch_is_rejected():
    requirement = make_requirement(
        requirement_id="requirement-1"
    )

    evidence = make_evidence(
        requirement_id="requirement-2",
        requirement_hash=(
            requirement.requirement_hash
        ),
    )

    with pytest.raises(
        GovernanceInterventionReverificationMeasurementLineageError,
        match="evidence requirement_id",
    ):
        build_measurement(
            requirement=requirement,
            evidence=evidence,
        )


def test_requirement_hash_mismatch_is_rejected():
    requirement = make_requirement()

    evidence = make_evidence(
        requirement_hash="different-requirement-hash"
    )

    with pytest.raises(
        GovernanceInterventionReverificationMeasurementLineageError,
        match="evidence requirement_hash",
    ):
        build_measurement(
            requirement=requirement,
            evidence=evidence,
        )


def test_metric_id_mismatch_is_rejected():
    requirement = make_requirement(
        metric_id="metric-1"
    )

    evidence = make_evidence(
        metric_id="metric-2",
        requirement_hash=(
            requirement.requirement_hash
        ),
    )

    with pytest.raises(
        GovernanceInterventionReverificationMeasurementLineageError,
        match="evidence metric_id",
    ):
        build_measurement(
            requirement=requirement,
            evidence=evidence,
        )


@pytest.mark.parametrize(
    "observed_value",
    [
        nan,
        inf,
        -inf,
    ],
)
def test_nonfinite_observed_value_is_rejected(
    observed_value,
):
    requirement = make_requirement()

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    with pytest.raises(
        GovernanceInterventionReverificationMeasurementValueError,
        match="observed_value must be finite",
    ):
        build_measurement(
            requirement=requirement,
            evidence=evidence,
            observed_value=observed_value,
        )


def test_unit_mismatch_is_rejected():
    requirement = make_requirement(
        unit="ms"
    )

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    with pytest.raises(
        GovernanceInterventionReverificationMeasurementLineageError,
        match="measurement unit does not match",
    ):
        build_measurement(
            requirement=requirement,
            evidence=evidence,
            unit="seconds",
        )


def test_blank_unit_is_rejected():
    requirement = make_requirement()

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    with pytest.raises(
        GovernanceInterventionReverificationMeasurementValueError,
        match="unit is required",
    ):
        build_measurement(
            requirement=requirement,
            evidence=evidence,
            unit="",
        )


def test_noncanonical_unit_is_rejected():
    requirement = make_requirement(
        unit="ms"
    )

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    with pytest.raises(
        GovernanceInterventionReverificationMeasurementValueError,
        match="unit must already be canonical",
    ):
        build_measurement(
            requirement=requirement,
            evidence=evidence,
            unit=" ms ",
        )


@pytest.mark.parametrize(
    "measurement_window_seconds",
    [
        0,
        -1,
    ],
)
def test_nonpositive_measurement_window_is_rejected(
    measurement_window_seconds,
):
    requirement = make_requirement()

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    with pytest.raises(
        GovernanceInterventionReverificationMeasurementValueError,
        match=(
            "measurement_window_seconds "
            "must be at least 1"
        ),
    ):
        build_measurement(
            requirement=requirement,
            evidence=evidence,
            measurement_window_seconds=(
                measurement_window_seconds
            ),
        )


def test_record_count_is_inherited_from_evidence():
    requirement = make_requirement(
        minimum_record_count=10
    )

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        ),
        record_count=7,
    )

    measurement = build_measurement(
        requirement=requirement,
        evidence=evidence,
    )

    assert measurement.record_count == 7


def test_subminimum_record_count_does_not_fail_measurement():
    requirement = make_requirement(
        minimum_record_count=10
    )

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        ),
        record_count=1,
    )

    measurement = build_measurement(
        requirement=requirement,
        evidence=evidence,
    )

    assert measurement.verify()
    assert measurement.record_count == 1
    assert requirement.minimum_record_count == 10


def test_measurement_window_is_not_forced_to_requirement_window():
    requirement = make_requirement(
        measurement_window_seconds=300
    )

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    measurement = build_measurement(
        requirement=requirement,
        evidence=evidence,
        measurement_window_seconds=120,
    )

    assert (
        measurement.measurement_window_seconds
        == 120
    )

    assert (
        requirement.measurement_window_seconds
        == 300
    )


def test_actuation_contract_hash_comes_from_requirement():
    requirement = make_requirement(
        actuation_contract_hash="contract-abc"
    )

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    measurement = build_measurement(
        requirement=requirement,
        evidence=evidence,
    )

    assert (
        measurement.actuation_contract_hash
        == "contract-abc"
    )


def test_attempt_and_request_lineage_is_preserved():
    requirement = make_requirement()

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        ),
        verification_record_hash="record-42",
        request_hash="request-42",
        work_order_hash="work-order-42",
        attempt_id="attempt-42",
        attempt_execution_id="attempt-exec-42",
    )

    measurement = build_measurement(
        requirement=requirement,
        evidence=evidence,
    )

    assert (
        measurement.verification_record_hash
        == "record-42"
    )

    assert measurement.request_hash == "request-42"
    assert (
        measurement.work_order_hash
        == "work-order-42"
    )
    assert measurement.attempt_id == "attempt-42"
    assert (
        measurement.attempt_execution_id
        == "attempt-exec-42"
    )


def test_measurement_contains_no_evaluation_or_judgment_fields():
    requirement = make_requirement()

    evidence = make_evidence(
        requirement_hash=(
            requirement.requirement_hash
        )
    )

    measurement = build_measurement(
        requirement=requirement,
        evidence=evidence,
    )

    payload = measurement.to_dict()

    forbidden = {
        "operator",
        "target_value",
        "requirement_satisfied",
        "evaluation_disposition",
        "satisfied",
        "not_satisfied",
        "insufficient_evidence",
        "verification_disposition",
        "verified",
        "not_verified",
        "inconclusive",
        "success",
        "failure",
        "causation",
        "causal_effect",
        "authorized",
        "recommended_action",
        "next_action",
        "superseded",
        "superseded_record_hash",
    }

    assert forbidden.isdisjoint(payload)