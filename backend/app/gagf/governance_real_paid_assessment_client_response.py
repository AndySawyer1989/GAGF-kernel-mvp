from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_client_acknowledgment import (
    GovernedPaidAssessmentClientAcknowledgment,
    PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_ID,
    PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_SCHEMA_VERSION,
    PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_VERSION,
)
from backend.app.gagf.governance_paid_assessment_client_response import (
    ClientAssessmentResponse,
    GovernedPaidAssessmentClientResponse,
    GovernancePaidAssessmentClientResponseService,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    canonical_json,
    sha256_text,
)
from backend.app.gagf.governance_paid_assessment_resumable_operator_runner import (
    GovernancePaidAssessmentResumableOperatorRunner,
    PaidAssessmentOperatorActionResult,
)


REAL_PAID_ASSESSMENT_CLIENT_RESPONSE_ID = (
    "governance-real-paid-assessment-client-response"
)
REAL_PAID_ASSESSMENT_CLIENT_RESPONSE_VERSION = "0.1.0"
REAL_PAID_ASSESSMENT_CLIENT_RESPONSE_SCHEMA_VERSION = "1.0.0"

CLIENT_RESPONSE_STATUS = "client_response_recorded"


class RealPaidAssessmentClientResponseError(RuntimeError):
    """Raised when a real client response cannot be recorded safely."""


@dataclass(frozen=True, slots=True)
class RealPaidAssessmentClientResponseResult:
    client_acknowledgment: GovernedPaidAssessmentClientAcknowledgment
    response_evidence: ClientAssessmentResponse
    client_response: GovernedPaidAssessmentClientResponse
    persistence_result: PaidAssessmentOperatorActionResult

    response_status: str = CLIENT_RESPONSE_STATUS
    result_type: str = REAL_PAID_ASSESSMENT_CLIENT_RESPONSE_ID
    version: str = REAL_PAID_ASSESSMENT_CLIENT_RESPONSE_VERSION
    schema_version: str = (
        REAL_PAID_ASSESSMENT_CLIENT_RESPONSE_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return self.client_response.hierarchy_key

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_type": self.result_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "hierarchy_key": self.hierarchy_key,
            "response_status": self.response_status,
            "client_response_recorded": True,
            "client_acknowledgment": (
                self.client_acknowledgment.to_dict()
            ),
            "response_evidence": self.response_evidence.to_dict(),
            "client_response": self.client_response.to_dict(),
            "persistence_result": self.persistence_result.to_dict(),
            "boundaries": {
                "receipt_is_not_response": True,
                "response_evidence_is_not_pa007_authority": True,
                "pa007_remains_client_response_authority": True,
                "pa013_remains_operator_coordination_authority": True,
                "pa012_remains_lifecycle_persistence_authority": True,
                "findings_disposition_is_not_intervention_authority": True,
                "recommendation_acceptance_is_not_implementation": True,
                "response_is_not_intervention_authorization": True,
                "response_is_not_execution": True,
                "response_is_not_remediation_success": True,
                "response_is_not_roi_verification": True,
                "response_is_not_customer_outcome": True,
            },
        }


