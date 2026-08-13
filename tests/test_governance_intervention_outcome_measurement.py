from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from math import inf, nan

import pytest

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_actuation_journal import (
    GovernanceInterventionActuationJournal,
)
from backend.app.gagf.governance_intervention_actuation_port import (
    GovernanceInterventionActuationAcceptance,
    GovernanceInterventionActuationDisposition,
    GovernanceInterventionActuationRequest,
)
from backend.app.gagf.governance_intervention_execution_adapter import (
    GovernanceInterventionAdapterExecutionReport,
)
from backend.app.gagf.governance_intervention_execution_coordinator import (
    GovernanceInterventionExecutionCoordinator,
)
from backend.app.gagf.governance_intervention_execution_receipt import (
    GovernanceInterventionExecutionReceiptBuilder,
)
from backend.app.gagf.governance_intervention_execution_result import (
    GovernanceInterventionExecutionDisposition,
)
from backend.app.gagf.governance_intervention_outcome_measurement import (
    GOVERNANCE_INTERVENTION_OUTCOME_MEASUREMENT_ID,
    GOVERNANCE_INTERVENTION_OUTCOME_MEASUREMENT_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_OUTCOME_MEASUREMENT_VERSION,
    GovernanceInterventionOutcomeMeasurementBuilder,
    GovernanceInterventionOutcomeMeasurementLineageError,
    GovernanceInterventionOutcomeMeasurementValueError,
)
from backend.app.gagf.governance_intervention_outcome_observation import (
    GovernanceInterventionOutcomeObservationBuilder,
)
from backend.app.gagf.governance_intervention_verification_commitment import (
    GovernanceInterventionVerificationCommitmentBuilder,
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


def make_requirement(contract):
    return GovernanceInterventionVerificationRequirementBuilder.build(
        actuation_contract=contract,
        legacy_requirement=LEGACY_REQUIREMENT,
        requirement_id="approval-latency-lte-120",
        description=(
            "Approval latency must be no greater than "
            "120 seconds after intervention."
        ),
        metric_id="approval_latency_seconds",
        operator=GovernanceInterventionVerificationOperator.LTE,
        target_value=120,
        unit="seconds",
        measurement_window_seconds=86400,
        minimum_record_count=10,
    )


def make_commitment(contract, requirement):
    return GovernanceInterventionVerificationCommitmentBuilder.build(
        actuation_contract=contract,
        requirement=requirement,
    )


def make_request(contract, commitment):
    return GovernanceInterventionActuationRequest(
        port_id="governance-intervention-actuation-port",
        port_version="0.1.0",
        tenant_id=contract.tenant_id,
        contract_hash=contract.contract_hash,
        intervention_id=contract.intervention_id,
        intervention_type=contract.intervention_type,
        verification_commitment_hash=commitment.commitment_hash,
        idempotency_key="measurement-execution-key",
    )


def make_acceptance(request):
    return GovernanceInterventionActuationAcceptance(
        disposition=GovernanceInterventionActuationDisposition.ACCEPTED,
        tenant_id=request.tenant_id,
        contract_hash=request.contract_hash,
        idempotency_key=request.idempotency_key,
        adapter_id="execution-adapter-a",
        adapter_version="1.0.0",
        accepted=True,
    )


class StubExecutionAdapter:
    adapter_id = "execution-adapter-a"
    adapter_version = "1.0.0"

    def execute(
        self,
        *,
        request,
        contract,
        attempt_number,
    ):
        return GovernanceInterventionAdapterExecutionReport(
            disposition=GovernanceInterventionExecutionDisposition.COMPLETED,
            observations=(
                "bounded execution attempt completed",
            ),
        )


def governed_evidence(tmp_path):
    contract = verified_contract()
    requirement = make_requirement(contract)
    commitment = make_commitment(
        contract,
        requirement,
    )
    request = make_request(
        contract,
        commitment,
    )
    acceptance = make_acceptance(request)

    journal = GovernanceInterventionActuationJournal(
        tmp_path / "gex-001ic1.sqlite3"
    )

    coordinator = GovernanceInterventionExecutionCoordinator(
        journal=journal
    )

    coordinated = coordinator.execute(
        contract=contract,
        request=request,
        verification_commitment=commitment,
        acceptance=acceptance,
        adapter=StubExecutionAdapter(),
        attempt_number=1,
    )

    receipt = GovernanceInterventionExecutionReceiptBuilder.build(
        execution_result=coordinated.execution_result,
        journal_record=coordinated.journal_record,
    )

    observation = GovernanceInterventionOutcomeObservationBuilder.build(
        contract=contract,
        execution_receipt=receipt,
        verification_requirement=LEGACY_REQUIREMENT,
        source_id="independent-metrics-service",
        source_kind="workflow_telemetry",
        observed_at="2026-08-11T22:00:00Z",
        observation_summary=(
            "post-execution approval latency telemetry collected"
        ),
        evidence_references=(
            "telemetry://approval-latency/window-001",
        ),
        record_count=42,
    )

    return (
        contract,
        requirement,
        receipt,
        observation,
    )


def build_measurement(
    tmp_path,
    *,
    observed_value=95.0,
    unit="seconds",
    measurement_window_seconds=86400,
):
    (
        contract,
        requirement,
        receipt,
        observation,
    ) = governed_evidence(tmp_path)

    measurement = GovernanceInterventionOutcomeMeasurementBuilder.build(
        requirement=requirement,
        execution_receipt=receipt,
        observation=observation,
        observed_value=observed_value,
        unit=unit,
        measurement_window_seconds=measurement_window_seconds,
    )

    return (
        contract,
        requirement,
        receipt,
        observation,
        measurement,
    )


def test_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_OUTCOME_MEASUREMENT_ID
        == "governance-intervention-outcome-measurement"
    )

    assert (
        GOVERNANCE_INTERVENTION_OUTCOME_MEASUREMENT_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_OUTCOME_MEASUREMENT_SCHEMA_VERSION
        == "1.0.0"
    )


