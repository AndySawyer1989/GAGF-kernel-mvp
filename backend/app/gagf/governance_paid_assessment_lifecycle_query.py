from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
    ImmutableAssessmentArtifact,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
    CLIENT_RESPONSE_ARTIFACT_TYPE,
    DELIVERY_ARTIFACT_TYPE,
)


PAID_ASSESSMENT_LIFECYCLE_QUERY_ID = (
    "governance-paid-assessment-lifecycle-query"
)
PAID_ASSESSMENT_LIFECYCLE_QUERY_VERSION = "0.1.0"
PAID_ASSESSMENT_LIFECYCLE_QUERY_SCHEMA_VERSION = "1.0.0"

LIFECYCLE_STAGE_NOT_STARTED = "post_assessment_lifecycle_not_started"
LIFECYCLE_STAGE_DELIVERED = "delivered"
LIFECYCLE_STAGE_RECEIPT_ACKNOWLEDGED = "client_receipt_acknowledged"
LIFECYCLE_STAGE_CLIENT_RESPONSE_RECORDED = "client_response_recorded"

NEXT_STEP_RECORD_DELIVERY = "record_delivery_event"
NEXT_STEP_RECORD_ACKNOWLEDGMENT = "record_client_receipt_acknowledgment"
NEXT_STEP_RECORD_RESPONSE = "record_client_response"
NEXT_STEP_NONE = "none"

LIFECYCLE_ARTIFACT_TYPES = (
    DELIVERY_ARTIFACT_TYPE,
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
    CLIENT_RESPONSE_ARTIFACT_TYPE,
)


class PaidAssessmentLifecycleQueryError(ValueError):
    """Raised when a lifecycle projection cannot be derived safely."""


@dataclass(frozen=True, slots=True)
class PaidAssessmentLifecycleArtifactReference:
    artifact_id: str
    artifact_type: str
    artifact_hash: str
    sequence_number: int
    chain_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "artifact_hash": self.artifact_hash,
            "sequence_number": self.sequence_number,
            "chain_hash": self.chain_hash,
        }


@dataclass(frozen=True, slots=True)
class PaidAssessmentLifecycleState:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    current_stage: str
    pending_next_step: str
    delivery_recorded: bool
    receipt_acknowledged: bool
    client_response_recorded: bool
    report_id: str | None
    findings_disposition: str | None
    recommendations_disposition: str | None
    lifecycle_artifact_count: int
    repository_artifact_count: int
    repository_chain_valid: bool
    latest_lifecycle_artifact: (
        PaidAssessmentLifecycleArtifactReference | None
    )
    lifecycle_artifacts: tuple[
        PaidAssessmentLifecycleArtifactReference, ...
    ]
    query_type: str = PAID_ASSESSMENT_LIFECYCLE_QUERY_ID
    version: str = PAID_ASSESSMENT_LIFECYCLE_QUERY_VERSION
    schema_version: str = PAID_ASSESSMENT_LIFECYCLE_QUERY_SCHEMA_VERSION

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
            "query_type": self.query_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "current_stage": self.current_stage,
            "pending_next_step": self.pending_next_step,
            "delivery_recorded": self.delivery_recorded,
            "receipt_acknowledged": self.receipt_acknowledged,
            "client_response_recorded": self.client_response_recorded,
            "report_id": self.report_id,
            "findings_disposition": self.findings_disposition,
            "recommendations_disposition": (
                self.recommendations_disposition
            ),
            "lifecycle_artifact_count": self.lifecycle_artifact_count,
            "repository_artifact_count": self.repository_artifact_count,
            "repository_chain_valid": self.repository_chain_valid,
            "latest_lifecycle_artifact": (
                None
                if self.latest_lifecycle_artifact is None
                else self.latest_lifecycle_artifact.to_dict()
            ),
            "lifecycle_artifacts": [
                item.to_dict()
                for item in self.lifecycle_artifacts
            ],
        }


