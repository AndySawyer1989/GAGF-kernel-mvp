from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.governance_assessment_intervention_plan import (
    InterventionType,
)
from backend.app.gagf.governance_assessment_roadmap import (
    AssessmentRoadmap,
    RoadmapHorizon,
    RoadmapItem,
    RoadmapItemStatus,
    RoadmapPhase,
)
from backend.app.gagf.governance_intervention_actuation_contract import (
    GOVERNANCE_INTERVENTION_ACTUATION_CONTRACT_ID,
    GOVERNANCE_INTERVENTION_ACTUATION_CONTRACT_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_ACTUATION_CONTRACT_VERSION,
    GovernanceInterventionActuationContractBuilder,
    GovernanceInterventionActuationLineageError,
    InvalidGovernanceInterventionAuthorizationError,
    UnboundedGovernanceInterventionError,
)
from backend.app.gagf.governance_intervention_execution_authorization import (
    GovernanceInterventionExecutionAuthorizationGate,
)
from backend.app.gagf.governance_intervention_execution_binding import (
    GovernanceInterventionExecutionBindingBuilder,
)
from backend.app.gagf.scientific_authorization import (
    ScientificTrustSignals,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificExecutionContext,
)


def _item() -> RoadmapItem:
    return RoadmapItem(
        roadmap_item_id="roadmap-item-001",
        intervention_id="intervention-001",
        intervention_type=InterventionType.REMOVE_BLOCKER,
        title="Remove recurring deployment blocker",
        horizon=RoadmapHorizon.DAY_30,
        sequence=1,
        owner_role="Operations Lead",
        measurable_outcome=(
            "Reduce governed deployment delay."
        ),
        value_score=0.91,
        implementation_burden=0.35,
        dependency_ids=(),
        status=RoadmapItemStatus.APPROVED,
    )


def _roadmap() -> AssessmentRoadmap:
    item = _item()

    return AssessmentRoadmap(
        tenant_id="tenant-a",
        client_id="client-a",
        engagement_id="engagement-a",
        assessment_id="assessment-a",
        intervention_plan_hash="plan-hash-001",
        phases=(
            RoadmapPhase(
                horizon=RoadmapHorizon.DAY_30,
                objective="Remove immediate governed friction.",
                items=(item,),
            ),
        ),
        total_items=1,
        roadmap_hash="roadmap-hash-001",
    )


def _context() -> ScientificExecutionContext:
    return ScientificExecutionContext(
        tenant_id="tenant-a",
        actor_id="actor-001",
        credential_id="credential-001",
        session_id="session-001",
        role_id="scientific-approver",
        policy_scope="scientific-authority:*",
        request_id="request-001",
        correlation_id="correlation-001",
    )


def _trust() -> ScientificTrustSignals:
    return ScientificTrustSignals(
        credential_verified=True,
        session_verified=True,
        device_trusted=True,
        step_up_verified=True,
        tenant_membership_verified=True,
    )


def _binding_and_authorization():
    context = _context()

    binding = (
        GovernanceInterventionExecutionBindingBuilder()
        .build(
            roadmap=_roadmap(),
            item=_item(),
            context=context,
        )
    )

    authorization = (
        GovernanceInterventionExecutionAuthorizationGate()
        .authorize(
            binding=binding,
            context=context,
            trust_signals=_trust(),
            constitutional_approval_submitted=True,
        )
    )

    return binding, authorization


def _build_contract():
    binding, authorization = _binding_and_authorization()

    return (
        GovernanceInterventionActuationContractBuilder()
        .build(
            binding=binding,
            authorization=authorization,
            requested_effect=(
                "Reduce approval delay for governed deployments."
            ),
            effect_boundary=(
                "Only the deployment approval workflow for tenant-a."
            ),
            preconditions=(
                "Current deployment workflow snapshot is verified.",
                "Rollback owner is available.",
            ),
            abort_criteria=(
                "Approval error rate exceeds baseline.",
                "Required audit evidence becomes unavailable.",
            ),
            rollback_strategy=(
                "Restore the prior deployment approval configuration."
            ),
            max_attempts=1,
            timeout_seconds=300,
            verification_requirements=(
                "Verify approval latency after intervention.",
                "Verify audit evidence continuity.",
            ),
        )
    )


