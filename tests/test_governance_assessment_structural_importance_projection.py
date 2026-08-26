from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import backend.app.gagf.governance_assessment_structural_importance_projection as projection_module

from backend.app.gagf.governance_assessment_persisted_reconstruction import (
    PersistedAssessmentReconstructionError,
)
from backend.app.gagf.governance_assessment_structural_importance_projection import (
    STRUCTURAL_IMPORTANCE_ARTIFACT_TYPE,
    STRUCTURAL_IMPORTANCE_PROJECTION_VERSION,
    GovernanceAssessmentStructuralImportanceProjectionService,
    StructuralImportanceProjectionError,
)


HIERARCHY_KEY = (
    "tenant-001/"
    "client-001/"
    "engagement-001/"
    "assessment-001"
)


CONTEXT = SimpleNamespace(
    hierarchy_key=HIERARCHY_KEY,
)


@dataclass
class FakeArtifact:
    artifact_id: str
    artifact_hash: str
    sequence_number: int
    payload: object


class FakeRepository:
    def __init__(
        self,
        *,
        artifacts: dict[
            str,
            list[FakeArtifact],
        ],
        verify_results: list[bool]
        | None = None,
    ) -> None:
        self.artifacts = artifacts

        self.verify_results = list(
            verify_results
            or (
                True,
                True,
            )
        )

        self.append_calls: list[
            tuple[
                object,
                str,
                object,
            ]
        ] = []

    def verify_chain(
        self,
        *,
        context,
    ) -> bool:
        if self.verify_results:
            return self.verify_results.pop(
                0
            )

        return True

    def list_artifacts(
        self,
        *,
        context,
        artifact_type=None,
    ):
        if artifact_type is None:
            flattened = []

            for values in (
                self.artifacts.values()
            ):
                flattened.extend(
                    values
                )

            return tuple(
                flattened
            )

        return tuple(
            self.artifacts.get(
                artifact_type,
                (),
            )
        )

    def append_artifact(
        self,
        *,
        context,
        artifact_type,
        payload,
    ):
        sequence_number = (
            sum(
                len(
                    values
                )
                for values
                in self.artifacts.values()
            )
            + 1
        )

        artifact = FakeArtifact(
            artifact_id=(
                f"artifact-{sequence_number}"
            ),
            artifact_hash=(
                f"hash-{sequence_number}"
            ),
            sequence_number=(
                sequence_number
            ),
            payload=payload,
        )

        self.artifacts.setdefault(
            artifact_type,
            [],
        ).append(
            artifact
        )

        self.append_calls.append(
            (
                context,
                artifact_type,
                payload,
            )
        )

        return artifact


class FakeReconstructionService:
    def __init__(
        self,
        *,
        intake_results=None,
        friction_summary=None,
    ) -> None:
        self.intake_results = (
            intake_results
            if intake_results is not None
            else ("intake-result",)
        )

        self.friction_summary = (
            friction_summary
            if friction_summary is not None
            else "friction-summary"
        )

        self.intake_payload = None
        self.friction_payload = None

    def require_single_artifact(
        self,
        *,
        repository,
        context,
        artifact_type,
    ):
        artifacts = (
            repository.list_artifacts(
                context=context,
                artifact_type=artifact_type,
            )
        )

        if len(
            artifacts
        ) != 1:
            raise (
                PersistedAssessmentReconstructionError(
                    f"assessment requires exactly one "
                    f"{artifact_type} artifact"
                )
            )

        return artifacts[0]

    def reconstruct_intake_results(
        self,
        *,
        payload,
        expected_hierarchy,
    ):
        self.intake_payload = payload

        assert (
            expected_hierarchy
            == HIERARCHY_KEY
        )

        return self.intake_results

    def reconstruct_friction_summary(
        self,
        *,
        payload,
        expected_hierarchy,
    ):
        self.friction_payload = payload

        assert (
            expected_hierarchy
            == HIERARCHY_KEY
        )

        return self.friction_summary


