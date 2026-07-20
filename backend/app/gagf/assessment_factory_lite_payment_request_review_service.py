from __future__ import annotations

from typing import Any

from backend.app.gagf.assessment_factory_lite_invoice_creation_event_service import (
    AssessmentFactoryLiteInvoiceCreationEventService,
)


class AssessmentFactoryLitePaymentRequestReviewService:
    """Build a governed payment request review.

    This review is created after invoice creation is recorded. It reviews
    payment-request readiness only. It does not request payment, confirm payment,
    authorize paid work, or start production onboarding.
    """

    EVENT_TYPE = "assessment_factory_lite_payment_request_review"
    REVIEW_STAGE = "payment_request_review"
    RELEASE = "assessment-factory-lite-scope-call-conversion"
    VERSION = "2.3.0"
    PACKAGE_NAME = "Assessment Factory Lite Demo Package"

    def build_review(
        self,
        *,
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
    ) -> dict[str, Any]:
        payment_request_context = payment_request_context or {}

        event = (
            invoice_creation_event
            or AssessmentFactoryLiteInvoiceCreationEventService().record_event(
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
            )
        )

        payment_request_identity = self._payment_request_identity(payment_request_context)
        source_summary = self._invoice_creation_event_summary(event)
        payment_request_details = self._payment_request_details(payment_request_context)
        buyer_notice_readiness = self._buyer_notice_readiness(payment_request_context)
        operator_review = self._operator_review(payment_request_context)
        review_checklist = self._review_checklist(
            event=event,
            payment_request_details=payment_request_details,
            buyer_notice_readiness=buyer_notice_readiness,
            operator_review=operator_review,
        )
        review_blockers = [
            key for key, value in review_checklist.items() if value is not True
        ]
        review_status = self._review_status(
            event=event,
            payment_request_details=payment_request_details,
            buyer_notice_readiness=buyer_notice_readiness,
            operator_review=operator_review,
            review_blockers=review_blockers,
        )
        review_score = self._review_score(review_checklist)

        return {
            "status": "ok",
            "event_type": self.EVENT_TYPE,
            "package_name": self.PACKAGE_NAME,
            "release": self.RELEASE,
            "version": self.VERSION,
            "review_stage": self.REVIEW_STAGE,
            "review_status": review_status,
            "payment_request_review_id": payment_request_identity[
                "payment_request_review_id"
            ],
            "prepared_at": payment_request_identity["prepared_at"],
            "source_invoice_creation_event": source_summary,
            "payment_request_details": payment_request_details,
            "buyer_notice_readiness": buyer_notice_readiness,
            "operator_review": operator_review,
            "review_checklist": review_checklist,
            "review_blockers": review_blockers,
            "review_score": review_score,
            "invoice_record": event.get("invoice_record", {}),
            "delivery_record": event.get("delivery_record", {}),
            "invoice_details_review": event.get("invoice_details_review", {}),
            "billing_readiness": event.get("billing_readiness", {}),
            "execution_evidence": event.get("execution_evidence", {}),
            "signature_record": event.get("signature_record", {}),
            "contract_document_review": event.get("contract_document_review", {}),
            "agreement_terms": event.get("agreement_terms", {}),
            "buyer_request": event.get("buyer_request", {}),
            "commercial_review": event.get("commercial_review", {}),
            "evidence_review": event.get("evidence_review", {}),
            "human_authorization": event.get("human_authorization", {}),
            "scheduling_boundary": self._scheduling_boundary(),
            "commercial_boundary": self._commercial_boundary(review_status),
            "evidence_boundary": self._evidence_boundary(),
            "governance_boundary": self._governance_boundary(),
            "boundary_notices": self._boundary_notices(),
            "audit_notes": self._audit_notes(review_status),
            "next_action": self._next_action(review_status),
            "operator_message": self._operator_message(review_status),
            "recommended_action": self._recommended_action(review_status),
        }

    def _payment_request_identity(
        self,
        payment_request_context: dict[str, Any],
    ) -> dict[str, str]:
        return {
            "payment_request_review_id": payment_request_context.get(
                "payment_request_review_id",
                "payment-request-review-draft-001",
            ),
            "prepared_at": payment_request_context.get("prepared_at", "not_recorded"),
        }

    def _invoice_creation_event_summary(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_type": event.get("event_type"),
            "event_stage": event.get("event_stage"),
            "event_status": event.get("event_status"),
            "release": event.get("release"),
            "version": event.get("version"),
            "invoice_creation_event_id": event.get("invoice_creation_event_id"),
            "recorded_at": event.get("recorded_at"),
            "recommended_action": event.get("recommended_action"),
        }

    def _payment_request_details(
        self,
        payment_request_context: dict[str, Any],
    ) -> dict[str, Any]:
        payment_amount_confirmed = (
            payment_request_context.get("payment_amount_confirmed") is True
        )
        invoice_reference_confirmed = (
            payment_request_context.get("invoice_reference_confirmed") is True
        )
        payment_due_date_confirmed = (
            payment_request_context.get("payment_due_date_confirmed") is True
        )
        payment_request_language_reviewed = (
            payment_request_context.get("payment_request_language_reviewed") is True
        )

        return {
            "payment_amount_confirmed": payment_amount_confirmed,
            "invoice_reference_confirmed": invoice_reference_confirmed,
            "payment_due_date_confirmed": payment_due_date_confirmed,
            "payment_request_language_reviewed": payment_request_language_reviewed,
            "payment_request_details_ready": (
                payment_amount_confirmed
                and invoice_reference_confirmed
                and payment_due_date_confirmed
                and payment_request_language_reviewed
            ),
            "payment_request_required_before_payment_confirmation": True,
            "payment_confirmation_required_before_paid_work": True,
        }

    def _buyer_notice_readiness(
        self,
        payment_request_context: dict[str, Any],
    ) -> dict[str, Any]:
        buyer_notice_prepared = (
            payment_request_context.get("buyer_notice_prepared") is True
        )
        buyer_notice_channel_confirmed = (
            payment_request_context.get("buyer_notice_channel_confirmed") is True
        )
        payment_instructions_included = (
            payment_request_context.get("payment_instructions_included") is True
        )

        return {
            "buyer_notice_prepared": buyer_notice_prepared,
            "buyer_notice_channel_confirmed": buyer_notice_channel_confirmed,
            "payment_instructions_included": payment_instructions_included,
            "buyer_notice_ready": (
                buyer_notice_prepared
                and buyer_notice_channel_confirmed
                and payment_instructions_included
            ),
            "buyer_notice_is_not_payment_confirmation": True,
            "buyer_notice_is_not_paid_work_authorization": True,
        }

    def _operator_review(self, payment_request_context: dict[str, Any]) -> dict[str, Any]:
        return {
            "human_operator_required": True,
            "payment_request_reviewed_by_operator": payment_request_context.get(
                "payment_request_reviewed_by_operator"
            )
            is True,
            "operator_review_status": payment_request_context.get(
                "operator_review_status",
                "payment_request_review_required",
            ),
            "payment_requested": False,
            "payment_confirmed": False,
            "paid_assessment_authorized": False,
            "production_onboarding_approved": False,
        }

    def _review_checklist(
        self,
        *,
        event: dict[str, Any],
        payment_request_details: dict[str, Any],
        buyer_notice_readiness: dict[str, Any],
        operator_review: dict[str, Any],
    ) -> dict[str, bool]:
        return {
            "invoice_creation_event_recorded": event.get("event_status")
            == "invoice_created",
            "payment_request_details_ready": payment_request_details[
                "payment_request_details_ready"
            ],
            "buyer_notice_ready": buyer_notice_readiness["buyer_notice_ready"],
            "buyer_notice_is_not_payment_confirmation": buyer_notice_readiness[
                "buyer_notice_is_not_payment_confirmation"
            ],
            "buyer_notice_is_not_paid_work_authorization": buyer_notice_readiness[
                "buyer_notice_is_not_paid_work_authorization"
            ],
            "payment_request_reviewed_by_operator": operator_review[
                "payment_request_reviewed_by_operator"
            ],
            "payment_not_requested": operator_review["payment_requested"] is False,
            "payment_not_confirmed": operator_review["payment_confirmed"] is False,
            "paid_assessment_not_authorized": operator_review[
                "paid_assessment_authorized"
            ]
            is False,
            "production_onboarding_not_started": operator_review[
                "production_onboarding_approved"
            ]
            is False,
        }

    def _review_status(
        self,
        *,
        event: dict[str, Any],
        payment_request_details: dict[str, Any],
        buyer_notice_readiness: dict[str, Any],
        operator_review: dict[str, Any],
        review_blockers: list[str],
    ) -> str:
        if event.get("event_status") == "blocked":
            return "blocked"

        if event.get("event_status") != "invoice_created":
            return "pending_invoice_creation_event"

        if payment_request_details["payment_request_details_ready"] is not True:
            return "pending_payment_request_details_review"

        if buyer_notice_readiness["buyer_notice_ready"] is not True:
            return "pending_buyer_notice_readiness"

        if operator_review["payment_request_reviewed_by_operator"] is not True:
            return "pending_operator_review"

        if review_blockers:
            return "pending_payment_request_review"

        return "ready_for_payment_request"

    def _review_score(self, review_checklist: dict[str, bool]) -> dict[str, Any]:
        total = len(review_checklist)
        passed = sum(1 for value in review_checklist.values() if value is True)

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

    def _commercial_boundary(self, review_status: str) -> dict[str, Any]:
        return {
            "payment_request_ready": review_status == "ready_for_payment_request",
            "payment_requested": False,
            "payment_confirmed": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "requires_actual_payment_request": True,
            "requires_separate_payment_confirmation": True,
            "requires_final_paid_work_authorization": True,
            "requires_separate_production_onboarding": True,
        }

    def _evidence_boundary(self) -> dict[str, Any]:
        return {
            "allowed_evidence": [
                "invoice_reference",
                "invoice_delivery_reference",
                "invoice_review_notes",
                "billing_readiness_notes",
                "payment_request_review_notes",
                "buyer_notice_notes",
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
            "payment_request_review_is_not_payment_request": True,
            "payment_request_review_is_not_payment_confirmation": True,
            "payment_request_review_is_not_paid_work_authorization": True,
        }

    def _boundary_notices(self) -> list[str]:
        return [
            "payment_request_review_does_not_request_payment",
            "payment_request_review_does_not_confirm_payment",
            "payment_request_review_does_not_authorize_paid_work",
            "payment_request_review_does_not_start_production_onboarding",
            "payment_request_review_requires_human_operator",
        ]

    def _audit_notes(self, review_status: str) -> list[str]:
        notes = [
            "payment_request_review_built",
            "payment_not_requested",
            "payment_not_confirmed",
            "paid_assessment_not_authorized",
            "production_onboarding_not_started",
        ]

        if review_status == "ready_for_payment_request":
            notes.append("payment_request_review_ready")
        elif review_status == "pending_invoice_creation_event":
            notes.append("payment_request_review_pending_invoice_creation_event")
        elif review_status == "pending_payment_request_details_review":
            notes.append("payment_request_review_pending_payment_request_details")
        elif review_status == "pending_buyer_notice_readiness":
            notes.append("payment_request_review_pending_buyer_notice_readiness")
        elif review_status == "pending_operator_review":
            notes.append("payment_request_review_pending_operator_review")
        elif review_status == "pending_payment_request_review":
            notes.append("payment_request_review_pending_review")
        else:
            notes.append("payment_request_review_blocked")

        return notes

    def _next_action(self, review_status: str) -> dict[str, str]:
        if review_status == "ready_for_payment_request":
            return {
                "action": "prepare_payment_request_event",
                "operator_instruction": (
                    "Prepare payment request event. Do not confirm payment, "
                    "authorize paid work, or start production onboarding from "
                    "this review."
                ),
                "future_action": "build_payment_request_event",
            }

        if review_status == "pending_invoice_creation_event":
            return {
                "action": "complete_invoice_creation_event",
                "operator_instruction": (
                    "Complete invoice creation event before payment request review "
                    "can become ready."
                ),
                "future_action": "rerun_payment_request_review",
            }

        if review_status == "pending_payment_request_details_review":
            return {
                "action": "complete_payment_request_details_review",
                "operator_instruction": (
                    "Confirm payment amount, invoice reference, due date, and "
                    "request language before moving forward."
                ),
                "future_action": "rerun_payment_request_review",
            }

        if review_status == "pending_buyer_notice_readiness":
            return {
                "action": "confirm_buyer_notice_readiness",
                "operator_instruction": (
                    "Confirm buyer notice, notice channel, and payment instructions "
                    "before moving forward."
                ),
                "future_action": "rerun_payment_request_review",
            }

        if review_status == "pending_operator_review":
            return {
                "action": "complete_operator_payment_request_review",
                "operator_instruction": (
                    "A human operator must complete payment request review before "
                    "moving forward."
                ),
                "future_action": "rerun_payment_request_review",
            }

        return {
            "action": "resolve_payment_request_review_gaps",
            "operator_instruction": (
                "Resolve payment request review blockers before moving forward."
            ),
            "future_action": "rerun_payment_request_review",
        }

    def _operator_message(self, review_status: str) -> str:
        if review_status == "ready_for_payment_request":
            return (
                "Payment request review is ready for payment request event. "
                "Payment confirmation, paid work authorization, and production "
                "onboarding remain blocked."
            )

        if review_status == "pending_invoice_creation_event":
            return (
                "Payment request review is pending because invoice creation event "
                "is not recorded."
            )

        if review_status == "pending_payment_request_details_review":
            return "Payment request review is pending payment request details review."

        if review_status == "pending_buyer_notice_readiness":
            return "Payment request review is pending buyer notice readiness."

        if review_status == "pending_operator_review":
            return "Payment request review is pending operator review."

        if review_status == "pending_payment_request_review":
            return "Payment request review has unresolved review blockers."

        return (
            "Payment request review is blocked. Resolve the listed blockers before "
            "moving forward."
        )

    def _recommended_action(self, review_status: str) -> str:
        if review_status == "ready_for_payment_request":
            return "prepare_payment_request_event"

        return "resolve_payment_request_review_gaps"