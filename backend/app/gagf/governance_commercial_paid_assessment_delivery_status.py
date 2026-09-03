from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    DELIVERY_ARTIFACT_TYPE,
)


COMMERCIAL_PAID_ASSESSMENT_DELIVERY_STATUS_ID = (
    "governance-commercial-paid-assessment-delivery-status"
)
COMMERCIAL_PAID_ASSESSMENT_DELIVERY_STATUS_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_DELIVERY_STATUS_SCHEMA_VERSION = "1.0.0"


class CommercialPaidAssessmentDeliveryStatusError(ValueError):
    """Raised when the governed delivery-status projection is invalid."""


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentDeliveryStatus:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    found: bool
    delivery_recorded: bool
    delivery_status: str | None
    report_id: str | None
    delivered_by: str | None
    delivered_at: str | None
    delivery_method: str | None
    delivery_reference: str | None
    repository_chain_valid: bool
    status_type: str = (
        COMMERCIAL_PAID_ASSESSMENT_DELIVERY_STATUS_ID
    )
    version: str = (
        COMMERCIAL_PAID_ASSESSMENT_DELIVERY_STATUS_VERSION
    )
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_DELIVERY_STATUS_SCHEMA_VERSION
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
            "status_type": self.status_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "found": self.found,
            "delivery_recorded": self.delivery_recorded,
            "delivery_status": self.delivery_status,
            "report_id": self.report_id,
            "delivered_by": self.delivered_by,
            "delivered_at": self.delivered_at,
            "delivery_method": self.delivery_method,
            "delivery_reference": self.delivery_reference,
            "repository_chain_valid": (
                self.repository_chain_valid
            ),
            "boundaries": {
                "delivery_status_is_read_only_projection": True,
                "delivery_is_not_client_receipt": True,
                "delivery_is_not_client_acknowledgment": True,
                "delivery_is_not_client_response": True,
                "delivery_is_not_closeout": True,
                "delivery_is_not_intervention_authority": True,
                "repository_integrity_is_not_delivery_correctness": True,
            },
        }


