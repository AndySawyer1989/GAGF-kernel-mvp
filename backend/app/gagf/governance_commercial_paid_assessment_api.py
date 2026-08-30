from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.gagf.governance_assessment_api import (
    AssessmentExecutionApiRequest,
    error_detail,
)
from backend.app.gagf.governance_commercial_paid_assessment_adapter import (
    CommercialContractExecutionEventInput,
    CommercialEvidenceDeclarationInput,
    CommercialExecutionEvidenceApprovalInput,
    CommercialPaidAssessmentAdapterError,
    CommercialPaidAssessmentIntakeInput,
    CommercialPaidWorkAuthorizationInput,
    CommercialStorageDeclarationInput,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    CommercialPaidAssessmentExecutionError,
    CommercialPaidAssessmentExecutionInput,
    GovernanceCommercialPaidAssessmentExecutionService,
)


COMMERCIAL_PAID_ASSESSMENT_API_VERSION = "0.2.0"
COMMERCIAL_PAID_ASSESSMENT_API_PREFIX = (
    "/api/v1/governance-paid-assessments"
)


class CommercialEvidenceDeclarationRequest(BaseModel):
    evidence_id: str = Field(min_length=1)
    source_kind: str = Field(min_length=1)
    description: str = Field(min_length=1)
    classification: str = Field(min_length=1)

    client_authorized_for_assessment: bool
    minimization_review_completed: bool
    direct_identifiers_removed: bool

    def to_domain(self) -> CommercialEvidenceDeclarationInput:
        return CommercialEvidenceDeclarationInput(
            evidence_id=self.evidence_id,
            source_kind=self.source_kind,
            description=self.description,
            classification=self.classification,
            client_authorized_for_assessment=(
                self.client_authorized_for_assessment
            ),
            minimization_review_completed=(
                self.minimization_review_completed
            ),
            direct_identifiers_removed=(
                self.direct_identifiers_removed
            ),
        )


class CommercialStorageDeclarationRequest(BaseModel):
    """
    Operator storage-control attestations.

    repository_path is intentionally absent. The server assigns the
    governed paid-assessment execution database path.
    """

    operator_controlled_location: bool
    access_restricted: bool
    storage_protection_confirmed: bool
    backup_plan_recorded: bool
    retention_period_recorded: bool
    deletion_plan_recorded: bool

    def to_domain(
        self,
        *,
        repository_path: str,
    ) -> CommercialStorageDeclarationInput:
        return CommercialStorageDeclarationInput(
            repository_path=repository_path,
            operator_controlled_location=(
                self.operator_controlled_location
            ),
            access_restricted=self.access_restricted,
            storage_protection_confirmed=(
                self.storage_protection_confirmed
            ),
            backup_plan_recorded=self.backup_plan_recorded,
            retention_period_recorded=(
                self.retention_period_recorded
            ),
            deletion_plan_recorded=self.deletion_plan_recorded,
        )


class CommercialPaidAssessmentIntakeRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    client_id: str = Field(min_length=1)
    engagement_id: str = Field(min_length=1)
    assessment_id: str = Field(min_length=1)

    client_display_name: str = Field(min_length=1)
    assessment_name: str = Field(min_length=1)

    operator_name: str = Field(min_length=1)
    client_contact_name: str = Field(min_length=1)

    assessment_scope_confirmed: bool
    evidence_scope_confirmed: bool
    client_data_use_confirmed: bool
    operator_readiness_confirmed: bool

    evidence: list[
        CommercialEvidenceDeclarationRequest
    ] = Field(min_length=1)

    storage: CommercialStorageDeclarationRequest

    def to_domain(
        self,
        *,
        repository_path: str,
    ) -> CommercialPaidAssessmentIntakeInput:
        return CommercialPaidAssessmentIntakeInput(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            engagement_id=self.engagement_id,
            assessment_id=self.assessment_id,
            client_display_name=self.client_display_name,
            assessment_name=self.assessment_name,
            operator_name=self.operator_name,
            client_contact_name=self.client_contact_name,
            assessment_scope_confirmed=(
                self.assessment_scope_confirmed
            ),
            evidence_scope_confirmed=(
                self.evidence_scope_confirmed
            ),
            client_data_use_confirmed=(
                self.client_data_use_confirmed
            ),
            operator_readiness_confirmed=(
                self.operator_readiness_confirmed
            ),
            evidence=tuple(
                item.to_domain()
                for item in self.evidence
            ),
            storage=self.storage.to_domain(
                repository_path=repository_path
            ),
        )


