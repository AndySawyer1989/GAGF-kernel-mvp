from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any


PAID_ASSESSMENT_EXECUTION_HANDOFF_ID = (
    "governance-paid-assessment-execution-handoff"
)
PAID_ASSESSMENT_EXECUTION_HANDOFF_VERSION = "0.1.0"
PAID_ASSESSMENT_EXECUTION_HANDOFF_SCHEMA_VERSION = "1.0.0"

EXPECTED_CONTRACT_EVENT_TYPE = (
    "assessment_factory_lite_contract_execution_event"
)
EXPECTED_CONTRACT_EVENT_STATUS = "contract_executed"


class PaidAssessmentExecutionHandoffError(ValueError):
    """Raised when a paid-assessment handoff is not constitutionally valid."""


class PaidAssessmentExecutionHandoffStatus(str, Enum):
    READY = "ready_for_assessment_execution"


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PaidAssessmentExecutionHandoffError(
            f"{field_name} must be non-empty text"
        )
    return value.strip()


def require_bool_true(value: Any, field_name: str) -> None:
    if value is not True:
        raise PaidAssessmentExecutionHandoffError(
            f"{field_name} must be true"
        )


@dataclass(frozen=True, slots=True)
class PaidAssessmentWorkAuthorization:
    authorization_id: str
    tenant_id: str
    engagement_id: str
    assessment_id: str
    contract_execution_event_id: str
    authorized_by: str
    authorized_at: str
    paid_assessment_authorized: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "authorization_id",
            "tenant_id",
            "engagement_id",
            "assessment_id",
            "contract_execution_event_id",
            "authorized_by",
            "authorized_at",
        ):
            object.__setattr__(
                self,
                field_name,
                require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        require_bool_true(
            self.paid_assessment_authorized,
            "paid_assessment_authorized",
        )

        try:
            datetime.fromisoformat(
                self.authorized_at.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise PaidAssessmentExecutionHandoffError(
                "authorized_at must be ISO-8601"
            ) from exc

    @property
    def authorization_hash(self) -> str:
        return sha256_text(
            canonical_json(
                {
                    "authorization_id": self.authorization_id,
                    "tenant_id": self.tenant_id,
                    "engagement_id": self.engagement_id,
                    "assessment_id": self.assessment_id,
                    "contract_execution_event_id": (
                        self.contract_execution_event_id
                    ),
                    "authorized_by": self.authorized_by,
                    "authorized_at": self.authorized_at,
                    "paid_assessment_authorized": (
                        self.paid_assessment_authorized
                    ),
                }
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorization_id": self.authorization_id,
            "tenant_id": self.tenant_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "contract_execution_event_id": (
                self.contract_execution_event_id
            ),
            "authorized_by": self.authorized_by,
            "authorized_at": self.authorized_at,
            "paid_assessment_authorized": (
                self.paid_assessment_authorized
            ),
            "authorization_hash": self.authorization_hash,
        }


@dataclass(frozen=True, slots=True)
class PaidAssessmentExecutionHandoff:
    tenant_id: str
    engagement_id: str
    assessment_id: str
    contract_execution_event_id: str
    contract_execution_event_hash: str
    paid_work_authorization_id: str
    paid_work_authorization_hash: str
    assessment_execution_request_hash: str
    status: PaidAssessmentExecutionHandoffStatus
    handoff_hash: str
    handoff_type: str = PAID_ASSESSMENT_EXECUTION_HANDOFF_ID
    version: str = PAID_ASSESSMENT_EXECUTION_HANDOFF_VERSION
    schema_version: str = (
        PAID_ASSESSMENT_EXECUTION_HANDOFF_SCHEMA_VERSION
    )

    @property
    def hierarchy_key(self) -> str:
        return "/".join(
            (
                self.tenant_id,
                self.engagement_id,
                self.assessment_id,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "handoff_type": self.handoff_type,
            "version": self.version,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "engagement_id": self.engagement_id,
            "assessment_id": self.assessment_id,
            "hierarchy_key": self.hierarchy_key,
            "contract_execution_event_id": (
                self.contract_execution_event_id
            ),
            "contract_execution_event_hash": (
                self.contract_execution_event_hash
            ),
            "paid_work_authorization_id": (
                self.paid_work_authorization_id
            ),
            "paid_work_authorization_hash": (
                self.paid_work_authorization_hash
            ),
            "assessment_execution_request_hash": (
                self.assessment_execution_request_hash
            ),
            "status": self.status.value,
            "handoff_hash": self.handoff_hash,
        }


class GovernancePaidAssessmentExecutionHandoffService:
    """
    Builds the governed boundary artifact between commercial contract
    execution and assessment execution.

    This service does not execute an assessment.

    A contract-execution event proves contract execution only. A separate
    explicit human paid-work authorization is required before this service
    can produce a READY handoff.
    """

    def build_handoff(
        self,
        *,
        contract_execution_event: dict[str, Any],
        paid_work_authorization: PaidAssessmentWorkAuthorization,
        assessment_execution_request: Any,
    ) -> PaidAssessmentExecutionHandoff:
        self._validate_contract_execution_event(
            contract_execution_event
        )

        context = getattr(
            assessment_execution_request,
            "context",
            None,
        )

        if context is None:
            raise PaidAssessmentExecutionHandoffError(
                "assessment_execution_request requires context"
            )

        tenant_id = require_text(
            getattr(context, "tenant_id", ""),
            "assessment_execution_request.context.tenant_id",
        )
        engagement_id = require_text(
            getattr(context, "engagement_id", ""),
            "assessment_execution_request.context.engagement_id",
        )
        assessment_id = require_text(
            getattr(context, "assessment_id", ""),
            "assessment_execution_request.context.assessment_id",
        )

        self._validate_hierarchy_binding(
            paid_work_authorization=paid_work_authorization,
            tenant_id=tenant_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )

        contract_execution_event_id = require_text(
            contract_execution_event.get(
                "contract_execution_event_id",
                "",
            ),
            "contract_execution_event_id",
        )

        if (
            paid_work_authorization.contract_execution_event_id
            != contract_execution_event_id
        ):
            raise PaidAssessmentExecutionHandoffError(
                "paid-work authorization is bound to a different "
                "contract_execution_event_id"
            )

        request_to_dict = getattr(
            assessment_execution_request,
            "to_dict",
            None,
        )

        if not callable(request_to_dict):
            raise PaidAssessmentExecutionHandoffError(
                "assessment_execution_request must expose to_dict()"
            )

        request_payload = request_to_dict()

        if not isinstance(request_payload, dict):
            raise PaidAssessmentExecutionHandoffError(
                "assessment_execution_request.to_dict() must return a dict"
            )

        expected_hierarchy_key = "/".join(
            (
                tenant_id,
                engagement_id,
                assessment_id,
            )
        )

        if (
            request_payload.get("hierarchy_key")
            != expected_hierarchy_key
        ):
            raise PaidAssessmentExecutionHandoffError(
                "assessment execution request hierarchy_key mismatch"
            )

        contract_execution_event_hash = sha256_text(
            canonical_json(contract_execution_event)
        )
        assessment_execution_request_hash = sha256_text(
            canonical_json(request_payload)
        )

        handoff_payload = {
            "handoff_type": PAID_ASSESSMENT_EXECUTION_HANDOFF_ID,
            "version": PAID_ASSESSMENT_EXECUTION_HANDOFF_VERSION,
            "schema_version": (
                PAID_ASSESSMENT_EXECUTION_HANDOFF_SCHEMA_VERSION
            ),
            "tenant_id": tenant_id,
            "engagement_id": engagement_id,
            "assessment_id": assessment_id,
            "contract_execution_event_id": (
                contract_execution_event_id
            ),
            "contract_execution_event_hash": (
                contract_execution_event_hash
            ),
            "paid_work_authorization_id": (
                paid_work_authorization.authorization_id
            ),
            "paid_work_authorization_hash": (
                paid_work_authorization.authorization_hash
            ),
            "assessment_execution_request_hash": (
                assessment_execution_request_hash
            ),
            "status": (
                PaidAssessmentExecutionHandoffStatus.READY.value
            ),
        }

        return PaidAssessmentExecutionHandoff(
            tenant_id=tenant_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            contract_execution_event_id=(
                contract_execution_event_id
            ),
            contract_execution_event_hash=(
                contract_execution_event_hash
            ),
            paid_work_authorization_id=(
                paid_work_authorization.authorization_id
            ),
            paid_work_authorization_hash=(
                paid_work_authorization.authorization_hash
            ),
            assessment_execution_request_hash=(
                assessment_execution_request_hash
            ),
            status=PaidAssessmentExecutionHandoffStatus.READY,
            handoff_hash=sha256_text(
                canonical_json(handoff_payload)
            ),
        )

    def _validate_contract_execution_event(
        self,
        event: dict[str, Any],
    ) -> None:
        if not isinstance(event, dict):
            raise PaidAssessmentExecutionHandoffError(
                "contract_execution_event must be a dict"
            )

        if event.get("status") != "ok":
            raise PaidAssessmentExecutionHandoffError(
                "contract execution event status must be ok"
            )

        if event.get("event_type") != EXPECTED_CONTRACT_EVENT_TYPE:
            raise PaidAssessmentExecutionHandoffError(
                "unsupported contract execution event_type"
            )

        if (
            event.get("event_status")
            != EXPECTED_CONTRACT_EVENT_STATUS
        ):
            raise PaidAssessmentExecutionHandoffError(
                "contract execution event must be contract_executed"
            )

        require_text(
            event.get("contract_execution_event_id", ""),
            "contract_execution_event_id",
        )

        execution_evidence = event.get(
            "execution_evidence",
            {},
        )
        event_checklist = event.get(
            "event_checklist",
            {},
        )
        commercial_boundary = event.get(
            "commercial_boundary",
            {},
        )
        governance_boundary = event.get(
            "governance_boundary",
            {},
        )

        require_bool_true(
            execution_evidence.get("contract_executed"),
            "execution_evidence.contract_executed",
        )
        require_bool_true(
            event_checklist.get(
                "contract_execution_review_ready"
            ),
            "event_checklist.contract_execution_review_ready",
        )
        require_bool_true(
            event_checklist.get(
                "contract_execution_confirmed"
            ),
            "event_checklist.contract_execution_confirmed",
        )
        require_bool_true(
            event_checklist.get(
                "executed_contract_reference_recorded"
            ),
            (
                "event_checklist."
                "executed_contract_reference_recorded"
            ),
        )
        require_bool_true(
            event_checklist.get("executed_at_recorded"),
            "event_checklist.executed_at_recorded",
        )
        require_bool_true(
            event_checklist.get(
                "all_required_signatures_recorded"
            ),
            (
                "event_checklist."
                "all_required_signatures_recorded"
            ),
        )
        require_bool_true(
            event_checklist.get(
                "human_operator_confirmed_execution"
            ),
            (
                "event_checklist."
                "human_operator_confirmed_execution"
            ),
        )

        require_bool_true(
            commercial_boundary.get("contract_executed"),
            "commercial_boundary.contract_executed",
        )

        if (
            commercial_boundary.get(
                "paid_assessment_authorized"
            )
            is not False
        ):
            raise PaidAssessmentExecutionHandoffError(
                "contract execution event must not itself authorize "
                "paid assessment work"
            )

        require_bool_true(
            commercial_boundary.get(
                "requires_final_paid_work_authorization"
            ),
            (
                "commercial_boundary."
                "requires_final_paid_work_authorization"
            ),
        )

        require_bool_true(
            governance_boundary.get(
                "human_boundary_required"
            ),
            "governance_boundary.human_boundary_required",
        )
        require_bool_true(
            governance_boundary.get(
                "gagf_kernel_authoritative"
            ),
            "governance_boundary.gagf_kernel_authoritative",
        )

        if (
            governance_boundary.get("ai_override_allowed")
            is not False
        ):
            raise PaidAssessmentExecutionHandoffError(
                "governance boundary must prohibit AI override"
            )

        require_bool_true(
            governance_boundary.get(
                "contract_execution_event_is_not_paid_work_authorization"
            ),
            (
                "governance_boundary."
                "contract_execution_event_is_not_paid_work_authorization"
            ),
        )

        blockers = event.get("event_blockers", [])

        if blockers:
            raise PaidAssessmentExecutionHandoffError(
                "contract execution event contains blockers"
            )

    def _validate_hierarchy_binding(
        self,
        *,
        paid_work_authorization: PaidAssessmentWorkAuthorization,
        tenant_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> None:
        expected = (
            tenant_id,
            engagement_id,
            assessment_id,
        )
        actual = (
            paid_work_authorization.tenant_id,
            paid_work_authorization.engagement_id,
            paid_work_authorization.assessment_id,
        )

        if actual != expected:
            raise PaidAssessmentExecutionHandoffError(
                "paid-work authorization hierarchy does not match "
                "assessment execution request"
            )


SERVICE = GovernancePaidAssessmentExecutionHandoffService()