class GovernanceRealPaidAssessmentClientResponseService:
    """
    Bridge serialized PILOT-009 client receipt acknowledgment into
    the existing PA007 governed client-response and PA013/PA012
    durable lifecycle path.

    A client response must exist independently before invocation.

    This service does not infer response from receipt and does not
    authorize implementation or intervention.
    """

    def record(
        self,
        *,
        database_path: Path,
        acknowledged_payload: dict[str, Any],
        response_payload: dict[str, Any],
    ) -> RealPaidAssessmentClientResponseResult:
        database_path = Path(database_path)

        if not database_path.exists():
            raise RealPaidAssessmentClientResponseError(
                "assessment database does not exist"
            )

        if not database_path.is_file():
            raise RealPaidAssessmentClientResponseError(
                "assessment database path is not a file"
            )

        client_acknowledgment = self._rehydrate_acknowledgment(
            acknowledged_payload
        )

        response_evidence = self._build_response_evidence(
            client_acknowledgment=client_acknowledgment,
            payload=response_payload,
        )

        client_response = (
            GovernancePaidAssessmentClientResponseService()
            .record_response(
                client_acknowledgment=client_acknowledgment,
                response=response_evidence,
            )
        )

        if client_response.response_status != CLIENT_RESPONSE_STATUS:
            raise RealPaidAssessmentClientResponseError(
                "PA007 did not produce "
                "response_status=client_response_recorded"
            )

        if (
            client_response.hierarchy_key
            != client_acknowledgment.hierarchy_key
        ):
            raise RealPaidAssessmentClientResponseError(
                "client response hierarchy does not match "
                "client acknowledgment"
            )

        if (
            client_response.report_id
            != client_acknowledgment.report_id
        ):
            raise RealPaidAssessmentClientResponseError(
                "client response report_id does not match "
                "client acknowledgment"
            )

        if (
            client_response.acknowledgment_id
            != client_acknowledgment.acknowledgment_id
        ):
            raise RealPaidAssessmentClientResponseError(
                "client response acknowledgment_id does not match "
                "client acknowledgment"
            )

        if (
            client_response.acknowledgment_hash
            != client_acknowledgment.acknowledgment_hash
        ):
            raise RealPaidAssessmentClientResponseError(
                "client response acknowledgment_hash does not match "
                "client acknowledgment"
            )

        if (
            client_response.response_evidence_hash
            != response_evidence.response_evidence_hash
        ):
            raise RealPaidAssessmentClientResponseError(
                "client response evidence hash does not match "
                "response evidence"
            )

        repository = GovernanceAssessmentRepository(
            database_path
        )

        runner = GovernancePaidAssessmentResumableOperatorRunner(
            repository=repository
        )

        persistence_result = runner.record_client_response(
            client_response=client_response
        )

        return RealPaidAssessmentClientResponseResult(
            client_acknowledgment=client_acknowledgment,
            response_evidence=response_evidence,
            client_response=client_response,
            persistence_result=persistence_result,
        )

    def _rehydrate_acknowledgment(
        self,
        payload: dict[str, Any],
    ) -> GovernedPaidAssessmentClientAcknowledgment:
        if not isinstance(payload, dict):
            raise RealPaidAssessmentClientResponseError(
                "acknowledged_payload must be an object"
            )

        if payload.get("client_receipt_recording_passed") is not True:
            raise RealPaidAssessmentClientResponseError(
                "PILOT-009 client receipt recording is not successful"
            )

        if payload.get("client_receipt_acknowledged") is not True:
            raise RealPaidAssessmentClientResponseError(
                "PILOT-009 result is not client_receipt_acknowledged"
            )

        result = payload.get("result")

        if not isinstance(result, dict):
            raise RealPaidAssessmentClientResponseError(
                "PILOT-009 result must be an object"
            )

        raw = result.get("client_acknowledgment")

        if not isinstance(raw, dict):
            raise RealPaidAssessmentClientResponseError(
                "PILOT-009 client_acknowledgment must be an object"
            )

        acknowledgment = GovernedPaidAssessmentClientAcknowledgment(
            tenant_id=self._require_text(
                raw.get("tenant_id"),
                "client_acknowledgment.tenant_id",
            ),
            client_id=self._require_text(
                raw.get("client_id"),
                "client_acknowledgment.client_id",
            ),
            engagement_id=self._require_text(
                raw.get("engagement_id"),
                "client_acknowledgment.engagement_id",
            ),
            assessment_id=self._require_text(
                raw.get("assessment_id"),
                "client_acknowledgment.assessment_id",
            ),
            report_id=self._require_text(
                raw.get("report_id"),
                "client_acknowledgment.report_id",
            ),
            delivery_event_id=self._require_text(
                raw.get("delivery_event_id"),
                "client_acknowledgment.delivery_event_id",
            ),
            delivery_event_hash=self._require_hash(
                raw.get("delivery_event_hash"),
                "client_acknowledgment.delivery_event_hash",
            ),
            acknowledgment_id=self._require_text(
                raw.get("acknowledgment_id"),
                "client_acknowledgment.acknowledgment_id",
            ),
            acknowledgment_evidence_hash=self._require_hash(
                raw.get("acknowledgment_evidence_hash"),
                (
                    "client_acknowledgment."
                    "acknowledgment_evidence_hash"
                ),
            ),
            acknowledged_by=self._require_text(
                raw.get("acknowledged_by"),
                "client_acknowledgment.acknowledged_by",
            ),
            acknowledged_at=self._require_text(
                raw.get("acknowledged_at"),
                "client_acknowledgment.acknowledged_at",
            ),
            acknowledgment_method=self._require_text(
                raw.get("acknowledgment_method"),
                "client_acknowledgment.acknowledgment_method",
            ),
            acknowledgment_reference=self._require_text(
                raw.get("acknowledgment_reference"),
                "client_acknowledgment.acknowledgment_reference",
            ),
            acknowledgment_status=self._require_text(
                raw.get("acknowledgment_status"),
                "client_acknowledgment.acknowledgment_status",
            ),
            acknowledgment_hash=self._require_hash(
                raw.get("acknowledgment_hash"),
                "client_acknowledgment.acknowledgment_hash",
            ),
        )

        if (
            acknowledgment.acknowledgment_status
            != "client_receipt_acknowledged"
        ):
            raise RealPaidAssessmentClientResponseError(
                "client acknowledgment does not have "
                "acknowledgment_status=client_receipt_acknowledged"
            )

        expected_hash = sha256_text(
            canonical_json(
                {
                    "acknowledgment_type": (
                        PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_ID
                    ),
                    "version": (
                        PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_VERSION
                    ),
                    "schema_version": (
                        PAID_ASSESSMENT_CLIENT_ACKNOWLEDGMENT_SCHEMA_VERSION
                    ),
                    "tenant_id": acknowledgment.tenant_id,
                    "client_id": acknowledgment.client_id,
                    "engagement_id": acknowledgment.engagement_id,
                    "assessment_id": acknowledgment.assessment_id,
                    "report_id": acknowledgment.report_id,
                    "delivery_event_id": (
                        acknowledgment.delivery_event_id
                    ),
                    "delivery_event_hash": (
                        acknowledgment.delivery_event_hash
                    ),
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
                    "acknowledgment_status": (
                        acknowledgment.acknowledgment_status
                    ),
                }
            )
        )

        if expected_hash != acknowledgment.acknowledgment_hash:
            raise RealPaidAssessmentClientResponseError(
                "serialized PA006 client acknowledgment hash is invalid"
            )

        return acknowledgment

    def _build_response_evidence(
        self,
        *,
        client_acknowledgment: GovernedPaidAssessmentClientAcknowledgment,
        payload: dict[str, Any],
    ) -> ClientAssessmentResponse:
        if not isinstance(payload, dict):
            raise RealPaidAssessmentClientResponseError(
                "response_payload must be an object"
            )

        for field_name, expected in (
            ("tenant_id", client_acknowledgment.tenant_id),
            ("client_id", client_acknowledgment.client_id),
            ("engagement_id", client_acknowledgment.engagement_id),
            ("assessment_id", client_acknowledgment.assessment_id),
            ("report_id", client_acknowledgment.report_id),
            (
                "acknowledgment_id",
                client_acknowledgment.acknowledgment_id,
            ),
            (
                "acknowledgment_hash",
                client_acknowledgment.acknowledgment_hash,
            ),
        ):
            actual = self._require_text(
                payload.get(field_name),
                field_name,
            )

            if actual != expected:
                raise RealPaidAssessmentClientResponseError(
                    f"{field_name} does not match client acknowledgment"
                )

        return ClientAssessmentResponse(
            response_id=self._require_text(
                payload.get("response_id"),
                "response_id",
            ),
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
            responded_by=self._require_text(
                payload.get("responded_by"),
                "responded_by",
            ),
            responded_at=self._require_text(
                payload.get("responded_at"),
                "responded_at",
            ),
            response_method=self._require_text(
                payload.get("response_method"),
                "response_method",
            ),
            response_reference=self._require_text(
                payload.get("response_reference"),
                "response_reference",
            ),
            findings_disposition=self._require_text(
                payload.get("findings_disposition"),
                "findings_disposition",
            ),
            recommendations_disposition=self._require_text(
                payload.get("recommendations_disposition"),
                "recommendations_disposition",
            ),
            response_note=self._require_text(
                payload.get("response_note"),
                "response_note",
            ),
        )

    @staticmethod
    def _require_text(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str) or not value.strip():
            raise RealPaidAssessmentClientResponseError(
                f"{field_name} must be a non-empty string"
            )

        return value.strip()

    @staticmethod
    def _require_hash(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise RealPaidAssessmentClientResponseError(
                f"{field_name} must be a SHA-256 hex digest"
            )

        normalized = value.strip()

        if len(normalized) != 64 or normalized != normalized.lower():
            raise RealPaidAssessmentClientResponseError(
                f"{field_name} must be a lowercase SHA-256 hex digest"
            )

        try:
            int(normalized, 16)
        except ValueError as exc:
            raise RealPaidAssessmentClientResponseError(
                f"{field_name} must be a SHA-256 hex digest"
            ) from exc

        return normalized


SERVICE_TYPE = GovernanceRealPaidAssessmentClientResponseService