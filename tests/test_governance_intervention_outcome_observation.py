from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_actuation_journal import (
    GovernanceInterventionActuationJournal,
)
from backend.app.gagf.governance_intervention_verification_commitment import (
    GovernanceInterventionVerificationCommitmentBuilder,
)
from backend.app.gagf.governance_intervention_verification_requirement import (
    GovernanceInterventionVerificationOperator,
    GovernanceInterventionVerificationRequirementBuilder,
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
from backend.app.gagf.governance_intervention_outcome_observation import (
    GOVERNANCE_INTERVENTION_OUTCOME_OBSERVATION_ID,
    GOVERNANCE_INTERVENTION_OUTCOME_OBSERVATION_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_OUTCOME_OBSERVATION_VERSION,
    GovernanceInterventionOutcomeObservationBuilder,
    GovernanceInterventionOutcomeObservationEvidenceError,
    GovernanceInterventionOutcomeObservationIndependenceError,
    GovernanceInterventionOutcomeObservationLineageError,
    GovernanceInterventionOutcomeObservationRequirementError,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


VERIFICATION_REQUIREMENT = "approval latency observed"


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
            VERIFICATION_REQUIREMENT,
            "approval workflow remains available",
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


def make_verification_commitment(
    contract: GovernanceInterventionActuationContract,
):
    legacy_requirement = contract.verification_requirements[0]

    requirement = (
        GovernanceInterventionVerificationRequirementBuilder.build(
            actuation_contract=contract,
            legacy_requirement=legacy_requirement,
            requirement_id="execution-fixture-verification",
            description=(
                "Structured verification requirement for the governed "
                "execution test fixture."
            ),
            metric_id="execution_fixture_metric",
            operator=GovernanceInterventionVerificationOperator.EQ,
            target_value=1,
            unit="fixture-unit",
            measurement_window_seconds=1,
            minimum_record_count=1,
        )
    )

    return GovernanceInterventionVerificationCommitmentBuilder.build(
        actuation_contract=contract,
        requirement=requirement,
    )


def make_verification_commitment_hash(
    contract: GovernanceInterventionActuationContract,
) -> str:
    legacy_requirement = contract.verification_requirements[0]

    requirement = (
        GovernanceInterventionVerificationRequirementBuilder.build(
            actuation_contract=contract,
            legacy_requirement=legacy_requirement,
            requirement_id="execution-fixture-verification",
            description=(
                "Structured verification requirement for the governed "
                "execution test fixture."
            ),
            metric_id="execution_fixture_metric",
            operator=GovernanceInterventionVerificationOperator.EQ,
            target_value=1,
            unit="fixture-unit",
            measurement_window_seconds=1,
            minimum_record_count=1,
        )
    )

    commitment = (
        GovernanceInterventionVerificationCommitmentBuilder.build(
            actuation_contract=contract,
            requirement=requirement,
        )
    )

    return commitment.commitment_hash


def make_request(
    contract: GovernanceInterventionActuationContract,
) -> GovernanceInterventionActuationRequest:
    return GovernanceInterventionActuationRequest(
        port_id="governance-intervention-actuation-port",
        port_version="0.1.0",
        tenant_id=contract.tenant_id,
        contract_hash=contract.contract_hash,
        intervention_id=contract.intervention_id,
        intervention_type=contract.intervention_type,
        verification_commitment_hash=(
            make_verification_commitment_hash(contract)
        ),
        idempotency_key="execution-key-1",
    )


def make_acceptance(
    request: GovernanceInterventionActuationRequest,
) -> GovernanceInterventionActuationAcceptance:
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


def governed_execution(tmp_path):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)

    journal = GovernanceInterventionActuationJournal(
        tmp_path / "gex-001ia.sqlite3"
    )

    coordinator = GovernanceInterventionExecutionCoordinator(
        journal=journal
    )

    coordinated = coordinator.execute(
        contract=contract,
        request=request,
        verification_commitment=make_verification_commitment(contract),
        acceptance=acceptance,
        adapter=StubExecutionAdapter(),
        attempt_number=1,
    )

    receipt = GovernanceInterventionExecutionReceiptBuilder.build(
        execution_result=coordinated.execution_result,
        journal_record=coordinated.journal_record,
    )

    return contract, coordinated, receipt


def build_observation(tmp_path):
    contract, coordinated, receipt = governed_execution(tmp_path)

    observation = GovernanceInterventionOutcomeObservationBuilder.build(
        contract=contract,
        execution_receipt=receipt,
        verification_requirement=VERIFICATION_REQUIREMENT,
        source_id="independent-metrics-service",
        source_kind="workflow_telemetry",
        observed_at="2026-08-10T01:00:00Z",
        observation_summary=(
            "post-execution approval latency telemetry collected"
        ),
        evidence_references=(
            "telemetry://approval-latency/window-001",
            "snapshot://workflow-state/post-001",
        ),
        record_count=42,
    )

    return contract, coordinated, receipt, observation


def test_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_OUTCOME_OBSERVATION_ID
        == "governance-intervention-outcome-observation"
    )
    assert (
        GOVERNANCE_INTERVENTION_OUTCOME_OBSERVATION_VERSION
        == "0.1.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_OUTCOME_OBSERVATION_SCHEMA_VERSION
        == "1.0.0"
    )


