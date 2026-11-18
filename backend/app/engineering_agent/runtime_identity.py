from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class RuntimeIdentityError(RuntimeError):
    """Base error for runtime identity resolution."""


class RuntimeAuthenticationError(RuntimeIdentityError):
    """Raised when request authentication is absent or invalid."""


class RuntimeIdentityProviderError(RuntimeIdentityError):
    """Raised when the identity provider cannot safely resolve identity."""


@dataclass(frozen=True, slots=True)
class AuthenticatedRuntimePrincipal:
    """Trusted identity established by an injected authentication provider."""

    tenant_id: str
    actor_id: str
    permissions: frozenset[str]

    def __post_init__(self) -> None:
        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise ValueError("tenant_id must be non-empty text")

        if not isinstance(self.actor_id, str) or not self.actor_id.strip():
            raise ValueError("actor_id must be non-empty text")

        if not isinstance(self.permissions, frozenset):
            raise TypeError("permissions must be a frozenset")

        if any(
            not isinstance(permission, str) or not permission.strip()
            for permission in self.permissions
        ):
            raise ValueError("permissions must contain non-empty strings")


class RuntimeIdentityProvider(Protocol):
    """Authenticates a request and resolves its trusted runtime principal.

    Implementations must validate real credentials and derive tenant and actor
    identity from trusted authentication state, never from caller-supplied
    tenant or actor headers or request-body fields.
    """

    async def authenticate(
        self,
        *,
        authentication_context: object,
    ) -> AuthenticatedRuntimePrincipal:
        """Return an authenticated principal or raise an identity error."""
        ...