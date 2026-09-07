from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    ClientAssessmentReceiptAcknowledgment,
    GovernancePaidAssessmentClientAcknowledgmentService,
    GovernedPaidAssessmentClientAcknowledgment,
    PaidAssessmentClientAcknowledgmentError,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernedPaidAssessmentDeliveryEvent,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
    DELIVERY_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_paid_assessment_resumable_operator_runner import (
    GovernancePaidAssessmentResumableOperatorRunner,
    PaidAssessmentOperatorActionResult,
    PaidAssessmentResumableOperatorRunnerError,
)


COMMERCIAL_PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_ID = (
    "governance-commercial-paid-assessment-client-acknowledgment"
)
COMMERCIAL_PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_SCHEMA_VERSION = "1.0.0"


class CommercialPaidAssessmentClientAcknowledgmentError(ValueError):
    """Raised when commercial client receipt cannot be recorded safely."""


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentClientAcknowledgmentResult:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str
    acknowledgment_id: str
    acknowledged_by: str
    acknowledged_at: str
    acknowledgment_method: str
    acknowledgment_reference: str
    acknowledgment_status: str
    persistence_result: PaidAssessmentOperatorActionResult
    result_type: str = (
        COMMERCIAL_PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_ID
    )
    version: str = (
        COMMERCIAL_PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_VERSION
    )
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_SCHEMA_VERSION
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
            "result_type": self.result_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "report_id": self.report_id,
            "acknowledgment_id": self.acknowledgment_id,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at,
            "acknowledgment_method": self.acknowledgment_method,
            "acknowledgment_reference": self.acknowledgment_reference,
            "acknowledgment_status": self.acknowledgment_status,
            "client_receipt_acknowledged": True,
            "persistence_result": self.persistence_result.to_dict(),
            "boundaries": {
                "receipt_is_not_findings_acceptance": True,
                "receipt_is_not_recommendation_acceptance": True,
                "receipt_is_not_client_response": True,
                "receipt_is_not_closeout": True,
                "receipt_is_not_intervention_authority": True,
                "receipt_is_not_execution_authority": True,
                "receipt_is_not_roi_verification": True,
                "receipt_is_not_customer_outcome": True,
            },
        }


