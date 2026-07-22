from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.scientific_authority_audit_receipt_ledger import (
    ScientificAuthorityAuditReceiptLedger,
)
from backend.app.gagf.scientific_authority_evidence_pipeline import (
    SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_ID,
    SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_VERSION,
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
    get_calculation_contract,
)
from backend.app.gagf.scientific_evidence_checkpoint_ledger import (
    ScientificEvidenceCheckpointLedger,
)
from backend.app.gagf.scientific_evidence_checkpoint_replay_verifier import (
    ScientificEvidenceCheckpointReplayVerifier,
)
from backend.app.gagf.scientific_pipeline_execution_receipt import (
    SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_ID,
    SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_SCHEMA_VERSION,
    SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_VERSION,
    ScientificPipelineExecutionReceipt,
)


SCIENTIFIC_PIPELINE_EXECUTION_REPLAY_VERIFIER_ID = (
    "scientific-pipeline-execution-replay-verifier"
)
SCIENTIFIC_PIPELINE_EXECUTION_REPLAY_VERIFIER_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class ScientificPipelineExecutionReplayResult:
    valid: bool
    verifier_id: str
    verifier_version: str
    execution_receipt_hash: str
    checks: dict[str, bool]
    errors: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "verifier_id": self.verifier_id,
            "verifier_version": self.verifier_version,
            "execution_receipt_hash": (
                self.execution_receipt_hash
            ),
            "checks": dict(self.checks),
            "errors": list(self.errors),
        }


