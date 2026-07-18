from __future__ import annotations

from typing import Any

from backend.app.gagf.assessment_factory_lite_scope_call_event_record_service import (
    AssessmentFactoryLiteScopeCallEventRecordService,
)


class AssessmentFactoryLitePaidAssessmentAuthorizationPackageService:
    """Build a governed paid assessment authorization package.

    This package is created after a human-operated scope call event record.
    It reviews whether paid assessment authorization may be prepared.

    It does not execute a contract, create an invoice, request payment, start
    production onboarding, or automatically authorize paid work.
    """

    EVENT_TYPE = "assessment_factory_lite_paid_assessment_authorization_package"
    PACKAGE_STAGE = "paid_assessment_authorization_package"
    RELEASE = "assessment-factory-lite-scope-call-conversion"
    VERSION = "2.3.0"
    PACKAGE_NAME = "Assessment Factory Lite Demo Package"

    def build_package(
        self,
        *,
        scope_call_event_record: dict[str, Any] | None = None,
        scope_call_event_package: dict[str, Any] | None = None,
        scope_call_agenda_message_event_record: dict[str, Any] | None = None,
        scope_call_agenda_message: dict[str, Any] | None = None,
        scope_call_package: dict[str, Any] | None = None,
        follow_up_event_record: dict[str, Any] | None = None,
        follow_up_message: dict[str, Any] | None = None,
        tracker: dict[str, Any] | None = None,
        event_record: dict[str, Any] | None = None,
        message: dict[str, Any] | None = None,
        delivery_package: dict[str, Any] | None = None,
        export_package: dict[str, Any] | None = None,
        export: dict[str, Any] | None = None,
        document: dict[str, Any] | None = None,
        proposal: dict[str, Any] | None = None,
        offer: dict[str, Any] | None = None,
        buyer_context: dict[str, Any] | None = None,
        operator_approval: dict[str, Any] | None = None,
        message_context: dict[str, Any] | None = None,
        event_context: dict[str, Any] | None = None,
        follow_up_context: dict[str, Any] | None = None,
        follow_up_message_context: dict[str, Any] | None = None,
        follow_up_event_context: dict[str, Any] | None = None,
        scope_call_context: dict[str, Any] | None = None,
        scope_call_message_context: dict[str, Any] | None = None,
        scope_call_message_event_context: dict[str, Any] | None = None,
        scope_call_event_context: dict[str, Any] | None = None,
        scope_call_record_context: dict[str, Any] | None = None,
        authorization_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        authorization_context = authorization_context or {}
        operator_approval = operator_approval or {}

        event_record_source = (
            scope_call_event_record
            or AssessmentFactoryLiteScopeCallEventRecordService().record_event(
                scope_call_event_package=scope_call_event_package,
                scope_call_agenda_message_event_record=scope_call_agenda_message_event_record,
                scope_call_agenda_message=scope_call_agenda_message,
                scope_call_package=scope_call_package,
                follow_up_event_record=follow_up_event_record,
                follow_up_message=follow_up_message,
                tracker=tracker,
                event_record=event_record,
                message=message,
                delivery_package=delivery_package,
                export_package=export_package,
                export=export,
                document=document,
                proposal=proposal,
                offer=offer,
                buyer_context=buyer_context,
                operator_approval=operator_approval,
                message_context=message_context,
                event_context=event_context,
                follow_up_context=follow_up_context,
                follow_up_message_context=follow_up_message_context,
                follow_up_event_context=follow_up_event_context,
                scope_call_context=scope_call_context,
                scope_call_message_context=scope_call_message_context,
                scope_call_message_event_context=scope_call_message_event_context,
                scope_call_event_context=scope_call_event_context,
                scope_call_record_context=scope_call_record_context,
            )
        )

        authorization_identity = self._authorization_identity(authorization_context)
        source_summary = self._source_event_summary(event_record_source)
        buyer_request = self._buyer_request(event_record_source, authorization_context)
        commercial_review = self._commercial_review(authorization_context)
        evidence_review = self._evidence_review(authorization_context)
        human_authorization = self._human_authorization(
            operator_approval,
            authorization_context,
        )
        package_checklist = self._package_checklist(
            source_event=event_record_source,
            buyer_request=buyer_request,
            commercial_review=commercial_review,
            evidence_review=evidence_review,
            human_authorization=human_authorization,
        )
        package_blockers = [
            key for key, value in package_checklist.items() if value is not True
        ]
        package_status = self._package_status(
            source_event=event_record_source,
            buyer_request=buyer_request,
            human_authorization=human_authorization,
            package_blockers=package_blockers,
        )
        authorization_score = self._authorization_score(package_checklist)

        return {
            "status": "ok",
            "event_type": self.EVENT_TYPE,
            "package_name": self.PACKAGE_NAME,
            "release": self.RELEASE,
            "version": self.VERSION,
            "package_stage": self.PACKAGE_STAGE,
            "package_status": package_status,
            "authorization_id": authorization_identity["authorization_id"],
            "prepared_at": authorization_identity["prepared_at"],
            "source_scope_call_event_record": source_summary,
            "buyer_request": buyer_request,
            "commercial_review": commercial_review,
            "evidence_review": evidence_review,
            "human_authorization": human_authorization,
            "package_checklist": package_checklist,
            "package_blockers": package_blockers,
            "authorization_score": authorization_score,
            "scope_call_package_summary": event_record_source.get(
                "scope_call_package_summary",
                {},
            ),
            "agenda_summary": event_record_source.get("agenda_summary", {}),
            "buyer_readiness": event_record_source.get("buyer_readiness", {}),
            "call_outcome": event_record_source.get("call_outcome", {}),
            "buyer_decision": event_record_source.get("buyer_decision", {}),
            "scheduling_boundary": self._scheduling_boundary(),
            "commercial_boundary": self._commercial_boundary(package_status),
            "evidence_boundary": self._evidence_boundary(),
            "governance_boundary": self._governance_boundary(),
            "boundary_notices": self._boundary_notices(),
            "audit_notes": self._audit_notes(package_status, buyer_request),
            "next_action": self._next_action(package_status),
            "operator_message": self._operator_message(package_status),
            "recommended_action": self._recommended_action(package_status),
        }

    def _authorization_identity(
        self,
        authorization_context: dict[str, Any],
    ) -> dict[str, str]:
        return {
            "authorization_id": authorization_context.get(
                "authorization_id",
                "paid-assessment-authorization-package-draft-001",
            ),
            "prepared_at": authorization_context.get("prepared_at", "not_recorded"),
        }

    def _source_event_summary(self, source_event: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_type": source_event.get("event_type"),
            "event_stage": source_event.get("event_stage"),
            "event_status": source_event.get("event_status"),
            "release": source_event.get("release"),
            "version": source_event.get("version"),
            "event_id": source_event.get("event_id"),
            "recorded_at": source_event.get("recorded_at"),
            "recommended_action": source_event.get("recommended_action"),
        }

    def _buyer_request(
        self,
        source_event: dict[str, Any],
        authorization_context: dict[str, Any],
    ) -> dict[str, Any]:
        buyer_decision = source_event.get("buyer_decision", {})
        requested = (
            buyer_decision.get("buyer_requested_paid_assessment") is True
            or authorization_context.get("buyer_requested_paid_assessment") is True
        )

        return {
            "buyer_requested_paid_assessment": requested,
            "buyer_decision_status": buyer_decision.get(
                "buyer_decision_status",
                "undecided",
            ),
            "requested_package_type": authorization_context.get(
                "requested_package_type",
                "assessment_factory_lite_paid_assessment",
            ),
            "buyer_request_summary": authorization_context.get(
                "buyer_request_summary",
                "not_recorded",
            ),
            "buyer_request_is_evidence_not_authorization": True,
        }

    def _commercial_review(
        self,
        authorization_context: dict[str, Any],
    ) -> dict[str, Any]:
        pricing_reviewed = authorization_context.get("pricing_reviewed") is True
        scope_reviewed = authorization_context.get("scope_reviewed") is True
        terms_reviewed = authorization_context.get("terms_reviewed") is True

        return {
            "pricing_reviewed": pricing_reviewed,
            "scope_reviewed": scope_reviewed,
            "terms_reviewed": terms_reviewed,
            "commercial_terms_ready": pricing_reviewed
            and scope_reviewed
            and terms_reviewed,
            "contract_required_before_execution": True,
            "invoice_required_before_payment": True,
            "payment_required_before_paid_work": True,
        }

    def _evidence_review(
        self,
        authorization_context: dict[str, Any],
    ) -> dict[str, Any]:
        evidence_reviewed = authorization_context.get("evidence_reviewed") is True
        evidence_boundary_approved = (
            authorization_context.get("evidence_boundary_approved") is True
        )

        return {
            "evidence_reviewed": evidence_reviewed,
            "evidence_boundary_approved": evidence_boundary_approved,
            "production_data_approved": False,
            "secrets_approved": False,
            "credentials_approved": False,
            "evidence_ready_for_paid_assessment": evidence_reviewed
            and evidence_boundary_approved,
        }

    def _human_authorization(
        self,
        operator_approval: dict[str, Any],
        authorization_context: dict[str, Any],
    ) -> dict[str, Any]:
        package_authorized = (
            authorization_context.get("human_operator_authorized_package") is True
            or operator_approval.get("paid_assessment_authorization_approved") is True
        )

        return {
            "human_operator_required": True,
            "human_operator_authorized_package": package_authorized,
            "authorization_status": authorization_context.get(
                "authorization_status",
                "authorization_review_required",
            ),
            "paid_assessment_authorized": False,
            "contract_execution_approved": False,
            "invoice_creation_approved": False,
            "payment_request_approved": False,
            "production_onboarding_approved": False,
        }

    def _package_checklist(
        self,
        *,
        source_event: dict[str, Any],
        buyer_request: dict[str, Any],
        commercial_review: dict[str, Any],
        evidence_review: dict[str, Any],
        human_authorization: dict[str, Any],
    ) -> dict[str, bool]:
        return {
            "scope_call_event_recorded": source_event.get("event_status") == "recorded",
            "buyer_requested_paid_assessment": buyer_request[
                "buyer_requested_paid_assessment"
            ],
            "buyer_request_is_evidence_not_authorization": buyer_request[
                "buyer_request_is_evidence_not_authorization"
            ],
            "commercial_terms_ready": commercial_review["commercial_terms_ready"],
            "evidence_ready_for_paid_assessment": evidence_review[
                "evidence_ready_for_paid_assessment"
            ],
            "human_operator_authorized_package": human_authorization[
                "human_operator_authorized_package"
            ],
            "paid_assessment_not_authorized_by_package": human_authorization[
                "paid_assessment_authorized"
            ]
            is False,
            "contract_not_executed": human_authorization[
                "contract_execution_approved"
            ]
            is False,
            "invoice_not_created": human_authorization["invoice_creation_approved"]
            is False,
            "payment_not_requested": human_authorization["payment_request_approved"]
            is False,
            "production_onboarding_not_started": human_authorization[
                "production_onboarding_approved"
            ]
            is False,
        }

    def _package_status(
        self,
        *,
        source_event: dict[str, Any],
        buyer_request: dict[str, Any],
        human_authorization: dict[str, Any],
        package_blockers: list[str],
    ) -> str:
        if source_event.get("event_status") == "blocked":
            return "blocked"

        if source_event.get("event_status") != "recorded":
            return "pending_scope_call_event_record"

        if buyer_request["buyer_requested_paid_assessment"] is not True:
            return "pending_buyer_request"

        if human_authorization["human_operator_authorized_package"] is not True:
            return "pending_human_authorization"

        if package_blockers:
            return "pending_authorization_review"

        return "ready_for_paid_assessment_authorization"

    def _authorization_score(
        self,
        package_checklist: dict[str, bool],
    ) -> dict[str, Any]:
        total = len(package_checklist)
        passed = sum(1 for value in package_checklist.values() if value is True)

        return {
            "passed": passed,
            "total": total,
            "score": round(passed / total, 4) if total else 0.0,
            "ready": passed == total,
        }

    def _scheduling_boundary(self) -> dict[str, Any]:
        return {
            "scope_call_scheduled_by_system": False,
            "calendar_invite_created": False,
            "automatic_scheduling_allowed": False,
            "manual_scheduling_required": True,
            "scheduling_authority": "human_operator",
        }

    def _commercial_boundary(self, package_status: str) -> dict[str, Any]:
        return {
            "authorization_package_ready": package_status
            == "ready_for_paid_assessment_authorization",
            "paid_assessment_authorized": False,
            "contract_created": False,
            "contract_executed": False,
            "invoice_created": False,
            "payment_requested": False,
            "production_onboarding_authorized": False,
            "requires_separate_contract": True,
            "requires_separate_invoice": True,
            "requires_separate_payment_confirmation": True,
        }

    def _evidence_boundary(self) -> dict[str, Any]:
        return {
            "allowed_evidence": [
                "operator_scope_call_notes",
                "buyer_approved_scope_call_summary",
                "redacted_operational_examples",
                "non_sensitive_workflow_context",
                "operator_approved_assessment_scope",
            ],
            "excluded_evidence": [
                "regulated_production_data",
                "secrets",
                "credentials",
                "unapproved_personal_data",
                "unapproved_customer_records",
            ],
            "production_data_requires_separate_approval": True,
        }

    def _governance_boundary(self) -> dict[str, Any]:
        return {
            "deterministic_status_required": True,
            "gagf_kernel_authoritative": True,
            "ai_override_allowed": False,
            "human_boundary_required": True,
            "release_marker_preserved": True,
            "authorization_is_package_readiness_only": True,
        }

    def _boundary_notices(self) -> list[str]:
        return [
            "paid_assessment_authorization_package_does_not_authorize_paid_work",
            "paid_assessment_authorization_package_does_not_execute_contract",
            "paid_assessment_authorization_package_does_not_create_invoice",
            "paid_assessment_authorization_package_does_not_request_payment",
            "paid_assessment_authorization_package_does_not_start_production_onboarding",
            "paid_assessment_authorization_package_requires_human_operator",
        ]

    def _audit_notes(
        self,
        package_status: str,
        buyer_request: dict[str, Any],
    ) -> list[str]:
        notes = [
            "paid_assessment_authorization_package_built",
            "buyer_request_treated_as_evidence_not_authorization",
            "paid_assessment_not_authorized",
            "contract_not_executed",
            "invoice_not_created",
            "payment_not_requested",
            "production_onboarding_not_started",
        ]

        if package_status == "ready_for_paid_assessment_authorization":
            notes.append("paid_assessment_authorization_package_ready")
        elif package_status == "pending_scope_call_event_record":
            notes.append("paid_assessment_authorization_pending_scope_call_event_record")
        elif package_status == "pending_buyer_request":
            notes.append("paid_assessment_authorization_pending_buyer_request")
        elif package_status == "pending_human_authorization":
            notes.append("paid_assessment_authorization_pending_human_authorization")
        elif package_status == "pending_authorization_review":
            notes.append("paid_assessment_authorization_pending_review")
        else:
            notes.append("paid_assessment_authorization_package_blocked")

        if buyer_request["buyer_requested_paid_assessment"]:
            notes.append("buyer_requested_paid_assessment_review")

        return notes

    def _next_action(self, package_status: str) -> dict[str, str]:
        if package_status == "ready_for_paid_assessment_authorization":
            return {
                "action": "prepare_paid_assessment_agreement_review",
                "operator_instruction": (
                    "Prepare the paid assessment agreement review. Do not begin "
                    "paid assessment work until contract, invoice, payment, and "
                    "authorization gates are completed."
                ),
                "future_action": "build_paid_assessment_agreement_review",
            }

        if package_status == "pending_scope_call_event_record":
            return {
                "action": "complete_scope_call_event_record",
                "operator_instruction": (
                    "Complete the scope-call event record before preparing the "
                    "paid assessment authorization package."
                ),
                "future_action": "rerun_paid_assessment_authorization_package",
            }

        if package_status == "pending_buyer_request":
            return {
                "action": "confirm_buyer_paid_assessment_request",
                "operator_instruction": (
                    "Confirm the buyer requested paid assessment review before "
                    "continuing authorization package preparation."
                ),
                "future_action": "rerun_paid_assessment_authorization_package",
            }

        if package_status == "pending_human_authorization":
            return {
                "action": "confirm_human_authorization_package_review",
                "operator_instruction": (
                    "A human operator must authorize package readiness before "
                    "moving toward paid assessment agreement review."
                ),
                "future_action": "rerun_paid_assessment_authorization_package",
            }

        if package_status == "pending_authorization_review":
            return {
                "action": "complete_authorization_review",
                "operator_instruction": (
                    "Complete commercial and evidence review before moving toward "
                    "paid assessment agreement review."
                ),
                "future_action": "rerun_paid_assessment_authorization_package",
            }

        return {
            "action": "resolve_paid_assessment_authorization_package_gaps",
            "operator_instruction": (
                "Resolve paid assessment authorization package blockers before "
                "moving forward."
            ),
            "future_action": "rerun_paid_assessment_authorization_package",
        }

    def _operator_message(self, package_status: str) -> str:
        if package_status == "ready_for_paid_assessment_authorization":
            return (
                "Paid assessment authorization package is ready for agreement "
                "review. Paid assessment work is still not authorized until "
                "contract, invoice, payment, and authorization gates are completed."
            )

        if package_status == "pending_scope_call_event_record":
            return (
                "Paid assessment authorization package is pending because the "
                "scope-call event record is not complete."
            )

        if package_status == "pending_buyer_request":
            return (
                "Paid assessment authorization package is pending buyer request "
                "confirmation."
            )

        if package_status == "pending_human_authorization":
            return (
                "Paid assessment authorization package is pending human operator "
                "authorization review."
            )

        if package_status == "pending_authorization_review":
            return (
                "Paid assessment authorization package is pending commercial or "
                "evidence review."
            )

        return (
            "Paid assessment authorization package is blocked. Resolve the listed "
            "blockers before moving forward."
        )

    def _recommended_action(self, package_status: str) -> str:
        if package_status == "ready_for_paid_assessment_authorization":
            return "prepare_paid_assessment_agreement_review"

        return "resolve_paid_assessment_authorization_package_gaps"