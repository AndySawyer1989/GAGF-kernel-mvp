from __future__ import annotations

from dataclasses import (
    FrozenInstanceError,
)
from datetime import (
    datetime,
    timezone,
)

import pytest

from backend.app.gagf.governance_assessment_diagnostic_significance import (
    ASSESSMENT_DIAGNOSTIC_SIGNIFICANCE_VERSION,
    DiagnosticLevel,
    DiagnosticSignificanceError,
    GovernanceAssessmentDiagnosticSignificanceService,
)
from backend.app.gagf.governance_assessment_evidence_intake import (
    AssessmentEvidenceIntakeResult,
    AssessmentEvidenceRecord,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    AssessmentFrictionSummary,
    ConstraintAggregation,
    ConstraintCategory,
    FrictionBand,
)


HIERARCHY = (
    "tenant-a/client-a/"
    "engagement-a/assessment-a"
)


def build_record(
    *,
    event_id: str,
    category: ConstraintCategory,
    occurred_at: str,
    work_item_id: str,
    actor_id: str,
    team_id: str,
    lifecycle_id: str,
    source: str,
    evidence_quality: str = "0.90",
    duration_minutes: str = "30",
) -> AssessmentEvidenceRecord:
    parsed = datetime.fromisoformat(
        occurred_at
    ).astimezone(
        timezone.utc
    )

    return AssessmentEvidenceRecord(
        tenant_id="tenant-a",
        client_id="client-a",
        engagement_id="engagement-a",
        assessment_id="assessment-a",
        source_id="csv-source",
        event_id=event_id,
        event_type=category.value,
        occurred_at=parsed,
        attributes={
            "work_item_id":
                work_item_id,
            "actor_id":
                actor_id,
            "team_id":
                team_id,
            "lifecycle_instance_id":
                lifecycle_id,
            "source":
                source,
            "evidence_quality":
                evidence_quality,
            "duration_minutes":
                duration_minutes,
        },
        row_number=2,
        evidence_hash=(
            f"hash-{event_id}"
        ),
    )


def build_intake(
    records: tuple[
        AssessmentEvidenceRecord,
        ...,
    ],
    *,
    hierarchy_key: str = HIERARCHY,
) -> AssessmentEvidenceIntakeResult:
    class Source:
        source_id = "csv-source"

    return AssessmentEvidenceIntakeResult(
        source=Source(),
        hierarchy_key=hierarchy_key,
        accepted_records=records,
        rejected_rows=(),
        total_rows=len(records),
        intake_hash="intake-hash",
    )


def build_aggregation(
    *,
    category: ConstraintCategory,
    event_count: int,
    unique_work_item_count: int,
    event_share: float,
    friction_score: float,
    band: FrictionBand,
    first: str,
    last: str,
) -> ConstraintAggregation:
    return ConstraintAggregation(
        category=category,
        event_count=event_count,
        unique_work_item_count=(
            unique_work_item_count
        ),
        first_occurred_at=(
            datetime.fromisoformat(
                first
            ).astimezone(
                timezone.utc
            )
        ),
        last_occurred_at=(
            datetime.fromisoformat(
                last
            ).astimezone(
                timezone.utc
            )
        ),
        weight=1.0,
        friction_score=(
            friction_score
        ),
        event_share=event_share,
        band=band,
    )


def build_summary(
    aggregations: tuple[
        ConstraintAggregation,
        ...,
    ],
    *,
    dominant:
        ConstraintCategory
        | None,
) -> AssessmentFrictionSummary:
    total_events = sum(
        item.event_count
        for item
        in aggregations
    )

    return AssessmentFrictionSummary(
        tenant_id="tenant-a",
        client_id="client-a",
        engagement_id="engagement-a",
        assessment_id="assessment-a",
        constraint_aggregations=(
            aggregations
        ),
        total_evidence_events=(
            total_events
        ),
        recognized_constraint_events=(
            total_events
        ),
        unrecognized_event_count=0,
        unique_work_item_count=sum(
            item.unique_work_item_count
            for item
            in aggregations
        ),
        total_friction_score=sum(
            item.friction_score
            for item
            in aggregations
        ),
        average_friction_per_event=1.0,
        dominant_constraint=dominant,
        unrecognized_event_types=(),
        summary_hash="friction-hash",
    )


