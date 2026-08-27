from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)
from backend.app.gagf.prelive_multimodel_structural_importance_replay import (
    STRUCTURAL_REPLAY_FILENAME,
)


PRELIVE_STRUCTURAL_COMPARISON_VERSION = "1.0.0"

PRELIVE_STRUCTURAL_COMPARISON_STATUS = (
    "structural_importance_comparison_complete"
)

PRELIVE_STRUCTURAL_COMPARISON_AUTHORITY = (
    "GAGF_FIP_ONLY"
)

STRUCTURAL_COMPARISON_FILENAME = (
    "structural_importance_comparison.json"
)


class PreliveStructuralImportanceComparisonError(
    RuntimeError
):
    """
    Raised when structural replay outputs cannot be
    compared deterministically.
    """


@dataclass(frozen=True, slots=True)
class PreliveModelStructuralImportanceComparison:
    model_label: str
    scenario_id: str
    scenario_sha256: str
    hierarchy_key: str

    expected_conditions: tuple[str, ...]

    high_conditions: tuple[str, ...]
    moderate_conditions: tuple[str, ...]
    low_conditions: tuple[str, ...]
    limited_conditions: tuple[str, ...]

    high_true_positives: tuple[str, ...]
    high_false_positives: tuple[str, ...]
    high_false_negatives: tuple[str, ...]

    high_or_moderate_true_positives: tuple[str, ...]
    high_or_moderate_false_positives: tuple[str, ...]
    high_or_moderate_false_negatives: tuple[str, ...]

    high_precision: float
    high_recall: float

    high_or_moderate_precision: float
    high_or_moderate_recall: float

    limited_rate: float

    benchmark_hash: str
    structural_replay_hash: str
    structural_classification_hash: str

    benchmark_binding_valid: bool
    repository_chain_valid: bool
    diagnostic_integrity_verified: bool

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

            "expected_conditions":
                list(
                    self.expected_conditions
                ),

            "high_conditions":
                list(
                    self.high_conditions
                ),
            "moderate_conditions":
                list(
                    self.moderate_conditions
                ),
            "low_conditions":
                list(
                    self.low_conditions
                ),
            "limited_conditions":
                list(
                    self.limited_conditions
                ),

            "high_true_positives":
                list(
                    self.high_true_positives
                ),
            "high_false_positives":
                list(
                    self.high_false_positives
                ),
            "high_false_negatives":
                list(
                    self.high_false_negatives
                ),

            "high_or_moderate_true_positives":
                list(
                    self.high_or_moderate_true_positives
                ),
            "high_or_moderate_false_positives":
                list(
                    self.high_or_moderate_false_positives
                ),
            "high_or_moderate_false_negatives":
                list(
                    self.high_or_moderate_false_negatives
                ),

            "high_precision":
                self.high_precision,
            "high_recall":
                self.high_recall,

            "high_or_moderate_precision":
                self.high_or_moderate_precision,
            "high_or_moderate_recall":
                self.high_or_moderate_recall,

            "limited_rate":
                self.limited_rate,

            "benchmark_hash":
                self.benchmark_hash,
            "structural_replay_hash":
                self.structural_replay_hash,
            "structural_classification_hash":
                self.structural_classification_hash,

            "benchmark_binding_valid":
                self.benchmark_binding_valid,
            "repository_chain_valid":
                self.repository_chain_valid,
            "diagnostic_integrity_verified":
                self.diagnostic_integrity_verified,
        }


