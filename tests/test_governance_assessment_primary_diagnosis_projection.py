from __future__ import annotations

from types import SimpleNamespace

import pytest

import backend.app.gagf.governance_assessment_primary_diagnosis_projection as module

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_primary_diagnosis_projection import (
    PRIMARY_DIAGNOSIS_EVIDENCE_ARTIFACT_TYPE,
    GovernanceAssessmentPrimaryDiagnosisProjectionService,
    PrimaryDiagnosisProjectionError,
)


HIERARCHY_KEY = (
    "tenant-a/client-a/"
    "engagement-a/assessment-a"
)


def build_context():
    return (
        CommercialHierarchyContext(
            tenant_id="tenant-a",
            client_id="client-a",
            engagement_id="engagement-a",
            assessment_id="assessment-a",
        )
    )


class FakeArtifact:
    def __init__(
        self,
        *,
        payload,
        artifact_id="artifact-1",
        artifact_hash="artifact-hash-1",
        sequence_number=10,
    ):
        self.payload = payload
        self.artifact_id = artifact_id
        self.artifact_hash = artifact_hash
        self.sequence_number = sequence_number


class FakeRepository:
    instances = []

    initial_chain_valid = True
    final_chain_valid = True
    existing_artifacts = []

    def __init__(
        self,
        database_path,
    ):
        self.database_path = database_path
        self.verify_count = 0
        self.append_calls = []
        self.list_calls = []

        self.artifacts = list(
            type(self)
            .existing_artifacts
        )

        type(self).instances.append(
            self
        )

    @classmethod
    def reset(
        cls,
    ):
        cls.instances = []
        cls.initial_chain_valid = True
        cls.final_chain_valid = True
        cls.existing_artifacts = []

    def verify_chain(
        self,
        *,
        context,
    ):
        self.verify_count += 1

        if self.verify_count == 1:
            return (
                type(self)
                .initial_chain_valid
            )

        return (
            type(self)
            .final_chain_valid
        )

    def list_artifacts(
        self,
        *,
        context,
        artifact_type,
    ):
        self.list_calls.append(
            (
                context.hierarchy_key,
                artifact_type,
            )
        )

        return list(
            self.artifacts
        )

    def append_artifact(
        self,
        *,
        context,
        artifact_type,
        payload,
    ):
        self.append_calls.append(
            (
                context.hierarchy_key,
                artifact_type,
                payload,
            )
        )

        artifact = FakeArtifact(
            payload=payload
        )

        self.artifacts.append(
            artifact
        )

        return artifact


class FakeStructuralProjectionService:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
        repository_chain_valid=True,
        diagnostic_integrity_verified=True,
    ):
        self.result = (
            SimpleNamespace(
                hierarchy_key=(
                    hierarchy_key
                ),

                structural_summary=(
                    SimpleNamespace(
                        hierarchy_key=(
                            hierarchy_key
                        )
                    )
                ),

                repository_chain_valid=(
                    repository_chain_valid
                ),

                diagnostic_integrity_verified=(
                    diagnostic_integrity_verified
                ),
            )
        )

        self.calls = []

    def project(
        self,
        *,
        database_path,
        context,
    ):
        self.calls.append(
            (
                str(database_path),
                context.hierarchy_key,
            )
        )

        return self.result


class FakeStructuralClassificationService:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
    ):
        self.result = (
            SimpleNamespace(
                hierarchy_key=(
                    hierarchy_key
                ),
                summary_hash=(
                    "classification-summary-hash"
                ),
            )
        )

        self.calls = []

    def classify(
        self,
        *,
        structural_summary,
    ):
        self.calls.append(
            structural_summary
        )

        return self.result


class FakePrimaryDiagnosisSummary:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
    ):
        self.hierarchy_key = (
            hierarchy_key
        )

        self.summary_hash = (
            "primary-summary-hash"
        )

        self.condition_count = 2

        self.highest_ranked_condition = (
            "APPROVAL_DELAYED"
        )

    def to_dict(
        self,
    ):
        return {
            "tenant_id":
                "tenant-a",
            "client_id":
                "client-a",
            "engagement_id":
                "engagement-a",
            "assessment_id":
                "assessment-a",
            "hierarchy_key":
                self.hierarchy_key,
            "conditions": [],
            "condition_count":
                self.condition_count,
            "ranked_conditions": [
                "APPROVAL_DELAYED",
                "SECURITY_REVIEW",
            ],
            "highest_ranked_condition":
                self.highest_ranked_condition,
            "summary_hash":
                self.summary_hash,
            "authority":
                "GAGF_FIP_ONLY",
            "schema_version":
                "1.0.0",
        }


