from __future__ import annotations

from typing import Any, Protocol

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from backend.app.gagf.governance_commercial_paid_assessment_delivery_approval_handoff import (
    CommercialPaidAssessmentDeliveryApprovalHandoffError,
    GovernanceCommercialPaidAssessmentDeliveryApprovalHandoffService,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_readiness import (
    CommercialPaidAssessmentDeliveryReadinessError,
    GovernanceCommercialPaidAssessmentDeliveryReadinessService,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_recording import (
    CommercialPaidAssessmentDeliveryRecordingError,
    GovernanceCommercialPaidAssessmentDeliveryRecordingService,
)
from backend.app.gagf.governance_commercial_paid_assessment_delivery_status import (
    CommercialPaidAssessmentDeliveryStatusError,
    GovernanceCommercialPaidAssessmentDeliveryStatusService,
)
from backend.app.gagf.governance_commercial_paid_assessment_lifecycle_status import (
    CommercialPaidAssessmentLifecycleStatusError,
    GovernanceCommercialPaidAssessmentLifecycleStatusService,
)
from backend.app.gagf.governance_commercial_paid_assessment_client_acknowledgment import (
    CommercialPaidAssessmentClientAcknowledgmentError,
    GovernanceCommercialPaidAssessmentClientAcknowledgmentService,
)
from backend.app.gagf.governance_commercial_paid_assessment_client_response import (
    CommercialPaidAssessmentClientResponseError,
    GovernanceCommercialPaidAssessmentClientResponseService,
)


COMMERCIAL_PAID_ASSESSMENT_DELIVERY_API_ID = (
    "governance-commercial-paid-assessment-delivery-api"
)
COMMERCIAL_PAID_ASSESSMENT_DELIVERY_API_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_DELIVERY_API_SCHEMA_VERSION = "1.0.0"

DELIVERY_API_PREFIX = "/api/v1/governance-paid-assessments"


class DeliveryReadinessService(Protocol):
    def verify(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> Any:
        ...


class DeliveryStatusService(Protocol):
    def get_status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> Any:
        ...


class LifecycleStatusService(Protocol):
    def get_status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> Any:
        ...


class ClientResponseService(Protocol):
    def record(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        response_payload: dict[str, Any],
    ) -> Any:
        ...


class ClientAcknowledgmentService(Protocol):
    def record(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        acknowledgment_payload: dict[str, Any],
    ) -> Any:
        ...


class DeliveryApprovalService(Protocol):
    def handoff(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        approval_payload: dict[str, Any],
    ) -> Any:
        ...


class DeliveryRecordingService(Protocol):
    def record(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        human_confirmation_payload: dict[str, Any],
    ) -> Any:
        ...


class ClientResponseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    response_id: str
    responded_by: str
    responded_at: str
    response_method: str
    response_reference: str
    findings_disposition: str
    recommendations_disposition: str
    response_note: str = ""


class ClientAcknowledgmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acknowledgment_id: str
    acknowledged_by: str
    acknowledged_at: str
    acknowledgment_method: str
    acknowledgment_reference: str
    client_acknowledged_receipt: bool


class DeliveryApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str
    approved_by: str
    approved_at: str
    scope_approved: bool
    evidence_boundary_approved: bool
    buyer_language_approved: bool
    delivery_approved: bool


class HumanDeliveryConfirmationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    delivery_event_id: str
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str
    delivered_by: str
    delivered_at: str
    delivery_method: str
    delivery_reference: str
    delivery_completed: bool


def create_governance_commercial_paid_assessment_delivery_router(
    *,
    readiness_service: DeliveryReadinessService,
    approval_service: DeliveryApprovalService,
    recording_service: DeliveryRecordingService,
    status_service: DeliveryStatusService,
    lifecycle_status_service: LifecycleStatusService,
    client_acknowledgment_service: ClientAcknowledgmentService,
    client_response_service: ClientResponseService,
) -> APIRouter:
    """
    Thin HTTP adapter over the already-authoritative 04F services.

    This router is not readiness, approval, delivery-event, recovery, or
    execution authority. It only validates the browser/API request shape and
    delegates to the governed services.
    """
    router = APIRouter(
        prefix=DELIVERY_API_PREFIX,
        tags=["governance-paid-assessment-delivery"],
    )

    hierarchy_path = (
        "/{tenant_id}/{client_id}/{engagement_id}/{assessment_id}"
    )

    @router.get(
        hierarchy_path + "/delivery-status",
    )
    def get_delivery_status(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> dict[str, Any]:
        try:
            result = status_service.get_status(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
            )
        except CommercialPaidAssessmentDeliveryStatusError as exc:
            raise HTTPException(
                status_code=409,
                detail=str(exc),
            ) from exc

        return _safe_result_dict(result)

    @router.get(
        hierarchy_path + "/lifecycle-status",
    )
    def get_lifecycle_status(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> dict[str, Any]:
        try:
            result = lifecycle_status_service.get_status(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
            )
        except CommercialPaidAssessmentLifecycleStatusError as exc:
            raise HTTPException(
                status_code=409,
                detail=str(exc),
            ) from exc

        return _safe_result_dict(result)

    @router.post(
        hierarchy_path + "/client-acknowledgment",
    )
    def post_client_acknowledgment(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        request: ClientAcknowledgmentRequest,
    ) -> dict[str, Any]:
        payload = request.model_dump()

        try:
            result = client_acknowledgment_service.record(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
                acknowledgment_payload=payload,
            )
        except CommercialPaidAssessmentClientAcknowledgmentError as exc:
            raise HTTPException(
                status_code=409,
                detail=str(exc),
            ) from exc

        return _safe_result_dict(result)

    @router.post(
        hierarchy_path + "/client-response",
    )
    def post_client_response(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        request: ClientResponseRequest,
    ) -> dict[str, Any]:
        try:
            result = client_response_service.record(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
                response_payload=request.model_dump(),
            )
        except CommercialPaidAssessmentClientResponseError as exc:
            raise HTTPException(
                status_code=409,
                detail=str(exc),
            ) from exc

        return _safe_result_dict(result)

    @router.get(
        hierarchy_path + "/delivery-readiness",
    )
    def get_delivery_readiness(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> dict[str, Any]:
        try:
            result = readiness_service.verify(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
            )
        except CommercialPaidAssessmentDeliveryReadinessError as exc:
            message = str(exc)
            status_code = (
                404
                if (
                    "snapshot was not found" in message
                    or "execution status was not found" in message
                )
                else 409
            )
            raise HTTPException(
                status_code=status_code,
                detail=message,
            ) from exc

        return _safe_result_dict(result)

    @router.post(
        hierarchy_path + "/delivery-approval",
    )
    def post_delivery_approval(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        request: DeliveryApprovalRequest,
    ) -> dict[str, Any]:
        payload = request.model_dump()

        _require_payload_hierarchy_matches_path(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            payload=payload,
        )

        try:
            result = approval_service.handoff(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
                approval_payload=payload,
            )
        except CommercialPaidAssessmentDeliveryApprovalHandoffError as exc:
            message = str(exc)
            status_code = (
                404
                if "snapshot was not found" in message
                else 409
            )
            raise HTTPException(
                status_code=status_code,
                detail=message,
            ) from exc

        return _safe_result_dict(result)

    @router.post(
        hierarchy_path + "/delivery-recording",
    )
    def post_delivery_recording(
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        request: HumanDeliveryConfirmationRequest,
    ) -> dict[str, Any]:
        payload = request.model_dump()

        _require_payload_hierarchy_matches_path(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            payload=payload,
        )

        try:
            result = recording_service.record(
                tenant_id=tenant_id,
                client_id=client_id,
                engagement_id=engagement_id,
                assessment_id=assessment_id,
                human_confirmation_payload=payload,
            )
        except CommercialPaidAssessmentDeliveryRecordingError as exc:
            message = str(exc)
            status_code = (
                404
                if "snapshot was not found" in message
                else 409
            )
            raise HTTPException(
                status_code=status_code,
                detail=message,
            ) from exc

        return _safe_result_dict(result)

    return router


def build_governance_commercial_paid_assessment_delivery_router(
    *,
    readiness_service: GovernanceCommercialPaidAssessmentDeliveryReadinessService,
    approval_service: GovernanceCommercialPaidAssessmentDeliveryApprovalHandoffService,
    recording_service: GovernanceCommercialPaidAssessmentDeliveryRecordingService,
    status_service: GovernanceCommercialPaidAssessmentDeliveryStatusService,
    lifecycle_status_service: GovernanceCommercialPaidAssessmentLifecycleStatusService,
    client_acknowledgment_service: GovernanceCommercialPaidAssessmentClientAcknowledgmentService,
    client_response_service: GovernanceCommercialPaidAssessmentClientResponseService,
) -> APIRouter:
    """
    Production-typed wrapper used by application registration.
    """
    if not isinstance(
        readiness_service,
        GovernanceCommercialPaidAssessmentDeliveryReadinessService,
    ):
        raise TypeError(
            "readiness_service must be a "
            "GovernanceCommercialPaidAssessmentDeliveryReadinessService"
        )

    if not isinstance(
        approval_service,
        GovernanceCommercialPaidAssessmentDeliveryApprovalHandoffService,
    ):
        raise TypeError(
            "approval_service must be a "
            "GovernanceCommercialPaidAssessmentDeliveryApprovalHandoffService"
        )

    if not isinstance(
        status_service,
        GovernanceCommercialPaidAssessmentDeliveryStatusService,
    ):
        raise TypeError(
            "status_service must be a "
            "GovernanceCommercialPaidAssessmentDeliveryStatusService"
        )

    if not isinstance(
        lifecycle_status_service,
        GovernanceCommercialPaidAssessmentLifecycleStatusService,
    ):
        raise TypeError(
            "lifecycle_status_service must be a "
            "GovernanceCommercialPaidAssessmentLifecycleStatusService"
        )

    if not isinstance(
        client_response_service,
        GovernanceCommercialPaidAssessmentClientResponseService,
    ):
        raise TypeError(
            "client_response_service must be a "
            "GovernanceCommercialPaidAssessmentClientResponseService"
        )

    if not isinstance(
        client_acknowledgment_service,
        GovernanceCommercialPaidAssessmentClientAcknowledgmentService,
    ):
        raise TypeError(
            "client_acknowledgment_service must be a "
            "GovernanceCommercialPaidAssessmentClientAcknowledgmentService"
        )

    if not isinstance(
        recording_service,
        GovernanceCommercialPaidAssessmentDeliveryRecordingService,
    ):
        raise TypeError(
            "recording_service must be a "
            "GovernanceCommercialPaidAssessmentDeliveryRecordingService"
        )

    return create_governance_commercial_paid_assessment_delivery_router(
        readiness_service=readiness_service,
        approval_service=approval_service,
        recording_service=recording_service,
        status_service=status_service,
        lifecycle_status_service=lifecycle_status_service,
        client_acknowledgment_service=client_acknowledgment_service,
        client_response_service=client_response_service,
    )


def _safe_result_dict(result: Any) -> dict[str, Any]:
    if not hasattr(result, "to_dict"):
        raise HTTPException(
            status_code=500,
            detail="governed delivery service returned invalid result",
        )

    payload = result.to_dict()

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=500,
            detail="governed delivery result must serialize to an object",
        )

    return payload


def _require_payload_hierarchy_matches_path(
    *,
    tenant_id: str,
    client_id: str,
    engagement_id: str,
    assessment_id: str,
    payload: dict[str, Any],
) -> None:
    expected = {
        "tenant_id": tenant_id,
        "client_id": client_id,
        "engagement_id": engagement_id,
        "assessment_id": assessment_id,
    }

    for field_name, expected_value in expected.items():
        if payload.get(field_name) != expected_value:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"{field_name} does not match request path"
                ),
            )
