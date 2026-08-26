from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from backend.app.gagf.governance_assessment_diagnostic_projection import (
    GovernanceAssessmentDiagnosticProjectionResult,
    GovernanceAssessmentDiagnosticProjectionService,
)
from backend.app.gagf.governance_assessment_diagnostic_scope import (
    AssessmentDiagnosticScopeSummary,
    GovernanceAssessmentDiagnosticScopeService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
    PreliveValidationResult,
    canonical_sha256,
    validate_pre_live_scenario,
)
from backend.app.gagf.prelive_systemic_diagnostic_replay_scoring import (
    PreliveSystemicDiagnosticReplayResult,
    PreliveSystemicDiagnosticReplayScoringService,
)


PRELIVE_MULTIMODEL_BENCHMARK_VERSION = "1.0.0"

PRELIVE_MULTIMODEL_BENCHMARK_STATUS = (
    "multimodel_diagnostic_benchmark_complete"
)

PRELIVE_MULTIMODEL_BENCHMARK_AUTHORITY = (
    "GAGF_FIP_ONLY"
)

BENCHMARK_DATABASE_FILENAME = (
    "diagnostic_benchmark.sqlite3"
)


@dataclass(
    frozen=True,
    slots=True,
)
class PreliveMultimodelDiagnosticBenchmarkResult:
    model_label: str
    scenario_id: str
    scenario_sha256: str

    hierarchy_key: str

    source_database_path: str
    benchmark_database_path: str
    output_directory: str

    projection: GovernanceAssessmentDiagnosticProjectionResult
    scope: AssessmentDiagnosticScopeSummary
    scoring: PreliveSystemicDiagnosticReplayResult

    benchmark_hash: str

    benchmark_status: str = (
        PRELIVE_MULTIMODEL_BENCHMARK_STATUS
    )

    authority: str = (
        PRELIVE_MULTIMODEL_BENCHMARK_AUTHORITY
    )

    benchmark_version: str = (
        PRELIVE_MULTIMODEL_BENCHMARK_VERSION
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "benchmark_status":
                self.benchmark_status,
            "authority":
                self.authority,
            "benchmark_version":
                self.benchmark_version,
            "model_label":
                self.model_label,
            "scenario_id":
                self.scenario_id,
            "scenario_sha256":
                self.scenario_sha256,
            "hierarchy_key":
                self.hierarchy_key,
            "source_database_path":
                self.source_database_path,
            "benchmark_database_path":
                self.benchmark_database_path,
            "output_directory":
                self.output_directory,
            "projection":
                self.projection.to_dict(),
            "scope":
                self.scope.to_dict(),
            "scoring":
                self.scoring.to_dict(),
            "benchmark_hash":
                self.benchmark_hash,
        }


