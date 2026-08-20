from datetime import datetime, timezone

import pytest

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
    GovernancePaidAssessmentCloseoutService,
    PaidAssessmentCloseoutRequest,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernedPaidAssessmentDeliveryEvent,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    GovernancePaidAssessmentLifecyclePersistenceService,
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
    GovernancePaidAssessmentOperatorWorkflowService,
)


HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
HEX_D = "d" * 64
HEX_E = "e" * 64
HEX_F = "f" * 64


def build_context():
    return CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )


@pytest.fixture
def repository(tmp_path):
    repo = GovernanceAssessmentRepository(
        tmp_path / "paid-assessment-operator-workflow.sqlite"
    )
    repo.create_assessment(
        context=build_context(),
        assessment_name="Paid Governance Assessment",
        status="completed",
    )
    return repo


def build_delivery():
    return GovernedPaidAssessmentDeliveryEvent(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        report_id="report-001",
        delivery_envelope_hash=HEX_A,
        delivery_approval_hash=HEX_B,
        human_delivery_confirmation_hash=HEX_C,
        delivery_event_id="delivery-event-001",
        delivered_by="FIP Operator",
        delivered_at="2026-08-18T19:15:00+00:00",
        delivery_method="email",
        delivery_reference="mail-message-001",
        delivery_status="delivered",
        delivery_event_hash=HEX_D,
    )


def build_acknowledgment(delivery):
    return GovernedPaidAssessmentClientAcknowledgment(
        tenant_id=delivery.tenant_id,
        client_id=delivery.client_id,
        engagement_id=delivery.engagement_id,
        assessment_id=delivery.assessment_id,
        report_id=delivery.report_id,
        delivery_event_id=delivery.delivery_event_id,
        delivery_event_hash=delivery.delivery_event_hash,
        acknowledgment_id="client-ack-001",
        acknowledgment_evidence_hash=HEX_E,
        acknowledged_by="ACME Client Representative",
        acknowledged_at="2026-08-18T19:30:00+00:00",
        acknowledgment_method="email_reply",
        acknowledgment_reference="mail-reply-001",
        acknowledgment_status="client_receipt_acknowledged",
        acknowledgment_hash=HEX_F,
    )


def build_response(acknowledgment):
    return GovernedPaidAssessmentClientResponse(
        tenant_id=acknowledgment.tenant_id,
        client_id=acknowledgment.client_id,
        engagement_id=acknowledgment.engagement_id,
        assessment_id=acknowledgment.assessment_id,
        report_id=acknowledgment.report_id,
        acknowledgment_id=acknowledgment.acknowledgment_id,
        acknowledgment_hash=acknowledgment.acknowledgment_hash,
        response_id="client-response-001",
        response_evidence_hash=HEX_A,
        responded_by="ACME Client Representative",
        responded_at="2026-08-18T20:00:00+00:00",
        response_method="email_reply",
        response_reference="assessment-response-001",
        findings_disposition="acknowledged",
        recommendations_disposition="accepted",
        response_note="Accepted for planning review.",
        response_status="client_response_recorded",
        response_hash=HEX_B,
    )


def workflow(repository):
    return GovernancePaidAssessmentOperatorWorkflowService(
        repository=repository
    )


def test_projects_awaiting_delivery(repository):
    before = repository.list_artifacts(context=build_context())

    state = workflow(repository).get_workflow(
        context=build_context()
    )

    after = repository.list_artifacts(context=build_context())

    assert state.workflow_stage == WORKFLOW_STAGE_AWAITING_DELIVERY
    assert state.required_operator_action == ACTION_RECORD_DELIVERY_EVENT
    assert state.allowed_operator_actions == (
        ACTION_RECORD_DELIVERY_EVENT,
    )
    assert state.assessment_closed is False
    assert state.report_id is None
    assert state.evidence_artifacts == ()
    assert before == after


def test_projects_awaiting_client_receipt(repository):
    delivery = build_delivery()

    GovernancePaidAssessmentLifecyclePersistenceService().persist_lifecycle(
        repository=repository,
        delivery_event=delivery,
        client_acknowledgment=build_acknowledgment(delivery),
        client_response=build_response(
            build_acknowledgment(delivery)
        ),
        created_at=datetime(
            2026, 8, 18, 20, 5, tzinfo=timezone.utc
        ),
    )

    # Remove acknowledgment/response to establish a valid delivery-only
    # repository state without inventing workflow metadata.
    with repository._connect() as connection:
        connection.execute(
            "DELETE FROM governance_assessment_artifacts "
            "WHERE sequence_number > 1"
        )

    state = workflow(repository).get_workflow(
        context=build_context()
    )

    assert (
        state.workflow_stage
        == WORKFLOW_STAGE_AWAITING_CLIENT_RECEIPT
    )
    assert state.required_operator_action == ACTION_RECORD_CLIENT_RECEIPT
    assert state.report_id == "report-001"


