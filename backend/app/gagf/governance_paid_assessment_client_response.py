from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    GovernedPaidAssessmentClientAcknowledgment,
)


PAID_ASSESSMENT_CLIENT_RESPONSE_ID = (
    "governance-paid-assessment-client-response"
)
PAID_ASSESSMENT_CLIENT_RESPONSE_VERSION = "0.1.0"
PAID_ASSESSMENT_CLIENT_RESPONSE_SCHEMA_VERSION = "1.0.0"

ALLOWED_FINDINGS_DISPOSITIONS = frozenset(
    {
        "acknowledged",
        "under_review",
        "disputed",
    }
)

ALLOWED_RECOMMENDATION_DISPOSITIONS = frozenset(
    {
        "under_review",
        "accepted",
        "partially_accepted",
        "declined",
    }
)


class PaidAssessmentClientResponseError(ValueError):
    """Raised when a governed paid-assessment client response is invalid."""


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
        raise PaidAssessmentClientResponseError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PaidAssessmentClientResponseError(
            f"{field_name} must not be empty"
        )

    return normalized


def require_hash(value: Any, field_name: str) -> str:
    normalized = require_text(value, field_name)

    if len(normalized) != 64:
        raise PaidAssessmentClientResponseError(
            f"{field_name} must be a SHA-256 hex digest"
        )

    try:
        int(normalized, 16)
    except ValueError as exc:
        raise PaidAssessmentClientResponseError(
            f"{field_name} must be a SHA-256 hex digest"
        ) from exc

    return normalized


