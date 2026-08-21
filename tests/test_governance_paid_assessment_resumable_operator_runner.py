from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    canonical_json,
    sha256_text,
)

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    GovernedPaidAssessmentClientAcknowledgment,
)
from backend.app.gagf.governance_paid_assessment_client_response import (
    GovernedPaidAssessmentClientResponse,
)
from backend.app.gagf.governance_paid_assessment_closeout import (
    PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    PaidAssessmentCloseoutRequest,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernedPaidAssessmentDeliveryEvent,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
    CLIENT_RESPONSE_ARTIFACT_TYPE,
    DELIVERY_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_paid_assessment_operator_workflow import (
    ACTION_CONFIRM_ADMINISTRATIVE_CLOSEOUT,
    ACTION_NONE,
    ACTION_RECORD_CLIENT_RECEIPT,
    ACTION_RECORD_CLIENT_RESPONSE,
    ACTION_RECORD_DELIVERY_EVENT,
    WORKFLOW_STAGE_AWAITING_CLIENT_RECEIPT,
    WORKFLOW_STAGE_AWAITING_CLIENT_RESPONSE,
    WORKFLOW_STAGE_AWAITING_DELIVERY,
    WORKFLOW_STAGE_CLOSED,
    WORKFLOW_STAGE_READY_FOR_CLOSEOUT,
)
from backend.app.gagf.governance_paid_assessment_resumable_operator_runner import (
    ACTION_RESULT_ALREADY_DURABLE,
    ACTION_RESULT_EXECUTED,
    GovernancePaidAssessmentResumableOperatorRunner,
    PaidAssessmentOperatorActionConflictError,
    PaidAssessmentOperatorActionNotAllowedError,
)


HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64
HEX_E = "e" * 64
HEX_F = "f" * 64


def build_context() -> CommercialHierarchyContext:
    return CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )


@pytest.fixture
def repository(tmp_path) -> GovernanceAssessmentRepository:
    repo = GovernanceAssessmentRepository(
        tmp_path / "paid-assessment.sqlite"
    )

    repo.create_assessment(
        context=build_context(),
        assessment_name="Paid Governance Assessment",
        status="completed",
    )

    return repo


@pytest.fixture
def runner(
    repository: GovernanceAssessmentRepository,
) -> GovernancePaidAssessmentResumableOperatorRunner:
    return GovernancePaidAssessmentResumableOperatorRunner(
        repository=repository
    )


def build_governed_with_computed_hash(
    *,
    governed_type,
    values,
    hash_field,
):
    working = dict(values)

    # Supply a syntactically valid provisional hash so the frozen governed
    # dataclass can be constructed and serialize its canonical full payload.
    working[hash_field] = "0" * 64

    provisional = governed_type(**working)
    payload = provisional.to_dict()

    claimed = payload.pop(hash_field, None)

    if claimed is None:
        raise AssertionError(
            f"governed fixture payload missing {hash_field}"
        )

    working[hash_field] = sha256_text(
        canonical_json(payload)
    )

    return governed_type(**working)

def build_delivery_event(
    **overrides,
) -> GovernedPaidAssessmentDeliveryEvent:
    values = {
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "report_id": "report-001",
        "delivery_envelope_hash": HEX_A,
        "delivery_approval_hash": HEX_B,
        "human_delivery_confirmation_hash": HEX_C,
        "delivery_event_id": "delivery-event-001",
        "delivered_by": "FIP Operator",
        "delivered_at": "2026-08-18T19:15:00+00:00",
        "delivery_method": "email",
        "delivery_reference": "mail-message-001",
        "delivery_status": "delivered",
        "delivery_event_hash": HEX_D,
    }
    values.update(overrides)

    return build_governed_with_computed_hash(
        governed_type=GovernedPaidAssessmentDeliveryEvent,
        values=values,
        hash_field="delivery_event_hash",
    )


