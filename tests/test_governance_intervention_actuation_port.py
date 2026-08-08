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
    GovernanceInterventionActuationContractBuilder,
)
from backend.app.gagf.governance_intervention_actuation_port import (
    GOVERNANCE_INTERVENTION_ACTUATION_PORT_ID,
    GOVERNANCE_INTERVENTION_ACTUATION_PORT_VERSION,
    GovernanceInterventionActuationAcceptance,
    GovernanceInterventionActuationDisposition,
    GovernanceInterventionActuationPort,
    GovernanceInterventionActuationRequestBuilder,
    InvalidGovernanceInterventionActuationContractError,
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


def _contract():
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

    return (
        GovernanceInterventionActuationContractBuilder()
        .build(
            binding=binding,
            authorization=authorization,
            requested_effect="Reduce deployment approval delay.",
            effect_boundary="Tenant-a deployment workflow only.",
            preconditions=("Baseline state verified.",),
            abort_criteria=("Error threshold exceeded.",),
            rollback_strategy="Restore prior approval workflow.",
            max_attempts=1,
            timeout_seconds=120,
            verification_requirements=(
                "Verify approval latency.",
            ),
        )
    )


def test_builds_actuation_request_from_valid_contract():
    contract = _contract()

    request = (
        GovernanceInterventionActuationRequestBuilder()
        .build(
            contract=contract,
            idempotency_key="actuation-001",
        )
    )

    assert request.port_id == (
        GOVERNANCE_INTERVENTION_ACTUATION_PORT_ID
    )
    assert request.port_version == (
        GOVERNANCE_INTERVENTION_ACTUATION_PORT_VERSION
    )
    assert request.tenant_id == contract.tenant_id
    assert request.contract_hash == contract.contract_hash
    assert request.intervention_id == contract.intervention_id
    assert request.intervention_type == (
        contract.intervention_type
    )
    assert request.idempotency_key == "actuation-001"


def test_request_builder_rejects_tampered_contract():
    contract = _contract()

    tampered = replace(
        contract,
        timeout_seconds=999,
    )

    assert tampered.verify() is False

    with pytest.raises(
        InvalidGovernanceInterventionActuationContractError
    ):
        (
            GovernanceInterventionActuationRequestBuilder()
            .build(
                contract=tampered,
                idempotency_key="actuation-001",
            )
        )


@pytest.mark.parametrize(
    "idempotency_key",
    (
        "",
        "   ",
    ),
)
def test_request_requires_idempotency_key(
    idempotency_key,
):
    with pytest.raises(
        InvalidGovernanceInterventionActuationContractError
    ):
        (
            GovernanceInterventionActuationRequestBuilder()
            .build(
                contract=_contract(),
                idempotency_key=idempotency_key,
            )
        )


def test_idempotency_key_is_normalized():
    request = (
        GovernanceInterventionActuationRequestBuilder()
        .build(
            contract=_contract(),
            idempotency_key="  actuation-001  ",
        )
    )

    assert request.idempotency_key == "actuation-001"


def test_identical_contract_and_key_produce_identical_request():
    contract = _contract()
    builder = GovernanceInterventionActuationRequestBuilder()

    first = builder.build(
        contract=contract,
        idempotency_key="actuation-001",
    )

    second = builder.build(
        contract=contract,
        idempotency_key="actuation-001",
    )

    assert first == second
    assert first.to_dict() == second.to_dict()


def test_request_is_immutable():
    request = (
        GovernanceInterventionActuationRequestBuilder()
        .build(
            contract=_contract(),
            idempotency_key="actuation-001",
        )
    )

    with pytest.raises(FrozenInstanceError):
        request.contract_hash = "tampered"


def test_request_serialization_preserves_contract_lineage():
    contract = _contract()

    request = (
        GovernanceInterventionActuationRequestBuilder()
        .build(
            contract=contract,
            idempotency_key="actuation-001",
        )
    )

    serialized = request.to_dict()

    assert serialized == {
        "port_id": GOVERNANCE_INTERVENTION_ACTUATION_PORT_ID,
        "port_version": (
            GOVERNANCE_INTERVENTION_ACTUATION_PORT_VERSION
        ),
        "tenant_id": contract.tenant_id,
        "contract_hash": contract.contract_hash,
        "intervention_id": contract.intervention_id,
        "intervention_type": contract.intervention_type,
        "idempotency_key": "actuation-001",
    }


def test_acceptance_serializes_explicit_disposition():
    acceptance = GovernanceInterventionActuationAcceptance(
        disposition=(
            GovernanceInterventionActuationDisposition.ACCEPTED
        ),
        tenant_id="tenant-a",
        contract_hash="contract-hash-001",
        idempotency_key="actuation-001",
        adapter_id="test-adapter",
        adapter_version="0.1.0",
        accepted=True,
    )

    assert acceptance.to_dict() == {
        "disposition": "ACCEPTED",
        "tenant_id": "tenant-a",
        "contract_hash": "contract-hash-001",
        "idempotency_key": "actuation-001",
        "adapter_id": "test-adapter",
        "adapter_version": "0.1.0",
        "accepted": True,
    }


def test_acceptance_is_immutable():
    acceptance = GovernanceInterventionActuationAcceptance(
        disposition=(
            GovernanceInterventionActuationDisposition.REJECTED
        ),
        tenant_id="tenant-a",
        contract_hash="contract-hash-001",
        idempotency_key="actuation-001",
        adapter_id="test-adapter",
        adapter_version="0.1.0",
        accepted=False,
    )

    with pytest.raises(FrozenInstanceError):
        acceptance.accepted = True


class _TestAdapter:
    @property
    def adapter_id(self) -> str:
        return "test-adapter"

    @property
    def adapter_version(self) -> str:
        return "0.1.0"

    def accept(
        self,
        *,
        request,
        contract,
    ):
        return GovernanceInterventionActuationAcceptance(
            disposition=(
                GovernanceInterventionActuationDisposition.ACCEPTED
            ),
            tenant_id=request.tenant_id,
            contract_hash=request.contract_hash,
            idempotency_key=request.idempotency_key,
            adapter_id=self.adapter_id,
            adapter_version=self.adapter_version,
            accepted=True,
        )


def test_runtime_protocol_accepts_compatible_adapter():
    adapter = _TestAdapter()

    assert isinstance(
        adapter,
        GovernanceInterventionActuationPort,
    )


def test_port_acceptance_does_not_claim_execution_success():
    contract = _contract()

    request = (
        GovernanceInterventionActuationRequestBuilder()
        .build(
            contract=contract,
            idempotency_key="actuation-001",
        )
    )

    acceptance = _TestAdapter().accept(
        request=request,
        contract=contract,
    )

    assert acceptance.accepted is True

    serialized = acceptance.to_dict()

    assert "executed" not in serialized
    assert "success" not in serialized
    assert "verified" not in serialized
    assert "rollback_performed" not in serialized


def test_port_contract_exposes_accept_but_not_execute():
    adapter = _TestAdapter()

    assert hasattr(adapter, "accept")
    assert not hasattr(adapter, "execute")
    assert not hasattr(adapter, "dispatch")
