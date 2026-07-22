from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.scientific_authority_audit_receipt_ledger import (
    ScientificAuthorityAuditReceiptLedger,
)
from backend.app.gagf.scientific_authority_guard import (
    AuthorityEscalationEvidence,
    ScientificAuthorityEscalationGuard,
)
from backend.app.gagf.scientific_authority_ledger_audit_receipt import (
    ScientificAuthorityLedgerAuditReceiptBuilder,
)
from backend.app.gagf.scientific_authority_ledger_auditor import (
    ScientificAuthorityLedgerIntegrityAuditor,
)
from backend.app.gagf.scientific_authority_receipt_ledger import (
    ScientificAuthorityReceiptLedger,
)
from backend.app.gagf.scientific_calculation_contract import (
    CalculationAuthority,
    ScientificCalculationContract,
)
from backend.app.gagf.scientific_evidence_checkpoint import (
    ScientificEvidenceCheckpointBuilder,
)
from backend.app.gagf.scientific_evidence_checkpoint_ledger import (
    ScientificEvidenceCheckpointLedger,
)


SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_ID = (
    "constitutional-scientific-authority-evidence-pipeline"
)
SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class ScientificAuthorityEvidencePipelineResult:
    pipeline_id: str
    pipeline_version: str
    calculation_id: str
    calculation_version: str
    requested_authority: str
    decision_allowed: bool
    authority_receipt_sequence: int
    authority_receipt_hash: str
    authority_ledger_audit_valid: bool
    audit_receipt_sequence: int
    audit_receipt_hash: str
    checkpoint_sequence: int
    checkpoint_hash: str
    checkpoint_valid: bool

    def to_dict(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "pipeline_version": self.pipeline_version,
            "calculation_id": self.calculation_id,
            "calculation_version": self.calculation_version,
            "requested_authority": self.requested_authority,
            "decision_allowed": self.decision_allowed,
            "authority_receipt_sequence": (
                self.authority_receipt_sequence
            ),
            "authority_receipt_hash": (
                self.authority_receipt_hash
            ),
            "authority_ledger_audit_valid": (
                self.authority_ledger_audit_valid
            ),
            "audit_receipt_sequence": (
                self.audit_receipt_sequence
            ),
            "audit_receipt_hash": self.audit_receipt_hash,
            "checkpoint_sequence": self.checkpoint_sequence,
            "checkpoint_hash": self.checkpoint_hash,
            "checkpoint_valid": self.checkpoint_valid,
        }


class ScientificAuthorityEvidencePipeline:
    def __init__(
        self,
        *,
        authority_database_path: str | Path,
        audit_database_path: str | Path,
        checkpoint_database_path: str | Path,
    ) -> None:
        self.authority_database_path = Path(
            authority_database_path
        )
        self.audit_database_path = Path(
            audit_database_path
        )
        self.checkpoint_database_path = Path(
            checkpoint_database_path
        )

        self._ensure_parent_directories()

        self.authority_ledger = ScientificAuthorityReceiptLedger(
            self.authority_database_path
        )
        self.audit_ledger = ScientificAuthorityAuditReceiptLedger(
            self.audit_database_path
        )
        self.checkpoint_ledger = ScientificEvidenceCheckpointLedger(
            self.checkpoint_database_path
        )

    def execute(
        self,
        *,
        contract: ScientificCalculationContract,
        requested_authority: CalculationAuthority,
        evidence: AuthorityEscalationEvidence,
    ) -> ScientificAuthorityEvidencePipelineResult:
        _, authority_receipt = (
            ScientificAuthorityEscalationGuard()
            .evaluate_with_receipt(
                contract=contract,
                requested_authority=requested_authority,
                evidence=evidence,
            )
        )

        authority_record = self.authority_ledger.append(
            authority_receipt
        )

        authority_audit = (
            ScientificAuthorityLedgerIntegrityAuditor()
            .audit(self.authority_database_path)
        )

        audit_receipt = (
            ScientificAuthorityLedgerAuditReceiptBuilder()
            .build(authority_audit)
        )

        audit_record = self.audit_ledger.append(
            audit_receipt
        )

        checkpoint = ScientificEvidenceCheckpointBuilder().build(
            authority_database_path=self.authority_database_path,
            audit_database_path=self.audit_database_path,
        )

        checkpoint_record = self.checkpoint_ledger.append(
            checkpoint=checkpoint,
            authority_database_path=self.authority_database_path,
            audit_database_path=self.audit_database_path,
        )

        return ScientificAuthorityEvidencePipelineResult(
            pipeline_id=(
                SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_ID
            ),
            pipeline_version=(
                SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_VERSION
            ),
            calculation_id=contract.calculation_id,
            calculation_version=contract.calculation_version,
            requested_authority=requested_authority.value,
            decision_allowed=bool(
                authority_receipt.decision["allowed"]
            ),
            authority_receipt_sequence=(
                authority_record.sequence_number
            ),
            authority_receipt_hash=(
                authority_receipt.receipt_hash
            ),
            authority_ledger_audit_valid=(
                authority_audit.valid
            ),
            audit_receipt_sequence=(
                audit_record.sequence_number
            ),
            audit_receipt_hash=audit_receipt.receipt_hash,
            checkpoint_sequence=(
                checkpoint_record.sequence_number
            ),
            checkpoint_hash=checkpoint.checkpoint_hash,
            checkpoint_valid=checkpoint.valid,
        )

    def _ensure_parent_directories(self) -> None:
        for database_path in (
            self.authority_database_path,
            self.audit_database_path,
            self.checkpoint_database_path,
        ):
            database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
