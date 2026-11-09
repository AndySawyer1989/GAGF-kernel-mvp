"""Human approval boundary contract for FIP/GAGF agent orchestration.

This module records and validates human approval evidence. It does not
authorize actions, execute external operations, mutate workflow state,
or override deterministic GAGF Kernel decisions.
"""

from __future__ import annotations

import hashlib
import json

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


APPROVAL_CONTRACT_ID = "gagf-agent-approval-contract"
APPROVAL_CONTRACT_VERSION = "0.1.0"
APPROVAL_SCHEMA_VERSION = 1
MAX_APPROVAL_PAYLOAD_BYTES = 262144


class AgentApprovalContractError(ValueError):
    """Raised when an approval request or decision violates the contract."""


class ApprovalRequesterType(str, Enum):
    HUMAN = "human"
    WORKER = "worker"
    SYSTEM = "system"


class ApprovalActorType(str, Enum):
    HUMAN = "human"
    WORKER = "worker"
    SYSTEM = "system"


class ApprovalActionClass(str, Enum):
    READ_ONLY = "read_only"
    INTERNAL_WORKFLOW_MUTATION = "internal_workflow_mutation"
    EXTERNAL_COMMUNICATION = "external_communication"
    EXTERNAL_SYSTEM_MUTATION = "external_system_mutation"
    SECURITY_CONTROL_CHANGE = "security_control_change"
    FINANCIAL_COMMITMENT = "financial_commitment"
    DATA_DISCLOSURE = "data_disclosure"
    PRODUCTION_DEPLOYMENT = "production_deployment"


class ApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


APPROVAL_REQUIRED_ACTION_CLASSES = frozenset({
    ApprovalActionClass.EXTERNAL_COMMUNICATION,
    ApprovalActionClass.EXTERNAL_SYSTEM_MUTATION,
    ApprovalActionClass.SECURITY_CONTROL_CHANGE,
    ApprovalActionClass.FINANCIAL_COMMITMENT,
    ApprovalActionClass.DATA_DISCLOSURE,
    ApprovalActionClass.PRODUCTION_DEPLOYMENT,
})


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentApprovalContractError(
            f"{field_name} must be a non-empty string"
        )

    return value.strip()


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise AgentApprovalContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise AgentApprovalContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise AgentApprovalContractError(
            "Value must contain valid JSON-compatible data"
        ) from exc


def _canonical_object_json(
    value: Mapping[str, Any],
    field_name: str,
) -> str:
    if not isinstance(value, Mapping):
        raise AgentApprovalContractError(
            f"{field_name} must be a mapping"
        )

    normalized = dict(value)

    if any(not isinstance(key, str) for key in normalized):
        raise AgentApprovalContractError(
            f"{field_name} keys must all be strings"
        )

    serialized = _canonical_json(normalized)

    if len(serialized.encode("utf-8")) > MAX_APPROVAL_PAYLOAD_BYTES:
        raise AgentApprovalContractError(
            f"{field_name} exceeds the maximum payload size"
        )

    return serialized


def _canonical_object_json_from_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise AgentApprovalContractError(
            f"{field_name} must be a JSON string"
        )

    try:
        decoded = json.loads(value)
    except (TypeError, ValueError) as exc:
        raise AgentApprovalContractError(
            f"{field_name} must contain valid JSON"
        ) from exc

    if not isinstance(decoded, dict):
        raise AgentApprovalContractError(
            f"{field_name} must contain a JSON object"
        )

    return _canonical_object_json(decoded, field_name)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_schema_version(value: Any) -> None:
    if type(value) is not int or value != APPROVAL_SCHEMA_VERSION:
        raise AgentApprovalContractError(
            "Unsupported approval contract schema version"
        )


def requires_human_approval(
    action_class: ApprovalActionClass,
) -> bool:
    """Return the contract's deterministic approval classification.

    This is an approval requirement, not an authorization decision.
    Kernel policy and action-specific authorization remain independent.
    """

    if not isinstance(action_class, ApprovalActionClass):
        raise AgentApprovalContractError(
            "action_class must be an ApprovalActionClass"
        )

    return action_class in APPROVAL_REQUIRED_ACTION_CLASSES


