from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    ArtifactAlreadyExistsError,
    ArtifactIntegrityError,
    AssessmentAlreadyExistsError,
    AssessmentRecordNotFoundError,
    AssessmentRepositoryError,
    GovernanceAssessmentRepository,
)


NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


def build_context(
    tenant_id="tenant-alpha",
    client_id="client-acme",
    engagement_id="engagement-001",
    assessment_id="assessment-001",
):
    return CommercialHierarchyContext(
        tenant_id=tenant_id,
        client_id=client_id,
        engagement_id=engagement_id,
        assessment_id=assessment_id,
    )


@pytest.fixture
def repository(tmp_path):
    return GovernanceAssessmentRepository(
        tmp_path / "governance-assessments.sqlite3"
    )


def create_assessment(repository, context=None):
    return repository.create_assessment(
        context=context or build_context(),
        assessment_name="Governance Runway Assessment",
        status="draft",
        created_at=NOW,
    )


def test_create_and_get_assessment(repository):
    created = create_assessment(repository)
    retrieved = repository.get_assessment(
        context=build_context()
    )

    assert retrieved == created
    assert retrieved.hierarchy_key == (
        "tenant-alpha/client-acme/"
        "engagement-001/assessment-001"
    )


def test_assessment_record_hash_is_deterministic(tmp_path):
    first_repository = GovernanceAssessmentRepository(
        tmp_path / "first.sqlite3"
    )
    second_repository = GovernanceAssessmentRepository(
        tmp_path / "second.sqlite3"
    )

    first = create_assessment(first_repository)
    second = create_assessment(second_repository)

    assert first.record_hash == second.record_hash


def test_duplicate_assessment_is_rejected(repository):
    create_assessment(repository)

    with pytest.raises(AssessmentAlreadyExistsError):
        create_assessment(repository)


def test_foreign_tenant_assessment_is_hidden(repository):
    create_assessment(repository)

    with pytest.raises(AssessmentRecordNotFoundError):
        repository.get_assessment(
            context=build_context(tenant_id="tenant-beta")
        )


def test_list_assessments_is_tenant_scoped(repository):
    create_assessment(repository)
    create_assessment(
        repository,
        build_context(
            tenant_id="tenant-beta",
            assessment_id="assessment-002",
        ),
    )

    visible = repository.list_assessments(
        tenant_id="tenant-alpha"
    )

    assert len(visible) == 1
    assert visible[0].tenant_id == "tenant-alpha"


def test_engagement_filter_requires_client(repository):
    with pytest.raises(
        AssessmentRepositoryError,
        match="requires client_id",
    ):
        repository.list_assessments(
            tenant_id="tenant-alpha",
            engagement_id="engagement-001",
        )


def test_append_artifact_persists_canonical_payload(repository):
    create_assessment(repository)

    artifact = repository.append_artifact(
        context=build_context(),
        artifact_type="scope-configuration",
        payload={"b": 2, "a": 1},
        created_at=NOW,
    )

    assert artifact.payload == {"a": 1, "b": 2}
    assert artifact.sequence_number == 1
    assert artifact.previous_artifact_hash is None


def test_artifact_requires_existing_assessment(repository):
    with pytest.raises(AssessmentRecordNotFoundError):
        repository.append_artifact(
            context=build_context(),
            artifact_type="scope-configuration",
            payload={"value": 1},
        )


def test_duplicate_immutable_artifact_is_rejected(repository):
    create_assessment(repository)

    repository.append_artifact(
        context=build_context(),
        artifact_type="scope-configuration",
        payload={"value": 1},
        created_at=NOW,
    )

    with pytest.raises(ArtifactAlreadyExistsError):
        repository.append_artifact(
            context=build_context(),
            artifact_type="scope-configuration",
            payload={"value": 1},
            created_at=NOW,
        )


def test_artifacts_receive_contiguous_sequence(repository):
    create_assessment(repository)

    first = repository.append_artifact(
        context=build_context(),
        artifact_type="scope-configuration",
        payload={"value": 1},
        created_at=NOW,
    )
    second = repository.append_artifact(
        context=build_context(),
        artifact_type="evidence-quality",
        payload={"value": 2},
        created_at=NOW,
    )

    assert first.sequence_number == 1
    assert second.sequence_number == 2
    assert second.previous_artifact_hash == first.artifact_hash


def test_list_artifacts_preserves_sequence(repository):
    create_assessment(repository)

    repository.append_artifact(
        context=build_context(),
        artifact_type="scope-configuration",
        payload={"value": 1},
    )
    repository.append_artifact(
        context=build_context(),
        artifact_type="evidence-quality",
        payload={"value": 2},
    )

    artifacts = repository.list_artifacts(
        context=build_context()
    )

    assert [item.sequence_number for item in artifacts] == [1, 2]


def test_artifact_listing_can_filter_by_type(repository):
    create_assessment(repository)

    repository.append_artifact(
        context=build_context(),
        artifact_type="scope-configuration",
        payload={"value": 1},
    )
    repository.append_artifact(
        context=build_context(),
        artifact_type="evidence-quality",
        payload={"value": 2},
    )

    artifacts = repository.list_artifacts(
        context=build_context(),
        artifact_type="evidence-quality",
    )

    assert len(artifacts) == 1
    assert artifacts[0].artifact_type == "evidence-quality"


def test_get_artifact_is_hierarchy_scoped(repository):
    create_assessment(repository)
    artifact = repository.append_artifact(
        context=build_context(),
        artifact_type="scope-configuration",
        payload={"value": 1},
    )

    with pytest.raises(AssessmentRecordNotFoundError):
        repository.get_artifact(
            context=build_context(tenant_id="tenant-beta"),
            artifact_id=artifact.artifact_id,
        )


def test_artifact_chain_verifies(repository):
    create_assessment(repository)

    for index in range(1, 4):
        repository.append_artifact(
            context=build_context(),
            artifact_type=f"artifact-{index}",
            payload={"index": index},
        )

    assert repository.verify_chain(
        context=build_context()
    ) is True


def test_tampered_payload_is_detected(repository):
    create_assessment(repository)
    artifact = repository.append_artifact(
        context=build_context(),
        artifact_type="scope-configuration",
        payload={"value": 1},
    )

    with repository._connect() as connection:
        connection.execute(
            "UPDATE governance_assessment_artifacts "
            "SET payload_json = ? WHERE artifact_id = ?",
            ('{"value":999}', artifact.artifact_id),
        )

    with pytest.raises(
        ArtifactIntegrityError,
        match="payload hash",
    ):
        repository.get_artifact(
            context=build_context(),
            artifact_id=artifact.artifact_id,
        )


def test_artifact_and_assessment_records_are_immutable(repository):
    assessment = create_assessment(repository)
    artifact = repository.append_artifact(
        context=build_context(),
        artifact_type="scope-configuration",
        payload={"value": 1},
    )

    with pytest.raises(FrozenInstanceError):
        assessment.status = "complete"

    with pytest.raises(FrozenInstanceError):
        artifact.artifact_type = "changed"
