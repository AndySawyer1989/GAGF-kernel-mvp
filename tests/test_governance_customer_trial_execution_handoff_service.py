from __future__ import annotations

import pytest

from backend.app.gagf.governance_customer_trial_execution_handoff_receipt_store import (
    CustomerTrialExecutionHandoffReceiptConflictError,
    GovernanceCustomerTrialExecutionHandoffReceiptStore,
)
from backend.app.gagf.governance_customer_trial_execution_handoff_service import (
    GovernanceCustomerTrialExecutionHandoffService,
)
from tests.test_governance_customer_trial_execution_handoff_bridge import (
    StubAssessmentExecutionRequest,
    build_authorization,
    build_contract_event,
    build_services,
    record_ready_preflight,
)


def build_handoff_service(
    tmp_path,
):
    preflight_service, bridge = (
        build_services(
            tmp_path
        )
    )

    receipt_store = (
        GovernanceCustomerTrialExecutionHandoffReceiptStore(
            tmp_path
            / "customer-trial-handoff-service.sqlite3"
        )
    )

    service = (
        GovernanceCustomerTrialExecutionHandoffService(
            bridge=bridge,
            receipt_store=receipt_store,
        )
    )

    return (
        preflight_service,
        service,
    )


def prepare(
    service,
    *,
    event=None,
    authorization=None,
    request=None,
):
    return service.prepare(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
        contract_execution_event=(
            event
            if event is not None
            else build_contract_event()
        ),
        paid_work_authorization=(
            authorization
            if authorization is not None
            else build_authorization()
        ),
        assessment_execution_request=(
            request
            if request is not None
            else StubAssessmentExecutionRequest()
        ),
    )


def test_prepare_builds_and_persists_handoff(
    tmp_path,
):
    preflight_service, service = (
        build_handoff_service(
            tmp_path
        )
    )

    record_ready_preflight(
        preflight_service
    )

    result = prepare(
        service
    )

    assert (
        result.bridge_result.handoff.status.value
        == "ready_for_assessment_execution"
    )

    assert (
        result.receipt.handoff_hash
        == result.bridge_result.handoff.handoff_hash
    )

    status = service.status(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
    )

    assert status.receipt_found is True
    assert status.receipt is not None

    assert (
        status.receipt.receipt_hash
        == result.receipt.receipt_hash
    )


def test_prepare_requires_existing_preflight(
    tmp_path,
):
    _, service = build_handoff_service(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="persisted preflight receipt",
    ):
        prepare(
            service
        )


def test_identical_prepare_is_idempotent(
    tmp_path,
):
    preflight_service, service = (
        build_handoff_service(
            tmp_path
        )
    )

    record_ready_preflight(
        preflight_service
    )

    first = prepare(
        service
    )

    second = prepare(
        service
    )

    assert (
        second.receipt.receipt_hash
        == first.receipt.receipt_hash
    )


def test_changed_handoff_lineage_is_rejected(
    tmp_path,
):
    preflight_service, service = (
        build_handoff_service(
            tmp_path
        )
    )

    record_ready_preflight(
        preflight_service
    )

    prepare(
        service
    )

    changed_event = (
        build_contract_event()
    )

    changed_event[
        "recorded_at"
    ] = "2026-09-11T04:00:00+00:00"

    with pytest.raises(
        CustomerTrialExecutionHandoffReceiptConflictError,
        match="does not match",
    ):
        prepare(
            service,
            event=changed_event,
        )


def test_missing_status_is_read_only_and_empty(
    tmp_path,
):
    _, service = build_handoff_service(
        tmp_path
    )

    status = service.status(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
    )

    assert status.receipt_found is False
    assert status.receipt is None

    payload = status.to_dict()

    assert (
        payload["boundaries"][
            "status_is_read_only"
        ]
        is True
    )

    assert (
        payload["boundaries"][
            "status_is_not_execution_authority"
        ]
        is True
    )


def test_prepare_preserves_non_authority_boundary(
    tmp_path,
):
    preflight_service, service = (
        build_handoff_service(
            tmp_path
        )
    )

    record_ready_preflight(
        preflight_service
    )

    payload = prepare(
        service
    ).to_dict()

    boundaries = payload[
        "boundaries"
    ]

    assert (
        boundaries[
            "service_is_not_execution_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "service_is_not_paid_work_authority"
        ]
        is True
    )

    assert (
        boundaries[
            "service_does_not_execute_assessment"
        ]
        is True
    )

    assert (
        boundaries[
            "service_does_not_authorize_intervention"
        ]
        is True
    )


def test_status_survives_service_reconstruction(
    tmp_path,
):
    preflight_service, first_service = (
        build_handoff_service(
            tmp_path
        )
    )

    record_ready_preflight(
        preflight_service
    )

    prepared = prepare(
        first_service
    )

    _, second_service = (
        build_handoff_service(
            tmp_path
        )
    )

    restored = second_service.status(
        tenant_id="tenant-alpha",
        client_id="client-customer-001",
        engagement_id="engagement-trial-001",
        assessment_id="assessment-trial-001",
    )

    assert restored.receipt_found is True
    assert restored.receipt is not None

    assert (
        restored.receipt.receipt_hash
        == prepared.receipt.receipt_hash
    )