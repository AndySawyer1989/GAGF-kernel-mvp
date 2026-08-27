from __future__ import annotations

from types import SimpleNamespace

import pytest

import backend.app.gagf.governance_assessment_diagnostic_separation_projection as module

from backend.app.gagf.governance_assessment_diagnostic_separation_projection import (
    DIAGNOSTIC_SEPARATION_ARTIFACT_TYPE,
    GovernanceAssessmentDiagnosticSeparationProjectionService,
    DiagnosticSeparationProjectionError,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
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
        sequence_number=20,
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
        self.database_path = (
            database_path
        )

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

        artifact = (
            FakeArtifact(
                payload=payload
            )
        )

        self.artifacts.append(
            artifact
        )

        return artifact


class FakePrimaryDiagnosisSummary:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
        summary_hash="primary-summary-hash",
    ):
        self.hierarchy_key = (
            hierarchy_key
        )

        self.summary_hash = (
            summary_hash
        )


class FakePrimaryProjectionResult:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
        summary_hierarchy_key=None,
        repository_chain_valid=True,
        structural_projection_verified=True,
        structural_classification_verified=True,
    ):
        self.hierarchy_key = (
            hierarchy_key
        )

        self.primary_diagnosis_summary = (
            FakePrimaryDiagnosisSummary(
                hierarchy_key=(
                    summary_hierarchy_key
                    or hierarchy_key
                )
            )
        )

        self.repository_chain_valid = (
            repository_chain_valid
        )

        self.structural_projection_verified = (
            structural_projection_verified
        )

        self.structural_classification_verified = (
            structural_classification_verified
        )


class FakePrimaryProjectionService:
    def __init__(
        self,
        *,
        result=None,
    ):
        self.result = (
            result
            or
            FakePrimaryProjectionResult()
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
                str(
                    database_path
                ),
                context.hierarchy_key,
            )
        )

        return (
            self.result
        )


class FakeSeparationSummary:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
        primary_summary_hash=(
            "primary-summary-hash"
        ),
    ):
        self.hierarchy_key = (
            hierarchy_key
        )

        self.primary_diagnosis_summary_hash = (
            primary_summary_hash
        )

        self.summary_hash = (
            "separation-summary-hash"
        )

        self.leading_candidate_category = (
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

            "leading_candidate_category":
                self.leading_candidate_category,

            "primary_diagnosis_summary_hash":
                self.primary_diagnosis_summary_hash,

            "summary_hash":
                self.summary_hash,

            "authority":
                "GAGF_FIP_ONLY",

            "schema_version":
                "1.0.0",
        }


