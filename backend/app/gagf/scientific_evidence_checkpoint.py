from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.scientific_authority_audit_ledger_auditor import (
    AuthorityAuditLedgerResult,
    ScientificAuthorityAuditLedgerIntegrityAuditor,
)
from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.scientific_authority_ledger_auditor import (
    AuthorityLedgerAuditResult,
    ScientificAuthorityLedgerIntegrityAuditor,
)


SCIENTIFIC_EVIDENCE_CHECKPOINT_ID = (
    "constitutional-scientific-evidence-checkpoint"
)
SCIENTIFIC_EVIDENCE_CHECKPOINT_VERSION = "0.1.0"
SCIENTIFIC_EVIDENCE_CHECKPOINT_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class ScientificEvidenceCheckpoint:
    checkpoint_schema_version: str
    checkpoint_id: str
    checkpoint_version: str
    authority_ledger_identity: str
    audit_ledger_identity: str
    authority_audit: dict
    audit_ledger_audit: dict
    valid: bool
    checkpoint_hash: str

    def payload(self) -> dict:
        return {
            "checkpoint_schema_version": (
                self.checkpoint_schema_version
            ),
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_version": self.checkpoint_version,
            "authority_ledger_identity": (
                self.authority_ledger_identity
            ),
            "audit_ledger_identity": (
                self.audit_ledger_identity
            ),
            "authority_audit": dict(self.authority_audit),
            "audit_ledger_audit": dict(
                self.audit_ledger_audit
            ),
            "valid": self.valid,
        }

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "checkpoint_hash": self.checkpoint_hash,
        }

    def verify(self) -> bool:
        expected_hash = sha256_hex(
            canonical_json(self.payload())
        )

        return expected_hash == self.checkpoint_hash


class ScientificEvidenceCheckpointBuilder:
    def build(
        self,
        *,
        authority_database_path: str | Path,
        audit_database_path: str | Path,
    ) -> ScientificEvidenceCheckpoint:
        authority_database = Path(
            authority_database_path
        ).resolve()
        audit_database = Path(
            audit_database_path
        ).resolve()

        authority_result = (
            ScientificAuthorityLedgerIntegrityAuditor()
            .audit(authority_database)
        )
        audit_ledger_result = (
            ScientificAuthorityAuditLedgerIntegrityAuditor()
            .audit(audit_database)
        )

        return self.build_from_results(
            authority_database_path=authority_database,
            audit_database_path=audit_database,
            authority_result=authority_result,
            audit_ledger_result=audit_ledger_result,
        )

    def build_from_results(
        self,
        *,
        authority_database_path: str | Path,
        audit_database_path: str | Path,
        authority_result: AuthorityLedgerAuditResult,
        audit_ledger_result: AuthorityAuditLedgerResult,
    ) -> ScientificEvidenceCheckpoint:
        authority_identity = self._database_identity(
            authority_database_path
        )
        audit_identity = self._database_identity(
            audit_database_path
        )

        authority_audit = self._serialize_authority_audit(
            authority_result
        )
        audit_ledger_audit = self._serialize_audit_ledger_audit(
            audit_ledger_result
        )

        valid = (
            authority_result.valid
            and audit_ledger_result.valid
        )

        payload = {
            "checkpoint_schema_version": (
                SCIENTIFIC_EVIDENCE_CHECKPOINT_SCHEMA_VERSION
            ),
            "checkpoint_id": (
                SCIENTIFIC_EVIDENCE_CHECKPOINT_ID
            ),
            "checkpoint_version": (
                SCIENTIFIC_EVIDENCE_CHECKPOINT_VERSION
            ),
            "authority_ledger_identity": authority_identity,
            "audit_ledger_identity": audit_identity,
            "authority_audit": authority_audit,
            "audit_ledger_audit": audit_ledger_audit,
            "valid": valid,
        }

        checkpoint_hash = sha256_hex(
            canonical_json(payload)
        )

        return ScientificEvidenceCheckpoint(
            checkpoint_schema_version=(
                SCIENTIFIC_EVIDENCE_CHECKPOINT_SCHEMA_VERSION
            ),
            checkpoint_id=(
                SCIENTIFIC_EVIDENCE_CHECKPOINT_ID
            ),
            checkpoint_version=(
                SCIENTIFIC_EVIDENCE_CHECKPOINT_VERSION
            ),
            authority_ledger_identity=authority_identity,
            audit_ledger_identity=audit_identity,
            authority_audit=authority_audit,
            audit_ledger_audit=audit_ledger_audit,
            valid=valid,
            checkpoint_hash=checkpoint_hash,
        )

    def _database_identity(
        self,
        database_path: str | Path,
    ) -> str:
        resolved = Path(database_path).resolve()

        return sha256_hex(
            canonical_json(
                {
                    "database_path": resolved.as_posix(),
                }
            )
        )

    def _serialize_authority_audit(
        self,
        result: AuthorityLedgerAuditResult,
    ) -> dict:
        return {
            "valid": result.valid,
            "auditor_id": result.auditor_id,
            "auditor_version": result.auditor_version,
            "record_count": result.record_count,
            "checks": dict(result.checks),
            "findings": [
                finding.to_dict()
                for finding in result.findings
            ],
        }

    def _serialize_audit_ledger_audit(
        self,
        result: AuthorityAuditLedgerResult,
    ) -> dict:
        return {
            "valid": result.valid,
            "auditor_id": result.auditor_id,
            "auditor_version": result.auditor_version,
            "record_count": result.record_count,
            "checks": dict(result.checks),
            "findings": [
                finding.to_dict()
                for finding in result.findings
            ],
        }