def test_builds_typed_measurement_from_governed_evidence(tmp_path):
    (
        contract,
        requirement,
        receipt,
        observation,
        measurement,
    ) = build_measurement(tmp_path)

    assert measurement.verify() is True

    assert measurement.tenant_id == contract.tenant_id
    assert measurement.contract_hash == contract.contract_hash

    assert (
        measurement.execution_receipt_hash
        == receipt.receipt_hash
    )

    assert (
        measurement.observation_hash
        == observation.observation_hash
    )

    assert measurement.intervention_id == contract.intervention_id
    assert measurement.intervention_type == contract.intervention_type

    assert measurement.requirement_id == requirement.requirement_id
    assert measurement.requirement_hash == requirement.requirement_hash
    assert measurement.metric_id == requirement.metric_id

    assert measurement.observed_value == 95.0
    assert measurement.unit == "seconds"
    assert measurement.measurement_window_seconds == 86400
    assert measurement.record_count == observation.record_count


def test_measurement_is_deterministic(tmp_path):
    first_path = tmp_path / "first"
    second_path = tmp_path / "second"

    first_path.mkdir()
    second_path.mkdir()

    first = build_measurement(first_path)[-1]
    second = build_measurement(second_path)[-1]

    assert first == second
    assert first.measurement_hash == second.measurement_hash


def test_measurement_is_frozen(tmp_path):
    measurement = build_measurement(tmp_path)[-1]

    with pytest.raises(FrozenInstanceError):
        measurement.observed_value = 999.0


def test_tampered_measurement_fails_verification(tmp_path):
    measurement = build_measurement(tmp_path)[-1]

    tampered = replace(
        measurement,
        observed_value=999.0,
    )

    assert tampered.verify() is False


@pytest.mark.parametrize(
    "observed_value",
    (
        nan,
        inf,
        -inf,
    ),
)
def test_rejects_nonfinite_observed_value(
    tmp_path,
    observed_value,
):
    with pytest.raises(
        GovernanceInterventionOutcomeMeasurementValueError
    ):
        build_measurement(
            tmp_path,
            observed_value=observed_value,
        )


@pytest.mark.parametrize(
    "unit",
    (
        "",
        "   ",
    ),
)
def test_rejects_blank_unit(
    tmp_path,
    unit,
):
    with pytest.raises(
        GovernanceInterventionOutcomeMeasurementValueError
    ):
        build_measurement(
            tmp_path,
            unit=unit,
        )


def test_rejects_unit_mismatch(tmp_path):
    with pytest.raises(
        GovernanceInterventionOutcomeMeasurementLineageError
    ):
        build_measurement(
            tmp_path,
            unit="milliseconds",
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
    tmp_path,
    measurement_window_seconds,
):
    with pytest.raises(
        GovernanceInterventionOutcomeMeasurementValueError
    ):
        build_measurement(
            tmp_path,
            measurement_window_seconds=measurement_window_seconds,
        )


def test_measurement_can_record_window_shorter_than_requirement(tmp_path):
    measurement = build_measurement(
        tmp_path,
        measurement_window_seconds=60,
    )[-1]

    assert measurement.verify() is True
    assert measurement.measurement_window_seconds == 60

    # Sufficiency belongs to GEX-001I-C2 evaluation,
    # not the C1 measurement artifact.
    assert measurement.measurement_window_seconds < 86400


def test_measurement_can_record_too_few_records_without_judgment(
    tmp_path,
):
    (
        _,
        requirement,
        receipt,
        observation,
    ) = governed_evidence(tmp_path)

    reduced_observation = replace(
        observation,
        record_count=1,
    )

    reduced_observation = replace(
        reduced_observation,
        observation_hash=sha256_hex(
            canonical_json(
                reduced_observation.payload()
            )
        ),
    )

    assert reduced_observation.verify() is True

    measurement = GovernanceInterventionOutcomeMeasurementBuilder.build(
        requirement=requirement,
        execution_receipt=receipt,
        observation=reduced_observation,
        observed_value=95.0,
        unit="seconds",
        measurement_window_seconds=86400,
    )

    assert measurement.record_count == 1
    assert measurement.record_count < requirement.minimum_record_count

    # Again, C1 records evidence; C2 decides sufficiency.
    assert measurement.verify() is True


