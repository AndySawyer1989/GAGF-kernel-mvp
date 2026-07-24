from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_debt_score import (
    GovernanceDebtBand,
    GovernanceDebtScoreResult,
)
from backend.app.gagf.governance_assessment_evidence_quality import (
    AssessmentEvidenceQualitySummary,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    AssessmentFrictionSummary,
)
from backend.app.gagf.governance_assessment_intervention_plan import (
    RankedInterventionPlan,
)
from backend.app.gagf.governance_assessment_roadmap import (
    AssessmentRoadmap,
    RoadmapHorizon,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    AssessmentScopeConfiguration,
)


EXECUTIVE_ASSESSMENT_PROJECTION_VERSION = "1.0.0"


class ExecutiveAssessmentProjectionError(ValueError):
    """Raised when an executive projection cannot be produced."""


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


@dataclass(frozen=True, slots=True)
class ExecutivePriority:
    rank: int
    intervention_id: str
    title: str
    priority: str
    value_score: float
    owner_role: str | None
    target_horizon: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "intervention_id": self.intervention_id,
            "title": self.title,
            "priority": self.priority,
            "value_score": self.value_score,
            "owner_role": self.owner_role,
            "target_horizon": self.target_horizon,
        }


@dataclass(frozen=True, slots=True)
class ExecutiveAssessmentProjection:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    assessment_name: str
    assessment_period: str
    workflow_count: int
    organizational_unit_count: int
    evidence_quality_score: float
    evidence_quality_grade: str
    evidence_ready_for_analysis: bool
    governance_debt_score: float
    governance_debt_band: str
    management_attention_required: bool
    total_friction_score: float
    affected_work_item_count: int
    dominant_constraint: str | None
    executive_summary: str
    key_findings: tuple[str, ...]
    priorities: tuple[ExecutivePriority, ...]
    roadmap_phase_counts: dict[str, int]
    source_commitments: dict[str, str]
    projection_hash: str
    schema_version: str = (
        EXECUTIVE_ASSESSMENT_PROJECTION_VERSION
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "assessment_name": self.assessment_name,
            "assessment_period": self.assessment_period,
            "workflow_count": self.workflow_count,
            "organizational_unit_count": (
                self.organizational_unit_count
            ),
            "evidence_quality_score": (
                self.evidence_quality_score
            ),
            "evidence_quality_grade": (
                self.evidence_quality_grade
            ),
            "evidence_ready_for_analysis": (
                self.evidence_ready_for_analysis
            ),
            "governance_debt_score": (
                self.governance_debt_score
            ),
            "governance_debt_band": (
                self.governance_debt_band
            ),
            "management_attention_required": (
                self.management_attention_required
            ),
            "total_friction_score": self.total_friction_score,
            "affected_work_item_count": (
                self.affected_work_item_count
            ),
            "dominant_constraint": self.dominant_constraint,
            "executive_summary": self.executive_summary,
            "key_findings": list(self.key_findings),
            "priorities": [
                priority.to_dict()
                for priority in self.priorities
            ],
            "roadmap_phase_counts": dict(
                self.roadmap_phase_counts
            ),
            "source_commitments": dict(
                self.source_commitments
            ),
            "projection_hash": self.projection_hash,
            "schema_version": self.schema_version,
        }


