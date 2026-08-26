from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)
from backend.app.gagf.governance_assessment_structural_importance import (
    AssessmentStructuralImportanceEvidenceSummary,
    StructuralConditionEvidence,
)


STRUCTURAL_IMPORTANCE_CLASSIFICATION_VERSION = "1.0.0"

STRUCTURAL_IMPORTANCE_CLASSIFICATION_AUTHORITY = (
    "GAGF_FIP_ONLY"
)


class StructuralImportanceClassificationError(
    RuntimeError
):
    """
    Raised when structural-importance evidence cannot
    be classified deterministically.
    """


class StructuralImportanceLevel(
    str,
    Enum,
):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    LIMITED = "LIMITED"


@dataclass(frozen=True, slots=True)
class StructuralEvidenceSufficiency:
    event_support: bool
    process_support: bool
    temporal_support: bool
    quality_observed: bool

    @property
    def sufficient(
        self,
    ) -> bool:
        return all(
            (
                self.event_support,
                self.process_support,
                self.temporal_support,
                self.quality_observed,
            )
        )

    @property
    def support_count(
        self,
    ) -> int:
        return sum(
            (
                self.event_support,
                self.process_support,
                self.temporal_support,
                self.quality_observed,
            )
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "event_support":
                self.event_support,
            "process_support":
                self.process_support,
            "temporal_support":
                self.temporal_support,
            "quality_observed":
                self.quality_observed,
            "support_count":
                self.support_count,
            "sufficient":
                self.sufficient,
        }


@dataclass(frozen=True, slots=True)
class StructuralImportanceAxes:
    burden: bool
    process_penetration: bool
    temporal_precedence: bool
    downstream_association: bool
    recurrence: bool
    context_propagation: bool
    evidence_quality: bool

    @property
    def active_count(
        self,
    ) -> int:
        return sum(
            (
                self.burden,
                self.process_penetration,
                self.temporal_precedence,
                self.downstream_association,
                self.recurrence,
                self.context_propagation,
                self.evidence_quality,
            )
        )

    @property
    def active_axes(
        self,
    ) -> tuple[str, ...]:
        values: list[str] = []

        if self.burden:
            values.append(
                "burden"
            )

        if self.process_penetration:
            values.append(
                "process_penetration"
            )

        if self.temporal_precedence:
            values.append(
                "temporal_precedence"
            )

        if self.downstream_association:
            values.append(
                "downstream_association"
            )

        if self.recurrence:
            values.append(
                "recurrence"
            )

        if self.context_propagation:
            values.append(
                "context_propagation"
            )

        if self.evidence_quality:
            values.append(
                "evidence_quality"
            )

        return tuple(
            values
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "burden":
                self.burden,
            "process_penetration":
                self.process_penetration,
            "temporal_precedence":
                self.temporal_precedence,
            "downstream_association":
                self.downstream_association,
            "recurrence":
                self.recurrence,
            "context_propagation":
                self.context_propagation,
            "evidence_quality":
                self.evidence_quality,
            "active_count":
                self.active_count,
            "active_axes":
                list(
                    self.active_axes
                ),
        }


@dataclass(frozen=True, slots=True)
class StructuralImportanceClassification:
    category: str
    level: StructuralImportanceLevel
    sufficiency: StructuralEvidenceSufficiency
    axes: StructuralImportanceAxes
    event_count: int
    event_share: float
    friction_score: float
    unique_work_item_count: int
    unique_team_count: int
    unique_lifecycle_count: int
    active_day_count: int
    precedence_rate: float
    downstream_event_count: int
    downstream_constraint_count: int
    mean_evidence_quality: float | None
    evidence_hash: str
    classification_hash: str

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "category":
                self.category,
            "level":
                self.level.value,
            "sufficiency":
                self.sufficiency.to_dict(),
            "axes":
                self.axes.to_dict(),
            "event_count":
                self.event_count,
            "event_share":
                self.event_share,
            "friction_score":
                self.friction_score,
            "unique_work_item_count":
                self.unique_work_item_count,
            "unique_team_count":
                self.unique_team_count,
            "unique_lifecycle_count":
                self.unique_lifecycle_count,
            "active_day_count":
                self.active_day_count,
            "precedence_rate":
                self.precedence_rate,
            "downstream_event_count":
                self.downstream_event_count,
            "downstream_constraint_count":
                self.downstream_constraint_count,
            "mean_evidence_quality":
                self.mean_evidence_quality,
            "evidence_hash":
                self.evidence_hash,
            "classification_hash":
                self.classification_hash,
        }


