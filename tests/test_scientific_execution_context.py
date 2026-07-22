import sqlite3
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
    SCIENTIFIC_CONTEXT_BINDING_LEDGER_ID,
    SCIENTIFIC_CONTEXT_BINDING_LEDGER_VERSION,
    SCIENTIFIC_EXECUTION_CONTEXT_ID,
    SCIENTIFIC_EXECUTION_CONTEXT_SCHEMA_VERSION,
    SCIENTIFIC_EXECUTION_CONTEXT_VERSION,
    InvalidScientificContextBindingError,
    ScientificContextBindingConflictError,
    ScientificContextBindingLedger,
    ScientificExecutionContext,
    ScientificExecutionContextBindingBuilder,
    ScientificExecutionContextError,
)
from backend.app.gagf.scientific_pipeline_execution_journal import (
    ScientificPipelineRecoveryCoordinator,
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
    actor_id="actor-1",
    request_id="request-1",
    correlation_id="correlation-1",
):
    return ScientificExecutionContext(
        tenant_id=tenant_id,
        actor_id=actor_id,
        credential_id="credential-1",
        session_id="session-1",
        role_id="scientific-reviewer",
        policy_scope="scientific-authority:evaluate",
        request_id=request_id,
        correlation_id=correlation_id,
    )


def build_result(tmp_path):
    coordinator = ScientificPipelineRecoveryCoordinator(
        authority_database_path=tmp_path / "authority.db",
        audit_database_path=tmp_path / "audit.db",
        checkpoint_database_path=tmp_path / "checkpoint.db",
        journal_database_path=tmp_path / "journal.db",
    )

    return coordinator.execute(
        contract=EVIDENCE_CONFIDENCE_CONTRACT,
        requested_authority=CalculationAuthority.ADVISORY,
        evidence=complete_evidence(),
    )


def build_binding(tmp_path, **context_kwargs):
    result = build_result(tmp_path)
    context = build_context(**context_kwargs)

    binding = ScientificExecutionContextBindingBuilder().build(
        context=context,
        result=result,
    )

    return context, result, binding


def test_context_components_have_stable_identity():
    assert SCIENTIFIC_EXECUTION_CONTEXT_ID == (
        "scientific-authority-execution-context"
    )
    assert SCIENTIFIC_EXECUTION_CONTEXT_VERSION == "0.1.0"
    assert (
        SCIENTIFIC_EXECUTION_CONTEXT_SCHEMA_VERSION
        == "1.0.0"
    )
    assert SCIENTIFIC_CONTEXT_BINDING_LEDGER_ID == (
        "scientific-authority-context-binding-ledger"
    )
    assert SCIENTIFIC_CONTEXT_BINDING_LEDGER_VERSION == (
        "0.1.0"
    )


def test_context_normalizes_surrounding_whitespace():
    context = ScientificExecutionContext(
        tenant_id=" tenant-alpha ",
        actor_id=" actor-1 ",
        credential_id=" credential-1 ",
        session_id=" session-1 ",
        role_id=" reviewer ",
        policy_scope=" authority:evaluate ",
        request_id=" request-1 ",
        correlation_id=" correlation-1 ",
    )

    assert context.tenant_id == "tenant-alpha"
    assert context.actor_id == "actor-1"
    assert context.request_id == "request-1"


@pytest.mark.parametrize(
    "field_name",
    [
        "tenant_id",
        "actor_id",
        "credential_id",
        "session_id",
        "role_id",
        "policy_scope",
        "request_id",
        "correlation_id",
    ],
)
def test_empty_context_identifiers_are_rejected(
    field_name,
):
    values = {
        "tenant_id": "tenant-alpha",
        "actor_id": "actor-1",
        "credential_id": "credential-1",
        "session_id": "session-1",
        "role_id": "reviewer",
        "policy_scope": "authority:evaluate",
        "request_id": "request-1",
        "correlation_id": "correlation-1",
    }
    values[field_name] = "   "

    with pytest.raises(
        ScientificExecutionContextError,
        match="must not be empty",
    ):
        ScientificExecutionContext(**values)


