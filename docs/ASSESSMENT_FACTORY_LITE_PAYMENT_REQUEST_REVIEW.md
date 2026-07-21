# Assessment Factory Lite Payment Request Review

## Release

Release:

assessment-factory-lite-scope-call-conversion

Version:

2.3.0

Story:

US-312 — Assessment Factory Lite Payment Request Review Documentation

## Purpose

The Assessment Factory Lite Payment Request Review is a governed payment-request-readiness object.

It is created after the Invoice Creation Event is recorded.

It reviews whether payment request details, buyer notice readiness, and operator review are complete before moving toward the payment request event.

It does not request payment.

It does not confirm payment.

It does not authorize paid assessment work.

It does not start production onboarding.

It preserves the boundary between payment-request readiness and actual payment request delivery.

## Endpoint

POST /products/assessment-factory-lite/payment-request-review

## Service

AssessmentFactoryLitePaymentRequestReviewService

Service file:

backend/app/gagf/assessment_factory_lite_payment_request_review_service.py

Endpoint file:

backend/app/main.py

## Event Type

assessment_factory_lite_payment_request_review

## Review Stage

payment_request_review

## Output Release

The review uses the scope-call conversion contract:

release: assessment-factory-lite-scope-call-conversion
version: 2.3.0

The review preserves the current system release marker:

version: 2.3.0
release: assessment-factory-lite-scope-call-conversion
sprint: 5.0
status: complete

## Source Object

The review is built from an Invoice Creation Event.

Expected source object:

assessment_factory_lite_invoice_creation_event

Expected source event stage:

invoice_creation_event

Expected source event status:

invoice_created

Expected source recommended action:

prepare_payment_request_review

If the source invoice creation event is not invoice_created, the payment request review cannot become ready_for_payment_request.

## Supported Inputs

The service accepts either a source invoice_creation_event directly or enough upstream context to build one.

Supported input keys include:

invoice_creation_event
invoice_creation_review
contract_execution_event
contract_execution_review
paid_assessment_agreement_review
paid_assessment_authorization_package
scope_call_event_record
scope_call_event_package
scope_call_agenda_message_event_record
scope_call_agenda_message
scope_call_package
follow_up_event_record
follow_up_message
tracker
event_record
message
delivery_package
export_package
export
document
proposal
offer
buyer_context
operator_approval
message_context
event_context
follow_up_context
follow_up_message_context
follow_up_event_context
scope_call_context
scope_call_message_context
scope_call_message_event_context
scope_call_event_context
scope_call_record_context
authorization_context
agreement_context
contract_context
contract_execution_context
invoice_context
invoice_creation_context
payment_request_context

## Payment Request Context

The payment_request_context provides payment request review identity, payment request detail review, buyer notice readiness, and operator review metadata.

Supported fields include:

payment_request_review_id
prepared_at
payment_amount_confirmed
invoice_reference_confirmed
payment_due_date_confirmed
payment_request_language_reviewed
buyer_notice_prepared
buyer_notice_channel_confirmed
payment_instructions_included
payment_request_reviewed_by_operator
operator_review_status

Default payment_request_review_id:

payment-request-review-draft-001

Default prepared_at:

not_recorded

## Core Output Fields

The payment request review returns:

status
event_type
package_name
release
version
review_stage
review_status
payment_request_review_id
prepared_at
source_invoice_creation_event
payment_request_details
buyer_notice_readiness
operator_review
review_checklist
review_blockers
review_score
invoice_record
delivery_record
invoice_details_review
billing_readiness
execution_evidence
signature_record
contract_document_review
agreement_terms
buyer_request
commercial_review
evidence_review
human_authorization
scheduling_boundary
commercial_boundary
evidence_boundary
governance_boundary
boundary_notices
audit_notes
next_action
operator_message
recommended_action

## Review Statuses

The service supports six review statuses.

ready_for_payment_request:

The invoice creation event is recorded, payment request details are ready, buyer notice readiness is complete, operator payment request review exists, and all review checklist boundaries pass.

pending_invoice_creation_event:

The source invoice creation event is not invoice_created.

pending_payment_request_details_review:

The invoice creation event is recorded, but payment amount, invoice reference, payment due date, or payment request language review is incomplete.

pending_buyer_notice_readiness:

The invoice creation event and payment request details are ready, but buyer notice, notice channel, or payment instructions are incomplete.

pending_operator_review:

The invoice creation event, payment request details, and buyer notice readiness are complete, but operator payment request review is missing.

pending_payment_request_review:

The review has remaining deterministic blockers after the main readiness categories pass.

blocked:

The source invoice creation event is blocked or another deterministic review boundary failed.

## Ready Conditions

The review becomes ready_for_payment_request when:

