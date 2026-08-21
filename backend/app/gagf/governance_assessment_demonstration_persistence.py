from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_demonstration import (
    GovernanceAssessmentDemonstrationResult,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    AssessmentAlreadyExistsError,
    AssessmentRecordNotFoundError,
    GovernanceAssessmentRepository,
    ImmutableAssessmentArtifact,
    PersistedAssessmentRecord,
)


DEMONSTRATION_PERSISTENCE_VERSION = "1.0.0"
ARTIFACT_TYPE_ORDER = (
    "scope-configuration",
    "evidence-intake-batch",
    "evidence-quality",
    "friction-summary",
    "governance-debt-score",
    "intervention-plan",
    "assessment-roadmap",
    "executive-projection",
    "client-report-package",
    "demonstration-manifest",
)


class DemonstrationPersistenceError(RuntimeError):
    """Raised when demonstration artifacts cannot be persisted."""


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


@dataclass(frozen=True, slots=True)
class PersistedDemonstrationArtifact:
    artifact_type: str
    artifact_id: str
    artifact_hash: str
    sequence_number: int
    reused_existing: bool

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PersistedDemonstrationArtifact):
            return NotImplemented

        return (
            self.artifact_type,
            self.artifact_id,
            self.artifact_hash,
            self.sequence_number,
        ) == (
            other.artifact_type,
            other.artifact_id,
            other.artifact_hash,
            other.sequence_number,
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.artifact_type,
                self.artifact_id,
                self.artifact_hash,
                self.sequence_number,
            )
        )
    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "artifact_id": self.artifact_id,
            "artifact_hash": self.artifact_hash,
            "sequence_number": self.sequence_number,
            "reused_existing": self.reused_existing,
        }


@dataclass(frozen=True, slots=True)
class DemonstrationPersistenceResult:
    assessment: PersistedAssessmentRecord
    artifacts: tuple[PersistedDemonstrationArtifact, ...]
    demonstration_hash: str
    repository_chain_valid: bool
    persistence_hash: str
    schema_version: str = DEMONSTRATION_PERSISTENCE_VERSION

    @property
    def hierarchy_key(self) -> str:
        return self.assessment.hierarchy_key

    @property
    def artifact_count(self) -> int:
        return len(self.artifacts)

    @property
    def reused_artifact_count(self) -> int:
        return sum(
            1
            for artifact in self.artifacts
            if artifact.reused_existing
        )

    @property
    def completed(self) -> bool:
        return (
            self.repository_chain_valid
            and self.artifact_count > 0
            and bool(self.persistence_hash)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hierarchy_key": self.hierarchy_key,
            "assessment": self.assessment.to_dict(),
            "artifacts": [
                artifact.to_dict()
                for artifact in self.artifacts
            ],
            "artifact_count": self.artifact_count,
            "reused_artifact_count": (
                self.reused_artifact_count
            ),
            "demonstration_hash": self.demonstration_hash,
            "repository_chain_valid": (
                self.repository_chain_valid
            ),
            "completed": self.completed,
            "persistence_hash": self.persistence_hash,
            "schema_version": self.schema_version,
        }