class ScientificPipelineExecutionReplayVerifier:
    def verify(
        self,
        *,
        receipt: ScientificPipelineExecutionReceipt,
        authority_database_path: str | Path,
        audit_database_path: str | Path,
        checkpoint_database_path: str | Path,
    ) -> ScientificPipelineExecutionReplayResult:
        checks = {
            "execution_receipt_hash_valid": receipt.verify(),
            "execution_receipt_schema_supported": (
                receipt.receipt_schema_version
                == SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_SCHEMA_VERSION
            ),
            "execution_receipt_identity_supported": (
                receipt.receipt_id
                == SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_ID
            ),
            "execution_receipt_version_supported": (
                receipt.receipt_version
                == SCIENTIFIC_PIPELINE_EXECUTION_RECEIPT_VERSION
            ),
            "pipeline_identity_supported": (
                receipt.pipeline_id
                == SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_ID
            ),
            "pipeline_version_supported": (
                receipt.pipeline_version
                == SCIENTIFIC_AUTHORITY_EVIDENCE_PIPELINE_VERSION
            ),
            "calculation_contract_present": False,
            "calculation_version_matches_registry": False,
            "authority_receipt_present": False,
            "authority_receipt_sequence_matches": False,
            "authority_receipt_hash_valid": False,
            "authority_receipt_contract_matches": False,
            "authority_request_matches": False,
            "authority_evidence_matches": False,
            "authority_decision_matches": False,
            "authority_ledger_audit_matches": False,
            "audit_receipt_present": False,
            "audit_receipt_sequence_matches": False,
            "audit_receipt_hash_valid": False,
            "audit_receipt_matches_current_audit": False,
            "checkpoint_present": False,
            "checkpoint_sequence_matches": False,
            "checkpoint_hash_valid": False,
            "checkpoint_validity_matches": False,
            "checkpoint_replay_valid": False,
        }
        errors: list[str] = []

        self._record_initial_errors(
            checks=checks,
            errors=errors,
        )

        contract = self._resolve_contract(
            receipt=receipt,
            checks=checks,
            errors=errors,
        )

        authority_ledger = ScientificAuthorityReceiptLedger(
            authority_database_path
        )
        audit_ledger = ScientificAuthorityAuditReceiptLedger(
            audit_database_path
        )
        checkpoint_ledger = ScientificEvidenceCheckpointLedger(
            checkpoint_database_path
        )

        authority_record = authority_ledger.get_by_hash(
            receipt.authority_receipt_hash
        )

        if authority_record is None:
            errors.append(
                "Authority receipt is missing from its ledger."
            )
        else:
            checks["authority_receipt_present"] = True

            checks["authority_receipt_sequence_matches"] = (
                authority_record.sequence_number
                == receipt.authority_receipt_sequence
            )
            if not checks[
                "authority_receipt_sequence_matches"
            ]:
                errors.append(
                    "Authority receipt sequence does not match "
                    "the execution receipt."
                )

            authority_receipt = authority_record.receipt

            checks["authority_receipt_hash_valid"] = (
                authority_receipt.verify()
            )
            if not checks["authority_receipt_hash_valid"]:
                errors.append(
                    "Authority receipt failed hash verification."
                )

            checks["authority_receipt_contract_matches"] = (
                authority_receipt.calculation_id
                == receipt.calculation_id
                and authority_receipt.calculation_version
                == receipt.calculation_version
            )
            if not checks[
                "authority_receipt_contract_matches"
            ]:
                errors.append(
                    "Authority receipt calculation contract does "
                    "not match the execution receipt."
                )

            checks["authority_request_matches"] = (
                authority_receipt.requested_authority
                == receipt.requested_authority
            )
            if not checks["authority_request_matches"]:
                errors.append(
                    "Authority request does not match the "
                    "execution receipt."
                )

            checks["authority_evidence_matches"] = (
                authority_receipt.evidence
                == receipt.evidence
            )
            if not checks["authority_evidence_matches"]:
                errors.append(
                    "Authority evidence does not match the "
                    "execution receipt."
                )

            checks["authority_decision_matches"] = (
                bool(authority_receipt.decision["allowed"])
                == receipt.decision_allowed
            )
            if not checks["authority_decision_matches"]:
                errors.append(
                    "Authority decision does not match the "
                    "execution receipt."
                )

        current_authority_audit = (
            ScientificAuthorityLedgerIntegrityAuditor()
            .audit(authority_database_path)
        )

        checks["authority_ledger_audit_matches"] = (
            current_authority_audit.valid
            == receipt.authority_ledger_audit_valid
        )
        if not checks["authority_ledger_audit_matches"]:
            errors.append(
                "Current authority-ledger audit validity does not "
                "match the execution receipt."
            )

        audit_record = audit_ledger.get_by_hash(
            receipt.audit_receipt_hash
        )

        if audit_record is None:
            errors.append(
                "Audit receipt is missing from its ledger."
            )
        else:
            checks["audit_receipt_present"] = True

            checks["audit_receipt_sequence_matches"] = (
                audit_record.sequence_number
                == receipt.audit_receipt_sequence
            )
            if not checks["audit_receipt_sequence_matches"]:
                errors.append(
                    "Audit receipt sequence does not match the "
                    "execution receipt."
                )

            audit_receipt = audit_record.receipt

            checks["audit_receipt_hash_valid"] = (
                audit_receipt.verify()
            )
            if not checks["audit_receipt_hash_valid"]:
                errors.append(
                    "Audit receipt failed hash verification."
                )

            expected_audit_receipt = (
                ScientificAuthorityLedgerAuditReceiptBuilder()
                .build(current_authority_audit)
            )

            checks["audit_receipt_matches_current_audit"] = (
                audit_receipt == expected_audit_receipt
            )
            if not checks[
                "audit_receipt_matches_current_audit"
            ]:
                errors.append(
                    "Stored audit receipt does not match the "
                    "current deterministic authority-ledger audit."
                )

        checkpoint_record = checkpoint_ledger.get_by_hash(
            receipt.checkpoint_hash
        )

        if checkpoint_record is None:
            errors.append(
                "Constitutional checkpoint is missing from its "
                "ledger."
            )
        else:
            checks["checkpoint_present"] = True

            checks["checkpoint_sequence_matches"] = (
                checkpoint_record.sequence_number
                == receipt.checkpoint_sequence
            )
            if not checks["checkpoint_sequence_matches"]:
                errors.append(
                    "Checkpoint sequence does not match the "
                    "execution receipt."
                )

            checkpoint = checkpoint_record.checkpoint

            checks["checkpoint_hash_valid"] = (
                checkpoint.verify()
            )
            if not checks["checkpoint_hash_valid"]:
                errors.append(
                    "Checkpoint failed hash verification."
                )

            checks["checkpoint_validity_matches"] = (
                checkpoint.valid
                == receipt.checkpoint_valid
            )
            if not checks["checkpoint_validity_matches"]:
                errors.append(
                    "Checkpoint validity does not match the "
                    "execution receipt."
                )

            checkpoint_replay = (
                ScientificEvidenceCheckpointReplayVerifier()
                .verify(
                    checkpoint=checkpoint,
                    authority_database_path=(
                        authority_database_path
                    ),
                    audit_database_path=audit_database_path,
                )
            )

            checks["checkpoint_replay_valid"] = (
                checkpoint_replay.valid
            )
            if not checks["checkpoint_replay_valid"]:
                errors.append(
                    "Checkpoint failed replay against the current "
                    "authority and audit ledgers: "
                    + "; ".join(checkpoint_replay.errors)
                )

        if contract is None:
            checks["calculation_version_matches_registry"] = (
                False
            )

        return ScientificPipelineExecutionReplayResult(
            valid=all(checks.values()),
            verifier_id=(
                SCIENTIFIC_PIPELINE_EXECUTION_REPLAY_VERIFIER_ID
            ),
            verifier_version=(
                SCIENTIFIC_PIPELINE_EXECUTION_REPLAY_VERIFIER_VERSION
            ),
            execution_receipt_hash=receipt.receipt_hash,
            checks=checks,
            errors=tuple(errors),
        )

    def _resolve_contract(
        self,
        *,
        receipt: ScientificPipelineExecutionReceipt,
        checks: dict[str, bool],
        errors: list[str],
    ):
        try:
            contract = get_calculation_contract(
                receipt.calculation_id
            )
        except KeyError:
            errors.append(
                "Calculation contract is not present in the "
                "scientific contract registry."
            )
            return None

        checks["calculation_contract_present"] = True
        checks["calculation_version_matches_registry"] = (
            contract.calculation_version
            == receipt.calculation_version
        )

        if not checks[
            "calculation_version_matches_registry"
        ]:
            errors.append(
                "Execution receipt calculation version does not "
                "match the scientific contract registry."
            )

        return contract

    def _record_initial_errors(
        self,
        *,
        checks: dict[str, bool],
        errors: list[str],
    ) -> None:
        messages = {
            "execution_receipt_hash_valid": (
                "Execution receipt failed SHA-256 verification."
            ),
            "execution_receipt_schema_supported": (
                "Execution receipt schema version is unsupported."
            ),
            "execution_receipt_identity_supported": (
                "Execution receipt identity is unsupported."
            ),
            "execution_receipt_version_supported": (
                "Execution receipt version is unsupported."
            ),
            "pipeline_identity_supported": (
                "Pipeline identity is unsupported."
            ),
            "pipeline_version_supported": (
                "Pipeline version is unsupported."
            ),
        }

        for check_name, message in messages.items():
            if not checks[check_name]:
                errors.append(message)
