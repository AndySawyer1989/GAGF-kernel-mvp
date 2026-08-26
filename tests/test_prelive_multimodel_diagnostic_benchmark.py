from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from backend.app.gagf.prelive_multimodel_diagnostic_benchmark import (
    BENCHMARK_DATABASE_FILENAME,
    PRELIVE_MULTIMODEL_BENCHMARK_AUTHORITY,
    PRELIVE_MULTIMODEL_BENCHMARK_STATUS,
    PreliveMultimodelDiagnosticBenchmarkService,
)


SCENARIO_HASH = (
    "a" * 64
)


def scenario(
    *,
    model_label: str = "Claude",
) -> dict:
    return {
        "schema_version":
            "1.0",
        "test_program":
            "PRELIVE-001",
        "scenario_id":
            "PRELIVE-001-CLAUDE-001",
        "generator": {
            "type":
                "external_ai",
            "model_label":
                model_label,
        },
        "organization": {
            "name":
                "Synthetic Claude Organization",
        },
        "events": [
            {
                "tenant_id":
                    "synthetic-claude-tenant",
            },
            {
                "tenant_id":
                    "synthetic-claude-tenant",
            },
        ],
    }


def oracle() -> dict:
    return {
        "schema_version":
            "1.0",
        "test_program":
            "PRELIVE-001",
        "oracle_status":
            "SEALED",
        "scenario_id":
            "PRELIVE-001-CLAUDE-001",
        "scenario_sha256":
            SCENARIO_HASH,
        "expected_conditions": [
            {
                "constraint_type":
                    "SECURITY_REVIEW",
            },
        ],
        "expected_dominant_constraint":
            "SECURITY_REVIEW",
    }


class FakeValidator:
    def __call__(
        self,
        value,
    ):
        return SimpleNamespace(
            valid=True,
            issues=(),
            scenario_sha256=(
                SCENARIO_HASH
            ),
        )


class InvalidValidator:
    def __call__(
        self,
        value,
    ):
        return SimpleNamespace(
            valid=False,
            issues=(
                SimpleNamespace(
                    message=(
                        "invalid scenario"
                    )
                ),
            ),
            scenario_sha256=None,
        )


class FakeProjectionResult:
    hierarchy_key = (
        "synthetic-claude-tenant/"
        "prelive-client/"
        "prelive-prelive-001-claude-001/"
        "assessment-prelive-001-claude-001"
    )

    diagnostic_summary = (
        SimpleNamespace(
            summary_hash=(
                "b" * 64
            )
        )
    )

    def to_dict(
        self,
    ):
        return {
            "hierarchy_key":
                self.hierarchy_key,
            "diagnostic_summary_hash":
                "b" * 64,
        }


class FakeProjectionService:
    def __init__(
        self,
    ):
        self.calls = []

    def project(
        self,
        *,
        database_path,
        context,
    ):
        self.calls.append(
            (
                Path(
                    database_path
                ),
                context,
            )
        )

        return (
            FakeProjectionResult()
        )


class FakeScopeSummary:
    hierarchy_key = (
        FakeProjectionResult
        .hierarchy_key
    )

    scope_hash = (
        "c" * 64
    )

    systemic_conditions = (
        "SECURITY_REVIEW",
    )

    dominant_systemic_condition = (
        "SECURITY_REVIEW"
    )

    def to_dict(
        self,
    ):
        return {
            "hierarchy_key":
                self.hierarchy_key,
            "scope_hash":
                self.scope_hash,
            "systemic_conditions": [
                "SECURITY_REVIEW"
            ],
            "dominant_systemic_condition":
                "SECURITY_REVIEW",
        }


class FakeScopeService:
    def __init__(
        self,
    ):
        self.calls = []

    def classify(
        self,
        *,
        significance_summary,
    ):
        self.calls.append(
            significance_summary
        )

        return FakeScopeSummary()


