from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_assessment_evidence_quality import (
    AssessmentEvidenceQualitySummary,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    AssessmentFrictionSummary,
    ConstraintCategory,
)


GOVERNANCE_DEBT_SCORE_VERSION = "1.0.0"


class GovernanceDebtScoreError(ValueError):
    """Raised when governance debt cannot be scored."""


class GovernanceDebtBand(str, Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


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


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def round_score(value: float) -> float:
    return round(value, 4)


def debt_band(score: float) -> GovernanceDebtBand:
    if score < 20.0:
        return GovernanceDebtBand.MINIMAL

    if score < 40.0:
        return GovernanceDebtBand.LOW

    if score < 60.0:
        return GovernanceDebtBand.MODERATE

    if score < 80.0:
        return GovernanceDebtBand.HIGH

    return GovernanceDebtBand.CRITICAL


@dataclass(frozen=True, slots=True)
class GovernanceDebtComponent:
    component_id: str
    label: str
    normalized_value: float
    weight: float
    weighted_points: float
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "label": self.label,
            "normalized_value": self.normalized_value,
            "weight": self.weight,
            "weighted_points": self.weighted_points,
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class GovernanceDebtScoreResult:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    score: float
    band: GovernanceDebtBand
    components: tuple[GovernanceDebtComponent, ...]
    dominant_constraint: ConstraintCategory | None
    recognized_constraint_events: int
    unique_work_item_count: int
    evidence_quality_score: float
    findings: tuple[str, ...]
    score_hash: str
    schema_version: str = GOVERNANCE_DEBT_SCORE_VERSION

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
    def requires_management_attention(self) -> bool:
        return self.band in (
            GovernanceDebtBand.HIGH,
            GovernanceDebtBand.CRITICAL,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "score": self.score,
            "band": self.band.value,
            "components": [
                component.to_dict()
                for component in self.components
            ],
            "dominant_constraint": (
                self.dominant_constraint.value
                if self.dominant_constraint is not None
                else None
            ),
            "recognized_constraint_events": (
                self.recognized_constraint_events
            ),
            "unique_work_item_count": (
                self.unique_work_item_count
            ),
            "evidence_quality_score": (
                self.evidence_quality_score
            ),
            "requires_management_attention": (
                self.requires_management_attention
            ),
            "findings": list(self.findings),
            "score_hash": self.score_hash,
            "schema_version": self.schema_version,
        }


class GovernanceAssessmentDebtScoreService:
    def score(
        self,
        *,
        quality_summary: AssessmentEvidenceQualitySummary,
        friction_summary: AssessmentFrictionSummary,
    ) -> GovernanceDebtScoreResult:
        if quality_summary.hierarchy_key != friction_summary.hierarchy_key:
            raise GovernanceDebtScoreError(
                "quality and friction hierarchies do not match"
            )

        if not quality_summary.ready_for_analysis:
            raise GovernanceDebtScoreError(
                "evidence quality is not ready for debt scoring"
            )

        if friction_summary.total_evidence_events != (
            quality_summary.accepted_rows
        ):
            raise GovernanceDebtScoreError(
                "friction evidence count does not match quality summary"
            )

        friction_intensity = clamp(
            friction_summary.average_friction_per_event / 3.0,
            0.0,
            1.0,
        )

        dominant_share = self._dominant_event_share(
            friction_summary
        )

        work_reach = clamp(
            friction_summary.unique_work_item_count / 20.0,
            0.0,
            1.0,
        )

        recognition_rate = (
            friction_summary.recognized_constraint_events
            / friction_summary.total_evidence_events
            if friction_summary.total_evidence_events > 0
            else 0.0
        )
        unrecognized_penalty = 1.0 - recognition_rate

        evidence_confidence = quality_summary.quality_score

        components = (
            self._component(
                component_id="friction-intensity",
                label="Friction intensity",
                normalized_value=friction_intensity,
                weight=0.40,
                explanation=(
                    "Weighted constraint pressure per recognized event."
                ),
            ),
            self._component(
                component_id="constraint-concentration",
                label="Constraint concentration",
                normalized_value=dominant_share,
                weight=0.20,
                explanation=(
                    "Share of recognized events represented by the "
                    "dominant constraint."
                ),
            ),
            self._component(
                component_id="work-reach",
                label="Affected-work reach",
                normalized_value=work_reach,
                weight=0.20,
                explanation=(
                    "Breadth of unique work items affected by friction."
                ),
            ),
            self._component(
                component_id="unrecognized-penalty",
                label="Unrecognized evidence penalty",
                normalized_value=unrecognized_penalty,
                weight=0.10,
                explanation=(
                    "Penalty for accepted events outside the governed "
                    "constraint taxonomy."
                ),
            ),
            self._component(
                component_id="evidence-confidence",
                label="Evidence confidence",
                normalized_value=evidence_confidence,
                weight=0.10,
                explanation=(
                    "Confidence multiplier derived from evidence quality."
                ),
            ),
        )

        raw_score = sum(
            component.weighted_points
            for component in components
        )
        final_score = round_score(
            clamp(raw_score, 0.0, 100.0)
        )
        band = debt_band(final_score)

        findings = self._build_findings(
            score=final_score,
            band=band,
            friction_summary=friction_summary,
            unrecognized_penalty=unrecognized_penalty,
        )

        payload = {
            "tenant_id": quality_summary.tenant_id,
            "client_id": quality_summary.client_id,
            "engagement_id": quality_summary.engagement_id,
            "assessment_id": quality_summary.assessment_id,
            "score": final_score,
            "band": band.value,
            "components": [
                component.to_dict()
                for component in components
            ],
            "dominant_constraint": (
                friction_summary.dominant_constraint.value
                if friction_summary.dominant_constraint is not None
                else None
            ),
            "recognized_constraint_events": (
                friction_summary.recognized_constraint_events
            ),
            "unique_work_item_count": (
                friction_summary.unique_work_item_count
            ),
            "evidence_quality_score": (
                quality_summary.quality_score
            ),
            "findings": findings,
            "schema_version": GOVERNANCE_DEBT_SCORE_VERSION,
        }

        return GovernanceDebtScoreResult(
            tenant_id=quality_summary.tenant_id,
            client_id=quality_summary.client_id,
            engagement_id=quality_summary.engagement_id,
            assessment_id=quality_summary.assessment_id,
            score=final_score,
            band=band,
            components=components,
            dominant_constraint=(
                friction_summary.dominant_constraint
            ),
            recognized_constraint_events=(
                friction_summary.recognized_constraint_events
            ),
            unique_work_item_count=(
                friction_summary.unique_work_item_count
            ),
            evidence_quality_score=(
                quality_summary.quality_score
            ),
            findings=findings,
            score_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def _component(
        self,
        *,
        component_id: str,
        label: str,
        normalized_value: float,
        weight: float,
        explanation: str,
    ) -> GovernanceDebtComponent:
        normalized = round_score(
            clamp(normalized_value, 0.0, 1.0)
        )
        weighted_points = round_score(
            normalized * weight * 100.0
        )

        return GovernanceDebtComponent(
            component_id=component_id,
            label=label,
            normalized_value=normalized,
            weight=weight,
            weighted_points=weighted_points,
            explanation=explanation,
        )

    def _dominant_event_share(
        self,
        friction_summary: AssessmentFrictionSummary,
    ) -> float:
        if not friction_summary.constraint_aggregations:
            return 0.0

        return max(
            aggregation.event_share
            for aggregation in (
                friction_summary.constraint_aggregations
            )
        )

    def _build_findings(
        self,
        *,
        score: float,
        band: GovernanceDebtBand,
        friction_summary: AssessmentFrictionSummary,
        unrecognized_penalty: float,
    ) -> tuple[str, ...]:
        findings = [
            f"Governance debt is {band.value} at {score:.2f} points."
        ]

        if friction_summary.dominant_constraint is not None:
            findings.append(
                "Dominant constraint: "
                + friction_summary.dominant_constraint.value
                + "."
            )

        if friction_summary.unique_work_item_count > 0:
            findings.append(
                f"{friction_summary.unique_work_item_count} unique "
                "work items were affected."
            )

        if unrecognized_penalty > 0.0:
            findings.append(
                "Some accepted evidence was outside the governed "
                "constraint taxonomy."
            )

        if band in (
            GovernanceDebtBand.HIGH,
            GovernanceDebtBand.CRITICAL,
        ):
            findings.append(
                "Management attention is required."
            )

        return tuple(findings)
