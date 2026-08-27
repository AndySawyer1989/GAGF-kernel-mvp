from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from backend.app.gagf.prelive_multimodel_structural_importance_replay import (
    PRELIVE_STRUCTURAL_REPLAY_AUTHORITY,
    PRELIVE_STRUCTURAL_REPLAY_STATUS,
    PRELIVE_STRUCTURAL_REPLAY_VERSION,
    STRUCTURAL_REPLAY_FILENAME,
    PreliveMultimodelStructuralImportanceReplayService,
    PreliveStructuralImportanceReplayError,
)


HIERARCHY_KEY = (
    "tenant-a/"
    "client-a/"
    "engagement-a/"
    "assessment-a"
)


class FakeStructuralSummary:
    hierarchy_key = HIERARCHY_KEY
    summary_hash = "structural-summary-hash"


class FakeProjectionResult:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
        chain_valid=True,
        diagnostic_verified=True,
    ):
        self.hierarchy_key = (
            hierarchy_key
        )

        self.repository_chain_valid = (
            chain_valid
        )

        self.diagnostic_integrity_verified = (
            diagnostic_verified
        )

        self.structural_summary = (
            FakeStructuralSummary()
        )

        self.artifact_id = (
            "structural-artifact"
        )

        self.artifact_hash = (
            "structural-artifact-hash"
        )

        self.sequence_number = 4

        self.reused_existing = False

        self.projection_version = "1.0.0"

    def to_dict(
        self,
    ):
        return {
            "hierarchy_key":
                self.hierarchy_key,
            "structural_summary_hash":
                self.structural_summary.summary_hash,
            "condition_count":
                4,
            "artifact_id":
                self.artifact_id,
            "artifact_hash":
                self.artifact_hash,
            "sequence_number":
                self.sequence_number,
            "repository_chain_valid":
                self.repository_chain_valid,
            "reused_existing":
                self.reused_existing,
            "diagnostic_integrity_verified":
                self.diagnostic_integrity_verified,
            "projection_version":
                self.projection_version,
        }


class FakeProjectionService:
    def __init__(
        self,
        result=None,
    ):
        self.result = (
            result
            or FakeProjectionResult()
        )

        self.calls = []

    def project(
        self,
        *,
        database_path,
        context,
    ):
        self.calls.append(
            (
                database_path,
                context,
            )
        )

        return self.result


class FakeClassificationSummary:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
    ):
        self._hierarchy_key = (
            hierarchy_key
        )

        self.summary_hash = (
            "classification-summary-hash"
        )

        self.high_importance_conditions = (
            "APPROVAL_DELAYED",
        )

        self.moderate_importance_conditions = (
            "SECURITY_REVIEW",
        )

        self.low_importance_conditions = (
            "OWNERSHIP_GAP",
        )

        self.limited_evidence_conditions = (
            "OVERRIDE",
        )

    @property
    def hierarchy_key(
        self,
    ):
        return self._hierarchy_key

    def to_dict(
        self,
    ):
        return {
            "hierarchy_key":
                self.hierarchy_key,
            "high_importance_conditions":
                list(
                    self.high_importance_conditions
                ),
            "moderate_importance_conditions":
                list(
                    self.moderate_importance_conditions
                ),
            "low_importance_conditions":
                list(
                    self.low_importance_conditions
                ),
            "limited_evidence_conditions":
                list(
                    self.limited_evidence_conditions
                ),
            "summary_hash":
                self.summary_hash,
            "authority":
                "GAGF_FIP_ONLY",
            "schema_version":
                "1.0.0",
            "conditions": [],
        }


class FakeClassificationService:
    def __init__(
        self,
        result=None,
    ):
        self.result = (
            result
            or FakeClassificationSummary()
        )

        self.calls = []

    def classify(
        self,
        *,
        structural_summary,
    ):
        self.calls.append(
            structural_summary
        )

        return self.result


def write_json(
    path,
    payload,
):
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def build_benchmark_directory(
    tmp_path,
):
    directory = (
        tmp_path
        / "benchmark"
    )

    directory.mkdir()

    database = (
        directory
        / "diagnostic_benchmark.sqlite3"
    )

    database.write_bytes(
        b"test-database"
    )

    write_json(
        directory
        / "benchmark_summary.json",
        {
            "model_label":
                "claude",
            "scenario_id":
                "scenario-001",
            "scenario_sha256":
                "a" * 64,
            "hierarchy_key":
                HIERARCHY_KEY,
            "benchmark_database_path":
                str(
                    database
                ),
            "benchmark_hash":
                "b" * 64,
        },
    )

    return (
        directory,
        database,
    )


