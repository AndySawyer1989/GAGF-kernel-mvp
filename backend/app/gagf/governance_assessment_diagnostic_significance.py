from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any

from backend.app.gagf.governance_assessment_evidence_intake import (
    AssessmentEvidenceIntakeResult,
    AssessmentEvidenceRecord,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    AssessmentFrictionSummary,
    ConstraintAggregation,
    ConstraintCategory,
)


ASSESSMENT_DIAGNOSTIC_SIGNIFICANCE_VERSION = "1.0.0"

MIN_RECURRING_EVENT_COUNT = 3
MIN_RECURRING_CONTEXT_SPREAD = 1
MIN_SIGNIFICANT_SUPPORT_AXES = 4
MIN_DOMINANT_SUPPORT_AXES = 5
MIN_HIGH_QUALITY_MEAN = 0.80


class DiagnosticSignificanceError(ValueError):
    """Raised when diagnostic significance cannot be determined."""


class DiagnosticLevel(str, Enum):
    OBSERVED = "observed"
    RECURRING = "recurring"
    SIGNIFICANT = "significant"
    DOMINANT = "dominant"


SUPPORT_AXIS_NAMES = (
    "recurrence",
    "work_item_spread",
    "actor_spread",
    "team_spread",
    "lifecycle_spread",
    "source_diversity",
    "temporal_persistence",
    "evidence_quality",
)


def canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(
    value: str,
) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def round_metric(
    value: float,
) -> float:
    return round(
        value,
        4,
    )


def parse_optional_float(
    value: str | None,
) -> float | None:
    if value is None:
        return None

    normalized = value.strip()

    if not normalized:
        return None

    try:
        parsed = float(
            normalized
        )
    except ValueError:
        return None

    return parsed


