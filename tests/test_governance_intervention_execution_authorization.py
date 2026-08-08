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
from backend.app.gagf.governance_intervention_execution_authorization import (
    GOVERNANCE_INTERVENTION_EXECUTION_AUTHORIZATION_ID,
    GOVERNANCE_INTERVENTION_EXECUTION_AUTHORIZATION_VERSION,
    GovernanceInterventionExecutionAuthorizationGate,
    GovernanceInterventionExecutionDeniedError,
    InvalidGovernanceInterventionExecutionBindingError,
)
from backend.app.gagf.governance_intervention_execution_binding import (
    GovernanceInterventionExecutionBindingBuilder,
)
from backend.app.gagf.scientific_authorization import (
    ScientificAuthorityAction,
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
        title="Remove governed approval bottleneck",
        horizon=RoadmapHorizon.DAY_30,
        sequence=1,
        owner_role="Operations Lead",
        measurable_outcome=(
            "Reduce governed approval delay."
        ),
        value_score=0.91,
        implementation_burden=0.35,
        dependency_ids=(),
        status=RoadmapItemStatus.APPROVED,
    )


def _roadmap(
    *,
    item: RoadmapItem | None = None,
) -> AssessmentRoadmap:
    canonical_item = item or _item()

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
                items=(canonical_item,),
            ),
        ),
        total_items=1,
        roadmap_hash="roadmap-hash-001",
    )


def _context(
    *,
    tenant_id: str = "tenant-a",
    role_id: str = "scientific-approver",
    request_id: str = "request-001",
    correlation_id: str = "correlation-001",
) -> ScientificExecutionContext:
    return ScientificExecutionContext(
        tenant_id=tenant_id,
        actor_id="actor-001",
        credential_id="credential-001",
        session_id="session-001",
        role_id=role_id,
        policy_scope="scientific-authority:*",
        request_id=request_id,
        correlation_id=correlation_id,
    )


def _trust(
    *,
    credential_verified: bool = True,
    session_verified: bool = True,
    device_trusted: bool = True,
    step_up_verified: bool = True,
    tenant_membership_verified: bool = True,
) -> ScientificTrustSignals:
    return ScientificTrustSignals(
        credential_verified=credential_verified,
        session_verified=session_verified,
        device_trusted=device_trusted,
        step_up_verified=step_up_verified,
        tenant_membership_verified=tenant_membership_verified,
    )


def _binding(
    *,
    context: ScientificExecutionContext | None = None,
):
    execution_context = context or _context()

    return (
        GovernanceInterventionExecutionBindingBuilder()
        .build(
            roadmap=_roadmap(),
            item=_item(),
            context=execution_context,
        )
    )


def test_intervention_execution_has_dedicated_authorization_action():
    assert (
        ScientificAuthorityAction
        .AUTHORIZE_INTERVENTION_EXECUTION
        .value
        == "AUTHORIZE_INTERVENTION_EXECUTION"
    )


def test_approver_can_authorize_verified_intervention_binding():
    context = _context()

    authorization = (
        GovernanceInterventionExecutionAuthorizationGate()
        .authorize(
            binding=_binding(context=context),
            context=context,
            trust_signals=_trust(),
            constitutional_approval_submitted=True,
        )
    )

    assert authorization.allowed is True
    assert (
        authorization.authorization_id
        == GOVERNANCE_INTERVENTION_EXECUTION_AUTHORIZATION_ID
    )
    assert (
        authorization.authorization_version
        == GOVERNANCE_INTERVENTION_EXECUTION_AUTHORIZATION_VERSION
    )
    assert authorization.binding_hash == (
        _binding(context=context).binding_hash
    )
    assert (
        authorization.execution_context_hash
        == context.context_hash
    )
    assert (
        authorization.decision.action
        == ScientificAuthorityAction
        .AUTHORIZE_INTERVENTION_EXECUTION
    )
    assert authorization.authorization_receipt.verify() is True


def test_reviewer_cannot_authorize_intervention_execution():
    context = _context(
        role_id="scientific-reviewer",
    )

    with pytest.raises(
        GovernanceInterventionExecutionDeniedError
    ) as exc_info:
        (
            GovernanceInterventionExecutionAuthorizationGate()
            .authorize(
                binding=_binding(context=context),
                context=context,
                trust_signals=_trust(),
                constitutional_approval_submitted=True,
            )
        )

    assert exc_info.value.decision.allowed is False
    assert exc_info.value.receipt.verify() is True


def test_authorization_requires_step_up():
    context = _context()

    with pytest.raises(
        GovernanceInterventionExecutionDeniedError
    ) as exc_info:
        (
            GovernanceInterventionExecutionAuthorizationGate()
            .authorize(
                binding=_binding(context=context),
                context=context,
                trust_signals=_trust(
                    step_up_verified=False,
                ),
                constitutional_approval_submitted=True,
            )
        )

    assert exc_info.value.decision.allowed is False


