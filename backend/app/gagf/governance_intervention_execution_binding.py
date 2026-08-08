from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_assessment_roadmap import (
    AssessmentRoadmap,
    RoadmapItem,
    RoadmapItemStatus,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificExecutionContext,
)


GOVERNANCE_INTERVENTION_EXECUTION_BINDING_ID = (
    "governance-intervention-execution-binding"
)

GOVERNANCE_INTERVENTION_EXECUTION_BINDING_VERSION = "0.1.0"

GOVERNANCE_INTERVENTION_EXECUTION_BINDING_SCHEMA_VERSION = (
    "1.0.0"
)


class GovernanceInterventionExecutionBindingError(
    ValueError
):
    """Raised when a governed intervention cannot be bound to execution."""


class GovernanceInterventionExecutionBindingMismatchError(
    GovernanceInterventionExecutionBindingError
):
    """Raised when roadmap, item, and execution context disagree."""


class GovernanceInterventionExecutionNotApprovedError(
    GovernanceInterventionExecutionBindingError
):
    """Raised when execution is requested before roadmap approval."""


def _require_identifier(
    *,
    field_name: str,
    value: str,
) -> str:
    normalized = value.strip()

    if not normalized:
        raise GovernanceInterventionExecutionBindingError(
            f"{field_name} must not be empty."
        )

    if len(normalized) > 256:
        raise GovernanceInterventionExecutionBindingError(
            f"{field_name} must not exceed 256 characters."
        )

    return normalized


@dataclass(frozen=True, slots=True)
class GovernanceInterventionExecutionBinding:
    binding_schema_version: str
    binding_id: str
    binding_version: str

    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str

    roadmap_hash: str
    intervention_plan_hash: str

    roadmap_item_id: str
    intervention_id: str
    intervention_type: str

    horizon: str
    sequence: int
    owner_role: str
    roadmap_status: str

    execution_context_hash: str
    request_id: str
    correlation_id: str

    binding_hash: str

    def payload(self) -> dict[str, Any]:
        return {
            "binding_schema_version": (
                self.binding_schema_version
            ),
            "binding_id": self.binding_id,
            "binding_version": self.binding_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "roadmap_hash": self.roadmap_hash,
            "intervention_plan_hash": (
                self.intervention_plan_hash
            ),
            "roadmap_item_id": self.roadmap_item_id,
            "intervention_id": self.intervention_id,
            "intervention_type": self.intervention_type,
            "horizon": self.horizon,
            "sequence": self.sequence,
            "owner_role": self.owner_role,
            "roadmap_status": self.roadmap_status,
            "execution_context_hash": (
                self.execution_context_hash
            ),
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.payload(),
            "binding_hash": self.binding_hash,
        }

    def verify(self) -> bool:
        expected_hash = sha256_hex(
            canonical_json(self.payload())
        )

        return expected_hash == self.binding_hash


class GovernanceInterventionExecutionBindingBuilder:
    def build(
        self,
        *,
        roadmap: AssessmentRoadmap,
        item: RoadmapItem,
        context: ScientificExecutionContext,
    ) -> GovernanceInterventionExecutionBinding:
        self._validate_relationships(
            roadmap=roadmap,
            item=item,
            context=context,
        )

        payload = {
            "binding_schema_version": (
                GOVERNANCE_INTERVENTION_EXECUTION_BINDING_SCHEMA_VERSION
            ),
            "binding_id": (
                GOVERNANCE_INTERVENTION_EXECUTION_BINDING_ID
            ),
            "binding_version": (
                GOVERNANCE_INTERVENTION_EXECUTION_BINDING_VERSION
            ),
            "tenant_id": roadmap.tenant_id,
            "client_id": roadmap.client_id,
            "engagement_id": roadmap.engagement_id,
            "assessment_id": roadmap.assessment_id,
            "roadmap_hash": roadmap.roadmap_hash,
            "intervention_plan_hash": (
                roadmap.intervention_plan_hash
            ),
            "roadmap_item_id": item.roadmap_item_id,
            "intervention_id": item.intervention_id,
            "intervention_type": item.intervention_type.value,
            "horizon": item.horizon.value,
            "sequence": item.sequence,
            "owner_role": item.owner_role,
            "roadmap_status": item.status.value,
            "execution_context_hash": context.context_hash,
            "request_id": context.request_id,
            "correlation_id": context.correlation_id,
        }

        binding_hash = sha256_hex(
            canonical_json(payload)
        )

        return GovernanceInterventionExecutionBinding(
            **payload,
            binding_hash=binding_hash,
        )

    def _validate_relationships(
        self,
        *,
        roadmap: AssessmentRoadmap,
        item: RoadmapItem,
        context: ScientificExecutionContext,
    ) -> None:
        tenant_id = _require_identifier(
            field_name="roadmap.tenant_id",
            value=roadmap.tenant_id,
        )

        _require_identifier(
            field_name="roadmap.client_id",
            value=roadmap.client_id,
        )

        _require_identifier(
            field_name="roadmap.engagement_id",
            value=roadmap.engagement_id,
        )

        _require_identifier(
            field_name="roadmap.assessment_id",
            value=roadmap.assessment_id,
        )

        _require_identifier(
            field_name="roadmap.roadmap_hash",
            value=roadmap.roadmap_hash,
        )

        _require_identifier(
            field_name="roadmap.intervention_plan_hash",
            value=roadmap.intervention_plan_hash,
        )

        _require_identifier(
            field_name="item.roadmap_item_id",
            value=item.roadmap_item_id,
        )

        _require_identifier(
            field_name="item.intervention_id",
            value=item.intervention_id,
        )

        _require_identifier(
            field_name="item.owner_role",
            value=item.owner_role,
        )

        if context.tenant_id != tenant_id:
            raise (
                GovernanceInterventionExecutionBindingMismatchError(
                    "Execution context tenant does not match "
                    "assessment roadmap tenant."
                )
            )

        roadmap_items = tuple(
            roadmap_item
            for phase in roadmap.phases
            for roadmap_item in phase.items
        )

        matching_items = tuple(
            roadmap_item
            for roadmap_item in roadmap_items
            if roadmap_item.roadmap_item_id
            == item.roadmap_item_id
        )

        if len(matching_items) != 1:
            raise (
                GovernanceInterventionExecutionBindingMismatchError(
                    "Roadmap item is not uniquely present in "
                    "the supplied assessment roadmap."
                )
            )

        canonical_item = matching_items[0]

        if canonical_item != item:
            raise (
                GovernanceInterventionExecutionBindingMismatchError(
                    "Supplied roadmap item does not match "
                    "the canonical item in the assessment roadmap."
                )
            )

        if item.status is not RoadmapItemStatus.APPROVED:
            raise GovernanceInterventionExecutionNotApprovedError(
                "Only approved roadmap items may be bound "
                "for execution."
            )
