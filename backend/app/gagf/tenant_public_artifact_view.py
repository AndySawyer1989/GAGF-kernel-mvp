from dataclasses import dataclass
from typing import Any

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.tenant_namespaced_artifact_resolver import (
    TenantNamespacedArtifactResolution,
)


TENANT_PUBLIC_ARTIFACT_VIEW_ID = (
    "tenant-public-scientific-artifact-view"
)
TENANT_PUBLIC_ARTIFACT_VIEW_VERSION = "0.1.0"
TENANT_PUBLIC_ARTIFACT_VIEW_SCHEMA_VERSION = "1.0.0"


_FORBIDDEN_EXACT_KEYS = frozenset(
    {
        "canonical_artifact_id",
        "actor_id",
        "credential_id",
        "session_id",
        "request_id",
        "correlation_id",
        "trust_signals",
        "authorization_receipt",
        "artifact_id",
        "binding_hash",
        "receipt_hash",
        "execution_id",
        "execution_receipt_hash",
        "authority_receipt_hash",
        "audit_receipt_hash",
        "checkpoint_hash",
        "context_hash",
        "request_hash",
        "transition_hash",
        "previous_transition_hash",
    }
)


@dataclass(frozen=True, slots=True)
class TenantPublicArtifactView:
    schema_version: str
    view_id: str
    view_version: str
    tenant_id: str
    artifact_type: str
    public_artifact_id: str
    namespace_sequence_number: int
    artifact: dict
    view_hash: str

    def payload(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "view_id": self.view_id,
            "view_version": self.view_version,
            "tenant_id": self.tenant_id,
            "artifact_type": self.artifact_type,
            "public_artifact_id": (
                self.public_artifact_id
            ),
            "namespace_sequence_number": (
                self.namespace_sequence_number
            ),
            "artifact": dict(self.artifact),
        }

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "view_hash": self.view_hash,
        }

    def verify(self) -> bool:
        expected_hash = sha256_hex(
            canonical_json(self.payload())
        )

        return expected_hash == self.view_hash


class TenantPublicArtifactViewBuilder:
    def build(
        self,
        *,
        resolution: TenantNamespacedArtifactResolution,
    ) -> TenantPublicArtifactView:
        sensitive_values = self._collect_sensitive_values(
            resolution
        )

        public_artifact = self._redact(
            value=resolution.artifact,
            sensitive_values=sensitive_values,
        )

        if not isinstance(public_artifact, dict):
            public_artifact = {
                "value": public_artifact,
            }

        payload = {
            "schema_version": (
                TENANT_PUBLIC_ARTIFACT_VIEW_SCHEMA_VERSION
            ),
            "view_id": TENANT_PUBLIC_ARTIFACT_VIEW_ID,
            "view_version": (
                TENANT_PUBLIC_ARTIFACT_VIEW_VERSION
            ),
            "tenant_id": resolution.tenant_id,
            "artifact_type": resolution.artifact_type,
            "public_artifact_id": (
                resolution.namespaced_artifact_id
            ),
            "namespace_sequence_number": (
                resolution.namespace_sequence_number
            ),
            "artifact": public_artifact,
        }

        return TenantPublicArtifactView(
            schema_version=(
                TENANT_PUBLIC_ARTIFACT_VIEW_SCHEMA_VERSION
            ),
            view_id=TENANT_PUBLIC_ARTIFACT_VIEW_ID,
            view_version=(
                TENANT_PUBLIC_ARTIFACT_VIEW_VERSION
            ),
            tenant_id=resolution.tenant_id,
            artifact_type=resolution.artifact_type,
            public_artifact_id=(
                resolution.namespaced_artifact_id
            ),
            namespace_sequence_number=(
                resolution.namespace_sequence_number
            ),
            artifact=public_artifact,
            view_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

    def _collect_sensitive_values(
        self,
        resolution: TenantNamespacedArtifactResolution,
    ) -> frozenset[str]:
        values = {
            resolution.canonical_artifact_id,
        }

        self._collect_hash_values(
            resolution.artifact,
            values,
        )

        values.discard(
            resolution.namespaced_artifact_id
        )
        values.discard("")

        return frozenset(values)

    def _collect_hash_values(
        self,
        value: Any,
        output: set[str],
        *,
        key: str | None = None,
    ) -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                self._collect_hash_values(
                    child_value,
                    output,
                    key=str(child_key),
                )
            return

        if isinstance(value, (list, tuple)):
            for item in value:
                self._collect_hash_values(
                    item,
                    output,
                    key=key,
                )
            return

        if (
            isinstance(value, str)
            and key is not None
            and self._is_forbidden_key(key)
        ):
            output.add(value)

    def _redact(
        self,
        *,
        value: Any,
        sensitive_values: frozenset[str],
    ) -> Any:
        if isinstance(value, dict):
            redacted: dict[str, Any] = {}

            for key, child_value in value.items():
                normalized_key = str(key)

                if self._is_forbidden_key(
                    normalized_key
                ):
                    continue

                sanitized = self._redact(
                    value=child_value,
                    sensitive_values=sensitive_values,
                )

                if sanitized is not None:
                    redacted[normalized_key] = sanitized

            return redacted

        if isinstance(value, list):
            return [
                sanitized
                for item in value
                if (
                    sanitized := self._redact(
                        value=item,
                        sensitive_values=sensitive_values,
                    )
                )
                is not None
            ]

        if isinstance(value, tuple):
            return [
                sanitized
                for item in value
                if (
                    sanitized := self._redact(
                        value=item,
                        sensitive_values=sensitive_values,
                    )
                )
                is not None
            ]

        if (
            isinstance(value, str)
            and value in sensitive_values
        ):
            return None

        return value

    def _is_forbidden_key(
        self,
        key: str,
    ) -> bool:
        normalized = key.strip().lower()

        return (
            normalized in _FORBIDDEN_EXACT_KEYS
            or normalized.startswith("canonical_")
            or normalized.endswith("_hash")
        )

