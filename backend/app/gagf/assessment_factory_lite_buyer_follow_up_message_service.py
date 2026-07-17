from backend.app.gagf.assessment_factory_lite_buyer_follow_up_tracker_service import (
    AssessmentFactoryLiteBuyerFollowUpTrackerService,
)


class AssessmentFactoryLiteBuyerFollowUpMessageService:
    """Build a human-operated buyer follow-up message draft from a follow-up tracker."""

    def __init__(
        self,
        tracker_service: AssessmentFactoryLiteBuyerFollowUpTrackerService | None = None,
    ):
        self.tracker_service = tracker_service or AssessmentFactoryLiteBuyerFollowUpTrackerService()

    def build_message(
        self,
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
    ) -> dict:
        source_tracker = tracker or self.tracker_service.build_tracker(
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
        )

        context = follow_up_message_context or {}
        message_status = self._message_status(source_tracker)

        return {
            "status": "ok",
            "message_type": "assessment_factory_lite_buyer_follow_up_message",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-proposal-export-package",
            "version": "2.1.0",
            "message_stage": "buyer_follow_up_message_draft",
            "message_status": message_status,
            "delivery_channel": context.get("delivery_channel", "email_draft"),
            "recipient": self._recipient(context),
            "sender": self._sender(context),
            "subject": self._subject(source_tracker, context),
            "message_body": self._message_body(source_tracker, context),
            "source_follow_up_tracker": self._source_follow_up_tracker(source_tracker),
            "buyer_response_summary": source_tracker.get("buyer_response", {}),
            "commercial_next_action": source_tracker.get("commercial_next_action", {}),
            "follow_up_schedule": source_tracker.get("follow_up_schedule", {}),
            "operator_review": self._operator_review(source_tracker),
            "boundary_notices": source_tracker.get("boundary_notices", []),
            "send_policy": self._send_policy(source_tracker, message_status),
            "next_action": self._next_action(message_status),
            "operator_message": self._operator_message(message_status),
            "recommended_action": (
                "review_buyer_follow_up_message"
                if message_status in {"draft_ready", "response_reply_draft_ready"}
                else "resolve_buyer_follow_up_message_gaps"
            ),
        }

    def _message_status(self, tracker: dict) -> str:
        tracker_status = tracker.get("tracker_status")

        if tracker_status == "active":
            return "draft_ready"

        if tracker_status == "response_received":
            return "response_reply_draft_ready"

        return "blocked"

    def _recipient(self, context: dict) -> dict:
        return {
            "recipient_type": "buyer_role",
            "recipient_role": context.get("recipient_role", "operations_leader"),
            "email_required": True,
            "email_status": context.get("email_status", "operator_to_provide"),
        }

    def _sender(self, context: dict) -> dict:
        return {
            "sender_type": "operator",
            "sender_name": context.get(
                "sender_name",
                "Assessment Factory Lite Operator",
            ),
            "signature_required": True,
        }

    def _subject(self, tracker: dict, context: dict) -> str:
        response_status = tracker.get("buyer_response", {}).get(
            "response_status",
            "no_response",
        )

        if response_status == "interested":
            return "Next Step: Assessment Factory Lite Scope Call"

        if response_status == "questions":
            return "Re: Assessment Factory Lite Proposal Questions"

        if response_status == "declined":
            return "Thank You for Reviewing Assessment Factory Lite"

        return context.get(
            "subject",
            "Following Up on the Assessment Factory Lite Proposal Package",
        )

    def _message_body(self, tracker: dict, context: dict) -> str:
        sender_name = context.get("sender_name", "Assessment Factory Lite Operator")
        response = tracker.get("buyer_response", {})
        response_status = response.get("response_status", "no_response")
        next_action = tracker.get("commercial_next_action", {}).get("action")

        greeting = "Hello,"

        if response_status == "interested":
            body = (
                "Thank you for your interest in the Assessment Factory Lite "
                "proposal package. The recommended next step is to schedule a "
                "bounded assessment scope call so we can confirm workflow scope, "
                "evidence boundaries, timing, and commercial terms."
            )
        elif response_status == "questions":
            body = (
                "Thank you for reviewing the Assessment Factory Lite proposal "
                "package. I received your questions and will respond while "
                "preserving the approved commercial, evidence, and scope boundaries."
            )
        elif response_status == "declined":
            body = (
                "Thank you for reviewing the Assessment Factory Lite proposal "
                "package. I appreciate the consideration and can keep the door open "
                "for a future bounded assessment conversation if priorities change."
            )
        else:
            due_at = tracker.get("follow_up_schedule", {}).get(
                "follow_up_due_at",
                "the follow-up due date",
            )
            body = (
                "I wanted to follow up on the Assessment Factory Lite proposal "
                "package prepared for your review. This follow-up is tied to the "
                f"tracked due date of {due_at} and is intended to confirm whether "
                "you would like to discuss the bounded assessment scope and next steps."
            )

        boundary = (
            "This follow-up is non-binding and does not create a contract, invoice, "
            "payment request, compliance certification, or production onboarding "
            "commitment."
        )

        action = (
            f"Current commercial next action: {next_action}."
            if next_action
            else "Current commercial next action: review buyer response."
        )

        closing = f"Thank you,\n{sender_name}"

        return "\n\n".join([greeting, body, boundary, action, closing])

    def _source_follow_up_tracker(self, tracker: dict) -> dict:
        return {
            "tracker_type": tracker.get("tracker_type"),
            "tracker_stage": tracker.get("tracker_stage"),
            "tracker_status": tracker.get("tracker_status"),
            "tracker_id": tracker.get("tracker_id"),
            "created_at": tracker.get("created_at"),
            "release": tracker.get("release"),
            "version": tracker.get("version"),
            "recommended_action": tracker.get("recommended_action"),
        }

    def _operator_review(self, tracker: dict) -> dict:
        blockers = tracker.get("follow_up_blockers", [])

        return {
            "tracker_status": tracker.get("tracker_status"),
            "follow_up_blockers": blockers,
            "review_required": True,
            "human_operator_required": True,
            "approved_for_sending": False,
        }

    def _send_policy(self, tracker: dict, message_status: str) -> dict:
        return {
            "send_allowed": False,
            "send_blocked_reason": (
                "Human operator review and approval are required before follow-up sending."
                if message_status != "blocked"
                else "Follow-up tracker must be active or response-received before drafting can proceed."
            ),
            "automated_send_allowed": False,
            "requires_human_operator": True,
            "send_rule": (
                "Buyer follow-up messages are draft-only and must be reviewed, "
                "approved, and sent by a human operator."
            ),
        }

    def _next_action(self, message_status: str) -> dict:
        if message_status == "response_reply_draft_ready":
            return {
                "action": "review_buyer_response_reply",
                "operator_instruction": (
                    "Review the response-based follow-up draft, verify buyer response "
                    "context, and send only through a human-operated channel."
                ),
                "future_action": "record_buyer_follow_up_event",
            }

        if message_status == "draft_ready":
            return {
                "action": "review_no_response_follow_up_draft",
                "operator_instruction": (
                    "Review the no-response follow-up draft, verify due date and "
                    "recipient details, and send only through a human-operated channel."
                ),
                "future_action": "record_buyer_follow_up_event",
            }

        return {
            "action": "resolve_buyer_follow_up_message_gaps",
            "operator_instruction": (
                "Resolve follow-up tracker gaps before preparing a buyer follow-up "
                "message draft."
            ),
            "future_action": "rerun_buyer_follow_up_message",
        }

    def _operator_message(self, message_status: str) -> str:
        if message_status == "response_reply_draft_ready":
            return (
                "Assessment Factory Lite buyer follow-up response reply draft is "
                "ready for operator review."
            )

        if message_status == "draft_ready":
            return (
                "Assessment Factory Lite buyer follow-up no-response draft is "
                "ready for operator review."
            )

        return (
            "Assessment Factory Lite buyer follow-up message is blocked because "
            "the follow-up tracker is not active or response-received."
        )