def classify_one(
    *,
    records: tuple[
        AssessmentEvidenceRecord,
        ...,
    ],
    aggregation:
        ConstraintAggregation,
    dominant:
        ConstraintCategory
        | None,
):
    result = (
        GovernanceAssessmentDiagnosticSignificanceService()
        .classify(
            friction_summary=(
                build_summary(
                    (aggregation,),
                    dominant=dominant,
                )
            ),
            intake_results=(
                build_intake(
                    records
                ),
            ),
        )
    )

    return result.conditions[0]


def test_single_event_is_observed():
    record = build_record(
        event_id="event-1",
        category=(
            ConstraintCategory
            .APPROVAL_REQUIRED
        ),
        occurred_at=(
            "2026-08-01T10:00:00+00:00"
        ),
        work_item_id="work-1",
        actor_id="actor-1",
        team_id="team-1",
        lifecycle_id="life-1",
        source="jira",
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .APPROVAL_REQUIRED
        ),
        event_count=1,
        unique_work_item_count=1,
        event_share=1.0,
        friction_score=1.0,
        band=FrictionBand.LOW,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-01T10:00:00+00:00"
        ),
    )

    condition = classify_one(
        records=(record,),
        aggregation=aggregation,
        dominant=(
            ConstraintCategory
            .APPROVAL_REQUIRED
        ),
    )

    assert (
        condition.level
        is DiagnosticLevel.OBSERVED
    )

    assert (
        condition.is_diagnosed_condition
        is False
    )


def test_repeated_single_context_is_observed():
    records = tuple(
        build_record(
            event_id=f"event-{index}",
            category=(
                ConstraintCategory
                .DEPENDENCY_WAIT
            ),
            occurred_at=(
                "2026-08-01T10:00:00+00:00"
            ),
            work_item_id="work-1",
            actor_id="actor-1",
            team_id="team-1",
            lifecycle_id="life-1",
            source="jira",
        )
        for index in range(
            1,
            4,
        )
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .DEPENDENCY_WAIT
        ),
        event_count=3,
        unique_work_item_count=1,
        event_share=1.0,
        friction_score=4.5,
        band=FrictionBand.MODERATE,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-01T10:00:00+00:00"
        ),
    )

    condition = classify_one(
        records=records,
        aggregation=aggregation,
        dominant=(
            ConstraintCategory
            .DEPENDENCY_WAIT
        ),
    )

    assert (
        condition.support_axes
        .recurrence
        is True
    )

    assert (
        condition.support_axes
        .context_spread_count
        == 0
    )

    assert (
        condition.level
        is DiagnosticLevel.OBSERVED
    )


def test_recurring_requires_context_spread():
    records = (
        build_record(
            event_id="event-1",
            category=(
                ConstraintCategory
                .ENVIRONMENT_FAILURE
            ),
            occurred_at=(
                "2026-08-01T10:00:00+00:00"
            ),
            work_item_id="work-1",
            actor_id="actor-1",
            team_id="team-1",
            lifecycle_id="life-1",
            source="monitoring",
            evidence_quality="0.50",
        ),
        build_record(
            event_id="event-2",
            category=(
                ConstraintCategory
                .ENVIRONMENT_FAILURE
            ),
            occurred_at=(
                "2026-08-01T11:00:00+00:00"
            ),
            work_item_id="work-2",
            actor_id="actor-1",
            team_id="team-1",
            lifecycle_id="life-1",
            source="monitoring",
            evidence_quality="0.50",
        ),
        build_record(
            event_id="event-3",
            category=(
                ConstraintCategory
                .ENVIRONMENT_FAILURE
            ),
            occurred_at=(
                "2026-08-01T12:00:00+00:00"
            ),
            work_item_id="work-2",
            actor_id="actor-1",
            team_id="team-1",
            lifecycle_id="life-1",
            source="monitoring",
            evidence_quality="0.50",
        ),
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .ENVIRONMENT_FAILURE
        ),
        event_count=3,
        unique_work_item_count=2,
        event_share=1.0,
        friction_score=7.5,
        band=FrictionBand.MODERATE,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-01T12:00:00+00:00"
        ),
    )

    condition = classify_one(
        records=records,
        aggregation=aggregation,
        dominant=(
            ConstraintCategory
            .ENVIRONMENT_FAILURE
        ),
    )

    assert (
        condition.level
        is DiagnosticLevel.RECURRING
    )

    assert (
        condition.is_diagnosed_condition
        is False
    )