@dataclass(frozen=True, slots=True)
class PreliveMultimodelStructuralImportanceComparisonResult:
    models: tuple[
        PreliveModelStructuralImportanceComparison,
        ...,
    ]

    model_count: int
    total_scenarios: int
    total_expected_conditions: int
    total_classified_conditions: int

    high_precision: float
    high_recall: float

    high_or_moderate_precision: float
    high_or_moderate_recall: float

    primary_high_hit_rate: float
    primary_high_or_moderate_hit_rate: float

    false_high_rate: float
    limited_rate: float

    models_with_all_expected_high: tuple[str, ...]
    models_with_all_expected_high_or_moderate: tuple[str, ...]
    models_with_false_highs: tuple[str, ...]
    models_with_limited_conditions: tuple[str, ...]

    comparison_hash: str

    status: str = (
        PRELIVE_STRUCTURAL_COMPARISON_STATUS
    )

    authority: str = (
        PRELIVE_STRUCTURAL_COMPARISON_AUTHORITY
    )

    version: str = (
        PRELIVE_STRUCTURAL_COMPARISON_VERSION
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
            "total_expected_conditions":
                self.total_expected_conditions,
            "total_classified_conditions":
                self.total_classified_conditions,

            "high_precision":
                self.high_precision,
            "high_recall":
                self.high_recall,

            "high_or_moderate_precision":
                self.high_or_moderate_precision,
            "high_or_moderate_recall":
                self.high_or_moderate_recall,

            "primary_high_hit_rate":
                self.primary_high_hit_rate,
            "primary_high_or_moderate_hit_rate":
                self.primary_high_or_moderate_hit_rate,

            "false_high_rate":
                self.false_high_rate,
            "limited_rate":
                self.limited_rate,

            "models_with_all_expected_high":
                list(
                    self.models_with_all_expected_high
                ),
            "models_with_all_expected_high_or_moderate":
                list(
                    self.models_with_all_expected_high_or_moderate
                ),
            "models_with_false_highs":
                list(
                    self.models_with_false_highs
                ),
            "models_with_limited_conditions":
                list(
                    self.models_with_limited_conditions
                ),

            "models": [
                model.to_dict()
                for model
                in self.models
            ],

            "comparison_hash":
                self.comparison_hash,
        }