@dataclass(frozen=True, slots=True)
class AssessmentStructuralImportanceClassificationSummary:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    conditions: tuple[
        StructuralImportanceClassification,
        ...,
    ]
    high_importance_conditions: tuple[
        str,
        ...,
    ]
    moderate_importance_conditions: tuple[
        str,
        ...,
    ]
    low_importance_conditions: tuple[
        str,
        ...,
    ]
    limited_evidence_conditions: tuple[
        str,
        ...,
    ]
    summary_hash: str
    authority: str = (
        STRUCTURAL_IMPORTANCE_CLASSIFICATION_AUTHORITY
    )
    schema_version: str = (
        STRUCTURAL_IMPORTANCE_CLASSIFICATION_VERSION
    )

    @property
    def hierarchy_key(
        self,
    ) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "tenant_id":
                self.tenant_id,
            "client_id":
                self.client_id,
            "engagement_id":
                self.engagement_id,
            "assessment_id":
                self.assessment_id,
            "hierarchy_key":
                self.hierarchy_key,
            "conditions": [
                condition.to_dict()
                for condition
                in self.conditions
            ],
            "high_importance_conditions":
                list(
                    self.high_importance_conditions
                ),
            "moderate_importance_conditions":
                list(
                    self.moderate_importance_conditions
                ),
            "low_importance_conditions":
                list(
                    self.low_importance_conditions
                ),
            "limited_evidence_conditions":
                list(
                    self.limited_evidence_conditions
                ),
            "summary_hash":
                self.summary_hash,
            "authority":
                self.authority,
            "schema_version":
                self.schema_version,
        }


