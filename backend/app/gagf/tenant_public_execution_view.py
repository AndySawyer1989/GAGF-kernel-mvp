from dataclasses import dataclass, replace

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.tenant_namespaced_execution import (
    TenantNamespacedExecutionResult,
)


TENANT_PUBLIC_EXECUTION_VIEW_ID = (
    "tenant-public-scientific-execution-view"
)
TENANT_PUBLIC_EXECUTION_VIEW_VERSION = "0.1.0"
TENANT_PUBLIC_EXECUTION_VIEW_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class TenantPublicArtifactIdentifiers:
    execution_id: str
    execution_receipt_id: str
    authority_receipt_id: str
    audit_receipt_id: str
    checkpoint_id: str
    context_binding_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "execution_id": self.execution_id,
            "execution_receipt_id": (
                self.execution_receipt_id
            ),
            "authority_receipt_id": (
                self.authority_receipt_id
            ),
            "audit_receipt_id": self.audit_receipt_id,
            "checkpoint_id": self.checkpoint_id,
            "context_binding_id": self.context_binding_id,
        }


@dataclass(frozen=True, slots=True)
class TenantPublicExecutionView:
    schema_version: str
    view_id: str
    view_version: str
    tenant_id: str
    resumed: bool
    decision_allowed: bool
    checkpoint_valid: bool
    context_binding_sequence_number: int
    namespace_sequence_numbers: tuple[int, ...]
    public_artifacts: TenantPublicArtifactIdentifiers
    view_hash: str

    def payload(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "view_id": self.view_id,
            "view_version": self.view_version,
            "tenant_id": self.tenant_id,
            "resumed": self.resumed,
            "decision_allowed": self.decision_allowed,
            "checkpoint_valid": self.checkpoint_valid,
            "context_binding_sequence_number": (
                self.context_binding_sequence_number
            ),
            "namespace_sequence_numbers": list(
                self.namespace_sequence_numbers
            ),
            "public_artifacts": (
                self.public_artifacts.to_dict()
            ),
        }

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "view_hash": self.view_hash,
        }

    def verify(self) -> bool:
        expected_hash = sha256_hex(
            canonical_json(self.payload())
        )

        return expected_hash == self.view_hash


class TenantPublicExecutionViewBuilder:
    def build(
        self,
        *,
        result: TenantNamespacedExecutionResult,
    ) -> TenantPublicExecutionView:
        bundle = result.namespace_bundle

        public_artifacts = TenantPublicArtifactIdentifiers(
            execution_id=(
                bundle.execution.namespaced_artifact_id
            ),
            execution_receipt_id=(
                bundle.execution_receipt
                .namespaced_artifact_id
            ),
            authority_receipt_id=(
                bundle.authority_receipt
                .namespaced_artifact_id
            ),
            audit_receipt_id=(
                bundle.audit_receipt
                .namespaced_artifact_id
            ),
            checkpoint_id=(
                bundle.checkpoint.namespaced_artifact_id
            ),
            context_binding_id=(
                bundle.context_binding
                .namespaced_artifact_id
            ),
        )

        payload = {
            "schema_version": (
                TENANT_PUBLIC_EXECUTION_VIEW_SCHEMA_VERSION
            ),
            "view_id": TENANT_PUBLIC_EXECUTION_VIEW_ID,
            "view_version": (
                TENANT_PUBLIC_EXECUTION_VIEW_VERSION
            ),
            "tenant_id": result.tenant_id,
            "resumed": result.pipeline_result.resumed,
            "decision_allowed": (
                result.pipeline_result.pipeline_result
                .decision_allowed
            ),
            "checkpoint_valid": (
                result.pipeline_result.pipeline_result
                .checkpoint_valid
            ),
            "context_binding_sequence_number": (
                result.context_binding.sequence_number
            ),
            "namespace_sequence_numbers": [
                record.sequence_number
                for record in result.namespace_records
            ],
            "public_artifacts": (
                public_artifacts.to_dict()
            ),
        }

        return TenantPublicExecutionView(
            schema_version=(
                TENANT_PUBLIC_EXECUTION_VIEW_SCHEMA_VERSION
            ),
            view_id=TENANT_PUBLIC_EXECUTION_VIEW_ID,
            view_version=(
                TENANT_PUBLIC_EXECUTION_VIEW_VERSION
            ),
            tenant_id=result.tenant_id,
            resumed=result.pipeline_result.resumed,
            decision_allowed=(
                result.pipeline_result.pipeline_result
                .decision_allowed
            ),
            checkpoint_valid=(
                result.pipeline_result.pipeline_result
                .checkpoint_valid
            ),
            context_binding_sequence_number=(
                result.context_binding.sequence_number
            ),
            namespace_sequence_numbers=tuple(
                record.sequence_number
                for record in result.namespace_records
            ),
            public_artifacts=public_artifacts,
            view_hash=sha256_hex(
                canonical_json(payload)
            ),
        )
