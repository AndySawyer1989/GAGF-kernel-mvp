from datetime import date

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
    GovernanceAssessmentApplicationService,
)
from backend.app.gagf.governance_assessment_demonstration import (
    DemonstrationEvidenceInput,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)
from backend.app.gagf.governance_paid_assessment_delivery_envelope import (
    GovernancePaidAssessmentDeliveryEnvelopeService,
    PaidAssessmentDeliveryApproval,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernancePaidAssessmentDeliveryEventService,
    HumanAssessmentDeliveryConfirmation,
)
from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    ClientAssessmentReceiptAcknowledgment,
    GovernancePaidAssessmentClientAcknowledgmentService,
)
from backend.app.gagf.governance_paid_assessment_client_response import (
    ClientAssessmentResponse,
    GovernancePaidAssessmentClientResponseService,
)
from backend.app.gagf.governance_paid_assessment_execution_coordinator import (
    GovernancePaidAssessmentExecutionCoordinator,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    GovernancePaidAssessmentExecutionHandoffService,
    PaidAssessmentExecutionHandoffStatus,
    PaidAssessmentWorkAuthorization,
)


EXPECTED_HIERARCHY = (
    "tenant-alpha/client-acme/engagement-001/assessment-001"
)


class CapturingGovernanceAssessmentApplicationService(
    GovernanceAssessmentApplicationService
):
    """
    Test observer around the real application service.

    Execution remains the production super().execute() path. The observer
    retains the exact result consumed by PA-002 so PA-004 can continue that
    same runtime lineage into PA-003 without executing the assessment twice.
    """

    def __init__(self, *, repository):
        super().__init__(repository=repository)
        self.last_result = None

    def execute(self, *, request):
        result = super().execute(request=request)
        self.last_result = result
        return result


def build_request() -> AssessmentExecutionRequest:
    csv_text = (
        "event_id,event_type,occurred_at,work_item_id\n"
        "event-001,APPROVAL_DELAYED,"
        "2026-01-01T12:00:00Z,TICKET-1\n"
        "event-002,APPROVAL_DELAYED,"
        "2026-01-01T13:00:00Z,TICKET-2\n"
        "event-003,WORK_BLOCKED,"
        "2026-01-02T12:00:00Z,TICKET-3\n"
        "event-004,ESCALATION,"
        "2026-01-03T12:00:00Z,TICKET-4\n"
    )

    context = CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    return AssessmentExecutionRequest(
        context=context,
        assessment_name="Governance Runway Assessment",
        workflow_names=("Incident Management",),
        organizational_units=("IT Operations",),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 6, 30),
        objectives=("Reduce governance friction",),
        expected_outcomes=("Faster completion",),
        evidence_requirements=(
            EvidenceRequirement(
                requirement_id="required-csv",
                source_kind=EvidenceSourceKind.CSV,
                description="Workflow evidence",
                required=True,
                minimum_record_count=4,
            ),
        ),
        evidence_inputs=(
            DemonstrationEvidenceInput(
                source=EvidenceSourceReference(
                    source_id="source-001",
                    kind=EvidenceSourceKind.CSV,
                    display_name="Workflow Export",
                ),
                csv_text=csv_text,
            ),
        ),
        client_display_name="ACME Corporation",
        prepared_by="FIP Governance Services",
    )