class PreliveMultimodelDiagnosticBenchmarkService:
    """
    Run the frozen PRELIVE diagnostic benchmark stack against a
    completed blind-assessment database.

    The original assessment database is never modified.

    Benchmark order:

    1. Validate the original blind scenario.
    2. Verify oracle/scenario binding.
    3. Verify external model identity.
    4. Derive the same commercial hierarchy used by PRELIVE.
    5. Copy the original assessment database.
    6. Project diagnostic significance into the copy.
    7. Classify diagnostic scope.
    8. Score systemic conditions against the sealed oracle.
    9. Write deterministic benchmark artifacts.

    This service does not execute an assessment and grants no
    execution or intervention authority.
    """

    def __init__(
        self,
        *,
        projection_service: (
            GovernanceAssessmentDiagnosticProjectionService
            | None
        ) = None,
        scope_service: (
            GovernanceAssessmentDiagnosticScopeService
            | None
        ) = None,
        scoring_service: (
            PreliveSystemicDiagnosticReplayScoringService
            | None
        ) = None,
        validator: Callable[
            [Any],
            PreliveValidationResult,
        ] = validate_pre_live_scenario,
    ) -> None:
        self._projection_service = (
            projection_service
            or GovernanceAssessmentDiagnosticProjectionService()
        )

        self._scope_service = (
            scope_service
            or GovernanceAssessmentDiagnosticScopeService()
        )

        self._scoring_service = (
            scoring_service
            or PreliveSystemicDiagnosticReplayScoringService()
        )

        self._validator = validator

    def benchmark(
        self,
        *,
        scenario: Mapping[str, Any],
        oracle: Mapping[str, Any],
        source_database_path: str | Path,
        output_directory: str | Path,
        model_label: str,
    ) -> PreliveMultimodelDiagnosticBenchmarkResult:
        if (
            not isinstance(
                model_label,
                str,
            )
            or not model_label.strip()
        ):
            raise PreliveScenarioError(
                "PRELIVE benchmark model_label "
                "must not be empty."
            )

        scenario_dict = dict(
            scenario
        )

        oracle_dict = dict(
            oracle
        )

        validation = self._validator(
            scenario_dict
        )

        if not validation.valid:
            messages = "; ".join(
                issue.message
                for issue
                in validation.issues
            )

            raise PreliveScenarioError(
                "PRELIVE benchmark scenario "
                f"validation failed: {messages}"
            )

        if (
            validation.scenario_sha256
            is None
        ):
            raise PreliveScenarioError(
                "PRELIVE benchmark scenario "
                "did not produce a SHA-256."
            )

        scenario_id = str(
            scenario_dict.get(
                "scenario_id",
                "",
            )
        ).strip()

        if not scenario_id:
            raise PreliveScenarioError(
                "PRELIVE benchmark requires "
                "scenario_id."
            )

        self._validate_generator(
            scenario=scenario_dict,
            model_label=model_label.strip(),
        )

        self._validate_oracle_binding(
            oracle=oracle_dict,
            scenario_id=scenario_id,
            scenario_sha256=(
                validation.scenario_sha256
            ),
        )

        source_path = Path(
            source_database_path
        )

        if not source_path.is_file():
            raise PreliveScenarioError(
                "PRELIVE benchmark source database "
                f"does not exist: {source_path}"
            )

        output_path = Path(
            output_directory
        )

        self._prepare_output_directory(
            output_path
        )

        benchmark_database_path = (
            output_path
            / BENCHMARK_DATABASE_FILENAME
        )

        shutil.copy2(
            source_path,
            benchmark_database_path,
        )

        context = self._build_context(
            scenario=scenario_dict,
        )

        projection = (
            self._projection_service
            .project(
                database_path=(
                    benchmark_database_path
                ),
                context=context,
            )
        )

        scope = (
            self._scope_service
            .classify(
                significance_summary=(
                    projection
                    .diagnostic_summary
                ),
            )
        )

        scoring = (
            self._scoring_service
            .score(
                scope_summary=scope,
                oracle=oracle_dict,
            )
        )

        if (
            projection.hierarchy_key
            != context.hierarchy_key
        ):
            raise PreliveScenarioError(
                "Diagnostic projection hierarchy "
                "does not match benchmark context."
            )

        if (
            scope.hierarchy_key
            != context.hierarchy_key
        ):
            raise PreliveScenarioError(
                "Diagnostic scope hierarchy "
                "does not match benchmark context."
            )

        if (
            scoring.hierarchy_key
            != context.hierarchy_key
        ):
            raise PreliveScenarioError(
                "Systemic scoring hierarchy "
                "does not match benchmark context."
            )

        benchmark_payload = {
            "benchmark_status":
                PRELIVE_MULTIMODEL_BENCHMARK_STATUS,
            "authority":
                PRELIVE_MULTIMODEL_BENCHMARK_AUTHORITY,
            "benchmark_version":
                PRELIVE_MULTIMODEL_BENCHMARK_VERSION,
            "model_label":
                model_label.strip(),
            "scenario_id":
                scenario_id,
            "scenario_sha256":
                validation.scenario_sha256,
            "hierarchy_key":
                context.hierarchy_key,
            "projection_hash":
                projection
                .diagnostic_summary
                .summary_hash,
            "scope_hash":
                scope.scope_hash,
            "systemic_replay_hash":
                scoring.replay_hash,
            "systemic_conditions":
                list(
                    scoring
                    .systemic_conditions
                ),
            "precision":
                scoring.precision,
            "recall":
                scoring.recall,
            "f1":
                scoring.f1,
            "exact_condition_match":
                scoring
                .exact_condition_match,
            "dominant_constraint_match":
                scoring
                .dominant_constraint_match,
        }

        benchmark_hash = canonical_sha256(
            benchmark_payload
        )

        result = (
            PreliveMultimodelDiagnosticBenchmarkResult(
                model_label=(
                    model_label.strip()
                ),
                scenario_id=(
                    scenario_id
                ),
                scenario_sha256=(
                    validation
                    .scenario_sha256
                ),
                hierarchy_key=(
                    context.hierarchy_key
                ),
                source_database_path=str(
                    source_path
                ),
                benchmark_database_path=str(
                    benchmark_database_path
                ),
                output_directory=str(
                    output_path
                ),
                projection=projection,
                scope=scope,
                scoring=scoring,
                benchmark_hash=(
                    benchmark_hash
                ),
            )
        )

        self._write_outputs(
            output_path=output_path,
            result=result,
        )

        return result

    def _validate_generator(
        self,
        *,
        scenario: Mapping[str, Any],
        model_label: str,
    ) -> None:
        generator = scenario.get(
            "generator"
        )

        if not isinstance(
            generator,
            Mapping,
        ):
            raise PreliveScenarioError(
                "PRELIVE benchmark scenario "
                "generator is invalid."
            )

        generated_by = generator.get(
            "model_label"
        )

        if (
            not isinstance(
                generated_by,
                str,
            )
            or generated_by.strip()
            != model_label
        ):
            raise PreliveScenarioError(
                "PRELIVE benchmark model_label "
                "does not match scenario generator."
            )

    def _validate_oracle_binding(
        self,
        *,
        oracle: Mapping[str, Any],
        scenario_id: str,
        scenario_sha256: str,
    ) -> None:
        oracle_scenario_id = oracle.get(
            "scenario_id"
        )

        if (
            not isinstance(
                oracle_scenario_id,
                str,
            )
            or oracle_scenario_id.strip()
            != scenario_id
        ):
            raise PreliveScenarioError(
                "PRELIVE benchmark oracle "
                "scenario_id does not match "
                "the blind scenario."
            )

        oracle_scenario_sha256 = (
            oracle.get(
                "scenario_sha256"
            )
        )

        if (
            not isinstance(
                oracle_scenario_sha256,
                str,
            )
            or oracle_scenario_sha256
            != scenario_sha256
        ):
            raise PreliveScenarioError(
                "PRELIVE benchmark oracle "
                "scenario_sha256 does not match "
                "the blind scenario."
            )

    def _build_context(
        self,
        *,
        scenario: Mapping[str, Any],
    ) -> CommercialHierarchyContext:
        events = scenario.get(
            "events"
        )

        if not isinstance(
            events,
            list,
        ):
            raise PreliveScenarioError(
                "PRELIVE benchmark scenario "
                "events are required."
            )

        tenants = {
            str(
                event["tenant_id"]
            ).strip()
            for event
            in events
            if (
                isinstance(
                    event,
                    Mapping,
                )
                and isinstance(
                    event.get(
                        "tenant_id"
                    ),
                    str,
                )
                and event[
                    "tenant_id"
                ].strip()
            )
        }

        if len(
            tenants
        ) != 1:
            raise PreliveScenarioError(
                "PRELIVE benchmark requires "
                "exactly one tenant."
            )

        scenario_id = str(
            scenario[
                "scenario_id"
            ]
        ).strip()

        safe_scenario_id = (
            scenario_id
            .lower()
            .replace(
                " ",
                "-",
            )
        )

        return CommercialHierarchyContext(
            tenant_id=next(
                iter(
                    tenants
                )
            ),
            client_id=(
                "prelive-client"
            ),
            engagement_id=(
                f"prelive-"
                f"{safe_scenario_id}"
            ),
            assessment_id=(
                f"assessment-"
                f"{safe_scenario_id}"
            ),
        )

    def _prepare_output_directory(
        self,
        output_path: Path,
    ) -> None:
        if output_path.exists():
            existing = tuple(
                output_path.iterdir()
            )

            if existing:
                raise PreliveScenarioError(
                    "PRELIVE benchmark output "
                    "directory must be empty."
                )
        else:
            output_path.mkdir(
                parents=True,
                exist_ok=False,
            )

    def _write_outputs(
        self,
        *,
        output_path: Path,
        result: PreliveMultimodelDiagnosticBenchmarkResult,
    ) -> None:
        self._write_json(
            output_path
            / "diagnostic_projection.json",
            result.projection.to_dict(),
        )

        self._write_json(
            output_path
            / "diagnostic_scope.json",
            result.scope.to_dict(),
        )

        self._write_json(
            output_path
            / "systemic_scoring.json",
            result.scoring.to_dict(),
        )

        self._write_json(
            output_path
            / "benchmark_summary.json",
            result.to_dict(),
        )

    def _write_json(
        self,
        path: Path,
        payload: Mapping[str, Any],
    ) -> None:
        path.write_text(
            json.dumps(
                dict(
                    payload
                ),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )