from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from backend.app.gagf.governance_assessment_friction_aggregation import (
    ConstraintCategory,
)
from backend.app.gagf.governance_assessment_structural_importance import (
    ASSESSMENT_STRUCTURAL_IMPORTANCE_VERSION,
    STRUCTURAL_IMPORTANCE_AUTHORITY,
    GovernanceAssessmentStructuralImportanceService,
    StructuralImportanceError,
)


HIERARCHY_KEY = (
    "tenant-001/"
    "client-001/"
    "engagement-001/"
    "assessment-001"
)


def timestamp(
    hour: int,
    minute: int = 0,
) -> datetime:
    return datetime(
        2026,
        8,
        1,
        hour,
        minute,
        tzinfo=timezone.utc,
    )


def record(
    *,
    event_id: str,
    category: ConstraintCategory,
    occurred_at: datetime,
    lifecycle_id: str | None,
    duration_minutes: str | float | int = 0,
) -> SimpleNamespace:
    attributes: dict[str, str] = {
        "duration_minutes":
            str(duration_minutes),
    }

    if lifecycle_id is not None:
        attributes[
            "lifecycle_instance_id"
        ] = lifecycle_id

    return SimpleNamespace(
        event_id=event_id,
        event_type=category.value,
        occurred_at=occurred_at,
        attributes=attributes,
    )


def aggregation(
    *,
    category: ConstraintCategory,
    event_count: int,
    event_share: float,
    friction_score: float,
    band: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        category=category,
        event_count=event_count,
        event_share=event_share,
        friction_score=friction_score,
        band=SimpleNamespace(
            value=band,
        ),
    )


def significance_condition(
    *,
    category: ConstraintCategory,
    level: str = "significant",
    total_duration_minutes: float = 0.0,
    work_items: int = 1,
    actors: int = 1,
    teams: int = 1,
    lifecycles: int = 1,
    active_days: int = 1,
    evidence_quality: float | None = 0.9,
    support_count: int = 4,
) -> SimpleNamespace:
    return SimpleNamespace(
        category=category,
        level=SimpleNamespace(
            value=level,
        ),
        total_duration_minutes=(
            total_duration_minutes
        ),
        unique_work_item_count=(
            work_items
        ),
        unique_actor_count=actors,
        unique_team_count=teams,
        unique_lifecycle_count=(
            lifecycles
        ),
        active_day_count=(
            active_days
        ),
        mean_evidence_quality=(
            evidence_quality
        ),
        support_axes=SimpleNamespace(
            support_count=(
                support_count
            ),
        ),
    )


def scope_condition(
    *,
    category: ConstraintCategory,
    level: str = "cross_context",
    breadth_count: int = 2,
    diagnosed: bool = True,
    systemic: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        category=category.value,
        scope_level=SimpleNamespace(
            value=level,
        ),
        scope_axes=SimpleNamespace(
            breadth_count=(
                breadth_count
            ),
        ),
        is_diagnosed_condition=(
            diagnosed
        ),
        is_systemic_condition=(
            systemic
        ),
    )


def friction_summary(
    aggregations,
    *,
    hierarchy_key: str = HIERARCHY_KEY,
) -> SimpleNamespace:
    (
        tenant_id,
        client_id,
        engagement_id,
        assessment_id,
    ) = hierarchy_key.split("/")

    return SimpleNamespace(
        tenant_id=tenant_id,
        client_id=client_id,
        engagement_id=(
            engagement_id
        ),
        assessment_id=assessment_id,
        hierarchy_key=hierarchy_key,
        constraint_aggregations=(
            tuple(
                aggregations
            )
        ),
    )


def significance_summary(
    conditions,
    *,
    hierarchy_key: str = HIERARCHY_KEY,
) -> SimpleNamespace:
    return SimpleNamespace(
        hierarchy_key=hierarchy_key,
        conditions=tuple(
            conditions
        ),
    )


def scope_summary(
    conditions,
    *,
    hierarchy_key: str = HIERARCHY_KEY,
) -> SimpleNamespace:
    return SimpleNamespace(
        hierarchy_key=hierarchy_key,
        conditions=tuple(
            conditions
        ),
    )


def intake_result(
    records,
    *,
    hierarchy_key: str = HIERARCHY_KEY,
) -> SimpleNamespace:
    return SimpleNamespace(
        hierarchy_key=hierarchy_key,
        accepted_records=tuple(
            records
        ),
    )


def build_basic_inputs():
    approval = (
        ConstraintCategory
        .APPROVAL_REQUIRED
    )

    blocked = (
        ConstraintCategory
        .WORK_BLOCKED
    )

    records = (
        record(
            event_id="evt-001",
            category=approval,
            occurred_at=timestamp(9),
            lifecycle_id="life-001",
            duration_minutes=30,
        ),
        record(
            event_id="evt-002",
            category=blocked,
            occurred_at=timestamp(10),
            lifecycle_id="life-001",
            duration_minutes=120,
        ),
    )

    friction = friction_summary(
        (
            aggregation(
                category=approval,
                event_count=1,
                event_share=0.5,
                friction_score=2.0,
                band="moderate",
            ),
            aggregation(
                category=blocked,
                event_count=1,
                event_share=0.5,
                friction_score=3.0,
                band="high",
            ),
        )
    )

    significance = (
        significance_summary(
            (
                significance_condition(
                    category=approval,
                    total_duration_minutes=(
                        30.0
                    ),
                    work_items=1,
                    actors=1,
                    teams=1,
                    lifecycles=1,
                    active_days=1,
                    support_count=4,
                ),
                significance_condition(
                    category=blocked,
                    total_duration_minutes=(
                        120.0
                    ),
                    work_items=1,
                    actors=1,
                    teams=1,
                    lifecycles=1,
                    active_days=1,
                    support_count=4,
                ),
            )
        )
    )

    scope = scope_summary(
        (
            scope_condition(
                category=approval,
                level="localized",
                breadth_count=1,
                diagnosed=True,
                systemic=False,
            ),
            scope_condition(
                category=blocked,
                level="localized",
                breadth_count=1,
                diagnosed=True,
                systemic=False,
            ),
        )
    )

    intake = (
        intake_result(
            records
        ),
    )

    return (
        friction,
        significance,
        scope,
        intake,
    )


def condition_by_category(
    result,
    category: ConstraintCategory,
):
    return next(
        condition
        for condition
        in result.conditions
        if condition.category
        is category
    )


def test_analyze_returns_structural_evidence():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    result = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    assert (
        result.hierarchy_key
        == HIERARCHY_KEY
    )

    assert (
        result.condition_count
        == 2
    )

    assert (
        result.authority
        == STRUCTURAL_IMPORTANCE_AUTHORITY
    )

    assert (
        result.schema_version
        == ASSESSMENT_STRUCTURAL_IMPORTANCE_VERSION
    )


def test_conditions_are_ordered_deterministically():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    result = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    categories = tuple(
        condition.category.value
        for condition
        in result.conditions
    )

    assert categories == tuple(
        sorted(
            categories
        )
    )


def test_burden_preserves_existing_measurements():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    result = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    blocked = condition_by_category(
        result,
        ConstraintCategory.WORK_BLOCKED,
    )

    assert (
        blocked.burden.event_count
        == 1
    )

    assert (
        blocked.burden.event_share
        == 0.5
    )

    assert (
        blocked.burden.friction_score
        == 3.0
    )

    assert (
        blocked.burden.friction_band
        == "high"
    )

    assert (
        blocked
        .burden
        .total_duration_minutes
        == 120.0
    )


def test_penetration_comes_from_significance():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    significance.conditions[0]

    approval = (
        significance_condition(
            category=(
                ConstraintCategory
                .APPROVAL_REQUIRED
            ),
            total_duration_minutes=30,
            work_items=7,
            actors=5,
            teams=3,
            lifecycles=6,
            active_days=4,
        )
    )

    significance = (
        significance_summary(
            (
                approval,
                significance.conditions[1],
            )
        )
    )

    result = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    condition = (
        condition_by_category(
            result,
            ConstraintCategory
            .APPROVAL_REQUIRED,
        )
    )

    assert (
        condition
        .penetration
        .unique_work_item_count
        == 7
    )

    assert (
        condition
        .penetration
        .unique_actor_count
        == 5
    )

    assert (
        condition
        .penetration
        .unique_team_count
        == 3
    )

    assert (
        condition
        .penetration
        .unique_lifecycle_count
        == 6
    )

    assert (
        condition
        .penetration
        .active_day_count
        == 4
    )


def test_temporal_precedence_is_observed():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    result = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    approval = (
        condition_by_category(
            result,
            ConstraintCategory
            .APPROVAL_REQUIRED,
        )
    )

    assert (
        approval
        .temporal
        .precedence_opportunity_count
        == 1
    )

    assert (
        approval
        .temporal
        .precedence_count
        == 1
    )

    assert (
        approval
        .temporal
        .precedence_rate
        == 1.0
    )


def test_later_condition_does_not_get_precedence():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    result = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    blocked = condition_by_category(
        result,
        ConstraintCategory.WORK_BLOCKED,
    )

    assert (
        blocked
        .temporal
        .precedence_opportunity_count
        == 1
    )

    assert (
        blocked
        .temporal
        .precedence_count
        == 0
    )

    assert (
        blocked
        .temporal
        .precedence_rate
        == 0.0
    )


