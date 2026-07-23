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
    ScientificContextBindingLedger,
    ScientificExecutionContext,
    ScientificExecutionContextBindingBuilder,
)
from backend.app.gagf.scientific_pipeline_execution_journal import (
    ScientificPipelineRecoveryCoordinator,
)
from backend.app.gagf.tenant_scientific_artifact_access import (
    TENANT_ARTIFACT_ACCESS_SERVICE_ID,
    TENANT_ARTIFACT_ACCESS_SERVICE_VERSION,
    TenantScientificArtifactAccessDeniedError,
    TenantScientificArtifactAccessService,
    TenantScientificArtifactNotFoundError,
    TenantScientificArtifactUnboundError,
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


def build_system(
    tmp_path,
    *,
    tenant_id="tenant-alpha",
    request_id="request-1",
):
    tmp_path.mkdir(parents=True, exist_ok=True)

    authority_database = tmp_path / "authority.db"
    audit_database = tmp_path / "audit.db"
    checkpoint_database = tmp_path / "checkpoint.db"
    journal_database = tmp_path / "journal.db"
    binding_database = tmp_path / "bindings.db"

    coordinator = ScientificPipelineRecoveryCoordinator(
        authority_database_path=authority_database,
        audit_database_path=audit_database,
        checkpoint_database_path=checkpoint_database,
        journal_database_path=journal_database,
    )

    result = coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )

    context = ScientificExecutionContext(
        tenant_id=tenant_id,
        actor_id="actor-1",
        credential_id="credential-1",
        session_id="session-1",
        role_id="scientific-reviewer",
        policy_scope="scientific-authority:evaluate",
        request_id=request_id,
        correlation_id="correlation-1",
    )

    binding = ScientificExecutionContextBindingBuilder().build(
        context=context,
        result=result,
    )

    binding_ledger = ScientificContextBindingLedger(
        binding_database
    )
    binding_record = binding_ledger.append(binding)

    service = TenantScientificArtifactAccessService(
        authority_database_path=authority_database,
        checkpoint_database_path=checkpoint_database,
        journal_database_path=journal_database,
        context_binding_database_path=binding_database,
    )

    return service, result, binding_record


def test_service_has_stable_identity():
    assert TENANT_ARTIFACT_ACCESS_SERVICE_ID == (
        "tenant-scientific-artifact-access-service"
    )
    assert TENANT_ARTIFACT_ACCESS_SERVICE_VERSION == "0.2.0"


def test_tenant_can_access_bound_authority_receipt(
    tmp_path,
):
    service, result, binding_record = build_system(
        tmp_path
    )

    access = service.get_authority_receipt(
        tenant_id="tenant-alpha",
        receipt_hash=(
            result.pipeline_result.authority_receipt_hash
        ),
    )

    assert access.tenant_id == "tenant-alpha"
    assert access.artifact_type == "authority_receipt"
    assert access.binding_hash == (
        binding_record.binding.binding_hash
    )
    assert access.artifact["receipt"]["receipt_hash"] == (
        result.pipeline_result.authority_receipt_hash
    )


def test_other_tenant_cannot_access_authority_receipt(
    tmp_path,
):
    service, result, _ = build_system(tmp_path)

    with pytest.raises(
        TenantScientificArtifactAccessDeniedError,
        match="Cross-tenant",
    ):
        service.get_authority_receipt(
            tenant_id="tenant-beta",
            receipt_hash=(
                result.pipeline_result
                .authority_receipt_hash
            ),
        )


def test_tenant_can_access_bound_checkpoint(tmp_path):
    service, result, binding_record = build_system(
        tmp_path
    )

    access = service.get_checkpoint(
        tenant_id="tenant-alpha",
        checkpoint_hash=(
            result.pipeline_result.checkpoint_hash
        ),
    )

    assert access.artifact_type == "checkpoint"
    assert access.binding_hash == (
        binding_record.binding.binding_hash
    )
    assert access.artifact["checkpoint"][
        "checkpoint_hash"
    ] == result.pipeline_result.checkpoint_hash


def test_other_tenant_cannot_access_checkpoint(tmp_path):
    service, result, _ = build_system(tmp_path)

    with pytest.raises(
        TenantScientificArtifactAccessDeniedError,
        match="Cross-tenant",
    ):
        service.get_checkpoint(
            tenant_id="tenant-beta",
            checkpoint_hash=(
                result.pipeline_result.checkpoint_hash
            ),
        )


