from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    ClientAssessmentReceiptAcknowledgment,
    GovernedPaidAssessmentClientAcknowledgment,
    GovernancePaidAssessmentClientAcknowledgmentService,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernedPaidAssessmentDeliveryEvent,
    PAID_ASSESSMENT_DELIVERY_EVENT_ID,
    PAID_ASSESSMENT_DELIVERY_EVENT_SCHEMA_VERSION,
    PAID_ASSESSMENT_DELIVERY_EVENT_VERSION,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    canonical_json,
    sha256_text,
)
from backend.app.gagf.governance_paid_assessment_resumable_operator_runner import (
    GovernancePaidAssessmentResumableOperatorRunner,
    PaidAssessmentOperatorActionResult,
)


REAL_PAID_ASSESSMENT_CLIENT_RECEIPT_ID = (
    "governance-real-paid-assessment-client-receipt"
)
REAL_PAID_ASSESSMENT_CLIENT_RECEIPT_VERSION = "0.1.0"
REAL_PAID_ASSESSMENT_CLIENT_RECEIPT_SCHEMA_VERSION = "1.0.0"

CLIENT_RECEIPT_STATUS = "client_receipt_acknowledged"


class RealPaidAssessmentClientReceiptError(RuntimeError):
    """Raised when real client receipt cannot be recorded safely."""


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentClientReceiptResult:
    delivery_event: GovernedPaidAssessmentDeliveryEvent
    receipt_evidence: ClientAssessmentReceiptAcknowledgment
    client_acknowledgment: GovernedPaidAssessmentClientAcknowledgment
    persistence_result: PaidAssessmentOperatorActionResult

    acknowledgment_status: str = CLIENT_RECEIPT_STATUS
    result_type: str = REAL_PAID_ASSESSMENT_CLIENT_RECEIPT_ID
    version: str = REAL_PAID_ASSESSMENT_CLIENT_RECEIPT_VERSION
    schema_version: str = (
        REAL_PAID_ASSESSMENT_CLIENT_RECEIPT_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return self.client_acknowledgment.hierarchy_key

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_type": self.result_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "hierarchy_key": self.hierarchy_key,
            "acknowledgment_status": self.acknowledgment_status,
            "client_receipt_acknowledged": True,
            "delivery_event": self.delivery_event.to_dict(),
            "receipt_evidence": self.receipt_evidence.to_dict(),
            "client_acknowledgment": (
                self.client_acknowledgment.to_dict()
            ),
            "persistence_result": self.persistence_result.to_dict(),
            "boundaries": {
                "delivery_is_not_client_receipt": True,
                "receipt_evidence_is_not_pa006_authority": True,
                "pa006_remains_client_acknowledgment_authority": True,
                "pa013_remains_operator_coordination_authority": True,
                "pa012_remains_lifecycle_persistence_authority": True,
                "client_receipt_is_not_client_response": True,
                "client_receipt_is_not_findings_acceptance": True,
                "client_receipt_is_not_recommendation_acceptance": True,
                "client_receipt_is_not_intervention_authorization": True,
                "client_receipt_is_not_customer_outcome": True,
            },
        }


