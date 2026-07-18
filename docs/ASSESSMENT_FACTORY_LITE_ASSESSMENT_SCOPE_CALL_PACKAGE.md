# Assessment Factory Lite Assessment Scope Call Package

## Purpose

The Assessment Factory Lite Assessment Scope Call Package prepares the operator-reviewed materials needed for a bounded paid-assessment scope call.

It does not schedule a meeting.

It does not create a calendar event, send a calendar invite, send an email, create a CRM record, create an invoice, create a payment request, create a contract, approve production onboarding, or certify compliance readiness.

It creates a deterministic package that captures the source follow-up event record, buyer response summary, commercial next action, scope-call readiness, agenda, evidence boundary, commercial boundary, operator approval gate, scheduling boundary, checklist, blockers, boundary notices, audit notes, next action, and operator message.

## Capability Chain

Assessment Factory Lite Buyer Follow-Up Event Record
→ Assessment Scope Call Package Service
→ Assessment Scope Call Package Endpoint
→ Operator Review
→ Future Scope Call Agenda Message
→ Future Scope Call Event Record
→ Future Paid Assessment Intake Package

## Service

### AssessmentFactoryLiteAssessmentScopeCallPackageService

File:

backend/app/gagf/assessment_factory_lite_assessment_scope_call_package_service.py

Purpose:

Build an operator-reviewed assessment scope call package.

The service can build the package from an existing follow_up_event_record, follow_up_message, buyer follow-up tracker, buyer delivery event record, buyer delivery message, buyer delivery package, proposal export package, Markdown export, formal proposal document, proposal-ready artifact, paid-assessment offer, buyer_context, operator_approval, message_context, event_context, follow_up_context, follow_up_message_context, follow_up_event_context, or scope_call_context.

## Endpoint

### Assessment Scope Call Package Endpoint

POST /products/assessment-factory-lite/assessment-scope-call-package

Purpose:

Returns an assessment scope call package object.

The Operator Workstation can use this endpoint to prepare bounded scope-call materials after a recorded human-operated follow-up event.

## Request Contract

The request body may include:

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

## Follow-Up Event Record Input

The follow_up_event_record object may be supplied when the operator wants to create a scope-call package from a previously generated buyer follow-up event record.

If follow_up_event_record is supplied, the scope-call package service uses it directly.

## Follow-Up Message Input

The follow_up_message object may be supplied when the operator wants the service chain to build a follow-up event record from a follow-up message and then create the scope-call package.

## Tracker Input

The tracker object may be supplied when the operator wants the service chain to start from a buyer follow-up tracker.

## Event Record Input

The event_record object may be supplied when the operator wants the service chain to start from a buyer delivery event record.

## Message Input

The message object may be supplied when the operator wants the service chain to start from a buyer delivery message.

## Delivery Package Input

The delivery_package object may be supplied when the operator wants the service chain to start from a buyer delivery package.

## Export Package Input

The export_package object may be supplied when the operator wants the service chain to start from a proposal export package.

## Export Input

The export object may be supplied when the operator wants the service chain to start from a Markdown export.

## Document Input

The document object may be supplied when the operator wants the service chain to start from a formal proposal document.

## Proposal Input

The proposal object may be supplied when the operator wants the service chain to start from a proposal-ready artifact.

## Offer Input

The offer object may be supplied when the operator wants the service chain to start from a paid-assessment offer.

## Buyer Context Input

The buyer_context object may include:

primary_buyer
secondary_buyers
buyer_pain
workflow_area
requested_sources
duration
deliverable_format
price_low
price_high
recommended_message

## Operator Approval Input

The operator_approval object may be supplied when the operator wants the service chain to generate a send-ready buyer delivery message, recorded delivery event, follow-up tracker, follow-up message, and follow-up event record before creating the scope-call package.

Supported approval fields:

approval_status
scope_approved
evidence_boundary_approved
commercial_terms_approved
buyer_language_approved
approval_note

## Message Context Input

The message_context object may include:

recipient_role
sender_name
delivery_channel

## Event Context Input

The event_context object may include:

