from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.app.gagf.governance_assessment_evidence_intake import (
    AssessmentEvidenceIntakeResult,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    AssessmentScopeConfiguration,
    EvidenceRequirement,
)


ASSESSMENT_EVIDENCE_QUALITY_VERSION = "1.0.0"


class EvidenceQualityError(ValueError):
    """Raised when evidence quality cannot be evaluated."""


class EvidenceQualityGrade(str, Enum):
    INSUFFICIENT = "insufficient"
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    STRONG = "strong"


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


def grade_for_score(
    *,
    score: float,
    required_requirements_met: bool,
) -> EvidenceQualityGrade:
    if not required_requirements_met:
        return EvidenceQualityGrade.INSUFFICIENT

    if score < 0.50:
        return EvidenceQualityGrade.POOR

    if score < 0.70:
        return EvidenceQualityGrade.FAIR

    if score < 0.85:
        return EvidenceQualityGrade.GOOD

    return EvidenceQualityGrade.STRONG


@dataclass(frozen=True, slots=True)
class EvidenceRequirementEvaluation:
    requirement_id: str
    source_kind: str
    required: bool
    minimum_record_count: int
    observed_record_count: int
    satisfied: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "source_kind": self.source_kind,
            "required": self.required,
            "minimum_record_count": self.minimum_record_count,
            "observed_record_count": self.observed_record_count,
            "satisfied": self.satisfied,
        }


@dataclass(frozen=True, slots=True)
class EvidenceSourceQualitySummary:
    source_id: str
    source_kind: str
    display_name: str
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    acceptance_rate: float
    valid: bool
    intake_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "display_name": self.display_name,
            "total_rows": self.total_rows,
            "accepted_rows": self.accepted_rows,
            "rejected_rows": self.rejected_rows,
            "acceptance_rate": self.acceptance_rate,
            "valid": self.valid,
            "intake_hash": self.intake_hash,
        }


