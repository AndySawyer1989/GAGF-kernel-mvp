from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.gagf.governance_customer_trial_engagement_package import (
    CustomerTrialEngagementPackage,
)
from backend.app.gagf.governance_customer_trial_preflight_decision import (
    CustomerTrialPreflightDecision,
    build_customer_trial_preflight_decision,
)
from backend.app.gagf.governance_customer_trial_preflight_receipt_store import (
    CustomerTrialPreflightReceipt,
    GovernanceCustomerTrialPreflightReceiptStore,
)


CUSTOMER_TRIAL_PREFLIGHT_SERVICE_ID = (
    "governance-customer-trial-preflight-service"
)

CUSTOMER_TRIAL_PREFLIGHT_SERVICE_VERSION = "0.1.0"


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialPreflightExecutionResult:
    decision: CustomerTrialPreflightDecision
    receipt: CustomerTrialPreflightReceipt

    @property
    def trial_ready(
        self,
    ) -> bool:
        return self.decision.trial_ready

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "service": (
                CUSTOMER_TRIAL_PREFLIGHT_SERVICE_ID
            ),
            "version": (
                CUSTOMER_TRIAL_PREFLIGHT_SERVICE_VERSION
            ),
            "trial_ready": self.trial_ready,
            "decision": self.decision.to_dict(),
            "receipt": self.receipt.to_dict(),
            "boundaries": {
                "preflight_is_not_paid_execution_authority": True,
                "preflight_is_not_delivery_approval": True,
                "preflight_is_not_delivery": True,
                "preflight_is_not_client_receipt": True,
                "preflight_is_not_client_response": True,
                "preflight_is_not_administrative_closeout": True,
                "preflight_is_not_intervention_authority": True,
            },
        }


@dataclass(
    frozen=True,
    slots=True,
)
class CustomerTrialPreflightStatusResult:
    receipt_found: bool
    receipt: CustomerTrialPreflightReceipt | None

    @property
    def trial_ready(
        self,
    ) -> bool | None:
        if self.receipt is None:
            return None

        value = self.receipt.decision_payload.get(
            "trial_ready"
        )

        return (
            value
            if isinstance(value, bool)
            else None
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "service": (
                CUSTOMER_TRIAL_PREFLIGHT_SERVICE_ID
            ),
            "version": (
                CUSTOMER_TRIAL_PREFLIGHT_SERVICE_VERSION
            ),
            "receipt_found": self.receipt_found,
            "trial_ready": self.trial_ready,
            "receipt": (
                self.receipt.to_dict()
                if self.receipt is not None
                else None
            ),
            "boundaries": {
                "status_is_read_only": True,
                "status_does_not_authorize_execution": True,
                "status_does_not_authorize_delivery": True,
                "status_does_not_create_closeout": True,
                "status_does_not_authorize_intervention": True,
            },
        }


class GovernanceCustomerTrialPreflightService:
    def __init__(
        self,
        *,
        receipt_store:
            GovernanceCustomerTrialPreflightReceiptStore,
    ) -> None:
        self.receipt_store = receipt_store

    def execute(
        self,
        *,
        package:
            CustomerTrialEngagementPackage,
        evaluated_at: str | None = None,
    ) -> CustomerTrialPreflightExecutionResult:
        decision = (
            build_customer_trial_preflight_decision(
                package,
                evaluated_at=evaluated_at,
            )
        )

        receipt = self.receipt_store.put(
            decision=decision
        )

        return CustomerTrialPreflightExecutionResult(
            decision=decision,
            receipt=receipt,
        )

    def status(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> CustomerTrialPreflightStatusResult:
        receipt = self.receipt_store.get(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        return CustomerTrialPreflightStatusResult(
            receipt_found=(
                receipt is not None
            ),
            receipt=receipt,
        )