event_id
recorded_at
human_operator_confirmed
delivery_completed
delivery_channel
channel_status
send_reference
email_status
recipient_confirmed
delivery_result
outcome_note
audit_notes

## Follow-Up Context Input

The follow_up_context object may include:

tracker_id
created_at
buyer_response_status
response_received_at
response_summary
buyer_questions
buyer_objections
follow_up_due_at
follow_up_channel
follow_up_owner
reminder_status
audit_notes

## Follow-Up Message Context Input

The follow_up_message_context object may include:

recipient_role
sender_name
delivery_channel
email_status
subject

## Follow-Up Event Context Input

The follow_up_event_context object may include:

event_id
recorded_at
human_operator_confirmed
follow_up_completed
follow_up_channel
channel_status
send_reference
email_status
recipient_confirmed
follow_up_result
outcome_note
audit_notes

## Scope Call Context Input

The scope_call_context object may include:

package_id
created_at
agenda_items
agenda_owner
allowed_evidence
excluded_evidence
price_range
approval_status
agenda_approved
evidence_boundary_approved
commercial_terms_approved
scheduling_language_approved

## Response Contract

The assessment scope call package response includes:

status
package_type
package_name
release
version
package_stage
package_status
package_id
created_at
source_follow_up_event_record
buyer_response_summary
commercial_next_action
scope_call_readiness
scope_call_agenda
evidence_boundary
commercial_boundary
operator_approval_gate
scheduling_boundary
package_checklist
package_blockers
boundary_notices
audit_notes
next_action
operator_message
recommended_action

## Package Type

The package_type value is:

assessment_factory_lite_assessment_scope_call_package

## Release Marker

The assessment scope call package object belongs to:

release:

assessment-factory-lite-buyer-delivery-follow-up

version:

2.2.0

## Package Stage

The package_stage value is:

assessment_scope_call_package

## Package Status Values

The package_status value can be:

ready
review_required
blocked

## Ready Status

ready means:

The source buyer follow-up event record is recorded.
The buyer response status is interested.
The commercial next action is schedule_assessment_scope_call.
A scope-call agenda is present.
Operator review is still required before scheduling.

Default ready recommended action:

review_assessment_scope_call_package

## Review-Required Status

review_required means:

The source buyer follow-up event record is recorded, but the buyer response or commercial next action does not yet support a scope call.

This commonly occurs when buyer_response_status is questions or declined.

Default review-required recommended action:

resolve_assessment_scope_call_package_gaps

## Blocked Status

blocked means:

The source buyer follow-up event record is not recorded.

A blocked follow-up event cannot produce a ready assessment scope call package.

Default blocked recommended action:

resolve_assessment_scope_call_package_gaps

## Package ID

Default package_id:

assessment-scope-call-package-draft-001

Custom package_id example:

assessment-scope-call-package-001

## Created At

created_at may be supplied by scope_call_context.

Example:

2026-07-21T12:30:00+00:00

If created_at is not supplied, the service generates a UTC timestamp.

## Source Follow-Up Event Record

The source_follow_up_event_record section preserves buyer follow-up event record identity.

Default values:

event_type: assessment_factory_lite_buyer_follow_up_event_record
event_stage: buyer_follow_up_event_record
event_status: recorded
event_id: buyer-follow-up-event-001
recorded_at: 2026-07-21T12:00:00+00:00
release: assessment-factory-lite-proposal-export-package
version: 2.1.0
recommended_action: review_buyer_follow_up_event_record

## Buyer Response Summary

The buyer_response_summary section preserves buyer response state from the follow-up event record.

Interested values may include:

response_status: interested
response_received: True
response_received_at: 2026-07-18T09:00:00+00:00
response_summary: Buyer wants to schedule a scope call.
buyer_questions: Can we start next week?
buyer_objections: []

Questions values may include:

response_status: questions
response_summary: Buyer has questions before scheduling.
buyer_questions: Can you clarify evidence boundaries?

## Commercial Next Action

The commercial_next_action section preserves the commercial action from the follow-up event record.

Scope-call-ready action:

schedule_assessment_scope_call

Other supported actions include:

send_follow_up_if_no_response
answer_buyer_questions
close_or_nurture_lead
resolve_delivery_event_before_follow_up

