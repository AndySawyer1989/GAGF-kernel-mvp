from dataclasses import dataclass
from typing import Any, Iterable

from backend.app.gagf.tenant_public_boundary_auditor import (
    TenantPublicBoundaryAuditResult,
    TenantPublicBoundaryAuditor,
    TenantPublicBoundaryLeakError,
)


TENANT_PUBLIC_RESPONSE_GATE_ID = (
    "tenant-public-response-boundary-gate"
)
TENANT_PUBLIC_RESPONSE_GATE_VERSION = "0.1.0"


class TenantPublicResponseGateError(RuntimeError):
    pass


class TenantPublicResponseRejectedError(
    TenantPublicResponseGateError
):
    pass


@dataclass(frozen=True, slots=True)
class TenantPublicResponseEnvelope:
    gate_id: str
    gate_version: str
    response: dict
    boundary_audit: TenantPublicBoundaryAuditResult

    def to_dict(self) -> dict:
        return {
            **self.response,
            "boundary_audit": (
                self.boundary_audit.to_dict()
            ),
        }


class TenantPublicResponseGate:
    def __init__(self) -> None:
        self.auditor = TenantPublicBoundaryAuditor()

    def inspect(
        self,
        *,
        response: dict,
        sensitive_values: Iterable[str] = (),
    ) -> TenantPublicResponseEnvelope:
        audit = self.auditor.audit(
            response=response,
            sensitive_values=sensitive_values,
        )

        return TenantPublicResponseEnvelope(
            gate_id=TENANT_PUBLIC_RESPONSE_GATE_ID,
            gate_version=(
                TENANT_PUBLIC_RESPONSE_GATE_VERSION
            ),
            response=dict(response),
            boundary_audit=audit,
        )

    def release(
        self,
        *,
        response: dict,
        sensitive_values: Iterable[str] = (),
        include_audit: bool = True,
    ) -> dict:
        try:
            audit = self.auditor.enforce(
                response=response,
                sensitive_values=sensitive_values,
            )
        except TenantPublicBoundaryLeakError as exc:
            raise TenantPublicResponseRejectedError(
                "Tenant public response was rejected by the "
                "constitutional boundary gate."
            ) from exc

        if not include_audit:
            return dict(response)

        envelope = TenantPublicResponseEnvelope(
            gate_id=TENANT_PUBLIC_RESPONSE_GATE_ID,
            gate_version=(
                TENANT_PUBLIC_RESPONSE_GATE_VERSION
            ),
            response=dict(response),
            boundary_audit=audit,
        )

        return envelope.to_dict()

    def release_error_detail(
        self,
        *,
        detail: dict,
        sensitive_values: Iterable[str] = (),
    ) -> dict:
        return self.release(
            response=detail,
            sensitive_values=sensitive_values,
            include_audit=True,
        )
