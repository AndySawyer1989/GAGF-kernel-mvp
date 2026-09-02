from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_commercial_paid_assessment_approved_delivery_store import (
    CommercialPaidAssessmentApprovedDeliveryStoreError,
    GovernanceCommercialPaidAssessmentApprovedDeliveryStore,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_real_paid_assessment_delivery_recording import (
    GovernanceRealPaidAssessmentDeliveryRecordingService,
    RealPaidAssessmentDeliveryRecordingError,
    RealPaidAssessmentDeliveryRecordingResult,
)


COMMERCIAL_PAID_ASSESSMENT_DELIVERY_RECORDING_ID = (
    "governance-commercial-paid-assessment-delivery-recording"
)
COMMERCIAL_PAID_ASSESSMENT_DELIVERY_RECORDING_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_DELIVERY_RECORDING_SCHEMA_VERSION = "1.0.0"

COMMERCIAL_PAID_ASSESSMENT_APPROVED_DELIVERY_DATABASE = (
    "commercial-paid-assessment-approved-deliveries.sqlite3"
)


class CommercialPaidAssessmentDeliveryRecordingError(RuntimeError):
    """Raised when governed commercial delivery cannot be recorded safely."""


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentDeliveryRecording:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    approved_delivery_snapshot_hash: str
    recording: RealPaidAssessmentDeliveryRecordingResult

    result_type: str = COMMERCIAL_PAID_ASSESSMENT_DELIVERY_RECORDING_ID
    version: str = COMMERCIAL_PAID_ASSESSMENT_DELIVERY_RECORDING_VERSION
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_DELIVERY_RECORDING_SCHEMA_VERSION
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
        event = self.recording.delivery_event
        confirmation = self.recording.human_confirmation

        return {
            "result_type": self.result_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "delivery_status": self.recording.delivery_status,
            "delivery_recorded": True,
            "delivery_event_id": event.delivery_event_id,
            "delivery_event_hash": event.delivery_event_hash,
            "report_id": event.report_id,
            "delivered_by": event.delivered_by,
            "delivered_at": event.delivered_at,
            "delivery_method": event.delivery_method,
            "delivery_reference": event.delivery_reference,
            "human_delivery_confirmation_hash": (
                confirmation.confirmation_hash
            ),
            "approved_delivery_snapshot_hash": (
                self.approved_delivery_snapshot_hash
            ),
            "boundaries": {
                "approval_is_not_delivery": True,
                "human_confirmation_is_required_for_delivery": True,
                "human_confirmation_is_not_delivery_event_authority": True,
                "existing_real_delivery_recording_is_authoritative": True,
                "pa005_remains_delivery_event_authority": True,
                "pa013_remains_operator_coordination_authority": True,
                "pa012_remains_lifecycle_persistence_authority": True,
                "delivery_is_not_client_receipt": True,
                "delivery_is_not_client_acknowledgment": True,
                "delivery_is_not_client_acceptance": True,
                "delivery_is_not_customer_outcome": True,
                "approved_delivery_payload_not_exposed": True,
            },
        }


class GovernanceCommercialPaidAssessmentDeliveryRecordingService:
    """
    Restart-safe commercial bridge into existing governed delivery recording.

    The exact approved PA003 handoff is loaded from durable commercial state.
    The browser or caller supplies only the separate human-delivery
    confirmation. The assessment database path remains server-controlled.

    This service does not infer delivery from approval and does not create
    client receipt, acknowledgment, acceptance, or customer outcome.
    """

    def __init__(
        self,
        *,
        execution_service: GovernanceCommercialPaidAssessmentExecutionService,
        approved_delivery_store: (
            GovernanceCommercialPaidAssessmentApprovedDeliveryStore | None
        ) = None,
        recording_service: (
            GovernanceRealPaidAssessmentDeliveryRecordingService | None
        ) = None,
    ) -> None:
        if not isinstance(
            execution_service,
            GovernanceCommercialPaidAssessmentExecutionService,
        ):
            raise CommercialPaidAssessmentDeliveryRecordingError(
                "execution_service must be a "
                "GovernanceCommercialPaidAssessmentExecutionService"
            )

        self._execution_service = execution_service

        self._approved_delivery_store = (
            approved_delivery_store
            if approved_delivery_store is not None
            else GovernanceCommercialPaidAssessmentApprovedDeliveryStore(
                Path(execution_service.execution_directory)
                / COMMERCIAL_PAID_ASSESSMENT_APPROVED_DELIVERY_DATABASE
            )
        )

        self._recording_service = (
            recording_service
            if recording_service is not None
            else GovernanceRealPaidAssessmentDeliveryRecordingService()
        )

    def record(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        human_confirmation_payload: dict[str, Any],
    ) -> CommercialPaidAssessmentDeliveryRecording:
        hierarchy = self._validate_hierarchy(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        if not isinstance(human_confirmation_payload, dict):
            raise CommercialPaidAssessmentDeliveryRecordingError(
                "human_confirmation_payload must be an object"
            )

        try:
            approved = self._approved_delivery_store.get(
                tenant_id=hierarchy[0],
                client_id=hierarchy[1],
                engagement_id=hierarchy[2],
                assessment_id=hierarchy[3],
            )
        except CommercialPaidAssessmentApprovedDeliveryStoreError as exc:
            raise CommercialPaidAssessmentDeliveryRecordingError(
                "durable approved-delivery snapshot is invalid: "
                f"{exc}"
            ) from exc

        if approved is None:
            raise CommercialPaidAssessmentDeliveryRecordingError(
                "durable approved-delivery snapshot was not found"
            )

        expected_hierarchy_key = "/".join(hierarchy)

        if approved.hierarchy_key != expected_hierarchy_key:
            raise CommercialPaidAssessmentDeliveryRecordingError(
                "approved-delivery snapshot hierarchy mismatch"
            )

        current_status = self._execution_service.status_store.get_status(
            tenant_id=hierarchy[0],
            client_id=hierarchy[1],
            engagement_id=hierarchy[2],
            assessment_id=hierarchy[3],
        )

        if current_status is None:
            raise CommercialPaidAssessmentDeliveryRecordingError(
                "durable commercial paid execution status was not found"
            )

        if approved.execution_status_hash != current_status.status_hash:
            raise CommercialPaidAssessmentDeliveryRecordingError(
                "approved-delivery snapshot is not bound to current "
                "durable execution status"
            )

        database_path = (
            self._execution_service.database_path_for_hierarchy(
                tenant_id=hierarchy[0],
                client_id=hierarchy[1],
                engagement_id=hierarchy[2],
                assessment_id=hierarchy[3],
            )
        )

        try:
            recording = self._recording_service.record(
                database_path=database_path,
                approved_delivery_payload=(
                    approved.approved_delivery_payload
                ),
                human_confirmation_payload=human_confirmation_payload,
            )
        except RealPaidAssessmentDeliveryRecordingError as exc:
            raise CommercialPaidAssessmentDeliveryRecordingError(
                "governed paid-assessment delivery recording failed: "
                f"{exc}"
            ) from exc

        if recording.hierarchy_key != expected_hierarchy_key:
            raise CommercialPaidAssessmentDeliveryRecordingError(
                "delivery recording hierarchy mismatch"
            )

        if recording.delivery_status != "delivered":
            raise CommercialPaidAssessmentDeliveryRecordingError(
                "delivery recording did not produce delivered status"
            )

        return CommercialPaidAssessmentDeliveryRecording(
            tenant_id=hierarchy[0],
            client_id=hierarchy[1],
            engagement_id=hierarchy[2],
            assessment_id=hierarchy[3],
            approved_delivery_snapshot_hash=approved.snapshot_hash,
            recording=recording,
        )

    @staticmethod
    def _validate_hierarchy(
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> tuple[str, str, str, str]:
        values = (
            tenant_id,
            client_id,
            engagement_id,
            assessment_id,
        )

        normalized: list[str] = []

        for name, value in zip(
            (
                "tenant_id",
                "client_id",
                "engagement_id",
                "assessment_id",
            ),
            values,
            strict=True,
        ):
            if not isinstance(value, str) or not value.strip():
                raise CommercialPaidAssessmentDeliveryRecordingError(
                    f"{name} must be non-empty"
                )
            normalized.append(value.strip())

        return (
            normalized[0],
            normalized[1],
            normalized[2],
            normalized[3],
        )
