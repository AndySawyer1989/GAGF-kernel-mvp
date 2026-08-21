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


@dataclass(frozen=True, slots=True)
class PaidAssessmentLifecycleEventPersistenceReceipt:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    artifact_type: str
    artifact_id: str
    artifact_hash: str
    sequence_number: int
    chain_hash: str
    repository_chain_valid: bool

    persistence_type: str = (
        "governance-paid-assessment-lifecycle-event-persistence"
    )
    version: str = (
        PAID_ASSESSMENT_LIFECYCLE_PERSISTENCE_VERSION
    )
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
            "artifact_type": self.artifact_type,
            "artifact_id": self.artifact_id,
            "artifact_hash": self.artifact_hash,
            "sequence_number": self.sequence_number,
            "chain_hash": self.chain_hash,
            "repository_chain_valid": (
                self.repository_chain_valid
            ),
            "boundaries": {
                "persistence_does_not_create_delivery": True,
                "persistence_does_not_create_acknowledgment": True,
                "persistence_does_not_create_client_response": True,
                "persistence_does_not_create_closeout": True,
                "persistence_does_not_authorize_intervention": True,
                "persistence_does_not_verify_customer_outcome": True,
            },
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

    def persist_delivery(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        delivery_event: GovernedPaidAssessmentDeliveryEvent,
        created_at: datetime | None = None,
    ) -> PaidAssessmentLifecycleEventPersistenceReceipt:
        self._require_repository(repository)
        self._validate_delivery_event(delivery_event)

        context = self._context_from_values(
            tenant_id=delivery_event.tenant_id,
            client_id=delivery_event.client_id,
            engagement_id=delivery_event.engagement_id,
            assessment_id=delivery_event.assessment_id,
        )

        repository.get_assessment(context=context)

        self._require_valid_chain(
            repository=repository,
            context=context,
            stage="before delivery persistence",
        )

        lifecycle = self._index_existing_lifecycle(
            repository=repository,
            context=context,
        )

        if DELIVERY_ARTIFACT_TYPE in lifecycle:
            raise PaidAssessmentLifecyclePersistenceError(
                "delivery lifecycle artifact already exists"
            )

        if (
            ACKNOWLEDGMENT_ARTIFACT_TYPE in lifecycle
            or CLIENT_RESPONSE_ARTIFACT_TYPE in lifecycle
        ):
            raise PaidAssessmentLifecyclePersistenceError(
                "downstream lifecycle artifact exists without "
                "persisted delivery"
            )

        artifact = repository.append_artifact(
            context=context,
            artifact_type=DELIVERY_ARTIFACT_TYPE,
            payload=delivery_event.to_dict(),
            created_at=created_at,
        )

        return self._event_receipt(
            repository=repository,
            context=context,
            artifact=artifact,
        )

    def persist_acknowledgment(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        client_acknowledgment: (
            GovernedPaidAssessmentClientAcknowledgment
        ),
        created_at: datetime | None = None,
    ) -> PaidAssessmentLifecycleEventPersistenceReceipt:
        self._require_repository(repository)
        self._validate_acknowledgment_core(
            client_acknowledgment
        )

        context = self._context_from_values(
            tenant_id=client_acknowledgment.tenant_id,
            client_id=client_acknowledgment.client_id,
            engagement_id=client_acknowledgment.engagement_id,
            assessment_id=client_acknowledgment.assessment_id,
        )

        repository.get_assessment(context=context)

        self._require_valid_chain(
            repository=repository,
            context=context,
            stage="before acknowledgment persistence",
        )

        lifecycle = self._index_existing_lifecycle(
            repository=repository,
            context=context,
        )

        delivery = lifecycle.get(
            DELIVERY_ARTIFACT_TYPE
        )

        if delivery is None:
            raise PaidAssessmentLifecyclePersistenceError(
                "cannot persist client acknowledgment "
                "before delivery"
            )

        if ACKNOWLEDGMENT_ARTIFACT_TYPE in lifecycle:
            raise PaidAssessmentLifecyclePersistenceError(
                "client acknowledgment lifecycle artifact "
                "already exists"
            )

        if CLIENT_RESPONSE_ARTIFACT_TYPE in lifecycle:
            raise PaidAssessmentLifecyclePersistenceError(
                "client response exists before "
                "acknowledgment persistence"
            )

        self._validate_acknowledgment_against_delivery_payload(
            delivery_payload=delivery.payload,
            client_acknowledgment=client_acknowledgment,
        )

        artifact = repository.append_artifact(
            context=context,
            artifact_type=ACKNOWLEDGMENT_ARTIFACT_TYPE,
            payload=client_acknowledgment.to_dict(),
            created_at=created_at,
        )

        return self._event_receipt(
            repository=repository,
            context=context,
            artifact=artifact,
        )

    def persist_client_response(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        client_response: GovernedPaidAssessmentClientResponse,
        created_at: datetime | None = None,
    ) -> PaidAssessmentLifecycleEventPersistenceReceipt:
        self._require_repository(repository)
        self._validate_client_response_core(
            client_response
        )

        context = self._context_from_values(
            tenant_id=client_response.tenant_id,
            client_id=client_response.client_id,
            engagement_id=client_response.engagement_id,
            assessment_id=client_response.assessment_id,
        )

        repository.get_assessment(context=context)

        self._require_valid_chain(
            repository=repository,
            context=context,
            stage="before client-response persistence",
        )

        lifecycle = self._index_existing_lifecycle(
            repository=repository,
            context=context,
        )

        if DELIVERY_ARTIFACT_TYPE not in lifecycle:
            raise PaidAssessmentLifecyclePersistenceError(
                "cannot persist client response before delivery"
            )

        acknowledgment = lifecycle.get(
            ACKNOWLEDGMENT_ARTIFACT_TYPE
        )

        if acknowledgment is None:
            raise PaidAssessmentLifecyclePersistenceError(
                "cannot persist client response before "
                "receipt acknowledgment"
            )

        if CLIENT_RESPONSE_ARTIFACT_TYPE in lifecycle:
            raise PaidAssessmentLifecyclePersistenceError(
                "client response lifecycle artifact already exists"
            )

        self._validate_response_against_acknowledgment_payload(
            acknowledgment_payload=acknowledgment.payload,
            client_response=client_response,
        )

        artifact = repository.append_artifact(
            context=context,
            artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
            payload=client_response.to_dict(),
            created_at=created_at,
        )

        return self._event_receipt(
            repository=repository,
            context=context,
            artifact=artifact,
        )

    def _require_repository(
        self,
        repository: GovernanceAssessmentRepository,
    ) -> None:
        if not isinstance(
            repository,
            GovernanceAssessmentRepository,
        ):
            raise PaidAssessmentLifecyclePersistenceError(
                "repository must be a "
                "GovernanceAssessmentRepository"
            )

    def _context_from_values(
        self,
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

    def _require_valid_chain(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        context: CommercialHierarchyContext,
        stage: str,
    ) -> None:
        if repository.verify_chain(context=context) is not True:
            raise PaidAssessmentLifecyclePersistenceError(
                f"repository chain is invalid {stage}"
            )

    def _index_existing_lifecycle(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        context: CommercialHierarchyContext,
    ) -> dict[str, ImmutableAssessmentArtifact]:
        lifecycle_types = {
            DELIVERY_ARTIFACT_TYPE,
            ACKNOWLEDGMENT_ARTIFACT_TYPE,
            CLIENT_RESPONSE_ARTIFACT_TYPE,
        }

        result: dict[str, ImmutableAssessmentArtifact] = {}

        for artifact in repository.list_artifacts(
            context=context
        ):
            if artifact.artifact_type not in lifecycle_types:
                continue

            if artifact.artifact_type in result:
                raise PaidAssessmentLifecyclePersistenceError(
                    "duplicate paid-assessment lifecycle "
                    "artifact type: "
                    f"{artifact.artifact_type}"
                )

            result[artifact.artifact_type] = artifact

        return result

    def _event_receipt(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        context: CommercialHierarchyContext,
        artifact: ImmutableAssessmentArtifact,
    ) -> PaidAssessmentLifecycleEventPersistenceReceipt:
        chain_valid = repository.verify_chain(
            context=context
        )

        if chain_valid is not True:
            raise PaidAssessmentLifecyclePersistenceError(
                "repository chain is invalid after "
                "lifecycle persistence"
            )

        return PaidAssessmentLifecycleEventPersistenceReceipt(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=context.engagement_id,
            assessment_id=context.assessment_id,
            artifact_type=artifact.artifact_type,
            artifact_id=artifact.artifact_id,
            artifact_hash=artifact.artifact_hash,
            sequence_number=artifact.sequence_number,
            chain_hash=artifact.chain_hash,
            repository_chain_valid=True,
        )

    def _validate_acknowledgment_core(
        self,
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

    def _validate_client_response_core(
        self,
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

        if (
            client_response.response_status
            != "client_response_recorded"
        ):
            raise PaidAssessmentLifecyclePersistenceError(
                "client response must have "
                "response_status=client_response_recorded"
            )

        require_hash(
            client_response.response_hash,
            "client_response.response_hash",
        )

    def _require_payload_text(
        self,
        payload: dict[str, Any],
        field_name: str,
    ) -> str:
        value = payload.get(field_name)

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise PaidAssessmentLifecyclePersistenceError(
                "persisted lifecycle artifact missing "
                f"{field_name}"
            )

        return value.strip()

    def _validate_acknowledgment_against_delivery_payload(
        self,
        *,
        delivery_payload: dict[str, Any],
        client_acknowledgment: (
            GovernedPaidAssessmentClientAcknowledgment
        ),
    ) -> None:
        if (
            self._require_payload_text(
                delivery_payload,
                "delivery_status",
            )
            != "delivered"
        ):
            raise PaidAssessmentLifecyclePersistenceError(
                "persisted delivery artifact must have "
                "delivery_status=delivered"
            )

        fields = (
            ("tenant_id", client_acknowledgment.tenant_id),
            ("client_id", client_acknowledgment.client_id),
            (
                "engagement_id",
                client_acknowledgment.engagement_id,
            ),
            (
                "assessment_id",
                client_acknowledgment.assessment_id,
            ),
            ("report_id", client_acknowledgment.report_id),
            (
                "delivery_event_id",
                client_acknowledgment.delivery_event_id,
            ),
            (
                "delivery_event_hash",
                client_acknowledgment.delivery_event_hash,
            ),
        )

        for field_name, actual in fields:
            expected = self._require_payload_text(
                delivery_payload,
                field_name,
            )

            if actual != expected:
                raise PaidAssessmentLifecyclePersistenceError(
                    "client acknowledgment lineage does not "
                    "match persisted delivery field "
                    f"{field_name}"
                )

    def _validate_response_against_acknowledgment_payload(
        self,
        *,
        acknowledgment_payload: dict[str, Any],
        client_response: GovernedPaidAssessmentClientResponse,
    ) -> None:
        if (
            self._require_payload_text(
                acknowledgment_payload,
                "acknowledgment_status",
            )
            != "client_receipt_acknowledged"
        ):
            raise PaidAssessmentLifecyclePersistenceError(
                "persisted acknowledgment artifact must have "
                "acknowledgment_status="
                "client_receipt_acknowledged"
            )

        fields = (
            ("tenant_id", client_response.tenant_id),
            ("client_id", client_response.client_id),
            (
                "engagement_id",
                client_response.engagement_id,
            ),
            (
                "assessment_id",
                client_response.assessment_id,
            ),
            ("report_id", client_response.report_id),
            (
                "acknowledgment_id",
                client_response.acknowledgment_id,
            ),
            (
                "acknowledgment_hash",
                client_response.acknowledgment_hash,
            ),
        )

        for field_name, actual in fields:
            expected = self._require_payload_text(
                acknowledgment_payload,
                field_name,
            )

            if actual != expected:
                raise PaidAssessmentLifecyclePersistenceError(
                    "client response lineage does not match "
                    "persisted acknowledgment field "
                    f"{field_name}"
                )
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