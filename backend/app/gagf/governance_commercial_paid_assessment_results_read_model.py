from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_demonstration_persistence import (
    GovernanceAssessmentDemonstrationPersistenceService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    AssessmentRecordNotFoundError,
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)

COMMERCIAL_PAID_ASSESSMENT_RESULTS_READ_MODEL_ID = (
    "governance-commercial-paid-assessment-results-read-model"
)
COMMERCIAL_PAID_ASSESSMENT_RESULTS_READ_MODEL_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_RESULTS_READ_MODEL_SCHEMA_VERSION = "1.0.0"

SAFE_RESULT_ARTIFACT_TYPES = (
    "evidence-quality",
    "friction-summary",
    "governance-debt-score",
    "intervention-plan",
    "assessment-roadmap",
    "executive-projection",
    "client-report-package",
    "demonstration-manifest",
)


class CommercialPaidAssessmentResultsReadModelError(RuntimeError):
    """Raised when governed paid-assessment results cannot be safely read."""


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentResultArtifact:
    artifact_id: str
    artifact_type: str
    artifact_hash: str
    payload: dict[str, Any]
    created_at: str
    sequence_number: int
    previous_artifact_hash: str | None
    chain_hash: str
    schema_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "artifact_hash": self.artifact_hash,
            "payload": self.payload,
            "created_at": self.created_at,
            "sequence_number": self.sequence_number,
            "previous_artifact_hash": self.previous_artifact_hash,
            "chain_hash": self.chain_hash,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentArtifactInventoryItem:
    artifact_id: str
    artifact_type: str
    artifact_hash: str
    sequence_number: int
    chain_hash: str
    schema_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "artifact_hash": self.artifact_hash,
            "sequence_number": self.sequence_number,
            "chain_hash": self.chain_hash,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentResultsReadModel:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    assessment_name: str
    hierarchy_key: str
    execution_disposition: str
    execution_status_hash: str
    execution_input_binding_hash: str
    assessment_execution_request_hash: str
    artifact_count: int
    repository_chain_valid: bool
    artifact_inventory: tuple[
        CommercialPaidAssessmentArtifactInventoryItem,
        ...,
    ]
    result_artifacts: tuple[
        CommercialPaidAssessmentResultArtifact,
        ...,
    ]
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_RESULTS_READ_MODEL_SCHEMA_VERSION
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "read_model_type": (
                COMMERCIAL_PAID_ASSESSMENT_RESULTS_READ_MODEL_ID
            ),
            "version": (
                COMMERCIAL_PAID_ASSESSMENT_RESULTS_READ_MODEL_VERSION
            ),
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "assessment_name": self.assessment_name,
            "hierarchy_key": self.hierarchy_key,
            "execution_disposition": self.execution_disposition,
            "execution_status_hash": self.execution_status_hash,
            "execution_input_binding_hash": (
                self.execution_input_binding_hash
            ),
            "assessment_execution_request_hash": (
                self.assessment_execution_request_hash
            ),
            "artifact_count": self.artifact_count,
            "repository_chain_valid": self.repository_chain_valid,
            "artifact_inventory": [
                item.to_dict() for item in self.artifact_inventory
            ],
            "result_artifacts": [
                artifact.to_dict() for artifact in self.result_artifacts
            ],
            "boundaries": {
                "read_model_is_read_only": True,
                "read_model_is_not_execution_authority": True,
                "read_model_is_not_recovery_authority": True,
                "read_model_is_not_delivery_approval": True,
                "repository_path_not_exposed": True,
                "raw_evidence_payloads_not_exposed": True,
                "evidence_intake_payload_not_exposed": True,
                "scope_configuration_payload_not_exposed": True,
                "result_payloads_are_canonical_paid_artifacts": True,
            },
        }


