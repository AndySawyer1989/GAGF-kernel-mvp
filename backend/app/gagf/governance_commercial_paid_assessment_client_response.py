from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_commercial_paid_assessment_execution import (
    GovernanceCommercialPaidAssessmentExecutionService,
)
from backend.app.gagf.governance_paid_assessment_client_response import (
    PaidAssessmentClientResponseError,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    ACKNOWLEDGMENT_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_real_paid_assessment_client_response import (
    GovernanceRealPaidAssessmentClientResponseService,
    RealPaidAssessmentClientResponseError,
)


COMMERCIAL_PAID_ASSESSMENT_CLIENT_RESPONSE_ID = (
    "governance-commercial-paid-assessment-client-response"
)
COMMERCIAL_PAID_ASSESSMENT_CLIENT_RESPONSE_VERSION = "0.1.0"
COMMERCIAL_PAID_ASSESSMENT_CLIENT_RESPONSE_SCHEMA_VERSION = "1.0.0"

CLIENT_RESPONSE_STATUS = "client_response_recorded"


class CommercialPaidAssessmentClientResponseError(RuntimeError):
    """Raised when a commercial client response cannot be recorded safely."""


@dataclass(frozen=True, slots=True)
class CommercialPaidAssessmentClientResponseResult:
    tenant_id: str
    client_id: str
    engagement_id: str
    assessment_id: str
    report_id: str

    response_id: str
    responded_by: str
    responded_at: str
    response_method: str
    response_reference: str
    findings_disposition: str
    recommendations_disposition: str
    response_note: str

    response_status: str = CLIENT_RESPONSE_STATUS

    result_type: str = (
        COMMERCIAL_PAID_ASSESSMENT_CLIENT_RESPONSE_ID
    )
    version: str = (
        COMMERCIAL_PAID_ASSESSMENT_CLIENT_RESPONSE_VERSION
    )
    schema_version: str = (
        COMMERCIAL_PAID_ASSESSMENT_CLIENT_RESPONSE_SCHEMA_VERSION
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
            "result_type": self.result_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "report_id": self.report_id,
            "response_id": self.response_id,
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
            "client_response_recorded": True,
            "boundaries": {
                "response_requires_prior_receipt": True,
                "response_is_not_inferred_from_receipt": True,
                "findings_acknowledgment_is_not_validation": True,
                "recommendation_acceptance_is_not_implementation": True,
                "response_is_not_closeout": True,
                "response_is_not_intervention_request": True,
                "response_is_not_intervention_authorization": True,
                "response_is_not_execution_authority": True,
                "response_is_not_roi_verification": True,
                "response_is_not_customer_outcome_verification": True,
                "pa007_remains_client_response_authority": True,
            },
        }


class GovernanceCommercialPaidAssessmentClientResponseService:
    """
    Commercial adapter over the existing real paid-assessment
    client-response lifecycle.

    Authority remains with:

        persisted PA006 acknowledgment
        -> GovernanceRealPaidAssessmentClientResponseService
        -> PA007 governed client response
        -> PA013 resumable operator
        -> PA012 lifecycle persistence

    The browser does not supply hierarchy, report identity,
    acknowledgment identity/hash, or database/repository paths.
    """

    def __init__(
        self,
        *,
        execution_service: (
            GovernanceCommercialPaidAssessmentExecutionService
        ),
    ) -> None:
        if not isinstance(
            execution_service,
            GovernanceCommercialPaidAssessmentExecutionService,
        ):
            raise TypeError(
                "execution_service must be a "
                "GovernanceCommercialPaidAssessmentExecutionService"
            )

        self._execution_service = execution_service
        self._response_service = (
            GovernanceRealPaidAssessmentClientResponseService()
        )

        # Optional downstream controlled-trial observer.
        #
        # PA-007 and PA-012 remain authoritative. This hook observes
        # only an already-authoritative commercial client response.
        self._customer_trial_client_response_observation_recorder = None

    def configure_customer_trial_client_response_observation_recorder(
        self,
        *,
        recorder: Any,
    ) -> None:
        from backend.app.gagf.governance_customer_trial_client_response_observation_recording_bridge import (
            GovernanceCustomerTrialClientResponseObservationRecordingBridge,
        )

        if not isinstance(
            recorder,
            GovernanceCustomerTrialClientResponseObservationRecordingBridge,
        ):
            raise CommercialPaidAssessmentClientResponseError(
                "recorder must be a "
                "GovernanceCustomerTrialClientResponseObservationRecordingBridge"
            )

        self._customer_trial_client_response_observation_recorder = recorder

    def record(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        response_payload: dict[str, Any],
    ) -> CommercialPaidAssessmentClientResponseResult:
        context = CommercialHierarchyContext(
            tenant_id=self._require_text(
                tenant_id,
                "tenant_id",
            ),
            client_id=self._require_text(
                client_id,
                "client_id",
            ),
            engagement_id=self._require_text(
                engagement_id,
                "engagement_id",
            ),
            assessment_id=self._require_text(
                assessment_id,
                "assessment_id",
            ),
        )

        if not isinstance(response_payload, dict):
            raise CommercialPaidAssessmentClientResponseError(
                "response_payload must be an object"
            )

        database_path = (
            self._execution_service.database_path_for_hierarchy(
                tenant_id=context.tenant_id,
                client_id=context.client_id,
                engagement_id=context.engagement_id,
                assessment_id=context.assessment_id,
            )
        )

        database_path = Path(database_path)

        if not database_path.exists():
            raise CommercialPaidAssessmentClientResponseError(
                "governed paid-assessment database does not exist"
            )

        if not database_path.is_file():
            raise CommercialPaidAssessmentClientResponseError(
                "governed paid-assessment database path is not a file"
            )

        repository = GovernanceAssessmentRepository(
            database_path
        )

        # Require the actual assessment record.
        repository.get_assessment(
            context=context
        )

        if not repository.verify_chain(
            context=context
        ):
            raise CommercialPaidAssessmentClientResponseError(
                "governed assessment repository chain is invalid"
            )

        artifacts = repository.list_artifacts(
            context=context
        )

        acknowledgment_artifacts = [
            artifact
            for artifact in artifacts
            if artifact.artifact_type
            == ACKNOWLEDGMENT_ARTIFACT_TYPE
        ]

        if len(acknowledgment_artifacts) != 1:
            raise CommercialPaidAssessmentClientResponseError(
                "exactly one persisted client receipt "
                "acknowledgment is required"
            )

        try:
            acknowledgment_payload = json.loads(
                acknowledgment_artifacts[0].payload_json
            )
        except json.JSONDecodeError as exc:
            raise CommercialPaidAssessmentClientResponseError(
                "persisted client acknowledgment payload "
                "is not valid JSON"
            ) from exc

        if not isinstance(
            acknowledgment_payload,
            dict,
        ):
            raise CommercialPaidAssessmentClientResponseError(
                "persisted client acknowledgment payload "
                "must be an object"
            )

        self._require_persisted_acknowledgment_hierarchy(
            context=context,
            acknowledgment_payload=acknowledgment_payload,
        )

        report_id = self._require_text(
            acknowledgment_payload.get("report_id"),
            "persisted acknowledgment report_id",
        )

        acknowledgment_id = self._require_text(
            acknowledgment_payload.get(
                "acknowledgment_id"
            ),
            "persisted acknowledgment acknowledgment_id",
        )

        acknowledgment_hash = self._require_text(
            acknowledgment_payload.get(
                "acknowledgment_hash"
            ),
            "persisted acknowledgment acknowledgment_hash",
        )

        # Reconstruct only the serialized wrapper required by the
        # already-authoritative real response bridge. The actual
        # acknowledgment content comes from immutable PA012 evidence.
        acknowledged_payload = {
            "client_receipt_recording_passed": True,
            "client_receipt_acknowledged": True,
            "result": {
                "client_acknowledgment": (
                    acknowledgment_payload
                ),
            },
        }

        governed_response_payload = {
            "response_id": self._require_text(
                response_payload.get("response_id"),
                "response_id",
            ),
            "tenant_id": context.tenant_id,
            "client_id": context.client_id,
            "engagement_id": context.engagement_id,
            "assessment_id": context.assessment_id,
            "report_id": report_id,
            "acknowledgment_id": acknowledgment_id,
            "acknowledgment_hash": acknowledgment_hash,
            "responded_by": self._require_text(
                response_payload.get("responded_by"),
                "responded_by",
            ),
            "responded_at": self._require_text(
                response_payload.get("responded_at"),
                "responded_at",
            ),
            "response_method": self._require_text(
                response_payload.get("response_method"),
                "response_method",
            ),
            "response_reference": self._require_text(
                response_payload.get("response_reference"),
                "response_reference",
            ),
            "findings_disposition": self._require_text(
                response_payload.get(
                    "findings_disposition"
                ),
                "findings_disposition",
            ),
            "recommendations_disposition": (
                self._require_text(
                    response_payload.get(
                        "recommendations_disposition"
                    ),
                    "recommendations_disposition",
                )
            ),
            # PA007 explicitly permits an empty response note,
            # but it must still be a string.
            "response_note": self._require_string(
                response_payload.get(
                    "response_note",
                    "",
                ),
                "response_note",
            ),
        }

        try:
            result = self._response_service.record(
                database_path=database_path,
                acknowledged_payload=acknowledged_payload,
                response_payload=governed_response_payload,
            )
        except (
            RealPaidAssessmentClientResponseError,
            PaidAssessmentClientResponseError,
        ) as exc:
            raise CommercialPaidAssessmentClientResponseError(
                str(exc)
            ) from exc

        if (
            result.response_status
            != CLIENT_RESPONSE_STATUS
        ):
            raise CommercialPaidAssessmentClientResponseError(
                "governed client-response service did not "
                "produce client_response_recorded"
            )

        client_response = result.client_response

        expected_hierarchy = (
            context.tenant_id,
            context.client_id,
            context.engagement_id,
            context.assessment_id,
        )
        actual_hierarchy = (
            client_response.tenant_id,
            client_response.client_id,
            client_response.engagement_id,
            client_response.assessment_id,
        )

        if actual_hierarchy != expected_hierarchy:
            raise CommercialPaidAssessmentClientResponseError(
                "governed client response hierarchy does "
                "not match requested hierarchy"
            )

        if client_response.report_id != report_id:
            raise CommercialPaidAssessmentClientResponseError(
                "governed client response report_id does "
                "not match persisted acknowledgment"
            )

        if (
            client_response.acknowledgment_id
            != acknowledgment_id
        ):
            raise CommercialPaidAssessmentClientResponseError(
                "governed client response acknowledgment_id "
                "does not match persisted acknowledgment"
            )

        if (
            client_response.acknowledgment_hash
            != acknowledgment_hash
        ):
            raise CommercialPaidAssessmentClientResponseError(
                "governed client response acknowledgment_hash "
                "does not match persisted acknowledgment"
            )

        if not repository.verify_chain(
            context=context
        ):
            raise CommercialPaidAssessmentClientResponseError(
                "governed assessment repository chain became "
                "invalid after client response persistence"
            )

        result = CommercialPaidAssessmentClientResponseResult(
            tenant_id=context.tenant_id,
            client_id=context.client_id,
            engagement_id=context.engagement_id,
            assessment_id=context.assessment_id,
            report_id=client_response.report_id,
            response_id=client_response.response_id,
            responded_by=client_response.responded_by,
            responded_at=client_response.responded_at,
            response_method=client_response.response_method,
            response_reference=(
                client_response.response_reference
            ),
            findings_disposition=(
                client_response.findings_disposition
            ),
            recommendations_disposition=(
                client_response.recommendations_disposition
            ),
            response_note=client_response.response_note,
        )

        if (
            self._customer_trial_client_response_observation_recorder
            is not None
        ):
            self._customer_trial_client_response_observation_recorder.capture(
                commercial_client_response=result
            )

        return result

    def _require_persisted_acknowledgment_hierarchy(
        self,
        *,
        context: CommercialHierarchyContext,
        acknowledgment_payload: dict[str, Any],
    ) -> None:
        expected = {
            "tenant_id": context.tenant_id,
            "client_id": context.client_id,
            "engagement_id": context.engagement_id,
            "assessment_id": context.assessment_id,
        }

        for field_name, expected_value in expected.items():
            actual = self._require_text(
                acknowledgment_payload.get(field_name),
                (
                    "persisted acknowledgment "
                    + field_name
                ),
            )

            if actual != expected_value:
                raise CommercialPaidAssessmentClientResponseError(
                    "persisted client acknowledgment hierarchy "
                    f"does not match requested {field_name}"
                )

        status = self._require_text(
            acknowledgment_payload.get(
                "acknowledgment_status"
            ),
            "persisted acknowledgment acknowledgment_status",
        )

        if status != "client_receipt_acknowledged":
            raise CommercialPaidAssessmentClientResponseError(
                "persisted acknowledgment is not "
                "client_receipt_acknowledged"
            )

    @staticmethod
    def _require_text(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise CommercialPaidAssessmentClientResponseError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise CommercialPaidAssessmentClientResponseError(
                f"{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _require_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise CommercialPaidAssessmentClientResponseError(
                f"{field_name} must be a string"
            )

        return value.strip()


SERVICE_TYPE = (
    GovernanceCommercialPaidAssessmentClientResponseService
)
