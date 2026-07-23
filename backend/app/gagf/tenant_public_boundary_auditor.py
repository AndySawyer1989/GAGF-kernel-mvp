from dataclasses import dataclass
from typing import Any, Iterable

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)


TENANT_PUBLIC_BOUNDARY_AUDITOR_ID = (
    "tenant-public-boundary-leak-auditor"
)
TENANT_PUBLIC_BOUNDARY_AUDITOR_VERSION = "0.1.0"
TENANT_PUBLIC_BOUNDARY_AUDIT_SCHEMA_VERSION = "1.0.0"


_FORBIDDEN_KEYS = frozenset(
    {
        "canonical_artifact_id",
        "actor_id",
        "credential_id",
        "session_id",
        "request_id",
        "correlation_id",
        "context_hash",
        "binding_hash",
        "receipt_hash",
        "execution_receipt_hash",
        "authority_receipt_hash",
        "audit_receipt_hash",
        "checkpoint_hash",
        "request_hash",
        "transition_hash",
        "previous_transition_hash",
        "trust_signals",
        "authorization_receipt",
        "internal_receipt_commitment",
    }
)


_ALLOWED_PUBLIC_HASH_KEYS = frozenset(
    {
        "view_hash",
        "audit_hash",
    }
)


_ALLOWED_PUBLIC_ID_KEYS = frozenset(
    {
        "public_artifact_id",
        "public_receipt_id",
        "execution_id",
        "execution_receipt_id",
        "authority_receipt_id",
        "audit_receipt_id",
        "checkpoint_id",
        "context_binding_id",
    }
)


class TenantPublicBoundaryLeakError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class TenantPublicBoundaryViolation:
    path: str
    violation_type: str
    key: str | None
    value_fingerprint: str | None
    message: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "violation_type": self.violation_type,
            "key": self.key,
            "value_fingerprint": self.value_fingerprint,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class TenantPublicBoundaryAuditResult:
    schema_version: str
    auditor_id: str
    auditor_version: str
    valid: bool
    violation_count: int
    violations: tuple[
        TenantPublicBoundaryViolation,
        ...,
    ]
    audit_hash: str

    def payload(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "auditor_id": self.auditor_id,
            "auditor_version": self.auditor_version,
            "valid": self.valid,
            "violation_count": self.violation_count,
            "violations": [
                violation.to_dict()
                for violation in self.violations
            ],
        }

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "audit_hash": self.audit_hash,
        }

    def verify(self) -> bool:
        expected_hash = sha256_hex(
            canonical_json(self.payload())
        )

        return expected_hash == self.audit_hash


