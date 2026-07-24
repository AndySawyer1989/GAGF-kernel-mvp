from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from backend.app.gagf.governance_assessment_evidence_intake import (
    AssessmentEvidenceIntakeResult,
    AssessmentEvidenceRecord,
)
from backend.app.gagf.governance_assessment_evidence_quality import (
    AssessmentEvidenceQualitySummary,
)


ASSESSMENT_FRICTION_AGGREGATION_VERSION = "1.0.0"


class FrictionAggregationError(ValueError):
    """Raised when assessment friction cannot be aggregated."""


class ConstraintCategory(str, Enum):
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_DELAYED = "APPROVAL_DELAYED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    WORK_BLOCKED = "WORK_BLOCKED"
    DEPENDENCY_WAIT = "DEPENDENCY_WAIT"
    OWNERSHIP_GAP = "OWNERSHIP_GAP"
    SECURITY_REVIEW = "SECURITY_REVIEW"
    ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"
    ESCALATION = "ESCALATION"
    OVERRIDE = "OVERRIDE"


class FrictionBand(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


CONSTRAINT_WEIGHTS: dict[ConstraintCategory, float] = {
    ConstraintCategory.APPROVAL_REQUIRED: 1.0,
    ConstraintCategory.APPROVAL_DELAYED: 2.0,
    ConstraintCategory.APPROVAL_REJECTED: 2.5,
    ConstraintCategory.WORK_BLOCKED: 3.0,
    ConstraintCategory.DEPENDENCY_WAIT: 1.5,
    ConstraintCategory.OWNERSHIP_GAP: 2.5,
    ConstraintCategory.SECURITY_REVIEW: 1.5,
    ConstraintCategory.ENVIRONMENT_FAILURE: 2.5,
    ConstraintCategory.ESCALATION: 2.0,
    ConstraintCategory.OVERRIDE: 2.0,
}


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


def round_score(value: float) -> float:
    return round(value, 4)


def friction_band(score: float) -> FrictionBand:
    if score < 3.0:
        return FrictionBand.LOW

    if score < 8.0:
        return FrictionBand.MODERATE

    if score < 15.0:
        return FrictionBand.HIGH

    return FrictionBand.SEVERE


@dataclass(frozen=True, slots=True)
class ConstraintAggregation:
    category: ConstraintCategory
    event_count: int
    unique_work_item_count: int
    first_occurred_at: datetime
    last_occurred_at: datetime
    weight: float
    friction_score: float
    event_share: float
    band: FrictionBand

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "event_count": self.event_count,
            "unique_work_item_count": (
                self.unique_work_item_count
            ),
            "first_occurred_at": (
                self.first_occurred_at.isoformat()
            ),
            "last_occurred_at": (
                self.last_occurred_at.isoformat()
            ),
            "weight": self.weight,
            "friction_score": self.friction_score,
            "event_share": self.event_share,
            "band": self.band.value,
        }


@dataclass(frozen=True, slots=True)
class AssessmentFrictionSummary:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    constraint_aggregations: tuple[
        ConstraintAggregation, ...
    ]
    total_evidence_events: int
    recognized_constraint_events: int
    unrecognized_event_count: int
    unique_work_item_count: int
    total_friction_score: float
    average_friction_per_event: float
    dominant_constraint: ConstraintCategory | None
    unrecognized_event_types: tuple[str, ...]
    summary_hash: str
    schema_version: str = (
        ASSESSMENT_FRICTION_AGGREGATION_VERSION
    )

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

    @property
    def has_measurable_friction(self) -> bool:
        return self.total_friction_score > 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "constraint_aggregations": [
                aggregation.to_dict()
                for aggregation in self.constraint_aggregations
            ],
            "total_evidence_events": (
                self.total_evidence_events
            ),
            "recognized_constraint_events": (
                self.recognized_constraint_events
            ),
            "unrecognized_event_count": (
                self.unrecognized_event_count
            ),
            "unique_work_item_count": (
                self.unique_work_item_count
            ),
            "total_friction_score": (
                self.total_friction_score
            ),
            "average_friction_per_event": (
                self.average_friction_per_event
            ),
            "dominant_constraint": (
                self.dominant_constraint.value
                if self.dominant_constraint is not None
                else None
            ),
            "unrecognized_event_types": list(
                self.unrecognized_event_types
            ),
            "has_measurable_friction": (
                self.has_measurable_friction
            ),
            "summary_hash": self.summary_hash,
            "schema_version": self.schema_version,
        }