def build_service(
    *,
    projection_result=None,
    classification_result=None,
):
    projection = (
        FakeProjectionService(
            projection_result
        )
    )

    classification = (
        FakeClassificationService(
            classification_result
        )
    )

    service = (
        PreliveMultimodelStructuralImportanceReplayService(
            projection_service=(
                projection
            ),
            classification_service=(
                classification
            ),
        )
    )

    return (
        service,
        projection,
        classification,
    )


def test_replay_runs_structural_projection(
    tmp_path,
):
    directory, database = (
        build_benchmark_directory(
            tmp_path
        )
    )

    service, projection, _ = (
        build_service()
    )

    result = service.replay(
        benchmark_directory=(
            directory
        )
    )

    assert (
        len(
            projection.calls
        )
        == 1
    )

    called_database, context = (
        projection.calls[0]
    )

    assert (
        called_database
        == database
    )

    assert (
        context.hierarchy_key
        == HIERARCHY_KEY
    )

    assert (
        result.hierarchy_key
        == HIERARCHY_KEY
    )


def test_replay_runs_frozen_classifier(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    service, _, classification = (
        build_service()
    )

    result = service.replay(
        benchmark_directory=(
            directory
        )
    )

    assert (
        classification.calls
        == [
            result.projection
            .structural_summary
        ]
    )


def test_replay_preserves_four_levels(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    service, _, _ = (
        build_service()
    )

    result = service.replay(
        benchmark_directory=(
            directory
        )
    )

    assert (
        result.high_conditions
        == (
            "APPROVAL_DELAYED",
        )
    )

    assert (
        result.moderate_conditions
        == (
            "SECURITY_REVIEW",
        )
    )

    assert (
        result.low_conditions
        == (
            "OWNERSHIP_GAP",
        )
    )

    assert (
        result.limited_conditions
        == (
            "OVERRIDE",
        )
    )


def test_replay_binds_source_benchmark_hash(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    service, _, _ = (
        build_service()
    )

    result = service.replay(
        benchmark_directory=(
            directory
        )
    )

    assert (
        result.source_benchmark_hash
        == "b" * 64
    )


def test_replay_writes_receipt(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    service, _, _ = (
        build_service()
    )

    result = service.replay(
        benchmark_directory=(
            directory
        )
    )

    receipt_path = (
        directory
        / STRUCTURAL_REPLAY_FILENAME
    )

    assert (
        receipt_path.is_file()
    )

    payload = json.loads(
        receipt_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        payload[
            "replay_hash"
        ]
        == result.replay_hash
    )


def test_replay_is_deterministic(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    service, _, _ = (
        build_service()
    )

    first = service.replay(
        benchmark_directory=(
            directory
        )
    )

    second = service.replay(
        benchmark_directory=(
            directory
        )
    )

    assert (
        first.replay_hash
        == second.replay_hash
    )

    assert (
        first.to_dict()
        == second.to_dict()
    )


def test_replay_reuses_identical_receipt(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    service, _, _ = (
        build_service()
    )

    first = service.replay(
        benchmark_directory=(
            directory
        )
    )

    receipt_path = (
        directory
        / STRUCTURAL_REPLAY_FILENAME
    )

    first_text = (
        receipt_path.read_text(
            encoding="utf-8"
        )
    )

    second = service.replay(
        benchmark_directory=(
            directory
        )
    )

    second_text = (
        receipt_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        first.replay_hash
        == second.replay_hash
    )

    assert (
        first_text
        == second_text
    )


def test_replay_rejects_receipt_drift(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    service, _, _ = (
        build_service()
    )

    service.replay(
        benchmark_directory=(
            directory
        )
    )

    write_json(
        directory
        / STRUCTURAL_REPLAY_FILENAME,
        {
            "replay_hash":
                "tampered",
        },
    )

    with pytest.raises(
        PreliveStructuralImportanceReplayError,
        match=(
            "does not match deterministic replay"
        ),
    ):
        service.replay(
            benchmark_directory=(
                directory
            )
        )


def test_rejects_missing_benchmark_directory(
    tmp_path,
):
    service, _, _ = (
        build_service()
    )

    with pytest.raises(
        PreliveStructuralImportanceReplayError,
        match=(
            "Benchmark directory does not exist"
        ),
    ):
        service.replay(
            benchmark_directory=(
                tmp_path
                / "missing"
            )
        )


def test_rejects_missing_summary(
    tmp_path,
):
    directory = (
        tmp_path
        / "benchmark"
    )

    directory.mkdir()

    service, _, _ = (
        build_service()
    )

    with pytest.raises(
        PreliveStructuralImportanceReplayError,
        match=(
            "Required replay input does not exist"
        ),
    ):
        service.replay(
            benchmark_directory=(
                directory
            )
        )


def test_rejects_missing_benchmark_database(
    tmp_path,
):
    directory = (
        tmp_path
        / "benchmark"
    )

    directory.mkdir()

    missing_database = (
        directory
        / "missing.sqlite3"
    )

    write_json(
        directory
        / "benchmark_summary.json",
        {
            "model_label":
                "gemini",
            "scenario_id":
                "scenario-001",
            "scenario_sha256":
                "a" * 64,
            "hierarchy_key":
                HIERARCHY_KEY,
            "benchmark_database_path":
                str(
                    missing_database
                ),
            "benchmark_hash":
                "b" * 64,
        },
    )

    service, _, _ = (
        build_service()
    )

    with pytest.raises(
        PreliveStructuralImportanceReplayError,
        match=(
            "Benchmark database does not exist"
        ),
    ):
        service.replay(
            benchmark_directory=(
                directory
            )
        )


def test_rejects_invalid_hierarchy_shape(
    tmp_path,
):
    directory, database = (
        build_benchmark_directory(
            tmp_path
        )
    )

    write_json(
        directory
        / "benchmark_summary.json",
        {
            "model_label":
                "copilot",
            "scenario_id":
                "scenario-001",
            "scenario_sha256":
                "a" * 64,
            "hierarchy_key":
                "invalid/hierarchy",
            "benchmark_database_path":
                str(
                    database
                ),
            "benchmark_hash":
                "b" * 64,
        },
    )

    service, _, _ = (
        build_service()
    )

    with pytest.raises(
        PreliveStructuralImportanceReplayError,
        match=(
            "tenant/client/engagement/assessment"
        ),
    ):
        service.replay(
            benchmark_directory=(
                directory
            )
        )


def test_rejects_projection_hierarchy_mismatch(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    projection_result = (
        FakeProjectionResult(
            hierarchy_key=(
                "wrong/hierarchy/key/value"
            )
        )
    )

    service, _, _ = (
        build_service(
            projection_result=(
                projection_result
            )
        )
    )

    with pytest.raises(
        PreliveStructuralImportanceReplayError,
        match=(
            "Structural projection hierarchy"
        ),
    ):
        service.replay(
            benchmark_directory=(
                directory
            )
        )


def test_rejects_invalid_repository_chain(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    projection_result = (
        FakeProjectionResult(
            chain_valid=False
        )
    )

    service, _, _ = (
        build_service(
            projection_result=(
                projection_result
            )
        )
    )

    with pytest.raises(
        PreliveStructuralImportanceReplayError,
        match=(
            "repository chain validity"
        ),
    ):
        service.replay(
            benchmark_directory=(
                directory
            )
        )


def test_requires_diagnostic_integrity_verification(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    projection_result = (
        FakeProjectionResult(
            diagnostic_verified=False
        )
    )

    service, _, _ = (
        build_service(
            projection_result=(
                projection_result
            )
        )
    )

    with pytest.raises(
        PreliveStructuralImportanceReplayError,
        match=(
            "persisted diagnostic integrity"
        ),
    ):
        service.replay(
            benchmark_directory=(
                directory
            )
        )


def test_rejects_classification_hierarchy_mismatch(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    classification_result = (
        FakeClassificationSummary(
            hierarchy_key=(
                "wrong/hierarchy/key/value"
            )
        )
    )

    service, _, _ = (
        build_service(
            classification_result=(
                classification_result
            )
        )
    )

    with pytest.raises(
        PreliveStructuralImportanceReplayError,
        match=(
            "Structural classification hierarchy"
        ),
    ):
        service.replay(
            benchmark_directory=(
                directory
            )
        )


def test_result_preserves_governance_boundary(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    service, _, _ = (
        build_service()
    )

    result = service.replay(
        benchmark_directory=(
            directory
        )
    )

    payload = result.to_dict()

    assert (
        payload[
            "authority"
        ]
        == PRELIVE_STRUCTURAL_REPLAY_AUTHORITY
    )

    assert (
        payload[
            "status"
        ]
        == PRELIVE_STRUCTURAL_REPLAY_STATUS
    )

    assert (
        payload[
            "version"
        ]
        == PRELIVE_STRUCTURAL_REPLAY_VERSION
    )

    assert (
        "oracle"
        not in payload
    )

    assert (
        "root_cause"
        not in payload
    )

    assert (
        "primary_condition"
        not in payload
    )

    assert (
        "intervention"
        not in payload
    )