class CommercialContractExecutionEventRequest(BaseModel):
    contract_execution_event_id: str = Field(min_length=1)

    contract_executed: bool
    contract_execution_review_ready: bool
    contract_execution_confirmed: bool
    executed_contract_reference_recorded: bool
    executed_at_recorded: bool
    all_required_signatures_recorded: bool
    human_operator_confirmed_execution: bool

    requires_final_paid_work_authorization: bool
    human_boundary_required: bool
    gagf_kernel_authoritative: bool
    ai_override_allowed: bool

    def to_domain(
        self,
    ) -> CommercialContractExecutionEventInput:
        return CommercialContractExecutionEventInput(
            contract_execution_event_id=(
                self.contract_execution_event_id
            ),
            contract_executed=self.contract_executed,
            contract_execution_review_ready=(
                self.contract_execution_review_ready
            ),
            contract_execution_confirmed=(
                self.contract_execution_confirmed
            ),
            executed_contract_reference_recorded=(
                self.executed_contract_reference_recorded
            ),
            executed_at_recorded=self.executed_at_recorded,
            all_required_signatures_recorded=(
                self.all_required_signatures_recorded
            ),
            human_operator_confirmed_execution=(
                self.human_operator_confirmed_execution
            ),
            requires_final_paid_work_authorization=(
                self.requires_final_paid_work_authorization
            ),
            human_boundary_required=(
                self.human_boundary_required
            ),
            gagf_kernel_authoritative=(
                self.gagf_kernel_authoritative
            ),
            ai_override_allowed=self.ai_override_allowed,
        )


class CommercialPaidWorkAuthorizationRequest(BaseModel):
    authorization_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    client_id: str = Field(min_length=1)
    engagement_id: str = Field(min_length=1)
    assessment_id: str = Field(min_length=1)
    contract_execution_event_id: str = Field(min_length=1)
    authorized_by: str = Field(min_length=1)
    authorized_at: str = Field(min_length=1)
    paid_assessment_authorized: bool

    def to_domain(
        self,
    ) -> CommercialPaidWorkAuthorizationInput:
        return CommercialPaidWorkAuthorizationInput(
            authorization_id=self.authorization_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            engagement_id=self.engagement_id,
            assessment_id=self.assessment_id,
            contract_execution_event_id=(
                self.contract_execution_event_id
            ),
            authorized_by=self.authorized_by,
            authorized_at=self.authorized_at,
            paid_assessment_authorized=(
                self.paid_assessment_authorized
            ),
        )


class CommercialExecutionEvidenceApprovalRequest(BaseModel):
    evidence_id: str = Field(min_length=1)
    approved_content_sha256: str = Field(min_length=1)
    approved_by: str = Field(min_length=1)
    approved_at: str = Field(min_length=1)
    execution_evidence_approved: bool

    def to_domain(
        self,
    ) -> CommercialExecutionEvidenceApprovalInput:
        return CommercialExecutionEvidenceApprovalInput(
            evidence_id=self.evidence_id,
            approved_content_sha256=(
                self.approved_content_sha256
            ),
            approved_by=self.approved_by,
            approved_at=self.approved_at,
            execution_evidence_approved=(
                self.execution_evidence_approved
            ),
        )


class CommercialPaidAssessmentExecutionApiRequest(BaseModel):
    intake: CommercialPaidAssessmentIntakeRequest
    contract_execution_event: CommercialContractExecutionEventRequest
    paid_work_authorization: CommercialPaidWorkAuthorizationRequest
    execution_evidence_approvals: list[
        CommercialExecutionEvidenceApprovalRequest
    ] = Field(min_length=1)
    assessment_execution_request: AssessmentExecutionApiRequest

    def to_execution_input(
        self,
        *,
        repository_path: str,
    ) -> CommercialPaidAssessmentExecutionInput:
        return CommercialPaidAssessmentExecutionInput(
            intake=self.intake.to_domain(
                repository_path=repository_path
            ),
            contract_execution_event=(
                self.contract_execution_event.to_domain()
            ),
            paid_work_authorization=(
                self.paid_work_authorization.to_domain()
            ),
            execution_evidence_approvals=tuple(
                item.to_domain()
                for item in self.execution_evidence_approvals
            ),
            assessment_execution_request=(
                self.assessment_execution_request
                .to_application_request()
            ),
        )


def create_governance_commercial_paid_assessment_router(
    *,
    service: GovernanceCommercialPaidAssessmentExecutionService,
    dependencies: list[Any] | None = None,
) -> APIRouter:
    router = APIRouter(
        prefix=COMMERCIAL_PAID_ASSESSMENT_API_PREFIX,
        tags=["governance-paid-assessments"],
        dependencies=dependencies or [],
    )

    @router.post(
        "/execute",
        status_code=status.HTTP_201_CREATED,
    )
    def execute_paid_assessment(
        request: CommercialPaidAssessmentExecutionApiRequest,
    ) -> dict[str, Any]:
        try:
            database_path = service.database_path_for_hierarchy(
                tenant_id=request.intake.tenant_id,
                client_id=request.intake.client_id,
                engagement_id=request.intake.engagement_id,
                assessment_id=request.intake.assessment_id,
            )

            execution_input = request.to_execution_input(
                repository_path=str(database_path)
            )

            result = service.execute(
                execution_input=execution_input
            )

            return {
                "operator_run_passed": True,
                "result": result.to_dict(),
                "boundaries": {
                    "api_request_is_not_paid_work_authorization": True,
                    "api_request_is_not_execution_authority": True,
                    "api_request_is_not_recovery_authority": True,
                    "repository_path_is_server_assigned": True,
                    "execution_database_is_hierarchy_scoped": True,
                    "recovery_service_remains_governed_authority_path": True,
                },
            }
        except (
            CommercialPaidAssessmentAdapterError,
            CommercialPaidAssessmentExecutionError,
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=error_detail(
                    code=(
                        "COMMERCIAL_PAID_ASSESSMENT_EXECUTION_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

    return router