from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from backend.app.gagf.governance_assessment_diagnostic_projection import (
    DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE,
    DiagnosticProjectionError,
    GovernanceAssessmentDiagnosticProjectionService,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)


GEMINI_HIERARCHY = (
    "synthetic-gemini-tenant/"
    "prelive-client/"
    "prelive-prelive-001-gemini-001/"
    "assessment-prelive-001-gemini-001"
)


def gemini_context() -> CommercialHierarchyContext:
    return CommercialHierarchyContext(
        tenant_id="synthetic-gemini-tenant",
        client_id="prelive-client",
        engagement_id=(
            "prelive-prelive-001-gemini-001"
        ),
        assessment_id=(
            "assessment-prelive-001-gemini-001"
        ),
    )


def source_database() -> Path:
    return Path(
        "artifacts"
    ) / "prelive_gemini_001" / "prelive.sqlite3"


def copied_database(
    tmp_path: Path,
) -> Path:
    source = source_database()

    if not source.is_file():
        pytest.skip(
            "PRELIVE Gemini benchmark database "
            "is not available locally"
        )

    target = (
        tmp_path
        / "prelive.sqlite3"
    )

    shutil.copy2(
        source,
        target,
    )

    return target


def test_projection_does_not_modify_original_benchmark(
    tmp_path,
):
    source = source_database()

    if not source.is_file():
        pytest.skip(
            "PRELIVE Gemini benchmark database "
            "is not available locally"
        )

    before = source.read_bytes()

    copied = copied_database(
        tmp_path
    )

    (
        GovernanceAssessmentDiagnosticProjectionService()
        .project(
            database_path=copied,
            context=gemini_context(),
        )
    )

    after = source.read_bytes()

    assert before == after


