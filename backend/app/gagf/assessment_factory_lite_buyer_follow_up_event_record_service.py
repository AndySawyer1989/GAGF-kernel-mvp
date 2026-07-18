from datetime import UTC, datetime

from backend.app.gagf.assessment_factory_lite_buyer_follow_up_message_service import (
    AssessmentFactoryLiteBuyerFollowUpMessageService,
)


class AssessmentFactoryLiteBuyerFollowUpEventRecordService:
    """Build a local event record for a human-operated buyer follow-up action."""

    def __init__(
        self,
        message_service: AssessmentFactoryLiteBuyerFollowUpMessageService | None = None,
    ):
        self.message_service = message_service or AssessmentFactoryLiteBuyerFollowUpMessageService()

    def build_event_record(
        self,
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
    ) -> dict:
        source_message = follow_up_message or self.message_service.build_message(
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
        )

        context = follow_up_event_context or {}
        event_status = self._event_status(source_message, context)

        return {
            "status": "ok",
            "event_type": "assessment_factory_lite_buyer_follow_up_event_record",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-proposal-export-package",
            "version": "2.1.0",
            "event_stage": "buyer_follow_up_event_record",
            "event_status": event_status,
            "event_id": self._event_id(context),
            "recorded_at": self._recorded_at(context),
            "source_follow_up_message": self._source_follow_up_message(source_message),
            "follow_up_channel": self._follow_up_channel(source_message, context),
            "recipient_status": self._recipient_status(source_message, context),
            "message_summary": self._message_summary(source_message),
            "send_policy_snapshot": source_message.get("send_policy", {}),
            "operator_review_snapshot": source_message.get("operator_review", {}),
            "buyer_response_summary": source_message.get("buyer_response_summary", {}),
            "commercial_next_action": source_message.get("commercial_next_action", {}),
            "boundary_notices": source_message.get("boundary_notices", []),
            "follow_up_outcome": self._follow_up_outcome(source_message, context, event_status),
            "audit_notes": self._audit_notes(context, event_status),
            "next_action": self._next_action(event_status),
            "operator_message": self._operator_message(event_status),
            "recommended_action": (
                "review_buyer_follow_up_event_record"
                if event_status == "recorded"
                else "resolve_buyer_follow_up_event_record_gaps"
            ),
        }

    def _event_status(self, message: dict, context: dict) -> str:
        if message.get("message_status") not in {
            "draft_ready",
            "response_reply_draft_ready",
        }:
            return "blocked"

        if context.get("human_operator_confirmed") is not True:
            return "pending_human_confirmation"

        if context.get("follow_up_completed") is True:
            return "recorded"

        return "pending_follow_up_completion"

    def _event_id(self, context: dict) -> str:
        return context.get("event_id", "buyer-follow-up-event-draft-001")

    def _recorded_at(self, context: dict) -> str:
        return context.get(
            "recorded_at",
            datetime.now(UTC).replace(microsecond=0).isoformat(),
        )

    def _source_follow_up_message(self, message: dict) -> dict:
        return {
            "message_type": message.get("message_type"),
            "message_stage": message.get("message_stage"),
            "message_status": message.get("message_status"),
            "delivery_channel": message.get("delivery_channel"),
            "release": message.get("release"),
            "version": message.get("version"),
            "recommended_action": message.get("recommended_action"),
        }

    def _follow_up_channel(self, message: dict, context: dict) -> dict:
        return {
            "channel": context.get("follow_up_channel", message.get("delivery_channel")),
            "channel_status": context.get("channel_status", "operator_recorded"),
            "automated_follow_up_used": False,
            "human_operated": True,
            "send_reference": context.get("send_reference", ""),
        }

    def _recipient_status(self, message: dict, context: dict) -> dict:
        recipient = message.get("recipient", {})

        return {
            "recipient_type": recipient.get("recipient_type"),
            "recipient_role": recipient.get("recipient_role"),
            "email_required": recipient.get("email_required"),
            "email_status": context.get(
                "email_status",
                recipient.get("email_status", "operator_to_provide"),
            ),
            "recipient_confirmed": context.get("recipient_confirmed", False),
        }

    def _message_summary(self, message: dict) -> dict:
        return {
            "subject": message.get("subject"),
            "message_status": message.get("message_status"),
            "message_stage": message.get("message_stage"),
            "message_type": message.get("message_type"),
            "commercial_next_action": message.get("commercial_next_action", {}).get(
                "action"
            ),
            "buyer_response_status": message.get("buyer_response_summary", {}).get(
                "response_status"
            ),
        }

    def _follow_up_outcome(
        self,
        message: dict,
        context: dict,
        event_status: str,
    ) -> dict:
        return {
            "follow_up_completed": context.get("follow_up_completed", False),
            "follow_up_result": context.get(
                "follow_up_result",
                "not_sent" if event_status != "recorded" else "sent",
            ),
            "message_status": message.get("message_status"),
            "send_allowed": message.get("send_policy", {}).get("send_allowed"),
            "human_operator_confirmed": context.get("human_operator_confirmed", False),
            "outcome_note": context.get(
                "outcome_note",
                "Follow-up event record created for operator review.",
            ),
        }

    def _audit_notes(self, context: dict, event_status: str) -> list[str]:
        notes = list(context.get("audit_notes", []))

        if event_status == "recorded":
            notes.append("human_operated_follow_up_recorded")

        if event_status == "pending_human_confirmation":
            notes.append("human_operator_confirmation_required")

        if event_status == "pending_follow_up_completion":
            notes.append("follow_up_completion_required")

        if event_status == "blocked":
            notes.append("valid_follow_up_message_required")

        notes.append("automated_follow_up_not_performed")

        return notes

    def _next_action(self, event_status: str) -> dict:
        if event_status == "recorded":
            return {
                "action": "review_follow_up_event_record",
                "operator_instruction": (
                    "Review the buyer follow-up event record, confirm follow-up "
                    "metadata, and preserve the record for commercial tracking."
                ),
                "future_action": "prepare_assessment_scope_call_package",
            }

        if event_status == "pending_human_confirmation":
            return {
                "action": "confirm_human_operator_follow_up",
                "operator_instruction": (
                    "Confirm that a human operator reviewed and controlled the "
                    "follow-up action before recording completion."
                ),
                "future_action": "record_buyer_follow_up_event",
            }

        if event_status == "pending_follow_up_completion":
            return {
                "action": "complete_follow_up_before_recording",
                "operator_instruction": (
                    "Complete the human-operated follow-up action before marking "
                    "the event as recorded."
                ),
                "future_action": "record_buyer_follow_up_event",
            }

        return {
            "action": "resolve_buyer_follow_up_event_record_gaps",
            "operator_instruction": (
                "Resolve follow-up message readiness or human confirmation gaps "
                "before recording buyer follow-up."
            ),
            "future_action": "rerun_buyer_follow_up_event_record",
        }

    def _operator_message(self, event_status: str) -> str:
        if event_status == "recorded":
            return (
                "Assessment Factory Lite buyer follow-up event record has been "
                "created for a human-operated follow-up action."
            )

        if event_status == "pending_human_confirmation":
            return (
                "Assessment Factory Lite buyer follow-up event record is pending "
                "human operator confirmation."
            )

        if event_status == "pending_follow_up_completion":
            return (
                "Assessment Factory Lite buyer follow-up event record is pending "
                "follow-up completion."
            )

        return (
            "Assessment Factory Lite buyer follow-up event record is blocked because "
            "the follow-up message is not valid for recording."
        )