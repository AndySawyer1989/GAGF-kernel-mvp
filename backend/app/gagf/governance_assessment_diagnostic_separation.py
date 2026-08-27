from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_primary_diagnosis_evidence import (
    AssessmentPrimaryDiagnosisEvidenceSummary,
    PrimaryDiagnosisConditionEvidence,
)
from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)


DIAGNOSTIC_SEPARATION_VERSION = "1.0.0"

DIAGNOSTIC_SEPARATION_AUTHORITY = (
    "GAGF_FIP_ONLY"
)


class DiagnosticSeparationEvidenceError(
    RuntimeError
):
    """
    Raised when threshold-free diagnostic-separation
    evidence cannot be derived deterministically.
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
class DiagnosticSeparationCandidateEvidence:
    category: str
    rank: int
    explanatory_score: float
    relative_to_highest: float
    evidence_quality: float | None
    structural_level: str
    primary_evidence_hash: str

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "category":
                self.category,

            "rank":
                self.rank,

            "explanatory_score":
                self.explanatory_score,

            "relative_to_highest":
                self.relative_to_highest,

            "evidence_quality":
                self.evidence_quality,

            "structural_level":
                self.structural_level,

            "primary_evidence_hash":
                self.primary_evidence_hash,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class DiagnosticSeparationMetrics:
    rank_1_score: float | None
    rank_2_score: float | None
    rank_3_score: float | None

    rank_1_to_rank_2_absolute: float | None
    rank_1_to_rank_2_relative: float | None

    rank_1_to_rank_3_absolute: float | None
    rank_1_to_rank_3_relative: float | None

    top_3_score_spread: float | None

    leading_relative_to_highest: float | None
    runner_up_relative_to_highest: float | None

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "rank_1_score":
                self.rank_1_score,

            "rank_2_score":
                self.rank_2_score,

            "rank_3_score":
                self.rank_3_score,

            "rank_1_to_rank_2_absolute":
                self.rank_1_to_rank_2_absolute,

            "rank_1_to_rank_2_relative":
                self.rank_1_to_rank_2_relative,

            "rank_1_to_rank_3_absolute":
                self.rank_1_to_rank_3_absolute,

            "rank_1_to_rank_3_relative":
                self.rank_1_to_rank_3_relative,

            "top_3_score_spread":
                self.top_3_score_spread,

            "leading_relative_to_highest":
                self.leading_relative_to_highest,

            "runner_up_relative_to_highest":
                self.runner_up_relative_to_highest,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class DiagnosticSeparationSupportEvidence:
    candidate_count: int

    ranked_candidate_count: int

    evidence_quality_observed_count: int

    leading_evidence_quality: float | None
    runner_up_evidence_quality: float | None

    leading_structural_level: str | None
    runner_up_structural_level: str | None

    leading_event_count: int | None
    runner_up_event_count: int | None

    leading_unique_work_item_count: int | None
    runner_up_unique_work_item_count: int | None

    leading_active_day_count: int | None
    runner_up_active_day_count: int | None

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "candidate_count":
                self.candidate_count,

            "ranked_candidate_count":
                self.ranked_candidate_count,

            "evidence_quality_observed_count":
                self.evidence_quality_observed_count,

            "leading_evidence_quality":
                self.leading_evidence_quality,

            "runner_up_evidence_quality":
                self.runner_up_evidence_quality,

            "leading_structural_level":
                self.leading_structural_level,

            "runner_up_structural_level":
                self.runner_up_structural_level,

            "leading_event_count":
                self.leading_event_count,

            "runner_up_event_count":
                self.runner_up_event_count,

            "leading_unique_work_item_count":
                self.leading_unique_work_item_count,

            "runner_up_unique_work_item_count":
                self.runner_up_unique_work_item_count,

            "leading_active_day_count":
                self.leading_active_day_count,

            "runner_up_active_day_count":
                self.runner_up_active_day_count,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class AssessmentDiagnosticSeparationEvidenceSummary:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    leading_candidate: (
        DiagnosticSeparationCandidateEvidence
        | None
    )

    runner_up_candidate: (
        DiagnosticSeparationCandidateEvidence
        | None
    )

    third_ranked_candidate: (
        DiagnosticSeparationCandidateEvidence
        | None
    )

    metrics: DiagnosticSeparationMetrics

    support: DiagnosticSeparationSupportEvidence

    primary_diagnosis_summary_hash: str

    summary_hash: str

    authority: str = (
        DIAGNOSTIC_SEPARATION_AUTHORITY
    )

    schema_version: str = (
        DIAGNOSTIC_SEPARATION_VERSION
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
    def leading_candidate_category(
        self,
    ) -> str | None:
        if self.leading_candidate is None:
            return None

        return (
            self.leading_candidate.category
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

            "leading_candidate":
                (
                    self.leading_candidate.to_dict()
                    if self.leading_candidate
                    is not None
                    else None
                ),

            "runner_up_candidate":
                (
                    self.runner_up_candidate.to_dict()
                    if self.runner_up_candidate
                    is not None
                    else None
                ),

            "third_ranked_candidate":
                (
                    self.third_ranked_candidate.to_dict()
                    if self.third_ranked_candidate
                    is not None
                    else None
                ),

            "leading_candidate_category":
                self.leading_candidate_category,

            "metrics":
                self.metrics.to_dict(),

            "support":
                self.support.to_dict(),

            "primary_diagnosis_summary_hash":
                self.primary_diagnosis_summary_hash,

            "summary_hash":
                self.summary_hash,

            "authority":
                self.authority,

            "schema_version":
                self.schema_version,
        }


class GovernanceAssessmentDiagnosticSeparationService:
    """
    Derive threshold-free diagnostic-separation evidence
    from frozen primary-diagnosis ranking evidence.

    This layer measures separation only.

    It does not:

    - classify confidence;
    - establish correctness;
    - establish causation;
    - identify root cause;
    - declare a final primary diagnosis;
    - authorize intervention.

    Separation != Confidence.
    Confidence != Correctness.
    Rank 1 != Primary Diagnosis.
    Primary Diagnosis != Root Cause.
    """

    def analyze(
        self,
        *,
        primary_diagnosis_summary: (
            AssessmentPrimaryDiagnosisEvidenceSummary
        ),
    ) -> AssessmentDiagnosticSeparationEvidenceSummary:
        conditions = tuple(
            primary_diagnosis_summary.conditions
        )

        self._validate_ranking(
            conditions
        )

        leading = (
            conditions[0]
            if len(
                conditions
            ) >= 1
            else None
        )

        runner_up = (
            conditions[1]
            if len(
                conditions
            ) >= 2
            else None
        )

        third = (
            conditions[2]
            if len(
                conditions
            ) >= 3
            else None
        )

        metrics = (
            self._build_metrics(
                leading=leading,
                runner_up=runner_up,
                third=third,
            )
        )

        support = (
            self._build_support(
                conditions=conditions,
                leading=leading,
                runner_up=runner_up,
            )
        )

        leading_evidence = (
            self._candidate_evidence(
                leading
            )
        )

        runner_up_evidence = (
            self._candidate_evidence(
                runner_up
            )
        )

        third_evidence = (
            self._candidate_evidence(
                third
            )
        )

        summary_payload = {
            "tenant_id":
                primary_diagnosis_summary
                .tenant_id,

            "client_id":
                primary_diagnosis_summary
                .client_id,

            "engagement_id":
                primary_diagnosis_summary
                .engagement_id,

            "assessment_id":
                primary_diagnosis_summary
                .assessment_id,

            "leading_candidate":
                (
                    leading_evidence.to_dict()
                    if leading_evidence
                    is not None
                    else None
                ),

            "runner_up_candidate":
                (
                    runner_up_evidence.to_dict()
                    if runner_up_evidence
                    is not None
                    else None
                ),

            "third_ranked_candidate":
                (
                    third_evidence.to_dict()
                    if third_evidence
                    is not None
                    else None
                ),

            "metrics":
                metrics.to_dict(),

            "support":
                support.to_dict(),

            "primary_diagnosis_summary_hash":
                primary_diagnosis_summary
                .summary_hash,

            "authority":
                DIAGNOSTIC_SEPARATION_AUTHORITY,

            "schema_version":
                DIAGNOSTIC_SEPARATION_VERSION,
        }

        summary_hash = sha256_text(
            canonical_json(
                summary_payload
            )
        )

        return (
            AssessmentDiagnosticSeparationEvidenceSummary(
                tenant_id=(
                    primary_diagnosis_summary
                    .tenant_id
                ),

                client_id=(
                    primary_diagnosis_summary
                    .client_id
                ),

                engagement_id=(
                    primary_diagnosis_summary
                    .engagement_id
                ),

                assessment_id=(
                    primary_diagnosis_summary
                    .assessment_id
                ),

                leading_candidate=(
                    leading_evidence
                ),

                runner_up_candidate=(
                    runner_up_evidence
                ),

                third_ranked_candidate=(
                    third_evidence
                ),

                metrics=(
                    metrics
                ),

                support=(
                    support
                ),

                primary_diagnosis_summary_hash=(
                    primary_diagnosis_summary
                    .summary_hash
                ),

                summary_hash=(
                    summary_hash
                ),
            )
        )

    def _build_metrics(
        self,
        *,
        leading: (
            PrimaryDiagnosisConditionEvidence
            | None
        ),
        runner_up: (
            PrimaryDiagnosisConditionEvidence
            | None
        ),
        third: (
            PrimaryDiagnosisConditionEvidence
            | None
        ),
    ) -> DiagnosticSeparationMetrics:
        rank_1_score = (
            self._score(
                leading
            )
        )

        rank_2_score = (
            self._score(
                runner_up
            )
        )

        rank_3_score = (
            self._score(
                third
            )
        )

        rank_1_to_rank_2_absolute = (
            self._absolute_difference(
                rank_1_score,
                rank_2_score,
            )
        )

        rank_1_to_rank_2_relative = (
            self._relative_difference(
                rank_1_score,
                rank_2_score,
            )
        )

        rank_1_to_rank_3_absolute = (
            self._absolute_difference(
                rank_1_score,
                rank_3_score,
            )
        )

        rank_1_to_rank_3_relative = (
            self._relative_difference(
                rank_1_score,
                rank_3_score,
            )
        )

        top_3_score_spread = (
            self._top_3_spread(
                rank_1_score=rank_1_score,
                rank_2_score=rank_2_score,
                rank_3_score=rank_3_score,
            )
        )

        return (
            DiagnosticSeparationMetrics(
                rank_1_score=(
                    rank_1_score
                ),

                rank_2_score=(
                    rank_2_score
                ),

                rank_3_score=(
                    rank_3_score
                ),

                rank_1_to_rank_2_absolute=(
                    rank_1_to_rank_2_absolute
                ),

                rank_1_to_rank_2_relative=(
                    rank_1_to_rank_2_relative
                ),

                rank_1_to_rank_3_absolute=(
                    rank_1_to_rank_3_absolute
                ),

                rank_1_to_rank_3_relative=(
                    rank_1_to_rank_3_relative
                ),

                top_3_score_spread=(
                    top_3_score_spread
                ),

                leading_relative_to_highest=(
                    leading.relative_to_highest
                    if leading
                    is not None
                    else None
                ),

                runner_up_relative_to_highest=(
                    runner_up.relative_to_highest
                    if runner_up
                    is not None
                    else None
                ),
            )
        )

    def _build_support(
        self,
        *,
        conditions: tuple[
            PrimaryDiagnosisConditionEvidence,
            ...,
        ],
        leading: (
            PrimaryDiagnosisConditionEvidence
            | None
        ),
        runner_up: (
            PrimaryDiagnosisConditionEvidence
            | None
        ),
    ) -> DiagnosticSeparationSupportEvidence:
        evidence_quality_observed_count = sum(
            condition.evidence_quality
            is not None
            for condition
            in conditions
        )

        return (
            DiagnosticSeparationSupportEvidence(
                candidate_count=(
                    len(
                        conditions
                    )
                ),

                ranked_candidate_count=(
                    len(
                        conditions
                    )
                ),

                evidence_quality_observed_count=(
                    evidence_quality_observed_count
                ),

                leading_evidence_quality=(
                    leading.evidence_quality
                    if leading
                    is not None
                    else None
                ),

                runner_up_evidence_quality=(
                    runner_up.evidence_quality
                    if runner_up
                    is not None
                    else None
                ),

                leading_structural_level=(
                    leading.structural_level.value
                    if leading
                    is not None
                    else None
                ),

                runner_up_structural_level=(
                    runner_up.structural_level.value
                    if runner_up
                    is not None
                    else None
                ),

                leading_event_count=(
                    leading.event_count
                    if leading
                    is not None
                    else None
                ),

                runner_up_event_count=(
                    runner_up.event_count
                    if runner_up
                    is not None
                    else None
                ),

                leading_unique_work_item_count=(
                    leading.unique_work_item_count
                    if leading
                    is not None
                    else None
                ),

                runner_up_unique_work_item_count=(
                    runner_up.unique_work_item_count
                    if runner_up
                    is not None
                    else None
                ),

                leading_active_day_count=(
                    leading.active_day_count
                    if leading
                    is not None
                    else None
                ),

                runner_up_active_day_count=(
                    runner_up.active_day_count
                    if runner_up
                    is not None
                    else None
                ),
            )
        )

    def _candidate_evidence(
        self,
        condition: (
            PrimaryDiagnosisConditionEvidence
            | None
        ),
    ) -> (
        DiagnosticSeparationCandidateEvidence
        | None
    ):
        if condition is None:
            return None

        return (
            DiagnosticSeparationCandidateEvidence(
                category=(
                    condition.category
                ),

                rank=(
                    condition.rank
                ),

                explanatory_score=(
                    condition
                    .explanatory_score
                ),

                relative_to_highest=(
                    condition
                    .relative_to_highest
                ),

                evidence_quality=(
                    condition
                    .evidence_quality
                ),

                structural_level=(
                    condition
                    .structural_level
                    .value
                ),

                primary_evidence_hash=(
                    condition
                    .evidence_hash
                ),
            )
        )

    def _validate_ranking(
        self,
        conditions: tuple[
            PrimaryDiagnosisConditionEvidence,
            ...,
        ],
    ) -> None:
        categories: set[str] = set()

        previous_score: float | None = None

        for expected_rank, condition in enumerate(
            conditions,
            start=1,
        ):
            if (
                condition.rank
                != expected_rank
            ):
                raise (
                    DiagnosticSeparationEvidenceError(
                        "Primary-diagnosis ranking must "
                        "be contiguous and ordered from "
                        "rank 1."
                    )
                )

            if condition.category in categories:
                raise (
                    DiagnosticSeparationEvidenceError(
                        "Primary-diagnosis ranking "
                        "contains duplicate category: "
                        f"{condition.category}"
                    )
                )

            categories.add(
                condition.category
            )

            score = (
                condition
                .explanatory_score
            )

            if (
                previous_score
                is not None
                and score
                > previous_score
            ):
                raise (
                    DiagnosticSeparationEvidenceError(
                        "Primary-diagnosis ranking scores "
                        "must be non-increasing."
                    )
                )

            previous_score = (
                score
            )

    def _score(
        self,
        condition: (
            PrimaryDiagnosisConditionEvidence
            | None
        ),
    ) -> float | None:
        if condition is None:
            return None

        return round_metric(
            condition
            .explanatory_score
        )

    def _absolute_difference(
        self,
        highest: float | None,
        lower: float | None,
    ) -> float | None:
        if (
            highest is None
            or lower is None
        ):
            return None

        return round_metric(
            highest
            - lower
        )

    def _relative_difference(
        self,
        highest: float | None,
        lower: float | None,
    ) -> float | None:
        if (
            highest is None
            or lower is None
        ):
            return None

        if highest <= 0:
            return 0.0

        return round_metric(
            (
                highest
                - lower
            )
            / highest
        )

    def _top_3_spread(
        self,
        *,
        rank_1_score: float | None,
        rank_2_score: float | None,
        rank_3_score: float | None,
    ) -> float | None:
        available = [
            score
            for score
            in (
                rank_1_score,
                rank_2_score,
                rank_3_score,
            )
            if score is not None
        ]

        if len(
            available
        ) < 2:
            return None

        return round_metric(
            max(
                available
            )
            - min(
                available
            )
        )