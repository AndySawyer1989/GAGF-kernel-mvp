from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

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
from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    ClientAssessmentReceiptAcknowledgment,
    GovernancePaidAssessmentClientAcknowledgmentService,
)
from backend.app.gagf.governance_paid_assessment_client_response import (
    ClientAssessmentResponse,
    GovernancePaidAssessmentClientResponseService,
)
from backend.app.gagf.governance_paid_assessment_closeout import (
    PAID_ASSESSMENT_CLOSEOUT_STATUS,
    GovernancePaidAssessmentCloseoutService,
    PaidAssessmentCloseoutRequest,
)
from backend.app.gagf.governance_paid_assessment_delivery_envelope import (
    GovernancePaidAssessmentDeliveryEnvelopeService,
    PaidAssessmentDeliveryApproval,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernancePaidAssessmentDeliveryEventService,
    HumanAssessmentDeliveryConfirmation,
)
from backend.app.gagf.governance_paid_assessment_execution_coordinator import (
    GovernancePaidAssessmentExecutionCoordinator,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    GovernancePaidAssessmentExecutionHandoffService,
    PaidAssessmentExecutionHandoffStatus,
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    GovernancePaidAssessmentLifecyclePersistenceService,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_query import (
    LIFECYCLE_STAGE_CLIENT_RESPONSE_RECORDED,
    NEXT_STEP_NONE,
    GovernancePaidAssessmentLifecycleQueryService,
)
from backend.app.gagf.governance_paid_assessment_operator_workflow import (
    ACTION_NONE,
    WORKFLOW_STAGE_CLOSED,
    GovernancePaidAssessmentOperatorWorkflowService,
)


SYNTHETIC_PAID_ASSESSMENT_DRY_RUN_ID = (
    "governance-synthetic-paid-assessment-dry-run"
)
SYNTHETIC_PAID_ASSESSMENT_DRY_RUN_VERSION = "0.1.0"
SYNTHETIC_PAID_ASSESSMENT_DRY_RUN_SCHEMA_VERSION = "1.0.0"

SYNTHETIC_SCENARIO_TYPE = "synthetic-controlled-paid-assessment"
EXPECTED_CORE_ARTIFACT_COUNT = 10
EXPECTED_FINAL_ARTIFACT_COUNT = 14


class SyntheticPaidAssessmentDryRunError(RuntimeError):
    """Raised when the synthetic paid-assessment proof fails closed."""


class _CapturingGovernanceAssessmentApplicationService(
    GovernanceAssessmentApplicationService
):
    """
    Observe the result of the real production application-service execution.

    The coordinator still invokes the actual super().execute() path. This
    wrapper only retains that exact result so the same runtime lineage can
    continue into report delivery without executing the assessment twice.
    """

    def __init__(
        self,
        *,
        repository: GovernanceAssessmentRepository,
    ) -> None:
        super().__init__(repository=repository)
        self.last_result = None

    def execute(self, *, request):
        result = super().execute(request=request)
        self.last_result = result
        return result


@dataclass(frozen=True, slots=True)
class SyntheticPaidAssessmentScenario:
    tenant_id: str = "synthetic-tenant"
    client_id: str = "synthetic-client"
    engagement_id: str = "synthetic-engagement-001"
    assessment_id: str = "synthetic-assessment-001"

    client_display_name: str = "Synthetic Client Corporation"
    prepared_by: str = "FIP Governance Services"

    operator_name: str = "Synthetic FIP Operator"
    client_representative: str = "Synthetic Client Representative"

    scenario_type: str = SYNTHETIC_SCENARIO_TYPE
    synthetic: bool = True

    @property
    def context(self) -> CommercialHierarchyContext:
        return CommercialHierarchyContext(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            engagement_id=self.engagement_id,
            assessment_id=self.assessment_id,
        )

    @property
    def hierarchy_key(self) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_type": self.scenario_type,
            "synthetic": self.synthetic,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "client_display_name": self.client_display_name,
            "prepared_by": self.prepared_by,
            "operator_name": self.operator_name,
            "client_representative": self.client_representative,
        }


