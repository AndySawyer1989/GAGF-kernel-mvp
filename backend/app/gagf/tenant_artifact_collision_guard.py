from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.app.gagf.scientific_context_binding_index import (
    DuplicateScientificArtifactBindingError,
    ScientificArtifactBindingOwner,
    ScientificContextBindingArtifactIndex,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificExecutionContextBinding,
)


TENANT_ARTIFACT_COLLISION_GUARD_ID = (
    "tenant-scientific-artifact-collision-guard"
)
TENANT_ARTIFACT_COLLISION_GUARD_VERSION = "0.1.0"


CollisionArtifactType = Literal[
    "authority_receipt",
    "checkpoint",
    "execution",
    "context_binding",
]


class TenantArtifactCollisionGuardError(RuntimeError):
    pass


class CrossTenantArtifactCollisionError(
    TenantArtifactCollisionGuardError
):
    pass


class AmbiguousArtifactOwnershipError(
    TenantArtifactCollisionGuardError
):
    pass


@dataclass(frozen=True, slots=True)
class TenantArtifactCollision:
    artifact_type: CollisionArtifactType
    artifact_id: str
    requested_tenant_id: str
    owning_tenant_id: str
    owning_binding_hash: str
    owning_execution_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "artifact_type": self.artifact_type,
            "artifact_id": self.artifact_id,
            "requested_tenant_id": self.requested_tenant_id,
            "owning_tenant_id": self.owning_tenant_id,
            "owning_binding_hash": self.owning_binding_hash,
            "owning_execution_id": self.owning_execution_id,
        }


@dataclass(frozen=True, slots=True)
class TenantArtifactCollisionDecision:
    allowed: bool
    guard_id: str
    guard_version: str
    tenant_id: str
    binding_hash: str
    collisions: tuple[TenantArtifactCollision, ...]

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "guard_id": self.guard_id,
            "guard_version": self.guard_version,
            "tenant_id": self.tenant_id,
            "binding_hash": self.binding_hash,
            "collisions": [
                collision.to_dict()
                for collision in self.collisions
            ],
        }


class TenantArtifactCollisionGuard:
    def __init__(
        self,
        context_binding_database_path: str | Path,
    ) -> None:
        self.index = ScientificContextBindingArtifactIndex(
            context_binding_database_path
        )

    def evaluate(
        self,
        binding: ScientificExecutionContextBinding,
    ) -> TenantArtifactCollisionDecision:
        tenant_id = binding.context["tenant_id"]
        collisions: list[TenantArtifactCollision] = []

        artifacts: tuple[
            tuple[CollisionArtifactType, str],
            ...,
        ] = (
            (
                "authority_receipt",
                binding.authority_receipt_hash,
            ),
            (
                "checkpoint",
                binding.checkpoint_hash,
            ),
            (
                "execution",
                binding.execution_id,
            ),
            (
                "context_binding",
                binding.binding_hash,
            ),
        )

        for artifact_type, artifact_id in artifacts:
            owner = self._find_owner(
                artifact_type=artifact_type,
                artifact_id=artifact_id,
            )

            if owner is None:
                continue

            if owner.tenant_id == tenant_id:
                continue

            collisions.append(
                self._build_collision(
                    artifact_type=artifact_type,
                    artifact_id=artifact_id,
                    requested_tenant_id=tenant_id,
                    owner=owner,
                )
            )

        return TenantArtifactCollisionDecision(
            allowed=not collisions,
            guard_id=TENANT_ARTIFACT_COLLISION_GUARD_ID,
            guard_version=(
                TENANT_ARTIFACT_COLLISION_GUARD_VERSION
            ),
            tenant_id=tenant_id,
            binding_hash=binding.binding_hash,
            collisions=tuple(collisions),
        )

    def enforce(
        self,
        binding: ScientificExecutionContextBinding,
    ) -> TenantArtifactCollisionDecision:
        decision = self.evaluate(binding)

        if not decision.allowed:
            collision_types = ", ".join(
                collision.artifact_type
                for collision in decision.collisions
            )

            raise CrossTenantArtifactCollisionError(
                "Cross-tenant deterministic artifact collision "
                f"detected for: {collision_types}."
            )

        return decision

    def _find_owner(
        self,
        *,
        artifact_type: CollisionArtifactType,
        artifact_id: str,
    ) -> ScientificArtifactBindingOwner | None:
        try:
            return self.index.find_owner(
                artifact_type=artifact_type,
                artifact_id=artifact_id,
            )
        except DuplicateScientificArtifactBindingError as exc:
            raise AmbiguousArtifactOwnershipError(
                "Scientific artifact already has ambiguous "
                "multi-context ownership."
            ) from exc

    def _build_collision(
        self,
        *,
        artifact_type: CollisionArtifactType,
        artifact_id: str,
        requested_tenant_id: str,
        owner: ScientificArtifactBindingOwner,
    ) -> TenantArtifactCollision:
        return TenantArtifactCollision(
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            requested_tenant_id=requested_tenant_id,
            owning_tenant_id=owner.tenant_id,
            owning_binding_hash=owner.binding_hash,
            owning_execution_id=owner.execution_id,
        )
