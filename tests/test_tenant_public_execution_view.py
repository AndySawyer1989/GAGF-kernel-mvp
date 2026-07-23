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
from backend.app.gagf.tenant_namespaced_execution import (
    TenantNamespacedExecutionPaths,
    TenantNamespacedScientificExecutionService,
)
from backend.app.gagf.tenant_public_execution_view import (
    TENANT_PUBLIC_EXECUTION_VIEW_ID,
    TENANT_PUBLIC_EXECUTION_VIEW_SCHEMA_VERSION,
    TENANT_PUBLIC_EXECUTION_VIEW_VERSION,
    TenantPublicExecutionViewBuilder,
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
        context=ScientificExecutionContext(
            tenant_id=tenant_id,
            actor_id="actor-1",
            credential_id="credential-1",
            session_id="session-1",
            role_id="scientific-reviewer",
            policy_scope="scientific-authority:evaluate",
            request_id=request_id,
            correlation_id="correlation-1",
        ),
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )


def collect_string_values(value):
    values = []

    if isinstance(value, str):
        values.append(value)

    elif isinstance(value, dict):
        for item in value.values():
            values.extend(collect_string_values(item))

    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(collect_string_values(item))

    return values


def test_public_view_has_stable_identity():
    assert TENANT_PUBLIC_EXECUTION_VIEW_ID == (
        "tenant-public-scientific-execution-view"
    )
    assert TENANT_PUBLIC_EXECUTION_VIEW_VERSION == "0.1.0"
    assert TENANT_PUBLIC_EXECUTION_VIEW_SCHEMA_VERSION == (
        "1.0.0"
    )


def test_public_view_contains_all_namespaced_ids(tmp_path):
    result = execute(build_service(tmp_path))

    view = TenantPublicExecutionViewBuilder().build(
        result=result
    )

    assert view.public_artifacts.execution_id == (
        result.namespace_bundle.execution
        .namespaced_artifact_id
    )
    assert view.public_artifacts.execution_receipt_id == (
        result.namespace_bundle.execution_receipt
        .namespaced_artifact_id
    )
    assert view.public_artifacts.authority_receipt_id == (
        result.namespace_bundle.authority_receipt
        .namespaced_artifact_id
    )
    assert view.public_artifacts.audit_receipt_id == (
        result.namespace_bundle.audit_receipt
        .namespaced_artifact_id
    )
    assert view.public_artifacts.checkpoint_id == (
        result.namespace_bundle.checkpoint
        .namespaced_artifact_id
    )
    assert view.public_artifacts.context_binding_id == (
        result.namespace_bundle.context_binding
        .namespaced_artifact_id
    )


def test_public_view_excludes_canonical_identifiers(
    tmp_path,
):
    result = execute(build_service(tmp_path))

    serialized = TenantPublicExecutionViewBuilder().build(
        result=result
    ).to_dict()

    visible_strings = set(
        collect_string_values(serialized)
    )

    canonical_ids = {
        result.pipeline_result.execution_id,
        (
            result.pipeline_result.execution_receipt
            .receipt_hash
        ),
        (
            result.pipeline_result.pipeline_result
            .authority_receipt_hash
        ),
        (
            result.pipeline_result.pipeline_result
            .audit_receipt_hash
        ),
        (
            result.pipeline_result.pipeline_result
            .checkpoint_hash
        ),
        (
            result.context_binding.binding.binding_hash
        ),
    }

    assert canonical_ids.isdisjoint(visible_strings)


def test_public_view_preserves_operational_status(
    tmp_path,
):
    result = execute(build_service(tmp_path))

    view = TenantPublicExecutionViewBuilder().build(
        result=result
    )

    assert view.resumed is False
    assert view.decision_allowed is True
    assert view.checkpoint_valid is True
    assert view.context_binding_sequence_number == 1


def test_public_view_contains_namespace_persistence_proof(
    tmp_path,
):
    result = execute(build_service(tmp_path))

    view = TenantPublicExecutionViewBuilder().build(
        result=result
    )

    assert view.namespace_sequence_numbers == (
        1,
        2,
        3,
        4,
        5,
        6,
    )


def test_same_tenant_replay_has_same_public_ids(
    tmp_path,
):
    service = build_service(tmp_path)

    first = TenantPublicExecutionViewBuilder().build(
        result=execute(service)
    )
    second = TenantPublicExecutionViewBuilder().build(
        result=execute(service)
    )

    assert first.public_artifacts == (
        second.public_artifacts
    )
    assert first.resumed is False
    assert second.resumed is True


def test_cross_tenant_public_views_are_isolated(
    tmp_path,
):
    service = build_service(tmp_path)

    alpha = TenantPublicExecutionViewBuilder().build(
        result=execute(
            service,
            tenant_id="tenant-alpha",
            request_id="request-alpha",
        )
    )
    beta = TenantPublicExecutionViewBuilder().build(
        result=execute(
            service,
            tenant_id="tenant-beta",
            request_id="request-beta",
        )
    )

    assert alpha.public_artifacts.execution_id != (
        beta.public_artifacts.execution_id
    )
    assert alpha.public_artifacts.checkpoint_id != (
        beta.public_artifacts.checkpoint_id
    )


def test_public_view_hash_verifies(tmp_path):
    result = execute(build_service(tmp_path))

    view = TenantPublicExecutionViewBuilder().build(
        result=result
    )

    assert view.verify() is True
    assert len(view.view_hash) == 64


def test_tampered_public_view_fails_verification(
    tmp_path,
):
    result = execute(build_service(tmp_path))

    view = TenantPublicExecutionViewBuilder().build(
        result=result
    )

    tampered = replace(
        view,
        tenant_id="tenant-beta",
    )

    assert tampered.verify() is False


def test_public_view_is_immutable(tmp_path):
    result = execute(build_service(tmp_path))

    view = TenantPublicExecutionViewBuilder().build(
        result=result
    )

    with pytest.raises(FrozenInstanceError):
        view.tenant_id = "tenant-beta"
