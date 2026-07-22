import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.scientific_authority_guard import (
    AuthorityDecisionReceipt,
)
from backend.app.gagf.scientific_authority_replay_verifier import (
    ScientificAuthorityReceiptReplayVerifier,
)


AUTHORITY_LEDGER_AUDITOR_ID = (
    "scientific-authority-ledger-integrity-auditor"
)
AUTHORITY_LEDGER_AUDITOR_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class AuthorityLedgerAuditFinding:
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
class AuthorityLedgerAuditResult:
    valid: bool
    auditor_id: str
    auditor_version: str
    record_count: int
    checks: dict[str, bool]
    findings: tuple[AuthorityLedgerAuditFinding, ...]

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


class ScientificAuthorityLedgerIntegrityAuditor:
    def audit(
        self,
        database_path: str | Path,
    ) -> AuthorityLedgerAuditResult:
        findings: list[AuthorityLedgerAuditFinding] = []

        checks = {
            "table_present": False,
            "sequence_contiguous": False,
            "receipt_hashes_unique": False,
            "receipt_json_valid": False,
            "stored_columns_match_receipts": False,
            "all_receipts_replay_valid": False,
        }

        rows = self._load_rows(
            database_path=database_path,
            checks=checks,
            findings=findings,
        )

        if rows is None:
            return self._result(
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

        json_valid = True
        columns_match = True
        replay_valid = True

        for row in rows:
            receipt = self._deserialize_receipt(
                row=row,
                findings=findings,
            )

            if receipt is None:
                json_valid = False
                columns_match = False
                replay_valid = False
                continue

            if not self._stored_columns_match_receipt(
                row=row,
                receipt=receipt,
                findings=findings,
            ):
                columns_match = False

            replay_result = (
                ScientificAuthorityReceiptReplayVerifier()
                .verify(receipt)
            )

            if not replay_result.valid:
                replay_valid = False
                findings.append(
                    AuthorityLedgerAuditFinding(
                        code="REPLAY_VERIFICATION_FAILED",
                        sequence_number=row["sequence_number"],
                        receipt_hash=row["receipt_hash"],
                        message=(
                            "Stored receipt failed deterministic "
                            "replay verification: "
                            + "; ".join(replay_result.errors)
                        ),
                    )
                )

        checks["receipt_json_valid"] = json_valid
        checks["stored_columns_match_receipts"] = columns_match
        checks["all_receipts_replay_valid"] = replay_valid

        return self._result(
            record_count=len(rows),
            checks=checks,
            findings=findings,
        )

    def _load_rows(
        self,
        *,
        database_path: str | Path,
        checks: dict[str, bool],
        findings: list[AuthorityLedgerAuditFinding],
    ) -> list[sqlite3.Row] | None:
        try:
            connection = sqlite3.connect(str(database_path))
            connection.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            findings.append(
                AuthorityLedgerAuditFinding(
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
                  AND name = 'scientific_authority_receipts'
                """
            ).fetchone()

            if table is None:
                findings.append(
                    AuthorityLedgerAuditFinding(
                        code="LEDGER_TABLE_MISSING",
                        sequence_number=None,
                        receipt_hash=None,
                        message=(
                            "Scientific authority receipt ledger "
                            "table does not exist."
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
                    policy_id,
                    policy_version,
                    calculation_id,
                    calculation_version,
                    current_authority,
                    requested_authority,
                    evidence_json,
                    decision_json,
                    receipt_json
                FROM scientific_authority_receipts
                ORDER BY sequence_number ASC
                """
            ).fetchall()
        except sqlite3.Error as exc:
            findings.append(
                AuthorityLedgerAuditFinding(
                    code="LEDGER_READ_FAILED",
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
        findings: list[AuthorityLedgerAuditFinding],
    ) -> bool:
        expected = list(range(1, len(rows) + 1))
        actual = [
            int(row["sequence_number"])
            for row in rows
        ]

        if actual == expected:
            return True

        findings.append(
            AuthorityLedgerAuditFinding(
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
        findings: list[AuthorityLedgerAuditFinding],
    ) -> bool:
        hashes = [
            row["receipt_hash"]
            for row in rows
        ]

        if len(hashes) == len(set(hashes)):
            return True

        findings.append(
            AuthorityLedgerAuditFinding(
                code="DUPLICATE_RECEIPT_HASH",
                sequence_number=None,
                receipt_hash=None,
                message=(
                    "The ledger contains duplicate receipt hashes."
                ),
            )
        )
        return False

    def _deserialize_receipt(
        self,
        *,
        row: sqlite3.Row,
        findings: list[AuthorityLedgerAuditFinding],
    ) -> AuthorityDecisionReceipt | None:
        try:
            data = json.loads(row["receipt_json"])

            return AuthorityDecisionReceipt(
                receipt_schema_version=data[
                    "receipt_schema_version"
                ],
                policy_id=data["policy_id"],
                policy_version=data["policy_version"],
                calculation_id=data["calculation_id"],
                calculation_version=data["calculation_version"],
                current_authority=data["current_authority"],
                requested_authority=data["requested_authority"],
                evidence=dict(data["evidence"]),
                decision=dict(data["decision"]),
                receipt_hash=data["receipt_hash"],
            )
        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            findings.append(
                AuthorityLedgerAuditFinding(
                    code="INVALID_RECEIPT_JSON",
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
        receipt: AuthorityDecisionReceipt,
        findings: list[AuthorityLedgerAuditFinding],
    ) -> bool:
        comparisons = {
            "receipt_hash": receipt.receipt_hash,
            "receipt_schema_version": (
                receipt.receipt_schema_version
            ),
            "policy_id": receipt.policy_id,
            "policy_version": receipt.policy_version,
            "calculation_id": receipt.calculation_id,
            "calculation_version": receipt.calculation_version,
            "current_authority": receipt.current_authority,
            "requested_authority": receipt.requested_authority,
        }

        mismatched_fields = [
            field_name
            for field_name, receipt_value in comparisons.items()
            if row[field_name] != receipt_value
        ]

        try:
            stored_evidence = json.loads(row["evidence_json"])
        except (json.JSONDecodeError, TypeError):
            stored_evidence = None

        if stored_evidence != receipt.evidence:
            mismatched_fields.append("evidence_json")

        try:
            stored_decision = json.loads(row["decision_json"])
        except (json.JSONDecodeError, TypeError):
            stored_decision = None

        if stored_decision != receipt.decision:
            mismatched_fields.append("decision_json")

        if not mismatched_fields:
            return True

        findings.append(
            AuthorityLedgerAuditFinding(
                code="STORED_COLUMN_MISMATCH",
                sequence_number=row["sequence_number"],
                receipt_hash=row["receipt_hash"],
                message=(
                    "Stored columns do not match receipt fields: "
                    + ", ".join(sorted(mismatched_fields))
                ),
            )
        )
        return False

    def _result(
        self,
        *,
        record_count: int,
        checks: dict[str, bool],
        findings: list[AuthorityLedgerAuditFinding],
    ) -> AuthorityLedgerAuditResult:
        return AuthorityLedgerAuditResult(
            valid=all(checks.values()),
            auditor_id=AUTHORITY_LEDGER_AUDITOR_ID,
            auditor_version=AUTHORITY_LEDGER_AUDITOR_VERSION,
            record_count=record_count,
            checks=checks,
            findings=tuple(findings),
        )