def test_rejects_tampered_requirement(tmp_path):
    (
        _,
        requirement,
        receipt,
        observation,
    ) = governed_evidence(tmp_path)

    tampered = replace(
        requirement,
        target_value=999.0,
    )

    assert tampered.verify() is False

    with pytest.raises(
        GovernanceInterventionOutcomeMeasurementLineageError
    ):
        GovernanceInterventionOutcomeMeasurementBuilder.build(
            requirement=tampered,
            execution_receipt=receipt,
            observation=observation,
            observed_value=95,
            unit="seconds",
            measurement_window_seconds=86400,
        )


def test_rejects_tampered_execution_receipt(tmp_path):
    (
        _,
        requirement,
        receipt,
        observation,
    ) = governed_evidence(tmp_path)

    tampered = replace(
        receipt,
        attempt_number=receipt.attempt_number + 1,
    )

    assert tampered.verify() is False

    with pytest.raises(
        GovernanceInterventionOutcomeMeasurementLineageError
    ):
        GovernanceInterventionOutcomeMeasurementBuilder.build(
            requirement=requirement,
            execution_receipt=tampered,
            observation=observation,
            observed_value=95,
            unit="seconds",
            measurement_window_seconds=86400,
        )


def test_rejects_tampered_observation(tmp_path):
    (
        _,
        requirement,
        receipt,
        observation,
    ) = governed_evidence(tmp_path)

    tampered = replace(
        observation,
        record_count=observation.record_count + 1,
    )

    assert tampered.verify() is False

    with pytest.raises(
        GovernanceInterventionOutcomeMeasurementLineageError
    ):
        GovernanceInterventionOutcomeMeasurementBuilder.build(
            requirement=requirement,
            execution_receipt=receipt,
            observation=tampered,
            observed_value=95,
            unit="seconds",
            measurement_window_seconds=86400,
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("tenant_id", "tenant-b"),
        ("contract_hash", "wrong-contract"),
        ("intervention_id", "wrong-intervention"),
        ("intervention_type", "WRONG_TYPE"),
    ),
)
def test_rejects_rehashed_observation_lineage_mismatch(
    tmp_path,
    field_name,
    bad_value,
):
    (
        _,
        requirement,
        receipt,
        observation,
    ) = governed_evidence(tmp_path)

    mismatched = replace(
        observation,
        **{
            field_name: bad_value,
        },
    )

    mismatched = replace(
        mismatched,
        observation_hash=sha256_hex(
            canonical_json(
                mismatched.payload()
            )
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionOutcomeMeasurementLineageError
    ):
        GovernanceInterventionOutcomeMeasurementBuilder.build(
            requirement=requirement,
            execution_receipt=receipt,
            observation=mismatched,
            observed_value=95,
            unit="seconds",
            measurement_window_seconds=86400,
        )


def test_rejects_observation_requirement_mismatch(tmp_path):
    (
        _,
        requirement,
        receipt,
        observation,
    ) = governed_evidence(tmp_path)

    mismatched = replace(
        observation,
        verification_requirement=(
            "Verify audit evidence continuity."
        ),
    )

    mismatched = replace(
        mismatched,
        observation_hash=sha256_hex(
            canonical_json(
                mismatched.payload()
            )
        ),
    )

    assert mismatched.verify() is True

    with pytest.raises(
        GovernanceInterventionOutcomeMeasurementLineageError
    ):
        GovernanceInterventionOutcomeMeasurementBuilder.build(
            requirement=requirement,
            execution_receipt=receipt,
            observation=mismatched,
            observed_value=95,
            unit="seconds",
            measurement_window_seconds=86400,
        )


def test_serialization_contains_measurement_hash(tmp_path):
    measurement = build_measurement(tmp_path)[-1]

    serialized = measurement.to_dict()

    assert (
        serialized["measurement_hash"]
        == measurement.measurement_hash
    )

    assert serialized["metric_id"] == "approval_latency_seconds"
    assert serialized["observed_value"] == 95.0
    assert serialized["unit"] == "seconds"


def test_measurement_contains_no_evaluation_or_verification_judgment(
    tmp_path,
):
    measurement = build_measurement(tmp_path)[-1]

    serialized = measurement.to_dict()

    forbidden_fields = {
        "operator",
        "target_value",
        "requirement_satisfied",
        "requirement_passed",
        "passed",
        "verified",
        "success",
        "outcome_achieved",
        "verification_result",
        "verification_disposition",
        "evaluation_result",
    }

    assert forbidden_fields.isdisjoint(serialized)


def test_builder_has_no_evaluation_or_verification_methods():
    forbidden_methods = (
        "evaluate",
        "compare",
        "verify_outcome",
        "determine_success",
        "determine_satisfaction",
        "issue_verification",
        "execute",
        "dispatch",
        "actuate",
    )

    for method_name in forbidden_methods:
        assert not hasattr(
            GovernanceInterventionOutcomeMeasurementBuilder,
            method_name,
        )