class GovernanceAssessmentExecutiveProjectionService:
    def project(
        self,
        *,
        configuration: AssessmentScopeConfiguration,
        quality_summary: AssessmentEvidenceQualitySummary,
        friction_summary: AssessmentFrictionSummary,
        debt_score: GovernanceDebtScoreResult,
        intervention_plan: RankedInterventionPlan,
        roadmap: AssessmentRoadmap,
        maximum_priorities: int = 3,
    ) -> ExecutiveAssessmentProjection:
        if maximum_priorities < 1:
            raise ExecutiveAssessmentProjectionError(
                "maximum_priorities must be at least 1"
            )

        hierarchy_keys = {
            configuration.hierarchy_key,
            quality_summary.hierarchy_key,
            friction_summary.hierarchy_key,
            debt_score.hierarchy_key,
            intervention_plan.hierarchy_key,
            roadmap.hierarchy_key,
        }

        if len(hierarchy_keys) != 1:
            raise ExecutiveAssessmentProjectionError(
                "assessment component hierarchies do not match"
            )

        if not quality_summary.ready_for_analysis:
            raise ExecutiveAssessmentProjectionError(
                "evidence is not ready for executive projection"
            )

        if intervention_plan.plan_hash != (
            roadmap.intervention_plan_hash
        ):
            raise ExecutiveAssessmentProjectionError(
                "roadmap does not reference the supplied plan"
            )

        roadmap_lookup = {
            item.intervention_id: item
            for phase in roadmap.phases
            for item in phase.items
        }

        priorities = tuple(
            self._priority(
                candidate=candidate,
                roadmap_item=roadmap_lookup.get(
                    candidate.intervention_id
                ),
            )
            for candidate in intervention_plan.interventions[
                :maximum_priorities
            ]
        )

        dominant_constraint = (
            friction_summary.dominant_constraint.value
            if friction_summary.dominant_constraint is not None
            else None
        )

        summary = self._executive_summary(
            debt_score=debt_score,
            friction_summary=friction_summary,
            priority_count=len(priorities),
        )

        key_findings = self._key_findings(
            quality_summary=quality_summary,
            friction_summary=friction_summary,
            debt_score=debt_score,
        )

        phase_counts = {
            phase.horizon.value: phase.item_count
            for phase in roadmap.phases
        }

        source_commitments = {
            "scope_configuration_hash": (
                configuration.configuration_hash
            ),
            "evidence_quality_hash": (
                quality_summary.summary_hash
            ),
            "friction_summary_hash": (
                friction_summary.summary_hash
            ),
            "governance_debt_score_hash": (
                debt_score.score_hash
            ),
            "intervention_plan_hash": (
                intervention_plan.plan_hash
            ),
            "roadmap_hash": roadmap.roadmap_hash,
        }

        assessment_period = (
            f"{configuration.period_start.isoformat()} to "
            f"{configuration.period_end.isoformat()}"
        )

        payload = {
            "tenant_id": configuration.tenant_id,
            "client_id": configuration.client_id,
            "engagement_id": configuration.engagement_id,
            "assessment_id": configuration.assessment_id,
            "assessment_name": configuration.assessment_name,
            "assessment_period": assessment_period,
            "workflow_count": len(
                configuration.workflow_names
            ),
            "organizational_unit_count": len(
                configuration.organizational_units
            ),
            "evidence_quality_score": (
                quality_summary.quality_score
            ),
            "evidence_quality_grade": (
                quality_summary.quality_grade.value
            ),
            "evidence_ready_for_analysis": (
                quality_summary.ready_for_analysis
            ),
            "governance_debt_score": debt_score.score,
            "governance_debt_band": debt_score.band.value,
            "management_attention_required": (
                debt_score.requires_management_attention
            ),
            "total_friction_score": (
                friction_summary.total_friction_score
            ),
            "affected_work_item_count": (
                friction_summary.unique_work_item_count
            ),
            "dominant_constraint": dominant_constraint,
            "executive_summary": summary,
            "key_findings": key_findings,
            "priorities": [
                priority.to_dict()
                for priority in priorities
            ],
            "roadmap_phase_counts": phase_counts,
            "source_commitments": source_commitments,
            "schema_version": (
                EXECUTIVE_ASSESSMENT_PROJECTION_VERSION
            ),
        }

        return ExecutiveAssessmentProjection(
            tenant_id=configuration.tenant_id,
            client_id=configuration.client_id,
            engagement_id=configuration.engagement_id,
            assessment_id=configuration.assessment_id,
            assessment_name=configuration.assessment_name,
            assessment_period=assessment_period,
            workflow_count=len(configuration.workflow_names),
            organizational_unit_count=len(
                configuration.organizational_units
            ),
            evidence_quality_score=(
                quality_summary.quality_score
            ),
            evidence_quality_grade=(
                quality_summary.quality_grade.value
            ),
            evidence_ready_for_analysis=(
                quality_summary.ready_for_analysis
            ),
            governance_debt_score=debt_score.score,
            governance_debt_band=debt_score.band.value,
            management_attention_required=(
                debt_score.requires_management_attention
            ),
            total_friction_score=(
                friction_summary.total_friction_score
            ),
            affected_work_item_count=(
                friction_summary.unique_work_item_count
            ),
            dominant_constraint=dominant_constraint,
            executive_summary=summary,
            key_findings=key_findings,
            priorities=priorities,
            roadmap_phase_counts=phase_counts,
            source_commitments=source_commitments,
            projection_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def _priority(
        self,
        *,
        candidate,
        roadmap_item,
    ) -> ExecutivePriority:
        return ExecutivePriority(
            rank=candidate.rank,
            intervention_id=candidate.intervention_id,
            title=candidate.title,
            priority=candidate.priority.value,
            value_score=candidate.value_score,
            owner_role=(
                roadmap_item.owner_role
                if roadmap_item is not None
                else None
            ),
            target_horizon=(
                roadmap_item.horizon.value
                if roadmap_item is not None
                else None
            ),
        )

    def _executive_summary(
        self,
        *,
        debt_score: GovernanceDebtScoreResult,
        friction_summary: AssessmentFrictionSummary,
        priority_count: int,
    ) -> str:
        attention = (
            "Management attention is required."
            if debt_score.requires_management_attention
            else "Management monitoring is recommended."
        )

        dominant = (
            friction_summary.dominant_constraint.value
            if friction_summary.dominant_constraint is not None
            else "no dominant governed constraint"
        )

        return (
            f"Governance debt is {debt_score.band.value} "
            f"at {debt_score.score:.2f} points. "
            f"The dominant constraint is {dominant}, affecting "
            f"{friction_summary.unique_work_item_count} unique "
            f"work items. {priority_count} priority interventions "
            f"are presented. {attention}"
        )

    def _key_findings(
        self,
        *,
        quality_summary: AssessmentEvidenceQualitySummary,
        friction_summary: AssessmentFrictionSummary,
        debt_score: GovernanceDebtScoreResult,
    ) -> tuple[str, ...]:
        findings = [
            (
                "Evidence quality is "
                f"{quality_summary.quality_grade.value} "
                f"at {quality_summary.quality_score:.2f}."
            ),
            (
                f"{friction_summary.recognized_constraint_events} "
                "governed constraint events were identified."
            ),
            (
                f"Total weighted friction is "
                f"{friction_summary.total_friction_score:.2f}."
            ),
            (
                f"Governance debt is {debt_score.band.value} "
                f"at {debt_score.score:.2f} points."
            ),
        ]

        if friction_summary.unrecognized_event_count > 0:
            findings.append(
                f"{friction_summary.unrecognized_event_count} "
                "accepted events were outside the governed taxonomy."
            )

        return tuple(findings)