class FakeSignificanceSummary:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
        summary_hash="significance-hash",
    ) -> None:
        self.hierarchy_key = (
            hierarchy_key
        )

        self.summary_hash = (
            summary_hash
        )

    def to_dict(
        self,
    ):
        return {
            "hierarchy_key":
                self.hierarchy_key,
            "summary_hash":
                self.summary_hash,
            "conditions": [],
            "diagnosed_conditions": [],
            "dominant_condition": None,
            "schema_version": "1.0.0",
        }


class FakeSignificanceService:
    def __init__(
        self,
        summary=None,
    ) -> None:
        self.summary = (
            summary
            or FakeSignificanceSummary()
        )

        self.calls = []

    def classify(
        self,
        *,
        friction_summary,
        intake_results,
    ):
        self.calls.append(
            (
                friction_summary,
                intake_results,
            )
        )

        return self.summary


class FakeScopeService:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
    ) -> None:
        self.hierarchy_key = (
            hierarchy_key
        )

        self.calls = []

    def classify(
        self,
        *,
        significance_summary,
    ):
        self.calls.append(
            significance_summary
        )

        return SimpleNamespace(
            hierarchy_key=(
                self.hierarchy_key
            ),
        )


class FakeStructuralSummary:
    def __init__(
        self,
        *,
        hierarchy_key=HIERARCHY_KEY,
        summary_hash="structural-hash",
    ) -> None:
        self.hierarchy_key = (
            hierarchy_key
        )

        self.summary_hash = (
            summary_hash
        )

        self.conditions = (
            SimpleNamespace(
                category="condition-a",
            ),
            SimpleNamespace(
                category="condition-b",
            ),
        )

    def to_dict(
        self,
    ):
        return {
            "tenant_id":
                "tenant-001",
            "client_id":
                "client-001",
            "engagement_id":
                "engagement-001",
            "assessment_id":
                "assessment-001",
            "hierarchy_key":
                self.hierarchy_key,
            "conditions": [
                {
                    "category":
                        "condition-a",
                },
                {
                    "category":
                        "condition-b",
                },
            ],
            "summary_hash":
                self.summary_hash,
            "authority":
                "GAGF_FIP_ONLY",
            "schema_version":
                "1.0.0",
        }


class FakeStructuralService:
    def __init__(
        self,
        summary=None,
    ) -> None:
        self.summary = (
            summary
            or FakeStructuralSummary()
        )

        self.calls = []

    def analyze(
        self,
        *,
        friction_summary,
        significance_summary,
        scope_summary,
        intake_results,
    ):
        self.calls.append(
            {
                "friction_summary":
                    friction_summary,
                "significance_summary":
                    significance_summary,
                "scope_summary":
                    scope_summary,
                "intake_results":
                    intake_results,
            }
        )

        return self.summary


def base_artifacts(
    *,
    diagnostic_payload=None,
):
    significance = (
        FakeSignificanceSummary()
    )

    if diagnostic_payload is None:
        diagnostic_payload = (
            significance.to_dict()
        )

    return {
        "evidence-intake-batch": [
            FakeArtifact(
                artifact_id=(
                    "intake-artifact"
                ),
                artifact_hash=(
                    "intake-hash"
                ),
                sequence_number=1,
                payload={
                    "intake_results": [],
                },
            ),
        ],
        "friction-summary": [
            FakeArtifact(
                artifact_id=(
                    "friction-artifact"
                ),
                artifact_hash=(
                    "friction-hash"
                ),
                sequence_number=2,
                payload={
                    "hierarchy_key":
                        HIERARCHY_KEY,
                },
            ),
        ],
        "diagnostic-significance": [
            FakeArtifact(
                artifact_id=(
                    "diagnostic-artifact"
                ),
                artifact_hash=(
                    "diagnostic-hash"
                ),
                sequence_number=3,
                payload=(
                    diagnostic_payload
                ),
            ),
        ],
    }


