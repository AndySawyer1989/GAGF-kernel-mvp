import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.scientific_authority_ledger_audit_receipt import (
    AuthorityLedgerAuditReceipt,
)


AUTHORITY_AUDIT_LEDGER_AUDITOR_ID = (
    "scientific-authority-audit-ledger-integrity-auditor"
)
AUTHORITY_AUDIT_LEDGER_AUDITOR_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class AuthorityAuditLedgerFinding:
    code: str
    sequence_number: int | None
    receipt_hash: str | None
    message: str

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "sequence_number": self.sequence_number,
            "receipt_hash": self.receipt_hash,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class AuthorityAuditLedgerResult:
    valid: bool
    auditor_id: str
    auditor_version: str
    record_count: int
    checks: dict[str, bool]
    findings: tuple[AuthorityAuditLedgerFinding, ...]

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "auditor_id": self.auditor_id,
            "auditor_version": self.auditor_version,
            "record_count": self.record_count,
            "checks": dict(self.checks),
            "findings": [
                finding.to_dict()
                for finding in self.findings
            ],
        }


class ScientificAuthorityAuditLedgerIntegrityAuditor:
    def audit(
        self,
        database_path: str | Path,
    ) -> AuthorityAuditLedgerResult:
        checks = {
            "table_present": False,
            "sequence_contiguous": False,
            "receipt_hashes_unique": False,
            "receipt_json_valid": False,
            "stored_columns_match_receipts": False,
            "all_receipt_hashes_valid": False,
        }
        findings: list[AuthorityAuditLedgerFinding] = []

        rows = self._load_rows(
            database_path=database_path,
            checks=checks,
            findings=findings,
        )

        if rows is None:
            return self._build_result(
                record_count=0,
                checks=checks,
                findings=findings,
            )

        checks["sequence_contiguous"] = (
            self._check_sequence_continuity(
                rows=rows,
                findings=findings,
            )
        )

        checks["receipt_hashes_unique"] = (
            self._check_hash_uniqueness(
                rows=rows,
                findings=findings,
            )
        )

        receipt_json_valid = True
        columns_match = True
        hashes_valid = True

        for row in rows:
            receipt = self._deserialize_receipt(
                row=row,
                findings=findings,
            )

            if receipt is None:
                receipt_json_valid = False
                columns_match = False
                hashes_valid = False
                continue

            if not self._stored_columns_match_receipt(
                row=row,
                receipt=receipt,
                findings=findings,
            ):
                columns_match = False

            if not receipt.verify():
                hashes_valid = False
                findings.append(
                    AuthorityAuditLedgerFinding(
                        code="AUDIT_RECEIPT_HASH_INVALID",
                        sequence_number=row["sequence_number"],
                        receipt_hash=row["receipt_hash"],
                        message=(
                            "Stored audit receipt failed SHA-256 "
                            "verification."
                        ),
                    )
                )

        checks["receipt_json_valid"] = receipt_json_valid
        checks["stored_columns_match_receipts"] = columns_match
        checks["all_receipt_hashes_valid"] = hashes_valid

        return self._build_result(
            record_count=len(rows),
            checks=checks,
            findings=findings,
        )

    def _load_rows(
        self,
        *,
        database_path: str | Path,
        checks: dict[str, bool],
        findings: list[AuthorityAuditLedgerFinding],
    ) -> list[sqlite3.Row] | None:
        try:
            connection = sqlite3.connect(str(database_path))
            connection.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            findings.append(
                AuthorityAuditLedgerFinding(
                    code="DATABASE_OPEN_FAILED",
                    sequence_number=None,
                    receipt_hash=None,
                    message=str(exc),
                )
            )
            return None

        try:
            table = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = 'scientific_authority_audit_receipts'
                """
            ).fetchone()

            if table is None:
                findings.append(
                    AuthorityAuditLedgerFinding(
                        code="AUDIT_LEDGER_TABLE_MISSING",
                        sequence_number=None,
                        receipt_hash=None,
                        message=(
                            "Scientific authority audit receipt "
                            "ledger table does not exist."
                        ),
                    )
                )
                return None

            checks["table_present"] = True

            return connection.execute(
                """
                SELECT
                    sequence_number,
                    receipt_hash,
                    receipt_schema_version,
                    receipt_id,
                    receipt_version,
                    auditor_id,
                    auditor_version,
                    audit_valid,
                    record_count,
                    checks_json,
                    findings_json,
                    receipt_json
                FROM scientific_authority_audit_receipts
                ORDER BY sequence_number ASC
                """
            ).fetchall()
        except sqlite3.Error as exc:
            findings.append(
                AuthorityAuditLedgerFinding(
                    code="AUDIT_LEDGER_READ_FAILED",
                    sequence_number=None,
                    receipt_hash=None,
                    message=str(exc),
                )
            )
            return None
        finally:
            connection.close()

    def _check_sequence_continuity(
        self,
        *,
        rows: list[sqlite3.Row],
        findings: list[AuthorityAuditLedgerFinding],
    ) -> bool:
        expected = list(range(1, len(rows) + 1))
        actual = [
            int(row["sequence_number"])
            for row in rows
        ]

        if actual == expected:
            return True

        findings.append(
            AuthorityAuditLedgerFinding(
                code="SEQUENCE_DISCONTINUITY",
                sequence_number=None,
                receipt_hash=None,
                message=(
                    f"Expected sequence numbers {expected}, "
                    f"but found {actual}."
                ),
            )
        )
        return False

    def _check_hash_uniqueness(
        self,
        *,
        rows: list[sqlite3.Row],
        findings: list[AuthorityAuditLedgerFinding],
    ) -> bool:
        hashes = [
            row["receipt_hash"]
            for row in rows
        ]

        if len(hashes) == len(set(hashes)):
            return True

        findings.append(
            AuthorityAuditLedgerFinding(
                code="DUPLICATE_AUDIT_RECEIPT_HASH",
                sequence_number=None,
                receipt_hash=None,
                message=(
                    "The audit receipt ledger contains duplicate "
                    "receipt hashes."
                ),
            )
        )
        return False

    def _deserialize_receipt(
        self,
        *,
        row: sqlite3.Row,
        findings: list[AuthorityAuditLedgerFinding],
    ) -> AuthorityLedgerAuditReceipt | None:
        try:
            data = json.loads(row["receipt_json"])

            return AuthorityLedgerAuditReceipt(
                receipt_schema_version=data[
                    "receipt_schema_version"
                ],
                receipt_id=data["receipt_id"],
                receipt_version=data["receipt_version"],
                auditor_id=data["auditor_id"],
                auditor_version=data["auditor_version"],
                valid=data["valid"],
                record_count=data["record_count"],
                checks=dict(data["checks"]),
                findings=tuple(
                    dict(finding)
                    for finding in data["findings"]
                ),
                receipt_hash=data["receipt_hash"],
            )
        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            findings.append(
                AuthorityAuditLedgerFinding(
                    code="INVALID_AUDIT_RECEIPT_JSON",
                    sequence_number=row["sequence_number"],
                    receipt_hash=row["receipt_hash"],
                    message=str(exc),
                )
            )
            return None

    def _stored_columns_match_receipt(
        self,
        *,
        row: sqlite3.Row,
        receipt: AuthorityLedgerAuditReceipt,
        findings: list[AuthorityAuditLedgerFinding],
    ) -> bool:
        comparisons = {
            "receipt_hash": receipt.receipt_hash,
            "receipt_schema_version": (
                receipt.receipt_schema_version
            ),
            "receipt_id": receipt.receipt_id,
            "receipt_version": receipt.receipt_version,
            "auditor_id": receipt.auditor_id,
            "auditor_version": receipt.auditor_version,
            "audit_valid": int(receipt.valid),
            "record_count": receipt.record_count,
        }

        mismatched_fields = [
            field_name
            for field_name, receipt_value in comparisons.items()
            if row[field_name] != receipt_value
        ]

        try:
            stored_checks = json.loads(row["checks_json"])
        except (json.JSONDecodeError, TypeError):
            stored_checks = None

        if stored_checks != receipt.checks:
            mismatched_fields.append("checks_json")

        try:
            findings_wrapper = json.loads(row["findings_json"])
            stored_findings = findings_wrapper["findings"]
        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
        ):
            stored_findings = None

        expected_findings = [
            dict(finding)
            for finding in receipt.findings
        ]

        if stored_findings != expected_findings:
            mismatched_fields.append("findings_json")

        if not mismatched_fields:
            return True

        findings.append(
            AuthorityAuditLedgerFinding(
                code="STORED_AUDIT_COLUMN_MISMATCH",
                sequence_number=row["sequence_number"],
                receipt_hash=row["receipt_hash"],
                message=(
                    "Stored audit-ledger columns do not match "
                    "receipt fields: "
                    + ", ".join(sorted(mismatched_fields))
                ),
            )
        )
        return False

    def _build_result(
        self,
        *,
        record_count: int,
        checks: dict[str, bool],
        findings: list[AuthorityAuditLedgerFinding],
    ) -> AuthorityAuditLedgerResult:
        return AuthorityAuditLedgerResult(
            valid=all(checks.values()),
            auditor_id=AUTHORITY_AUDIT_LEDGER_AUDITOR_ID,
            auditor_version=AUTHORITY_AUDIT_LEDGER_AUDITOR_VERSION,
            record_count=record_count,
            checks=checks,
            findings=tuple(findings),
        )
