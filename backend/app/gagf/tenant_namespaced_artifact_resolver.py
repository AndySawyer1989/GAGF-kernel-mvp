from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.app.gagf.tenant_artifact_namespace import (
    TenantArtifactNamespaceLedger,
    TenantArtifactNamespaceLedgerRecord,
)
from backend.app.gagf.tenant_scientific_artifact_access import (
    TenantArtifactAccessResult,
    TenantExecutionAccessResult,
    TenantScientificArtifactAccessService,
)


TENANT_NAMESPACED_ARTIFACT_RESOLVER_ID = (
    "tenant-namespaced-scientific-artifact-resolver"
)
TENANT_NAMESPACED_ARTIFACT_RESOLVER_VERSION = "0.1.0"


ResolvableTenantArtifactType = Literal[
    "authority_receipt",
    "checkpoint",
    "execution",
    "context_binding",
]


class TenantNamespacedArtifactResolutionError(RuntimeError):
    pass


class TenantNamespacedArtifactNotFoundError(
    TenantNamespacedArtifactResolutionError
):
    pass


class TenantNamespacedArtifactTypeMismatchError(
    TenantNamespacedArtifactResolutionError
):
    pass


class TenantNamespacedArtifactIntegrityError(
    TenantNamespacedArtifactResolutionError
):
    pass


@dataclass(frozen=True, slots=True)
class TenantNamespacedArtifactResolution:
    resolver_id: str
    resolver_version: str
    tenant_id: str
    artifact_type: ResolvableTenantArtifactType
    namespaced_artifact_id: str
    canonical_artifact_id: str
    namespace_sequence_number: int
    artifact: dict

    def to_dict(self) -> dict:
        return {
            "resolver_id": self.resolver_id,
            "resolver_version": self.resolver_version,
            "tenant_id": self.tenant_id,
            "artifact_type": self.artifact_type,
            "namespaced_artifact_id": (
                self.namespaced_artifact_id
            ),
            "canonical_artifact_id": (
                self.canonical_artifact_id
            ),
            "namespace_sequence_number": (
                self.namespace_sequence_number
            ),
            "artifact": dict(self.artifact),
        }