class GovernanceRealPaidAssessmentClientReceiptService:
    """
    Bridge serialized PILOT-008 delivered-state evidence into the existing
    PA006 client-receipt acknowledgment and PA013/PA012 persistence path.

    Delivery alone never implies client receipt.

    An explicit external client-receipt acknowledgment must preexist this
    service invocation.

    PA006 remains acknowledgment authority.
    PA013 remains resumable operator coordination.
    PA012 remains lifecycle persistence authority.
    """

    def record(
        self,
        *,
        database_path: Path,
        delivered_payload: dict[str, Any],
        receipt_payload: dict[str, Any],
    ) -> RealPaidAssessmentClientReceiptResult:
        database_path = Path(database_path)

        if not database_path.exists():
            raise RealPaidAssessmentClientReceiptError(
                "assessment database does not exist"
            )

        if not database_path.is_file():
            raise RealPaidAssessmentClientReceiptError(
                "assessment database path is not a file"
            )

        delivery_event = self._rehydrate_delivery_event(
            delivered_payload
        )

        receipt_evidence = self._build_receipt_evidence(
            delivery_event=delivery_event,
            payload=receipt_payload,
        )

        client_acknowledgment = (
            GovernancePaidAssessmentClientAcknowledgmentService()
            .record_acknowledgment(
                delivery_event=delivery_event,
                acknowledgment=receipt_evidence,
            )
        )

        if (
            client_acknowledgment.acknowledgment_status
            != CLIENT_RECEIPT_STATUS
        ):
            raise RealPaidAssessmentClientReceiptError(
                "PA006 did not produce "
                "acknowledgment_status=client_receipt_acknowledged"
            )

        if (
            client_acknowledgment.hierarchy_key
            != delivery_event.hierarchy_key
        ):
            raise RealPaidAssessmentClientReceiptError(
                "client acknowledgment hierarchy does not match "
                "delivery event"
            )

        if (
            client_acknowledgment.report_id
            != delivery_event.report_id
        ):
            raise RealPaidAssessmentClientReceiptError(
                "client acknowledgment report_id does not match "
                "delivery event"
            )

        if (
            client_acknowledgment.delivery_event_id
            != delivery_event.delivery_event_id
        ):
            raise RealPaidAssessmentClientReceiptError(
                "client acknowledgment delivery_event_id does not "
                "match delivery event"
            )

        if (
            client_acknowledgment.delivery_event_hash
            != delivery_event.delivery_event_hash
        ):
            raise RealPaidAssessmentClientReceiptError(
                "client acknowledgment delivery_event_hash does not "
                "match delivery event"
            )

        if (
            client_acknowledgment.acknowledgment_evidence_hash
            != receipt_evidence.acknowledgment_evidence_hash
        ):
            raise RealPaidAssessmentClientReceiptError(
                "client acknowledgment evidence hash does not match "
                "receipt evidence"
            )

        repository = GovernanceAssessmentRepository(
            database_path
        )

        runner = GovernancePaidAssessmentResumableOperatorRunner(
            repository=repository
        )

        persistence_result = runner.record_client_receipt(
            client_acknowledgment=client_acknowledgment
        )

        return RealPaidAssessmentClientReceiptResult(
            delivery_event=delivery_event,
            receipt_evidence=receipt_evidence,
            client_acknowledgment=client_acknowledgment,
            persistence_result=persistence_result,
        )

    def _rehydrate_delivery_event(
        self,
        payload: dict[str, Any],
    ) -> GovernedPaidAssessmentDeliveryEvent:
        if not isinstance(payload, dict):
            raise RealPaidAssessmentClientReceiptError(
                "delivered_payload must be an object"
            )

        if payload.get("delivery_recording_passed") is not True:
            raise RealPaidAssessmentClientReceiptError(
                "PILOT-008 delivery recording is not successful"
            )

        if payload.get("delivery_recorded") is not True:
            raise RealPaidAssessmentClientReceiptError(
                "PILOT-008 result is not delivered"
            )

        result = payload.get("result")

        if not isinstance(result, dict):
            raise RealPaidAssessmentClientReceiptError(
                "PILOT-008 result must be an object"
            )

        raw_event = result.get("delivery_event")

        if not isinstance(raw_event, dict):
            raise RealPaidAssessmentClientReceiptError(
                "PILOT-008 delivery_event must be an object"
            )

        delivery_event = GovernedPaidAssessmentDeliveryEvent(
            tenant_id=self._require_text(
                raw_event.get("tenant_id"),
                "delivery_event.tenant_id",
            ),
            client_id=self._require_text(
                raw_event.get("client_id"),
                "delivery_event.client_id",
            ),
            engagement_id=self._require_text(
                raw_event.get("engagement_id"),
                "delivery_event.engagement_id",
            ),
            assessment_id=self._require_text(
                raw_event.get("assessment_id"),
                "delivery_event.assessment_id",
            ),
            report_id=self._require_text(
                raw_event.get("report_id"),
                "delivery_event.report_id",
            ),
            delivery_envelope_hash=self._require_hash(
                raw_event.get("delivery_envelope_hash"),
                "delivery_event.delivery_envelope_hash",
            ),
            delivery_approval_hash=self._require_hash(
                raw_event.get("delivery_approval_hash"),
                "delivery_event.delivery_approval_hash",
            ),
            human_delivery_confirmation_hash=self._require_hash(
                raw_event.get(
                    "human_delivery_confirmation_hash"
                ),
                (
                    "delivery_event."
                    "human_delivery_confirmation_hash"
                ),
            ),
            delivery_event_id=self._require_text(
                raw_event.get("delivery_event_id"),
                "delivery_event.delivery_event_id",
            ),
            delivered_by=self._require_text(
                raw_event.get("delivered_by"),
                "delivery_event.delivered_by",
            ),
            delivered_at=self._require_text(
                raw_event.get("delivered_at"),
                "delivery_event.delivered_at",
            ),
            delivery_method=self._require_text(
                raw_event.get("delivery_method"),
                "delivery_event.delivery_method",
            ),
            delivery_reference=self._require_text(
                raw_event.get("delivery_reference"),
                "delivery_event.delivery_reference",
            ),
            delivery_status=self._require_text(
                raw_event.get("delivery_status"),
                "delivery_event.delivery_status",
            ),
            delivery_event_hash=self._require_hash(
                raw_event.get("delivery_event_hash"),
                "delivery_event.delivery_event_hash",
            ),
        )

        if delivery_event.delivery_status != "delivered":
            raise RealPaidAssessmentClientReceiptError(
                "delivery event does not have delivery_status=delivered"
            )

        expected_hash = sha256_text(
            canonical_json(
                {
                    "event_type": PAID_ASSESSMENT_DELIVERY_EVENT_ID,
                    "version": PAID_ASSESSMENT_DELIVERY_EVENT_VERSION,
                    "schema_version": (
                        PAID_ASSESSMENT_DELIVERY_EVENT_SCHEMA_VERSION
                    ),
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

        if expected_hash != delivery_event.delivery_event_hash:
            raise RealPaidAssessmentClientReceiptError(
                "serialized PA005 delivery event hash is invalid"
            )

        return delivery_event

    def _build_receipt_evidence(
        self,
        *,
        delivery_event: GovernedPaidAssessmentDeliveryEvent,
        payload: dict[str, Any],
    ) -> ClientAssessmentReceiptAcknowledgment:
        if not isinstance(payload, dict):
            raise RealPaidAssessmentClientReceiptError(
                "receipt_payload must be an object"
            )

        for field_name, expected in (
            ("tenant_id", delivery_event.tenant_id),
            ("client_id", delivery_event.client_id),
            ("engagement_id", delivery_event.engagement_id),
            ("assessment_id", delivery_event.assessment_id),
            ("report_id", delivery_event.report_id),
            ("delivery_event_id", delivery_event.delivery_event_id),
            (
                "delivery_event_hash",
                delivery_event.delivery_event_hash,
            ),
        ):
            actual = self._require_text(
                payload.get(field_name),
                field_name,
            )

            if actual != expected:
                raise RealPaidAssessmentClientReceiptError(
                    f"{field_name} does not match delivered event"
                )

        if payload.get("client_acknowledged_receipt") is not True:
            raise RealPaidAssessmentClientReceiptError(
                "client_acknowledged_receipt must be explicitly true"
            )

        # Existing PA006 evidence type remains authoritative for its
        # timestamp semantics, receipt validation, and evidence hash.
        return ClientAssessmentReceiptAcknowledgment(
            acknowledgment_id=self._require_text(
                payload.get("acknowledgment_id"),
                "acknowledgment_id",
            ),
            tenant_id=delivery_event.tenant_id,
            client_id=delivery_event.client_id,
            engagement_id=delivery_event.engagement_id,
            assessment_id=delivery_event.assessment_id,
            report_id=delivery_event.report_id,
            delivery_event_id=delivery_event.delivery_event_id,
            delivery_event_hash=delivery_event.delivery_event_hash,
            acknowledged_by=self._require_text(
                payload.get("acknowledged_by"),
                "acknowledged_by",
            ),
            acknowledged_at=self._require_text(
                payload.get("acknowledged_at"),
                "acknowledged_at",
            ),
            acknowledgment_method=self._require_text(
                payload.get("acknowledgment_method"),
                "acknowledgment_method",
            ),
            acknowledgment_reference=self._require_text(
                payload.get("acknowledgment_reference"),
                "acknowledgment_reference",
            ),
            client_acknowledged_receipt=True,
        )

    @staticmethod
    def _require_text(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise RealPaidAssessmentClientReceiptError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()

    @staticmethod
    def _require_hash(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise RealPaidAssessmentClientReceiptError(
                f"{field_name} must be a SHA-256 hex digest"
            )

        normalized = value.strip()

        if len(normalized) != 64 or normalized != normalized.lower():
            raise RealPaidAssessmentClientReceiptError(
                f"{field_name} must be a lowercase SHA-256 hex digest"
            )

        try:
            int(normalized, 16)
        except ValueError as exc:
            raise RealPaidAssessmentClientReceiptError(
                f"{field_name} must be a SHA-256 hex digest"
            ) from exc

        return normalized


SERVICE_TYPE = GovernanceRealPaidAssessmentClientReceiptService