def test_multi_axis_corroboration_is_significant():
    records = (
        build_record(
            event_id="event-1",
            category=(
                ConstraintCategory
                .APPROVAL_DELAYED
            ),
            occurred_at=(
                "2026-08-01T10:00:00+00:00"
            ),
            work_item_id="work-1",
            actor_id="actor-1",
            team_id="team-1",
            lifecycle_id="life-1",
            source="jira",
        ),
        build_record(
            event_id="event-2",
            category=(
                ConstraintCategory
                .APPROVAL_DELAYED
            ),
            occurred_at=(
                "2026-08-02T10:00:00+00:00"
            ),
            work_item_id="work-2",
            actor_id="actor-2",
            team_id="team-1",
            lifecycle_id="life-2",
            source="jira",
        ),
        build_record(
            event_id="event-3",
            category=(
                ConstraintCategory
                .APPROVAL_DELAYED
            ),
            occurred_at=(
                "2026-08-02T11:00:00+00:00"
            ),
            work_item_id="work-2",
            actor_id="actor-2",
            team_id="team-1",
            lifecycle_id="life-2",
            source="jira",
        ),
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .APPROVAL_DELAYED
        ),
        event_count=3,
        unique_work_item_count=2,
        event_share=1.0,
        friction_score=6.0,
        band=FrictionBand.MODERATE,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-02T11:00:00+00:00"
        ),
    )

    condition = classify_one(
        records=records,
        aggregation=aggregation,
        dominant=None,
    )

    assert (
        condition.support_axes
        .support_count
        >= 4
    )

    assert (
        condition.level
        is DiagnosticLevel.SIGNIFICANT
    )

    assert (
        condition.is_diagnosed_condition
        is True
    )


def test_dominant_requires_significance_first():
    records = (
        build_record(
            event_id="event-1",
            category=(
                ConstraintCategory
                .SECURITY_REVIEW
            ),
            occurred_at=(
                "2026-08-01T10:00:00+00:00"
            ),
            work_item_id="work-1",
            actor_id="actor-1",
            team_id="team-1",
            lifecycle_id="life-1",
            source="defender",
        ),
        build_record(
            event_id="event-2",
            category=(
                ConstraintCategory
                .SECURITY_REVIEW
            ),
            occurred_at=(
                "2026-08-02T10:00:00+00:00"
            ),
            work_item_id="work-2",
            actor_id="actor-2",
            team_id="team-2",
            lifecycle_id="life-2",
            source="sentinel",
        ),
        build_record(
            event_id="event-3",
            category=(
                ConstraintCategory
                .SECURITY_REVIEW
            ),
            occurred_at=(
                "2026-08-03T10:00:00+00:00"
            ),
            work_item_id="work-3",
            actor_id="actor-3",
            team_id="team-2",
            lifecycle_id="life-3",
            source="defender",
        ),
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .SECURITY_REVIEW
        ),
        event_count=3,
        unique_work_item_count=3,
        event_share=1.0,
        friction_score=4.5,
        band=FrictionBand.MODERATE,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-03T10:00:00+00:00"
        ),
    )

    condition = classify_one(
        records=records,
        aggregation=aggregation,
        dominant=(
            ConstraintCategory
            .SECURITY_REVIEW
        ),
    )

    assert (
        condition.support_axes
        .support_count
        >= 5
    )

    assert (
        condition.level
        is DiagnosticLevel.DOMINANT
    )

    assert (
        condition.is_diagnosed_condition
        is True
    )


