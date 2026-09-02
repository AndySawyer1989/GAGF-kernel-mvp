from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.gagf.governance_assessment_application import (
    AssessmentApplicationError,
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
    ArtifactIntegrityError,
    AssessmentRecordNotFoundError,
    AssessmentRepositoryError,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution_input_binding import (
    CommercialPaidAssessmentExecutionInputBindingError,
    GovernanceCommercialPaidAssessmentExecutionInputBindingService,
)


ASSESSMENT_APPLICATION_API_VERSION = "1.0.0"


class EvidenceRequirementRequest(BaseModel):
    requirement_id: str = Field(min_length=1)
    source_kind: EvidenceSourceKind
    description: str = Field(min_length=1)
    required: bool = True
    minimum_record_count: int = Field(default=1, ge=0)


class EvidenceSourceRequest(BaseModel):
    source_id: str = Field(min_length=1)
    kind: EvidenceSourceKind
    display_name: str = Field(min_length=1)
    source_location: str | None = None


class EvidenceInputRequest(BaseModel):
    source: EvidenceSourceRequest
    csv_text: str = Field(min_length=1)


class AssessmentExecutionApiRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    client_id: str = Field(min_length=1)
    engagement_id: str = Field(min_length=1)
    assessment_id: str = Field(min_length=1)
    assessment_name: str = Field(min_length=1)
    workflow_names: list[str] = Field(min_length=1)
    organizational_units: list[str] = Field(min_length=1)
    period_start: date
    period_end: date
    objectives: list[str] = Field(min_length=1)
    expected_outcomes: list[str] = Field(min_length=1)
    evidence_requirements: list[
        EvidenceRequirementRequest
    ] = Field(min_length=1)
    evidence_inputs: list[EvidenceInputRequest] = Field(
        min_length=1
    )
    client_display_name: str = Field(min_length=1)
    prepared_by: str = Field(min_length=1)
    exclusions: list[str] = Field(default_factory=list)
    maximum_priorities: int = Field(default=3, ge=1)

    def to_application_request(self) -> AssessmentExecutionRequest:
        context = CommercialHierarchyContext(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            engagement_id=self.engagement_id,
            assessment_id=self.assessment_id,
        )

        requirements = tuple(
            EvidenceRequirement(
                requirement_id=item.requirement_id,
                source_kind=item.source_kind,
                description=item.description,
                required=item.required,
                minimum_record_count=item.minimum_record_count,
            )
            for item in self.evidence_requirements
        )

        evidence_inputs = tuple(
            DemonstrationEvidenceInput(
                source=EvidenceSourceReference(
                    source_id=item.source.source_id,
                    kind=item.source.kind,
                    display_name=item.source.display_name,
                    source_location=item.source.source_location,
                ),
                csv_text=item.csv_text,
            )
            for item in self.evidence_inputs
        )

        return AssessmentExecutionRequest(
            context=context,
            assessment_name=self.assessment_name,
            workflow_names=tuple(self.workflow_names),
            organizational_units=tuple(
                self.organizational_units
            ),
            period_start=self.period_start,
            period_end=self.period_end,
            objectives=tuple(self.objectives),
            expected_outcomes=tuple(self.expected_outcomes),
            evidence_requirements=requirements,
            evidence_inputs=evidence_inputs,
            client_display_name=self.client_display_name,
            prepared_by=self.prepared_by,
            exclusions=tuple(self.exclusions),
            maximum_priorities=self.maximum_priorities,
        )


def hierarchy_context(
    *,
    tenant_id: str,
    client_id: str,
    engagement_id: str,
    assessment_id: str,
) -> CommercialHierarchyContext:
    return CommercialHierarchyContext(
        tenant_id=tenant_id,
        client_id=client_id,
        engagement_id=engagement_id,
        assessment_id=assessment_id,
    )


def error_detail(
    *,
    code: str,
    message: str,
) -> dict[str, str]:
    return {
        "code": code,
        "message": message,
    }


def create_governance_assessment_router(
    *,
    service: GovernanceAssessmentApplicationService,
    execution_input_binding_service: (
        GovernanceCommercialPaidAssessmentExecutionInputBindingService
        | None
    ) = None,
    dependencies: list[Depends] | None = None,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/governance-assessments",
        tags=["governance-assessments"],
        dependencies=dependencies or [],
    )

    @router.post(
        "/execute",
        status_code=status.HTTP_201_CREATED,
    )
    def execute_assessment(
        request: AssessmentExecutionApiRequest,
    ) -> dict[str, Any]:
        try:
            application_request = (
                request.to_application_request()
            )

            if (
                execution_input_binding_service
                is not None
            ):
                execution_input_binding_service.bind(
                    request=application_request
                )

            result = service.execute(
                request=application_request
            )

            return result.to_dict()

        except (
            CommercialPaidAssessmentExecutionInputBindingError
        ) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_detail(
                    code=(
                        "ASSESSMENT_EXECUTION_INPUT_BINDING_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

        except AssessmentApplicationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=error_detail(
                    code="ASSESSMENT_APPLICATION_ERROR",
                    message=str(exc),
                ),
            ) from exc

        except AssessmentRepositoryError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_detail(
                    code="ASSESSMENT_REPOSITORY_ERROR",
                    message=str(exc),
                ),
            ) from exc

    @router.get(
        "/{tenant_id}/{client_id}/{engagement_id}/"
        "{assessment_id}",
    )
    def get_assessment(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> dict[str, Any]:
        context = hierarchy_context(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        try:
            return service.get_assessment(
                context=context
            ).to_dict()
        except AssessmentRecordNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_detail(
                    code="ASSESSMENT_NOT_FOUND",
                    message=str(exc),
                ),
            ) from exc

    @router.get("")
    def list_assessments(
        tenant_id: str,
        client_id: str | None = None,
        engagement_id: str | None = None,
    ) -> dict[str, Any]:
        try:
            assessments = service.list_assessments(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
            )
        except AssessmentRepositoryError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=error_detail(
                    code="ASSESSMENT_QUERY_ERROR",
                    message=str(exc),
                ),
            ) from exc

        return {
            "items": [
                assessment.to_dict()
                for assessment in assessments
            ],
            "count": len(assessments),
        }

    @router.get(
        "/{tenant_id}/{client_id}/{engagement_id}/"
        "{assessment_id}/artifacts",
    )
    def list_artifacts(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        artifact_type: str | None = None,
    ) -> dict[str, Any]:
        context = hierarchy_context(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        try:
            artifacts = service.list_artifacts(
                context=context,
                artifact_type=artifact_type,
            )
        except ArtifactIntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_detail(
                    code="ARTIFACT_INTEGRITY_ERROR",
                    message=str(exc),
                ),
            ) from exc

        return {
            "hierarchy_key": context.hierarchy_key,
            "items": [
                artifact.to_dict()
                for artifact in artifacts
            ],
            "count": len(artifacts),
        }

    @router.get(
        "/{tenant_id}/{client_id}/{engagement_id}/"
        "{assessment_id}/summary",
    )
    def summarize_assessment(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> dict[str, Any]:
        context = hierarchy_context(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        try:
            return service.summarize(
                context=context
            ).to_dict()
        except AssessmentRecordNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_detail(
                    code="ASSESSMENT_NOT_FOUND",
                    message=str(exc),
                ),
            ) from exc
        except ArtifactIntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_detail(
                    code="ARTIFACT_INTEGRITY_ERROR",
                    message=str(exc),
                ),
            ) from exc

    return router