invoice_creation_event_recorded is true
payment_request_details_ready is true
buyer_notice_ready is true
buyer_notice_is_not_payment_confirmation is true
buyer_notice_is_not_paid_work_authorization is true
payment_request_reviewed_by_operator is true
payment_not_requested is true
payment_not_confirmed is true
paid_assessment_not_authorized is true
production_onboarding_not_started is true

## Pending Invoice Creation Event Conditions

The review becomes pending_invoice_creation_event when:

source invoice creation event is not recorded
source invoice creation event is pending_invoice_creation_review
source invoice creation event is pending_invoice_creation_confirmation
source invoice creation event is pending_invoice_record
source invoice creation event is pending_invoice_delivery
source invoice creation event is pending_operator_confirmation
source invoice creation event is pending_invoice_creation_event_review

## Pending Payment Request Details Review Conditions

The review becomes pending_payment_request_details_review when:

payment_amount_confirmed is false
invoice_reference_confirmed is false
payment_due_date_confirmed is false
payment_request_language_reviewed is false
payment_request_details_ready is false

## Pending Buyer Notice Readiness Conditions

The review becomes pending_buyer_notice_readiness when:

buyer_notice_prepared is false
buyer_notice_channel_confirmed is false
payment_instructions_included is false
buyer_notice_ready is false

## Pending Operator Review Conditions

The review becomes pending_operator_review when:

payment_request_reviewed_by_operator is false
operator_review_status is payment_request_review_required
human operator payment request review is missing

## Blocked Conditions

The review becomes blocked when:

source invoice creation event is blocked
upstream proposal export is invalid
payment request review cannot be classified as pending review
deterministic review checklist contains unresolved blockers

## Source Invoice Creation Event Summary

The source_invoice_creation_event object includes:

event_type
event_stage
event_status
release
version
invoice_creation_event_id
recorded_at
recommended_action

This preserves traceability without copying the full invoice creation event artifact.

## Payment Request Details

The payment_request_details object includes:

payment_amount_confirmed
invoice_reference_confirmed
payment_due_date_confirmed
payment_request_language_reviewed
payment_request_details_ready
payment_request_required_before_payment_confirmation
payment_confirmation_required_before_paid_work

Required boundary values:

payment_request_required_before_payment_confirmation: true
payment_confirmation_required_before_paid_work: true

Payment request details readiness does not request payment.

Payment request details readiness does not confirm payment.

Payment request details readiness does not authorize paid work.

## Buyer Notice Readiness

The buyer_notice_readiness object includes:

buyer_notice_prepared
buyer_notice_channel_confirmed
payment_instructions_included
buyer_notice_ready
buyer_notice_is_not_payment_confirmation
buyer_notice_is_not_paid_work_authorization

Required boundary values:

buyer_notice_is_not_payment_confirmation: true
buyer_notice_is_not_paid_work_authorization: true

Buyer notice readiness is not payment confirmation.

Buyer notice readiness is not paid-work authorization.

## Operator Review

The operator_review object includes:

human_operator_required
payment_request_reviewed_by_operator
operator_review_status
payment_requested
payment_confirmed
paid_assessment_authorized
production_onboarding_approved

Required boundary values:

human_operator_required: true
payment_requested: false
payment_confirmed: false
paid_assessment_authorized: false
production_onboarding_approved: false

Operator review approves payment request readiness only.

It does not request payment.

It does not confirm payment.

It does not authorize paid assessment work.

It does not start production onboarding.

## Review Checklist

The review_checklist includes:

invoice_creation_event_recorded
payment_request_details_ready
buyer_notice_ready
buyer_notice_is_not_payment_confirmation
buyer_notice_is_not_paid_work_authorization
payment_request_reviewed_by_operator
payment_not_requested
payment_not_confirmed
paid_assessment_not_authorized
production_onboarding_not_started

## Review Blockers

The review_blockers list contains any review checklist item that is not true.

Common blockers include:

invoice_creation_event_recorded
payment_request_details_ready
buyer_notice_ready
payment_request_reviewed_by_operator
payment_not_requested
payment_not_confirmed
paid_assessment_not_authorized
production_onboarding_not_started

## Review Score

The review_score object includes:

passed
total
score
ready

For a ready review:

passed: 10
total: 10
score: 1.0
ready: true

The review score is advisory evidence for the operator, but deterministic review_status remains authoritative.

## Scheduling Boundary

The scheduling_boundary object includes:

scope_call_scheduled_by_system
calendar_invite_created
automatic_scheduling_allowed
manual_scheduling_required
scheduling_authority

Required values:

scope_call_scheduled_by_system: false
calendar_invite_created: false
automatic_scheduling_allowed: false
manual_scheduling_required: true
scheduling_authority: human_operator

