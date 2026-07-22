from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.scientific_calculation_contract import (
    CalculationAuthority,
)
from backend.app.gagf.scientific_execution_context import (
    ScientificExecutionContext,
)


SCIENTIFIC_AUTHORIZATION_POLICY_ID = (
    "scientific-authority-zero-trust-policy"
)
SCIENTIFIC_AUTHORIZATION_POLICY_VERSION = "0.1.0"
SCIENTIFIC_AUTHORIZATION_RECEIPT_SCHEMA_VERSION = "1.0.0"


class ScientificAuthorityAction(str, Enum):
    LIST_CONTRACTS = "LIST_CONTRACTS"
    EVALUATE = "EVALUATE"
    READ_RECEIPT = "READ_RECEIPT"
    READ_CHECKPOINT = "READ_CHECKPOINT"
    VERIFY_CHECKPOINT = "VERIFY_CHECKPOINT"
    READ_EXECUTION = "READ_EXECUTION"
    SUBMIT_CONSTITUTIONAL_APPROVAL = (
        "SUBMIT_CONSTITUTIONAL_APPROVAL"
    )
    ADMINISTER_CONTRACTS = "ADMINISTER_CONTRACTS"


class ScientificAuthorityRole(str, Enum):
    OBSERVER = "scientific-observer"
    REVIEWER = "scientific-reviewer"
    APPROVER = "scientific-approver"
    ADMINISTRATOR = "scientific-administrator"


ROLE_PERMISSIONS: Mapping[
    ScientificAuthorityRole,
    frozenset[ScientificAuthorityAction],
] = MappingProxyType(
    {
        ScientificAuthorityRole.OBSERVER: frozenset(
            {
                ScientificAuthorityAction.LIST_CONTRACTS,
                ScientificAuthorityAction.READ_RECEIPT,
                ScientificAuthorityAction.READ_CHECKPOINT,
                ScientificAuthorityAction.READ_EXECUTION,
            }
        ),
        ScientificAuthorityRole.REVIEWER: frozenset(
            {
                ScientificAuthorityAction.LIST_CONTRACTS,
                ScientificAuthorityAction.EVALUATE,
                ScientificAuthorityAction.READ_RECEIPT,
                ScientificAuthorityAction.READ_CHECKPOINT,
                ScientificAuthorityAction.VERIFY_CHECKPOINT,
                ScientificAuthorityAction.READ_EXECUTION,
            }
        ),
        ScientificAuthorityRole.APPROVER: frozenset(
            {
                ScientificAuthorityAction.LIST_CONTRACTS,
                ScientificAuthorityAction.EVALUATE,
                ScientificAuthorityAction.READ_RECEIPT,
                ScientificAuthorityAction.READ_CHECKPOINT,
                ScientificAuthorityAction.VERIFY_CHECKPOINT,
                ScientificAuthorityAction.READ_EXECUTION,
                ScientificAuthorityAction.SUBMIT_CONSTITUTIONAL_APPROVAL,
            }
        ),
        ScientificAuthorityRole.ADMINISTRATOR: frozenset(
            set(ScientificAuthorityAction)
        ),
    }
)


@dataclass(frozen=True, slots=True)
class ScientificTrustSignals:
    credential_verified: bool
    session_verified: bool
    device_trusted: bool
    step_up_verified: bool
    tenant_membership_verified: bool

    def to_dict(self) -> dict[str, bool]:
        return {
            "credential_verified": self.credential_verified,
            "session_verified": self.session_verified,
            "device_trusted": self.device_trusted,
            "step_up_verified": self.step_up_verified,
            "tenant_membership_verified": (
                self.tenant_membership_verified
            ),
        }