def test_builds_observation_from_real_execution_receipt(tmp_path):
    contract, coordinated, receipt, observation = build_observation(
        tmp_path
    )

    assert observation.verify() is True
    assert observation.tenant_id == contract.tenant_id
    assert observation.contract_hash == contract.contract_hash
    assert observation.execution_receipt_hash == receipt.receipt_hash
    assert (
        observation.execution_result_hash
        == coordinated.execution_result.result_hash
    )
    assert observation.actuation_id == receipt.actuation_id
    assert observation.intervention_id == contract.intervention_id
    assert observation.intervention_type == contract.intervention_type


def test_observation_binds_precommitted_requirement(tmp_path):
    _, _, _, observation = build_observation(tmp_path)

    assert (
        observation.verification_requirement
        == VERIFICATION_REQUIREMENT
    )


def test_observation_binds_execution_adapter_identity(tmp_path):
    _, _, receipt, observation = build_observation(tmp_path)

    assert observation.execution_adapter_id == receipt.adapter_id
    assert observation.execution_adapter_version == receipt.adapter_version


def test_observation_preserves_independent_source_identity(tmp_path):
    _, _, _, observation = build_observation(tmp_path)

    assert observation.source_id == "independent-metrics-service"
    assert observation.source_kind == "workflow_telemetry"


def test_observation_preserves_evidence_references(tmp_path):
    _, _, _, observation = build_observation(tmp_path)

    assert observation.evidence_references == (
        "telemetry://approval-latency/window-001",
        "snapshot://workflow-state/post-001",
    )
    assert observation.record_count == 42


def test_observation_is_deterministic(tmp_path):
    contract, _, receipt = governed_execution(tmp_path)

    kwargs = {
        "contract": contract,
        "execution_receipt": receipt,
        "verification_requirement": VERIFICATION_REQUIREMENT,
        "source_id": "independent-metrics-service",
        "source_kind": "workflow_telemetry",
        "observed_at": "2026-08-10T01:00:00Z",
        "observation_summary": "post-execution telemetry collected",
        "evidence_references": (
            "telemetry://approval-latency/window-001",
        ),
        "record_count": 42,
    }

    first = GovernanceInterventionOutcomeObservationBuilder.build(
        **kwargs
    )
    second = GovernanceInterventionOutcomeObservationBuilder.build(
        **kwargs
    )

    assert first == second
    assert first.observation_hash == second.observation_hash


def test_observation_is_frozen(tmp_path):
    _, _, _, observation = build_observation(tmp_path)

    with pytest.raises(FrozenInstanceError):
        observation.source_id = "tampered-source"