class FakeSeparationService:
    def __init__(
        self,
        *,
        result=None,
    ):
        self.result = (
            result
            or
            FakeSeparationSummary()
        )

        self.calls = []

    def analyze(
        self,
        *,
        primary_diagnosis_summary,
    ):
        self.calls.append(
            primary_diagnosis_summary
        )

        return (
            self.result
        )


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
    primary_projection=None,
    separation=None,
):
    return (
        GovernanceAssessmentDiagnosticSeparationProjectionService(
            primary_projection_service=(
                primary_projection
                or
                FakePrimaryProjectionService()
            ),

            separation_service=(
                separation
                or
                FakeSeparationService()
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


def test_projection_calls_primary_projection():
    primary = (
        FakePrimaryProjectionService()
    )

    service = build_service(
        primary_projection=(
            primary
        )
    )

    service.project(
        database_path="assessment.sqlite3",
        context=build_context(),
    )

    assert (
        primary.calls
        == [
            (
                "assessment.sqlite3",
                HIERARCHY_KEY,
            )
        ]
    )


def test_projection_analyzes_projected_primary_summary():
    primary = (
        FakePrimaryProjectionService()
    )

    separation = (
        FakeSeparationService()
    )

    service = build_service(
        primary_projection=(
            primary
        ),
        separation=(
            separation
        ),
    )

    service.project(
        database_path="assessment.sqlite3",
        context=build_context(),
    )

    assert (
        separation.calls
        == [
            primary.result
            .primary_diagnosis_summary
        ]
    )


def test_projection_appends_expected_artifact_type():
    service = (
        build_service()
    )

    result = (
        service.project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )
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
        == DIAGNOSTIC_SEPARATION_ARTIFACT_TYPE
    )

    assert (
        payload
        == result
        .separation_summary
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
    separation = (
        FakeSeparationService()
    )

    FakeRepository.existing_artifacts = [
        FakeArtifact(
            payload=(
                separation.result
                .to_dict()
            ),
            artifact_id="existing-artifact",
            artifact_hash="existing-hash",
            sequence_number=33,
        )
    ]

    result = (
        build_service(
            separation=separation
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
        == 33
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
        DiagnosticSeparationProjectionError,
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
        DiagnosticSeparationProjectionError,
        match=(
            "multiple diagnostic-separation-evidence"
        ),
    ):
        build_service().project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_rejects_invalid_initial_chain():
    FakeRepository.initial_chain_valid = (
        False
    )

    with pytest.raises(
        DiagnosticSeparationProjectionError,
        match=(
            "invalid before diagnostic-separation projection"
        ),
    ):
        build_service().project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_rejects_invalid_final_chain():
    FakeRepository.final_chain_valid = (
        False
    )

    with pytest.raises(
        DiagnosticSeparationProjectionError,
        match=(
            "invalid after diagnostic-separation projection"
        ),
    ):
        build_service().project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_rejects_primary_projection_hierarchy_mismatch():
    primary = (
        FakePrimaryProjectionService(
            result=(
                FakePrimaryProjectionResult(
                    hierarchy_key=(
                        "wrong/client/"
                        "engagement/assessment"
                    )
                )
            )
        )
    )

    with pytest.raises(
        DiagnosticSeparationProjectionError,
        match=(
            "primary-diagnosis projection hierarchy"
        ),
    ):
        build_service(
            primary_projection=(
                primary
            )
        ).project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_requires_primary_chain_validity():
    primary = (
        FakePrimaryProjectionService(
            result=(
                FakePrimaryProjectionResult(
                    repository_chain_valid=False
                )
            )
        )
    )

    with pytest.raises(
        DiagnosticSeparationProjectionError,
        match=(
            "preserve repository chain validity"
        ),
    ):
        build_service(
            primary_projection=(
                primary
            )
        ).project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_requires_structural_projection_verification():
    primary = (
        FakePrimaryProjectionService(
            result=(
                FakePrimaryProjectionResult(
                    structural_projection_verified=False
                )
            )
        )
    )

    with pytest.raises(
        DiagnosticSeparationProjectionError,
        match=(
            "verify structural projection"
        ),
    ):
        build_service(
            primary_projection=(
                primary
            )
        ).project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_requires_structural_classification_verification():
    primary = (
        FakePrimaryProjectionService(
            result=(
                FakePrimaryProjectionResult(
                    structural_classification_verified=False
                )
            )
        )
    )

    with pytest.raises(
        DiagnosticSeparationProjectionError,
        match=(
            "verify structural classification"
        ),
    ):
        build_service(
            primary_projection=(
                primary
            )
        ).project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_rejects_primary_summary_hierarchy_mismatch():
    primary = (
        FakePrimaryProjectionService(
            result=(
                FakePrimaryProjectionResult(
                    hierarchy_key=(
                        HIERARCHY_KEY
                    ),
                    summary_hierarchy_key=(
                        "wrong/client/"
                        "engagement/assessment"
                    ),
                )
            )
        )
    )

    with pytest.raises(
        DiagnosticSeparationProjectionError,
        match=(
            "projected primary-diagnosis evidence hierarchy"
        ),
    ):
        build_service(
            primary_projection=(
                primary
            )
        ).project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_rejects_separation_hierarchy_mismatch():
    separation = (
        FakeSeparationService(
            result=(
                FakeSeparationSummary(
                    hierarchy_key=(
                        "wrong/client/"
                        "engagement/assessment"
                    )
                )
            )
        )
    )

    with pytest.raises(
        DiagnosticSeparationProjectionError,
        match=(
            "diagnostic-separation hierarchy"
        ),
    ):
        build_service(
            separation=(
                separation
            )
        ).project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_rejects_primary_summary_hash_mismatch():
    separation = (
        FakeSeparationService(
            result=(
                FakeSeparationSummary(
                    primary_summary_hash=(
                        "wrong-primary-hash"
                    )
                )
            )
        )
    )

    with pytest.raises(
        DiagnosticSeparationProjectionError,
        match=(
            "not bound to the projected"
        ),
    ):
        build_service(
            separation=(
                separation
            )
        ).project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )


def test_projection_result_exposes_separation_summary_hash():
    result = (
        build_service()
        .project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )
    )

    payload = (
        result.to_dict()
    )

    assert (
        payload[
            "separation_summary_hash"
        ]
        == "separation-summary-hash"
    )


def test_projection_result_exposes_primary_summary_binding():
    result = (
        build_service()
        .project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )
    )

    payload = (
        result.to_dict()
    )

    assert (
        payload[
            "primary_diagnosis_summary_hash"
        ]
        == "primary-summary-hash"
    )


def test_projection_result_exposes_leading_candidate_only_as_rank():
    result = (
        build_service()
        .project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )
    )

    payload = (
        result.to_dict()
    )

    assert (
        payload[
            "leading_candidate_category"
        ]
        == "APPROVAL_DELAYED"
    )

    assert (
        "primary_diagnosis"
        not in payload
    )

    assert (
        "root_cause"
        not in payload
    )

    assert (
        "confidence"
        not in payload
    )


def test_projection_reports_integrity_flags():
    result = (
        build_service()
        .project(
            database_path="assessment.sqlite3",
            context=build_context(),
        )
    )

    assert (
        result.primary_projection_verified
        is True
    )

    assert (
        result.structural_projection_verified
        is True
    )

    assert (
        result.structural_classification_verified
        is True
    )

    assert (
        result.repository_chain_valid
        is True
    )