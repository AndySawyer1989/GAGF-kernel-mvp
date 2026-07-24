from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_evidence_intake import (
    GovernanceAssessmentEvidenceIntakeService,
)
from backend.app.gagf.governance_assessment_evidence_quality import (
    GovernanceAssessmentEvidenceQualityService,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    ConstraintCategory,
    FrictionAggregationError,
    FrictionBand,
    GovernanceAssessmentFrictionAggregationService,
    friction_band,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
    GovernanceAssessmentScopeConfigurationService,
    ScopeConfigurationStatus,
)


INTAKE_SERVICE = GovernanceAssessmentEvidenceIntakeService()
QUALITY_SERVICE = GovernanceAssessmentEvidenceQualityService()
AGGREGATION_SERVICE = (
    GovernanceAssessmentFrictionAggregationService()
)
SCOPE_SERVICE = GovernanceAssessmentScopeConfigurationService()


def build_context(tenant_id="tenant-alpha"):
    return CommercialHierarchyContext(
        tenant_id=tenant_id,
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )


def build_configuration(context=None, minimum_count=1):
    context = context or build_context()

    return SCOPE_SERVICE.configure(
        context=context,
        assessment_name="Governance Runway Assessment",
        workflow_names=("Incident Management",),
        organizational_units=("IT Operations",),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 6, 30),
        objectives=("Reduce governance friction",),
        expected_outcomes=("Faster workflow completion",),
        evidence_requirements=(
            EvidenceRequirement(
                requirement_id="required-csv",
                source_kind=EvidenceSourceKind.CSV,
                description="Workflow events",
                required=True,
                minimum_record_count=minimum_count,
            ),
        ),
        status=ScopeConfigurationStatus.LOCKED,
    )


def build_source(source_id="source-001"):
    return EvidenceSourceReference(
        source_id=source_id,
        kind=EvidenceSourceKind.CSV,
        display_name="Workflow Export",
    )


def build_csv():
    return (
        "event_id,event_type,occurred_at,work_item_id\n"
        "event-001,APPROVAL_DELAYED,"
        "2026-01-01T12:00:00Z,TICKET-1\n"
        "event-002,APPROVAL_DELAYED,"
        "2026-01-01T13:00:00Z,TICKET-2\n"
        "event-003,WORK_BLOCKED,"
        "2026-01-02T12:00:00Z,TICKET-2\n"
        "event-004,ESCALATION,"
        "2026-01-03T12:00:00Z,TICKET-3\n"
    )


def build_intake(
    *,
    context=None,
    csv_text=None,
    source_id="source-001",
):
    return INTAKE_SERVICE.ingest_csv(
        context=context or build_context(),
        source=build_source(source_id),
        csv_text=csv_text or build_csv(),
    )


def build_quality(
    *,
    context=None,
    intake_results=None,
):
    context = context or build_context()
    intake_results = intake_results or (
        build_intake(context=context),
    )

    return QUALITY_SERVICE.summarize(
        configuration=build_configuration(
            context=context
        ),
        intake_results=intake_results,
    )


def build_summary():
    intake = build_intake()
    quality = build_quality(
        intake_results=(intake,)
    )

    return AGGREGATION_SERVICE.aggregate(
        quality_summary=quality,
        intake_results=(intake,),
    )


def test_constraint_taxonomy_is_stable():
    assert ConstraintCategory.APPROVAL_DELAYED.value == (
        "APPROVAL_DELAYED"
    )
    assert ConstraintCategory.OWNERSHIP_GAP.value == (
        "OWNERSHIP_GAP"
    )
    assert ConstraintCategory.OVERRIDE.value == "OVERRIDE"


def test_friction_band_thresholds_are_stable():
    assert friction_band(2.9) is FrictionBand.LOW
    assert friction_band(3.0) is FrictionBand.MODERATE
    assert friction_band(8.0) is FrictionBand.HIGH
    assert friction_band(15.0) is FrictionBand.SEVERE


def test_summary_is_bound_to_assessment_hierarchy():
    summary = build_summary()

    assert summary.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_summary_counts_recognized_events():
    summary = build_summary()

    assert summary.total_evidence_events == 4
    assert summary.recognized_constraint_events == 4
    assert summary.unrecognized_event_count == 0


def test_summary_counts_unique_work_items():
    summary = build_summary()

    assert summary.unique_work_item_count == 3


def test_aggregation_groups_constraint_categories():
    summary = build_summary()
    by_category = {
        aggregation.category: aggregation
        for aggregation in summary.constraint_aggregations
    }

    approval = by_category[
        ConstraintCategory.APPROVAL_DELAYED
    ]

    assert approval.event_count == 2
    assert approval.unique_work_item_count == 2
    assert approval.weight == 2.0
    assert approval.friction_score == 4.0
    assert approval.event_share == 0.5


