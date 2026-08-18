from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernedPaidAssessmentDeliveryEvent,
)


PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_ID = (
    "governance-paid-assessment-client-acknowledgment"
)
PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_VERSION = "0.1.0"
PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_SCHEMA_VERSION = "1.0.0"


class PaidAssessmentClientAcknowledgmentError(ValueError):
    """Raised when a paid-assessment client acknowledgment is invalid."""


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
        raise PaidAssessmentClientAcknowledgmentError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PaidAssessmentClientAcknowledgmentError(
            f"{field_name} must not be empty"
        )

    return normalized


def require_hash(value: Any, field_name: str) -> str:
    normalized = require_text(value, field_name)

    if len(normalized) != 64:
        raise PaidAssessmentClientAcknowledgmentError(
            f"{field_name} must be a SHA-256 hex digest"
        )

    try:
        int(normalized, 16)
    except ValueError as exc:
        raise PaidAssessmentClientAcknowledgmentError(
            f"{field_name} must be a SHA-256 hex digest"
        ) from exc

    return normalized


def parse_timestamp(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise PaidAssessmentClientAcknowledgmentError(
            f"{field_name} must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise PaidAssessmentClientAcknowledgmentError(
            f"{field_name} must include a timezone"
        )

    return parsed


@dataclass(frozen=True, slots=True)
class ClientAssessmentReceiptAcknowledgment:
    acknowledgment_id: str
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str
    delivery_event_id: str
    delivery_event_hash: str
    acknowledged_by: str
    acknowledged_at: str
    acknowledgment_method: str
    acknowledgment_reference: str
    client_acknowledged_receipt: bool

    def __post_init__(self) -> None:
        for field_name in (
            "acknowledgment_id",
            "tenant_id",
            "client_id",
            "engagement_id",
            "assessment_id",
            "report_id",
            "delivery_event_id",
            "acknowledged_by",
            "acknowledged_at",
            "acknowledgment_method",
            "acknowledgment_reference",
        ):
            object.__setattr__(
                self,
                field_name,
                require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        object.__setattr__(
            self,
            "delivery_event_hash",
            require_hash(
                self.delivery_event_hash,
                "delivery_event_hash",
            ),
        )

        parse_timestamp(
            self.acknowledged_at,
            "acknowledged_at",
        )

        if self.client_acknowledged_receipt is not True:
            raise PaidAssessmentClientAcknowledgmentError(
                "client_acknowledged_receipt must be true before "
                "client receipt acknowledgment can be recorded"
            )

    @property
    def acknowledgment_evidence_hash(self) -> str:
        return sha256_text(
            canonical_json(
                {
                    "acknowledgment_id": self.acknowledgment_id,
                    "tenant_id": self.tenant_id,
                    "client_id": self.client_id,
                    "engagement_id": self.engagement_id,
                    "assessment_id": self.assessment_id,
                    "report_id": self.report_id,
                    "delivery_event_id": self.delivery_event_id,
                    "delivery_event_hash": self.delivery_event_hash,
                    "acknowledged_by": self.acknowledged_by,
                    "acknowledged_at": self.acknowledged_at,
                    "acknowledgment_method": (
                        self.acknowledgment_method
                    ),
                    "acknowledgment_reference": (
                        self.acknowledgment_reference
                    ),
                    "client_acknowledged_receipt": (
                        self.client_acknowledged_receipt
                    ),
                }
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "acknowledgment_id": self.acknowledgment_id,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "report_id": self.report_id,
            "delivery_event_id": self.delivery_event_id,
            "delivery_event_hash": self.delivery_event_hash,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at,
            "acknowledgment_method": self.acknowledgment_method,
            "acknowledgment_reference": (
                self.acknowledgment_reference
            ),
            "client_acknowledged_receipt": (
                self.client_acknowledged_receipt
            ),
            "acknowledgment_evidence_hash": (
                self.acknowledgment_evidence_hash
            ),
        }


@dataclass(frozen=True, slots=True)
class GovernedPaidAssessmentClientAcknowledgment:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str
    delivery_event_id: str
    delivery_event_hash: str
    acknowledgment_id: str
    acknowledgment_evidence_hash: str
    acknowledged_by: str
    acknowledged_at: str
    acknowledgment_method: str
    acknowledgment_reference: str
    acknowledgment_status: str
    acknowledgment_hash: str
    acknowledgment_type: str = (
        PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_ID
    )
    version: str = PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_VERSION
    schema_version: str = (
        PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_SCHEMA_VERSION
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
            "acknowledgment_type": self.acknowledgment_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "report_id": self.report_id,
            "delivery_event_id": self.delivery_event_id,
            "delivery_event_hash": self.delivery_event_hash,
            "acknowledgment_id": self.acknowledgment_id,
            "acknowledgment_evidence_hash": (
                self.acknowledgment_evidence_hash
            ),
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at,
            "acknowledgment_method": self.acknowledgment_method,
            "acknowledgment_reference": (
                self.acknowledgment_reference
            ),
            "acknowledgment_status": self.acknowledgment_status,
            "acknowledgment_hash": self.acknowledgment_hash,
        }


class GovernancePaidAssessmentClientAcknowledgmentService:
    """
    Records explicit client acknowledgment that a PA-005 delivered report
    was received.

    Receipt acknowledgment is intentionally distinct from acceptance of
    findings or recommendations, intervention authorization, satisfaction,
    causal success, ROI, remediation success, or verified customer outcomes.
    """

    REQUIRED_DELIVERY_STATUS = "delivered"
    ACKNOWLEDGMENT_STATUS = "client_receipt_acknowledged"

    def record_acknowledgment(
        self,
        *,
        delivery_event: GovernedPaidAssessmentDeliveryEvent,
        acknowledgment: ClientAssessmentReceiptAcknowledgment,
    ) -> GovernedPaidAssessmentClientAcknowledgment:
        self._validate_delivery_event(delivery_event)
        self._validate_acknowledgment(
            delivery_event=delivery_event,
            acknowledgment=acknowledgment,
        )

        payload = {
            "acknowledgment_type": (
                PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_ID
            ),
            "version": (
                PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_VERSION
            ),
            "schema_version": (
                PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_SCHEMA_VERSION
            ),
            "tenant_id": delivery_event.tenant_id,
            "client_id": delivery_event.client_id,
            "engagement_id": delivery_event.engagement_id,
            "assessment_id": delivery_event.assessment_id,
            "report_id": delivery_event.report_id,
            "delivery_event_id": delivery_event.delivery_event_id,
            "delivery_event_hash": delivery_event.delivery_event_hash,
            "acknowledgment_id": acknowledgment.acknowledgment_id,
            "acknowledgment_evidence_hash": (
                acknowledgment.acknowledgment_evidence_hash
            ),
            "acknowledged_by": acknowledgment.acknowledged_by,
            "acknowledged_at": acknowledgment.acknowledged_at,
            "acknowledgment_method": (
                acknowledgment.acknowledgment_method
            ),
            "acknowledgment_reference": (
                acknowledgment.acknowledgment_reference
            ),
            "acknowledgment_status": self.ACKNOWLEDGMENT_STATUS,
        }

        return GovernedPaidAssessmentClientAcknowledgment(
            tenant_id=delivery_event.tenant_id,
            client_id=delivery_event.client_id,
            engagement_id=delivery_event.engagement_id,
            assessment_id=delivery_event.assessment_id,
            report_id=delivery_event.report_id,
            delivery_event_id=delivery_event.delivery_event_id,
            delivery_event_hash=delivery_event.delivery_event_hash,
            acknowledgment_id=acknowledgment.acknowledgment_id,
            acknowledgment_evidence_hash=(
                acknowledgment.acknowledgment_evidence_hash
            ),
            acknowledged_by=acknowledgment.acknowledged_by,
            acknowledged_at=acknowledgment.acknowledged_at,
            acknowledgment_method=(
                acknowledgment.acknowledgment_method
            ),
            acknowledgment_reference=(
                acknowledgment.acknowledgment_reference
            ),
            acknowledgment_status=self.ACKNOWLEDGMENT_STATUS,
            acknowledgment_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def _validate_delivery_event(
        self,
        delivery_event: GovernedPaidAssessmentDeliveryEvent,
    ) -> None:
        if not isinstance(
            delivery_event,
            GovernedPaidAssessmentDeliveryEvent,
        ):
            raise PaidAssessmentClientAcknowledgmentError(
                "delivery_event must be a "
                "GovernedPaidAssessmentDeliveryEvent"
            )

        if (
            delivery_event.delivery_status
            != self.REQUIRED_DELIVERY_STATUS
        ):
            raise PaidAssessmentClientAcknowledgmentError(
                "delivery event must have delivery_status=delivered"
            )

        require_hash(
            delivery_event.delivery_event_hash,
            "delivery_event.delivery_event_hash",
        )

        expected_hash = sha256_text(
            canonical_json(
                {
                    "event_type": delivery_event.event_type,
                    "version": delivery_event.version,
                    "schema_version": delivery_event.schema_version,
                    "tenant_id": delivery_event.tenant_id,
                    "client_id": delivery_event.client_id,
                    "engagement_id": delivery_event.engagement_id,
                    "assessment_id": delivery_event.assessment_id,
                    "report_id": delivery_event.report_id,
                    "delivery_envelope_hash": (
                        delivery_event.delivery_envelope_hash
                    ),
                    "delivery_approval_hash": (
                        delivery_event.delivery_approval_hash
                    ),
                    "human_delivery_confirmation_hash": (
                        delivery_event.human_delivery_confirmation_hash
                    ),
                    "delivery_event_id": (
                        delivery_event.delivery_event_id
                    ),
                    "delivered_by": delivery_event.delivered_by,
                    "delivered_at": delivery_event.delivered_at,
                    "delivery_method": delivery_event.delivery_method,
                    "delivery_reference": (
                        delivery_event.delivery_reference
                    ),
                    "delivery_status": delivery_event.delivery_status,
                }
            )
        )

        if delivery_event.delivery_event_hash != expected_hash:
            raise PaidAssessmentClientAcknowledgmentError(
                "delivery event failed deterministic hash verification"
            )

    def _validate_acknowledgment(
        self,
        *,
        delivery_event: GovernedPaidAssessmentDeliveryEvent,
        acknowledgment: ClientAssessmentReceiptAcknowledgment,
    ) -> None:
        if not isinstance(
            acknowledgment,
            ClientAssessmentReceiptAcknowledgment,
        ):
            raise PaidAssessmentClientAcknowledgmentError(
                "acknowledgment must be a "
                "ClientAssessmentReceiptAcknowledgment"
            )

        expected = (
            delivery_event.tenant_id,
            delivery_event.client_id,
            delivery_event.engagement_id,
            delivery_event.assessment_id,
            delivery_event.report_id,
            delivery_event.delivery_event_id,
            delivery_event.delivery_event_hash,
        )

        actual = (
            acknowledgment.tenant_id,
            acknowledgment.client_id,
            acknowledgment.engagement_id,
            acknowledgment.assessment_id,
            acknowledgment.report_id,
            acknowledgment.delivery_event_id,
            acknowledgment.delivery_event_hash,
        )

        if actual != expected:
            raise PaidAssessmentClientAcknowledgmentError(
                "client acknowledgment lineage does not match "
                "governed delivery event"
            )

        delivered_at = parse_timestamp(
            delivery_event.delivered_at,
            "delivery_event.delivered_at",
        )
        acknowledged_at = parse_timestamp(
            acknowledgment.acknowledged_at,
            "acknowledged_at",
        )

        if acknowledged_at < delivered_at:
            raise PaidAssessmentClientAcknowledgmentError(
                "acknowledged_at must not occur before delivered_at"
            )


SERVICE = GovernancePaidAssessmentClientAcknowledgmentService()