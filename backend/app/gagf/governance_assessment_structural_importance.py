from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_diagnostic_scope import (
    AssessmentDiagnosticScopeSummary,
)
from backend.app.gagf.governance_assessment_diagnostic_significance import (
    AssessmentDiagnosticSignificanceSummary,
    DiagnosticCondition,
)
from backend.app.gagf.governance_assessment_evidence_intake import (
    AssessmentEvidenceIntakeResult,
    AssessmentEvidenceRecord,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    AssessmentFrictionSummary,
    ConstraintAggregation,
    ConstraintCategory,
)


ASSESSMENT_STRUCTURAL_IMPORTANCE_VERSION = "1.0.0"

STRUCTURAL_IMPORTANCE_AUTHORITY = "GAGF_FIP_ONLY"


class StructuralImportanceError(ValueError):
    """
    Raised when structural-importance evidence
    cannot be derived safely.
    """


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
        float(value),
        4,
    )


@dataclass(
    frozen=True,
    slots=True,
)
class StructuralTemporalEvidence:
    """
    Observational temporal evidence only.

    A precedence relationship means that one
    observed condition occurred earlier than
    another condition within the same lifecycle.

    It does not establish causation.
    """

    precedence_opportunity_count: int
    precedence_count: int
    precedence_rate: float

    downstream_event_count: int
    downstream_constraint_count: int
    downstream_lifecycle_count: int
    downstream_duration_minutes: float

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "precedence_opportunity_count":
                self.precedence_opportunity_count,
            "precedence_count":
                self.precedence_count,
            "precedence_rate":
                self.precedence_rate,
            "downstream_event_count":
                self.downstream_event_count,
            "downstream_constraint_count":
                self.downstream_constraint_count,
            "downstream_lifecycle_count":
                self.downstream_lifecycle_count,
            "downstream_duration_minutes":
                self.downstream_duration_minutes,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class StructuralBurdenEvidence:
    event_count: int
    event_share: float
    friction_score: float
    friction_band: str
    total_duration_minutes: float

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "event_count":
                self.event_count,
            "event_share":
                self.event_share,
            "friction_score":
                self.friction_score,
            "friction_band":
                self.friction_band,
            "total_duration_minutes":
                self.total_duration_minutes,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class StructuralPenetrationEvidence:
    unique_work_item_count: int
    unique_actor_count: int
    unique_team_count: int
    unique_lifecycle_count: int
    active_day_count: int

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "unique_work_item_count":
                self.unique_work_item_count,
            "unique_actor_count":
                self.unique_actor_count,
            "unique_team_count":
                self.unique_team_count,
            "unique_lifecycle_count":
                self.unique_lifecycle_count,
            "active_day_count":
                self.active_day_count,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class StructuralEvidenceSupport:
    significance_level: str
    scope_level: str
    mean_evidence_quality: float | None
    diagnostic_support_count: int
    scope_breadth_count: int
    is_diagnosed_condition: bool
    is_systemic_condition: bool

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "significance_level":
                self.significance_level,
            "scope_level":
                self.scope_level,
            "mean_evidence_quality":
                self.mean_evidence_quality,
            "diagnostic_support_count":
                self.diagnostic_support_count,
            "scope_breadth_count":
                self.scope_breadth_count,
            "is_diagnosed_condition":
                self.is_diagnosed_condition,
            "is_systemic_condition":
                self.is_systemic_condition,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class StructuralConditionEvidence:
    category: ConstraintCategory

    burden: StructuralBurdenEvidence
    penetration: StructuralPenetrationEvidence
    temporal: StructuralTemporalEvidence
    support: StructuralEvidenceSupport

    evidence_hash: str

    @property
    def category_name(
        self,
    ) -> str:
        return self.category.value

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "category":
                self.category.value,
            "burden":
                self.burden.to_dict(),
            "penetration":
                self.penetration.to_dict(),
            "temporal":
                self.temporal.to_dict(),
            "support":
                self.support.to_dict(),
            "evidence_hash":
                self.evidence_hash,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class AssessmentStructuralImportanceEvidenceSummary:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    conditions: tuple[
        StructuralConditionEvidence,
        ...,
    ]

    summary_hash: str

    authority: str = (
        STRUCTURAL_IMPORTANCE_AUTHORITY
    )

    schema_version: str = (
        ASSESSMENT_STRUCTURAL_IMPORTANCE_VERSION
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
    def condition_count(
        self,
    ) -> int:
        return len(
            self.conditions
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
            "condition_count":
                self.condition_count,
            "summary_hash":
                self.summary_hash,
            "authority":
                self.authority,
            "schema_version":
                self.schema_version,
        }


class GovernanceAssessmentStructuralImportanceService:
    """
    Derive deterministic observational evidence
    relevant to structural importance.

    This service does NOT:

    - identify a root cause;
    - declare a primary diagnosis;
    - use PRELIVE oracle information;
    - tune diagnostic significance;
    - change diagnostic scope;
    - assert causal relationships;
    - authorize interventions.

    It measures burden, penetration, temporal
    precedence, downstream association, and
    evidence support using already-governed
    assessment evidence.
    """

    def analyze(
        self,
        *,
        friction_summary:
            AssessmentFrictionSummary,
        significance_summary:
            AssessmentDiagnosticSignificanceSummary,
        scope_summary:
            AssessmentDiagnosticScopeSummary,
        intake_results: tuple[
            AssessmentEvidenceIntakeResult,
            ...,
        ],
    ) -> AssessmentStructuralImportanceEvidenceSummary:
        self._validate_hierarchy(
            friction_summary=(
                friction_summary
            ),
            significance_summary=(
                significance_summary
            ),
            scope_summary=(
                scope_summary
            ),
            intake_results=(
                intake_results
            ),
        )

        all_records = tuple(
            record
            for result
            in intake_results
            for record
            in result.accepted_records
        )

        aggregations = {
            aggregation.category:
                aggregation
            for aggregation
            in friction_summary
            .constraint_aggregations
        }

        significance_conditions = {
            condition.category:
                condition
            for condition
            in significance_summary.conditions
        }

        scope_conditions = {
            condition.category:
                condition
            for condition
            in scope_summary.conditions
        }

        recognized_categories = tuple(
            sorted(
                aggregations.keys(),
                key=lambda category:
                    category.value,
            )
        )

        records_by_category = (
            self._records_by_category(
                records=all_records,
                categories=(
                    recognized_categories
                ),
            )
        )

        records_by_lifecycle = (
            self._records_by_lifecycle(
                records=all_records,
                categories=(
                    recognized_categories
                ),
            )
        )

        conditions = tuple(
            self._build_condition(
                category=category,
                aggregation=(
                    aggregations[
                        category
                    ]
                ),
                significance=(
                    significance_conditions.get(
                        category
                    )
                ),
                scope=(
                    scope_conditions.get(
                        category.value
                    )
                ),
                category_records=(
                    records_by_category.get(
                        category,
                        (),
                    )
                ),
                records_by_lifecycle=(
                    records_by_lifecycle
                ),
                recognized_categories=(
                    recognized_categories
                ),
            )
            for category
            in recognized_categories
        )

        payload = {
            "hierarchy_key":
                friction_summary.hierarchy_key,
            "conditions": [
                condition.to_dict()
                for condition
                in conditions
            ],
            "authority":
                STRUCTURAL_IMPORTANCE_AUTHORITY,
            "schema_version":
                ASSESSMENT_STRUCTURAL_IMPORTANCE_VERSION,
        }

        summary_hash = sha256_text(
            canonical_json(
                payload
            )
        )

        return (
            AssessmentStructuralImportanceEvidenceSummary(
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
                summary_hash=(
                    summary_hash
                ),
            )
        )

    def _build_condition(
        self,
        *,
        category:
            ConstraintCategory,
        aggregation:
            ConstraintAggregation,
        significance:
            DiagnosticCondition | None,
        scope: Any,
        category_records: tuple[
            AssessmentEvidenceRecord,
            ...,
        ],
        records_by_lifecycle: dict[
            str,
            tuple[
                AssessmentEvidenceRecord,
                ...,
            ],
        ],
        recognized_categories: tuple[
            ConstraintCategory,
            ...,
        ],
    ) -> StructuralConditionEvidence:
        if significance is None:
            raise (
                StructuralImportanceError(
                    "Significance summary "
                    "does not contain "
                    f"{category.value}."
                )
            )

        if scope is None:
            raise (
                StructuralImportanceError(
                    "Scope summary does not "
                    "contain "
                    f"{category.value}."
                )
            )

        burden = (
            StructuralBurdenEvidence(
                event_count=(
                    aggregation.event_count
                ),
                event_share=(
                    round_metric(
                        aggregation.event_share
                    )
                ),
                friction_score=(
                    round_metric(
                        aggregation
                        .friction_score
                    )
                ),
                friction_band=(
                    aggregation.band.value
                ),
                total_duration_minutes=(
                    round_metric(
                        significance
                        .total_duration_minutes
                    )
                ),
            )
        )

        penetration = (
            StructuralPenetrationEvidence(
                unique_work_item_count=(
                    significance
                    .unique_work_item_count
                ),
                unique_actor_count=(
                    significance
                    .unique_actor_count
                ),
                unique_team_count=(
                    significance
                    .unique_team_count
                ),
                unique_lifecycle_count=(
                    significance
                    .unique_lifecycle_count
                ),
                active_day_count=(
                    significance
                    .active_day_count
                ),
            )
        )

        temporal = (
            self._temporal_evidence(
                category=category,
                category_records=(
                    category_records
                ),
                records_by_lifecycle=(
                    records_by_lifecycle
                ),
                recognized_categories=(
                    recognized_categories
                ),
            )
        )

        support = (
            StructuralEvidenceSupport(
                significance_level=(
                    significance
                    .level
                    .value
                ),
                scope_level=(
                    scope
                    .scope_level
                    .value
                ),
                mean_evidence_quality=(
                    significance
                    .mean_evidence_quality
                ),
                diagnostic_support_count=(
                    significance
                    .support_axes
                    .support_count
                ),
                scope_breadth_count=(
                    scope
                    .scope_axes
                    .breadth_count
                ),
                is_diagnosed_condition=(
                    scope
                    .is_diagnosed_condition
                ),
                is_systemic_condition=(
                    scope
                    .is_systemic_condition
                ),
            )
        )

        condition_payload = {
            "category":
                category.value,
            "burden":
                burden.to_dict(),
            "penetration":
                penetration.to_dict(),
            "temporal":
                temporal.to_dict(),
            "support":
                support.to_dict(),
            "schema_version":
                ASSESSMENT_STRUCTURAL_IMPORTANCE_VERSION,
        }

        evidence_hash = sha256_text(
            canonical_json(
                condition_payload
            )
        )

        return (
            StructuralConditionEvidence(
                category=category,
                burden=burden,
                penetration=penetration,
                temporal=temporal,
                support=support,
                evidence_hash=(
                    evidence_hash
                ),
            )
        )

    def _temporal_evidence(
        self,
        *,
        category:
            ConstraintCategory,
        category_records: tuple[
            AssessmentEvidenceRecord,
            ...,
        ],
        records_by_lifecycle: dict[
            str,
            tuple[
                AssessmentEvidenceRecord,
                ...,
            ],
        ],
        recognized_categories: tuple[
            ConstraintCategory,
            ...,
        ],
    ) -> StructuralTemporalEvidence:
        category_value = (
            self._normalized_category(
                category.value
            )
        )

        precedence_opportunity_count = 0
        precedence_count = 0

        downstream_events: dict[
            str,
            AssessmentEvidenceRecord,
        ] = {}

        downstream_categories: set[
            str
        ] = set()

        downstream_lifecycles: set[
            str
        ] = set()

        category_lifecycles = {
            lifecycle_id
            for record
            in category_records
            if (
                lifecycle_id
                := self._lifecycle_id(
                    record
                )
            )
        }

        recognized_values = {
            self._normalized_category(
                value.value
            )
            for value
            in recognized_categories
        }

        for lifecycle_id in sorted(
            category_lifecycles
        ):
            lifecycle_records = (
                records_by_lifecycle.get(
                    lifecycle_id,
                    (),
                )
            )

            subject_records = tuple(
                record
                for record
                in lifecycle_records
                if (
                    self._normalized_category(
                        record.event_type
                    )
                    == category_value
                )
            )

            if not subject_records:
                continue

            subject_first = min(
                record.occurred_at
                for record
                in subject_records
            )

            other_by_category: dict[
                str,
                list[
                    AssessmentEvidenceRecord
                ],
            ] = {}

            for record in lifecycle_records:
                normalized = (
                    self._normalized_category(
                        record.event_type
                    )
                )

                if (
                    normalized
                    == category_value
                ):
                    continue

                if (
                    normalized
                    not in recognized_values
                ):
                    continue

                other_by_category.setdefault(
                    normalized,
                    [],
                ).append(
                    record
                )

            for other_category in sorted(
                other_by_category
            ):
                precedence_opportunity_count += 1

                other_first = min(
                    record.occurred_at
                    for record
                    in other_by_category[
                        other_category
                    ]
                )

                if (
                    subject_first
                    < other_first
                ):
                    precedence_count += 1

            lifecycle_has_downstream = False

            for record in lifecycle_records:
                normalized = (
                    self._normalized_category(
                        record.event_type
                    )
                )

                if (
                    normalized
                    == category_value
                ):
                    continue

                if (
                    normalized
                    not in recognized_values
                ):
                    continue

                if (
                    record.occurred_at
                    <= subject_first
                ):
                    continue

                downstream_events[
                    record.event_id
                ] = record

                downstream_categories.add(
                    normalized
                )

                lifecycle_has_downstream = (
                    True
                )

            if lifecycle_has_downstream:
                downstream_lifecycles.add(
                    lifecycle_id
                )

        precedence_rate = (
            (
                precedence_count
                / precedence_opportunity_count
            )
            if (
                precedence_opportunity_count
                > 0
            )
            else 0.0
        )

        downstream_duration_minutes = (
            round_metric(
                sum(
                    self._safe_nonnegative_float(
                        record.attributes.get(
                            "duration_minutes"
                        )
                    )
                    for record
                    in downstream_events.values()
                )
            )
        )

        return (
            StructuralTemporalEvidence(
                precedence_opportunity_count=(
                    precedence_opportunity_count
                ),
                precedence_count=(
                    precedence_count
                ),
                precedence_rate=(
                    round_metric(
                        precedence_rate
                    )
                ),
                downstream_event_count=(
                    len(
                        downstream_events
                    )
                ),
                downstream_constraint_count=(
                    len(
                        downstream_categories
                    )
                ),
                downstream_lifecycle_count=(
                    len(
                        downstream_lifecycles
                    )
                ),
                downstream_duration_minutes=(
                    downstream_duration_minutes
                ),
            )
        )

    def _records_by_category(
        self,
        *,
        records: tuple[
            AssessmentEvidenceRecord,
            ...,
        ],
        categories: tuple[
            ConstraintCategory,
            ...,
        ],
    ) -> dict[
        ConstraintCategory,
        tuple[
            AssessmentEvidenceRecord,
            ...,
        ],
    ]:
        category_lookup = {
            self._normalized_category(
                category.value
            ):
                category
            for category
            in categories
        }

        grouped: dict[
            ConstraintCategory,
            list[
                AssessmentEvidenceRecord
            ],
        ] = {
            category: []
            for category
            in categories
        }

        for record in records:
            normalized = (
                self._normalized_category(
                    record.event_type
                )
            )

            category = (
                category_lookup.get(
                    normalized
                )
            )

            if category is None:
                continue

            grouped[
                category
            ].append(
                record
            )

        return {
            category: tuple(
                sorted(
                    values,
                    key=lambda record: (
                        record.occurred_at,
                        record.event_id,
                    ),
                )
            )
            for category, values
            in grouped.items()
        }

    def _records_by_lifecycle(
        self,
        *,
        records: tuple[
            AssessmentEvidenceRecord,
            ...,
        ],
        categories: tuple[
            ConstraintCategory,
            ...,
        ],
    ) -> dict[
        str,
        tuple[
            AssessmentEvidenceRecord,
            ...,
        ],
    ]:
        recognized_values = {
            self._normalized_category(
                category.value
            )
            for category
            in categories
        }

        grouped: dict[
            str,
            list[
                AssessmentEvidenceRecord
            ],
        ] = {}

        for record in records:
            normalized = (
                self._normalized_category(
                    record.event_type
                )
            )

            if (
                normalized
                not in recognized_values
            ):
                continue

            lifecycle_id = (
                self._lifecycle_id(
                    record
                )
            )

            if lifecycle_id is None:
                continue

            grouped.setdefault(
                lifecycle_id,
                [],
            ).append(
                record
            )

        return {
            lifecycle_id: tuple(
                sorted(
                    values,
                    key=lambda record: (
                        record.occurred_at,
                        record.event_id,
                    ),
                )
            )
            for lifecycle_id, values
            in grouped.items()
        }

    def _validate_hierarchy(
        self,
        *,
        friction_summary:
            AssessmentFrictionSummary,
        significance_summary:
            AssessmentDiagnosticSignificanceSummary,
        scope_summary:
            AssessmentDiagnosticScopeSummary,
        intake_results: tuple[
            AssessmentEvidenceIntakeResult,
            ...,
        ],
    ) -> None:
        expected = (
            friction_summary
            .hierarchy_key
        )

        if (
            significance_summary
            .hierarchy_key
            != expected
        ):
            raise (
                StructuralImportanceError(
                    "Friction and "
                    "significance hierarchies "
                    "do not match."
                )
            )

        if (
            scope_summary
            .hierarchy_key
            != expected
        ):
            raise (
                StructuralImportanceError(
                    "Friction and scope "
                    "hierarchies do not match."
                )
            )

        for result in intake_results:
            if (
                result.hierarchy_key
                != expected
            ):
                raise (
                    StructuralImportanceError(
                        "Evidence intake "
                        "hierarchy does not "
                        "match diagnostic "
                        "hierarchy."
                    )
                )

    def _lifecycle_id(
        self,
        record:
            AssessmentEvidenceRecord,
    ) -> str | None:
        value = record.attributes.get(
            "lifecycle_instance_id"
        )

        if value is None:
            return None

        normalized = str(
            value
        ).strip()

        return (
            normalized
            if normalized
            else None
        )

    def _normalized_category(
        self,
        value: str,
    ) -> str:
        return (
            str(value)
            .strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

    def _safe_nonnegative_float(
        self,
        value: Any,
    ) -> float:
        if value is None:
            return 0.0

        try:
            result = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

        if result < 0.0:
            return 0.0

        return result