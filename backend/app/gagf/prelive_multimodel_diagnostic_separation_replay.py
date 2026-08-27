from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.governance_assessment_diagnostic_separation_projection import (
    GovernanceAssessmentDiagnosticSeparationProjectionResult,
    GovernanceAssessmentDiagnosticSeparationProjectionService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)


PRELIVE_DIAGNOSTIC_SEPARATION_REPLAY_VERSION = (
    "1.0.0"
)

PRELIVE_DIAGNOSTIC_SEPARATION_REPLAY_STATUS = (
    "diagnostic_separation_replay_complete"
)

PRELIVE_DIAGNOSTIC_SEPARATION_REPLAY_AUTHORITY = (
    "GAGF_FIP_ONLY"
)

DIAGNOSTIC_SEPARATION_REPLAY_FILENAME = (
    "diagnostic_separation_replay.json"
)

PRIMARY_DIAGNOSIS_REPLAY_FILENAME = (
    "primary_diagnosis_ranking_replay.json"
)


class PreliveDiagnosticSeparationReplayError(
    RuntimeError
):
    """
    Raised when a frozen PRELIVE benchmark cannot be
    replayed through threshold-free diagnostic separation
    deterministically.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class PreliveDiagnosticSeparationReplayResult:
    model_label: str
    scenario_id: str
    scenario_sha256: str
    hierarchy_key: str

    benchmark_directory: str
    benchmark_database_path: str
    source_benchmark_hash: str

    primary_diagnosis_replay_hash: str

    projection: (
        GovernanceAssessmentDiagnosticSeparationProjectionResult
    )

    replay_hash: str

    status: str = (
        PRELIVE_DIAGNOSTIC_SEPARATION_REPLAY_STATUS
    )

    authority: str = (
        PRELIVE_DIAGNOSTIC_SEPARATION_REPLAY_AUTHORITY
    )

    version: str = (
        PRELIVE_DIAGNOSTIC_SEPARATION_REPLAY_VERSION
    )

    @property
    def leading_candidate(
        self,
    ) -> str | None:
        summary = (
            self.projection
            .separation_summary
        )

        return (
            summary
            .leading_candidate_category
        )

    @property
    def runner_up_candidate(
        self,
    ) -> str | None:
        summary = (
            self.projection
            .separation_summary
        )

        if (
            summary.runner_up_candidate
            is None
        ):
            return None

        return (
            summary.runner_up_candidate
            .category
        )

    @property
    def rank_1_score(
        self,
    ) -> float | None:
        return (
            self.projection
            .separation_summary
            .metrics
            .rank_1_score
        )

    @property
    def rank_2_score(
        self,
    ) -> float | None:
        return (
            self.projection
            .separation_summary
            .metrics
            .rank_2_score
        )

    @property
    def rank_1_to_rank_2_absolute(
        self,
    ) -> float | None:
        return (
            self.projection
            .separation_summary
            .metrics
            .rank_1_to_rank_2_absolute
        )

    @property
    def rank_1_to_rank_2_relative(
        self,
    ) -> float | None:
        return (
            self.projection
            .separation_summary
            .metrics
            .rank_1_to_rank_2_relative
        )

    @property
    def rank_1_to_rank_3_absolute(
        self,
    ) -> float | None:
        return (
            self.projection
            .separation_summary
            .metrics
            .rank_1_to_rank_3_absolute
        )

    @property
    def rank_1_to_rank_3_relative(
        self,
    ) -> float | None:
        return (
            self.projection
            .separation_summary
            .metrics
            .rank_1_to_rank_3_relative
        )

    @property
    def top_3_score_spread(
        self,
    ) -> float | None:
        return (
            self.projection
            .separation_summary
            .metrics
            .top_3_score_spread
        )

    def _stable_projection_dict(
        self,
    ) -> dict[str, Any]:
        payload = dict(
            self.projection.to_dict()
        )

        payload.pop(
            "reused_existing",
            None,
        )

        return payload

    def to_dict(
        self,
    ) -> dict[str, Any]:
        summary = (
            self.projection
            .separation_summary
        )

        return {
            "status":
                self.status,

            "authority":
                self.authority,

            "version":
                self.version,

            "model_label":
                self.model_label,

            "scenario_id":
                self.scenario_id,

            "scenario_sha256":
                self.scenario_sha256,

            "hierarchy_key":
                self.hierarchy_key,

            "benchmark_directory":
                self.benchmark_directory,

            "benchmark_database_path":
                self.benchmark_database_path,

            "source_benchmark_hash":
                self.source_benchmark_hash,

            "primary_diagnosis_replay_hash":
                self.primary_diagnosis_replay_hash,

            "projection":
                self._stable_projection_dict(),

            "separation_summary_hash":
                summary.summary_hash,

            "primary_diagnosis_summary_hash":
                summary.primary_diagnosis_summary_hash,

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

            "support":
                summary.support.to_dict(),

            "replay_hash":
                self.replay_hash,
        }


class PreliveMultimodelDiagnosticSeparationReplayService:
    """
    Replay one frozen PRELIVE diagnostic benchmark through
    threshold-free diagnostic separation.

    Inputs:

    - benchmark_summary.json
    - primary_diagnosis_ranking_replay.json
    - existing benchmark database

    This service does not:

    - invoke an external AI model;
    - regenerate evidence;
    - inspect an oracle;
    - read expected conditions;
    - select separation thresholds;
    - classify confidence;
    - establish correctness;
    - establish causation;
    - declare root cause;
    - authorize intervention.
    """

    def __init__(
        self,
        *,
        projection_service: (
            GovernanceAssessmentDiagnosticSeparationProjectionService
            | None
        ) = None,
    ) -> None:
        self._projection_service = (
            projection_service
            or
            GovernanceAssessmentDiagnosticSeparationProjectionService()
        )

    def replay(
        self,
        *,
        benchmark_directory: str | Path,
    ) -> PreliveDiagnosticSeparationReplayResult:
        directory = Path(
            benchmark_directory
        )

        if not directory.is_dir():
            raise (
                PreliveDiagnosticSeparationReplayError(
                    "Benchmark directory does not exist: "
                    f"{directory}"
                )
            )

        benchmark = self._read_json(
            directory
            / "benchmark_summary.json"
        )

        primary_replay = self._read_json(
            directory
            / PRIMARY_DIAGNOSIS_REPLAY_FILENAME
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

        source_benchmark_hash = (
            self._required_string(
                benchmark,
                "benchmark_hash",
            )
        )

        primary_diagnosis_replay_hash = (
            self._required_string(
                primary_replay,
                "replay_hash",
            )
        )

        self._verify_primary_replay_binding(
            benchmark=benchmark,
            primary_replay=primary_replay,
        )

        benchmark_database_path = Path(
            self._required_string(
                benchmark,
                "benchmark_database_path",
            )
        )

        if not benchmark_database_path.is_file():
            raise (
                PreliveDiagnosticSeparationReplayError(
                    "Benchmark database does not exist: "
                    f"{benchmark_database_path}"
                )
            )

        context = self._context_from_hierarchy(
            hierarchy_key
        )

        projection = (
            self._projection_service.project(
                database_path=(
                    benchmark_database_path
                ),
                context=context,
            )
        )

        if (
            projection.hierarchy_key
            != hierarchy_key
        ):
            raise (
                PreliveDiagnosticSeparationReplayError(
                    "Diagnostic-separation projection "
                    "hierarchy does not match benchmark."
                )
            )

        if (
            projection.repository_chain_valid
            is not True
        ):
            raise (
                PreliveDiagnosticSeparationReplayError(
                    "Diagnostic-separation projection did "
                    "not preserve repository chain validity."
                )
            )

        if (
            projection.primary_projection_verified
            is not True
        ):
            raise (
                PreliveDiagnosticSeparationReplayError(
                    "Diagnostic-separation projection did "
                    "not verify primary projection."
                )
            )

        if (
            projection.structural_projection_verified
            is not True
        ):
            raise (
                PreliveDiagnosticSeparationReplayError(
                    "Diagnostic-separation projection did "
                    "not verify structural projection."
                )
            )

        if (
            projection.structural_classification_verified
            is not True
        ):
            raise (
                PreliveDiagnosticSeparationReplayError(
                    "Diagnostic-separation projection did "
                    "not verify structural classification."
                )
            )

        summary = (
            projection
            .separation_summary
        )

        if (
            summary.hierarchy_key
            != hierarchy_key
        ):
            raise (
                PreliveDiagnosticSeparationReplayError(
                    "Diagnostic-separation evidence "
                    "hierarchy does not match benchmark."
                )
            )

        replay_payload = {
            "status":
                PRELIVE_DIAGNOSTIC_SEPARATION_REPLAY_STATUS,

            "authority":
                PRELIVE_DIAGNOSTIC_SEPARATION_REPLAY_AUTHORITY,

            "version":
                PRELIVE_DIAGNOSTIC_SEPARATION_REPLAY_VERSION,

            "model_label":
                model_label,

            "scenario_id":
                scenario_id,

            "scenario_sha256":
                scenario_sha256,

            "hierarchy_key":
                hierarchy_key,

            "source_benchmark_hash":
                source_benchmark_hash,

            "primary_diagnosis_replay_hash":
                primary_diagnosis_replay_hash,

            "separation_summary_hash":
                summary.summary_hash,

            "primary_diagnosis_summary_hash":
                summary.primary_diagnosis_summary_hash,

            "leading_candidate":
                summary.leading_candidate_category,

            "runner_up_candidate":
                (
                    summary.runner_up_candidate.category
                    if summary.runner_up_candidate
                    is not None
                    else None
                ),

            "metrics":
                summary.metrics.to_dict(),

            "support":
                summary.support.to_dict(),

            "repository_chain_valid":
                projection.repository_chain_valid,

            "primary_projection_verified":
                projection.primary_projection_verified,

            "structural_projection_verified":
                projection.structural_projection_verified,

            "structural_classification_verified":
                projection.structural_classification_verified,
        }

        replay_hash = sha256_text(
            canonical_json(
                replay_payload
            )
        )

        result = (
            PreliveDiagnosticSeparationReplayResult(
                model_label=(
                    model_label
                ),

                scenario_id=(
                    scenario_id
                ),

                scenario_sha256=(
                    scenario_sha256
                ),

                hierarchy_key=(
                    hierarchy_key
                ),

                benchmark_directory=str(
                    directory
                ),

                benchmark_database_path=str(
                    benchmark_database_path
                ),

                source_benchmark_hash=(
                    source_benchmark_hash
                ),

                primary_diagnosis_replay_hash=(
                    primary_diagnosis_replay_hash
                ),

                projection=(
                    projection
                ),

                replay_hash=(
                    replay_hash
                ),
            )
        )

        self.write_receipt(
            benchmark_directory=directory,
            result=result,
        )

        return result

    def write_receipt(
        self,
        *,
        benchmark_directory: str | Path,
        result: PreliveDiagnosticSeparationReplayResult,
    ) -> Path:
        directory = Path(
            benchmark_directory
        )

        output_path = (
            directory
            / DIAGNOSTIC_SEPARATION_REPLAY_FILENAME
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
                    PreliveDiagnosticSeparationReplayError(
                        "Existing diagnostic-separation "
                        "replay receipt does not match "
                        "deterministic replay."
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

    def _verify_primary_replay_binding(
        self,
        *,
        benchmark: Mapping[str, Any],
        primary_replay: Mapping[str, Any],
    ) -> None:
        fields = (
            "model_label",
            "scenario_id",
            "scenario_sha256",
            "hierarchy_key",
        )

        for field_name in fields:
            benchmark_value = (
                self._required_string(
                    benchmark,
                    field_name,
                )
            )

            replay_value = (
                self._required_string(
                    primary_replay,
                    field_name,
                )
            )

            if (
                benchmark_value
                != replay_value
            ):
                raise (
                    PreliveDiagnosticSeparationReplayError(
                        "Primary-diagnosis replay "
                        f"{field_name} binding mismatch."
                    )
                )

        benchmark_hash = (
            self._required_string(
                benchmark,
                "benchmark_hash",
            )
        )

        replay_benchmark_hash = (
            self._required_string(
                primary_replay,
                "source_benchmark_hash",
            )
        )

        if (
            benchmark_hash
            != replay_benchmark_hash
        ):
            raise (
                PreliveDiagnosticSeparationReplayError(
                    "Primary-diagnosis replay benchmark "
                    "hash binding mismatch."
                )
            )

    def _context_from_hierarchy(
        self,
        hierarchy_key: str,
    ) -> CommercialHierarchyContext:
        parts = hierarchy_key.split(
            "/"
        )

        if (
            len(parts) != 4
            or any(
                not part.strip()
                for part
                in parts
            )
        ):
            raise (
                PreliveDiagnosticSeparationReplayError(
                    "Benchmark hierarchy_key must contain "
                    "tenant/client/engagement/assessment."
                )
            )

        return (
            CommercialHierarchyContext(
                tenant_id=(
                    parts[0].strip()
                ),

                client_id=(
                    parts[1].strip()
                ),

                engagement_id=(
                    parts[2].strip()
                ),

                assessment_id=(
                    parts[3].strip()
                ),
            )
        )

    def _read_json(
        self,
        path: Path,
    ) -> Mapping[str, Any]:
        if not path.is_file():
            raise (
                PreliveDiagnosticSeparationReplayError(
                    "Required diagnostic-separation "
                    f"replay input does not exist: {path}"
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
                PreliveDiagnosticSeparationReplayError(
                    "Unable to read diagnostic-separation "
                    f"replay input: {path}"
                )
            ) from exc

        if not isinstance(
            value,
            Mapping,
        ):
            raise (
                PreliveDiagnosticSeparationReplayError(
                    "Diagnostic-separation replay input "
                    f"must be a JSON object: {path}"
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
                PreliveDiagnosticSeparationReplayError(
                    f"{field_name} must be a "
                    "non-empty string."
                )
            )

        return value.strip()