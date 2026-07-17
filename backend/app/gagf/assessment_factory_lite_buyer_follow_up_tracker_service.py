from datetime import UTC, datetime, timedelta

from backend.app.gagf.assessment_factory_lite_buyer_delivery_event_record_service import (
    AssessmentFactoryLiteBuyerDeliveryEventRecordService,
)


class AssessmentFactoryLiteBuyerFollowUpTrackerService:
    """Build a buyer follow-up tracker from a recorded buyer delivery event."""

    def __init__(
        self,
        event_record_service: AssessmentFactoryLiteBuyerDeliveryEventRecordService | None = None,
    ):
        self.event_record_service = (
            event_record_service or AssessmentFactoryLiteBuyerDeliveryEventRecordService()
        )

    def build_tracker(
        self,
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
    ) -> dict:
        source_event = event_record or self.event_record_service.build_event_record(
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
        )

        context = follow_up_context or {}
        tracker_status = self._tracker_status(source_event, context)

        return {
            "status": "ok",
            "tracker_type": "assessment_factory_lite_buyer_follow_up_tracker",
            "package_name": "Assessment Factory Lite Demo Package",
            "release": "assessment-factory-lite-proposal-export-package",
            "version": "2.1.0",
            "tracker_stage": "buyer_follow_up_tracker",
            "tracker_status": tracker_status,
            "tracker_id": self._tracker_id(context),
            "created_at": self._created_at(context),
            "source_event_record": self._source_event_record(source_event),
            "buyer_response": self._buyer_response(context),
            "follow_up_schedule": self._follow_up_schedule(source_event, context),
            "commercial_next_action": self._commercial_next_action(
                tracker_status,
                context,
            ),
            "follow_up_checklist": self._follow_up_checklist(source_event, context),
            "follow_up_blockers": self._follow_up_blockers(source_event, context),
            "boundary_notices": source_event.get("boundary_notices", []),
            "audit_notes": self._audit_notes(source_event, context, tracker_status),
            "next_action": self._next_action(tracker_status),
            "operator_message": self._operator_message(tracker_status),
            "recommended_action": (
                "review_buyer_follow_up_tracker"
                if tracker_status in {"active", "response_received"}
                else "resolve_buyer_follow_up_tracker_gaps"
            ),
        }

    def _tracker_status(self, event_record: dict, context: dict) -> str:
        if event_record.get("event_status") != "recorded":
            return "blocked"

        buyer_response_status = context.get("buyer_response_status", "no_response")

        if buyer_response_status in {"interested", "questions", "declined"}:
            return "response_received"

        return "active"

    def _tracker_id(self, context: dict) -> str:
        return context.get("tracker_id", "buyer-follow-up-tracker-draft-001")

    def _created_at(self, context: dict) -> str:
        return context.get(
            "created_at",
            datetime.now(UTC).replace(microsecond=0).isoformat(),
        )

    def _source_event_record(self, event_record: dict) -> dict:
        return {
            "event_type": event_record.get("event_type"),
            "event_stage": event_record.get("event_stage"),
            "event_status": event_record.get("event_status"),
            "event_id": event_record.get("event_id"),
            "recorded_at": event_record.get("recorded_at"),
            "release": event_record.get("release"),
            "version": event_record.get("version"),
            "recommended_action": event_record.get("recommended_action"),
        }

    def _buyer_response(self, context: dict) -> dict:
        response_status = context.get("buyer_response_status", "no_response")

        return {
            "response_status": response_status,
            "response_received": response_status != "no_response",
            "response_received_at": context.get("response_received_at", ""),
            "response_summary": context.get("response_summary", ""),
            "buyer_questions": context.get("buyer_questions", []),
            "buyer_objections": context.get("buyer_objections", []),
        }

    def _follow_up_schedule(self, event_record: dict, context: dict) -> dict:
        base_time = context.get("created_at") or event_record.get("recorded_at")
        follow_up_due_at = context.get("follow_up_due_at")

        if not follow_up_due_at:
            follow_up_due_at = self._default_due_at(base_time)

        return {
            "follow_up_required": True,
            "follow_up_due_at": follow_up_due_at,
            "follow_up_channel": context.get("follow_up_channel", "email"),
            "follow_up_owner": context.get("follow_up_owner", "operator"),
            "reminder_status": context.get("reminder_status", "pending"),
        }

    def _default_due_at(self, base_time: str | None) -> str:
        if not base_time:
            return (
                datetime.now(UTC)
                .replace(microsecond=0)
                .__add__(timedelta(days=3))
                .isoformat()
            )

        try:
            parsed = datetime.fromisoformat(base_time.replace("Z", "+00:00"))
        except ValueError:
            return (
                datetime.now(UTC)
                .replace(microsecond=0)
                .__add__(timedelta(days=3))
                .isoformat()
            )

        return (parsed + timedelta(days=3)).isoformat()

    def _commercial_next_action(self, tracker_status: str, context: dict) -> dict:
        response_status = context.get("buyer_response_status", "no_response")

        if tracker_status == "blocked":
            return {
                "action": "resolve_delivery_event_before_follow_up",
                "description": (
                    "Resolve delivery event record gaps before creating a buyer "
                    "follow-up tracker."
                ),
            }

        if response_status == "interested":
            return {
                "action": "schedule_assessment_scope_call",
                "description": (
                    "Buyer expressed interest. Schedule a scope call for the "
                    "bounded paid assessment."
                ),
            }

        if response_status == "questions":
            return {
                "action": "answer_buyer_questions",
                "description": (
                    "Buyer responded with questions. Prepare answers while preserving "
                    "commercial and evidence boundaries."
                ),
            }

        if response_status == "declined":
            return {
                "action": "close_or_nurture_lead",
                "description": (
                    "Buyer declined. Close the opportunity or preserve a light "
                    "nurture note for later."
                ),
            }

        return {
            "action": "send_follow_up_if_no_response",
            "description": (
                "No buyer response recorded. Prepare a human-operated follow-up "
                "message after the due date."
            ),
        }

    def _follow_up_checklist(self, event_record: dict, context: dict) -> list[dict]:
        response_status = context.get("buyer_response_status", "no_response")

        return [
            {
                "check": "delivery_event_recorded",
                "passed": event_record.get("event_status") == "recorded",
                "description": "Buyer delivery event must be recorded.",
            },
            {
                "check": "recipient_confirmed",
                "passed": event_record.get("recipient_status", {}).get(
                    "recipient_confirmed"
                )
                is True,
                "description": "Recipient must be confirmed.",
            },
            {
                "check": "delivery_completed",
                "passed": event_record.get("delivery_outcome", {}).get(
                    "delivery_completed"
                )
                is True,
                "description": "Delivery must be completed.",
            },
            {
                "check": "follow_up_owner_assigned",
                "passed": bool(context.get("follow_up_owner", "operator")),
                "description": "Follow-up owner must be assigned.",
            },
            {
                "check": "buyer_response_classified",
                "passed": response_status
                in {"no_response", "interested", "questions", "declined"},
                "description": "Buyer response status must be classified.",
            },
        ]

    def _follow_up_blockers(self, event_record: dict, context: dict) -> list[str]:
        blockers = [
            item["check"]
            for item in self._follow_up_checklist(event_record, context)
            if not item["passed"]
        ]

        return sorted(set(blockers))

    def _audit_notes(
        self,
        event_record: dict,
        context: dict,
        tracker_status: str,
    ) -> list[str]:
        notes = list(context.get("audit_notes", []))

        if tracker_status == "active":
            notes.append("buyer_follow_up_tracker_active")

        if tracker_status == "response_received":
            notes.append("buyer_response_recorded")

        if tracker_status == "blocked":
            notes.append("recorded_delivery_event_required")

        notes.append("automated_follow_up_not_performed")

        return notes

    def _next_action(self, tracker_status: str) -> dict:
        if tracker_status == "response_received":
            return {
                "action": "review_buyer_response",
                "operator_instruction": (
                    "Review buyer response, update commercial next action, and "
                    "prepare the next human-operated step."
                ),
                "future_action": "prepare_assessment_scope_call_or_response",
            }

        if tracker_status == "active":
            return {
                "action": "monitor_for_buyer_response",
                "operator_instruction": (
                    "Monitor for buyer response and prepare follow-up after the "
                    "due date if no response is recorded."
                ),
                "future_action": "prepare_buyer_follow_up_message",
            }

        return {
            "action": "resolve_buyer_follow_up_tracker_gaps",
            "operator_instruction": (
                "Resolve delivery event, recipient, or completion gaps before "
                "tracking buyer follow-up."
            ),
            "future_action": "rerun_buyer_follow_up_tracker",
        }

    def _operator_message(self, tracker_status: str) -> str:
        if tracker_status == "response_received":
            return (
                "Assessment Factory Lite buyer follow-up tracker has recorded a "
                "buyer response for operator review."
            )

        if tracker_status == "active":
            return (
                "Assessment Factory Lite buyer follow-up tracker is active and "
                "waiting for buyer response."
            )

        return (
            "Assessment Factory Lite buyer follow-up tracker is blocked because "
            "the delivery event is not recorded."
        )