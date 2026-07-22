from dataclasses import dataclass

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.scientific_authority_ledger_auditor import (
    AuthorityLedgerAuditFinding,
    AuthorityLedgerAuditResult,
)


AUTHORITY_LEDGER_AUDIT_RECEIPT_ID = (
    "scientific-authority-ledger-audit-receipt"
)
AUTHORITY_LEDGER_AUDIT_RECEIPT_VERSION = "0.1.0"
AUTHORITY_LEDGER_AUDIT_RECEIPT_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class AuthorityLedgerAuditReceipt:
    receipt_schema_version: str
    receipt_id: str
    receipt_version: str
    auditor_id: str
    auditor_version: str
    valid: bool
    record_count: int
    checks: dict[str, bool]
    findings: tuple[dict, ...]
    receipt_hash: str

    def payload(self) -> dict:
        return {
            "receipt_schema_version": self.receipt_schema_version,
            "receipt_id": self.receipt_id,
            "receipt_version": self.receipt_version,
            "auditor_id": self.auditor_id,
            "auditor_version": self.auditor_version,
            "valid": self.valid,
            "record_count": self.record_count,
            "checks": dict(self.checks),
            "findings": [
                dict(finding)
                for finding in self.findings
            ],
        }

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "receipt_hash": self.receipt_hash,
        }

    def verify(self) -> bool:
        expected_hash = sha256_hex(
            canonical_json(self.payload())
        )

        return expected_hash == self.receipt_hash


class ScientificAuthorityLedgerAuditReceiptBuilder:
    def build(
        self,
        audit_result: AuthorityLedgerAuditResult,
    ) -> AuthorityLedgerAuditReceipt:
        findings = tuple(
            self._serialize_finding(finding)
            for finding in audit_result.findings
        )

        payload = {
            "receipt_schema_version": (
                AUTHORITY_LEDGER_AUDIT_RECEIPT_SCHEMA_VERSION
            ),
            "receipt_id": AUTHORITY_LEDGER_AUDIT_RECEIPT_ID,
            "receipt_version": (
                AUTHORITY_LEDGER_AUDIT_RECEIPT_VERSION
            ),
            "auditor_id": audit_result.auditor_id,
            "auditor_version": audit_result.auditor_version,
            "valid": audit_result.valid,
            "record_count": audit_result.record_count,
            "checks": dict(audit_result.checks),
            "findings": [
                dict(finding)
                for finding in findings
            ],
        }

        receipt_hash = sha256_hex(
            canonical_json(payload)
        )

        return AuthorityLedgerAuditReceipt(
            receipt_schema_version=(
                AUTHORITY_LEDGER_AUDIT_RECEIPT_SCHEMA_VERSION
            ),
            receipt_id=AUTHORITY_LEDGER_AUDIT_RECEIPT_ID,
            receipt_version=(
                AUTHORITY_LEDGER_AUDIT_RECEIPT_VERSION
            ),
            auditor_id=audit_result.auditor_id,
            auditor_version=audit_result.auditor_version,
            valid=audit_result.valid,
            record_count=audit_result.record_count,
            checks=dict(audit_result.checks),
            findings=findings,
            receipt_hash=receipt_hash,
        )

    def _serialize_finding(
        self,
        finding: AuthorityLedgerAuditFinding,
    ) -> dict:
        return {
            "code": finding.code,
            "sequence_number": finding.sequence_number,
            "receipt_hash": finding.receipt_hash,
            "message": finding.message,
        }