## Scope Call Readiness

The scope_call_readiness section includes:

scope_call_ready
event_recorded
buyer_interested
commercial_action_supported
requires_operator_review
automatic_scheduling_allowed

Ready values:

scope_call_ready: True
event_recorded: True
buyer_interested: True
commercial_action_supported: True
requires_operator_review: True
automatic_scheduling_allowed: False

Questions-response values may include:

scope_call_ready: False
event_recorded: True
buyer_interested: False
commercial_action_supported: False

## Scope Call Agenda

The scope_call_agenda section includes required agenda items.

Default agenda:

confirm workflow scope
confirm evidence sources
confirm evidence boundaries
confirm timeline and deliverables
confirm commercial terms
confirm next approval step

Each agenda item includes:

item
required
owner

Default owner:

operator

## Evidence Boundary

The evidence_boundary section includes:

allowed_evidence
excluded_evidence
approval_required

Default allowed evidence:

non-sensitive sample workflow data
redacted operational examples
operator-approved buyer-provided context

Default excluded evidence:

regulated production data
secrets or credentials
unapproved personal data
unapproved customer records

approval_required: True

## Commercial Boundary

The commercial_boundary section includes:

scope_call_is_non_binding
not_a_contract
not_an_invoice
not_a_payment_request
not_production_onboarding
price_range
final_terms_require_operator_approval

Default values:

scope_call_is_non_binding: True
not_a_contract: True
not_an_invoice: True
not_a_payment_request: True
not_production_onboarding: True
price_range: USD 1500 - 3500
final_terms_require_operator_approval: True

## Operator Approval Gate

The operator_approval_gate section includes:

approval_status
agenda_approved
evidence_boundary_approved
commercial_terms_approved
scheduling_language_approved

Default values:

approval_status: operator_review_required
agenda_approved: False
evidence_boundary_approved: False
commercial_terms_approved: False
scheduling_language_approved: False

## Scheduling Boundary

The scheduling_boundary section includes:

calendar_event_created
calendar_invite_sent
automatic_scheduling_allowed
requires_human_operator
scheduling_rule

Default values:

calendar_event_created: False
calendar_invite_sent: False
automatic_scheduling_allowed: False
requires_human_operator: True

Scheduling rule:

The package may prepare scope-call material, but a human operator must approve and schedule the call.

## Package Checklist

The package_checklist section includes:

follow_up_event_recorded
buyer_interested
scope_call_action_supported
agenda_present
operator_review_required

Ready checklist values:

follow_up_event_recorded: True
buyer_interested: True
scope_call_action_supported: True
agenda_present: True
operator_review_required: True

## Package Blockers

The package_blockers section lists failed checklist items.

Ready package blockers:

[]

Questions-response package blockers may include:

buyer_interested
scope_call_action_supported

Blocked package blockers may include:

follow_up_event_recorded
buyer_interested
scope_call_action_supported

## Boundary Notices

The assessment scope call package preserves boundary notices from the follow-up event record and upstream chain.

Required boundary concepts include:

commercial_boundary
evidence_boundary
pdf_boundary
constitutional_boundary

## Audit Notes

Ready package audit notes:

assessment_scope_call_package_ready
automatic_scheduling_not_performed

Review-required audit notes:

assessment_scope_call_package_review_required
automatic_scheduling_not_performed

Blocked audit notes:

assessment_scope_call_package_blocked
automatic_scheduling_not_performed

Every assessment scope call package includes:

automatic_scheduling_not_performed

## Ready Next Action

When package_status is ready, next_action includes:

action: review_and_prepare_scope_call

operator_instruction:

Review the agenda, evidence boundary, commercial boundary, and scheduling language before manually scheduling the scope call.

future_action:

prepare_scope_call_agenda_message

## Review-Required Next Action

When package_status is review_required, next_action includes:

action: review_buyer_response_before_scope_call

operator_instruction:

Review buyer response and commercial next action before preparing a scope call package.

future_action:

rerun_assessment_scope_call_package

## Blocked Next Action

When package_status is blocked, next_action includes:

action: resolve_assessment_scope_call_package_gaps

