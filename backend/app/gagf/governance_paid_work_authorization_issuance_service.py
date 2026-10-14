from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Callable, Mapping

from backend.app.gagf.governance_assessment_auth import (
    ASSESSMENT_ADMIN_ROLE,
    AssessmentActorContext,
)
from backend.app.gagf.governance_paid_assessment_execution_handoff import (
    PaidAssessmentWorkAuthorization,
)
from backend.app.gagf.governance_paid_work_authorization_record import (
    GovernancePaidWorkAuthorizationRecord,
    build_paid_work_authorization_record,
)
from backend.app.gagf.governance_paid_work_authorization_record_store import (
    GovernancePaidWorkAuthorizationRecordStore,
)


PAID_WORK_AUTHORIZATION_ISSUANCE_SERVICE_VERSION = "0.1.0"

EXPECTED_AUTHORIZATION_PACKAGE_TYPE = (
    "assessment_factory_lite_paid_assessment_authorization_package"
)
EXPECTED_AUTHORIZATION_PACKAGE_STATUS = (
    "ready_for_paid_assessment_authorization"
)

EXPECTED_CONTRACT_EXECUTION_EVENT_TYPE = (
    "assessment_factory_lite_contract_execution_event"
)
EXPECTED_CONTRACT_EXECUTION_EVENT_STATUS = "contract_executed"

EXPECTED_PAYMENT_CONFIRMATION_EVENT_TYPE = (
    "assessment_factory_lite_payment_confirmation_event"
)
EXPECTED_PAYMENT_CONFIRMATION_EVENT_STATUS = "payment_confirmed"


class GovernancePaidWorkAuthorizationIssuanceError(ValueError):
    """Raised when PA-001 cannot be issued from governed commercial evidence."""


