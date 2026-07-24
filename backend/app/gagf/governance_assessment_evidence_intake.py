from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from backend.app.gagf.governance_assessment_domain import (
    EvidenceSourceKind,
    EvidenceSourceReference,
)
from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)


ASSESSMENT_EVIDENCE_SCHEMA_VERSION = "1.0.0"
REQUIRED_CSV_COLUMNS = (
    "event_id",
    "event_type",
    "occurred_at",
)


class AssessmentEvidenceIntakeError(ValueError):
    """Raised when assessment evidence cannot be accepted."""


def require_text(value: str, field_name: str) -> str:
    normalized = value.strip()

    if not normalized:
        raise AssessmentEvidenceIntakeError(
            f"{field_name} must not be empty"
        )

    return normalized


def parse_timestamp(value: str) -> datetime:
    normalized = require_text(value, "occurred_at")

    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AssessmentEvidenceIntakeError(
            "occurred_at must be an ISO-8601 timestamp"
        ) from exc

    if parsed.tzinfo is None:
        raise AssessmentEvidenceIntakeError(
            "occurred_at must include a timezone"
        )

    return parsed.astimezone(timezone.utc)


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class AssessmentEvidenceRecord:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    source_id: str
    event_id: str
    event_type: str
    occurred_at: datetime
    attributes: dict[str, str]
    row_number: int
    evidence_hash: str
    schema_version: str = ASSESSMENT_EVIDENCE_SCHEMA_VERSION

    @property
    def hierarchy_key(self) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "source_id": self.source_id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "attributes": dict(self.attributes),
            "row_number": self.row_number,
            "evidence_hash": self.evidence_hash,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class RejectedEvidenceRow:
    row_number: int
    event_id: str | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_number": self.row_number,
            "event_id": self.event_id,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class AssessmentEvidenceIntakeResult:
    source: EvidenceSourceReference
    hierarchy_key: str
    accepted_records: tuple[AssessmentEvidenceRecord, ...]
    rejected_rows: tuple[RejectedEvidenceRow, ...]
    total_rows: int
    intake_hash: str

    @property
    def accepted_count(self) -> int:
        return len(self.accepted_records)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected_rows)

    @property
    def valid(self) -> bool:
        return self.rejected_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": {
                "source_id": self.source.source_id,
                "kind": self.source.kind.value,
                "display_name": self.source.display_name,
                "source_location": self.source.source_location,
            },
            "hierarchy_key": self.hierarchy_key,
            "accepted_records": [
                record.to_dict()
                for record in self.accepted_records
            ],
            "rejected_rows": [
                row.to_dict()
                for row in self.rejected_rows
            ],
            "total_rows": self.total_rows,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "valid": self.valid,
            "intake_hash": self.intake_hash,
        }


class GovernanceAssessmentEvidenceIntakeService:
    def ingest_csv(
        self,
        *,
        context: CommercialHierarchyContext,
        source: EvidenceSourceReference,
        csv_text: str,
    ) -> AssessmentEvidenceIntakeResult:
        if context.engagement_id is None:
            raise AssessmentEvidenceIntakeError(
                "evidence intake requires engagement_id"
            )

        if context.assessment_id is None:
            raise AssessmentEvidenceIntakeError(
                "evidence intake requires assessment_id"
            )

        if source.kind is not EvidenceSourceKind.CSV:
            raise AssessmentEvidenceIntakeError(
                "ingest_csv requires a CSV evidence source"
            )

        if not csv_text.strip():
            raise AssessmentEvidenceIntakeError(
                "csv_text must not be empty"
            )

        reader = csv.DictReader(io.StringIO(csv_text))

        if reader.fieldnames is None:
            raise AssessmentEvidenceIntakeError(
                "CSV header is required"
            )

        normalized_headers = tuple(
            header.strip()
            for header in reader.fieldnames
            if header is not None
        )

        missing_columns = tuple(
            column
            for column in REQUIRED_CSV_COLUMNS
            if column not in normalized_headers
        )

        if missing_columns:
            raise AssessmentEvidenceIntakeError(
                "CSV is missing required columns: "
                + ", ".join(missing_columns)
            )

        accepted: list[AssessmentEvidenceRecord] = []
        rejected: list[RejectedEvidenceRow] = []
        seen_event_ids: set[str] = set()
        total_rows = 0

        for row_number, row in enumerate(reader, start=2):
            total_rows += 1

            raw_event_id = row.get("event_id")
            event_id = (
                raw_event_id.strip()
                if isinstance(raw_event_id, str)
                else ""
            )

            try:
                record = self._build_record(
                    context=context,
                    source=source,
                    row=row,
                    row_number=row_number,
                    seen_event_ids=seen_event_ids,
                )
            except AssessmentEvidenceIntakeError as exc:
                rejected.append(
                    RejectedEvidenceRow(
                        row_number=row_number,
                        event_id=event_id or None,
                        reason=str(exc),
                    )
                )
                continue

            accepted.append(record)
            seen_event_ids.add(record.event_id)

        intake_payload = {
            "hierarchy_key": context.hierarchy_key,
            "source_id": source.source_id,
            "accepted_hashes": [
                record.evidence_hash
                for record in accepted
            ],
            "rejected_rows": [
                row.to_dict()
                for row in rejected
            ],
            "total_rows": total_rows,
        }

        return AssessmentEvidenceIntakeResult(
            source=source,
            hierarchy_key=context.hierarchy_key,
            accepted_records=tuple(accepted),
            rejected_rows=tuple(rejected),
            total_rows=total_rows,
            intake_hash=sha256_text(
                canonical_json(intake_payload)
            ),
        )

    def _build_record(
        self,
        *,
        context: CommercialHierarchyContext,
        source: EvidenceSourceReference,
        row: dict[str, str | None],
        row_number: int,
        seen_event_ids: set[str],
    ) -> AssessmentEvidenceRecord:
        event_id = require_text(
            row.get("event_id") or "",
            "event_id",
        )

        if event_id in seen_event_ids:
            raise AssessmentEvidenceIntakeError(
                f"duplicate event_id: {event_id}"
            )

        event_type = require_text(
            row.get("event_type") or "",
            "event_type",
        )
        occurred_at = parse_timestamp(
            row.get("occurred_at") or ""
        )

        attributes = {
            key.strip(): value.strip()
            for key, value in row.items()
            if key is not None
            and key.strip() not in REQUIRED_CSV_COLUMNS
            and value is not None
            and value.strip()
        }

        canonical_payload = {
            "tenant_id": context.tenant_id,
            "client_id": context.client_id,
            "engagement_id": context.engagement_id,
            "assessment_id": context.assessment_id,
            "source_id": source.source_id,
            "event_id": event_id,
            "event_type": event_type,
            "occurred_at": occurred_at.isoformat(),
            "attributes": attributes,
            "schema_version": ASSESSMENT_EVIDENCE_SCHEMA_VERSION,
        }

        return AssessmentEvidenceRecord(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=context.engagement_id,
            assessment_id=context.assessment_id,
            source_id=source.source_id,
            event_id=event_id,
            event_type=event_type,
            occurred_at=occurred_at,
            attributes=attributes,
            row_number=row_number,
            evidence_hash=sha256_text(
                canonical_json(canonical_payload)
            ),
        )
