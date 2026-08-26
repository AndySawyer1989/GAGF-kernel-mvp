from __future__ import annotations

from datetime import date

import pytest

from backend.app.gagf.governance_assessment_diagnostic_scope import (
    AssessmentDiagnosticScopeSummary,
    DiagnosticScopeAxes,
    DiagnosticScopeCondition,
    DiagnosticScopeLevel,
)
from backend.app.gagf.governance_assessment_diagnostic_significance import (
    DiagnosticLevel,
)
from backend.app.gagf.prelive_blind_assessment import (
    PreliveScenarioError,
)
from backend.app.gagf.prelive_systemic_diagnostic_replay_scoring import (
    PRELIVE_SYSTEMIC_REPLAY_AUTHORITY,
    PRELIVE_SYSTEMIC_REPLAY_STATUS,
    PreliveSystemicDiagnosticReplayScoringService,
)


def build_scope_condition(
    *,
    category: str,
    significance_level:
        DiagnosticLevel,
    scope_level:
        DiagnosticScopeLevel,
    diagnosed: bool,
    systemic: bool,
) -> DiagnosticScopeCondition:
    return DiagnosticScopeCondition(
        category=category,
        significance_level=(
            significance_level
        ),
        scope_level=(
            scope_level
        ),
        unique_work_item_count=4,
        unique_actor_count=3,
        unique_team_count=2,
        unique_lifecycle_count=4,
        unique_source_count=2,
        active_day_count=8,
        scope_axes=(
            DiagnosticScopeAxes(
                process_breadth=True,
                organizational_breadth=(
                    scope_level
                    is DiagnosticScopeLevel.SYSTEMIC
                ),
                source_breadth=True,
                temporal_breadth=True,
            )
        ),
        is_diagnosed_condition=(
            diagnosed
        ),
        is_systemic_condition=(
            systemic
        ),
    )


def build_scope_summary(
    *,
    systemic_conditions: tuple[
        str,
        ...,
    ],
    dominant: str | None,
) -> AssessmentDiagnosticScopeSummary:
    all_categories = (
        "APPROVAL_DELAYED",
        "ENVIRONMENT_FAILURE",
        "ESCALATION",
        "OWNERSHIP_GAP",
        "SECURITY_REVIEW",
        "WORK_BLOCKED",
    )

    conditions = tuple(
        build_scope_condition(
            category=category,
            significance_level=(
                DiagnosticLevel.DOMINANT
                if category
                == dominant
                else DiagnosticLevel.SIGNIFICANT
            ),
            scope_level=(
                DiagnosticScopeLevel.SYSTEMIC
                if category
                in systemic_conditions
                else DiagnosticScopeLevel.CROSS_CONTEXT
            ),
            diagnosed=True,
            systemic=(
                category
                in systemic_conditions
            ),
        )
        for category
        in all_categories
    )

    return AssessmentDiagnosticScopeSummary(
        tenant_id="tenant-a",
        client_id="client-a",
        engagement_id="engagement-a",
        assessment_id="assessment-a",
        conditions=conditions,
        systemic_conditions=(
            systemic_conditions
        ),
        dominant_systemic_condition=(
            dominant
        ),
        scope_hash="a" * 64,
    )


def build_oracle(
    *conditions: str,
    dominant: str | None = None,
) -> dict:
    return {
        "schema_version": "1.0",
        "test_program": "PRELIVE-001",
        "oracle_status": "SEALED",
        "scenario_id": "test-scenario",
        "scenario_sha256": "b" * 64,
        "expected_conditions": [
            {
                "constraint_type":
                    condition
            }
            for condition
            in conditions
        ],
        "expected_dominant_constraint":
            dominant,
    }