def test_authorization_requires_constitutional_approval():
    context = _context()

    with pytest.raises(
        GovernanceInterventionExecutionDeniedError
    ) as exc_info:
        (
            GovernanceInterventionExecutionAuthorizationGate()
            .authorize(
                binding=_binding(context=context),
                context=context,
                trust_signals=_trust(),
                constitutional_approval_submitted=False,
            )
        )

    assert exc_info.value.decision.allowed is False


@pytest.mark.parametrize(
    "trust_override",
    (
        {"credential_verified": False},
        {"session_verified": False},
        {"device_trusted": False},
        {"tenant_membership_verified": False},
    ),
)
def test_zero_trust_failure_denies_intervention_authorization(
    trust_override,
):
    context = _context()

    with pytest.raises(
        GovernanceInterventionExecutionDeniedError
    ) as exc_info:
        (
            GovernanceInterventionExecutionAuthorizationGate()
            .authorize(
                binding=_binding(context=context),
                context=context,
                trust_signals=_trust(
                    **trust_override,
                ),
                constitutional_approval_submitted=True,
            )
        )

    assert exc_info.value.decision.allowed is False


def test_tampered_binding_is_rejected_before_policy_authorization():
    context = _context()

    tampered = replace(
        _binding(context=context),
        owner_role="Unauthorized Owner",
    )

    assert tampered.verify() is False

    with pytest.raises(
        InvalidGovernanceInterventionExecutionBindingError
    ):
        (
            GovernanceInterventionExecutionAuthorizationGate()
            .authorize(
                binding=tampered,
                context=context,
                trust_signals=_trust(),
                constitutional_approval_submitted=True,
            )
        )


def test_different_execution_context_is_rejected():
    bound_context = _context()

    different_context = _context(
        request_id="request-002",
    )

    with pytest.raises(
        InvalidGovernanceInterventionExecutionBindingError
    ):
        (
            GovernanceInterventionExecutionAuthorizationGate()
            .authorize(
                binding=_binding(
                    context=bound_context,
                ),
                context=different_context,
                trust_signals=_trust(),
                constitutional_approval_submitted=True,
            )
        )


def test_cross_tenant_context_is_rejected_before_policy():
    bound_context = _context()

    foreign_context = _context(
        tenant_id="tenant-b",
    )

    with pytest.raises(
        InvalidGovernanceInterventionExecutionBindingError
    ):
        (
            GovernanceInterventionExecutionAuthorizationGate()
            .authorize(
                binding=_binding(
                    context=bound_context,
                ),
                context=foreign_context,
                trust_signals=_trust(),
                constitutional_approval_submitted=True,
            )
        )


def test_authorization_is_deterministic_for_identical_inputs():
    context = _context()
    binding = _binding(context=context)
    gate = GovernanceInterventionExecutionAuthorizationGate()

    first = gate.authorize(
        binding=binding,
        context=context,
        trust_signals=_trust(),
        constitutional_approval_submitted=True,
    )

    second = gate.authorize(
        binding=binding,
        context=context,
        trust_signals=_trust(),
        constitutional_approval_submitted=True,
    )

    assert first.to_dict() == second.to_dict()
    assert (
        first.authorization_receipt.receipt_hash
        == second.authorization_receipt.receipt_hash
    )


def test_serialization_preserves_binding_and_authorization_lineage():
    context = _context()
    binding = _binding(context=context)

    authorization = (
        GovernanceInterventionExecutionAuthorizationGate()
        .authorize(
            binding=binding,
            context=context,
            trust_signals=_trust(),
            constitutional_approval_submitted=True,
        )
    )

    serialized = authorization.to_dict()

    assert serialized["binding_hash"] == binding.binding_hash
    assert (
        serialized["execution_context_hash"]
        == context.context_hash
    )
    assert serialized["decision"]["allowed"] is True
    assert (
        serialized["decision"]["action"]
        == "AUTHORIZE_INTERVENTION_EXECUTION"
    )
    assert (
        serialized["authorization_receipt"][
            "receipt_hash"
        ]
        == authorization.authorization_receipt.receipt_hash
    )


def test_authorization_result_is_immutable():
    context = _context()

    authorization = (
        GovernanceInterventionExecutionAuthorizationGate()
        .authorize(
            binding=_binding(context=context),
            context=context,
            trust_signals=_trust(),
            constitutional_approval_submitted=True,
        )
    )

    with pytest.raises(FrozenInstanceError):
        authorization.binding_hash = "tampered"
