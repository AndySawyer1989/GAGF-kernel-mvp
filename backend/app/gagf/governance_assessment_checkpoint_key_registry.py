from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any


ASSESSMENT_CHECKPOINT_KEY_REGISTRY_VERSION = "1.0.0"


@dataclass(frozen=True)
class AssessmentCheckpointSigningKey:
    tenant_id: str
    key_id: str
    secret: bytes
    active: bool
    created_at: str
    retired_at: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "key_id": self.key_id,
            "active": self.active,
            "created_at": self.created_at,
            "retired_at": self.retired_at,
        }


class AssessmentCheckpointSigningKeyRegistry:
    def __init__(self) -> None:
        self._keys: dict[
            tuple[str, str],
            AssessmentCheckpointSigningKey,
        ] = {}
        self._active_key_ids: dict[str, str] = {}
        self._lock = RLock()

    def register_key(
        self,
        *,
        tenant_id: str,
        key_id: str,
        secret: bytes,
        make_active: bool = False,
    ) -> AssessmentCheckpointSigningKey:
        normalized_tenant_id = tenant_id.strip()
        normalized_key_id = key_id.strip()

        if not normalized_tenant_id:
            raise ValueError("tenant_id is required")

        if not normalized_key_id:
            raise ValueError("key_id is required")

        if not secret:
            raise ValueError("signing secret is required")

        identity = (
            normalized_tenant_id,
            normalized_key_id,
        )

        with self._lock:
            if identity in self._keys:
                raise ValueError(
                    "checkpoint signing key already exists"
                )

            key = AssessmentCheckpointSigningKey(
                tenant_id=normalized_tenant_id,
                key_id=normalized_key_id,
                secret=secret,
                active=False,
                created_at=datetime.now(
                    timezone.utc
                ).isoformat(),
            )
            self._keys[identity] = key

            if make_active:
                return self.activate_key(
                    tenant_id=normalized_tenant_id,
                    key_id=normalized_key_id,
                )

            return key

    def activate_key(
        self,
        *,
        tenant_id: str,
        key_id: str,
    ) -> AssessmentCheckpointSigningKey:
        identity = (tenant_id, key_id)

        with self._lock:
            selected = self._keys.get(identity)

            if selected is None:
                raise KeyError(
                    "checkpoint signing key was not found"
                )

            current_key_id = self._active_key_ids.get(
                tenant_id
            )

            if current_key_id is not None:
                current_identity = (
                    tenant_id,
                    current_key_id,
                )
                current = self._keys[current_identity]
                self._keys[current_identity] = (
                    AssessmentCheckpointSigningKey(
                        tenant_id=current.tenant_id,
                        key_id=current.key_id,
                        secret=current.secret,
                        active=False,
                        created_at=current.created_at,
                        retired_at=datetime.now(
                            timezone.utc
                        ).isoformat(),
                    )
                )

            activated = AssessmentCheckpointSigningKey(
                tenant_id=selected.tenant_id,
                key_id=selected.key_id,
                secret=selected.secret,
                active=True,
                created_at=selected.created_at,
                retired_at=None,
            )
            self._keys[identity] = activated
            self._active_key_ids[tenant_id] = key_id
            return activated

    def get_active_key(
        self,
        *,
        tenant_id: str,
    ) -> AssessmentCheckpointSigningKey:
        with self._lock:
            key_id = self._active_key_ids.get(tenant_id)

            if key_id is None:
                raise KeyError(
                    "active checkpoint signing key was not found"
                )

            return self._keys[(tenant_id, key_id)]

    def get_key(
        self,
        *,
        tenant_id: str,
        key_id: str,
    ) -> AssessmentCheckpointSigningKey:
        with self._lock:
            key = self._keys.get((tenant_id, key_id))

            if key is None:
                raise KeyError(
                    "checkpoint signing key was not found"
                )

            return key

    def list_key_metadata(
        self,
        *,
        tenant_id: str,
    ) -> list[dict[str, Any]]:
        with self._lock:
            keys = [
                key
                for (stored_tenant_id, _), key
                in self._keys.items()
                if stored_tenant_id == tenant_id
            ]

        keys.sort(
            key=lambda item: (item.created_at, item.key_id),
            reverse=True,
        )
        return [key.to_metadata() for key in keys]