## Commercial Boundary

The commercial_boundary object includes:

payment_request_ready
payment_requested
payment_confirmed
paid_assessment_authorized
production_onboarding_authorized
requires_actual_payment_request
requires_separate_payment_confirmation
requires_final_paid_work_authorization
requires_separate_production_onboarding

Required values:

payment_request_ready: true
payment_requested: false
payment_confirmed: false
paid_assessment_authorized: false
production_onboarding_authorized: false
requires_actual_payment_request: true
requires_separate_payment_confirmation: true
requires_final_paid_work_authorization: true
requires_separate_production_onboarding: true

## Evidence Boundary

Allowed evidence examples include:

invoice_reference
invoice_delivery_reference
invoice_review_notes
billing_readiness_notes
payment_request_review_notes
buyer_notice_notes
non_sensitive_workflow_context

Excluded evidence examples include:

regulated_production_data
secrets
credentials
unapproved_personal_data
unapproved_customer_records

Production data requires separate approval.

## Governance Boundary

The governance_boundary object includes:

deterministic_status_required
gagf_kernel_authoritative
ai_override_allowed
human_boundary_required
release_marker_preserved
payment_request_review_is_not_payment_request
payment_request_review_is_not_payment_confirmation
payment_request_review_is_not_paid_work_authorization

Required values:

deterministic_status_required: true
gagf_kernel_authoritative: true
ai_override_allowed: false
human_boundary_required: true
release_marker_preserved: true
payment_request_review_is_not_payment_request: true
payment_request_review_is_not_payment_confirmation: true
payment_request_review_is_not_paid_work_authorization: true

## Boundary Notices

The review emits these boundary notices:

payment_request_review_does_not_request_payment
payment_request_review_does_not_confirm_payment
payment_request_review_does_not_authorize_paid_work
payment_request_review_does_not_start_production_onboarding
payment_request_review_requires_human_operator

## Audit Notes

All review statuses include:

payment_request_review_built
payment_not_requested
payment_not_confirmed
paid_assessment_not_authorized
production_onboarding_not_started

When ready_for_payment_request, audit notes include:

payment_request_review_ready

When pending_invoice_creation_event, audit notes include:

payment_request_review_pending_invoice_creation_event

When pending_payment_request_details_review, audit notes include:

payment_request_review_pending_payment_request_details

When pending_buyer_notice_readiness, audit notes include:

payment_request_review_pending_buyer_notice_readiness

When pending_operator_review, audit notes include:

payment_request_review_pending_operator_review

When pending_payment_request_review, audit notes include:

payment_request_review_pending_review

When blocked, audit notes include:

payment_request_review_blocked

## Next Action

When ready_for_payment_request:

action: prepare_payment_request_event
future_action: build_payment_request_event

When pending_invoice_creation_event:

action: complete_invoice_creation_event
future_action: rerun_payment_request_review

When pending_payment_request_details_review:

action: complete_payment_request_details_review
future_action: rerun_payment_request_review

When pending_buyer_notice_readiness:

action: confirm_buyer_notice_readiness
future_action: rerun_payment_request_review

When pending_operator_review:

action: complete_operator_payment_request_review
future_action: rerun_payment_request_review

When pending_payment_request_review or blocked:

action: resolve_payment_request_review_gaps
future_action: rerun_payment_request_review

## Recommended Action

When ready_for_payment_request:

prepare_payment_request_event

When not ready:

resolve_payment_request_review_gaps

## Human Operator Boundary

The review requires a human operator.

The review may become ready for payment request event preparation.

The review does not request payment.

The review does not confirm payment.

The review does not authorize paid assessment work.

The review does not start production onboarding.

## Payment Request Boundary

The payment request review is not the payment request.

The payment request review is not payment confirmation.

The payment request review is not authorization to begin paid work.

A separate payment request event must occur before payment confirmation, final paid-work authorization, and production onboarding gates.

## GAGF Meaning

The review represents the GAGF pattern:

Invoice Creation Evidence → Payment Request Detail Review → Buyer Notice Readiness → Human Review → Boundary Preservation → Governed Next Action

The object is not a generic collections-stage update.

It is a deterministic governance checkpoint for payment-request readiness.

It proves the system can move toward requesting payment without collapsing payment request, payment confirmation, paid-work authorization, and onboarding into one unsafe step.

## Product Meaning

This review moves Assessment Factory Lite from recorded invoice creation into payment-request readiness.

It is the final review layer before the payment request event.

It keeps the product commercially useful while preserving evidence, commercial, scheduling, and governance boundaries.

## Next Story

US-313 — Assessment Factory Lite Payment Request Review Release Marker
