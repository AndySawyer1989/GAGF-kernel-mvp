from dataclasses import dataclass
from pathlib import Path

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.tenant_public_boundary_audit_ledger import (
    TenantPublicBoundaryAuditLedger,
    TenantPublicBoundaryAuditRecord,
)


TENANT_BOUNDARY_AUDIT_QUERY_SERVICE_ID = (
    "tenant-boundary-audit-evidence-query-service"
)
TENANT_BOUNDARY_AUDIT_QUERY_SERVICE_VERSION = "0.1.0"

TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_ID = (
    "tenant-public-boundary-audit-record"
)
TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_VERSION = "0.1.0"
TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class TenantPublicBoundaryAuditRecord:
    schema_version: str
    view_id: str
    view_version: str
    tenant_id: str
    public_record_id: str
    tenant_sequence_number: int
    response_kind: str
    released: bool
    audit_valid: bool
    violation_count: int
    view_hash: str

    def payload(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "view_id": self.view_id,
            "view_version": self.view_version,
            "tenant_id": self.tenant_id,
            "public_record_id": self.public_record_id,
            "tenant_sequence_number": (
                self.tenant_sequence_number
            ),
            "response_kind": self.response_kind,
            "released": self.released,
            "audit_valid": self.audit_valid,
            "violation_count": self.violation_count,
        }

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "view_hash": self.view_hash,
        }

    def verify(self) -> bool:
        return self.view_hash == sha256_hex(
            canonical_json(self.payload())
        )


@dataclass(frozen=True, slots=True)
class TenantBoundaryAuditQueryResult:
    service_id: str
    service_version: str
    tenant_id: str
    record_count: int
    records: tuple[
        TenantPublicBoundaryAuditRecord,
        ...,
    ]
    result_hash: str

    def payload(self) -> dict:
        return {
            "service_id": self.service_id,
            "service_version": self.service_version,
            "tenant_id": self.tenant_id,
            "record_count": self.record_count,
            "records": [
                record.to_dict()
                for record in self.records
            ],
        }

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "result_hash": self.result_hash,
        }

    def verify(self) -> bool:
        if not all(
            record.verify()
            for record in self.records
        ):
            return False

        return self.result_hash == sha256_hex(
            canonical_json(self.payload())
        )


class TenantBoundaryAuditEvidenceQueryService:
    def __init__(
        self,
        *,
        database_path: str | Path,
    ) -> None:
        self.ledger = TenantPublicBoundaryAuditLedger(
            database_path
        )

    def list_for_tenant(
        self,
        *,
        tenant_id: str,
    ) -> TenantBoundaryAuditQueryResult:
        normalized_tenant_id = tenant_id.strip()

        if not normalized_tenant_id:
            raise ValueError(
                "tenant_id must not be empty."
            )

        internal_records = self.ledger.list_records(
            tenant_id=normalized_tenant_id
        )

        public_records = tuple(
            self._project_record(
                record=record,
                tenant_sequence_number=index,
            )
            for index, record in enumerate(
                internal_records,
                start=1,
            )
        )

        payload = {
            "service_id": (
                TENANT_BOUNDARY_AUDIT_QUERY_SERVICE_ID
            ),
            "service_version": (
                TENANT_BOUNDARY_AUDIT_QUERY_SERVICE_VERSION
            ),
            "tenant_id": normalized_tenant_id,
            "record_count": len(public_records),
            "records": [
                record.to_dict()
                for record in public_records
            ],
        }

        return TenantBoundaryAuditQueryResult(
            service_id=(
                TENANT_BOUNDARY_AUDIT_QUERY_SERVICE_ID
            ),
            service_version=(
                TENANT_BOUNDARY_AUDIT_QUERY_SERVICE_VERSION
            ),
            tenant_id=normalized_tenant_id,
            record_count=len(public_records),
            records=public_records,
            result_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    def get_for_tenant(
        self,
        *,
        tenant_id: str,
        public_record_id: str,
    ) -> TenantPublicBoundaryAuditRecord | None:
        normalized_public_record_id = (
            public_record_id.strip()
        )

        if not normalized_public_record_id:
            raise ValueError(
                "public_record_id must not be empty."
            )

        result = self.list_for_tenant(
            tenant_id=tenant_id
        )

        for record in result.records:
            if (
                record.public_record_id
                == normalized_public_record_id
            ):
                return record

        return None

    def _project_record(
        self,
        *,
        record: TenantPublicBoundaryAuditRecord,
        tenant_sequence_number: int,
    ) -> TenantPublicBoundaryAuditRecord:
        public_record_id = self._derive_public_record_id(
            record=record
        )

        payload = {
            "schema_version": (
                TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_SCHEMA_VERSION
            ),
            "view_id": (
                TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_ID
            ),
            "view_version": (
                TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_VERSION
            ),
            "tenant_id": record.tenant_id,
            "public_record_id": public_record_id,
            "tenant_sequence_number": (
                tenant_sequence_number
            ),
            "response_kind": record.response_kind,
            "released": record.released,
            "audit_valid": record.audit_valid,
            "violation_count": record.violation_count,
        }

        return TenantPublicBoundaryAuditRecord(
            schema_version=(
                TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_SCHEMA_VERSION
            ),
            view_id=(
                TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_ID
            ),
            view_version=(
                TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_VERSION
            ),
            tenant_id=record.tenant_id,
            public_record_id=public_record_id,
            tenant_sequence_number=(
                tenant_sequence_number
            ),
            response_kind=record.response_kind,
            released=record.released,
            audit_valid=record.audit_valid,
            violation_count=record.violation_count,
            view_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    def _derive_public_record_id(
        self,
        *,
        record: TenantPublicBoundaryAuditRecord,
    ) -> str:
        commitment = {
            "derivation_id": (
                "tenant-boundary-audit-public-record-id"
            ),
            "derivation_version": "1.0.0",
            "tenant_id": record.tenant_id,
            "internal_record_commitment": (
                record.record_hash
            ),
        }

        return sha256_hex(
            canonical_json(commitment)
        )
