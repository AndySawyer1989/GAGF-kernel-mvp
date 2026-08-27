from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from backend.app.gagf.governance_assessment_structural_importance_classification import (
    StructuralImportanceLevel,
)
from backend.app.gagf.prelive_multimodel_primary_diagnosis_replay import (
    PRIMARY_DIAGNOSIS_REPLAY_FILENAME,
    PRELIVE_PRIMARY_DIAGNOSIS_REPLAY_AUTHORITY,
    PreliveMultimodelPrimaryDiagnosisReplayService,
    PrelivePrimaryDiagnosisReplayError,
)


HIERARCHY_KEY = (
    "tenant-a/client-a/"
    "engagement-a/assessment-a"
)


class FakeCondition:
    def __init__(
        self,
        *,
        category,
        rank,
        score,
        relative,
        structural_level=(
            StructuralImportanceLevel.HIGH
        ),
        quality=0.9,
    ):
        self.category = category
        self.rank = rank
        self.explanatory_score = score
        self.relative_to_highest = relative
        self.structural_level = (
            structural_level
        )
        self.evidence_quality = quality
        self.evidence_hash = (
            f"{category}-evidence-hash"
        )


class FakeSummary:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
    ):
        self.hierarchy_key = (
            hierarchy_key
        )

        self.summary_hash = (
            "primary-summary-hash"
        )

        self.conditions = (
            FakeCondition(
                category="APPROVAL_DELAYED",
                rank=1,
                score=0.9,
                relative=1.0,
            ),
            FakeCondition(
                category="SECURITY_REVIEW",
                rank=2,
                score=0.7,
                relative=0.7778,
                structural_level=(
                    StructuralImportanceLevel.MODERATE
                ),
            ),
        )

        self.ranked_conditions = (
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        )

        self.highest_ranked_condition = (
            "APPROVAL_DELAYED"
        )