def test_identical_contexts_have_identical_hashes():
    first = build_context()
    second = build_context()

    assert first == second
    assert first.context_hash == second.context_hash


def test_different_tenants_have_different_context_hashes():
    first = build_context(tenant_id="tenant-alpha")
    second = build_context(tenant_id="tenant-beta")

    assert first.context_hash != second.context_hash


def test_context_hash_is_sha256_hex():
    context = build_context()

    assert len(context.context_hash) == 64
    int(context.context_hash, 16)


def test_binding_binds_complete_execution(tmp_path):
    context, result, binding = build_binding(tmp_path)

    assert binding.context_hash == context.context_hash
    assert binding.execution_id == result.execution_id
    assert binding.execution_receipt_hash == (
        result.execution_receipt.receipt_hash
    )
    assert binding.authority_receipt_hash == (
        result.pipeline_result.authority_receipt_hash
    )
    assert binding.audit_receipt_hash == (
        result.pipeline_result.audit_receipt_hash
    )
    assert binding.checkpoint_hash == (
        result.pipeline_result.checkpoint_hash
    )
    assert binding.verify() is True


def test_binding_is_deterministic(tmp_path):
    context, result, _ = build_binding(tmp_path)
    builder = ScientificExecutionContextBindingBuilder()

    first = builder.build(
        context=context,
        result=result,
    )
    second = builder.build(
        context=context,
        result=result,
    )

    assert first == second
    assert first.binding_hash == second.binding_hash


def test_tampered_context_fails_binding_verification(
    tmp_path,
):
    _, _, binding = build_binding(tmp_path)

    changed_context = dict(binding.context)
    changed_context["tenant_id"] = "tenant-beta"

    tampered = replace(
        binding,
        context=changed_context,
    )

    assert tampered.verify() is False


def test_tampered_execution_hash_fails_verification(
    tmp_path,
):
    _, _, binding = build_binding(tmp_path)

    tampered = replace(
        binding,
        execution_receipt_hash="0" * 64,
    )

    assert tampered.verify() is False


def test_binding_is_immutable(tmp_path):
    _, _, binding = build_binding(tmp_path)

    with pytest.raises(FrozenInstanceError):
        binding.binding_hash = "changed"


def test_binding_ledger_persists_valid_binding(tmp_path):
    _, _, binding = build_binding(
        tmp_path / "source"
    )
    ledger = ScientificContextBindingLedger(
        tmp_path / "bindings.db"
    )

    record = ledger.append(binding)

    assert record.sequence_number == 1
    assert record.binding == binding
    assert ledger.count() == 1


def test_identical_binding_append_is_idempotent(tmp_path):
    _, _, binding = build_binding(
        tmp_path / "source"
    )
    ledger = ScientificContextBindingLedger(
        tmp_path / "bindings.db"
    )

    first = ledger.append(binding)
    second = ledger.append(binding)

    assert first.sequence_number == 1
    assert second.sequence_number == 1
    assert ledger.count() == 1


def test_invalid_binding_is_rejected(tmp_path):
    _, _, binding = build_binding(
        tmp_path / "source"
    )
    ledger = ScientificContextBindingLedger(
        tmp_path / "bindings.db"
    )

    tampered = replace(
        binding,
        binding_hash="0" * 64,
    )

    with pytest.raises(
        InvalidScientificContextBindingError,
        match="failed hash verification",
    ):
        ledger.append(tampered)

    assert ledger.count() == 0


def test_binding_can_be_retrieved_by_hash(tmp_path):
    _, _, binding = build_binding(
        tmp_path / "source"
    )
    ledger = ScientificContextBindingLedger(
        tmp_path / "bindings.db"
    )
    ledger.append(binding)

    restored = ledger.get_by_hash(
        binding.binding_hash
    )

    assert restored is not None
    assert restored.sequence_number == 1
    assert restored.binding == binding
    assert restored.binding.verify() is True