class PreliveMultimodelStructuralImportanceComparisonService:
    """
    Compare frozen structural-importance replay receipts
    against the sealed expected-condition outputs already
    present in systemic_scoring.json.

    This service performs calibration only.

    It does not:

    - change structural-importance thresholds;
    - regenerate model evidence;
    - rerun an assessment;
    - assign root cause;
    - assign primary diagnosis;
    - authorize intervention.
    """

    def compare(
        self,
        *,
        benchmark_directories: Sequence[
            str | Path
        ],
    ) -> (
        PreliveMultimodelStructuralImportanceComparisonResult
    ):
        if not benchmark_directories:
            raise (
                PreliveStructuralImportanceComparisonError(
                    "At least one benchmark directory "
                    "is required."
                )
            )

        models = tuple(
            self._load_model(
                Path(
                    directory
                )
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
                PreliveStructuralImportanceComparisonError(
                    "Benchmark model labels must "
                    "be unique."
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
                PreliveStructuralImportanceComparisonError(
                    "Benchmark scenario IDs must "
                    "be unique."
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

        total_expected = sum(
            len(
                model.expected_conditions
            )
            for model
            in ordered
        )

        total_classified = sum(
            len(
                set(
                    model.high_conditions
                )
                | set(
                    model.moderate_conditions
                )
                | set(
                    model.low_conditions
                )
                | set(
                    model.limited_conditions
                )
            )
            for model
            in ordered
        )

        high_detected_total = sum(
            len(
                model.high_conditions
            )
            for model
            in ordered
        )

        high_true_positive_total = sum(
            len(
                model.high_true_positives
            )
            for model
            in ordered
        )

        high_false_positive_total = sum(
            len(
                model.high_false_positives
            )
            for model
            in ordered
        )

        high_or_moderate_detected_total = sum(
            len(
                set(
                    model.high_conditions
                )
                | set(
                    model.moderate_conditions
                )
            )
            for model
            in ordered
        )

        high_or_moderate_true_positive_total = sum(
            len(
                model.high_or_moderate_true_positives
            )
            for model
            in ordered
        )

        limited_total = sum(
            len(
                model.limited_conditions
            )
            for model
            in ordered
        )

        high_precision = self._ratio(
            high_true_positive_total,
            high_detected_total,
        )

        high_recall = self._ratio(
            high_true_positive_total,
            total_expected,
        )

        high_or_moderate_precision = (
            self._ratio(
                high_or_moderate_true_positive_total,
                high_or_moderate_detected_total,
            )
        )

        high_or_moderate_recall = (
            self._ratio(
                high_or_moderate_true_positive_total,
                total_expected,
            )
        )

        false_high_rate = self._ratio(
            high_false_positive_total,
            high_detected_total,
        )

        limited_rate = self._ratio(
            limited_total,
            total_classified,
        )

        payload_without_hash = {
            "status":
                PRELIVE_STRUCTURAL_COMPARISON_STATUS,
            "authority":
                PRELIVE_STRUCTURAL_COMPARISON_AUTHORITY,
            "version":
                PRELIVE_STRUCTURAL_COMPARISON_VERSION,

            "model_count":
                len(
                    ordered
                ),
            "total_scenarios":
                len(
                    ordered
                ),
            "total_expected_conditions":
                total_expected,
            "total_classified_conditions":
                total_classified,

            "high_precision":
                high_precision,
            "high_recall":
                high_recall,

            "high_or_moderate_precision":
                high_or_moderate_precision,
            "high_or_moderate_recall":
                high_or_moderate_recall,

            # Explicit aliases make the calibration
            # interpretation visible in the receipt.
            "primary_high_hit_rate":
                high_recall,
            "primary_high_or_moderate_hit_rate":
                high_or_moderate_recall,

            "false_high_rate":
                false_high_rate,
            "limited_rate":
                limited_rate,

            "models_with_all_expected_high": [
                model.model_label
                for model
                in ordered
                if (
                    bool(
                        model.expected_conditions
                    )
                    and
                    not model.high_false_negatives
                )
            ],

            "models_with_all_expected_high_or_moderate": [
                model.model_label
                for model
                in ordered
                if (
                    bool(
                        model.expected_conditions
                    )
                    and
                    not (
                        model
                        .high_or_moderate_false_negatives
                    )
                )
            ],

            "models_with_false_highs": [
                model.model_label
                for model
                in ordered
                if model.high_false_positives
            ],

            "models_with_limited_conditions": [
                model.model_label
                for model
                in ordered
                if model.limited_conditions
            ],

            "models": [
                model.to_dict()
                for model
                in ordered
            ],
        }

        comparison_hash = sha256_text(
            canonical_json(
                payload_without_hash
            )
        )

        return (
            PreliveMultimodelStructuralImportanceComparisonResult(
                models=ordered,

                model_count=len(
                    ordered
                ),
                total_scenarios=len(
                    ordered
                ),
                total_expected_conditions=(
                    total_expected
                ),
                total_classified_conditions=(
                    total_classified
                ),

                high_precision=(
                    high_precision
                ),
                high_recall=(
                    high_recall
                ),

                high_or_moderate_precision=(
                    high_or_moderate_precision
                ),
                high_or_moderate_recall=(
                    high_or_moderate_recall
                ),

                primary_high_hit_rate=(
                    high_recall
                ),
                primary_high_or_moderate_hit_rate=(
                    high_or_moderate_recall
                ),

                false_high_rate=(
                    false_high_rate
                ),
                limited_rate=(
                    limited_rate
                ),

                models_with_all_expected_high=tuple(
                    payload_without_hash[
                        "models_with_all_expected_high"
                    ]
                ),

                models_with_all_expected_high_or_moderate=tuple(
                    payload_without_hash[
                        "models_with_all_expected_high_or_moderate"
                    ]
                ),

                models_with_false_highs=tuple(
                    payload_without_hash[
                        "models_with_false_highs"
                    ]
                ),

                models_with_limited_conditions=tuple(
                    payload_without_hash[
                        "models_with_limited_conditions"
                    ]
                ),

                comparison_hash=(
                    comparison_hash
                ),
            )
        )

    def write_receipt(
        self,
        *,
        output_directory: str | Path,
        result: (
            PreliveMultimodelStructuralImportanceComparisonResult
        ),
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
            / STRUCTURAL_COMPARISON_FILENAME
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
                    PreliveStructuralImportanceComparisonError(
                        "Existing structural comparison "
                        "receipt does not match "
                        "deterministic comparison."
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

    def _load_model(
        self,
        directory: Path,
    ) -> PreliveModelStructuralImportanceComparison:
        if not directory.is_dir():
            raise (
                PreliveStructuralImportanceComparisonError(
                    "Benchmark directory does not exist: "
                    f"{directory}"
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

        replay = self._read_json(
            directory
            / STRUCTURAL_REPLAY_FILENAME
        )

        model_label = self._required_string(
            benchmark,
            "model_label",
        )

        scenario_id = self._required_string(
            benchmark,
            "scenario_id",
        )

        scenario_sha256 = self._required_string(
            benchmark,
            "scenario_sha256",
        )

        hierarchy_key = self._required_string(
            benchmark,
            "hierarchy_key",
        )

        benchmark_hash = self._required_string(
            benchmark,
            "benchmark_hash",
        )

        self._require_equal(
            field_name="model_label",
            expected=model_label,
            observed=self._required_string(
                replay,
                "model_label",
            ),
        )

        self._require_equal(
            field_name="scenario_id",
            expected=scenario_id,
            observed=self._required_string(
                replay,
                "scenario_id",
            ),
        )

        self._require_equal(
            field_name="scenario_sha256",
            expected=scenario_sha256,
            observed=self._required_string(
                replay,
                "scenario_sha256",
            ),
        )

        self._require_equal(
            field_name="hierarchy_key",
            expected=hierarchy_key,
            observed=self._required_string(
                replay,
                "hierarchy_key",
            ),
        )

        source_benchmark_hash = (
            self._required_string(
                replay,
                "source_benchmark_hash",
            )
        )

        if (
            source_benchmark_hash
            != benchmark_hash
        ):
            raise (
                PreliveStructuralImportanceComparisonError(
                    "Structural replay benchmark hash "
                    "does not match benchmark summary."
                )
            )

        expected_conditions = (
            self._string_tuple(
                systemic.get(
                    "expected_conditions",
                    [],
                ),
                field_name=(
                    "expected_conditions"
                ),
            )
        )

        high_conditions = (
            self._string_tuple(
                replay.get(
                    "high_conditions",
                    [],
                ),
                field_name=(
                    "high_conditions"
                ),
            )
        )

        moderate_conditions = (
            self._string_tuple(
                replay.get(
                    "moderate_conditions",
                    [],
                ),
                field_name=(
                    "moderate_conditions"
                ),
            )
        )

        low_conditions = (
            self._string_tuple(
                replay.get(
                    "low_conditions",
                    [],
                ),
                field_name=(
                    "low_conditions"
                ),
            )
        )

        limited_conditions = (
            self._string_tuple(
                replay.get(
                    "limited_conditions",
                    [],
                ),
                field_name=(
                    "limited_conditions"
                ),
            )
        )

        self._validate_disjoint_buckets(
            high=high_conditions,
            moderate=moderate_conditions,
            low=low_conditions,
            limited=limited_conditions,
        )

        expected_set = set(
            expected_conditions
        )

        high_set = set(
            high_conditions
        )

        high_or_moderate_set = (
            high_set
            | set(
                moderate_conditions
            )
        )

        high_true_positives = tuple(
            sorted(
                expected_set
                & high_set
            )
        )

        high_false_positives = tuple(
            sorted(
                high_set
                - expected_set
            )
        )

        high_false_negatives = tuple(
            sorted(
                expected_set
                - high_set
            )
        )

        high_or_moderate_true_positives = tuple(
            sorted(
                expected_set
                & high_or_moderate_set
            )
        )

        high_or_moderate_false_positives = tuple(
            sorted(
                high_or_moderate_set
                - expected_set
            )
        )

        high_or_moderate_false_negatives = tuple(
            sorted(
                expected_set
                - high_or_moderate_set
            )
        )

        classified_count = len(
            high_set
            | set(
                moderate_conditions
            )
            | set(
                low_conditions
            )
            | set(
                limited_conditions
            )
        )

        projection = replay.get(
            "projection"
        )

        if not isinstance(
            projection,
            Mapping,
        ):
            raise (
                PreliveStructuralImportanceComparisonError(
                    "Structural replay projection "
                    "payload is required."
                )
            )

        classification = replay.get(
            "classification"
        )

        if not isinstance(
            classification,
            Mapping,
        ):
            raise (
                PreliveStructuralImportanceComparisonError(
                    "Structural replay classification "
                    "payload is required."
                )
            )

        return (
            PreliveModelStructuralImportanceComparison(
                model_label=model_label,
                scenario_id=scenario_id,
                scenario_sha256=(
                    scenario_sha256
                ),
                hierarchy_key=(
                    hierarchy_key
                ),

                expected_conditions=(
                    expected_conditions
                ),

                high_conditions=(
                    high_conditions
                ),
                moderate_conditions=(
                    moderate_conditions
                ),
                low_conditions=(
                    low_conditions
                ),
                limited_conditions=(
                    limited_conditions
                ),

                high_true_positives=(
                    high_true_positives
                ),
                high_false_positives=(
                    high_false_positives
                ),
                high_false_negatives=(
                    high_false_negatives
                ),

                high_or_moderate_true_positives=(
                    high_or_moderate_true_positives
                ),
                high_or_moderate_false_positives=(
                    high_or_moderate_false_positives
                ),
                high_or_moderate_false_negatives=(
                    high_or_moderate_false_negatives
                ),

                high_precision=self._ratio(
                    len(
                        high_true_positives
                    ),
                    len(
                        high_conditions
                    ),
                ),

                high_recall=self._ratio(
                    len(
                        high_true_positives
                    ),
                    len(
                        expected_conditions
                    ),
                ),

                high_or_moderate_precision=(
                    self._ratio(
                        len(
                            high_or_moderate_true_positives
                        ),
                        len(
                            high_or_moderate_set
                        ),
                    )
                ),

                high_or_moderate_recall=(
                    self._ratio(
                        len(
                            high_or_moderate_true_positives
                        ),
                        len(
                            expected_conditions
                        ),
                    )
                ),

                limited_rate=self._ratio(
                    len(
                        limited_conditions
                    ),
                    classified_count,
                ),

                benchmark_hash=(
                    benchmark_hash
                ),

                structural_replay_hash=(
                    self._required_string(
                        replay,
                        "replay_hash",
                    )
                ),

                structural_classification_hash=(
                    self._required_string(
                        classification,
                        "summary_hash",
                    )
                ),

                benchmark_binding_valid=True,

                repository_chain_valid=bool(
                    projection.get(
                        "repository_chain_valid",
                        False,
                    )
                ),

                diagnostic_integrity_verified=bool(
                    projection.get(
                        "diagnostic_integrity_verified",
                        False,
                    )
                ),
            )
        )

    def _validate_disjoint_buckets(
        self,
        *,
        high: tuple[str, ...],
        moderate: tuple[str, ...],
        low: tuple[str, ...],
        limited: tuple[str, ...],
    ) -> None:
        buckets = (
            ("HIGH", set(high)),
            ("MODERATE", set(moderate)),
            ("LOW", set(low)),
            ("LIMITED", set(limited)),
        )

        for index, (
            left_name,
            left_values,
        ) in enumerate(
            buckets
        ):
            for (
                right_name,
                right_values,
            ) in buckets[
                index + 1:
            ]:
                overlap = (
                    left_values
                    & right_values
                )

                if overlap:
                    raise (
                        PreliveStructuralImportanceComparisonError(
                            "Structural classification "
                            "buckets overlap: "
                            f"{left_name}/{right_name}: "
                            f"{sorted(overlap)}"
                        )
                    )

    def _string_tuple(
        self,
        value: Any,
        *,
        field_name: str,
    ) -> tuple[str, ...]:
        if not isinstance(
            value,
            list,
        ):
            raise (
                PreliveStructuralImportanceComparisonError(
                    f"{field_name} must be a list."
                )
            )

        normalized = tuple(
            sorted(
                {
                    str(item).strip()
                    for item
                    in value
                    if str(item).strip()
                }
            )
        )

        return normalized

    def _require_equal(
        self,
        *,
        field_name: str,
        expected: str,
        observed: str,
    ) -> None:
        if observed != expected:
            raise (
                PreliveStructuralImportanceComparisonError(
                    "Structural replay "
                    f"{field_name} does not match "
                    "benchmark summary."
                )
            )

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
                PreliveStructuralImportanceComparisonError(
                    f"{field_name} must be "
                    "a non-empty string."
                )
            )

        return value.strip()

    def _read_json(
        self,
        path: Path,
    ) -> Mapping[str, Any]:
        if not path.is_file():
            raise (
                PreliveStructuralImportanceComparisonError(
                    "Required comparison input "
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
                PreliveStructuralImportanceComparisonError(
                    "Unable to read comparison "
                    f"input: {path}"
                )
            ) from exc

        if not isinstance(
            value,
            Mapping,
        ):
            raise (
                PreliveStructuralImportanceComparisonError(
                    "Comparison input must be "
                    f"a JSON object: {path}"
                )
            )

        return value

    def _ratio(
        self,
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator <= 0:
            return 0.0

        return round(
            numerator
            / denominator,
            10,
        )