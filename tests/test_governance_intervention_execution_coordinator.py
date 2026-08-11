from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_actuation_journal import (
    GovernanceInterventionActuationJournal,
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
    GOVERNANCE_INTERVENTION_EXECUTION_ADAPTER_ID,
    GOVERNANCE_INTERVENTION_EXECUTION_ADAPTER_VERSION,
    GovernanceInterventionAdapterExecutionReport,
    GovernanceInterventionExecutionAdapter,
)
from backend.app.gagf.governance_intervention_execution_coordinator import (
    GOVERNANCE_INTERVENTION_EXECUTION_COORDINATOR_ID,
    GOVERNANCE_INTERVENTION_EXECUTION_COORDINATOR_VERSION,
    GovernanceInterventionExecutionAdapterError,
    GovernanceInterventionExecutionCoordinator,
    GovernanceInterventionExecutionCoordinatorError,
    GovernanceInterventionExecutionPreconditionError,
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
        disposition=(
            GovernanceInterventionExecutionDisposition.COMPLETED
        ),
        observations=(
            "bounded adapter work completed",
        ),
        error_code=None,
        error_message=None,
    ):
        self.disposition = disposition
        self.observations = observations
        self.error_code = error_code
        self.error_message = error_message
        self.call_count = 0
        self.last_request = None
        self.last_contract = None
        self.last_attempt_number = None

    def execute(
        self,
        *,
        request,
        contract,
        attempt_number,
    ):
        self.call_count += 1
        self.last_request = request
        self.last_contract = contract
        self.last_attempt_number = attempt_number

        return GovernanceInterventionAdapterExecutionReport(
            disposition=self.disposition,
            observations=self.observations,
            error_code=self.error_code,
            error_message=self.error_message,
        )


class RaisingExecutionAdapter:
    adapter_id = "adapter-a"
    adapter_version = "1.0.0"

    def __init__(self):
        self.call_count = 0

    def execute(
        self,
        *,
        request,
        contract,
        attempt_number,
    ):
        self.call_count += 1
        raise RuntimeError("adapter transport failure")


def make_coordinator(tmp_path):
    journal = GovernanceInterventionActuationJournal(
        tmp_path / "gex-001g.sqlite3"
    )

    coordinator = GovernanceInterventionExecutionCoordinator(
        journal=journal
    )

    return journal, coordinator


def execute_completed(tmp_path):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    adapter = StubExecutionAdapter()
    journal, coordinator = make_coordinator(tmp_path)

    result = coordinator.execute(
        contract=contract,
        request=request,
        acceptance=acceptance,
        adapter=adapter,
        attempt_number=1,
    )

    return (
        contract,
        request,
        acceptance,
        adapter,
        journal,
        result,
    )


def test_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_EXECUTION_ADAPTER_ID
        == "governance-intervention-execution-adapter"
    )
    assert (
        GOVERNANCE_INTERVENTION_EXECUTION_ADAPTER_VERSION
        == "0.1.0"
    )
    assert (
        GOVERNANCE_INTERVENTION_EXECUTION_COORDINATOR_ID
        == "governance-intervention-execution-coordinator"
    )
    assert (
        GOVERNANCE_INTERVENTION_EXECUTION_COORDINATOR_VERSION
        == "0.1.0"
    )


def test_runtime_protocol_accepts_compatible_adapter():
    assert isinstance(
        StubExecutionAdapter(),
        GovernanceInterventionExecutionAdapter,
    )


def test_completed_execution_invokes_adapter_once(tmp_path):
    (
        contract,
        request,
        _,
        adapter,
        _,
        result,
    ) = execute_completed(tmp_path)

    assert adapter.call_count == 1
    assert adapter.last_contract == contract
    assert adapter.last_request == request
    assert adapter.last_attempt_number == 1
    assert (
        result.execution_result.disposition
        is GovernanceInterventionExecutionDisposition.COMPLETED
    )


def test_completed_execution_finishes_journal(tmp_path):
    *_, result = execute_completed(tmp_path)

    assert (
        result.journal_record.current_state
        is GovernanceInterventionActuationState.COMPLETED
    )
    assert result.journal_record.transition_count == 3


def test_completed_execution_result_is_verified(tmp_path):
    *_, result = execute_completed(tmp_path)

    assert result.execution_result.verify() is True
    assert (
        result.journal_record.details["result_hash"]
        == result.execution_result.result_hash
    )


@pytest.mark.parametrize(
    ("disposition", "expected_state", "error_code"),
    (
        (
            GovernanceInterventionExecutionDisposition.FAILED,
            GovernanceInterventionActuationState.FAILED,
            "ADAPTER_FAILED",
        ),
        (
            GovernanceInterventionExecutionDisposition.ABORTED,
            GovernanceInterventionActuationState.ABORTED,
            "ADAPTER_ABORTED",
        ),
        (
            GovernanceInterventionExecutionDisposition.ROLLBACK_REQUIRED,
            GovernanceInterventionActuationState.ROLLBACK_REQUIRED,
            "ROLLBACK_REQUIRED",
        ),
    ),
)
def test_result_disposition_controls_terminal_journal_state(
    tmp_path,
    disposition,
    expected_state,
    error_code,
):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)

    adapter = StubExecutionAdapter(
        disposition=disposition,
        observations=("bounded attempt did not complete normally",),
        error_code=error_code,
        error_message="adapter reported bounded failure",
    )

    _, coordinator = make_coordinator(tmp_path)

    coordinated = coordinator.execute(
        contract=contract,
        request=request,
        acceptance=acceptance,
        adapter=adapter,
        attempt_number=1,
    )

    assert (
        coordinated.execution_result.disposition
        is disposition
    )
    assert (
        coordinated.journal_record.current_state
        is expected_state
    )


