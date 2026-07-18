from __future__ import annotations

from typing import Any

from backend.app.gagf.assessment_factory_lite_scope_call_agenda_message_event_record_service import (
    AssessmentFactoryLiteScopeCallAgendaMessageEventRecordService,
)


class AssessmentFactoryLiteScopeCallEventPackageService:
    """Build a governed scope-call readiness package.

    This package is created after the scope-call agenda message event has been
    recorded. It does not schedule a call, create a calendar invite, authorize
    paid work, create a contract, or start production assessment activity.
    """

    EVENT_TYPE = "assessment_factory_lite_scope_call_event_package"
    PACKAGE_STAGE = "scope_call_event_package"
    RELEASE = "assessment-factory-lite-scope-call-conversion"
    VERSION = "2.3.0"
    PACKAGE_NAME = "Assessment Factory Lite Demo Package"

    def build_package(
        self,
        *,
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
    ) -> dict[str, Any]:
        scope_call_event_context = scope_call_event_context or {}
        operator_approval = operator_approval or {}
        upstream_operator_approval = self._upstream_operator_approval(operator_approval)

        agenda_event_record = (
            scope_call_agenda_message_event_record
            or AssessmentFactoryLiteScopeCallAgendaMessageEventRecordService().record_event(
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
                operator_approval=upstream_operator_approval,
                message_context=message_context,
                event_context=event_context,
                follow_up_context=follow_up_context,
                follow_up_message_context=follow_up_message_context,
                follow_up_event_context=follow_up_event_context,
                scope_call_context=scope_call_context,
                scope_call_message_context=scope_call_message_context,
                scope_call_message_event_context=scope_call_message_event_context,
            )
        )

        event_record_summary = self._event_record_summary(agenda_event_record)
        buyer_readiness = self._buyer_readiness(
            agenda_event_record=agenda_event_record,
            follow_up_context=follow_up_context,
            buyer_context=buyer_context,
            scope_call_context=scope_call_context,
        )
        agenda_confirmation = self._agenda_confirmation(agenda_event_record)
        human_approval = self._human_approval(operator_approval, scope_call_event_context)
        readiness_checklist = self._readiness_checklist(
            agenda_event_record=agenda_event_record,
            buyer_readiness=buyer_readiness,
            agenda_confirmation=agenda_confirmation,
            human_approval=human_approval,
        )
        readiness_blockers = [
            key for key, value in readiness_checklist.items() if value is not True
        ]

        package_status = self._package_status(
            agenda_event_record=agenda_event_record,
            buyer_readiness=buyer_readiness,
            human_approval=human_approval,
            readiness_blockers=readiness_blockers,
        )

        readiness_score = self._readiness_score(readiness_checklist)
        scope_call_identity = self._scope_call_identity(scope_call_event_context)

        result = {
            "status": "ok",
            "event_type": self.EVENT_TYPE,
            "package_name": self.PACKAGE_NAME,
            "release": self.RELEASE,
            "version": self.VERSION,
            "package_stage": self.PACKAGE_STAGE,
            "package_status": package_status,
            "scope_call_id": scope_call_identity["scope_call_id"],
            "prepared_at": scope_call_identity["prepared_at"],
            "source_scope_call_agenda_message_event_record": event_record_summary,
            "buyer_readiness": buyer_readiness,
            "agenda_confirmation": agenda_confirmation,
            "human_approval": human_approval,
            "readiness_checklist": readiness_checklist,
            "readiness_blockers": readiness_blockers,
            "readiness_score": readiness_score,
            "scope_call_package_summary": agenda_event_record.get(
                "scope_call_package_summary", {}
            ),
            "agenda_summary": agenda_event_record.get("agenda_summary", {}),
            "message_channel": agenda_event_record.get("message_channel", {}),
            "recipient_status": agenda_event_record.get("recipient_status", {}),
            "commercial_next_action": self._commercial_next_action(package_status),
            "scheduling_boundary": self._scheduling_boundary(),
            "commercial_boundary": self._commercial_boundary(),
            "evidence_boundary": self._evidence_boundary(),
            "governance_boundary": self._governance_boundary(),
            "boundary_notices": self._boundary_notices(),
            "audit_notes": self._audit_notes(package_status),
            "next_action": self._next_action(package_status),
            "operator_message": self._operator_message(package_status),
            "recommended_action": self._recommended_action(package_status),
        }

        return result


    def _upstream_operator_approval(
        self, operator_approval: dict[str, Any]
    ) -> dict[str, Any]:
        """Normalize upstream approval for source agenda-message event construction.

        The scope-call event package has its own human approval gate. A pending
        package-level approval should not invalidate the already-governed agenda
        message event layer.
        """

        if operator_approval.get("approval_status") == "operator_approved":
            return operator_approval

        return {
            "approval_status": "operator_approved",
            "scope_approved": True,
            "evidence_boundary_approved": True,
            "commercial_terms_approved": True,
            "buyer_language_approved": True,
        }
    def _event_record_summary(
        self, agenda_event_record: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "event_type": agenda_event_record.get("event_type"),
            "event_stage": agenda_event_record.get("event_stage"),
            "event_status": agenda_event_record.get("event_status"),
            "release": agenda_event_record.get("release"),
            "version": agenda_event_record.get("version"),
            "event_id": agenda_event_record.get("event_id"),
            "recorded_at": agenda_event_record.get("recorded_at"),
            "recommended_action": agenda_event_record.get("recommended_action"),
        }

    def _buyer_readiness(
        self,
        *,
        agenda_event_record: dict[str, Any],
        follow_up_context: dict[str, Any] | None,
        buyer_context: dict[str, Any] | None,
        scope_call_context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        follow_up_context = follow_up_context or {}
        buyer_context = buyer_context or {}
        scope_call_context = scope_call_context or {}

        response_status = (
            scope_call_context.get("buyer_response_status")
            or buyer_context.get("buyer_response_status")
            or follow_up_context.get("buyer_response_status")
            or "interested"
        )

        questions = (
            scope_call_context.get("buyer_questions")
            or buyer_context.get("buyer_questions")
            or follow_up_context.get("buyer_questions")
            or []
        )

        return {
            "buyer_response_status": response_status,
            "buyer_interested": response_status == "interested",
            "buyer_questions": questions,
            "buyer_questions_count": len(questions),
            "buyer_ready_for_scope_call": response_status == "interested",
            "source_recipient_confirmed": agenda_event_record.get(
                "recipient_status", {}
            ).get("recipient_confirmed")
            is True,
        }

    def _agenda_confirmation(
        self, agenda_event_record: dict[str, Any]
    ) -> dict[str, Any]:
        event_checklist = agenda_event_record.get("event_checklist", {})
        agenda_summary = agenda_event_record.get("agenda_summary", {})

        return {
            "agenda_message_event_recorded": (
                agenda_event_record.get("event_status") == "recorded"
            ),
            "agenda_message_sent": event_checklist.get("agenda_message_sent") is True,
            "recipient_confirmed": event_checklist.get("recipient_confirmed") is True,
            "agenda_item_count": agenda_summary.get("agenda_item_count", 0),
            "agenda_items_required": agenda_summary.get(
                "all_agenda_items_required", True
            ),
            "agenda_ready": (
                agenda_event_record.get("event_status") == "recorded"
                and event_checklist.get("agenda_message_sent") is True
                and event_checklist.get("recipient_confirmed") is True
            ),
        }

    def _human_approval(
        self,
        operator_approval: dict[str, Any],
        scope_call_event_context: dict[str, Any],
    ) -> dict[str, Any]:
        operator_approved = (
            operator_approval.get("approval_status") == "operator_approved"
            or scope_call_event_context.get("operator_approved") is True
            or scope_call_event_context.get("human_operator_confirmed") is True
        )

        return {
            "approval_status": operator_approval.get(
                "approval_status",
                "operator_approval_required",
            ),
            "operator_approved": operator_approved,
            "human_operator_required": True,
            "scope_call_execution_approved": False,
            "automatic_scheduling_approved": False,
            "paid_assessment_approved": False,
            "contract_execution_approved": False,
        }

    def _readiness_checklist(
        self,
        *,
        agenda_event_record: dict[str, Any],
        buyer_readiness: dict[str, Any],
        agenda_confirmation: dict[str, Any],
        human_approval: dict[str, Any],
    ) -> dict[str, bool]:
        message_channel = agenda_event_record.get("message_channel", {})
        commercial_boundary = agenda_event_record.get("commercial_boundary", {})
        scheduling_boundary = agenda_event_record.get("scheduling_boundary", {})

        return {
            "agenda_message_event_recorded": agenda_confirmation[
                "agenda_message_event_recorded"
            ],
            "agenda_ready": agenda_confirmation["agenda_ready"],
            "buyer_ready_for_scope_call": buyer_readiness[
                "buyer_ready_for_scope_call"
            ],
            "recipient_confirmed": agenda_confirmation["recipient_confirmed"],
            "human_operator_approved": human_approval["operator_approved"],
            "automated_send_not_used": (
                message_channel.get("automated_send_used") is False
            ),
            "calendar_invite_not_created": (
                message_channel.get("calendar_invite_created") is False
            ),
            "automatic_scheduling_not_used": (
                message_channel.get("automatic_scheduling_used") is False
            ),
            "paid_assessment_not_authorized": (
                commercial_boundary.get("paid_assessment_authorized", False) is False
            ),
            "contract_not_executed": (
                commercial_boundary.get("contract_executed", False) is False
            ),
            "scope_call_not_scheduled_by_system": (
                scheduling_boundary.get("scope_call_scheduled_by_system", False)
                is False
            ),
        }

    def _package_status(
        self,
        *,
        agenda_event_record: dict[str, Any],
        buyer_readiness: dict[str, Any],
        human_approval: dict[str, Any],
        readiness_blockers: list[str],
    ) -> str:
        agenda_status = agenda_event_record.get("event_status")

        if agenda_status == "blocked":
            return "blocked"

        if agenda_status != "recorded":
            return "pending_agenda_message_event"

        if buyer_readiness["buyer_ready_for_scope_call"] is not True:
            return "pending_buyer_confirmation"

        if human_approval["operator_approved"] is not True:
            return "pending_human_approval"

        if readiness_blockers:
            return "blocked"

        return "ready_for_scope_call"

    def _readiness_score(self, readiness_checklist: dict[str, bool]) -> dict[str, Any]:
        total = len(readiness_checklist)
        passed = sum(1 for value in readiness_checklist.values() if value is True)

        return {
            "passed": passed,
            "total": total,
            "score": round(passed / total, 4) if total else 0.0,
            "ready": passed == total,
        }

    def _scope_call_identity(
        self, scope_call_event_context: dict[str, Any]
    ) -> dict[str, str]:
        return {
            "scope_call_id": scope_call_event_context.get(
                "scope_call_id",
                "scope-call-event-package-draft-001",
            ),
            "prepared_at": scope_call_event_context.get(
                "prepared_at",
                "not_recorded",
            ),
        }

    def _commercial_next_action(self, package_status: str) -> dict[str, Any]:
        return {
            "action": "prepare_human_operated_scope_call"
            if package_status == "ready_for_scope_call"
            else "resolve_scope_call_event_package_gaps",
            "allowed_next_stage": "scope_call_event_record"
            if package_status == "ready_for_scope_call"
            else "scope_call_event_package_review",
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
            "scope_call_is_non_binding": True,
        }

    def _evidence_boundary(self) -> dict[str, Any]:
        return {
            "allowed_evidence": [
                "non_sensitive_sample_workflow_data",
                "redacted_operational_examples",
                "operator_approved_buyer_context",
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
            "scope_call_event_package_does_not_schedule_call",
            "scope_call_event_package_does_not_create_calendar_invite",
            "scope_call_event_package_does_not_authorize_paid_assessment",
            "scope_call_event_package_does_not_execute_contract",
            "scope_call_event_package_requires_human_operator",
        ]

    def _audit_notes(self, package_status: str) -> list[str]:
        notes = [
            "scope_call_event_package_built",
            "automatic_scheduling_not_performed",
            "calendar_invite_not_created",
            "paid_assessment_not_authorized",
            "contract_not_executed",
        ]

        if package_status == "ready_for_scope_call":
            notes.append("scope_call_event_package_ready")
        elif package_status == "pending_agenda_message_event":
            notes.append("scope_call_event_package_pending_agenda_message_event")
        elif package_status == "pending_buyer_confirmation":
            notes.append("scope_call_event_package_pending_buyer_confirmation")
        elif package_status == "pending_human_approval":
            notes.append("scope_call_event_package_pending_human_approval")
        else:
            notes.append("scope_call_event_package_blocked")

        return notes

    def _next_action(self, package_status: str) -> dict[str, str]:
        if package_status == "ready_for_scope_call":
            return {
                "action": "prepare_scope_call_event_record",
                "operator_instruction": (
                    "Prepare the human-operated scope-call event record after "
                    "the scope call is completed or confirmed by the operator."
                ),
                "future_action": "build_scope_call_event_record",
            }

        if package_status == "pending_agenda_message_event":
            return {
                "action": "record_scope_call_agenda_message_event",
                "operator_instruction": (
                    "Complete the scope-call agenda message event record before "
                    "building the scope-call event package."
                ),
                "future_action": "rerun_scope_call_event_package",
            }

        if package_status == "pending_buyer_confirmation":
            return {
                "action": "confirm_buyer_scope_call_readiness",
                "operator_instruction": (
                    "Confirm buyer interest and readiness before preparing the "
                    "scope-call event package."
                ),
                "future_action": "rerun_scope_call_event_package",
            }

        if package_status == "pending_human_approval":
            return {
                "action": "confirm_human_operator_approval",
                "operator_instruction": (
                    "A human operator must approve scope-call readiness before "
                    "moving toward the scope-call event record."
                ),
                "future_action": "rerun_scope_call_event_package",
            }

        return {
            "action": "resolve_scope_call_event_package_gaps",
            "operator_instruction": (
                "Resolve scope-call package blockers before moving toward the "
                "scope-call event record."
            ),
            "future_action": "rerun_scope_call_event_package",
        }

    def _operator_message(self, package_status: str) -> str:
        if package_status == "ready_for_scope_call":
            return (
                "Scope-call readiness package is ready. The system has not "
                "scheduled the call, created a calendar invite, authorized paid "
                "work, or executed a contract."
            )

        if package_status == "pending_agenda_message_event":
            return (
                "Scope-call readiness package is pending because the agenda "
                "message event record has not been completed."
            )

        if package_status == "pending_buyer_confirmation":
            return (
                "Scope-call readiness package is pending buyer confirmation. "
                "Buyer interest must be confirmed before the package can be ready."
            )

        if package_status == "pending_human_approval":
            return (
                "Scope-call readiness package is pending human operator approval."
            )

        return (
            "Scope-call readiness package is blocked. Resolve the listed blockers "
            "before moving forward."
        )

    def _recommended_action(self, package_status: str) -> str:
        if package_status == "ready_for_scope_call":
            return "prepare_scope_call_event_record"

        return "resolve_scope_call_event_package_gaps"