def parse_timestamp(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise PaidAssessmentClientResponseError(
            f"{field_name} must be ISO-8601"
        ) from exc

    if parsed.tzinfo is None:
        raise PaidAssessmentClientResponseError(
            f"{field_name} must include a timezone"
        )

    return parsed


@dataclass(frozen=True, slots=True)
class ClientAssessmentResponse:
    response_id: str
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str
    acknowledgment_id: str
    acknowledgment_hash: str
    responded_by: str
    responded_at: str
    response_method: str
    response_reference: str
    findings_disposition: str
    recommendations_disposition: str
    response_note: str

    def __post_init__(self) -> None:
        for field_name in (
            "response_id",
            "tenant_id",
            "client_id",
            "engagement_id",
            "assessment_id",
            "report_id",
            "acknowledgment_id",
            "responded_by",
            "responded_at",
            "response_method",
            "response_reference",
            "findings_disposition",
            "recommendations_disposition",
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
            "acknowledgment_hash",
            require_hash(
                self.acknowledgment_hash,
                "acknowledgment_hash",
            ),
        )

        if not isinstance(self.response_note, str):
            raise PaidAssessmentClientResponseError(
                "response_note must be a string"
            )

        object.__setattr__(
            self,
            "response_note",
            self.response_note.strip(),
        )

        parse_timestamp(
            self.responded_at,
            "responded_at",
        )

        if (
            self.findings_disposition
            not in ALLOWED_FINDINGS_DISPOSITIONS
        ):
            raise PaidAssessmentClientResponseError(
                "findings_disposition must be one of: "
                + ", ".join(
                    sorted(ALLOWED_FINDINGS_DISPOSITIONS)
                )
            )

        if (
            self.recommendations_disposition
            not in ALLOWED_RECOMMENDATION_DISPOSITIONS
        ):
            raise PaidAssessmentClientResponseError(
                "recommendations_disposition must be one of: "
                + ", ".join(
                    sorted(
                        ALLOWED_RECOMMENDATION_DISPOSITIONS
                    )
                )
            )

    @property
    def response_evidence_hash(self) -> str:
        return sha256_text(
            canonical_json(
                {
                    "response_id": self.response_id,
                    "tenant_id": self.tenant_id,
                    "client_id": self.client_id,
                    "engagement_id": self.engagement_id,
                    "assessment_id": self.assessment_id,
                    "report_id": self.report_id,
                    "acknowledgment_id": self.acknowledgment_id,
                    "acknowledgment_hash": self.acknowledgment_hash,
                    "responded_by": self.responded_by,
                    "responded_at": self.responded_at,
                    "response_method": self.response_method,
                    "response_reference": self.response_reference,
                    "findings_disposition": (
                        self.findings_disposition
                    ),
                    "recommendations_disposition": (
                        self.recommendations_disposition
                    ),
                    "response_note": self.response_note,
                }
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "response_id": self.response_id,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "report_id": self.report_id,
            "acknowledgment_id": self.acknowledgment_id,
            "acknowledgment_hash": self.acknowledgment_hash,
            "responded_by": self.responded_by,
            "responded_at": self.responded_at,
            "response_method": self.response_method,
            "response_reference": self.response_reference,
            "findings_disposition": self.findings_disposition,
            "recommendations_disposition": (
                self.recommendations_disposition
            ),
            "response_note": self.response_note,
            "response_evidence_hash": self.response_evidence_hash,
        }


@dataclass(frozen=True, slots=True)
class GovernedPaidAssessmentClientResponse:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str
    acknowledgment_id: str
    acknowledgment_hash: str
    response_id: str
    response_evidence_hash: str
    responded_by: str
    responded_at: str
    response_method: str
    response_reference: str
    findings_disposition: str
    recommendations_disposition: str
    response_note: str
    response_status: str
    response_hash: str
    response_type: str = PAID_ASSESSMENT_CLIENT_RESPONSE_ID
    version: str = PAID_ASSESSMENT_CLIENT_RESPONSE_VERSION
    schema_version: str = (
        PAID_ASSESSMENT_CLIENT_RESPONSE_SCHEMA_VERSION
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
            "response_type": self.response_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "report_id": self.report_id,
            "acknowledgment_id": self.acknowledgment_id,
            "acknowledgment_hash": self.acknowledgment_hash,
            "response_id": self.response_id,
            "response_evidence_hash": self.response_evidence_hash,
            "responded_by": self.responded_by,
            "responded_at": self.responded_at,
            "response_method": self.response_method,
            "response_reference": self.response_reference,
            "findings_disposition": self.findings_disposition,
            "recommendations_disposition": (
                self.recommendations_disposition
            ),
            "response_note": self.response_note,
            "response_status": self.response_status,
            "response_hash": self.response_hash,
        }


class GovernancePaidAssessmentClientResponseService:
    """
    Records a client's explicit response to the findings and recommendations
    of a paid assessment after PA-006 receipt acknowledgment.

    Findings disposition and recommendation disposition are independent.

    Recommendation acceptance does not authorize implementation or an
    intervention. This service does not create an intervention request,
    authorization, execution, causal claim, ROI claim, remediation-success
    claim, or verified customer outcome.
    """

    REQUIRED_ACKNOWLEDGMENT_STATUS = (
        "client_receipt_acknowledged"
    )
    RESPONSE_STATUS = "client_response_recorded"

    def record_response(
        self,
        *,
        client_acknowledgment: (
            GovernedPaidAssessmentClientAcknowledgment
        ),
        response: ClientAssessmentResponse,
    ) -> GovernedPaidAssessmentClientResponse:
        self._validate_client_acknowledgment(
            client_acknowledgment
        )
        self._validate_response(
            client_acknowledgment=client_acknowledgment,
            response=response,
        )

        payload = {
            "response_type": PAID_ASSESSMENT_CLIENT_RESPONSE_ID,
            "version": PAID_ASSESSMENT_CLIENT_RESPONSE_VERSION,
            "schema_version": (
                PAID_ASSESSMENT_CLIENT_RESPONSE_SCHEMA_VERSION
            ),
            "tenant_id": client_acknowledgment.tenant_id,
            "client_id": client_acknowledgment.client_id,
            "engagement_id": (
                client_acknowledgment.engagement_id
            ),
            "assessment_id": (
                client_acknowledgment.assessment_id
            ),
            "report_id": client_acknowledgment.report_id,
            "acknowledgment_id": (
                client_acknowledgment.acknowledgment_id
            ),
            "acknowledgment_hash": (
                client_acknowledgment.acknowledgment_hash
            ),
            "response_id": response.response_id,
            "response_evidence_hash": (
                response.response_evidence_hash
            ),
            "responded_by": response.responded_by,
            "responded_at": response.responded_at,
            "response_method": response.response_method,
            "response_reference": response.response_reference,
            "findings_disposition": (
                response.findings_disposition
            ),
            "recommendations_disposition": (
                response.recommendations_disposition
            ),
            "response_note": response.response_note,
            "response_status": self.RESPONSE_STATUS,
        }

        return GovernedPaidAssessmentClientResponse(
            tenant_id=client_acknowledgment.tenant_id,
            client_id=client_acknowledgment.client_id,
            engagement_id=client_acknowledgment.engagement_id,
            assessment_id=client_acknowledgment.assessment_id,
            report_id=client_acknowledgment.report_id,
            acknowledgment_id=(
                client_acknowledgment.acknowledgment_id
            ),
            acknowledgment_hash=(
                client_acknowledgment.acknowledgment_hash
            ),
            response_id=response.response_id,
            response_evidence_hash=response.response_evidence_hash,
            responded_by=response.responded_by,
            responded_at=response.responded_at,
            response_method=response.response_method,
            response_reference=response.response_reference,
            findings_disposition=response.findings_disposition,
            recommendations_disposition=(
                response.recommendations_disposition
            ),
            response_note=response.response_note,
            response_status=self.RESPONSE_STATUS,
            response_hash=sha256_text(
                canonical_json(payload)
            ),
        )

    def _validate_client_acknowledgment(
        self,
        client_acknowledgment: (
            GovernedPaidAssessmentClientAcknowledgment
        ),
    ) -> None:
        if not isinstance(
            client_acknowledgment,
            GovernedPaidAssessmentClientAcknowledgment,
        ):
            raise PaidAssessmentClientResponseError(
                "client_acknowledgment must be a "
                "GovernedPaidAssessmentClientAcknowledgment"
            )

        if (
            client_acknowledgment.acknowledgment_status
            != self.REQUIRED_ACKNOWLEDGMENT_STATUS
        ):
            raise PaidAssessmentClientResponseError(
                "client acknowledgment must have "
                "acknowledgment_status=client_receipt_acknowledged"
            )

        require_hash(
            client_acknowledgment.acknowledgment_hash,
            "client_acknowledgment.acknowledgment_hash",
        )

        expected_hash = sha256_text(
            canonical_json(
                {
                    "acknowledgment_type": (
                        client_acknowledgment.acknowledgment_type
                    ),
                    "version": client_acknowledgment.version,
                    "schema_version": (
                        client_acknowledgment.schema_version
                    ),
                    "tenant_id": client_acknowledgment.tenant_id,
                    "client_id": client_acknowledgment.client_id,
                    "engagement_id": (
                        client_acknowledgment.engagement_id
                    ),
                    "assessment_id": (
                        client_acknowledgment.assessment_id
                    ),
                    "report_id": client_acknowledgment.report_id,
                    "delivery_event_id": (
                        client_acknowledgment.delivery_event_id
                    ),
                    "delivery_event_hash": (
                        client_acknowledgment.delivery_event_hash
                    ),
                    "acknowledgment_id": (
                        client_acknowledgment.acknowledgment_id
                    ),
                    "acknowledgment_evidence_hash": (
                        client_acknowledgment.
                        acknowledgment_evidence_hash
                    ),
                    "acknowledged_by": (
                        client_acknowledgment.acknowledged_by
                    ),
                    "acknowledged_at": (
                        client_acknowledgment.acknowledged_at
                    ),
                    "acknowledgment_method": (
                        client_acknowledgment.
                        acknowledgment_method
                    ),
                    "acknowledgment_reference": (
                        client_acknowledgment.
                        acknowledgment_reference
                    ),
                    "acknowledgment_status": (
                        client_acknowledgment.
                        acknowledgment_status
                    ),
                }
            )
        )

        if (
            client_acknowledgment.acknowledgment_hash
            != expected_hash
        ):
            raise PaidAssessmentClientResponseError(
                "client acknowledgment failed deterministic "
                "hash verification"
            )

    def _validate_response(
        self,
        *,
        client_acknowledgment: (
            GovernedPaidAssessmentClientAcknowledgment
        ),
        response: ClientAssessmentResponse,
    ) -> None:
        if not isinstance(
            response,
            ClientAssessmentResponse,
        ):
            raise PaidAssessmentClientResponseError(
                "response must be a ClientAssessmentResponse"
            )

        expected = (
            client_acknowledgment.tenant_id,
            client_acknowledgment.client_id,
            client_acknowledgment.engagement_id,
            client_acknowledgment.assessment_id,
            client_acknowledgment.report_id,
            client_acknowledgment.acknowledgment_id,
            client_acknowledgment.acknowledgment_hash,
        )

        actual = (
            response.tenant_id,
            response.client_id,
            response.engagement_id,
            response.assessment_id,
            response.report_id,
            response.acknowledgment_id,
            response.acknowledgment_hash,
        )

        if actual != expected:
            raise PaidAssessmentClientResponseError(
                "client response lineage does not match governed "
                "client receipt acknowledgment"
            )

        acknowledged_at = parse_timestamp(
            client_acknowledgment.acknowledged_at,
            "client_acknowledgment.acknowledged_at",
        )
        responded_at = parse_timestamp(
            response.responded_at,
            "responded_at",
        )

        if responded_at < acknowledged_at:
            raise PaidAssessmentClientResponseError(
                "responded_at must not occur before acknowledged_at"
            )


SERVICE = GovernancePaidAssessmentClientResponseService()