def build_contract_event() -> dict:
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_contract_execution_event"
        ),
        "package_name": "assessment_factory_lite",
        "release": "assessment-factory-lite-scope-call-conversion",
        "version": "2.3.0",
        "event_stage": "contract_execution",
        "event_status": "contract_executed",
        "contract_execution_event_id": "contract-event-001",
        "recorded_at": "2026-08-18T15:00:00+00:00",
        "execution_evidence": {
            "executed_contract_reference": "contract-ref-001",
            "executed_at": "2026-08-18T14:30:00+00:00",
            "executed_contract_reference_recorded": True,
            "executed_at_recorded": True,
            "contract_execution_confirmed": True,
            "contract_executed": True,
        },
        "event_checklist": {
            "contract_execution_review_ready": True,
            "contract_execution_confirmed": True,
            "executed_contract_reference_recorded": True,
            "executed_at_recorded": True,
            "execution_method_recorded": True,
            "all_required_signatures_recorded": True,
            "human_operator_confirmed_execution": True,
            "signature_record_is_not_invoice": True,
            "signature_record_is_not_payment": True,
            "invoice_not_created": True,
            "payment_not_requested": True,
            "paid_assessment_not_authorized": True,
            "production_onboarding_not_started": True,
        },
        "event_blockers": [],
        "commercial_boundary": {
            "contract_execution_recorded": True,
            "contract_executed": True,
            "invoice_created": False,
            "payment_requested": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "requires_separate_invoice": True,
            "requires_separate_payment_confirmation": True,
            "requires_final_paid_work_authorization": True,
            "requires_separate_production_onboarding": True,
        },
        "governance_boundary": {
            "deterministic_status_required": True,
            "gagf_kernel_authoritative": True,
            "ai_override_allowed": False,
            "human_boundary_required": True,
            "release_marker_preserved": True,
            "contract_execution_event_is_not_invoice": True,
            "contract_execution_event_is_not_payment": True,
            (
                "contract_execution_event_is_not_paid_work_authorization"
            ): True,
        },
    }


def build_work_authorization() -> PaidAssessmentWorkAuthorization:
    return PaidAssessmentWorkAuthorization(
        authorization_id="paid-work-auth-001",
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        contract_execution_event_id="contract-event-001",
        authorized_by="Andy Sawyer",
        authorized_at="2026-08-18T15:10:00+00:00",
        paid_assessment_authorized=True,
    )