def _require_text(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise GovernancePaidWorkAuthorizationIssuanceError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise GovernancePaidWorkAuthorizationIssuanceError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_mapping(
    value: Any,
    field_name: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise GovernancePaidWorkAuthorizationIssuanceError(
            f"{field_name} must be a mapping"
        )

    return value


def _require_true(
    value: Any,
    field_name: str,
) -> None:
    if value is not True:
        raise GovernancePaidWorkAuthorizationIssuanceError(
            f"{field_name} must be true"
        )


def _require_false(
    value: Any,
    field_name: str,
) -> None:
    if value is not False:
        raise GovernancePaidWorkAuthorizationIssuanceError(
            f"{field_name} must be false"
        )


def _require_no_blockers(
    value: Any,
    field_name: str,
) -> None:
    if not isinstance(value, list):
        raise GovernancePaidWorkAuthorizationIssuanceError(
            f"{field_name} must be a list"
        )

    if value:
        raise GovernancePaidWorkAuthorizationIssuanceError(
            f"{field_name} must be empty"
        )


def _canonical_json(
    value: Mapping[str, Any],
) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256_mapping(
    value: Mapping[str, Any],
) -> str:
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class GovernancePaidWorkAuthorizationIssuanceResult:
    authorization: PaidAssessmentWorkAuthorization
    record: GovernancePaidWorkAuthorizationRecord

    authorization_package_id: str
    authorization_package_hash: str

    contract_execution_event_id: str
    contract_execution_event_hash: str

    payment_confirmation_event_id: str
    payment_confirmation_event_hash: str

    issued_by_actor_id: str
    service_version: str = (
        PAID_WORK_AUTHORIZATION_ISSUANCE_SERVICE_VERSION
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_version": self.service_version,
            "authorization": self.authorization.to_dict(),
            "record": self.record.to_dict(),
            "authorization_package_id": self.authorization_package_id,
            "authorization_package_hash": self.authorization_package_hash,
            "contract_execution_event_id": (
                self.contract_execution_event_id
            ),
            "contract_execution_event_hash": (
                self.contract_execution_event_hash
            ),
            "payment_confirmation_event_id": (
                self.payment_confirmation_event_id
            ),
            "payment_confirmation_event_hash": (
                self.payment_confirmation_event_hash
            ),
            "issued_by_actor_id": self.issued_by_actor_id,
            "boundaries": {
                "package_readiness_is_not_authority": True,
                "contract_execution_is_not_authority": True,
                "payment_confirmation_is_not_authority": True,
                "admin_issuance_action_creates_pa001": True,
                "pa001_is_not_execution": True,
                "pa001_is_not_delivery": True,
                "pa001_is_not_production_onboarding": True,
                "pa001_is_not_intervention_authority": True,
                "record_integrity_is_not_actor_authentication": True,
            },
        }


class GovernancePaidWorkAuthorizationIssuanceService:
    """
    Issue PA-001 only after deterministic commercial prerequisites pass.

    The service consumes evidence that is already produced by the governed
    commercial workflow. It does not treat package readiness, contract
    execution, or payment confirmation as paid-work authority by themselves.

    The caller must supply an AssessmentActorContext established by the
    application authentication/authorization boundary. Only assessment:admin
    may issue PA-001 in this service.

    The durable PA-001 store records the issued authority. Persistence itself
    does not create authority; authority is created by this explicit issuance
    operation after all prerequisite checks pass.
    """

    def __init__(
        self,
        *,
        record_store: GovernancePaidWorkAuthorizationRecordStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(
            record_store,
            GovernancePaidWorkAuthorizationRecordStore,
        ):
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "record_store must be a "
                "GovernancePaidWorkAuthorizationRecordStore"
            )

        self.record_store = record_store
        self.clock = clock or _utc_now

    def issue(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        authorization_package: Mapping[str, Any],
        contract_execution_event: Mapping[str, Any],
        payment_confirmation_event: Mapping[str, Any],
        actor: AssessmentActorContext,
    ) -> GovernancePaidWorkAuthorizationIssuanceResult:
        tenant_id = _require_text(
            tenant_id,
            "tenant_id",
        )
        client_id = _require_text(
            client_id,
            "client_id",
        )
        engagement_id = _require_text(
            engagement_id,
            "engagement_id",
        )
        assessment_id = _require_text(
            assessment_id,
            "assessment_id",
        )

        self._validate_actor(
            actor=actor,
            tenant_id=tenant_id,
        )

        authorization_package = _require_mapping(
            authorization_package,
            "authorization_package",
        )
        contract_execution_event = _require_mapping(
            contract_execution_event,
            "contract_execution_event",
        )
        payment_confirmation_event = _require_mapping(
            payment_confirmation_event,
            "payment_confirmation_event",
        )

        package_id = self._validate_authorization_package(
            authorization_package
        )
        contract_event_id = self._validate_contract_execution_event(
            contract_execution_event
        )
        payment_event_id = self._validate_payment_confirmation_event(
            payment_confirmation_event
        )

        authorization_id = self._authorization_id(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            authorization_package_id=package_id,
            contract_execution_event_id=contract_event_id,
            payment_confirmation_event_id=payment_event_id,
        )

        existing = self.record_store.get_optional(
            authorization_id=authorization_id
        )

        if existing is not None:
            if existing.hierarchy_key != "/".join(
                (
                    tenant_id,
                    client_id,
                    engagement_id,
                    assessment_id,
                )
            ):
                raise GovernancePaidWorkAuthorizationIssuanceError(
                    "existing PA-001 hierarchy does not match issuance request"
                )

            if (
                existing.contract_execution_event_id
                != contract_event_id
            ):
                raise GovernancePaidWorkAuthorizationIssuanceError(
                    "existing PA-001 contract event does not match issuance request"
                )

            authorization = existing.to_paid_work_authorization()

            return self._result(
                authorization=authorization,
                record=existing,
                authorization_package=authorization_package,
                authorization_package_id=package_id,
                contract_execution_event=contract_execution_event,
                contract_execution_event_id=contract_event_id,
                payment_confirmation_event=payment_confirmation_event,
                payment_confirmation_event_id=payment_event_id,
                actor=actor,
            )

        authorized_at = self._authorized_at()

        authorization = PaidAssessmentWorkAuthorization(
            authorization_id=authorization_id,
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
            contract_execution_event_id=contract_event_id,
            authorized_by=actor.actor_id,
            authorized_at=authorized_at,
            paid_assessment_authorized=True,
        )

        record = build_paid_work_authorization_record(
            authorization=authorization
        )

        stored = self.record_store.save(
            record=record
        )

        return self._result(
            authorization=stored.to_paid_work_authorization(),
            record=stored,
            authorization_package=authorization_package,
            authorization_package_id=package_id,
            contract_execution_event=contract_execution_event,
            contract_execution_event_id=contract_event_id,
            payment_confirmation_event=payment_confirmation_event,
            payment_confirmation_event_id=payment_event_id,
            actor=actor,
        )

    def _authorized_at(self) -> str:
        value = self.clock()

        if not isinstance(value, datetime):
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "clock must return a datetime"
            )

        if value.tzinfo is None or value.utcoffset() is None:
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "clock must return a timezone-aware datetime"
            )

        return value.isoformat()

    @staticmethod
    def _validate_actor(
        *,
        actor: AssessmentActorContext,
        tenant_id: str,
    ) -> None:
        if not isinstance(
            actor,
            AssessmentActorContext,
        ):
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "actor must be an AssessmentActorContext"
            )

        actor_tenant = _require_text(
            actor.tenant_id,
            "actor.tenant_id",
        )

        if actor_tenant != tenant_id:
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "actor tenant does not match PA-001 tenant"
            )

        _require_text(
            actor.actor_id,
            "actor.actor_id",
        )

        if not actor.has_any_role(
            ASSESSMENT_ADMIN_ROLE
        ):
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "PA-001 issuance requires assessment:admin"
            )

    @staticmethod
    def _validate_authorization_package(
        package: Mapping[str, Any],
    ) -> str:
        if package.get("status") != "ok":
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "authorization package status must be ok"
            )

        if (
            package.get("event_type")
            != EXPECTED_AUTHORIZATION_PACKAGE_TYPE
        ):
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "unsupported authorization package event_type"
            )

        if (
            package.get("package_status")
            != EXPECTED_AUTHORIZATION_PACKAGE_STATUS
        ):
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "authorization package is not ready"
            )

        package_id = _require_text(
            package.get("authorization_id"),
            "authorization_package.authorization_id",
        )

        _require_no_blockers(
            package.get("package_blockers"),
            "authorization_package.package_blockers",
        )

        human_authorization = _require_mapping(
            package.get("human_authorization"),
            "authorization_package.human_authorization",
        )

        commercial_boundary = _require_mapping(
            package.get("commercial_boundary"),
            "authorization_package.commercial_boundary",
        )

        governance_boundary = _require_mapping(
            package.get("governance_boundary"),
            "authorization_package.governance_boundary",
        )

        _require_true(
            human_authorization.get(
                "human_operator_authorized_package"
            ),
            (
                "authorization_package.human_authorization."
                "human_operator_authorized_package"
            ),
        )

        _require_true(
            commercial_boundary.get(
                "authorization_package_ready"
            ),
            (
                "authorization_package.commercial_boundary."
                "authorization_package_ready"
            ),
        )

        _require_false(
            commercial_boundary.get(
                "paid_assessment_authorized"
            ),
            (
                "authorization_package.commercial_boundary."
                "paid_assessment_authorized"
            ),
        )

        for field_name in (
            "requires_separate_contract",
            "requires_separate_invoice",
            "requires_separate_payment_confirmation",
        ):
            _require_true(
                commercial_boundary.get(field_name),
                (
                    "authorization_package.commercial_boundary."
                    f"{field_name}"
                ),
            )

        GovernancePaidWorkAuthorizationIssuanceService._validate_governance_boundary(
            governance_boundary,
            boundary_prefix="authorization_package.governance_boundary",
            required_true_field=(
                "authorization_is_package_readiness_only"
            ),
        )

        return package_id

    @staticmethod
    def _validate_contract_execution_event(
        event: Mapping[str, Any],
    ) -> str:
        if event.get("status") != "ok":
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "contract execution event status must be ok"
            )

        if (
            event.get("event_type")
            != EXPECTED_CONTRACT_EXECUTION_EVENT_TYPE
        ):
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "unsupported contract execution event_type"
            )

        if (
            event.get("event_status")
            != EXPECTED_CONTRACT_EXECUTION_EVENT_STATUS
        ):
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "contract execution event must be contract_executed"
            )

        event_id = _require_text(
            event.get("contract_execution_event_id"),
            "contract_execution_event.contract_execution_event_id",
        )

        _require_no_blockers(
            event.get("event_blockers"),
            "contract_execution_event.event_blockers",
        )

        execution_evidence = _require_mapping(
            event.get("execution_evidence"),
            "contract_execution_event.execution_evidence",
        )
        commercial_boundary = _require_mapping(
            event.get("commercial_boundary"),
            "contract_execution_event.commercial_boundary",
        )
        governance_boundary = _require_mapping(
            event.get("governance_boundary"),
            "contract_execution_event.governance_boundary",
        )

        _require_true(
            execution_evidence.get("contract_executed"),
            (
                "contract_execution_event.execution_evidence."
                "contract_executed"
            ),
        )
        _require_true(
            commercial_boundary.get("contract_executed"),
            (
                "contract_execution_event.commercial_boundary."
                "contract_executed"
            ),
        )
        _require_false(
            commercial_boundary.get(
                "paid_assessment_authorized"
            ),
            (
                "contract_execution_event.commercial_boundary."
                "paid_assessment_authorized"
            ),
        )
        _require_true(
            commercial_boundary.get(
                "requires_final_paid_work_authorization"
            ),
            (
                "contract_execution_event.commercial_boundary."
                "requires_final_paid_work_authorization"
            ),
        )

        GovernancePaidWorkAuthorizationIssuanceService._validate_governance_boundary(
            governance_boundary,
            boundary_prefix="contract_execution_event.governance_boundary",
            required_true_field=(
                "contract_execution_event_is_not_paid_work_authorization"
            ),
        )

        return event_id

    @staticmethod
    def _validate_payment_confirmation_event(
        event: Mapping[str, Any],
    ) -> str:
        if event.get("status") != "ok":
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "payment confirmation event status must be ok"
            )

        if (
            event.get("event_type")
            != EXPECTED_PAYMENT_CONFIRMATION_EVENT_TYPE
        ):
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "unsupported payment confirmation event_type"
            )

        if (
            event.get("event_status")
            != EXPECTED_PAYMENT_CONFIRMATION_EVENT_STATUS
        ):
            raise GovernancePaidWorkAuthorizationIssuanceError(
                "payment confirmation event must be payment_confirmed"
            )

        event_id = _require_text(
            event.get("payment_confirmation_event_id"),
            (
                "payment_confirmation_event."
                "payment_confirmation_event_id"
            ),
        )

        _require_no_blockers(
            event.get("event_blockers"),
            "payment_confirmation_event.event_blockers",
        )

        payment_record = _require_mapping(
            event.get("payment_confirmation_record"),
            "payment_confirmation_event.payment_confirmation_record",
        )
        reconciliation_record = _require_mapping(
            event.get("reconciliation_record"),
            "payment_confirmation_event.reconciliation_record",
        )
        operator_confirmation = _require_mapping(
            event.get("operator_confirmation"),
            "payment_confirmation_event.operator_confirmation",
        )
        commercial_boundary = _require_mapping(
            event.get("commercial_boundary"),
            "payment_confirmation_event.commercial_boundary",
        )
        governance_boundary = _require_mapping(
            event.get("governance_boundary"),
            "payment_confirmation_event.governance_boundary",
        )

        _require_true(
            payment_record.get("payment_confirmed"),
            (
                "payment_confirmation_event.payment_confirmation_record."
                "payment_confirmed"
            ),
        )
        _require_true(
            reconciliation_record.get(
                "reconciliation_recorded"
            ),
            (
                "payment_confirmation_event.reconciliation_record."
                "reconciliation_recorded"
            ),
        )
        _require_true(
            operator_confirmation.get(
                "human_operator_confirmed_payment"
            ),
            (
                "payment_confirmation_event.operator_confirmation."
                "human_operator_confirmed_payment"
            ),
        )
        _require_true(
            commercial_boundary.get("payment_confirmed"),
            (
                "payment_confirmation_event.commercial_boundary."
                "payment_confirmed"
            ),
        )
        _require_false(
            commercial_boundary.get(
                "paid_assessment_authorized"
            ),
            (
                "payment_confirmation_event.commercial_boundary."
                "paid_assessment_authorized"
            ),
        )
        _require_true(
            commercial_boundary.get(
                "requires_final_paid_work_authorization"
            ),
            (
                "payment_confirmation_event.commercial_boundary."
                "requires_final_paid_work_authorization"
            ),
        )

        GovernancePaidWorkAuthorizationIssuanceService._validate_governance_boundary(
            governance_boundary,
            boundary_prefix="payment_confirmation_event.governance_boundary",
            required_true_field=(
                "payment_confirmation_event_is_not_paid_work_authorization"
            ),
        )

        return event_id

    @staticmethod
    def _validate_governance_boundary(
        boundary: Mapping[str, Any],
        *,
        boundary_prefix: str,
        required_true_field: str,
    ) -> None:
        _require_true(
            boundary.get("gagf_kernel_authoritative"),
            f"{boundary_prefix}.gagf_kernel_authoritative",
        )
        _require_true(
            boundary.get("human_boundary_required"),
            f"{boundary_prefix}.human_boundary_required",
        )
        _require_false(
            boundary.get("ai_override_allowed"),
            f"{boundary_prefix}.ai_override_allowed",
        )
        _require_true(
            boundary.get(required_true_field),
            f"{boundary_prefix}.{required_true_field}",
        )

    @staticmethod
    def _authorization_id(
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        authorization_package_id: str,
        contract_execution_event_id: str,
        payment_confirmation_event_id: str,
    ) -> str:
        identity_payload = {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "engagement_id": engagement_id,
            "assessment_id": assessment_id,
            "authorization_package_id": authorization_package_id,
            "contract_execution_event_id": contract_execution_event_id,
            "payment_confirmation_event_id": payment_confirmation_event_id,
        }

        digest = hashlib.sha256(
            _canonical_json(identity_payload).encode("utf-8")
        ).hexdigest()

        return f"pa-001-{digest}"

    @staticmethod
    def _result(
        *,
        authorization: PaidAssessmentWorkAuthorization,
        record: GovernancePaidWorkAuthorizationRecord,
        authorization_package: Mapping[str, Any],
        authorization_package_id: str,
        contract_execution_event: Mapping[str, Any],
        contract_execution_event_id: str,
        payment_confirmation_event: Mapping[str, Any],
        payment_confirmation_event_id: str,
        actor: AssessmentActorContext,
    ) -> GovernancePaidWorkAuthorizationIssuanceResult:
        return GovernancePaidWorkAuthorizationIssuanceResult(
            authorization=authorization,
            record=record,
            authorization_package_id=authorization_package_id,
            authorization_package_hash=_sha256_mapping(
                authorization_package
            ),
            contract_execution_event_id=contract_execution_event_id,
            contract_execution_event_hash=_sha256_mapping(
                contract_execution_event
            ),
            payment_confirmation_event_id=payment_confirmation_event_id,
            payment_confirmation_event_hash=_sha256_mapping(
                payment_confirmation_event
            ),
            issued_by_actor_id=actor.actor_id,
        )


SERVICE_TYPE = GovernancePaidWorkAuthorizationIssuanceService
