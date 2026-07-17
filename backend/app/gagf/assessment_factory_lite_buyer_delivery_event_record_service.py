from datetime import UTC, datetime

from backend.app.gagf.assessment_factory_lite_buyer_delivery_message_service import (
    AssessmentFactoryLiteBuyerDeliveryMessageService,
)


class AssessmentFactoryLiteBuyerDeliveryEventRecordService:
    """Build a local event record for a human-operated buyer delivery action."""

    def __init__(
        self,
        message_service: AssessmentFactoryLiteBuyerDeliveryMessageService | None = None,
    ):
        self.message_service = message_service or AssessmentFactoryLiteBuyerDeliveryMessageService()

    def build_event_record(
        self,
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
    ) -> dict:
        source_message = message or self.message_service.build_message(
            delivery_package=delivery_package,
            export_package=export_package,
            export=export,
            document=document,
            proposal=proposal,
            offer=offer,
            buyer_context=buyer_context,
            operator_approval=operator_approval,
            message_context=message_context,
        )

        context = event_context or {}
        event_status = self._event_status(source_message, context)
        delivery_outcome = self._delivery_outcome(source_message, context, event_status)

        return {
            "status": "ok",
            "event_type": "assessment_factory_lite_buyer_delivery_event_record",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-proposal-export-package",
            "version": "2.1.0",
            "event_stage": "buyer_delivery_event_record",
            "event_status": event_status,
            "event_id": self._event_id(context),
            "recorded_at": self._recorded_at(context),
            "source_message": self._source_message(source_message),
            "delivery_channel": self._delivery_channel(source_message, context),
            "recipient_status": self._recipient_status(source_message, context),
            "attachment_summary": self._attachment_summary(source_message),
            "send_policy_snapshot": source_message.get("send_policy", {}),
            "operator_approval_snapshot": source_message.get("operator_review", {}),
            "boundary_notices": source_message.get("boundary_notices", []),
            "delivery_outcome": delivery_outcome,
            "audit_notes": self._audit_notes(context, event_status),
            "next_action": self._next_action(event_status),
            "operator_message": self._operator_message(event_status),
            "recommended_action": (
                "review_buyer_delivery_event_record"
                if event_status == "recorded"
                else "resolve_buyer_delivery_event_record_gaps"
            ),
        }

    def _event_status(self, message: dict, context: dict) -> str:
        if message.get("message_status") != "send_ready_draft":
            return "blocked"

        if context.get("human_operator_confirmed") is not True:
            return "pending_human_confirmation"

        if context.get("delivery_completed") is True:
            return "recorded"

        return "pending_delivery_completion"

    def _event_id(self, context: dict) -> str:
        return context.get("event_id", "buyer-delivery-event-draft-001")

    def _recorded_at(self, context: dict) -> str:
        return context.get(
            "recorded_at",
            datetime.now(UTC).replace(microsecond=0).isoformat(),
        )

    def _source_message(self, message: dict) -> dict:
        return {
            "message_type": message.get("message_type"),
            "message_stage": message.get("message_stage"),
            "message_status": message.get("message_status"),
            "delivery_channel": message.get("delivery_channel"),
            "release": message.get("release"),
            "version": message.get("version"),
            "recommended_action": message.get("recommended_action"),
        }

    def _delivery_channel(self, message: dict, context: dict) -> dict:
        return {
            "channel": context.get("delivery_channel", message.get("delivery_channel")),
            "channel_status": context.get("channel_status", "operator_recorded"),
            "automated_send_used": False,
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

    def _attachment_summary(self, message: dict) -> dict:
        attachments = message.get("attachments", [])

        return {
            "attachment_count": len(attachments),
            "ready_attachment_count": len(
                [item for item in attachments if item.get("ready") is True]
            ),
            "buyer_facing_attachment_count": len(
                [item for item in attachments if item.get("buyer_facing") is True]
            ),
            "attachments": [
                {
                    "attachment": item.get("attachment"),
                    "filename": item.get("filename"),
                    "format": item.get("format"),
                    "ready": item.get("ready"),
                    "buyer_facing": item.get("buyer_facing"),
                    "attachment_status": item.get("attachment_status"),
                }
                for item in attachments
            ],
        }

    def _delivery_outcome(
        self,
        message: dict,
        context: dict,
        event_status: str,
    ) -> dict:
        return {
            "delivery_completed": context.get("delivery_completed", False),
            "delivery_result": context.get(
                "delivery_result",
                "not_delivered" if event_status != "recorded" else "delivered",
            ),
            "message_status": message.get("message_status"),
            "send_allowed": message.get("send_policy", {}).get("send_allowed"),
            "human_operator_confirmed": context.get("human_operator_confirmed", False),
            "outcome_note": context.get(
                "outcome_note",
                "Delivery event record created for operator review.",
            ),
        }

    def _audit_notes(self, context: dict, event_status: str) -> list[str]:
        notes = list(context.get("audit_notes", []))

        if event_status == "recorded":
            notes.append("human_operated_delivery_recorded")

        if event_status == "pending_human_confirmation":
            notes.append("human_operator_confirmation_required")

        if event_status == "pending_delivery_completion":
            notes.append("delivery_completion_required")

        if event_status == "blocked":
            notes.append("send_ready_message_required")

        notes.append("automated_send_not_performed")

        return notes

    def _next_action(self, event_status: str) -> dict:
        if event_status == "recorded":
            return {
                "action": "review_delivery_event_record",
                "operator_instruction": (
                    "Review the buyer delivery event record, confirm delivery "
                    "metadata, and preserve the record for future follow-up."
                ),
                "future_action": "prepare_buyer_follow_up_tracker",
            }

        if event_status == "pending_human_confirmation":
            return {
                "action": "confirm_human_operator_delivery",
                "operator_instruction": (
                    "Confirm that a human operator reviewed and controlled the "
                    "delivery action before recording completion."
                ),
                "future_action": "record_buyer_delivery_event",
            }

        if event_status == "pending_delivery_completion":
            return {
                "action": "complete_delivery_before_recording",
                "operator_instruction": (
                    "Complete the human-operated delivery action before marking "
                    "the event as recorded."
                ),
                "future_action": "record_buyer_delivery_event",
            }

        return {
            "action": "resolve_buyer_delivery_event_record_gaps",
            "operator_instruction": (
                "Resolve message readiness, delivery approval, or send-policy gaps "
                "before recording buyer delivery."
            ),
            "future_action": "rerun_buyer_delivery_event_record",
        }

    def _operator_message(self, event_status: str) -> str:
        if event_status == "recorded":
            return (
                "Assessment Factory Lite buyer delivery event record has been "
                "created for a human-operated delivery action."
            )

        if event_status == "pending_human_confirmation":
            return (
                "Assessment Factory Lite buyer delivery event record is pending "
                "human operator confirmation."
            )

        if event_status == "pending_delivery_completion":
            return (
                "Assessment Factory Lite buyer delivery event record is pending "
                "delivery completion."
            )

        return (
            "Assessment Factory Lite buyer delivery event record is blocked because "
            "the message is not send-ready."
        )