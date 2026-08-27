from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)
from backend.app.gagf.governance_assessment_structural_importance_classification import (
    AssessmentStructuralImportanceClassificationSummary,
    StructuralImportanceClassification,
    StructuralImportanceLevel,
)


PRIMARY_DIAGNOSIS_EVIDENCE_VERSION = "1.0.0"

PRIMARY_DIAGNOSIS_EVIDENCE_AUTHORITY = (
    "GAGF_FIP_ONLY"
)


class PrimaryDiagnosisEvidenceError(
    RuntimeError
):
    """
    Raised when relative primary-diagnosis evidence
    cannot be derived deterministically.
    """


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
class PrimaryDiagnosisRelativeAxes:
    burden: float
    process_penetration: float
    temporal_position: float
    structural_importance: float

    @property
    def explanatory_score(
        self,
    ) -> float:
        """
        Transparent relative explanatory score.

        This score is observational and comparative.
        It does not establish causation or root cause.
        """

        return round_metric(
            (
                0.25
                * self.burden
            )
            + (
                0.25
                * self.process_penetration
            )
            + (
                0.30
                * self.temporal_position
            )
            + (
                0.20
                * self.structural_importance
            )
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "burden":
                self.burden,
            "process_penetration":
                self.process_penetration,
            "temporal_position":
                self.temporal_position,
            "structural_importance":
                self.structural_importance,
            "explanatory_score":
                self.explanatory_score,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class PrimaryDiagnosisConditionEvidence:
    category: str

    structural_level: (
        StructuralImportanceLevel
    )

    rank: int

    axes: PrimaryDiagnosisRelativeAxes

    relative_to_highest: float

    evidence_quality: float | None

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

    structural_evidence_hash: str
    structural_classification_hash: str

    evidence_hash: str

    @property
    def explanatory_score(
        self,
    ) -> float:
        return (
            self.axes
            .explanatory_score
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "category":
                self.category,

            "structural_level":
                self.structural_level.value,

            "rank":
                self.rank,

            "axes":
                self.axes.to_dict(),

            "relative_to_highest":
                self.relative_to_highest,

            "evidence_quality":
                self.evidence_quality,

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

            "structural_evidence_hash":
                self.structural_evidence_hash,
            "structural_classification_hash":
                self.structural_classification_hash,

            "evidence_hash":
                self.evidence_hash,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class AssessmentPrimaryDiagnosisEvidenceSummary:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    conditions: tuple[
        PrimaryDiagnosisConditionEvidence,
        ...,
    ]

    summary_hash: str

    authority: str = (
        PRIMARY_DIAGNOSIS_EVIDENCE_AUTHORITY
    )

    schema_version: str = (
        PRIMARY_DIAGNOSIS_EVIDENCE_VERSION
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

    @property
    def ranked_conditions(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            condition.category
            for condition
            in self.conditions
        )

    @property
    def highest_ranked_condition(
        self,
    ) -> str | None:
        if not self.conditions:
            return None

        return (
            self.conditions[0]
            .category
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

            "ranked_conditions":
                list(
                    self.ranked_conditions
                ),

            "highest_ranked_condition":
                self.highest_ranked_condition,

            "summary_hash":
                self.summary_hash,

            "authority":
                self.authority,

            "schema_version":
                self.schema_version,
        }


class GovernanceAssessmentPrimaryDiagnosisEvidenceService:
    """
    Derive relative explanatory evidence from the frozen
    structural-importance classification.

    This service performs comparative observational analysis.

    It does not establish:

    - causation;
    - root cause;
    - a final primary diagnosis;
    - intervention authority.

    Ranking is deterministic and relative only to the
    conditions observed inside the same assessment.
    """

    def analyze(
        self,
        *,
        structural_classification_summary: (
            AssessmentStructuralImportanceClassificationSummary
        ),
    ) -> AssessmentPrimaryDiagnosisEvidenceSummary:
        conditions = tuple(
            structural_classification_summary
            .conditions
        )

        if not conditions:
            return (
                self._empty_summary(
                    structural_classification_summary
                )
            )

        maxima = (
            self._build_maxima(
                conditions
            )
        )

        provisional = tuple(
            self._build_provisional(
                condition=condition,
                maxima=maxima,
            )
            for condition
            in conditions
        )

        ordered = tuple(
            sorted(
                provisional,
                key=lambda item: (
                    -item[
                        "axes"
                    ].explanatory_score,
                    item[
                        "category"
                    ],
                ),
            )
        )

        highest_score = (
            ordered[0][
                "axes"
            ].explanatory_score
            if ordered
            else 0.0
        )

        ranked_conditions = tuple(
            self._finalize_condition(
                item=item,
                rank=index,
                highest_score=(
                    highest_score
                ),
            )
            for index, item
            in enumerate(
                ordered,
                start=1,
            )
        )

        summary_payload = {
            "tenant_id":
                structural_classification_summary
                .tenant_id,
            "client_id":
                structural_classification_summary
                .client_id,
            "engagement_id":
                structural_classification_summary
                .engagement_id,
            "assessment_id":
                structural_classification_summary
                .assessment_id,

            "conditions": [
                condition.to_dict()
                for condition
                in ranked_conditions
            ],

            "authority":
                PRIMARY_DIAGNOSIS_EVIDENCE_AUTHORITY,

            "schema_version":
                PRIMARY_DIAGNOSIS_EVIDENCE_VERSION,
        }

        summary_hash = sha256_text(
            canonical_json(
                summary_payload
            )
        )

        return (
            AssessmentPrimaryDiagnosisEvidenceSummary(
                tenant_id=(
                    structural_classification_summary
                    .tenant_id
                ),
                client_id=(
                    structural_classification_summary
                    .client_id
                ),
                engagement_id=(
                    structural_classification_summary
                    .engagement_id
                ),
                assessment_id=(
                    structural_classification_summary
                    .assessment_id
                ),
                conditions=(
                    ranked_conditions
                ),
                summary_hash=(
                    summary_hash
                ),
            )
        )

    def _build_maxima(
        self,
        conditions: tuple[
            StructuralImportanceClassification,
            ...,
        ],
    ) -> dict[str, float]:
        return {
            "friction_score":
                self._max_value(
                    condition.friction_score
                    for condition
                    in conditions
                ),

            "work_items":
                self._max_value(
                    condition.unique_work_item_count
                    for condition
                    in conditions
                ),

            "teams":
                self._max_value(
                    condition.unique_team_count
                    for condition
                    in conditions
                ),

            "lifecycles":
                self._max_value(
                    condition.unique_lifecycle_count
                    for condition
                    in conditions
                ),

            "active_days":
                self._max_value(
                    condition.active_day_count
                    for condition
                    in conditions
                ),

            "downstream_events":
                self._max_value(
                    condition.downstream_event_count
                    for condition
                    in conditions
                ),

            "downstream_constraints":
                self._max_value(
                    condition.downstream_constraint_count
                    for condition
                    in conditions
                ),
        }

    def _build_provisional(
        self,
        *,
        condition: (
            StructuralImportanceClassification
        ),
        maxima: dict[str, float],
    ) -> dict[str, Any]:
        burden = round_metric(
            (
                condition.event_share
                +
                self._normalize(
                    condition.friction_score,
                    maxima[
                        "friction_score"
                    ],
                )
            )
            / 2.0
        )

        process_penetration = (
            round_metric(
                (
                    self._normalize(
                        condition
                        .unique_work_item_count,
                        maxima[
                            "work_items"
                        ],
                    )
                    +
                    self._normalize(
                        condition
                        .unique_team_count,
                        maxima[
                            "teams"
                        ],
                    )
                    +
                    self._normalize(
                        condition
                        .unique_lifecycle_count,
                        maxima[
                            "lifecycles"
                        ],
                    )
                    +
                    self._normalize(
                        condition
                        .active_day_count,
                        maxima[
                            "active_days"
                        ],
                    )
                )
                / 4.0
            )
        )

        temporal_position = (
            round_metric(
                (
                    condition
                    .precedence_rate
                    +
                    self._normalize(
                        condition
                        .downstream_event_count,
                        maxima[
                            "downstream_events"
                        ],
                    )
                    +
                    self._normalize(
                        condition
                        .downstream_constraint_count,
                        maxima[
                            "downstream_constraints"
                        ],
                    )
                )
                / 3.0
            )
        )

        structural_importance = (
            self._structural_level_weight(
                condition.level
            )
        )

        axes = (
            PrimaryDiagnosisRelativeAxes(
                burden=burden,
                process_penetration=(
                    process_penetration
                ),
                temporal_position=(
                    temporal_position
                ),
                structural_importance=(
                    structural_importance
                ),
            )
        )

        return {
            "category":
                condition.category,

            "structural_level":
                condition.level,

            "axes":
                axes,

            "evidence_quality":
                condition
                .mean_evidence_quality,

            "event_count":
                condition.event_count,
            "event_share":
                condition.event_share,
            "friction_score":
                condition.friction_score,

            "unique_work_item_count":
                condition
                .unique_work_item_count,
            "unique_team_count":
                condition
                .unique_team_count,
            "unique_lifecycle_count":
                condition
                .unique_lifecycle_count,
            "active_day_count":
                condition
                .active_day_count,

            "precedence_rate":
                condition.precedence_rate,

            "downstream_event_count":
                condition
                .downstream_event_count,

            "downstream_constraint_count":
                condition
                .downstream_constraint_count,

            "structural_evidence_hash":
                condition.evidence_hash,

            "structural_classification_hash":
                condition
                .classification_hash,
        }

    def _finalize_condition(
        self,
        *,
        item: dict[str, Any],
        rank: int,
        highest_score: float,
    ) -> PrimaryDiagnosisConditionEvidence:
        relative_to_highest = (
            self._normalize(
                item[
                    "axes"
                ].explanatory_score,
                highest_score,
            )
        )

        hash_payload = {
            "category":
                item[
                    "category"
                ],

            "structural_level":
                item[
                    "structural_level"
                ].value,

            "rank":
                rank,

            "axes":
                item[
                    "axes"
                ].to_dict(),

            "relative_to_highest":
                relative_to_highest,

            "evidence_quality":
                item[
                    "evidence_quality"
                ],

            "event_count":
                item[
                    "event_count"
                ],
            "event_share":
                item[
                    "event_share"
                ],
            "friction_score":
                item[
                    "friction_score"
                ],

            "unique_work_item_count":
                item[
                    "unique_work_item_count"
                ],
            "unique_team_count":
                item[
                    "unique_team_count"
                ],
            "unique_lifecycle_count":
                item[
                    "unique_lifecycle_count"
                ],
            "active_day_count":
                item[
                    "active_day_count"
                ],

            "precedence_rate":
                item[
                    "precedence_rate"
                ],

            "downstream_event_count":
                item[
                    "downstream_event_count"
                ],

            "downstream_constraint_count":
                item[
                    "downstream_constraint_count"
                ],

            "structural_evidence_hash":
                item[
                    "structural_evidence_hash"
                ],

            "structural_classification_hash":
                item[
                    "structural_classification_hash"
                ],

            "authority":
                PRIMARY_DIAGNOSIS_EVIDENCE_AUTHORITY,

            "schema_version":
                PRIMARY_DIAGNOSIS_EVIDENCE_VERSION,
        }

        evidence_hash = sha256_text(
            canonical_json(
                hash_payload
            )
        )

        return (
            PrimaryDiagnosisConditionEvidence(
                category=(
                    item[
                        "category"
                    ]
                ),

                structural_level=(
                    item[
                        "structural_level"
                    ]
                ),

                rank=rank,

                axes=(
                    item[
                        "axes"
                    ]
                ),

                relative_to_highest=(
                    relative_to_highest
                ),

                evidence_quality=(
                    item[
                        "evidence_quality"
                    ]
                ),

                event_count=(
                    item[
                        "event_count"
                    ]
                ),

                event_share=(
                    item[
                        "event_share"
                    ]
                ),

                friction_score=(
                    item[
                        "friction_score"
                    ]
                ),

                unique_work_item_count=(
                    item[
                        "unique_work_item_count"
                    ]
                ),

                unique_team_count=(
                    item[
                        "unique_team_count"
                    ]
                ),

                unique_lifecycle_count=(
                    item[
                        "unique_lifecycle_count"
                    ]
                ),

                active_day_count=(
                    item[
                        "active_day_count"
                    ]
                ),

                precedence_rate=(
                    item[
                        "precedence_rate"
                    ]
                ),

                downstream_event_count=(
                    item[
                        "downstream_event_count"
                    ]
                ),

                downstream_constraint_count=(
                    item[
                        "downstream_constraint_count"
                    ]
                ),

                structural_evidence_hash=(
                    item[
                        "structural_evidence_hash"
                    ]
                ),

                structural_classification_hash=(
                    item[
                        "structural_classification_hash"
                    ]
                ),

                evidence_hash=(
                    evidence_hash
                ),
            )
        )

    def _structural_level_weight(
        self,
        level: StructuralImportanceLevel,
    ) -> float:
        weights = {
            StructuralImportanceLevel.HIGH:
                1.0,
            StructuralImportanceLevel.MODERATE:
                0.7,
            StructuralImportanceLevel.LOW:
                0.3,
            StructuralImportanceLevel.LIMITED:
                0.0,
        }

        try:
            return weights[
                level
            ]

        except KeyError as exc:
            raise (
                PrimaryDiagnosisEvidenceError(
                    "Unsupported structural "
                    f"importance level: {level}"
                )
            ) from exc

    def _normalize(
        self,
        value: float | int,
        maximum: float,
    ) -> float:
        if maximum <= 0:
            return 0.0

        return round_metric(
            min(
                max(
                    float(value)
                    / float(maximum),
                    0.0,
                ),
                1.0,
            )
        )

    def _max_value(
        self,
        values,
    ) -> float:
        normalized = [
            float(value)
            for value
            in values
        ]

        if not normalized:
            return 0.0

        return max(
            normalized
        )

    def _empty_summary(
        self,
        source: (
            AssessmentStructuralImportanceClassificationSummary
        ),
    ) -> AssessmentPrimaryDiagnosisEvidenceSummary:
        payload = {
            "tenant_id":
                source.tenant_id,
            "client_id":
                source.client_id,
            "engagement_id":
                source.engagement_id,
            "assessment_id":
                source.assessment_id,
            "conditions": [],
            "authority":
                PRIMARY_DIAGNOSIS_EVIDENCE_AUTHORITY,
            "schema_version":
                PRIMARY_DIAGNOSIS_EVIDENCE_VERSION,
        }

        return (
            AssessmentPrimaryDiagnosisEvidenceSummary(
                tenant_id=(
                    source.tenant_id
                ),
                client_id=(
                    source.client_id
                ),
                engagement_id=(
                    source.engagement_id
                ),
                assessment_id=(
                    source.assessment_id
                ),
                conditions=(),
                summary_hash=(
                    sha256_text(
                        canonical_json(
                            payload
                        )
                    )
                ),
            )
        )