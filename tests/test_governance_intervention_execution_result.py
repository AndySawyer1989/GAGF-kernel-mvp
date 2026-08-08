from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.governance_intervention_actuation_contract import (
    GovernanceInterventionActuationContract,
)
from backend.app.gagf.governance_intervention_actuation_journal import (
    GovernanceInterventionActuationJournalRecord,
    GovernanceInterventionActuationState,
)
from backend.app.gagf.governance_intervention_actuation_port import (
    GovernanceInterventionActuationAcceptance,
    GovernanceInterventionActuationDisposition,
    GovernanceInterventionActuationRequest,
)
from backend.app.gagf.governance_intervention_execution_result import (
    GOVERNANCE_INTERVENTION_EXECUTION_RESULT_ID,
    GOVERNANCE_INTERVENTION_EXECUTION_RESULT_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_EXECUTION_RESULT_VERSION,
    GovernanceInterventionExecutionDisposition,
    GovernanceInterventionExecutionResultBuilder,
    InvalidGovernanceInterventionExecutionDispositionError,
    InvalidGovernanceInterventionExecutionLineageError,
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
        verification_requirements=("approval latency observed",),
        contract_hash="",
    )


def verified_contract() -> GovernanceInterventionActuationContract:
    from dataclasses import replace

    from backend.app.gagf.scientific_authority_guard import (
        canonical_json,
        sha256_hex,
    )

    contract = make_contract()

    payload = contract.to_dict()
    payload.pop("contract_hash")

    return replace(
        contract,
        contract_hash=sha256_hex(canonical_json(payload)),
    )


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
        adapter_id="adapter-a",
        adapter_version="1.0.0",
        accepted=True,
    )


def make_journal(
    request: GovernanceInterventionActuationRequest,
    state: GovernanceInterventionActuationState = (
        GovernanceInterventionActuationState.STARTED
    ),
) -> GovernanceInterventionActuationJournalRecord:
    return GovernanceInterventionActuationJournalRecord(
        actuation_id="actuation-1",
        tenant_id=request.tenant_id,
        contract_hash=request.contract_hash,
        idempotency_key=request.idempotency_key,
        current_state=state,
        transition_count=2,
        details=None,
    )


def build_result(
    *,
    disposition: GovernanceInterventionExecutionDisposition = (
        GovernanceInterventionExecutionDisposition.COMPLETED
    ),
    error_code: str | None = None,
    error_message: str | None = None,
):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    journal = make_journal(request)

    return GovernanceInterventionExecutionResultBuilder.build(
        contract=contract,
        request=request,
        acceptance=acceptance,
        journal_record=journal,
        adapter_id="adapter-a",
        adapter_version="1.0.0",
        attempt_number=1,
        disposition=disposition,
        observations=("adapter reported bounded work complete",),
        error_code=error_code,
        error_message=error_message,
    )


def test_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_EXECUTION_RESULT_ID
        == "governance-intervention-execution-result"
    )
    assert GOVERNANCE_INTERVENTION_EXECUTION_RESULT_VERSION == "0.1.0"
    assert (
        GOVERNANCE_INTERVENTION_EXECUTION_RESULT_SCHEMA_VERSION
        == "1.0.0"
    )


def test_builds_completed_result():
    result = build_result()

    assert result.disposition is (
        GovernanceInterventionExecutionDisposition.COMPLETED
    )
    assert result.verify() is True
    assert result.error_code is None
    assert result.error_message is None


def test_result_is_deterministic():
    first = build_result()
    second = build_result()

    assert first.result_hash == second.result_hash


def test_result_is_frozen():
    result = build_result()

    with pytest.raises(FrozenInstanceError):
        result.attempt_number = 2


def test_to_dict_contains_result_hash():
    result = build_result()
    payload = result.to_dict()

    assert payload["result_hash"] == result.result_hash
    assert payload["actuation_id"] == "actuation-1"
    assert payload["adapter_id"] == "adapter-a"


def test_completed_does_not_expose_verification_claims():
    payload = build_result().to_dict()

    assert "verified" not in payload
    assert "outcome_verified" not in payload
    assert "desired_outcome_achieved" not in payload
    assert "successful" not in payload


@pytest.mark.parametrize(
    "disposition",
    [
        GovernanceInterventionExecutionDisposition.FAILED,
        GovernanceInterventionExecutionDisposition.ABORTED,
        GovernanceInterventionExecutionDisposition.ROLLBACK_REQUIRED,
    ],
)
def test_non_completed_result_requires_error_code(disposition):
    with pytest.raises(
        InvalidGovernanceInterventionExecutionDispositionError
    ):
        build_result(disposition=disposition)


