from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.tenant_artifact_namespace import (
    TENANT_ARTIFACT_NAMESPACE_ID,
    TENANT_ARTIFACT_NAMESPACE_LEDGER_ID,
    TENANT_ARTIFACT_NAMESPACE_LEDGER_VERSION,
    TENANT_ARTIFACT_NAMESPACE_SCHEMA_VERSION,
    TENANT_ARTIFACT_NAMESPACE_VERSION,
    InvalidTenantArtifactNamespaceRecordError,
    TenantArtifactNamespaceBundleBuilder,
    TenantArtifactNamespaceDeriver,
    TenantArtifactNamespaceError,
    TenantArtifactNamespaceLedger,
)


def artifact_id(character="a"):
    return character * 64


def build_bundle(
    *,
    tenant_id="tenant-alpha",
):
    return TenantArtifactNamespaceBundleBuilder().build(
        tenant_id=tenant_id,
        execution_id=artifact_id("1"),
        execution_receipt_hash=artifact_id("2"),
        authority_receipt_hash=artifact_id("3"),
        audit_receipt_hash=artifact_id("4"),
        checkpoint_hash=artifact_id("5"),
        context_binding_hash=artifact_id("6"),
    )


def test_namespace_components_have_stable_identity():
    assert TENANT_ARTIFACT_NAMESPACE_ID == (
        "tenant-scientific-artifact-namespace"
    )
    assert TENANT_ARTIFACT_NAMESPACE_VERSION == "0.1.0"
    assert TENANT_ARTIFACT_NAMESPACE_SCHEMA_VERSION == (
        "1.0.0"
    )
    assert TENANT_ARTIFACT_NAMESPACE_LEDGER_ID == (
        "tenant-scientific-artifact-namespace-ledger"
    )
    assert TENANT_ARTIFACT_NAMESPACE_LEDGER_VERSION == (
        "0.1.0"
    )


def test_namespace_derivation_is_deterministic():
    deriver = TenantArtifactNamespaceDeriver()

    first = deriver.derive(
        tenant_id="tenant-alpha",
        artifact_type="checkpoint",
        canonical_artifact_id=artifact_id("a"),
    )
    second = deriver.derive(
        tenant_id="tenant-alpha",
        artifact_type="checkpoint",
        canonical_artifact_id=artifact_id("a"),
    )

    assert first == second
    assert first.namespaced_artifact_id == (
        second.namespaced_artifact_id
    )
    assert first.verify() is True


def test_different_tenants_receive_different_ids():
    deriver = TenantArtifactNamespaceDeriver()

    alpha = deriver.derive(
        tenant_id="tenant-alpha",
        artifact_type="checkpoint",
        canonical_artifact_id=artifact_id("a"),
    )
    beta = deriver.derive(
        tenant_id="tenant-beta",
        artifact_type="checkpoint",
        canonical_artifact_id=artifact_id("a"),
    )

    assert alpha.canonical_artifact_id == (
        beta.canonical_artifact_id
    )
    assert alpha.namespaced_artifact_id != (
        beta.namespaced_artifact_id
    )


def test_different_artifact_types_receive_different_ids():
    deriver = TenantArtifactNamespaceDeriver()

    checkpoint = deriver.derive(
        tenant_id="tenant-alpha",
        artifact_type="checkpoint",
        canonical_artifact_id=artifact_id("a"),
    )
    receipt = deriver.derive(
        tenant_id="tenant-alpha",
        artifact_type="authority_receipt",
        canonical_artifact_id=artifact_id("a"),
    )

    assert checkpoint.namespaced_artifact_id != (
        receipt.namespaced_artifact_id
    )


def test_namespace_normalizes_tenant_whitespace():
    namespace = TenantArtifactNamespaceDeriver().derive(
        tenant_id=" tenant-alpha ",
        artifact_type="execution",
        canonical_artifact_id=artifact_id("a"),
    )

    assert namespace.tenant_id == "tenant-alpha"


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("tenant_id", "   "),
        ("canonical_artifact_id", ""),
    ],
)
def test_empty_namespace_values_are_rejected(
    field_name,
    value,
):
    values = {
        "tenant_id": "tenant-alpha",
        "artifact_type": "checkpoint",
        "canonical_artifact_id": artifact_id("a"),
    }
    values[field_name] = value

    with pytest.raises(
        TenantArtifactNamespaceError,
        match="must not be empty",
    ):
        TenantArtifactNamespaceDeriver().derive(
            **values
        )


def test_tampered_namespace_fails_verification():
    namespace = TenantArtifactNamespaceDeriver().derive(
        tenant_id="tenant-alpha",
        artifact_type="checkpoint",
        canonical_artifact_id=artifact_id("a"),
    )

    tampered = replace(
        namespace,
        tenant_id="tenant-beta",
    )

    assert tampered.verify() is False


def test_namespace_is_immutable():
    namespace = TenantArtifactNamespaceDeriver().derive(
        tenant_id="tenant-alpha",
        artifact_type="checkpoint",
        canonical_artifact_id=artifact_id("a"),
    )

    with pytest.raises(FrozenInstanceError):
        namespace.tenant_id = "tenant-beta"


def test_bundle_contains_all_artifact_types():
    bundle = build_bundle()

    assert bundle.verify() is True
    assert bundle.execution.artifact_type == "execution"
    assert bundle.execution_receipt.artifact_type == (
        "execution_receipt"
    )
    assert bundle.authority_receipt.artifact_type == (
        "authority_receipt"
    )
    assert bundle.audit_receipt.artifact_type == (
        "audit_receipt"
    )
    assert bundle.checkpoint.artifact_type == "checkpoint"
    assert bundle.context_binding.artifact_type == (
        "context_binding"
    )


