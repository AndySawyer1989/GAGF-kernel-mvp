from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_assessment_intervention_plan import (
    InterventionCandidate,
    InterventionPriority,
    InterventionType,
    RankedInterventionPlan,
)


ASSESSMENT_ROADMAP_VERSION = "1.0.0"


class AssessmentRoadmapError(ValueError):
    """Raised when an assessment roadmap cannot be generated."""


class RoadmapHorizon(str, Enum):
    DAY_30 = "30-day"
    DAY_60 = "60-day"
    DAY_90 = "90-day"


class RoadmapItemStatus(str, Enum):
    PLANNED = "planned"
    APPROVED = "approved"
    IN_PROGRESS = "in-progress"
    COMPLETE = "complete"
    DEFERRED = "deferred"


DEFAULT_OWNER_ROLE_BY_TYPE = {
    InterventionType.STREAMLINE_APPROVAL: (
        "Process Owner"
    ),
    InterventionType.CLARIFY_OWNERSHIP: (
        "Business Unit Leader"
    ),
    InterventionType.REMOVE_BLOCKER: (
        "Operations Lead"
    ),
    InterventionType.REDUCE_DEPENDENCY_WAIT: (
        "Service Delivery Lead"
    ),
    InterventionType.IMPROVE_ENVIRONMENT_RELIABILITY: (
        "Platform Engineering Lead"
    ),
    InterventionType.REDUCE_ESCALATION: (
        "Operations Manager"
    ),
    InterventionType.GOVERN_OVERRIDE: (
        "Governance Owner"
    ),
    InterventionType.REVIEW_SECURITY_GATE: (
        "Security Governance Lead"
    ),
}