class FakeScoringResult:
    hierarchy_key = (
        FakeProjectionResult
        .hierarchy_key
    )

    systemic_conditions = (
        "SECURITY_REVIEW",
    )

    precision = 1.0
    recall = 1.0
    f1 = 1.0

    exact_condition_match = True
    dominant_constraint_match = True

    replay_hash = (
        "d" * 64
    )

    def to_dict(
        self,
    ):
        return {
            "hierarchy_key":
                self.hierarchy_key,
            "systemic_conditions": [
                "SECURITY_REVIEW"
            ],
            "precision":
                1.0,
            "recall":
                1.0,
            "f1":
                1.0,
            "exact_condition_match":
                True,
            "dominant_constraint_match":
                True,
            "replay_hash":
                self.replay_hash,
        }


class FakeScoringService:
    def __init__(
        self,
    ):
        self.calls = []

    def score(
        self,
        *,
        scope_summary,
        oracle,
    ):
        self.calls.append(
            (
                scope_summary,
                oracle,
            )
        )

        return FakeScoringResult()


def service(
    *,
    validator=None,
):
    return (
        PreliveMultimodelDiagnosticBenchmarkService(
            projection_service=(
                FakeProjectionService()
            ),
            scope_service=(
                FakeScopeService()
            ),
            scoring_service=(
                FakeScoringService()
            ),
            validator=(
                validator
                or FakeValidator()
            ),
        )
    )


def source_database(
    tmp_path: Path,
) -> Path:
    path = (
        tmp_path
        / "prelive.sqlite3"
    )

    path.write_bytes(
        b"original-database"
    )

    return path


def test_benchmark_copies_source_database(
    tmp_path,
):
    source = source_database(
        tmp_path
    )

    output = (
        tmp_path
        / "benchmark"
    )

    result = service().benchmark(
        scenario=scenario(),
        oracle=oracle(),
        source_database_path=source,
        output_directory=output,
        model_label="Claude",
    )

    copied = (
        output
        / BENCHMARK_DATABASE_FILENAME
    )

    assert copied.is_file()

    assert (
        copied.read_bytes()
        == source.read_bytes()
    )

    assert (
        result.benchmark_database_path
        == str(
            copied
        )
    )


def test_original_database_is_not_modified(
    tmp_path,
):
    source = source_database(
        tmp_path
    )

    before = source.read_bytes()

    service().benchmark(
        scenario=scenario(),
        oracle=oracle(),
        source_database_path=source,
        output_directory=(
            tmp_path
            / "benchmark"
        ),
        model_label="Claude",
    )

    assert (
        source.read_bytes()
        == before
    )


def test_context_matches_prelive_runner_convention(
    tmp_path,
):
    benchmark_service = service()

    result = benchmark_service.benchmark(
        scenario=scenario(),
        oracle=oracle(),
        source_database_path=(
            source_database(
                tmp_path
            )
        ),
        output_directory=(
            tmp_path
            / "benchmark"
        ),
        model_label="Claude",
    )

    assert (
        result.hierarchy_key
        == (
            "synthetic-claude-tenant/"
            "prelive-client/"
            "prelive-prelive-001-claude-001/"
            "assessment-prelive-001-claude-001"
        )
    )


def test_writes_benchmark_artifacts(
    tmp_path,
):
    output = (
        tmp_path
        / "benchmark"
    )

    service().benchmark(
        scenario=scenario(),
        oracle=oracle(),
        source_database_path=(
            source_database(
                tmp_path
            )
        ),
        output_directory=output,
        model_label="Claude",
    )

    assert (
        output
        / "diagnostic_projection.json"
    ).is_file()

    assert (
        output
        / "diagnostic_scope.json"
    ).is_file()

    assert (
        output
        / "systemic_scoring.json"
    ).is_file()

    assert (
        output
        / "benchmark_summary.json"
    ).is_file()


def test_rejects_missing_source_database(
    tmp_path,
):
    with pytest.raises(
        PreliveScenarioError,
        match="does not exist",
    ):
        service().benchmark(
            scenario=scenario(),
            oracle=oracle(),
            source_database_path=(
                tmp_path
                / "missing.sqlite3"
            ),
            output_directory=(
                tmp_path
                / "benchmark"
            ),
            model_label="Claude",
        )