class GovernancePaidAssessmentLifecycleQueryService:
    """
    Read-only deterministic projection of paid-assessment lifecycle state.

    The projection is derived only from immutable repository artifacts and
    verified repository ordering/integrity.

    Query projection does not create delivery, acknowledgment, client
    acceptance, intervention request, intervention authorization, execution,
    causation, ROI, remediation-success, or verified-outcome authority.
    """

    def __init__(
        self,
        *,
        repository: GovernanceAssessmentRepository,
    ) -> None:
        if not isinstance(
            repository,
            GovernanceAssessmentRepository,
        ):
            raise PaidAssessmentLifecycleQueryError(
                "repository must be a GovernanceAssessmentRepository"
            )

        self._repository = repository

    def get_state(
        self,
        *,
        context: CommercialHierarchyContext,
    ) -> PaidAssessmentLifecycleState:
        self._repository.get_assessment(context=context)

        artifacts = self._repository.list_artifacts(
            context=context
        )

        chain_valid = self._repository.verify_chain(
            context=context
        )

        lifecycle_artifacts = tuple(
            artifact
            for artifact in artifacts
            if artifact.artifact_type in LIFECYCLE_ARTIFACT_TYPES
        )

        by_type = self._index_lifecycle_artifacts(
            lifecycle_artifacts
        )

        delivery = by_type.get(DELIVERY_ARTIFACT_TYPE)
        acknowledgment = by_type.get(
            ACKNOWLEDGMENT_ARTIFACT_TYPE
        )
        response = by_type.get(CLIENT_RESPONSE_ARTIFACT_TYPE)

        self._validate_presence_order(
            delivery=delivery,
            acknowledgment=acknowledgment,
            response=response,
        )

        delivery_payload = (
            None if delivery is None else delivery.payload
        )
        acknowledgment_payload = (
            None
            if acknowledgment is None
            else acknowledgment.payload
        )
        response_payload = (
            None if response is None else response.payload
        )

        if delivery_payload is not None:
            self._validate_delivery_payload(
                context=context,
                payload=delivery_payload,
            )

        if acknowledgment_payload is not None:
            assert delivery_payload is not None
            self._validate_acknowledgment_payload(
                context=context,
                delivery_payload=delivery_payload,
                acknowledgment_payload=acknowledgment_payload,
            )

        if response_payload is not None:
            assert acknowledgment_payload is not None
            self._validate_response_payload(
                context=context,
                acknowledgment_payload=acknowledgment_payload,
                response_payload=response_payload,
            )

        current_stage, pending_next_step = (
            self._derive_stage(
                delivery=delivery,
                acknowledgment=acknowledgment,
                response=response,
            )
        )

        references = tuple(
            self._reference(artifact)
            for artifact in lifecycle_artifacts
        )

        report_id = self._derive_report_id(
            delivery_payload=delivery_payload,
            acknowledgment_payload=acknowledgment_payload,
            response_payload=response_payload,
        )

        findings_disposition = (
            None
            if response_payload is None
            else self._require_text(
                response_payload,
                "findings_disposition",
            )
        )

        recommendations_disposition = (
            None
            if response_payload is None
            else self._require_text(
                response_payload,
                "recommendations_disposition",
            )
        )

        return PaidAssessmentLifecycleState(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=self._require_context_text(
                context.engagement_id,
                "engagement_id",
            ),
            assessment_id=self._require_context_text(
                context.assessment_id,
                "assessment_id",
            ),
            current_stage=current_stage,
            pending_next_step=pending_next_step,
            delivery_recorded=delivery is not None,
            receipt_acknowledged=acknowledgment is not None,
            client_response_recorded=response is not None,
            report_id=report_id,
            findings_disposition=findings_disposition,
            recommendations_disposition=(
                recommendations_disposition
            ),
            lifecycle_artifact_count=len(
                lifecycle_artifacts
            ),
            repository_artifact_count=len(artifacts),
            repository_chain_valid=chain_valid,
            latest_lifecycle_artifact=(
                None
                if not references
                else references[-1]
            ),
            lifecycle_artifacts=references,
        )

    def _index_lifecycle_artifacts(
        self,
        artifacts: tuple[ImmutableAssessmentArtifact, ...],
    ) -> dict[str, ImmutableAssessmentArtifact]:
        result: dict[str, ImmutableAssessmentArtifact] = {}

        for artifact in artifacts:
            if artifact.artifact_type in result:
                raise PaidAssessmentLifecycleQueryError(
                    "duplicate paid-assessment lifecycle artifact type: "
                    f"{artifact.artifact_type}"
                )

            result[artifact.artifact_type] = artifact

        return result

    def _validate_presence_order(
        self,
        *,
        delivery: ImmutableAssessmentArtifact | None,
        acknowledgment: ImmutableAssessmentArtifact | None,
        response: ImmutableAssessmentArtifact | None,
    ) -> None:
        if acknowledgment is not None and delivery is None:
            raise PaidAssessmentLifecycleQueryError(
                "client acknowledgment exists without delivery event"
            )

        if response is not None and acknowledgment is None:
            raise PaidAssessmentLifecycleQueryError(
                "client response exists without receipt acknowledgment"
            )

        if (
            delivery is not None
            and acknowledgment is not None
            and acknowledgment.sequence_number
            <= delivery.sequence_number
        ):
            raise PaidAssessmentLifecycleQueryError(
                "client acknowledgment must follow delivery event"
            )

        if (
            acknowledgment is not None
            and response is not None
            and response.sequence_number
            <= acknowledgment.sequence_number
        ):
            raise PaidAssessmentLifecycleQueryError(
                "client response must follow receipt acknowledgment"
            )

    def _validate_delivery_payload(
        self,
        *,
        context: CommercialHierarchyContext,
        payload: dict[str, Any],
    ) -> None:
        self._validate_context_payload(
            context=context,
            payload=payload,
        )

        if self._require_text(
            payload,
            "delivery_status",
        ) != LIFECYCLE_STAGE_DELIVERED:
            raise PaidAssessmentLifecycleQueryError(
                "delivery lifecycle artifact must have "
                "delivery_status=delivered"
            )

        self._require_text(payload, "report_id")
        self._require_text(payload, "delivery_event_id")
        self._require_text(payload, "delivery_event_hash")

    def _validate_acknowledgment_payload(
        self,
        *,
        context: CommercialHierarchyContext,
        delivery_payload: dict[str, Any],
        acknowledgment_payload: dict[str, Any],
    ) -> None:
        self._validate_context_payload(
            context=context,
            payload=acknowledgment_payload,
        )

        if self._require_text(
            acknowledgment_payload,
            "acknowledgment_status",
        ) != LIFECYCLE_STAGE_RECEIPT_ACKNOWLEDGED:
            raise PaidAssessmentLifecycleQueryError(
                "acknowledgment lifecycle artifact must have "
                "acknowledgment_status=client_receipt_acknowledged"
            )

        lineage_fields = (
            "report_id",
            "delivery_event_id",
            "delivery_event_hash",
        )

        for field_name in lineage_fields:
            if self._require_text(
                acknowledgment_payload,
                field_name,
            ) != self._require_text(
                delivery_payload,
                field_name,
            ):
                raise PaidAssessmentLifecycleQueryError(
                    "client acknowledgment lineage does not match "
                    f"delivery event field {field_name}"
                )

        self._require_text(
            acknowledgment_payload,
            "acknowledgment_id",
        )
        self._require_text(
            acknowledgment_payload,
            "acknowledgment_hash",
        )

    def _validate_response_payload(
        self,
        *,
        context: CommercialHierarchyContext,
        acknowledgment_payload: dict[str, Any],
        response_payload: dict[str, Any],
    ) -> None:
        self._validate_context_payload(
            context=context,
            payload=response_payload,
        )

        if self._require_text(
            response_payload,
            "response_status",
        ) != LIFECYCLE_STAGE_CLIENT_RESPONSE_RECORDED:
            raise PaidAssessmentLifecycleQueryError(
                "client response lifecycle artifact must have "
                "response_status=client_response_recorded"
            )

        lineage_fields = (
            "report_id",
            "acknowledgment_id",
            "acknowledgment_hash",
        )

        for field_name in lineage_fields:
            if self._require_text(
                response_payload,
                field_name,
            ) != self._require_text(
                acknowledgment_payload,
                field_name,
            ):
                raise PaidAssessmentLifecycleQueryError(
                    "client response lineage does not match "
                    f"acknowledgment field {field_name}"
                )

        self._require_text(
            response_payload,
            "findings_disposition",
        )
        self._require_text(
            response_payload,
            "recommendations_disposition",
        )

    def _validate_context_payload(
        self,
        *,
        context: CommercialHierarchyContext,
        payload: dict[str, Any],
    ) -> None:
        expected = {
            "tenant_id": context.tenant_id,
            "client_id": context.client_id,
            "engagement_id": self._require_context_text(
                context.engagement_id,
                "engagement_id",
            ),
            "assessment_id": self._require_context_text(
                context.assessment_id,
                "assessment_id",
            ),
        }

        for field_name, expected_value in expected.items():
            if self._require_text(
                payload,
                field_name,
            ) != expected_value:
                raise PaidAssessmentLifecycleQueryError(
                    "lifecycle artifact hierarchy mismatch for "
                    f"{field_name}"
                )

    def _derive_stage(
        self,
        *,
        delivery: ImmutableAssessmentArtifact | None,
        acknowledgment: ImmutableAssessmentArtifact | None,
        response: ImmutableAssessmentArtifact | None,
    ) -> tuple[str, str]:
        if response is not None:
            return (
                LIFECYCLE_STAGE_CLIENT_RESPONSE_RECORDED,
                NEXT_STEP_NONE,
            )

        if acknowledgment is not None:
            return (
                LIFECYCLE_STAGE_RECEIPT_ACKNOWLEDGED,
                NEXT_STEP_RECORD_RESPONSE,
            )

        if delivery is not None:
            return (
                LIFECYCLE_STAGE_DELIVERED,
                NEXT_STEP_RECORD_ACKNOWLEDGMENT,
            )

        return (
            LIFECYCLE_STAGE_NOT_STARTED,
            NEXT_STEP_RECORD_DELIVERY,
        )

    def _derive_report_id(
        self,
        *,
        delivery_payload: dict[str, Any] | None,
        acknowledgment_payload: dict[str, Any] | None,
        response_payload: dict[str, Any] | None,
    ) -> str | None:
        for payload in (
            response_payload,
            acknowledgment_payload,
            delivery_payload,
        ):
            if payload is not None:
                return self._require_text(
                    payload,
                    "report_id",
                )

        return None

    def _reference(
        self,
        artifact: ImmutableAssessmentArtifact,
    ) -> PaidAssessmentLifecycleArtifactReference:
        return PaidAssessmentLifecycleArtifactReference(
            artifact_id=artifact.artifact_id,
            artifact_type=artifact.artifact_type,
            artifact_hash=artifact.artifact_hash,
            sequence_number=artifact.sequence_number,
            chain_hash=artifact.chain_hash,
        )

    def _require_text(
        self,
        payload: dict[str, Any],
        field_name: str,
    ) -> str:
        value = payload.get(field_name)

        if not isinstance(value, str) or not value.strip():
            raise PaidAssessmentLifecycleQueryError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()

    def _require_context_text(
        self,
        value: str | None,
        field_name: str,
    ) -> str:
        if value is None or not value.strip():
            raise PaidAssessmentLifecycleQueryError(
                f"context requires {field_name}"
            )

        return value.strip()


SERVICE_TYPE = GovernancePaidAssessmentLifecycleQueryService