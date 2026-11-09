"""Application service coordinating human approval requests and decisions.

This module does not authorize or execute approved actions.

The injected identity provider is a trusted boundary. Its implementation
must resolve authentication context using a real authentication system.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from backend.app.gagf.governance_agent_approval_contract import (
    AgentApprovalDecisionRecord,
    AgentApprovalRequest,
    ApprovalActorType,
    ApprovalDecision,
    requires_human_approval,
)
from backend.app.gagf.governance_agent_approval_store import (
    AgentApprovalConflictError,
    AgentApprovalNotFoundError,
    AgentApprovalStore,
)


class AgentApprovalServiceError(Exception):
    """Base exception for approval-service failures."""


class AgentApprovalIdentityError(AgentApprovalServiceError):
    """Raised when trusted actor identity cannot be established."""


@dataclass(frozen=True, slots=True)
class AuthenticatedApprovalActor:
    """Identity resolved by a trusted authentication adapter.

    Constructing this object is not authentication. The service trusts only
    the injected identity provider that returns it.
    """

    tenant_id: str
    actor_id: str
    actor_type: ApprovalActorType


class ApprovalIdentityProvider(Protocol):
    """Trusted adapter for resolving an actor from authentication context."""

    def resolve_actor(
        self,
        *,
        tenant_id: str,
        authentication_context: object,
    ) -> AuthenticatedApprovalActor:
        """Resolve the authenticated actor for the requested tenant."""
        ...


class GovernanceAgentApprovalService:
    """Coordinate approval persistence without granting execution authority."""

    def __init__(
        self,
        *,
        store: AgentApprovalStore,
        identity_provider: ApprovalIdentityProvider,
    ) -> None:
        if not isinstance(store, AgentApprovalStore):
            raise AgentApprovalServiceError(
                "store must be an AgentApprovalStore"
            )

        if not callable(getattr(identity_provider, "resolve_actor", None)):
            raise AgentApprovalServiceError(
                "identity_provider must implement resolve_actor"
            )

        self._store = store
        self._identity_provider = identity_provider

    def create_request(
        self,
        request: AgentApprovalRequest,
    ) -> AgentApprovalRequest:
        """Validate and persist an approval-required request."""

        if not isinstance(request, AgentApprovalRequest):
            raise AgentApprovalServiceError(
                "request must be an AgentApprovalRequest"
            )

        if not requires_human_approval(request.action_class):
            raise AgentApprovalServiceError(
                "This action class does not require human approval"
            )

        return self._store.save_request(request)

    def get_request(
        self,
        *,
        tenant_id: str,
        request_id: str,
    ) -> AgentApprovalRequest:
        """Retrieve a request within its tenant boundary."""

        return self._store.get_request(
            tenant_id=tenant_id,
            request_id=request_id,
        )

    def submit_decision(
        self,
        *,
        tenant_id: str,
        request_id: str,
        decision: ApprovalDecision,
        authentication_context: object,
        idempotency_key: str,
        reason: str | None = None,
    ) -> AgentApprovalDecisionRecord:
        """Resolve a human actor and persist one final approval decision.

        Authentication is performed before replay handling. Replays return
        the original record only when the submitted intent matches exactly.
        """

        request = self._store.get_request(
            tenant_id=tenant_id,
            request_id=request_id,
        )

        actor = self._resolve_human_actor(
            tenant_id=tenant_id,
            authentication_context=authentication_context,
        )

        existing = self._get_existing_decision(
            tenant_id=tenant_id,
            request_id=request_id,
        )

        if existing is not None:
            if self._decision_matches_intent(
                existing,
                decision=decision,
                actor_id=actor.actor_id,
                idempotency_key=idempotency_key,
                reason=reason,
            ):
                return existing

            raise AgentApprovalConflictError(
                "Approval request already has a different final decision"
            )

        record = AgentApprovalDecisionRecord.create(
            decision_id=str(uuid4()),
            request=request,
            decision=decision,
            approver_id=actor.actor_id,
            approver_type=actor.actor_type,
            decided_at=datetime.now(timezone.utc),
            idempotency_key=idempotency_key,
            reason=reason,
        )

        try:
            return self._store.record_decision(record)
        except AgentApprovalConflictError:
            # Another request may have committed the same intent between
            # our initial read and the transactional store operation.
            concurrent = self._get_existing_decision(
                tenant_id=tenant_id,
                request_id=request_id,
            )

            if concurrent is not None and self._decision_matches_intent(
                concurrent,
                decision=decision,
                actor_id=actor.actor_id,
                idempotency_key=idempotency_key,
                reason=reason,
            ):
                return concurrent

            raise

    def get_decision(
        self,
        *,
        tenant_id: str,
        request_id: str,
    ) -> AgentApprovalDecisionRecord:
        """Retrieve the final decision within its tenant boundary."""

        return self._store.get_decision(
            tenant_id=tenant_id,
            request_id=request_id,
        )

    def _resolve_human_actor(
        self,
        *,
        tenant_id: str,
        authentication_context: object,
    ) -> AuthenticatedApprovalActor:
        try:
            actor = self._identity_provider.resolve_actor(
                tenant_id=tenant_id,
                authentication_context=authentication_context,
            )
        except Exception as exc:
            raise AgentApprovalIdentityError(
                "Unable to resolve authenticated approval actor"
            ) from exc

        if not isinstance(actor, AuthenticatedApprovalActor):
            raise AgentApprovalIdentityError(
                "Identity provider returned an invalid actor"
            )

        if actor.tenant_id != tenant_id:
            raise AgentApprovalIdentityError(
                "Authenticated actor tenant does not match request tenant"
            )

        if not isinstance(actor.actor_id, str) or not actor.actor_id.strip():
            raise AgentApprovalIdentityError(
                "Authenticated actor ID is invalid"
            )

        if actor.actor_type is not ApprovalActorType.HUMAN:
            raise AgentApprovalIdentityError(
                "Only an authenticated human actor may decide approval"
            )

        return actor

    def _get_existing_decision(
        self,
        *,
        tenant_id: str,
        request_id: str,
    ) -> AgentApprovalDecisionRecord | None:
        try:
            return self._store.get_decision(
                tenant_id=tenant_id,
                request_id=request_id,
            )
        except AgentApprovalNotFoundError:
            return None

    @staticmethod
    def _decision_matches_intent(
        existing: AgentApprovalDecisionRecord,
        *,
        decision: ApprovalDecision,
        actor_id: str,
        idempotency_key: str,
        reason: str | None,
    ) -> bool:
        return (
            existing.decision is decision
            and existing.approver_id == actor_id
            and existing.approver_type is ApprovalActorType.HUMAN
            and existing.idempotency_key == idempotency_key
            and existing.reason == reason
        )