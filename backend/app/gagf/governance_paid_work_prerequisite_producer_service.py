from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Callable, Mapping

from backend.app.gagf.governance_assessment_auth import AssessmentActorContext

from backend.app.gagf.assessment_factory_lite_contract_execution_event_service import (
    AssessmentFactoryLiteContractExecutionEventService,
)
from backend.app.gagf.assessment_factory_lite_paid_assessment_authorization_package_service import (
    AssessmentFactoryLitePaidAssessmentAuthorizationPackageService,
)
from backend.app.gagf.assessment_factory_lite_payment_confirmation_event_service import (
    AssessmentFactoryLitePaymentConfirmationEventService,
)
from backend.app.gagf.governance_paid_work_prerequisite_persistence_bridge import (
    GovernancePaidWorkPrerequisitePersistenceBridge,
)
from backend.app.gagf.governance_paid_work_prerequisite_record import (
    AUTHORIZATION_PACKAGE_KIND,
    CONTRACT_EXECUTION_EVENT_KIND,
    PAYMENT_CONFIRMATION_EVENT_KIND,
    GovernancePaidWorkPrerequisiteRecord,
)


GOVERNANCE_PAID_WORK_PREREQUISITE_PRODUCER_VERSION = "0.2.0"


class GovernancePaidWorkPrerequisiteProducerError(RuntimeError):
    """Raised when a governed prerequisite cannot be produced safely."""


@dataclass(frozen=True, slots=True)
class GovernancePaidWorkPrerequisiteProductionResult:
    prerequisite_kind: str
    record: GovernancePaidWorkPrerequisiteRecord
    created: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": (
                "produced_and_recorded"
                if self.created
                else "existing_record_reused"
            ),
            "producer_version": (
                GOVERNANCE_PAID_WORK_PREREQUISITE_PRODUCER_VERSION
            ),
            "prerequisite_kind": self.prerequisite_kind,
            "artifact_id": self.record.artifact_id,
            "hierarchy_key": self.record.hierarchy_key,
            "created": self.created,
            "record": self.record.to_dict(),
            "boundaries": {
                "server_owns_prerequisite_identity": True,
                "server_owns_prerequisite_timestamp": True,
                "operator_evidence_is_not_prerequisite_identity": True,
                "producer_actor_context_is_bound": True,
                "evidence_instances_are_append_only": True,
                "production_is_not_paid_work_authority": True,
                "prerequisite_record_is_not_pa001": True,
                "production_requires_pre_authenticated_actor_context": True,
                "production_does_not_authorize_execution": True,
                "production_does_not_approve_delivery": True,
                "production_does_not_grant_intervention_authority": True,
            },
        }