def test_acceptance_alone_does_not_execute_adapter(tmp_path):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    adapter = StubExecutionAdapter()

    journal, _ = make_coordinator(tmp_path)

    record = journal.begin(
        tenant_id=request.tenant_id,
        contract_hash=request.contract_hash,
        idempotency_key=request.idempotency_key,
        details={
            "adapter_id": acceptance.adapter_id,
            "adapter_version": acceptance.adapter_version,
        },
    )

    assert (
        record.current_state
        is GovernanceInterventionActuationState.ACCEPTED
    )
    assert adapter.call_count == 0


def test_coordinator_moves_through_started_before_terminal(
    tmp_path,
):
    (
        _,
        _,
        _,
        _,
        journal,
        result,
    ) = execute_completed(tmp_path)

    transitions = journal.list_transitions(
        result.journal_record.actuation_id
    )

    assert [
        transition.state
        for transition in transitions
    ] == [
        GovernanceInterventionActuationState.ACCEPTED,
        GovernanceInterventionActuationState.STARTED,
        GovernanceInterventionActuationState.COMPLETED,
    ]


def test_rejects_tampered_contract_before_adapter_call(tmp_path):
    contract = verified_contract()
    tampered = replace(
        contract,
        timeout_seconds=999,
    )

    request = make_request(contract)
    acceptance = make_acceptance(request)
    adapter = StubExecutionAdapter()
    _, coordinator = make_coordinator(tmp_path)

    assert tampered.verify() is False

    with pytest.raises(
        GovernanceInterventionExecutionPreconditionError
    ):
        coordinator.execute(
            contract=tampered,
            request=request,
            acceptance=acceptance,
            adapter=adapter,
            attempt_number=1,
        )

    assert adapter.call_count == 0


def test_rejects_request_tenant_mismatch_before_adapter_call(
    tmp_path,
):
    contract = verified_contract()
    request = make_request(contract)

    request = replace(
        request,
        tenant_id="tenant-b",
    )

    acceptance = make_acceptance(request)
    adapter = StubExecutionAdapter()
    _, coordinator = make_coordinator(tmp_path)

    with pytest.raises(
        GovernanceInterventionExecutionPreconditionError
    ):
        coordinator.execute(
            contract=contract,
            request=request,
            acceptance=acceptance,
            adapter=adapter,
            attempt_number=1,
        )

    assert adapter.call_count == 0


def test_rejects_unaccepted_request_before_adapter_call(tmp_path):
    contract = verified_contract()
    request = make_request(contract)

    acceptance = GovernanceInterventionActuationAcceptance(
        disposition=(
            GovernanceInterventionActuationDisposition.REJECTED
        ),
        tenant_id=request.tenant_id,
        contract_hash=request.contract_hash,
        idempotency_key=request.idempotency_key,
        adapter_id="adapter-a",
        adapter_version="1.0.0",
        accepted=False,
    )

    adapter = StubExecutionAdapter()
    _, coordinator = make_coordinator(tmp_path)

    with pytest.raises(
        GovernanceInterventionExecutionPreconditionError
    ):
        coordinator.execute(
            contract=contract,
            request=request,
            acceptance=acceptance,
            adapter=adapter,
            attempt_number=1,
        )

    assert adapter.call_count == 0


def test_rejects_acceptance_idempotency_mismatch(tmp_path):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)

    acceptance = replace(
        acceptance,
        idempotency_key="different-key",
    )

    adapter = StubExecutionAdapter()
    _, coordinator = make_coordinator(tmp_path)

    with pytest.raises(
        GovernanceInterventionExecutionPreconditionError
    ):
        coordinator.execute(
            contract=contract,
            request=request,
            acceptance=acceptance,
            adapter=adapter,
            attempt_number=1,
        )

    assert adapter.call_count == 0


def test_rejects_adapter_identity_mismatch(tmp_path):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)

    adapter = StubExecutionAdapter()
    adapter.adapter_id = "different-adapter"

    _, coordinator = make_coordinator(tmp_path)

    with pytest.raises(
        GovernanceInterventionExecutionPreconditionError
    ):
        coordinator.execute(
            contract=contract,
            request=request,
            acceptance=acceptance,
            adapter=adapter,
            attempt_number=1,
        )

    assert adapter.call_count == 0


