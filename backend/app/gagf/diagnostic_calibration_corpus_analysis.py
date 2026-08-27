from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Mapping, Sequence

from backend.app.gagf.diagnostic_calibration_oracle_evaluation import (
    CALIBRATION_ORACLE_EVALUATION_AUTHORITY,
    CalibrationOracleEvaluationResult,
)
from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)


CALIBRATION_CORPUS_ANALYSIS_VERSION = "1.0.0"

CALIBRATION_CORPUS_ANALYSIS_AUTHORITY = (
    "GAGF_FIP_CALIBRATION_ANALYSIS_ONLY"
)


class CalibrationCorpusAnalysisError(
    RuntimeError
):
    """
    Raised when frozen calibration evaluations cannot be
    safely aggregated into corpus-level observations.
    """


def round_metric(
    value: float,
) -> float:
    return round(
        float(value),
        6,
    )


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationAnalysisObservation:
    scenario_id: str
    public_hash: str
    oracle_hash: str

    evaluation_hash: str

    difficulty: str
    ambiguity: str

    rank_1_hit: bool
    top_2_hit: bool
    top_3_hit: bool

    reciprocal_rank: float

    candidate_count: int

    leading_structural_level: str | None
    leading_evidence_quality: float | None

    absolute_separation: float | None
    relative_separation: float | None

    authority: str = (
        CALIBRATION_CORPUS_ANALYSIS_AUTHORITY
    )

    version: str = (
        CALIBRATION_CORPUS_ANALYSIS_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "scenario_id":
                self.scenario_id,

            "public_hash":
                self.public_hash,

            "oracle_hash":
                self.oracle_hash,

            "evaluation_hash":
                self.evaluation_hash,

            "difficulty":
                self.difficulty,

            "ambiguity":
                self.ambiguity,

            "rank_1_hit":
                self.rank_1_hit,

            "top_2_hit":
                self.top_2_hit,

            "top_3_hit":
                self.top_3_hit,

            "reciprocal_rank":
                self.reciprocal_rank,

            "candidate_count":
                self.candidate_count,

            "leading_structural_level":
                self.leading_structural_level,

            "leading_evidence_quality":
                self.leading_evidence_quality,

            "absolute_separation":
                self.absolute_separation,

            "relative_separation":
                self.relative_separation,

            "authority":
                self.authority,

            "version":
                self.version,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationCohortMetrics:
    scenario_count: int

    rank_1_rate: float
    top_2_rate: float
    top_3_rate: float

    mean_reciprocal_rank: float

    mean_candidate_count: float

    mean_evidence_quality: float | None

    mean_absolute_separation: float | None
    mean_relative_separation: float | None

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "scenario_count":
                self.scenario_count,

            "rank_1_rate":
                self.rank_1_rate,

            "top_2_rate":
                self.top_2_rate,

            "top_3_rate":
                self.top_3_rate,

            "mean_reciprocal_rank":
                self.mean_reciprocal_rank,

            "mean_candidate_count":
                self.mean_candidate_count,

            "mean_evidence_quality":
                self.mean_evidence_quality,

            "mean_absolute_separation":
                self.mean_absolute_separation,

            "mean_relative_separation":
                self.mean_relative_separation,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationCohortResult:
    cohort_key: str
    metrics: CalibrationCohortMetrics

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "cohort_key":
                self.cohort_key,

            "metrics":
                self.metrics.to_dict(),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationCorrelationSummary:
    relative_separation_vs_rank_1: float | None
    relative_separation_vs_reciprocal_rank: float | None

    evidence_quality_vs_rank_1: float | None
    evidence_quality_vs_reciprocal_rank: float | None

    candidate_count_vs_rank_1: float | None
    candidate_count_vs_reciprocal_rank: float | None

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "relative_separation_vs_rank_1":
                self.relative_separation_vs_rank_1,

            "relative_separation_vs_reciprocal_rank":
                self.relative_separation_vs_reciprocal_rank,

            "evidence_quality_vs_rank_1":
                self.evidence_quality_vs_rank_1,

            "evidence_quality_vs_reciprocal_rank":
                self.evidence_quality_vs_reciprocal_rank,

            "candidate_count_vs_rank_1":
                self.candidate_count_vs_rank_1,

            "candidate_count_vs_reciprocal_rank":
                self.candidate_count_vs_reciprocal_rank,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class CalibrationCorpusAnalysisResult:
    scenario_count: int

    scenario_ids: tuple[str, ...]

    overall: CalibrationCohortMetrics

    by_structural_level: tuple[
        CalibrationCohortResult,
        ...,
    ]

    by_candidate_count: tuple[
        CalibrationCohortResult,
        ...,
    ]

    by_difficulty: tuple[
        CalibrationCohortResult,
        ...,
    ]

    by_ambiguity: tuple[
        CalibrationCohortResult,
        ...,
    ]

    correlations: CalibrationCorrelationSummary

    source_evaluation_hashes: tuple[str, ...]

    analysis_hash: str

    authority: str = (
        CALIBRATION_CORPUS_ANALYSIS_AUTHORITY
    )

    version: str = (
        CALIBRATION_CORPUS_ANALYSIS_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "scenario_count":
                self.scenario_count,

            "scenario_ids":
                list(
                    self.scenario_ids
                ),

            "overall":
                self.overall.to_dict(),

            "by_structural_level": [
                item.to_dict()
                for item
                in self.by_structural_level
            ],

            "by_candidate_count": [
                item.to_dict()
                for item
                in self.by_candidate_count
            ],

            "by_difficulty": [
                item.to_dict()
                for item
                in self.by_difficulty
            ],

            "by_ambiguity": [
                item.to_dict()
                for item
                in self.by_ambiguity
            ],

            "correlations":
                self.correlations.to_dict(),

            "source_evaluation_hashes":
                list(
                    self.source_evaluation_hashes
                ),

            "analysis_hash":
                self.analysis_hash,

            "authority":
                self.authority,

            "version":
                self.version,
        }


class DiagnosticCalibrationCorpusAnalysisService:
    """
    Aggregate frozen scenario-level oracle evaluations.

    This service operates only after:

        blind execution
        -> diagnostic freeze
        -> oracle evaluation

    It may observe associations between calibration
    variables and ranking performance.

    It does not:

    - modify diagnostic evidence;
    - modify diagnostic ranking;
    - establish causation;
    - create diagnostic confidence;
    - define confidence thresholds;
    - label root cause;
    - authorize intervention.

    Correlation != Causation.
    Association != Confidence.
    """

    def observe(
        self,
        *,
        evaluation: CalibrationOracleEvaluationResult,
        oracle: Mapping[str, Any],
    ) -> CalibrationAnalysisObservation:
        if (
            evaluation.authority
            != CALIBRATION_ORACLE_EVALUATION_AUTHORITY
        ):
            raise (
                CalibrationCorpusAnalysisError(
                    "Corpus analysis requires a governed "
                    "calibration oracle evaluation."
                )
            )

        oracle_payload = dict(
            oracle
        )

        scenario_id = self._required_text(
            oracle_payload,
            "scenario_id",
        )

        public_hash = self._required_text(
            oracle_payload,
            "public_hash",
        )

        oracle_hash = self._required_text(
            oracle_payload,
            "oracle_hash",
        )

        difficulty = self._required_text(
            oracle_payload,
            "intended_difficulty",
        )

        ambiguity = self._required_text(
            oracle_payload,
            "intended_ambiguity",
        )

        if (
            scenario_id
            != evaluation.scenario_id
        ):
            raise (
                CalibrationCorpusAnalysisError(
                    "Oracle scenario_id does not match "
                    "evaluation."
                )
            )

        if (
            public_hash
            != evaluation.public_hash
        ):
            raise (
                CalibrationCorpusAnalysisError(
                    "Oracle public_hash does not match "
                    "evaluation."
                )
            )

        if (
            oracle_hash
            != evaluation.oracle_hash
        ):
            raise (
                CalibrationCorpusAnalysisError(
                    "Oracle oracle_hash does not match "
                    "evaluation."
                )
            )

        if evaluation.candidate_count < 1:
            raise (
                CalibrationCorpusAnalysisError(
                    "Calibration evaluation must contain "
                    "at least one ranked candidate."
                )
            )

        return (
            CalibrationAnalysisObservation(
                scenario_id=(
                    evaluation.scenario_id
                ),

                public_hash=(
                    evaluation.public_hash
                ),

                oracle_hash=(
                    evaluation.oracle_hash
                ),

                evaluation_hash=(
                    evaluation.evaluation_hash
                ),

                difficulty=(
                    difficulty
                ),

                ambiguity=(
                    ambiguity
                ),

                rank_1_hit=(
                    evaluation.rank_1_hit
                ),

                top_2_hit=(
                    evaluation.top_2_hit
                ),

                top_3_hit=(
                    evaluation.top_3_hit
                ),

                reciprocal_rank=(
                    evaluation.reciprocal_rank
                ),

                candidate_count=(
                    evaluation.candidate_count
                ),

                leading_structural_level=(
                    evaluation.leading_structural_level
                ),

                leading_evidence_quality=(
                    evaluation.leading_evidence_quality
                ),

                absolute_separation=(
                    evaluation.absolute_separation
                ),

                relative_separation=(
                    evaluation.relative_separation
                ),
            )
        )

    def analyze(
        self,
        *,
        observations: Sequence[
            CalibrationAnalysisObservation
        ],
    ) -> CalibrationCorpusAnalysisResult:
        items = tuple(
            observations
        )

        if not items:
            raise (
                CalibrationCorpusAnalysisError(
                    "Calibration corpus analysis requires "
                    "at least one observation."
                )
            )

        self._validate_observations(
            items
        )

        ordered = tuple(
            sorted(
                items,
                key=lambda item: (
                    item.scenario_id
                ),
            )
        )

        overall = self._metrics(
            ordered
        )

        by_structural_level = (
            self._group_metrics(
                ordered,
                key_function=lambda item: (
                    item.leading_structural_level
                    or "UNOBSERVED"
                ),
            )
        )

        by_candidate_count = (
            self._group_metrics(
                ordered,
                key_function=lambda item: (
                    str(
                        item.candidate_count
                    )
                ),
            )
        )

        by_difficulty = (
            self._group_metrics(
                ordered,
                key_function=lambda item: (
                    item.difficulty
                ),
            )
        )

        by_ambiguity = (
            self._group_metrics(
                ordered,
                key_function=lambda item: (
                    item.ambiguity
                ),
            )
        )

        correlations = (
            self._correlations(
                ordered
            )
        )

        scenario_ids = tuple(
            item.scenario_id
            for item
            in ordered
        )

        source_hashes = tuple(
            item.evaluation_hash
            for item
            in ordered
        )

        analysis_payload = {
            "scenario_count":
                len(
                    ordered
                ),

            "scenario_ids":
                list(
                    scenario_ids
                ),

            "overall":
                overall.to_dict(),

            "by_structural_level": [
                item.to_dict()
                for item
                in by_structural_level
            ],

            "by_candidate_count": [
                item.to_dict()
                for item
                in by_candidate_count
            ],

            "by_difficulty": [
                item.to_dict()
                for item
                in by_difficulty
            ],

            "by_ambiguity": [
                item.to_dict()
                for item
                in by_ambiguity
            ],

            "correlations":
                correlations.to_dict(),

            "source_evaluation_hashes":
                list(
                    source_hashes
                ),

            "authority":
                CALIBRATION_CORPUS_ANALYSIS_AUTHORITY,

            "version":
                CALIBRATION_CORPUS_ANALYSIS_VERSION,
        }

        analysis_hash = sha256_text(
            canonical_json(
                analysis_payload
            )
        )

        return (
            CalibrationCorpusAnalysisResult(
                scenario_count=(
                    len(
                        ordered
                    )
                ),

                scenario_ids=(
                    scenario_ids
                ),

                overall=(
                    overall
                ),

                by_structural_level=(
                    by_structural_level
                ),

                by_candidate_count=(
                    by_candidate_count
                ),

                by_difficulty=(
                    by_difficulty
                ),

                by_ambiguity=(
                    by_ambiguity
                ),

                correlations=(
                    correlations
                ),

                source_evaluation_hashes=(
                    source_hashes
                ),

                analysis_hash=(
                    analysis_hash
                ),
            )
        )

    def _validate_observations(
        self,
        observations: tuple[
            CalibrationAnalysisObservation,
            ...,
        ],
    ) -> None:
        scenario_ids = [
            item.scenario_id
            for item
            in observations
        ]

        if len(
            scenario_ids
        ) != len(
            set(
                scenario_ids
            )
        ):
            raise (
                CalibrationCorpusAnalysisError(
                    "Calibration corpus contains duplicate "
                    "scenario_id values."
                )
            )

        evaluation_hashes = [
            item.evaluation_hash
            for item
            in observations
        ]

        if len(
            evaluation_hashes
        ) != len(
            set(
                evaluation_hashes
            )
        ):
            raise (
                CalibrationCorpusAnalysisError(
                    "Calibration corpus contains duplicate "
                    "evaluation hashes."
                )
            )

        for item in observations:
            if (
                item.authority
                != CALIBRATION_CORPUS_ANALYSIS_AUTHORITY
            ):
                raise (
                    CalibrationCorpusAnalysisError(
                        "Calibration observation has "
                        "unexpected authority."
                    )
                )

            if item.candidate_count < 1:
                raise (
                    CalibrationCorpusAnalysisError(
                        "Calibration observation candidate "
                        "count must be at least 1."
                    )
                )

            if not (
                0.0
                <= item.reciprocal_rank
                <= 1.0
            ):
                raise (
                    CalibrationCorpusAnalysisError(
                        "Calibration reciprocal rank must "
                        "be between 0 and 1."
                    )
                )

            if (
                item.leading_evidence_quality
                is not None
                and not (
                    0.0
                    <= item.leading_evidence_quality
                    <= 1.0
                )
            ):
                raise (
                    CalibrationCorpusAnalysisError(
                        "Calibration evidence quality must "
                        "be between 0 and 1."
                    )
                )

            if (
                item.absolute_separation
                is not None
                and item.absolute_separation < 0.0
            ):
                raise (
                    CalibrationCorpusAnalysisError(
                        "Absolute separation must not "
                        "be negative."
                    )
                )

            if (
                item.relative_separation
                is not None
                and item.relative_separation < 0.0
            ):
                raise (
                    CalibrationCorpusAnalysisError(
                        "Relative separation must not "
                        "be negative."
                    )
                )

    def _metrics(
        self,
        observations: Sequence[
            CalibrationAnalysisObservation
        ],
    ) -> CalibrationCohortMetrics:
        items = tuple(
            observations
        )

        count = len(
            items
        )

        if count < 1:
            raise (
                CalibrationCorpusAnalysisError(
                    "Cannot calculate metrics for an "
                    "empty cohort."
                )
            )

        rank_1_rate = self._rate(
            item.rank_1_hit
            for item
            in items
        )

        top_2_rate = self._rate(
            item.top_2_hit
            for item
            in items
        )

        top_3_rate = self._rate(
            item.top_3_hit
            for item
            in items
        )

        mean_reciprocal_rank = (
            self._mean(
                [
                    item.reciprocal_rank
                    for item
                    in items
                ]
            )
        )

        mean_candidate_count = (
            self._mean(
                [
                    float(
                        item.candidate_count
                    )
                    for item
                    in items
                ]
            )
        )

        mean_evidence_quality = (
            self._optional_mean(
                [
                    item.leading_evidence_quality
                    for item
                    in items
                ]
            )
        )

        mean_absolute_separation = (
            self._optional_mean(
                [
                    item.absolute_separation
                    for item
                    in items
                ]
            )
        )

        mean_relative_separation = (
            self._optional_mean(
                [
                    item.relative_separation
                    for item
                    in items
                ]
            )
        )

        return (
            CalibrationCohortMetrics(
                scenario_count=(
                    count
                ),

                rank_1_rate=(
                    rank_1_rate
                ),

                top_2_rate=(
                    top_2_rate
                ),

                top_3_rate=(
                    top_3_rate
                ),

                mean_reciprocal_rank=(
                    mean_reciprocal_rank
                ),

                mean_candidate_count=(
                    mean_candidate_count
                ),

                mean_evidence_quality=(
                    mean_evidence_quality
                ),

                mean_absolute_separation=(
                    mean_absolute_separation
                ),

                mean_relative_separation=(
                    mean_relative_separation
                ),
            )
        )

    def _group_metrics(
        self,
        observations: tuple[
            CalibrationAnalysisObservation,
            ...,
        ],
        *,
        key_function,
    ) -> tuple[
        CalibrationCohortResult,
        ...,
    ]:
        grouped: dict[
            str,
            list[
                CalibrationAnalysisObservation
            ],
        ] = {}

        for item in observations:
            key = str(
                key_function(
                    item
                )
            )

            grouped.setdefault(
                key,
                [],
            ).append(
                item
            )

        return tuple(
            CalibrationCohortResult(
                cohort_key=key,
                metrics=self._metrics(
                    grouped[
                        key
                    ]
                ),
            )
            for key
            in sorted(
                grouped
            )
        )

    def _correlations(
        self,
        observations: tuple[
            CalibrationAnalysisObservation,
            ...,
        ],
    ) -> CalibrationCorrelationSummary:
        rank_1 = [
            1.0
            if item.rank_1_hit
            else 0.0
            for item
            in observations
        ]

        reciprocal_rank = [
            item.reciprocal_rank
            for item
            in observations
        ]

        separation_rank_1 = (
            self._optional_pair_correlation(
                observations=(
                    observations
                ),
                value_function=lambda item: (
                    item.relative_separation
                ),
                outcome_values=(
                    rank_1
                ),
            )
        )

        separation_rr = (
            self._optional_pair_correlation(
                observations=(
                    observations
                ),
                value_function=lambda item: (
                    item.relative_separation
                ),
                outcome_values=(
                    reciprocal_rank
                ),
            )
        )

        quality_rank_1 = (
            self._optional_pair_correlation(
                observations=(
                    observations
                ),
                value_function=lambda item: (
                    item.leading_evidence_quality
                ),
                outcome_values=(
                    rank_1
                ),
            )
        )

        quality_rr = (
            self._optional_pair_correlation(
                observations=(
                    observations
                ),
                value_function=lambda item: (
                    item.leading_evidence_quality
                ),
                outcome_values=(
                    reciprocal_rank
                ),
            )
        )

        candidate_count = [
            float(
                item.candidate_count
            )
            for item
            in observations
        ]

        candidate_rank_1 = (
            self._pearson(
                candidate_count,
                rank_1,
            )
        )

        candidate_rr = (
            self._pearson(
                candidate_count,
                reciprocal_rank,
            )
        )

        return (
            CalibrationCorrelationSummary(
                relative_separation_vs_rank_1=(
                    separation_rank_1
                ),

                relative_separation_vs_reciprocal_rank=(
                    separation_rr
                ),

                evidence_quality_vs_rank_1=(
                    quality_rank_1
                ),

                evidence_quality_vs_reciprocal_rank=(
                    quality_rr
                ),

                candidate_count_vs_rank_1=(
                    candidate_rank_1
                ),

                candidate_count_vs_reciprocal_rank=(
                    candidate_rr
                ),
            )
        )

    def _optional_pair_correlation(
        self,
        *,
        observations: tuple[
            CalibrationAnalysisObservation,
            ...,
        ],
        value_function,
        outcome_values: Sequence[
            float
        ],
    ) -> float | None:
        x_values = []
        y_values = []

        for index, item in enumerate(
            observations
        ):
            value = value_function(
                item
            )

            if value is None:
                continue

            x_values.append(
                float(
                    value
                )
            )

            y_values.append(
                float(
                    outcome_values[
                        index
                    ]
                )
            )

        return self._pearson(
            x_values,
            y_values,
        )

    def _pearson(
        self,
        x_values: Sequence[
            float
        ],
        y_values: Sequence[
            float
        ],
    ) -> float | None:
        x = tuple(
            float(
                value
            )
            for value
            in x_values
        )

        y = tuple(
            float(
                value
            )
            for value
            in y_values
        )

        if len(
            x
        ) != len(
            y
        ):
            raise (
                CalibrationCorpusAnalysisError(
                    "Correlation inputs have different "
                    "lengths."
                )
            )

        if len(
            x
        ) < 2:
            return None

        mean_x = sum(
            x
        ) / len(
            x
        )

        mean_y = sum(
            y
        ) / len(
            y
        )

        numerator = sum(
            (
                left
                - mean_x
            )
            * (
                right
                - mean_y
            )
            for left, right
            in zip(
                x,
                y,
            )
        )

        x_variance = sum(
            (
                value
                - mean_x
            )
            ** 2
            for value
            in x
        )

        y_variance = sum(
            (
                value
                - mean_y
            )
            ** 2
            for value
            in y
        )

        denominator = sqrt(
            x_variance
            * y_variance
        )

        if denominator == 0.0:
            return None

        return round_metric(
            numerator
            / denominator
        )

    def _rate(
        self,
        values,
    ) -> float:
        normalized = tuple(
            bool(
                value
            )
            for value
            in values
        )

        if not normalized:
            raise (
                CalibrationCorpusAnalysisError(
                    "Cannot calculate rate for an "
                    "empty sequence."
                )
            )

        return round_metric(
            sum(
                1
                for value
                in normalized
                if value
            )
            / len(
                normalized
            )
        )

    def _mean(
        self,
        values: Sequence[
            float
        ],
    ) -> float:
        normalized = tuple(
            float(
                value
            )
            for value
            in values
        )

        if not normalized:
            raise (
                CalibrationCorpusAnalysisError(
                    "Cannot calculate mean for an "
                    "empty sequence."
                )
            )

        return round_metric(
            sum(
                normalized
            )
            / len(
                normalized
            )
        )

    def _optional_mean(
        self,
        values: Sequence[
            float | None
        ],
    ) -> float | None:
        observed = tuple(
            float(
                value
            )
            for value
            in values
            if value is not None
        )

        if not observed:
            return None

        return self._mean(
            observed
        )

    def _required_text(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> str:
        value = payload.get(
            field_name
        )

        if not isinstance(
            value,
            str,
        ):
            raise (
                CalibrationCorpusAnalysisError(
                    f"{field_name} must be a string."
                )
            )

        normalized = (
            value.strip()
        )

        if not normalized:
            raise (
                CalibrationCorpusAnalysisError(
                    f"{field_name} must not be empty."
                )
            )

        return normalized