def test_paid_assessment_true_end_to_end_runtime_chain(tmp_path):
    request = build_request()

    repository = GovernanceAssessmentRepository(
        tmp_path / "paid-assessment-e2e.sqlite3"
    )

    application_service = (
        CapturingGovernanceAssessmentApplicationService(
            repository=repository
        )
    )

    handoff_service = (
        GovernancePaidAssessmentExecutionHandoffService()
    )

    handoff = handoff_service.build_handoff(
        contract_execution_event=build_contract_event(),
        paid_work_authorization=build_work_authorization(),
        assessment_execution_request=request,
    )

    assert handoff.status == PaidAssessmentExecutionHandoffStatus.READY
    assert handoff.hierarchy_key == EXPECTED_HIERARCHY
    assert handoff.tenant_id == request.context.tenant_id
    assert handoff.client_id == request.context.client_id
    assert handoff.engagement_id == request.context.engagement_id
    assert handoff.assessment_id == request.context.assessment_id

    coordinator = GovernancePaidAssessmentExecutionCoordinator(
        application_service=application_service
    )

    execution_result = coordinator.execute(
        handoff=handoff,
        request=request,
    )

    application_result = application_service.last_result

    assert application_result is not None
    assert application_result.completed is True
    assert application_result.hierarchy_key == EXPECTED_HIERARCHY

    # Proves the real persistence path completed rather than a fake
    # application response satisfying the PA-002 contract.
    assert application_result.persistence.completed is True
    assert application_result.persistence.artifact_count == 10
    assert application_result.persistence.repository_chain_valid is True

    report_package = application_result.demonstration.report_package

    assert report_package.hierarchy_key == EXPECTED_HIERARCHY
    assert report_package.markdown
    assert (
        report_package.report_id
        == execution_result.report_id
    )
    assert (
        report_package.manifest.package_hash
        == application_result.demonstration.artifact_commitments[
            "report_package_hash"
        ]
    )

    # Proves PA-002 carried the exact production result forward.
    assert execution_result.application_completed is True
    assert execution_result.hierarchy_key == EXPECTED_HIERARCHY
    assert execution_result.artifact_count == 10
    assert (
        execution_result.handoff_hash
        == handoff.handoff_hash
    )
    assert (
        execution_result.assessment_execution_request_hash
        == handoff.assessment_execution_request_hash
    )
    assert (
        execution_result.application_request_hash
        == application_result.request_hash
    )
    assert (
        execution_result.application_hash
        == application_result.application_hash
    )
    assert (
        execution_result.demonstration_hash
        == application_result.demonstration.demonstration_hash
    )
    assert (
        execution_result.persistence_hash
        == application_result.persistence.persistence_hash
    )

    delivery_approval = PaidAssessmentDeliveryApproval(
        approval_id="delivery-approval-001",
        tenant_id=execution_result.tenant_id,
        client_id=execution_result.client_id,
        engagement_id=execution_result.engagement_id,
        assessment_id=execution_result.assessment_id,
        report_id=execution_result.report_id,
        approved_by="Andy Sawyer",
        approved_at="2026-08-18T17:30:00+00:00",
        scope_approved=True,
        evidence_boundary_approved=True,
        buyer_language_approved=True,
        delivery_approved=True,
    )

    envelope_service = (
        GovernancePaidAssessmentDeliveryEnvelopeService()
    )

    envelope = envelope_service.build_envelope(
        execution_result=execution_result,
        report_package=report_package,
        delivery_approval=delivery_approval,
    )

    assert envelope.hierarchy_key == EXPECTED_HIERARCHY
    assert envelope.report_id == report_package.report_id
    assert (
        envelope.execution_result_hash
        == execution_result.execution_result_hash
    )
    assert (
        envelope.application_hash
        == execution_result.application_hash
    )
    assert (
        envelope.report_package_hash
        == report_package.manifest.package_hash
    )
    assert (
        envelope.report_markdown_hash
        == report_package.manifest.markdown_hash
    )
    assert (
        envelope.delivery_approval_hash
        == delivery_approval.approval_hash
    )
    assert envelope.delivery_status == "approved_for_human_delivery"

    serialized = envelope.to_dict()

    # Constitutional boundary: this proof stops at approval for future
    # human delivery. It does not manufacture downstream business facts.
    assert "delivered" not in serialized
    assert "client_acknowledged" not in serialized
    assert "recommendations_accepted" not in serialized
    assert "intervention_authorized" not in serialized
    assert "customer_outcome_verified" not in serialized

    human_delivery_confirmation = (
        HumanAssessmentDeliveryConfirmation(
            delivery_event_id="delivery-event-001",
            tenant_id=envelope.tenant_id,
            client_id=envelope.client_id,
            engagement_id=envelope.engagement_id,
            assessment_id=envelope.assessment_id,
            report_id=envelope.report_id,
            delivered_by="Andy Sawyer",
            delivered_at="2026-08-18T19:15:00+00:00",
            delivery_method="email",
            delivery_reference="mail-message-001",
            delivery_completed=True,
        )
    )

    delivery_event_service = (
        GovernancePaidAssessmentDeliveryEventService()
    )

    delivery_event = delivery_event_service.record_delivery(
        delivery_envelope=envelope,
        human_confirmation=human_delivery_confirmation,
    )

    assert delivery_event.delivery_status == "delivered"
    assert delivery_event.hierarchy_key == EXPECTED_HIERARCHY
    assert delivery_event.report_id == envelope.report_id
    assert (
        delivery_event.delivery_envelope_hash
        == envelope.envelope_hash
    )
    assert (
        delivery_event.delivery_approval_hash
        == envelope.delivery_approval_hash
    )
    assert (
        delivery_event.human_delivery_confirmation_hash
        == human_delivery_confirmation.confirmation_hash
    )
    assert delivery_event.delivered_by == "Andy Sawyer"
    assert delivery_event.delivery_method == "email"
    assert (
        delivery_event.delivery_reference
        == "mail-message-001"
    )

    delivery_event_payload = delivery_event.to_dict()

    # PA-005 records only the completed human delivery action.
    # Delivery is not client receipt, acknowledgment, acceptance,
    # intervention authorization, or verified customer outcome.
    assert "client_received" not in delivery_event_payload
    assert "client_acknowledged" not in delivery_event_payload
    assert "client_accepted" not in delivery_event_payload
    assert "recommendations_accepted" not in delivery_event_payload
    assert "intervention_authorized" not in delivery_event_payload
    assert "customer_outcome_verified" not in delivery_event_payload
    assert "causal_success" not in delivery_event_payload
    assert "roi_verified" not in delivery_event_payload

    client_receipt_acknowledgment = (
        ClientAssessmentReceiptAcknowledgment(
            acknowledgment_id="client-ack-001",
            tenant_id=delivery_event.tenant_id,
            client_id=delivery_event.client_id,
            engagement_id=delivery_event.engagement_id,
            assessment_id=delivery_event.assessment_id,
            report_id=delivery_event.report_id,
            delivery_event_id=delivery_event.delivery_event_id,
            delivery_event_hash=delivery_event.delivery_event_hash,
            acknowledged_by="ACME Client Representative",
            acknowledged_at="2026-08-18T19:30:00+00:00",
            acknowledgment_method="email_reply",
            acknowledgment_reference="mail-reply-001",
            client_acknowledged_receipt=True,
        )
    )

    acknowledgment_service = (
        GovernancePaidAssessmentClientAcknowledgmentService()
    )

    client_acknowledgment = (
        acknowledgment_service.record_acknowledgment(
            delivery_event=delivery_event,
            acknowledgment=client_receipt_acknowledgment,
        )
    )

    assert (
        client_acknowledgment.acknowledgment_status
        == "client_receipt_acknowledged"
    )
    assert (
        client_acknowledgment.hierarchy_key
        == EXPECTED_HIERARCHY
    )
    assert (
        client_acknowledgment.report_id
        == delivery_event.report_id
    )
    assert (
        client_acknowledgment.delivery_event_id
        == delivery_event.delivery_event_id
    )
    assert (
        client_acknowledgment.delivery_event_hash
        == delivery_event.delivery_event_hash
    )
    assert (
        client_acknowledgment.acknowledgment_evidence_hash
        == client_receipt_acknowledgment.acknowledgment_evidence_hash
    )

    acknowledgment_payload = client_acknowledgment.to_dict()

    # Receipt acknowledgment proves only that the client explicitly
    # acknowledged receipt of the delivered assessment.
    assert "findings_accepted" not in acknowledgment_payload
    assert "recommendations_accepted" not in acknowledgment_payload
    assert "client_satisfied" not in acknowledgment_payload
    assert "intervention_authorized" not in acknowledgment_payload
    assert "causal_success" not in acknowledgment_payload
    assert "roi_verified" not in acknowledgment_payload
    assert "remediation_success" not in acknowledgment_payload
    assert "customer_outcome_verified" not in acknowledgment_payload

    client_response_evidence = ClientAssessmentResponse(
        response_id="client-response-001",
        tenant_id=client_acknowledgment.tenant_id,
        client_id=client_acknowledgment.client_id,
        engagement_id=client_acknowledgment.engagement_id,
        assessment_id=client_acknowledgment.assessment_id,
        report_id=client_acknowledgment.report_id,
        acknowledgment_id=client_acknowledgment.acknowledgment_id,
        acknowledgment_hash=client_acknowledgment.acknowledgment_hash,
        responded_by="ACME Client Representative",
        responded_at="2026-08-18T20:00:00+00:00",
        response_method="email_reply",
        response_reference="assessment-response-001",
        findings_disposition="acknowledged",
        recommendations_disposition="accepted",
        response_note="Client accepts recommendations for planning review.",
    )

    client_response_service = (
        GovernancePaidAssessmentClientResponseService()
    )

    client_response = client_response_service.record_response(
        client_acknowledgment=client_acknowledgment,
        response=client_response_evidence,
    )

    assert client_response.response_status == "client_response_recorded"
    assert client_response.hierarchy_key == EXPECTED_HIERARCHY
    assert client_response.report_id == client_acknowledgment.report_id
    assert (
        client_response.acknowledgment_id
        == client_acknowledgment.acknowledgment_id
    )
    assert (
        client_response.acknowledgment_hash
        == client_acknowledgment.acknowledgment_hash
    )
    assert client_response.findings_disposition == "acknowledged"
    assert client_response.recommendations_disposition == "accepted"
    assert (
        client_response.response_evidence_hash
        == client_response_evidence.response_evidence_hash
    )

    response_payload = client_response.to_dict()

    # Recommendation acceptance is a client disposition only.
    # It does not create authority to implement or intervene.
    assert "intervention_requested" not in response_payload
    assert "intervention_authorized" not in response_payload
    assert "intervention_executed" not in response_payload
    assert "causal_success" not in response_payload
    assert "roi_verified" not in response_payload
    assert "remediation_success" not in response_payload
    assert "customer_outcome_verified" not in response_payload