@dataclass(frozen=True, slots=True)
class AgentApprovalRequest:
    """Immutable request describing one exact proposed action."""

    request_id: str
    tenant_id: str
    workflow_id: str
    work_item_id: str
    action_class: ApprovalActionClass
    requester_id: str
    requester_type: ApprovalRequesterType
    requested_at: datetime
    expires_at: datetime
    correlation_id: str
    idempotency_key: str
    action_json: str
    action_hash: str
    schema_version: int = APPROVAL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "tenant_id",
            "workflow_id",
            "work_item_id",
            "requester_id",
            "correlation_id",
            "idempotency_key",
            "action_hash",
        ):
            _require_text(getattr(self, field_name), field_name)

        if not isinstance(self.action_class, ApprovalActionClass):
            raise AgentApprovalContractError(
                "action_class must be an ApprovalActionClass"
            )

        if not isinstance(self.requester_type, ApprovalRequesterType):
            raise AgentApprovalContractError(
                "requester_type must be an ApprovalRequesterType"
            )

        requested = _require_aware_datetime(
            self.requested_at,
            "requested_at",
        )
        expires = _require_aware_datetime(
            self.expires_at,
            "expires_at",
        )

        if expires <= requested:
            raise AgentApprovalContractError(
                "expires_at must be later than requested_at"
            )

        normalized_action = _canonical_object_json_from_string(
            self.action_json,
            "action",
        )

        expected_hash = _sha256_text(normalized_action)

        if self.action_hash != expected_hash:
            raise AgentApprovalContractError(
                "action_hash does not match the canonical action payload"
            )

        _validate_schema_version(self.schema_version)

        object.__setattr__(self, "requested_at", requested)
        object.__setattr__(self, "expires_at", expires)
        object.__setattr__(self, "action_json", normalized_action)

    @classmethod
    def create(
        cls,
        *,
        request_id: str,
        tenant_id: str,
        workflow_id: str,
        work_item_id: str,
        action_class: ApprovalActionClass,
        requester_id: str,
        requester_type: ApprovalRequesterType,
        requested_at: datetime,
        expires_at: datetime,
        correlation_id: str,
        idempotency_key: str,
        action: Mapping[str, Any],
    ) -> AgentApprovalRequest:
        action_json = _canonical_object_json(action, "action")

        return cls(
            request_id=_require_text(request_id, "request_id"),
            tenant_id=_require_text(tenant_id, "tenant_id"),
            workflow_id=_require_text(workflow_id, "workflow_id"),
            work_item_id=_require_text(work_item_id, "work_item_id"),
            action_class=action_class,
            requester_id=_require_text(requester_id, "requester_id"),
            requester_type=requester_type,
            requested_at=_require_aware_datetime(
                requested_at,
                "requested_at",
            ),
            expires_at=_require_aware_datetime(
                expires_at,
                "expires_at",
            ),
            correlation_id=_require_text(
                correlation_id,
                "correlation_id",
            ),
            idempotency_key=_require_text(
                idempotency_key,
                "idempotency_key",
            ),
            action_json=action_json,
            action_hash=_sha256_text(action_json),
        )

    @property
    def action(self) -> dict[str, Any]:
        return json.loads(self.action_json)

    @property
    def request_hash(self) -> str:
        """Fingerprint the complete immutable approval request."""

        return _sha256_text(_canonical_json({
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "workflow_id": self.workflow_id,
            "work_item_id": self.work_item_id,
            "action_class": self.action_class.value,
            "requester_id": self.requester_id,
            "requester_type": self.requester_type.value,
            "requested_at": self.requested_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "correlation_id": self.correlation_id,
            "idempotency_key": self.idempotency_key,
            "action_hash": self.action_hash,
            "schema_version": self.schema_version,
        }))

    def is_expired(self, at: datetime) -> bool:
        current = _require_aware_datetime(at, "at")
        return current >= self.expires_at


