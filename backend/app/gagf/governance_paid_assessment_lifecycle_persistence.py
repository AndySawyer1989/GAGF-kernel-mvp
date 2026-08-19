from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
    ImmutableAssessmentArtifact,
)
from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    GovernedPaidAssessmentClientAcknowledgment,
)
from backend.app.gagf.governance_paid_assessment_client_response import (
    GovernedPaidAssessmentClientResponse,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernedPaidAssessmentDeliveryEvent,
)


PAID_ASSESSMENT_LIFECYCLE_PERSISTENCE_ID = (
    "governance-paid-assessment-lifecycle-persistence"
)
PAID_ASSESSMENT_LIFECYCLE_PERSISTENCE_VERSION = "0.1.0"
PAID_ASSESSMENT_LIFECYCLE_PERSISTENCE_SCHEMA_VERSION = "1.0.0"

DELIVERY_ARTIFACT_TYPE = "paid-assessment-delivery-event"
ACKNOWLEDGMENT_ARTIFACT_TYPE = "paid-assessment-client-acknowledgment"
CLIENT_RESPONSE_ARTIFACT_TYPE = "paid-assessment-client-response"


class PaidAssessmentLifecyclePersistenceError(ValueError):
    """Raised when paid-assessment lifecycle persistence is invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_hash(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise PaidAssessmentLifecyclePersistenceError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if len(normalized) != 64:
        raise PaidAssessmentLifecyclePersistenceError(
            f"{field_name} must be a SHA-256 hex digest"
        )

    try:
        int(normalized, 16)
    except ValueError as exc:
        raise PaidAssessmentLifecyclePersistenceError(
            f"{field_name} must be a SHA-256 hex digest"
        ) from exc

    return normalized


@dataclass(frozen=True, slots=True)
class PaidAssessmentLifecyclePersistenceReceipt:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    delivery_artifact_id: str
    delivery_artifact_hash: str
    acknowledgment_artifact_id: str
    acknowledgment_artifact_hash: str
    response_artifact_id: str
    response_artifact_hash: str
    first_sequence_number: int
    last_sequence_number: int
    repository_chain_valid: bool
    lifecycle_hash: str
    persistence_type: str = (
        PAID_ASSESSMENT_LIFECYCLE_PERSISTENCE_ID
    )
    version: str = PAID_ASSESSMENT_LIFECYCLE_PERSISTENCE_VERSION
    schema_version: str = (
        PAID_ASSESSMENT_LIFECYCLE_PERSISTENCE_SCHEMA_VERSION
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
            "persistence_type": self.persistence_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "delivery_artifact_id": self.delivery_artifact_id,
            "delivery_artifact_hash": self.delivery_artifact_hash,
            "acknowledgment_artifact_id": (
                self.acknowledgment_artifact_id
            ),
            "acknowledgment_artifact_hash": (
                self.acknowledgment_artifact_hash
            ),
            "response_artifact_id": self.response_artifact_id,
            "response_artifact_hash": self.response_artifact_hash,
            "first_sequence_number": self.first_sequence_number,
            "last_sequence_number": self.last_sequence_number,
            "repository_chain_valid": self.repository_chain_valid,
            "lifecycle_hash": self.lifecycle_hash,
        }


class GovernancePaidAssessmentLifecyclePersistenceService:
    """
    Persists the post-execution governed paid-assessment lifecycle into the
    existing GovernanceAssessmentRepository immutable artifact chain.

    Persistence does not create approval, delivery, acknowledgment,
    recommendation acceptance, intervention authority, causal authority,
    ROI authority, remediation-success authority, or verified outcome
    authority.
    """

    def persist_lifecycle(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        delivery_event: GovernedPaidAssessmentDeliveryEvent,
        client_acknowledgment: (
            GovernedPaidAssessmentClientAcknowledgment
        ),
        client_response: GovernedPaidAssessmentClientResponse,
        created_at: datetime | None = None,
    ) -> PaidAssessmentLifecyclePersistenceReceipt:
        if not isinstance(
            repository,
            GovernanceAssessmentRepository,
        ):
            raise PaidAssessmentLifecyclePersistenceError(
                "repository must be a GovernanceAssessmentRepository"
            )

        self._validate_delivery_event(delivery_event)
        self._validate_acknowledgment(
            delivery_event=delivery_event,
            client_acknowledgment=client_acknowledgment,
        )
        self._validate_client_response(
            client_acknowledgment=client_acknowledgment,
            client_response=client_response,
        )

        context = CommercialHierarchyContext(
            tenant_id=delivery_event.tenant_id,
            client_id=delivery_event.client_id,
            engagement_id=delivery_event.engagement_id,
            assessment_id=delivery_event.assessment_id,
        )

        # Require the real assessment record to already exist.
        repository.get_assessment(context=context)

        delivery_artifact = repository.append_artifact(
            context=context,
            artifact_type=DELIVERY_ARTIFACT_TYPE,
            payload=delivery_event.to_dict(),
            created_at=created_at,
        )

        acknowledgment_artifact = repository.append_artifact(
            context=context,
            artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
            payload=client_acknowledgment.to_dict(),
            created_at=created_at,
        )

        response_artifact = repository.append_artifact(
            context=context,
            artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
            payload=client_response.to_dict(),
            created_at=created_at,
        )

        chain_valid = repository.verify_chain(
            context=context
        )

        payload = {
            "persistence_type": (
                PAID_ASSESSMENT_LIFECYCLE_PERSISTENCE_ID
            ),
            "version": (
                PAID_ASSESSMENT_LIFECYCLE_PERSISTENCE_VERSION
            ),
            "schema_version": (
                PAID_ASSESSMENT_LIFECYCLE_PERSISTENCE_SCHEMA_VERSION
            ),
            "tenant_id": delivery_event.tenant_id,
            "client_id": delivery_event.client_id,
            "engagement_id": delivery_event.engagement_id,
            "assessment_id": delivery_event.assessment_id,
            "delivery_artifact_id": (
                delivery_artifact.artifact_id
            ),
            "delivery_artifact_hash": (
                delivery_artifact.artifact_hash
            ),
            "acknowledgment_artifact_id": (
                acknowledgment_artifact.artifact_id
            ),
            "acknowledgment_artifact_hash": (
                acknowledgment_artifact.artifact_hash
            ),
            "response_artifact_id": (
                response_artifact.artifact_id
            ),
            "response_artifact_hash": (
                response_artifact.artifact_hash
            ),
            "first_sequence_number": (
                delivery_artifact.sequence_number
            ),
            "last_sequence_number": (
                response_artifact.sequence_number
            ),
            "repository_chain_valid": chain_valid,
        }

        return PaidAssessmentLifecyclePersistenceReceipt(
            tenant_id=delivery_event.tenant_id,
            client_id=delivery_event.client_id,
            engagement_id=delivery_event.engagement_id,
            assessment_id=delivery_event.assessment_id,
            delivery_artifact_id=delivery_artifact.artifact_id,
            delivery_artifact_hash=delivery_artifact.artifact_hash,
            acknowledgment_artifact_id=(
                acknowledgment_artifact.artifact_id
            ),
            acknowledgment_artifact_hash=(
                acknowledgment_artifact.artifact_hash
            ),
            response_artifact_id=response_artifact.artifact_id,
            response_artifact_hash=response_artifact.artifact_hash,
            first_sequence_number=delivery_artifact.sequence_number,
            last_sequence_number=response_artifact.sequence_number,
            repository_chain_valid=chain_valid,
            lifecycle_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def _validate_delivery_event(
        self,
        delivery_event: GovernedPaidAssessmentDeliveryEvent,
    ) -> None:
        if not isinstance(
            delivery_event,
            GovernedPaidAssessmentDeliveryEvent,
        ):
            raise PaidAssessmentLifecyclePersistenceError(
                "delivery_event must be a "
                "GovernedPaidAssessmentDeliveryEvent"
            )

        if delivery_event.delivery_status != "delivered":
            raise PaidAssessmentLifecyclePersistenceError(
                "delivery_event must have delivery_status=delivered"
            )

        require_hash(
            delivery_event.delivery_event_hash,
            "delivery_event.delivery_event_hash",
        )

    def _validate_acknowledgment(
        self,
        *,
        delivery_event: GovernedPaidAssessmentDeliveryEvent,
        client_acknowledgment: (
            GovernedPaidAssessmentClientAcknowledgment
        ),
    ) -> None:
        if not isinstance(
            client_acknowledgment,
            GovernedPaidAssessmentClientAcknowledgment,
        ):
            raise PaidAssessmentLifecyclePersistenceError(
                "client_acknowledgment must be a "
                "GovernedPaidAssessmentClientAcknowledgment"
            )

        if (
            client_acknowledgment.acknowledgment_status
            != "client_receipt_acknowledged"
        ):
            raise PaidAssessmentLifecyclePersistenceError(
                "client acknowledgment must be "
                "client_receipt_acknowledged"
            )

        require_hash(
            client_acknowledgment.acknowledgment_hash,
            "client_acknowledgment.acknowledgment_hash",
        )

        expected = (
            delivery_event.tenant_id,
            delivery_event.client_id,
            delivery_event.engagement_id,
            delivery_event.assessment_id,
            delivery_event.report_id,
            delivery_event.delivery_event_id,
            delivery_event.delivery_event_hash,
        )

        actual = (
            client_acknowledgment.tenant_id,
            client_acknowledgment.client_id,
            client_acknowledgment.engagement_id,
            client_acknowledgment.assessment_id,
            client_acknowledgment.report_id,
            client_acknowledgment.delivery_event_id,
            client_acknowledgment.delivery_event_hash,
        )

        if actual != expected:
            raise PaidAssessmentLifecyclePersistenceError(
                "client acknowledgment lineage does not match "
                "delivery event"
            )

    def _validate_client_response(
        self,
        *,
        client_acknowledgment: (
            GovernedPaidAssessmentClientAcknowledgment
        ),
        client_response: GovernedPaidAssessmentClientResponse,
    ) -> None:
        if not isinstance(
            client_response,
            GovernedPaidAssessmentClientResponse,
        ):
            raise PaidAssessmentLifecyclePersistenceError(
                "client_response must be a "
                "GovernedPaidAssessmentClientResponse"
            )

        if client_response.response_status != "client_response_recorded":
            raise PaidAssessmentLifecyclePersistenceError(
                "client response must have "
                "response_status=client_response_recorded"
            )

        require_hash(
            client_response.response_hash,
            "client_response.response_hash",
        )

        expected = (
            client_acknowledgment.tenant_id,
            client_acknowledgment.client_id,
            client_acknowledgment.engagement_id,
            client_acknowledgment.assessment_id,
            client_acknowledgment.report_id,
            client_acknowledgment.acknowledgment_id,
            client_acknowledgment.acknowledgment_hash,
        )

        actual = (
            client_response.tenant_id,
            client_response.client_id,
            client_response.engagement_id,
            client_response.assessment_id,
            client_response.report_id,
            client_response.acknowledgment_id,
            client_response.acknowledgment_hash,
        )

        if actual != expected:
            raise PaidAssessmentLifecyclePersistenceError(
                "client response lineage does not match "
                "client acknowledgment"
            )


SERVICE = GovernancePaidAssessmentLifecyclePersistenceService()