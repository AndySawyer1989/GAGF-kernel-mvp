from __future__ import annotations

from typing import Any

from backend.app.gagf.assessment_factory_lite_payment_request_event_service import (
    AssessmentFactoryLitePaymentRequestEventService,
)


class AssessmentFactoryLitePaymentConfirmationReviewService:
    """Build a governed payment confirmation review.

    This review is created after payment request event is recorded. It reviews
    payment-confirmation readiness only. It does not confirm payment, authorize
    paid work, or start production onboarding.
    """

    EVENT_TYPE = "assessment_factory_lite_payment_confirmation_review"
    REVIEW_STAGE = "payment_confirmation_review"
    RELEASE = "assessment-factory-lite-scope-call-conversion"
    VERSION = "2.3.0"
    PACKAGE_NAME = "Assessment Factory Lite Demo Package"

    def build_review(
        self,
        *,
        payment_request_event: dict[str, Any] | None = None,
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
        payment_confirmation_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payment_confirmation_context = payment_confirmation_context or {}

        event = (
            payment_request_event
            or AssessmentFactoryLitePaymentRequestEventService().record_event(
                payment_request_review=payment_request_review,
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
                payment_request_event_context=payment_request_event_context,
            )
        )

        review_identity = self._review_identity(payment_confirmation_context)
        source_summary = self._payment_request_event_summary(event)
        payment_evidence_review = self._payment_evidence_review(
            payment_confirmation_context
        )
        reconciliation_review = self._reconciliation_review(
            payment_confirmation_context
        )
        operator_review = self._operator_review(payment_confirmation_context)
        review_checklist = self._review_checklist(
            event=event,
            payment_evidence_review=payment_evidence_review,
            reconciliation_review=reconciliation_review,
            operator_review=operator_review,
        )
        review_blockers = [
            key for key, value in review_checklist.items() if value is not True
        ]
        review_status = self._review_status(
            event=event,
            payment_evidence_review=payment_evidence_review,
            reconciliation_review=reconciliation_review,
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
            "payment_confirmation_review_id": review_identity[
                "payment_confirmation_review_id"
            ],
            "prepared_at": review_identity["prepared_at"],
            "source_payment_request_event": source_summary,
            "payment_evidence_review": payment_evidence_review,
            "reconciliation_review": reconciliation_review,
            "operator_review": operator_review,
            "review_checklist": review_checklist,
            "review_blockers": review_blockers,
            "review_score": review_score,
            "payment_request_record": event.get("payment_request_record", {}),
            "payment_request_delivery_record": event.get("delivery_record", {}),
            "payment_request_details": event.get("payment_request_details", {}),
            "buyer_notice_readiness": event.get("buyer_notice_readiness", {}),
            "invoice_record": event.get("invoice_record", {}),
            "invoice_delivery_record": event.get("delivery_source_record", {}),
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

    def _review_identity(
        self,
        payment_confirmation_context: dict[str, Any],
    ) -> dict[str, str]:
        return {
            "payment_confirmation_review_id": payment_confirmation_context.get(
                "payment_confirmation_review_id",
                "payment-confirmation-review-draft-001",
            ),
            "prepared_at": payment_confirmation_context.get(
                "prepared_at",
                "not_recorded",
            ),
        }

    def _payment_request_event_summary(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_type": event.get("event_type"),
            "event_stage": event.get("event_stage"),
            "event_status": event.get("event_status"),
            "release": event.get("release"),
            "version": event.get("version"),
            "payment_request_event_id": event.get("payment_request_event_id"),
            "recorded_at": event.get("recorded_at"),
            "recommended_action": event.get("recommended_action"),
        }

    def _payment_evidence_review(
        self,
        payment_confirmation_context: dict[str, Any],
    ) -> dict[str, Any]:
        payment_receipt_available = (
            payment_confirmation_context.get("payment_receipt_available") is True
        )
        payment_reference_available = (
            payment_confirmation_context.get("payment_reference_available") is True
        )
        received_amount_reviewed = (
            payment_confirmation_context.get("received_amount_reviewed") is True
        )
        received_at_reviewed = (
            payment_confirmation_context.get("received_at_reviewed") is True
        )

        return {
            "payment_receipt_available": payment_receipt_available,
            "payment_reference_available": payment_reference_available,
            "received_amount_reviewed": received_amount_reviewed,
            "received_at_reviewed": received_at_reviewed,
            "payment_evidence_ready": (
                payment_receipt_available
                and payment_reference_available
                and received_amount_reviewed
                and received_at_reviewed
            ),
            "payment_evidence_review_is_not_payment_confirmation": True,
            "payment_evidence_review_is_not_paid_work_authorization": True,
        }

    def _reconciliation_review(
        self,
        payment_confirmation_context: dict[str, Any],
    ) -> dict[str, Any]:
        amount_matches_request = (
            payment_confirmation_context.get("amount_matches_request") is True
        )
        invoice_reference_matches = (
            payment_confirmation_context.get("invoice_reference_matches") is True
        )
        payment_method_reviewed = (
            payment_confirmation_context.get("payment_method_reviewed") is True
        )

        return {
            "amount_matches_request": amount_matches_request,
            "invoice_reference_matches": invoice_reference_matches,
            "payment_method_reviewed": payment_method_reviewed,
            "reconciliation_ready": (
                amount_matches_request
                and invoice_reference_matches
                and payment_method_reviewed
            ),
            "reconciliation_is_not_payment_confirmation": True,
            "reconciliation_is_not_paid_work_authorization": True,
        }

    def _operator_review(
        self,
        payment_confirmation_context: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "human_operator_required": True,
            "payment_confirmation_reviewed_by_operator": payment_confirmation_context.get(
                "payment_confirmation_reviewed_by_operator"
            )
            is True,
            "operator_review_status": payment_confirmation_context.get(
                "operator_review_status",
                "payment_confirmation_review_required",
            ),
            "payment_confirmed": False,
            "paid_assessment_authorized": False,
            "production_onboarding_approved": False,
        }

    def _review_checklist(
        self,
        *,
        event: dict[str, Any],
        payment_evidence_review: dict[str, Any],
        reconciliation_review: dict[str, Any],
        operator_review: dict[str, Any],
    ) -> dict[str, bool]:
        return {
            "payment_request_event_recorded": event.get("event_status")
            == "payment_requested",
            "payment_evidence_ready": payment_evidence_review[
                "payment_evidence_ready"
            ],
            "payment_evidence_review_is_not_payment_confirmation": payment_evidence_review[
                "payment_evidence_review_is_not_payment_confirmation"
            ],
            "payment_evidence_review_is_not_paid_work_authorization": payment_evidence_review[
                "payment_evidence_review_is_not_paid_work_authorization"
            ],
            "reconciliation_ready": reconciliation_review["reconciliation_ready"],
            "reconciliation_is_not_payment_confirmation": reconciliation_review[
                "reconciliation_is_not_payment_confirmation"
            ],
            "reconciliation_is_not_paid_work_authorization": reconciliation_review[
                "reconciliation_is_not_paid_work_authorization"
            ],
            "payment_confirmation_reviewed_by_operator": operator_review[
                "payment_confirmation_reviewed_by_operator"
            ],
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
        payment_evidence_review: dict[str, Any],
        reconciliation_review: dict[str, Any],
        operator_review: dict[str, Any],
        review_blockers: list[str],
    ) -> str:
        if event.get("event_status") == "blocked":
            return "blocked"

        if event.get("event_status") != "payment_requested":
            return "pending_payment_request_event"

        if payment_evidence_review["payment_evidence_ready"] is not True:
            return "pending_payment_evidence_review"

        if reconciliation_review["reconciliation_ready"] is not True:
            return "pending_reconciliation_review"

        if operator_review["payment_confirmation_reviewed_by_operator"] is not True:
            return "pending_operator_review"

        if review_blockers:
            return "pending_payment_confirmation_review"

        return "ready_for_payment_confirmation"

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
            "payment_confirmation_ready": review_status
            == "ready_for_payment_confirmation",
            "payment_confirmed": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "requires_actual_payment_confirmation": True,
            "requires_final_paid_work_authorization": True,
            "requires_separate_production_onboarding": True,
        }

    def _evidence_boundary(self) -> dict[str, Any]:
        return {
            "allowed_evidence": [
                "payment_request_reference",
                "payment_request_delivery_reference",
                "payment_receipt_reference",
                "received_amount_review_notes",
                "payment_reconciliation_notes",
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
            "payment_confirmation_review_is_not_payment_confirmation": True,
            "payment_confirmation_review_is_not_paid_work_authorization": True,
        }

    def _boundary_notices(self) -> list[str]:
        return [
            "payment_confirmation_review_does_not_confirm_payment",
            "payment_confirmation_review_does_not_authorize_paid_work",
            "payment_confirmation_review_does_not_start_production_onboarding",
            "payment_confirmation_review_requires_human_operator",
        ]

    def _audit_notes(self, review_status: str) -> list[str]:
        notes = [
            "payment_confirmation_review_built",
            "payment_not_confirmed",
            "paid_assessment_not_authorized",
            "production_onboarding_not_started",
        ]

        if review_status == "ready_for_payment_confirmation":
            notes.append("payment_confirmation_review_ready")
        elif review_status == "pending_payment_request_event":
            notes.append("payment_confirmation_review_pending_payment_request_event")
        elif review_status == "pending_payment_evidence_review":
            notes.append("payment_confirmation_review_pending_payment_evidence")
        elif review_status == "pending_reconciliation_review":
            notes.append("payment_confirmation_review_pending_reconciliation")
        elif review_status == "pending_operator_review":
            notes.append("payment_confirmation_review_pending_operator_review")
        elif review_status == "pending_payment_confirmation_review":
            notes.append("payment_confirmation_review_pending_review")
        else:
            notes.append("payment_confirmation_review_blocked")

        return notes

    def _next_action(self, review_status: str) -> dict[str, str]:
        if review_status == "ready_for_payment_confirmation":
            return {
                "action": "prepare_payment_confirmation_event",
                "operator_instruction": (
                    "Prepare payment confirmation event. Do not authorize paid "
                    "work or start production onboarding from this review."
                ),
                "future_action": "build_payment_confirmation_event",
            }

        if review_status == "pending_payment_request_event":
            return {
                "action": "complete_payment_request_event",
                "operator_instruction": (
                    "Complete payment request event before payment confirmation "
                    "review can become ready."
                ),
                "future_action": "rerun_payment_confirmation_review",
            }

        if review_status == "pending_payment_evidence_review":
            return {
                "action": "complete_payment_evidence_review",
                "operator_instruction": (
                    "Review payment receipt, payment reference, received amount, "
                    "and received_at timestamp before moving forward."
                ),
                "future_action": "rerun_payment_confirmation_review",
            }

        if review_status == "pending_reconciliation_review":
            return {
                "action": "complete_payment_reconciliation_review",
                "operator_instruction": (
                    "Confirm amount match, invoice reference match, and payment "
                    "method review before moving forward."
                ),
                "future_action": "rerun_payment_confirmation_review",
            }

        if review_status == "pending_operator_review":
            return {
                "action": "complete_operator_payment_confirmation_review",
                "operator_instruction": (
                    "A human operator must complete payment confirmation review "
                    "before moving forward."
                ),
                "future_action": "rerun_payment_confirmation_review",
            }

        return {
            "action": "resolve_payment_confirmation_review_gaps",
            "operator_instruction": (
                "Resolve payment confirmation review blockers before moving forward."
            ),
            "future_action": "rerun_payment_confirmation_review",
        }

    def _operator_message(self, review_status: str) -> str:
        if review_status == "ready_for_payment_confirmation":
            return (
                "Payment confirmation review is ready for payment confirmation "
                "event. Paid work authorization and production onboarding remain "
                "blocked."
            )

        if review_status == "pending_payment_request_event":
            return (
                "Payment confirmation review is pending because payment request "
                "event is not recorded."
            )

        if review_status == "pending_payment_evidence_review":
            return "Payment confirmation review is pending payment evidence review."

        if review_status == "pending_reconciliation_review":
            return "Payment confirmation review is pending reconciliation review."

        if review_status == "pending_operator_review":
            return "Payment confirmation review is pending operator review."

        if review_status == "pending_payment_confirmation_review":
            return "Payment confirmation review has unresolved review blockers."

        return (
            "Payment confirmation review is blocked. Resolve the listed blockers "
            "before moving forward."
        )

    def _recommended_action(self, review_status: str) -> str:
        if review_status == "ready_for_payment_confirmation":
            return "prepare_payment_confirmation_event"

        return "resolve_payment_confirmation_review_gaps"