class GovernanceAssessmentDemonstrationPersistenceService:
    def __init__(
        self,
        repository: GovernanceAssessmentRepository,
    ) -> None:
        self._repository = repository

    ARTIFACT_ORDER = (
        "scope-configuration",
        "evidence-intake-batch",
        "evidence-quality",
        "friction-summary",
        "governance-debt-score",
        "intervention-plan",
        "assessment-roadmap",
        "executive-projection",
        "client-report-package",
        "demonstration-manifest",
    )

    def persist(
        self,
        *,
        demonstration: GovernanceAssessmentDemonstrationResult,
    ) -> DemonstrationPersistenceResult:
        if not demonstration.completed:
            raise DemonstrationPersistenceError(
                "demonstration must be complete before persistence"
            )

        context = CommercialHierarchyContext(
            tenant_id=demonstration.configuration.tenant_id,
            client_id=demonstration.configuration.client_id,
            engagement_id=(
                demonstration.configuration.engagement_id
            ),
            assessment_id=(
                demonstration.configuration.assessment_id
            ),
        )

        assessment = self._get_or_create_assessment(
            repository=self._repository,
            context=context,
            demonstration=demonstration,
        )

        artifact_payloads = self._artifact_payloads(
            demonstration
        )

        persisted = tuple(
            self._append_or_reuse(
                repository=self._repository,
                context=context,
                artifact_type=artifact_type,
                payload=artifact_payloads[artifact_type],
            )
            for artifact_type in self.ARTIFACT_ORDER
        )

        stored_artifacts = self._repository.list_artifacts(
            context=context
        )

        self._validate_persisted_artifacts(
            demonstration=demonstration,
            persisted=persisted,
            stored_artifacts=stored_artifacts,
        )

        chain_verified = self._repository.verify_chain(
            context=context
        )

        persistence_payload = {
            "hierarchy_key": context.hierarchy_key,
            "demonstration_hash": (
                demonstration.demonstration_hash
            ),
            "assessment_identity": {
                "tenant_id": assessment.tenant_id,
                "client_id": assessment.client_id,
                "engagement_id": assessment.engagement_id,
                "assessment_id": assessment.assessment_id,
                "assessment_name": assessment.assessment_name,
                "status": assessment.status,
            },
            "artifacts": [
                {
                    "artifact_type": artifact.artifact_type,
                    "artifact_id": artifact.artifact_id,
                    "artifact_hash": artifact.artifact_hash,
                    "sequence_number": artifact.sequence_number,
                }
                for artifact in persisted
            ],
            "repository_chain_valid": chain_verified,
            "schema_version": DEMONSTRATION_PERSISTENCE_VERSION,
        }

        return DemonstrationPersistenceResult(
            assessment=assessment,
            artifacts=persisted,
            demonstration_hash=(
                demonstration.demonstration_hash
            ),
            repository_chain_valid=chain_verified,
            persistence_hash=sha256_text(
                canonical_json(persistence_payload)
            ),
        )

    def _get_or_create_assessment(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        context: CommercialHierarchyContext,
        demonstration: GovernanceAssessmentDemonstrationResult,
    ) -> PersistedAssessmentRecord:
        try:
            existing = self._repository.get_assessment(
                context=context
            )
        except AssessmentRecordNotFoundError:
            try:
                return self._repository.create_assessment(
                    context=context,
                    assessment_name=(
                        demonstration.configuration.assessment_name
                    ),
                    status="complete",
                )
            except AssessmentAlreadyExistsError:
                return self._repository.get_assessment(
                    context=context
                )

        if existing.assessment_name != (
            demonstration.configuration.assessment_name
        ):
            raise DemonstrationPersistenceError(
                "persisted assessment name does not match demonstration"
            )

        return existing

    def _artifact_payloads(
        self,
        demonstration: GovernanceAssessmentDemonstrationResult,
    ) -> dict[str, Any]:
        return {
            "scope-configuration": (
                demonstration.configuration.to_dict()
            ),
            "evidence-intake-batch": {
                "intake_results": [
                    result.to_dict()
                    for result in demonstration.intake_results
                ],
            },
            "evidence-quality": (
                demonstration.quality_summary.to_dict()
            ),
            "friction-summary": (
                demonstration.friction_summary.to_dict()
            ),
            "governance-debt-score": (
                demonstration.debt_score.to_dict()
            ),
            "intervention-plan": (
                demonstration.intervention_plan.to_dict()
            ),
            "assessment-roadmap": (
                demonstration.roadmap.to_dict()
            ),
            "executive-projection": (
                demonstration.executive_projection.to_dict()
            ),
            "client-report-package": (
                demonstration.report_package.to_dict()
            ),
            "demonstration-manifest": {
                "hierarchy_key": demonstration.hierarchy_key,
                "artifact_commitments": dict(
                    demonstration.artifact_commitments
                ),
                "demonstration_hash": (
                    demonstration.demonstration_hash
                ),
                "completed": demonstration.completed,
                "schema_version": demonstration.schema_version,
            },
        }

    def _append_or_reuse(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        context: CommercialHierarchyContext,
        artifact_type: str,
        payload: Any,
    ) -> PersistedDemonstrationArtifact:
        payload_json = canonical_json(payload)
        expected_hash = sha256_text(payload_json)

        artifacts_of_type = self._repository.list_artifacts(
            context=context,
            artifact_type=artifact_type,
        )

        conflicting = tuple(
            artifact
            for artifact in artifacts_of_type
            if artifact.artifact_hash != expected_hash
        )

        if conflicting:
            raise DemonstrationPersistenceError(
                "repository contains conflicting artifact payload "
                f"for type: {artifact_type}"
            )

        existing = tuple(
            artifact
            for artifact in artifacts_of_type
            if artifact.artifact_hash == expected_hash
        )

        if len(existing) > 1:
            raise DemonstrationPersistenceError(
                "repository contains duplicate matching artifacts"
            )

        if existing:
            artifact = existing[0]
            return self._persisted_artifact(
                artifact=artifact,
                reused_existing=True,
            )

        artifact = self._repository.append_artifact(
            context=context,
            artifact_type=artifact_type,
            payload=payload,
        )

        return self._persisted_artifact(
            artifact=artifact,
            reused_existing=False,
        )

    def _persisted_artifact(
        self,
        *,
        artifact: ImmutableAssessmentArtifact,
        reused_existing: bool,
    ) -> PersistedDemonstrationArtifact:
        return PersistedDemonstrationArtifact(
            artifact_type=artifact.artifact_type,
            artifact_id=artifact.artifact_id,
            artifact_hash=artifact.artifact_hash,
            sequence_number=artifact.sequence_number,
            reused_existing=reused_existing,
        )

    def _validate_persisted_artifacts(
        self,
        *,
        demonstration: GovernanceAssessmentDemonstrationResult,
        persisted: tuple[PersistedDemonstrationArtifact, ...],
        stored_artifacts: tuple[ImmutableAssessmentArtifact, ...],
    ) -> None:
        if tuple(
            artifact.artifact_type
            for artifact in persisted
        ) != self.ARTIFACT_ORDER:
            raise DemonstrationPersistenceError(
                "persisted artifact order is invalid"
            )

        persisted_ids = {
            artifact.artifact_id
            for artifact in persisted
        }

        if len(persisted_ids) != len(persisted):
            raise DemonstrationPersistenceError(
                "persisted artifacts contain duplicate identifiers"
            )

        stored_by_id = {
            artifact.artifact_id: artifact
            for artifact in stored_artifacts
        }

        for artifact in persisted:
            stored = stored_by_id.get(artifact.artifact_id)

            if stored is None:
                raise DemonstrationPersistenceError(
                    "persisted artifact could not be retrieved"
                )

            if stored.artifact_hash != artifact.artifact_hash:
                raise DemonstrationPersistenceError(
                    "persisted artifact hash does not match storage"
                )

        manifest = stored_by_id[persisted[-1].artifact_id].payload

        if manifest["demonstration_hash"] != (
            demonstration.demonstration_hash
        ):
            raise DemonstrationPersistenceError(
                "stored demonstration hash is invalid"
            )

        if manifest["artifact_commitments"] != (
            demonstration.artifact_commitments
        ):
            raise DemonstrationPersistenceError(
                "stored artifact commitments are invalid"
            )