def build_service(
    *,
    significance_summary=None,
    scope_hierarchy=HIERARCHY_KEY,
    structural_summary=None,
):
    reconstruction = (
        FakeReconstructionService()
    )

    significance = (
        FakeSignificanceService(
            significance_summary
        )
    )

    scope = (
        FakeScopeService(
            hierarchy_key=(
                scope_hierarchy
            )
        )
    )

    structural = (
        FakeStructuralService(
            structural_summary
        )
    )

    service = (
        GovernanceAssessmentStructuralImportanceProjectionService(
            reconstruction_service=(
                reconstruction
            ),
            significance_service=(
                significance
            ),
            scope_service=scope,
            structural_service=(
                structural
            ),
        )
    )

    return (
        service,
        reconstruction,
        significance,
        scope,
        structural,
    )


def install_repository(
    monkeypatch,
    repository,
):
    monkeypatch.setattr(
        projection_module,
        "GovernanceAssessmentRepository",
        lambda database_path:
            repository,
    )


def test_projection_appends_structural_artifact(
    monkeypatch,
):
    repository = FakeRepository(
        artifacts=base_artifacts()
    )

    install_repository(
        monkeypatch,
        repository,
    )

    (
        service,
        reconstruction,
        significance,
        scope,
        structural,
    ) = build_service()

    result = service.project(
        database_path="ignored.db",
        context=CONTEXT,
    )

    assert (
        result.hierarchy_key
        == HIERARCHY_KEY
    )

    assert (
        result.reused_existing
        is False
    )

    assert (
        result.repository_chain_valid
        is True
    )

    assert (
        result.diagnostic_integrity_verified
        is True
    )

    assert (
        result.condition_count
        == 2
    )

    assert (
        result.projection_version
        == STRUCTURAL_IMPORTANCE_PROJECTION_VERSION
    )

    assert (
        len(
            repository.append_calls
        )
        == 1
    )

    assert (
        repository.append_calls[
            0
        ][
            1
        ]
        == STRUCTURAL_IMPORTANCE_ARTIFACT_TYPE
    )

    assert (
        significance.calls
        == [
            (
                "friction-summary",
                ("intake-result",),
            )
        ]
    )

    assert (
        len(
            scope.calls
        )
        == 1
    )

    assert (
        len(
            structural.calls
        )
        == 1
    )

    assert (
        reconstruction.intake_payload
        == {
            "intake_results": [],
        }
    )


def test_projection_reuses_matching_existing_artifact(
    monkeypatch,
):
    structural_summary = (
        FakeStructuralSummary()
    )

    artifacts = base_artifacts()

    artifacts[
        STRUCTURAL_IMPORTANCE_ARTIFACT_TYPE
    ] = [
        FakeArtifact(
            artifact_id=(
                "existing-structural"
            ),
            artifact_hash=(
                "existing-hash"
            ),
            sequence_number=4,
            payload=(
                structural_summary.to_dict()
            ),
        ),
    ]

    repository = FakeRepository(
        artifacts=artifacts
    )

    install_repository(
        monkeypatch,
        repository,
    )

    (
        service,
        _,
        _,
        _,
        _,
    ) = build_service(
        structural_summary=(
            structural_summary
        )
    )

    result = service.project(
        database_path="ignored.db",
        context=CONTEXT,
    )

    assert (
        result.reused_existing
        is True
    )

    assert (
        result.artifact_id
        == "existing-structural"
    )

    assert (
        repository.append_calls
        == []
    )


def test_projection_is_idempotent(
    monkeypatch,
):
    repository = FakeRepository(
        artifacts=base_artifacts(),
        verify_results=[
            True,
            True,
            True,
            True,
        ],
    )

    install_repository(
        monkeypatch,
        repository,
    )

    (
        service,
        _,
        _,
        _,
        _,
    ) = build_service()

    first = service.project(
        database_path="ignored.db",
        context=CONTEXT,
    )

    second = service.project(
        database_path="ignored.db",
        context=CONTEXT,
    )

    assert (
        first.reused_existing
        is False
    )

    assert (
        second.reused_existing
        is True
    )

    assert (
        first.artifact_id
        == second.artifact_id
    )

    assert (
        first.artifact_hash
        == second.artifact_hash
    )

    assert (
        len(
            repository.append_calls
        )
        == 1
    )


