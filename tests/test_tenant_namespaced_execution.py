from dataclasses import FrozenInstanceError

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
from backend.app.gagf.tenant_namespaced_execution import (
    TENANT_NAMESPACED_EXECUTION_SERVICE_ID,
    TENANT_NAMESPACED_EXECUTION_SERVICE_VERSION,
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


def build_context(
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


def build_service(tmp_path):
    return TenantNamespacedScientificExecutionService(
        paths=TenantNamespacedExecutionPaths(
            authority_database_path=(
                tmp_path / "authority.db"
            ),
            audit_database_path=tmp_path / "audit.db",
            checkpoint_database_path=(
                tmp_path / "checkpoint.db"
            ),
            journal_database_path=tmp_path / "journal.db",
            context_binding_database_path=(
                tmp_path / "bindings.db"
            ),
            namespace_database_path=(
                tmp_path / "namespaces.db"
            ),
        )
    )


def execute(
    service,
    *,
    tenant_id="tenant-alpha",
    request_id="request-alpha",
):
    return service.execute(
        context=build_context(
            tenant_id=tenant_id,
            request_id=request_id,
        ),
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )


def test_service_has_stable_identity():
    assert TENANT_NAMESPACED_EXECUTION_SERVICE_ID == (
        "tenant-namespaced-scientific-execution-service"
    )
    assert TENANT_NAMESPACED_EXECUTION_SERVICE_VERSION == (
        "0.1.0"
    )


def test_execution_persists_context_binding(tmp_path):
    service = build_service(tmp_path)

    result = execute(service)

    assert result.tenant_id == "tenant-alpha"
    assert result.context_binding.sequence_number == 1
    assert result.context_binding.binding.context[
        "tenant_id"
    ] == "tenant-alpha"
    assert service.context_binding_ledger.count() == 1


def test_execution_persists_six_namespace_records(
    tmp_path,
):
    service = build_service(tmp_path)

    result = execute(service)

    assert len(result.namespace_records) == 6
    assert service.namespace_ledger.count() == 6
    assert service.namespace_ledger.count(
        tenant_id="tenant-alpha"
    ) == 6


def test_namespace_bundle_binds_pipeline_artifacts(
    tmp_path,
):
    service = build_service(tmp_path)

    result = execute(service)
    bundle = result.namespace_bundle
    pipeline = result.pipeline_result

    assert bundle.execution.canonical_artifact_id == (
        pipeline.execution_id
    )
    assert (
        bundle.execution_receipt.canonical_artifact_id
        == pipeline.execution_receipt.receipt_hash
    )
    assert (
        bundle.authority_receipt.canonical_artifact_id
        == pipeline.pipeline_result.authority_receipt_hash
    )
    assert (
        bundle.audit_receipt.canonical_artifact_id
        == pipeline.pipeline_result.audit_receipt_hash
    )
    assert bundle.checkpoint.canonical_artifact_id == (
        pipeline.pipeline_result.checkpoint_hash
    )
    assert (
        bundle.context_binding.canonical_artifact_id
        == result.context_binding.binding.binding_hash
    )


def test_same_tenant_replay_is_idempotent(tmp_path):
    service = build_service(tmp_path)

    first = execute(service)
    second = execute(service)

    assert first.pipeline_result.execution_id == (
        second.pipeline_result.execution_id
    )
    assert first.context_binding.sequence_number == 1
    assert second.context_binding.sequence_number == 1
    assert first.namespace_bundle == second.namespace_bundle
    assert service.context_binding_ledger.count() == 1
    assert service.namespace_ledger.count() == 6


def test_identical_cross_tenant_execution_is_allowed(
    tmp_path,
):
    service = build_service(tmp_path)

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

    assert alpha.pipeline_result.execution_id == (
        beta.pipeline_result.execution_id
    )
    assert (
        alpha.pipeline_result.pipeline_result
        .authority_receipt_hash
        == beta.pipeline_result.pipeline_result
        .authority_receipt_hash
    )

    assert service.context_binding_ledger.count() == 2
    assert service.namespace_ledger.count() == 12


def test_cross_tenant_public_execution_ids_are_distinct(
    tmp_path,
):
    service = build_service(tmp_path)

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
        alpha.namespace_bundle.execution
        .namespaced_artifact_id
        != beta.namespace_bundle.execution
        .namespaced_artifact_id
    )


@pytest.mark.parametrize(
    "bundle_field",
    [
        "execution",
        "execution_receipt",
        "authority_receipt",
        "audit_receipt",
        "checkpoint",
        "context_binding",
    ],
)
def test_every_public_artifact_id_is_tenant_isolated(
    tmp_path,
    bundle_field,
):
    service = build_service(tmp_path)

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

    alpha_namespace = getattr(
        alpha.namespace_bundle,
        bundle_field,
    )
    beta_namespace = getattr(
        beta.namespace_bundle,
        bundle_field,
    )

    assert (
        alpha_namespace.canonical_artifact_id
        == beta_namespace.canonical_artifact_id
    ) or bundle_field == "context_binding"

    assert (
        alpha_namespace.namespaced_artifact_id
        != beta_namespace.namespaced_artifact_id
    )


def test_cross_tenant_namespace_lookup_isolated(tmp_path):
    service = build_service(tmp_path)

    alpha = execute(
        service,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    execute(
        service,
        tenant_id="tenant-beta",
        request_id="request-beta",
    )

    alpha_public_checkpoint = (
        alpha.namespace_bundle.checkpoint
        .namespaced_artifact_id
    )

    alpha_lookup = (
        service.namespace_ledger.get_by_namespaced_id(
            tenant_id="tenant-alpha",
            artifact_type="checkpoint",
            namespaced_artifact_id=(
                alpha_public_checkpoint
            ),
        )
    )
    beta_lookup = (
        service.namespace_ledger.get_by_namespaced_id(
            tenant_id="tenant-beta",
            artifact_type="checkpoint",
            namespaced_artifact_id=(
                alpha_public_checkpoint
            ),
        )
    )

    assert alpha_lookup is not None
    assert beta_lookup is None


def test_result_serialization_contains_public_ids(
    tmp_path,
):
    service = build_service(tmp_path)

    result = execute(service)
    serialized = result.to_dict()

    assert serialized["service_id"] == (
        "tenant-namespaced-scientific-execution-service"
    )
    assert serialized["tenant_id"] == "tenant-alpha"
    assert len(
        serialized["namespace_bundle"]["execution"][
            "namespaced_artifact_id"
        ]
    ) == 64
    assert len(serialized["namespace_records"]) == 6


def test_result_is_immutable(tmp_path):
    service = build_service(tmp_path)

    result = execute(service)

    with pytest.raises(FrozenInstanceError):
        result.tenant_id = "tenant-beta"
