from dataclasses import FrozenInstanceError
from datetime import date, datetime, timezone

import pytest

from backend.app.gagf.governance_assessment_domain import (
    AssessmentScope,
    AssessmentStatus,
    ClientRecord,
    EngagementRecord,
    EvidenceSourceKind,
    EvidenceSourceReference,
    FindingReference,
    GovernanceAssessment,
    InterventionReference,
    InterventionStatus,
    MetricReference,
    ReportReference,
)


NOW = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)


def build_scope():
    return AssessmentScope(
        workflow_names=("Incident Management",),
        organizational_units=("IT Operations",),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 6, 30),
        objectives=(
            "Reduce approval delay",
        ),
    )


def build_assessment(**overrides):
    values = {
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "name": "Governance Runway Assessment",
        "status": AssessmentStatus.DRAFT,
        "scope": build_scope(),
        "evidence_sources": (
            EvidenceSourceReference(
                source_id="source-001",
                kind=EvidenceSourceKind.CSV,
                display_name="Ticket Export",
            ),
        ),
        "findings": (
            FindingReference(
                finding_id="finding-001",
                category="APPROVAL_DELAYED",
                title="Security approval delay",
                severity=4,
                confidence=0.9,
            ),
        ),
        "metrics": (
            MetricReference(
                metric_id="metric-001",
                name="Median approval delay",
                value=18.5,
                unit="hours",
            ),
        ),
        "interventions": (
            InterventionReference(
                intervention_id="intervention-001",
                title="Delegate low-risk approvals",
                related_finding_ids=("finding-001",),
                priority=1,
            ),
        ),
        "reports": (
            ReportReference(
                report_id="report-001",
                report_format="pdf",
                location="reports/assessment-001.pdf",
                generated_at=NOW,
            ),
        ),
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return GovernanceAssessment(**values)


def test_assessment_status_values_are_stable():
    assert AssessmentStatus.DRAFT.value == "draft"
    assert AssessmentStatus.COMPLETE.value == "complete"


def test_evidence_source_kinds_cover_initial_inputs():
    assert EvidenceSourceKind.CSV.value == "csv"
    assert EvidenceSourceKind.JIRA.value == "jira"
    assert EvidenceSourceKind.SERVICENOW.value == "servicenow"
    assert EvidenceSourceKind.INTERVIEW.value == "interview"


def test_client_record_normalizes_text():
    client = ClientRecord(
        tenant_id=" tenant-alpha ",
        client_id=" client-acme ",
        name=" ACME Corporation ",
        created_at=NOW,
    )

    assert client.tenant_id == "tenant-alpha"
    assert client.client_id == "client-acme"
    assert client.name == "ACME Corporation"


def test_client_record_rejects_empty_tenant():
    with pytest.raises(ValueError, match="tenant_id"):
        ClientRecord(
            tenant_id=" ",
            client_id="client-acme",
            name="ACME Corporation",
            created_at=NOW,
        )


def test_engagement_preserves_commercial_hierarchy():
    engagement = EngagementRecord(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        name="Initial Assessment",
        created_at=NOW,
    )

    assert engagement.tenant_id == "tenant-alpha"
    assert engagement.client_id == "client-acme"
    assert engagement.engagement_id == "engagement-001"


def test_scope_requires_at_least_one_workflow():
    with pytest.raises(ValueError, match="workflow_names"):
        AssessmentScope(
            workflow_names=(),
            organizational_units=("IT",),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 2, 1),
            objectives=("Find friction",),
        )


def test_scope_rejects_reversed_period():
    with pytest.raises(ValueError, match="period_end"):
        AssessmentScope(
            workflow_names=("Incident Management",),
            organizational_units=("IT",),
            period_start=date(2026, 2, 1),
            period_end=date(2026, 1, 1),
            objectives=("Find friction",),
        )


def test_finding_validates_severity():
    with pytest.raises(ValueError, match="severity"):
        FindingReference(
            finding_id="finding-001",
            category="WORK_BLOCKED",
            title="Blocked workflow",
            severity=6,
            confidence=0.8,
        )


def test_finding_validates_confidence():
    with pytest.raises(ValueError, match="confidence"):
        FindingReference(
            finding_id="finding-001",
            category="WORK_BLOCKED",
            title="Blocked workflow",
            severity=4,
            confidence=1.1,
        )


def test_intervention_requires_related_findings():
    with pytest.raises(ValueError, match="related_finding_ids"):
        InterventionReference(
            intervention_id="intervention-001",
            title="Change workflow",
            related_finding_ids=(),
            priority=1,
        )


def test_assessment_builds_complete_commercial_hierarchy():
    assessment = build_assessment()

    assert assessment.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )
    assert assessment.status is AssessmentStatus.DRAFT
    assert len(assessment.evidence_sources) == 1
    assert len(assessment.findings) == 1
    assert len(assessment.interventions) == 1


def test_assessment_rejects_duplicate_source_ids():
    source = EvidenceSourceReference(
        source_id="source-001",
        kind=EvidenceSourceKind.CSV,
        display_name="Ticket Export",
    )

    with pytest.raises(ValueError, match="duplicate"):
        build_assessment(
            evidence_sources=(source, source),
        )


def test_assessment_rejects_unknown_intervention_finding():
    intervention = InterventionReference(
        intervention_id="intervention-002",
        title="Unknown intervention",
        related_finding_ids=("finding-missing",),
        priority=2,
        status=InterventionStatus.PROPOSED,
    )

    with pytest.raises(ValueError, match="unknown findings"):
        build_assessment(
            interventions=(intervention,),
        )


def test_assessment_rejects_reversed_timestamps():
    earlier = datetime(
        2026, 7, 22, 12, 0, tzinfo=timezone.utc
    )

    with pytest.raises(ValueError, match="updated_at"):
        build_assessment(
            created_at=NOW,
            updated_at=earlier,
        )


def test_assessment_serializes_to_public_dictionary():
    serialized = build_assessment().to_dict()

    assert serialized["status"] == "draft"
    assert serialized["scope"]["period_start"] == "2026-01-01"
    assert (
        serialized["evidence_sources"][0]["kind"]
        == "csv"
    )
    assert (
        serialized["interventions"][0]["status"]
        == "proposed"
    )
    assert serialized["created_at"] == NOW.isoformat()


def test_assessment_is_immutable():
    assessment = build_assessment()

    with pytest.raises(FrozenInstanceError):
        assessment.status = AssessmentStatus.COMPLETE