def test_tenant_can_access_bound_execution(tmp_path):
    service, result, binding_record = build_system(
        tmp_path
    )

    access = service.get_execution(
        tenant_id="tenant-alpha",
        execution_id=result.execution_id,
    )

    assert access.execution_id == result.execution_id
    assert access.binding_hash == (
        binding_record.binding.binding_hash
    )
    assert access.execution["state"] == "COMPLETED"
    assert access.transitions[0]["state"] == "STARTED"
    assert access.transitions[-1]["state"] == "COMPLETED"


def test_other_tenant_cannot_access_execution(tmp_path):
    service, result, _ = build_system(tmp_path)

    with pytest.raises(
        TenantScientificArtifactAccessDeniedError,
        match="Cross-tenant",
    ):
        service.get_execution(
            tenant_id="tenant-beta",
            execution_id=result.execution_id,
        )


def test_tenant_can_access_its_context_binding(
    tmp_path,
):
    service, _, binding_record = build_system(tmp_path)

    access = service.get_context_binding(
        tenant_id="tenant-alpha",
        binding_hash=(
            binding_record.binding.binding_hash
        ),
    )

    assert access.artifact_type == "context_binding"
    assert access.artifact["binding"]["context"][
        "tenant_id"
    ] == "tenant-alpha"


def test_other_tenant_cannot_access_context_binding(
    tmp_path,
):
    service, _, binding_record = build_system(tmp_path)

    with pytest.raises(
        TenantScientificArtifactAccessDeniedError,
        match="Cross-tenant",
    ):
        service.get_context_binding(
            tenant_id="tenant-beta",
            binding_hash=(
                binding_record.binding.binding_hash
            ),
        )


def test_unknown_authority_receipt_returns_not_found(
    tmp_path,
):
    service, _, _ = build_system(tmp_path)

    with pytest.raises(
        TenantScientificArtifactNotFoundError,
        match="Authority receipt",
    ):
        service.get_authority_receipt(
            tenant_id="tenant-alpha",
            receipt_hash="0" * 64,
        )


def test_unknown_checkpoint_returns_not_found(tmp_path):
    service, _, _ = build_system(tmp_path)

    with pytest.raises(
        TenantScientificArtifactNotFoundError,
        match="checkpoint",
    ):
        service.get_checkpoint(
            tenant_id="tenant-alpha",
            checkpoint_hash="0" * 64,
        )


def test_existing_but_unbound_artifact_is_denied(
    tmp_path,
):
    service, result, binding_record = build_system(
        tmp_path
    )

    with service.binding_ledger._connect() as connection:
        connection.execute(
            """
            DELETE FROM scientific_execution_context_bindings
            WHERE binding_hash = ?
            """,
            (
                binding_record.binding.binding_hash,
            ),
        )

    with pytest.raises(
        TenantScientificArtifactUnboundError,
        match="not bound",
    ):
        service.get_authority_receipt(
            tenant_id="tenant-alpha",
            receipt_hash=(
                result.pipeline_result
                .authority_receipt_hash
            ),
        )


def test_tenant_binding_listing_is_isolated(tmp_path):
    alpha_service, _, alpha_binding = build_system(
        tmp_path / "alpha",
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    _, _, beta_binding = build_system(
        tmp_path / "beta",
        tenant_id="tenant-beta",
        request_id="request-beta",
    )

    alpha_service.binding_ledger.append(
        beta_binding.binding
    )

    alpha_records = alpha_service.list_tenant_bindings(
        tenant_id="tenant-alpha"
    )
    beta_records = alpha_service.list_tenant_bindings(
        tenant_id="tenant-beta"
    )

    assert len(alpha_records) == 1
    assert len(beta_records) == 1
    assert alpha_records[0].tenant_id == "tenant-alpha"
    assert beta_records[0].tenant_id == "tenant-beta"


def test_access_result_is_immutable(tmp_path):
    service, result, _ = build_system(tmp_path)

    access = service.get_authority_receipt(
        tenant_id="tenant-alpha",
        receipt_hash=(
            result.pipeline_result.authority_receipt_hash
        ),
    )

    with pytest.raises(FrozenInstanceError):
        access.tenant_id = "tenant-beta"


def test_access_serialization_preserves_binding_proof(
    tmp_path,
):
    service, result, binding_record = build_system(
        tmp_path
    )

    access = service.get_checkpoint(
        tenant_id="tenant-alpha",
        checkpoint_hash=(
            result.pipeline_result.checkpoint_hash
        ),
    )
    serialized = access.to_dict()

    assert serialized["service_id"] == (
        "tenant-scientific-artifact-access-service"
    )
    assert serialized["tenant_id"] == "tenant-alpha"
    assert serialized["binding_hash"] == (
        binding_record.binding.binding_hash
    )