def test_tampered_observation_fails_verification(tmp_path):
    _, _, _, observation = build_observation(tmp_path)

    tampered = replace(
        observation,
        record_count=observation.record_count + 1,
    )

    assert tampered.verify() is False


def test_serialization_contains_observation_hash(tmp_path):
    _, _, _, observation = build_observation(tmp_path)

    serialized = observation.to_dict()

    assert serialized["observation_hash"] == observation.observation_hash
    assert serialized["source_id"] == observation.source_id
    assert serialized["record_count"] == 42


def test_rejects_requirement_not_fixed_in_contract(tmp_path):
    contract, _, receipt = governed_execution(tmp_path)

    with pytest.raises(
        GovernanceInterventionOutcomeObservationRequirementError
    ):
        GovernanceInterventionOutcomeObservationBuilder.build(
            contract=contract,
            execution_receipt=receipt,
            verification_requirement="invented after execution",
            source_id="independent-metrics-service",
            source_kind="workflow_telemetry",
            observed_at="2026-08-10T01:00:00Z",
            observation_summary="observation",
            evidence_references=("evidence://1",),
            record_count=1,
        )


def test_rejects_execution_adapter_as_observation_source(tmp_path):
    contract, _, receipt = governed_execution(tmp_path)

    with pytest.raises(
        GovernanceInterventionOutcomeObservationIndependenceError
    ):
        GovernanceInterventionOutcomeObservationBuilder.build(
            contract=contract,
            execution_receipt=receipt,
            verification_requirement=VERIFICATION_REQUIREMENT,
            source_id=receipt.adapter_id,
            source_kind="adapter_report",
            observed_at="2026-08-10T01:00:00Z",
            observation_summary="adapter self-certification",
            evidence_references=("adapter://self-report",),
            record_count=1,
        )


def test_rejects_tampered_contract(tmp_path):
    contract, _, receipt = governed_execution(tmp_path)

    tampered_contract = replace(
        contract,
        requested_effect="tampered requested effect",
    )

    assert tampered_contract.verify() is False

    with pytest.raises(
        GovernanceInterventionOutcomeObservationLineageError
    ):
        GovernanceInterventionOutcomeObservationBuilder.build(
            contract=tampered_contract,
            execution_receipt=receipt,
            verification_requirement=VERIFICATION_REQUIREMENT,
            source_id="independent-source",
            source_kind="workflow_telemetry",
            observed_at="2026-08-10T01:00:00Z",
            observation_summary="observation",
            evidence_references=("evidence://1",),
            record_count=1,
        )


def test_rejects_tampered_execution_receipt(tmp_path):
    contract, _, receipt = governed_execution(tmp_path)

    tampered_receipt = replace(
        receipt,
        attempt_number=receipt.attempt_number + 1,
    )

    assert tampered_receipt.verify() is False

    with pytest.raises(
        GovernanceInterventionOutcomeObservationLineageError
    ):
        GovernanceInterventionOutcomeObservationBuilder.build(
            contract=contract,
            execution_receipt=tampered_receipt,
            verification_requirement=VERIFICATION_REQUIREMENT,
            source_id="independent-source",
            source_kind="workflow_telemetry",
            observed_at="2026-08-10T01:00:00Z",
            observation_summary="observation",
            evidence_references=("evidence://1",),
            record_count=1,
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
def test_rejects_execution_receipt_lineage_mismatch(
    tmp_path,
    field_name,
    bad_value,
):
    contract, _, receipt = governed_execution(tmp_path)

    tampered_receipt = replace(
        receipt,
        **{field_name: bad_value},
    )

    payload = tampered_receipt.payload()

    tampered_receipt = replace(
        tampered_receipt,
        receipt_hash=sha256_hex(
            canonical_json(payload)
        ),
    )

    assert tampered_receipt.verify() is True

    with pytest.raises(
        GovernanceInterventionOutcomeObservationLineageError
    ):
        GovernanceInterventionOutcomeObservationBuilder.build(
            contract=contract,
            execution_receipt=tampered_receipt,
            verification_requirement=VERIFICATION_REQUIREMENT,
            source_id="independent-source",
            source_kind="workflow_telemetry",
            observed_at="2026-08-10T01:00:00Z",
            observation_summary="observation",
            evidence_references=("evidence://1",),
            record_count=1,
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("source_id", "   "),
        ("source_kind", ""),
        ("observed_at", " "),
        ("observation_summary", ""),
    ),
)
def test_rejects_empty_required_observation_fields(
    tmp_path,
    field_name,
    bad_value,
):
    contract, _, receipt = governed_execution(tmp_path)

    kwargs = {
        "contract": contract,
        "execution_receipt": receipt,
        "verification_requirement": VERIFICATION_REQUIREMENT,
        "source_id": "independent-source",
        "source_kind": "workflow_telemetry",
        "observed_at": "2026-08-10T01:00:00Z",
        "observation_summary": "observation",
        "evidence_references": ("evidence://1",),
        "record_count": 1,
    }

    kwargs[field_name] = bad_value

    with pytest.raises(
        GovernanceInterventionOutcomeObservationEvidenceError
    ):
        GovernanceInterventionOutcomeObservationBuilder.build(
            **kwargs
        )