def test_rejects_invalid_chain_before_projection(
    monkeypatch,
):
    repository = FakeRepository(
        artifacts=base_artifacts(),
        verify_results=[
            False,
        ],
    )

    install_repository(
        monkeypatch,
        repository,
    )

    service, _, _, _, _ = (
        build_service()
    )

    with pytest.raises(
        StructuralImportanceProjectionError,
        match="before structural-importance",
    ):
        service.project(
            database_path="ignored.db",
            context=CONTEXT,
        )

    assert (
        repository.append_calls
        == []
    )


def test_rejects_invalid_chain_after_projection(
    monkeypatch,
):
    repository = FakeRepository(
        artifacts=base_artifacts(),
        verify_results=[
            True,
            False,
        ],
    )

    install_repository(
        monkeypatch,
        repository,
    )

    service, _, _, _, _ = (
        build_service()
    )

    with pytest.raises(
        StructuralImportanceProjectionError,
        match="after structural-importance",
    ):
        service.project(
            database_path="ignored.db",
            context=CONTEXT,
        )


def test_requires_exactly_one_intake_artifact(
    monkeypatch,
):
    artifacts = base_artifacts()

    artifacts[
        "evidence-intake-batch"
    ] = []

    repository = FakeRepository(
        artifacts=artifacts
    )

    install_repository(
        monkeypatch,
        repository,
    )

    service, _, _, _, _ = (
        build_service()
    )

    with pytest.raises(
        StructuralImportanceProjectionError,
        match=(
            "exactly one "
            "evidence-intake-batch"
        ),
    ):
        service.project(
            database_path="ignored.db",
            context=CONTEXT,
        )


def test_requires_exactly_one_friction_artifact(
    monkeypatch,
):
    artifacts = base_artifacts()

    artifacts[
        "friction-summary"
    ] = []

    repository = FakeRepository(
        artifacts=artifacts
    )

    install_repository(
        monkeypatch,
        repository,
    )

    service, _, _, _, _ = (
        build_service()
    )

    with pytest.raises(
        StructuralImportanceProjectionError,
        match=(
            "exactly one "
            "friction-summary"
        ),
    ):
        service.project(
            database_path="ignored.db",
            context=CONTEXT,
        )


def test_requires_exactly_one_diagnostic_artifact(
    monkeypatch,
):
    artifacts = base_artifacts()

    artifacts[
        "diagnostic-significance"
    ] = []

    repository = FakeRepository(
        artifacts=artifacts
    )

    install_repository(
        monkeypatch,
        repository,
    )

    service, _, _, _, _ = (
        build_service()
    )

    with pytest.raises(
        StructuralImportanceProjectionError,
        match=(
            "exactly one "
            "diagnostic-significance"
        ),
    ):
        service.project(
            database_path="ignored.db",
            context=CONTEXT,
        )


def test_rejects_persisted_diagnostic_drift(
    monkeypatch,
):
    repository = FakeRepository(
        artifacts=base_artifacts(
            diagnostic_payload={
                "hierarchy_key":
                    HIERARCHY_KEY,
                "summary_hash":
                    "tampered",
            }
        )
    )

    install_repository(
        monkeypatch,
        repository,
    )

    service, _, _, _, _ = (
        build_service()
    )

    with pytest.raises(
        StructuralImportanceProjectionError,
        match=(
            "does not match deterministic "
            "recomputation"
        ),
    ):
        service.project(
            database_path="ignored.db",
            context=CONTEXT,
        )

    assert (
        repository.append_calls
        == []
    )


def test_rejects_significance_hierarchy_mismatch(
    monkeypatch,
):
    repository = FakeRepository(
        artifacts=base_artifacts()
    )

    install_repository(
        monkeypatch,
        repository,
    )

    significance_summary = (
        FakeSignificanceSummary(
            hierarchy_key=(
                "wrong-hierarchy"
            )
        )
    )

    (
        service,
        _,
        _,
        _,
        _,
    ) = build_service(
        significance_summary=(
            significance_summary
        )
    )

    with pytest.raises(
        StructuralImportanceProjectionError,
        match=(
            "recomputed diagnostic significance "
            "hierarchy"
        ),
    ):
        service.project(
            database_path="ignored.db",
            context=CONTEXT,
        )