def test_downstream_association_is_measured():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    result = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    approval = (
        condition_by_category(
            result,
            ConstraintCategory
            .APPROVAL_REQUIRED,
        )
    )

    assert (
        approval
        .temporal
        .downstream_event_count
        == 1
    )

    assert (
        approval
        .temporal
        .downstream_constraint_count
        == 1
    )

    assert (
        approval
        .temporal
        .downstream_lifecycle_count
        == 1
    )

    assert (
        approval
        .temporal
        .downstream_duration_minutes
        == 120.0
    )


def test_same_timestamp_is_not_treated_as_precedence():
    approval = (
        ConstraintCategory
        .APPROVAL_REQUIRED
    )

    blocked = (
        ConstraintCategory
        .WORK_BLOCKED
    )

    shared_time = timestamp(9)

    intake = (
        intake_result(
            (
                record(
                    event_id="evt-001",
                    category=approval,
                    occurred_at=shared_time,
                    lifecycle_id=(
                        "life-001"
                    ),
                ),
                record(
                    event_id="evt-002",
                    category=blocked,
                    occurred_at=shared_time,
                    lifecycle_id=(
                        "life-001"
                    ),
                ),
            )
        ),
    )

    friction = friction_summary(
        (
            aggregation(
                category=approval,
                event_count=1,
                event_share=0.5,
                friction_score=1,
                band="low",
            ),
            aggregation(
                category=blocked,
                event_count=1,
                event_share=0.5,
                friction_score=1,
                band="low",
            ),
        )
    )

    significance = (
        significance_summary(
            (
                significance_condition(
                    category=approval,
                ),
                significance_condition(
                    category=blocked,
                ),
            )
        )
    )

    scope = scope_summary(
        (
            scope_condition(
                category=approval,
            ),
            scope_condition(
                category=blocked,
            ),
        )
    )

    result = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    approval_result = (
        condition_by_category(
            result,
            approval,
        )
    )

    assert (
        approval_result
        .temporal
        .precedence_count
        == 0
    )

    assert (
        approval_result
        .temporal
        .downstream_event_count
        == 0
    )


def test_missing_lifecycle_does_not_invent_sequence():
    (
        friction,
        significance,
        scope,
        _,
    ) = build_basic_inputs()

    intake = (
        intake_result(
            (
                record(
                    event_id="evt-001",
                    category=(
                        ConstraintCategory
                        .APPROVAL_REQUIRED
                    ),
                    occurred_at=timestamp(9),
                    lifecycle_id=None,
                    duration_minutes=30,
                ),
                record(
                    event_id="evt-002",
                    category=(
                        ConstraintCategory
                        .WORK_BLOCKED
                    ),
                    occurred_at=timestamp(10),
                    lifecycle_id=None,
                    duration_minutes=120,
                ),
            )
        ),
    )

    result = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    approval = (
        condition_by_category(
            result,
            ConstraintCategory
            .APPROVAL_REQUIRED,
        )
    )

    assert (
        approval
        .temporal
        .precedence_opportunity_count
        == 0
    )

    assert (
        approval
        .temporal
        .precedence_count
        == 0
    )

    assert (
        approval
        .temporal
        .downstream_event_count
        == 0
    )


def test_negative_downstream_duration_is_not_counted():
    (
        friction,
        significance,
        scope,
        _,
    ) = build_basic_inputs()

    intake = (
        intake_result(
            (
                record(
                    event_id="evt-001",
                    category=(
                        ConstraintCategory
                        .APPROVAL_REQUIRED
                    ),
                    occurred_at=timestamp(9),
                    lifecycle_id=(
                        "life-001"
                    ),
                    duration_minutes=30,
                ),
                record(
                    event_id="evt-002",
                    category=(
                        ConstraintCategory
                        .WORK_BLOCKED
                    ),
                    occurred_at=timestamp(10),
                    lifecycle_id=(
                        "life-001"
                    ),
                    duration_minutes=-100,
                ),
            )
        ),
    )

    result = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    approval = (
        condition_by_category(
            result,
            ConstraintCategory
            .APPROVAL_REQUIRED,
        )
    )

    assert (
        approval
        .temporal
        .downstream_event_count
        == 1
    )

    assert (
        approval
        .temporal
        .downstream_duration_minutes
        == 0.0
    )


def test_support_preserves_significance_and_scope():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    result = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    approval = (
        condition_by_category(
            result,
            ConstraintCategory
            .APPROVAL_REQUIRED,
        )
    )

    assert (
        approval
        .support
        .significance_level
        == "significant"
    )

    assert (
        approval
        .support
        .scope_level
        == "localized"
    )

    assert (
        approval
        .support
        .diagnostic_support_count
        == 4
    )

    assert (
        approval
        .support
        .scope_breadth_count
        == 1
    )

    assert (
        approval
        .support
        .is_diagnosed_condition
        is True
    )

    assert (
        approval
        .support
        .is_systemic_condition
        is False
    )


