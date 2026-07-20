# Assessment Factory Lite Invoice Creation Event

## Release

Release:

assessment-factory-lite-scope-call-conversion

Version:

2.3.0

Story:

US-308 — Assessment Factory Lite Invoice Creation Event Documentation

## Purpose

The Assessment Factory Lite Invoice Creation Event is a governed commercial event record.

It is created after the Invoice Creation Review is ready.

It records that invoice creation occurred.

It records invoice reference, invoice timestamp, invoice amount, delivery evidence, and human operator confirmation.

It may record that an invoice has been created.

It does not request payment.

It does not confirm payment.

It does not authorize paid assessment work.

It does not start production onboarding.

It preserves the boundary between invoice creation and downstream payment or work authorization actions.

## Endpoint

POST /products/assessment-factory-lite/invoice-creation-event

## Service

AssessmentFactoryLiteInvoiceCreationEventService

Service file:

backend/app/gagf/assessment_factory_lite_invoice_creation_event_service.py

Endpoint file:

backend/app/main.py

## Event Type

assessment_factory_lite_invoice_creation_event

## Event Stage

invoice_creation_event

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

The event is built from an Invoice Creation Review.

Expected source object:

assessment_factory_lite_invoice_creation_review

Expected source review stage:

invoice_creation_review

Expected source review status:

ready_for_invoice_creation

Expected source recommended action:

prepare_invoice_creation_event

If the source invoice creation review is not ready_for_invoice_creation, the invoice creation event cannot become invoice_created.

## Supported Inputs

The service accepts either a source invoice_creation_review directly or enough upstream context to build one.

Supported input keys include:

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

## Invoice Creation Context

The invoice_creation_context provides event identity, invoice record, delivery record, and human operator confirmation metadata.

Supported fields include:

invoice_creation_event_id
recorded_at
invoice_created
invoice_reference
invoice_created_at
invoice_amount
invoice_delivered_to_buyer
delivery_channel
delivery_reference
human_operator_confirmed_invoice_creation
operator_name
operator_notes

Default invoice_creation_event_id:

invoice-creation-event-draft-001

Default recorded_at:

not_recorded

## Core Output Fields

The invoice creation event returns:

status
event_type
package_name
release
version
event_stage
event_status
invoice_creation_event_id
recorded_at
source_invoice_creation_review
invoice_record
delivery_record
operator_confirmation
event_checklist
event_blockers
event_score
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

The service supports eight event statuses.

invoice_created:

The invoice creation review is ready, invoice creation is confirmed, invoice reference is recorded, invoice created_at is recorded, invoice amount is recorded, invoice delivery is recorded, human operator confirmation exists, and all event checklist boundaries pass.

pending_invoice_creation_review:

The source invoice creation review is not ready_for_invoice_creation.

pending_invoice_creation_confirmation:

The source review is ready, but invoice creation confirmation is missing.

pending_invoice_record:

The source review is ready and invoice creation is confirmed, but invoice reference, invoice_created_at, or invoice amount is missing.

pending_invoice_delivery:

The source review is ready, invoice record exists, but buyer delivery status, delivery channel, or delivery reference is missing.

pending_operator_confirmation:

The source review is ready, invoice record exists, delivery record exists, but human operator confirmation is missing.

pending_invoice_creation_event_review:

The event has remaining deterministic blockers after the main readiness categories pass.

blocked:

The source invoice creation review is blocked or another deterministic event boundary failed.

## Invoice Created Conditions

The event becomes invoice_created when:

invoice_creation_review_ready is true
invoice_created is true
invoice_reference_recorded is true
invoice_created_at_recorded is true
invoice_amount_recorded is true
invoice_record_is_not_payment_request is true
invoice_record_is_not_payment_confirmation is true
invoice_record_is_not_paid_work_authorization is true
invoice_delivered_to_buyer is true
delivery_channel_recorded is true
delivery_reference_recorded is true
invoice_delivery_is_not_payment_request is true
human_operator_confirmed_invoice_creation is true
payment_not_requested is true
payment_not_confirmed is true
paid_assessment_not_authorized is true
production_onboarding_not_started is true

## Pending Invoice Creation Review Conditions

The event becomes pending_invoice_creation_review when:

source invoice creation review is not ready
source invoice creation review is pending_contract_execution_event
source invoice creation review is pending_invoice_details_review
source invoice creation review is pending_billing_readiness
source invoice creation review is pending_operator_review
source invoice creation review is pending_invoice_creation_review