@dataclass(frozen=True, slots=True)
class SyntheticPaidAssessmentDryRunResult:
    scenario_type: str
    synthetic: bool

    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    database_path: str
    report_id: str

    paid_work_authorized: bool
    execution_handoff_ready: bool
    assessment_execution_complete: bool
    report_ready: bool
    delivery_approved: bool
    delivery_recorded: bool
    client_receipt_acknowledged: bool
    client_response_recorded: bool
    lifecycle_persisted: bool
    assessment_closed: bool

    operator_workflow_stage: str
    operator_required_action: str

    core_artifact_count: int
    final_artifact_count: int
    repository_chain_valid: bool

    findings_disposition: str
    recommendations_disposition: str

    dry_run_passed: bool

    dry_run_type: str = SYNTHETIC_PAID_ASSESSMENT_DRY_RUN_ID
    version: str = SYNTHETIC_PAID_ASSESSMENT_DRY_RUN_VERSION
    schema_version: str = (
        SYNTHETIC_PAID_ASSESSMENT_DRY_RUN_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dry_run_type": self.dry_run_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "scenario_type": self.scenario_type,
            "synthetic": self.synthetic,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "database_path": self.database_path,
            "report_id": self.report_id,
            "paid_work_authorized": self.paid_work_authorized,
            "execution_handoff_ready": (
                self.execution_handoff_ready
            ),
            "assessment_execution_complete": (
                self.assessment_execution_complete
            ),
            "report_ready": self.report_ready,
            "delivery_approved": self.delivery_approved,
            "delivery_recorded": self.delivery_recorded,
            "client_receipt_acknowledged": (
                self.client_receipt_acknowledged
            ),
            "client_response_recorded": (
                self.client_response_recorded
            ),
            "lifecycle_persisted": self.lifecycle_persisted,
            "assessment_closed": self.assessment_closed,
            "operator_workflow_stage": (
                self.operator_workflow_stage
            ),
            "operator_required_action": (
                self.operator_required_action
            ),
            "core_artifact_count": self.core_artifact_count,
            "final_artifact_count": self.final_artifact_count,
            "repository_chain_valid": (
                self.repository_chain_valid
            ),
            "findings_disposition": self.findings_disposition,
            "recommendations_disposition": (
                self.recommendations_disposition
            ),
            "dry_run_passed": self.dry_run_passed,
            "boundaries": {
                "synthetic_dry_run_is_not_real_customer_acceptance": True,
                "assessment_closed_is_not_recommendations_implemented": True,
                "assessment_closed_is_not_intervention_authorized": True,
                "assessment_closed_is_not_remediation_success": True,
                "assessment_closed_is_not_roi_verified": True,
                "assessment_closed_is_not_customer_outcome_verified": True,
            },
        }