def test_non_dominant_significant_stays_significant():
    records = (
        build_record(
            event_id="event-1",
            category=(
                ConstraintCategory
                .APPROVAL_DELAYED
            ),
            occurred_at=(
                "2026-08-01T10:00:00+00:00"
            ),
            work_item_id="work-1",
            actor_id="actor-1",
            team_id="team-1",
            lifecycle_id="life-1",
            source="jira",
        ),
        build_record(
            event_id="event-2",
            category=(
                ConstraintCategory
                .APPROVAL_DELAYED
            ),
            occurred_at=(
                "2026-08-02T10:00:00+00:00"
            ),
            work_item_id="work-2",
            actor_id="actor-2",
            team_id="team-2",
            lifecycle_id="life-2",
            source="servicenow",
        ),
        build_record(
            event_id="event-3",
            category=(
                ConstraintCategory
                .APPROVAL_DELAYED
            ),
            occurred_at=(
                "2026-08-03T10:00:00+00:00"
            ),
            work_item_id="work-3",
            actor_id="actor-3",
            team_id="team-2",
            lifecycle_id="life-3",
            source="jira",
        ),
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .APPROVAL_DELAYED
        ),
        event_count=3,
        unique_work_item_count=3,
        event_share=1.0,
        friction_score=6.0,
        band=FrictionBand.MODERATE,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-03T10:00:00+00:00"
        ),
    )

    condition = classify_one(
        records=records,
        aggregation=aggregation,
        dominant=(
            ConstraintCategory
            .SECURITY_REVIEW
        ),
    )

    assert (
        condition.level
        is DiagnosticLevel.SIGNIFICANT
    )


def test_mean_evidence_quality_is_measured():
    records = (
        build_record(
            event_id="event-1",
            category=(
                ConstraintCategory
                .WORK_BLOCKED
            ),
            occurred_at=(
                "2026-08-01T10:00:00+00:00"
            ),
            work_item_id="work-1",
            actor_id="actor-1",
            team_id="team-1",
            lifecycle_id="life-1",
            source="jira",
            evidence_quality="0.80",
        ),
        build_record(
            event_id="event-2",
            category=(
                ConstraintCategory
                .WORK_BLOCKED
            ),
            occurred_at=(
                "2026-08-02T10:00:00+00:00"
            ),
            work_item_id="work-2",
            actor_id="actor-2",
            team_id="team-2",
            lifecycle_id="life-2",
            source="servicenow",
            evidence_quality="1.00",
        ),
        build_record(
            event_id="event-3",
            category=(
                ConstraintCategory
                .WORK_BLOCKED
            ),
            occurred_at=(
                "2026-08-03T10:00:00+00:00"
            ),
            work_item_id="work-3",
            actor_id="actor-3",
            team_id="team-3",
            lifecycle_id="life-3",
            source="jira",
            evidence_quality="0.90",
        ),
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .WORK_BLOCKED
        ),
        event_count=3,
        unique_work_item_count=3,
        event_share=1.0,
        friction_score=9.0,
        band=FrictionBand.HIGH,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-03T10:00:00+00:00"
        ),
    )

    condition = classify_one(
        records=records,
        aggregation=aggregation,
        dominant=(
            ConstraintCategory
            .WORK_BLOCKED
        ),
    )

    assert (
        condition.mean_evidence_quality
        == 0.9
    )

    assert (
        condition.support_axes
        .evidence_quality
        is True
    )