def test_builds_bounded_actuation_contract_from_authorized_lineage():
    binding, authorization = _binding_and_authorization()

    contract = (
        GovernanceInterventionActuationContractBuilder()
        .build(
            binding=binding,
            authorization=authorization,
            requested_effect="Reduce deployment approval delay.",
            effect_boundary="Tenant-a deployment approval workflow only.",
            preconditions=("Baseline state verified.",),
            abort_criteria=("Error rate exceeds threshold.",),
            rollback_strategy="Restore prior approval workflow.",
            max_attempts=1,
            timeout_seconds=120,
            verification_requirements=(
                "Verify approval latency.",
            ),
        )
    )

    assert contract.contract_id == (
        GOVERNANCE_INTERVENTION_ACTUATION_CONTRACT_ID
    )
    assert contract.contract_version == (
        GOVERNANCE_INTERVENTION_ACTUATION_CONTRACT_VERSION
    )
    assert contract.schema_version == (
        GOVERNANCE_INTERVENTION_ACTUATION_CONTRACT_SCHEMA_VERSION
    )
    assert contract.tenant_id == binding.tenant_id
    assert contract.binding_hash == binding.binding_hash
    assert contract.authorization_receipt_hash == (
        authorization.authorization_receipt.receipt_hash
    )
    assert contract.execution_context_hash == (
        authorization.execution_context_hash
    )
    assert contract.intervention_id == binding.intervention_id
    assert contract.intervention_type == binding.intervention_type
    assert contract.verify() is True


def test_identical_inputs_produce_identical_contract_hash():
    first = _build_contract()
    second = _build_contract()

    assert first.contract_hash == second.contract_hash
    assert first.to_dict() == second.to_dict()


def test_contract_is_immutable():
    contract = _build_contract()

    with pytest.raises(FrozenInstanceError):
        contract.timeout_seconds = 999


def test_tampering_breaks_contract_verification():
    contract = _build_contract()

    tampered = replace(
        contract,
        timeout_seconds=999,
    )

    assert tampered.verify() is False


@pytest.mark.parametrize(
    ("field_name", "override"),
    (
        ("requested_effect", ""),
        ("effect_boundary", ""),
        ("rollback_strategy", ""),
    ),
)
def test_required_scalar_bounds_cannot_be_blank(
    field_name,
    override,
):
    binding, authorization = _binding_and_authorization()

    kwargs = {
        "binding": binding,
        "authorization": authorization,
        "requested_effect": "Reduce deployment delay.",
        "effect_boundary": "Tenant-a workflow only.",
        "preconditions": ("Baseline verified.",),
        "abort_criteria": ("Error threshold exceeded.",),
        "rollback_strategy": "Restore prior configuration.",
        "max_attempts": 1,
        "timeout_seconds": 120,
        "verification_requirements": (
            "Verify post-change latency.",
        ),
    }

    kwargs[field_name] = override

    with pytest.raises(
        UnboundedGovernanceInterventionError
    ):
        (
            GovernanceInterventionActuationContractBuilder()
            .build(**kwargs)
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "preconditions",
        "abort_criteria",
        "verification_requirements",
    ),
)
def test_required_bound_collections_cannot_be_empty(
    field_name,
):
    binding, authorization = _binding_and_authorization()

    kwargs = {
        "binding": binding,
        "authorization": authorization,
        "requested_effect": "Reduce deployment delay.",
        "effect_boundary": "Tenant-a workflow only.",
        "preconditions": ("Baseline verified.",),
        "abort_criteria": ("Error threshold exceeded.",),
        "rollback_strategy": "Restore prior configuration.",
        "max_attempts": 1,
        "timeout_seconds": 120,
        "verification_requirements": (
            "Verify post-change latency.",
        ),
    }

    kwargs[field_name] = ()

    with pytest.raises(
        UnboundedGovernanceInterventionError
    ):
        (
            GovernanceInterventionActuationContractBuilder()
            .build(**kwargs)
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "preconditions",
        "abort_criteria",
        "verification_requirements",
    ),
)
def test_required_bound_collections_reject_blank_entries(
    field_name,
):
    binding, authorization = _binding_and_authorization()

    kwargs = {
        "binding": binding,
        "authorization": authorization,
        "requested_effect": "Reduce deployment delay.",
        "effect_boundary": "Tenant-a workflow only.",
        "preconditions": ("Baseline verified.",),
        "abort_criteria": ("Error threshold exceeded.",),
        "rollback_strategy": "Restore prior configuration.",
        "max_attempts": 1,
        "timeout_seconds": 120,
        "verification_requirements": (
            "Verify post-change latency.",
        ),
    }

    kwargs[field_name] = ("valid", "   ")

    with pytest.raises(
        UnboundedGovernanceInterventionError
    ):
        (
            GovernanceInterventionActuationContractBuilder()
            .build(**kwargs)
        )


@pytest.mark.parametrize(
    ("max_attempts", "timeout_seconds"),
    (
        (0, 120),
        (-1, 120),
        (1, 0),
        (1, -1),
    ),
)
def test_execution_limits_must_be_positive(
    max_attempts,
    timeout_seconds,
):
    binding, authorization = _binding_and_authorization()

    with pytest.raises(
        UnboundedGovernanceInterventionError
    ):
        (
            GovernanceInterventionActuationContractBuilder()
            .build(
                binding=binding,
                authorization=authorization,
                requested_effect="Reduce deployment delay.",
                effect_boundary="Tenant-a workflow only.",
                preconditions=("Baseline verified.",),
                abort_criteria=("Error threshold exceeded.",),
                rollback_strategy="Restore prior configuration.",
                max_attempts=max_attempts,
                timeout_seconds=timeout_seconds,
                verification_requirements=(
                    "Verify post-change latency.",
                ),
            )
        )