class GovernanceCommercialPaidAssessmentResultsReadModelService:
    """
    Build a read-only projection from the canonical PA015 repository.

    This service does not execute, resume, reconcile, repair, authorize,
    approve delivery, or mutate the paid assessment repository.
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
            raise CommercialPaidAssessmentResultsReadModelError(
                "execution_service must be a "
                "GovernanceCommercialPaidAssessmentExecutionService"
            )
        self._execution_service = execution_service

    def read(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CommercialPaidAssessmentResultsReadModel:
        context = CommercialHierarchyContext(
            tenant_id=self._require_text(tenant_id, "tenant_id"),
            client_id=self._require_text(client_id, "client_id"),
            engagement_id=self._require_text(
                engagement_id, "engagement_id"
            ),
            assessment_id=self._require_text(
                assessment_id, "assessment_id"
            ),
        )

        execution_status = self._execution_service.status_store.get_status(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=context.engagement_id,
            assessment_id=context.assessment_id,
        )

        if execution_status is None:
            raise CommercialPaidAssessmentResultsReadModelError(
                "durable paid execution status was not found"
            )

        if execution_status.hierarchy_key != context.hierarchy_key:
            raise CommercialPaidAssessmentResultsReadModelError(
                "durable paid execution status hierarchy mismatch"
            )

        database_path = (
            self._execution_service.database_path_for_hierarchy(
                tenant_id=context.tenant_id,
                client_id=context.client_id,
                engagement_id=context.engagement_id,
                assessment_id=context.assessment_id,
            )
        )

        if not database_path.exists():
            raise CommercialPaidAssessmentResultsReadModelError(
                "governed paid assessment database does not exist"
            )

        if not database_path.is_file():
            raise CommercialPaidAssessmentResultsReadModelError(
                "governed paid assessment database path is not a file"
            )

        repository = GovernanceAssessmentRepository(Path(database_path))

        try:
            assessment = repository.get_assessment(context=context)
        except AssessmentRecordNotFoundError as exc:
            raise CommercialPaidAssessmentResultsReadModelError(
                "completed paid assessment record was not found"
            ) from exc

        if assessment.status != "complete":
            raise CommercialPaidAssessmentResultsReadModelError(
                "paid assessment record is not complete"
            )

        artifacts = repository.list_artifacts(context=context)
        expected_order = (
            GovernanceAssessmentDemonstrationPersistenceService.ARTIFACT_ORDER
        )

        if len(artifacts) != len(expected_order):
            raise CommercialPaidAssessmentResultsReadModelError(
                "canonical paid assessment artifact count is invalid"
            )

        artifact_types = tuple(
            artifact.artifact_type for artifact in artifacts
        )

        if artifact_types != expected_order:
            raise CommercialPaidAssessmentResultsReadModelError(
                "canonical paid assessment artifact order is invalid"
            )

        if len(set(artifact_types)) != len(artifact_types):
            raise CommercialPaidAssessmentResultsReadModelError(
                "canonical paid assessment contains duplicate artifact types"
            )

        for artifact in artifacts:
            if artifact.hierarchy_key != context.hierarchy_key:
                raise CommercialPaidAssessmentResultsReadModelError(
                    "canonical paid assessment artifact hierarchy mismatch"
                )
            repository.verify_artifact(artifact)

        repository_chain_valid = repository.verify_chain(context=context)

        if repository_chain_valid is not True:
            raise CommercialPaidAssessmentResultsReadModelError(
                "canonical paid assessment artifact chain is invalid"
            )

        inventory = tuple(
            CommercialPaidAssessmentArtifactInventoryItem(
                artifact_id=artifact.artifact_id,
                artifact_type=artifact.artifact_type,
                artifact_hash=artifact.artifact_hash,
                sequence_number=artifact.sequence_number,
                chain_hash=artifact.chain_hash,
                schema_version=artifact.schema_version,
            )
            for artifact in artifacts
        )

        result_artifacts = tuple(
            self._safe_result_artifact(artifact=artifact)
            for artifact in artifacts
            if artifact.artifact_type in SAFE_RESULT_ARTIFACT_TYPES
        )

        expected_safe_types = tuple(
            artifact_type
            for artifact_type in expected_order
            if artifact_type in SAFE_RESULT_ARTIFACT_TYPES
        )
        actual_safe_types = tuple(
            artifact.artifact_type for artifact in result_artifacts
        )

        if actual_safe_types != expected_safe_types:
            raise CommercialPaidAssessmentResultsReadModelError(
                "safe governed paid result artifact set is invalid"
            )

        return CommercialPaidAssessmentResultsReadModel(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=context.engagement_id,
            assessment_id=context.assessment_id,
            assessment_name=assessment.assessment_name,
            hierarchy_key=context.hierarchy_key,
            execution_disposition=execution_status.disposition,
            execution_status_hash=execution_status.status_hash,
            execution_input_binding_hash=(
                execution_status.execution_input_binding_hash
            ),
            assessment_execution_request_hash=(
                execution_status.assessment_execution_request_hash
            ),
            artifact_count=len(artifacts),
            repository_chain_valid=repository_chain_valid,
            artifact_inventory=inventory,
            result_artifacts=result_artifacts,
        )

    def _safe_result_artifact(
        self,
        *,
        artifact: Any,
    ) -> CommercialPaidAssessmentResultArtifact:
        payload = artifact.payload

        if not isinstance(payload, dict):
            raise CommercialPaidAssessmentResultsReadModelError(
                "governed paid result artifact payload must be an object"
            )

        return CommercialPaidAssessmentResultArtifact(
            artifact_id=artifact.artifact_id,
            artifact_type=artifact.artifact_type,
            artifact_hash=artifact.artifact_hash,
            payload=payload,
            created_at=artifact.created_at.isoformat(),
            sequence_number=artifact.sequence_number,
            previous_artifact_hash=artifact.previous_artifact_hash,
            chain_hash=artifact.chain_hash,
            schema_version=artifact.schema_version,
        )

    def _require_text(
        self,
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise CommercialPaidAssessmentResultsReadModelError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise CommercialPaidAssessmentResultsReadModelError(
                f"{field_name} must not be empty"
            )

        return normalized