def test_duration_is_measured_not_used_as_magic_gate():
    records = tuple(
        build_record(
            event_id=f"event-{index}",
            category=(
                ConstraintCategory
                .ESCALATION
            ),
            occurred_at=(
                f"2026-08-0{index}"
                "T10:00:00+00:00"
            ),
            work_item_id=(
                f"work-{index}"
            ),
            actor_id=(
                f"actor-{index}"
            ),
            team_id=(
                f"team-{index}"
            ),
            lifecycle_id=(
                f"life-{index}"
            ),
            source=(
                "jira"
                if index % 2
                else "servicenow"
            ),
            duration_minutes="60",
        )
        for index in range(
            1,
            4,
        )
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .ESCALATION
        ),
        event_count=3,
        unique_work_item_count=3,
        event_share=1.0,
        friction_score=6.0,
        band=FrictionBand.MODERATE,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-03T10:00:00+00:00"
        ),
    )

    condition = classify_one(
        records=records,
        aggregation=aggregation,
        dominant=(
            ConstraintCategory
            .ESCALATION
        ),
    )

    assert (
        condition.total_duration_minutes
        == 180.0
    )

    assert (
        condition.level
        is DiagnosticLevel.DOMINANT
    )


def test_classification_does_not_depend_on_event_share():
    records = tuple(
        build_record(
            event_id=f"event-{index}",
            category=(
                ConstraintCategory
                .OWNERSHIP_GAP
            ),
            occurred_at=(
                f"2026-08-0{index}"
                "T10:00:00+00:00"
            ),
            work_item_id=(
                f"work-{index}"
            ),
            actor_id=(
                f"actor-{index}"
            ),
            team_id=(
                f"team-{index}"
            ),
            lifecycle_id=(
                f"life-{index}"
            ),
            source=(
                "jira"
                if index % 2
                else "servicenow"
            ),
        )
        for index in range(
            1,
            4,
        )
    )

    low_share = build_aggregation(
        category=(
            ConstraintCategory
            .OWNERSHIP_GAP
        ),
        event_count=3,
        unique_work_item_count=3,
        event_share=0.01,
        friction_score=7.5,
        band=FrictionBand.MODERATE,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-03T10:00:00+00:00"
        ),
    )

    high_share = build_aggregation(
        category=(
            ConstraintCategory
            .OWNERSHIP_GAP
        ),
        event_count=3,
        unique_work_item_count=3,
        event_share=0.90,
        friction_score=7.5,
        band=FrictionBand.MODERATE,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-03T10:00:00+00:00"
        ),
    )

    low_condition = classify_one(
        records=records,
        aggregation=low_share,
        dominant=None,
    )

    high_condition = classify_one(
        records=records,
        aggregation=high_share,
        dominant=None,
    )

    assert (
        low_condition.level
        == high_condition.level
    )

    assert (
        low_condition.level
        is DiagnosticLevel.SIGNIFICANT
    )


