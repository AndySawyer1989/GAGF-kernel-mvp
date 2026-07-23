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
from backend.app.gagf.tenant_artifact_collision_guard import (
    TENANT_ARTIFACT_COLLISION_GUARD_ID,
    TENANT_ARTIFACT_COLLISION_GUARD_VERSION,
    CrossTenantArtifactCollisionError,
    TenantArtifactCollisionGuard,
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


def build_result(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)

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


def build_binding(
    *,
    result,
    tenant_id,
    request_id,
):
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

    return ScientificExecutionContextBindingBuilder().build(
        context=context,
        result=result,
    )


def test_collision_guard_has_stable_identity():
    assert TENANT_ARTIFACT_COLLISION_GUARD_ID == (
        "tenant-scientific-artifact-collision-guard"
    )
    assert TENANT_ARTIFACT_COLLISION_GUARD_VERSION == "0.1.0"


def test_empty_ledger_allows_binding(tmp_path):
    result = build_result(tmp_path / "source")
    binding = build_binding(
        result=result,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )

    decision = TenantArtifactCollisionGuard(
        tmp_path / "bindings.db"
    ).evaluate(binding)

    assert decision.allowed is True
    assert decision.collisions == ()


def test_same_tenant_replay_is_allowed(tmp_path):
    result = build_result(tmp_path / "source")
    binding = build_binding(
        result=result,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    database_path = tmp_path / "bindings.db"

    ScientificContextBindingLedger(
        database_path
    ).append(binding)

    decision = TenantArtifactCollisionGuard(
        database_path
    ).evaluate(binding)

    assert decision.allowed is True
    assert decision.collisions == ()


def test_other_tenant_same_execution_is_denied(tmp_path):
    result = build_result(tmp_path / "source")
    database_path = tmp_path / "bindings.db"

    alpha_binding = build_binding(
        result=result,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    beta_binding = build_binding(
        result=result,
        tenant_id="tenant-beta",
        request_id="request-beta",
    )

    ScientificContextBindingLedger(
        database_path
    ).append(alpha_binding)

    decision = TenantArtifactCollisionGuard(
        database_path
    ).evaluate(beta_binding)

    assert decision.allowed is False
    assert decision.tenant_id == "tenant-beta"

    collision_types = {
        collision.artifact_type
        for collision in decision.collisions
    }

    assert "authority_receipt" in collision_types
    assert "checkpoint" in collision_types
    assert "execution" in collision_types


def test_tenant_specific_binding_hash_does_not_collide(
    tmp_path,
):
    result = build_result(tmp_path / "source")

    alpha_binding = build_binding(
        result=result,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    beta_binding = build_binding(
        result=result,
        tenant_id="tenant-beta",
        request_id="request-beta",
    )

    assert alpha_binding.binding_hash != beta_binding.binding_hash


def test_collision_identifies_owning_tenant(tmp_path):
    result = build_result(tmp_path / "source")
    database_path = tmp_path / "bindings.db"

    alpha_binding = build_binding(
        result=result,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    beta_binding = build_binding(
        result=result,
        tenant_id="tenant-beta",
        request_id="request-beta",
    )

    ScientificContextBindingLedger(
        database_path
    ).append(alpha_binding)

    decision = TenantArtifactCollisionGuard(
        database_path
    ).evaluate(beta_binding)

    collision = next(
        item
        for item in decision.collisions
        if item.artifact_type == "execution"
    )

    assert collision.requested_tenant_id == "tenant-beta"
    assert collision.owning_tenant_id == "tenant-alpha"
    assert collision.owning_binding_hash == (
        alpha_binding.binding_hash
    )
    assert collision.owning_execution_id == result.execution_id


def test_enforce_returns_allowed_decision(tmp_path):
    result = build_result(tmp_path / "source")
    binding = build_binding(
        result=result,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )

    decision = TenantArtifactCollisionGuard(
        tmp_path / "bindings.db"
    ).enforce(binding)

    assert decision.allowed is True


def test_enforce_raises_for_cross_tenant_collision(
    tmp_path,
):
    result = build_result(tmp_path / "source")
    database_path = tmp_path / "bindings.db"

    alpha_binding = build_binding(
        result=result,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    beta_binding = build_binding(
        result=result,
        tenant_id="tenant-beta",
        request_id="request-beta",
    )

    ScientificContextBindingLedger(
        database_path
    ).append(alpha_binding)

    guard = TenantArtifactCollisionGuard(database_path)

    with pytest.raises(
        CrossTenantArtifactCollisionError,
        match="Cross-tenant deterministic artifact collision",
    ):
        guard.enforce(beta_binding)


def test_denied_binding_is_not_persisted(tmp_path):
    result = build_result(tmp_path / "source")
    database_path = tmp_path / "bindings.db"

    ledger = ScientificContextBindingLedger(
        database_path
    )

    alpha_binding = build_binding(
        result=result,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    beta_binding = build_binding(
        result=result,
        tenant_id="tenant-beta",
        request_id="request-beta",
    )

    ledger.append(alpha_binding)

    with pytest.raises(CrossTenantArtifactCollisionError):
        TenantArtifactCollisionGuard(
            database_path
        ).enforce(beta_binding)

    assert ledger.count() == 1
    assert ledger.count(tenant_id="tenant-alpha") == 1
    assert ledger.count(tenant_id="tenant-beta") == 0


def test_collision_decision_serializes_proof(tmp_path):
    result = build_result(tmp_path / "source")
    database_path = tmp_path / "bindings.db"

    alpha_binding = build_binding(
        result=result,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )
    beta_binding = build_binding(
        result=result,
        tenant_id="tenant-beta",
        request_id="request-beta",
    )

    ScientificContextBindingLedger(
        database_path
    ).append(alpha_binding)

    decision = TenantArtifactCollisionGuard(
        database_path
    ).evaluate(beta_binding)

    serialized = decision.to_dict()

    assert serialized["allowed"] is False
    assert serialized["tenant_id"] == "tenant-beta"
    assert serialized["guard_id"] == (
        "tenant-scientific-artifact-collision-guard"
    )
    assert len(serialized["collisions"]) >= 3


def test_allowed_decision_serializes_empty_collision_list(
    tmp_path,
):
    result = build_result(tmp_path / "source")
    binding = build_binding(
        result=result,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )

    serialized = TenantArtifactCollisionGuard(
        tmp_path / "bindings.db"
    ).evaluate(binding).to_dict()

    assert serialized["allowed"] is True
    assert serialized["collisions"] == []


def test_collision_decision_is_immutable(tmp_path):
    result = build_result(tmp_path / "source")
    binding = build_binding(
        result=result,
        tenant_id="tenant-alpha",
        request_id="request-alpha",
    )

    decision = TenantArtifactCollisionGuard(
        tmp_path / "bindings.db"
    ).evaluate(binding)

    with pytest.raises(FrozenInstanceError):
        decision.allowed = False
