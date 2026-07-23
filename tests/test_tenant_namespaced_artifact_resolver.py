from dataclasses import FrozenInstanceError
import sqlite3

import pytest

from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
)
from backend.app.gagf.scientific_calculation_contract import (
    EVIDENCE_CONFIDENCE_CONTRACT,
    CalculationAuthority,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificExecutionContext,
)
from backend.app.gagf.tenant_namespaced_artifact_resolver import (
    TENANT_NAMESPACED_ARTIFACT_RESOLVER_ID,
    TENANT_NAMESPACED_ARTIFACT_RESOLVER_VERSION,
    TenantNamespacedArtifactIntegrityError,
    TenantNamespacedArtifactNotFoundError,
    TenantNamespacedArtifactResolver,
)
from backend.app.gagf.tenant_namespaced_execution import (
    TenantNamespacedExecutionPaths,
    TenantNamespacedScientificExecutionService,
)


def complete_evidence() -> AuthorityEscalationEvidence:
    return AuthorityEscalationEvidence(
        deterministic_replay_verified=True,
        canonical_input_binding_verified=True,
        calculation_version_frozen=True,
        regression_suite_passed=True,
        validation_report_present=True,
        constitutional_approval_present=True,
    )


def context(
    *,
    tenant_id="tenant-alpha",
    request_id="request-alpha",
):
    return ScientificExecutionContext(
        tenant_id=tenant_id,
        actor_id="actor-1",
        credential_id="credential-1",
        session_id="session-1",
        role_id="scientific-reviewer",
        policy_scope="scientific-authority:evaluate",
        request_id=request_id,
        correlation_id="correlation-1",
    )


def paths(tmp_path) -> TenantNamespacedExecutionPaths:
    return TenantNamespacedExecutionPaths(
        authority_database_path=tmp_path / "authority.db",
        audit_database_path=tmp_path / "audit.db",
        checkpoint_database_path=tmp_path / "checkpoint.db",
        journal_database_path=tmp_path / "journal.db",
        context_binding_database_path=(
            tmp_path / "bindings.db"
        ),
        namespace_database_path=(
            tmp_path / "namespaces.db"
        ),
    )


def build_system(tmp_path):
    execution_paths = paths(tmp_path)

    execution_service = (
        TenantNamespacedScientificExecutionService(
            paths=execution_paths
        )
    )

    resolver = TenantNamespacedArtifactResolver(
        namespace_database_path=(
            execution_paths.namespace_database_path
        ),
        authority_database_path=(
            execution_paths.authority_database_path
        ),
        checkpoint_database_path=(
            execution_paths.checkpoint_database_path
        ),
        journal_database_path=(
            execution_paths.journal_database_path
        ),
        context_binding_database_path=(
            execution_paths.context_binding_database_path
        ),
    )

    return execution_service, resolver, execution_paths


def execute(
    service,
    *,
    tenant_id="tenant-alpha",
    request_id="request-alpha",
):
    return service.execute(
        context=context(
            tenant_id=tenant_id,
            request_id=request_id,
        ),
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )


def test_resolver_has_stable_identity():
    assert TENANT_NAMESPACED_ARTIFACT_RESOLVER_ID == (
        "tenant-namespaced-scientific-artifact-resolver"
    )
    assert TENANT_NAMESPACED_ARTIFACT_RESOLVER_VERSION == (
        "0.1.0"
    )


def test_resolves_namespaced_authority_receipt(tmp_path):
    service, resolver, _ = build_system(tmp_path)
    execution = execute(service)

    public_id = (
        execution.namespace_bundle.authority_receipt
        .namespaced_artifact_id
    )

    resolution = resolver.resolve_authority_receipt(
        tenant_id="tenant-alpha",
        namespaced_artifact_id=public_id,
    )

    assert resolution.tenant_id == "tenant-alpha"
    assert resolution.artifact_type == "authority_receipt"
    assert resolution.namespaced_artifact_id == public_id
    assert resolution.canonical_artifact_id == (
        execution.pipeline_result.pipeline_result
        .authority_receipt_hash
    )
    assert resolution.artifact["artifact_type"] == (
        "authority_receipt"
    )


def test_resolves_namespaced_checkpoint(tmp_path):
    service, resolver, _ = build_system(tmp_path)
    execution = execute(service)

    public_id = (
        execution.namespace_bundle.checkpoint
        .namespaced_artifact_id
    )

    resolution = resolver.resolve_checkpoint(
        tenant_id="tenant-alpha",
        namespaced_artifact_id=public_id,
    )

    assert resolution.artifact_type == "checkpoint"
    assert resolution.canonical_artifact_id == (
        execution.pipeline_result.pipeline_result
        .checkpoint_hash
    )


def test_resolves_namespaced_execution(tmp_path):
    service, resolver, _ = build_system(tmp_path)
    execution = execute(service)

    public_id = (
        execution.namespace_bundle.execution
        .namespaced_artifact_id
    )

    resolution = resolver.resolve_execution(
        tenant_id="tenant-alpha",
        namespaced_artifact_id=public_id,
    )

    assert resolution.artifact_type == "execution"
    assert resolution.canonical_artifact_id == (
        execution.pipeline_result.execution_id
    )
    assert resolution.artifact["execution"]["state"] == (
        "COMPLETED"
    )


