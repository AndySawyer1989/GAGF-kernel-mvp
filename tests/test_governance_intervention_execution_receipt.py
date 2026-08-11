from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_actuation_journal import (
    GovernanceInterventionActuationJournal,
    GovernanceInterventionActuationJournalRecord,
    GovernanceInterventionActuationState,
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
    GOVERNANCE_INTERVENTION_EXECUTION_RECEIPT_ID,
    GOVERNANCE_INTERVENTION_EXECUTION_RECEIPT_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_EXECUTION_RECEIPT_VERSION,
    GovernanceInterventionExecutionReceiptBuilder,
    InvalidGovernanceInterventionExecutionReceiptLineageError,
    InvalidGovernanceInterventionExecutionReceiptStateError,
)
from backend.app.gagf.governance_intervention_execution_result import (
    GovernanceInterventionExecutionDisposition,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


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
            "approval latency observed",
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
        disposition=(
            GovernanceInterventionActuationDisposition.ACCEPTED
        ),
        tenant_id=request.tenant_id,
        contract_hash=request.contract_hash,
        idempotency_key=request.idempotency_key,
        adapter_id="adapter-a",
        adapter_version="1.0.0",
        accepted=True,
    )


class StubExecutionAdapter:
    adapter_id = "adapter-a"
    adapter_version = "1.0.0"

    def __init__(
        self,
        *,
        disposition=(
            GovernanceInterventionExecutionDisposition.COMPLETED
        ),
        observations=("bounded adapter work completed",),
        error_code=None,
        error_message=None,
    ):
        self.disposition = disposition
        self.observations = observations
        self.error_code = error_code
        self.error_message = error_message

    def execute(
        self,
        *,
        request,
        contract,
        attempt_number,
    ):
        return GovernanceInterventionAdapterExecutionReport(
            disposition=self.disposition,
            observations=self.observations,
            error_code=self.error_code,
            error_message=self.error_message,
        )


def coordinated_execution(
    tmp_path,
    *,
    disposition=(
        GovernanceInterventionExecutionDisposition.COMPLETED
    ),
):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)

    if disposition is GovernanceInterventionExecutionDisposition.COMPLETED:
        adapter = StubExecutionAdapter()
    else:
        adapter = StubExecutionAdapter(
            disposition=disposition,
            observations=("bounded execution did not complete normally",),
            error_code="ADAPTER_RESULT",
            error_message="adapter reported non-completed disposition",
        )

    journal = GovernanceInterventionActuationJournal(
        tmp_path / "gex-001h.sqlite3"
    )

    coordinator = GovernanceInterventionExecutionCoordinator(
        journal=journal
    )

    coordinated = coordinator.execute(
        contract=contract,
        request=request,
        acceptance=acceptance,
        adapter=adapter,
        attempt_number=1,
    )

    return coordinated


def build_receipt(
    tmp_path,
    *,
    disposition=(
        GovernanceInterventionExecutionDisposition.COMPLETED
    ),
):
    coordinated = coordinated_execution(
        tmp_path,
        disposition=disposition,
    )

    receipt = GovernanceInterventionExecutionReceiptBuilder.build(
        execution_result=coordinated.execution_result,
        journal_record=coordinated.journal_record,
    )

    return coordinated, receipt


def test_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_EXECUTION_RECEIPT_ID
        == "governance-intervention-execution-receipt"
    )
    assert (
        GOVERNANCE_INTERVENTION_EXECUTION_RECEIPT_VERSION
        == "0.1.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_EXECUTION_RECEIPT_SCHEMA_VERSION
        == "1.0.0"
    )


def test_builds_receipt_from_real_coordinator_output(tmp_path):
    coordinated, receipt = build_receipt(tmp_path)

    assert receipt.verify() is True
    assert (
        receipt.result_hash
        == coordinated.execution_result.result_hash
    )
    assert (
        receipt.actuation_id
        == coordinated.journal_record.actuation_id
    )
    assert (
        receipt.journal_state
        is GovernanceInterventionActuationState.COMPLETED
    )


def test_receipt_is_deterministic(tmp_path):
    coordinated = coordinated_execution(tmp_path)

    first = GovernanceInterventionExecutionReceiptBuilder.build(
        execution_result=coordinated.execution_result,
        journal_record=coordinated.journal_record,
    )
    second = GovernanceInterventionExecutionReceiptBuilder.build(
        execution_result=coordinated.execution_result,
        journal_record=coordinated.journal_record,
    )

    assert first == second
    assert first.receipt_hash == second.receipt_hash


def test_receipt_is_frozen(tmp_path):
    _, receipt = build_receipt(tmp_path)

    with pytest.raises(FrozenInstanceError):
        receipt.receipt_hash = "tampered"


def test_serialization_preserves_execution_lineage(tmp_path):
    coordinated, receipt = build_receipt(tmp_path)

    serialized = receipt.to_dict()

    assert (
        serialized["tenant_id"]
        == coordinated.execution_result.tenant_id
    )
    assert (
        serialized["contract_hash"]
        == coordinated.execution_result.contract_hash
    )
    assert (
        serialized["idempotency_key"]
        == coordinated.execution_result.idempotency_key
    )
    assert (
        serialized["result_hash"]
        == coordinated.execution_result.result_hash
    )
    assert (
        serialized["receipt_hash"]
        == receipt.receipt_hash
    )


