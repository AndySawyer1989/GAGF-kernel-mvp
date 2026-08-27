from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence

from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)


PRELIVE_DIAGNOSTIC_SEPARATION_OBSERVATION_VERSION = (
    "1.0.0"
)

PRELIVE_DIAGNOSTIC_SEPARATION_OBSERVATION_STATUS = (
    "diagnostic_separation_observation_complete"
)

PRELIVE_DIAGNOSTIC_SEPARATION_OBSERVATION_AUTHORITY = (
    "GAGF_FIP_ONLY"
)

DIAGNOSTIC_SEPARATION_REPLAY_FILENAME = (
    "diagnostic_separation_replay.json"
)

DIAGNOSTIC_SEPARATION_OBSERVATION_FILENAME = (
    "diagnostic_separation_observation.json"
)


class PreliveDiagnosticSeparationObservationError(
    RuntimeError
):
    """
    Raised when frozen diagnostic-separation replay
    receipts cannot be aggregated safely.
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
class PreliveDiagnosticSeparationModelObservation:
    model_label: str
    scenario_id: str
    scenario_sha256: str
    hierarchy_key: str

    benchmark_hash: str
    primary_diagnosis_replay_hash: str
    separation_replay_hash: str
    separation_summary_hash: str

    leading_candidate: str | None
    runner_up_candidate: str | None

    rank_1_score: float | None
    rank_2_score: float | None

    rank_1_to_rank_2_absolute: float | None
    rank_1_to_rank_2_relative: float | None

    rank_1_to_rank_3_absolute: float | None
    rank_1_to_rank_3_relative: float | None

    top_3_score_spread: float | None

    candidate_count: int
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

    repository_chain_valid: bool
    primary_projection_verified: bool
    structural_projection_verified: bool
    structural_classification_verified: bool

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

            "primary_diagnosis_replay_hash":
                self.primary_diagnosis_replay_hash,

            "separation_replay_hash":
                self.separation_replay_hash,

            "separation_summary_hash":
                self.separation_summary_hash,

            "leading_candidate":
                self.leading_candidate,

            "runner_up_candidate":
                self.runner_up_candidate,

            "rank_1_score":
                self.rank_1_score,

            "rank_2_score":
                self.rank_2_score,

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

            "candidate_count":
                self.candidate_count,

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

            "repository_chain_valid":
                self.repository_chain_valid,

            "primary_projection_verified":
                self.primary_projection_verified,

            "structural_projection_verified":
                self.structural_projection_verified,

            "structural_classification_verified":
                self.structural_classification_verified,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class PreliveDiagnosticSeparationAggregateObservation:
    observed_model_count: int

    absolute_separation_count: int
    relative_separation_count: int

    mean_rank_1_to_rank_2_absolute: float | None
    median_rank_1_to_rank_2_absolute: float | None
    min_rank_1_to_rank_2_absolute: float | None
    max_rank_1_to_rank_2_absolute: float | None

    mean_rank_1_to_rank_2_relative: float | None
    median_rank_1_to_rank_2_relative: float | None
    min_rank_1_to_rank_2_relative: float | None
    max_rank_1_to_rank_2_relative: float | None

    mean_rank_1_to_rank_3_absolute: float | None
    mean_rank_1_to_rank_3_relative: float | None

    mean_top_3_score_spread: float | None

    mean_leading_evidence_quality: float | None
    mean_runner_up_evidence_quality: float | None

    mean_candidate_count: float | None

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "observed_model_count":
                self.observed_model_count,

            "absolute_separation_count":
                self.absolute_separation_count,

            "relative_separation_count":
                self.relative_separation_count,

            "mean_rank_1_to_rank_2_absolute":
                self.mean_rank_1_to_rank_2_absolute,

            "median_rank_1_to_rank_2_absolute":
                self.median_rank_1_to_rank_2_absolute,

            "min_rank_1_to_rank_2_absolute":
                self.min_rank_1_to_rank_2_absolute,

            "max_rank_1_to_rank_2_absolute":
                self.max_rank_1_to_rank_2_absolute,

            "mean_rank_1_to_rank_2_relative":
                self.mean_rank_1_to_rank_2_relative,

            "median_rank_1_to_rank_2_relative":
                self.median_rank_1_to_rank_2_relative,

            "min_rank_1_to_rank_2_relative":
                self.min_rank_1_to_rank_2_relative,

            "max_rank_1_to_rank_2_relative":
                self.max_rank_1_to_rank_2_relative,

            "mean_rank_1_to_rank_3_absolute":
                self.mean_rank_1_to_rank_3_absolute,

            "mean_rank_1_to_rank_3_relative":
                self.mean_rank_1_to_rank_3_relative,

            "mean_top_3_score_spread":
                self.mean_top_3_score_spread,

            "mean_leading_evidence_quality":
                self.mean_leading_evidence_quality,

            "mean_runner_up_evidence_quality":
                self.mean_runner_up_evidence_quality,

            "mean_candidate_count":
                self.mean_candidate_count,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class PreliveDiagnosticSeparationObservationResult:
    models: tuple[
        PreliveDiagnosticSeparationModelObservation,
        ...,
    ]

    aggregate: (
        PreliveDiagnosticSeparationAggregateObservation
    )

    observation_hash: str

    status: str = (
        PRELIVE_DIAGNOSTIC_SEPARATION_OBSERVATION_STATUS
    )

    authority: str = (
        PRELIVE_DIAGNOSTIC_SEPARATION_OBSERVATION_AUTHORITY
    )

    version: str = (
        PRELIVE_DIAGNOSTIC_SEPARATION_OBSERVATION_VERSION
    )

    @property
    def model_count(
        self,
    ) -> int:
        return len(
            self.models
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

            "aggregate":
                self.aggregate.to_dict(),

            "models": [
                model.to_dict()
                for model
                in self.models
            ],

            "observation_hash":
                self.observation_hash,
        }


class PreliveMultimodelDiagnosticSeparationObservationService:
    """
    Aggregate already-frozen diagnostic-separation replay
    receipts into one observational cross-model receipt.

    This service does not:

    - rerun diagnostic projections;
    - read expected conditions;
    - inspect an oracle;
    - evaluate correctness;
    - define thresholds;
    - classify confidence;
    - establish causation;
    - declare root cause;
    - authorize intervention.

    Observed separation distribution is not calibrated
    diagnostic confidence.
    """

    def observe(
        self,
        *,
        benchmark_directories: Sequence[
            str | Path
        ],
        output_directory: str | Path,
    ) -> PreliveDiagnosticSeparationObservationResult:
        model_results = tuple(
            sorted(
                (
                    self._observe_model(
                        Path(
                            directory
                        )
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
                PreliveDiagnosticSeparationObservationError(
                    "At least one benchmark directory "
                    "is required."
                )
            )

        self._validate_unique_models(
            model_results
        )

        aggregate = (
            self._aggregate(
                model_results
            )
        )

        observation_payload = {
            "status":
                PRELIVE_DIAGNOSTIC_SEPARATION_OBSERVATION_STATUS,

            "authority":
                PRELIVE_DIAGNOSTIC_SEPARATION_OBSERVATION_AUTHORITY,

            "version":
                PRELIVE_DIAGNOSTIC_SEPARATION_OBSERVATION_VERSION,

            "model_count":
                len(
                    model_results
                ),

            "aggregate":
                aggregate.to_dict(),

            "models": [
                model.to_dict()
                for model
                in model_results
            ],
        }

        observation_hash = sha256_text(
            canonical_json(
                observation_payload
            )
        )

        result = (
            PreliveDiagnosticSeparationObservationResult(
                models=(
                    model_results
                ),

                aggregate=(
                    aggregate
                ),

                observation_hash=(
                    observation_hash
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

    def _observe_model(
        self,
        directory: Path,
    ) -> PreliveDiagnosticSeparationModelObservation:
        replay = (
            self._read_json(
                directory
                / DIAGNOSTIC_SEPARATION_REPLAY_FILENAME
            )
        )

        projection = self._required_mapping(
            replay,
            "projection",
        )

        support = self._required_mapping(
            replay,
            "support",
        )

        model_label = self._required_string(
            replay,
            "model_label",
        )

        if (
            self._required_string(
                replay,
                "status",
            )
            != "diagnostic_separation_replay_complete"
        ):
            raise (
                PreliveDiagnosticSeparationObservationError(
                    "Unexpected diagnostic-separation "
                    f"replay status for {model_label}."
                )
            )

        if (
            self._required_string(
                replay,
                "authority",
            )
            != "GAGF_FIP_ONLY"
        ):
            raise (
                PreliveDiagnosticSeparationObservationError(
                    "Unexpected diagnostic-separation "
                    f"authority for {model_label}."
                )
            )

        repository_chain_valid = (
            self._required_bool(
                projection,
                "repository_chain_valid",
            )
        )

        primary_projection_verified = (
            self._required_bool(
                projection,
                "primary_projection_verified",
            )
        )

        structural_projection_verified = (
            self._required_bool(
                projection,
                "structural_projection_verified",
            )
        )

        structural_classification_verified = (
            self._required_bool(
                projection,
                "structural_classification_verified",
            )
        )

        if not all(
            (
                repository_chain_valid,
                primary_projection_verified,
                structural_projection_verified,
                structural_classification_verified,
            )
        ):
            raise (
                PreliveDiagnosticSeparationObservationError(
                    "Diagnostic-separation replay integrity "
                    f"is not fully verified for {model_label}."
                )
            )

        replay_hierarchy = (
            self._required_string(
                replay,
                "hierarchy_key",
            )
        )

        projection_hierarchy = (
            self._required_string(
                projection,
                "hierarchy_key",
            )
        )

        if (
            replay_hierarchy
            != projection_hierarchy
        ):
            raise (
                PreliveDiagnosticSeparationObservationError(
                    "Diagnostic-separation projection "
                    f"hierarchy mismatch for {model_label}."
                )
            )

        replay_summary_hash = (
            self._required_string(
                replay,
                "separation_summary_hash",
            )
        )

        projection_summary_hash = (
            self._required_string(
                projection,
                "separation_summary_hash",
            )
        )

        if (
            replay_summary_hash
            != projection_summary_hash
        ):
            raise (
                PreliveDiagnosticSeparationObservationError(
                    "Diagnostic-separation summary hash "
                    f"binding mismatch for {model_label}."
                )
            )

        replay_primary_hash = (
            self._required_string(
                replay,
                "primary_diagnosis_summary_hash",
            )
        )

        projection_primary_hash = (
            self._required_string(
                projection,
                "primary_diagnosis_summary_hash",
            )
        )

        if (
            replay_primary_hash
            != projection_primary_hash
        ):
            raise (
                PreliveDiagnosticSeparationObservationError(
                    "Primary-diagnosis summary hash "
                    f"binding mismatch for {model_label}."
                )
            )

        return (
            PreliveDiagnosticSeparationModelObservation(
                model_label=(
                    model_label
                ),

                scenario_id=(
                    self._required_string(
                        replay,
                        "scenario_id",
                    )
                ),

                scenario_sha256=(
                    self._required_string(
                        replay,
                        "scenario_sha256",
                    )
                ),

                hierarchy_key=(
                    replay_hierarchy
                ),

                benchmark_hash=(
                    self._required_string(
                        replay,
                        "source_benchmark_hash",
                    )
                ),

                primary_diagnosis_replay_hash=(
                    self._required_string(
                        replay,
                        "primary_diagnosis_replay_hash",
                    )
                ),

                separation_replay_hash=(
                    self._required_string(
                        replay,
                        "replay_hash",
                    )
                ),

                separation_summary_hash=(
                    replay_summary_hash
                ),

                leading_candidate=(
                    self._optional_string(
                        replay,
                        "leading_candidate",
                    )
                ),

                runner_up_candidate=(
                    self._optional_string(
                        replay,
                        "runner_up_candidate",
                    )
                ),

                rank_1_score=(
                    self._optional_float(
                        replay,
                        "rank_1_score",
                    )
                ),

                rank_2_score=(
                    self._optional_float(
                        replay,
                        "rank_2_score",
                    )
                ),

                rank_1_to_rank_2_absolute=(
                    self._optional_float(
                        replay,
                        "rank_1_to_rank_2_absolute",
                    )
                ),

                rank_1_to_rank_2_relative=(
                    self._optional_float(
                        replay,
                        "rank_1_to_rank_2_relative",
                    )
                ),

                rank_1_to_rank_3_absolute=(
                    self._optional_float(
                        replay,
                        "rank_1_to_rank_3_absolute",
                    )
                ),

                rank_1_to_rank_3_relative=(
                    self._optional_float(
                        replay,
                        "rank_1_to_rank_3_relative",
                    )
                ),

                top_3_score_spread=(
                    self._optional_float(
                        replay,
                        "top_3_score_spread",
                    )
                ),

                candidate_count=(
                    self._required_nonnegative_int(
                        support,
                        "candidate_count",
                    )
                ),

                evidence_quality_observed_count=(
                    self._required_nonnegative_int(
                        support,
                        "evidence_quality_observed_count",
                    )
                ),

                leading_evidence_quality=(
                    self._optional_float(
                        support,
                        "leading_evidence_quality",
                    )
                ),

                runner_up_evidence_quality=(
                    self._optional_float(
                        support,
                        "runner_up_evidence_quality",
                    )
                ),

                leading_structural_level=(
                    self._optional_string(
                        support,
                        "leading_structural_level",
                    )
                ),

                runner_up_structural_level=(
                    self._optional_string(
                        support,
                        "runner_up_structural_level",
                    )
                ),

                leading_event_count=(
                    self._optional_int(
                        support,
                        "leading_event_count",
                    )
                ),

                runner_up_event_count=(
                    self._optional_int(
                        support,
                        "runner_up_event_count",
                    )
                ),

                leading_unique_work_item_count=(
                    self._optional_int(
                        support,
                        "leading_unique_work_item_count",
                    )
                ),

                runner_up_unique_work_item_count=(
                    self._optional_int(
                        support,
                        "runner_up_unique_work_item_count",
                    )
                ),

                leading_active_day_count=(
                    self._optional_int(
                        support,
                        "leading_active_day_count",
                    )
                ),

                runner_up_active_day_count=(
                    self._optional_int(
                        support,
                        "runner_up_active_day_count",
                    )
                ),

                repository_chain_valid=(
                    repository_chain_valid
                ),

                primary_projection_verified=(
                    primary_projection_verified
                ),

                structural_projection_verified=(
                    structural_projection_verified
                ),

                structural_classification_verified=(
                    structural_classification_verified
                ),
            )
        )

    def _aggregate(
        self,
        models: tuple[
            PreliveDiagnosticSeparationModelObservation,
            ...,
        ],
    ) -> PreliveDiagnosticSeparationAggregateObservation:
        absolute = [
            value
            for value
            in (
                model.rank_1_to_rank_2_absolute
                for model
                in models
            )
            if value is not None
        ]

        relative = [
            value
            for value
            in (
                model.rank_1_to_rank_2_relative
                for model
                in models
            )
            if value is not None
        ]

        rank_1_to_3_absolute = [
            value
            for value
            in (
                model.rank_1_to_rank_3_absolute
                for model
                in models
            )
            if value is not None
        ]

        rank_1_to_3_relative = [
            value
            for value
            in (
                model.rank_1_to_rank_3_relative
                for model
                in models
            )
            if value is not None
        ]

        top_3 = [
            value
            for value
            in (
                model.top_3_score_spread
                for model
                in models
            )
            if value is not None
        ]

        leading_quality = [
            value
            for value
            in (
                model.leading_evidence_quality
                for model
                in models
            )
            if value is not None
        ]

        runner_quality = [
            value
            for value
            in (
                model.runner_up_evidence_quality
                for model
                in models
            )
            if value is not None
        ]

        candidate_counts = [
            float(
                model.candidate_count
            )
            for model
            in models
        ]

        return (
            PreliveDiagnosticSeparationAggregateObservation(
                observed_model_count=(
                    len(
                        models
                    )
                ),

                absolute_separation_count=(
                    len(
                        absolute
                    )
                ),

                relative_separation_count=(
                    len(
                        relative
                    )
                ),

                mean_rank_1_to_rank_2_absolute=(
                    self._mean(
                        absolute
                    )
                ),

                median_rank_1_to_rank_2_absolute=(
                    self._median(
                        absolute
                    )
                ),

                min_rank_1_to_rank_2_absolute=(
                    self._minimum(
                        absolute
                    )
                ),

                max_rank_1_to_rank_2_absolute=(
                    self._maximum(
                        absolute
                    )
                ),

                mean_rank_1_to_rank_2_relative=(
                    self._mean(
                        relative
                    )
                ),

                median_rank_1_to_rank_2_relative=(
                    self._median(
                        relative
                    )
                ),

                min_rank_1_to_rank_2_relative=(
                    self._minimum(
                        relative
                    )
                ),

                max_rank_1_to_rank_2_relative=(
                    self._maximum(
                        relative
                    )
                ),

                mean_rank_1_to_rank_3_absolute=(
                    self._mean(
                        rank_1_to_3_absolute
                    )
                ),

                mean_rank_1_to_rank_3_relative=(
                    self._mean(
                        rank_1_to_3_relative
                    )
                ),

                mean_top_3_score_spread=(
                    self._mean(
                        top_3
                    )
                ),

                mean_leading_evidence_quality=(
                    self._mean(
                        leading_quality
                    )
                ),

                mean_runner_up_evidence_quality=(
                    self._mean(
                        runner_quality
                    )
                ),

                mean_candidate_count=(
                    self._mean(
                        candidate_counts
                    )
                ),
            )
        )

    def _validate_unique_models(
        self,
        models: tuple[
            PreliveDiagnosticSeparationModelObservation,
            ...,
        ],
    ) -> None:
        labels = [
            model.model_label
            for model
            in models
        ]

        if (
            len(
                labels
            )
            != len(
                set(
                    labels
                )
            )
        ):
            raise (
                PreliveDiagnosticSeparationObservationError(
                    "Diagnostic-separation observations "
                    "contain duplicate model labels."
                )
            )

    def write_receipt(
        self,
        *,
        output_directory: str | Path,
        result: PreliveDiagnosticSeparationObservationResult,
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
            / DIAGNOSTIC_SEPARATION_OBSERVATION_FILENAME
        )

        payload = (
            result.to_dict()
        )

        if output_path.exists():
            existing = (
                self._read_json(
                    output_path
                )
            )

            if canonical_json(
                existing
            ) != canonical_json(
                payload
            ):
                raise (
                    PreliveDiagnosticSeparationObservationError(
                        "Existing diagnostic-separation "
                        "observation receipt does not match "
                        "deterministic aggregation."
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

    def _mean(
        self,
        values: Sequence[float],
    ) -> float | None:
        if not values:
            return None

        return round_metric(
            sum(
                values
            )
            / len(
                values
            )
        )

    def _median(
        self,
        values: Sequence[float],
    ) -> float | None:
        if not values:
            return None

        return round_metric(
            median(
                values
            )
        )

    def _minimum(
        self,
        values: Sequence[float],
    ) -> float | None:
        if not values:
            return None

        return round_metric(
            min(
                values
            )
        )

    def _maximum(
        self,
        values: Sequence[float],
    ) -> float | None:
        if not values:
            return None

        return round_metric(
            max(
                values
            )
        )

    def _read_json(
        self,
        path: Path,
    ) -> Mapping[str, Any]:
        if not path.is_file():
            raise (
                PreliveDiagnosticSeparationObservationError(
                    "Required diagnostic-separation "
                    f"observation input does not exist: {path}"
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
                PreliveDiagnosticSeparationObservationError(
                    "Unable to read diagnostic-separation "
                    f"observation input: {path}"
                )
            ) from exc

        if not isinstance(
            value,
            Mapping,
        ):
            raise (
                PreliveDiagnosticSeparationObservationError(
                    "Diagnostic-separation observation "
                    f"input must be a JSON object: {path}"
                )
            )

        return value

    def _required_mapping(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> Mapping[str, Any]:
        value = payload.get(
            field_name
        )

        if not isinstance(
            value,
            Mapping,
        ):
            raise (
                PreliveDiagnosticSeparationObservationError(
                    f"{field_name} must be an object."
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
                PreliveDiagnosticSeparationObservationError(
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
                PreliveDiagnosticSeparationObservationError(
                    f"{field_name} must be null "
                    "or a non-empty string."
                )
            )

        return value.strip()

    def _required_bool(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> bool:
        value = payload.get(
            field_name
        )

        if not isinstance(
            value,
            bool,
        ):
            raise (
                PreliveDiagnosticSeparationObservationError(
                    f"{field_name} must be boolean."
                )
            )

        return value

    def _optional_float(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> float | None:
        value = payload.get(
            field_name
        )

        if value is None:
            return None

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
                PreliveDiagnosticSeparationObservationError(
                    f"{field_name} must be null "
                    "or numeric."
                )
            )

        return float(
            value
        )

    def _required_nonnegative_int(
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
            or value < 0
        ):
            raise (
                PreliveDiagnosticSeparationObservationError(
                    f"{field_name} must be a "
                    "non-negative integer."
                )
            )

        return value

    def _optional_int(
        self,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> int | None:
        value = payload.get(
            field_name
        )

        if value is None:
            return None

        if (
            not isinstance(
                value,
                int,
            )
            or isinstance(
                value,
                bool,
            )
            or value < 0
        ):
            raise (
                PreliveDiagnosticSeparationObservationError(
                    f"{field_name} must be null or "
                    "a non-negative integer."
                )
            )

        return value