def test_tampered_binding_is_rejected():
    binding, authorization = _binding_and_authorization()

    tampered_binding = replace(
        binding,
        intervention_id="tampered-intervention",
    )

    with pytest.raises(
        GovernanceInterventionActuationLineageError
    ):
        (
            GovernanceInterventionActuationContractBuilder()
            .build(
                binding=tampered_binding,
                authorization=authorization,
                requested_effect="Reduce deployment delay.",
                effect_boundary="Tenant-a workflow only.",
                preconditions=("Baseline verified.",),
                abort_criteria=("Error threshold exceeded.",),
                rollback_strategy="Restore prior configuration.",
                max_attempts=1,
                timeout_seconds=120,
                verification_requirements=(
                    "Verify post-change latency.",
                ),
            )
        )


def test_authorization_for_different_binding_is_rejected():
    binding, authorization = _binding_and_authorization()

    mismatched_authorization = replace(
        authorization,
        binding_hash="different-binding-hash",
    )

    with pytest.raises(
        GovernanceInterventionActuationLineageError
    ):
        (
            GovernanceInterventionActuationContractBuilder()
            .build(
                binding=binding,
                authorization=mismatched_authorization,
                requested_effect="Reduce deployment delay.",
                effect_boundary="Tenant-a workflow only.",
                preconditions=("Baseline verified.",),
                abort_criteria=("Error threshold exceeded.",),
                rollback_strategy="Restore prior configuration.",
                max_attempts=1,
                timeout_seconds=120,
                verification_requirements=(
                    "Verify post-change latency.",
                ),
            )
        )


def test_denied_authorization_cannot_support_actuation():
    binding, authorization = _binding_and_authorization()

    denied = replace(
        authorization,
        decision=replace(
            authorization.decision,
            allowed=False,
        ),
    )

    with pytest.raises(
        InvalidGovernanceInterventionAuthorizationError
    ):
        (
            GovernanceInterventionActuationContractBuilder()
            .build(
                binding=binding,
                authorization=denied,
                requested_effect="Reduce deployment delay.",
                effect_boundary="Tenant-a workflow only.",
                preconditions=("Baseline verified.",),
                abort_criteria=("Error threshold exceeded.",),
                rollback_strategy="Restore prior configuration.",
                max_attempts=1,
                timeout_seconds=120,
                verification_requirements=(
                    "Verify post-change latency.",
                ),
            )
        )


def test_tampered_authorization_receipt_is_rejected():
    binding, authorization = _binding_and_authorization()

    tampered_receipt = replace(
        authorization.authorization_receipt,
        receipt_hash="0" * 64,
    )

    tampered_authorization = replace(
        authorization,
        authorization_receipt=tampered_receipt,
    )

    with pytest.raises(
        InvalidGovernanceInterventionAuthorizationError
    ):
        (
            GovernanceInterventionActuationContractBuilder()
            .build(
                binding=binding,
                authorization=tampered_authorization,
                requested_effect="Reduce deployment delay.",
                effect_boundary="Tenant-a workflow only.",
                preconditions=("Baseline verified.",),
                abort_criteria=("Error threshold exceeded.",),
                rollback_strategy="Restore prior configuration.",
                max_attempts=1,
                timeout_seconds=120,
                verification_requirements=(
                    "Verify post-change latency.",
                ),
            )
        )


def test_serialization_preserves_bounded_actuation_lineage():
    contract = _build_contract()

    serialized = contract.to_dict()

    assert serialized["tenant_id"] == "tenant-a"
    assert serialized["binding_hash"] == contract.binding_hash
    assert (
        serialized["authorization_receipt_hash"]
        == contract.authorization_receipt_hash
    )
    assert (
        serialized["execution_context_hash"]
        == contract.execution_context_hash
    )
    assert serialized["requested_effect"] == (
        contract.requested_effect
    )
    assert serialized["effect_boundary"] == (
        contract.effect_boundary
    )
    assert serialized["preconditions"] == list(
        contract.preconditions
    )
    assert serialized["abort_criteria"] == list(
        contract.abort_criteria
    )
    assert serialized["rollback_strategy"] == (
        contract.rollback_strategy
    )
    assert serialized["verification_requirements"] == list(
        contract.verification_requirements
    )
    assert serialized["contract_hash"] == (
        contract.contract_hash
    )


def test_contract_exposes_no_execution_method():
    contract = _build_contract()
    builder = GovernanceInterventionActuationContractBuilder()

    assert not hasattr(contract, "execute")
    assert not hasattr(builder, "execute")
    assert not hasattr(contract, "dispatch")
    assert not hasattr(builder, "dispatch")