@pytest.mark.parametrize(
    "disposition",
    [
        GovernanceInterventionExecutionDisposition.FAILED,
        GovernanceInterventionExecutionDisposition.ABORTED,
        GovernanceInterventionExecutionDisposition.ROLLBACK_REQUIRED,
    ],
)
def test_non_completed_result_accepts_error_code(disposition):
    result = build_result(
        disposition=disposition,
        error_code="ADAPTER_FAILURE",
        error_message="bounded adapter work did not complete",
    )

    assert result.disposition is disposition
    assert result.error_code == "ADAPTER_FAILURE"
    assert result.verify() is True


def test_completed_rejects_error_code():
    with pytest.raises(
        InvalidGovernanceInterventionExecutionDispositionError
    ):
        build_result(
            error_code="SHOULD_NOT_EXIST",
        )


def test_completed_rejects_error_message():
    with pytest.raises(
        InvalidGovernanceInterventionExecutionDispositionError
    ):
        build_result(
            error_message="should not exist",
        )


def test_rejects_non_started_journal():
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    journal = make_journal(
        request,
        GovernanceInterventionActuationState.ACCEPTED,
    )

    with pytest.raises(
        InvalidGovernanceInterventionExecutionLineageError
    ):
        GovernanceInterventionExecutionResultBuilder.build(
            contract=contract,
            request=request,
            acceptance=acceptance,
            journal_record=journal,
            adapter_id="adapter-a",
            adapter_version="1.0.0",
            attempt_number=1,
            disposition=(
                GovernanceInterventionExecutionDisposition.COMPLETED
            ),
        )


def test_rejects_unaccepted_request():
    contract = verified_contract()
    request = make_request(contract)

    acceptance = GovernanceInterventionActuationAcceptance(
        disposition=GovernanceInterventionActuationDisposition.REJECTED,
        tenant_id=request.tenant_id,
        contract_hash=request.contract_hash,
        idempotency_key=request.idempotency_key,
        adapter_id="adapter-a",
        adapter_version="1.0.0",
        accepted=False,
    )

    journal = make_journal(request)

    with pytest.raises(
        InvalidGovernanceInterventionExecutionLineageError
    ):
        GovernanceInterventionExecutionResultBuilder.build(
            contract=contract,
            request=request,
            acceptance=acceptance,
            journal_record=journal,
            adapter_id="adapter-a",
            adapter_version="1.0.0",
            attempt_number=1,
            disposition=(
                GovernanceInterventionExecutionDisposition.COMPLETED
            ),
        )


def test_rejects_adapter_identity_mismatch():
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    journal = make_journal(request)

    with pytest.raises(
        InvalidGovernanceInterventionExecutionLineageError
    ):
        GovernanceInterventionExecutionResultBuilder.build(
            contract=contract,
            request=request,
            acceptance=acceptance,
            journal_record=journal,
            adapter_id="different-adapter",
            adapter_version="1.0.0",
            attempt_number=1,
            disposition=(
                GovernanceInterventionExecutionDisposition.COMPLETED
            ),
        )


def test_rejects_attempt_below_one():
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    journal = make_journal(request)

    with pytest.raises(
        InvalidGovernanceInterventionExecutionLineageError
    ):
        GovernanceInterventionExecutionResultBuilder.build(
            contract=contract,
            request=request,
            acceptance=acceptance,
            journal_record=journal,
            adapter_id="adapter-a",
            adapter_version="1.0.0",
            attempt_number=0,
            disposition=(
                GovernanceInterventionExecutionDisposition.COMPLETED
            ),
        )


def test_rejects_attempt_above_contract_limit():
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    journal = make_journal(request)

    with pytest.raises(
        InvalidGovernanceInterventionExecutionLineageError
    ):
        GovernanceInterventionExecutionResultBuilder.build(
            contract=contract,
            request=request,
            acceptance=acceptance,
            journal_record=journal,
            adapter_id="adapter-a",
            adapter_version="1.0.0",
            attempt_number=contract.max_attempts + 1,
            disposition=(
                GovernanceInterventionExecutionDisposition.COMPLETED
            ),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("adapter_id", ""),
        ("adapter_id", "   "),
        ("adapter_version", ""),
        ("adapter_version", "   "),
    ],
)
def test_rejects_blank_adapter_identity(field, value):
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    journal = make_journal(request)

    kwargs = {
        "contract": contract,
        "request": request,
        "acceptance": acceptance,
        "journal_record": journal,
        "adapter_id": "adapter-a",
        "adapter_version": "1.0.0",
        "attempt_number": 1,
        "disposition": (
            GovernanceInterventionExecutionDisposition.COMPLETED
        ),
    }

    kwargs[field] = value

    with pytest.raises(
        InvalidGovernanceInterventionExecutionLineageError
    ):
        GovernanceInterventionExecutionResultBuilder.build(**kwargs)


