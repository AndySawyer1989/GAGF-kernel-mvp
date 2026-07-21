# Assessment Factory Lite Payment Request Event

## Release

Release:

assessment-factory-lite-scope-call-conversion

Version:

2.3.0

Story:

US-316 — Assessment Factory Lite Payment Request Event Documentation

## Purpose

The Assessment Factory Lite Payment Request Event is a governed commercial event record.

It is created after the Payment Request Review is ready.

It records that payment was requested from the buyer.

It records payment request reference, requested timestamp, requested amount, delivery evidence, and human operator confirmation.

It may record that payment has been requested.

It does not confirm payment.

It does not authorize paid assessment work.

It does not start production onboarding.

It preserves the boundary between payment request delivery and downstream payment confirmation or work authorization.

## Endpoint

POST /products/assessment-factory-lite/payment-request-event

## Service

AssessmentFactoryLitePaymentRequestEventService

Service file:

backend/app/gagf/assessment_factory_lite_payment_request_event_service.py

Endpoint file:

backend/app/main.py

## Event Type

assessment_factory_lite_payment_request_event

## Event Stage

payment_request_event

## Output Release

The event uses the scope-call conversion contract:

release: assessment-factory-lite-scope-call-conversion
version: 2.3.0

The event preserves the current system release marker:

version: 2.3.0
release: assessment-factory-lite-scope-call-conversion
sprint: 5.0
status: complete

## Source Object

The event is built from a Payment Request Review.

Expected source object:

assessment_factory_lite_payment_request_review

Expected source review stage:

payment_request_review

Expected source review status:

ready_for_payment_request

Expected source recommended action:

prepare_payment_request_event

If the source payment request review is not ready_for_payment_request, the payment request event cannot become payment_requested.

## Supported Inputs

The service accepts either a source payment_request_review directly or enough upstream context to build one.

Supported input keys include:

payment_request_review
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
payment_request_event_context

## Payment Request Event Context

The payment_request_event_context provides event identity, payment request record, delivery record, and human operator confirmation metadata.

Supported fields include:

payment_request_event_id
recorded_at
payment_requested
payment_request_reference
payment_requested_at
requested_amount
payment_request_delivered_to_buyer
delivery_channel
delivery_reference
human_operator_confirmed_payment_request
operator_name
operator_notes

Default payment_request_event_id:

payment-request-event-draft-001

Default recorded_at:

not_recorded

## Core Output Fields

The payment request event returns:

status
event_type
package_name
release
version
event_stage
event_status
payment_request_event_id
recorded_at
source_payment_request_review
payment_request_record
delivery_record
operator_confirmation
event_checklist
event_blockers
event_score
payment_request_details
buyer_notice_readiness
invoice_record
delivery_source_record
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

## Event Statuses

The service supports seven event statuses.

payment_requested:

The payment request review is ready, payment request is confirmed, payment request reference is recorded, requested timestamp is recorded, requested amount is recorded, delivery to buyer is recorded, human operator confirmation exists, and all event checklist boundaries pass.

pending_payment_request_review:

The source payment request review is not ready_for_payment_request.

pending_payment_request_confirmation:

The source review is ready, but payment request confirmation is missing.

pending_payment_request_record:

The source review is ready and payment request is confirmed, but payment request reference, payment_requested_at timestamp, or requested amount is missing.

pending_payment_request_delivery:

The source review is ready, payment request record exists, but buyer delivery status, delivery channel, or delivery reference is missing.

pending_operator_confirmation:

The source review is ready, payment request record exists, delivery record exists, but human operator confirmation is missing.

pending_payment_request_event_review:

The event has remaining deterministic blockers after the main readiness categories pass.

blocked:

The source payment request review is blocked or another deterministic event boundary failed.

## Payment Requested Conditions

The event becomes payment_requested when:

payment_request_review_ready is true
payment_requested is true
payment_request_reference_recorded is true
payment_requested_at_recorded is true
requested_amount_recorded is true
payment_request_record_is_not_payment_confirmation is true
payment_request_record_is_not_paid_work_authorization is true
payment_request_delivered_to_buyer is true
delivery_channel_recorded is true
delivery_reference_recorded is true
payment_request_delivery_is_not_payment_confirmation is true
payment_request_delivery_is_not_paid_work_authorization is true
human_operator_confirmed_payment_request is true
payment_not_confirmed is true
paid_assessment_not_authorized is true
production_onboarding_not_started is true

