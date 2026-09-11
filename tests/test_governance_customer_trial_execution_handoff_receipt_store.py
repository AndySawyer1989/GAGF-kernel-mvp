from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest

from backend.app.gagf.governance_customer_trial_execution_handoff_receipt_store import (
    CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_TABLE,
    CustomerTrialExecutionHandoffReceiptConflictError,
    CustomerTrialExecutionHandoffReceiptIntegrityError,
    GovernanceCustomerTrialExecutionHandoffReceiptStore,
)
from tests.test_governance_customer_trial_execution_handoff_bridge import (
    StubAssessmentExecutionRequest,
    build_authorization,
    build_contract_event,
    build_services,
    record_ready_preflight,
)


def build_bridge_result(
    tmp_path,
):
    service, bridge = build_services(
        tmp_path
    )

    record_ready_preflight(
        service
    )

    result = bridge.prepare_handoff(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
        contract_execution_event=(
            build_contract_event()
        ),
        paid_work_authorization=(
            build_authorization()
        ),
        assessment_execution_request=(
            StubAssessmentExecutionRequest()
        ),
    )

    return result


def build_store(
    tmp_path,
):
    return (
        GovernanceCustomerTrialExecutionHandoffReceiptStore(
            tmp_path
            / "customer-trial-handoff.sqlite3"
        )
    )


def test_persists_full_preflight_to_handoff_lineage(
    tmp_path,
):
    result = build_bridge_result(
        tmp_path
    )

    store = build_store(
        tmp_path
    )

    receipt = store.put(
        bridge_result=result
    )

    assert (
        receipt.preflight_receipt_hash
        == result.preflight_receipt_hash
    )

    assert (
        receipt.preflight_decision_payload_hash
        == result.preflight_decision_payload_hash
    )

    assert (
        receipt.preflight_package_hash
        == result.preflight_package_hash
    )

    assert (
        receipt.contract_execution_event_hash
        == (
            result.handoff
            .contract_execution_event_hash
        )
    )

    assert (
        receipt.paid_work_authorization_hash
        == (
            result.handoff
            .paid_work_authorization_hash
        )
    )

    assert (
        receipt.assessment_execution_request_hash
        == (
            result.handoff
            .assessment_execution_request_hash
        )
    )

    assert (
        receipt.handoff_hash
        == result.handoff.handoff_hash
    )

    assert len(
        receipt.lineage_hash
    ) == 64

    assert len(
        receipt.receipt_hash
    ) == 64


def test_identical_write_is_idempotent(
    tmp_path,
):
    result = build_bridge_result(
        tmp_path
    )

    store = build_store(
        tmp_path
    )

    first = store.put(
        bridge_result=result
    )

    second = store.put(
        bridge_result=result
    )

    assert (
        second.receipt_hash
        == first.receipt_hash
    )

    assert (
        second.lineage_hash
        == first.lineage_hash
    )


def test_restart_readback_restores_exact_receipt(
    tmp_path,
):
    result = build_bridge_result(
        tmp_path
    )

    database_path = (
        tmp_path
        / "customer-trial-handoff.sqlite3"
    )

    first_store = (
        GovernanceCustomerTrialExecutionHandoffReceiptStore(
            database_path
        )
    )

    written = first_store.put(
        bridge_result=result
    )

    second_store = (
        GovernanceCustomerTrialExecutionHandoffReceiptStore(
            database_path
        )
    )

    restored = second_store.get(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
    )

    assert restored is not None

    assert (
        restored.receipt_hash
        == written.receipt_hash
    )

    assert (
        restored.lineage_hash
        == written.lineage_hash
    )


def test_conflicting_lineage_for_same_hierarchy_is_rejected(
    tmp_path,
):
    result = build_bridge_result(
        tmp_path
    )

    store = build_store(
        tmp_path
    )

    store.put(
        bridge_result=result
    )

    changed_handoff = replace(
        result.handoff,
        handoff_hash="f" * 64,
    )

    changed_result = replace(
        result,
        handoff=changed_handoff,
    )

    with pytest.raises(
        CustomerTrialExecutionHandoffReceiptConflictError,
        match="does not match",
    ):
        store.put(
            bridge_result=changed_result
        )


def test_tampered_handoff_hash_fails_closed(
    tmp_path,
):
    result = build_bridge_result(
        tmp_path
    )

    store = build_store(
        tmp_path
    )

    store.put(
        bridge_result=result
    )

    with sqlite3.connect(
        store.database_path
    ) as connection:
        connection.execute(
            f"""
            UPDATE
                {CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_TABLE}
            SET
                handoff_hash = ?
            WHERE hierarchy_key = ?
            """,
            (
                "tampered-handoff-hash",
                result.hierarchy_key,
            ),
        )

    with pytest.raises(
        CustomerTrialExecutionHandoffReceiptIntegrityError,
        match="lineage hash verification failed",
    ):
        store.get(
            tenant_id="tenant-alpha",
            client_id="client-customer-001",
            engagement_id="engagement-trial-001",
            assessment_id="assessment-trial-001",
        )


def test_tampered_receipt_hash_fails_closed(
    tmp_path,
):
    result = build_bridge_result(
        tmp_path
    )

    store = build_store(
        tmp_path
    )

    store.put(
        bridge_result=result
    )

    with sqlite3.connect(
        store.database_path
    ) as connection:
        connection.execute(
            f"""
            UPDATE
                {CUSTOMER_TRIAL_EXECUTION_HANDOFF_RECEIPT_TABLE}
            SET
                receipt_hash = ?
            WHERE hierarchy_key = ?
            """,
            (
                "tampered-receipt-hash",
                result.hierarchy_key,
            ),
        )

    with pytest.raises(
        CustomerTrialExecutionHandoffReceiptIntegrityError,
        match="receipt hash verification failed",
    ):
        store.get(
            tenant_id="tenant-alpha",
            client_id="client-customer-001",
            engagement_id="engagement-trial-001",
            assessment_id="assessment-trial-001",
        )


def test_missing_receipt_returns_none(
    tmp_path,
):
    store = build_store(
        tmp_path
    )

    result = store.get(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
    )

    assert result is None


def test_receipt_remains_non_authoritative(
    tmp_path,
):
    result = build_bridge_result(
        tmp_path
    )

    store = build_store(
        tmp_path
    )

    payload = store.put(
        bridge_result=result
    ).to_dict()

    boundaries = payload[
        "boundaries"
    ]

    assert (
        boundaries[
            "receipt_is_audit_evidence_only"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_execution_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_paid_work_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_assessment_execution"
        ]
        is True
    )

    assert (
        boundaries[
            "receipt_is_not_intervention_authority"
        ]
        is True
    )