## Pending Invoice Creation Confirmation Conditions

The event becomes pending_invoice_creation_confirmation when:

invoice_created is false
invoice creation has not been confirmed
invoice creation evidence has not been accepted by the human operator

## Pending Invoice Record Conditions

The event becomes pending_invoice_record when:

invoice_reference_recorded is false
invoice_created_at_recorded is false
invoice_amount_recorded is false
invoice reference is missing
invoice_created_at timestamp is missing
invoice amount is missing

## Pending Invoice Delivery Conditions

The event becomes pending_invoice_delivery when:

invoice_delivered_to_buyer is false
delivery_channel_recorded is false
delivery_reference_recorded is false
buyer delivery status is missing
delivery channel is missing
delivery reference is missing

## Pending Operator Confirmation Conditions

The event becomes pending_operator_confirmation when:

human_operator_confirmed_invoice_creation is false
human operator confirmation is missing
operator confirmation has not been recorded

## Blocked Conditions

The event becomes blocked when:

source invoice creation review is blocked
upstream proposal export is invalid
invoice creation event cannot be classified as pending review
deterministic event checklist contains unresolved blockers

## Source Invoice Creation Review Summary

The source_invoice_creation_review object includes:

event_type
review_stage
review_status
release
version
invoice_review_id
prepared_at
recommended_action

This preserves traceability without copying the full invoice creation review artifact.

## Invoice Record

The invoice_record object includes:

invoice_created
invoice_reference
invoice_created_at
invoice_amount
invoice_reference_recorded
invoice_created_at_recorded
invoice_amount_recorded
invoice_record_is_not_payment_request
invoice_record_is_not_payment_confirmation
invoice_record_is_not_paid_work_authorization

Required boundary values:

invoice_record_is_not_payment_request: true
invoice_record_is_not_payment_confirmation: true
invoice_record_is_not_paid_work_authorization: true

The invoice record records invoice creation only.

It is not a payment request.

It is not payment confirmation.

It is not paid-work authorization.

## Delivery Record

The delivery_record object includes:

invoice_delivered_to_buyer
delivery_channel
delivery_reference
delivery_channel_recorded
delivery_reference_recorded
invoice_delivery_is_not_payment_request

Required boundary value:

invoice_delivery_is_not_payment_request: true

Invoice delivery is not a payment request.

Invoice delivery is not payment confirmation.

Invoice delivery is not paid-work authorization.

## Operator Confirmation

The operator_confirmation object includes:

human_operator_required
human_operator_confirmed_invoice_creation
operator_name
operator_notes
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

Operator confirmation records invoice creation only.

It does not request payment.

It does not confirm payment.

It does not authorize paid assessment work.

It does not start production onboarding.

## Event Checklist

The event_checklist includes:

invoice_creation_review_ready
invoice_created
invoice_reference_recorded
invoice_created_at_recorded
invoice_amount_recorded
invoice_record_is_not_payment_request
invoice_record_is_not_payment_confirmation
invoice_record_is_not_paid_work_authorization
invoice_delivered_to_buyer
delivery_channel_recorded
delivery_reference_recorded
invoice_delivery_is_not_payment_request
human_operator_confirmed_invoice_creation
payment_not_requested
payment_not_confirmed
paid_assessment_not_authorized
production_onboarding_not_started

## Event Blockers

The event_blockers list contains any event checklist item that is not true.

Common blockers include:

invoice_creation_review_ready
invoice_created
invoice_reference_recorded
invoice_created_at_recorded
invoice_amount_recorded
invoice_delivered_to_buyer
delivery_channel_recorded
delivery_reference_recorded
human_operator_confirmed_invoice_creation
payment_not_requested
payment_not_confirmed
paid_assessment_not_authorized
production_onboarding_not_started

## Event Score

The event_score object includes:

passed
total
score
ready

For a completed invoice creation event:

passed: 17
total: 17
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

invoice_creation_recorded
invoice_created
payment_requested
payment_confirmed
paid_assessment_authorized
production_onboarding_authorized
requires_separate_payment_request
requires_separate_payment_confirmation
requires_final_paid_work_authorization
requires_separate_production_onboarding

Required values after invoice creation event recording:

