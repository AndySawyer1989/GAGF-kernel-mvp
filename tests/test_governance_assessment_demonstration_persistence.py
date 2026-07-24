from dataclasses import FrozenInstanceError, replace
from datetime import date

import pytest

from backend.app.gagf.governance_assessment_demonstration import (
    DemonstrationEvidenceInput,
    GovernanceAssessmentDemonstrationService,
)
from backend.app.gagf.governance_assessment_demonstration_persistence import (
    ARTIFACT_TYPE_ORDER,
    DemonstrationPersistenceError,
    GovernanceAssessmentDemonstrationPersistenceService,
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


DEMONSTRATION_SERVICE = GovernanceAssessmentDemonstrationService()


def build_context(tenant_id="tenant-alpha"):
    return CommercialHierarchyContext(
        tenant_id=tenant_id,
        client_id="client-acme",
        engagement_id="engagement-001",
        assessment_id="assessment-001",
    )


def build_demonstration(tenant_id="tenant-alpha"):
    context = build_context(tenant_id)
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

    return DEMONSTRATION_SERVICE.run(
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
                description="Workflow evidence",
                required=True,
                minimum_record_count=4,
            ),
        ),
        evidence_inputs=(
            DemonstrationEvidenceInput(
                source=EvidenceSourceReference(
                    source_id="source-001",
                    kind=EvidenceSourceKind.CSV,
                    display_name="Workflow Export",
                ),
                csv_text=csv_text,
            ),
        ),
        client_display_name="ACME Corporation",
        prepared_by="FIP Governance Services",
    )


@pytest.fixture
def repository(tmp_path):
    return GovernanceAssessmentRepository(
        tmp_path / "assessment-persistence.sqlite3"
    )


@pytest.fixture
def persistence_service(repository):
    return GovernanceAssessmentDemonstrationPersistenceService(
        repository
    )


def test_persist_creates_assessment_record(
    persistence_service,
):
    result = persistence_service.persist(
        demonstration=build_demonstration()
    )

    assert result.assessment.assessment_name == (
        "Governance Runway Assessment"
    )
    assert result.assessment.status == "complete"


def test_persist_is_bound_to_full_hierarchy(
    persistence_service,
):
    result = persistence_service.persist(
        demonstration=build_demonstration()
    )

    assert result.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_persist_writes_complete_artifact_set(
    persistence_service,
):
    result = persistence_service.persist(
        demonstration=build_demonstration()
    )

    assert result.artifact_count == 10
    assert tuple(
        artifact.artifact_type
        for artifact in result.artifacts
    ) == ARTIFACT_TYPE_ORDER


def test_artifacts_receive_contiguous_sequence_numbers(
    persistence_service,
):
    result = persistence_service.persist(
        demonstration=build_demonstration()
    )

    assert [
        artifact.sequence_number
        for artifact in result.artifacts
    ] == list(range(1, 11))


def test_repository_chain_is_verified(
    persistence_service,
):
    result = persistence_service.persist(
        demonstration=build_demonstration()
    )

    assert result.repository_chain_valid is True
    assert result.completed is True


def test_persisted_payloads_match_demonstration(
    persistence_service,
    repository,
):
    demonstration = build_demonstration()
    persistence_service.persist(
        demonstration=demonstration
    )

    artifacts = repository.list_artifacts(
        context=build_context()
    )
    by_type = {
        artifact.artifact_type: artifact
        for artifact in artifacts
    }

    assert by_type["scope-configuration"].payload == (
        demonstration.configuration.to_dict()
    )
    assert by_type["governance-debt-score"].payload == (
        demonstration.debt_score.to_dict()
    )


def test_report_package_is_persisted(
    persistence_service,
    repository,
):
    demonstration = build_demonstration()
    persistence_service.persist(
        demonstration=demonstration
    )

    report = repository.list_artifacts(
        context=build_context(),
        artifact_type="client-report-package",
    )[0]

    assert report.payload["manifest"]["package_hash"] == (
        demonstration.report_package.manifest.package_hash
    )
    assert "## Executive Summary" in report.payload["markdown"]


def test_manifest_preserves_demonstration_hash(
    persistence_service,
    repository,
):
    demonstration = build_demonstration()
    persistence_service.persist(
        demonstration=demonstration
    )

    manifest = repository.list_artifacts(
        context=build_context(),
        artifact_type="demonstration-manifest",
    )[0]

    assert manifest.payload["demonstration_hash"] == (
        demonstration.demonstration_hash
    )


def test_persistence_is_idempotent(
    persistence_service,
    repository,
):
    demonstration = build_demonstration()

    first = persistence_service.persist(
        demonstration=demonstration
    )
    second = persistence_service.persist(
        demonstration=demonstration
    )

    assert first.persistence_hash == second.persistence_hash
    assert first.artifacts == second.artifacts
    assert len(
        repository.list_artifacts(context=build_context())
    ) == 10


def test_persistence_hash_is_deterministic(tmp_path):
    first_repository = GovernanceAssessmentRepository(
        tmp_path / "first.sqlite3"
    )
    second_repository = GovernanceAssessmentRepository(
        tmp_path / "second.sqlite3"
    )
    demonstration = build_demonstration()

    first = GovernanceAssessmentDemonstrationPersistenceService(
        first_repository
    ).persist(demonstration=demonstration)
    second = GovernanceAssessmentDemonstrationPersistenceService(
        second_repository
    ).persist(demonstration=demonstration)

    assert first.persistence_hash == second.persistence_hash


def test_persistence_hash_changes_by_tenant(tmp_path):
    repository = GovernanceAssessmentRepository(
        tmp_path / "multi-tenant.sqlite3"
    )
    service = GovernanceAssessmentDemonstrationPersistenceService(
        repository
    )

    alpha = service.persist(
        demonstration=build_demonstration("tenant-alpha")
    )
    beta = service.persist(
        demonstration=build_demonstration("tenant-beta")
    )

    assert alpha.persistence_hash != beta.persistence_hash


def test_incomplete_demonstration_is_rejected(
    persistence_service,
):
    demonstration = build_demonstration()
    incomplete = replace(
        demonstration,
        artifact_commitments={
            **demonstration.artifact_commitments,
            "report_package_hash": "wrong-hash",
        },
    )

    with pytest.raises(
        DemonstrationPersistenceError,
        match="must be complete",
    ):
        persistence_service.persist(
            demonstration=incomplete
        )


def test_existing_assessment_name_mismatch_is_rejected(
    persistence_service,
    repository,
):
    repository.create_assessment(
        context=build_context(),
        assessment_name="Different Assessment",
        status="draft",
    )

    with pytest.raises(
        DemonstrationPersistenceError,
        match="name does not match",
    ):
        persistence_service.persist(
            demonstration=build_demonstration()
        )


def test_serialized_result_contains_repository_manifest(
    persistence_service,
):
    serialized = persistence_service.persist(
        demonstration=build_demonstration()
    ).to_dict()

    assert serialized["completed"] is True
    assert serialized["artifact_count"] == 10
    assert serialized["repository_chain_valid"] is True
    assert serialized["persistence_hash"]


def test_persistence_result_is_immutable(
    persistence_service,
):
    result = persistence_service.persist(
        demonstration=build_demonstration()
    )

    with pytest.raises(FrozenInstanceError):
        result.persistence_hash = "changed"