class GovernanceAssessmentStructuralImportanceClassificationService:
    """
    Deterministically classify the strength of
    structural-importance evidence.

    HIGH does not mean root cause.
    MODERATE does not mean secondary cause.

    LOW means sufficient evidence supports low
    observed structural importance.

    LIMITED means evidence is insufficient to
    confidently judge structural importance.

    Temporal precedence remains observational.
    Downstream association remains observational.

    No classification authorizes intervention.
    """

    def classify(
        self,
        *,
        structural_summary: (
            AssessmentStructuralImportanceEvidenceSummary
        ),
    ) -> AssessmentStructuralImportanceClassificationSummary:
        classifications = tuple(
            self._classify_condition(
                condition
            )
            for condition
            in sorted(
                structural_summary.conditions,
                key=lambda item:
                    item.category.value,
            )
        )

        high = tuple(
            condition.category
            for condition
            in classifications
            if condition.level
            == StructuralImportanceLevel.HIGH
        )

        moderate = tuple(
            condition.category
            for condition
            in classifications
            if condition.level
            == StructuralImportanceLevel.MODERATE
        )

        low = tuple(
            condition.category
            for condition
            in classifications
            if condition.level
            == StructuralImportanceLevel.LOW
        )

        limited = tuple(
            condition.category
            for condition
            in classifications
            if condition.level
            == StructuralImportanceLevel.LIMITED
        )

        summary_payload = {
            "tenant_id":
                structural_summary.tenant_id,
            "client_id":
                structural_summary.client_id,
            "engagement_id":
                structural_summary.engagement_id,
            "assessment_id":
                structural_summary.assessment_id,
            "hierarchy_key":
                structural_summary.hierarchy_key,
            "conditions": [
                condition.to_dict()
                for condition
                in classifications
            ],
            "high_importance_conditions":
                list(
                    high
                ),
            "moderate_importance_conditions":
                list(
                    moderate
                ),
            "low_importance_conditions":
                list(
                    low
                ),
            "limited_evidence_conditions":
                list(
                    limited
                ),
            "authority":
                STRUCTURAL_IMPORTANCE_CLASSIFICATION_AUTHORITY,
            "schema_version":
                STRUCTURAL_IMPORTANCE_CLASSIFICATION_VERSION,
        }

        summary_hash = sha256_text(
            canonical_json(
                summary_payload
            )
        )

        return (
            AssessmentStructuralImportanceClassificationSummary(
                tenant_id=(
                    structural_summary.tenant_id
                ),
                client_id=(
                    structural_summary.client_id
                ),
                engagement_id=(
                    structural_summary.engagement_id
                ),
                assessment_id=(
                    structural_summary.assessment_id
                ),
                conditions=classifications,
                high_importance_conditions=high,
                moderate_importance_conditions=moderate,
                low_importance_conditions=low,
                limited_evidence_conditions=limited,
                summary_hash=summary_hash,
            )
        )

    def _classify_condition(
        self,
        condition: StructuralConditionEvidence,
    ) -> StructuralImportanceClassification:
        sufficiency = (
            self._evaluate_sufficiency(
                condition
            )
        )

        axes = (
            self._evaluate_axes(
                condition
            )
        )

        level = (
            self._classify_level(
                sufficiency=sufficiency,
                axes=axes,
            )
        )

        category = (
            condition.category.value
        )

        classification_payload = {
            "category":
                category,
            "level":
                level.value,
            "sufficiency":
                sufficiency.to_dict(),
            "axes":
                axes.to_dict(),
            "event_count":
                condition.burden.event_count,
            "event_share":
                condition.burden.event_share,
            "friction_score":
                condition.burden.friction_score,
            "unique_work_item_count":
                condition.penetration.unique_work_item_count,
            "unique_team_count":
                condition.penetration.unique_team_count,
            "unique_lifecycle_count":
                condition.penetration.unique_lifecycle_count,
            "active_day_count":
                condition.penetration.active_day_count,
            "precedence_rate":
                condition.temporal.precedence_rate,
            "downstream_event_count":
                condition.temporal.downstream_event_count,
            "downstream_constraint_count":
                condition.temporal.downstream_constraint_count,
            "mean_evidence_quality":
                condition.support.mean_evidence_quality,
            "evidence_hash":
                condition.evidence_hash,
        }

        classification_hash = sha256_text(
            canonical_json(
                classification_payload
            )
        )

        return StructuralImportanceClassification(
            category=category,
            level=level,
            sufficiency=sufficiency,
            axes=axes,
            event_count=(
                condition.burden.event_count
            ),
            event_share=(
                condition.burden.event_share
            ),
            friction_score=(
                condition.burden.friction_score
            ),
            unique_work_item_count=(
                condition.penetration.unique_work_item_count
            ),
            unique_team_count=(
                condition.penetration.unique_team_count
            ),
            unique_lifecycle_count=(
                condition.penetration.unique_lifecycle_count
            ),
            active_day_count=(
                condition.penetration.active_day_count
            ),
            precedence_rate=(
                condition.temporal.precedence_rate
            ),
            downstream_event_count=(
                condition.temporal.downstream_event_count
            ),
            downstream_constraint_count=(
                condition.temporal.downstream_constraint_count
            ),
            mean_evidence_quality=(
                condition.support.mean_evidence_quality
            ),
            evidence_hash=(
                condition.evidence_hash
            ),
            classification_hash=(
                classification_hash
            ),
        )

    def _evaluate_sufficiency(
        self,
        condition: StructuralConditionEvidence,
    ) -> StructuralEvidenceSufficiency:
        return StructuralEvidenceSufficiency(
            event_support=(
                condition.burden.event_count
                >= 3
            ),
            process_support=(
                condition.penetration.unique_work_item_count
                >= 2
            ),
            temporal_support=(
                condition.penetration.active_day_count
                >= 2
            ),
            quality_observed=(
                condition.support.mean_evidence_quality
                is not None
            ),
        )

    def _evaluate_axes(
        self,
        condition: StructuralConditionEvidence,
    ) -> StructuralImportanceAxes:
        burden = (
            condition.burden.event_count
            >= 2
            and
            condition.burden.event_share
            >= 0.10
        )

        process_penetration = (
            condition.penetration.unique_work_item_count
            >= 2
            and
            condition.penetration.unique_lifecycle_count
            >= 2
        )

        temporal_precedence = (
            condition.temporal.precedence_opportunity_count
            >= 2
            and
            condition.temporal.precedence_rate
            >= 0.50
        )

        downstream_association = (
            condition.temporal.downstream_event_count
            >= 2
            and
            condition.temporal.downstream_constraint_count
            >= 1
        )

        # Recurrence must be stronger than the minimum
        # observation required merely to judge the condition.
        recurrence = (
            condition.burden.event_count
            >= 4
            and
            condition.penetration.active_day_count
            >= 3
        )

        context_propagation = (
            condition.penetration.unique_team_count
            >= 2
            or
            condition.support.scope_breadth_count
            >= 2
        )

        evidence_quality = (
            condition.support.mean_evidence_quality
            is not None
            and
            condition.support.mean_evidence_quality
            >= 0.80
        )

        return StructuralImportanceAxes(
            burden=burden,
            process_penetration=(
                process_penetration
            ),
            temporal_precedence=(
                temporal_precedence
            ),
            downstream_association=(
                downstream_association
            ),
            recurrence=recurrence,
            context_propagation=(
                context_propagation
            ),
            evidence_quality=(
                evidence_quality
            ),
        )

    def _classify_level(
        self,
        *,
        sufficiency: StructuralEvidenceSufficiency,
        axes: StructuralImportanceAxes,
    ) -> StructuralImportanceLevel:
        if not sufficiency.sufficient:
            return (
                StructuralImportanceLevel.LIMITED
            )

        structural_path_support = (
            axes.temporal_precedence
            or
            axes.downstream_association
        )

        structural_reach_support = (
            axes.burden
            or
            axes.process_penetration
        )

        if (
            axes.active_count >= 5
            and
            axes.evidence_quality
            and
            structural_path_support
            and
            structural_reach_support
        ):
            return (
                StructuralImportanceLevel.HIGH
            )

        if axes.active_count >= 3:
            return (
                StructuralImportanceLevel.MODERATE
            )

        low_structural_reach = (
            not axes.burden
            and
            not axes.process_penetration
            and
            not axes.temporal_precedence
            and
            not axes.downstream_association
            and
            not axes.recurrence
            and
            not axes.context_propagation
        )

        if low_structural_reach:
            return (
                StructuralImportanceLevel.LOW
            )

        return (
            StructuralImportanceLevel.MODERATE
        )