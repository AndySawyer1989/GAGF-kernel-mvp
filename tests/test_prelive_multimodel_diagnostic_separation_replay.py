from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from backend.app.gagf.prelive_multimodel_diagnostic_separation_replay import (
    DIAGNOSTIC_SEPARATION_REPLAY_FILENAME,
    PRELIVE_DIAGNOSTIC_SEPARATION_REPLAY_AUTHORITY,
    PreliveDiagnosticSeparationReplayError,
    PreliveMultimodelDiagnosticSeparationReplayService,
)


HIERARCHY_KEY = (
    "tenant-a/client-a/"
    "engagement-a/assessment-a"
)


class FakeMetrics:
    rank_1_score = 0.80
    rank_2_score = 0.60
    rank_3_score = 0.40

    rank_1_to_rank_2_absolute = 0.20
    rank_1_to_rank_2_relative = 0.25

    rank_1_to_rank_3_absolute = 0.40
    rank_1_to_rank_3_relative = 0.50

    top_3_score_spread = 0.40

    def to_dict(
        self,
    ):
        return {
            "rank_1_score":
                self.rank_1_score,
            "rank_2_score":
                self.rank_2_score,
            "rank_3_score":
                self.rank_3_score,
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
        }


class FakeSupport:
    def to_dict(
        self,
    ):
        return {
            "candidate_count":
                3,
            "ranked_candidate_count":
                3,
            "evidence_quality_observed_count":
                3,
            "leading_evidence_quality":
                0.95,
            "runner_up_evidence_quality":
                0.85,
            "leading_structural_level":
                "HIGH",
            "runner_up_structural_level":
                "MODERATE",
        }


class FakeSeparationSummary:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
    ):
        self.hierarchy_key = (
            hierarchy_key
        )

        self.summary_hash = (
            "separation-summary-hash"
        )

        self.primary_diagnosis_summary_hash = (
            "primary-summary-hash"
        )

        self.leading_candidate_category = (
            "APPROVAL_DELAYED"
        )

        self.runner_up_candidate = (
            SimpleNamespace(
                category="SECURITY_REVIEW"
            )
        )

        self.metrics = (
            FakeMetrics()
        )

        self.support = (
            FakeSupport()
        )


class FakeProjectionResult:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
        repository_chain_valid=True,
        primary_projection_verified=True,
        structural_projection_verified=True,
        structural_classification_verified=True,
        reused_existing=False,
    ):
        self.hierarchy_key = (
            hierarchy_key
        )

        self.separation_summary = (
            FakeSeparationSummary(
                hierarchy_key=(
                    hierarchy_key
                )
            )
        )

        self.repository_chain_valid = (
            repository_chain_valid
        )

        self.primary_projection_verified = (
            primary_projection_verified
        )

        self.structural_projection_verified = (
            structural_projection_verified
        )

        self.structural_classification_verified = (
            structural_classification_verified
        )

        self.reused_existing = (
            reused_existing
        )

    def to_dict(
        self,
    ):
        return {
            "hierarchy_key":
                self.hierarchy_key,

            "separation_summary_hash":
                self.separation_summary
                .summary_hash,

            "primary_diagnosis_summary_hash":
                self.separation_summary
                .primary_diagnosis_summary_hash,

            "leading_candidate_category":
                self.separation_summary
                .leading_candidate_category,

            "artifact_id":
                "separation-artifact",

            "artifact_hash":
                "separation-artifact-hash",

            "sequence_number":
                20,

            "repository_chain_valid":
                self.repository_chain_valid,

            "reused_existing":
                self.reused_existing,

            "primary_projection_verified":
                self.primary_projection_verified,

            "structural_projection_verified":
                self.structural_projection_verified,

            "structural_classification_verified":
                self.structural_classification_verified,

            "projection_version":
                "1.0.0",
        }


class FakeProjectionService:
    def __init__(
        self,
        *,
        result=None,
    ):
        self.result = (
            result
            or
            FakeProjectionResult()
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
                str(
                    database_path
                ),
                context.hierarchy_key,
            )
        )

        return (
            self.result
        )