@dataclass(frozen=True, slots=True)
class ScientificAuthorizationRequest:
    context: ScientificExecutionContext
    action: ScientificAuthorityAction
    target_tenant_id: str
    requested_authority: CalculationAuthority | None
    constitutional_approval_submitted: bool
    trust_signals: ScientificTrustSignals

    def to_dict(self) -> dict:
        return {
            "context": self.context.to_dict(),
            "action": self.action.value,
            "target_tenant_id": self.target_tenant_id,
            "requested_authority": (
                self.requested_authority.value
                if self.requested_authority is not None
                else None
            ),
            "constitutional_approval_submitted": (
                self.constitutional_approval_submitted
            ),
            "trust_signals": self.trust_signals.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ScientificAuthorizationDecision:
    allowed: bool
    policy_id: str
    policy_version: str
    action: str
    tenant_id: str
    actor_id: str
    role_id: str
    checks: dict[str, bool]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "action": self.action,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "role_id": self.role_id,
            "checks": dict(self.checks),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True, slots=True)
class ScientificAuthorizationReceipt:
    receipt_schema_version: str
    policy_id: str
    policy_version: str
    request: dict
    decision: dict
    receipt_hash: str

    def payload(self) -> dict:
        return {
            "receipt_schema_version": (
                self.receipt_schema_version
            ),
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "request": dict(self.request),
            "decision": dict(self.decision),
        }

    def to_dict(self) -> dict:
        return {
            **self.payload(),
            "receipt_hash": self.receipt_hash,
        }

    def verify(self) -> bool:
        expected_hash = sha256_hex(
            canonical_json(self.payload())
        )

        return expected_hash == self.receipt_hash