def test_exact_systemic_match_scores_one():
    summary = build_scope_summary(
        systemic_conditions=(
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        ),
        dominant="SECURITY_REVIEW",
    )

    result = (
        PreliveSystemicDiagnosticReplayScoringService()
        .score(
            scope_summary=summary,
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

    assert (
        result.exact_condition_match
        is True
    )

    assert (
        result.dominant_constraint_match
        is True
    )


def test_cross_context_findings_are_not_false_positives():
    summary = build_scope_summary(
        systemic_conditions=(
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        ),
        dominant="SECURITY_REVIEW",
    )

    result = (
        PreliveSystemicDiagnosticReplayScoringService()
        .score(
            scope_summary=summary,
            oracle=build_oracle(
                "APPROVAL_DELAYED",
                "SECURITY_REVIEW",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    assert (
        "ENVIRONMENT_FAILURE"
        not in
        result.false_positives
    )

    assert (
        "ESCALATION"
        not in
        result.false_positives
    )

    assert (
        "OWNERSHIP_GAP"
        not in
        result.false_positives
    )

    assert (
        "WORK_BLOCKED"
        not in
        result.false_positives
    )


def test_extra_systemic_condition_is_false_positive():
    summary = build_scope_summary(
        systemic_conditions=(
            "APPROVAL_DELAYED",
            "ESCALATION",
            "SECURITY_REVIEW",
        ),
        dominant="SECURITY_REVIEW",
    )

    result = (
        PreliveSystemicDiagnosticReplayScoringService()
        .score(
            scope_summary=summary,
            oracle=build_oracle(
                "APPROVAL_DELAYED",
                "SECURITY_REVIEW",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    assert (
        result.false_positives
        == (
            "ESCALATION",
        )
    )

    assert (
        result.precision
        == round(
            2 / 3,
            4,
        )
    )


def test_missing_systemic_condition_is_false_negative():
    summary = build_scope_summary(
        systemic_conditions=(
            "SECURITY_REVIEW",
        ),
        dominant="SECURITY_REVIEW",
    )

    result = (
        PreliveSystemicDiagnosticReplayScoringService()
        .score(
            scope_summary=summary,
            oracle=build_oracle(
                "APPROVAL_DELAYED",
                "SECURITY_REVIEW",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    assert (
        result.false_negatives
        == (
            "APPROVAL_DELAYED",
        )
    )

    assert result.precision == 1.0
    assert result.recall == 0.5


def test_wrong_dominant_is_detected():
    summary = build_scope_summary(
        systemic_conditions=(
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        ),
        dominant="APPROVAL_DELAYED",
    )

    result = (
        PreliveSystemicDiagnosticReplayScoringService()
        .score(
            scope_summary=summary,
            oracle=build_oracle(
                "APPROVAL_DELAYED",
                "SECURITY_REVIEW",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    assert (
        result.dominant_constraint_match
        is False
    )


def test_expected_dominant_is_optional():
    summary = build_scope_summary(
        systemic_conditions=(
            "SECURITY_REVIEW",
        ),
        dominant="SECURITY_REVIEW",
    )

    result = (
        PreliveSystemicDiagnosticReplayScoringService()
        .score(
            scope_summary=summary,
            oracle=build_oracle(
                "SECURITY_REVIEW",
            ),
        )
    )

    assert (
        result.dominant_constraint_match
        is None
    )


def test_empty_systemic_set_can_score():
    summary = build_scope_summary(
        systemic_conditions=(),
        dominant=None,
    )

    result = (
        PreliveSystemicDiagnosticReplayScoringService()
        .score(
            scope_summary=summary,
            oracle=build_oracle(
                "SECURITY_REVIEW",
            ),
        )
    )

    assert result.precision == 1.0
    assert result.recall == 0.0
    assert result.f1 == 0.0

    assert (
        result.false_negatives
        == (
            "SECURITY_REVIEW",
        )
    )


def test_replay_is_deterministic():
    summary = build_scope_summary(
        systemic_conditions=(
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        ),
        dominant="SECURITY_REVIEW",
    )

    oracle = build_oracle(
        "APPROVAL_DELAYED",
        "SECURITY_REVIEW",
        dominant="SECURITY_REVIEW",
    )

    service = (
        PreliveSystemicDiagnosticReplayScoringService()
    )

    first = service.score(
        scope_summary=summary,
        oracle=oracle,
    )

    second = service.score(
        scope_summary=summary,
        oracle=oracle,
    )

    assert first == second

    assert (
        len(
            first.replay_hash
        )
        == 64
    )


def test_replay_binds_scope_hash():
    summary = build_scope_summary(
        systemic_conditions=(
            "SECURITY_REVIEW",
        ),
        dominant="SECURITY_REVIEW",
    )

    result = (
        PreliveSystemicDiagnosticReplayScoringService()
        .score(
            scope_summary=summary,
            oracle=build_oracle(
                "SECURITY_REVIEW",
            ),
        )
    )

    assert (
        result.scope_hash
        == summary.scope_hash
    )


def test_result_has_governance_boundary():
    summary = build_scope_summary(
        systemic_conditions=(
            "SECURITY_REVIEW",
        ),
        dominant="SECURITY_REVIEW",
    )

    result = (
        PreliveSystemicDiagnosticReplayScoringService()
        .score(
            scope_summary=summary,
            oracle=build_oracle(
                "SECURITY_REVIEW",
            ),
        )
    )

    assert (
        result.replay_status
        == PRELIVE_SYSTEMIC_REPLAY_STATUS
    )

    assert (
        result.authority
        == PRELIVE_SYSTEMIC_REPLAY_AUTHORITY
    )


def test_rejects_unsealed_oracle():
    summary = build_scope_summary(
        systemic_conditions=(
            "SECURITY_REVIEW",
        ),
        dominant="SECURITY_REVIEW",
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
            PreliveSystemicDiagnosticReplayScoringService()
            .score(
                scope_summary=summary,
                oracle=oracle,
            )
        )


def test_rejects_duplicate_oracle_conditions():
    summary = build_scope_summary(
        systemic_conditions=(
            "SECURITY_REVIEW",
        ),
        dominant="SECURITY_REVIEW",
    )

    with pytest.raises(
        PreliveScenarioError,
        match="duplicate",
    ):
        (
            PreliveSystemicDiagnosticReplayScoringService()
            .score(
                scope_summary=summary,
                oracle=build_oracle(
                    "SECURITY_REVIEW",
                    "SECURITY_REVIEW",
                ),
            )
        )


def test_rejects_dominant_not_in_oracle_conditions():
    summary = build_scope_summary(
        systemic_conditions=(
            "SECURITY_REVIEW",
        ),
        dominant="SECURITY_REVIEW",
    )

    with pytest.raises(
        PreliveScenarioError,
        match="must also be expected",
    ):
        (
            PreliveSystemicDiagnosticReplayScoringService()
            .score(
                scope_summary=summary,
                oracle=build_oracle(
                    "APPROVAL_DELAYED",
                    dominant="SECURITY_REVIEW",
                ),
            )
        )


def test_rejects_dominant_not_in_systemic_set():
    summary = (
        AssessmentDiagnosticScopeSummary(
            tenant_id="tenant-a",
            client_id="client-a",
            engagement_id="engagement-a",
            assessment_id="assessment-a",
            conditions=(),
            systemic_conditions=(
                "APPROVAL_DELAYED",
            ),
            dominant_systemic_condition=(
                "SECURITY_REVIEW"
            ),
            scope_hash="a" * 64,
        )
    )

    with pytest.raises(
        PreliveScenarioError,
        match="must also be systemic",
    ):
        (
            PreliveSystemicDiagnosticReplayScoringService()
            .score(
                scope_summary=summary,
                oracle=build_oracle(
                    "APPROVAL_DELAYED",
                ),
            )
        )


def test_result_serializes_systemic_metrics():
    summary = build_scope_summary(
        systemic_conditions=(
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        ),
        dominant="SECURITY_REVIEW",
    )

    result = (
        PreliveSystemicDiagnosticReplayScoringService()
        .score(
            scope_summary=summary,
            oracle=build_oracle(
                "APPROVAL_DELAYED",
                "SECURITY_REVIEW",
                dominant="SECURITY_REVIEW",
            ),
        )
    )

    payload = result.to_dict()

    assert payload[
        "systemic_conditions"
    ] == [
        "APPROVAL_DELAYED",
        "SECURITY_REVIEW",
    ]

    assert payload["precision"] == 1.0
    assert payload["recall"] == 1.0
    assert payload["f1"] == 1.0

    assert (
        len(
            payload[
                "replay_hash"
            ]
        )
        == 64
    )