def test_binding_can_be_retrieved_by_execution_id(
    tmp_path,
):
    _, result, binding = build_binding(
        tmp_path / "source"
    )
    ledger = ScientificContextBindingLedger(
        tmp_path / "bindings.db"
    )
    ledger.append(binding)

    restored = ledger.get_by_execution_id(
        result.execution_id
    )

    assert restored is not None
    assert restored.binding.binding_hash == (
        binding.binding_hash
    )


def test_tenant_scoped_listing_prevents_mixed_results(
    tmp_path,
):
    ledger = ScientificContextBindingLedger(
        tmp_path / "bindings.db"
    )

    _, _, alpha_binding = build_binding(
        tmp_path / "alpha-source",
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    _, _, beta_binding = build_binding(
        tmp_path / "beta-source",
        tenant_id="tenant-beta",
        request_id="request-beta",
    )

    ledger.append(alpha_binding)
    ledger.append(beta_binding)

    alpha_records = ledger.list_for_tenant(
        "tenant-alpha"
    )
    beta_records = ledger.list_for_tenant(
        "tenant-beta"
    )

    assert len(alpha_records) == 1
    assert len(beta_records) == 1
    assert (
        alpha_records[0].binding.context["tenant_id"]
        == "tenant-alpha"
    )
    assert (
        beta_records[0].binding.context["tenant_id"]
        == "tenant-beta"
    )


def test_same_request_id_is_allowed_across_tenants(
    tmp_path,
):
    ledger = ScientificContextBindingLedger(
        tmp_path / "bindings.db"
    )

    _, _, alpha_binding = build_binding(
        tmp_path / "alpha-source",
        tenant_id="tenant-alpha",
        request_id="shared-request",
    )
    _, _, beta_binding = build_binding(
        tmp_path / "beta-source",
        tenant_id="tenant-beta",
        request_id="shared-request",
    )

    ledger.append(alpha_binding)
    ledger.append(beta_binding)

    assert ledger.count() == 2
    assert ledger.count(tenant_id="tenant-alpha") == 1
    assert ledger.count(tenant_id="tenant-beta") == 1


def test_tenant_request_rebinding_is_rejected(tmp_path):
    ledger = ScientificContextBindingLedger(
        tmp_path / "bindings.db"
    )

    _, _, first_binding = build_binding(
        tmp_path / "first-source",
        tenant_id="tenant-alpha",
        actor_id="actor-1",
        request_id="request-1",
    )
    _, _, second_binding = build_binding(
        tmp_path / "second-source",
        tenant_id="tenant-alpha",
        actor_id="actor-2",
        request_id="request-1",
    )

    ledger.append(first_binding)

    with pytest.raises(
        ScientificContextBindingConflictError,
        match="already bound",
    ):
        ledger.append(second_binding)


def test_database_content_conflict_is_detected(tmp_path):
    _, _, binding = build_binding(
        tmp_path / "source"
    )
    database_path = tmp_path / "bindings.db"
    ledger = ScientificContextBindingLedger(
        database_path
    )
    ledger.append(binding)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE scientific_execution_context_bindings
            SET binding_json = ?
            WHERE binding_hash = ?
            """,
            (
                '{"tampered":true}',
                binding.binding_hash,
            ),
        )

    with pytest.raises(
        ScientificContextBindingConflictError,
        match="different content",
    ):
        ledger.append(binding)


def test_verify_all_accepts_valid_bindings(tmp_path):
    _, _, binding = build_binding(
        tmp_path / "source"
    )
    ledger = ScientificContextBindingLedger(
        tmp_path / "bindings.db"
    )
    ledger.append(binding)

    assert ledger.verify_all() is True


def test_empty_binding_ledger_verifies_vacuously(
    tmp_path,
):
    ledger = ScientificContextBindingLedger(
        tmp_path / "bindings.db"
    )

    assert ledger.verify_all() is True