class ScientificAuthorityAuthorizationPolicy:
    def evaluate(
        self,
        request: ScientificAuthorizationRequest,
    ) -> ScientificAuthorizationDecision:
        checks = {
            "tenant_target_present": bool(
                request.target_tenant_id.strip()
            ),
            "tenant_matches_context": (
                request.context.tenant_id
                == request.target_tenant_id.strip()
            ),
            "tenant_membership_verified": (
                request.trust_signals
                .tenant_membership_verified
            ),
            "credential_verified": (
                request.trust_signals.credential_verified
            ),
            "session_verified": (
                request.trust_signals.session_verified
            ),
            "device_trusted": (
                request.trust_signals.device_trusted
            ),
            "role_recognized": False,
            "action_permitted": False,
            "policy_scope_matches_action": False,
            "authority_level_permitted": False,
            "step_up_requirement_satisfied": False,
            "constitutional_approval_requirement_satisfied": (
                False
            ),
        }
        reasons: list[str] = []

        role = self._resolve_role(
            request.context.role_id
        )

        checks["role_recognized"] = role is not None

        if role is None:
            reasons.append(
                "The execution role is not recognized."
            )
        else:
            checks["action_permitted"] = (
                request.action
                in ROLE_PERMISSIONS[role]
            )

            if not checks["action_permitted"]:
                reasons.append(
                    "The role is not permitted to perform "
                    "the requested action."
                )

        checks["policy_scope_matches_action"] = (
            self._scope_matches_action(
                policy_scope=request.context.policy_scope,
                action=request.action,
            )
        )

        if not checks["policy_scope_matches_action"]:
            reasons.append(
                "The bound policy scope does not authorize "
                "the requested action."
            )

        checks["authority_level_permitted"] = (
            self._authority_level_permitted(
                role=role,
                action=request.action,
                requested_authority=(
                    request.requested_authority
                ),
            )
        )

        if not checks["authority_level_permitted"]:
            reasons.append(
                "The role is not permitted to request the "
                "specified authority level."
            )

        step_up_required = self._requires_step_up(
            request
        )
        checks["step_up_requirement_satisfied"] = (
            not step_up_required
            or request.trust_signals.step_up_verified
        )

        if not checks["step_up_requirement_satisfied"]:
            reasons.append(
                "Step-up authentication is required."
            )

        approval_required = (
            request.action
            == ScientificAuthorityAction
            .SUBMIT_CONSTITUTIONAL_APPROVAL
            or request.requested_authority
            == CalculationAuthority.AUTHORITATIVE
        )

        checks[
            "constitutional_approval_requirement_satisfied"
        ] = (
            not approval_required
            or request.constitutional_approval_submitted
        )

        if not checks[
            "constitutional_approval_requirement_satisfied"
        ]:
            reasons.append(
                "Constitutional approval evidence is required."
            )

        for check_name, message in (
            (
                "tenant_target_present",
                "A target tenant is required.",
            ),
            (
                "tenant_matches_context",
                "Cross-tenant access is denied.",
            ),
            (
                "tenant_membership_verified",
                "Tenant membership has not been verified.",
            ),
            (
                "credential_verified",
                "Credential trust has not been verified.",
            ),
            (
                "session_verified",
                "Session trust has not been verified.",
            ),
            (
                "device_trusted",
                "Device trust has not been verified.",
            ),
        ):
            if not checks[check_name]:
                reasons.append(message)

        return ScientificAuthorizationDecision(
            allowed=all(checks.values()),
            policy_id=SCIENTIFIC_AUTHORIZATION_POLICY_ID,
            policy_version=(
                SCIENTIFIC_AUTHORIZATION_POLICY_VERSION
            ),
            action=request.action.value,
            tenant_id=request.context.tenant_id,
            actor_id=request.context.actor_id,
            role_id=request.context.role_id,
            checks=checks,
            reasons=tuple(reasons),
        )

    def evaluate_with_receipt(
        self,
        request: ScientificAuthorizationRequest,
    ) -> tuple[
        ScientificAuthorizationDecision,
        ScientificAuthorizationReceipt,
    ]:
        decision = self.evaluate(request)

        payload = {
            "receipt_schema_version": (
                SCIENTIFIC_AUTHORIZATION_RECEIPT_SCHEMA_VERSION
            ),
            "policy_id": SCIENTIFIC_AUTHORIZATION_POLICY_ID,
            "policy_version": (
                SCIENTIFIC_AUTHORIZATION_POLICY_VERSION
            ),
            "request": request.to_dict(),
            "decision": decision.to_dict(),
        }

        receipt = ScientificAuthorizationReceipt(
            receipt_schema_version=(
                SCIENTIFIC_AUTHORIZATION_RECEIPT_SCHEMA_VERSION
            ),
            policy_id=SCIENTIFIC_AUTHORIZATION_POLICY_ID,
            policy_version=(
                SCIENTIFIC_AUTHORIZATION_POLICY_VERSION
            ),
            request=request.to_dict(),
            decision=decision.to_dict(),
            receipt_hash=sha256_hex(
                canonical_json(payload)
            ),
        )

        return decision, receipt

    def _resolve_role(
        self,
        role_id: str,
    ) -> ScientificAuthorityRole | None:
        try:
            return ScientificAuthorityRole(role_id)
        except ValueError:
            return None

    def _scope_matches_action(
        self,
        *,
        policy_scope: str,
        action: ScientificAuthorityAction,
    ) -> bool:
        normalized_scope = policy_scope.strip().lower()

        accepted_scopes = {
            "*",
            "scientific-authority:*",
            (
                "scientific-authority:"
                + action.value.lower().replace("_", "-")
            ),
        }

        return normalized_scope in accepted_scopes

    def _authority_level_permitted(
        self,
        *,
        role: ScientificAuthorityRole | None,
        action: ScientificAuthorityAction,
        requested_authority: CalculationAuthority | None,
    ) -> bool:
        if action != ScientificAuthorityAction.EVALUATE:
            return requested_authority is None

        if role is None or requested_authority is None:
            return False

        if requested_authority in {
            CalculationAuthority.NON_AUTHORITATIVE,
            CalculationAuthority.ADVISORY,
        }:
            return role in {
                ScientificAuthorityRole.REVIEWER,
                ScientificAuthorityRole.APPROVER,
                ScientificAuthorityRole.ADMINISTRATOR,
            }

        if requested_authority == (
            CalculationAuthority.AUTHORITATIVE
        ):
            return role in {
                ScientificAuthorityRole.APPROVER,
                ScientificAuthorityRole.ADMINISTRATOR,
            }

        return False

    def _requires_step_up(
        self,
        request: ScientificAuthorizationRequest,
    ) -> bool:
        return (
            request.action
            in {
                ScientificAuthorityAction
                .SUBMIT_CONSTITUTIONAL_APPROVAL,
                ScientificAuthorityAction
                .ADMINISTER_CONTRACTS,
            }
            or request.requested_authority
            == CalculationAuthority.AUTHORITATIVE
        )