def test_tampered_receipt_fails_verification(tmp_path):
    _, receipt = build_receipt(tmp_path)

    tampered = replace(
        receipt,
        attempt_number=receipt.attempt_number + 1,
    )

    assert tampered.verify() is False


@pytest.mark.parametrize(
    ("disposition", "expected_state"),
    (
        (
            GovernanceInterventionExecutionDisposition.COMPLETED,
            GovernanceInterventionActuationState.COMPLETED,
        ),
        (
            GovernanceInterventionExecutionDisposition.FAILED,
            GovernanceInterventionActuationState.FAILED,
        ),
        (
            GovernanceInterventionExecutionDisposition.ABORTED,
            GovernanceInterventionActuationState.ABORTED,
        ),
        (
            GovernanceInterventionExecutionDisposition.ROLLBACK_REQUIRED,
            GovernanceInterventionActuationState.ROLLBACK_REQUIRED,
        ),
    ),
)
def test_all_governed_terminal_dispositions_can_be_receipted(
    tmp_path,
    disposition,
    expected_state,
):
    _, receipt = build_receipt(
        tmp_path,
        disposition=disposition,
    )

    assert receipt.disposition is disposition
    assert receipt.journal_state is expected_state
    assert receipt.verify() is True


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("tenant_id", "tenant-b"),
        ("actuation_id", "wrong-actuation"),
        ("contract_hash", "wrong-contract"),
        ("idempotency_key", "wrong-key"),
    ),
)
def test_rejects_core_journal_lineage_mismatch(
    tmp_path,
    field_name,
    bad_value,
):
    coordinated = coordinated_execution(tmp_path)

    journal_record = replace(
        coordinated.journal_record,
        **{field_name: bad_value},
    )

    with pytest.raises(
        InvalidGovernanceInterventionExecutionReceiptLineageError
    ):
        GovernanceInterventionExecutionReceiptBuilder.build(
            execution_result=coordinated.execution_result,
            journal_record=journal_record,
        )


@pytest.mark.parametrize(
    ("detail_name", "bad_value"),
    (
        ("result_hash", "wrong-result"),
        ("adapter_id", "wrong-adapter"),
        ("adapter_version", "9.9.9"),
        ("attempt_number", 99),
    ),
)
def test_rejects_terminal_journal_detail_mismatch(
    tmp_path,
    detail_name,
    bad_value,
):
    coordinated = coordinated_execution(tmp_path)

    details = dict(coordinated.journal_record.details)
    details[detail_name] = bad_value

    journal_record = replace(
        coordinated.journal_record,
        details=details,
    )

    with pytest.raises(
        InvalidGovernanceInterventionExecutionReceiptLineageError
    ):
        GovernanceInterventionExecutionReceiptBuilder.build(
            execution_result=coordinated.execution_result,
            journal_record=journal_record,
        )


def test_rejects_tampered_execution_result(tmp_path):
    coordinated = coordinated_execution(tmp_path)

    tampered = replace(
        coordinated.execution_result,
        attempt_number=2,
    )

    assert tampered.verify() is False

    with pytest.raises(
        InvalidGovernanceInterventionExecutionReceiptLineageError
    ):
        GovernanceInterventionExecutionReceiptBuilder.build(
            execution_result=tampered,
            journal_record=coordinated.journal_record,
        )


def test_rejects_non_matching_terminal_state(tmp_path):
    coordinated = coordinated_execution(tmp_path)

    journal_record = replace(
        coordinated.journal_record,
        current_state=GovernanceInterventionActuationState.FAILED,
    )

    with pytest.raises(
        InvalidGovernanceInterventionExecutionReceiptStateError
    ):
        GovernanceInterventionExecutionReceiptBuilder.build(
            execution_result=coordinated.execution_result,
            journal_record=journal_record,
        )


def test_rejects_incomplete_execution_lifecycle(tmp_path):
    coordinated = coordinated_execution(tmp_path)

    journal_record = replace(
        coordinated.journal_record,
        transition_count=2,
    )

    with pytest.raises(
        InvalidGovernanceInterventionExecutionReceiptStateError
    ):
        GovernanceInterventionExecutionReceiptBuilder.build(
            execution_result=coordinated.execution_result,
            journal_record=journal_record,
        )


def test_receipt_does_not_claim_outcome_verification(tmp_path):
    _, receipt = build_receipt(tmp_path)

    serialized = receipt.to_dict()

    assert "outcome_verified" not in serialized
    assert "desired_outcome_achieved" not in serialized
    assert "external_effect_verified" not in serialized
    assert "verification_result" not in serialized


def test_receipt_builder_has_no_execution_methods():
    assert not hasattr(
        GovernanceInterventionExecutionReceiptBuilder,
        "execute",
    )
    assert not hasattr(
        GovernanceInterventionExecutionReceiptBuilder,
        "dispatch",
    )
    assert not hasattr(
        GovernanceInterventionExecutionReceiptBuilder,
        "actuate",
    )
    assert not hasattr(
        GovernanceInterventionExecutionReceiptBuilder,
        "rollback",
    )
    assert not hasattr(
        GovernanceInterventionExecutionReceiptBuilder,
        "verify_outcome",
    )