class GovernanceAssessmentFrictionAggregationService:
    def aggregate(
        self,
        *,
        quality_summary: AssessmentEvidenceQualitySummary,
        intake_results: tuple[
            AssessmentEvidenceIntakeResult, ...
        ],
    ) -> AssessmentFrictionSummary:
        if not quality_summary.ready_for_analysis:
            raise FrictionAggregationError(
                "evidence quality is not ready for analysis"
            )

        expected_hierarchy = quality_summary.hierarchy_key

        for result in intake_results:
            if result.hierarchy_key != expected_hierarchy:
                raise FrictionAggregationError(
                    "evidence hierarchy does not match quality summary"
                )

        records = tuple(
            record
            for result in intake_results
            for record in result.accepted_records
        )

        evidence_hashes = [
            record.evidence_hash
            for record in records
        ]

        if len(evidence_hashes) != len(set(evidence_hashes)):
            raise FrictionAggregationError(
                "duplicate evidence records were supplied"
            )

        categorized: dict[
            ConstraintCategory,
            list[AssessmentEvidenceRecord],
        ] = {}
        unrecognized_types: set[str] = set()

        for record in records:
            try:
                category = ConstraintCategory(
                    record.event_type
                )
            except ValueError:
                unrecognized_types.add(record.event_type)
                continue

            categorized.setdefault(category, []).append(
                record
            )

        recognized_count = sum(
            len(category_records)
            for category_records in categorized.values()
        )

        aggregations = tuple(
            self._aggregate_category(
                category=category,
                records=tuple(category_records),
                recognized_count=recognized_count,
            )
            for category, category_records in sorted(
                categorized.items(),
                key=lambda item: item[0].value,
            )
        )

        total_friction_score = round_score(
            sum(
                aggregation.friction_score
                for aggregation in aggregations
            )
        )

        average_friction = (
            total_friction_score / recognized_count
            if recognized_count > 0
            else 0.0
        )

        dominant_constraint = (
            max(
                aggregations,
                key=lambda aggregation: (
                    aggregation.friction_score,
                    aggregation.event_count,
                    aggregation.category.value,
                ),
            ).category
            if aggregations
            else None
        )

        unique_work_items = {
            record.attributes["work_item_id"]
            for record in records
            if record.attributes.get("work_item_id")
        }

        payload = {
            "tenant_id": quality_summary.tenant_id,
            "client_id": quality_summary.client_id,
            "engagement_id": quality_summary.engagement_id,
            "assessment_id": quality_summary.assessment_id,
            "constraint_aggregations": [
                aggregation.to_dict()
                for aggregation in aggregations
            ],
            "total_evidence_events": len(records),
            "recognized_constraint_events": recognized_count,
            "unrecognized_event_count": (
                len(records) - recognized_count
            ),
            "unique_work_item_count": len(unique_work_items),
            "total_friction_score": total_friction_score,
            "average_friction_per_event": round_score(
                average_friction
            ),
            "dominant_constraint": (
                dominant_constraint.value
                if dominant_constraint is not None
                else None
            ),
            "unrecognized_event_types": sorted(
                unrecognized_types
            ),
            "schema_version": (
                ASSESSMENT_FRICTION_AGGREGATION_VERSION
            ),
        }

        return AssessmentFrictionSummary(
            tenant_id=quality_summary.tenant_id,
            client_id=quality_summary.client_id,
            engagement_id=quality_summary.engagement_id,
            assessment_id=quality_summary.assessment_id,
            constraint_aggregations=aggregations,
            total_evidence_events=len(records),
            recognized_constraint_events=recognized_count,
            unrecognized_event_count=(
                len(records) - recognized_count
            ),
            unique_work_item_count=len(unique_work_items),
            total_friction_score=total_friction_score,
            average_friction_per_event=round_score(
                average_friction
            ),
            dominant_constraint=dominant_constraint,
            unrecognized_event_types=tuple(
                sorted(unrecognized_types)
            ),
            summary_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def _aggregate_category(
        self,
        *,
        category: ConstraintCategory,
        records: tuple[AssessmentEvidenceRecord, ...],
        recognized_count: int,
    ) -> ConstraintAggregation:
        event_count = len(records)
        weight = CONSTRAINT_WEIGHTS[category]
        score = round_score(event_count * weight)

        unique_work_items = {
            record.attributes["work_item_id"]
            for record in records
            if record.attributes.get("work_item_id")
        }

        occurred_times = tuple(
            record.occurred_at
            for record in records
        )

        event_share = (
            event_count / recognized_count
            if recognized_count > 0
            else 0.0
        )

        return ConstraintAggregation(
            category=category,
            event_count=event_count,
            unique_work_item_count=len(unique_work_items),
            first_occurred_at=min(occurred_times),
            last_occurred_at=max(occurred_times),
            weight=weight,
            friction_score=score,
            event_share=round_score(event_share),
            band=friction_band(score),
        )
