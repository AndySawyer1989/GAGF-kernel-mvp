from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence


PRELIVE_MULTIMODEL_COMPARISON_VERSION = "1.0.0"

PRELIVE_MULTIMODEL_COMPARISON_STATUS = (
    "multimodel_benchmark_comparison_complete"
)

PRELIVE_MULTIMODEL_COMPARISON_AUTHORITY = (
    "GAGF_FIP_ONLY"
)


class PreliveMultimodelComparisonError(
    ValueError
):
    pass


def canonical_sha256(
    value: Mapping[str, Any],
) -> str:
    encoded = json.dumps(
        dict(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


@dataclass(
    frozen=True,
    slots=True,
)
class PreliveModelBenchmarkComparison:
    model_label: str
    scenario_id: str
    scenario_sha256: str
    event_count: int

    raw_precision: float
    raw_recall: float
    raw_f1: float
    raw_exact_condition_match: bool
    raw_dominant_constraint_match: bool

    systemic_precision: float
    systemic_recall: float
    systemic_f1: float
    systemic_exact_condition_match: bool
    systemic_dominant_constraint_match: bool

    expected_conditions: tuple[str, ...]
    raw_detected_conditions: tuple[str, ...]
    systemic_conditions: tuple[str, ...]

    systemic_false_positives: tuple[str, ...]
    systemic_false_negatives: tuple[str, ...]

    dominant_expected: str | None
    dominant_raw: str | None
    dominant_systemic: str | None

    benchmark_hash: str
    scope_hash: str

    repository_chain_valid: bool
    oracle_leakage_detected: bool

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
            "event_count":
                self.event_count,

            "raw_precision":
                self.raw_precision,
            "raw_recall":
                self.raw_recall,
            "raw_f1":
                self.raw_f1,
            "raw_exact_condition_match":
                self.raw_exact_condition_match,
            "raw_dominant_constraint_match":
                self.raw_dominant_constraint_match,

            "systemic_precision":
                self.systemic_precision,
            "systemic_recall":
                self.systemic_recall,
            "systemic_f1":
                self.systemic_f1,
            "systemic_exact_condition_match":
                self.systemic_exact_condition_match,
            "systemic_dominant_constraint_match":
                self.systemic_dominant_constraint_match,

            "expected_conditions":
                list(
                    self.expected_conditions
                ),
            "raw_detected_conditions":
                list(
                    self.raw_detected_conditions
                ),
            "systemic_conditions":
                list(
                    self.systemic_conditions
                ),

            "systemic_false_positives":
                list(
                    self.systemic_false_positives
                ),
            "systemic_false_negatives":
                list(
                    self.systemic_false_negatives
                ),

            "dominant_expected":
                self.dominant_expected,
            "dominant_raw":
                self.dominant_raw,
            "dominant_systemic":
                self.dominant_systemic,

            "benchmark_hash":
                self.benchmark_hash,
            "scope_hash":
                self.scope_hash,

            "repository_chain_valid":
                self.repository_chain_valid,
            "oracle_leakage_detected":
                self.oracle_leakage_detected,
        }


@dataclass(
    frozen=True,
    slots=True,
)
class PreliveMultimodelBenchmarkComparisonResult:
    models: tuple[
        PreliveModelBenchmarkComparison,
        ...
    ]

    model_count: int
    total_scenarios: int
    total_events: int

    mean_raw_precision: float
    mean_raw_recall: float
    mean_raw_f1: float

    mean_systemic_precision: float
    mean_systemic_recall: float
    mean_systemic_f1: float

    raw_primary_recall_rate: float
    systemic_primary_recall_rate: float

    raw_exact_match_rate: float
    systemic_exact_match_rate: float

    raw_dominant_match_rate: float
    systemic_dominant_match_rate: float

    models_with_raw_exact_match: tuple[str, ...]
    models_with_systemic_exact_match: tuple[str, ...]

    models_with_raw_dominant_match: tuple[str, ...]
    models_with_systemic_dominant_match: tuple[str, ...]

    models_with_systemic_false_negatives: tuple[str, ...]
    models_with_systemic_false_positives: tuple[str, ...]

    comparison_hash: str

    status: str = (
        PRELIVE_MULTIMODEL_COMPARISON_STATUS
    )

    authority: str = (
        PRELIVE_MULTIMODEL_COMPARISON_AUTHORITY
    )

    version: str = (
        PRELIVE_MULTIMODEL_COMPARISON_VERSION
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
            "total_scenarios":
                self.total_scenarios,
            "total_events":
                self.total_events,

            "mean_raw_precision":
                self.mean_raw_precision,
            "mean_raw_recall":
                self.mean_raw_recall,
            "mean_raw_f1":
                self.mean_raw_f1,

            "mean_systemic_precision":
                self.mean_systemic_precision,
            "mean_systemic_recall":
                self.mean_systemic_recall,
            "mean_systemic_f1":
                self.mean_systemic_f1,

            "raw_primary_recall_rate":
                self.raw_primary_recall_rate,
            "systemic_primary_recall_rate":
                self.systemic_primary_recall_rate,

            "raw_exact_match_rate":
                self.raw_exact_match_rate,
            "systemic_exact_match_rate":
                self.systemic_exact_match_rate,

            "raw_dominant_match_rate":
                self.raw_dominant_match_rate,
            "systemic_dominant_match_rate":
                self.systemic_dominant_match_rate,

            "models_with_raw_exact_match":
                list(
                    self.models_with_raw_exact_match
                ),

            "models_with_systemic_exact_match":
                list(
                    self.models_with_systemic_exact_match
                ),

            "models_with_raw_dominant_match":
                list(
                    self.models_with_raw_dominant_match
                ),

            "models_with_systemic_dominant_match":
                list(
                    self.models_with_systemic_dominant_match
                ),

            "models_with_systemic_false_negatives":
                list(
                    self.models_with_systemic_false_negatives
                ),

            "models_with_systemic_false_positives":
                list(
                    self.models_with_systemic_false_positives
                ),

            "comparison_hash":
                self.comparison_hash,

            "models": [
                model.to_dict()
                for model
                in self.models
            ],
        }


class PreliveMultimodelBenchmarkComparisonService:
    def compare(
        self,
        *,
        benchmark_directories:
            Sequence[
                str | Path
            ],
    ) -> (
        PreliveMultimodelBenchmarkComparisonResult
    ):
        if not benchmark_directories:
            raise (
                PreliveMultimodelComparisonError(
                    "At least one benchmark "
                    "directory is required."
                )
            )

        models = tuple(
            self._load_model(
                Path(directory)
            )
            for directory
            in benchmark_directories
        )

        labels = [
            model.model_label
            for model
            in models
        ]

        if (
            len(labels)
            != len(set(labels))
        ):
            raise (
                PreliveMultimodelComparisonError(
                    "Benchmark model labels "
                    "must be unique."
                )
            )

        scenario_ids = [
            model.scenario_id
            for model
            in models
        ]

        if (
            len(scenario_ids)
            != len(set(scenario_ids))
        ):
            raise (
                PreliveMultimodelComparisonError(
                    "Benchmark scenario IDs "
                    "must be unique."
                )
            )

        ordered = tuple(
            sorted(
                models,
                key=lambda item:
                    item.model_label
                    .strip()
                    .lower(),
            )
        )

        model_count = len(
            ordered
        )

        total_events = sum(
            model.event_count
            for model
            in ordered
        )

        raw_expected_total = sum(
            len(
                model.expected_conditions
            )
            for model
            in ordered
        )

        raw_true_positive_total = sum(
            self._true_positive_count(
                expected=(
                    model.expected_conditions
                ),
                detected=(
                    model.raw_detected_conditions
                ),
            )
            for model
            in ordered
        )

        systemic_expected_total = sum(
            len(
                model.expected_conditions
            )
            for model
            in ordered
        )

        systemic_true_positive_total = sum(
            self._true_positive_count(
                expected=(
                    model.expected_conditions
                ),
                detected=(
                    model.systemic_conditions
                ),
            )
            for model
            in ordered
        )

        payload_without_hash = {
            "model_count":
                model_count,
            "total_scenarios":
                model_count,
            "total_events":
                total_events,

            "mean_raw_precision":
                self._mean(
                    model.raw_precision
                    for model
                    in ordered
                ),
            "mean_raw_recall":
                self._mean(
                    model.raw_recall
                    for model
                    in ordered
                ),
            "mean_raw_f1":
                self._mean(
                    model.raw_f1
                    for model
                    in ordered
                ),

            "mean_systemic_precision":
                self._mean(
                    model.systemic_precision
                    for model
                    in ordered
                ),
            "mean_systemic_recall":
                self._mean(
                    model.systemic_recall
                    for model
                    in ordered
                ),
            "mean_systemic_f1":
                self._mean(
                    model.systemic_f1
                    for model
                    in ordered
                ),

            "raw_primary_recall_rate":
                self._ratio(
                    raw_true_positive_total,
                    raw_expected_total,
                ),

            "systemic_primary_recall_rate":
                self._ratio(
                    systemic_true_positive_total,
                    systemic_expected_total,
                ),

            "raw_exact_match_rate":
                self._mean(
                    1.0
                    if model.raw_exact_condition_match
                    else 0.0
                    for model
                    in ordered
                ),

            "systemic_exact_match_rate":
                self._mean(
                    1.0
                    if model.systemic_exact_condition_match
                    else 0.0
                    for model
                    in ordered
                ),

            "raw_dominant_match_rate":
                self._mean(
                    1.0
                    if model.raw_dominant_constraint_match
                    else 0.0
                    for model
                    in ordered
                ),

            "systemic_dominant_match_rate":
                self._mean(
                    1.0
                    if model.systemic_dominant_constraint_match
                    else 0.0
                    for model
                    in ordered
                ),

            "models_with_raw_exact_match":
                [
                    model.model_label
                    for model
                    in ordered
                    if model.raw_exact_condition_match
                ],

            "models_with_systemic_exact_match":
                [
                    model.model_label
                    for model
                    in ordered
                    if model.systemic_exact_condition_match
                ],

            "models_with_raw_dominant_match":
                [
                    model.model_label
                    for model
                    in ordered
                    if model.raw_dominant_constraint_match
                ],

            "models_with_systemic_dominant_match":
                [
                    model.model_label
                    for model
                    in ordered
                    if model.systemic_dominant_constraint_match
                ],

            "models_with_systemic_false_negatives":
                [
                    model.model_label
                    for model
                    in ordered
                    if model.systemic_false_negatives
                ],

            "models_with_systemic_false_positives":
                [
                    model.model_label
                    for model
                    in ordered
                    if model.systemic_false_positives
                ],

            "models": [
                model.to_dict()
                for model
                in ordered
            ],
        }

        comparison_hash = (
            canonical_sha256(
                payload_without_hash
            )
        )

        return (
            PreliveMultimodelBenchmarkComparisonResult(
                models=ordered,

                model_count=model_count,
                total_scenarios=model_count,
                total_events=total_events,

                mean_raw_precision=(
                    payload_without_hash[
                        "mean_raw_precision"
                    ]
                ),
                mean_raw_recall=(
                    payload_without_hash[
                        "mean_raw_recall"
                    ]
                ),
                mean_raw_f1=(
                    payload_without_hash[
                        "mean_raw_f1"
                    ]
                ),

                mean_systemic_precision=(
                    payload_without_hash[
                        "mean_systemic_precision"
                    ]
                ),
                mean_systemic_recall=(
                    payload_without_hash[
                        "mean_systemic_recall"
                    ]
                ),
                mean_systemic_f1=(
                    payload_without_hash[
                        "mean_systemic_f1"
                    ]
                ),

                raw_primary_recall_rate=(
                    payload_without_hash[
                        "raw_primary_recall_rate"
                    ]
                ),
                systemic_primary_recall_rate=(
                    payload_without_hash[
                        "systemic_primary_recall_rate"
                    ]
                ),

                raw_exact_match_rate=(
                    payload_without_hash[
                        "raw_exact_match_rate"
                    ]
                ),
                systemic_exact_match_rate=(
                    payload_without_hash[
                        "systemic_exact_match_rate"
                    ]
                ),

                raw_dominant_match_rate=(
                    payload_without_hash[
                        "raw_dominant_match_rate"
                    ]
                ),
                systemic_dominant_match_rate=(
                    payload_without_hash[
                        "systemic_dominant_match_rate"
                    ]
                ),

                models_with_raw_exact_match=(
                    tuple(
                        payload_without_hash[
                            "models_with_raw_exact_match"
                        ]
                    )
                ),

                models_with_systemic_exact_match=(
                    tuple(
                        payload_without_hash[
                            "models_with_systemic_exact_match"
                        ]
                    )
                ),

                models_with_raw_dominant_match=(
                    tuple(
                        payload_without_hash[
                            "models_with_raw_dominant_match"
                        ]
                    )
                ),

                models_with_systemic_dominant_match=(
                    tuple(
                        payload_without_hash[
                            "models_with_systemic_dominant_match"
                        ]
                    )
                ),

                models_with_systemic_false_negatives=(
                    tuple(
                        payload_without_hash[
                            "models_with_systemic_false_negatives"
                        ]
                    )
                ),

                models_with_systemic_false_positives=(
                    tuple(
                        payload_without_hash[
                            "models_with_systemic_false_positives"
                        ]
                    )
                ),

                comparison_hash=(
                    comparison_hash
                ),
            )
        )

    def write_receipt(
        self,
        *,
        result:
            PreliveMultimodelBenchmarkComparisonResult,
        output_path:
            str | Path,
    ) -> None:
        path = Path(
            output_path
        )

        if path.exists():
            raise (
                PreliveMultimodelComparisonError(
                    "Comparison receipt already "
                    f"exists: {path}"
                )
            )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                result.to_dict(),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

    def _load_model(
        self,
        directory: Path,
    ) -> PreliveModelBenchmarkComparison:
        if not directory.is_dir():
            raise (
                PreliveMultimodelComparisonError(
                    "Benchmark directory does "
                    f"not exist: {directory}"
                )
            )

        benchmark = self._read_json(
            directory
            / "benchmark_summary.json"
        )

        systemic = self._read_json(
            directory
            / "systemic_scoring.json"
        )

        source_database = Path(
            str(
                benchmark[
                    "source_database_path"
                ]
            )
        )

        source_directory = (
            source_database.parent
        )

        run_summary = self._read_json(
            source_directory
            / "run_summary.json"
        )

        scenario = self._read_json(
            source_directory
            / "scenario_input.json"
        )

        raw_scoring = self._read_json(
            source_directory
            / "scoring.json"
        )

        model_label = str(
            benchmark[
                "model_label"
            ]
        ).strip()

        if not model_label:
            raise (
                PreliveMultimodelComparisonError(
                    "Benchmark model_label "
                    "must not be empty."
                )
            )

        scenario_id = str(
            benchmark[
                "scenario_id"
            ]
        ).strip()

        scenario_sha256 = str(
            benchmark[
                "scenario_sha256"
            ]
        ).strip()

        events = scenario.get(
            "events"
        )

        if not isinstance(
            events,
            list,
        ):
            raise (
                PreliveMultimodelComparisonError(
                    "Scenario events must "
                    "be a list."
                )
            )

        expected_conditions = tuple(
            sorted(
                str(value)
                for value
                in systemic.get(
                    "expected_conditions",
                    [],
                )
            )
        )

        raw_detected_conditions = (
            self._raw_detected_conditions(
                raw_scoring
            )
        )

        systemic_conditions = tuple(
            sorted(
                str(value)
                for value
                in systemic.get(
                    "systemic_conditions",
                    [],
                )
            )
        )

        scope = benchmark.get(
            "scope"
        )

        if not isinstance(
            scope,
            Mapping,
        ):
            raise (
                PreliveMultimodelComparisonError(
                    "Benchmark scope payload "
                    "is required."
                )
            )

        benchmark_hash = str(
            benchmark[
                "benchmark_hash"
            ]
        ).strip()

        scope_hash = str(
            scope[
                "scope_hash"
            ]
        ).strip()

        dominant_expected = (
            self._optional_string(
                systemic.get(
                    "expected_dominant_constraint"
                )
            )
        )

        dominant_systemic = (
            self._optional_string(
                systemic.get(
                    "detected_dominant_constraint"
                )
            )
        )

        dominant_raw = (
            self._raw_dominant(
                benchmark=benchmark,
                run_summary=run_summary,
            )
        )

        return (
            PreliveModelBenchmarkComparison(
                model_label=model_label,
                scenario_id=scenario_id,
                scenario_sha256=(
                    scenario_sha256
                ),
                event_count=len(events),

                raw_precision=float(
                    run_summary[
                        "precision"
                    ]
                ),
                raw_recall=float(
                    run_summary[
                        "recall"
                    ]
                ),
                raw_f1=float(
                    run_summary[
                        "f1"
                    ]
                ),
                raw_exact_condition_match=bool(
                    run_summary[
                        "exact_condition_match"
                    ]
                ),
                raw_dominant_constraint_match=bool(
                    run_summary[
                        "dominant_constraint_match"
                    ]
                ),

                systemic_precision=float(
                    systemic[
                        "precision"
                    ]
                ),
                systemic_recall=float(
                    systemic[
                        "recall"
                    ]
                ),
                systemic_f1=float(
                    systemic[
                        "f1"
                    ]
                ),
                systemic_exact_condition_match=bool(
                    systemic[
                        "exact_condition_match"
                    ]
                ),
                systemic_dominant_constraint_match=bool(
                    systemic[
                        "dominant_constraint_match"
                    ]
                ),

                expected_conditions=(
                    expected_conditions
                ),
                raw_detected_conditions=(
                    raw_detected_conditions
                ),
                systemic_conditions=(
                    systemic_conditions
                ),

                systemic_false_positives=tuple(
                    sorted(
                        str(value)
                        for value
                        in systemic.get(
                            "false_positives",
                            [],
                        )
                    )
                ),

                systemic_false_negatives=tuple(
                    sorted(
                        str(value)
                        for value
                        in systemic.get(
                            "false_negatives",
                            [],
                        )
                    )
                ),

                dominant_expected=(
                    dominant_expected
                ),
                dominant_raw=(
                    dominant_raw
                ),
                dominant_systemic=(
                    dominant_systemic
                ),

                benchmark_hash=(
                    benchmark_hash
                ),
                scope_hash=(
                    scope_hash
                ),

                repository_chain_valid=bool(
                    run_summary[
                        "repository_chain_valid"
                    ]
                ),

                oracle_leakage_detected=bool(
                    run_summary[
                        "oracle_leakage_detected"
                    ]
                ),
            )
        )

    def _raw_detected_conditions(
        self,
        scoring: Mapping[str, Any],
    ) -> tuple[str, ...]:
        true_positives = {
            str(value)
            for value
            in scoring.get(
                "true_positives",
                [],
            )
        }

        false_positives = {
            str(value)
            for value
            in scoring.get(
                "false_positives",
                [],
            )
        }

        return tuple(
            sorted(
                true_positives
                | false_positives
            )
        )

    def _raw_dominant(
        self,
        *,
        benchmark: Mapping[str, Any],
        run_summary: Mapping[str, Any],
    ) -> str | None:
        projection = benchmark.get(
            "projection"
        )

        if isinstance(
            projection,
            Mapping,
        ):
            value = projection.get(
                "dominant_condition"
            )

            return (
                self._optional_string(
                    value
                )
            )

        if bool(
            run_summary.get(
                "dominant_constraint_match"
            )
        ):
            return None

        return None

    def _read_json(
        self,
        path: Path,
    ) -> dict[str, Any]:
        if not path.is_file():
            raise (
                PreliveMultimodelComparisonError(
                    "Required benchmark artifact "
                    f"does not exist: {path}"
                )
            )

        try:
            value = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise (
                PreliveMultimodelComparisonError(
                    "Invalid JSON benchmark "
                    f"artifact: {path}"
                )
            ) from exc

        if not isinstance(
            value,
            dict,
        ):
            raise (
                PreliveMultimodelComparisonError(
                    "Benchmark artifact root "
                    "must be an object: "
                    f"{path}"
                )
            )

        return value

    def _mean(
        self,
        values,
    ) -> float:
        items = tuple(
            float(value)
            for value
            in values
        )

        if not items:
            return 0.0

        return round(
            mean(items),
            4,
        )

    def _ratio(
        self,
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator == 0:
            return 0.0

        return round(
            numerator / denominator,
            4,
        )

    def _true_positive_count(
        self,
        *,
        expected: Sequence[str],
        detected: Sequence[str],
    ) -> int:
        return len(
            set(expected)
            & set(detected)
        )

    def _optional_string(
        self,
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        text = str(
            value
        ).strip()

        return text or None