def test_projection_appends_diagnostic_artifact(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    before = repository.list_artifacts(
        context=gemini_context()
    )

    assert len(before) == 10

    result = (
        GovernanceAssessmentDiagnosticProjectionService()
        .project(
            database_path=database_path,
            context=gemini_context(),
        )
    )

    after = repository.list_artifacts(
        context=gemini_context()
    )

    assert len(after) == 11

    assert (
        after[-1].artifact_type
        == DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE
    )

    assert (
        result.sequence_number
        == 11
    )


def test_projection_preserves_repository_chain(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    result = (
        GovernanceAssessmentDiagnosticProjectionService()
        .project(
            database_path=database_path,
            context=gemini_context(),
        )
    )

    assert (
        result.repository_chain_valid
        is True
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    assert (
        repository.verify_chain(
            context=gemini_context()
        )
        is True
    )


def test_projection_is_deterministic_and_idempotent(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    service = (
        GovernanceAssessmentDiagnosticProjectionService()
    )

    first = service.project(
        database_path=database_path,
        context=gemini_context(),
    )

    second = service.project(
        database_path=database_path,
        context=gemini_context(),
    )

    assert (
        first.diagnostic_summary
        == second.diagnostic_summary
    )

    assert (
        first.artifact_hash
        == second.artifact_hash
    )

    assert (
        first.reused_existing
        is False
    )

    assert (
        second.reused_existing
        is True
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    artifacts = repository.list_artifacts(
        context=gemini_context(),
        artifact_type=(
            DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE
        ),
    )

    assert len(artifacts) == 1


def test_projection_recovers_original_hierarchy(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    result = (
        GovernanceAssessmentDiagnosticProjectionService()
        .project(
            database_path=database_path,
            context=gemini_context(),
        )
    )

    assert (
        result.hierarchy_key
        == GEMINI_HIERARCHY
    )

    assert (
        result.diagnostic_summary
        .hierarchy_key
        == GEMINI_HIERARCHY
    )


def test_projection_contains_security_review(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    result = (
        GovernanceAssessmentDiagnosticProjectionService()
        .project(
            database_path=database_path,
            context=gemini_context(),
        )
    )

    levels = {
        condition.category.value:
            condition.level.value
        for condition
        in result.diagnostic_summary.conditions
    }

    assert "SECURITY_REVIEW" in levels

    assert levels[
        "SECURITY_REVIEW"
    ] in {
        "significant",
        "dominant",
    }


def test_projection_preserves_raw_observed_categories(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    result = (
        GovernanceAssessmentDiagnosticProjectionService()
        .project(
            database_path=database_path,
            context=gemini_context(),
        )
    )

    raw_categories = {
        condition.category.value
        for condition
        in result.diagnostic_summary.conditions
    }

    assert raw_categories == {
        "APPROVAL_DELAYED",
        "APPROVAL_REQUIRED",
        "DEPENDENCY_WAIT",
        "ENVIRONMENT_FAILURE",
        "ESCALATION",
        "OWNERSHIP_GAP",
        "SECURITY_REVIEW",
        "WORK_BLOCKED",
    }


def test_projection_exposes_diagnosed_subset(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    result = (
        GovernanceAssessmentDiagnosticProjectionService()
        .project(
            database_path=database_path,
            context=gemini_context(),
        )
    )

    raw_categories = {
        condition.category.value
        for condition
        in result.diagnostic_summary.conditions
    }

    diagnosed = set(
        result.diagnosed_conditions
    )

    assert diagnosed
    assert diagnosed.issubset(
        raw_categories
    )


def test_projection_exposes_one_dominant_condition(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    result = (
        GovernanceAssessmentDiagnosticProjectionService()
        .project(
            database_path=database_path,
            context=gemini_context(),
        )
    )

    dominant_levels = [
        condition
        for condition
        in result.diagnostic_summary.conditions
        if condition.level.value
        == "dominant"
    ]

    assert len(
        dominant_levels
    ) <= 1

    if dominant_levels:
        assert (
            result.dominant_condition
            == dominant_levels[0]
            .category.value
        )


def test_projection_artifact_payload_matches_summary(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    result = (
        GovernanceAssessmentDiagnosticProjectionService()
        .project(
            database_path=database_path,
            context=gemini_context(),
        )
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    artifacts = repository.list_artifacts(
        context=gemini_context(),
        artifact_type=(
            DIAGNOSTIC_SIGNIFICANCE_ARTIFACT_TYPE
        ),
    )

    assert len(artifacts) == 1

    assert (
        artifacts[0].payload
        == result.diagnostic_summary.to_dict()
    )


def test_projection_rejects_wrong_hierarchy(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    wrong_context = CommercialHierarchyContext(
        tenant_id="wrong-tenant",
        client_id="prelive-client",
        engagement_id=(
            "prelive-prelive-001-gemini-001"
        ),
        assessment_id=(
            "assessment-prelive-001-gemini-001"
        ),
    )

    with pytest.raises(
        Exception,
    ):
        (
            GovernanceAssessmentDiagnosticProjectionService()
            .project(
                database_path=database_path,
                context=wrong_context,
            )
        )


def test_projection_requires_original_intake_artifact(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    intake = repository.list_artifacts(
        context=gemini_context(),
        artifact_type="evidence-intake-batch",
    )

    assert len(intake) == 1


def test_projection_requires_original_friction_artifact(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    friction = repository.list_artifacts(
        context=gemini_context(),
        artifact_type="friction-summary",
    )

    assert len(friction) == 1


def test_projection_summary_hash_is_present(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    result = (
        GovernanceAssessmentDiagnosticProjectionService()
        .project(
            database_path=database_path,
            context=gemini_context(),
        )
    )

    assert len(
        result.diagnostic_summary.summary_hash
    ) == 64


def test_projection_result_is_readable_as_operator_contract(
    tmp_path,
):
    database_path = copied_database(
        tmp_path
    )

    result = (
        GovernanceAssessmentDiagnosticProjectionService()
        .project(
            database_path=database_path,
            context=gemini_context(),
        )
    )

    payload = result.to_dict()

    assert (
        payload["repository_chain_valid"]
        is True
    )

    assert (
        payload["sequence_number"]
        == 11
    )

    assert isinstance(
        payload["diagnosed_conditions"],
        list,
    )