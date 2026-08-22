import hashlib
from datetime import date

from backend.app.gagf.governance_assessment_application import (
    AssessmentExecutionRequest,
)
from backend.app.gagf.governance_assessment_demonstration import (
    DemonstrationEvidenceInput,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_real_paid_assessment_authorization_bridge import (
    GovernanceRealPaidAssessmentAuthorizationBridgeService,
)
from backend.app.gagf.governance_real_paid_assessment_execution import (
    EXPECTED_CORE_ARTIFACT_COUNT,
    REAL_EXECUTION_STATUS_COMPLETE,
    GovernanceRealPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_real_paid_assessment_execution_evidence import (
    GovernanceRealPaidAssessmentExecutionEvidenceService,
    RealAssessmentExecutionEvidenceApproval,
)
from backend.app.gagf.governance_real_paid_assessment_readiness import (
    EvidenceDataClassification,
    GovernanceRealPaidAssessmentReadinessService,
    RealAssessmentEvidenceDeclaration,
    RealAssessmentStorageDeclaration,
    RealPaidAssessmentIntake,
)


CSV_TEXT = (
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


def sha256_text(value):
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def build_contract_event():
    return {
        "status": "ok",
        "event_type": (
            "assessment_factory_lite_contract_execution_event"
        ),
        "package_name": "assessment_factory_lite",
        "release": (
            "assessment-factory-lite-scope-call-conversion"
        ),
        "version": "2.3.0",
        "event_stage": "contract_execution",
        "event_status": "contract_executed",
        "contract_execution_event_id": "contract-event-real-001",
        "recorded_at": "2026-08-20T18:30:00+00:00",
        "execution_evidence": {
            "executed_contract_reference": "contract-ref-real-001",
            "executed_at": "2026-08-20T18:25:00+00:00",
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
            "contract_execution_event_is_not_paid_work_authorization": True,
        },
    }


def test_controlled_real_paid_assessment_executes_to_report_boundary(
    tmp_path,
):
    database_path = (
        tmp_path / "controlled-real-paid-assessment.sqlite3"
    )

    intake = RealPaidAssessmentIntake(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        client_display_name="ACME Corporation",
        assessment_name="Governance Runway Assessment",
        operator_name="FIP Operator",
        client_contact_name="Client Representative",
        assessment_scope_confirmed=True,
        evidence_scope_confirmed=True,
        client_data_use_confirmed=True,
        operator_readiness_confirmed=True,
        evidence=(
            RealAssessmentEvidenceDeclaration(
                evidence_id="source-001",
                source_kind="csv",
                description="Redacted workflow export",
                classification=EvidenceDataClassification.REDACTED,
                client_authorized_for_assessment=True,
                minimization_review_completed=True,
                direct_identifiers_removed=True,
            ),
        ),
        storage=RealAssessmentStorageDeclaration(
            repository_path=str(database_path),
            operator_controlled_location=True,
            access_restricted=True,
            storage_protection_confirmed=True,
            backup_plan_recorded=True,
            retention_period_recorded=True,
            deletion_plan_recorded=True,
        ),
    )

    readiness = GovernanceRealPaidAssessmentReadinessService().evaluate(
        intake=intake
    )

    authorization = PaidAssessmentWorkAuthorization(
        authorization_id="paid-work-auth-real-001",
        tenant_id=intake.tenant_id,
        client_id=intake.client_id,
        engagement_id=intake.engagement_id,
        assessment_id=intake.assessment_id,
        contract_execution_event_id="contract-event-real-001",
        authorized_by="FIP Operator",
        authorized_at="2026-08-20T18:35:00+00:00",
        paid_assessment_authorized=True,
    )

    bridge = (
        GovernanceRealPaidAssessmentAuthorizationBridgeService()
        .bind(
            intake=intake,
            readiness=readiness,
            paid_work_authorization=authorization,
        )
    )

    request = AssessmentExecutionRequest(
        context=intake.context,
        assessment_name=intake.assessment_name,
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
                    display_name="Redacted Workflow Export",
                ),
                csv_text=CSV_TEXT,
            ),
        ),
        client_display_name=intake.client_display_name,
        prepared_by=intake.operator_name,
    )

    evidence_binding = (
        GovernanceRealPaidAssessmentExecutionEvidenceService()
        .bind(
            intake=intake,
            request=request,
            approvals=(
                RealAssessmentExecutionEvidenceApproval(
                    evidence_id="source-001",
                    approved_content_sha256=sha256_text(CSV_TEXT),
                    approved_by="FIP Operator",
                    approved_at="2026-08-20T18:40:00+00:00",
                    execution_evidence_approved=True,
                ),
            ),
        )
    )

    result = GovernanceRealPaidAssessmentExecutionService().execute(
        database_path=database_path,
        intake=intake,
        authorization_bridge=bridge,
        evidence_binding=evidence_binding,
        contract_execution_event=build_contract_event(),
        paid_work_authorization=authorization,
        request=request,
    )

    assert database_path.exists()

    assert (
        result.execution_status
        == REAL_EXECUTION_STATUS_COMPLETE
    )
    assert result.application_completed is True
    assert result.repository_chain_valid is True
    assert result.artifact_count == EXPECTED_CORE_ARTIFACT_COUNT
    assert result.artifact_count == 10
    assert result.report_id
    assert result.report_package_hash
    assert result.assessment_execution_request_hash
    assert result.application_request_hash
    assert result.demonstration_hash

    assert (
        result.hierarchy_key
        == "tenant-alpha/client-acme/engagement-001/assessment-001"
    )

    payload = result.to_dict()

    assert (
        payload["assessment_execution_request_hash"]
        == result.assessment_execution_request_hash
    )
    assert (
        payload["application_request_hash"]
        == result.application_request_hash
    )
    assert (
        payload["demonstration_hash"]
        == result.demonstration_hash
    )

    assert payload["boundaries"][
        "execution_complete_is_not_delivery_approval"
    ] is True
    assert payload["boundaries"][
        "execution_complete_is_not_delivery"
    ] is True
    assert payload["boundaries"][
        "execution_complete_is_not_client_acceptance"
    ] is True
    assert payload["boundaries"][
        "execution_complete_is_not_intervention_authorization"
    ] is True
    assert payload["boundaries"][
        "execution_complete_is_not_customer_outcome_verified"
    ] is True

    assert "delivered" not in payload
    assert "client_acknowledged" not in payload
    assert "recommendations_accepted" not in payload
    assert "intervention_authorized" not in payload
    assert "customer_outcome_verified" not in payload