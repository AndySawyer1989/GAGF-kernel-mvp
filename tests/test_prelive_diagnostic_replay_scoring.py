from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from backend.app.gagf.governance_assessment_diagnostic_significance import (
    AssessmentDiagnosticSignificanceSummary,
    DiagnosticCondition,
    DiagnosticLevel,
    DiagnosticSupportAxes,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    ConstraintCategory,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from backend.app.gagf.prelive_diagnostic_replay_scoring import (
    PRELIVE_DIAGNOSTIC_REPLAY_AUTHORITY,
    PRELIVE_DIAGNOSTIC_REPLAY_STATUS,
    PreliveDiagnosticReplayScoringService,
)


CONTEXT = CommercialHierarchyContext(
    tenant_id="tenant-a",
    client_id="client-a",
    engagement_id="engagement-a",
    assessment_id="assessment-a",
)


def create_parent_assessment(
    repository: GovernanceAssessmentRepository,
) -> None:
    repository.create_assessment(
        context=CONTEXT,
        assessment_name=(
            "PRELIVE Diagnostic Replay Test"
        ),
        status="complete",
    )


def build_condition(
    *,
    category: ConstraintCategory,
    level: DiagnosticLevel,
) -> DiagnosticCondition:
    return DiagnosticCondition(
        category=category,
        level=level,
        event_count=10,
        event_share=0.10,
        friction_score=20.0,
        friction_band="severe",
        unique_work_item_count=4,
        unique_actor_count=3,
        unique_team_count=2,
        unique_lifecycle_count=3,
        unique_source_count=2,
        active_day_count=3,
        mean_evidence_quality=0.9,
        total_duration_minutes=300.0,
        support_axes=DiagnosticSupportAxes(
            recurrence=True,
            work_item_spread=True,
            actor_spread=True,
            team_spread=True,
            lifecycle_spread=True,
            source_diversity=True,
            temporal_persistence=True,
            evidence_quality=True,
        ),
        first_occurred_on=date(
            2026,
            8,
            1,
        ),
        last_occurred_on=date(
            2026,
            8,
            3,
        ),
        is_diagnosed_condition=(
            level
            in {
                DiagnosticLevel.SIGNIFICANT,
                DiagnosticLevel.DOMINANT,
            }
        ),
    )


def build_summary(
    *,
    diagnosed: tuple[
        ConstraintCategory,
        ...,
    ],
    dominant:
        ConstraintCategory
        | None,
) -> AssessmentDiagnosticSignificanceSummary:
    conditions = tuple(
        build_condition(
            category=category,
            level=(
                DiagnosticLevel.DOMINANT
                if category == dominant
                else DiagnosticLevel.SIGNIFICANT
            ),
        )
        for category
        in diagnosed
    )

    return AssessmentDiagnosticSignificanceSummary(
        tenant_id="tenant-a",
        client_id="client-a",
        engagement_id="engagement-a",
        assessment_id="assessment-a",
        conditions=conditions,
        diagnosed_conditions=diagnosed,
        dominant_condition=dominant,
        summary_hash=(
            "a" * 64
        ),
    )


def build_database(
    tmp_path: Path,
    *,
    diagnosed: tuple[
        ConstraintCategory,
        ...,
    ],
    dominant:
        ConstraintCategory
        | None,
) -> Path:
    database_path = (
        tmp_path
        / "assessment.sqlite3"
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    create_parent_assessment(
        repository
    )

    summary = build_summary(
        diagnosed=diagnosed,
        dominant=dominant,
    )

    repository.append_artifact(
        context=CONTEXT,
        artifact_type=(
            "diagnostic-significance"
        ),
        payload=summary.to_dict(),
    )

    assert (
        repository.verify_chain(
            context=CONTEXT
        )
        is True
    )

    return database_path


def build_oracle(
    *expected: str,
    dominant: str | None = None,
) -> dict:
    return {
        "schema_version": "1.0",
        "test_program": "PRELIVE-001",
        "oracle_status": "SEALED",
        "scenario_id": "test-scenario",
        "scenario_sha256": (
            "b" * 64
        ),
        "expected_conditions": [
            {
                "constraint_type":
                    condition
            }
            for condition
            in expected
        ],
        "expected_dominant_constraint":
            dominant,
    }


def test_exact_match_scores_one(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(
            ConstraintCategory.APPROVAL_DELAYED,
            ConstraintCategory.SECURITY_REVIEW,
        ),
        dominant=(
            ConstraintCategory.SECURITY_REVIEW
        ),
    )

    result = (
        PreliveDiagnosticReplayScoringService()
        .score(
            database_path=database_path,
            context=CONTEXT,
            oracle=build_oracle(
                "APPROVAL_DELAYED",
                "SECURITY_REVIEW",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.f1 == 1.0
    assert result.exact_condition_match is True
    assert result.dominant_constraint_match is True


def test_scores_false_positive(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(
            ConstraintCategory.APPROVAL_DELAYED,
            ConstraintCategory.SECURITY_REVIEW,
            ConstraintCategory.ESCALATION,
        ),
        dominant=(
            ConstraintCategory.SECURITY_REVIEW
        ),
    )

    result = (
        PreliveDiagnosticReplayScoringService()
        .score(
            database_path=database_path,
            context=CONTEXT,
            oracle=build_oracle(
                "APPROVAL_DELAYED",
                "SECURITY_REVIEW",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    assert result.false_positives == (
        "ESCALATION",
    )

    assert result.precision == round(
        2 / 3,
        4,
    )

    assert result.recall == 1.0


def test_scores_false_negative(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(
            ConstraintCategory.SECURITY_REVIEW,
        ),
        dominant=(
            ConstraintCategory.SECURITY_REVIEW
        ),
    )

    result = (
        PreliveDiagnosticReplayScoringService()
        .score(
            database_path=database_path,
            context=CONTEXT,
            oracle=build_oracle(
                "APPROVAL_DELAYED",
                "SECURITY_REVIEW",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    assert result.false_negatives == (
        "APPROVAL_DELAYED",
    )

    assert result.precision == 1.0
    assert result.recall == 0.5


def test_observed_and_recurring_are_not_diagnosed(
    tmp_path,
):
    database_path = (
        tmp_path
        / "assessment.sqlite3"
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    create_parent_assessment(
        repository
    )

    observed = build_condition(
        category=(
            ConstraintCategory.APPROVAL_REQUIRED
        ),
        level=DiagnosticLevel.OBSERVED,
    )

    recurring = build_condition(
        category=(
            ConstraintCategory.ESCALATION
        ),
        level=DiagnosticLevel.RECURRING,
    )

    significant = build_condition(
        category=(
            ConstraintCategory.SECURITY_REVIEW
        ),
        level=DiagnosticLevel.DOMINANT,
    )

    summary = (
        AssessmentDiagnosticSignificanceSummary(
            tenant_id="tenant-a",
            client_id="client-a",
            engagement_id="engagement-a",
            assessment_id="assessment-a",
            conditions=(
                observed,
                recurring,
                significant,
            ),
            diagnosed_conditions=(
                ConstraintCategory.SECURITY_REVIEW,
            ),
            dominant_condition=(
                ConstraintCategory.SECURITY_REVIEW
            ),
            summary_hash=(
                "a" * 64
            ),
        )
    )

    repository.append_artifact(
        context=CONTEXT,
        artifact_type=(
            "diagnostic-significance"
        ),
        payload=summary.to_dict(),
    )

    result = (
        PreliveDiagnosticReplayScoringService()
        .score(
            database_path=database_path,
            context=CONTEXT,
            oracle=build_oracle(
                "SECURITY_REVIEW",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    assert result.diagnosed_conditions == (
        "SECURITY_REVIEW",
    )

    assert result.false_positives == ()


def test_replay_binds_artifact_hash(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(
            ConstraintCategory.SECURITY_REVIEW,
        ),
        dominant=(
            ConstraintCategory.SECURITY_REVIEW
        ),
    )

    result = (
        PreliveDiagnosticReplayScoringService()
        .score(
            database_path=database_path,
            context=CONTEXT,
            oracle=build_oracle(
                "SECURITY_REVIEW",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    assert len(
        result.diagnostic_artifact_hash
    ) == 64

    assert len(
        result.replay_hash
    ) == 64


def test_replay_is_deterministic(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(
            ConstraintCategory.APPROVAL_DELAYED,
            ConstraintCategory.SECURITY_REVIEW,
        ),
        dominant=(
            ConstraintCategory.SECURITY_REVIEW
        ),
    )

    service = (
        PreliveDiagnosticReplayScoringService()
    )

    oracle = build_oracle(
        "APPROVAL_DELAYED",
        "SECURITY_REVIEW",
        dominant="SECURITY_REVIEW",
    )

    first = service.score(
        database_path=database_path,
        context=CONTEXT,
        oracle=oracle,
    )

    second = service.score(
        database_path=database_path,
        context=CONTEXT,
        oracle=oracle,
    )

    assert first == second


def test_result_has_governance_boundary(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(
            ConstraintCategory.SECURITY_REVIEW,
        ),
        dominant=(
            ConstraintCategory.SECURITY_REVIEW
        ),
    )

    result = (
        PreliveDiagnosticReplayScoringService()
        .score(
            database_path=database_path,
            context=CONTEXT,
            oracle=build_oracle(
                "SECURITY_REVIEW",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    assert (
        result.replay_status
        == PRELIVE_DIAGNOSTIC_REPLAY_STATUS
    )

    assert (
        result.authority
        == PRELIVE_DIAGNOSTIC_REPLAY_AUTHORITY
    )


def test_requires_diagnostic_artifact(
    tmp_path,
):
    database_path = (
        tmp_path
        / "assessment.sqlite3"
    )

    repository = GovernanceAssessmentRepository(
        database_path
    )

    create_parent_assessment(
        repository
    )

    with pytest.raises(
        PreliveScenarioError,
        match="exactly one",
    ):
        (
            PreliveDiagnosticReplayScoringService()
            .score(
                database_path=database_path,
                context=CONTEXT,
                oracle=build_oracle(
                    "SECURITY_REVIEW",
                ),
            )
        )


def test_rejects_unsealed_oracle(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(
            ConstraintCategory.SECURITY_REVIEW,
        ),
        dominant=(
            ConstraintCategory.SECURITY_REVIEW
        ),
    )

    oracle = build_oracle(
        "SECURITY_REVIEW",
    )

    oracle["oracle_status"] = (
        "UNSEALED"
    )

    with pytest.raises(
        PreliveScenarioError,
        match="SEALED",
    ):
        (
            PreliveDiagnosticReplayScoringService()
            .score(
                database_path=database_path,
                context=CONTEXT,
                oracle=oracle,
            )
        )


def test_rejects_duplicate_expected_condition(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(
            ConstraintCategory.SECURITY_REVIEW,
        ),
        dominant=(
            ConstraintCategory.SECURITY_REVIEW
        ),
    )

    oracle = build_oracle(
        "SECURITY_REVIEW",
        "SECURITY_REVIEW",
    )

    with pytest.raises(
        PreliveScenarioError,
        match="duplicate",
    ):
        (
            PreliveDiagnosticReplayScoringService()
            .score(
                database_path=database_path,
                context=CONTEXT,
                oracle=oracle,
            )
        )


def test_wrong_dominant_scores_false(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(
            ConstraintCategory.SECURITY_REVIEW,
            ConstraintCategory.APPROVAL_DELAYED,
        ),
        dominant=(
            ConstraintCategory.APPROVAL_DELAYED
        ),
    )

    result = (
        PreliveDiagnosticReplayScoringService()
        .score(
            database_path=database_path,
            context=CONTEXT,
            oracle=build_oracle(
                "SECURITY_REVIEW",
                "APPROVAL_DELAYED",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    assert (
        result.dominant_constraint_match
        is False
    )


def test_expected_dominant_optional(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(
            ConstraintCategory.SECURITY_REVIEW,
        ),
        dominant=(
            ConstraintCategory.SECURITY_REVIEW
        ),
    )

    result = (
        PreliveDiagnosticReplayScoringService()
        .score(
            database_path=database_path,
            context=CONTEXT,
            oracle=build_oracle(
                "SECURITY_REVIEW",
            ),
        )
    )

    assert (
        result.dominant_constraint_match
        is None
    )


def test_empty_diagnosed_set_can_score(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(),
        dominant=None,
    )

    result = (
        PreliveDiagnosticReplayScoringService()
        .score(
            database_path=database_path,
            context=CONTEXT,
            oracle=build_oracle(
                "SECURITY_REVIEW",
            ),
        )
    )

    assert result.precision == 1.0
    assert result.recall == 0.0
    assert result.f1 == 0.0

    assert result.false_negatives == (
        "SECURITY_REVIEW",
    )


def test_result_serializes_metrics(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(
            ConstraintCategory.SECURITY_REVIEW,
        ),
        dominant=(
            ConstraintCategory.SECURITY_REVIEW
        ),
    )

    result = (
        PreliveDiagnosticReplayScoringService()
        .score(
            database_path=database_path,
            context=CONTEXT,
            oracle=build_oracle(
                "SECURITY_REVIEW",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    payload = result.to_dict()

    assert payload["precision"] == 1.0
    assert payload["recall"] == 1.0
    assert payload["f1"] == 1.0

    assert payload[
        "diagnosed_conditions"
    ] == [
        "SECURITY_REVIEW"
    ]


def test_hierarchy_is_preserved(
    tmp_path,
):
    database_path = build_database(
        tmp_path,
        diagnosed=(
            ConstraintCategory.SECURITY_REVIEW,
        ),
        dominant=(
            ConstraintCategory.SECURITY_REVIEW
        ),
    )

    result = (
        PreliveDiagnosticReplayScoringService()
        .score(
            database_path=database_path,
            context=CONTEXT,
            oracle=build_oracle(
                "SECURITY_REVIEW",
            ),
        )
    )

    assert (
        result.hierarchy_key
        == CONTEXT.hierarchy_key
    )