invoice_creation_recorded: true
invoice_created: true
payment_requested: false
payment_confirmed: false
paid_assessment_authorized: false
production_onboarding_authorized: false
requires_separate_payment_request: true
requires_separate_payment_confirmation: true
requires_final_paid_work_authorization: true
requires_separate_production_onboarding: true

## Evidence Boundary

Allowed evidence examples include:

executed_contract_reference
signature_evidence
invoice_review_notes
billing_readiness_notes
invoice_reference
invoice_delivery_reference
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
invoice_creation_event_is_not_payment_request
invoice_creation_event_is_not_payment_confirmation
invoice_creation_event_is_not_paid_work_authorization

Required values:

deterministic_status_required: true
gagf_kernel_authoritative: true
ai_override_allowed: false
human_boundary_required: true
release_marker_preserved: true
invoice_creation_event_is_not_payment_request: true
invoice_creation_event_is_not_payment_confirmation: true
invoice_creation_event_is_not_paid_work_authorization: true

## Boundary Notices

The event emits these boundary notices:

invoice_creation_event_records_invoice_creation_only
invoice_creation_event_does_not_request_payment
invoice_creation_event_does_not_confirm_payment
invoice_creation_event_does_not_authorize_paid_work
invoice_creation_event_does_not_start_production_onboarding
invoice_creation_event_requires_human_operator

## Audit Notes

All event statuses include:

invoice_creation_event_built
payment_not_requested
payment_not_confirmed
paid_assessment_not_authorized
production_onboarding_not_started

When invoice_created, audit notes include:

invoice_creation_event_recorded

When pending_invoice_creation_review, audit notes include:

invoice_creation_event_pending_review

When pending_invoice_creation_confirmation, audit notes include:

invoice_creation_event_pending_creation_confirmation

When pending_invoice_record, audit notes include:

invoice_creation_event_pending_invoice_record

When pending_invoice_delivery, audit notes include:

invoice_creation_event_pending_invoice_delivery

When pending_operator_confirmation, audit notes include:

invoice_creation_event_pending_operator_confirmation

When pending_invoice_creation_event_review, audit notes include:

invoice_creation_event_pending_event_review

When blocked, audit notes include:

invoice_creation_event_blocked

## Next Action

When invoice_created:

action: prepare_payment_request_review
future_action: build_payment_request_review

When pending_invoice_creation_review:

action: complete_invoice_creation_review
future_action: rerun_invoice_creation_event

When pending_invoice_creation_confirmation:

action: confirm_invoice_creation
future_action: rerun_invoice_creation_event

When pending_invoice_record:

action: record_invoice_reference
future_action: rerun_invoice_creation_event

When pending_invoice_delivery:

action: record_invoice_delivery
future_action: rerun_invoice_creation_event

When pending_operator_confirmation:

action: confirm_operator_invoice_creation_event
future_action: rerun_invoice_creation_event

When pending_invoice_creation_event_review or blocked:

action: resolve_invoice_creation_event_gaps
future_action: rerun_invoice_creation_event

## Recommended Action

When invoice_created:

prepare_payment_request_review

When not ready:

resolve_invoice_creation_event_gaps

## Human Operator Boundary

The event requires a human operator.

The event may record invoice creation.

The event does not request payment.

The event does not confirm payment.

The event does not authorize paid assessment work.

The event does not start production onboarding.

## Invoice Creation Boundary

The invoice creation event records invoice creation only.

The invoice creation event is not a payment request.

The invoice creation event is not payment confirmation.

The invoice creation event is not authorization to begin paid work.

A separate payment request review, payment confirmation, final paid-work authorization, and production onboarding gate must occur after this event.

## GAGF Meaning

The event represents the GAGF pattern:

Invoice Readiness → Invoice Record → Buyer Delivery → Human Confirmation → Boundary Preservation → Governed Next Action

The object is not a generic billing-stage update.

It is a deterministic governance checkpoint for recording invoice creation without overclaiming downstream payment or work authority.

It proves the system can record a real invoice event while preserving payment request, payment confirmation, paid-work authorization, and onboarding boundaries.

## Product Meaning

This event moves Assessment Factory Lite from invoice-creation readiness into recorded invoice creation.

It is the first object in the workflow that may confirm an actual created invoice.

It keeps the product commercially useful while preserving evidence, commercial, scheduling, and governance boundaries.

## Next Story

US-309 — Assessment Factory Lite Invoice Creation Event Release Marker
