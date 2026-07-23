from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from backend.app.gagf.scientific_authority_receipt_ledger import (
    AuthorityReceiptLedgerRecord,
    ScientificAuthorityReceiptLedger,
)
from backend.app.gagf.scientific_context_binding_index import (
    DuplicateScientificArtifactBindingError,
    ScientificContextBindingArtifactIndex,
)
from backend.app.gagf.scientific_evidence_checkpoint_ledger import (
    ScientificEvidenceCheckpointLedger,
    ScientificEvidenceCheckpointLedgerRecord,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificContextBindingLedger,
    ScientificContextBindingLedgerRecord,
)
from backend.app.gagf.scientific_pipeline_execution_journal import (
    ScientificPipelineExecutionJournal,
    ScientificPipelineJournalRecord,
    ScientificPipelineJournalTransition,
)


TENANT_ARTIFACT_ACCESS_SERVICE_ID = (
    "tenant-scientific-artifact-access-service"
)
TENANT_ARTIFACT_ACCESS_SERVICE_VERSION = "0.2.0"


ScientificArtifactType = Literal[
    "authority_receipt",
    "checkpoint",
    "execution",
    "context_binding",
]


class TenantScientificArtifactAccessError(RuntimeError):
    pass


class TenantScientificArtifactNotFoundError(
    TenantScientificArtifactAccessError
):
    pass


class TenantScientificArtifactAccessDeniedError(
    TenantScientificArtifactAccessError
):
    pass


class TenantScientificArtifactUnboundError(
    TenantScientificArtifactAccessError
):
    pass


class TenantScientificArtifactBindingConflictError(
    TenantScientificArtifactAccessError
):
    pass


@dataclass(frozen=True, slots=True)
class TenantArtifactAccessResult:
    service_id: str
    service_version: str
    tenant_id: str
    artifact_type: ScientificArtifactType
    artifact_id: str
    binding_hash: str
    artifact: dict

    def to_dict(self) -> dict:
        return {
            "service_id": self.service_id,
            "service_version": self.service_version,
            "tenant_id": self.tenant_id,
            "artifact_type": self.artifact_type,
            "artifact_id": self.artifact_id,
            "binding_hash": self.binding_hash,
            "artifact": dict(self.artifact),
        }


@dataclass(frozen=True, slots=True)
class TenantExecutionAccessResult:
    service_id: str
    service_version: str
    tenant_id: str
    execution_id: str
    binding_hash: str
    execution: dict
    transitions: tuple[dict, ...]

    def to_dict(self) -> dict:
        return {
            "service_id": self.service_id,
            "service_version": self.service_version,
            "tenant_id": self.tenant_id,
            "execution_id": self.execution_id,
            "binding_hash": self.binding_hash,
            "execution": dict(self.execution),
            "transitions": [
                dict(transition)
                for transition in self.transitions
            ],
        }