@dataclass(frozen=True, slots=True)
class AssessmentEvidenceQualitySummary:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    source_summaries: tuple[
        EvidenceSourceQualitySummary, ...
    ]
    requirement_evaluations: tuple[
        EvidenceRequirementEvaluation, ...
    ]
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    acceptance_rate: float
    requirement_coverage_rate: float
    required_requirements_met: bool
    quality_score: float
    quality_grade: EvidenceQualityGrade
    findings: tuple[str, ...]
    summary_hash: str
    schema_version: str = ASSESSMENT_EVIDENCE_QUALITY_VERSION

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
    def ready_for_analysis(self) -> bool:
        return (
            self.required_requirements_met
            and self.accepted_rows > 0
            and self.quality_grade in (
                EvidenceQualityGrade.GOOD,
                EvidenceQualityGrade.STRONG,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "source_summaries": [
                summary.to_dict()
                for summary in self.source_summaries
            ],
            "requirement_evaluations": [
                evaluation.to_dict()
                for evaluation in self.requirement_evaluations
            ],
            "total_rows": self.total_rows,
            "accepted_rows": self.accepted_rows,
            "rejected_rows": self.rejected_rows,
            "acceptance_rate": self.acceptance_rate,
            "requirement_coverage_rate": (
                self.requirement_coverage_rate
            ),
            "required_requirements_met": (
                self.required_requirements_met
            ),
            "quality_score": self.quality_score,
            "quality_grade": self.quality_grade.value,
            "ready_for_analysis": self.ready_for_analysis,
            "findings": list(self.findings),
            "summary_hash": self.summary_hash,
            "schema_version": self.schema_version,
        }


class GovernanceAssessmentEvidenceQualityService:
    def summarize(
        self,
        *,
        configuration: AssessmentScopeConfiguration,
        intake_results: tuple[
            AssessmentEvidenceIntakeResult, ...
        ],
    ) -> AssessmentEvidenceQualitySummary:
        expected_hierarchy = configuration.hierarchy_key

        source_ids = [
            result.source.source_id
            for result in intake_results
        ]

        if len(source_ids) != len(set(source_ids)):
            raise EvidenceQualityError(
                "intake_results contains duplicate source identifiers"
            )

        for result in intake_results:
            if result.hierarchy_key != expected_hierarchy:
                raise EvidenceQualityError(
                    "evidence intake hierarchy does not match scope"
                )

        source_summaries = tuple(
            self._summarize_source(result)
            for result in intake_results
        )

        total_rows = sum(
            result.total_rows
            for result in intake_results
        )
        accepted_rows = sum(
            result.accepted_count
            for result in intake_results
        )
        rejected_rows = sum(
            result.rejected_count
            for result in intake_results
        )

        acceptance_rate = (
            accepted_rows / total_rows
            if total_rows > 0
            else 0.0
        )

        evaluations = tuple(
            self._evaluate_requirement(
                requirement=requirement,
                intake_results=intake_results,
            )
            for requirement in configuration.evidence_requirements
        )

        satisfied_count = sum(
            1
            for evaluation in evaluations
            if evaluation.satisfied
        )
        requirement_coverage_rate = (
            satisfied_count / len(evaluations)
            if evaluations
            else 0.0
        )

        required_requirements_met = all(
            evaluation.satisfied
            for evaluation in evaluations
            if evaluation.required
        )

        if not evaluations:
            required_requirements_met = False

        quality_score = round_score(
            (0.60 * acceptance_rate)
            + (0.40 * requirement_coverage_rate)
        )

        quality_grade = grade_for_score(
            score=quality_score,
            required_requirements_met=(
                required_requirements_met
            ),
        )

        findings = self._build_findings(
            intake_results=intake_results,
            evaluations=evaluations,
            accepted_rows=accepted_rows,
            rejected_rows=rejected_rows,
        )

        payload = {
            "tenant_id": configuration.tenant_id,
            "client_id": configuration.client_id,
            "engagement_id": configuration.engagement_id,
            "assessment_id": configuration.assessment_id,
            "source_summaries": [
                summary.to_dict()
                for summary in source_summaries
            ],
            "requirement_evaluations": [
                evaluation.to_dict()
                for evaluation in evaluations
            ],
            "total_rows": total_rows,
            "accepted_rows": accepted_rows,
            "rejected_rows": rejected_rows,
            "acceptance_rate": round_score(
                acceptance_rate
            ),
            "requirement_coverage_rate": round_score(
                requirement_coverage_rate
            ),
            "required_requirements_met": (
                required_requirements_met
            ),
            "quality_score": quality_score,
            "quality_grade": quality_grade.value,
            "findings": findings,
            "schema_version": (
                ASSESSMENT_EVIDENCE_QUALITY_VERSION
            ),
        }

        return AssessmentEvidenceQualitySummary(
            tenant_id=configuration.tenant_id,
            client_id=configuration.client_id,
            engagement_id=configuration.engagement_id,
            assessment_id=configuration.assessment_id,
            source_summaries=source_summaries,
            requirement_evaluations=evaluations,
            total_rows=total_rows,
            accepted_rows=accepted_rows,
            rejected_rows=rejected_rows,
            acceptance_rate=round_score(
                acceptance_rate
            ),
            requirement_coverage_rate=round_score(
                requirement_coverage_rate
            ),
            required_requirements_met=(
                required_requirements_met
            ),
            quality_score=quality_score,
            quality_grade=quality_grade,
            findings=findings,
            summary_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def _summarize_source(
        self,
        result: AssessmentEvidenceIntakeResult,
    ) -> EvidenceSourceQualitySummary:
        acceptance_rate = (
            result.accepted_count / result.total_rows
            if result.total_rows > 0
            else 0.0
        )

        return EvidenceSourceQualitySummary(
            source_id=result.source.source_id,
            source_kind=result.source.kind.value,
            display_name=result.source.display_name,
            total_rows=result.total_rows,
            accepted_rows=result.accepted_count,
            rejected_rows=result.rejected_count,
            acceptance_rate=round_score(
                acceptance_rate
            ),
            valid=result.valid,
            intake_hash=result.intake_hash,
        )

    def _evaluate_requirement(
        self,
        *,
        requirement: EvidenceRequirement,
        intake_results: tuple[
            AssessmentEvidenceIntakeResult, ...
        ],
    ) -> EvidenceRequirementEvaluation:
        observed_count = sum(
            result.accepted_count
            for result in intake_results
            if result.source.kind is requirement.source_kind
        )

        satisfied = (
            observed_count
            >= requirement.minimum_record_count
        )

        return EvidenceRequirementEvaluation(
            requirement_id=requirement.requirement_id,
            source_kind=requirement.source_kind.value,
            required=requirement.required,
            minimum_record_count=(
                requirement.minimum_record_count
            ),
            observed_record_count=observed_count,
            satisfied=satisfied,
        )

    def _build_findings(
        self,
        *,
        intake_results: tuple[
            AssessmentEvidenceIntakeResult, ...
        ],
        evaluations: tuple[
            EvidenceRequirementEvaluation, ...
        ],
        accepted_rows: int,
        rejected_rows: int,
    ) -> tuple[str, ...]:
        findings: list[str] = []

        if not intake_results:
            findings.append(
                "No evidence sources were submitted."
            )

        if accepted_rows == 0:
            findings.append(
                "No evidence rows were accepted."
            )

        if rejected_rows > 0:
            findings.append(
                f"{rejected_rows} evidence rows were rejected."
            )

        for evaluation in evaluations:
            if not evaluation.satisfied:
                findings.append(
                    "Evidence requirement "
                    f"{evaluation.requirement_id} is unmet: "
                    f"{evaluation.observed_record_count} of "
                    f"{evaluation.minimum_record_count} "
                    "required records were accepted."
                )

        if not findings:
            findings.append(
                "All configured evidence requirements were met."
            )

        return tuple(findings)
