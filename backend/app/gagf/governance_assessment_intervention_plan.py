from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_assessment_debt_score import (
    GovernanceDebtScoreResult,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    AssessmentFrictionSummary,
    ConstraintAggregation,
    ConstraintCategory,
)


INTERVENTION_PLAN_VERSION = "1.0.0"


class InterventionPlanError(ValueError):
    """Raised when an intervention plan cannot be produced."""


class InterventionType(str, Enum):
    STREAMLINE_APPROVAL = "streamline-approval"
    CLARIFY_OWNERSHIP = "clarify-ownership"
    REMOVE_BLOCKER = "remove-blocker"
    REDUCE_DEPENDENCY_WAIT = "reduce-dependency-wait"
    IMPROVE_ENVIRONMENT_RELIABILITY = (
        "improve-environment-reliability"
    )
    REDUCE_ESCALATION = "reduce-escalation"
    GOVERN_OVERRIDE = "govern-override"
    REVIEW_SECURITY_GATE = "review-security-gate"


class InterventionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


INTERVENTION_BY_CONSTRAINT = {
    ConstraintCategory.APPROVAL_REQUIRED: (
        InterventionType.STREAMLINE_APPROVAL
    ),
    ConstraintCategory.APPROVAL_DELAYED: (
        InterventionType.STREAMLINE_APPROVAL
    ),
    ConstraintCategory.APPROVAL_REJECTED: (
        InterventionType.STREAMLINE_APPROVAL
    ),
    ConstraintCategory.WORK_BLOCKED: (
        InterventionType.REMOVE_BLOCKER
    ),
    ConstraintCategory.DEPENDENCY_WAIT: (
        InterventionType.REDUCE_DEPENDENCY_WAIT
    ),
    ConstraintCategory.OWNERSHIP_GAP: (
        InterventionType.CLARIFY_OWNERSHIP
    ),
    ConstraintCategory.SECURITY_REVIEW: (
        InterventionType.REVIEW_SECURITY_GATE
    ),
    ConstraintCategory.ENVIRONMENT_FAILURE: (
        InterventionType.IMPROVE_ENVIRONMENT_RELIABILITY
    ),
    ConstraintCategory.ESCALATION: (
        InterventionType.REDUCE_ESCALATION
    ),
    ConstraintCategory.OVERRIDE: (
        InterventionType.GOVERN_OVERRIDE
    ),
}


INTERVENTION_TITLES = {
    InterventionType.STREAMLINE_APPROVAL: (
        "Streamline the approval path"
    ),
    InterventionType.CLARIFY_OWNERSHIP: (
        "Clarify accountable ownership"
    ),
    InterventionType.REMOVE_BLOCKER: (
        "Remove recurring workflow blockers"
    ),
    InterventionType.REDUCE_DEPENDENCY_WAIT: (
        "Reduce dependency waiting time"
    ),
    InterventionType.IMPROVE_ENVIRONMENT_RELIABILITY: (
        "Improve environment reliability"
    ),
    InterventionType.REDUCE_ESCALATION: (
        "Reduce avoidable escalations"
    ),
    InterventionType.GOVERN_OVERRIDE: (
        "Govern exception and override use"
    ),
    InterventionType.REVIEW_SECURITY_GATE: (
        "Review the security approval gate"
    ),
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


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def round_score(value: float) -> float:
    return round(value, 4)


def priority_for_score(score: float) -> InterventionPriority:
    if score < 30.0:
        return InterventionPriority.LOW

    if score < 55.0:
        return InterventionPriority.MEDIUM

    if score < 75.0:
        return InterventionPriority.HIGH

    return InterventionPriority.URGENT


@dataclass(frozen=True, slots=True)
class InterventionCandidate:
    intervention_id: str
    intervention_type: InterventionType
    title: str
    constraint_category: ConstraintCategory
    priority: InterventionPriority
    rank: int
    value_score: float
    expected_friction_reduction: float
    evidence_confidence: float
    affected_work_reach: float
    implementation_burden: float
    reversibility: float
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type.value,
            "title": self.title,
            "constraint_category": (
                self.constraint_category.value
            ),
            "priority": self.priority.value,
            "rank": self.rank,
            "value_score": self.value_score,
            "expected_friction_reduction": (
                self.expected_friction_reduction
            ),
            "evidence_confidence": self.evidence_confidence,
            "affected_work_reach": self.affected_work_reach,
            "implementation_burden": (
                self.implementation_burden
            ),
            "reversibility": self.reversibility,
            "rationale": list(self.rationale),
        }


@dataclass(frozen=True, slots=True)
class RankedInterventionPlan:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    governance_debt_score: float
    interventions: tuple[InterventionCandidate, ...]
    plan_hash: str
    schema_version: str = INTERVENTION_PLAN_VERSION

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
    def top_intervention(self) -> InterventionCandidate | None:
        return self.interventions[0] if self.interventions else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "governance_debt_score": self.governance_debt_score,
            "interventions": [
                intervention.to_dict()
                for intervention in self.interventions
            ],
            "top_intervention_id": (
                self.top_intervention.intervention_id
                if self.top_intervention is not None
                else None
            ),
            "plan_hash": self.plan_hash,
            "schema_version": self.schema_version,
        }