def build_acknowledgment(
    delivery_event: GovernedPaidAssessmentDeliveryEvent | None = None,
    **overrides,
) -> GovernedPaidAssessmentClientAcknowledgment:
    delivery_event = delivery_event or build_delivery_event()

    values = {
        "tenant_id": delivery_event.tenant_id,
        "client_id": delivery_event.client_id,
        "engagement_id": delivery_event.engagement_id,
        "assessment_id": delivery_event.assessment_id,
        "report_id": delivery_event.report_id,
        "delivery_event_id": delivery_event.delivery_event_id,
        "delivery_event_hash": delivery_event.delivery_event_hash,
        "acknowledgment_id": "client-ack-001",
        "acknowledgment_evidence_hash": HEX_E,
        "acknowledged_by": "ACME Client Representative",
        "acknowledged_at": "2026-08-18T19:30:00+00:00",
        "acknowledgment_method": "email_reply",
        "acknowledgment_reference": "mail-reply-001",
        "acknowledgment_status": "client_receipt_acknowledged",
        "acknowledgment_hash": HEX_F,
    }
    values.update(overrides)

    return build_governed_with_computed_hash(
        governed_type=GovernedPaidAssessmentClientAcknowledgment,
        values=values,
        hash_field="acknowledgment_hash",
    )


def build_response(
    acknowledgment: GovernedPaidAssessmentClientAcknowledgment | None = None,
    **overrides,
) -> GovernedPaidAssessmentClientResponse:
    acknowledgment = acknowledgment or build_acknowledgment()

    values = {
        "tenant_id": acknowledgment.tenant_id,
        "client_id": acknowledgment.client_id,
        "engagement_id": acknowledgment.engagement_id,
        "assessment_id": acknowledgment.assessment_id,
        "report_id": acknowledgment.report_id,
        "acknowledgment_id": acknowledgment.acknowledgment_id,
        "acknowledgment_hash": acknowledgment.acknowledgment_hash,
        "response_id": "client-response-001",
        "response_evidence_hash": HEX_A,
        "responded_by": "ACME Client Representative",
        "responded_at": "2026-08-18T20:00:00+00:00",
        "response_method": "email_reply",
        "response_reference": "assessment-response-001",
        "findings_disposition": "acknowledged",
        "recommendations_disposition": "accepted",
        "response_note": "Accepted for planning review.",
        "response_status": "client_response_recorded",
        "response_hash": HEX_B,
    }
    values.update(overrides)

    return build_governed_with_computed_hash(
        governed_type=GovernedPaidAssessmentClientResponse,
        values=values,
        hash_field="response_hash",
    )


def establish_through_response(
    runner: GovernancePaidAssessmentResumableOperatorRunner,
):
    delivery = build_delivery_event()

    delivery_result = runner.record_delivery(
        delivery_event=delivery,
        created_at=datetime(
            2026, 8, 18, 19, 15, tzinfo=timezone.utc
        ),
    )

    acknowledgment = build_acknowledgment(delivery)

    acknowledgment_result = runner.record_client_receipt(
        client_acknowledgment=acknowledgment,
        created_at=datetime(
            2026, 8, 18, 19, 30, tzinfo=timezone.utc
        ),
    )

    response = build_response(acknowledgment)

    response_result = runner.record_client_response(
        client_response=response,
        created_at=datetime(
            2026, 8, 18, 20, 0, tzinfo=timezone.utc
        ),
    )

    return (
        delivery,
        acknowledgment,
        response,
        delivery_result,
        acknowledgment_result,
        response_result,
    )


def test_records_delivery_and_advances_operator_state(
    repository,
    runner,
):
    before = repository.list_artifacts(
        context=build_context()
    )

    result = runner.record_delivery(
        delivery_event=build_delivery_event(),
    )

    after = repository.list_artifacts(
        context=build_context()
    )

    assert len(before) == 0
    assert len(after) == 1

    assert result.disposition == ACTION_RESULT_EXECUTED
    assert result.artifact_type == DELIVERY_ARTIFACT_TYPE
    assert result.workflow_stage_after == (
        WORKFLOW_STAGE_AWAITING_CLIENT_RECEIPT
    )
    assert result.required_operator_action_after == (
        ACTION_RECORD_CLIENT_RECEIPT
    )
    assert result.repository_chain_valid is True

    assert repository.verify_chain(
        context=build_context()
    ) is True


