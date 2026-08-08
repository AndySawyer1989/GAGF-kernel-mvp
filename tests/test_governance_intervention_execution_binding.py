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
from backend.app.gagf.governance_intervention_execution_binding import (
    GOVERNANCE_INTERVENTION_EXECUTION_BINDING_ID,
    GOVERNANCE_INTERVENTION_EXECUTION_BINDING_SCHEMA_VERSION,
    GOVERNANCE_INTERVENTION_EXECUTION_BINDING_VERSION,
    GovernanceInterventionExecutionBindingBuilder,
    GovernanceInterventionExecutionBindingMismatchError,
    GovernanceInterventionExecutionNotApprovedError,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificExecutionContext,
)


def _approved_item() -> RoadmapItem:
    return RoadmapItem(
        roadmap_item_id="roadmap-item-001",
        intervention_id="intervention-001",
        intervention_type=InterventionType.REMOVE_BLOCKER,
        title="Remove recurring deployment blocker",
        horizon=RoadmapHorizon.DAY_30,
        sequence=1,
        owner_role="Operations Lead",
        measurable_outcome=(
            "Reduce recurring blocked-work events."
        ),
        value_score=0.91,
        implementation_burden=0.35,
        dependency_ids=(),
        status=RoadmapItemStatus.APPROVED,
    )


def _roadmap(
    *,
    item: RoadmapItem | None = None,
    tenant_id: str = "tenant-a",
) -> AssessmentRoadmap:
    governed_item = item or _approved_item()

    phase = RoadmapPhase(
        horizon=RoadmapHorizon.DAY_30,
        objective="Stabilize the highest-value governance constraint.",
        items=(governed_item,),
    )

    return AssessmentRoadmap(
        tenant_id=tenant_id,
        client_id="client-a",
        engagement_id="engagement-a",
        assessment_id="assessment-a",
        intervention_plan_hash="plan-hash-001",
        phases=(phase,),
        total_items=1,
        roadmap_hash="roadmap-hash-001",
    )


def _context(
    *,
    tenant_id: str = "tenant-a",
    request_id: str = "request-001",
    correlation_id: str = "correlation-001",
) -> ScientificExecutionContext:
    return ScientificExecutionContext(
        tenant_id=tenant_id,
        actor_id="actor-001",
        credential_id="credential-001",
        session_id="session-001",
        role_id="scientific-approver",
        policy_scope="scientific-authority:*",
        request_id=request_id,
        correlation_id=correlation_id,
    )


def test_builds_verifiable_binding_for_approved_roadmap_item():
    item = _approved_item()
    roadmap = _roadmap(item=item)
    context = _context()

    binding = (
        GovernanceInterventionExecutionBindingBuilder()
        .build(
            roadmap=roadmap,
            item=item,
            context=context,
        )
    )

    assert binding.verify() is True

    assert binding.binding_id == (
        GOVERNANCE_INTERVENTION_EXECUTION_BINDING_ID
    )
    assert binding.binding_version == (
        GOVERNANCE_INTERVENTION_EXECUTION_BINDING_VERSION
    )
    assert binding.binding_schema_version == (
        GOVERNANCE_INTERVENTION_EXECUTION_BINDING_SCHEMA_VERSION
    )

    assert binding.tenant_id == roadmap.tenant_id
    assert binding.client_id == roadmap.client_id
    assert binding.engagement_id == roadmap.engagement_id
    assert binding.assessment_id == roadmap.assessment_id

    assert binding.roadmap_hash == roadmap.roadmap_hash
    assert binding.intervention_plan_hash == (
        roadmap.intervention_plan_hash
    )

    assert binding.roadmap_item_id == item.roadmap_item_id
    assert binding.intervention_id == item.intervention_id
    assert binding.intervention_type == (
        item.intervention_type.value
    )
    assert binding.horizon == item.horizon.value
    assert binding.sequence == item.sequence
    assert binding.owner_role == item.owner_role
    assert binding.roadmap_status == item.status.value

    assert binding.execution_context_hash == (
        context.context_hash
    )
    assert binding.request_id == context.request_id
    assert binding.correlation_id == context.correlation_id