@dataclass(frozen=True, slots=True)
class AgentApprovalDecisionRecord:
    """Immutable human decision bound to one exact approval request."""

    decision_id: str
    request_id: str
    request_hash: str
    tenant_id: str
    workflow_id: str
    work_item_id: str
    action_hash: str
    decision: ApprovalDecision
    approver_id: str
    approver_type: ApprovalActorType
    decided_at: datetime
    idempotency_key: str
    reason: str | None
    schema_version: int
    decision_hash: str

    def __post_init__(self) -> None:
        for field_name in (
            "decision_id",
            "request_id",
            "request_hash",
            "tenant_id",
            "workflow_id",
            "work_item_id",
            "action_hash",
            "approver_id",
            "idempotency_key",
            "decision_hash",
        ):
            _require_text(getattr(self, field_name), field_name)

        if not isinstance(self.decision, ApprovalDecision):
            raise AgentApprovalContractError(
                "decision must be an ApprovalDecision"
            )

        if not isinstance(self.approver_type, ApprovalActorType):
            raise AgentApprovalContractError(
                "approver_type must be an ApprovalActorType"
            )

        decided = _require_aware_datetime(
            self.decided_at,
            "decided_at",
        )

        normalized_reason = (
            _require_text(self.reason, "reason")
            if self.reason is not None
            else None
        )

        _validate_schema_version(self.schema_version)

        object.__setattr__(self, "decided_at", decided)
        object.__setattr__(self, "reason", normalized_reason)

        if self.decision_hash != self._calculate_hash():
            raise AgentApprovalContractError(
                "decision_hash does not match the decision record"
            )

    def _calculate_hash(self) -> str:
        return _sha256_text(_canonical_json({
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "request_hash": self.request_hash,
            "tenant_id": self.tenant_id,
            "workflow_id": self.workflow_id,
            "work_item_id": self.work_item_id,
            "action_hash": self.action_hash,
            "decision": self.decision.value,
            "approver_id": self.approver_id,
            "approver_type": self.approver_type.value,
            "decided_at": self.decided_at.isoformat(),
            "idempotency_key": self.idempotency_key,
            "reason": self.reason,
            "schema_version": self.schema_version,
        }))

    def verify_integrity(self) -> bool:
        return self.decision_hash == self._calculate_hash()

    @classmethod
    def create(
        cls,
        *,
        decision_id: str,
        request: AgentApprovalRequest,
        decision: ApprovalDecision,
        approver_id: str,
        approver_type: ApprovalActorType,
        decided_at: datetime,
        idempotency_key: str,
        reason: str | None = None,
    ) -> AgentApprovalDecisionRecord:
        if not isinstance(request, AgentApprovalRequest):
            raise AgentApprovalContractError(
                "request must be an AgentApprovalRequest"
            )

        if not requires_human_approval(request.action_class):
            raise AgentApprovalContractError(
                "This action class does not require human approval"
            )

        if not isinstance(decision, ApprovalDecision):
            raise AgentApprovalContractError(
                "decision must be an ApprovalDecision"
            )

        if approver_type is not ApprovalActorType.HUMAN:
            raise AgentApprovalContractError(
                "Only a human actor may issue an approval decision"
            )

        normalized_approver = _require_text(
            approver_id,
            "approver_id",
        )

        if normalized_approver == request.requester_id:
            raise AgentApprovalContractError(
                "The requester cannot approve or reject their own request"
            )

        decided = _require_aware_datetime(
            decided_at,
            "decided_at",
        )

        if decided < request.requested_at:
            raise AgentApprovalContractError(
                "Decision cannot predate its approval request"
            )

        if decided >= request.expires_at:
            raise AgentApprovalContractError(
                "Expired approval requests cannot receive decisions"
            )

        normalized_reason = (
            _require_text(reason, "reason")
            if reason is not None
            else None
        )

        fields = {
            "decision_id": _require_text(decision_id, "decision_id"),
            "request_id": request.request_id,
            "request_hash": request.request_hash,
            "tenant_id": request.tenant_id,
            "workflow_id": request.workflow_id,
            "work_item_id": request.work_item_id,
            "action_hash": request.action_hash,
            "decision": decision,
            "approver_id": normalized_approver,
            "approver_type": approver_type,
            "decided_at": decided,
            "idempotency_key": _require_text(
                idempotency_key,
                "idempotency_key",
            ),
            "reason": normalized_reason,
            "schema_version": APPROVAL_SCHEMA_VERSION,
        }


        digest = _sha256_text(_canonical_json({
            **{
                key: value.value if isinstance(value, Enum)
                else value.isoformat() if isinstance(value, datetime)
                else value
                for key, value in fields.items()
            }
        }))

        return cls(
            **fields,
            decision_hash=digest,
        )

    def validate_against(
        self,
        request: AgentApprovalRequest,
    ) -> None:
        """Verify exact request binding and decision validity."""

        if not isinstance(request, AgentApprovalRequest):
            raise AgentApprovalContractError(
                "request must be an AgentApprovalRequest"
            )

        if not requires_human_approval(request.action_class):
            raise AgentApprovalContractError(
                "This action class does not require human approval"
            )

        if not self.verify_integrity():
            raise AgentApprovalContractError(
                "Approval decision integrity verification failed"
            )

        if (
            self.request_id != request.request_id
            or self.request_hash != request.request_hash
            or self.tenant_id != request.tenant_id
            or self.workflow_id != request.workflow_id
            or self.work_item_id != request.work_item_id
            or self.action_hash != request.action_hash
        ):
            raise AgentApprovalContractError(
                "Approval decision does not match its request context"
            )

        if self.approver_type is not ApprovalActorType.HUMAN:
            raise AgentApprovalContractError(
                "Approval decision was not issued by a human actor"
            )

        if self.approver_id == request.requester_id:
            raise AgentApprovalContractError(
                "The requester cannot approve or reject their own request"
            )

        if self.decided_at < request.requested_at:
            raise AgentApprovalContractError(
                "Decision predates the approval request"
            )

        if self.decided_at >= request.expires_at:
            raise AgentApprovalContractError(
                "Decision was issued after request expiration"
            )


SERVICE_TYPE = AgentApprovalRequest