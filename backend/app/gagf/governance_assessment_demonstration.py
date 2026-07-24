from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from backend.app.gagf.governance_assessment_debt_score import (
    GovernanceAssessmentDebtScoreService,
    GovernanceDebtScoreResult,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_evidence_intake import (
    AssessmentEvidenceIntakeResult,
    GovernanceAssessmentEvidenceIntakeService,
)
from backend.app.gagf.governance_assessment_evidence_quality import (
    AssessmentEvidenceQualitySummary,
    GovernanceAssessmentEvidenceQualityService,
)
from backend.app.gagf.governance_assessment_executive_projection import (
    ExecutiveAssessmentProjection,
    GovernanceAssessmentExecutiveProjectionService,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    AssessmentFrictionSummary,
    ConstraintCategory,
    GovernanceAssessmentFrictionAggregationService,
)
from backend.app.gagf.governance_assessment_intervention_plan import (
    GovernanceAssessmentInterventionPlanService,
    InterventionType,
    RankedInterventionPlan,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_report_package import (
    ClientReadyReportPackage,
    GovernanceAssessmentReportPackageService,
)
from backend.app.gagf.governance_assessment_roadmap import (
    AssessmentRoadmap,
    GovernanceAssessmentRoadmapService,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    AssessmentScopeConfiguration,
    EvidenceRequirement,
    GovernanceAssessmentScopeConfigurationService,
    ScopeConfigurationStatus,
)


GOVERNANCE_ASSESSMENT_DEMONSTRATION_VERSION = "1.0.0"


class GovernanceAssessmentDemonstrationError(ValueError):
    """Raised when the end-to-end demonstration cannot complete."""


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
class DemonstrationEvidenceInput:
    source: EvidenceSourceReference
    csv_text: str


@dataclass(frozen=True, slots=True)
class GovernanceAssessmentDemonstrationResult:
    configuration: AssessmentScopeConfiguration
    intake_results: tuple[AssessmentEvidenceIntakeResult, ...]
    quality_summary: AssessmentEvidenceQualitySummary
    friction_summary: AssessmentFrictionSummary
    debt_score: GovernanceDebtScoreResult
    intervention_plan: RankedInterventionPlan
    roadmap: AssessmentRoadmap
    executive_projection: ExecutiveAssessmentProjection
    report_package: ClientReadyReportPackage
    artifact_commitments: dict[str, str]
    demonstration_hash: str
    schema_version: str = (
        GOVERNANCE_ASSESSMENT_DEMONSTRATION_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return self.configuration.hierarchy_key

    @property
    def completed(self) -> bool:
        return (
            self.quality_summary.ready_for_analysis
            and bool(self.report_package.markdown)
            and self.report_package.manifest.package_hash
            == self.artifact_commitments["report_package_hash"]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hierarchy_key": self.hierarchy_key,
            "completed": self.completed,
            "configuration": self.configuration.to_dict(),
            "intake_results": [
                result.to_dict()
                for result in self.intake_results
            ],
            "quality_summary": self.quality_summary.to_dict(),
            "friction_summary": self.friction_summary.to_dict(),
            "debt_score": self.debt_score.to_dict(),
            "intervention_plan": self.intervention_plan.to_dict(),
            "roadmap": self.roadmap.to_dict(),
            "executive_projection": (
                self.executive_projection.to_dict()
            ),
            "report_package": self.report_package.to_dict(),
            "artifact_commitments": dict(
                self.artifact_commitments
            ),
            "demonstration_hash": self.demonstration_hash,
            "schema_version": self.schema_version,
        }


class GovernanceAssessmentDemonstrationService:
    def __init__(self) -> None:
        self._scope_service = (
            GovernanceAssessmentScopeConfigurationService()
        )
        self._intake_service = (
            GovernanceAssessmentEvidenceIntakeService()
        )
        self._quality_service = (
            GovernanceAssessmentEvidenceQualityService()
        )
        self._friction_service = (
            GovernanceAssessmentFrictionAggregationService()
        )
        self._debt_service = (
            GovernanceAssessmentDebtScoreService()
        )
        self._plan_service = (
            GovernanceAssessmentInterventionPlanService()
        )
        self._roadmap_service = (
            GovernanceAssessmentRoadmapService()
        )
        self._projection_service = (
            GovernanceAssessmentExecutiveProjectionService()
        )
        self._report_service = (
            GovernanceAssessmentReportPackageService()
        )

    def run(
        self,
        *,
        context: CommercialHierarchyContext,
        assessment_name: str,
        workflow_names: tuple[str, ...],
        organizational_units: tuple[str, ...],
        period_start: date,
        period_end: date,
        objectives: tuple[str, ...],
        expected_outcomes: tuple[str, ...],
        evidence_requirements: tuple[
            EvidenceRequirement, ...
        ],
        evidence_inputs: tuple[
            DemonstrationEvidenceInput, ...
        ],
        client_display_name: str,
        prepared_by: str,
        exclusions: tuple[str, ...] = (),
        implementation_burdens: dict[
            ConstraintCategory, float
        ] | None = None,
        reversibility_scores: dict[
            ConstraintCategory, float
        ] | None = None,
        owner_roles: dict[
            InterventionType, str
        ] | None = None,
        maximum_priorities: int = 3,
    ) -> GovernanceAssessmentDemonstrationResult:
        if not evidence_inputs:
            raise GovernanceAssessmentDemonstrationError(
                "at least one evidence input is required"
            )

        source_ids = [
            evidence_input.source.source_id
            for evidence_input in evidence_inputs
        ]

        if len(source_ids) != len(set(source_ids)):
            raise GovernanceAssessmentDemonstrationError(
                "evidence inputs contain duplicate source identifiers"
            )

        configuration = self._scope_service.configure(
            context=context,
            assessment_name=assessment_name,
            workflow_names=workflow_names,
            organizational_units=organizational_units,
            period_start=period_start,
            period_end=period_end,
            objectives=objectives,
            expected_outcomes=expected_outcomes,
            exclusions=exclusions,
            evidence_requirements=evidence_requirements,
            status=ScopeConfigurationStatus.LOCKED,
        )

        self._scope_service.validate_ready_for_evidence(
            configuration
        )

        intake_results = tuple(
            self._intake_service.ingest_csv(
                context=context,
                source=evidence_input.source,
                csv_text=evidence_input.csv_text,
            )
            for evidence_input in evidence_inputs
        )

        quality_summary = self._quality_service.summarize(
            configuration=configuration,
            intake_results=intake_results,
        )

        if not quality_summary.ready_for_analysis:
            raise GovernanceAssessmentDemonstrationError(
                "evidence quality did not pass the analysis gate"
            )

        friction_summary = self._friction_service.aggregate(
            quality_summary=quality_summary,
            intake_results=intake_results,
        )

        debt_score = self._debt_service.score(
            quality_summary=quality_summary,
            friction_summary=friction_summary,
        )

        intervention_plan = self._plan_service.rank(
            debt_score=debt_score,
            friction_summary=friction_summary,
            implementation_burdens=implementation_burdens,
            reversibility_scores=reversibility_scores,
        )

        roadmap = self._roadmap_service.generate(
            plan=intervention_plan,
            owner_roles=owner_roles,
        )

        executive_projection = self._projection_service.project(
            configuration=configuration,
            quality_summary=quality_summary,
            friction_summary=friction_summary,
            debt_score=debt_score,
            intervention_plan=intervention_plan,
            roadmap=roadmap,
            maximum_priorities=maximum_priorities,
        )

        report_package = self._report_service.build(
            projection=executive_projection,
            client_display_name=client_display_name,
            prepared_by=prepared_by,
        )

        artifact_commitments = {
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
            "executive_projection_hash": (
                executive_projection.projection_hash
            ),
            "report_markdown_hash": (
                report_package.manifest.markdown_hash
            ),
            "report_package_hash": (
                report_package.manifest.package_hash
            ),
        }

        self._validate_commitment_chain(
            executive_projection=executive_projection,
            report_package=report_package,
            artifact_commitments=artifact_commitments,
        )

        demonstration_payload = {
            "hierarchy_key": configuration.hierarchy_key,
            "artifact_commitments": artifact_commitments,
            "intake_hashes": [
                result.intake_hash
                for result in intake_results
            ],
            "schema_version": (
                GOVERNANCE_ASSESSMENT_DEMONSTRATION_VERSION
            ),
        }

        return GovernanceAssessmentDemonstrationResult(
            configuration=configuration,
            intake_results=intake_results,
            quality_summary=quality_summary,
            friction_summary=friction_summary,
            debt_score=debt_score,
            intervention_plan=intervention_plan,
            roadmap=roadmap,
            executive_projection=executive_projection,
            report_package=report_package,
            artifact_commitments=artifact_commitments,
            demonstration_hash=sha256_text(
                canonical_json(demonstration_payload)
            ),
        )

    def _validate_commitment_chain(
        self,
        *,
        executive_projection: ExecutiveAssessmentProjection,
        report_package: ClientReadyReportPackage,
        artifact_commitments: dict[str, str],
    ) -> None:
        projection_commitments = (
            executive_projection.source_commitments
        )

        expected_projection_commitments = {
            "scope_configuration_hash": (
                artifact_commitments["scope_configuration_hash"]
            ),
            "evidence_quality_hash": (
                artifact_commitments["evidence_quality_hash"]
            ),
            "friction_summary_hash": (
                artifact_commitments["friction_summary_hash"]
            ),
            "governance_debt_score_hash": (
                artifact_commitments[
                    "governance_debt_score_hash"
                ]
            ),
            "intervention_plan_hash": (
                artifact_commitments["intervention_plan_hash"]
            ),
            "roadmap_hash": artifact_commitments["roadmap_hash"],
        }

        if projection_commitments != (
            expected_projection_commitments
        ):
            raise GovernanceAssessmentDemonstrationError(
                "executive projection commitment chain is invalid"
            )

        manifest_commitments = (
            report_package.manifest.source_commitments
        )

        if manifest_commitments.get(
            "executive_projection_hash"
        ) != artifact_commitments["executive_projection_hash"]:
            raise GovernanceAssessmentDemonstrationError(
                "report package projection commitment is invalid"
            )

        if report_package.manifest.package_hash != (
            artifact_commitments["report_package_hash"]
        ):
            raise GovernanceAssessmentDemonstrationError(
                "report package commitment is invalid"
            )