def test_rejects_blank_observation():
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)
    journal = make_journal(request)

    with pytest.raises(
        InvalidGovernanceInterventionExecutionDispositionError
    ):
        GovernanceInterventionExecutionResultBuilder.build(
            contract=contract,
            request=request,
            acceptance=acceptance,
            journal_record=journal,
            adapter_id="adapter-a",
            adapter_version="1.0.0",
            attempt_number=1,
            disposition=(
                GovernanceInterventionExecutionDisposition.COMPLETED
            ),
            observations=("valid", "   "),
        )


def test_rejects_contract_request_lineage_mismatch():
    contract = verified_contract()
    request = make_request(contract)

    request = GovernanceInterventionActuationRequest(
        port_id=request.port_id,
        port_version=request.port_version,
        tenant_id="tenant-b",
        contract_hash=request.contract_hash,
        intervention_id=request.intervention_id,
        intervention_type=request.intervention_type,
        idempotency_key=request.idempotency_key,
    )

    acceptance = make_acceptance(request)
    journal = make_journal(request)

    with pytest.raises(
        InvalidGovernanceInterventionExecutionLineageError
    ):
        GovernanceInterventionExecutionResultBuilder.build(
            contract=contract,
            request=request,
            acceptance=acceptance,
            journal_record=journal,
            adapter_id="adapter-a",
            adapter_version="1.0.0",
            attempt_number=1,
            disposition=(
                GovernanceInterventionExecutionDisposition.COMPLETED
            ),
        )


def test_rejects_acceptance_request_lineage_mismatch():
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)

    acceptance = GovernanceInterventionActuationAcceptance(
        disposition=acceptance.disposition,
        tenant_id=acceptance.tenant_id,
        contract_hash=acceptance.contract_hash,
        idempotency_key="other-key",
        adapter_id=acceptance.adapter_id,
        adapter_version=acceptance.adapter_version,
        accepted=acceptance.accepted,
    )

    journal = make_journal(request)

    with pytest.raises(
        InvalidGovernanceInterventionExecutionLineageError
    ):
        GovernanceInterventionExecutionResultBuilder.build(
            contract=contract,
            request=request,
            acceptance=acceptance,
            journal_record=journal,
            adapter_id="adapter-a",
            adapter_version="1.0.0",
            attempt_number=1,
            disposition=(
                GovernanceInterventionExecutionDisposition.COMPLETED
            ),
        )


def test_rejects_journal_request_lineage_mismatch():
    contract = verified_contract()
    request = make_request(contract)
    acceptance = make_acceptance(request)

    journal = GovernanceInterventionActuationJournalRecord(
        actuation_id="actuation-1",
        tenant_id=request.tenant_id,
        contract_hash="wrong-contract",
        idempotency_key=request.idempotency_key,
        current_state=GovernanceInterventionActuationState.STARTED,
        transition_count=2,
        details=None,
    )

    with pytest.raises(
        InvalidGovernanceInterventionExecutionLineageError
    ):
        GovernanceInterventionExecutionResultBuilder.build(
            contract=contract,
            request=request,
            acceptance=acceptance,
            journal_record=journal,
            adapter_id="adapter-a",
            adapter_version="1.0.0",
            attempt_number=1,
            disposition=(
                GovernanceInterventionExecutionDisposition.COMPLETED
            ),
        )


def test_builder_has_no_execution_methods():
    assert not hasattr(
        GovernanceInterventionExecutionResultBuilder,
        "execute",
    )
    assert not hasattr(
        GovernanceInterventionExecutionResultBuilder,
        "dispatch",
    )
    assert not hasattr(
        GovernanceInterventionExecutionResultBuilder,
        "actuate",
    )
    assert not hasattr(
        GovernanceInterventionExecutionResultBuilder,
        "rollback",
    )
    assert not hasattr(
        GovernanceInterventionExecutionResultBuilder,
        "verify_outcome",
    )