class GovernanceAssessmentInterventionPlanService:
    def rank(
        self,
        *,
        debt_score: GovernanceDebtScoreResult,
        friction_summary: AssessmentFrictionSummary,
        implementation_burdens: dict[
            ConstraintCategory, float
        ] | None = None,
        reversibility_scores: dict[
            ConstraintCategory, float
        ] | None = None,
    ) -> RankedInterventionPlan:
        if debt_score.hierarchy_key != friction_summary.hierarchy_key:
            raise InterventionPlanError(
                "debt and friction hierarchies do not match"
            )

        burdens = implementation_burdens or {}
        reversibility = reversibility_scores or {}

        candidates = [
            self._build_candidate(
                debt_score=debt_score,
                aggregation=aggregation,
                implementation_burden=burdens.get(
                    aggregation.category,
                    0.5,
                ),
                reversibility=reversibility.get(
                    aggregation.category,
                    0.5,
                ),
            )
            for aggregation in (
                friction_summary.constraint_aggregations
            )
        ]

        ordered = sorted(
            candidates,
            key=lambda candidate: (
                -candidate.value_score,
                candidate.constraint_category.value,
            ),
        )

        ranked = tuple(
            InterventionCandidate(
                intervention_id=candidate.intervention_id,
                intervention_type=candidate.intervention_type,
                title=candidate.title,
                constraint_category=(
                    candidate.constraint_category
                ),
                priority=candidate.priority,
                rank=index,
                value_score=candidate.value_score,
                expected_friction_reduction=(
                    candidate.expected_friction_reduction
                ),
                evidence_confidence=(
                    candidate.evidence_confidence
                ),
                affected_work_reach=(
                    candidate.affected_work_reach
                ),
                implementation_burden=(
                    candidate.implementation_burden
                ),
                reversibility=candidate.reversibility,
                rationale=candidate.rationale,
            )
            for index, candidate in enumerate(ordered, start=1)
        )

        payload = {
            "tenant_id": debt_score.tenant_id,
            "client_id": debt_score.client_id,
            "engagement_id": debt_score.engagement_id,
            "assessment_id": debt_score.assessment_id,
            "governance_debt_score": debt_score.score,
            "interventions": [
                candidate.to_dict()
                for candidate in ranked
            ],
            "schema_version": INTERVENTION_PLAN_VERSION,
        }

        return RankedInterventionPlan(
            tenant_id=debt_score.tenant_id,
            client_id=debt_score.client_id,
            engagement_id=debt_score.engagement_id,
            assessment_id=debt_score.assessment_id,
            governance_debt_score=debt_score.score,
            interventions=ranked,
            plan_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def _build_candidate(
        self,
        *,
        debt_score: GovernanceDebtScoreResult,
        aggregation: ConstraintAggregation,
        implementation_burden: float,
        reversibility: float,
    ) -> InterventionCandidate:
        burden = clamp(implementation_burden, 0.0, 1.0)
        reversible = clamp(reversibility, 0.0, 1.0)

        friction_reduction = clamp(
            aggregation.friction_score / 15.0,
            0.0,
            1.0,
        )
        work_reach = clamp(
            aggregation.unique_work_item_count / 20.0,
            0.0,
            1.0,
        )
        evidence_confidence = clamp(
            debt_score.evidence_quality_score,
            0.0,
            1.0,
        )

        value_score = round_score(
            (friction_reduction * 40.0)
            + (evidence_confidence * 20.0)
            + (work_reach * 15.0)
            + (reversible * 10.0)
            + ((1.0 - burden) * 15.0)
        )

        intervention_type = INTERVENTION_BY_CONSTRAINT[
            aggregation.category
        ]

        intervention_id = sha256_text(
            canonical_json(
                {
                    "tenant_id": debt_score.tenant_id,
                    "client_id": debt_score.client_id,
                    "engagement_id": debt_score.engagement_id,
                    "assessment_id": debt_score.assessment_id,
                    "constraint_category": (
                        aggregation.category.value
                    ),
                    "intervention_type": (
                        intervention_type.value
                    ),
                }
            )
        )[:24]

        rationale = (
            f"{aggregation.event_count} governed events were observed.",
            (
                f"{aggregation.unique_work_item_count} unique work "
                "items were affected."
            ),
            (
                "Evidence confidence is "
                f"{evidence_confidence:.2f}."
            ),
            (
                "Estimated implementation burden is "
                f"{burden:.2f}."
            ),
        )

        return InterventionCandidate(
            intervention_id=intervention_id,
            intervention_type=intervention_type,
            title=INTERVENTION_TITLES[intervention_type],
            constraint_category=aggregation.category,
            priority=priority_for_score(value_score),
            rank=0,
            value_score=value_score,
            expected_friction_reduction=round_score(
                friction_reduction
            ),
            evidence_confidence=round_score(
                evidence_confidence
            ),
            affected_work_reach=round_score(work_reach),
            implementation_burden=round_score(burden),
            reversibility=round_score(reversible),
            rationale=rationale,
        )
