from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from backend.app.gagf.governance_assessment_application import (
    AssessmentApplicationError,
    AssessmentExecutionRequest,
    GovernanceAssessmentApplicationService,
)
from backend.app.gagf.governance_assessment_demonstration import (
    DemonstrationEvidenceInput,
)
from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_assessment_scope_configuration import (
    EvidenceRequirement,
)


def build_context(tenant_id="tenant-alpha"):
    return CommercialHierarchyContext(
        tenant_id=tenant_id,
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )


def build_request(tenant_id="tenant-alpha", **overrides):
    csv_text = (
        "event_id,event_type,occurred_at,work_item_id\n"
        "event-001,APPROVAL_DELAYED,"
        "2026-01-01T12:00:00Z,TICKET-1\n"
        "event-002,APPROVAL_DELAYED,"
        "2026-01-01T13:00:00Z,TICKET-2\n"
        "event-003,WORK_BLOCKED,"
        "2026-01-02T12:00:00Z,TICKET-3\n"
        "event-004,ESCALATION,"
        "2026-01-03T12:00:00Z,TICKET-4\n"
    )

    values = {
        "context": build_context(tenant_id),
        "assessment_name": "Governance Runway Assessment",
        "workflow_names": ("Incident Management",),
        "organizational_units": ("IT Operations",),
        "period_start": date(2026, 1, 1),
        "period_end": date(2026, 6, 30),
        "objectives": ("Reduce governance friction",),
        "expected_outcomes": ("Faster completion",),
        "evidence_requirements": (
            EvidenceRequirement(
                requirement_id="required-csv",
                source_kind=EvidenceSourceKind.CSV,
                description="Workflow evidence",
                required=True,
                minimum_record_count=4,
            ),
        ),
        "evidence_inputs": (
            DemonstrationEvidenceInput(
                source=EvidenceSourceReference(
                    source_id="source-001",
                    kind=EvidenceSourceKind.CSV,
                    display_name="Workflow Export",
                ),
                csv_text=csv_text,
            ),
        ),
        "client_display_name": "ACME Corporation",
        "prepared_by": "FIP Governance Services",
    }
    values.update(overrides)
    return AssessmentExecutionRequest(**values)


@pytest.fixture
def repository(tmp_path):
    return GovernanceAssessmentRepository(
        tmp_path / "application.sqlite3"
    )


@pytest.fixture
def service(repository):
    return GovernanceAssessmentApplicationService(
        repository=repository
    )


def test_execute_runs_and_persists_complete_assessment(service):
    result = service.execute(request=build_request())

    assert result.completed is True
    assert result.persistence.artifact_count == 10
    assert result.demonstration.report_package.markdown


def test_execute_preserves_full_hierarchy(service):
    result = service.execute(request=build_request())

    assert result.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_application_hash_is_deterministic(tmp_path):
    first_service = GovernanceAssessmentApplicationService(
        repository=GovernanceAssessmentRepository(
            tmp_path / "first.sqlite3"
        )
    )
    second_service = GovernanceAssessmentApplicationService(
        repository=GovernanceAssessmentRepository(
            tmp_path / "second.sqlite3"
        )
    )

    first = first_service.execute(request=build_request())
    second = second_service.execute(request=build_request())

    assert first.application_hash == second.application_hash


def test_application_hash_changes_by_tenant(tmp_path):
    service = GovernanceAssessmentApplicationService(
        repository=GovernanceAssessmentRepository(
            tmp_path / "multi.sqlite3"
        )
    )

    alpha = service.execute(
        request=build_request("tenant-alpha")
    )
    beta = service.execute(
        request=build_request("tenant-beta")
    )

    assert alpha.application_hash != beta.application_hash


def test_execute_is_idempotent(service, repository):
    request = build_request()

    first = service.execute(request=request)
    second = service.execute(request=request)

    assert first.application_hash == second.application_hash
    assert len(
        repository.list_artifacts(context=build_context())
    ) == 10


def test_get_assessment_returns_persisted_record(service):
    service.execute(request=build_request())

    assessment = service.get_assessment(
        context=build_context()
    )

    assert assessment.assessment_name == (
        "Governance Runway Assessment"
    )
    assert assessment.status == "complete"


def test_list_assessments_is_tenant_scoped(service):
    service.execute(request=build_request())

    visible = service.list_assessments(
        tenant_id="tenant-alpha"
    )

    assert len(visible) == 1
    assert visible[0].tenant_id == "tenant-alpha"


def test_list_artifacts_returns_ordered_inventory(service):
    service.execute(request=build_request())

    artifacts = service.list_artifacts(
        context=build_context()
    )

    assert len(artifacts) == 10
    assert [
        artifact.sequence_number
        for artifact in artifacts
    ] == list(range(1, 11))


def test_list_artifacts_filters_by_type(service):
    service.execute(request=build_request())

    reports = service.list_artifacts(
        context=build_context(),
        artifact_type="client-report-package",
    )

    assert len(reports) == 1
    assert reports[0].artifact_type == (
        "client-report-package"
    )


def test_summarize_returns_verified_inventory(service):
    service.execute(request=build_request())

    summary = service.summarize(context=build_context())

    assert summary.repository_chain_valid is True
    assert summary.artifact_count == 10
    assert summary.summary_hash


def test_summary_hash_is_deterministic(service):
    service.execute(request=build_request())

    first = service.summarize(context=build_context())
    second = service.summarize(context=build_context())

    assert first.summary_hash == second.summary_hash


def test_request_rejects_empty_workflows():
    with pytest.raises(
        AssessmentApplicationError,
        match="workflow_names",
    ):
        build_request(workflow_names=())


def test_request_rejects_empty_evidence_inputs():
    with pytest.raises(
        AssessmentApplicationError,
        match="evidence_inputs",
    ):
        build_request(evidence_inputs=())


def test_application_result_serializes_contract(service):
    serialized = service.execute(
        request=build_request()
    ).to_dict()

    assert serialized["completed"] is True
    assert serialized["artifact_count"] == 10
    assert serialized["request_hash"]
    assert serialized["application_hash"]


def test_application_result_is_immutable(service):
    result = service.execute(request=build_request())

    with pytest.raises(FrozenInstanceError):
        result.application_hash = "changed"