def test_exact_delivery_retry_returns_already_durable_without_append(
    repository,
    runner,
):
    delivery = build_delivery_event()

    first = runner.record_delivery(
        delivery_event=delivery
    )

    before_retry = repository.list_artifacts(
        context=build_context()
    )

    retry = runner.record_delivery(
        delivery_event=delivery
    )

    after_retry = repository.list_artifacts(
        context=build_context()
    )

    assert first.disposition == ACTION_RESULT_EXECUTED
    assert retry.disposition == ACTION_RESULT_ALREADY_DURABLE

    assert retry.artifact_id == first.artifact_id
    assert retry.artifact_hash == first.artifact_hash
    assert retry.sequence_number == first.sequence_number
    assert retry.chain_hash == first.chain_hash

    assert before_retry == after_retry
    assert len(after_retry) == 1


def test_conflicting_delivery_retry_fails_closed_without_append(
    repository,
    runner,
):
    delivery = build_delivery_event()

    runner.record_delivery(
        delivery_event=delivery
    )

    before = repository.list_artifacts(
        context=build_context()
    )

    conflicting = build_delivery_event(
        delivery_event_id="delivery-event-conflict",
    )

    with pytest.raises(
        PaidAssessmentOperatorActionConflictError,
        match="different governed event identity/hash",
    ):
        runner.record_delivery(
            delivery_event=conflicting
        )

    after = repository.list_artifacts(
        context=build_context()
    )

    assert before == after
    assert len(after) == 1


def test_receipt_before_delivery_is_rejected_without_append(
    repository,
    runner,
):
    acknowledgment = build_acknowledgment()

    with pytest.raises(
        PaidAssessmentOperatorActionNotAllowedError,
        match="not allowed",
    ):
        runner.record_client_receipt(
            client_acknowledgment=acknowledgment
        )

    assert not repository.list_artifacts(
        context=build_context()
    )

    workflow = runner.get_workflow(
        context=build_context()
    )

    assert workflow.workflow_stage == (
        WORKFLOW_STAGE_AWAITING_DELIVERY
    )
    assert workflow.required_operator_action == (
        ACTION_RECORD_DELIVERY_EVENT
    )


def test_full_lifecycle_progression_is_durable_and_resumable(
    repository,
    runner,
):
    (
        delivery,
        acknowledgment,
        response,
        delivery_result,
        acknowledgment_result,
        response_result,
    ) = establish_through_response(runner)

    assert delivery_result.disposition == ACTION_RESULT_EXECUTED
    assert acknowledgment_result.disposition == ACTION_RESULT_EXECUTED
    assert response_result.disposition == ACTION_RESULT_EXECUTED

    assert delivery_result.workflow_stage_after == (
        WORKFLOW_STAGE_AWAITING_CLIENT_RECEIPT
    )
    assert acknowledgment_result.workflow_stage_after == (
        WORKFLOW_STAGE_AWAITING_CLIENT_RESPONSE
    )
    assert response_result.workflow_stage_after == (
        WORKFLOW_STAGE_READY_FOR_CLOSEOUT
    )

    assert delivery_result.required_operator_action_after == (
        ACTION_RECORD_CLIENT_RECEIPT
    )
    assert acknowledgment_result.required_operator_action_after == (
        ACTION_RECORD_CLIENT_RESPONSE
    )
    assert response_result.required_operator_action_after == (
        ACTION_CONFIRM_ADMINISTRATIVE_CLOSEOUT
    )

    artifacts = repository.list_artifacts(
        context=build_context()
    )

    assert [item.artifact_type for item in artifacts] == [
        DELIVERY_ARTIFACT_TYPE,
        ACKNOWLEDGMENT_ARTIFACT_TYPE,
        CLIENT_RESPONSE_ARTIFACT_TYPE,
    ]

    assert [item.sequence_number for item in artifacts] == [
        1,
        2,
        3,
    ]

    assert repository.verify_chain(
        context=build_context()
    ) is True

    delivery_retry = runner.record_delivery(
        delivery_event=delivery
    )
    acknowledgment_retry = runner.record_client_receipt(
        client_acknowledgment=acknowledgment
    )
    response_retry = runner.record_client_response(
        client_response=response
    )

    assert delivery_retry.disposition == (
        ACTION_RESULT_ALREADY_DURABLE
    )
    assert acknowledgment_retry.disposition == (
        ACTION_RESULT_ALREADY_DURABLE
    )
    assert response_retry.disposition == (
        ACTION_RESULT_ALREADY_DURABLE
    )

    artifacts_after_retries = repository.list_artifacts(
        context=build_context()
    )

    assert artifacts_after_retries == artifacts


