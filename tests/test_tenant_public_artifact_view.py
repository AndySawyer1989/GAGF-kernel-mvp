from dataclasses import FrozenInstanceError, replace

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
    TenantNamespacedArtifactResolver,
)
from backend.app.gagf.tenant_namespaced_execution import (
    TenantNamespacedExecutionPaths,
    TenantNamespacedScientificExecutionService,
)
from backend.app.gagf.tenant_public_artifact_view import (
    TENANT_PUBLIC_ARTIFACT_VIEW_ID,
    TENANT_PUBLIC_ARTIFACT_VIEW_SCHEMA_VERSION,
    TENANT_PUBLIC_ARTIFACT_VIEW_VERSION,
    TenantPublicArtifactViewBuilder,
)


def complete_evidence():
    return AuthorityEscalationEvidence(
        deterministic_replay_verified=True,
        canonical_input_binding_verified=True,
        calculation_version_frozen=True,
        regression_suite_passed=True,
        validation_report_present=True,
        constitutional_approval_present=True,
    )


def build_system(tmp_path):
    paths = TenantNamespacedExecutionPaths(
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

    execution_service = (
        TenantNamespacedScientificExecutionService(
            paths=paths
        )
    )

    resolver = TenantNamespacedArtifactResolver(
        namespace_database_path=(
            paths.namespace_database_path
        ),
        authority_database_path=(
            paths.authority_database_path
        ),
        checkpoint_database_path=(
            paths.checkpoint_database_path
        ),
        journal_database_path=(
            paths.journal_database_path
        ),
        context_binding_database_path=(
            paths.context_binding_database_path
        ),
    )

    result = execution_service.execute(
        context=ScientificExecutionContext(
            tenant_id="tenant-alpha",
            actor_id="actor-1",
            credential_id="credential-1",
            session_id="session-1",
            role_id="scientific-reviewer",
            policy_scope="scientific-authority:evaluate",
            request_id="request-alpha",
            correlation_id="correlation-1",
        ),
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    return resolver, result


def collect_keys(value):
    keys = set()

    if isinstance(value, dict):
        keys.update(value.keys())

        for child in value.values():
            keys.update(collect_keys(child))

    elif isinstance(value, list):
        for child in value:
            keys.update(collect_keys(child))

    return keys


def collect_strings(value):
    strings = set()

    if isinstance(value, str):
        strings.add(value)

    elif isinstance(value, dict):
        for child in value.values():
            strings.update(collect_strings(child))

    elif isinstance(value, list):
        for child in value:
            strings.update(collect_strings(child))

    return strings


def test_public_artifact_view_has_stable_identity():
    assert TENANT_PUBLIC_ARTIFACT_VIEW_ID == (
        "tenant-public-scientific-artifact-view"
    )
    assert TENANT_PUBLIC_ARTIFACT_VIEW_VERSION == "0.1.0"
    assert TENANT_PUBLIC_ARTIFACT_VIEW_SCHEMA_VERSION == (
        "1.0.0"
    )


@pytest.mark.parametrize(
    ("artifact_type", "bundle_field"),
    [
        ("authority_receipt", "authority_receipt"),
        ("checkpoint", "checkpoint"),
        ("execution", "execution"),
        ("context_binding", "context_binding"),
    ],
)
def test_public_view_projects_each_artifact_type(
    tmp_path,
    artifact_type,
    bundle_field,
):
    resolver, result = build_system(tmp_path)

    namespace = getattr(
        result.namespace_bundle,
        bundle_field,
    )

    resolution = resolver.resolve(
        tenant_id="tenant-alpha",
        artifact_type=artifact_type,
        namespaced_artifact_id=(
            namespace.namespaced_artifact_id
        ),
    )

    view = TenantPublicArtifactViewBuilder().build(
        resolution=resolution
    )

    assert view.tenant_id == "tenant-alpha"
    assert view.artifact_type == artifact_type
    assert view.public_artifact_id == (
        namespace.namespaced_artifact_id
    )
    assert view.verify() is True


def test_public_view_excludes_canonical_identifier(
    tmp_path,
):
    resolver, result = build_system(tmp_path)

    resolution = resolver.resolve_checkpoint(
        tenant_id="tenant-alpha",
        namespaced_artifact_id=(
            result.namespace_bundle.checkpoint
            .namespaced_artifact_id
        ),
    )

    serialized = TenantPublicArtifactViewBuilder().build(
        resolution=resolution
    ).to_dict()

    strings = collect_strings(serialized)

    assert resolution.canonical_artifact_id not in strings


def test_public_view_removes_hash_fields(tmp_path):
    resolver, result = build_system(tmp_path)

    resolution = resolver.resolve_execution(
        tenant_id="tenant-alpha",
        namespaced_artifact_id=(
            result.namespace_bundle.execution
            .namespaced_artifact_id
        ),
    )

    serialized = TenantPublicArtifactViewBuilder().build(
        resolution=resolution
    ).to_dict()

    nested_keys = collect_keys(
        serialized["artifact"]
    )

    assert all(
        not key.endswith("_hash")
        for key in nested_keys
    )
    assert "binding_hash" not in nested_keys
    assert "canonical_artifact_id" not in nested_keys


def test_public_id_is_preserved(tmp_path):
    resolver, result = build_system(tmp_path)

    public_id = (
        result.namespace_bundle.authority_receipt
        .namespaced_artifact_id
    )

    resolution = resolver.resolve_authority_receipt(
        tenant_id="tenant-alpha",
        namespaced_artifact_id=public_id,
    )

    view = TenantPublicArtifactViewBuilder().build(
        resolution=resolution
    )

    assert view.public_artifact_id == public_id


def test_view_hash_detects_tampering(tmp_path):
    resolver, result = build_system(tmp_path)

    resolution = resolver.resolve_checkpoint(
        tenant_id="tenant-alpha",
        namespaced_artifact_id=(
            result.namespace_bundle.checkpoint
            .namespaced_artifact_id
        ),
    )

    view = TenantPublicArtifactViewBuilder().build(
        resolution=resolution
    )

    tampered = replace(
        view,
        tenant_id="tenant-beta",
    )

    assert view.verify() is True
    assert tampered.verify() is False


def test_public_artifact_view_is_immutable(tmp_path):
    resolver, result = build_system(tmp_path)

    resolution = resolver.resolve_execution(
        tenant_id="tenant-alpha",
        namespaced_artifact_id=(
            result.namespace_bundle.execution
            .namespaced_artifact_id
        ),
    )

    view = TenantPublicArtifactViewBuilder().build(
        resolution=resolution
    )

    with pytest.raises(FrozenInstanceError):
        view.tenant_id = "tenant-beta"