def test_binding_is_deterministic_for_same_governed_inputs():
    item = _approved_item()
    roadmap = _roadmap(item=item)
    context = _context()

    builder = GovernanceInterventionExecutionBindingBuilder()

    first = builder.build(
        roadmap=roadmap,
        item=item,
        context=context,
    )

    second = builder.build(
        roadmap=roadmap,
        item=item,
        context=context,
    )

    assert first == second
    assert first.binding_hash == second.binding_hash
    assert first.to_dict() == second.to_dict()


def test_binding_changes_when_execution_request_changes():
    item = _approved_item()
    roadmap = _roadmap(item=item)

    builder = GovernanceInterventionExecutionBindingBuilder()

    first = builder.build(
        roadmap=roadmap,
        item=item,
        context=_context(
            request_id="request-001",
        ),
    )

    second = builder.build(
        roadmap=roadmap,
        item=item,
        context=_context(
            request_id="request-002",
        ),
    )

    assert first.execution_context_hash != (
        second.execution_context_hash
    )
    assert first.binding_hash != second.binding_hash


def test_rejects_unapproved_roadmap_item():
    item = replace(
        _approved_item(),
        status=RoadmapItemStatus.PLANNED,
    )

    roadmap = _roadmap(item=item)

    with pytest.raises(
        GovernanceInterventionExecutionNotApprovedError,
        match="Only approved roadmap items",
    ):
        GovernanceInterventionExecutionBindingBuilder().build(
            roadmap=roadmap,
            item=item,
            context=_context(),
        )


def test_rejects_cross_tenant_execution_context():
    item = _approved_item()

    with pytest.raises(
        GovernanceInterventionExecutionBindingMismatchError,
        match="tenant does not match",
    ):
        GovernanceInterventionExecutionBindingBuilder().build(
            roadmap=_roadmap(item=item),
            item=item,
            context=_context(
                tenant_id="tenant-b",
            ),
        )


def test_rejects_item_not_present_in_supplied_roadmap():
    canonical_item = _approved_item()

    foreign_item = replace(
        canonical_item,
        roadmap_item_id="roadmap-item-foreign",
        intervention_id="intervention-foreign",
    )

    with pytest.raises(
        GovernanceInterventionExecutionBindingMismatchError,
        match="not uniquely present",
    ):
        GovernanceInterventionExecutionBindingBuilder().build(
            roadmap=_roadmap(item=canonical_item),
            item=foreign_item,
            context=_context(),
        )


def test_rejects_tampered_copy_of_canonical_roadmap_item():
    canonical_item = _approved_item()

    tampered_item = replace(
        canonical_item,
        owner_role="Unauthorized Owner",
    )

    with pytest.raises(
        GovernanceInterventionExecutionBindingMismatchError,
        match="does not match the canonical item",
    ):
        GovernanceInterventionExecutionBindingBuilder().build(
            roadmap=_roadmap(item=canonical_item),
            item=tampered_item,
            context=_context(),
        )


def test_hash_verification_detects_binding_tampering():
    item = _approved_item()

    binding = (
        GovernanceInterventionExecutionBindingBuilder()
        .build(
            roadmap=_roadmap(item=item),
            item=item,
            context=_context(),
        )
    )

    tampered = replace(
        binding,
        owner_role="Tampered Owner",
    )

    assert binding.verify() is True
    assert tampered.verify() is False


def test_serialization_exposes_hash_bound_execution_lineage():
    item = _approved_item()
    context = _context()

    binding = (
        GovernanceInterventionExecutionBindingBuilder()
        .build(
            roadmap=_roadmap(item=item),
            item=item,
            context=context,
        )
    )

    serialized = binding.to_dict()

    assert serialized["roadmap_item_id"] == (
        item.roadmap_item_id
    )
    assert serialized["intervention_id"] == (
        item.intervention_id
    )
    assert serialized["execution_context_hash"] == (
        context.context_hash
    )
    assert serialized["request_id"] == context.request_id
    assert serialized["correlation_id"] == (
        context.correlation_id
    )
    assert serialized["binding_hash"] == binding.binding_hash


def test_binding_is_immutable():
    item = _approved_item()

    binding = (
        GovernanceInterventionExecutionBindingBuilder()
        .build(
            roadmap=_roadmap(item=item),
            item=item,
            context=_context(),
        )
    )

    with pytest.raises(FrozenInstanceError):
        binding.owner_role = "Mutated Owner"