class TenantScientificArtifactAccessService:
    def __init__(
        self,
        *,
        authority_database_path: str | Path,
        checkpoint_database_path: str | Path,
        journal_database_path: str | Path,
        context_binding_database_path: str | Path,
    ) -> None:
        self.authority_ledger = ScientificAuthorityReceiptLedger(
            authority_database_path
        )
        self.checkpoint_ledger = ScientificEvidenceCheckpointLedger(
            checkpoint_database_path
        )
        self.journal = ScientificPipelineExecutionJournal(
            journal_database_path
        )
        self.binding_ledger = ScientificContextBindingLedger(
            context_binding_database_path
        )
        self.binding_index = ScientificContextBindingArtifactIndex(
            context_binding_database_path
        )

    def get_authority_receipt(
        self,
        *,
        tenant_id: str,
        receipt_hash: str,
    ) -> TenantArtifactAccessResult:
        record = self.authority_ledger.get_by_hash(
            receipt_hash
        )

        if record is None:
            raise TenantScientificArtifactNotFoundError(
                "Authority receipt was not found."
            )

        binding_record = self._find_binding_for_artifact(
            tenant_id=tenant_id,
            artifact_type="authority_receipt",
            artifact_id=receipt_hash,
        )

        return self._authority_receipt_result(
            tenant_id=tenant_id,
            record=record,
            binding_record=binding_record,
        )

    def get_checkpoint(
        self,
        *,
        tenant_id: str,
        checkpoint_hash: str,
    ) -> TenantArtifactAccessResult:
        record = self.checkpoint_ledger.get_by_hash(
            checkpoint_hash
        )

        if record is None:
            raise TenantScientificArtifactNotFoundError(
                "Scientific evidence checkpoint was not found."
            )

        binding_record = self._find_binding_for_artifact(
            tenant_id=tenant_id,
            artifact_type="checkpoint",
            artifact_id=checkpoint_hash,
        )

        return self._checkpoint_result(
            tenant_id=tenant_id,
            record=record,
            binding_record=binding_record,
        )

    def get_execution(
        self,
        *,
        tenant_id: str,
        execution_id: str,
    ) -> TenantExecutionAccessResult:
        execution = self.journal.get(execution_id)

        if execution is None:
            raise TenantScientificArtifactNotFoundError(
                "Scientific pipeline execution was not found."
            )

        binding_record = self._find_binding_for_artifact(
            tenant_id=tenant_id,
            artifact_type="execution",
            artifact_id=execution_id,
        )
        transitions = self.journal.list_transitions(
            execution_id
        )

        return self._execution_result(
            tenant_id=tenant_id,
            execution=execution,
            transitions=transitions,
            binding_record=binding_record,
        )

    def get_context_binding(
        self,
        *,
        tenant_id: str,
        binding_hash: str,
    ) -> TenantArtifactAccessResult:
        try:
            record = self.binding_index.find_for_tenant(
                tenant_id=tenant_id,
                artifact_type="context_binding",
                artifact_id=binding_hash,
            )
        except DuplicateScientificArtifactBindingError as exc:
            raise TenantScientificArtifactBindingConflictError(
                str(exc)
            ) from exc

        if record is not None:
            return TenantArtifactAccessResult(
                service_id=TENANT_ARTIFACT_ACCESS_SERVICE_ID,
                service_version=(
                    TENANT_ARTIFACT_ACCESS_SERVICE_VERSION
                ),
                tenant_id=tenant_id,
                artifact_type="context_binding",
                artifact_id=binding_hash,
                binding_hash=binding_hash,
                artifact=record.to_dict(),
            )

        owner = self.binding_index.find_owner(
            artifact_type="context_binding",
            artifact_id=binding_hash,
        )

        if owner is not None:
            raise TenantScientificArtifactAccessDeniedError(
                "Cross-tenant context-binding access is denied."
            )

        raise TenantScientificArtifactNotFoundError(
            "Scientific execution context binding was not found."
        )

    def list_tenant_bindings(
        self,
        *,
        tenant_id: str,
    ) -> tuple[TenantArtifactAccessResult, ...]:
        records = self.binding_ledger.list_for_tenant(
            tenant_id
        )

        return tuple(
            TenantArtifactAccessResult(
                service_id=TENANT_ARTIFACT_ACCESS_SERVICE_ID,
                service_version=(
                    TENANT_ARTIFACT_ACCESS_SERVICE_VERSION
                ),
                tenant_id=tenant_id,
                artifact_type="context_binding",
                artifact_id=record.binding.binding_hash,
                binding_hash=record.binding.binding_hash,
                artifact=record.to_dict(),
            )
            for record in records
        )

    def _find_binding_for_artifact(
        self,
        *,
        tenant_id: str,
        artifact_type: ScientificArtifactType,
        artifact_id: str,
    ) -> ScientificContextBindingLedgerRecord:
        try:
            tenant_binding = self.binding_index.find_for_tenant(
                tenant_id=tenant_id,
                artifact_type=artifact_type,
                artifact_id=artifact_id,
            )
        except DuplicateScientificArtifactBindingError as exc:
            raise TenantScientificArtifactBindingConflictError(
                str(exc)
            ) from exc

        if tenant_binding is not None:
            return tenant_binding

        try:
            owner = self.binding_index.find_owner(
                artifact_type=artifact_type,
                artifact_id=artifact_id,
            )
        except DuplicateScientificArtifactBindingError as exc:
            raise TenantScientificArtifactBindingConflictError(
                str(exc)
            ) from exc

        if owner is not None:
            raise TenantScientificArtifactAccessDeniedError(
                "Cross-tenant scientific artifact access is denied."
            )

        raise TenantScientificArtifactUnboundError(
            "Scientific artifact exists but is not bound to a "
            "tenant execution context."
        )

    def _authority_receipt_result(
        self,
        *,
        tenant_id: str,
        record: AuthorityReceiptLedgerRecord,
        binding_record: ScientificContextBindingLedgerRecord,
    ) -> TenantArtifactAccessResult:
        return TenantArtifactAccessResult(
            service_id=TENANT_ARTIFACT_ACCESS_SERVICE_ID,
            service_version=(
                TENANT_ARTIFACT_ACCESS_SERVICE_VERSION
            ),
            tenant_id=tenant_id,
            artifact_type="authority_receipt",
            artifact_id=record.receipt.receipt_hash,
            binding_hash=(
                binding_record.binding.binding_hash
            ),
            artifact=record.to_dict(),
        )

    def _checkpoint_result(
        self,
        *,
        tenant_id: str,
        record: ScientificEvidenceCheckpointLedgerRecord,
        binding_record: ScientificContextBindingLedgerRecord,
    ) -> TenantArtifactAccessResult:
        return TenantArtifactAccessResult(
            service_id=TENANT_ARTIFACT_ACCESS_SERVICE_ID,
            service_version=(
                TENANT_ARTIFACT_ACCESS_SERVICE_VERSION
            ),
            tenant_id=tenant_id,
            artifact_type="checkpoint",
            artifact_id=(
                record.checkpoint.checkpoint_hash
            ),
            binding_hash=(
                binding_record.binding.binding_hash
            ),
            artifact=record.to_dict(),
        )

    def _execution_result(
        self,
        *,
        tenant_id: str,
        execution: ScientificPipelineJournalRecord,
        transitions: tuple[
            ScientificPipelineJournalTransition,
            ...,
        ],
        binding_record: ScientificContextBindingLedgerRecord,
    ) -> TenantExecutionAccessResult:
        return TenantExecutionAccessResult(
            service_id=TENANT_ARTIFACT_ACCESS_SERVICE_ID,
            service_version=(
                TENANT_ARTIFACT_ACCESS_SERVICE_VERSION
            ),
            tenant_id=tenant_id,
            execution_id=execution.execution_id,
            binding_hash=(
                binding_record.binding.binding_hash
            ),
            execution=execution.to_dict(),
            transitions=tuple(
                transition.to_dict()
                for transition in transitions
            ),
        )