class GovernancePaidWorkPrerequisiteProducerService:
    """
    Produce terminal commercial prerequisite artifacts with server-owned
    identity/time and persist them through the governed prerequisite bridge.

    Caller-supplied business evidence may contribute to Factory Lite artifact
    evaluation, but caller-supplied prerequisite IDs and timestamps are ignored.
    This service does not create PA-001.
    """

    def __init__(
        self,
        *,
        persistence_bridge: GovernancePaidWorkPrerequisitePersistenceBridge,
        authorization_package_service: (
            AssessmentFactoryLitePaidAssessmentAuthorizationPackageService
            | None
        ) = None,
        contract_execution_event_service: (
            AssessmentFactoryLiteContractExecutionEventService
            | None
        ) = None,
        payment_confirmation_event_service: (
            AssessmentFactoryLitePaymentConfirmationEventService
            | None
        ) = None,
        clock: Callable[[], datetime] | None = None,
        instance_id_factory: Callable[[], str] | None = None,
    ) -> None:
        if not isinstance(
            persistence_bridge,
            GovernancePaidWorkPrerequisitePersistenceBridge,
        ):
            raise TypeError(
                "persistence_bridge must be a "
                "GovernancePaidWorkPrerequisitePersistenceBridge"
            )

        self.persistence_bridge = persistence_bridge
        self.authorization_package_service = (
            authorization_package_service
            or AssessmentFactoryLitePaidAssessmentAuthorizationPackageService()
        )
        self.contract_execution_event_service = (
            contract_execution_event_service
            or AssessmentFactoryLiteContractExecutionEventService()
        )
        self.payment_confirmation_event_service = (
            payment_confirmation_event_service
            or AssessmentFactoryLitePaymentConfirmationEventService()
        )
        self.clock = clock or (
            lambda: datetime.now(timezone.utc)
        )
        self.instance_id_factory = (
            instance_id_factory
            or self._default_instance_id
        )

    def produce_authorization_package(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        source: Mapping[str, Any],
        actor: AssessmentActorContext,
    ) -> GovernancePaidWorkPrerequisiteProductionResult:
        hierarchy = self._hierarchy(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )
        actor = self._require_actor(
            actor=actor,
            tenant_id=hierarchy["tenant_id"],
        )
        evidence_instance_id = self._evidence_instance_id()
        artifact_id = self._artifact_id(
            prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
            hierarchy=hierarchy,
            evidence_instance_id=evidence_instance_id,
            producer_actor_id=actor.actor_id,
        )

        source_dict = self._source_dict(source)
        prepared_at = self._server_timestamp()

        authorization_context = self._sanitized_context(
            source_dict.get("authorization_context"),
            forbidden_fields=(
                "authorization_id",
                "prepared_at",
            ),
        )
        authorization_context["authorization_id"] = artifact_id
        authorization_context["prepared_at"] = prepared_at

        artifact = self.authorization_package_service.build_package(
            **self._select(
                source_dict,
                (
                    "scope_call_event_record",
                    "scope_call_event_package",
                    "scope_call_agenda_message_event_record",
                    "scope_call_agenda_message",
                    "scope_call_package",
                    "follow_up_event_record",
                    "follow_up_message",
                    "tracker",
                    "event_record",
                    "message",
                    "delivery_package",
                    "export_package",
                    "export",
                    "document",
                    "proposal",
                    "offer",
                    "buyer_context",
                    "operator_approval",
                    "message_context",
                    "event_context",
                    "follow_up_context",
                    "follow_up_message_context",
                    "follow_up_event_context",
                    "scope_call_context",
                    "scope_call_message_context",
                    "scope_call_message_event_context",
                    "scope_call_event_context",
                    "scope_call_record_context",
                ),
            ),
            authorization_context=authorization_context,
        )

        artifact = self._with_provenance(
            artifact=artifact,
            actor=actor,
            evidence_instance_id=evidence_instance_id,
        )

        persisted = self.persistence_bridge.record_authorization_package(
            artifact=artifact,
            **hierarchy,
        )

        return GovernancePaidWorkPrerequisiteProductionResult(
            prerequisite_kind=AUTHORIZATION_PACKAGE_KIND,
            record=persisted.record,
            created=True,
        )

    def produce_contract_execution_event(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        source: Mapping[str, Any],
        actor: AssessmentActorContext,
    ) -> GovernancePaidWorkPrerequisiteProductionResult:
        hierarchy = self._hierarchy(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )
        actor = self._require_actor(
            actor=actor,
            tenant_id=hierarchy["tenant_id"],
        )
        evidence_instance_id = self._evidence_instance_id()
        artifact_id = self._artifact_id(
            prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
            hierarchy=hierarchy,
            evidence_instance_id=evidence_instance_id,
            producer_actor_id=actor.actor_id,
        )

        source_dict = self._source_dict(source)
        recorded_at = self._server_timestamp()

        contract_execution_context = self._sanitized_context(
            source_dict.get("contract_execution_context"),
            forbidden_fields=(
                "contract_execution_event_id",
                "recorded_at",
            ),
        )
        contract_execution_context[
            "contract_execution_event_id"
        ] = artifact_id
        contract_execution_context["recorded_at"] = recorded_at

        artifact = self.contract_execution_event_service.record_event(
            **self._select(
                source_dict,
                (
                    "contract_execution_review",
                    "paid_assessment_agreement_review",
                    "paid_assessment_authorization_package",
                    "scope_call_event_record",
                    "scope_call_event_package",
                    "scope_call_agenda_message_event_record",
                    "scope_call_agenda_message",
                    "scope_call_package",
                    "follow_up_event_record",
                    "follow_up_message",
                    "tracker",
                    "event_record",
                    "message",
                    "delivery_package",
                    "export_package",
                    "export",
                    "document",
                    "proposal",
                    "offer",
                    "buyer_context",
                    "operator_approval",
                    "message_context",
                    "event_context",
                    "follow_up_context",
                    "follow_up_message_context",
                    "follow_up_event_context",
                    "scope_call_context",
                    "scope_call_message_context",
                    "scope_call_message_event_context",
                    "scope_call_event_context",
                    "scope_call_record_context",
                    "authorization_context",
                    "agreement_context",
                    "contract_context",
                ),
            ),
            contract_execution_context=contract_execution_context,
        )

        artifact = self._with_provenance(
            artifact=artifact,
            actor=actor,
            evidence_instance_id=evidence_instance_id,
        )

        persisted = self.persistence_bridge.record_contract_execution_event(
            artifact=artifact,
            **hierarchy,
        )

        return GovernancePaidWorkPrerequisiteProductionResult(
            prerequisite_kind=CONTRACT_EXECUTION_EVENT_KIND,
            record=persisted.record,
            created=True,
        )

    def produce_payment_confirmation_event(
        self,
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
        source: Mapping[str, Any],
        actor: AssessmentActorContext,
    ) -> GovernancePaidWorkPrerequisiteProductionResult:
        hierarchy = self._hierarchy(
            tenant_id=tenant_id,
            client_id=client_id,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )
        actor = self._require_actor(
            actor=actor,
            tenant_id=hierarchy["tenant_id"],
        )
        evidence_instance_id = self._evidence_instance_id()
        artifact_id = self._artifact_id(
            prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
            hierarchy=hierarchy,
            evidence_instance_id=evidence_instance_id,
            producer_actor_id=actor.actor_id,
        )

        source_dict = self._source_dict(source)
        recorded_at = self._server_timestamp()

        payment_confirmation_event_context = self._sanitized_context(
            source_dict.get("payment_confirmation_event_context"),
            forbidden_fields=(
                "payment_confirmation_event_id",
                "recorded_at",
            ),
        )
        payment_confirmation_event_context[
            "payment_confirmation_event_id"
        ] = artifact_id
        payment_confirmation_event_context["recorded_at"] = recorded_at

        artifact = self.payment_confirmation_event_service.record_event(
            **self._select(
                source_dict,
                (
                    "payment_confirmation_review",
                    "payment_request_event",
                    "payment_request_review",
                    "invoice_creation_event",
                    "invoice_creation_review",
                    "contract_execution_event",
                    "contract_execution_review",
                    "paid_assessment_agreement_review",
                    "paid_assessment_authorization_package",
                    "scope_call_event_record",
                    "scope_call_event_package",
                    "scope_call_agenda_message_event_record",
                    "scope_call_agenda_message",
                    "scope_call_package",
                    "follow_up_event_record",
                    "follow_up_message",
                    "tracker",
                    "event_record",
                    "message",
                    "delivery_package",
                    "export_package",
                    "export",
                    "document",
                    "proposal",
                    "offer",
                    "buyer_context",
                    "operator_approval",
                    "message_context",
                    "event_context",
                    "follow_up_context",
                    "follow_up_message_context",
                    "follow_up_event_context",
                    "scope_call_context",
                    "scope_call_message_context",
                    "scope_call_message_event_context",
                    "scope_call_event_context",
                    "scope_call_record_context",
                    "authorization_context",
                    "agreement_context",
                    "contract_context",
                    "contract_execution_context",
                    "invoice_context",
                    "invoice_creation_context",
                    "payment_request_context",
                    "payment_request_event_context",
                    "payment_confirmation_context",
                ),
            ),
            payment_confirmation_event_context=(
                payment_confirmation_event_context
            ),
        )

        artifact = self._with_provenance(
            artifact=artifact,
            actor=actor,
            evidence_instance_id=evidence_instance_id,
        )

        persisted = self.persistence_bridge.record_payment_confirmation_event(
            artifact=artifact,
            **hierarchy,
        )

        return GovernancePaidWorkPrerequisiteProductionResult(
            prerequisite_kind=PAYMENT_CONFIRMATION_EVENT_KIND,
            record=persisted.record,
            created=True,
        )

    @staticmethod
    def _hierarchy(
        *,
        tenant_id: str,
        client_id: str,
        engagement_id: str,
        assessment_id: str,
    ) -> dict[str, str]:
        hierarchy = {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "engagement_id": engagement_id,
            "assessment_id": assessment_id,
        }

        normalized: dict[str, str] = {}
        for field_name, value in hierarchy.items():
            text = str(value).strip()
            if not text:
                raise GovernancePaidWorkPrerequisiteProducerError(
                    f"{field_name} must not be empty"
                )
            normalized[field_name] = text

        return normalized

    @staticmethod
    def _source_dict(
        source: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(source, Mapping):
            raise GovernancePaidWorkPrerequisiteProducerError(
                "source must be a mapping"
            )

        return dict(source)

    @staticmethod
    def _sanitized_context(
        value: Any,
        *,
        forbidden_fields: tuple[str, ...],
    ) -> dict[str, Any]:
        if value is None:
            context: dict[str, Any] = {}
        elif isinstance(value, Mapping):
            context = dict(value)
        else:
            raise GovernancePaidWorkPrerequisiteProducerError(
                "producer context must be a mapping"
            )

        for field_name in forbidden_fields:
            context.pop(field_name, None)

        return context

    @staticmethod
    def _select(
        source: Mapping[str, Any],
        field_names: tuple[str, ...],
    ) -> dict[str, Any]:
        return {
            field_name: source[field_name]
            for field_name in field_names
            if field_name in source
        }

    def _server_timestamp(self) -> str:
        value = self.clock()

        if not isinstance(value, datetime):
            raise GovernancePaidWorkPrerequisiteProducerError(
                "clock must return datetime"
            )

        if value.tzinfo is None:
            value = value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _require_actor(
        *,
        actor: AssessmentActorContext,
        tenant_id: str,
    ) -> AssessmentActorContext:
        if not isinstance(actor, AssessmentActorContext):
            raise GovernancePaidWorkPrerequisiteProducerError(
                "actor must be an AssessmentActorContext"
            )
        if actor.tenant_id != tenant_id:
            raise GovernancePaidWorkPrerequisiteProducerError(
                "actor tenant does not match prerequisite tenant"
            )
        if not str(actor.actor_id).strip():
            raise GovernancePaidWorkPrerequisiteProducerError(
                "actor.actor_id must not be empty"
            )
        return actor

    @staticmethod
    def _default_instance_id() -> str:
        from uuid import uuid4
        return str(uuid4())

    def _evidence_instance_id(self) -> str:
        value = str(self.instance_id_factory()).strip()
        if not value:
            raise GovernancePaidWorkPrerequisiteProducerError(
                "instance_id_factory must return a non-empty value"
            )
        return value

    @staticmethod
    def _with_provenance(
        *,
        artifact: Mapping[str, Any],
        actor: AssessmentActorContext,
        evidence_instance_id: str,
    ) -> dict[str, Any]:
        if not isinstance(artifact, Mapping):
            raise GovernancePaidWorkPrerequisiteProducerError(
                "produced prerequisite artifact must be a mapping"
            )
        enriched = dict(artifact)
        enriched["governance_provenance"] = {
            "evidence_instance_id": evidence_instance_id,
            "producer_actor_id": actor.actor_id,
            "producer_tenant_id": actor.tenant_id,
            "producer_roles": sorted(actor.roles),
            "actor_context_bound": True,
        }
        return enriched

    @staticmethod
    def _artifact_id(
        *,
        prerequisite_kind: str,
        hierarchy: Mapping[str, str],
        evidence_instance_id: str,
        producer_actor_id: str,
    ) -> str:
        canonical = json.dumps(
            {
                "prerequisite_kind": prerequisite_kind,
                "tenant_id": hierarchy["tenant_id"],
                "client_id": hierarchy["client_id"],
                "engagement_id": hierarchy["engagement_id"],
                "assessment_id": hierarchy["assessment_id"],
                "evidence_instance_id": evidence_instance_id,
                "producer_actor_id": producer_actor_id,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        digest = hashlib.sha256(
            canonical
        ).hexdigest()

        prefix = {
            AUTHORIZATION_PACKAGE_KIND: "authorization-package",
            CONTRACT_EXECUTION_EVENT_KIND: "contract-execution-event",
            PAYMENT_CONFIRMATION_EVENT_KIND: "payment-confirmation-event",
        }[prerequisite_kind]

        return f"{prefix}-{digest[:24]}"
