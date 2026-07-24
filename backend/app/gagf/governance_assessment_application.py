from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from backend.app.gagf.governance_assessment_demonstration import (
    DemonstrationEvidenceInput,
    GovernanceAssessmentDemonstrationResult,
    GovernanceAssessmentDemonstrationService,
)
from backend.app.gagf.governance_assessment_demonstration_persistence import (
    DemonstrationPersistenceResult,
    GovernanceAssessmentDemonstrationPersistenceService,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    ConstraintCategory,
)
from backend.app.gagf.governance_assessment_intervention_plan import (
    InterventionType,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
    ImmutableAssessmentArtifact,
    PersistedAssessmentRecord,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)


ASSESSMENT_APPLICATION_VERSION = "1.0.0"


class AssessmentApplicationError(RuntimeError):
    """Raised when an application-level assessment operation fails."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def require_text(value: str, field_name: str) -> str:
    normalized = value.strip()

    if not normalized:
        raise AssessmentApplicationError(
            f"{field_name} must not be empty"
        )

    return normalized


@dataclass(frozen=True, slots=True)
class AssessmentExecutionRequest:
    context: CommercialHierarchyContext
    assessment_name: str
    workflow_names: tuple[str, ...]
    organizational_units: tuple[str, ...]
    period_start: date
    period_end: date
    objectives: tuple[str, ...]
    expected_outcomes: tuple[str, ...]
    evidence_requirements: tuple[EvidenceRequirement, ...]
    evidence_inputs: tuple[DemonstrationEvidenceInput, ...]
    client_display_name: str
    prepared_by: str
    exclusions: tuple[str, ...] = ()
    implementation_burdens: dict[
        ConstraintCategory, float
    ] | None = None
    reversibility_scores: dict[
        ConstraintCategory, float
    ] | None = None
    owner_roles: dict[InterventionType, str] | None = None
    maximum_priorities: int = 3

    def __post_init__(self) -> None:
        require_text(self.assessment_name, "assessment_name")
        require_text(
            self.client_display_name,
            "client_display_name",
        )
        require_text(self.prepared_by, "prepared_by")

        if not self.workflow_names:
            raise AssessmentApplicationError(
                "workflow_names must not be empty"
            )

        if not self.organizational_units:
            raise AssessmentApplicationError(
                "organizational_units must not be empty"
            )

        if not self.evidence_inputs:
            raise AssessmentApplicationError(
                "evidence_inputs must not be empty"
            )

        if self.maximum_priorities < 1:
            raise AssessmentApplicationError(
                "maximum_priorities must be at least 1"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hierarchy_key": self.context.hierarchy_key,
            "assessment_name": self.assessment_name,
            "workflow_names": list(self.workflow_names),
            "organizational_units": list(
                self.organizational_units
            ),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "objectives": list(self.objectives),
            "expected_outcomes": list(
                self.expected_outcomes
            ),
            "evidence_requirement_count": len(
                self.evidence_requirements
            ),
            "evidence_input_count": len(self.evidence_inputs),
            "client_display_name": self.client_display_name,
            "prepared_by": self.prepared_by,
            "exclusions": list(self.exclusions),
            "maximum_priorities": self.maximum_priorities,
        }


@dataclass(frozen=True, slots=True)
class AssessmentArtifactInventoryItem:
    artifact_type: str
    artifact_id: str
    artifact_hash: str
    sequence_number: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "artifact_id": self.artifact_id,
            "artifact_hash": self.artifact_hash,
            "sequence_number": self.sequence_number,
        }


@dataclass(frozen=True, slots=True)
class AssessmentApplicationResult:
    request_hash: str
    demonstration: GovernanceAssessmentDemonstrationResult
    persistence: DemonstrationPersistenceResult
    application_hash: str
    schema_version: str = ASSESSMENT_APPLICATION_VERSION

    @property
    def hierarchy_key(self) -> str:
        return self.demonstration.hierarchy_key

    @property
    def completed(self) -> bool:
        return (
            self.demonstration.completed
            and self.persistence.completed
            and self.demonstration.demonstration_hash
            == self.persistence.demonstration_hash
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hierarchy_key": self.hierarchy_key,
            "completed": self.completed,
            "request_hash": self.request_hash,
            "demonstration_hash": (
                self.demonstration.demonstration_hash
            ),
            "persistence_hash": (
                self.persistence.persistence_hash
            ),
            "report_id": (
                self.demonstration.report_package.report_id
            ),
            "artifact_count": self.persistence.artifact_count,
            "application_hash": self.application_hash,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class AssessmentApplicationSummary:
    assessment: PersistedAssessmentRecord
    artifact_inventory: tuple[
        AssessmentArtifactInventoryItem, ...
    ]
    repository_chain_valid: bool
    summary_hash: str
    schema_version: str = ASSESSMENT_APPLICATION_VERSION

    @property
    def hierarchy_key(self) -> str:
        return self.assessment.hierarchy_key

    @property
    def artifact_count(self) -> int:
        return len(self.artifact_inventory)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hierarchy_key": self.hierarchy_key,
            "assessment": self.assessment.to_dict(),
            "artifact_inventory": [
                item.to_dict()
                for item in self.artifact_inventory
            ],
            "artifact_count": self.artifact_count,
            "repository_chain_valid": (
                self.repository_chain_valid
            ),
            "summary_hash": self.summary_hash,
            "schema_version": self.schema_version,
        }


class GovernanceAssessmentApplicationService:
    def __init__(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        demonstration_service: (
            GovernanceAssessmentDemonstrationService | None
        ) = None,
        persistence_service: (
            GovernanceAssessmentDemonstrationPersistenceService
            | None
        ) = None,
    ) -> None:
        self._repository = repository
        self._demonstration_service = (
            demonstration_service
            or GovernanceAssessmentDemonstrationService()
        )
        self._persistence_service = (
            persistence_service
            or GovernanceAssessmentDemonstrationPersistenceService(
                repository
            )
        )

    def execute(
        self,
        *,
        request: AssessmentExecutionRequest,
    ) -> AssessmentApplicationResult:
        request_hash = sha256_text(
            canonical_json(request.to_dict())
        )

        demonstration = self._demonstration_service.run(
            context=request.context,
            assessment_name=request.assessment_name,
            workflow_names=request.workflow_names,
            organizational_units=(
                request.organizational_units
            ),
            period_start=request.period_start,
            period_end=request.period_end,
            objectives=request.objectives,
            expected_outcomes=request.expected_outcomes,
            evidence_requirements=(
                request.evidence_requirements
            ),
            evidence_inputs=request.evidence_inputs,
            client_display_name=request.client_display_name,
            prepared_by=request.prepared_by,
            exclusions=request.exclusions,
            implementation_burdens=(
                request.implementation_burdens
            ),
            reversibility_scores=(
                request.reversibility_scores
            ),
            owner_roles=request.owner_roles,
            maximum_priorities=request.maximum_priorities,
        )

        if demonstration.hierarchy_key != (
            request.context.hierarchy_key
        ):
            raise AssessmentApplicationError(
                "demonstration hierarchy does not match request"
            )

        persistence = self._persistence_service.persist(
            demonstration=demonstration
        )

        if persistence.hierarchy_key != (
            request.context.hierarchy_key
        ):
            raise AssessmentApplicationError(
                "persistence hierarchy does not match request"
            )

        if persistence.demonstration_hash != (
            demonstration.demonstration_hash
        ):
            raise AssessmentApplicationError(
                "persistence does not reference the demonstration"
            )

        application_payload = {
            "hierarchy_key": request.context.hierarchy_key,
            "request_hash": request_hash,
            "demonstration_hash": (
                demonstration.demonstration_hash
            ),
            "persistence_hash": persistence.persistence_hash,
            "report_id": demonstration.report_package.report_id,
            "schema_version": ASSESSMENT_APPLICATION_VERSION,
        }

        return AssessmentApplicationResult(
            request_hash=request_hash,
            demonstration=demonstration,
            persistence=persistence,
            application_hash=sha256_text(
                canonical_json(application_payload)
            ),
        )

    def get_assessment(
        self,
        *,
        context: CommercialHierarchyContext,
    ) -> PersistedAssessmentRecord:
        return self._repository.get_assessment(
            context=context
        )

    def list_assessments(
        self,
        *,
        tenant_id: str,
        client_id: str | None = None,
        engagement_id: str | None = None,
    ) -> tuple[PersistedAssessmentRecord, ...]:
        return self._repository.list_assessments(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
        )

    def list_artifacts(
        self,
        *,
        context: CommercialHierarchyContext,
        artifact_type: str | None = None,
    ) -> tuple[ImmutableAssessmentArtifact, ...]:
        return self._repository.list_artifacts(
            context=context,
            artifact_type=artifact_type,
        )

    def summarize(
        self,
        *,
        context: CommercialHierarchyContext,
    ) -> AssessmentApplicationSummary:
        assessment = self.get_assessment(context=context)
        artifacts = self.list_artifacts(context=context)
        chain_valid = self._repository.verify_chain(
            context=context
        )

        inventory = tuple(
            AssessmentArtifactInventoryItem(
                artifact_type=artifact.artifact_type,
                artifact_id=artifact.artifact_id,
                artifact_hash=artifact.artifact_hash,
                sequence_number=artifact.sequence_number,
            )
            for artifact in artifacts
        )

        summary_payload = {
            "hierarchy_key": context.hierarchy_key,
            "assessment_record_hash": assessment.record_hash,
            "artifact_inventory": [
                item.to_dict()
                for item in inventory
            ],
            "repository_chain_valid": chain_valid,
            "schema_version": ASSESSMENT_APPLICATION_VERSION,
        }

        return AssessmentApplicationSummary(
            assessment=assessment,
            artifact_inventory=inventory,
            repository_chain_valid=chain_valid,
            summary_hash=sha256_text(
                canonical_json(summary_payload)
            ),
        )