def test_rejects_nonempty_output_directory(
    tmp_path,
):
    output = (
        tmp_path
        / "benchmark"
    )

    output.mkdir()

    (
        output
        / "existing.txt"
    ).write_text(
        "existing",
        encoding="utf-8",
    )

    with pytest.raises(
        PreliveScenarioError,
        match="must be empty",
    ):
        service().benchmark(
            scenario=scenario(),
            oracle=oracle(),
            source_database_path=(
                source_database(
                    tmp_path
                )
            ),
            output_directory=output,
            model_label="Claude",
        )


def test_rejects_invalid_scenario(
    tmp_path,
):
    with pytest.raises(
        PreliveScenarioError,
        match="validation failed",
    ):
        service(
            validator=(
                InvalidValidator()
            )
        ).benchmark(
            scenario=scenario(),
            oracle=oracle(),
            source_database_path=(
                source_database(
                    tmp_path
                )
            ),
            output_directory=(
                tmp_path
                / "benchmark"
            ),
            model_label="Claude",
        )


def test_rejects_model_label_mismatch(
    tmp_path,
):
    with pytest.raises(
        PreliveScenarioError,
        match="model_label",
    ):
        service().benchmark(
            scenario=scenario(
                model_label="Copilot"
            ),
            oracle=oracle(),
            source_database_path=(
                source_database(
                    tmp_path
                )
            ),
            output_directory=(
                tmp_path
                / "benchmark"
            ),
            model_label="Claude",
        )


def test_rejects_oracle_scenario_id_mismatch(
    tmp_path,
):
    bad_oracle = oracle()

    bad_oracle[
        "scenario_id"
    ] = "WRONG"

    with pytest.raises(
        PreliveScenarioError,
        match="scenario_id",
    ):
        service().benchmark(
            scenario=scenario(),
            oracle=bad_oracle,
            source_database_path=(
                source_database(
                    tmp_path
                )
            ),
            output_directory=(
                tmp_path
                / "benchmark"
            ),
            model_label="Claude",
        )


def test_rejects_oracle_hash_mismatch(
    tmp_path,
):
    bad_oracle = oracle()

    bad_oracle[
        "scenario_sha256"
    ] = "e" * 64

    with pytest.raises(
        PreliveScenarioError,
        match="scenario_sha256",
    ):
        service().benchmark(
            scenario=scenario(),
            oracle=bad_oracle,
            source_database_path=(
                source_database(
                    tmp_path
                )
            ),
            output_directory=(
                tmp_path
                / "benchmark"
            ),
            model_label="Claude",
        )


def test_benchmark_hash_is_deterministic(
    tmp_path,
):
    first = service().benchmark(
        scenario=scenario(),
        oracle=oracle(),
        source_database_path=(
            source_database(
                tmp_path
            )
        ),
        output_directory=(
            tmp_path
            / "benchmark-one"
        ),
        model_label="Claude",
    )

    second = service().benchmark(
        scenario=scenario(),
        oracle=oracle(),
        source_database_path=(
            tmp_path
            / "prelive.sqlite3"
        ),
        output_directory=(
            tmp_path
            / "benchmark-two"
        ),
        model_label="Claude",
    )

    assert (
        first.benchmark_hash
        == second.benchmark_hash
    )

    assert len(
        first.benchmark_hash
    ) == 64


def test_result_preserves_governance_boundary(
    tmp_path,
):
    result = service().benchmark(
        scenario=scenario(),
        oracle=oracle(),
        source_database_path=(
            source_database(
                tmp_path
            )
        ),
        output_directory=(
            tmp_path
            / "benchmark"
        ),
        model_label="Claude",
    )

    assert (
        result.benchmark_status
        == PRELIVE_MULTIMODEL_BENCHMARK_STATUS
    )

    assert (
        result.authority
        == PRELIVE_MULTIMODEL_BENCHMARK_AUTHORITY
    )

    assert (
        result.scoring.precision
        == 1.0
    )