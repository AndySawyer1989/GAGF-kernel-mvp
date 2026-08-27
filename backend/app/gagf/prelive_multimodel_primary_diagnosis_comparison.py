from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)


PRELIVE_PRIMARY_DIAGNOSIS_COMPARISON_VERSION = (
    "1.0.0"
)

PRELIVE_PRIMARY_DIAGNOSIS_COMPARISON_STATUS = (
    "primary_diagnosis_ranking_comparison_complete"
)

PRELIVE_PRIMARY_DIAGNOSIS_COMPARISON_AUTHORITY = (
    "GAGF_FIP_ONLY"
)

PRIMARY_DIAGNOSIS_COMPARISON_FILENAME = (
    "primary_diagnosis_ranking_comparison.json"
)

PRIMARY_DIAGNOSIS_REPLAY_FILENAME = (
    "primary_diagnosis_ranking_replay.json"
)


class PrelivePrimaryDiagnosisComparisonError(
    RuntimeError
):
    """
    Raised when frozen primary-diagnosis ranking
    receipts cannot be compared safely.
    """


def round_metric(
    value: float,
) -> float:
    return round(
        float(value),
        10,
    )


@dataclass(
    frozen=True,
    slots=True,
)
class PrelivePrimaryDiagnosisExpectedConditionResult:
    category: str
    rank: int | None
    reciprocal_rank: float
    explanatory_score: float | None
    score_deficit_from_highest: float | None
    structural_level: str | None

    @property
    def in_top_1(
        self,
    ) -> bool:
        return self.rank == 1

    @property
    def in_top_2(
        self,
    ) -> bool:
        return (
            self.rank is not None
            and self.rank <= 2
        )

    @property
    def in_top_3(
        self,
    ) -> bool:
        return (
            self.rank is not None
            and self.rank <= 3
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "category":
                self.category,

            "rank":
                self.rank,

            "reciprocal_rank":
                self.reciprocal_rank,

            "explanatory_score":
                self.explanatory_score,

            "score_deficit_from_highest":
                self.score_deficit_from_highest,

            "structural_level":
                self.structural_level,

            "in_top_1":
                self.in_top_1,

            "in_top_2":
                self.in_top_2,

            "in_top_3":
                self.in_top_3,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class PrelivePrimaryDiagnosisModelComparison:
    model_label: str
    scenario_id: str
    scenario_sha256: str
    hierarchy_key: str

    benchmark_hash: str
    structural_replay_hash: str
    primary_diagnosis_replay_hash: str

    benchmark_binding_valid: bool
    hierarchy_binding_valid: bool
    scenario_binding_valid: bool

    expected_conditions: tuple[
        str,
        ...,
    ]

    ranked_conditions: tuple[
        str,
        ...,
    ]

    highest_ranked_condition: str | None

    expected_results: tuple[
        PrelivePrimaryDiagnosisExpectedConditionResult,
        ...,
    ]

    rank_1_score: float | None
    rank_2_score: float | None
    rank_1_to_rank_2_margin: float | None

    mean_expected_reciprocal_rank: float

    @property
    def expected_condition_count(
        self,
    ) -> int:
        return len(
            self.expected_conditions
        )

    @property
    def expected_at_rank_1_count(
        self,
    ) -> int:
        return sum(
            result.in_top_1
            for result
            in self.expected_results
        )

    @property
    def expected_within_top_2_count(
        self,
    ) -> int:
        return sum(
            result.in_top_2
            for result
            in self.expected_results
        )

    @property
    def expected_within_top_3_count(
        self,
    ) -> int:
        return sum(
            result.in_top_3
            for result
            in self.expected_results
        )

    @property
    def has_expected_at_rank_1(
        self,
    ) -> bool:
        return (
            self.expected_at_rank_1_count
            > 0
        )

    @property
    def all_expected_within_top_2(
        self,
    ) -> bool:
        return (
            self.expected_condition_count
            > 0
            and
            self.expected_within_top_2_count
            == self.expected_condition_count
        )

    @property
    def all_expected_within_top_3(
        self,
    ) -> bool:
        return (
            self.expected_condition_count
            > 0
            and
            self.expected_within_top_3_count
            == self.expected_condition_count
        )

    @property
    def best_expected_rank(
        self,
    ) -> int | None:
        ranks = [
            result.rank
            for result
            in self.expected_results
            if result.rank is not None
        ]

        if not ranks:
            return None

        return min(
            ranks
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "model_label":
                self.model_label,

            "scenario_id":
                self.scenario_id,

            "scenario_sha256":
                self.scenario_sha256,

            "hierarchy_key":
                self.hierarchy_key,

            "benchmark_hash":
                self.benchmark_hash,

            "structural_replay_hash":
                self.structural_replay_hash,

            "primary_diagnosis_replay_hash":
                self.primary_diagnosis_replay_hash,

            "benchmark_binding_valid":
                self.benchmark_binding_valid,

            "hierarchy_binding_valid":
                self.hierarchy_binding_valid,

            "scenario_binding_valid":
                self.scenario_binding_valid,

            "expected_conditions":
                list(
                    self.expected_conditions
                ),

            "ranked_conditions":
                list(
                    self.ranked_conditions
                ),

            "highest_ranked_condition":
                self.highest_ranked_condition,

            "expected_results": [
                result.to_dict()
                for result
                in self.expected_results
            ],

            "expected_condition_count":
                self.expected_condition_count,

            "expected_at_rank_1_count":
                self.expected_at_rank_1_count,

            "expected_within_top_2_count":
                self.expected_within_top_2_count,

            "expected_within_top_3_count":
                self.expected_within_top_3_count,

            "has_expected_at_rank_1":
                self.has_expected_at_rank_1,

            "all_expected_within_top_2":
                self.all_expected_within_top_2,

            "all_expected_within_top_3":
                self.all_expected_within_top_3,

            "best_expected_rank":
                self.best_expected_rank,

            "mean_expected_reciprocal_rank":
                self.mean_expected_reciprocal_rank,

            "rank_1_score":
                self.rank_1_score,

            "rank_2_score":
                self.rank_2_score,

            "rank_1_to_rank_2_margin":
                self.rank_1_to_rank_2_margin,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class PrelivePrimaryDiagnosisComparisonResult:
    models: tuple[
        PrelivePrimaryDiagnosisModelComparison,
        ...,
    ]

    comparison_hash: str

    status: str = (
        PRELIVE_PRIMARY_DIAGNOSIS_COMPARISON_STATUS
    )

    authority: str = (
        PRELIVE_PRIMARY_DIAGNOSIS_COMPARISON_AUTHORITY
    )

    version: str = (
        PRELIVE_PRIMARY_DIAGNOSIS_COMPARISON_VERSION
    )

    @property
    def model_count(
        self,
    ) -> int:
        return len(
            self.models
        )

    @property
    def total_expected_conditions(
        self,
    ) -> int:
        return sum(
            model.expected_condition_count
            for model
            in self.models
        )

    @property
    def expected_at_rank_1_count(
        self,
    ) -> int:
        return sum(
            model.expected_at_rank_1_count
            for model
            in self.models
        )

    @property
    def expected_within_top_2_count(
        self,
    ) -> int:
        return sum(
            model.expected_within_top_2_count
            for model
            in self.models
        )

    @property
    def expected_within_top_3_count(
        self,
    ) -> int:
        return sum(
            model.expected_within_top_3_count
            for model
            in self.models
        )

    @property
    def expected_rank_1_rate(
        self,
    ) -> float:
        return self._rate(
            self.expected_at_rank_1_count,
            self.total_expected_conditions,
        )

    @property
    def expected_top_2_rate(
        self,
    ) -> float:
        return self._rate(
            self.expected_within_top_2_count,
            self.total_expected_conditions,
        )

    @property
    def expected_top_3_rate(
        self,
    ) -> float:
        return self._rate(
            self.expected_within_top_3_count,
            self.total_expected_conditions,
        )

    @property
    def models_with_expected_at_rank_1(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            model.model_label
            for model
            in self.models
            if model.has_expected_at_rank_1
        )

    @property
    def models_with_all_expected_top_2(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            model.model_label
            for model
            in self.models
            if model.all_expected_within_top_2
        )

    @property
    def models_with_all_expected_top_3(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            model.model_label
            for model
            in self.models
            if model.all_expected_within_top_3
        )

    @property
    def mean_expected_reciprocal_rank(
        self,
    ) -> float:
        values = [
            result.reciprocal_rank
            for model
            in self.models
            for result
            in model.expected_results
        ]

        if not values:
            return 0.0

        return round_metric(
            sum(
                values
            )
            / len(
                values
            )
        )

    @property
    def mean_model_expected_reciprocal_rank(
        self,
    ) -> float:
        if not self.models:
            return 0.0

        return round_metric(
            sum(
                model.mean_expected_reciprocal_rank
                for model
                in self.models
            )
            / len(
                self.models
            )
        )

    def _rate(
        self,
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator <= 0:
            return 0.0

        return round_metric(
            numerator
            / denominator
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "status":
                self.status,

            "authority":
                self.authority,

            "version":
                self.version,

            "model_count":
                self.model_count,

            "total_expected_conditions":
                self.total_expected_conditions,

            "expected_at_rank_1_count":
                self.expected_at_rank_1_count,

            "expected_within_top_2_count":
                self.expected_within_top_2_count,

            "expected_within_top_3_count":
                self.expected_within_top_3_count,

            "expected_rank_1_rate":
                self.expected_rank_1_rate,

            "expected_top_2_rate":
                self.expected_top_2_rate,

            "expected_top_3_rate":
                self.expected_top_3_rate,

            "mean_expected_reciprocal_rank":
                self.mean_expected_reciprocal_rank,

            "mean_model_expected_reciprocal_rank":
                self.mean_model_expected_reciprocal_rank,

            "models_with_expected_at_rank_1":
                list(
                    self.models_with_expected_at_rank_1
                ),

            "models_with_all_expected_top_2":
                list(
                    self.models_with_all_expected_top_2
                ),

            "models_with_all_expected_top_3":
                list(
                    self.models_with_all_expected_top_3
                ),

            "models": [
                model.to_dict()
                for model
                in self.models
            ],

            "comparison_hash":
                self.comparison_hash,
        }


class PreliveMultimodelPrimaryDiagnosisComparisonService:
    """
    Evaluate frozen primary-diagnosis ranking receipts
    against already-sealed expected-condition metadata.

    This service is evaluation-only.

    It does not:

    - generate evidence;
    - rerun an AI model;
    - modify ranking weights;
    - modify structural classification;
    - modify a benchmark database;
    - establish causation;
    - declare root cause;
    - authorize intervention.
    """

    def compare(
        self,
        *,
        structural_comparison_path: str | Path,
        benchmark_directories: Sequence[
            str | Path
        ],
        output_directory: str | Path,
    ) -> PrelivePrimaryDiagnosisComparisonResult:
        structural_comparison = (
            self._read_json(
                Path(
                    structural_comparison_path
                )
            )
        )

        structural_models = (
            self._structural_model_map(
                structural_comparison
            )
        )

        model_results = tuple(
            sorted(
                (
                    self._compare_model(
                        benchmark_directory=Path(
                            directory
                        ),
                        structural_models=(
                            structural_models
                        ),
                    )
                    for directory
                    in benchmark_directories
                ),
                key=lambda item:
                    item.model_label,
            )
        )

        if not model_results:
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    "At least one benchmark directory "
                    "is required."
                )
            )

        comparison_payload = (
            self._comparison_payload(
                model_results
            )
        )

        comparison_hash = sha256_text(
            canonical_json(
                comparison_payload
            )
        )

        result = (
            PrelivePrimaryDiagnosisComparisonResult(
                models=model_results,
                comparison_hash=(
                    comparison_hash
                ),
            )
        )

        self.write_receipt(
            output_directory=(
                output_directory
            ),
            result=result,
        )

        return result

    def _compare_model(
        self,
        *,
        benchmark_directory: Path,
        structural_models: Mapping[
            str,
            Mapping[str, Any],
        ],
    ) -> PrelivePrimaryDiagnosisModelComparison:
        replay_path = (
            benchmark_directory
            / PRIMARY_DIAGNOSIS_REPLAY_FILENAME
        )

        replay = self._read_json(
            replay_path
        )

        model_label = self._required_string(
            replay,
            "model_label",
        )

        structural = (
            structural_models.get(
                model_label
            )
        )

        if structural is None:
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    "Primary-diagnosis replay model "
                    "does not exist in structural "
                    f"comparison: {model_label}"
                )
            )

        scenario_id = self._required_string(
            replay,
            "scenario_id",
        )

        scenario_sha256 = self._required_string(
            replay,
            "scenario_sha256",
        )

        hierarchy_key = self._required_string(
            replay,
            "hierarchy_key",
        )

        benchmark_hash = self._required_string(
            structural,
            "benchmark_hash",
        )

        source_benchmark_hash = (
            self._required_string(
                replay,
                "source_benchmark_hash",
            )
        )

        benchmark_binding_valid = (
            source_benchmark_hash
            == benchmark_hash
        )

        if not benchmark_binding_valid:
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    "Primary-diagnosis replay benchmark "
                    f"binding mismatch for {model_label}."
                )
            )

        expected_hierarchy = (
            self._required_string(
                structural,
                "hierarchy_key",
            )
        )

        hierarchy_binding_valid = (
            hierarchy_key
            == expected_hierarchy
        )

        if not hierarchy_binding_valid:
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    "Primary-diagnosis replay hierarchy "
                    f"binding mismatch for {model_label}."
                )
            )

        expected_scenario_id = (
            self._required_string(
                structural,
                "scenario_id",
            )
        )

        expected_scenario_sha256 = (
            self._required_string(
                structural,
                "scenario_sha256",
            )
        )

        scenario_binding_valid = (
            scenario_id
            == expected_scenario_id
            and
            scenario_sha256
            == expected_scenario_sha256
        )

        if not scenario_binding_valid:
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    "Primary-diagnosis replay scenario "
                    f"binding mismatch for {model_label}."
                )
            )

        expected_conditions = (
            self._required_string_tuple(
                structural,
                "expected_conditions",
            )
        )

        ranked_conditions = (
            self._required_string_tuple(
                replay,
                "ranked_conditions",
            )
        )

        if len(
            set(
                ranked_conditions
            )
        ) != len(
            ranked_conditions
        ):
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    "Primary-diagnosis ranking contains "
                    f"duplicate conditions for {model_label}."
                )
            )

        ranking = self._ranking_records(
            replay,
            model_label=model_label,
        )

        ranking_categories = tuple(
            item[
                "category"
            ]
            for item
            in ranking
        )

        if (
            ranking_categories
            != ranked_conditions
        ):
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    "Ranking records do not match "
                    "ranked_conditions for "
                    f"{model_label}."
                )
            )

        expected_results = (
            self._score_expected_conditions(
                expected_conditions=(
                    expected_conditions
                ),
                ranking=ranking,
            )
        )

        rank_1_score = (
            self._score_at_rank(
                ranking,
                1,
            )
        )

        rank_2_score = (
            self._score_at_rank(
                ranking,
                2,
            )
        )

        if (
            rank_1_score is None
            or rank_2_score is None
        ):
            rank_margin = None
        else:
            rank_margin = round_metric(
                rank_1_score
                - rank_2_score
            )

        if expected_results:
            mean_expected_reciprocal_rank = (
                round_metric(
                    sum(
                        result.reciprocal_rank
                        for result
                        in expected_results
                    )
                    / len(
                        expected_results
                    )
                )
            )
        else:
            mean_expected_reciprocal_rank = (
                0.0
            )

        return (
            PrelivePrimaryDiagnosisModelComparison(
                model_label=model_label,

                scenario_id=scenario_id,

                scenario_sha256=(
                    scenario_sha256
                ),

                hierarchy_key=(
                    hierarchy_key
                ),

                benchmark_hash=(
                    benchmark_hash
                ),

                structural_replay_hash=(
                    self._required_string(
                        structural,
                        "structural_replay_hash",
                    )
                ),

                primary_diagnosis_replay_hash=(
                    self._required_string(
                        replay,
                        "replay_hash",
                    )
                ),

                benchmark_binding_valid=(
                    benchmark_binding_valid
                ),

                hierarchy_binding_valid=(
                    hierarchy_binding_valid
                ),

                scenario_binding_valid=(
                    scenario_binding_valid
                ),

                expected_conditions=(
                    expected_conditions
                ),

                ranked_conditions=(
                    ranked_conditions
                ),

                highest_ranked_condition=(
                    self._optional_string(
                        replay,
                        "highest_ranked_condition",
                    )
                ),

                expected_results=(
                    expected_results
                ),

                rank_1_score=(
                    rank_1_score
                ),

                rank_2_score=(
                    rank_2_score
                ),

                rank_1_to_rank_2_margin=(
                    rank_margin
                ),

                mean_expected_reciprocal_rank=(
                    mean_expected_reciprocal_rank
                ),
            )
        )

    def _score_expected_conditions(
        self,
        *,
        expected_conditions: tuple[
            str,
            ...,
        ],
        ranking: tuple[
            Mapping[str, Any],
            ...,
        ],
    ) -> tuple[
        PrelivePrimaryDiagnosisExpectedConditionResult,
        ...,
    ]:
        by_category = {
            self._required_string(
                item,
                "category",
            ):
                item
            for item
            in ranking
        }

        highest_score = (
            self._score_at_rank(
                ranking,
                1,
            )
        )

        results: list[
            PrelivePrimaryDiagnosisExpectedConditionResult
        ] = []

        for category in expected_conditions:
            item = by_category.get(
                category
            )

            if item is None:
                results.append(
                    PrelivePrimaryDiagnosisExpectedConditionResult(
                        category=category,
                        rank=None,
                        reciprocal_rank=0.0,
                        explanatory_score=None,
                        score_deficit_from_highest=None,
                        structural_level=None,
                    )
                )

                continue

            rank = self._required_int(
                item,
                "rank",
            )

            explanatory_score = (
                self._required_float(
                    item,
                    "explanatory_score",
                )
            )

            reciprocal_rank = round_metric(
                1.0
                / rank
            )

            if highest_score is None:
                score_deficit = None
            else:
                score_deficit = round_metric(
                    highest_score
                    - explanatory_score
                )

            results.append(
                PrelivePrimaryDiagnosisExpectedConditionResult(
                    category=category,

                    rank=rank,

                    reciprocal_rank=(
                        reciprocal_rank
                    ),

                    explanatory_score=(
                        explanatory_score
                    ),

                    score_deficit_from_highest=(
                        score_deficit
                    ),

                    structural_level=(
                        self._optional_string(
                            item,
                            "structural_level",
                        )
                    ),
                )
            )

        return tuple(
            results
        )

    def _ranking_records(
        self,
        replay: Mapping[str, Any],
        *,
        model_label: str,
    ) -> tuple[
        Mapping[str, Any],
        ...,
    ]:
        value = replay.get(
            "ranking"
        )

        if (
            not isinstance(
                value,
                list,
            )
        ):
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    "ranking must be a list for "
                    f"{model_label}."
                )
            )

        records: list[
            Mapping[str, Any]
        ] = []

        for expected_rank, item in enumerate(
            value,
            start=1,
        ):
            if not isinstance(
                item,
                Mapping,
            ):
                raise (
                    PrelivePrimaryDiagnosisComparisonError(
                        "ranking entries must be objects "
                        f"for {model_label}."
                    )
                )

            actual_rank = self._required_int(
                item,
                "rank",
            )

            if actual_rank != expected_rank:
                raise (
                    PrelivePrimaryDiagnosisComparisonError(
                        "ranking positions must be "
                        "contiguous and ordered for "
                        f"{model_label}."
                    )
                )

            records.append(
                item
            )

        return tuple(
            records
        )

    def _score_at_rank(
        self,
        ranking: tuple[
            Mapping[str, Any],
            ...,
        ],
        rank: int,
    ) -> float | None:
        for item in ranking:
            if (
                self._required_int(
                    item,
                    "rank",
                )
                == rank
            ):
                return (
                    self._required_float(
                        item,
                        "explanatory_score",
                    )
                )

        return None

    def _structural_model_map(
        self,
        payload: Mapping[str, Any],
    ) -> dict[
        str,
        Mapping[str, Any],
    ]:
        models = payload.get(
            "models"
        )

        if not isinstance(
            models,
            list,
        ):
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    "Structural comparison must "
                    "contain a models list."
                )
            )

        result: dict[
            str,
            Mapping[str, Any],
        ] = {}

        for item in models:
            if not isinstance(
                item,
                Mapping,
            ):
                raise (
                    PrelivePrimaryDiagnosisComparisonError(
                        "Structural comparison model "
                        "entries must be objects."
                    )
                )

            model_label = (
                self._required_string(
                    item,
                    "model_label",
                )
            )

            if model_label in result:
                raise (
                    PrelivePrimaryDiagnosisComparisonError(
                        "Structural comparison contains "
                        "duplicate model label: "
                        f"{model_label}"
                    )
                )

            result[
                model_label
            ] = item

        return result

    def _comparison_payload(
        self,
        models: tuple[
            PrelivePrimaryDiagnosisModelComparison,
            ...,
        ],
    ) -> dict[str, Any]:
        total_expected = sum(
            model.expected_condition_count
            for model
            in models
        )

        rank_1_count = sum(
            model.expected_at_rank_1_count
            for model
            in models
        )

        top_2_count = sum(
            model.expected_within_top_2_count
            for model
            in models
        )

        top_3_count = sum(
            model.expected_within_top_3_count
            for model
            in models
        )

        reciprocal_values = [
            result.reciprocal_rank
            for model
            in models
            for result
            in model.expected_results
        ]

        if reciprocal_values:
            mean_reciprocal = (
                round_metric(
                    sum(
                        reciprocal_values
                    )
                    / len(
                        reciprocal_values
                    )
                )
            )
        else:
            mean_reciprocal = 0.0

        model_mrr_values = [
            model.mean_expected_reciprocal_rank
            for model
            in models
        ]

        if model_mrr_values:
            mean_model_mrr = (
                round_metric(
                    sum(
                        model_mrr_values
                    )
                    / len(
                        model_mrr_values
                    )
                )
            )
        else:
            mean_model_mrr = 0.0

        return {
            "status":
                PRELIVE_PRIMARY_DIAGNOSIS_COMPARISON_STATUS,

            "authority":
                PRELIVE_PRIMARY_DIAGNOSIS_COMPARISON_AUTHORITY,

            "version":
                PRELIVE_PRIMARY_DIAGNOSIS_COMPARISON_VERSION,

            "model_count":
                len(
                    models
                ),

            "total_expected_conditions":
                total_expected,

            "expected_at_rank_1_count":
                rank_1_count,

            "expected_within_top_2_count":
                top_2_count,

            "expected_within_top_3_count":
                top_3_count,

            "expected_rank_1_rate":
                self._rate(
                    rank_1_count,
                    total_expected,
                ),

            "expected_top_2_rate":
                self._rate(
                    top_2_count,
                    total_expected,
                ),

            "expected_top_3_rate":
                self._rate(
                    top_3_count,
                    total_expected,
                ),

            "mean_expected_reciprocal_rank":
                mean_reciprocal,

            "mean_model_expected_reciprocal_rank":
                mean_model_mrr,

            "models_with_expected_at_rank_1": [
                model.model_label
                for model
                in models
                if model.has_expected_at_rank_1
            ],

            "models_with_all_expected_top_2": [
                model.model_label
                for model
                in models
                if model.all_expected_within_top_2
            ],

            "models_with_all_expected_top_3": [
                model.model_label
                for model
                in models
                if model.all_expected_within_top_3
            ],

            "models": [
                model.to_dict()
                for model
                in models
            ],
        }

    def _rate(
        self,
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator <= 0:
            return 0.0

        return round_metric(
            numerator
            / denominator
        )

    def write_receipt(
        self,
        *,
        output_directory: str | Path,
        result: PrelivePrimaryDiagnosisComparisonResult,
    ) -> Path:
        directory = Path(
            output_directory
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            directory
            / PRIMARY_DIAGNOSIS_COMPARISON_FILENAME
        )

        payload = (
            result.to_dict()
        )

        if output_path.exists():
            existing = self._read_json(
                output_path
            )

            if canonical_json(
                existing
            ) != canonical_json(
                payload
            ):
                raise (
                    PrelivePrimaryDiagnosisComparisonError(
                        "Existing primary-diagnosis "
                        "ranking comparison receipt "
                        "does not match deterministic "
                        "comparison."
                    )
                )

            return output_path

        output_path.write_text(
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        return output_path

    def _read_json(
        self,
        path: Path,
    ) -> Mapping[str, Any]:
        if not path.is_file():
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    f"Required comparison input "
                    f"does not exist: {path}"
                )
            )

        try:
            value = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    f"Unable to read comparison "
                    f"input: {path}"
                )
            ) from exc

        if not isinstance(
            value,
            Mapping,
        ):
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    "Comparison input must be a "
                    f"JSON object: {path}"
                )
            )

        return value

    def _required_string(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> str:
        value = payload.get(
            field_name
        )

        if (
            not isinstance(
                value,
                str,
            )
            or not value.strip()
        ):
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    f"{field_name} must be a "
                    "non-empty string."
                )
            )

        return value.strip()

    def _optional_string(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> str | None:
        value = payload.get(
            field_name
        )

        if value is None:
            return None

        if (
            not isinstance(
                value,
                str,
            )
            or not value.strip()
        ):
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    f"{field_name} must be null "
                    "or a non-empty string."
                )
            )

        return value.strip()

    def _required_string_tuple(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> tuple[str, ...]:
        value = payload.get(
            field_name
        )

        if not isinstance(
            value,
            list,
        ):
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    f"{field_name} must be a list."
                )
            )

        result: list[str] = []

        for item in value:
            if (
                not isinstance(
                    item,
                    str,
                )
                or not item.strip()
            ):
                raise (
                    PrelivePrimaryDiagnosisComparisonError(
                        f"{field_name} must contain "
                        "only non-empty strings."
                    )
                )

            result.append(
                item.strip()
            )

        return tuple(
            result
        )

    def _required_int(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> int:
        value = payload.get(
            field_name
        )

        if (
            not isinstance(
                value,
                int,
            )
            or isinstance(
                value,
                bool,
            )
            or value <= 0
        ):
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    f"{field_name} must be a "
                    "positive integer."
                )
            )

        return value

    def _required_float(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> float:
        value = payload.get(
            field_name
        )

        if (
            isinstance(
                value,
                bool,
            )
            or not isinstance(
                value,
                (
                    int,
                    float,
                ),
            )
        ):
            raise (
                PrelivePrimaryDiagnosisComparisonError(
                    f"{field_name} must be numeric."
                )
            )

        return float(
            value
        )