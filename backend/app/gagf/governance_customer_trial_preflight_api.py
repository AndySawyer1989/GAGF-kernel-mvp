from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from pydantic import (
    BaseModel,
    Field,
)

from backend.app.gagf.governance_customer_trial_engagement_package import (
    CustomerTrialEngagementPackage,
    CustomerTrialEvidenceRequirement,
)
from backend.app.gagf.governance_customer_trial_preflight_receipt_store import (
    CustomerTrialPreflightReceiptStoreError,
)
from backend.app.gagf.governance_customer_trial_preflight_service import (
    GovernanceCustomerTrialPreflightService,
)


CUSTOMER_TRIAL_PREFLIGHT_API_VERSION = "1.0.0"

CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX = (
    "/api/v1/governance-customer-trials"
)

CUSTOMER_TRIAL_PREFLIGHT_API_TAG = (
    "governance-customer-trials"
)


def _error_detail(
    *,
    code: str,
    message: str,
) -> dict[str, str]:
    return {
        "code": code,
        "message": message,
    }


class CustomerTrialEvidenceRequirementApiRequest(
    BaseModel
):
    requirement_id: str = Field(
        min_length=1
    )

    description: str = Field(
        min_length=1
    )

    minimum_records: int = Field(
        ge=1
    )

    accepted_formats: list[str] = Field(
        min_length=1
    )

    def to_domain(
        self,
    ) -> CustomerTrialEvidenceRequirement:
        return CustomerTrialEvidenceRequirement(
            requirement_id=(
                self.requirement_id
            ),
            description=self.description,
            minimum_records=(
                self.minimum_records
            ),
            accepted_formats=tuple(
                self.accepted_formats
            ),
        )


class CustomerTrialPreflightApiRequest(
    BaseModel
):
    tenant_id: str = Field(
        min_length=1
    )

    client_id: str = Field(
        min_length=1
    )

    client_display_name: str = Field(
        min_length=1
    )

    engagement_id: str = Field(
        min_length=1
    )

    assessment_id: str = Field(
        min_length=1
    )

    assessment_name: str = Field(
        min_length=1
    )

    period_start: str = Field(
        min_length=1
    )

    period_end: str = Field(
        min_length=1
    )

    workflows: list[str] = Field(
        min_length=1
    )

    organizational_units: list[str] = Field(
        min_length=1
    )

    objectives: list[str] = Field(
        min_length=1
    )

    expected_outcomes: list[str] = Field(
        min_length=1
    )

    evidence_requirements: list[
        CustomerTrialEvidenceRequirementApiRequest
    ] = Field(
        min_length=1
    )

    data_classification: str = Field(
        min_length=1
    )

    prepared_by: str = Field(
        min_length=1
    )

    customer_deliverables: list[str] = Field(
        min_length=1
    )

    trial_boundaries: list[str] = Field(
        min_length=1
    )

    completion_criteria: list[str] = Field(
        min_length=1
    )

    evaluated_at: str | None = None

    def to_domain(
        self,
    ) -> CustomerTrialEngagementPackage:
        return CustomerTrialEngagementPackage(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_display_name=(
                self.client_display_name
            ),
            engagement_id=(
                self.engagement_id
            ),
            assessment_id=(
                self.assessment_id
            ),
            assessment_name=(
                self.assessment_name
            ),
            period_start=self.period_start,
            period_end=self.period_end,
            workflows=tuple(
                self.workflows
            ),
            organizational_units=tuple(
                self.organizational_units
            ),
            objectives=tuple(
                self.objectives
            ),
            expected_outcomes=tuple(
                self.expected_outcomes
            ),
            evidence_requirements=tuple(
                requirement.to_domain()
                for requirement
                in self.evidence_requirements
            ),
            data_classification=(
                self.data_classification
            ),
            prepared_by=self.prepared_by,
            customer_deliverables=tuple(
                self.customer_deliverables
            ),
            trial_boundaries=tuple(
                self.trial_boundaries
            ),
            completion_criteria=tuple(
                self.completion_criteria
            ),
        )


def create_customer_trial_preflight_router(
    *,
    service:
        GovernanceCustomerTrialPreflightService,
) -> APIRouter:
    """
    Expose controlled customer-trial preflight.

    Constitutional boundary:

    This API may validate and persist trial
    readiness only.

    It does not authorize:
    - paid assessment execution
    - delivery approval
    - delivery
    - client acknowledgment
    - client response
    - administrative closeout
    - intervention
    """

    router = APIRouter(
        prefix=(
            CUSTOMER_TRIAL_PREFLIGHT_API_PREFIX
        ),
        tags=[
            CUSTOMER_TRIAL_PREFLIGHT_API_TAG
        ],
    )

    @router.post(
        "/preflight",
        status_code=(
            status.HTTP_201_CREATED
        ),
    )
    def execute_preflight(
        request:
            CustomerTrialPreflightApiRequest,
    ) -> dict[str, Any]:
        try:
            package = request.to_domain()

            result = service.execute(
                package=package,
                evaluated_at=(
                    request.evaluated_at
                ),
            )

            return {
                "api_version": (
                    CUSTOMER_TRIAL_PREFLIGHT_API_VERSION
                ),
                "operation": "preflight",
                "authority": (
                    "READINESS_ONLY"
                ),
                "result": result.to_dict(),
            }

        except ValueError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_CONTENT
                ),
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "PREFLIGHT_VALIDATION_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

        except (
            CustomerTrialPreflightReceiptStoreError
        ) as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "PREFLIGHT_RECEIPT_CONFLICT"
                    ),
                    message=str(exc),
                ),
            ) from exc

    @router.get(
        (
            "/{tenant_id}/{client_id}/"
            "{engagement_id}/{assessment_id}/"
            "preflight-status"
        ),
        status_code=status.HTTP_200_OK,
    )
    def get_preflight_status(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> dict[str, Any]:
        try:
            result = service.status(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=(
                    engagement_id
                ),
                assessment_id=(
                    assessment_id
                ),
            )

            return {
                "api_version": (
                    CUSTOMER_TRIAL_PREFLIGHT_API_VERSION
                ),
                "operation": (
                    "preflight-status"
                ),
                "authority": (
                    "READ_ONLY"
                ),
                "result": result.to_dict(),
            }

        except (
            CustomerTrialPreflightReceiptStoreError
        ) as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=_error_detail(
                    code=(
                        "CUSTOMER_TRIAL_"
                        "PREFLIGHT_STATUS_ERROR"
                    ),
                    message=str(exc),
                ),
            ) from exc

    return router