def test_total_friction_score_is_weighted():
    summary = build_summary()

    assert summary.total_friction_score == 9.0
    assert summary.average_friction_per_event == 2.25
    assert summary.has_measurable_friction is True


def test_work_blocked_is_dominant_constraint():
    summary = build_summary()

    assert summary.dominant_constraint is (
        ConstraintCategory.APPROVAL_DELAYED
    )


def test_aggregation_preserves_time_range():
    summary = build_summary()
    approval = next(
        aggregation
        for aggregation in summary.constraint_aggregations
        if aggregation.category is (
            ConstraintCategory.APPROVAL_DELAYED
        )
    )

    assert approval.first_occurred_at.isoformat() == (
        "2026-01-01T12:00:00+00:00"
    )
    assert approval.last_occurred_at.isoformat() == (
        "2026-01-01T13:00:00+00:00"
    )


def test_unknown_event_types_are_reported():
    csv_text = (
        "event_id,event_type,occurred_at,work_item_id\n"
        "event-001,WORK_BLOCKED,"
        "2026-01-01T12:00:00Z,TICKET-1\n"
        "event-002,CUSTOM_EVENT,"
        "2026-01-01T13:00:00Z,TICKET-2\n"
    )
    intake = build_intake(csv_text=csv_text)
    quality = build_quality(
        intake_results=(intake,)
    )

    summary = AGGREGATION_SERVICE.aggregate(
        quality_summary=quality,
        intake_results=(intake,),
    )

    assert summary.total_evidence_events == 2
    assert summary.recognized_constraint_events == 1
    assert summary.unrecognized_event_count == 1
    assert summary.unrecognized_event_types == (
        "CUSTOM_EVENT",
    )


def test_quality_gate_blocks_unready_evidence():
    configuration = build_configuration(
        minimum_count=5
    )
    intake = build_intake()
    quality = QUALITY_SERVICE.summarize(
        configuration=configuration,
        intake_results=(intake,),
    )

    with pytest.raises(
        FrictionAggregationError,
        match="not ready for analysis",
    ):
        AGGREGATION_SERVICE.aggregate(
            quality_summary=quality,
            intake_results=(intake,),
        )


def test_foreign_hierarchy_evidence_is_rejected():
    alpha_intake = build_intake()
    alpha_quality = build_quality(
        intake_results=(alpha_intake,)
    )
    beta_intake = build_intake(
        context=build_context("tenant-beta")
    )

    with pytest.raises(
        FrictionAggregationError,
        match="hierarchy",
    ):
        AGGREGATION_SERVICE.aggregate(
            quality_summary=alpha_quality,
            intake_results=(beta_intake,),
        )


def test_duplicate_evidence_records_are_rejected():
    intake = build_intake()
    quality = build_quality(
        intake_results=(intake,)
    )

    duplicate_source_result = type(intake)(
        source=build_source("source-duplicate"),
        hierarchy_key=intake.hierarchy_key,
        accepted_records=intake.accepted_records,
        rejected_rows=(),
        total_rows=intake.total_rows,
        intake_hash="duplicate-intake-hash",
    )

    with pytest.raises(
        FrictionAggregationError,
        match="duplicate evidence records",
    ):
        AGGREGATION_SERVICE.aggregate(
            quality_summary=quality,
            intake_results=(
                intake,
                duplicate_source_result,
            ),
        )


def test_summary_hash_is_deterministic():
    first = build_summary()
    second = build_summary()

    assert first.summary_hash == second.summary_hash


def test_summary_hash_changes_by_tenant():
    alpha = build_summary()

    beta_context = build_context("tenant-beta")
    beta_intake = build_intake(
        context=beta_context
    )
    beta_quality = build_quality(
        context=beta_context,
        intake_results=(beta_intake,),
    )
    beta = AGGREGATION_SERVICE.aggregate(
        quality_summary=beta_quality,
        intake_results=(beta_intake,),
    )

    assert alpha.summary_hash != beta.summary_hash


def test_summary_serializes_public_contract():
    serialized = build_summary().to_dict()

    assert serialized["total_evidence_events"] == 4
    assert serialized["dominant_constraint"] == (
        "APPROVAL_DELAYED"
    )
    assert serialized["has_measurable_friction"] is True
    assert serialized["constraint_aggregations"][0][
        "category"
    ] == "APPROVAL_DELAYED"


def test_summary_is_immutable():
    summary = build_summary()

    with pytest.raises(FrozenInstanceError):
        summary.total_friction_score = 0.0
