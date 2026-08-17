from __future__ import annotations

from dataclasses import replace

import pytest

from backend.app.gagf.governance_intervention_reverification_request import (
    GovernanceInterventionReverificationRequest,
)
from backend.app.gagf.governance_intervention_reverification_request_ledger import (
    GovernanceInterventionReverificationRequestLedger,
    GovernanceInterventionReverificationRequestLedgerEntry,
)
from backend.app.gagf.governance_intervention_reverification_work_order import (
    GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_ID,
    GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_VERSION,
    GovernanceInterventionReverificationWorkOrderBuilder,
    GovernanceInterventionReverificationWorkOrderError,
    GovernanceInterventionReverificationWorkOrderIntegrityError,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


def make_request(
    *,
    tenant_id: str = "tenant-a",
    intervention_id: str = "intervention-1",
    verification_record_hash: str = "record-1",
    lifecycle_event_hash: str = "lifecycle-event-1",
    freshness_evaluation_hash: str = "freshness-1",
    reverification_scope: str = "POLICY",
    trigger_codes: tuple[str, ...] = (
        "POLICY_CHANGED",
    ),
) -> GovernanceInterventionReverificationRequest:
    payload = {
        "request_id": (
            "governance-intervention-reverification-request"
        ),
        "version": "0.1.0",
        "schema_version": "1.0.0",
        "tenant_id": tenant_id,
        "intervention_id": intervention_id,
        "verification_record_hash": (
            verification_record_hash
        ),
        "lifecycle_event_hash": (
            lifecycle_event_hash
        ),
        "freshness_evaluation_hash": (
            freshness_evaluation_hash
        ),
        "reverification_scope": (
            reverification_scope
        ),
        "trigger_codes": list(
            trigger_codes
        ),
    }

    return GovernanceInterventionReverificationRequest(
        request_id=payload["request_id"],
        version=payload["version"],
        schema_version=payload["schema_version"],
        tenant_id=payload["tenant_id"],
        intervention_id=payload["intervention_id"],
        verification_record_hash=payload[
            "verification_record_hash"
        ],
        lifecycle_event_hash=payload[
            "lifecycle_event_hash"
        ],
        freshness_evaluation_hash=payload[
            "freshness_evaluation_hash"
        ],
        reverification_scope=payload[
            "reverification_scope"
        ],
        trigger_codes=trigger_codes,
        request_hash=sha256_hex(
            canonical_json(payload)
        ),
    )


def persist_request(
    database_path,
    *,
    request=None,
):
    if request is None:
        request = make_request()

    ledger = GovernanceInterventionReverificationRequestLedger(
        database_path
    )

    entry = ledger.append(
        request=request
    )

    return ledger, request, entry


def build_work_order(
    *,
    request,
    ledger_entry,
    attempt_id: str = "attempt-1",
):
    return GovernanceInterventionReverificationWorkOrderBuilder.build(
        request=request,
        ledger_entry=ledger_entry,
        attempt_id=attempt_id,
    )


def test_work_order_constants_are_stable():
    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_ID
        == "governance-intervention-reverification-work-order"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_VERSION
        == "0.1.0"
    )

    assert (
        GOVERNANCE_INTERVENTION_REVERIFICATION_WORK_ORDER_SCHEMA_VERSION
        == "1.0.0"
    )


