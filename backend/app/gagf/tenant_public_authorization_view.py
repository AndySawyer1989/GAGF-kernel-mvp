from dataclasses import dataclass

from backend.app.gagf.scientific_authority_guard import (
    canonical_json,
    sha256_hex,
)
from backend.app.gagf.scientific_authorization import (
    ScientificAuthorizationDecision,
    ScientificAuthorizationReceipt,
)


TENANT_PUBLIC_AUTHORIZATION_VIEW_ID = (
    "tenant-public-scientific-authorization-view"
)
TENANT_PUBLIC_AUTHORIZATION_VIEW_VERSION = "0.1.0"
TENANT_PUBLIC_AUTHORIZATION_VIEW_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class TenantPublicAuthorizationDecision:
    allowed: bool
    action: str
    tenant_id: str
    role_id: str
    policy_id: str
    policy_version: str
    checks: dict[str, bool]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "action": self.action,
            "tenant_id": self.tenant_id,
            "role_id": self.role_id,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "checks": dict(self.checks),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True, slots=True)
class TenantPublicAuthorizationReceipt:
    policy_id: str
    policy_version: str
    public_receipt_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "public_receipt_id": self.public_receipt_id,
        }


@dataclass(frozen=True, slots=True)
class TenantPublicAuthorizationView:
    schema_version: str
    view_id: str
    view_version: str
    decision: TenantPublicAuthorizationDecision
    receipt: TenantPublicAuthorizationReceipt
    view_hash: str

    def payload(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "view_id": self.view_id,
            "view_version": self.view_version,
            "decision": self.decision.to_dict(),
            "receipt": self.receipt.to_dict(),
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


class TenantPublicAuthorizationViewBuilder:
    def build(
        self,
        *,
        decision: ScientificAuthorizationDecision,
        receipt: ScientificAuthorizationReceipt,
    ) -> TenantPublicAuthorizationView:
        public_decision = TenantPublicAuthorizationDecision(
            allowed=decision.allowed,
            action=decision.action,
            tenant_id=decision.tenant_id,
            role_id=decision.role_id,
            policy_id=decision.policy_id,
            policy_version=decision.policy_version,
            checks=dict(decision.checks),
            reasons=tuple(decision.reasons),
        )

        public_receipt_payload = {
            "view_id": TENANT_PUBLIC_AUTHORIZATION_VIEW_ID,
            "view_version": (
                TENANT_PUBLIC_AUTHORIZATION_VIEW_VERSION
            ),
            "tenant_id": decision.tenant_id,
            "action": decision.action,
            "role_id": decision.role_id,
            "policy_id": receipt.policy_id,
            "policy_version": receipt.policy_version,
            "allowed": decision.allowed,
            "internal_receipt_commitment": (
                receipt.receipt_hash
            ),
        }

        public_receipt = TenantPublicAuthorizationReceipt(
            policy_id=receipt.policy_id,
            policy_version=receipt.policy_version,
            public_receipt_id=sha256_hex(
                canonical_json(public_receipt_payload)
            ),
        )

        payload = {
            "schema_version": (
                TENANT_PUBLIC_AUTHORIZATION_VIEW_SCHEMA_VERSION
            ),
            "view_id": TENANT_PUBLIC_AUTHORIZATION_VIEW_ID,
            "view_version": (
                TENANT_PUBLIC_AUTHORIZATION_VIEW_VERSION
            ),
            "decision": public_decision.to_dict(),
            "receipt": public_receipt.to_dict(),
        }

        return TenantPublicAuthorizationView(
            schema_version=(
                TENANT_PUBLIC_AUTHORIZATION_VIEW_SCHEMA_VERSION
            ),
            view_id=TENANT_PUBLIC_AUTHORIZATION_VIEW_ID,
            view_version=(
                TENANT_PUBLIC_AUTHORIZATION_VIEW_VERSION
            ),
            decision=public_decision,
            receipt=public_receipt,
            view_hash=sha256_hex(
                canonical_json(payload)
            ),
        )