class FakePrimaryDiagnosisService:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
    ):
        self.result = (
            FakePrimaryDiagnosisSummary(
                hierarchy_key=(
                    hierarchy_key
                )
            )
        )

        self.calls = []

    def analyze(
        self,
        *,
        structural_classification_summary,
    ):
        self.calls.append(
            structural_classification_summary
        )

        return self.result


@pytest.fixture(
    autouse=True
)
def patch_repository(
    monkeypatch,
):
    FakeRepository.reset()

    monkeypatch.setattr(
        module,
        "GovernanceAssessmentRepository",
        FakeRepository,
    )


def build_service(
    *,
    structural_projection=None,
    classification=None,
    primary=None,
):
    return (
        GovernanceAssessmentPrimaryDiagnosisProjectionService(
            structural_projection_service=(
                structural_projection
                or
                FakeStructuralProjectionService()
            ),

            structural_classification_service=(
                classification
                or
                FakeStructuralClassificationService()
            ),

            primary_diagnosis_service=(
                primary
                or
                FakePrimaryDiagnosisService()
            ),
        )
    )


def test_projection_preserves_hierarchy():
    result = (
        build_service()
        .project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )
    )

    assert (
        result.hierarchy_key
        == HIERARCHY_KEY
    )


def test_projection_uses_structural_projection():
    structural = (
        FakeStructuralProjectionService()
    )

    service = build_service(
        structural_projection=(
            structural
        )
    )

    service.project(
        database_path="assessment.sqlite3",
        context=build_context(),
    )

    assert (
        structural.calls
        == [
            (
                "assessment.sqlite3",
                HIERARCHY_KEY,
            )
        ]
    )


def test_projection_classifies_structural_summary():
    structural = (
        FakeStructuralProjectionService()
    )

    classification = (
        FakeStructuralClassificationService()
    )

    service = build_service(
        structural_projection=(
            structural
        ),
        classification=(
            classification
        ),
    )

    service.project(
        database_path="assessment.sqlite3",
        context=build_context(),
    )

    assert (
        classification.calls
        == [
            structural.result
            .structural_summary
        ]
    )


def test_projection_derives_primary_diagnosis_evidence():
    classification = (
        FakeStructuralClassificationService()
    )

    primary = (
        FakePrimaryDiagnosisService()
    )

    service = build_service(
        classification=(
            classification
        ),
        primary=primary,
    )

    service.project(
        database_path="assessment.sqlite3",
        context=build_context(),
    )

    assert (
        primary.calls
        == [
            classification.result
        ]
    )


def test_projection_appends_expected_artifact_type():
    service = build_service()

    result = service.project(
        database_path="assessment.sqlite3",
        context=build_context(),
    )

    repository = (
        FakeRepository.instances[0]
    )

    assert len(
        repository.append_calls
    ) == 1

    _, artifact_type, payload = (
        repository.append_calls[0]
    )

    assert (
        artifact_type
        == PRIMARY_DIAGNOSIS_EVIDENCE_ARTIFACT_TYPE
    )

    assert (
        payload
        == result
        .primary_diagnosis_summary
        .to_dict()
    )


def test_projection_marks_new_artifact_not_reused():
    result = (
        build_service()
        .project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )
    )

    assert (
        result.reused_existing
        is False
    )


def test_projection_reuses_identical_existing_artifact():
    primary = (
        FakePrimaryDiagnosisService()
    )

    FakeRepository.existing_artifacts = [
        FakeArtifact(
            payload=(
                primary.result
                .to_dict()
            ),
            artifact_id="existing-artifact",
            artifact_hash="existing-hash",
            sequence_number=22,
        )
    ]

    result = (
        build_service(
            primary=primary
        )
        .project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )
    )

    repository = (
        FakeRepository.instances[0]
    )

    assert (
        result.reused_existing
        is True
    )

    assert (
        result.artifact_id
        == "existing-artifact"
    )

    assert (
        result.artifact_hash
        == "existing-hash"
    )

    assert (
        result.sequence_number
        == 22
    )

    assert (
        repository.append_calls
        == []
    )


