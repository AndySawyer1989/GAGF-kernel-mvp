from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_primary_diagnosis_projection import (
    GovernanceAssessmentPrimaryDiagnosisProjectionResult,
    GovernanceAssessmentPrimaryDiagnosisProjectionService,
)
from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)


PRELIVE_PRIMARY_DIAGNOSIS_REPLAY_VERSION = (
    "1.0.0"
)

PRELIVE_PRIMARY_DIAGNOSIS_REPLAY_STATUS = (
    "primary_diagnosis_ranking_replay_complete"
)

PRELIVE_PRIMARY_DIAGNOSIS_REPLAY_AUTHORITY = (
    "GAGF_FIP_ONLY"
)

PRIMARY_DIAGNOSIS_REPLAY_FILENAME = (
    "primary_diagnosis_ranking_replay.json"
)


class PrelivePrimaryDiagnosisReplayError(
    RuntimeError
):
    """
    Raised when a frozen PRELIVE multimodel benchmark
    cannot be replayed through primary-diagnosis
    evidence ranking deterministically.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class PrelivePrimaryDiagnosisReplayResult:
    model_label: str
    scenario_id: str
    scenario_sha256: str
    hierarchy_key: str

    benchmark_directory: str
    benchmark_database_path: str
    source_benchmark_hash: str

    projection: (
        GovernanceAssessmentPrimaryDiagnosisProjectionResult
    )

    replay_hash: str

    status: str = (
        PRELIVE_PRIMARY_DIAGNOSIS_REPLAY_STATUS
    )

    authority: str = (
        PRELIVE_PRIMARY_DIAGNOSIS_REPLAY_AUTHORITY
    )

    version: str = (
        PRELIVE_PRIMARY_DIAGNOSIS_REPLAY_VERSION
    )

    @property
    def ranked_conditions(
        self,
    ) -> tuple[str, ...]:
        return (
            self.projection
            .primary_diagnosis_summary
            .ranked_conditions
        )

    @property
    def highest_ranked_condition(
        self,
    ) -> str | None:
        return (
            self.projection
            .primary_diagnosis_summary
            .highest_ranked_condition
        )

    @property
    def ranking(
        self,
    ) -> tuple[dict[str, Any], ...]:
        return tuple(
            {
                "category":
                    condition.category,

                "rank":
                    condition.rank,

                "explanatory_score":
                    condition.explanatory_score,

                "relative_to_highest":
                    condition.relative_to_highest,

                "structural_level":
                    condition.structural_level.value,

                "evidence_quality":
                    condition.evidence_quality,

                "evidence_hash":
                    condition.evidence_hash,
            }
            for condition
            in (
                self.projection
                .primary_diagnosis_summary
                .conditions
            )
        )

    def _stable_projection_dict(
        self,
    ) -> dict[str, Any]:
        """
        Remove execution-state values that may differ
        between first projection and deterministic reuse.
        """

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

            "projection":
                self._stable_projection_dict(),

            "ranked_conditions":
                list(
                    self.ranked_conditions
                ),

            "highest_ranked_condition":
                self.highest_ranked_condition,

            "ranking": [
                dict(item)
                for item
                in self.ranking
            ],

            "replay_hash":
                self.replay_hash,
        }


class PreliveMultimodelPrimaryDiagnosisReplayService:
    """
    Replay one completed PRELIVE multimodel diagnostic
    benchmark through the frozen relative explanatory
    ranking stack.

    Inputs:

    - benchmark_summary.json
    - existing diagnostic benchmark database

    This service does NOT:

    - invoke an external AI model;
    - regenerate scenario evidence;
    - inspect systemic_scoring.json;
    - inspect a sealed oracle;
    - read planted expected conditions;
    - tune ranking weights;
    - declare root cause;
    - declare a final primary diagnosis;
    - authorize intervention.
    """

    def __init__(
        self,
        *,
        projection_service: (
            GovernanceAssessmentPrimaryDiagnosisProjectionService
            | None
        ) = None,
    ) -> None:
        self._projection_service = (
            projection_service
            or
            GovernanceAssessmentPrimaryDiagnosisProjectionService()
        )

    def replay(
        self,
        *,
        benchmark_directory: str | Path,
    ) -> PrelivePrimaryDiagnosisReplayResult:
        directory = Path(
            benchmark_directory
        )

        if not directory.is_dir():
            raise (
                PrelivePrimaryDiagnosisReplayError(
                    "Benchmark directory does not exist: "
                    f"{directory}"
                )
            )

        benchmark = self._read_json(
            directory
            / "benchmark_summary.json"
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

        benchmark_database_path = Path(
            self._required_string(
                benchmark,
                "benchmark_database_path",
            )
        )

        if not benchmark_database_path.is_file():
            raise (
                PrelivePrimaryDiagnosisReplayError(
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
                PrelivePrimaryDiagnosisReplayError(
                    "Primary-diagnosis projection hierarchy "
                    "does not match benchmark hierarchy."
                )
            )

        if (
            projection.repository_chain_valid
            is not True
        ):
            raise (
                PrelivePrimaryDiagnosisReplayError(
                    "Primary-diagnosis projection did not "
                    "preserve repository chain validity."
                )
            )

        if (
            projection.structural_projection_verified
            is not True
        ):
            raise (
                PrelivePrimaryDiagnosisReplayError(
                    "Primary-diagnosis projection did not "
                    "verify structural projection."
                )
            )

        if (
            projection.structural_classification_verified
            is not True
        ):
            raise (
                PrelivePrimaryDiagnosisReplayError(
                    "Primary-diagnosis projection did not "
                    "verify structural classification."
                )
            )

        summary = (
            projection
            .primary_diagnosis_summary
        )

        if (
            summary.hierarchy_key
            != hierarchy_key
        ):
            raise (
                PrelivePrimaryDiagnosisReplayError(
                    "Primary-diagnosis evidence hierarchy "
                    "does not match benchmark hierarchy."
                )
            )

        replay_payload = {
            "status":
                PRELIVE_PRIMARY_DIAGNOSIS_REPLAY_STATUS,

            "authority":
                PRELIVE_PRIMARY_DIAGNOSIS_REPLAY_AUTHORITY,

            "version":
                PRELIVE_PRIMARY_DIAGNOSIS_REPLAY_VERSION,

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

            "primary_diagnosis_summary_hash":
                summary.summary_hash,

            "ranked_conditions":
                list(
                    summary
                    .ranked_conditions
                ),

            "highest_ranked_condition":
                summary
                .highest_ranked_condition,

            "ranking": [
                {
                    "category":
                        condition.category,

                    "rank":
                        condition.rank,

                    "explanatory_score":
                        condition.explanatory_score,

                    "relative_to_highest":
                        condition.relative_to_highest,

                    "structural_level":
                        condition.structural_level.value,

                    "evidence_hash":
                        condition.evidence_hash,
                }
                for condition
                in summary.conditions
            ],

            "repository_chain_valid":
                projection
                .repository_chain_valid,

            "structural_projection_verified":
                projection
                .structural_projection_verified,

            "structural_classification_verified":
                projection
                .structural_classification_verified,
        }

        replay_hash = sha256_text(
            canonical_json(
                replay_payload
            )
        )

        result = (
            PrelivePrimaryDiagnosisReplayResult(
                model_label=model_label,

                scenario_id=scenario_id,

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

                projection=projection,

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
        result: PrelivePrimaryDiagnosisReplayResult,
    ) -> Path:
        directory = Path(
            benchmark_directory
        )

        output_path = (
            directory
            / PRIMARY_DIAGNOSIS_REPLAY_FILENAME
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
                    PrelivePrimaryDiagnosisReplayError(
                        "Existing primary-diagnosis ranking "
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
                PrelivePrimaryDiagnosisReplayError(
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
                PrelivePrimaryDiagnosisReplayError(
                    "Required ranking replay input "
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
                PrelivePrimaryDiagnosisReplayError(
                    "Unable to read ranking replay "
                    f"input: {path}"
                )
            ) from exc

        if not isinstance(
            value,
            Mapping,
        ):
            raise (
                PrelivePrimaryDiagnosisReplayError(
                    "Ranking replay input must be "
                    f"a JSON object: {path}"
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
                PrelivePrimaryDiagnosisReplayError(
                    f"{field_name} must be a "
                    "non-empty string."
                )
            )

        return value.strip()