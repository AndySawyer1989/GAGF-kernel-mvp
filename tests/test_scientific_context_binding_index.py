import sqlite3

import pytest

from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
)
from backend.app.gagf.scientific_calculation_contract import (
    EVIDENCE_CONFIDENCE_CONTRACT,
    CalculationAuthority,
)
from backend.app.gagf.scientific_context_binding_index import (
    SCIENTIFIC_CONTEXT_BINDING_INDEX_ID,
    SCIENTIFIC_CONTEXT_BINDING_INDEX_VERSION,
    DuplicateScientificArtifactBindingError,
    ScientificContextBindingArtifactIndex,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificContextBindingLedger,
    ScientificExecutionContext,
    ScientificExecutionContextBindingBuilder,
)
from backend.app.gagf.scientific_pipeline_execution_journal import (
    ScientificPipelineRecoveryCoordinator,
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


def create_binding(
    tmp_path,
    *,
    tenant_id="tenant-alpha",
    request_id="request-1",
):
    tmp_path.mkdir(parents=True, exist_ok=True)

    coordinator = ScientificPipelineRecoveryCoordinator(
        authority_database_path=tmp_path / "authority.db",
        audit_database_path=tmp_path / "audit.db",
        checkpoint_database_path=tmp_path / "checkpoint.db",
        journal_database_path=tmp_path / "journal.db",
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

    return result, binding


def test_index_has_stable_identity():
    assert SCIENTIFIC_CONTEXT_BINDING_INDEX_ID == (
        "scientific-context-binding-artifact-index"
    )
    assert SCIENTIFIC_CONTEXT_BINDING_INDEX_VERSION == (
        "0.1.0"
    )


def test_index_finds_authority_receipt_for_tenant(
    tmp_path,
):
    database_path = tmp_path / "bindings.db"
    result, binding = create_binding(
        tmp_path / "source"
    )
    ScientificContextBindingLedger(
        database_path
    ).append(binding)

    index = ScientificContextBindingArtifactIndex(
        database_path
    )

    record = index.find_for_tenant(
        tenant_id="tenant-alpha",
        artifact_type="authority_receipt",
        artifact_id=(
            result.pipeline_result.authority_receipt_hash
        ),
    )

    assert record is not None
    assert record.binding == binding


def test_index_does_not_return_cross_tenant_record(
    tmp_path,
):
    database_path = tmp_path / "bindings.db"
    result, binding = create_binding(
        tmp_path / "source"
    )
    ScientificContextBindingLedger(
        database_path
    ).append(binding)

    index = ScientificContextBindingArtifactIndex(
        database_path
    )

    record = index.find_for_tenant(
        tenant_id="tenant-beta",
        artifact_type="authority_receipt",
        artifact_id=(
            result.pipeline_result.authority_receipt_hash
        ),
    )

    assert record is None


@pytest.mark.parametrize(
    ("artifact_type", "artifact_attribute"),
    [
        ("authority_receipt", "authority_receipt_hash"),
        ("checkpoint", "checkpoint_hash"),
        ("execution", "execution_id"),
        ("context_binding", "binding_hash"),
    ],
)
def test_index_resolves_each_artifact_type(
    tmp_path,
    artifact_type,
    artifact_attribute,
):
    database_path = tmp_path / "bindings.db"
    result, binding = create_binding(
        tmp_path / artifact_type
    )
    ScientificContextBindingLedger(
        database_path
    ).append(binding)

    if artifact_attribute == "execution_id":
        artifact_id = result.execution_id
    else:
        artifact_id = getattr(
            binding,
            artifact_attribute,
        )

    index = ScientificContextBindingArtifactIndex(
        database_path
    )

    record = index.find_for_tenant(
        tenant_id="tenant-alpha",
        artifact_type=artifact_type,
        artifact_id=artifact_id,
    )

    assert record is not None
    assert record.binding.binding_hash == (
        binding.binding_hash
    )


def test_index_reports_artifact_owner(tmp_path):
    database_path = tmp_path / "bindings.db"
    result, binding = create_binding(
        tmp_path / "source"
    )
    ScientificContextBindingLedger(
        database_path
    ).append(binding)

    owner = ScientificContextBindingArtifactIndex(
        database_path
    ).find_owner(
        artifact_type="checkpoint",
        artifact_id=(
            result.pipeline_result.checkpoint_hash
        ),
    )

    assert owner is not None
    assert owner.tenant_id == "tenant-alpha"
    assert owner.binding_hash == binding.binding_hash
    assert owner.execution_id == result.execution_id


def test_unknown_artifact_has_no_owner(tmp_path):
    index = ScientificContextBindingArtifactIndex(
        tmp_path / "bindings.db"
    )

    owner = index.find_owner(
        artifact_type="checkpoint",
        artifact_id="0" * 64,
    )

    assert owner is None


def test_belongs_to_tenant_returns_boolean(tmp_path):
    database_path = tmp_path / "bindings.db"
    result, binding = create_binding(
        tmp_path / "source"
    )
    ScientificContextBindingLedger(
        database_path
    ).append(binding)

    index = ScientificContextBindingArtifactIndex(
        database_path
    )

    assert index.belongs_to_tenant(
        tenant_id="tenant-alpha",
        artifact_type="execution",
        artifact_id=result.execution_id,
    ) is True

    assert index.belongs_to_tenant(
        tenant_id="tenant-beta",
        artifact_type="execution",
        artifact_id=result.execution_id,
    ) is False


def test_duplicate_artifact_ownership_is_detected(
    tmp_path,
):
    database_path = tmp_path / "bindings.db"
    _, binding = create_binding(
        tmp_path / "source"
    )

    ledger = ScientificContextBindingLedger(
        database_path
    )
    ledger.append(binding)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO scientific_execution_context_bindings (
                binding_hash,
                context_hash,
                tenant_id,
                actor_id,
                credential_id,
                session_id,
                role_id,
                policy_scope,
                request_id,
                correlation_id,
                execution_id,
                execution_receipt_hash,
                authority_receipt_hash,
                audit_receipt_hash,
                checkpoint_hash,
                binding_json
            )
            SELECT
                ?,
                context_hash,
                ?,
                actor_id,
                credential_id,
                session_id,
                role_id,
                policy_scope,
                ?,
                correlation_id,
                execution_id,
                execution_receipt_hash,
                authority_receipt_hash,
                audit_receipt_hash,
                checkpoint_hash,
                binding_json
            FROM scientific_execution_context_bindings
            WHERE binding_hash = ?
            """,
            (
                "f" * 64,
                "tenant-beta",
                "request-beta",
                binding.binding_hash,
            ),
        )

    index = ScientificContextBindingArtifactIndex(
        database_path
    )

    with pytest.raises(
        DuplicateScientificArtifactBindingError,
        match="multiple",
    ):
        index.find_owner(
            artifact_type="authority_receipt",
            artifact_id=binding.authority_receipt_hash,
        )


def test_required_indexes_are_created(tmp_path):
    database_path = tmp_path / "bindings.db"
    ScientificContextBindingArtifactIndex(
        database_path
    )

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'index'
            """
        ).fetchall()

    names = {
        row[0]
        for row in rows
    }

    assert (
        "idx_context_bindings_tenant_authority_receipt"
        in names
    )
    assert "idx_context_bindings_tenant_checkpoint" in names
    assert "idx_context_bindings_tenant_execution" in names
    assert "idx_context_bindings_tenant_binding" in names