def test_summary_hash_is_deterministic():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    service = (
        GovernanceAssessmentStructuralImportanceService()
    )

    first = service.analyze(
        friction_summary=friction,
        significance_summary=(
            significance
        ),
        scope_summary=scope,
        intake_results=intake,
    )

    second = service.analyze(
        friction_summary=friction,
        significance_summary=(
            significance
        ),
        scope_summary=scope,
        intake_results=intake,
    )

    assert (
        first.summary_hash
        == second.summary_hash
    )

    assert tuple(
        condition.evidence_hash
        for condition
        in first.conditions
    ) == tuple(
        condition.evidence_hash
        for condition
        in second.conditions
    )


def test_record_order_does_not_change_hash():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    original = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    reversed_intake = (
        intake_result(
            tuple(
                reversed(
                    intake[0]
                    .accepted_records
                )
            )
        ),
    )

    reordered = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=(
                reversed_intake
            ),
        )
    )

    assert (
        original.summary_hash
        == reordered.summary_hash
    )


def test_mismatched_significance_hierarchy_is_rejected():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    significance = (
        significance_summary(
            significance.conditions,
            hierarchy_key=(
                "tenant-999/"
                "client-001/"
                "engagement-001/"
                "assessment-001"
            ),
        )
    )

    with pytest.raises(
        StructuralImportanceError,
        match="significance",
    ):
        (
            GovernanceAssessmentStructuralImportanceService()
            .analyze(
                friction_summary=(
                    friction
                ),
                significance_summary=(
                    significance
                ),
                scope_summary=scope,
                intake_results=(
                    intake
                ),
            )
        )


def test_mismatched_scope_hierarchy_is_rejected():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    scope = scope_summary(
        scope.conditions,
        hierarchy_key=(
            "tenant-999/"
            "client-001/"
            "engagement-001/"
            "assessment-001"
        ),
    )

    with pytest.raises(
        StructuralImportanceError,
        match="scope",
    ):
        (
            GovernanceAssessmentStructuralImportanceService()
            .analyze(
                friction_summary=(
                    friction
                ),
                significance_summary=(
                    significance
                ),
                scope_summary=scope,
                intake_results=(
                    intake
                ),
            )
        )


def test_mismatched_intake_hierarchy_is_rejected():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    bad_intake = (
        intake_result(
            intake[0].accepted_records,
            hierarchy_key=(
                "tenant-999/"
                "client-001/"
                "engagement-001/"
                "assessment-001"
            ),
        ),
    )

    with pytest.raises(
        StructuralImportanceError,
        match="Evidence intake",
    ):
        (
            GovernanceAssessmentStructuralImportanceService()
            .analyze(
                friction_summary=(
                    friction
                ),
                significance_summary=(
                    significance
                ),
                scope_summary=scope,
                intake_results=(
                    bad_intake
                ),
            )
        )


def test_missing_significance_condition_is_rejected():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    significance = (
        significance_summary(
            (
                significance.conditions[
                    0
                ],
            )
        )
    )

    with pytest.raises(
        StructuralImportanceError,
        match="Significance summary",
    ):
        (
            GovernanceAssessmentStructuralImportanceService()
            .analyze(
                friction_summary=(
                    friction
                ),
                significance_summary=(
                    significance
                ),
                scope_summary=scope,
                intake_results=(
                    intake
                ),
            )
        )


def test_missing_scope_condition_is_rejected():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    scope = scope_summary(
        (
            scope.conditions[0],
        )
    )

    with pytest.raises(
        StructuralImportanceError,
        match="Scope summary",
    ):
        (
            GovernanceAssessmentStructuralImportanceService()
            .analyze(
                friction_summary=(
                    friction
                ),
                significance_summary=(
                    significance
                ),
                scope_summary=scope,
                intake_results=(
                    intake
                ),
            )
        )


def test_output_contains_no_primary_or_root_cause_claim():
    (
        friction,
        significance,
        scope,
        intake,
    ) = build_basic_inputs()

    result = (
        GovernanceAssessmentStructuralImportanceService()
        .analyze(
            friction_summary=friction,
            significance_summary=(
                significance
            ),
            scope_summary=scope,
            intake_results=intake,
        )
    )

    payload = result.to_dict()

    payload_text = str(
        payload
    ).lower()

    assert (
        "primary_condition"
        not in payload_text
    )

    assert (
        "root_cause"
        not in payload_text
    )

    assert (
        "causal"
        not in payload_text
    )