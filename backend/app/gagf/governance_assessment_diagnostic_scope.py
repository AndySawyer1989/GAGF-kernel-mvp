from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_assessment_diagnostic_significance import (
    AssessmentDiagnosticSignificanceSummary,
    DiagnosticCondition,
    DiagnosticLevel,
)


ASSESSMENT_DIAGNOSTIC_SCOPE_VERSION = "1.0.0"

MIN_PROCESS_WORK_ITEMS = 2
MIN_PROCESS_LIFECYCLES = 2

MIN_ORGANIZATIONAL_ACTORS = 2
MIN_ORGANIZATIONAL_TEAMS = 2

MIN_SOURCE_COUNT = 2
MIN_TEMPORAL_ACTIVE_DAYS = 3

MIN_CROSS_CONTEXT_AXES = 2


class DiagnosticScopeError(ValueError):
    """Raised when diagnostic scope cannot be classified."""


class DiagnosticScopeLevel(str, Enum):
    LOCALIZED = "localized"
    CROSS_CONTEXT = "cross_context"
    SYSTEMIC = "systemic"


SCOPE_AXIS_NAMES = (
    "process_breadth",
    "organizational_breadth",
    "source_breadth",
    "temporal_breadth",
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


@dataclass(
    frozen=True,
    slots=True,
)
class DiagnosticScopeAxes:
    process_breadth: bool
    organizational_breadth: bool
    source_breadth: bool
    temporal_breadth: bool

    @property
    def breadth_count(
        self,
    ) -> int:
        return sum(
            (
                self.process_breadth,
                self.organizational_breadth,
                self.source_breadth,
                self.temporal_breadth,
            )
        )

    def active_axes(
        self,
    ) -> tuple[str, ...]:
        values = {
            "process_breadth":
                self.process_breadth,
            "organizational_breadth":
                self.organizational_breadth,
            "source_breadth":
                self.source_breadth,
            "temporal_breadth":
                self.temporal_breadth,
        }

        return tuple(
            name
            for name
            in SCOPE_AXIS_NAMES
            if values[name]
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "process_breadth":
                self.process_breadth,
            "organizational_breadth":
                self.organizational_breadth,
            "source_breadth":
                self.source_breadth,
            "temporal_breadth":
                self.temporal_breadth,
            "breadth_count":
                self.breadth_count,
            "active_axes":
                list(
                    self.active_axes()
                ),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class DiagnosticScopeCondition:
    category: str

    significance_level: DiagnosticLevel
    scope_level: DiagnosticScopeLevel

    unique_work_item_count: int
    unique_actor_count: int
    unique_team_count: int
    unique_lifecycle_count: int
    unique_source_count: int
    active_day_count: int

    scope_axes: DiagnosticScopeAxes

    is_diagnosed_condition: bool
    is_systemic_condition: bool

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "category":
                self.category,
            "significance_level":
                self.significance_level.value,
            "scope_level":
                self.scope_level.value,
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
            "scope_axes":
                self.scope_axes.to_dict(),
            "is_diagnosed_condition":
                self.is_diagnosed_condition,
            "is_systemic_condition":
                self.is_systemic_condition,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class AssessmentDiagnosticScopeSummary:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    conditions: tuple[
        DiagnosticScopeCondition,
        ...,
    ]

    systemic_conditions: tuple[
        str,
        ...,
    ]

    dominant_systemic_condition: (
        str
        | None
    )

    scope_hash: str

    schema_version: str = (
        ASSESSMENT_DIAGNOSTIC_SCOPE_VERSION
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
    def localized_count(
        self,
    ) -> int:
        return sum(
            condition.scope_level
            is DiagnosticScopeLevel.LOCALIZED
            for condition
            in self.conditions
        )

    @property
    def cross_context_count(
        self,
    ) -> int:
        return sum(
            condition.scope_level
            is DiagnosticScopeLevel.CROSS_CONTEXT
            for condition
            in self.conditions
        )

    @property
    def systemic_count(
        self,
    ) -> int:
        return sum(
            condition.scope_level
            is DiagnosticScopeLevel.SYSTEMIC
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
            "systemic_conditions":
                list(
                    self.systemic_conditions
                ),
            "dominant_systemic_condition":
                self.dominant_systemic_condition,
            "localized_count":
                self.localized_count,
            "cross_context_count":
                self.cross_context_count,
            "systemic_count":
                self.systemic_count,
            "scope_hash":
                self.scope_hash,
            "schema_version":
                self.schema_version,
        }


class GovernanceAssessmentDiagnosticScopeService:
    """
    Classify the breadth of each diagnostic pattern independently
    from diagnostic significance.

    Significance answers whether the evidence is strong enough
    to matter.

    Scope answers how broadly that supported pattern propagates
    across process, organizational, evidentiary, and temporal
    contexts.

    This service does not use PRELIVE oracle information.
    """

    def classify(
        self,
        *,
        significance_summary:
            AssessmentDiagnosticSignificanceSummary,
    ) -> AssessmentDiagnosticScopeSummary:
        conditions = tuple(
            self._classify_condition(
                condition
            )
            for condition
            in significance_summary.conditions
        )

        systemic_conditions = tuple(
            condition.category
            for condition
            in conditions
            if (
                condition.is_diagnosed_condition
                and condition.is_systemic_condition
            )
        )

        dominant_category = (
            significance_summary
            .dominant_condition
        )

        dominant_systemic_condition = (
            dominant_category.value
            if (
                dominant_category
                is not None
                and dominant_category.value
                in systemic_conditions
            )
            else None
        )

        payload = {
            "hierarchy_key":
                significance_summary
                .hierarchy_key,
            "conditions": [
                condition.to_dict()
                for condition
                in conditions
            ],
            "systemic_conditions":
                list(
                    systemic_conditions
                ),
            "dominant_systemic_condition":
                dominant_systemic_condition,
            "schema_version":
                ASSESSMENT_DIAGNOSTIC_SCOPE_VERSION,
        }

        return AssessmentDiagnosticScopeSummary(
            tenant_id=(
                significance_summary
                .tenant_id
            ),
            client_id=(
                significance_summary
                .client_id
            ),
            engagement_id=(
                significance_summary
                .engagement_id
            ),
            assessment_id=(
                significance_summary
                .assessment_id
            ),
            conditions=conditions,
            systemic_conditions=(
                systemic_conditions
            ),
            dominant_systemic_condition=(
                dominant_systemic_condition
            ),
            scope_hash=sha256_text(
                canonical_json(
                    payload
                )
            ),
        )

    def _classify_condition(
        self,
        condition: DiagnosticCondition,
    ) -> DiagnosticScopeCondition:
        if (
            condition.unique_work_item_count
            < 0
            or condition.unique_actor_count
            < 0
            or condition.unique_team_count
            < 0
            or condition.unique_lifecycle_count
            < 0
            or condition.unique_source_count
            < 0
            or condition.active_day_count
            < 0
        ):
            raise DiagnosticScopeError(
                "diagnostic scope counts cannot be negative"
            )

        process_breadth = (
            condition.unique_work_item_count
            >= MIN_PROCESS_WORK_ITEMS
            and condition.unique_lifecycle_count
            >= MIN_PROCESS_LIFECYCLES
        )

        organizational_breadth = (
            condition.unique_actor_count
            >= MIN_ORGANIZATIONAL_ACTORS
            and condition.unique_team_count
            >= MIN_ORGANIZATIONAL_TEAMS
        )

        source_breadth = (
            condition.unique_source_count
            >= MIN_SOURCE_COUNT
        )

        temporal_breadth = (
            condition.active_day_count
            >= MIN_TEMPORAL_ACTIVE_DAYS
        )

        axes = DiagnosticScopeAxes(
            process_breadth=(
                process_breadth
            ),
            organizational_breadth=(
                organizational_breadth
            ),
            source_breadth=(
                source_breadth
            ),
            temporal_breadth=(
                temporal_breadth
            ),
        )

        scope_level = self._scope_level(
            axes
        )

        return DiagnosticScopeCondition(
            category=(
                condition.category.value
            ),
            significance_level=(
                condition.level
            ),
            scope_level=(
                scope_level
            ),
            unique_work_item_count=(
                condition
                .unique_work_item_count
            ),
            unique_actor_count=(
                condition
                .unique_actor_count
            ),
            unique_team_count=(
                condition
                .unique_team_count
            ),
            unique_lifecycle_count=(
                condition
                .unique_lifecycle_count
            ),
            unique_source_count=(
                condition
                .unique_source_count
            ),
            active_day_count=(
                condition
                .active_day_count
            ),
            scope_axes=axes,
            is_diagnosed_condition=(
                condition
                .is_diagnosed_condition
            ),
            is_systemic_condition=(
                scope_level
                is DiagnosticScopeLevel.SYSTEMIC
            ),
        )

    def _scope_level(
        self,
        axes: DiagnosticScopeAxes,
    ) -> DiagnosticScopeLevel:
        if (
            axes.process_breadth
            and axes.organizational_breadth
            and axes.temporal_breadth
        ):
            return (
                DiagnosticScopeLevel.SYSTEMIC
            )

        if (
            axes.breadth_count
            >= MIN_CROSS_CONTEXT_AXES
        ):
            return (
                DiagnosticScopeLevel.CROSS_CONTEXT
            )

        return (
            DiagnosticScopeLevel.LOCALIZED
        )