@dataclass(
    frozen=True,
    slots=True,
)
class DiagnosticSupportAxes:
    recurrence: bool
    work_item_spread: bool
    actor_spread: bool
    team_spread: bool
    lifecycle_spread: bool
    source_diversity: bool
    temporal_persistence: bool
    evidence_quality: bool

    @property
    def support_count(
        self,
    ) -> int:
        return sum(
            (
                self.recurrence,
                self.work_item_spread,
                self.actor_spread,
                self.team_spread,
                self.lifecycle_spread,
                self.source_diversity,
                self.temporal_persistence,
                self.evidence_quality,
            )
        )

    @property
    def context_spread_count(
        self,
    ) -> int:
        return sum(
            (
                self.work_item_spread,
                self.actor_spread,
                self.team_spread,
                self.lifecycle_spread,
                self.source_diversity,
                self.temporal_persistence,
            )
        )

    def active_axes(
        self,
    ) -> tuple[str, ...]:
        values = {
            "recurrence":
                self.recurrence,
            "work_item_spread":
                self.work_item_spread,
            "actor_spread":
                self.actor_spread,
            "team_spread":
                self.team_spread,
            "lifecycle_spread":
                self.lifecycle_spread,
            "source_diversity":
                self.source_diversity,
            "temporal_persistence":
                self.temporal_persistence,
            "evidence_quality":
                self.evidence_quality,
        }

        return tuple(
            name
            for name
            in SUPPORT_AXIS_NAMES
            if values[name]
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "recurrence":
                self.recurrence,
            "work_item_spread":
                self.work_item_spread,
            "actor_spread":
                self.actor_spread,
            "team_spread":
                self.team_spread,
            "lifecycle_spread":
                self.lifecycle_spread,
            "source_diversity":
                self.source_diversity,
            "temporal_persistence":
                self.temporal_persistence,
            "evidence_quality":
                self.evidence_quality,
            "support_count":
                self.support_count,
            "context_spread_count":
                self.context_spread_count,
            "active_axes":
                list(
                    self.active_axes()
                ),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class DiagnosticCondition:
    category: ConstraintCategory
    level: DiagnosticLevel

    event_count: int
    event_share: float
    friction_score: float
    friction_band: str

    unique_work_item_count: int
    unique_actor_count: int
    unique_team_count: int
    unique_lifecycle_count: int
    unique_source_count: int
    active_day_count: int

    mean_evidence_quality: float | None
    total_duration_minutes: float

    support_axes: DiagnosticSupportAxes

    first_occurred_on: date
    last_occurred_on: date

    is_diagnosed_condition: bool

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "category":
                self.category.value,
            "level":
                self.level.value,
            "event_count":
                self.event_count,
            "event_share":
                self.event_share,
            "friction_score":
                self.friction_score,
            "friction_band":
                self.friction_band,
            "unique_work_item_count":
                self.unique_work_item_count,
            "unique_actor_count":
                self.unique_actor_count,
            "unique_team_count":
                self.unique_team_count,
            "unique_lifecycle_count":
                self.unique_lifecycle_count,
            "unique_source_count":
                self.unique_source_count,
            "active_day_count":
                self.active_day_count,
            "mean_evidence_quality":
                self.mean_evidence_quality,
            "total_duration_minutes":
                self.total_duration_minutes,
            "support_axes":
                self.support_axes.to_dict(),
            "first_occurred_on":
                self.first_occurred_on.isoformat(),
            "last_occurred_on":
                self.last_occurred_on.isoformat(),
            "is_diagnosed_condition":
                self.is_diagnosed_condition,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class AssessmentDiagnosticSignificanceSummary:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    conditions: tuple[
        DiagnosticCondition,
        ...
    ]

    diagnosed_conditions: tuple[
        ConstraintCategory,
        ...
    ]

    dominant_condition: (
        ConstraintCategory
        | None
    )

    summary_hash: str

    schema_version: str = (
        ASSESSMENT_DIAGNOSTIC_SIGNIFICANCE_VERSION
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

    @property
    def observed_count(
        self,
    ) -> int:
        return sum(
            condition.level
            is DiagnosticLevel.OBSERVED
            for condition
            in self.conditions
        )

    @property
    def recurring_count(
        self,
    ) -> int:
        return sum(
            condition.level
            is DiagnosticLevel.RECURRING
            for condition
            in self.conditions
        )

    @property
    def significant_count(
        self,
    ) -> int:
        return sum(
            condition.level
            is DiagnosticLevel.SIGNIFICANT
            for condition
            in self.conditions
        )

    @property
    def dominant_count(
        self,
    ) -> int:
        return sum(
            condition.level
            is DiagnosticLevel.DOMINANT
            for condition
            in self.conditions
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
            "diagnosed_conditions": [
                category.value
                for category
                in self.diagnosed_conditions
            ],
            "dominant_condition": (
                self.dominant_condition.value
                if self.dominant_condition
                is not None
                else None
            ),
            "observed_count":
                self.observed_count,
            "recurring_count":
                self.recurring_count,
            "significant_count":
                self.significant_count,
            "dominant_count":
                self.dominant_count,
            "summary_hash":
                self.summary_hash,
            "schema_version":
                self.schema_version,
        }


class GovernanceAssessmentDiagnosticSignificanceService:
    """
    Convert observed constraint aggregations into
    deterministic diagnostic significance levels.

    This layer deliberately does not use an oracle,
    expected answer, or PRELIVE score.

    Classification is based on independent evidence
    corroboration axes and the pre-existing deterministic
    friction aggregation.
    """

    def classify(
        self,
        *,
        friction_summary:
            AssessmentFrictionSummary,
        intake_results: tuple[
            AssessmentEvidenceIntakeResult,
            ...,
        ],
    ) -> AssessmentDiagnosticSignificanceSummary:
        self._validate_hierarchy(
            friction_summary=(
                friction_summary
            ),
            intake_results=(
                intake_results
            ),
        )

        records = tuple(
            record
            for result
            in intake_results
            for record
            in result.accepted_records
        )

        records_by_category = (
            self._records_by_category(
                records
            )
        )

        conditions = tuple(
            self._classify_aggregation(
                aggregation=aggregation,
                records=records_by_category.get(
                    aggregation.category,
                    (),
                ),
                dominant_constraint=(
                    friction_summary
                    .dominant_constraint
                ),
            )
            for aggregation
            in friction_summary
            .constraint_aggregations
        )

        diagnosed_conditions = tuple(
            condition.category
            for condition
            in conditions
            if condition.is_diagnosed_condition
        )

        dominant_condition = next(
            (
                condition.category
                for condition
                in conditions
                if condition.level
                is DiagnosticLevel.DOMINANT
            ),
            None,
        )

        payload = {
            "hierarchy_key":
                friction_summary
                .hierarchy_key,
            "conditions": [
                condition.to_dict()
                for condition
                in conditions
            ],
            "diagnosed_conditions": [
                category.value
                for category
                in diagnosed_conditions
            ],
            "dominant_condition": (
                dominant_condition.value
                if dominant_condition
                is not None
                else None
            ),
            "schema_version": (
                ASSESSMENT_DIAGNOSTIC_SIGNIFICANCE_VERSION
            ),
        }

        return (
            AssessmentDiagnosticSignificanceSummary(
                tenant_id=(
                    friction_summary
                    .tenant_id
                ),
                client_id=(
                    friction_summary
                    .client_id
                ),
                engagement_id=(
                    friction_summary
                    .engagement_id
                ),
                assessment_id=(
                    friction_summary
                    .assessment_id
                ),
                conditions=conditions,
                diagnosed_conditions=(
                    diagnosed_conditions
                ),
                dominant_condition=(
                    dominant_condition
                ),
                summary_hash=sha256_text(
                    canonical_json(
                        payload
                    )
                ),
            )
        )

    def _validate_hierarchy(
        self,
        *,
        friction_summary:
            AssessmentFrictionSummary,
        intake_results: tuple[
            AssessmentEvidenceIntakeResult,
            ...,
        ],
    ) -> None:
        for result in intake_results:
            if (
                result.hierarchy_key
                != friction_summary
                .hierarchy_key
            ):
                raise (
                    DiagnosticSignificanceError(
                        "evidence hierarchy does not "
                        "match friction summary"
                    )
                )

    def _records_by_category(
        self,
        records: tuple[
            AssessmentEvidenceRecord,
            ...,
        ],
    ) -> dict[
        ConstraintCategory,
        tuple[
            AssessmentEvidenceRecord,
            ...,
        ],
    ]:
        categorized: dict[
            ConstraintCategory,
            list[
                AssessmentEvidenceRecord
            ],
        ] = {}

        for record in records:
            try:
                category = (
                    ConstraintCategory(
                        record.event_type
                    )
                )
            except ValueError:
                continue

            categorized.setdefault(
                category,
                [],
            ).append(
                record
            )

        return {
            category: tuple(
                sorted(
                    category_records,
                    key=lambda record: (
                        record.occurred_at,
                        record.event_id,
                    ),
                )
            )
            for category, category_records
            in categorized.items()
        }

    def _classify_aggregation(
        self,
        *,
        aggregation:
            ConstraintAggregation,
        records: tuple[
            AssessmentEvidenceRecord,
            ...,
        ],
        dominant_constraint:
            ConstraintCategory
            | None,
    ) -> DiagnosticCondition:
        if (
            len(records)
            != aggregation.event_count
        ):
            raise (
                DiagnosticSignificanceError(
                    "constraint aggregation event "
                    "count does not match accepted "
                    "evidence records"
                )
            )

        if not records:
            raise (
                DiagnosticSignificanceError(
                    "constraint aggregation has no "
                    "accepted evidence records"
                )
            )

        work_items = self._attribute_values(
            records,
            "work_item_id",
        )

        actors = self._attribute_values(
            records,
            "actor_id",
        )

        teams = self._attribute_values(
            records,
            "team_id",
        )

        lifecycles = (
            self._attribute_values(
                records,
                "lifecycle_instance_id",
            )
        )

        event_sources = (
            self._attribute_values(
                records,
                "source",
            )
        )

        if not event_sources:
            event_sources = {
                record.source_id
                for record in records
                if record.source_id
            }

        active_days = {
            record.occurred_at.date()
            for record in records
        }

        evidence_quality_values = tuple(
            quality
            for quality
            in (
                parse_optional_float(
                    record.attributes.get(
                        "evidence_quality"
                    )
                )
                for record
                in records
            )
            if quality is not None
        )

        duration_values = tuple(
            duration
            for duration
            in (
                parse_optional_float(
                    record.attributes.get(
                        "duration_minutes"
                    )
                )
                for record
                in records
            )
            if duration is not None
            and duration >= 0.0
        )

        mean_evidence_quality = (
            round_metric(
                sum(
                    evidence_quality_values
                )
                / len(
                    evidence_quality_values
                )
            )
            if evidence_quality_values
            else None
        )

        total_duration_minutes = (
            round_metric(
                sum(
                    duration_values
                )
            )
        )

        support_axes = (
            DiagnosticSupportAxes(
                recurrence=(
                    aggregation.event_count
                    >= MIN_RECURRING_EVENT_COUNT
                ),
                work_item_spread=(
                    len(work_items)
                    >= 2
                ),
                actor_spread=(
                    len(actors)
                    >= 2
                ),
                team_spread=(
                    len(teams)
                    >= 2
                ),
                lifecycle_spread=(
                    len(lifecycles)
                    >= 2
                ),
                source_diversity=(
                    len(event_sources)
                    >= 2
                ),
                temporal_persistence=(
                    len(active_days)
                    >= 2
                ),
                evidence_quality=(
                    mean_evidence_quality
                    is not None
                    and mean_evidence_quality
                    >= MIN_HIGH_QUALITY_MEAN
                ),
            )
        )

        level = self._diagnostic_level(
            category=(
                aggregation.category
            ),
            support_axes=(
                support_axes
            ),
            dominant_constraint=(
                dominant_constraint
            ),
        )

        return DiagnosticCondition(
            category=(
                aggregation.category
            ),
            level=level,
            event_count=(
                aggregation.event_count
            ),
            event_share=(
                aggregation.event_share
            ),
            friction_score=(
                aggregation.friction_score
            ),
            friction_band=(
                aggregation.band.value
            ),
            unique_work_item_count=(
                len(work_items)
            ),
            unique_actor_count=(
                len(actors)
            ),
            unique_team_count=(
                len(teams)
            ),
            unique_lifecycle_count=(
                len(lifecycles)
            ),
            unique_source_count=(
                len(event_sources)
            ),
            active_day_count=(
                len(active_days)
            ),
            mean_evidence_quality=(
                mean_evidence_quality
            ),
            total_duration_minutes=(
                total_duration_minutes
            ),
            support_axes=(
                support_axes
            ),
            first_occurred_on=(
                min(active_days)
            ),
            last_occurred_on=(
                max(active_days)
            ),
            is_diagnosed_condition=(
                level
                in {
                    DiagnosticLevel
                    .SIGNIFICANT,
                    DiagnosticLevel
                    .DOMINANT,
                }
            ),
        )

    def _diagnostic_level(
        self,
        *,
        category:
            ConstraintCategory,
        support_axes:
            DiagnosticSupportAxes,
        dominant_constraint:
            ConstraintCategory
            | None,
    ) -> DiagnosticLevel:
        recurring = (
            support_axes.recurrence
            and (
                support_axes
                .context_spread_count
                >= MIN_RECURRING_CONTEXT_SPREAD
            )
        )

        if not recurring:
            return (
                DiagnosticLevel.OBSERVED
            )

        significant = (
            support_axes.support_count
            >= MIN_SIGNIFICANT_SUPPORT_AXES
        )

        if not significant:
            return (
                DiagnosticLevel.RECURRING
            )

        if (
            category
            == dominant_constraint
            and (
                support_axes
                .support_count
                >= MIN_DOMINANT_SUPPORT_AXES
            )
        ):
            return (
                DiagnosticLevel.DOMINANT
            )

        return (
            DiagnosticLevel.SIGNIFICANT
        )

    def _attribute_values(
        self,
        records: tuple[
            AssessmentEvidenceRecord,
            ...,
        ],
        field_name: str,
    ) -> set[str]:
        return {
            value
            for record
            in records
            for value
            in (
                record.attributes.get(
                    field_name,
                    "",
                ).strip(),
            )
            if value
        }