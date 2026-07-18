from __future__ import annotations

from typing import Any

from backend.app.gagf.assessment_factory_lite_scope_call_event_package_service import (
    AssessmentFactoryLiteScopeCallEventPackageService,
)


class AssessmentFactoryLiteScopeCallEventRecordService:
    """Record a human-operated scope-call event.

    This service records the scope call outcome after the scope-call event
    package is ready. It does not schedule a call, create a calendar invite,
    authorize paid assessment work, execute a contract, create an invoice, or
    start production onboarding.
    """

    EVENT_TYPE = "assessment_factory_lite_scope_call_event_record"
    EVENT_STAGE = "scope_call_event_record"
    RELEASE = "assessment-factory-lite-scope-call-conversion"
    VERSION = "2.3.0"
    PACKAGE_NAME = "Assessment Factory Lite Demo Package"

    def record_event(
        self,
        *,
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
    ) -> dict[str, Any]:
        scope_call_record_context = scope_call_record_context or {}

        event_package = (
            scope_call_event_package
            or AssessmentFactoryLiteScopeCallEventPackageService().build_package(
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
            )
        )

        call_outcome = self._call_outcome(scope_call_record_context)
        operator_confirmation = self._operator_confirmation(scope_call_record_context)
        buyer_decision = self._buyer_decision(scope_call_record_context)
        event_checklist = self._event_checklist(
            event_package=event_package,
            call_outcome=call_outcome,
            operator_confirmation=operator_confirmation,
            buyer_decision=buyer_decision,
        )
        event_blockers = [
            key for key, value in event_checklist.items() if value is not True
        ]
        event_status = self._event_status(
            event_package=event_package,
            call_outcome=call_outcome,
            operator_confirmation=operator_confirmation,
            event_blockers=event_blockers,
        )

        return {
            "status": "ok",
            "event_type": self.EVENT_TYPE,
            "package_name": self.PACKAGE_NAME,
            "release": self.RELEASE,
            "version": self.VERSION,
            "event_stage": self.EVENT_STAGE,
            "event_status": event_status,
            "event_id": scope_call_record_context.get(
                "event_id",
                "scope-call-event-record-draft-001",
            ),
            "recorded_at": scope_call_record_context.get("recorded_at", "not_recorded"),
            "source_scope_call_event_package": self._event_package_summary(
                event_package
            ),
            "call_outcome": call_outcome,
            "operator_confirmation": operator_confirmation,
            "buyer_decision": buyer_decision,
            "event_checklist": event_checklist,
            "event_blockers": event_blockers,
            "scope_call_package_summary": event_package.get(
                "scope_call_package_summary", {}
            ),
            "agenda_summary": event_package.get("agenda_summary", {}),
            "buyer_readiness": event_package.get("buyer_readiness", {}),
            "readiness_score": event_package.get("readiness_score", {}),
            "commercial_next_action": self._commercial_next_action(
                event_status, buyer_decision
            ),
            "scheduling_boundary": self._scheduling_boundary(),
            "commercial_boundary": self._commercial_boundary(),
            "evidence_boundary": self._evidence_boundary(),
            "governance_boundary": self._governance_boundary(),
            "boundary_notices": self._boundary_notices(),
            "audit_notes": self._audit_notes(event_status, buyer_decision),
            "next_action": self._next_action(event_status, buyer_decision),
            "operator_message": self._operator_message(event_status, buyer_decision),
            "recommended_action": self._recommended_action(
                event_status, buyer_decision
            ),
        }

    def _event_package_summary(self, event_package: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_type": event_package.get("event_type"),
            "package_stage": event_package.get("package_stage"),
            "package_status": event_package.get("package_status"),
            "release": event_package.get("release"),
            "version": event_package.get("version"),
            "scope_call_id": event_package.get("scope_call_id"),
            "prepared_at": event_package.get("prepared_at"),
            "recommended_action": event_package.get("recommended_action"),
        }

    def _call_outcome(
        self, scope_call_record_context: dict[str, Any]
    ) -> dict[str, Any]:
        call_completed = scope_call_record_context.get("call_completed") is True
        call_confirmed = scope_call_record_context.get("call_confirmed") is True

        outcome_status = scope_call_record_context.get(
            "outcome_status",
            "completed" if call_completed else "pending",
        )

        return {
            "call_completed": call_completed,
            "call_confirmed": call_confirmed,
            "outcome_status": outcome_status,
            "outcome_summary": scope_call_record_context.get(
                "outcome_summary",
                "not_recorded",
            ),
            "buyer_needs_summary": scope_call_record_context.get(
                "buyer_needs_summary",
                "not_recorded",
            ),
            "assessment_fit": scope_call_record_context.get(
                "assessment_fit",
                "not_determined",
            ),
            "next_step_requested": scope_call_record_context.get(
                "next_step_requested",
                "not_recorded",
            ),
        }

    def _operator_confirmation(
        self, scope_call_record_context: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "human_operator_confirmed": (
                scope_call_record_context.get("human_operator_confirmed") is True
            ),
            "operator_name": scope_call_record_context.get("operator_name", "not_recorded"),
            "operator_notes": scope_call_record_context.get("operator_notes", []),
            "manual_recording_required": True,
            "automatic_call_recording_used": False,
            "ai_summary_authoritative": False,
        }

    def _buyer_decision(
        self, scope_call_record_context: dict[str, Any]
    ) -> dict[str, Any]:
        buyer_decision_status = scope_call_record_context.get(
            "buyer_decision_status",
            "undecided",
        )

        return {
            "buyer_decision_status": buyer_decision_status,
            "buyer_requested_paid_assessment": buyer_decision_status
            == "requested_paid_assessment",
            "buyer_declined": buyer_decision_status == "declined",
            "buyer_needs_follow_up": buyer_decision_status
            in {"needs_follow_up", "undecided"},
            "paid_assessment_authorization_required": True,
            "paid_assessment_authorized": False,
        }

    def _event_checklist(
        self,
        *,
        event_package: dict[str, Any],
        call_outcome: dict[str, Any],
        operator_confirmation: dict[str, Any],
        buyer_decision: dict[str, Any],
    ) -> dict[str, bool]:
        return {
            "scope_call_event_package_ready": event_package.get("package_status")
            == "ready_for_scope_call",
            "call_completed": call_outcome["call_completed"],
            "call_confirmed": call_outcome["call_confirmed"],
            "human_operator_confirmed": operator_confirmation[
                "human_operator_confirmed"
            ],
            "outcome_summary_recorded": call_outcome["outcome_summary"]
            != "not_recorded",
            "buyer_decision_recorded": buyer_decision["buyer_decision_status"]
            != "undecided",
            "paid_assessment_not_authorized": buyer_decision[
                "paid_assessment_authorized"
            ]
            is False,
            "automatic_call_recording_not_used": operator_confirmation[
                "automatic_call_recording_used"
            ]
            is False,
            "ai_summary_not_authoritative": operator_confirmation[
                "ai_summary_authoritative"
            ]
            is False,
        }

    def _event_status(
        self,
        *,
        event_package: dict[str, Any],
        call_outcome: dict[str, Any],
        operator_confirmation: dict[str, Any],
        event_blockers: list[str],
    ) -> str:
        if event_package.get("package_status") == "blocked":
            return "blocked"

        if event_package.get("package_status") != "ready_for_scope_call":
            return "pending_scope_call_event_package"

        if operator_confirmation["human_operator_confirmed"] is not True:
            return "pending_human_confirmation"

        if call_outcome["call_completed"] is not True:
            return "pending_scope_call_completion"

        if event_blockers:
            return "blocked"

        return "recorded"

    def _commercial_next_action(
        self,
        event_status: str,
        buyer_decision: dict[str, Any],
    ) -> dict[str, Any]:
        if event_status == "recorded" and buyer_decision[
            "buyer_requested_paid_assessment"
        ]:
            return {
                "action": "prepare_paid_assessment_authorization_package",
                "allowed_next_stage": "paid_assessment_authorization_package",
                "automatic_execution_allowed": False,
                "human_operator_required": True,
            }

        if event_status == "recorded" and buyer_decision["buyer_needs_follow_up"]:
            return {
                "action": "prepare_post_scope_call_follow_up",
                "allowed_next_stage": "post_scope_call_follow_up",
                "automatic_execution_allowed": False,
                "human_operator_required": True,
            }

        if event_status == "recorded" and buyer_decision["buyer_declined"]:
            return {
                "action": "close_buyer_opportunity",
                "allowed_next_stage": "closed_lost_record",
                "automatic_execution_allowed": False,
                "human_operator_required": True,
            }

        return {
            "action": "resolve_scope_call_event_record_gaps",
            "allowed_next_stage": "scope_call_event_record_review",
            "automatic_execution_allowed": False,
            "human_operator_required": True,
        }

    def _scheduling_boundary(self) -> dict[str, Any]:
        return {
            "scope_call_scheduled_by_system": False,
            "calendar_invite_created": False,
            "automatic_scheduling_allowed": False,
            "manual_scheduling_required": True,
            "scheduling_authority": "human_operator",
        }

    def _commercial_boundary(self) -> dict[str, Any]:
        return {
            "contract_created": False,
            "contract_executed": False,
            "invoice_created": False,
            "payment_requested": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "paid_assessment_requires_authorization_package": True,
        }

    def _evidence_boundary(self) -> dict[str, Any]:
        return {
            "allowed_evidence": [
                "operator_scope_call_notes",
                "buyer_approved_scope_call_summary",
                "redacted_operational_examples",
                "non_sensitive_workflow_context",
            ],
            "excluded_evidence": [
                "regulated_production_data",
                "secrets",
                "credentials",
                "unapproved_personal_data",
                "unapproved_customer_records",
            ],
            "evidence_review_required_before_paid_assessment": True,
        }

    def _governance_boundary(self) -> dict[str, Any]:
        return {
            "deterministic_status_required": True,
            "gagf_kernel_authoritative": True,
            "ai_override_allowed": False,
            "human_boundary_required": True,
            "release_marker_preserved": True,
        }

    def _boundary_notices(self) -> list[str]:
        return [
            "scope_call_event_record_does_not_authorize_paid_assessment",
            "scope_call_event_record_does_not_execute_contract",
            "scope_call_event_record_does_not_create_invoice",
            "scope_call_event_record_does_not_start_production_onboarding",
            "scope_call_event_record_requires_human_operator",
        ]

    def _audit_notes(
        self,
        event_status: str,
        buyer_decision: dict[str, Any],
    ) -> list[str]:
        notes = [
            "scope_call_event_record_built",
            "paid_assessment_not_authorized",
            "contract_not_executed",
            "invoice_not_created",
            "production_onboarding_not_started",
        ]

        if event_status == "recorded":
            notes.append("scope_call_event_record_recorded")
        elif event_status == "pending_scope_call_event_package":
            notes.append("scope_call_event_record_pending_package")
        elif event_status == "pending_human_confirmation":
            notes.append("scope_call_event_record_pending_human_confirmation")
        elif event_status == "pending_scope_call_completion":
            notes.append("scope_call_event_record_pending_completion")
        else:
            notes.append("scope_call_event_record_blocked")

        if buyer_decision["buyer_requested_paid_assessment"]:
            notes.append("buyer_requested_paid_assessment_authorization_review")
        elif buyer_decision["buyer_declined"]:
            notes.append("buyer_declined_after_scope_call")
        elif buyer_decision["buyer_needs_follow_up"]:
            notes.append("buyer_requires_post_scope_call_follow_up")

        return notes

    def _next_action(
        self,
        event_status: str,
        buyer_decision: dict[str, Any],
    ) -> dict[str, str]:
        if event_status == "recorded" and buyer_decision[
            "buyer_requested_paid_assessment"
        ]:
            return {
                "action": "prepare_paid_assessment_authorization_package",
                "operator_instruction": (
                    "Prepare the paid assessment authorization package. Do not "
                    "authorize paid work until the authorization package is "
                    "explicitly approved."
                ),
                "future_action": "build_paid_assessment_authorization_package",
            }

        if event_status == "recorded" and buyer_decision["buyer_needs_follow_up"]:
            return {
                "action": "prepare_post_scope_call_follow_up",
                "operator_instruction": (
                    "Prepare a human-reviewed post-scope-call follow-up before "
                    "moving to paid assessment authorization."
                ),
                "future_action": "build_post_scope_call_follow_up",
            }

        if event_status == "recorded" and buyer_decision["buyer_declined"]:
            return {
                "action": "close_buyer_opportunity",
                "operator_instruction": (
                    "Record the buyer decline outcome and close the opportunity "
                    "without starting paid assessment work."
                ),
                "future_action": "build_closed_lost_record",
            }

        if event_status == "pending_scope_call_event_package":
            return {
                "action": "complete_scope_call_event_package",
                "operator_instruction": (
                    "Complete the scope-call event package before recording the "
                    "scope-call event."
                ),
                "future_action": "rerun_scope_call_event_record",
            }

        if event_status == "pending_human_confirmation":
            return {
                "action": "confirm_scope_call_event_record",
                "operator_instruction": (
                    "A human operator must confirm the scope-call event record."
                ),
                "future_action": "rerun_scope_call_event_record",
            }

        if event_status == "pending_scope_call_completion":
            return {
                "action": "complete_scope_call",
                "operator_instruction": (
                    "Complete or confirm the scope call before recording the event."
                ),
                "future_action": "rerun_scope_call_event_record",
            }

        return {
            "action": "resolve_scope_call_event_record_gaps",
            "operator_instruction": (
                "Resolve scope-call event record blockers before moving forward."
            ),
            "future_action": "rerun_scope_call_event_record",
        }

    def _operator_message(
        self,
        event_status: str,
        buyer_decision: dict[str, Any],
    ) -> str:
        if event_status == "recorded" and buyer_decision[
            "buyer_requested_paid_assessment"
        ]:
            return (
                "Scope-call event recorded. Buyer requested paid assessment review, "
                "but paid assessment work is not authorized until a later "
                "authorization package is explicitly approved."
            )

        if event_status == "recorded" and buyer_decision["buyer_needs_follow_up"]:
            return (
                "Scope-call event recorded. Buyer requires human-reviewed "
                "post-scope-call follow-up."
            )

        if event_status == "recorded" and buyer_decision["buyer_declined"]:
            return (
                "Scope-call event recorded. Buyer declined; close the opportunity "
                "without paid assessment authorization."
            )

        if event_status == "pending_scope_call_event_package":
            return (
                "Scope-call event record is pending because the scope-call event "
                "package is not ready."
            )

        if event_status == "pending_human_confirmation":
            return (
                "Scope-call event record is pending human operator confirmation."
            )

        if event_status == "pending_scope_call_completion":
            return "Scope-call event record is pending scope-call completion."

        return (
            "Scope-call event record is blocked. Resolve the listed blockers before "
            "moving forward."
        )

    def _recommended_action(
        self,
        event_status: str,
        buyer_decision: dict[str, Any],
    ) -> str:
        if event_status == "recorded" and buyer_decision[
            "buyer_requested_paid_assessment"
        ]:
            return "prepare_paid_assessment_authorization_package"

        if event_status == "recorded" and buyer_decision["buyer_needs_follow_up"]:
            return "prepare_post_scope_call_follow_up"

        if event_status == "recorded" and buyer_decision["buyer_declined"]:
            return "close_buyer_opportunity"

        return "resolve_scope_call_event_record_gaps"