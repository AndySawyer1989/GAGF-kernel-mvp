from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from backend.app.gagf.governance_assessment_diagnostic_scope import (
    ASSESSMENT_DIAGNOSTIC_SCOPE_VERSION,
    DiagnosticScopeError,
    DiagnosticScopeLevel,
    GovernanceAssessmentDiagnosticScopeService,
)
from backend.app.gagf.governance_assessment_diagnostic_significance import (
    AssessmentDiagnosticSignificanceSummary,
    DiagnosticCondition,
    DiagnosticLevel,
    DiagnosticSupportAxes,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    ConstraintCategory,
)


def support_axes() -> DiagnosticSupportAxes:
    return DiagnosticSupportAxes(
        recurrence=True,
        work_item_spread=True,
        actor_spread=True,
        team_spread=True,
        lifecycle_spread=True,
        source_diversity=True,
        temporal_persistence=True,
        evidence_quality=True,
    )


def build_condition(
    *,
    category:
        ConstraintCategory,
    level:
        DiagnosticLevel = DiagnosticLevel.SIGNIFICANT,
    work_items: int = 1,
    actors: int = 1,
    teams: int = 1,
    lifecycles: int = 1,
    sources: int = 1,
    active_days: int = 1,
) -> DiagnosticCondition:
    return DiagnosticCondition(
        category=category,
        level=level,
        event_count=5,
        event_share=0.1,
        friction_score=10.0,
        friction_band="high",
        unique_work_item_count=work_items,
        unique_actor_count=actors,
        unique_team_count=teams,
        unique_lifecycle_count=lifecycles,
        unique_source_count=sources,
        active_day_count=active_days,
        mean_evidence_quality=0.9,
        total_duration_minutes=120.0,
        support_axes=support_axes(),
        first_occurred_on=date(
            2026,
            8,
            1,
        ),
        last_occurred_on=date(
            2026,
            8,
            max(
                1,
                min(
                    active_days,
                    28,
                ),
            ),
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
    *conditions:
        DiagnosticCondition,
    dominant:
        ConstraintCategory
        | None = None,
) -> AssessmentDiagnosticSignificanceSummary:
    diagnosed = tuple(
        condition.category
        for condition
        in conditions
        if condition.is_diagnosed_condition
    )

    return (
        AssessmentDiagnosticSignificanceSummary(
            tenant_id="tenant-a",
            client_id="client-a",
            engagement_id="engagement-a",
            assessment_id="assessment-a",
            conditions=conditions,
            diagnosed_conditions=diagnosed,
            dominant_condition=dominant,
            summary_hash="a" * 64,
        )
    )


def classify_one(
    condition:
        DiagnosticCondition,
):
    result = (
        GovernanceAssessmentDiagnosticScopeService()
        .classify(
            significance_summary=(
                build_summary(
                    condition
                )
            )
        )
    )

    return result.conditions[0]


def test_single_context_is_localized():
    condition = build_condition(
        category=(
            ConstraintCategory
            .APPROVAL_REQUIRED
        ),
        work_items=1,
        actors=1,
        teams=1,
        lifecycles=1,
        sources=1,
        active_days=1,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.scope_level
        is DiagnosticScopeLevel.LOCALIZED
    )

    assert (
        scoped.scope_axes.breadth_count
        == 0
    )


def test_process_breadth_requires_work_and_lifecycle_spread():
    condition = build_condition(
        category=(
            ConstraintCategory
            .ENVIRONMENT_FAILURE
        ),
        work_items=3,
        actors=1,
        teams=1,
        lifecycles=3,
        sources=1,
        active_days=1,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.scope_axes
        .process_breadth
        is True
    )


def test_work_item_spread_alone_is_not_process_breadth():
    condition = build_condition(
        category=(
            ConstraintCategory
            .ENVIRONMENT_FAILURE
        ),
        work_items=3,
        actors=1,
        teams=1,
        lifecycles=1,
        sources=1,
        active_days=1,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.scope_axes
        .process_breadth
        is False
    )


def test_organizational_breadth_requires_actor_and_team_spread():
    condition = build_condition(
        category=(
            ConstraintCategory
            .APPROVAL_DELAYED
        ),
        work_items=1,
        actors=4,
        teams=3,
        lifecycles=1,
        sources=1,
        active_days=1,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.scope_axes
        .organizational_breadth
        is True
    )


def test_actor_spread_without_team_spread_is_not_organizational():
    condition = build_condition(
        category=(
            ConstraintCategory
            .OWNERSHIP_GAP
        ),
        work_items=2,
        actors=4,
        teams=1,
        lifecycles=2,
        sources=1,
        active_days=4,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.scope_axes
        .organizational_breadth
        is False
    )


def test_source_breadth_requires_multiple_sources():
    condition = build_condition(
        category=(
            ConstraintCategory
            .SECURITY_REVIEW
        ),
        sources=2,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.scope_axes
        .source_breadth
        is True
    )


def test_temporal_breadth_requires_persistence():
    condition = build_condition(
        category=(
            ConstraintCategory
            .ESCALATION
        ),
        active_days=3,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.scope_axes
        .temporal_breadth
        is True
    )


def test_two_breadth_axes_are_cross_context():
    condition = build_condition(
        category=(
            ConstraintCategory
            .WORK_BLOCKED
        ),
        work_items=2,
        actors=1,
        teams=1,
        lifecycles=2,
        sources=1,
        active_days=4,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.scope_axes
        .process_breadth
        is True
    )

    assert (
        scoped.scope_axes
        .temporal_breadth
        is True
    )

    assert (
        scoped.scope_level
        is DiagnosticScopeLevel.CROSS_CONTEXT
    )


def test_process_org_and_temporal_is_systemic():
    condition = build_condition(
        category=(
            ConstraintCategory
            .APPROVAL_DELAYED
        ),
        work_items=4,
        actors=4,
        teams=3,
        lifecycles=4,
        sources=1,
        active_days=8,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.scope_level
        is DiagnosticScopeLevel.SYSTEMIC
    )


def test_source_diversity_is_not_required_for_systemic():
    condition = build_condition(
        category=(
            ConstraintCategory
            .APPROVAL_DELAYED
        ),
        work_items=4,
        actors=4,
        teams=3,
        lifecycles=4,
        sources=1,
        active_days=8,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.scope_axes
        .source_breadth
        is False
    )

    assert (
        scoped.scope_level
        is DiagnosticScopeLevel.SYSTEMIC
    )


def test_security_review_example_is_systemic():
    condition = build_condition(
        category=(
            ConstraintCategory
            .SECURITY_REVIEW
        ),
        level=(
            DiagnosticLevel.DOMINANT
        ),
        work_items=21,
        actors=3,
        teams=2,
        lifecycles=21,
        sources=2,
        active_days=25,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.scope_axes
        .breadth_count
        == 4
    )

    assert (
        scoped.scope_level
        is DiagnosticScopeLevel.SYSTEMIC
    )


def test_localized_significance_is_preserved():
    condition = build_condition(
        category=(
            ConstraintCategory
            .ENVIRONMENT_FAILURE
        ),
        level=(
            DiagnosticLevel.SIGNIFICANT
        ),
        work_items=1,
        actors=1,
        teams=1,
        lifecycles=1,
        sources=1,
        active_days=1,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.significance_level
        is DiagnosticLevel.SIGNIFICANT
    )

    assert (
        scoped.scope_level
        is DiagnosticScopeLevel.LOCALIZED
    )

    assert (
        scoped.is_diagnosed_condition
        is True
    )


def test_observed_condition_can_have_scope_without_becoming_diagnosed():
    condition = build_condition(
        category=(
            ConstraintCategory
            .APPROVAL_REQUIRED
        ),
        level=(
            DiagnosticLevel.OBSERVED
        ),
        work_items=5,
        actors=4,
        teams=3,
        lifecycles=5,
        sources=2,
        active_days=5,
    )

    scoped = classify_one(
        condition
    )

    assert (
        scoped.scope_level
        is DiagnosticScopeLevel.SYSTEMIC
    )

    assert (
        scoped.is_diagnosed_condition
        is False
    )


def test_summary_exposes_only_diagnosed_systemic_conditions():
    approval = build_condition(
        category=(
            ConstraintCategory
            .APPROVAL_DELAYED
        ),
        work_items=4,
        actors=4,
        teams=3,
        lifecycles=4,
        sources=1,
        active_days=8,
    )

    security = build_condition(
        category=(
            ConstraintCategory
            .SECURITY_REVIEW
        ),
        level=(
            DiagnosticLevel.DOMINANT
        ),
        work_items=21,
        actors=3,
        teams=2,
        lifecycles=21,
        sources=2,
        active_days=25,
    )

    escalation = build_condition(
        category=(
            ConstraintCategory
            .ESCALATION
        ),
        work_items=3,
        actors=1,
        teams=1,
        lifecycles=3,
        sources=1,
        active_days=3,
    )

    observed = build_condition(
        category=(
            ConstraintCategory
            .APPROVAL_REQUIRED
        ),
        level=(
            DiagnosticLevel.OBSERVED
        ),
        work_items=5,
        actors=4,
        teams=3,
        lifecycles=5,
        sources=2,
        active_days=5,
    )

    result = (
        GovernanceAssessmentDiagnosticScopeService()
        .classify(
            significance_summary=(
                build_summary(
                    approval,
                    security,
                    escalation,
                    observed,
                    dominant=(
                        ConstraintCategory
                        .SECURITY_REVIEW
                    ),
                )
            )
        )
    )

    assert (
        result.systemic_conditions
        == (
            "APPROVAL_DELAYED",
            "SECURITY_REVIEW",
        )
    )

    assert (
        result.dominant_systemic_condition
        == "SECURITY_REVIEW"
    )


def test_scope_summary_hash_is_deterministic():
    condition = build_condition(
        category=(
            ConstraintCategory
            .SECURITY_REVIEW
        ),
        level=(
            DiagnosticLevel.DOMINANT
        ),
        work_items=21,
        actors=3,
        teams=2,
        lifecycles=21,
        sources=2,
        active_days=25,
    )

    summary = build_summary(
        condition,
        dominant=(
            ConstraintCategory
            .SECURITY_REVIEW
        ),
    )

    service = (
        GovernanceAssessmentDiagnosticScopeService()
    )

    first = service.classify(
        significance_summary=summary
    )

    second = service.classify(
        significance_summary=summary
    )

    assert first == second

    assert (
        first.scope_hash
        == second.scope_hash
    )

    assert (
        len(
            first.scope_hash
        )
        == 64
    )


def test_negative_scope_count_is_rejected():
    condition = build_condition(
        category=(
            ConstraintCategory
            .WORK_BLOCKED
        ),
        work_items=-1,
    )

    with pytest.raises(
        DiagnosticScopeError,
        match="negative",
    ):
        classify_one(
            condition
        )


def test_scope_result_is_immutable():
    condition = build_condition(
        category=(
            ConstraintCategory
            .SECURITY_REVIEW
        ),
        work_items=21,
        actors=3,
        teams=2,
        lifecycles=21,
        sources=2,
        active_days=25,
    )

    result = (
        GovernanceAssessmentDiagnosticScopeService()
        .classify(
            significance_summary=(
                build_summary(
                    condition
                )
            )
        )
    )

    scoped = result.conditions[0]

    with pytest.raises(
        FrozenInstanceError
    ):
        scoped.active_day_count = 99

    with pytest.raises(
        FrozenInstanceError
    ):
        result.scope_hash = "changed"


def test_schema_version_is_explicit():
    condition = build_condition(
        category=(
            ConstraintCategory
            .SECURITY_REVIEW
        )
    )

    result = (
        GovernanceAssessmentDiagnosticScopeService()
        .classify(
            significance_summary=(
                build_summary(
                    condition
                )
            )
        )
    )

    assert (
        result.schema_version
        == ASSESSMENT_DIAGNOSTIC_SCOPE_VERSION
    )