def test_conflicting_acknowledgment_retry_fails_closed(
    repository,
    runner,
):
    delivery = build_delivery_event()
    runner.record_delivery(delivery_event=delivery)

    acknowledgment = build_acknowledgment(delivery)

    runner.record_client_receipt(
        client_acknowledgment=acknowledgment
    )

    before = repository.list_artifacts(
        context=build_context()
    )

    conflicting = build_acknowledgment(
        delivery,
        acknowledgment_id="client-ack-conflict",
    )

    with pytest.raises(
        PaidAssessmentOperatorActionConflictError,
        match="different governed event identity/hash",
    ):
        runner.record_client_receipt(
            client_acknowledgment=conflicting
        )

    assert repository.list_artifacts(
        context=build_context()
    ) == before


def test_conflicting_response_retry_fails_closed(
    repository,
    runner,
):
    delivery = build_delivery_event()
    runner.record_delivery(delivery_event=delivery)

    acknowledgment = build_acknowledgment(delivery)
    runner.record_client_receipt(
        client_acknowledgment=acknowledgment
    )

    response = build_response(acknowledgment)
    runner.record_client_response(
        client_response=response
    )

    before = repository.list_artifacts(
        context=build_context()
    )

    conflicting = build_response(
        acknowledgment,
        response_id="client-response-conflict",
    )

    with pytest.raises(
        PaidAssessmentOperatorActionConflictError,
        match="different governed event identity/hash",
    ):
        runner.record_client_response(
            client_response=conflicting
        )

    assert repository.list_artifacts(
        context=build_context()
    ) == before


def test_closeout_executes_then_exact_retry_reconciles(
    repository,
    runner,
):
    establish_through_response(runner)

    request = PaidAssessmentCloseoutRequest(
        context=build_context(),
        report_id="report-001",
        closed_by="FIP Operator",
        closeout_reason=(
            "Assessment delivery, receipt, and client response "
            "have been recorded."
        ),
        administrative_closeout_confirmed=True,
    )

    first = runner.confirm_administrative_closeout(
        request=request,
        created_at=datetime(
            2026, 8, 18, 20, 30, tzinfo=timezone.utc
        ),
    )

    artifacts_after_first = repository.list_artifacts(
        context=build_context()
    )

    retry = runner.confirm_administrative_closeout(
        request=request
    )

    artifacts_after_retry = repository.list_artifacts(
        context=build_context()
    )

    assert first.disposition == ACTION_RESULT_EXECUTED
    assert retry.disposition == ACTION_RESULT_ALREADY_DURABLE

    assert first.artifact_type == (
        PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE
    )
    assert retry.artifact_id == first.artifact_id
    assert retry.artifact_hash == first.artifact_hash

    assert artifacts_after_retry == artifacts_after_first
    assert len(artifacts_after_retry) == 4

    workflow = runner.get_workflow(
        context=build_context()
    )

    assert workflow.workflow_stage == WORKFLOW_STAGE_CLOSED
    assert workflow.required_operator_action == ACTION_NONE
    assert workflow.allowed_operator_actions == ()
    assert workflow.assessment_closed is True

    assert repository.verify_chain(
        context=build_context()
    ) is True


