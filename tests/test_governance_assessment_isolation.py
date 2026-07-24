from datetime import date, datetime, timezone

import pytest

from backend.app.gagf.governance_assessment_domain import (
    AssessmentScope,
    AssessmentStatus,
    ClientRecord,
    EngagementRecord,
    GovernanceAssessment,
)
from backend.app.gagf.governance_assessment_isolation import (
    AssessmentNotFoundError,
    ClientNotFoundError,
    CommercialHierarchyContext,
    EngagementNotFoundError,
    GovernanceAssessmentIsolationError,
    GovernanceAssessmentIsolationService,
)


NOW = datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc)
SERVICE = GovernanceAssessmentIsolationService()


def build_client(
    *,
    tenant_id="tenant-alpha",
    client_id="client-acme",
):
    return ClientRecord(
        tenant_id=tenant_id,
        client_id=client_id,
        name=client_id,
        created_at=NOW,
    )


def build_engagement(
    *,
    tenant_id="tenant-alpha",
    client_id="client-acme",
    engagement_id="engagement-001",
):
    return EngagementRecord(
        tenant_id=tenant_id,
        client_id=client_id,
        engagement_id=engagement_id,
        name=engagement_id,
        created_at=NOW,
    )


def build_assessment(
    *,
    tenant_id="tenant-alpha",
    client_id="client-acme",
    engagement_id="engagement-001",
    assessment_id="assessment-001",
):
    return GovernanceAssessment(
        tenant_id=tenant_id,
        client_id=client_id,
        engagement_id=engagement_id,
        assessment_id=assessment_id,
        name="Governance Runway Assessment",
        status=AssessmentStatus.DRAFT,
        scope=AssessmentScope(
            workflow_names=("Incident Management",),
            organizational_units=("IT Operations",),
            period_start=date(2026, 1, 1),
            period_end=date(2026, 6, 30),
            objectives=("Reduce approval delay",),
        ),
        evidence_sources=(),
        findings=(),
        metrics=(),
        interventions=(),
        reports=(),
        created_at=NOW,
        updated_at=NOW,
    )


def test_context_builds_hierarchy_key():
    context = CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    assert context.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_context_requires_engagement_for_assessment():
    with pytest.raises(
        GovernanceAssessmentIsolationError,
        match="requires engagement_id",
    ):
        CommercialHierarchyContext(
            tenant_id="tenant-alpha",
            client_id="client-acme",
            assessment_id="assessment-001",
        )


def test_validate_client_accepts_matching_context():
    context = CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
    )
    client = build_client()

    assert SERVICE.validate_client(
        context=context,
        client=client,
    ) is client


def test_validate_client_rejects_foreign_tenant():
    context = CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
    )

    with pytest.raises(
        GovernanceAssessmentIsolationError,
        match="tenant",
    ):
        SERVICE.validate_client(
            context=context,
            client=build_client(tenant_id="tenant-beta"),
        )


def test_validate_engagement_rejects_foreign_client():
    context = CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
    )

    with pytest.raises(
        GovernanceAssessmentIsolationError,
        match="client",
    ):
        SERVICE.validate_engagement(
            context=context,
            engagement=build_engagement(
                client_id="client-other"
            ),
        )


def test_validate_assessment_accepts_full_hierarchy():
    context = CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )
    assessment = build_assessment()

    assert SERVICE.validate_assessment(
        context=context,
        assessment=assessment,
    ) is assessment


def test_validate_assessment_rejects_foreign_engagement():
    context = CommercialHierarchyContext(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )

    with pytest.raises(
        GovernanceAssessmentIsolationError,
        match="hierarchy",
    ):
        SERVICE.validate_assessment(
            context=context,
            assessment=build_assessment(
                engagement_id="engagement-002"
            ),
        )


def test_resolve_client_is_tenant_scoped():
    clients = (
        build_client(),
        build_client(
            tenant_id="tenant-beta",
            client_id="client-acme",
        ),
    )

    resolved = SERVICE.resolve_client(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        clients=clients,
    )

    assert resolved.tenant_id == "tenant-alpha"


def test_resolve_client_hides_foreign_tenant():
    with pytest.raises(ClientNotFoundError):
        SERVICE.resolve_client(
            tenant_id="tenant-alpha",
            client_id="client-acme",
            clients=(
                build_client(tenant_id="tenant-beta"),
            ),
        )


def test_resolve_engagement_is_client_scoped():
    engagements = (
        build_engagement(),
        build_engagement(
            client_id="client-other",
        ),
    )

    resolved = SERVICE.resolve_engagement(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        engagements=engagements,
    )

    assert resolved.client_id == "client-acme"


def test_resolve_engagement_hides_foreign_client():
    with pytest.raises(EngagementNotFoundError):
        SERVICE.resolve_engagement(
            tenant_id="tenant-alpha",
            client_id="client-acme",
            engagement_id="engagement-001",
            engagements=(
                build_engagement(client_id="client-other"),
            ),
        )


def test_resolve_assessment_is_engagement_scoped():
    assessments = (
        build_assessment(),
        build_assessment(
            engagement_id="engagement-002",
        ),
    )

    resolved = SERVICE.resolve_assessment(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
        assessments=assessments,
    )

    assert resolved.engagement_id == "engagement-001"


def test_resolve_assessment_hides_foreign_engagement():
    with pytest.raises(AssessmentNotFoundError):
        SERVICE.resolve_assessment(
            tenant_id="tenant-alpha",
            client_id="client-acme",
            engagement_id="engagement-001",
            assessment_id="assessment-001",
            assessments=(
                build_assessment(
                    engagement_id="engagement-002"
                ),
            ),
        )


def test_visible_clients_return_only_tenant_records():
    clients = (
        build_client(client_id="client-one"),
        build_client(client_id="client-two"),
        build_client(
            tenant_id="tenant-beta",
            client_id="client-three",
        ),
    )

    visible = SERVICE.visible_clients(
        tenant_id="tenant-alpha",
        clients=clients,
    )

    assert {client.client_id for client in visible} == {
        "client-one",
        "client-two",
    }


def test_visible_engagements_return_only_client_records():
    engagements = (
        build_engagement(engagement_id="engagement-001"),
        build_engagement(engagement_id="engagement-002"),
        build_engagement(
            client_id="client-other",
            engagement_id="engagement-003",
        ),
    )

    visible = SERVICE.visible_engagements(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagements=engagements,
    )

    assert {
        engagement.engagement_id
        for engagement in visible
    } == {
        "engagement-001",
        "engagement-002",
    }


def test_visible_assessments_return_only_engagement_records():
    assessments = (
        build_assessment(assessment_id="assessment-001"),
        build_assessment(assessment_id="assessment-002"),
        build_assessment(
            engagement_id="engagement-other",
            assessment_id="assessment-003",
        ),
    )

    visible = SERVICE.visible_assessments(
        tenant_id="tenant-alpha",
        client_id="client-acme",
        engagement_id="engagement-001",
        assessments=assessments,
    )

    assert {
        assessment.assessment_id
        for assessment in visible
    } == {
        "assessment-001",
        "assessment-002",
    }