class FakeProjectionResult:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
        repository_chain_valid=True,
        structural_projection_verified=True,
        structural_classification_verified=True,
        reused_existing=False,
    ):
        self.hierarchy_key = (
            hierarchy_key
        )

        self.repository_chain_valid = (
            repository_chain_valid
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

        self.primary_diagnosis_summary = (
            FakeSummary(
                hierarchy_key=(
                    hierarchy_key
                )
            )
        )

    def to_dict(
        self,
    ):
        return {
            "hierarchy_key":
                self.hierarchy_key,

            "primary_diagnosis_summary_hash":
                self.primary_diagnosis_summary
                .summary_hash,

            "artifact_id":
                "primary-artifact",

            "artifact_hash":
                "primary-artifact-hash",

            "sequence_number":
                15,

            "repository_chain_valid":
                self.repository_chain_valid,

            "reused_existing":
                self.reused_existing,

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
                str(database_path),
                context.hierarchy_key,
            )
        )

        return self.result


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

    summary = {
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
            summary
        ),
        encoding="utf-8",
    )

    return (
        directory,
        database_path,
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
        PreliveMultimodelPrimaryDiagnosisReplayService(
            projection_service=(
                FakeProjectionService()
            )
        )
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

    (
        PreliveMultimodelPrimaryDiagnosisReplayService(
            projection_service=projection
        )
        .replay(
            benchmark_directory=directory
        )
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


def test_replay_exposes_ranked_conditions(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        PreliveMultimodelPrimaryDiagnosisReplayService(
            projection_service=(
                FakeProjectionService()
            )
        )
        .replay(
            benchmark_directory=directory
        )
    )

    assert (
        result.ranked_conditions
        == (
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        )
    )


def test_replay_exposes_highest_ranked_condition(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        PreliveMultimodelPrimaryDiagnosisReplayService(
            projection_service=(
                FakeProjectionService()
            )
        )
        .replay(
            benchmark_directory=directory
        )
    )

    assert (
        result.highest_ranked_condition
        == "APPROVAL_DELAYED"
    )


def test_replay_preserves_ranking_scores(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        PreliveMultimodelPrimaryDiagnosisReplayService(
            projection_service=(
                FakeProjectionService()
            )
        )
        .replay(
            benchmark_directory=directory
        )
    )

    assert (
        result.ranking[0][
            "explanatory_score"
        ]
        == 0.9
    )

    assert (
        result.ranking[1][
            "relative_to_highest"
        ]
        == 0.7778
    )


def test_replay_writes_receipt(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    service = (
        PreliveMultimodelPrimaryDiagnosisReplayService(
            projection_service=(
                FakeProjectionService()
            )
        )
    )

    result = service.replay(
        benchmark_directory=directory
    )

    output = (
        directory
        / PRIMARY_DIAGNOSIS_REPLAY_FILENAME
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


def test_replay_receipt_has_gagf_fip_authority(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        PreliveMultimodelPrimaryDiagnosisReplayService(
            projection_service=(
                FakeProjectionService()
            )
        )
        .replay(
            benchmark_directory=directory
        )
    )

    assert (
        result.authority
        == PRELIVE_PRIMARY_DIAGNOSIS_REPLAY_AUTHORITY
    )


def test_replay_rejects_missing_benchmark_directory(
    tmp_path,
):
    with pytest.raises(
        PrelivePrimaryDiagnosisReplayError,
        match="does not exist",
    ):
        (
            PreliveMultimodelPrimaryDiagnosisReplayService(
                projection_service=(
                    FakeProjectionService()
                )
            )
            .replay(
                benchmark_directory=(
                    tmp_path
                    / "missing"
                )
            )
        )


def test_replay_rejects_invalid_hierarchy(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    summary_path = (
        directory
        / "benchmark_summary.json"
    )

    payload = json.loads(
        summary_path.read_text(
            encoding="utf-8"
        )
    )

    payload[
        "hierarchy_key"
    ] = "invalid"

    summary_path.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        PrelivePrimaryDiagnosisReplayError,
        match="tenant/client/engagement/assessment",
    ):
        (
            PreliveMultimodelPrimaryDiagnosisReplayService(
                projection_service=(
                    FakeProjectionService()
                )
            )
            .replay(
                benchmark_directory=directory
            )
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
            FakeProjectionResult(
                hierarchy_key=(
                    "wrong/client/engagement/assessment"
                )
            )
        )
    )

    with pytest.raises(
        PrelivePrimaryDiagnosisReplayError,
        match="projection hierarchy",
    ):
        (
            PreliveMultimodelPrimaryDiagnosisReplayService(
                projection_service=projection
            )
            .replay(
                benchmark_directory=directory
            )
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
            FakeProjectionResult(
                repository_chain_valid=False
            )
        )
    )

    with pytest.raises(
        PrelivePrimaryDiagnosisReplayError,
        match="repository chain validity",
    ):
        (
            PreliveMultimodelPrimaryDiagnosisReplayService(
                projection_service=projection
            )
            .replay(
                benchmark_directory=directory
            )
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
            FakeProjectionResult(
                structural_projection_verified=False
            )
        )
    )

    with pytest.raises(
        PrelivePrimaryDiagnosisReplayError,
        match="verify structural projection",
    ):
        (
            PreliveMultimodelPrimaryDiagnosisReplayService(
                projection_service=projection
            )
            .replay(
                benchmark_directory=directory
            )
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
            FakeProjectionResult(
                structural_classification_verified=False
            )
        )
    )

    with pytest.raises(
        PrelivePrimaryDiagnosisReplayError,
        match="verify structural classification",
    ):
        (
            PreliveMultimodelPrimaryDiagnosisReplayService(
                projection_service=projection
            )
            .replay(
                benchmark_directory=directory
            )
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
        PreliveMultimodelPrimaryDiagnosisReplayService(
            projection_service=(
                FakeProjectionService()
            )
        )
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
        FakeProjectionService(
            FakeProjectionResult()
        )
    )

    service = (
        PreliveMultimodelPrimaryDiagnosisReplayService(
            projection_service=projection
        )
    )

    first = service.replay(
        benchmark_directory=directory
    )

    projection.result.reused_existing = True

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


def test_replay_does_not_emit_oracle_fields(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        PreliveMultimodelPrimaryDiagnosisReplayService(
            projection_service=(
                FakeProjectionService()
            )
        )
        .replay(
            benchmark_directory=directory
        )
    )

    payload = result.to_dict()

    assert "expected_conditions" not in payload
    assert "oracle" not in payload
    assert "ground_truth" not in payload
    assert "root_cause" not in payload


def test_replay_does_not_name_highest_rank_as_primary(
    tmp_path,
):
    directory, _ = (
        build_benchmark_directory(
            tmp_path
        )
    )

    result = (
        PreliveMultimodelPrimaryDiagnosisReplayService(
            projection_service=(
                FakeProjectionService()
            )
        )
        .replay(
            benchmark_directory=directory
        )
    )

    payload = result.to_dict()

    assert (
        payload[
            "highest_ranked_condition"
        ]
        == "APPROVAL_DELAYED"
    )

    assert "primary_diagnosis" not in payload
    assert "primary_condition" not in payload
    assert "causal_condition" not in payload