def test_resolves_namespaced_context_binding(tmp_path):
    service, resolver, _ = build_system(tmp_path)
    execution = execute(service)

    public_id = (
        execution.namespace_bundle.context_binding
        .namespaced_artifact_id
    )

    resolution = resolver.resolve_context_binding(
        tenant_id="tenant-alpha",
        namespaced_artifact_id=public_id,
    )

    assert resolution.artifact_type == "context_binding"
    assert resolution.canonical_artifact_id == (
        execution.context_binding.binding.binding_hash
    )


def test_other_tenant_cannot_resolve_public_id(tmp_path):
    service, resolver, _ = build_system(tmp_path)
    execution = execute(service)

    public_id = (
        execution.namespace_bundle.checkpoint
        .namespaced_artifact_id
    )

    with pytest.raises(
        TenantNamespacedArtifactNotFoundError,
        match="was not found",
    ):
        resolver.resolve_checkpoint(
            tenant_id="tenant-beta",
            namespaced_artifact_id=public_id,
        )


def test_identical_canonical_results_resolve_per_tenant(
    tmp_path,
):
    service, resolver, _ = build_system(tmp_path)

    alpha = execute(
        service,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    beta = execute(
        service,
        tenant_id="tenant-beta",
        request_id="request-beta",
    )

    assert (
        alpha.namespace_bundle.checkpoint
        .canonical_artifact_id
        == beta.namespace_bundle.checkpoint
        .canonical_artifact_id
    )

    alpha_resolution = resolver.resolve_checkpoint(
        tenant_id="tenant-alpha",
        namespaced_artifact_id=(
            alpha.namespace_bundle.checkpoint
            .namespaced_artifact_id
        ),
    )
    beta_resolution = resolver.resolve_checkpoint(
        tenant_id="tenant-beta",
        namespaced_artifact_id=(
            beta.namespace_bundle.checkpoint
            .namespaced_artifact_id
        ),
    )

    assert (
        alpha_resolution.namespaced_artifact_id
        != beta_resolution.namespaced_artifact_id
    )
    assert (
        alpha_resolution.canonical_artifact_id
        == beta_resolution.canonical_artifact_id
    )


def test_wrong_artifact_type_does_not_resolve(tmp_path):
    service, resolver, _ = build_system(tmp_path)
    execution = execute(service)

    checkpoint_public_id = (
        execution.namespace_bundle.checkpoint
        .namespaced_artifact_id
    )

    with pytest.raises(
        TenantNamespacedArtifactNotFoundError,
    ):
        resolver.resolve_execution(
            tenant_id="tenant-alpha",
            namespaced_artifact_id=checkpoint_public_id,
        )


def test_unknown_namespaced_id_returns_not_found(
    tmp_path,
):
    _, resolver, _ = build_system(tmp_path)

    with pytest.raises(
        TenantNamespacedArtifactNotFoundError,
    ):
        resolver.resolve_checkpoint(
            tenant_id="tenant-alpha",
            namespaced_artifact_id="0" * 64,
        )


def test_tampered_namespace_is_detected(tmp_path):
    service, resolver, execution_paths = build_system(
        tmp_path
    )
    execution = execute(service)

    public_id = (
        execution.namespace_bundle.checkpoint
        .namespaced_artifact_id
    )

    with sqlite3.connect(
        execution_paths.namespace_database_path
    ) as connection:
        row = connection.execute(
            """
            SELECT namespace_json
            FROM tenant_artifact_namespaces
            WHERE namespaced_artifact_id = ?
            """,
            (public_id,),
        ).fetchone()

        tampered = row[0].replace(
            '"tenant-alpha"',
            '"tenant-beta"',
        )

        connection.execute(
            """
            UPDATE tenant_artifact_namespaces
            SET namespace_json = ?
            WHERE namespaced_artifact_id = ?
            """,
            (tampered, public_id),
        )

    with pytest.raises(
        TenantNamespacedArtifactIntegrityError,
        match="integrity",
    ):
        resolver.resolve_checkpoint(
            tenant_id="tenant-alpha",
            namespaced_artifact_id=public_id,
        )


def test_resolution_serialization_preserves_both_ids(
    tmp_path,
):
    service, resolver, _ = build_system(tmp_path)
    execution = execute(service)

    public_id = (
        execution.namespace_bundle.execution
        .namespaced_artifact_id
    )

    serialized = resolver.resolve_execution(
        tenant_id="tenant-alpha",
        namespaced_artifact_id=public_id,
    ).to_dict()

    assert serialized["namespaced_artifact_id"] == (
        public_id
    )
    assert serialized["canonical_artifact_id"] == (
        execution.pipeline_result.execution_id
    )
    assert serialized["resolver_id"] == (
        "tenant-namespaced-scientific-artifact-resolver"
    )


def test_resolution_is_immutable(tmp_path):
    service, resolver, _ = build_system(tmp_path)
    execution = execute(service)

    resolution = resolver.resolve_checkpoint(
        tenant_id="tenant-alpha",
        namespaced_artifact_id=(
            execution.namespace_bundle.checkpoint
            .namespaced_artifact_id
        ),
    )

    with pytest.raises(FrozenInstanceError):
        resolution.tenant_id = "tenant-beta"