def test_summary_exposes_only_significant_and_dominant_as_diagnosed():
    observed_record = build_record(
        event_id="observed-1",
        category=(
            ConstraintCategory
            .APPROVAL_REQUIRED
        ),
        occurred_at=(
            "2026-08-01T10:00:00+00:00"
        ),
        work_item_id="work-o",
        actor_id="actor-o",
        team_id="team-o",
        lifecycle_id="life-o",
        source="jira",
    )

    significant_records = tuple(
        build_record(
            event_id=f"significant-{index}",
            category=(
                ConstraintCategory
                .SECURITY_REVIEW
            ),
            occurred_at=(
                f"2026-08-0{index}"
                "T10:00:00+00:00"
            ),
            work_item_id=(
                f"work-{index}"
            ),
            actor_id=(
                f"actor-{index}"
            ),
            team_id=(
                f"team-{index}"
            ),
            lifecycle_id=(
                f"life-{index}"
            ),
            source=(
                "defender"
                if index % 2
                else "sentinel"
            ),
        )
        for index in range(
            1,
            4,
        )
    )

    observed_aggregation = (
        build_aggregation(
            category=(
                ConstraintCategory
                .APPROVAL_REQUIRED
            ),
            event_count=1,
            unique_work_item_count=1,
            event_share=0.25,
            friction_score=1.0,
            band=FrictionBand.LOW,
            first=(
                "2026-08-01T10:00:00+00:00"
            ),
            last=(
                "2026-08-01T10:00:00+00:00"
            ),
        )
    )

    dominant_aggregation = (
        build_aggregation(
            category=(
                ConstraintCategory
                .SECURITY_REVIEW
            ),
            event_count=3,
            unique_work_item_count=3,
            event_share=0.75,
            friction_score=4.5,
            band=(
                FrictionBand.MODERATE
            ),
            first=(
                "2026-08-01T10:00:00+00:00"
            ),
            last=(
                "2026-08-03T10:00:00+00:00"
            ),
        )
    )

    summary = (
        GovernanceAssessmentDiagnosticSignificanceService()
        .classify(
            friction_summary=(
                build_summary(
                    (
                        observed_aggregation,
                        dominant_aggregation,
                    ),
                    dominant=(
                        ConstraintCategory
                        .SECURITY_REVIEW
                    ),
                )
            ),
            intake_results=(
                build_intake(
                    (
                        observed_record,
                        *significant_records,
                    )
                ),
            ),
        )
    )

    assert (
        summary.diagnosed_conditions
        == (
            ConstraintCategory
            .SECURITY_REVIEW,
        )
    )

    assert (
        summary.dominant_condition
        is ConstraintCategory
        .SECURITY_REVIEW
    )

    assert summary.observed_count == 1
    assert summary.dominant_count == 1


def test_summary_hash_is_deterministic():
    records = tuple(
        build_record(
            event_id=f"event-{index}",
            category=(
                ConstraintCategory
                .WORK_BLOCKED
            ),
            occurred_at=(
                f"2026-08-0{index}"
                "T10:00:00+00:00"
            ),
            work_item_id=(
                f"work-{index}"
            ),
            actor_id=(
                f"actor-{index}"
            ),
            team_id=(
                f"team-{index}"
            ),
            lifecycle_id=(
                f"life-{index}"
            ),
            source="jira",
        )
        for index in range(
            1,
            4,
        )
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .WORK_BLOCKED
        ),
        event_count=3,
        unique_work_item_count=3,
        event_share=1.0,
        friction_score=9.0,
        band=FrictionBand.HIGH,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-03T10:00:00+00:00"
        ),
    )

    service = (
        GovernanceAssessmentDiagnosticSignificanceService()
    )

    friction = build_summary(
        (aggregation,),
        dominant=(
            ConstraintCategory
            .WORK_BLOCKED
        ),
    )

    intake = (
        build_intake(
            records
        ),
    )

    first = service.classify(
        friction_summary=friction,
        intake_results=intake,
    )

    second = service.classify(
        friction_summary=friction,
        intake_results=intake,
    )

    assert first == second

    assert (
        first.summary_hash
        == second.summary_hash
    )

    assert len(
        first.summary_hash
    ) == 64


def test_hierarchy_mismatch_is_rejected():
    record = build_record(
        event_id="event-1",
        category=(
            ConstraintCategory
            .WORK_BLOCKED
        ),
        occurred_at=(
            "2026-08-01T10:00:00+00:00"
        ),
        work_item_id="work-1",
        actor_id="actor-1",
        team_id="team-1",
        lifecycle_id="life-1",
        source="jira",
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .WORK_BLOCKED
        ),
        event_count=1,
        unique_work_item_count=1,
        event_share=1.0,
        friction_score=3.0,
        band=FrictionBand.MODERATE,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-01T10:00:00+00:00"
        ),
    )

    with pytest.raises(
        DiagnosticSignificanceError,
        match="hierarchy",
    ):
        (
            GovernanceAssessmentDiagnosticSignificanceService()
            .classify(
                friction_summary=(
                    build_summary(
                        (aggregation,),
                        dominant=(
                            ConstraintCategory
                            .WORK_BLOCKED
                        ),
                    )
                ),
                intake_results=(
                    build_intake(
                        (record,),
                        hierarchy_key=(
                            "wrong/hierarchy/"
                            "engagement/assessment"
                        ),
                    ),
                ),
            )
        )


