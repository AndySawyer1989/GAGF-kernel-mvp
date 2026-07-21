from __future__ import annotations

from typing import Any

from backend.app.gagf.assessment_factory_lite_payment_request_review_service import (
    AssessmentFactoryLitePaymentRequestReviewService,
)


class AssessmentFactoryLitePaymentRequestEventService:
    """Record a governed payment request event.

    This event is created after payment request review is ready. It may record
    that payment has been requested, but it does not confirm payment, authorize
    paid work, or start production onboarding.
    """

    EVENT_TYPE = "assessment_factory_lite_payment_request_event"
    EVENT_STAGE = "payment_request_event"
    RELEASE = "assessment-factory-lite-scope-call-conversion"
    VERSION = "2.3.0"
    PACKAGE_NAME = "Assessment Factory Lite Demo Package"

    def record_event(
        self,
        *,
        payment_request_review: dict[str, Any] | None = None,
        invoice_creation_event: dict[str, Any] | None = None,
        invoice_creation_review: dict[str, Any] | None = None,
        contract_execution_event: dict[str, Any] | None = None,
        contract_execution_review: dict[str, Any] | None = None,
        paid_assessment_agreement_review: dict[str, Any] | None = None,
        paid_assessment_authorization_package: dict[str, Any] | None = None,
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
        agreement_context: dict[str, Any] | None = None,
        contract_context: dict[str, Any] | None = None,
        contract_execution_context: dict[str, Any] | None = None,
        invoice_context: dict[str, Any] | None = None,
        invoice_creation_context: dict[str, Any] | None = None,
        payment_request_context: dict[str, Any] | None = None,
        payment_request_event_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payment_request_event_context = payment_request_event_context or {}

        review = (
            payment_request_review
            or AssessmentFactoryLitePaymentRequestReviewService().build_review(
                invoice_creation_event=invoice_creation_event,
                invoice_creation_review=invoice_creation_review,
                contract_execution_event=contract_execution_event,
                contract_execution_review=contract_execution_review,
                paid_assessment_agreement_review=paid_assessment_agreement_review,
                paid_assessment_authorization_package=paid_assessment_authorization_package,
                scope_call_event_record=scope_call_event_record,
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
                authorization_context=authorization_context,
                agreement_context=agreement_context,
                contract_context=contract_context,
                contract_execution_context=contract_execution_context,
                invoice_context=invoice_context,
                invoice_creation_context=invoice_creation_context,
                payment_request_context=payment_request_context,
            )
        )

        event_identity = self._event_identity(payment_request_event_context)
        source_summary = self._payment_request_review_summary(review)
        payment_request_record = self._payment_request_record(
            payment_request_event_context
        )
        delivery_record = self._delivery_record(payment_request_event_context)
        operator_confirmation = self._operator_confirmation(
            payment_request_event_context
        )
        event_checklist = self._event_checklist(
            review=review,
            payment_request_record=payment_request_record,
            delivery_record=delivery_record,
            operator_confirmation=operator_confirmation,
        )
        event_blockers = [
            key for key, value in event_checklist.items() if value is not True
        ]
        event_status = self._event_status(
            review=review,
            payment_request_record=payment_request_record,
            delivery_record=delivery_record,
            operator_confirmation=operator_confirmation,
            event_blockers=event_blockers,
        )
        event_score = self._event_score(event_checklist)

        return {
            "status": "ok",
            "event_type": self.EVENT_TYPE,
            "package_name": self.PACKAGE_NAME,
            "release": self.RELEASE,
            "version": self.VERSION,
            "event_stage": self.EVENT_STAGE,
            "event_status": event_status,
            "payment_request_event_id": event_identity["payment_request_event_id"],
            "recorded_at": event_identity["recorded_at"],
            "source_payment_request_review": source_summary,
            "payment_request_record": payment_request_record,
            "delivery_record": delivery_record,
            "operator_confirmation": operator_confirmation,
            "event_checklist": event_checklist,
            "event_blockers": event_blockers,
            "event_score": event_score,
            "payment_request_details": review.get("payment_request_details", {}),
            "buyer_notice_readiness": review.get("buyer_notice_readiness", {}),
            "invoice_record": review.get("invoice_record", {}),
            "delivery_source_record": review.get("delivery_record", {}),
            "invoice_details_review": review.get("invoice_details_review", {}),
            "billing_readiness": review.get("billing_readiness", {}),
            "execution_evidence": review.get("execution_evidence", {}),
            "signature_record": review.get("signature_record", {}),
            "contract_document_review": review.get("contract_document_review", {}),
            "agreement_terms": review.get("agreement_terms", {}),
            "buyer_request": review.get("buyer_request", {}),
            "commercial_review": review.get("commercial_review", {}),
            "evidence_review": review.get("evidence_review", {}),
            "human_authorization": review.get("human_authorization", {}),
            "scheduling_boundary": self._scheduling_boundary(),
            "commercial_boundary": self._commercial_boundary(event_status),
            "evidence_boundary": self._evidence_boundary(),
            "governance_boundary": self._governance_boundary(),
            "boundary_notices": self._boundary_notices(),
            "audit_notes": self._audit_notes(event_status),
            "next_action": self._next_action(event_status),
            "operator_message": self._operator_message(event_status),
            "recommended_action": self._recommended_action(event_status),
        }

    def _event_identity(
        self,
        payment_request_event_context: dict[str, Any],
    ) -> dict[str, str]:
        return {
            "payment_request_event_id": payment_request_event_context.get(
                "payment_request_event_id",
                "payment-request-event-draft-001",
            ),
            "recorded_at": payment_request_event_context.get(
                "recorded_at",
                "not_recorded",
            ),
        }

    def _payment_request_review_summary(
        self,
        review: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "event_type": review.get("event_type"),
            "review_stage": review.get("review_stage"),
            "review_status": review.get("review_status"),
            "release": review.get("release"),
            "version": review.get("version"),
            "payment_request_review_id": review.get("payment_request_review_id"),
            "prepared_at": review.get("prepared_at"),
            "recommended_action": review.get("recommended_action"),
        }

    def _payment_request_record(
        self,
        payment_request_event_context: dict[str, Any],
    ) -> dict[str, Any]:
        payment_requested = (
            payment_request_event_context.get("payment_requested") is True
        )
        payment_request_reference = payment_request_event_context.get(
            "payment_request_reference",
            "not_recorded",
        )
        payment_requested_at = payment_request_event_context.get(
            "payment_requested_at",
            "not_recorded",
        )
        requested_amount = payment_request_event_context.get(
            "requested_amount",
            "not_recorded",
        )

        return {
            "payment_requested": payment_requested,
            "payment_request_reference": payment_request_reference,
            "payment_requested_at": payment_requested_at,
            "requested_amount": requested_amount,
            "payment_request_reference_recorded": payment_request_reference
            != "not_recorded",
            "payment_requested_at_recorded": payment_requested_at != "not_recorded",
            "requested_amount_recorded": requested_amount != "not_recorded",
            "payment_request_record_is_not_payment_confirmation": True,
            "payment_request_record_is_not_paid_work_authorization": True,
        }

    def _delivery_record(
        self,
        payment_request_event_context: dict[str, Any],
    ) -> dict[str, Any]:
        payment_request_delivered_to_buyer = (
            payment_request_event_context.get("payment_request_delivered_to_buyer")
            is True
        )
        delivery_channel = payment_request_event_context.get(
            "delivery_channel",
            "not_recorded",
        )
        delivery_reference = payment_request_event_context.get(
            "delivery_reference",
            "not_recorded",
        )

        return {
            "payment_request_delivered_to_buyer": payment_request_delivered_to_buyer,
            "delivery_channel": delivery_channel,
            "delivery_reference": delivery_reference,
            "delivery_channel_recorded": delivery_channel != "not_recorded",
            "delivery_reference_recorded": delivery_reference != "not_recorded",
            "payment_request_delivery_is_not_payment_confirmation": True,
            "payment_request_delivery_is_not_paid_work_authorization": True,
        }

    def _operator_confirmation(
        self,
        payment_request_event_context: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "human_operator_required": True,
            "human_operator_confirmed_payment_request": payment_request_event_context.get(
                "human_operator_confirmed_payment_request"
            )
            is True,
            "operator_name": payment_request_event_context.get(
                "operator_name",
                "not_recorded",
            ),
            "operator_notes": payment_request_event_context.get("operator_notes", []),
            "payment_confirmed": False,
            "paid_assessment_authorized": False,
            "production_onboarding_approved": False,
        }

    def _event_checklist(
        self,
        *,
        review: dict[str, Any],
        payment_request_record: dict[str, Any],
        delivery_record: dict[str, Any],
        operator_confirmation: dict[str, Any],
    ) -> dict[str, bool]:
        return {
            "payment_request_review_ready": review.get("review_status")
            == "ready_for_payment_request",
            "payment_requested": payment_request_record["payment_requested"],
            "payment_request_reference_recorded": payment_request_record[
                "payment_request_reference_recorded"
            ],
            "payment_requested_at_recorded": payment_request_record[
                "payment_requested_at_recorded"
            ],
            "requested_amount_recorded": payment_request_record[
                "requested_amount_recorded"
            ],
            "payment_request_record_is_not_payment_confirmation": payment_request_record[
                "payment_request_record_is_not_payment_confirmation"
            ],
            "payment_request_record_is_not_paid_work_authorization": payment_request_record[
                "payment_request_record_is_not_paid_work_authorization"
            ],
            "payment_request_delivered_to_buyer": delivery_record[
                "payment_request_delivered_to_buyer"
            ],
            "delivery_channel_recorded": delivery_record["delivery_channel_recorded"],
            "delivery_reference_recorded": delivery_record[
                "delivery_reference_recorded"
            ],
            "payment_request_delivery_is_not_payment_confirmation": delivery_record[
                "payment_request_delivery_is_not_payment_confirmation"
            ],
            "payment_request_delivery_is_not_paid_work_authorization": delivery_record[
                "payment_request_delivery_is_not_paid_work_authorization"
            ],
            "human_operator_confirmed_payment_request": operator_confirmation[
                "human_operator_confirmed_payment_request"
            ],
            "payment_not_confirmed": operator_confirmation["payment_confirmed"]
            is False,
            "paid_assessment_not_authorized": operator_confirmation[
                "paid_assessment_authorized"
            ]
            is False,
            "production_onboarding_not_started": operator_confirmation[
                "production_onboarding_approved"
            ]
            is False,
        }

    def _event_status(
        self,
        *,
        review: dict[str, Any],
        payment_request_record: dict[str, Any],
        delivery_record: dict[str, Any],
        operator_confirmation: dict[str, Any],
        event_blockers: list[str],
    ) -> str:
        if review.get("review_status") == "blocked":
            return "blocked"

        if review.get("review_status") != "ready_for_payment_request":
            return "pending_payment_request_review"

        if payment_request_record["payment_requested"] is not True:
            return "pending_payment_request_confirmation"

        if not (
            payment_request_record["payment_request_reference_recorded"]
            and payment_request_record["payment_requested_at_recorded"]
            and payment_request_record["requested_amount_recorded"]
        ):
            return "pending_payment_request_record"

        if not (
            delivery_record["payment_request_delivered_to_buyer"]
            and delivery_record["delivery_channel_recorded"]
            and delivery_record["delivery_reference_recorded"]
        ):
            return "pending_payment_request_delivery"

        if operator_confirmation["human_operator_confirmed_payment_request"] is not True:
            return "pending_operator_confirmation"

        if event_blockers:
            return "pending_payment_request_event_review"

        return "payment_requested"

    def _event_score(self, event_checklist: dict[str, bool]) -> dict[str, Any]:
        total = len(event_checklist)
        passed = sum(1 for value in event_checklist.values() if value is True)

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

    def _commercial_boundary(self, event_status: str) -> dict[str, Any]:
        return {
            "payment_request_recorded": event_status == "payment_requested",
            "payment_requested": event_status == "payment_requested",
            "payment_confirmed": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "requires_separate_payment_confirmation": True,
            "requires_final_paid_work_authorization": True,
            "requires_separate_production_onboarding": True,
        }

    def _evidence_boundary(self) -> dict[str, Any]:
        return {
            "allowed_evidence": [
                "invoice_reference",
                "invoice_delivery_reference",
                "payment_request_review_notes",
                "buyer_notice_notes",
                "payment_request_reference",
                "payment_request_delivery_reference",
                "non_sensitive_workflow_context",
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
            "payment_request_event_is_not_payment_confirmation": True,
            "payment_request_event_is_not_paid_work_authorization": True,
        }

    def _boundary_notices(self) -> list[str]:
        return [
            "payment_request_event_records_payment_request_only",
            "payment_request_event_does_not_confirm_payment",
            "payment_request_event_does_not_authorize_paid_work",
            "payment_request_event_does_not_start_production_onboarding",
            "payment_request_event_requires_human_operator",
        ]

    def _audit_notes(self, event_status: str) -> list[str]:
        notes = [
            "payment_request_event_built",
            "payment_not_confirmed",
            "paid_assessment_not_authorized",
            "production_onboarding_not_started",
        ]

        if event_status == "payment_requested":
            notes.append("payment_request_event_recorded")
        elif event_status == "pending_payment_request_review":
            notes.append("payment_request_event_pending_review")
        elif event_status == "pending_payment_request_confirmation":
            notes.append("payment_request_event_pending_request_confirmation")
        elif event_status == "pending_payment_request_record":
            notes.append("payment_request_event_pending_request_record")
        elif event_status == "pending_payment_request_delivery":
            notes.append("payment_request_event_pending_delivery")
        elif event_status == "pending_operator_confirmation":
            notes.append("payment_request_event_pending_operator_confirmation")
        elif event_status == "pending_payment_request_event_review":
            notes.append("payment_request_event_pending_event_review")
        else:
            notes.append("payment_request_event_blocked")

        return notes

    def _next_action(self, event_status: str) -> dict[str, str]:
        if event_status == "payment_requested":
            return {
                "action": "prepare_payment_confirmation_review",
                "operator_instruction": (
                    "Prepare payment confirmation review. Do not authorize paid "
                    "work or start production onboarding from this payment request "
                    "event."
                ),
                "future_action": "build_payment_confirmation_review",
            }

        if event_status == "pending_payment_request_review":
            return {
                "action": "complete_payment_request_review",
                "operator_instruction": (
                    "Complete payment request review before recording payment "
                    "request."
                ),
                "future_action": "rerun_payment_request_event",
            }

        if event_status == "pending_payment_request_confirmation":
            return {
                "action": "confirm_payment_request",
                "operator_instruction": (
                    "Confirm that payment was actually requested before recording "
                    "the event."
                ),
                "future_action": "rerun_payment_request_event",
            }

        if event_status == "pending_payment_request_record":
            return {
                "action": "record_payment_request_reference",
                "operator_instruction": (
                    "Record payment request reference, requested_at timestamp, and "
                    "requested amount before continuing."
                ),
                "future_action": "rerun_payment_request_event",
            }

        if event_status == "pending_payment_request_delivery":
            return {
                "action": "record_payment_request_delivery",
                "operator_instruction": (
                    "Record buyer delivery status, delivery channel, and delivery "
                    "reference before continuing."
                ),
                "future_action": "rerun_payment_request_event",
            }

        if event_status == "pending_operator_confirmation":
            return {
                "action": "confirm_operator_payment_request_event",
                "operator_instruction": (
                    "A human operator must confirm the payment request event before "
                    "moving forward."
                ),
                "future_action": "rerun_payment_request_event",
            }

        return {
            "action": "resolve_payment_request_event_gaps",
            "operator_instruction": (
                "Resolve payment request event blockers before moving forward."
            ),
            "future_action": "rerun_payment_request_event",
        }

    def _operator_message(self, event_status: str) -> str:
        if event_status == "payment_requested":
            return (
                "Payment request has been recorded. Payment confirmation, paid work "
                "authorization, and production onboarding remain blocked."
            )

        if event_status == "pending_payment_request_review":
            return (
                "Payment request event is pending because payment request review is "
                "not ready."
            )

        if event_status == "pending_payment_request_confirmation":
            return "Payment request event is pending payment request confirmation."

        if event_status == "pending_payment_request_record":
            return "Payment request event is pending payment request record."

        if event_status == "pending_payment_request_delivery":
            return "Payment request event is pending payment request delivery."

        if event_status == "pending_operator_confirmation":
            return "Payment request event is pending operator confirmation."

        if event_status == "pending_payment_request_event_review":
            return "Payment request event has unresolved event blockers."

        return (
            "Payment request event is blocked. Resolve the listed blockers before "
            "moving forward."
        )

    def _recommended_action(self, event_status: str) -> str:
        if event_status == "payment_requested":
            return "prepare_payment_confirmation_review"

        return "resolve_payment_request_event_gaps"