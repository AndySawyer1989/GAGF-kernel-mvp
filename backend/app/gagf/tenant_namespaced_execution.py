from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
)
from backend.app.gagf.scientific_calculation_contract import (
    CalculationAuthority,
    ScientificCalculationContract,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificContextBindingLedger,
    ScientificContextBindingLedgerRecord,
    ScientificExecutionContext,
    ScientificExecutionContextBindingBuilder,
)
from backend.app.gagf.scientific_pipeline_execution_journal import (
    RecoverableScientificPipelineResult,
    ScientificPipelineRecoveryCoordinator,
)
from backend.app.gagf.tenant_artifact_namespace import (
    TenantArtifactNamespaceBundle,
    TenantArtifactNamespaceBundleBuilder,
    TenantArtifactNamespaceLedger,
    TenantArtifactNamespaceLedgerRecord,
)


TENANT_NAMESPACED_EXECUTION_SERVICE_ID = (
    "tenant-namespaced-scientific-execution-service"
)
TENANT_NAMESPACED_EXECUTION_SERVICE_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class TenantNamespacedExecutionPaths:
    authority_database_path: Path
    audit_database_path: Path
    checkpoint_database_path: Path
    journal_database_path: Path
    context_binding_database_path: Path
    namespace_database_path: Path


@dataclass(frozen=True, slots=True)
class TenantNamespacedExecutionResult:
    service_id: str
    service_version: str
    tenant_id: str
    pipeline_result: RecoverableScientificPipelineResult
    context_binding: ScientificContextBindingLedgerRecord
    namespace_bundle: TenantArtifactNamespaceBundle
    namespace_records: tuple[
        TenantArtifactNamespaceLedgerRecord,
        ...,
    ]

    def to_dict(self) -> dict:
        return {
            "service_id": self.service_id,
            "service_version": self.service_version,
            "tenant_id": self.tenant_id,
            "pipeline_result": self.pipeline_result.to_dict(),
            "context_binding": self.context_binding.to_dict(),
            "namespace_bundle": self.namespace_bundle.to_dict(),
            "namespace_records": [
                record.to_dict()
                for record in self.namespace_records
            ],
        }


class TenantNamespacedScientificExecutionService:
    def __init__(
        self,
        *,
        paths: TenantNamespacedExecutionPaths,
    ) -> None:
        self.coordinator = ScientificPipelineRecoveryCoordinator(
            authority_database_path=(
                paths.authority_database_path
            ),
            audit_database_path=paths.audit_database_path,
            checkpoint_database_path=(
                paths.checkpoint_database_path
            ),
            journal_database_path=paths.journal_database_path,
        )

        self.context_binding_ledger = (
            ScientificContextBindingLedger(
                paths.context_binding_database_path
            )
        )

        self.namespace_ledger = TenantArtifactNamespaceLedger(
            paths.namespace_database_path
        )

        self.binding_builder = (
            ScientificExecutionContextBindingBuilder()
        )
        self.namespace_builder = (
            TenantArtifactNamespaceBundleBuilder()
        )

    def execute(
        self,
        *,
        context: ScientificExecutionContext,
        contract: ScientificCalculationContract,
        requested_authority: CalculationAuthority,
        evidence: AuthorityEscalationEvidence,
    ) -> TenantNamespacedExecutionResult:
        pipeline_result = self.coordinator.execute(
            contract=contract,
            requested_authority=requested_authority,
            evidence=evidence,
        )

        binding = self.binding_builder.build(
            context=context,
            result=pipeline_result,
        )

        binding_record = self.context_binding_ledger.append(
            binding
        )

        namespace_bundle = self.namespace_builder.build(
            tenant_id=context.tenant_id,
            execution_id=pipeline_result.execution_id,
            execution_receipt_hash=(
                pipeline_result.execution_receipt.receipt_hash
            ),
            authority_receipt_hash=(
                pipeline_result.pipeline_result
                .authority_receipt_hash
            ),
            audit_receipt_hash=(
                pipeline_result.pipeline_result
                .audit_receipt_hash
            ),
            checkpoint_hash=(
                pipeline_result.pipeline_result.checkpoint_hash
            ),
            context_binding_hash=binding.binding_hash,
        )

        namespace_records = (
            self.namespace_ledger.append_bundle(
                namespace_bundle
            )
        )

        return TenantNamespacedExecutionResult(
            service_id=(
                TENANT_NAMESPACED_EXECUTION_SERVICE_ID
            ),
            service_version=(
                TENANT_NAMESPACED_EXECUTION_SERVICE_VERSION
            ),
            tenant_id=context.tenant_id,
            pipeline_result=pipeline_result,
            context_binding=binding_record,
            namespace_bundle=namespace_bundle,
            namespace_records=namespace_records,
        )