def test_rejects_scope_hierarchy_mismatch(
    monkeypatch,
):
    repository = FakeRepository(
        artifacts=base_artifacts()
    )

    install_repository(
        monkeypatch,
        repository,
    )

    (
        service,
        _,
        _,
        _,
        _,
    ) = build_service(
        scope_hierarchy=(
            "wrong-hierarchy"
        )
    )

    with pytest.raises(
        StructuralImportanceProjectionError,
        match=(
            "diagnostic scope hierarchy"
        ),
    ):
        service.project(
            database_path="ignored.db",
            context=CONTEXT,
        )


def test_rejects_structural_hierarchy_mismatch(
    monkeypatch,
):
    repository = FakeRepository(
        artifacts=base_artifacts()
    )

    install_repository(
        monkeypatch,
        repository,
    )

    structural_summary = (
        FakeStructuralSummary(
            hierarchy_key=(
                "wrong-hierarchy"
            )
        )
    )

    (
        service,
        _,
        _,
        _,
        _,
    ) = build_service(
        structural_summary=(
            structural_summary
        )
    )

    with pytest.raises(
        StructuralImportanceProjectionError,
        match=(
            "structural-importance hierarchy"
        ),
    ):
        service.project(
            database_path="ignored.db",
            context=CONTEXT,
        )


def test_rejects_multiple_existing_structural_artifacts(
    monkeypatch,
):
    structural_summary = (
        FakeStructuralSummary()
    )

    artifacts = base_artifacts()

    artifacts[
        STRUCTURAL_IMPORTANCE_ARTIFACT_TYPE
    ] = [
        FakeArtifact(
            artifact_id="structural-1",
            artifact_hash="hash-1",
            sequence_number=4,
            payload=(
                structural_summary.to_dict()
            ),
        ),
        FakeArtifact(
            artifact_id="structural-2",
            artifact_hash="hash-2",
            sequence_number=5,
            payload=(
                structural_summary.to_dict()
            ),
        ),
    ]

    repository = FakeRepository(
        artifacts=artifacts
    )

    install_repository(
        monkeypatch,
        repository,
    )

    (
        service,
        _,
        _,
        _,
        _,
    ) = build_service(
        structural_summary=(
            structural_summary
        )
    )

    with pytest.raises(
        StructuralImportanceProjectionError,
        match=(
            "multiple structural-importance"
        ),
    ):
        service.project(
            database_path="ignored.db",
            context=CONTEXT,
        )


def test_rejects_existing_structural_drift(
    monkeypatch,
):
    artifacts = base_artifacts()

    artifacts[
        STRUCTURAL_IMPORTANCE_ARTIFACT_TYPE
    ] = [
        FakeArtifact(
            artifact_id=(
                "existing-structural"
            ),
            artifact_hash=(
                "existing-hash"
            ),
            sequence_number=4,
            payload={
                "summary_hash":
                    "different",
            },
        ),
    ]

    repository = FakeRepository(
        artifacts=artifacts
    )

    install_repository(
        monkeypatch,
        repository,
    )

    service, _, _, _, _ = (
        build_service()
    )

    with pytest.raises(
        StructuralImportanceProjectionError,
        match=(
            "does not match deterministic "
            "projection"
        ),
    ):
        service.project(
            database_path="ignored.db",
            context=CONTEXT,
        )


def test_result_to_dict_is_stable(
    monkeypatch,
):
    repository = FakeRepository(
        artifacts=base_artifacts()
    )

    install_repository(
        monkeypatch,
        repository,
    )

    service, _, _, _, _ = (
        build_service()
    )

    result = service.project(
        database_path="ignored.db",
        context=CONTEXT,
    )

    payload = result.to_dict()

    assert (
        payload[
            "hierarchy_key"
        ]
        == HIERARCHY_KEY
    )

    assert (
        payload[
            "structural_summary_hash"
        ]
        == "structural-hash"
    )

    assert (
        payload[
            "condition_count"
        ]
        == 2
    )

    assert (
        payload[
            "diagnostic_integrity_verified"
        ]
        is True
    )

    assert (
        payload[
            "projection_version"
        ]
        == STRUCTURAL_IMPORTANCE_PROJECTION_VERSION
    )