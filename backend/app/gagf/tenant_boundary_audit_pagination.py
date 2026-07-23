from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.tenant_boundary_audit_query import (
    TenantBoundaryAuditEvidenceQueryService,
    TenantPublicBoundaryAuditRecord,
)


TENANT_BOUNDARY_AUDIT_PAGINATION_SERVICE_ID = (
    "tenant-boundary-audit-pagination-service"
)
TENANT_BOUNDARY_AUDIT_PAGINATION_SERVICE_VERSION = "0.2.0"

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


class TenantBoundaryAuditCursorError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TenantBoundaryAuditCursor:
    position: int
    snapshot_sequence: int


@dataclass(frozen=True, slots=True)
class TenantBoundaryAuditPage:
    service_id: str
    service_version: str
    tenant_id: str
    page_size: int
    returned_count: int
    snapshot_sequence: int
    records: tuple[
        TenantPublicBoundaryAuditRecord,
        ...,
    ]
    next_cursor: str | None
    has_more: bool
    page_hash: str

    def payload(self) -> dict:
        return {
            "service_id": self.service_id,
            "service_version": self.service_version,
            "tenant_id": self.tenant_id,
            "page_size": self.page_size,
            "returned_count": self.returned_count,
            "snapshot_sequence": (
                self.snapshot_sequence
            ),
            "records": [
                record.to_dict()
                for record in self.records
            ],
            "next_cursor": self.next_cursor,
            "has_more": self.has_more,
        }

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "page_hash": self.page_hash,
        }

    def verify(self) -> bool:
        if not all(
            record.verify()
            for record in self.records
        ):
            return False

        return self.page_hash == sha256_hex(
            canonical_json(self.payload())
        )


class TenantBoundaryAuditPaginationService:
    def __init__(
        self,
        *,
        database_path: str | Path,
    ) -> None:
        self.query_service = (
            TenantBoundaryAuditEvidenceQueryService(
                database_path=database_path
            )
        )

    def list_page(
        self,
        *,
        tenant_id: str,
        page_size: int = DEFAULT_PAGE_SIZE,
        cursor: str | None = None,
    ) -> TenantBoundaryAuditPage:
        normalized_tenant_id = tenant_id.strip()

        if not normalized_tenant_id:
            raise ValueError(
                "tenant_id must not be empty."
            )

        if page_size < 1:
            raise ValueError(
                "page_size must be at least 1."
            )

        if page_size > MAX_PAGE_SIZE:
            raise ValueError(
                f"page_size must not exceed {MAX_PAGE_SIZE}."
            )

        query_result = (
            self.query_service.list_for_tenant(
                tenant_id=normalized_tenant_id
            )
        )

        if cursor is None:
            cursor_state = TenantBoundaryAuditCursor(
                position=0,
                snapshot_sequence=(
                    query_result.records[-1]
                    .tenant_sequence_number
                    if query_result.records
                    else 0
                ),
            )
        else:
            cursor_state = self._decode_cursor(
                tenant_id=normalized_tenant_id,
                cursor=cursor,
            )

        eligible_records = tuple(
            record
            for record in query_result.records
            if (
                record.tenant_sequence_number
                > cursor_state.position
                and record.tenant_sequence_number
                <= cursor_state.snapshot_sequence
            )
        )

        selected_records = eligible_records[
            :page_size
        ]

        has_more = (
            len(eligible_records)
            > len(selected_records)
        )

        next_cursor = None

        if has_more and selected_records:
            next_cursor = self._encode_cursor(
                tenant_id=normalized_tenant_id,
                position=(
                    selected_records[-1]
                    .tenant_sequence_number
                ),
                snapshot_sequence=(
                    cursor_state.snapshot_sequence
                ),
            )

        payload = {
            "service_id": (
                TENANT_BOUNDARY_AUDIT_PAGINATION_SERVICE_ID
            ),
            "service_version": (
                TENANT_BOUNDARY_AUDIT_PAGINATION_SERVICE_VERSION
            ),
            "tenant_id": normalized_tenant_id,
            "page_size": page_size,
            "returned_count": len(
                selected_records
            ),
            "snapshot_sequence": (
                cursor_state.snapshot_sequence
            ),
            "records": [
                record.to_dict()
                for record in selected_records
            ],
            "next_cursor": next_cursor,
            "has_more": has_more,
        }

        return TenantBoundaryAuditPage(
            service_id=(
                TENANT_BOUNDARY_AUDIT_PAGINATION_SERVICE_ID
            ),
            service_version=(
                TENANT_BOUNDARY_AUDIT_PAGINATION_SERVICE_VERSION
            ),
            tenant_id=normalized_tenant_id,
            page_size=page_size,
            returned_count=len(
                selected_records
            ),
            snapshot_sequence=(
                cursor_state.snapshot_sequence
            ),
            records=selected_records,
            next_cursor=next_cursor,
            has_more=has_more,
            page_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    def _encode_cursor(
        self,
        *,
        tenant_id: str,
        position: int,
        snapshot_sequence: int,
    ) -> str:
        payload = {
            "cursor_id": (
                "tenant-boundary-audit-page-cursor"
            ),
            "cursor_version": "2.0.0",
            "tenant_id": tenant_id,
            "position": position,
            "snapshot_sequence": snapshot_sequence,
        }

        cursor_hash = sha256_hex(
            canonical_json(payload)
        )

        return (
            f"{cursor_hash}."
            f"{position}."
            f"{snapshot_sequence}"
        )

    def _decode_cursor(
        self,
        *,
        tenant_id: str,
        cursor: str,
    ) -> TenantBoundaryAuditCursor:
        normalized_cursor = cursor.strip()

        if not normalized_cursor:
            raise TenantBoundaryAuditCursorError(
                "cursor must not be empty."
            )

        parts = normalized_cursor.split(".")

        if len(parts) != 3:
            raise TenantBoundaryAuditCursorError(
                "cursor format is invalid."
            )

        _, position_text, snapshot_text = parts

        try:
            position = int(position_text)
            snapshot_sequence = int(
                snapshot_text
            )
        except ValueError as exc:
            raise TenantBoundaryAuditCursorError(
                "cursor sequence is invalid."
            ) from exc

        if position < 1:
            raise TenantBoundaryAuditCursorError(
                "cursor position must be positive."
            )

        if snapshot_sequence < position:
            raise TenantBoundaryAuditCursorError(
                "cursor snapshot is invalid."
            )

        expected_cursor = self._encode_cursor(
            tenant_id=tenant_id,
            position=position,
            snapshot_sequence=snapshot_sequence,
        )

        if expected_cursor != normalized_cursor:
            raise TenantBoundaryAuditCursorError(
                "cursor verification failed."
            )

        return TenantBoundaryAuditCursor(
            position=position,
            snapshot_sequence=snapshot_sequence,
        )