def build_benchmark_directory(
    tmp_path,
):
    database_path = (
        tmp_path
        / "diagnostic_benchmark.sqlite3"
    )

    database_path.write_bytes(
        b"benchmark"
    )

    directory = (
        tmp_path
        / "benchmark"
    )

    directory.mkdir()

    benchmark = {
        "model_label":
            "Gemini",

        "scenario_id":
            "scenario-001",

        "scenario_sha256":
            "scenario-sha",

        "hierarchy_key":
            HIERARCHY_KEY,

        "benchmark_hash":
            "benchmark-hash",

        "benchmark_database_path":
            str(
                database_path
            ),
    }

    (
        directory
        / "benchmark_summary.json"
    ).write_text(
        json.dumps(
            benchmark
        ),
        encoding="utf-8",
    )

    primary_replay = {
        "model_label":
            "Gemini",

        "scenario_id":
            "scenario-001",

        "scenario_sha256":
            "scenario-sha",

        "hierarchy_key":
            HIERARCHY_KEY,

        "source_benchmark_hash":
            "benchmark-hash",

        "replay_hash":
            "primary-replay-hash",
    }

    (
        directory
        / "primary_diagnosis_ranking_replay.json"
    ).write_text(
        json.dumps(
            primary_replay
        ),
        encoding="utf-8",
    )

    return (
        directory,
        database_path,
    )


def build_service(
    *,
    projection=None,
):
    return (
        PreliveMultimodelDiagnosticSeparationReplayService(
            projection_service=(
                projection
                or
                FakeProjectionService()
            )
        )
    )


def test_replay_preserves_benchmark_identity(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        build_service()
        .replay(
            benchmark_directory=(
                directory
            )
        )
    )

    assert result.model_label == "Gemini"
    assert result.scenario_id == "scenario-001"
    assert result.scenario_sha256 == "scenario-sha"
    assert result.hierarchy_key == HIERARCHY_KEY
    assert result.source_benchmark_hash == "benchmark-hash"


def test_replay_binds_primary_diagnosis_replay_hash(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        build_service()
        .replay(
            benchmark_directory=directory
        )
    )

    assert (
        result.primary_diagnosis_replay_hash
        == "primary-replay-hash"
    )


def test_replay_calls_projection_with_benchmark_database(
    tmp_path,
):
    directory, database_path = (
        build_benchmark_directory(
            tmp_path
        )
    )

    projection = (
        FakeProjectionService()
    )

    build_service(
        projection=projection
    ).replay(
        benchmark_directory=directory
    )

    assert (
        projection.calls
        == [
            (
                str(
                    database_path
                ),
                HIERARCHY_KEY,
            )
        ]
    )


def test_replay_exposes_leading_candidate(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        build_service()
        .replay(
            benchmark_directory=directory
        )
    )

    assert (
        result.leading_candidate
        == "APPROVAL_DELAYED"
    )


def test_replay_exposes_runner_up_candidate(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        build_service()
        .replay(
            benchmark_directory=directory
        )
    )

    assert (
        result.runner_up_candidate
        == "SECURITY_REVIEW"
    )


def test_replay_exposes_rank_1_to_rank_2_absolute(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        build_service()
        .replay(
            benchmark_directory=directory
        )
    )

    assert (
        result.rank_1_to_rank_2_absolute
        == 0.20
    )


def test_replay_exposes_rank_1_to_rank_2_relative(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        build_service()
        .replay(
            benchmark_directory=directory
        )
    )

    assert (
        result.rank_1_to_rank_2_relative
        == 0.25
    )


def test_replay_exposes_rank_1_to_rank_3_absolute(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        build_service()
        .replay(
            benchmark_directory=directory
        )
    )

    assert (
        result.rank_1_to_rank_3_absolute
        == 0.40
    )


def test_replay_exposes_top_3_spread(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        build_service()
        .replay(
            benchmark_directory=directory
        )
    )

    assert (
        result.top_3_score_spread
        == 0.40
    )


def test_replay_writes_receipt(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        build_service()
        .replay(
            benchmark_directory=directory
        )
    )

    output = (
        directory
        / DIAGNOSTIC_SEPARATION_REPLAY_FILENAME
    )

    assert output.is_file()

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert (
        payload
        == result.to_dict()
    )


def test_replay_uses_gagf_fip_authority(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        build_service()
        .replay(
            benchmark_directory=directory
        )
    )

    assert (
        result.authority
        == PRELIVE_DIAGNOSTIC_SEPARATION_REPLAY_AUTHORITY
    )


def test_replay_rejects_missing_directory(
    tmp_path,
):
    with pytest.raises(
        PreliveDiagnosticSeparationReplayError,
        match="does not exist",
    ):
        build_service().replay(
            benchmark_directory=(
                tmp_path
                / "missing"
            )
        )


