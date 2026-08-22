from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_delivery_envelope import (
    GovernedPaidAssessmentDeliveryEnvelope,
    PAID_ASSESSMENT_DELIVERY_ENVELOPE_ID,
    PAID_ASSESSMENT_DELIVERY_ENVELOPE_SCHEMA_VERSION,
    PAID_ASSESSMENT_DELIVERY_ENVELOPE_VERSION,
    canonical_json,
    sha256_text,
)
from backend.app.gagf.governance_paid_assessment_delivery_event import (
    GovernedPaidAssessmentDeliveryEvent,
    GovernancePaidAssessmentDeliveryEventService,
    HumanAssessmentDeliveryConfirmation,
)
from backend.app.gagf.governance_paid_assessment_resumable_operator_runner import (
    GovernancePaidAssessmentResumableOperatorRunner,
    PaidAssessmentOperatorActionResult,
)


REAL_PAID_ASSESSMENT_DELIVERY_RECORDING_ID = (
    "governance-real-paid-assessment-delivery-recording"
)
REAL_PAID_ASSESSMENT_DELIVERY_RECORDING_VERSION = "0.1.0"
REAL_PAID_ASSESSMENT_DELIVERY_RECORDING_SCHEMA_VERSION = "1.0.0"

DELIVERY_RECORDED_STATUS = "delivered"


class RealPaidAssessmentDeliveryRecordingError(RuntimeError):
    """Raised when a real delivery action cannot be recorded safely."""


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentDeliveryRecordingResult:
    delivery_envelope: GovernedPaidAssessmentDeliveryEnvelope
    human_confirmation: HumanAssessmentDeliveryConfirmation
    delivery_event: GovernedPaidAssessmentDeliveryEvent
    persistence_result: PaidAssessmentOperatorActionResult

    delivery_status: str = DELIVERY_RECORDED_STATUS
    result_type: str = REAL_PAID_ASSESSMENT_DELIVERY_RECORDING_ID
    version: str = REAL_PAID_ASSESSMENT_DELIVERY_RECORDING_VERSION
    schema_version: str = (
        REAL_PAID_ASSESSMENT_DELIVERY_RECORDING_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return self.delivery_event.hierarchy_key

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_type": self.result_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "hierarchy_key": self.hierarchy_key,
            "delivery_status": self.delivery_status,
            "delivery_recorded": True,
            "delivery_envelope": self.delivery_envelope.to_dict(),
            "human_confirmation": self.human_confirmation.to_dict(),
            "delivery_event": self.delivery_event.to_dict(),
            "persistence_result": self.persistence_result.to_dict(),
            "boundaries": {
                "approved_for_human_delivery_is_not_delivery": True,
                "human_confirmation_is_not_delivery_event_authority": True,
                "pa005_remains_delivery_event_authority": True,
                "runner_is_not_delivery_event_authority": True,
                "pa012_remains_lifecycle_persistence_authority": True,
                "delivery_is_not_client_receipt": True,
                "delivery_is_not_client_acknowledgment": True,
                "delivery_is_not_client_acceptance": True,
                "delivery_is_not_customer_outcome": True,
            },
        }


