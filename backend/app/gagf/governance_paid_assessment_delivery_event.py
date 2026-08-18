from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.app.gagf.governance_paid_assessment_delivery_envelope import (
    GovernedPaidAssessmentDeliveryEnvelope,
)


PAID_ASSESSMENT_DELIVERY_EVENT_ID = (
    "governance-paid-assessment-delivery-event"
)
PAID_ASSESSMENT_DELIVERY_EVENT_VERSION = "0.1.0"
PAID_ASSESSMENT_DELIVERY_EVENT_SCHEMA_VERSION = "1.0.0"


class PaidAssessmentDeliveryEventError(ValueError):
    """Raised when a governed assessment delivery event is invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise PaidAssessmentDeliveryEventError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PaidAssessmentDeliveryEventError(
            f"{field_name} must not be empty"
        )

    return normalized


def require_hash(value: Any, field_name: str) -> str:
    normalized = require_text(value, field_name)

    if len(normalized) != 64:
        raise PaidAssessmentDeliveryEventError(
            f"{field_name} must be a SHA-256 hex digest"
        )

    try:
        int(normalized, 16)
    except ValueError as exc:
        raise PaidAssessmentDeliveryEventError(
            f"{field_name} must be a SHA-256 hex digest"
        ) from exc

    return normalized


@dataclass(frozen=True, slots=True)
class HumanAssessmentDeliveryConfirmation:
    delivery_event_id: str
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str
    delivered_by: str
    delivered_at: str
    delivery_method: str
    delivery_reference: str
    delivery_completed: bool

    def __post_init__(self) -> None:
        for field_name in (
            "delivery_event_id",
            "tenant_id",
            "client_id",
            "engagement_id",
            "assessment_id",
            "report_id",
            "delivered_by",
            "delivered_at",
            "delivery_method",
            "delivery_reference",
        ):
            object.__setattr__(
                self,
                field_name,
                require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        try:
            datetime.fromisoformat(
                self.delivered_at.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise PaidAssessmentDeliveryEventError(
                "delivered_at must be ISO-8601"
            ) from exc

        if self.delivery_completed is not True:
            raise PaidAssessmentDeliveryEventError(
                "delivery_completed must be true before delivery "
                "can be recorded"
            )

    @property
    def confirmation_hash(self) -> str:
        return sha256_text(
            canonical_json(
                {
                    "delivery_event_id": self.delivery_event_id,
                    "tenant_id": self.tenant_id,
                    "client_id": self.client_id,
                    "engagement_id": self.engagement_id,
                    "assessment_id": self.assessment_id,
                    "report_id": self.report_id,
                    "delivered_by": self.delivered_by,
                    "delivered_at": self.delivered_at,
                    "delivery_method": self.delivery_method,
                    "delivery_reference": self.delivery_reference,
                    "delivery_completed": self.delivery_completed,
                }
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery_event_id": self.delivery_event_id,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "report_id": self.report_id,
            "delivered_by": self.delivered_by,
            "delivered_at": self.delivered_at,
            "delivery_method": self.delivery_method,
            "delivery_reference": self.delivery_reference,
            "delivery_completed": self.delivery_completed,
            "confirmation_hash": self.confirmation_hash,
        }


@dataclass(frozen=True, slots=True)
class GovernedPaidAssessmentDeliveryEvent:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str
    delivery_envelope_hash: str
    delivery_approval_hash: str
    human_delivery_confirmation_hash: str
    delivery_event_id: str
    delivered_by: str
    delivered_at: str
    delivery_method: str
    delivery_reference: str
    delivery_status: str
    delivery_event_hash: str
    event_type: str = PAID_ASSESSMENT_DELIVERY_EVENT_ID
    version: str = PAID_ASSESSMENT_DELIVERY_EVENT_VERSION
    schema_version: str = (
        PAID_ASSESSMENT_DELIVERY_EVENT_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.client_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "report_id": self.report_id,
            "delivery_envelope_hash": self.delivery_envelope_hash,
            "delivery_approval_hash": self.delivery_approval_hash,
            "human_delivery_confirmation_hash": (
                self.human_delivery_confirmation_hash
            ),
            "delivery_event_id": self.delivery_event_id,
            "delivered_by": self.delivered_by,
            "delivered_at": self.delivered_at,
            "delivery_method": self.delivery_method,
            "delivery_reference": self.delivery_reference,
            "delivery_status": self.delivery_status,
            "delivery_event_hash": self.delivery_event_hash,
        }


class GovernancePaidAssessmentDeliveryEventService:
    """
    Records a completed human-operated delivery action for a governed
    paid-assessment report.

    Delivery recording requires an existing PA-003 envelope whose status is
    approved_for_human_delivery plus an explicit human confirmation that the
    delivery action was completed.

    This service does not record client receipt, acknowledgment, acceptance,
    recommendation acceptance, intervention authorization, causal success,
    ROI, remediation success, or verified customer outcomes.
    """

    REQUIRED_ENVELOPE_STATUS = "approved_for_human_delivery"
    DELIVERY_STATUS = "delivered"

    def record_delivery(
        self,
        *,
        delivery_envelope: GovernedPaidAssessmentDeliveryEnvelope,
        human_confirmation: HumanAssessmentDeliveryConfirmation,
    ) -> GovernedPaidAssessmentDeliveryEvent:
        self._validate_delivery_envelope(delivery_envelope)
        self._validate_human_confirmation(
            delivery_envelope=delivery_envelope,
            human_confirmation=human_confirmation,
        )

        payload = {
            "event_type": PAID_ASSESSMENT_DELIVERY_EVENT_ID,
            "version": PAID_ASSESSMENT_DELIVERY_EVENT_VERSION,
            "schema_version": (
                PAID_ASSESSMENT_DELIVERY_EVENT_SCHEMA_VERSION
            ),
            "tenant_id": delivery_envelope.tenant_id,
            "client_id": delivery_envelope.client_id,
            "engagement_id": delivery_envelope.engagement_id,
            "assessment_id": delivery_envelope.assessment_id,
            "report_id": delivery_envelope.report_id,
            "delivery_envelope_hash": (
                delivery_envelope.envelope_hash
            ),
            "delivery_approval_hash": (
                delivery_envelope.delivery_approval_hash
            ),
            "human_delivery_confirmation_hash": (
                human_confirmation.confirmation_hash
            ),
            "delivery_event_id": (
                human_confirmation.delivery_event_id
            ),
            "delivered_by": human_confirmation.delivered_by,
            "delivered_at": human_confirmation.delivered_at,
            "delivery_method": human_confirmation.delivery_method,
            "delivery_reference": (
                human_confirmation.delivery_reference
            ),
            "delivery_status": self.DELIVERY_STATUS,
        }

        return GovernedPaidAssessmentDeliveryEvent(
            tenant_id=delivery_envelope.tenant_id,
            client_id=delivery_envelope.client_id,
            engagement_id=delivery_envelope.engagement_id,
            assessment_id=delivery_envelope.assessment_id,
            report_id=delivery_envelope.report_id,
            delivery_envelope_hash=delivery_envelope.envelope_hash,
            delivery_approval_hash=(
                delivery_envelope.delivery_approval_hash
            ),
            human_delivery_confirmation_hash=(
                human_confirmation.confirmation_hash
            ),
            delivery_event_id=(
                human_confirmation.delivery_event_id
            ),
            delivered_by=human_confirmation.delivered_by,
            delivered_at=human_confirmation.delivered_at,
            delivery_method=human_confirmation.delivery_method,
            delivery_reference=(
                human_confirmation.delivery_reference
            ),
            delivery_status=self.DELIVERY_STATUS,
            delivery_event_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def _validate_delivery_envelope(
        self,
        delivery_envelope: GovernedPaidAssessmentDeliveryEnvelope,
    ) -> None:
        if not isinstance(
            delivery_envelope,
            GovernedPaidAssessmentDeliveryEnvelope,
        ):
            raise PaidAssessmentDeliveryEventError(
                "delivery_envelope must be a "
                "GovernedPaidAssessmentDeliveryEnvelope"
            )

        if (
            delivery_envelope.delivery_status
            != self.REQUIRED_ENVELOPE_STATUS
        ):
            raise PaidAssessmentDeliveryEventError(
                "delivery envelope must be approved_for_human_delivery"
            )

        require_hash(
            delivery_envelope.envelope_hash,
            "delivery_envelope.envelope_hash",
        )
        require_hash(
            delivery_envelope.delivery_approval_hash,
            "delivery_envelope.delivery_approval_hash",
        )

    def _validate_human_confirmation(
        self,
        *,
        delivery_envelope: GovernedPaidAssessmentDeliveryEnvelope,
        human_confirmation: HumanAssessmentDeliveryConfirmation,
    ) -> None:
        if not isinstance(
            human_confirmation,
            HumanAssessmentDeliveryConfirmation,
        ):
            raise PaidAssessmentDeliveryEventError(
                "human_confirmation must be a "
                "HumanAssessmentDeliveryConfirmation"
            )

        expected = (
            delivery_envelope.tenant_id,
            delivery_envelope.client_id,
            delivery_envelope.engagement_id,
            delivery_envelope.assessment_id,
            delivery_envelope.report_id,
        )

        actual = (
            human_confirmation.tenant_id,
            human_confirmation.client_id,
            human_confirmation.engagement_id,
            human_confirmation.assessment_id,
            human_confirmation.report_id,
        )

        if actual != expected:
            raise PaidAssessmentDeliveryEventError(
                "human delivery confirmation identity does not match "
                "approved assessment delivery envelope"
            )


SERVICE = GovernancePaidAssessmentDeliveryEventService()