class TenantPublicBoundaryAuditor:
    def audit(
        self,
        *,
        response: Any,
        sensitive_values: Iterable[str] = (),
    ) -> TenantPublicBoundaryAuditResult:
        normalized_sensitive_values = frozenset(
            value
            for value in sensitive_values
            if isinstance(value, str) and value
        )

        violations: list[
            TenantPublicBoundaryViolation
        ] = []

        self._inspect(
            value=response,
            path="$",
            parent_key=None,
            sensitive_values=normalized_sensitive_values,
            violations=violations,
        )

        ordered_violations = tuple(
            sorted(
                violations,
                key=lambda violation: (
                    violation.path,
                    violation.violation_type,
                    violation.message,
                ),
            )
        )

        payload = {
            "schema_version": (
                TENANT_PUBLIC_BOUNDARY_AUDIT_SCHEMA_VERSION
            ),
            "auditor_id": (
                TENANT_PUBLIC_BOUNDARY_AUDITOR_ID
            ),
            "auditor_version": (
                TENANT_PUBLIC_BOUNDARY_AUDITOR_VERSION
            ),
            "valid": not ordered_violations,
            "violation_count": len(
                ordered_violations
            ),
            "violations": [
                violation.to_dict()
                for violation in ordered_violations
            ],
        }

        return TenantPublicBoundaryAuditResult(
            schema_version=(
                TENANT_PUBLIC_BOUNDARY_AUDIT_SCHEMA_VERSION
            ),
            auditor_id=(
                TENANT_PUBLIC_BOUNDARY_AUDITOR_ID
            ),
            auditor_version=(
                TENANT_PUBLIC_BOUNDARY_AUDITOR_VERSION
            ),
            valid=not ordered_violations,
            violation_count=len(
                ordered_violations
            ),
            violations=ordered_violations,
            audit_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    def enforce(
        self,
        *,
        response: Any,
        sensitive_values: Iterable[str] = (),
    ) -> TenantPublicBoundaryAuditResult:
        result = self.audit(
            response=response,
            sensitive_values=sensitive_values,
        )

        if not result.valid:
            paths = ", ".join(
                violation.path
                for violation in result.violations
            )

            raise TenantPublicBoundaryLeakError(
                "Tenant public response contains forbidden "
                f"internal data at: {paths}."
            )

        return result

    def _inspect(
        self,
        *,
        value: Any,
        path: str,
        parent_key: str | None,
        sensitive_values: frozenset[str],
        violations: list[
            TenantPublicBoundaryViolation
        ],
    ) -> None:
        if isinstance(value, dict):
            for raw_key, child_value in value.items():
                key = str(raw_key)
                child_path = self._dict_path(
                    path=path,
                    key=key,
                )

                if self._is_forbidden_key(key):
                    violations.append(
                        TenantPublicBoundaryViolation(
                            path=child_path,
                            violation_type=(
                                "FORBIDDEN_KEY"
                            ),
                            key=key,
                            value_fingerprint=(
                                self._fingerprint(
                                    child_value
                                )
                            ),
                            message=(
                                "Tenant response contains a "
                                "forbidden internal field."
                            ),
                        )
                    )

                self._inspect(
                    value=child_value,
                    path=child_path,
                    parent_key=key,
                    sensitive_values=(
                        sensitive_values
                    ),
                    violations=violations,
                )

            return

        if isinstance(value, (list, tuple)):
            for index, child_value in enumerate(
                value
            ):
                self._inspect(
                    value=child_value,
                    path=f"{path}[{index}]",
                    parent_key=parent_key,
                    sensitive_values=(
                        sensitive_values
                    ),
                    violations=violations,
                )

            return

        if (
            isinstance(value, str)
            and value in sensitive_values
        ):
            violations.append(
                TenantPublicBoundaryViolation(
                    path=path,
                    violation_type=(
                        "SENSITIVE_VALUE_EXPOSURE"
                    ),
                    key=parent_key,
                    value_fingerprint=(
                        self._fingerprint(value)
                    ),
                    message=(
                        "Tenant response exposes a known "
                        "sensitive internal value."
                    ),
                )
            )

    def _is_forbidden_key(
        self,
        key: str,
    ) -> bool:
        normalized = key.strip().lower()

        if normalized in _ALLOWED_PUBLIC_HASH_KEYS:
            return False

        if normalized in _ALLOWED_PUBLIC_ID_KEYS:
            return False

        return (
            normalized in _FORBIDDEN_KEYS
            or normalized.startswith(
                "canonical_"
            )
            or normalized.startswith(
                "internal_"
            )
            or normalized.endswith("_hash")
        )

    def _dict_path(
        self,
        *,
        path: str,
        key: str,
    ) -> str:
        if key.isidentifier():
            return f"{path}.{key}"

        escaped = key.replace(
            "\\",
            "\\\\",
        ).replace(
            "'",
            "\\'",
        )

        return f"{path}['{escaped}']"

    def _fingerprint(
        self,
        value: Any,
    ) -> str:
        try:
            serialized = canonical_json(value)
        except (TypeError, ValueError):
            serialized = repr(value)

        return sha256_hex(serialized)