class GovernanceRealPaidAssessmentDeliveryRecordingService:
    """
    Bridge serialized PILOT-007 approval output into the existing governed
    delivery-event and durable lifecycle authorities.

    This service does not infer delivery from approval.

    A separate human-delivery confirmation must explicitly establish that
    delivery occurred before PA005 is invoked.

    PA005 remains delivery-event authority.
    PA013 remains resumable operator coordination.
    PA012 remains lifecycle persistence authority.
    """

    def record(
        self,
        *,
        database_path: Path,
        approved_delivery_payload: dict[str, Any],
        human_confirmation_payload: dict[str, Any],
    ) -> RealPaidAssessmentDeliveryRecordingResult:
        database_path = Path(database_path)

        if not database_path.exists():
            raise RealPaidAssessmentDeliveryRecordingError(
                "assessment database does not exist"
            )

        if not database_path.is_file():
            raise RealPaidAssessmentDeliveryRecordingError(
                "assessment database path is not a file"
            )

        delivery_envelope = self._rehydrate_delivery_envelope(
            approved_delivery_payload
        )

        human_confirmation = self._build_human_confirmation(
            delivery_envelope=delivery_envelope,
            payload=human_confirmation_payload,
        )

        delivery_event = (
            GovernancePaidAssessmentDeliveryEventService()
            .record_delivery(
                delivery_envelope=delivery_envelope,
                human_confirmation=human_confirmation,
            )
        )

        if delivery_event.delivery_status != DELIVERY_RECORDED_STATUS:
            raise RealPaidAssessmentDeliveryRecordingError(
                "PA005 did not produce delivery_status=delivered"
            )

        if delivery_event.hierarchy_key != delivery_envelope.hierarchy_key:
            raise RealPaidAssessmentDeliveryRecordingError(
                "delivery event hierarchy does not match delivery envelope"
            )

        if delivery_event.report_id != delivery_envelope.report_id:
            raise RealPaidAssessmentDeliveryRecordingError(
                "delivery event report_id does not match delivery envelope"
            )

        if (
            delivery_event.delivery_envelope_hash
            != delivery_envelope.envelope_hash
        ):
            raise RealPaidAssessmentDeliveryRecordingError(
                "delivery event envelope hash does not match approved envelope"
            )

        if (
            delivery_event.human_delivery_confirmation_hash
            != human_confirmation.confirmation_hash
        ):
            raise RealPaidAssessmentDeliveryRecordingError(
                "delivery event confirmation hash does not match "
                "human confirmation"
            )

        repository = GovernanceAssessmentRepository(database_path)

        runner = GovernancePaidAssessmentResumableOperatorRunner(
            repository=repository
        )

        persistence_result = runner.record_delivery(
            delivery_event=delivery_event
        )

        return RealPaidAssessmentDeliveryRecordingResult(
            delivery_envelope=delivery_envelope,
            human_confirmation=human_confirmation,
            delivery_event=delivery_event,
            persistence_result=persistence_result,
        )

    def _rehydrate_delivery_envelope(
        self,
        payload: dict[str, Any],
    ) -> GovernedPaidAssessmentDeliveryEnvelope:
        if not isinstance(payload, dict):
            raise RealPaidAssessmentDeliveryRecordingError(
                "approved_delivery_payload must be an object"
            )

        if payload.get("operator_handoff_passed") is not True:
            raise RealPaidAssessmentDeliveryRecordingError(
                "PILOT-007 operator handoff is not successful"
            )

        if payload.get("approved_for_human_delivery") is not True:
            raise RealPaidAssessmentDeliveryRecordingError(
                "PILOT-007 result is not approved_for_human_delivery"
            )

        result = payload.get("result")

        if not isinstance(result, dict):
            raise RealPaidAssessmentDeliveryRecordingError(
                "PILOT-007 result must be an object"
            )

        raw_envelope = result.get("delivery_envelope")

        if not isinstance(raw_envelope, dict):
            raise RealPaidAssessmentDeliveryRecordingError(
                "PILOT-007 delivery_envelope must be an object"
            )

        envelope = GovernedPaidAssessmentDeliveryEnvelope(
            tenant_id=self._require_text(
                raw_envelope.get("tenant_id"),
                "delivery_envelope.tenant_id",
            ),
            client_id=self._require_text(
                raw_envelope.get("client_id"),
                "delivery_envelope.client_id",
            ),
            engagement_id=self._require_text(
                raw_envelope.get("engagement_id"),
                "delivery_envelope.engagement_id",
            ),
            assessment_id=self._require_text(
                raw_envelope.get("assessment_id"),
                "delivery_envelope.assessment_id",
            ),
            report_id=self._require_text(
                raw_envelope.get("report_id"),
                "delivery_envelope.report_id",
            ),
            execution_result_hash=self._require_hash(
                raw_envelope.get("execution_result_hash"),
                "delivery_envelope.execution_result_hash",
            ),
            application_hash=self._require_hash(
                raw_envelope.get("application_hash"),
                "delivery_envelope.application_hash",
            ),
            report_package_hash=self._require_hash(
                raw_envelope.get("report_package_hash"),
                "delivery_envelope.report_package_hash",
            ),
            report_markdown_hash=self._require_hash(
                raw_envelope.get("report_markdown_hash"),
                "delivery_envelope.report_markdown_hash",
            ),
            delivery_approval_id=self._require_text(
                raw_envelope.get("delivery_approval_id"),
                "delivery_envelope.delivery_approval_id",
            ),
            delivery_approval_hash=self._require_hash(
                raw_envelope.get("delivery_approval_hash"),
                "delivery_envelope.delivery_approval_hash",
            ),
            delivery_status=self._require_text(
                raw_envelope.get("delivery_status"),
                "delivery_envelope.delivery_status",
            ),
            envelope_hash=self._require_hash(
                raw_envelope.get("envelope_hash"),
                "delivery_envelope.envelope_hash",
            ),
        )

        if envelope.delivery_status != "approved_for_human_delivery":
            raise RealPaidAssessmentDeliveryRecordingError(
                "delivery envelope is not approved_for_human_delivery"
            )

        expected_hash = sha256_text(
            canonical_json(
                {
                    "envelope_type": (
                        PAID_ASSESSMENT_DELIVERY_ENVELOPE_ID
                    ),
                    "version": (
                        PAID_ASSESSMENT_DELIVERY_ENVELOPE_VERSION
                    ),
                    "schema_version": (
                        PAID_ASSESSMENT_DELIVERY_ENVELOPE_SCHEMA_VERSION
                    ),
                    "tenant_id": envelope.tenant_id,
                    "client_id": envelope.client_id,
                    "engagement_id": envelope.engagement_id,
                    "assessment_id": envelope.assessment_id,
                    "report_id": envelope.report_id,
                    "execution_result_hash": (
                        envelope.execution_result_hash
                    ),
                    "application_hash": envelope.application_hash,
                    "report_package_hash": envelope.report_package_hash,
                    "report_markdown_hash": (
                        envelope.report_markdown_hash
                    ),
                    "delivery_approval_id": (
                        envelope.delivery_approval_id
                    ),
                    "delivery_approval_hash": (
                        envelope.delivery_approval_hash
                    ),
                    "delivery_status": envelope.delivery_status,
                }
            )
        )

        if expected_hash != envelope.envelope_hash:
            raise RealPaidAssessmentDeliveryRecordingError(
                "serialized PA003 delivery envelope hash is invalid"
            )

        return envelope

    def _build_human_confirmation(
        self,
        *,
        delivery_envelope: GovernedPaidAssessmentDeliveryEnvelope,
        payload: dict[str, Any],
    ) -> HumanAssessmentDeliveryConfirmation:
        if not isinstance(payload, dict):
            raise RealPaidAssessmentDeliveryRecordingError(
                "human_confirmation_payload must be an object"
            )

        for field_name, expected in (
            ("tenant_id", delivery_envelope.tenant_id),
            ("client_id", delivery_envelope.client_id),
            ("engagement_id", delivery_envelope.engagement_id),
            ("assessment_id", delivery_envelope.assessment_id),
            ("report_id", delivery_envelope.report_id),
        ):
            actual = self._require_text(
                payload.get(field_name),
                field_name,
            )

            if actual != expected:
                raise RealPaidAssessmentDeliveryRecordingError(
                    f"{field_name} does not match approved delivery envelope"
                )

        if payload.get("delivery_completed") is not True:
            raise RealPaidAssessmentDeliveryRecordingError(
                "delivery_completed must be explicitly true"
            )

        # Existing PA005 type remains authoritative for timestamp validation,
        # completed-delivery validation, and confirmation_hash derivation.
        return HumanAssessmentDeliveryConfirmation(
            delivery_event_id=self._require_text(
                payload.get("delivery_event_id"),
                "delivery_event_id",
            ),
            tenant_id=delivery_envelope.tenant_id,
            client_id=delivery_envelope.client_id,
            engagement_id=delivery_envelope.engagement_id,
            assessment_id=delivery_envelope.assessment_id,
            report_id=delivery_envelope.report_id,
            delivered_by=self._require_text(
                payload.get("delivered_by"),
                "delivered_by",
            ),
            delivered_at=self._require_text(
                payload.get("delivered_at"),
                "delivered_at",
            ),
            delivery_method=self._require_text(
                payload.get("delivery_method"),
                "delivery_method",
            ),
            delivery_reference=self._require_text(
                payload.get("delivery_reference"),
                "delivery_reference",
            ),
            delivery_completed=True,
        )

    @staticmethod
    def _require_text(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise RealPaidAssessmentDeliveryRecordingError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()

    @staticmethod
    def _require_hash(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise RealPaidAssessmentDeliveryRecordingError(
                f"{field_name} must be a SHA-256 hex digest"
            )

        normalized = value.strip()

        if len(normalized) != 64 or normalized != normalized.lower():
            raise RealPaidAssessmentDeliveryRecordingError(
                f"{field_name} must be a lowercase SHA-256 hex digest"
            )

        try:
            int(normalized, 16)
        except ValueError as exc:
            raise RealPaidAssessmentDeliveryRecordingError(
                f"{field_name} must be a SHA-256 hex digest"
            ) from exc

        return normalized


SERVICE_TYPE = GovernanceRealPaidAssessmentDeliveryRecordingService