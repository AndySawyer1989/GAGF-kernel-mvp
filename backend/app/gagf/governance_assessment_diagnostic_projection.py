from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.governance_assessment_diagnostic_significance import (
    AssessmentDiagnosticSignificanceSummary,
    GovernanceAssessmentDiagnosticSignificanceService,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_evidence_intake import (
    AssessmentEvidenceIntakeResult,
    AssessmentEvidenceRecord,
    RejectedEvidenceRow,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    AssessmentFrictionSummary,
    ConstraintAggregation,
    ConstraintCategory,
    FrictionBand,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
    ImmutableAssessmentArtifact,
    canonical_json,
)


DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE = (
    "diagnostic-significance"
)

DIAGNOSTIC_PROJECTION_VERSION = "1.0.0"


class DiagnosticProjectionError(RuntimeError):
    """Raised when persisted assessment evidence cannot be projected."""


@dataclass(frozen=True, slots=True)
class GovernanceAssessmentDiagnosticProjectionResult:
    hierarchy_key: str
    diagnostic_summary: AssessmentDiagnosticSignificanceSummary
    artifact_id: str
    artifact_hash: str
    sequence_number: int
    repository_chain_valid: bool
    reused_existing: bool
    projection_version: str = DIAGNOSTIC_PROJECTION_VERSION

    @property
    def diagnosed_conditions(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            category.value
            for category
            in self.diagnostic_summary.diagnosed_conditions
        )

    @property
    def dominant_condition(
        self,
    ) -> str | None:
        value = self.diagnostic_summary.dominant_condition

        return (
            value.value
            if value is not None
            else None
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "hierarchy_key":
                self.hierarchy_key,
            "diagnosed_conditions":
                list(
                    self.diagnosed_conditions
                ),
            "dominant_condition":
                self.dominant_condition,
            "diagnostic_summary_hash":
                self.diagnostic_summary.summary_hash,
            "artifact_id":
                self.artifact_id,
            "artifact_hash":
                self.artifact_hash,
            "sequence_number":
                self.sequence_number,
            "repository_chain_valid":
                self.repository_chain_valid,
            "reused_existing":
                self.reused_existing,
            "projection_version":
                self.projection_version,
        }


class GovernanceAssessmentDiagnosticProjectionService:
    """
    Build diagnostic significance from already-persisted governed
    assessment evidence.

    The projection:

    1. Reads the immutable evidence-intake-batch artifact.
    2. Reads the immutable friction-summary artifact.
    3. Reconstructs the exact domain objects needed by
       GovernanceAssessmentDiagnosticSignificanceService.
    4. Computes diagnostic significance deterministically.
    5. Appends one immutable diagnostic-significance artifact.
    6. Verifies the repository chain after append.

    It does not alter or reinterpret the original evidence artifacts.
    """

    def __init__(
        self,
        *,
        significance_service: (
            GovernanceAssessmentDiagnosticSignificanceService
            | None
        ) = None,
    ) -> None:
        self._significance_service = (
            significance_service
            or GovernanceAssessmentDiagnosticSignificanceService()
        )

    def project(
        self,
        *,
        database_path: str | Path,
        context: CommercialHierarchyContext,
    ) -> GovernanceAssessmentDiagnosticProjectionResult:
        repository = GovernanceAssessmentRepository(
            database_path
        )

        if repository.verify_chain(
            context=context
        ) is not True:
            raise DiagnosticProjectionError(
                "assessment repository chain is invalid before "
                "diagnostic projection"
            )

        intake_artifact = self._require_single_artifact(
            repository=repository,
            context=context,
            artifact_type="evidence-intake-batch",
        )

        friction_artifact = self._require_single_artifact(
            repository=repository,
            context=context,
            artifact_type="friction-summary",
        )

        intake_results = self._reconstruct_intake_results(
            payload=intake_artifact.payload,
            expected_hierarchy=context.hierarchy_key,
        )

        friction_summary = self._reconstruct_friction_summary(
            payload=friction_artifact.payload,
            expected_hierarchy=context.hierarchy_key,
        )

        diagnostic_summary = (
            self._significance_service.classify(
                friction_summary=friction_summary,
                intake_results=intake_results,
            )
        )

        if (
            diagnostic_summary.hierarchy_key
            != context.hierarchy_key
        ):
            raise DiagnosticProjectionError(
                "diagnostic significance hierarchy does not match "
                "the persisted assessment"
            )

        payload = diagnostic_summary.to_dict()

        existing = repository.list_artifacts(
            context=context,
            artifact_type=(
                DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE
            ),
        )

        if existing:
            if len(existing) != 1:
                raise DiagnosticProjectionError(
                    "assessment contains multiple diagnostic-significance "
                    "artifacts"
                )

            artifact = existing[0]

            if canonical_json(
                artifact.payload
            ) != canonical_json(
                payload
            ):
                raise DiagnosticProjectionError(
                    "existing diagnostic-significance artifact does not "
                    "match deterministic projection"
                )

            reused_existing = True
        else:
            artifact = repository.append_artifact(
                context=context,
                artifact_type=(
                    DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE
                ),
                payload=payload,
            )

            reused_existing = False

        chain_valid = repository.verify_chain(
            context=context
        )

        if chain_valid is not True:
            raise DiagnosticProjectionError(
                "assessment repository chain is invalid after "
                "diagnostic projection"
            )

        return GovernanceAssessmentDiagnosticProjectionResult(
            hierarchy_key=context.hierarchy_key,
            diagnostic_summary=diagnostic_summary,
            artifact_id=artifact.artifact_id,
            artifact_hash=artifact.artifact_hash,
            sequence_number=artifact.sequence_number,
            repository_chain_valid=chain_valid,
            reused_existing=reused_existing,
        )

    def _require_single_artifact(
        self,
        *,
        repository: GovernanceAssessmentRepository,
        context: CommercialHierarchyContext,
        artifact_type: str,
    ) -> ImmutableAssessmentArtifact:
        artifacts = repository.list_artifacts(
            context=context,
            artifact_type=artifact_type,
        )

        if len(artifacts) != 1:
            raise DiagnosticProjectionError(
                f"assessment requires exactly one {artifact_type} artifact"
            )

        return artifacts[0]

    def _reconstruct_intake_results(
        self,
        *,
        payload: Any,
        expected_hierarchy: str,
    ) -> tuple[
        AssessmentEvidenceIntakeResult,
        ...,
    ]:
        if not isinstance(
            payload,
            Mapping,
        ):
            raise DiagnosticProjectionError(
                "persisted evidence-intake-batch is not an object"
            )

        raw_results = payload.get(
            "intake_results"
        )

        if not isinstance(
            raw_results,
            list,
        ):
            raise DiagnosticProjectionError(
                "persisted evidence-intake-batch does not contain "
                "intake_results"
            )

        if not raw_results:
            raise DiagnosticProjectionError(
                "persisted evidence-intake-batch is empty"
            )

        return tuple(
            self._reconstruct_intake_result(
                raw_result=raw_result,
                expected_hierarchy=expected_hierarchy,
            )
            for raw_result
            in raw_results
        )

    def _reconstruct_intake_result(
        self,
        *,
        raw_result: Any,
        expected_hierarchy: str,
    ) -> AssessmentEvidenceIntakeResult:
        if not isinstance(
            raw_result,
            Mapping,
        ):
            raise DiagnosticProjectionError(
                "persisted intake result is not an object"
            )

        hierarchy_key = self._required_string(
            raw_result,
            "hierarchy_key",
        )

        if hierarchy_key != expected_hierarchy:
            raise DiagnosticProjectionError(
                "persisted intake hierarchy does not match assessment"
            )

        raw_source = raw_result.get(
            "source"
        )

        if not isinstance(
            raw_source,
            Mapping,
        ):
            raise DiagnosticProjectionError(
                "persisted intake result source is invalid"
            )

        try:
            source_kind = EvidenceSourceKind(
                self._required_string(
                    raw_source,
                    "kind",
                )
            )
        except ValueError as exc:
            raise DiagnosticProjectionError(
                "persisted intake result contains unsupported "
                "evidence source kind"
            ) from exc

        source = EvidenceSourceReference(
            source_id=self._required_string(
                raw_source,
                "source_id",
            ),
            kind=source_kind,
            display_name=self._required_string(
                raw_source,
                "display_name",
            ),
            source_location=(
                str(
                    raw_source[
                        "source_location"
                    ]
                )
                if raw_source.get(
                    "source_location"
                ) is not None
                else None
            ),
        )

        raw_records = raw_result.get(
            "accepted_records"
        )

        if not isinstance(
            raw_records,
            list,
        ):
            raise DiagnosticProjectionError(
                "persisted intake result accepted_records is invalid"
            )

        records = tuple(
            self._reconstruct_record(
                raw_record=raw_record,
                expected_hierarchy=expected_hierarchy,
            )
            for raw_record
            in raw_records
        )

        raw_rejected = raw_result.get(
            "rejected_rows",
            [],
        )

        if not isinstance(
            raw_rejected,
            list,
        ):
            raise DiagnosticProjectionError(
                "persisted intake result rejected_rows is invalid"
            )

        rejected = tuple(
            self._reconstruct_rejected_row(
                raw_row
            )
            for raw_row
            in raw_rejected
        )

        total_rows = self._required_int(
            raw_result,
            "total_rows",
        )

        intake_hash = self._required_string(
            raw_result,
            "intake_hash",
        )

        return AssessmentEvidenceIntakeResult(
            source=source,
            hierarchy_key=hierarchy_key,
            accepted_records=records,
            rejected_rows=rejected,
            total_rows=total_rows,
            intake_hash=intake_hash,
        )

    def _reconstruct_record(
        self,
        *,
        raw_record: Any,
        expected_hierarchy: str,
    ) -> AssessmentEvidenceRecord:
        if not isinstance(
            raw_record,
            Mapping,
        ):
            raise DiagnosticProjectionError(
                "persisted accepted evidence record is not an object"
            )

        tenant_id = self._required_string(
            raw_record,
            "tenant_id",
        )

        client_id = self._required_string(
            raw_record,
            "client_id",
        )

        engagement_id = self._required_string(
            raw_record,
            "engagement_id",
        )

        assessment_id = self._required_string(
            raw_record,
            "assessment_id",
        )

        hierarchy_key = "/".join(
            (
                tenant_id,
                client_id,
                engagement_id,
                assessment_id,
            )
        )

        if hierarchy_key != expected_hierarchy:
            raise DiagnosticProjectionError(
                "persisted evidence record hierarchy does not match "
                "assessment"
            )

        raw_attributes = raw_record.get(
            "attributes"
        )

        if not isinstance(
            raw_attributes,
            Mapping,
        ):
            raise DiagnosticProjectionError(
                "persisted evidence record attributes are invalid"
            )

        attributes = {
            str(key): str(value)
            for key, value
            in raw_attributes.items()
        }

        occurred_at_text = self._required_string(
            raw_record,
            "occurred_at",
        )

        try:
            occurred_at = datetime.fromisoformat(
                occurred_at_text
            )
        except ValueError as exc:
            raise DiagnosticProjectionError(
                "persisted evidence record occurred_at is invalid"
            ) from exc

        if occurred_at.tzinfo is None:
            raise DiagnosticProjectionError(
                "persisted evidence record occurred_at lacks timezone"
            )

        return AssessmentEvidenceRecord(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            source_id=self._required_string(
                raw_record,
                "source_id",
            ),
            event_id=self._required_string(
                raw_record,
                "event_id",
            ),
            event_type=self._required_string(
                raw_record,
                "event_type",
            ),
            occurred_at=occurred_at,
            attributes=attributes,
            row_number=self._required_int(
                raw_record,
                "row_number",
            ),
            evidence_hash=self._required_string(
                raw_record,
                "evidence_hash",
            ),
        )

    def _reconstruct_rejected_row(
        self,
        raw_row: Any,
    ) -> RejectedEvidenceRow:
        if not isinstance(
            raw_row,
            Mapping,
        ):
            raise DiagnosticProjectionError(
                "persisted rejected evidence row is invalid"
            )

        event_id = raw_row.get(
            "event_id"
        )

        return RejectedEvidenceRow(
            row_number=self._required_int(
                raw_row,
                "row_number",
            ),
            event_id=(
                str(event_id)
                if event_id is not None
                else None
            ),
            reason=self._required_string(
                raw_row,
                "reason",
            ),
        )

    def _reconstruct_friction_summary(
        self,
        *,
        payload: Any,
        expected_hierarchy: str,
    ) -> AssessmentFrictionSummary:
        if not isinstance(
            payload,
            Mapping,
        ):
            raise DiagnosticProjectionError(
                "persisted friction-summary is not an object"
            )

        hierarchy_key = self._required_string(
            payload,
            "hierarchy_key",
        )

        if hierarchy_key != expected_hierarchy:
            raise DiagnosticProjectionError(
                "persisted friction summary hierarchy does not match "
                "assessment"
            )

        raw_aggregations = payload.get(
            "constraint_aggregations"
        )

        if not isinstance(
            raw_aggregations,
            list,
        ):
            raise DiagnosticProjectionError(
                "persisted friction summary constraint_aggregations "
                "is invalid"
            )

        aggregations = tuple(
            self._reconstruct_aggregation(
                raw
            )
            for raw
            in raw_aggregations
        )

        raw_dominant = payload.get(
            "dominant_constraint"
        )

        dominant = (
            ConstraintCategory(
                raw_dominant
            )
            if raw_dominant is not None
            else None
        )

        raw_unrecognized = payload.get(
            "unrecognized_event_types",
            [],
        )

        if not isinstance(
            raw_unrecognized,
            list,
        ):
            raise DiagnosticProjectionError(
                "persisted friction summary unrecognized_event_types "
                "is invalid"
            )

        return AssessmentFrictionSummary(
            tenant_id=self._required_string(
                payload,
                "tenant_id",
            ),
            client_id=self._required_string(
                payload,
                "client_id",
            ),
            engagement_id=self._required_string(
                payload,
                "engagement_id",
            ),
            assessment_id=self._required_string(
                payload,
                "assessment_id",
            ),
            constraint_aggregations=aggregations,
            total_evidence_events=self._required_int(
                payload,
                "total_evidence_events",
            ),
            recognized_constraint_events=self._required_int(
                payload,
                "recognized_constraint_events",
            ),
            unrecognized_event_count=self._required_int(
                payload,
                "unrecognized_event_count",
            ),
            unique_work_item_count=self._required_int(
                payload,
                "unique_work_item_count",
            ),
            total_friction_score=self._required_float(
                payload,
                "total_friction_score",
            ),
            average_friction_per_event=self._required_float(
                payload,
                "average_friction_per_event",
            ),
            dominant_constraint=dominant,
            unrecognized_event_types=tuple(
                str(value)
                for value
                in raw_unrecognized
            ),
            summary_hash=self._required_string(
                payload,
                "summary_hash",
            ),
        )

    def _reconstruct_aggregation(
        self,
        raw: Any,
    ) -> ConstraintAggregation:
        if not isinstance(
            raw,
            Mapping,
        ):
            raise DiagnosticProjectionError(
                "persisted constraint aggregation is not an object"
            )

        try:
            category = ConstraintCategory(
                self._required_string(
                    raw,
                    "category",
                )
            )
        except ValueError as exc:
            raise DiagnosticProjectionError(
                "persisted constraint aggregation category is invalid"
            ) from exc

        try:
            band = FrictionBand(
                self._required_string(
                    raw,
                    "band",
                )
            )
        except ValueError as exc:
            raise DiagnosticProjectionError(
                "persisted constraint aggregation band is invalid"
            ) from exc

        try:
            first_occurred_at = datetime.fromisoformat(
                self._required_string(
                    raw,
                    "first_occurred_at",
                )
            )

            last_occurred_at = datetime.fromisoformat(
                self._required_string(
                    raw,
                    "last_occurred_at",
                )
            )
        except ValueError as exc:
            raise DiagnosticProjectionError(
                "persisted constraint aggregation timestamp is invalid"
            ) from exc

        return ConstraintAggregation(
            category=category,
            event_count=self._required_int(
                raw,
                "event_count",
            ),
            unique_work_item_count=self._required_int(
                raw,
                "unique_work_item_count",
            ),
            first_occurred_at=first_occurred_at,
            last_occurred_at=last_occurred_at,
            weight=self._required_float(
                raw,
                "weight",
            ),
            friction_score=self._required_float(
                raw,
                "friction_score",
            ),
            event_share=self._required_float(
                raw,
                "event_share",
            ),
            band=band,
        )

    def _required_string(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> str:
        value = payload.get(
            field_name
        )

        if (
            not isinstance(
                value,
                str,
            )
            or not value.strip()
        ):
            raise DiagnosticProjectionError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()

    def _required_int(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> int:
        value = payload.get(
            field_name
        )

        if (
            not isinstance(
                value,
                int,
            )
            or isinstance(
                value,
                bool,
            )
        ):
            raise DiagnosticProjectionError(
                f"{field_name} must be an integer"
            )

        return value

    def _required_float(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> float:
        value = payload.get(
            field_name
        )

        if (
            not isinstance(
                value,
                (int, float),
            )
            or isinstance(
                value,
                bool,
            )
        ):
            raise DiagnosticProjectionError(
                f"{field_name} must be numeric"
            )

        return float(
            value
        )