## Pending Payment Request Review Conditions

The event becomes pending_payment_request_review when:

source payment request review is not ready
source payment request review is pending_invoice_creation_event
source payment request review is pending_payment_request_details_review
source payment request review is pending_buyer_notice_readiness
source payment request review is pending_operator_review
source payment request review is pending_payment_request_review

## Pending Payment Request Confirmation Conditions

The event becomes pending_payment_request_confirmation when:

payment_requested is false
payment request has not been confirmed
payment request evidence has not been accepted by the human operator

## Pending Payment Request Record Conditions

The event becomes pending_payment_request_record when:

payment_request_reference_recorded is false
payment_requested_at_recorded is false
requested_amount_recorded is false
payment request reference is missing
payment_requested_at timestamp is missing
requested amount is missing

## Pending Payment Request Delivery Conditions

The event becomes pending_payment_request_delivery when:

payment_request_delivered_to_buyer is false
delivery_channel_recorded is false
delivery_reference_recorded is false
buyer delivery status is missing
delivery channel is missing
delivery reference is missing

## Pending Operator Confirmation Conditions

The event becomes pending_operator_confirmation when:

human_operator_confirmed_payment_request is false
human operator confirmation is missing
operator confirmation has not been recorded

## Blocked Conditions

The event becomes blocked when:

source payment request review is blocked
upstream proposal export is invalid
payment request event cannot be classified as pending review
deterministic event checklist contains unresolved blockers

## Source Payment Request Review Summary

The source_payment_request_review object includes:

event_type
review_stage
review_status
release
version
payment_request_review_id
prepared_at
recommended_action

This preserves traceability without copying the full payment request review artifact.

## Payment Request Record

The payment_request_record object includes:

payment_requested
payment_request_reference
payment_requested_at
requested_amount
payment_request_reference_recorded
payment_requested_at_recorded
requested_amount_recorded
payment_request_record_is_not_payment_confirmation
payment_request_record_is_not_paid_work_authorization

Required boundary values:

payment_request_record_is_not_payment_confirmation: true
payment_request_record_is_not_paid_work_authorization: true

The payment request record records payment request delivery only.

It is not payment confirmation.

It is not paid-work authorization.

## Delivery Record

The delivery_record object includes:

payment_request_delivered_to_buyer
delivery_channel
delivery_reference
delivery_channel_recorded
delivery_reference_recorded
payment_request_delivery_is_not_payment_confirmation
payment_request_delivery_is_not_paid_work_authorization

Required boundary values:

payment_request_delivery_is_not_payment_confirmation: true
payment_request_delivery_is_not_paid_work_authorization: true

Payment request delivery is not payment confirmation.

Payment request delivery is not paid-work authorization.

## Operator Confirmation

The operator_confirmation object includes:

human_operator_required
human_operator_confirmed_payment_request
operator_name
operator_notes
payment_confirmed
paid_assessment_authorized
production_onboarding_approved

Required boundary values:

human_operator_required: true
payment_confirmed: false
paid_assessment_authorized: false
production_onboarding_approved: false

Operator confirmation records payment request delivery only.

It does not confirm payment.

It does not authorize paid assessment work.

It does not start production onboarding.

## Event Checklist

The event_checklist includes:

payment_request_review_ready
payment_requested
payment_request_reference_recorded
payment_requested_at_recorded
requested_amount_recorded
payment_request_record_is_not_payment_confirmation
payment_request_record_is_not_paid_work_authorization
payment_request_delivered_to_buyer
delivery_channel_recorded
delivery_reference_recorded
payment_request_delivery_is_not_payment_confirmation
payment_request_delivery_is_not_paid_work_authorization
human_operator_confirmed_payment_request
payment_not_confirmed
paid_assessment_not_authorized
production_onboarding_not_started

## Event Blockers

The event_blockers list contains any event checklist item that is not true.

Common blockers include:

payment_request_review_ready
payment_requested
payment_request_reference_recorded
payment_requested_at_recorded
requested_amount_recorded
payment_request_delivered_to_buyer
delivery_channel_recorded
delivery_reference_recorded
human_operator_confirmed_payment_request
payment_not_confirmed
paid_assessment_not_authorized
production_onboarding_not_started

## Event Score

The event_score object includes:

passed
total
score
ready

For a completed payment request event:

