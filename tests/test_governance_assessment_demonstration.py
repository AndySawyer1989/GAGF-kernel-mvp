from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from backend.app.gagf.governance_assessment_demonstration import (
    DemonstrationEvidenceInput,
    GovernanceAssessmentDemonstrationError,
    GovernanceAssessmentDemonstrationService,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_friction_aggregation import (
    ConstraintCategory,
)
from backend.app.gagf.governance_assessment_intervention_plan import (
    InterventionType,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)


SERVICE = GovernanceAssessmentDemonstrationService()


def build_context(tenant_id="tenant-alpha"):
    return CommercialHierarchyContext(
        tenant_id=tenant_id,
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )


def build_csv():
    return (
        "event_id,event_type,occurred_at,work_item_id,owner\n"
        "event-001,APPROVAL_DELAYED,"
        "2026-01-01T12:00:00Z,TICKET-1,security\n"
        "event-002,APPROVAL_DELAYED,"
        "2026-01-01T13:00:00Z,TICKET-2,security\n"
        "event-003,WORK_BLOCKED,"
        "2026-01-02T12:00:00Z,TICKET-3,operations\n"
        "event-004,ESCALATION,"
        "2026-01-03T12:00:00Z,TICKET-4,operations\n"
    )


def build_evidence_input(
    source_id="source-001",
    csv_text=None,
):
    return DemonstrationEvidenceInput(
        source=EvidenceSourceReference(
            source_id=source_id,
            kind=EvidenceSourceKind.CSV,
            display_name="Workflow Export",
            source_location="uploads/workflow.csv",
        ),
        csv_text=csv_text or build_csv(),
    )


def build_result(tenant_id="tenant-alpha", **overrides):
    values = {
        "context": build_context(tenant_id),
        "assessment_name": "Governance Runway Assessment",
        "workflow_names": ("Incident Management",),
        "organizational_units": ("IT Operations",),
        "period_start": date(2026, 1, 1),
        "period_end": date(2026, 6, 30),
        "objectives": ("Reduce governance friction",),
        "expected_outcomes": ("Faster workflow completion",),
        "evidence_requirements": (
            EvidenceRequirement(
                requirement_id="required-csv",
                source_kind=EvidenceSourceKind.CSV,
                description="Workflow evidence",
                required=True,
                minimum_record_count=4,
            ),
        ),
        "evidence_inputs": (build_evidence_input(),),
        "client_display_name": "ACME Corporation",
        "prepared_by": "FIP Governance Services",
    }
    values.update(overrides)
    return SERVICE.run(**values)


def test_demonstration_completes_full_pipeline():
    result = build_result()

    assert result.completed is True
    assert result.quality_summary.ready_for_analysis is True
    assert result.friction_summary.has_measurable_friction is True
    assert result.report_package.markdown


def test_demonstration_is_bound_to_full_hierarchy():
    result = build_result()

    assert result.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_demonstration_produces_all_major_artifacts():
    result = build_result()

    assert result.configuration
    assert result.intake_results
    assert result.quality_summary
    assert result.friction_summary
    assert result.debt_score
    assert result.intervention_plan
    assert result.roadmap
    assert result.executive_projection
    assert result.report_package


def test_demonstration_preserves_evidence_counts():
    result = build_result()

    assert result.quality_summary.accepted_rows == 4
    assert result.friction_summary.total_evidence_events == 4
    assert result.debt_score.recognized_constraint_events == 4


def test_demonstration_produces_ranked_plan_and_roadmap():
    result = build_result()

    assert len(result.intervention_plan.interventions) == 3
    assert result.intervention_plan.top_intervention is not None
    assert result.roadmap.total_items == 3


def test_demonstration_produces_client_report():
    result = build_result()

    assert result.report_package.title == (
        "Governance Runway Assessment — ACME Corporation"
    )
    assert "## Executive Summary" in (
        result.report_package.markdown
    )
    assert "## Evidence Commitments" in (
        result.report_package.markdown
    )


def test_artifact_commitment_chain_is_complete():
    result = build_result()

    assert set(result.artifact_commitments) == {
        "scope_configuration_hash",
        "evidence_quality_hash",
        "friction_summary_hash",
        "governance_debt_score_hash",
        "intervention_plan_hash",
        "roadmap_hash",
        "executive_projection_hash",
        "report_markdown_hash",
        "report_package_hash",
    }


def test_report_commitment_matches_demonstration_chain():
    result = build_result()

    assert result.artifact_commitments[
        "report_package_hash"
    ] == result.report_package.manifest.package_hash


def test_demonstration_hash_is_deterministic():
    first = build_result()
    second = build_result()

    assert first.demonstration_hash == second.demonstration_hash


def test_demonstration_hash_changes_by_tenant():
    alpha = build_result()
    beta = build_result("tenant-beta")

    assert alpha.demonstration_hash != beta.demonstration_hash


def test_duplicate_source_identifiers_are_rejected():
    evidence_input = build_evidence_input()

    with pytest.raises(
        GovernanceAssessmentDemonstrationError,
        match="duplicate source identifiers",
    ):
        build_result(
            evidence_inputs=(
                evidence_input,
                evidence_input,
            )
        )


def test_empty_evidence_inputs_are_rejected():
    with pytest.raises(
        GovernanceAssessmentDemonstrationError,
        match="at least one evidence input",
    ):
        build_result(evidence_inputs=())


def test_failed_quality_gate_stops_demonstration():
    requirement = EvidenceRequirement(
        requirement_id="required-csv",
        source_kind=EvidenceSourceKind.CSV,
        description="Workflow evidence",
        required=True,
        minimum_record_count=10,
    )

    with pytest.raises(
        GovernanceAssessmentDemonstrationError,
        match="analysis gate",
    ):
        build_result(
            evidence_requirements=(requirement,)
        )


def test_commercial_overrides_flow_through_pipeline():
    result = build_result(
        implementation_burdens={
            ConstraintCategory.APPROVAL_DELAYED: 0.1,
        },
        reversibility_scores={
            ConstraintCategory.APPROVAL_DELAYED: 0.9,
        },
        owner_roles={
            InterventionType.STREAMLINE_APPROVAL: (
                "Chief Operating Officer"
            ),
        },
        maximum_priorities=2,
    )

    approval = next(
        intervention
        for intervention in result.intervention_plan.interventions
        if intervention.constraint_category is (
            ConstraintCategory.APPROVAL_DELAYED
        )
    )
    roadmap_item = next(
        item
        for phase in result.roadmap.phases
        for item in phase.items
        if item.intervention_id == approval.intervention_id
    )

    assert approval.implementation_burden == 0.1
    assert approval.reversibility == 0.9
    assert roadmap_item.owner_role == "Chief Operating Officer"
    assert len(result.executive_projection.priorities) == 2


def test_demonstration_serializes_public_contract():
    serialized = build_result().to_dict()

    assert serialized["completed"] is True
    assert serialized["hierarchy_key"].endswith(
        "assessment-001"
    )
    assert serialized["report_package"]["manifest"][
        "package_hash"
    ]
    assert serialized["demonstration_hash"]


def test_demonstration_result_is_immutable():
    result = build_result()

    with pytest.raises(FrozenInstanceError):
        result.demonstration_hash = "changed"