def test_rejects_empty_evidence_references(tmp_path):
    contract, _, receipt = governed_execution(tmp_path)

    with pytest.raises(
        GovernanceInterventionOutcomeObservationEvidenceError
    ):
        GovernanceInterventionOutcomeObservationBuilder.build(
            contract=contract,
            execution_receipt=receipt,
            verification_requirement=VERIFICATION_REQUIREMENT,
            source_id="independent-source",
            source_kind="workflow_telemetry",
            observed_at="2026-08-10T01:00:00Z",
            observation_summary="observation",
            evidence_references=(),
            record_count=1,
        )


def test_rejects_duplicate_evidence_references(tmp_path):
    contract, _, receipt = governed_execution(tmp_path)

    with pytest.raises(
        GovernanceInterventionOutcomeObservationEvidenceError
    ):
        GovernanceInterventionOutcomeObservationBuilder.build(
            contract=contract,
            execution_receipt=receipt,
            verification_requirement=VERIFICATION_REQUIREMENT,
            source_id="independent-source",
            source_kind="workflow_telemetry",
            observed_at="2026-08-10T01:00:00Z",
            observation_summary="observation",
            evidence_references=(
                "evidence://1",
                "evidence://1",
            ),
            record_count=2,
        )


@pytest.mark.parametrize(
    "record_count",
    (
        0,
        -1,
        -100,
    ),
)
def test_rejects_invalid_record_count(
    tmp_path,
    record_count,
):
    contract, _, receipt = governed_execution(tmp_path)

    with pytest.raises(
        GovernanceInterventionOutcomeObservationEvidenceError
    ):
        GovernanceInterventionOutcomeObservationBuilder.build(
            contract=contract,
            execution_receipt=receipt,
            verification_requirement=VERIFICATION_REQUIREMENT,
            source_id="independent-source",
            source_kind="workflow_telemetry",
            observed_at="2026-08-10T01:00:00Z",
            observation_summary="observation",
            evidence_references=("evidence://1",),
            record_count=record_count,
        )


def test_observation_contains_no_verification_judgment(tmp_path):
    _, _, _, observation = build_observation(tmp_path)

    serialized = observation.to_dict()

    forbidden_fields = {
        "verified",
        "success",
        "outcome_achieved",
        "requirement_passed",
        "caused_by_intervention",
        "verification_result",
        "verification_disposition",
    }

    assert forbidden_fields.isdisjoint(serialized)


def test_builder_has_no_verification_or_execution_methods():
    forbidden_methods = (
        "execute",
        "dispatch",
        "actuate",
        "verify_outcome",
        "evaluate",
        "determine_success",
        "rollback",
    )

    for method_name in forbidden_methods:
        assert not hasattr(
            GovernanceInterventionOutcomeObservationBuilder,
            method_name,
        )