def test_conflicting_closeout_retry_fails_closed(
    repository,
    runner,
):
    establish_through_response(runner)

    request = PaidAssessmentCloseoutRequest(
        context=build_context(),
        report_id="report-001",
        closed_by="FIP Operator",
        closeout_reason="Administrative paid-assessment closeout.",
        administrative_closeout_confirmed=True,
    )

    runner.confirm_administrative_closeout(
        request=request
    )

    before = repository.list_artifacts(
        context=build_context()
    )

    conflicting = PaidAssessmentCloseoutRequest(
        context=build_context(),
        report_id="report-001",
        closed_by="Different Operator",
        closeout_reason="Different closeout evidence.",
        administrative_closeout_confirmed=True,
    )

    with pytest.raises(
        PaidAssessmentOperatorActionConflictError,
        match="different request evidence",
    ):
        runner.confirm_administrative_closeout(
            request=conflicting
        )

    after = repository.list_artifacts(
        context=build_context()
    )

    assert after == before


def test_runner_result_does_not_create_downstream_authority(
    runner,
):
    result = runner.record_delivery(
        delivery_event=build_delivery_event()
    )

    payload = result.to_dict()

    assert payload["boundaries"][
        "operator_command_is_not_event_authority"
    ] is True
    assert payload["boundaries"][
        "runner_is_not_a_second_workflow_ledger"
    ] is True
    assert payload["boundaries"][
        "retry_is_not_a_duplicate_business_event"
    ] is True

    assert "intervention_requested" not in payload
    assert "intervention_authorized" not in payload
    assert "intervention_executed" not in payload
    assert "causal_success" not in payload
    assert "roi_verified" not in payload
    assert "customer_outcome_verified" not in payload

def test_delivery_retry_with_same_identity_hash_but_changed_payload_fails_closed(
    repository,
    runner,
):
    delivery = build_delivery_event()

    runner.record_delivery(
        delivery_event=delivery
    )

    before = repository.list_artifacts(
        context=build_context()
    )

    forged = replace(
        delivery,
        delivered_by="Different Operator",
    )

    with pytest.raises(Exception):
        runner.record_delivery(
            delivery_event=forged
        )

    assert repository.list_artifacts(
        context=build_context()
    ) == before


def test_acknowledgment_retry_with_same_identity_hash_but_changed_payload_fails_closed(
    repository,
    runner,
):
    delivery = build_delivery_event()
    runner.record_delivery(
        delivery_event=delivery
    )

    acknowledgment = build_acknowledgment(delivery)
    runner.record_client_receipt(
        client_acknowledgment=acknowledgment
    )

    before = repository.list_artifacts(
        context=build_context()
    )

    forged = replace(
        acknowledgment,
        acknowledged_by="Different Client Representative",
    )

    with pytest.raises(Exception):
        runner.record_client_receipt(
            client_acknowledgment=forged
        )

    assert repository.list_artifacts(
        context=build_context()
    ) == before


def test_response_retry_with_same_identity_hash_but_changed_payload_fails_closed(
    repository,
    runner,
):
    delivery = build_delivery_event()
    runner.record_delivery(
        delivery_event=delivery
    )

    acknowledgment = build_acknowledgment(delivery)
    runner.record_client_receipt(
        client_acknowledgment=acknowledgment
    )

    response = build_response(acknowledgment)
    runner.record_client_response(
        client_response=response
    )

    before = repository.list_artifacts(
        context=build_context()
    )

    forged = replace(
        response,
        responded_by="Different Client Representative",
    )

    with pytest.raises(Exception):
        runner.record_client_response(
            client_response=forged
        )

    assert repository.list_artifacts(
        context=build_context()
    ) == before