def test_projection_rejects_different_existing_artifact():
    FakeRepository.existing_artifacts = [
        FakeArtifact(
            payload={
                "different":
                    True,
            }
        )
    ]

    with pytest.raises(
        PrimaryDiagnosisProjectionError,
        match=(
            "does not match deterministic projection"
        ),
    ):
        build_service().project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_rejects_multiple_existing_artifacts():
    FakeRepository.existing_artifacts = [
        FakeArtifact(
            payload={}
        ),
        FakeArtifact(
            payload={}
        ),
    ]

    with pytest.raises(
        PrimaryDiagnosisProjectionError,
        match=(
            "multiple primary-diagnosis-evidence"
        ),
    ):
        build_service().project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_rejects_invalid_initial_chain():
    FakeRepository.initial_chain_valid = False

    with pytest.raises(
        PrimaryDiagnosisProjectionError,
        match=(
            "invalid before primary-diagnosis projection"
        ),
    ):
        build_service().project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_rejects_invalid_final_chain():
    FakeRepository.final_chain_valid = False

    with pytest.raises(
        PrimaryDiagnosisProjectionError,
        match=(
            "invalid after primary-diagnosis projection"
        ),
    ):
        build_service().project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_rejects_structural_hierarchy_mismatch():
    structural = (
        FakeStructuralProjectionService(
            hierarchy_key=(
                "wrong/client/engagement/assessment"
            )
        )
    )

    with pytest.raises(
        PrimaryDiagnosisProjectionError,
        match=(
            "structural projection hierarchy"
        ),
    ):
        build_service(
            structural_projection=(
                structural
            )
        ).project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_requires_structural_chain_validity():
    structural = (
        FakeStructuralProjectionService(
            repository_chain_valid=False
        )
    )

    with pytest.raises(
        PrimaryDiagnosisProjectionError,
        match=(
            "preserve repository chain validity"
        ),
    ):
        build_service(
            structural_projection=(
                structural
            )
        ).project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_requires_diagnostic_integrity():
    structural = (
        FakeStructuralProjectionService(
            diagnostic_integrity_verified=False
        )
    )

    with pytest.raises(
        PrimaryDiagnosisProjectionError,
        match=(
            "did not verify diagnostic integrity"
        ),
    ):
        build_service(
            structural_projection=(
                structural
            )
        ).project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_rejects_classification_hierarchy_mismatch():
    classification = (
        FakeStructuralClassificationService(
            hierarchy_key=(
                "wrong/client/engagement/assessment"
            )
        )
    )

    with pytest.raises(
        PrimaryDiagnosisProjectionError,
        match=(
            "structural classification hierarchy"
        ),
    ):
        build_service(
            classification=(
                classification
            )
        ).project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_rejects_primary_evidence_hierarchy_mismatch():
    primary = (
        FakePrimaryDiagnosisService(
            hierarchy_key=(
                "wrong/client/engagement/assessment"
            )
        )
    )

    with pytest.raises(
        PrimaryDiagnosisProjectionError,
        match=(
            "primary-diagnosis evidence hierarchy"
        ),
    ):
        build_service(
            primary=primary
        ).project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_result_exposes_primary_summary_hash():
    result = (
        build_service()
        .project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )
    )

    payload = result.to_dict()

    assert (
        payload[
            "primary_diagnosis_summary_hash"
        ]
        == "primary-summary-hash"
    )


def test_projection_result_exposes_classification_binding():
    result = (
        build_service()
        .project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )
    )

    payload = result.to_dict()

    assert (
        payload[
            "structural_classification_summary_hash"
        ]
        == "classification-summary-hash"
    )


def test_projection_result_preserves_rank_without_declaring_primary():
    result = (
        build_service()
        .project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )
    )

    payload = result.to_dict()

    assert (
        payload[
            "highest_ranked_condition"
        ]
        == "APPROVAL_DELAYED"
    )

    assert (
        "primary_condition"
        not in payload
    )

    assert (
        "root_cause"
        not in payload
    )

    assert (
        "intervention"
        not in payload
    )