OUTCOME_BY_TYPE = {
    InterventionType.STREAMLINE_APPROVAL: (
        "Reduce approval delay and unnecessary human touches."
    ),
    InterventionType.CLARIFY_OWNERSHIP: (
        "Reduce unresolved ownership gaps and routing ambiguity."
    ),
    InterventionType.REMOVE_BLOCKER: (
        "Reduce recurring blocked-work events."
    ),
    InterventionType.REDUCE_DEPENDENCY_WAIT: (
        "Reduce average dependency waiting time."
    ),
    InterventionType.IMPROVE_ENVIRONMENT_RELIABILITY: (
        "Reduce environment-failure events and recovery time."
    ),
    InterventionType.REDUCE_ESCALATION: (
        "Reduce avoidable escalation frequency."
    ),
    InterventionType.GOVERN_OVERRIDE: (
        "Reduce ungoverned exception and override use."
    ),
    InterventionType.REVIEW_SECURITY_GATE: (
        "Reduce security-review delay without weakening controls."
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


def horizon_for_candidate(
    candidate: InterventionCandidate,
) -> RoadmapHorizon:
    if candidate.priority is InterventionPriority.URGENT:
        return RoadmapHorizon.DAY_30

    if candidate.priority is InterventionPriority.HIGH:
        return (
            RoadmapHorizon.DAY_30
            if candidate.implementation_burden <= 0.5
            else RoadmapHorizon.DAY_60
        )

    if candidate.priority is InterventionPriority.MEDIUM:
        return RoadmapHorizon.DAY_60

    return RoadmapHorizon.DAY_90


@dataclass(frozen=True, slots=True)
class RoadmapItem:
    roadmap_item_id: str
    intervention_id: str
    intervention_type: InterventionType
    title: str
    horizon: RoadmapHorizon
    sequence: int
    owner_role: str
    measurable_outcome: str
    value_score: float
    implementation_burden: float
    dependency_ids: tuple[str, ...]
    status: RoadmapItemStatus = RoadmapItemStatus.PLANNED

    def to_dict(self) -> dict[str, Any]:
        return {
            "roadmap_item_id": self.roadmap_item_id,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type.value,
            "title": self.title,
            "horizon": self.horizon.value,
            "sequence": self.sequence,
            "owner_role": self.owner_role,
            "measurable_outcome": self.measurable_outcome,
            "value_score": self.value_score,
            "implementation_burden": (
                self.implementation_burden
            ),
            "dependency_ids": list(self.dependency_ids),
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class RoadmapPhase:
    horizon: RoadmapHorizon
    objective: str
    items: tuple[RoadmapItem, ...]

    @property
    def item_count(self) -> int:
        return len(self.items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "horizon": self.horizon.value,
            "objective": self.objective,
            "item_count": self.item_count,
            "items": [
                item.to_dict()
                for item in self.items
            ],
        }


@dataclass(frozen=True, slots=True)
class AssessmentRoadmap:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    intervention_plan_hash: str
    phases: tuple[RoadmapPhase, ...]
    total_items: int
    roadmap_hash: str
    schema_version: str = ASSESSMENT_ROADMAP_VERSION

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

    def items_for_horizon(
        self,
        horizon: RoadmapHorizon,
    ) -> tuple[RoadmapItem, ...]:
        for phase in self.phases:
            if phase.horizon is horizon:
                return phase.items

        return ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "intervention_plan_hash": (
                self.intervention_plan_hash
            ),
            "phases": [
                phase.to_dict()
                for phase in self.phases
            ],
            "total_items": self.total_items,
            "roadmap_hash": self.roadmap_hash,
            "schema_version": self.schema_version,
        }


class GovernanceAssessmentRoadmapService:
    def generate(
        self,
        *,
        plan: RankedInterventionPlan,
        owner_roles: dict[
            InterventionType, str
        ] | None = None,
    ) -> AssessmentRoadmap:
        owners = owner_roles or {}

        seen_intervention_ids: set[str] = set()

        for candidate in plan.interventions:
            if candidate.intervention_id in seen_intervention_ids:
                raise AssessmentRoadmapError(
                    "intervention plan contains duplicate identifiers"
                )

            seen_intervention_ids.add(
                candidate.intervention_id
            )

        items = tuple(
            self._build_item(
                plan=plan,
                candidate=candidate,
                owner_role=owners.get(
                    candidate.intervention_type,
                    DEFAULT_OWNER_ROLE_BY_TYPE[
                        candidate.intervention_type
                    ],
                ),
                preceding_item=(
                    plan.interventions[index - 1]
                    if index > 0
                    else None
                ),
            )
            for index, candidate in enumerate(
                plan.interventions
            )
        )

        phases = tuple(
            RoadmapPhase(
                horizon=horizon,
                objective=self._phase_objective(horizon),
                items=tuple(
                    item
                    for item in items
                    if item.horizon is horizon
                ),
            )
            for horizon in (
                RoadmapHorizon.DAY_30,
                RoadmapHorizon.DAY_60,
                RoadmapHorizon.DAY_90,
            )
        )

        payload = {
            "tenant_id": plan.tenant_id,
            "client_id": plan.client_id,
            "engagement_id": plan.engagement_id,
            "assessment_id": plan.assessment_id,
            "intervention_plan_hash": plan.plan_hash,
            "phases": [
                phase.to_dict()
                for phase in phases
            ],
            "total_items": len(items),
            "schema_version": ASSESSMENT_ROADMAP_VERSION,
        }

        return AssessmentRoadmap(
            tenant_id=plan.tenant_id,
            client_id=plan.client_id,
            engagement_id=plan.engagement_id,
            assessment_id=plan.assessment_id,
            intervention_plan_hash=plan.plan_hash,
            phases=phases,
            total_items=len(items),
            roadmap_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def _build_item(
        self,
        *,
        plan: RankedInterventionPlan,
        candidate: InterventionCandidate,
        owner_role: str,
        preceding_item: InterventionCandidate | None,
    ) -> RoadmapItem:
        normalized_owner = owner_role.strip()

        if not normalized_owner:
            raise AssessmentRoadmapError(
                "owner role must not be empty"
            )

        horizon = horizon_for_candidate(candidate)

        dependency_ids: tuple[str, ...] = ()

        if (
            preceding_item is not None
            and candidate.rank > 1
            and horizon is not RoadmapHorizon.DAY_30
        ):
            dependency_ids = (
                preceding_item.intervention_id,
            )

        roadmap_item_id = sha256_text(
            canonical_json(
                {
                    "tenant_id": plan.tenant_id,
                    "client_id": plan.client_id,
                    "engagement_id": plan.engagement_id,
                    "assessment_id": plan.assessment_id,
                    "intervention_id": candidate.intervention_id,
                    "horizon": horizon.value,
                    "sequence": candidate.rank,
                }
            )
        )[:24]

        return RoadmapItem(
            roadmap_item_id=roadmap_item_id,
            intervention_id=candidate.intervention_id,
            intervention_type=candidate.intervention_type,
            title=candidate.title,
            horizon=horizon,
            sequence=candidate.rank,
            owner_role=normalized_owner,
            measurable_outcome=OUTCOME_BY_TYPE[
                candidate.intervention_type
            ],
            value_score=candidate.value_score,
            implementation_burden=(
                candidate.implementation_burden
            ),
            dependency_ids=dependency_ids,
        )

    def _phase_objective(
        self,
        horizon: RoadmapHorizon,
    ) -> str:
        objectives = {
            RoadmapHorizon.DAY_30: (
                "Stabilize high-value constraints and establish owners."
            ),
            RoadmapHorizon.DAY_60: (
                "Implement structural workflow improvements."
            ),
            RoadmapHorizon.DAY_90: (
                "Consolidate gains and measure sustained outcomes."
            ),
        }

        return objectives[horizon]