def test_replay_rejects_primary_model_binding_mismatch(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    replay_path = (
        directory
        / "primary_diagnosis_ranking_replay.json"
    )

    payload = json.loads(
        replay_path.read_text(
            encoding="utf-8"
        )
    )

    payload[
        "model_label"
    ] = "Claude"

    replay_path.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PreliveDiagnosticSeparationReplayError,
        match="model_label binding mismatch",
    ):
        build_service().replay(
            benchmark_directory=directory
        )


def test_replay_rejects_primary_benchmark_hash_mismatch(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    replay_path = (
        directory
        / "primary_diagnosis_ranking_replay.json"
    )

    payload = json.loads(
        replay_path.read_text(
            encoding="utf-8"
        )
    )

    payload[
        "source_benchmark_hash"
    ] = "wrong-hash"

    replay_path.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PreliveDiagnosticSeparationReplayError,
        match="benchmark hash binding mismatch",
    ):
        build_service().replay(
            benchmark_directory=directory
        )


def test_replay_rejects_projection_hierarchy_mismatch(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    projection = (
        FakeProjectionService(
            result=(
                FakeProjectionResult(
                    hierarchy_key=(
                        "wrong/client/"
                        "engagement/assessment"
                    )
                )
            )
        )
    )

    with pytest.raises(
        PreliveDiagnosticSeparationReplayError,
        match="projection hierarchy",
    ):
        build_service(
            projection=projection
        ).replay(
            benchmark_directory=directory
        )


def test_replay_requires_repository_chain_validity(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    projection = (
        FakeProjectionService(
            result=(
                FakeProjectionResult(
                    repository_chain_valid=False
                )
            )
        )
    )

    with pytest.raises(
        PreliveDiagnosticSeparationReplayError,
        match="repository chain validity",
    ):
        build_service(
            projection=projection
        ).replay(
            benchmark_directory=directory
        )


def test_replay_requires_primary_projection_verification(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    projection = (
        FakeProjectionService(
            result=(
                FakeProjectionResult(
                    primary_projection_verified=False
                )
            )
        )
    )

    with pytest.raises(
        PreliveDiagnosticSeparationReplayError,
        match="verify primary projection",
    ):
        build_service(
            projection=projection
        ).replay(
            benchmark_directory=directory
        )


def test_replay_requires_structural_projection_verification(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    projection = (
        FakeProjectionService(
            result=(
                FakeProjectionResult(
                    structural_projection_verified=False
                )
            )
        )
    )

    with pytest.raises(
        PreliveDiagnosticSeparationReplayError,
        match="verify structural projection",
    ):
        build_service(
            projection=projection
        ).replay(
            benchmark_directory=directory
        )


def test_replay_requires_structural_classification_verification(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    projection = (
        FakeProjectionService(
            result=(
                FakeProjectionResult(
                    structural_classification_verified=False
                )
            )
        )
    )

    with pytest.raises(
        PreliveDiagnosticSeparationReplayError,
        match="verify structural classification",
    ):
        build_service(
            projection=projection
        ).replay(
            benchmark_directory=directory
        )


def test_replay_hash_is_deterministic(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    service = (
        build_service()
    )

    first = service.replay(
        benchmark_directory=directory
    )

    second = service.replay(
        benchmark_directory=directory
    )

    assert (
        first.replay_hash
        == second.replay_hash
    )


def test_receipt_ignores_projection_reuse_state(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    projection = (
        FakeProjectionService()
    )

    service = (
        build_service(
            projection=projection
        )
    )

    first = service.replay(
        benchmark_directory=directory
    )

    projection.result.reused_existing = (
        True
    )

    second = service.replay(
        benchmark_directory=directory
    )

    assert (
        first.replay_hash
        == second.replay_hash
    )

    assert (
        first.to_dict()
        == second.to_dict()
    )

    assert (
        "reused_existing"
        not in first.to_dict()[
            "projection"
        ]
    )


def test_replay_does_not_emit_confidence_or_oracle_fields(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        build_service()
        .replay(
            benchmark_directory=directory
        )
    )

    payload = (
        result.to_dict()
    )

    forbidden = (
        "confidence",
        "confidence_level",
        "expected_conditions",
        "oracle",
        "ground_truth",
        "root_cause",
        "primary_diagnosis",
        "authorized_action",
        "intervention",
    )

    for field in forbidden:
        assert field not in payload