@pytest.mark.parametrize(
    "attempt_number",
    (0, -1),
)
def test_rejects_attempt_below_one(
    tmp_path,
    attempt_number,
):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    adapter = StubExecutionAdapter()
    _, coordinator = make_coordinator(tmp_path)

    with pytest.raises(
        GovernanceInterventionExecutionPreconditionError
    ):
        coordinator.execute(
            contract=contract,
            request=request,
            acceptance=acceptance,
            adapter=adapter,
            attempt_number=attempt_number,
        )

    assert adapter.call_count == 0


def test_rejects_attempt_above_contract_limit(tmp_path):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    adapter = StubExecutionAdapter()
    _, coordinator = make_coordinator(tmp_path)

    with pytest.raises(
        GovernanceInterventionExecutionPreconditionError
    ):
        coordinator.execute(
            contract=contract,
            request=request,
            acceptance=acceptance,
            adapter=adapter,
            attempt_number=contract.max_attempts + 1,
        )

    assert adapter.call_count == 0


def test_coordination_result_is_frozen(tmp_path):
    *_, coordinated = execute_completed(tmp_path)

    with pytest.raises(FrozenInstanceError):
        coordinated.journal_record = None


def test_coordination_serialization_preserves_result_and_journal(
    tmp_path,
):
    *_, coordinated = execute_completed(tmp_path)

    serialized = coordinated.to_dict()

    assert (
        serialized["execution_result"]["result_hash"]
        == coordinated.execution_result.result_hash
    )
    assert (
        serialized["journal_record"]["actuation_id"]
        == coordinated.journal_record.actuation_id
    )


def test_completed_does_not_claim_outcome_verification(tmp_path):
    *_, coordinated = execute_completed(tmp_path)

    serialized = coordinated.to_dict()
    execution = serialized["execution_result"]

    assert "outcome_verified" not in execution
    assert "desired_outcome_achieved" not in execution
    assert "verification_receipt" not in execution
    assert "execution_receipt" not in serialized


def test_adapter_report_is_not_governed_result():
    report = GovernanceInterventionAdapterExecutionReport(
        disposition=(
            GovernanceInterventionExecutionDisposition.COMPLETED
        ),
        observations=("bounded work completed",),
    )

    assert not hasattr(report, "result_hash")
    assert not hasattr(report, "receipt_hash")
    assert not hasattr(report, "verify")


def test_coordinator_exposes_no_receipt_or_outcome_verifier(
    tmp_path,
):
    _, coordinator = make_coordinator(tmp_path)

    assert not hasattr(coordinator, "build_receipt")
    assert not hasattr(coordinator, "issue_receipt")
    assert not hasattr(coordinator, "verify_outcome")
    assert not hasattr(coordinator, "rollback")


def test_unexpected_adapter_exception_marks_journal_failed(
    tmp_path,
):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    adapter = RaisingExecutionAdapter()

    journal, coordinator = make_coordinator(tmp_path)

    with pytest.raises(
        GovernanceInterventionExecutionAdapterError
    ) as exc_info:
        coordinator.execute(
            contract=contract,
            request=request,
            acceptance=acceptance,
            adapter=adapter,
            attempt_number=1,
        )

    assert adapter.call_count == 1
    assert isinstance(exc_info.value.__cause__, RuntimeError)

    actuation_id = (
        GovernanceInterventionActuationJournal
        .derive_actuation_id(
            tenant_id=request.tenant_id,
            contract_hash=request.contract_hash,
            idempotency_key=request.idempotency_key,
        )
    )

    record = journal.get(actuation_id)

    assert record is not None
    assert (
        record.current_state
        is GovernanceInterventionActuationState.FAILED
    )
    assert record.transition_count == 3
    assert record.details["adapter_id"] == adapter.adapter_id
    assert (
        record.details["adapter_version"]
        == adapter.adapter_version
    )
    assert record.details["attempt_number"] == 1
    assert record.details["error_type"] == "RuntimeError"
    assert (
        record.details["error_message"]
        == "adapter transport failure"
    )


def test_unexpected_adapter_exception_creates_no_result(
    tmp_path,
):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    adapter = RaisingExecutionAdapter()

    journal, coordinator = make_coordinator(tmp_path)

    with pytest.raises(
        GovernanceInterventionExecutionAdapterError
    ):
        coordinator.execute(
            contract=contract,
            request=request,
            acceptance=acceptance,
            adapter=adapter,
            attempt_number=1,
        )

    actuation_id = (
        GovernanceInterventionActuationJournal
        .derive_actuation_id(
            tenant_id=request.tenant_id,
            contract_hash=request.contract_hash,
            idempotency_key=request.idempotency_key,
        )
    )

    transitions = journal.list_transitions(actuation_id)

    assert [
        transition.state
        for transition in transitions
    ] == [
        GovernanceInterventionActuationState.ACCEPTED,
        GovernanceInterventionActuationState.STARTED,
        GovernanceInterventionActuationState.FAILED,
    ]

    assert all(
        "result_hash" not in transition.details
        for transition in transitions
    )


def test_error_hierarchy_is_stable():
    assert issubclass(
        GovernanceInterventionExecutionPreconditionError,
        GovernanceInterventionExecutionCoordinatorError,
    )
    assert issubclass(
        GovernanceInterventionExecutionAdapterError,
        GovernanceInterventionExecutionCoordinatorError,
    )
