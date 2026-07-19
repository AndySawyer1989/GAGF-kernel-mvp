from __future__ import annotations

from typing import Any

from backend.app.gagf.assessment_factory_lite_paid_assessment_agreement_review_service import (
    AssessmentFactoryLitePaidAssessmentAgreementReviewService,
)


class AssessmentFactoryLiteContractExecutionReviewService:
    """Build a governed contract execution review.

    This review is created after paid assessment agreement review is ready.
    It prepares the operator for contract execution review only. It does not
    execute a contract, create an invoice, request payment, authorize paid work,
    or start production onboarding.
    """

    EVENT_TYPE = "assessment_factory_lite_contract_execution_review"
    REVIEW_STAGE = "contract_execution_review"
    RELEASE = "assessment-factory-lite-scope-call-conversion"
    VERSION = "2.3.0"
    PACKAGE_NAME = "Assessment Factory Lite Demo Package"

    def build_review(
        self,
        *,
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
    ) -> dict[str, Any]:
        contract_context = contract_context or {}

        agreement_review = (
            paid_assessment_agreement_review
            or AssessmentFactoryLitePaidAssessmentAgreementReviewService().build_review(
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
            )
        )

        contract_identity = self._contract_identity(contract_context)
        source_summary = self._agreement_review_summary(agreement_review)
        contract_document_review = self._contract_document_review(contract_context)
        signature_readiness = self._signature_readiness(contract_context)
        operator_review = self._operator_review(contract_context)
        review_checklist = self._review_checklist(
            agreement_review=agreement_review,
            contract_document_review=contract_document_review,
            signature_readiness=signature_readiness,
            operator_review=operator_review,
        )
        review_blockers = [
            key for key, value in review_checklist.items() if value is not True
        ]
        review_status = self._review_status(
            agreement_review=agreement_review,
            contract_document_review=contract_document_review,
            signature_readiness=signature_readiness,
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
            "contract_review_id": contract_identity["contract_review_id"],
            "prepared_at": contract_identity["prepared_at"],
            "source_paid_assessment_agreement_review": source_summary,
            "contract_document_review": contract_document_review,
            "signature_readiness": signature_readiness,
            "operator_review": operator_review,
            "review_checklist": review_checklist,
            "review_blockers": review_blockers,
            "review_score": review_score,
            "agreement_terms": agreement_review.get("agreement_terms", {}),
            "buyer_acknowledgment": agreement_review.get("buyer_acknowledgment", {}),
            "buyer_request": agreement_review.get("buyer_request", {}),
            "commercial_review": agreement_review.get("commercial_review", {}),
            "evidence_review": agreement_review.get("evidence_review", {}),
            "human_authorization": agreement_review.get("human_authorization", {}),
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

    def _contract_identity(self, contract_context: dict[str, Any]) -> dict[str, str]:
        return {
            "contract_review_id": contract_context.get(
                "contract_review_id",
                "contract-execution-review-draft-001",
            ),
            "prepared_at": contract_context.get("prepared_at", "not_recorded"),
        }

    def _agreement_review_summary(
        self,
        agreement_review: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "event_type": agreement_review.get("event_type"),
            "review_stage": agreement_review.get("review_stage"),
            "review_status": agreement_review.get("review_status"),
            "release": agreement_review.get("release"),
            "version": agreement_review.get("version"),
            "agreement_review_id": agreement_review.get("agreement_review_id"),
            "prepared_at": agreement_review.get("prepared_at"),
            "recommended_action": agreement_review.get("recommended_action"),
        }

    def _contract_document_review(
        self,
        contract_context: dict[str, Any],
    ) -> dict[str, Any]:
        contract_document_prepared = (
            contract_context.get("contract_document_prepared") is True
        )
        contract_terms_reviewed = contract_context.get("contract_terms_reviewed") is True
        legal_language_reviewed = contract_context.get("legal_language_reviewed") is True
        scope_matches_agreement = contract_context.get("scope_matches_agreement") is True

        return {
            "contract_document_prepared": contract_document_prepared,
            "contract_terms_reviewed": contract_terms_reviewed,
            "legal_language_reviewed": legal_language_reviewed,
            "scope_matches_agreement": scope_matches_agreement,
            "contract_document_ready": (
                contract_document_prepared
                and contract_terms_reviewed
                and legal_language_reviewed
                and scope_matches_agreement
            ),
            "contract_execution_required_before_invoice": True,
            "invoice_required_before_payment": True,
            "payment_required_before_paid_work": True,
        }

    def _signature_readiness(
        self,
        contract_context: dict[str, Any],
    ) -> dict[str, Any]:
        buyer_signature_ready = contract_context.get("buyer_signature_ready") is True
        provider_signature_ready = (
            contract_context.get("provider_signature_ready") is True
        )
        signature_method_confirmed = (
            contract_context.get("signature_method_confirmed") is True
        )

        return {
            "buyer_signature_ready": buyer_signature_ready,
            "provider_signature_ready": provider_signature_ready,
            "signature_method_confirmed": signature_method_confirmed,
            "signature_readiness_confirmed": (
                buyer_signature_ready
                and provider_signature_ready
                and signature_method_confirmed
            ),
            "signature_readiness_is_not_execution": True,
            "contract_executed": False,
        }

    def _operator_review(self, contract_context: dict[str, Any]) -> dict[str, Any]:
        return {
            "human_operator_required": True,
            "contract_execution_reviewed_by_operator": contract_context.get(
                "contract_execution_reviewed_by_operator"
            )
            is True,
            "operator_review_status": contract_context.get(
                "operator_review_status",
                "contract_execution_review_required",
            ),
            "contract_execution_approved": False,
            "invoice_creation_approved": False,
            "payment_request_approved": False,
            "paid_assessment_authorized": False,
            "production_onboarding_approved": False,
        }

    def _review_checklist(
        self,
        *,
        agreement_review: dict[str, Any],
        contract_document_review: dict[str, Any],
        signature_readiness: dict[str, Any],
        operator_review: dict[str, Any],
    ) -> dict[str, bool]:
        return {
            "agreement_review_ready": agreement_review.get("review_status")
            == "ready_for_agreement_execution_review",
            "contract_document_ready": contract_document_review[
                "contract_document_ready"
            ],
            "signature_readiness_confirmed": signature_readiness[
                "signature_readiness_confirmed"
            ],
            "signature_readiness_is_not_execution": signature_readiness[
                "signature_readiness_is_not_execution"
            ],
            "contract_execution_reviewed_by_operator": operator_review[
                "contract_execution_reviewed_by_operator"
            ],
            "contract_not_executed": signature_readiness["contract_executed"] is False,
            "invoice_not_created": operator_review["invoice_creation_approved"]
            is False,
            "payment_not_requested": operator_review["payment_request_approved"]
            is False,
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
        agreement_review: dict[str, Any],
        contract_document_review: dict[str, Any],
        signature_readiness: dict[str, Any],
        operator_review: dict[str, Any],
        review_blockers: list[str],
    ) -> str:
        if agreement_review.get("review_status") == "blocked":
            return "blocked"

        if agreement_review.get("review_status") != "ready_for_agreement_execution_review":
            return "pending_agreement_review"

        if contract_document_review["contract_document_ready"] is not True:
            return "pending_contract_document_review"

        if signature_readiness["signature_readiness_confirmed"] is not True:
            return "pending_signature_readiness"

        if operator_review["contract_execution_reviewed_by_operator"] is not True:
            return "pending_operator_review"

        if review_blockers:
            return "pending_contract_execution_review"

        return "ready_for_contract_execution"

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
            "contract_execution_ready": review_status == "ready_for_contract_execution",
            "contract_created": False,
            "contract_executed": False,
            "invoice_created": False,
            "payment_requested": False,
            "paid_assessment_authorized": False,
            "production_onboarding_authorized": False,
            "requires_actual_contract_execution": True,
            "requires_separate_invoice": True,
            "requires_separate_payment_confirmation": True,
            "requires_final_paid_work_authorization": True,
        }

    def _evidence_boundary(self) -> dict[str, Any]:
        return {
            "allowed_evidence": [
                "operator_scope_call_notes",
                "buyer_approved_scope_call_summary",
                "redacted_operational_examples",
                "non_sensitive_workflow_context",
                "operator_approved_assessment_scope",
                "agreement_review_notes",
                "contract_review_notes",
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
            "contract_execution_review_is_not_execution": True,
        }

    def _boundary_notices(self) -> list[str]:
        return [
            "contract_execution_review_does_not_execute_contract",
            "contract_execution_review_does_not_create_invoice",
            "contract_execution_review_does_not_request_payment",
            "contract_execution_review_does_not_authorize_paid_work",
            "contract_execution_review_does_not_start_production_onboarding",
            "contract_execution_review_requires_human_operator",
        ]

    def _audit_notes(self, review_status: str) -> list[str]:
        notes = [
            "contract_execution_review_built",
            "contract_execution_review_is_not_contract_execution",
            "invoice_not_created",
            "payment_not_requested",
            "paid_assessment_not_authorized",
            "production_onboarding_not_started",
        ]

        if review_status == "ready_for_contract_execution":
            notes.append("contract_execution_review_ready")
        elif review_status == "pending_agreement_review":
            notes.append("contract_execution_review_pending_agreement_review")
        elif review_status == "pending_contract_document_review":
            notes.append("contract_execution_review_pending_document_review")
        elif review_status == "pending_signature_readiness":
            notes.append("contract_execution_review_pending_signature_readiness")
        elif review_status == "pending_operator_review":
            notes.append("contract_execution_review_pending_operator_review")
        elif review_status == "pending_contract_execution_review":
            notes.append("contract_execution_review_pending_review")
        else:
            notes.append("contract_execution_review_blocked")

        return notes

    def _next_action(self, review_status: str) -> dict[str, str]:
        if review_status == "ready_for_contract_execution":
            return {
                "action": "prepare_contract_execution_event",
                "operator_instruction": (
                    "Prepare contract execution event. Do not create an invoice, "
                    "request payment, authorize paid work, or start production "
                    "onboarding from this review."
                ),
                "future_action": "build_contract_execution_event",
            }

        if review_status == "pending_agreement_review":
            return {
                "action": "complete_paid_assessment_agreement_review",
                "operator_instruction": (
                    "Complete paid assessment agreement review before contract "
                    "execution review can become ready."
                ),
                "future_action": "rerun_contract_execution_review",
            }

        if review_status == "pending_contract_document_review":
            return {
                "action": "complete_contract_document_review",
                "operator_instruction": (
                    "Prepare and review the contract document, legal language, "
                    "and scope alignment before moving forward."
                ),
                "future_action": "rerun_contract_execution_review",
            }

        if review_status == "pending_signature_readiness":
            return {
                "action": "confirm_signature_readiness",
                "operator_instruction": (
                    "Confirm buyer signature readiness, provider signature "
                    "readiness, and signature method before moving forward."
                ),
                "future_action": "rerun_contract_execution_review",
            }

        if review_status == "pending_operator_review":
            return {
                "action": "complete_operator_contract_execution_review",
                "operator_instruction": (
                    "A human operator must complete contract execution review "
                    "before moving forward."
                ),
                "future_action": "rerun_contract_execution_review",
            }

        return {
            "action": "resolve_contract_execution_review_gaps",
            "operator_instruction": (
                "Resolve contract execution review blockers before moving forward."
            ),
            "future_action": "rerun_contract_execution_review",
        }

    def _operator_message(self, review_status: str) -> str:
        if review_status == "ready_for_contract_execution":
            return (
                "Contract execution review is ready for contract execution event. "
                "Invoice creation, payment request, paid work authorization, and "
                "production onboarding remain blocked."
            )

        if review_status == "pending_agreement_review":
            return (
                "Contract execution review is pending because paid assessment "
                "agreement review is not ready."
            )

        if review_status == "pending_contract_document_review":
            return "Contract execution review is pending contract document review."

        if review_status == "pending_signature_readiness":
            return "Contract execution review is pending signature readiness."

        if review_status == "pending_operator_review":
            return "Contract execution review is pending operator review."

        if review_status == "pending_contract_execution_review":
            return "Contract execution review has unresolved review blockers."

        return (
            "Contract execution review is blocked. Resolve the listed blockers "
            "before moving forward."
        )

    def _recommended_action(self, review_status: str) -> str:
        if review_status == "ready_for_contract_execution":
            return "prepare_contract_execution_event"

        return "resolve_contract_execution_review_gaps"