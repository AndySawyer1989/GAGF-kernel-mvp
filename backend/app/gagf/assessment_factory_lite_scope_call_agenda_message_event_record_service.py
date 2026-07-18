from backend.app.gagf.assessment_factory_lite_scope_call_agenda_message_service import (
    AssessmentFactoryLiteScopeCallAgendaMessageService,
)


class AssessmentFactoryLiteScopeCallAgendaMessageEventRecordService:
    """Record a human-operated scope-call agenda message event."""

    def __init__(
        self,
        agenda_message_service: AssessmentFactoryLiteScopeCallAgendaMessageService | None = None,
    ):
        self.agenda_message_service = (
            agenda_message_service or AssessmentFactoryLiteScopeCallAgendaMessageService()
        )

    def record_event(
        self,
        scope_call_agenda_message: dict | None = None,
        scope_call_package: dict | None = None,
        follow_up_event_record: dict | None = None,
        follow_up_message: dict | None = None,
        tracker: dict | None = None,
        event_record: dict | None = None,
        message: dict | None = None,
        delivery_package: dict | None = None,
        export_package: dict | None = None,
        export: dict | None = None,
        document: dict | None = None,
        proposal: dict | None = None,
        offer: dict | None = None,
        buyer_context: dict | None = None,
        operator_approval: dict | None = None,
        message_context: dict | None = None,
        event_context: dict | None = None,
        follow_up_context: dict | None = None,
        follow_up_message_context: dict | None = None,
        follow_up_event_context: dict | None = None,
        scope_call_context: dict | None = None,
        scope_call_message_context: dict | None = None,
        scope_call_message_event_context: dict | None = None,
    ) -> dict:
        source_message = scope_call_agenda_message or self.agenda_message_service.build_message(
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
        )

        context = scope_call_message_event_context or {}
        event_status = self._event_status(source_message, context)

        return {
            "status": "ok",
            "event_type": "assessment_factory_lite_scope_call_agenda_message_event_record",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-scope-call-conversion",
            "version": "2.3.0",
            "event_stage": "scope_call_agenda_message_event_record",
            "event_status": event_status,
            "event_id": context.get("event_id", "scope-call-agenda-message-event-draft-001"),
            "recorded_at": context.get("recorded_at"),
            "source_scope_call_agenda_message": self._source_message(source_message),
            "message_channel": self._message_channel(source_message, context),
            "recipient_status": self._recipient_status(source_message, context),
            "message_summary": self._message_summary(source_message),
            "send_policy_snapshot": source_message.get("send_policy", {}),
            "operator_review_snapshot": source_message.get("operator_review", {}),
            "scope_call_package_summary": source_message.get("source_scope_call_package", {}),
            "agenda_summary": source_message.get("agenda_summary", {}),
            "commercial_next_action": source_message.get("commercial_next_action", {}),
            "scheduling_boundary": source_message.get("scheduling_boundary", {}),
            "commercial_boundary": source_message.get("commercial_boundary", {}),
            "evidence_boundary": source_message.get("evidence_boundary", {}),
            "event_checklist": self._event_checklist(source_message, context),
            "event_blockers": self._event_blockers(source_message, context),
            "boundary_notices": source_message.get("boundary_notices", []),
            "audit_notes": self._audit_notes(event_status),
            "next_action": self._next_action(event_status),
            "operator_message": self._operator_message(event_status),
            "recommended_action": (
                "prepare_scope_call_event_record"
                if event_status == "recorded"
                else "resolve_scope_call_agenda_message_event_gaps"
            ),
        }

    def _event_status(self, message: dict, context: dict) -> str:
        if message.get("message_status") != "draft_ready":
            return "blocked"

        if context.get("human_operator_confirmed") is not True:
            return "pending_human_confirmation"

        if context.get("agenda_message_sent") is not True:
            return "pending_agenda_message_completion"

        return "recorded"

    def _source_message(self, message: dict) -> dict:
        return {
            "message_type": message.get("message_type"),
            "message_stage": message.get("message_stage"),
            "message_status": message.get("message_status"),
            "release": message.get("release"),
            "version": message.get("version"),
            "delivery_channel": message.get("delivery_channel"),
            "subject": message.get("subject"),
            "recommended_action": message.get("recommended_action"),
        }

    def _message_channel(self, message: dict, context: dict) -> dict:
        return {
            "delivery_channel": context.get(
                "delivery_channel",
                message.get("delivery_channel", "email_draft"),
            ),
            "automated_send_used": False,
            "calendar_invite_created": False,
            "automatic_scheduling_used": False,
            "human_operated": True,
        }

    def _recipient_status(self, message: dict, context: dict) -> dict:
        recipient = message.get("recipient", {})

        return {
            "recipient_type": recipient.get("recipient_type", "buyer_role"),
            "recipient_role": recipient.get("recipient_role", "operations_leader"),
            "email_required": recipient.get("email_required", True),
            "email_status": context.get(
                "email_status",
                recipient.get("email_status", "operator_to_provide"),
            ),
            "recipient_confirmed": context.get("recipient_confirmed", False),
        }

    def _message_summary(self, message: dict) -> dict:
        body = message.get("message_body", "")

        return {
            "subject": message.get("subject"),
            "body_available": bool(body),
            "body_character_count": len(body),
            "agenda_item_count": message.get("agenda_summary", {}).get("agenda_item_count", 0),
            "non_binding_notice_included": "non-binding" in body,
            "no_calendar_invite_notice_included": "calendar invite" in body,
            "human_operator_notice_included": "human operator" in body,
        }

    def _event_checklist(self, message: dict, context: dict) -> dict:
        return {
            "message_draft_ready": message.get("message_status") == "draft_ready",
            "human_operator_confirmed": context.get("human_operator_confirmed") is True,
            "agenda_message_sent": context.get("agenda_message_sent") is True,
            "recipient_confirmed": context.get("recipient_confirmed") is True,
            "automated_send_not_used": True,
            "calendar_invite_not_created": True,
            "automatic_scheduling_not_used": True,
        }

    def _event_blockers(self, message: dict, context: dict) -> list[str]:
        checklist = self._event_checklist(message, context)
        blockers = [key for key, value in checklist.items() if value is not True]
        return sorted(blockers)

    def _audit_notes(self, event_status: str) -> list[str]:
        if event_status == "recorded":
            return [
                "scope_call_agenda_message_event_recorded",
                "human_operator_confirmed_agenda_message_action",
                "automated_scope_call_sending_not_performed",
                "automatic_scheduling_not_performed",
            ]

        if event_status == "pending_human_confirmation":
            return [
                "scope_call_agenda_message_event_pending_human_confirmation",
                "automated_scope_call_sending_not_performed",
                "automatic_scheduling_not_performed",
            ]

        if event_status == "pending_agenda_message_completion":
            return [
                "scope_call_agenda_message_event_pending_completion",
                "automated_scope_call_sending_not_performed",
                "automatic_scheduling_not_performed",
            ]

        return [
            "scope_call_agenda_message_event_blocked",
            "automated_scope_call_sending_not_performed",
            "automatic_scheduling_not_performed",
        ]

    def _next_action(self, event_status: str) -> dict:
        if event_status == "recorded":
            return {
                "action": "prepare_scope_call_event_record",
                "operator_instruction": (
                    "Use the recorded scope-call agenda message event to prepare "
                    "the next human-operated scope-call event record."
                ),
                "future_action": "build_scope_call_event_record",
            }

        if event_status == "pending_human_confirmation":
            return {
                "action": "confirm_scope_call_agenda_message_event",
                "operator_instruction": (
                    "Confirm that a human operator reviewed and controlled the "
                    "scope-call agenda message action."
                ),
                "future_action": "rerun_scope_call_agenda_message_event_record",
            }

        if event_status == "pending_agenda_message_completion":
            return {
                "action": "complete_scope_call_agenda_message_action",
                "operator_instruction": (
                    "Complete or confirm the agenda message action before recording "
                    "the event as complete."
                ),
                "future_action": "rerun_scope_call_agenda_message_event_record",
            }

        return {
            "action": "resolve_scope_call_agenda_message_event_gaps",
            "operator_instruction": (
                "Resolve scope-call agenda message readiness gaps before recording "
                "a buyer-facing agenda message event."
            ),
            "future_action": "rerun_scope_call_agenda_message_event_record",
        }

    def _operator_message(self, event_status: str) -> str:
        if event_status == "recorded":
            return (
                "Assessment Factory Lite scope-call agenda message event has been "
                "recorded as a human-operated buyer communication action."
            )

        if event_status == "pending_human_confirmation":
            return (
                "Assessment Factory Lite scope-call agenda message event is pending "
                "human operator confirmation."
            )

        if event_status == "pending_agenda_message_completion":
            return (
                "Assessment Factory Lite scope-call agenda message event is pending "
                "agenda message completion."
            )

        return (
            "Assessment Factory Lite scope-call agenda message event is blocked "
            "because the source message is not ready."
        )