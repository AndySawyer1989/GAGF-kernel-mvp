from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from backend.app.gagf.tenant_public_boundary_audit_ledger import (
    TenantPublicBoundaryAuditLedger,
    TenantPublicBoundaryAuditRecord,
)
from backend.app.gagf.tenant_public_response_gate import (
    TenantPublicResponseGate,
    TenantPublicResponseRejectedError,
)


TENANT_RECORDED_PUBLIC_RESPONSE_GATE_ID = (
    "tenant-recorded-public-response-boundary-gate"
)
TENANT_RECORDED_PUBLIC_RESPONSE_GATE_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class TenantRecordedPublicResponse:
    gate_id: str
    gate_version: str
    response: dict
    audit_record: TenantPublicBoundaryAuditRecord

    def to_dict(self) -> dict:
        return {
            **self.response,
            "boundary_audit_record": (
                self.audit_record.to_dict()
            ),
        }


class TenantRecordedPublicResponseGate:
    def __init__(
        self,
        *,
        database_path: str | Path,
    ) -> None:
        self.response_gate = TenantPublicResponseGate()
        self.audit_ledger = (
            TenantPublicBoundaryAuditLedger(
                database_path
            )
        )

    def release(
        self,
        *,
        tenant_id: str,
        response_kind: str,
        response: dict,
        sensitive_values: Iterable[str] = (),
        include_boundary_audit: bool = True,
        include_ledger_record: bool = True,
    ) -> dict:
        inspection = self.response_gate.inspect(
            response=response,
            sensitive_values=sensitive_values,
        )

        if not inspection.boundary_audit.valid:
            self.audit_ledger.append(
                tenant_id=tenant_id,
                response_kind=response_kind,
                released=False,
                audit=inspection.boundary_audit,
            )

            raise TenantPublicResponseRejectedError(
                "Tenant public response was rejected by the "
                "constitutional boundary gate."
            )

        released_response = (
            self.response_gate.release(
                response=response,
                sensitive_values=sensitive_values,
                include_audit=include_boundary_audit,
            )
        )

        record = self.audit_ledger.append(
            tenant_id=tenant_id,
            response_kind=response_kind,
            released=True,
            audit=inspection.boundary_audit,
        )

        if not include_ledger_record:
            return released_response

        return TenantRecordedPublicResponse(
            gate_id=(
                TENANT_RECORDED_PUBLIC_RESPONSE_GATE_ID
            ),
            gate_version=(
                TENANT_RECORDED_PUBLIC_RESPONSE_GATE_VERSION
            ),
            response=released_response,
            audit_record=record,
        ).to_dict()

    def release_error_detail(
        self,
        *,
        tenant_id: str,
        response_kind: str,
        detail: dict,
        sensitive_values: Iterable[str] = (),
        include_boundary_audit: bool = True,
        include_ledger_record: bool = True,
    ) -> dict:
        return self.release(
            tenant_id=tenant_id,
            response_kind=response_kind,
            response=detail,
            sensitive_values=sensitive_values,
            include_boundary_audit=include_boundary_audit,
            include_ledger_record=include_ledger_record,
        )

    def verify_ledger(self):
        return self.audit_ledger.verify_chain()
