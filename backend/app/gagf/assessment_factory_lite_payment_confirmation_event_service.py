from __future__ import annotations

from typing import Any

from backend.app.gagf.assessment_factory_lite_payment_confirmation_review_service import (
    AssessmentFactoryLitePaymentConfirmationReviewService,
)


class AssessmentFactoryLitePaymentConfirmationEventService:
    """Record a governed payment confirmation event.

    This event is created after payment confirmation review is ready. It may
    record that payment has been confirmed, but it does not authorize paid work
    or start production onboarding.
    """

    EVENT_TYPE = "assessment_factory_lite_payment_confirmation_event"
    EVENT_STAGE = "payment_confirmation_event"
    RELEASE = "assessment-factory-lite-scope-call-conversion"
    VERSION = "2.3.0"
    PACKAGE_NAME = "Assessment Factory Lite Demo Package"

    def record_event(
        self,
        *,
        payment_confirmation_review: dict[str, Any] | None = None,
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
        payment_confirmation_event_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payment_confirmation_event_context = payment_confirmation_event_context or {}

        review = (
            payment_confirmation_review
            or AssessmentFactoryLitePaymentConfirmationReviewService().build_review(
                payment_request_event=payment_request_event,
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
                payment_confirmation_context=payment_confirmation_context,
            )
        )

        event_identity = self._event_identity(payment_confirmation_event_context)
        source_summary = self._payment_confirmation_review_summary(review)
        payment_confirmation_record = self._payment_confirmation_record(
            payment_confirmation_event_context
        )
        reconciliation_record = self._reconciliation_record(
            payment_confirmation_event_context
        )
        operator_confirmation = self._operator_confirmation(
            payment_confirmation_event_context
        )
        event_checklist = self._event_checklist(
            review=review,
            payment_confirmation_record=payment_confirmation_record,
            reconciliation_record=reconciliation_record,
            operator_confirmation=operator_confirmation,
        )
        event_blockers = [
            key for key, value in event_checklist.items() if value is not True
        ]
        event_status = self._event_status(
            review=review,
            payment_confirmation_record=payment_confirmation_record,
            reconciliation_record=reconciliation_record,
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
            "payment_confirmation_event_id": event_identity[
                "payment_confirmation_event_id"
            ],
            "recorded_at": event_identity["recorded_at"],
            "source_payment_confirmation_review": source_summary,
            "payment_confirmation_record": payment_confirmation_record,
            "reconciliation_record": reconciliation_record,
            "operator_confirmation": operator_confirmation,
            "event_checklist": event_checklist,
            "event_blockers": event_blockers,
            "event_score": event_score,
            "payment_evidence_review": review.get("payment_evidence_review", {}),
            "reconciliation_review": review.get("reconciliation_review", {}),
            "payment_request_record": review.get("payment_request_record", {}),
            "payment_request_delivery_record": review.get(
                "payment_request_delivery_record",
                {},
            ),
            "payment_request_details": review.get("payment_request_details", {}),
            "buyer_notice_readiness": review.get("buyer_notice_readiness", {}),
            "invoice_record": review.get("invoice_record", {}),
            "invoice_delivery_record": review.get("invoice_delivery_record", {}),
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
        payment_confirmation_event_context: dict[str, Any],
    ) -> dict[str, str]:
        return {
            "payment_confirmation_event_id": payment_confirmation_event_context.get(
                "payment_confirmation_event_id",
                "payment-confirmation-event-draft-001",
            ),
            "recorded_at": payment_confirmation_event_context.get(
                "recorded_at",
                "not_recorded",
            ),
        }

    def _payment_confirmation_review_summary(
        self,
        review: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "event_type": review.get("event_type"),
            "review_stage": review.get("review_stage"),
            "review_status": review.get("review_status"),
            "release": review.get("release"),
            "version": review.get("version"),
            "payment_confirmation_review_id": review.get(
                "payment_confirmation_review_id"
            ),
            "prepared_at": review.get("prepared_at"),
            "recommended_action": review.get("recommended_action"),
        }

    def _payment_confirmation_record(
        self,
        payment_confirmation_event_context: dict[str, Any],
    ) -> dict[str, Any]:
        payment_confirmed = (
            payment_confirmation_event_context.get("payment_confirmed") is True
        )
        payment_confirmation_reference = payment_confirmation_event_context.get(
            "payment_confirmation_reference",
            "not_recorded",
        )
        payment_confirmed_at = payment_confirmation_event_context.get(
            "payment_confirmed_at",
            "not_recorded",
        )
        confirmed_amount = payment_confirmation_event_context.get(
            "confirmed_amount",
            "not_recorded",
        )

        return {
            "payment_confirmed": payment_confirmed,
            "payment_confirmation_reference": payment_confirmation_reference,
            "payment_confirmed_at": payment_confirmed_at,
            "confirmed_amount": confirmed_amount,
            "payment_confirmation_reference_recorded": (
                payment_confirmation_reference != "not_recorded"
            ),
            "payment_confirmed_at_recorded": payment_confirmed_at != "not_recorded",
            "confirmed_amount_recorded": confirmed_amount != "not_recorded",
            "payment_confirmation_record_is_not_paid_work_authorization": True,
            "payment_confirmation_record_is_not_production_onboarding": True,
        }

    def _reconciliation_record(
        self,
        payment_confirmation_event_context: dict[str, Any],
    ) -> dict[str, Any]:
        amount_reconciled = (
            payment_confirmation_event_context.get("amount_reconciled") is True
        )
        invoice_reference_reconciled = (
            payment_confirmation_event_context.get("invoice_reference_reconciled")
            is True
        )
        payment_method_recorded = (
            payment_confirmation_event_context.get("payment_method_recorded") is True
        )

        return {
            "amount_reconciled": amount_reconciled,
            "invoice_reference_reconciled": invoice_reference_reconciled,
            "payment_method_recorded": payment_method_recorded,
            "reconciliation_recorded": (
                amount_reconciled
                and invoice_reference_reconciled
                and payment_method_recorded
            ),
            "reconciliation_record_is_not_paid_work_authorization": True,
            "reconciliation_record_is_not_production_onboarding": True,
        }

    def _operator_confirmation(
        self,
        payment_confirmation_event_context: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "human_operator_required": True,
            "human_operator_confirmed_payment": payment_confirmation_event_context.get(
                "human_operator_confirmed_payment"
            )
            is True,
            "operator_name": payment_confirmation_event_context.get(
                "operator_name",
                "not_recorded",
            ),
            "operator_notes": payment_confirmation_event_context.get(
                "operator_notes",
                [],
            ),
            "paid_assessment_authorized": False,
            "production_onboarding_approved": False,
        }

    def _event_checklist(
        self,
        *,
        review: dict[str, Any],
        payment_confirmation_record: dict[str, Any],
        reconciliation_record: dict[str, Any],
        operator_confirmation: dict[str, Any],
    ) -> dict[str, bool]:
        return {
            "payment_confirmation_review_ready": review.get("review_status")
            == "ready_for_payment_confirmation",
            "payment_confirmed": payment_confirmation_record["payment_confirmed"],
            "payment_confirmation_reference_recorded": payment_confirmation_record[
                "payment_confirmation_reference_recorded"
            ],
            "payment_confirmed_at_recorded": payment_confirmation_record[
                "payment_confirmed_at_recorded"
            ],
            "confirmed_amount_recorded": payment_confirmation_record[
                "confirmed_amount_recorded"
            ],
            "payment_confirmation_record_is_not_paid_work_authorization": payment_confirmation_record[
                "payment_confirmation_record_is_not_paid_work_authorization"
            ],
            "payment_confirmation_record_is_not_production_onboarding": payment_confirmation_record[
                "payment_confirmation_record_is_not_production_onboarding"
            ],
            "reconciliation_recorded": reconciliation_record[
                "reconciliation_recorded"
            ],
            "reconciliation_record_is_not_paid_work_authorization": reconciliation_record[
                "reconciliation_record_is_not_paid_work_authorization"
            ],
            "reconciliation_record_is_not_production_onboarding": reconciliation_record[
                "reconciliation_record_is_not_production_onboarding"
            ],
            "human_operator_confirmed_payment": operator_confirmation[
                "human_operator_confirmed_payment"
            ],
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
        payment_confirmation_record: dict[str, Any],
        reconciliation_record: dict[str, Any],
        operator_confirmation: dict[str, Any],
        event_blockers: list[str],
    ) -> str:
        if review.get("review_status") == "blocked":
            return "blocked"

        if review.get("review_status") != "ready_for_payment_confirmation":
            return "pending_payment_confirmation_review"

        if payment_confirmation_record["payment_confirmed"] is not True:
            return "pending_payment_confirmation"

        if not (
            payment_confirmation_record["payment_confirmation_reference_recorded"]
            and payment_confirmation_record["payment_confirmed_at_recorded"]
            and payment_confirmation_record["confirmed_amount_recorded"]
        ):
            return "pending_payment_confirmation_record"

        if reconciliation_record["reconciliation_recorded"] is not True:
            return "pending_reconciliation_record"

        if operator_confirmation["human_operator_confirmed_payment"] is not True:
            return "pending_operator_confirmation"

        if event_blockers:
            return "pending_payment_confirmation_event_review"

        return "payment_confirmed"

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
            "payment_confirmation_recorded": event_status == "payment_confirmed",
            "payment_confirmed": event_status == "payment_confirmed",
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "requires_final_paid_work_authorization": True,
            "requires_separate_production_onboarding": True,
        }

    def _evidence_boundary(self) -> dict[str, Any]:
        return {
            "allowed_evidence": [
                "payment_request_reference",
                "payment_request_delivery_reference",
                "payment_receipt_reference",
                "payment_confirmation_reference",
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
            "payment_confirmation_event_is_not_paid_work_authorization": True,
            "payment_confirmation_event_is_not_production_onboarding": True,
        }

    def _boundary_notices(self) -> list[str]:
        return [
            "payment_confirmation_event_records_payment_confirmation_only",
            "payment_confirmation_event_does_not_authorize_paid_work",
            "payment_confirmation_event_does_not_start_production_onboarding",
            "payment_confirmation_event_requires_human_operator",
        ]

    def _audit_notes(self, event_status: str) -> list[str]:
        notes = [
            "payment_confirmation_event_built",
            "paid_assessment_not_authorized",
            "production_onboarding_not_started",
        ]

        if event_status == "payment_confirmed":
            notes.append("payment_confirmation_event_recorded")
        elif event_status == "pending_payment_confirmation_review":
            notes.append("payment_confirmation_event_pending_review")
        elif event_status == "pending_payment_confirmation":
            notes.append("payment_confirmation_event_pending_confirmation")
        elif event_status == "pending_payment_confirmation_record":
            notes.append("payment_confirmation_event_pending_record")
        elif event_status == "pending_reconciliation_record":
            notes.append("payment_confirmation_event_pending_reconciliation")
        elif event_status == "pending_operator_confirmation":
            notes.append("payment_confirmation_event_pending_operator_confirmation")
        elif event_status == "pending_payment_confirmation_event_review":
            notes.append("payment_confirmation_event_pending_event_review")
        else:
            notes.append("payment_confirmation_event_blocked")

        return notes

    def _next_action(self, event_status: str) -> dict[str, str]:
        if event_status == "payment_confirmed":
            return {
                "action": "prepare_paid_assessment_authorization_review",
                "operator_instruction": (
                    "Prepare paid assessment authorization review. Do not authorize "
                    "paid work or start production onboarding from this payment "
                    "confirmation event."
                ),
                "future_action": "build_paid_assessment_authorization_review",
            }

        if event_status == "pending_payment_confirmation_review":
            return {
                "action": "complete_payment_confirmation_review",
                "operator_instruction": (
                    "Complete payment confirmation review before recording payment "
                    "confirmation."
                ),
                "future_action": "rerun_payment_confirmation_event",
            }

        if event_status == "pending_payment_confirmation":
            return {
                "action": "confirm_payment_received",
                "operator_instruction": (
                    "Confirm that payment was actually received before recording "
                    "the event."
                ),
                "future_action": "rerun_payment_confirmation_event",
            }

        if event_status == "pending_payment_confirmation_record":
            return {
                "action": "record_payment_confirmation_reference",
                "operator_instruction": (
                    "Record payment confirmation reference, confirmed_at timestamp, "
                    "and confirmed amount before continuing."
                ),
                "future_action": "rerun_payment_confirmation_event",
            }

        if event_status == "pending_reconciliation_record":
            return {
                "action": "record_payment_reconciliation",
                "operator_instruction": (
                    "Record amount reconciliation, invoice reference reconciliation, "
                    "and payment method before continuing."
                ),
                "future_action": "rerun_payment_confirmation_event",
            }

        if event_status == "pending_operator_confirmation":
            return {
                "action": "confirm_operator_payment_confirmation_event",
                "operator_instruction": (
                    "A human operator must confirm the payment confirmation event "
                    "before moving forward."
                ),
                "future_action": "rerun_payment_confirmation_event",
            }

        return {
            "action": "resolve_payment_confirmation_event_gaps",
            "operator_instruction": (
                "Resolve payment confirmation event blockers before moving forward."
            ),
            "future_action": "rerun_payment_confirmation_event",
        }

    def _operator_message(self, event_status: str) -> str:
        if event_status == "payment_confirmed":
            return (
                "Payment confirmation has been recorded. Paid assessment "
                "authorization and production onboarding remain blocked."
            )

        if event_status == "pending_payment_confirmation_review":
            return (
                "Payment confirmation event is pending because payment confirmation "
                "review is not ready."
            )

        if event_status == "pending_payment_confirmation":
            return "Payment confirmation event is pending payment receipt confirmation."

        if event_status == "pending_payment_confirmation_record":
            return "Payment confirmation event is pending payment confirmation record."

        if event_status == "pending_reconciliation_record":
            return "Payment confirmation event is pending reconciliation record."

        if event_status == "pending_operator_confirmation":
            return "Payment confirmation event is pending operator confirmation."

        if event_status == "pending_payment_confirmation_event_review":
            return "Payment confirmation event has unresolved event blockers."

        return (
            "Payment confirmation event is blocked. Resolve the listed blockers "
            "before moving forward."
        )

    def _recommended_action(self, event_status: str) -> str:
        if event_status == "payment_confirmed":
            return "prepare_paid_assessment_authorization_review"

        return "resolve_payment_confirmation_event_gaps"