def test_projects_awaiting_client_response(repository):
    delivery = build_delivery()
    acknowledgment = build_acknowledgment(delivery)

    GovernancePaidAssessmentLifecyclePersistenceService().persist_lifecycle(
        repository=repository,
        delivery_event=delivery,
        client_acknowledgment=acknowledgment,
        client_response=build_response(acknowledgment),
        created_at=datetime(
            2026, 8, 18, 20, 5, tzinfo=timezone.utc
        ),
    )

    with repository._connect() as connection:
        connection.execute(
            "DELETE FROM governance_assessment_artifacts "
            "WHERE sequence_number > 2"
        )

    state = workflow(repository).get_workflow(
        context=build_context()
    )

    assert (
        state.workflow_stage
        == WORKFLOW_STAGE_AWAITING_CLIENT_RESPONSE
    )
    assert state.required_operator_action == ACTION_RECORD_CLIENT_RESPONSE
    assert state.report_id == "report-001"


def establish_client_response(repository):
    delivery = build_delivery()
    acknowledgment = build_acknowledgment(delivery)
    response = build_response(acknowledgment)

    GovernancePaidAssessmentLifecyclePersistenceService().persist_lifecycle(
        repository=repository,
        delivery_event=delivery,
        client_acknowledgment=acknowledgment,
        client_response=response,
        created_at=datetime(
            2026, 8, 18, 20, 5, tzinfo=timezone.utc
        ),
    )

    return response


def test_projects_ready_for_closeout(repository):
    establish_client_response(repository)

    before = repository.list_artifacts(context=build_context())

    state = workflow(repository).get_workflow(
        context=build_context()
    )

    after = repository.list_artifacts(context=build_context())

    assert state.workflow_stage == WORKFLOW_STAGE_READY_FOR_CLOSEOUT
    assert (
        state.required_operator_action
        == ACTION_CONFIRM_ADMINISTRATIVE_CLOSEOUT
    )
    assert state.allowed_operator_actions == (
        ACTION_CONFIRM_ADMINISTRATIVE_CLOSEOUT,
    )
    assert state.assessment_closed is False
    assert state.findings_disposition == "acknowledged"
    assert state.recommendations_disposition == "accepted"
    assert len(state.evidence_artifacts) == 3
    assert before == after


def test_projects_closed(repository):
    establish_client_response(repository)

    closeout = GovernancePaidAssessmentCloseoutService(
        repository=repository
    ).close_assessment(
        request=PaidAssessmentCloseoutRequest(
            context=build_context(),
            report_id="report-001",
            closed_by="FIP Operator",
            closeout_reason="Administrative paid-assessment closeout.",
            administrative_closeout_confirmed=True,
        ),
        created_at=datetime(
            2026, 8, 18, 20, 30, tzinfo=timezone.utc
        ),
    )

    before = repository.list_artifacts(context=build_context())

    state = workflow(repository).get_workflow(
        context=build_context()
    )

    after = repository.list_artifacts(context=build_context())

    assert state.workflow_stage == WORKFLOW_STAGE_CLOSED
    assert state.required_operator_action == ACTION_NONE
    assert state.allowed_operator_actions == ()
    assert state.assessment_closed is True
    assert state.closeout_artifact is not None
    assert state.closeout_artifact.artifact_id == closeout.artifact_id
    assert len(state.evidence_artifacts) == 4
    assert before == after


def test_closed_projection_has_no_downstream_authority(repository):
    establish_client_response(repository)

    GovernancePaidAssessmentCloseoutService(
        repository=repository
    ).close_assessment(
        request=PaidAssessmentCloseoutRequest(
            context=build_context(),
            report_id="report-001",
            closed_by="FIP Operator",
            closeout_reason="Administrative paid-assessment closeout.",
            administrative_closeout_confirmed=True,
        ),
        created_at=datetime(
            2026, 8, 18, 20, 30, tzinfo=timezone.utc
        ),
    )

    payload = workflow(repository).get_workflow(
        context=build_context()
    ).to_dict()

    assert payload["workflow_stage"] == "closed"
    assert payload["assessment_closed"] is True

    assert "recommendations_implemented" not in payload
    assert "intervention_requested" not in payload
    assert "intervention_authorized" not in payload
    assert "intervention_executed" not in payload
    assert "causal_success" not in payload
    assert "roi_verified" not in payload
    assert "remediation_success" not in payload
    assert "customer_outcome_verified" not in payload


def test_operator_projection_is_read_only(repository):
    establish_client_response(repository)

    assessment_before = repository.get_assessment(
        context=build_context()
    )
    artifacts_before = repository.list_artifacts(
        context=build_context()
    )

    workflow(repository).get_workflow(
        context=build_context()
    )

    assessment_after = repository.get_assessment(
        context=build_context()
    )
    artifacts_after = repository.list_artifacts(
        context=build_context()
    )

    assert assessment_after == assessment_before
    assert artifacts_after == artifacts_before


def test_operator_evidence_preserves_repository_order(repository):
    establish_client_response(repository)

    GovernancePaidAssessmentCloseoutService(
        repository=repository
    ).close_assessment(
        request=PaidAssessmentCloseoutRequest(
            context=build_context(),
            report_id="report-001",
            closed_by="FIP Operator",
            closeout_reason="Administrative paid-assessment closeout.",
            administrative_closeout_confirmed=True,
        ),
        created_at=datetime(
            2026, 8, 18, 20, 30, tzinfo=timezone.utc
        ),
    )

    state = workflow(repository).get_workflow(
        context=build_context()
    )

    assert [
        item.sequence_number
        for item in state.evidence_artifacts
    ] == [1, 2, 3, 4]

    assert state.repository_chain_valid is True