def test_aggregation_record_count_mismatch_is_rejected():
    record = build_record(
        event_id="event-1",
        category=(
            ConstraintCategory
            .WORK_BLOCKED
        ),
        occurred_at=(
            "2026-08-01T10:00:00+00:00"
        ),
        work_item_id="work-1",
        actor_id="actor-1",
        team_id="team-1",
        lifecycle_id="life-1",
        source="jira",
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .WORK_BLOCKED
        ),
        event_count=2,
        unique_work_item_count=1,
        event_share=1.0,
        friction_score=6.0,
        band=FrictionBand.MODERATE,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-01T10:00:00+00:00"
        ),
    )

    with pytest.raises(
        DiagnosticSignificanceError,
        match="event count",
    ):
        (
            GovernanceAssessmentDiagnosticSignificanceService()
            .classify(
                friction_summary=(
                    build_summary(
                        (aggregation,),
                        dominant=(
                            ConstraintCategory
                            .WORK_BLOCKED
                        ),
                    )
                ),
                intake_results=(
                    build_intake(
                        (record,)
                    ),
                ),
            )
        )


def test_condition_and_summary_are_immutable():
    records = tuple(
        build_record(
            event_id=f"event-{index}",
            category=(
                ConstraintCategory
                .WORK_BLOCKED
            ),
            occurred_at=(
                f"2026-08-0{index}"
                "T10:00:00+00:00"
            ),
            work_item_id=(
                f"work-{index}"
            ),
            actor_id=(
                f"actor-{index}"
            ),
            team_id=(
                f"team-{index}"
            ),
            lifecycle_id=(
                f"life-{index}"
            ),
            source="jira",
        )
        for index in range(
            1,
            4,
        )
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .WORK_BLOCKED
        ),
        event_count=3,
        unique_work_item_count=3,
        event_share=1.0,
        friction_score=9.0,
        band=FrictionBand.HIGH,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-03T10:00:00+00:00"
        ),
    )

    summary = (
        GovernanceAssessmentDiagnosticSignificanceService()
        .classify(
            friction_summary=(
                build_summary(
                    (aggregation,),
                    dominant=(
                        ConstraintCategory
                        .WORK_BLOCKED
                    ),
                )
            ),
            intake_results=(
                build_intake(
                    records
                ),
            ),
        )
    )

    condition = summary.conditions[0]

    with pytest.raises(
        FrozenInstanceError
    ):
        condition.event_count = 99

    with pytest.raises(
        FrozenInstanceError
    ):
        summary.summary_hash = "changed"


def test_schema_version_is_explicit():
    records = (
        build_record(
            event_id="event-1",
            category=(
                ConstraintCategory
                .APPROVAL_REQUIRED
            ),
            occurred_at=(
                "2026-08-01T10:00:00+00:00"
            ),
            work_item_id="work-1",
            actor_id="actor-1",
            team_id="team-1",
            lifecycle_id="life-1",
            source="jira",
        ),
    )

    aggregation = build_aggregation(
        category=(
            ConstraintCategory
            .APPROVAL_REQUIRED
        ),
        event_count=1,
        unique_work_item_count=1,
        event_share=1.0,
        friction_score=1.0,
        band=FrictionBand.LOW,
        first=(
            "2026-08-01T10:00:00+00:00"
        ),
        last=(
            "2026-08-01T10:00:00+00:00"
        ),
    )

    result = (
        GovernanceAssessmentDiagnosticSignificanceService()
        .classify(
            friction_summary=(
                build_summary(
                    (aggregation,),
                    dominant=(
                        ConstraintCategory
                        .APPROVAL_REQUIRED
                    ),
                )
            ),
            intake_results=(
                build_intake(
                    records
                ),
            ),
        )
    )

    assert (
        result.schema_version
        == ASSESSMENT_DIAGNOSTIC_SIGNIFICANCE_VERSION
    )