def test_same_canonical_bundle_isolated_across_tenants():
    alpha = build_bundle(tenant_id="tenant-alpha")
    beta = build_bundle(tenant_id="tenant-beta")

    assert (
        alpha.execution.canonical_artifact_id
        == beta.execution.canonical_artifact_id
    )
    assert (
        alpha.execution.namespaced_artifact_id
        != beta.execution.namespaced_artifact_id
    )
    assert (
        alpha.checkpoint.namespaced_artifact_id
        != beta.checkpoint.namespaced_artifact_id
    )


def test_ledger_persists_namespace(tmp_path):
    ledger = TenantArtifactNamespaceLedger(
        tmp_path / "namespace.db"
    )
    namespace = build_bundle().checkpoint

    record = ledger.append(namespace)

    assert record.sequence_number == 1
    assert record.namespace == namespace
    assert ledger.count() == 1


def test_identical_append_is_idempotent(tmp_path):
    ledger = TenantArtifactNamespaceLedger(
        tmp_path / "namespace.db"
    )
    namespace = build_bundle().checkpoint

    first = ledger.append(namespace)
    second = ledger.append(namespace)

    assert first.sequence_number == 1
    assert second.sequence_number == 1
    assert ledger.count() == 1


def test_invalid_namespace_is_rejected(tmp_path):
    ledger = TenantArtifactNamespaceLedger(
        tmp_path / "namespace.db"
    )
    namespace = build_bundle().checkpoint

    tampered = replace(
        namespace,
        namespaced_artifact_id="0" * 64,
    )

    with pytest.raises(
        InvalidTenantArtifactNamespaceRecordError,
        match="failed hash verification",
    ):
        ledger.append(tampered)

    assert ledger.count() == 0


def test_bundle_append_persists_six_records(tmp_path):
    ledger = TenantArtifactNamespaceLedger(
        tmp_path / "namespace.db"
    )

    records = ledger.append_bundle(build_bundle())

    assert len(records) == 6
    assert ledger.count() == 6
    assert all(
        record.sequence_number == index
        for index, record in enumerate(
            records,
            start=1,
        )
    )


def test_namespaced_lookup_is_tenant_scoped(tmp_path):
    ledger = TenantArtifactNamespaceLedger(
        tmp_path / "namespace.db"
    )
    alpha = build_bundle(tenant_id="tenant-alpha")
    beta = build_bundle(tenant_id="tenant-beta")

    ledger.append_bundle(alpha)
    ledger.append_bundle(beta)

    alpha_record = ledger.get_by_namespaced_id(
        tenant_id="tenant-alpha",
        artifact_type="checkpoint",
        namespaced_artifact_id=(
            alpha.checkpoint.namespaced_artifact_id
        ),
    )
    cross_tenant = ledger.get_by_namespaced_id(
        tenant_id="tenant-beta",
        artifact_type="checkpoint",
        namespaced_artifact_id=(
            alpha.checkpoint.namespaced_artifact_id
        ),
    )

    assert alpha_record is not None
    assert alpha_record.namespace == alpha.checkpoint
    assert cross_tenant is None


def test_canonical_lookup_is_tenant_scoped(tmp_path):
    ledger = TenantArtifactNamespaceLedger(
        tmp_path / "namespace.db"
    )
    alpha = build_bundle(tenant_id="tenant-alpha")
    beta = build_bundle(tenant_id="tenant-beta")

    ledger.append_bundle(alpha)
    ledger.append_bundle(beta)

    alpha_record = ledger.get_by_canonical_id(
        tenant_id="tenant-alpha",
        artifact_type="checkpoint",
        canonical_artifact_id=(
            alpha.checkpoint.canonical_artifact_id
        ),
    )
    beta_record = ledger.get_by_canonical_id(
        tenant_id="tenant-beta",
        artifact_type="checkpoint",
        canonical_artifact_id=(
            beta.checkpoint.canonical_artifact_id
        ),
    )

    assert alpha_record is not None
    assert beta_record is not None
    assert (
        alpha_record.namespace.namespaced_artifact_id
        != beta_record.namespace.namespaced_artifact_id
    )


def test_tenant_listing_is_isolated(tmp_path):
    ledger = TenantArtifactNamespaceLedger(
        tmp_path / "namespace.db"
    )

    ledger.append_bundle(
        build_bundle(tenant_id="tenant-alpha")
    )
    ledger.append_bundle(
        build_bundle(tenant_id="tenant-beta")
    )

    alpha = ledger.list_for_tenant("tenant-alpha")
    beta = ledger.list_for_tenant("tenant-beta")

    assert len(alpha) == 6
    assert len(beta) == 6
    assert all(
        record.namespace.tenant_id == "tenant-alpha"
        for record in alpha
    )
    assert all(
        record.namespace.tenant_id == "tenant-beta"
        for record in beta
    )


def test_ledger_verifies_all_records(tmp_path):
    ledger = TenantArtifactNamespaceLedger(
        tmp_path / "namespace.db"
    )
    ledger.append_bundle(build_bundle())

    assert ledger.verify_all() is True


def test_empty_ledger_verifies_vacuously(tmp_path):
    ledger = TenantArtifactNamespaceLedger(
        tmp_path / "namespace.db"
    )

    assert ledger.verify_all() is True