class SyntheticPaidAssessmentDryRunService:
    """
    Execute one deterministic synthetic paid-assessment engagement.

    This is an executable integration proof over existing governed services.
    It does not weaken, replace, or bypass their validation boundaries.
    """

    def run(
        self,
        *,
        database_path: str | Path,
        scenario: SyntheticPaidAssessmentScenario | None = None,
    ) -> SyntheticPaidAssessmentDryRunResult:
        scenario = scenario or SyntheticPaidAssessmentScenario()

        if not isinstance(
            scenario,
            SyntheticPaidAssessmentScenario,
        ):
            raise SyntheticPaidAssessmentDryRunError(
                "scenario must be a SyntheticPaidAssessmentScenario"
            )

        if scenario.synthetic is not True:
            raise SyntheticPaidAssessmentDryRunError(
                "PILOT-001 requires an explicitly synthetic scenario"
            )

        path = Path(database_path)

        if not str(path).strip():
            raise SyntheticPaidAssessmentDryRunError(
                "database_path is required"
            )

        if path.exists():
            raise SyntheticPaidAssessmentDryRunError(
                "synthetic dry-run database already exists: "
                f"{path}"
            )

        if path.parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        repository = GovernanceAssessmentRepository(path)
        request = self._build_request(scenario)

        authorization = self._build_work_authorization(
            scenario
        )

        self._require(
            authorization.paid_assessment_authorized is True,
            "synthetic paid-work authorization was not explicit",
        )

        handoff = (
            GovernancePaidAssessmentExecutionHandoffService()
            .build_handoff(
                contract_execution_event=(
                    self._build_contract_execution_event(
                        scenario
                    )
                ),
                paid_work_authorization=authorization,
                assessment_execution_request=request,
            )
        )

        self._require(
            handoff.status
            is PaidAssessmentExecutionHandoffStatus.READY,
            "paid-assessment execution handoff is not READY",
        )

        self._require(
            handoff.hierarchy_key == scenario.hierarchy_key,
            "execution handoff hierarchy mismatch",
        )

        application_service = (
            _CapturingGovernanceAssessmentApplicationService(
                repository=repository
            )
        )

        coordinator = GovernancePaidAssessmentExecutionCoordinator(
            application_service=application_service
        )

        execution_result = coordinator.execute(
            handoff=handoff,
            request=request,
        )

        application_result = application_service.last_result

        self._require(
            application_result is not None,
            "real application execution result was not captured",
        )
        self._require(
            application_result.completed is True,
            "assessment application did not complete",
        )
        self._require(
            application_result.persistence.completed is True,
            "assessment persistence did not complete",
        )
        self._require(
            application_result.persistence.artifact_count
            == EXPECTED_CORE_ARTIFACT_COUNT,
            "assessment core artifact count is not 10",
        )
        self._require(
            application_result.persistence.repository_chain_valid
            is True,
            "assessment repository chain is invalid after execution",
        )

        report_package = (
            application_result.demonstration.report_package
        )

        self._require(
            report_package.report_id
            == execution_result.report_id,
            "report package does not match execution result",
        )
        self._require(
            bool(report_package.markdown),
            "client-ready report markdown is empty",
        )

        delivery_approval = PaidAssessmentDeliveryApproval(
            approval_id="synthetic-delivery-approval-001",
            tenant_id=execution_result.tenant_id,
            client_id=execution_result.client_id,
            engagement_id=execution_result.engagement_id,
            assessment_id=execution_result.assessment_id,
            report_id=execution_result.report_id,
            approved_by=scenario.operator_name,
            approved_at="2026-08-20T13:00:00+00:00",
            scope_approved=True,
            evidence_boundary_approved=True,
            buyer_language_approved=True,
            delivery_approved=True,
        )

        envelope = (
            GovernancePaidAssessmentDeliveryEnvelopeService()
            .build_envelope(
                execution_result=execution_result,
                report_package=report_package,
                delivery_approval=delivery_approval,
            )
        )

        self._require(
            envelope.delivery_status
            == "approved_for_human_delivery",
            "report is not approved for human delivery",
        )

        human_delivery_confirmation = (
            HumanAssessmentDeliveryConfirmation(
                delivery_event_id="synthetic-delivery-event-001",
                tenant_id=envelope.tenant_id,
                client_id=envelope.client_id,
                engagement_id=envelope.engagement_id,
                assessment_id=envelope.assessment_id,
                report_id=envelope.report_id,
                delivered_by=scenario.operator_name,
                delivered_at="2026-08-20T13:15:00+00:00",
                delivery_method="synthetic_email",
                delivery_reference=(
                    "synthetic-message-reference-001"
                ),
                delivery_completed=True,
            )
        )

        delivery_event = (
            GovernancePaidAssessmentDeliveryEventService()
            .record_delivery(
                delivery_envelope=envelope,
                human_confirmation=human_delivery_confirmation,
            )
        )

        self._require(
            delivery_event.delivery_status == "delivered",
            "synthetic delivery was not recorded",
        )

        receipt_evidence = (
            ClientAssessmentReceiptAcknowledgment(
                acknowledgment_id="synthetic-client-ack-001",
                tenant_id=delivery_event.tenant_id,
                client_id=delivery_event.client_id,
                engagement_id=delivery_event.engagement_id,
                assessment_id=delivery_event.assessment_id,
                report_id=delivery_event.report_id,
                delivery_event_id=delivery_event.delivery_event_id,
                delivery_event_hash=delivery_event.delivery_event_hash,
                acknowledged_by=scenario.client_representative,
                acknowledged_at="2026-08-20T13:30:00+00:00",
                acknowledgment_method="synthetic_email_reply",
                acknowledgment_reference=(
                    "synthetic-receipt-reference-001"
                ),
                client_acknowledged_receipt=True,
            )
        )

        client_acknowledgment = (
            GovernancePaidAssessmentClientAcknowledgmentService()
            .record_acknowledgment(
                delivery_event=delivery_event,
                acknowledgment=receipt_evidence,
            )
        )

        self._require(
            client_acknowledgment.acknowledgment_status
            == "client_receipt_acknowledged",
            "synthetic client receipt was not acknowledged",
        )

        response_evidence = ClientAssessmentResponse(
            response_id="synthetic-client-response-001",
            tenant_id=client_acknowledgment.tenant_id,
            client_id=client_acknowledgment.client_id,
            engagement_id=client_acknowledgment.engagement_id,
            assessment_id=client_acknowledgment.assessment_id,
            report_id=client_acknowledgment.report_id,
            acknowledgment_id=(
                client_acknowledgment.acknowledgment_id
            ),
            acknowledgment_hash=(
                client_acknowledgment.acknowledgment_hash
            ),
            responded_by=scenario.client_representative,
            responded_at="2026-08-20T13:45:00+00:00",
            response_method="synthetic_email_reply",
            response_reference=(
                "synthetic-assessment-response-001"
            ),
            findings_disposition="acknowledged",
            recommendations_disposition="accepted",
            response_note=(
                "Synthetic client accepts recommendations "
                "for planning review only."
            ),
        )

        client_response = (
            GovernancePaidAssessmentClientResponseService()
            .record_response(
                client_acknowledgment=client_acknowledgment,
                response=response_evidence,
            )
        )

        self._require(
            client_response.response_status
            == "client_response_recorded",
            "synthetic client response was not recorded",
        )

        lifecycle_receipt = (
            GovernancePaidAssessmentLifecyclePersistenceService()
            .persist_lifecycle(
                repository=repository,
                delivery_event=delivery_event,
                client_acknowledgment=client_acknowledgment,
                client_response=client_response,
            )
        )

        self._require(
            lifecycle_receipt.repository_chain_valid is True,
            "repository chain is invalid after lifecycle persistence",
        )
        self._require(
            lifecycle_receipt.first_sequence_number == 11,
            "paid-assessment lifecycle did not begin at artifact 11",
        )
        self._require(
            lifecycle_receipt.last_sequence_number == 13,
            "paid-assessment lifecycle did not end at artifact 13",
        )

        lifecycle_state = (
            GovernancePaidAssessmentLifecycleQueryService(
                repository=repository
            ).get_state(
                context=scenario.context
            )
        )

        self._require(
            lifecycle_state.current_stage
            == LIFECYCLE_STAGE_CLIENT_RESPONSE_RECORDED,
            "lifecycle did not reach client_response_recorded",
        )
        self._require(
            lifecycle_state.pending_next_step == NEXT_STEP_NONE,
            "lifecycle still has a pending post-response step",
        )
        self._require(
            lifecycle_state.findings_disposition
            == "acknowledged",
            "synthetic findings disposition mismatch",
        )
        self._require(
            lifecycle_state.recommendations_disposition
            == "accepted",
            "synthetic recommendations disposition mismatch",
        )

        closeout = GovernancePaidAssessmentCloseoutService(
            repository=repository
        ).close_assessment(
            request=PaidAssessmentCloseoutRequest(
                context=scenario.context,
                report_id=execution_result.report_id,
                closed_by=scenario.operator_name,
                closeout_reason=(
                    "Synthetic assessment delivery, receipt, "
                    "and client response have been recorded."
                ),
                administrative_closeout_confirmed=True,
            )
        )

        self._require(
            closeout.closeout_status
            == PAID_ASSESSMENT_CLOSEOUT_STATUS,
            "synthetic assessment did not reach administrative closeout",
        )
        self._require(
            closeout.sequence_number
            == EXPECTED_FINAL_ARTIFACT_COUNT,
            "closeout was not artifact 14",
        )
        self._require(
            closeout.repository_chain_valid is True,
            "repository chain is invalid after closeout",
        )

        artifacts_before_operator_projection = (
            repository.list_artifacts(
                context=scenario.context
            )
        )

        self._require(
            len(artifacts_before_operator_projection)
            == EXPECTED_FINAL_ARTIFACT_COUNT,
            "final repository does not contain exactly 14 artifacts",
        )

        operator_workflow = (
            GovernancePaidAssessmentOperatorWorkflowService(
                repository=repository
            ).get_workflow(
                context=scenario.context
            )
        )

        self._require(
            operator_workflow.workflow_stage
            == WORKFLOW_STAGE_CLOSED,
            "operator workflow is not closed",
        )
        self._require(
            operator_workflow.required_operator_action
            == ACTION_NONE,
            "closed operator workflow still requires an action",
        )
        self._require(
            operator_workflow.assessment_closed is True,
            "operator workflow does not project assessment_closed",
        )

        artifacts_after_operator_projection = (
            repository.list_artifacts(
                context=scenario.context
            )
        )

        self._require(
            artifacts_after_operator_projection
            == artifacts_before_operator_projection,
            "operator workflow projection mutated repository artifacts",
        )
        self._require(
            len(artifacts_after_operator_projection)
            == EXPECTED_FINAL_ARTIFACT_COUNT,
            "operator projection created artifact 15",
        )

        final_chain_valid = repository.verify_chain(
            context=scenario.context
        )

        self._require(
            final_chain_valid is True,
            "final synthetic repository chain is invalid",
        )

        return SyntheticPaidAssessmentDryRunResult(
            scenario_type=scenario.scenario_type,
            synthetic=True,
            tenant_id=scenario.tenant_id,
            client_id=scenario.client_id,
            engagement_id=scenario.engagement_id,
            assessment_id=scenario.assessment_id,
            database_path=str(path),
            report_id=execution_result.report_id,
            paid_work_authorized=True,
            execution_handoff_ready=True,
            assessment_execution_complete=True,
            report_ready=True,
            delivery_approved=True,
            delivery_recorded=True,
            client_receipt_acknowledged=True,
            client_response_recorded=True,
            lifecycle_persisted=True,
            assessment_closed=True,
            operator_workflow_stage=(
                operator_workflow.workflow_stage
            ),
            operator_required_action=(
                operator_workflow.required_operator_action
            ),
            core_artifact_count=EXPECTED_CORE_ARTIFACT_COUNT,
            final_artifact_count=(
                len(artifacts_after_operator_projection)
            ),
            repository_chain_valid=final_chain_valid,
            findings_disposition=(
                lifecycle_state.findings_disposition
            ),
            recommendations_disposition=(
                lifecycle_state.recommendations_disposition
            ),
            dry_run_passed=True,
        )

    @staticmethod
    def _build_request(
        scenario: SyntheticPaidAssessmentScenario,
    ) -> AssessmentExecutionRequest:
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

        return AssessmentExecutionRequest(
            context=scenario.context,
            assessment_name="Synthetic Governance Runway Assessment",
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
                    description="Synthetic workflow evidence",
                    required=True,
                    minimum_record_count=4,
                ),
            ),
            evidence_inputs=(
                DemonstrationEvidenceInput(
                    source=EvidenceSourceReference(
                        source_id="synthetic-source-001",
                        kind=EvidenceSourceKind.CSV,
                        display_name="Synthetic Workflow Export",
                    ),
                    csv_text=csv_text,
                ),
            ),
            client_display_name=scenario.client_display_name,
            prepared_by=scenario.prepared_by,
        )

    @staticmethod
    def _build_work_authorization(
        scenario: SyntheticPaidAssessmentScenario,
    ) -> PaidAssessmentWorkAuthorization:
        return PaidAssessmentWorkAuthorization(
            authorization_id="synthetic-paid-work-auth-001",
            tenant_id=scenario.tenant_id,
            client_id=scenario.client_id,
            engagement_id=scenario.engagement_id,
            assessment_id=scenario.assessment_id,
            contract_execution_event_id=(
                "synthetic-contract-event-001"
            ),
            authorized_by=scenario.operator_name,
            authorized_at="2026-08-20T12:10:00+00:00",
            paid_assessment_authorized=True,
        )

    @staticmethod
    def _build_contract_execution_event(
        scenario: SyntheticPaidAssessmentScenario,
    ) -> dict[str, Any]:
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
            "contract_execution_event_id": (
                "synthetic-contract-event-001"
            ),
            "recorded_at": "2026-08-20T12:00:00+00:00",
            "execution_evidence": {
                "executed_contract_reference": (
                    "synthetic-contract-ref-001"
                ),
                "executed_at": "2026-08-20T11:55:00+00:00",
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
                    "contract_execution_event_is_not_"
                    "paid_work_authorization"
                ): True,
            },
            "synthetic": True,
            "synthetic_hierarchy_key": scenario.hierarchy_key,
        }

    @staticmethod
    def _require(
        condition: bool,
        message: str,
    ) -> None:
        if condition is not True:
            raise SyntheticPaidAssessmentDryRunError(message)


SERVICE_TYPE = SyntheticPaidAssessmentDryRunService