def test_valid_persisted_request_builds_work_order(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    work_order = build_work_order(
        request=request,
        ledger_entry=entry,
    )

    assert work_order.tenant_id == "tenant-a"
    assert work_order.intervention_id == "intervention-1"

    assert (
        work_order.verification_record_hash
        == "record-1"
    )

    assert (
        work_order.request_hash
        == request.request_hash
    )

    assert (
        work_order.request_ledger_chain_hash
        == entry.chain_hash
    )

    assert work_order.attempt_id == "attempt-1"
    assert work_order.reverification_scope == "POLICY"

    assert work_order.trigger_codes == (
        "POLICY_CHANGED",
    )

    assert work_order.verify() is True


def test_same_inputs_produce_same_work_order(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    first = build_work_order(
        request=request,
        ledger_entry=entry,
    )

    second = build_work_order(
        request=request,
        ledger_entry=entry,
    )

    assert first == second
    assert (
        first.work_order_hash
        == second.work_order_hash
    )


def test_different_attempt_id_changes_work_order_hash(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    first = build_work_order(
        request=request,
        ledger_entry=entry,
        attempt_id="attempt-1",
    )

    second = build_work_order(
        request=request,
        ledger_entry=entry,
        attempt_id="attempt-2",
    )

    assert (
        first.work_order_hash
        != second.work_order_hash
    )


def test_blank_attempt_id_is_rejected(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderError,
        match="attempt_id is required",
    ):
        build_work_order(
            request=request,
            ledger_entry=entry,
            attempt_id="",
        )


def test_whitespace_attempt_id_is_rejected(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderError,
        match="attempt_id is required",
    ):
        build_work_order(
            request=request,
            ledger_entry=entry,
            attempt_id="   ",
        )


def test_noncanonical_attempt_id_is_rejected(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderError,
        match="must already be canonical",
    ):
        build_work_order(
            request=request,
            ledger_entry=entry,
            attempt_id=" attempt-1 ",
        )


def test_tampered_request_is_rejected(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    tampered = replace(
        request,
        reverification_scope="FULL",
    )

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderIntegrityError,
        match="request failed deterministic verification",
    ):
        build_work_order(
            request=tampered,
            ledger_entry=entry,
        )


def test_tampered_ledger_chain_hash_is_rejected(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    tampered = replace(
        entry,
        chain_hash="f" * 64,
    )

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderIntegrityError,
        match="failed chain verification",
    ):
        build_work_order(
            request=request,
            ledger_entry=tampered,
        )


def test_cross_tenant_ledger_binding_is_rejected(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    payload = entry.chain_payload()
    payload["tenant_id"] = "tenant-b"

    tampered = GovernanceInterventionReverificationRequestLedgerEntry(
        tenant_id="tenant-b",
        sequence_number=entry.sequence_number,
        request_hash=entry.request_hash,
        verification_record_hash=(
            entry.verification_record_hash
        ),
        previous_chain_hash=(
            entry.previous_chain_hash
        ),
        chain_hash=sha256_hex(
            canonical_json(payload)
        ),
        ledger_schema_version=(
            entry.ledger_schema_version
        ),
    )

    assert tampered.verify_chain_hash() is True

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderIntegrityError,
        match="tenant does not match",
    ):
        build_work_order(
            request=request,
            ledger_entry=tampered,
        )


def test_wrong_request_hash_binding_is_rejected(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    payload = entry.chain_payload()
    payload["request_hash"] = "wrong-request"

    tampered = GovernanceInterventionReverificationRequestLedgerEntry(
        tenant_id=entry.tenant_id,
        sequence_number=entry.sequence_number,
        request_hash="wrong-request",
        verification_record_hash=(
            entry.verification_record_hash
        ),
        previous_chain_hash=(
            entry.previous_chain_hash
        ),
        chain_hash=sha256_hex(
            canonical_json(payload)
        ),
        ledger_schema_version=(
            entry.ledger_schema_version
        ),
    )

    assert tampered.verify_chain_hash() is True

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderIntegrityError,
        match="not bound to request",
    ):
        build_work_order(
            request=request,
            ledger_entry=tampered,
        )


def test_wrong_record_binding_is_rejected(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    payload = entry.chain_payload()
    payload["verification_record_hash"] = "other-record"

    tampered = GovernanceInterventionReverificationRequestLedgerEntry(
        tenant_id=entry.tenant_id,
        sequence_number=entry.sequence_number,
        request_hash=entry.request_hash,
        verification_record_hash="other-record",
        previous_chain_hash=(
            entry.previous_chain_hash
        ),
        chain_hash=sha256_hex(
            canonical_json(payload)
        ),
        ledger_schema_version=(
            entry.ledger_schema_version
        ),
    )

    assert tampered.verify_chain_hash() is True

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderIntegrityError,
        match="verification record does not match",
    ):
        build_work_order(
            request=request,
            ledger_entry=tampered,
        )


def test_unsupported_scope_is_rejected(
    tmp_path,
):
    request = make_request(
        reverification_scope="UNKNOWN",
    )

    assert request.verify() is True

    _, persisted_request, entry = persist_request(
        tmp_path / "requests.db",
        request=request,
    )

    assert persisted_request == request
    assert entry.request_hash == request.request_hash

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderIntegrityError,
        match="unsupported reverification scope",
    ):
        build_work_order(
            request=request,
            ledger_entry=entry,
        )


def test_request_without_triggers_is_rejected(
    tmp_path,
):
    request = make_request(
        trigger_codes=(),
    )

    assert request.verify() is True

    _, persisted_request, entry = persist_request(
        tmp_path / "requests.db",
        request=request,
    )

    assert persisted_request == request
    assert entry.request_hash == request.request_hash

    with pytest.raises(
        GovernanceInterventionReverificationWorkOrderIntegrityError,
        match="at least one trigger",
    ):
        build_work_order(
            request=request,
            ledger_entry=entry,
        )


def test_work_order_hash_detects_tampering(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    work_order = build_work_order(
        request=request,
        ledger_entry=entry,
    )

    tampered = replace(
        work_order,
        attempt_id="attempt-2",
    )

    assert work_order.verify() is True
    assert tampered.verify() is False


def test_work_order_preserves_request_scope_and_triggers(
    tmp_path,
):
    request = make_request(
        reverification_scope="REQUIREMENTS",
        trigger_codes=(
            "POLICY_CHANGED",
            "REQUIREMENTS_CHANGED",
        ),
    )

    _, request, entry = persist_request(
        tmp_path / "requests.db",
        request=request,
    )

    work_order = build_work_order(
        request=request,
        ledger_entry=entry,
    )

    assert (
        work_order.reverification_scope
        == "REQUIREMENTS"
    )

    assert work_order.trigger_codes == (
        "POLICY_CHANGED",
        "REQUIREMENTS_CHANGED",
    )


def test_work_order_contains_no_execution_or_completion_claims(
    tmp_path,
):
    _, request, entry = persist_request(
        tmp_path / "requests.db"
    )

    work_order = build_work_order(
        request=request,
        ledger_entry=entry,
    )

    payload = work_order.to_dict()

    forbidden = {
        "executed",
        "execution_status",
        "started",
        "completed",
        "reverified",
        "reverification_completed",
        "verification_disposition",
        "measurement",
        "observation",
        "success",
        "failure",
        "causation",
        "causal_effect",
        "authorized",
        "rollback",
        "continue_intervention",
        "next_action",
    }

    assert forbidden.isdisjoint(payload)


def test_work_order_builder_has_no_execution_methods():
    actual_methods = {
        name
        for name in dir(
            GovernanceInterventionReverificationWorkOrderBuilder
        )
        if not name.startswith("_")
    }

    forbidden_methods = {
        "execute",
        "start",
        "complete",
        "reverify",
        "measure",
        "observe",
        "verify_outcome",
        "authorize",
        "actuate",
        "rollback",
        "supersede",
    }

    assert forbidden_methods.isdisjoint(
        actual_methods
    )