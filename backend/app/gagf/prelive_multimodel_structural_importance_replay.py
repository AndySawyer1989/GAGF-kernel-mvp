from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    canonical_json,
    sha256_text,
)
from backend.app.gagf.governance_assessment_structural_importance_classification import (
    AssessmentStructuralImportanceClassificationSummary,
    GovernanceAssessmentStructuralImportanceClassificationService,
)
from backend.app.gagf.governance_assessment_structural_importance_projection import (
    GovernanceAssessmentStructuralImportanceProjectionResult,
    GovernanceAssessmentStructuralImportanceProjectionService,
)


PRELIVE_STRUCTURAL_REPLAY_VERSION = "1.0.0"

PRELIVE_STRUCTURAL_REPLAY_STATUS = (
    "structural_importance_replay_complete"
)

PRELIVE_STRUCTURAL_REPLAY_AUTHORITY = (
    "GAGF_FIP_ONLY"
)

STRUCTURAL_REPLAY_FILENAME = (
    "structural_importance_replay.json"
)


class PreliveStructuralImportanceReplayError(
    RuntimeError
):
    """
    Raised when a frozen PRELIVE multimodel benchmark
    cannot be replayed through structural-importance
    analysis deterministically.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class PreliveStructuralImportanceReplayResult:
    model_label: str
    scenario_id: str
    scenario_sha256: str
    hierarchy_key: str

    benchmark_directory: str
    benchmark_database_path: str
    source_benchmark_hash: str

    projection: (
        GovernanceAssessmentStructuralImportanceProjectionResult
    )

    classification: (
        AssessmentStructuralImportanceClassificationSummary
    )

    replay_hash: str

    status: str = (
        PRELIVE_STRUCTURAL_REPLAY_STATUS
    )

    authority: str = (
        PRELIVE_STRUCTURAL_REPLAY_AUTHORITY
    )

    version: str = (
        PRELIVE_STRUCTURAL_REPLAY_VERSION
    )

    @property
    def high_conditions(
        self,
    ) -> tuple[str, ...]:
        return (
            self.classification
            .high_importance_conditions
        )

    @property
    def moderate_conditions(
        self,
    ) -> tuple[str, ...]:
        return (
            self.classification
            .moderate_importance_conditions
        )

    @property
    def low_conditions(
        self,
    ) -> tuple[str, ...]:
        return (
            self.classification
            .low_importance_conditions
        )

    @property
    def limited_conditions(
        self,
    ) -> tuple[str, ...]:
        return (
            self.classification
            .limited_evidence_conditions
        )

    def _stable_projection_dict(
        self,
    ) -> dict[str, Any]:
        """
        Return the evidence-bearing projection receipt while
        excluding execution-state fields that can legitimately
        differ between an initial projection and deterministic reuse.
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

            "classification":
                self.classification.to_dict(),

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

            "replay_hash":
                self.replay_hash,
        }