class GovernanceCommercialPaidAssessmentDeliveryStatusService:
    """
    Reads durable paid-assessment delivery state from the existing
    PA012 lifecycle artifact chain.

    This service does not create approval, delivery, acknowledgment,
    client response, closeout, intervention authority, or outcome
    authority.
    """

    def __init__(
        self,
        *,
        execution_service: (
            GovernanceCommercialPaidAssessmentExecutionService
        ),
    ) -> None:
        if not isinstance(
            execution_service,
            GovernanceCommercialPaidAssessmentExecutionService,
        ):
            raise CommercialPaidAssessmentDeliveryStatusError(
                "execution_service must be a "
                "GovernanceCommercialPaidAssessmentExecutionService"
            )

        self._execution_service = execution_service

    def get_status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CommercialPaidAssessmentDeliveryStatus:
        hierarchy = self._validate_hierarchy(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        database_path = (
            self._execution_service.database_path_for_hierarchy(
                tenant_id=hierarchy.tenant_id,
                client_id=hierarchy.client_id,
                engagement_id=hierarchy.engagement_id,
                assessment_id=hierarchy.assessment_id,
            )
        )

        if not database_path.exists():
            return self._not_found(
                hierarchy=hierarchy,
            )

        if not database_path.is_file():
            raise CommercialPaidAssessmentDeliveryStatusError(
                "governed assessment database path is not a file"
            )

        try:
            repository = GovernanceAssessmentRepository(
                database_path
            )

            repository.get_assessment(
                context=hierarchy
            )

            if (
                repository.verify_chain(
                    context=hierarchy
                )
                is not True
            ):
                raise CommercialPaidAssessmentDeliveryStatusError(
                    "governed assessment repository chain is invalid"
                )

            delivery_artifacts = (
                repository.list_artifacts(
                    context=hierarchy,
                    artifact_type=DELIVERY_ARTIFACT_TYPE,
                )
            )

        except CommercialPaidAssessmentDeliveryStatusError:
            raise

        except Exception as exc:
            raise CommercialPaidAssessmentDeliveryStatusError(
                "governed delivery status could not be read: "
                f"{exc}"
            ) from exc

        if len(delivery_artifacts) == 0:
            return self._not_found(
                hierarchy=hierarchy,
                repository_chain_valid=True,
            )

        if len(delivery_artifacts) != 1:
            raise CommercialPaidAssessmentDeliveryStatusError(
                "expected exactly one persisted delivery artifact"
            )

        artifact = delivery_artifacts[0]
        payload = artifact.payload

        self._validate_delivery_payload(
            payload=payload,
            hierarchy=hierarchy,
        )

        return CommercialPaidAssessmentDeliveryStatus(
            tenant_id=hierarchy.tenant_id,
            client_id=hierarchy.client_id,
            engagement_id=hierarchy.engagement_id,
            assessment_id=hierarchy.assessment_id,
            found=True,
            delivery_recorded=True,
            delivery_status="delivered",
            report_id=self._require_payload_text(
                payload,
                "report_id",
            ),
            delivered_by=self._require_payload_text(
                payload,
                "delivered_by",
            ),
            delivered_at=self._require_payload_text(
                payload,
                "delivered_at",
            ),
            delivery_method=self._require_payload_text(
                payload,
                "delivery_method",
            ),
            delivery_reference=self._require_payload_text(
                payload,
                "delivery_reference",
            ),
            repository_chain_valid=True,
        )

    @staticmethod
    def _validate_hierarchy(
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CommercialHierarchyContext:
        values = (
            ("tenant_id", tenant_id),
            ("client_id", client_id),
            ("engagement_id", engagement_id),
            ("assessment_id", assessment_id),
        )

        normalized: dict[str, str] = {}

        for field_name, value in values:
            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise CommercialPaidAssessmentDeliveryStatusError(
                    f"{field_name} must be non-empty"
                )

            normalized[field_name] = value.strip()

        return CommercialHierarchyContext(
            tenant_id=normalized["tenant_id"],
            client_id=normalized["client_id"],
            engagement_id=normalized["engagement_id"],
            assessment_id=normalized["assessment_id"],
        )

    def _validate_delivery_payload(
        self,
        *,
        payload: dict[str, Any],
        hierarchy: CommercialHierarchyContext,
    ) -> None:
        if not isinstance(payload, dict):
            raise CommercialPaidAssessmentDeliveryStatusError(
                "persisted delivery payload must be an object"
            )

        expected = {
            "tenant_id": hierarchy.tenant_id,
            "client_id": hierarchy.client_id,
            "engagement_id": hierarchy.engagement_id,
            "assessment_id": hierarchy.assessment_id,
        }

        for field_name, expected_value in expected.items():
            actual = self._require_payload_text(
                payload,
                field_name,
            )

            if actual != expected_value:
                raise CommercialPaidAssessmentDeliveryStatusError(
                    "persisted delivery hierarchy mismatch: "
                    f"{field_name}"
                )

        delivery_status = self._require_payload_text(
            payload,
            "delivery_status",
        )

        if delivery_status != "delivered":
            raise CommercialPaidAssessmentDeliveryStatusError(
                "persisted delivery artifact must have "
                "delivery_status=delivered"
            )

        delivery_completed = payload.get(
            "delivery_completed"
        )

        if delivery_completed is not True:
            raise CommercialPaidAssessmentDeliveryStatusError(
                "persisted delivery artifact must have "
                "delivery_completed=true"
            )

        self._require_payload_text(
            payload,
            "report_id",
        )
        self._require_payload_text(
            payload,
            "delivered_by",
        )
        self._require_payload_text(
            payload,
            "delivered_at",
        )
        self._require_payload_text(
            payload,
            "delivery_method",
        )
        self._require_payload_text(
            payload,
            "delivery_reference",
        )

    @staticmethod
    def _require_payload_text(
        payload: dict[str, Any],
        field_name: str,
    ) -> str:
        value = payload.get(field_name)

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise CommercialPaidAssessmentDeliveryStatusError(
                f"persisted delivery {field_name} must be non-empty"
            )

        return value.strip()

    @staticmethod
    def _not_found(
        *,
        hierarchy: CommercialHierarchyContext,
        repository_chain_valid: bool = False,
    ) -> CommercialPaidAssessmentDeliveryStatus:
        return CommercialPaidAssessmentDeliveryStatus(
            tenant_id=hierarchy.tenant_id,
            client_id=hierarchy.client_id,
            engagement_id=hierarchy.engagement_id,
            assessment_id=hierarchy.assessment_id,
            found=False,
            delivery_recorded=False,
            delivery_status=None,
            report_id=None,
            delivered_by=None,
            delivered_at=None,
            delivery_method=None,
            delivery_reference=None,
            repository_chain_valid=repository_chain_valid,
        )