class GovernanceCommercialPaidAssessmentClientAcknowledgmentService:
    """
    Thin commercial adapter over the existing PA006 and PA012 authorities.

    Browser/operator input supplies only explicit receipt evidence.
    Delivery lineage is rehydrated server-side from the immutable assessment
    repository. The browser never supplies authoritative delivery hashes.
    """

    def __init__(
        self,
        *,
        execution_service: GovernanceCommercialPaidAssessmentExecutionService,
    ) -> None:
        if not isinstance(
            execution_service,
            GovernanceCommercialPaidAssessmentExecutionService,
        ):
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                "execution_service must be a "
                "GovernanceCommercialPaidAssessmentExecutionService"
            )

        self._execution_service = execution_service

    def record(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        acknowledgment_payload: dict[str, Any],
    ) -> CommercialPaidAssessmentClientAcknowledgmentResult:
        context = CommercialHierarchyContext(
            tenant_id=self._require_text(tenant_id, "tenant_id"),
            client_id=self._require_text(client_id, "client_id"),
            engagement_id=self._require_text(
                engagement_id,
                "engagement_id",
            ),
            assessment_id=self._require_text(
                assessment_id,
                "assessment_id",
            ),
        )

        if not isinstance(acknowledgment_payload, dict):
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                "acknowledgment_payload must be an object"
            )

        database_path = Path(
            self._execution_service.database_path_for_hierarchy(
                tenant_id=context.tenant_id,
                client_id=context.client_id,
                engagement_id=context.engagement_id,
                assessment_id=context.assessment_id,
            )
        )

        if not database_path.exists():
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                "paid assessment hierarchy database does not exist"
            )

        if not database_path.is_file():
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                "paid assessment hierarchy database path is not a file"
            )

        repository = GovernanceAssessmentRepository(
            database_path
        )

        repository.get_assessment(
            context=context
        )

        if repository.verify_chain(context=context) is not True:
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                "paid assessment repository chain is invalid"
            )

        artifacts = repository.list_artifacts(
            context=context
        )

        delivery_artifacts = [
            artifact
            for artifact in artifacts
            if artifact.artifact_type == DELIVERY_ARTIFACT_TYPE
        ]

        if len(delivery_artifacts) != 1:
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                "exactly one paid assessment delivery event is required"
            )

        existing_acknowledgments = [
            artifact
            for artifact in artifacts
            if artifact.artifact_type == ACKNOWLEDGMENT_ARTIFACT_TYPE
        ]

        if existing_acknowledgments:
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                "client receipt acknowledgment already exists"
            )

        try:
            delivery_payload = json.loads(
                delivery_artifacts[0].payload_json
            )
        except json.JSONDecodeError as exc:
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                "persisted delivery event payload is not valid JSON"
            ) from exc

        if not isinstance(delivery_payload, dict):
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                "persisted delivery event payload must be an object"
            )

        delivery_event = self._rehydrate_delivery_event(
            context=context,
            payload=delivery_payload,
        )

        try:
            acknowledgment = ClientAssessmentReceiptAcknowledgment(
                acknowledgment_id=self._require_text(
                    acknowledgment_payload.get("acknowledgment_id"),
                    "acknowledgment_id",
                ),
                tenant_id=context.tenant_id,
                client_id=context.client_id,
                engagement_id=context.engagement_id,
                assessment_id=context.assessment_id,
                report_id=delivery_event.report_id,
                delivery_event_id=delivery_event.delivery_event_id,
                delivery_event_hash=delivery_event.delivery_event_hash,
                acknowledged_by=self._require_text(
                    acknowledgment_payload.get("acknowledged_by"),
                    "acknowledged_by",
                ),
                acknowledged_at=self._require_text(
                    acknowledgment_payload.get("acknowledged_at"),
                    "acknowledged_at",
                ),
                acknowledgment_method=self._require_text(
                    acknowledgment_payload.get("acknowledgment_method"),
                    "acknowledgment_method",
                ),
                acknowledgment_reference=self._require_text(
                    acknowledgment_payload.get("acknowledgment_reference"),
                    "acknowledgment_reference",
                ),
                client_acknowledged_receipt=(
                    acknowledgment_payload.get(
                        "client_acknowledged_receipt"
                    )
                ),
            )

            governed_acknowledgment = (
                GovernancePaidAssessmentClientAcknowledgmentService()
                .record_acknowledgment(
                    delivery_event=delivery_event,
                    acknowledgment=acknowledgment,
                )
            )

            runner = GovernancePaidAssessmentResumableOperatorRunner(
                repository=repository
            )

            persistence_result = runner.record_client_receipt(
                client_acknowledgment=governed_acknowledgment
            )

        except (
            PaidAssessmentClientAcknowledgmentError,
            PaidAssessmentResumableOperatorRunnerError,
        ) as exc:
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                str(exc)
            ) from exc

        return self._build_result(
            acknowledgment=governed_acknowledgment,
            persistence_result=persistence_result,
        )

    def _rehydrate_delivery_event(
        self,
        *,
        context: CommercialHierarchyContext,
        payload: dict[str, Any],
    ) -> GovernedPaidAssessmentDeliveryEvent:
        self._require_payload_context(
            context=context,
            payload=payload,
        )

        return GovernedPaidAssessmentDeliveryEvent(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=context.engagement_id,
            assessment_id=context.assessment_id,
            report_id=self._require_text(
                payload.get("report_id"),
                "delivery.report_id",
            ),
            delivery_envelope_hash=self._require_hash(
                payload.get("delivery_envelope_hash"),
                "delivery.delivery_envelope_hash",
            ),
            delivery_approval_hash=self._require_hash(
                payload.get("delivery_approval_hash"),
                "delivery.delivery_approval_hash",
            ),
            human_delivery_confirmation_hash=self._require_hash(
                payload.get("human_delivery_confirmation_hash"),
                "delivery.human_delivery_confirmation_hash",
            ),
            delivery_event_id=self._require_text(
                payload.get("delivery_event_id"),
                "delivery.delivery_event_id",
            ),
            delivered_by=self._require_text(
                payload.get("delivered_by"),
                "delivery.delivered_by",
            ),
            delivered_at=self._require_text(
                payload.get("delivered_at"),
                "delivery.delivered_at",
            ),
            delivery_method=self._require_text(
                payload.get("delivery_method"),
                "delivery.delivery_method",
            ),
            delivery_reference=self._require_text(
                payload.get("delivery_reference"),
                "delivery.delivery_reference",
            ),
            delivery_status=self._require_text(
                payload.get("delivery_status"),
                "delivery.delivery_status",
            ),
            delivery_event_hash=self._require_hash(
                payload.get("delivery_event_hash"),
                "delivery.delivery_event_hash",
            ),
        )

    def _build_result(
        self,
        *,
        acknowledgment: GovernedPaidAssessmentClientAcknowledgment,
        persistence_result: PaidAssessmentOperatorActionResult,
    ) -> CommercialPaidAssessmentClientAcknowledgmentResult:
        return CommercialPaidAssessmentClientAcknowledgmentResult(
            tenant_id=acknowledgment.tenant_id,
            client_id=acknowledgment.client_id,
            engagement_id=acknowledgment.engagement_id,
            assessment_id=acknowledgment.assessment_id,
            report_id=acknowledgment.report_id,
            acknowledgment_id=acknowledgment.acknowledgment_id,
            acknowledged_by=acknowledgment.acknowledged_by,
            acknowledged_at=acknowledgment.acknowledged_at,
            acknowledgment_method=(
                acknowledgment.acknowledgment_method
            ),
            acknowledgment_reference=(
                acknowledgment.acknowledgment_reference
            ),
            acknowledgment_status=(
                acknowledgment.acknowledgment_status
            ),
            persistence_result=persistence_result,
        )

    def _require_payload_context(
        self,
        *,
        context: CommercialHierarchyContext,
        payload: dict[str, Any],
    ) -> None:
        expected = {
            "tenant_id": context.tenant_id,
            "client_id": context.client_id,
            "engagement_id": context.engagement_id,
            "assessment_id": context.assessment_id,
        }

        for field_name, expected_value in expected.items():
            actual = self._require_text(
                payload.get(field_name),
                f"delivery.{field_name}",
            )

            if actual != expected_value:
                raise CommercialPaidAssessmentClientAcknowledgmentError(
                    f"persisted delivery {field_name} does not "
                    "match assessment hierarchy"
                )

    def _require_text(
        self,
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                f"{field_name} must be a string"
            )

        value = value.strip()

        if not value:
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                f"{field_name} must not be empty"
            )

        return value

    def _require_hash(
        self,
        value: Any,
        field_name: str,
    ) -> str:
        value = self._require_text(
            value,
            field_name,
        )

        if len(value) != 64:
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                f"{field_name} must be a 64-character SHA-256 hash"
            )

        try:
            int(value, 16)
        except ValueError as exc:
            raise CommercialPaidAssessmentClientAcknowledgmentError(
                f"{field_name} must be hexadecimal"
            ) from exc

        return value.lower()