operator_instruction:

Resolve follow-up event, buyer response, or commercial action gaps before preparing a scope call package.

future_action:

rerun_assessment_scope_call_package

## Ready Operator Message

Assessment Factory Lite assessment scope call package is ready for operator review.

## Review-Required Operator Message

Assessment Factory Lite assessment scope call package requires operator review before scope-call preparation.

## Blocked Operator Message

Assessment Factory Lite assessment scope call package is blocked because the buyer follow-up event or buyer interest state is incomplete.

## Full Ready Scope Call Package Example

A ready scope call package requires:

event_status: recorded
buyer_response_status: interested
commercial_next_action.action: schedule_assessment_scope_call
scope_call_ready: True
automatic_scheduling_allowed: False

Expected result:

package_status: ready
recommended_action: review_assessment_scope_call_package
next_action.action: review_and_prepare_scope_call
audit_notes: assessment_scope_call_package_ready and automatic_scheduling_not_performed
package_blockers: []

## Questions Response Review-Required Example

If buyer_response_status is questions, the package becomes:

package_status: review_required
recommended_action: resolve_assessment_scope_call_package_gaps
scope_call_readiness.buyer_interested: False
package_blockers: buyer_interested and scope_call_action_supported
next_action.action: review_buyer_response_before_scope_call

## Blocked Follow-Up Event Example

If the source follow-up event record is blocked, the package becomes:

package_status: blocked
recommended_action: resolve_assessment_scope_call_package_gaps
source_follow_up_event_record.event_status: blocked
package_blockers: follow_up_event_recorded, buyer_interested, and scope_call_action_supported
next_action.action: resolve_assessment_scope_call_package_gaps

## Relationship to Buyer Follow-Up Event Record

The buyer follow-up event record captures whether a human-operated follow-up action was confirmed, completed, and recorded.

The assessment scope call package uses that event record to determine whether the buyer is ready for a bounded assessment scope call.

The buyer follow-up event record answers:

Was a follow-up message sent by a human operator, and what follow-up metadata should be preserved?

The assessment scope call package answers:

Is the buyer ready for a bounded paid-assessment scope call, and what material must the operator review before scheduling?

## Relationship to Future Scope Call Agenda Message

The assessment scope call package does not create the scope-call invitation message.

A future scope call agenda message may use:

scope_call_agenda
evidence_boundary
commercial_boundary
operator_approval_gate
scheduling_boundary
buyer_response_summary
commercial_next_action
operator-approved scheduling language

## Relationship to Future Scope Call Event Record

The assessment scope call package does not record that a scope call was scheduled or completed.

A future scope call event record may use:

package_id
operator identity
buyer identity
scope call time
calendar reference
human confirmation
agenda snapshot
evidence boundary snapshot
commercial boundary snapshot
audit notes
immutable event hash

## Relationship to Future Paid Assessment Intake Package

The assessment scope call package does not start a paid assessment.

A future paid assessment intake package may use:

scope call event record
approved evidence sources
approved workflow scope
buyer pain
commercial terms
deliverable expectations
operator approval
payment status
engagement boundary
contract boundary

## Commercial Boundary

The assessment scope call package does not create a binding quote, binding sales contract, invoice, legal agreement, payment request, signed proposal, CRM opportunity, calendar invite, scope call, or production onboarding commitment.

The package only prepares scope-call material for operator review.

## Compliance Boundary

The Assessment Factory Lite Assessment Scope Call Package does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It creates a deterministic scope-call package for a bounded paid-assessment conversation.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Assessment Scope Call Package does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, live integrations, buyer delivery, send actions, email delivery, follow-up sending, CRM creation, calendar scheduling, scope call scheduling, paid assessment start, payment collection, or operator approval.

It does not perform automated scheduling.

It prepares a scope-call package only after a recorded follow-up event exists and buyer interest supports the scope-call commercial next action.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain, summarize, or adapt scope-call materials, but AI must not override deterministic delivery checks, evidence boundaries, approval requirements, operator notes, boundary notices, commercial terms, blocked package behavior, scope-call package status, scheduling boundary, or operator approval gates without human-approved policy changes.