class PreliveMultimodelStructuralImportanceReplayService:
    """
    Replay one completed PRELIVE multimodel diagnostic
    benchmark through the frozen structural-importance
    stack.

    Input authority:

    - benchmark_summary.json
    - diagnostic benchmark database copied by the
      existing multimodel benchmark

    Processing:

    1. Read the existing benchmark summary.
    2. Validate its identity and hierarchy.
    3. Open the existing copied benchmark database.
    4. Run deterministic structural-importance
       projection.
    5. Verify persisted diagnostic significance through
       the structural projection boundary.
    6. Run the frozen four-level classifier.
    7. Bind the result to the original benchmark hash.
    8. Write one deterministic replay receipt.

    This service does not:

    - invoke Gemini, Claude, Copilot, or another model;
    - regenerate evidence;
    - execute a customer assessment;
    - inspect or modify a sealed oracle;
    - label a root cause;
    - assign primary diagnosis;
    - authorize intervention.
    """

    def __init__(
        self,
        *,
        projection_service: (
            GovernanceAssessmentStructuralImportanceProjectionService
            | None
        ) = None,
        classification_service: (
            GovernanceAssessmentStructuralImportanceClassificationService
            | None
        ) = None,
    ) -> None:
        self._projection_service = (
            projection_service
            or
            GovernanceAssessmentStructuralImportanceProjectionService()
        )

        self._classification_service = (
            classification_service
            or
            GovernanceAssessmentStructuralImportanceClassificationService()
        )

    def replay(
        self,
        *,
        benchmark_directory: str | Path,
    ) -> PreliveStructuralImportanceReplayResult:
        directory = Path(
            benchmark_directory
        )

        if not directory.is_dir():
            raise (
                PreliveStructuralImportanceReplayError(
                    "Benchmark directory does not exist: "
                    f"{directory}"
                )
            )

        summary_path = (
            directory
            / "benchmark_summary.json"
        )

        benchmark = self._read_json(
            summary_path
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
                PreliveStructuralImportanceReplayError(
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
                PreliveStructuralImportanceReplayError(
                    "Structural projection hierarchy "
                    "does not match benchmark hierarchy."
                )
            )

        if (
            projection.repository_chain_valid
            is not True
        ):
            raise (
                PreliveStructuralImportanceReplayError(
                    "Structural projection did not "
                    "preserve repository chain validity."
                )
            )

        if (
            projection.diagnostic_integrity_verified
            is not True
        ):
            raise (
                PreliveStructuralImportanceReplayError(
                    "Structural projection did not "
                    "verify persisted diagnostic integrity."
                )
            )

        classification = (
            self._classification_service.classify(
                structural_summary=(
                    projection
                    .structural_summary
                )
            )
        )

        if (
            classification.hierarchy_key
            != hierarchy_key
        ):
            raise (
                PreliveStructuralImportanceReplayError(
                    "Structural classification hierarchy "
                    "does not match benchmark hierarchy."
                )
            )

        replay_payload = {
            "status":
                PRELIVE_STRUCTURAL_REPLAY_STATUS,
            "authority":
                PRELIVE_STRUCTURAL_REPLAY_AUTHORITY,
            "version":
                PRELIVE_STRUCTURAL_REPLAY_VERSION,

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

            "structural_projection_hash":
                projection
                .structural_summary
                .summary_hash,

            "structural_classification_hash":
                classification
                .summary_hash,

            "high_conditions":
                list(
                    classification
                    .high_importance_conditions
                ),

            "moderate_conditions":
                list(
                    classification
                    .moderate_importance_conditions
                ),

            "low_conditions":
                list(
                    classification
                    .low_importance_conditions
                ),

            "limited_conditions":
                list(
                    classification
                    .limited_evidence_conditions
                ),

            "repository_chain_valid":
                projection
                .repository_chain_valid,

            "diagnostic_integrity_verified":
                projection
                .diagnostic_integrity_verified,
        }

        replay_hash = sha256_text(
            canonical_json(
                replay_payload
            )
        )

        result = (
            PreliveStructuralImportanceReplayResult(
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
                classification=(
                    classification
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
        result: PreliveStructuralImportanceReplayResult,
    ) -> Path:
        directory = Path(
            benchmark_directory
        )

        output_path = (
            directory
            / STRUCTURAL_REPLAY_FILENAME
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
                    PreliveStructuralImportanceReplayError(
                        "Existing structural importance "
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
                PreliveStructuralImportanceReplayError(
                    "Benchmark hierarchy_key must contain "
                    "tenant/client/engagement/assessment."
                )
            )

        return CommercialHierarchyContext(
            tenant_id=parts[0].strip(),
            client_id=parts[1].strip(),
            engagement_id=parts[2].strip(),
            assessment_id=parts[3].strip(),
        )

    def _read_json(
        self,
        path: Path,
    ) -> Mapping[str, Any]:
        if not path.is_file():
            raise (
                PreliveStructuralImportanceReplayError(
                    f"Required replay input does not exist: {path}"
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
                PreliveStructuralImportanceReplayError(
                    f"Unable to read replay input: {path}"
                )
            ) from exc

        if not isinstance(
            value,
            Mapping,
        ):
            raise (
                PreliveStructuralImportanceReplayError(
                    f"Replay input must be a JSON object: {path}"
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
                PreliveStructuralImportanceReplayError(
                    f"{field_name} must be a non-empty string."
                )
            )

        return value.strip()