class TenantNamespacedArtifactResolver:
    def __init__(
        self,
        *,
        namespace_database_path: str | Path,
        authority_database_path: str | Path,
        checkpoint_database_path: str | Path,
        journal_database_path: str | Path,
        context_binding_database_path: str | Path,
    ) -> None:
        self.namespace_ledger = TenantArtifactNamespaceLedger(
            namespace_database_path
        )

        self.artifact_access = (
            TenantScientificArtifactAccessService(
                authority_database_path=(
                    authority_database_path
                ),
                checkpoint_database_path=(
                    checkpoint_database_path
                ),
                journal_database_path=journal_database_path,
                context_binding_database_path=(
                    context_binding_database_path
                ),
            )
        )

    def resolve(
        self,
        *,
        tenant_id: str,
        artifact_type: ResolvableTenantArtifactType,
        namespaced_artifact_id: str,
    ) -> TenantNamespacedArtifactResolution:
        namespace_record = self._get_namespace(
            tenant_id=tenant_id,
            artifact_type=artifact_type,
            namespaced_artifact_id=(
                namespaced_artifact_id
            ),
        )

        canonical_artifact_id = (
            namespace_record.namespace
            .canonical_artifact_id
        )

        artifact = self._resolve_canonical_artifact(
            tenant_id=tenant_id,
            artifact_type=artifact_type,
            canonical_artifact_id=canonical_artifact_id,
        )

        return TenantNamespacedArtifactResolution(
            resolver_id=(
                TENANT_NAMESPACED_ARTIFACT_RESOLVER_ID
            ),
            resolver_version=(
                TENANT_NAMESPACED_ARTIFACT_RESOLVER_VERSION
            ),
            tenant_id=tenant_id,
            artifact_type=artifact_type,
            namespaced_artifact_id=(
                namespaced_artifact_id
            ),
            canonical_artifact_id=canonical_artifact_id,
            namespace_sequence_number=(
                namespace_record.sequence_number
            ),
            artifact=artifact,
        )

    def resolve_authority_receipt(
        self,
        *,
        tenant_id: str,
        namespaced_artifact_id: str,
    ) -> TenantNamespacedArtifactResolution:
        return self.resolve(
            tenant_id=tenant_id,
            artifact_type="authority_receipt",
            namespaced_artifact_id=(
                namespaced_artifact_id
            ),
        )

    def resolve_checkpoint(
        self,
        *,
        tenant_id: str,
        namespaced_artifact_id: str,
    ) -> TenantNamespacedArtifactResolution:
        return self.resolve(
            tenant_id=tenant_id,
            artifact_type="checkpoint",
            namespaced_artifact_id=(
                namespaced_artifact_id
            ),
        )

    def resolve_execution(
        self,
        *,
        tenant_id: str,
        namespaced_artifact_id: str,
    ) -> TenantNamespacedArtifactResolution:
        return self.resolve(
            tenant_id=tenant_id,
            artifact_type="execution",
            namespaced_artifact_id=(
                namespaced_artifact_id
            ),
        )

    def resolve_context_binding(
        self,
        *,
        tenant_id: str,
        namespaced_artifact_id: str,
    ) -> TenantNamespacedArtifactResolution:
        return self.resolve(
            tenant_id=tenant_id,
            artifact_type="context_binding",
            namespaced_artifact_id=(
                namespaced_artifact_id
            ),
        )

    def _get_namespace(
        self,
        *,
        tenant_id: str,
        artifact_type: ResolvableTenantArtifactType,
        namespaced_artifact_id: str,
    ) -> TenantArtifactNamespaceLedgerRecord:
        record = self.namespace_ledger.get_by_namespaced_id(
            tenant_id=tenant_id,
            artifact_type=artifact_type,
            namespaced_artifact_id=(
                namespaced_artifact_id
            ),
        )

        if record is None:
            raise TenantNamespacedArtifactNotFoundError(
                "Tenant namespaced scientific artifact "
                "was not found."
            )

        if not record.namespace.verify():
            raise TenantNamespacedArtifactIntegrityError(
                "Tenant artifact namespace failed integrity "
                "verification."
            )

        if record.namespace.artifact_type != artifact_type:
            raise TenantNamespacedArtifactTypeMismatchError(
                "Tenant artifact namespace type does not "
                "match the requested artifact type."
            )

        if record.namespace.tenant_id != tenant_id:
            raise TenantNamespacedArtifactIntegrityError(
                "Tenant artifact namespace tenant binding "
                "does not match the requesting tenant."
            )

        return record

    def _resolve_canonical_artifact(
        self,
        *,
        tenant_id: str,
        artifact_type: ResolvableTenantArtifactType,
        canonical_artifact_id: str,
    ) -> dict:
        result: (
            TenantArtifactAccessResult
            | TenantExecutionAccessResult
        )

        if artifact_type == "authority_receipt":
            result = (
                self.artifact_access
                .get_authority_receipt(
                    tenant_id=tenant_id,
                    receipt_hash=canonical_artifact_id,
                )
            )
            return result.to_dict()

        if artifact_type == "checkpoint":
            result = self.artifact_access.get_checkpoint(
                tenant_id=tenant_id,
                checkpoint_hash=canonical_artifact_id,
            )
            return result.to_dict()

        if artifact_type == "execution":
            result = self.artifact_access.get_execution(
                tenant_id=tenant_id,
                execution_id=canonical_artifact_id,
            )
            return result.to_dict()

        if artifact_type == "context_binding":
            result = (
                self.artifact_access
                .get_context_binding(
                    tenant_id=tenant_id,
                    binding_hash=canonical_artifact_id,
                )
            )
            return result.to_dict()

        raise TenantNamespacedArtifactTypeMismatchError(
            "Unsupported tenant artifact type."
        )