passed: 16
total: 16
score: 1.0
ready: true

The event score is advisory evidence for the operator, but deterministic event_status remains authoritative.

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

payment_request_recorded
payment_requested
payment_confirmed
paid_assessment_authorized
production_onboarding_authorized
requires_separate_payment_confirmation
requires_final_paid_work_authorization
requires_separate_production_onboarding

Required values after payment request event recording:

payment_request_recorded: true
payment_requested: true
payment_confirmed: false
paid_assessment_authorized: false
production_onboarding_authorized: false
requires_separate_payment_confirmation: true
requires_final_paid_work_authorization: true
requires_separate_production_onboarding: true

## Evidence Boundary

Allowed evidence examples include:

invoice_reference
invoice_delivery_reference
payment_request_review_notes
buyer_notice_notes
payment_request_reference
payment_request_delivery_reference
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
payment_request_event_is_not_payment_confirmation
payment_request_event_is_not_paid_work_authorization

Required values:

deterministic_status_required: true
gagf_kernel_authoritative: true
ai_override_allowed: false
human_boundary_required: true
release_marker_preserved: true
payment_request_event_is_not_payment_confirmation: true
payment_request_event_is_not_paid_work_authorization: true

## Boundary Notices

The event emits these boundary notices:

payment_request_event_records_payment_request_only
payment_request_event_does_not_confirm_payment
payment_request_event_does_not_authorize_paid_work
payment_request_event_does_not_start_production_onboarding
payment_request_event_requires_human_operator

## Audit Notes

All event statuses include:

payment_request_event_built
payment_not_confirmed
paid_assessment_not_authorized
production_onboarding_not_started

When payment_requested, audit notes include:

payment_request_event_recorded

When pending_payment_request_review, audit notes include:

payment_request_event_pending_review

When pending_payment_request_confirmation, audit notes include:

payment_request_event_pending_request_confirmation

When pending_payment_request_record, audit notes include:

payment_request_event_pending_request_record

When pending_payment_request_delivery, audit notes include:

payment_request_event_pending_delivery

When pending_operator_confirmation, audit notes include:

payment_request_event_pending_operator_confirmation

When pending_payment_request_event_review, audit notes include:

payment_request_event_pending_event_review

When blocked, audit notes include:

payment_request_event_blocked

## Next Action

When payment_requested:

action: prepare_payment_confirmation_review
future_action: build_payment_confirmation_review

When pending_payment_request_review:

action: complete_payment_request_review
future_action: rerun_payment_request_event

When pending_payment_request_confirmation:

action: confirm_payment_request
future_action: rerun_payment_request_event

When pending_payment_request_record:

action: record_payment_request_reference
future_action: rerun_payment_request_event

When pending_payment_request_delivery:

action: record_payment_request_delivery
future_action: rerun_payment_request_event

When pending_operator_confirmation:

action: confirm_operator_payment_request_event
future_action: rerun_payment_request_event

When pending_payment_request_event_review or blocked:

action: resolve_payment_request_event_gaps
future_action: rerun_payment_request_event

## Recommended Action

When payment_requested:

prepare_payment_confirmation_review

When not ready:

resolve_payment_request_event_gaps

## Human Operator Boundary

The event requires a human operator.

The event may record that payment was requested.

The event does not confirm payment.

The event does not authorize paid assessment work.

The event does not start production onboarding.

## Payment Request Boundary

The payment request event records payment request only.

The payment request event is not payment confirmation.

The payment request event is not authorization to begin paid work.

A separate payment confirmation review, payment confirmation event, final paid-work authorization, and production onboarding gate must occur after this event.

## GAGF Meaning

The event represents the GAGF pattern:

Payment Request Readiness → Payment Request Record → Buyer Delivery → Human Confirmation → Boundary Preservation → Governed Next Action

The object is not a generic payment-stage update.

It is a deterministic governance checkpoint for recording payment request delivery without overclaiming downstream payment confirmation or work authority.

It proves the system can request payment while preserving payment confirmation, paid-work authorization, and onboarding boundaries.

## Product Meaning

This event moves Assessment Factory Lite from payment-request readiness into recorded payment request delivery.

It is the first object in the workflow that may confirm an actual payment request was sent to the buyer.

It keeps the product commercially useful while preserving evidence, commercial, scheduling, and governance boundaries.

## Next Story

US-317 — Assessment Factory Lite Payment Request Event Release Marker
