# Assessment Factory Lite Buyer Follow-Up Event Record

## Purpose

The Assessment Factory Lite Buyer Follow-Up Event Record creates a local record for a human-operated buyer follow-up action.

It does not send a follow-up message.

It does not create an automated email, CRM record, calendar event, invoice, contract, payment request, production onboarding action, or compliance certification.

It creates a deterministic event record that captures the follow-up message status, follow-up channel, recipient status, message summary, send policy snapshot, operator review snapshot, buyer response summary, commercial next action, boundary notices, follow-up outcome, audit notes, and next action.

## Capability Chain

Assessment Factory Lite Buyer Follow-Up Message
→ Buyer Follow-Up Event Record Service
→ Buyer Follow-Up Event Record Endpoint
→ Human-Operated Follow-Up Record
→ Future Assessment Scope Call Package
→ Future Delivery Ledger

## Service

### AssessmentFactoryLiteBuyerFollowUpEventRecordService

File:

backend/app/gagf/assessment_factory_lite_buyer_follow_up_event_record_service.py

Purpose:

Build a local event record for a human-operated buyer follow-up action.

The service can build the event record from an existing follow_up_message, buyer follow-up tracker, buyer delivery event record, buyer delivery message, buyer delivery package, proposal export package, Markdown export, formal proposal document, proposal-ready artifact, paid-assessment offer, buyer_context, operator_approval, message_context, event_context, follow_up_context, follow_up_message_context, or follow_up_event_context.

## Endpoint

### Buyer Follow-Up Event Record Endpoint

POST /products/assessment-factory-lite/buyer-follow-up-event-record

Purpose:

Returns a buyer follow-up event record object.

The Operator Workstation can use this endpoint to record follow-up metadata after a human-operated follow-up action.

## Request Contract

The request body may include:

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

## Follow-Up Message Input

The follow_up_message object may be supplied when the operator wants to create an event record from a previously generated buyer follow-up message.

If follow_up_message is supplied, the event record service uses it directly.

## Tracker Input

The tracker object may be supplied when the operator wants the service chain to build a follow-up message from a buyer follow-up tracker and then create the event record.

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

The operator_approval object may be supplied when the operator wants the service chain to generate a send-ready buyer delivery message, recorded delivery event, follow-up tracker, and follow-up message before creating the event record.

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

## Response Contract

The buyer follow-up event record response includes:

status
event_type
package_name
release
version
event_stage
event_status
event_id
recorded_at
source_follow_up_message
follow_up_channel
recipient_status
message_summary
send_policy_snapshot
operator_review_snapshot
buyer_response_summary
commercial_next_action
boundary_notices
follow_up_outcome
audit_notes
next_action
operator_message
recommended_action

## Event Type

The event_type value is:

assessment_factory_lite_buyer_follow_up_event_record

## Release Marker

The buyer follow-up event record object belongs to:

release:

assessment-factory-lite-proposal-export-package

version:

2.1.0

## Event Stage

The event_stage value is:

buyer_follow_up_event_record

## Event Status Values

The event_status value can be:

recorded
pending_human_confirmation
pending_follow_up_completion
blocked

## Recorded Status

recorded means:

The source buyer follow-up message is draft_ready or response_reply_draft_ready.
A human operator confirmed the follow-up action.
The follow-up action was marked complete.
The event record can be reviewed and preserved.

Default recorded recommended action:

review_buyer_follow_up_event_record

## Pending Human Confirmation Status

pending_human_confirmation means:

The source buyer follow-up message is valid.
The follow-up may be complete.
Human operator confirmation is missing.

Default pending human confirmation next action:

confirm_human_operator_follow_up

## Pending Follow-Up Completion Status

pending_follow_up_completion means:

The source buyer follow-up message is valid.
Human operator confirmation exists.
Follow-up completion is not yet marked true.

Default pending follow-up completion next action:

complete_follow_up_before_recording

## Blocked Status

blocked means:

The source buyer follow-up message is not draft_ready or response_reply_draft_ready.

A blocked follow-up message cannot be recorded as a completed buyer follow-up event.

Default blocked recommended action:

resolve_buyer_follow_up_event_record_gaps

## Event ID

Default event_id:

buyer-follow-up-event-draft-001

Custom event_id example:

buyer-follow-up-event-001

## Recorded At

recorded_at may be supplied by follow_up_event_context.

Example:

2026-07-21T12:00:00+00:00

If recorded_at is not supplied, the service generates a UTC timestamp.

## Source Follow-Up Message

The source_follow_up_message section preserves buyer follow-up message identity.

Default values:

message_type: assessment_factory_lite_buyer_follow_up_message
message_stage: buyer_follow_up_message_draft
message_status: draft_ready
delivery_channel: email_draft
release: assessment-factory-lite-proposal-export-package
version: 2.1.0
recommended_action: review_buyer_follow_up_message

Response reply values may include:

message_status: response_reply_draft_ready

## Follow-Up Channel

The follow_up_channel section includes:

channel
channel_status
automated_follow_up_used
human_operated
send_reference

Default human-operated values:

channel: email_draft
channel_status: operator_recorded
automated_follow_up_used: False
human_operated: True
send_reference: manual-follow-up-log-001

## Recipient Status

The recipient_status section includes:

recipient_type
recipient_role
email_required
email_status
recipient_confirmed

Example values:

recipient_type: buyer_role
recipient_role: founder_operator
email_required: True
email_status: operator_confirmed
recipient_confirmed: True

## Message Summary

The message_summary section includes:

subject
message_status
message_stage
message_type
commercial_next_action
buyer_response_status

No-response example:

subject: Following Up on the Assessment Factory Lite Proposal Package
message_status: draft_ready
message_stage: buyer_follow_up_message_draft
message_type: assessment_factory_lite_buyer_follow_up_message
commercial_next_action: send_follow_up_if_no_response
buyer_response_status: no_response

Interested-response example:

subject: Next Step: Assessment Factory Lite Scope Call
message_status: response_reply_draft_ready
commercial_next_action: schedule_assessment_scope_call
buyer_response_status: interested

## Send Policy Snapshot

The send_policy_snapshot section captures the send policy from the source buyer follow-up message.

Default values:

send_allowed: False
send_blocked_reason: Human operator review and approval are required before follow-up sending.
automated_send_allowed: False
requires_human_operator: True

Send rule:

Buyer follow-up messages are draft-only and must be reviewed, approved, and sent by a human operator.

## Operator Review Snapshot

The operator_review_snapshot section captures operator review status from the source buyer follow-up message.

Active tracker default values:

tracker_status: active
follow_up_blockers: []
review_required: True
human_operator_required: True
approved_for_sending: False

Response-received values may include:

tracker_status: response_received

## Buyer Response Summary

The buyer_response_summary section preserves buyer response state from the follow-up message.

Default no-response values:

response_status: no_response
response_received: False
response_received_at: empty string
response_summary: empty string
buyer_questions: []
buyer_objections: []

Interested values may include:

response_status: interested
response_received: True
response_summary: Buyer wants to schedule a scope call.

## Commercial Next Action

The commercial_next_action section preserves the follow-up commercial action.

Supported actions include:

send_follow_up_if_no_response
schedule_assessment_scope_call
answer_buyer_questions
close_or_nurture_lead
resolve_delivery_event_before_follow_up

## Boundary Notices

The buyer follow-up event record preserves boundary notices from the source message and delivery chain.

Required boundary concepts include:

commercial_boundary
evidence_boundary
pdf_boundary
constitutional_boundary

## Follow-Up Outcome

The follow_up_outcome section includes:

follow_up_completed
follow_up_result
message_status
send_allowed
human_operator_confirmed
outcome_note

Recorded example:

follow_up_completed: True
follow_up_result: sent
message_status: draft_ready
send_allowed: False
human_operator_confirmed: True
outcome_note: Human operator sent the approved buyer follow-up message.

Important:

send_allowed remains False because this service records a human-operated follow-up action. It does not authorize automated sending.

## Audit Notes

The audit_notes section preserves supplied audit notes and adds deterministic status notes.

Recorded event audit notes include:

follow_up_message_review_completed
human_operated_follow_up_recorded
automated_follow_up_not_performed

Pending human confirmation audit note:

human_operator_confirmation_required

Pending follow-up completion audit note:

follow_up_completion_required

Blocked audit note:

valid_follow_up_message_required

Every follow-up event record includes:

automated_follow_up_not_performed

## Recorded Next Action

When event_status is recorded, next_action includes:

action: review_follow_up_event_record

operator_instruction:

Review the buyer follow-up event record, confirm follow-up metadata, and preserve the record for commercial tracking.

future_action:

prepare_assessment_scope_call_package

## Pending Human Confirmation Next Action

When event_status is pending_human_confirmation, next_action includes:

action: confirm_human_operator_follow_up

operator_instruction:

Confirm that a human operator reviewed and controlled the follow-up action before recording completion.

future_action:

record_buyer_follow_up_event

## Pending Follow-Up Completion Next Action

When event_status is pending_follow_up_completion, next_action includes:

action: complete_follow_up_before_recording

operator_instruction:

Complete the human-operated follow-up action before marking the event as recorded.

future_action:

record_buyer_follow_up_event

## Blocked Next Action

When event_status is blocked, next_action includes:

action: resolve_buyer_follow_up_event_record_gaps

operator_instruction:

Resolve follow-up message readiness or human confirmation gaps before recording buyer follow-up.

future_action:

rerun_buyer_follow_up_event_record

## Recorded Operator Message

Assessment Factory Lite buyer follow-up event record has been created for a human-operated follow-up action.

## Pending Human Confirmation Operator Message

Assessment Factory Lite buyer follow-up event record is pending human operator confirmation.

## Pending Follow-Up Completion Operator Message

Assessment Factory Lite buyer follow-up event record is pending follow-up completion.

## Blocked Operator Message

Assessment Factory Lite buyer follow-up event record is blocked because the follow-up message is not valid for recording.

## Full Recorded Follow-Up Event Example

A recorded follow-up event requires:

message_status: draft_ready
human_operator_confirmed: True
follow_up_completed: True
follow_up_result: sent

Expected result:

event_status: recorded
recommended_action: review_buyer_follow_up_event_record
human_operated_follow_up_recorded
automated_follow_up_not_performed
next_action.action: review_follow_up_event_record

## Interested Response Follow-Up Event Example

An interested buyer response may produce:

message_status: response_reply_draft_ready
subject: Next Step: Assessment Factory Lite Scope Call
commercial_next_action: schedule_assessment_scope_call
buyer_response_status: interested

Expected result:

event_status: recorded
recommended_action: review_buyer_follow_up_event_record

## Pending Human Confirmation Example

If follow_up_completed is True but human_operator_confirmed is False, the event record becomes:

event_status: pending_human_confirmation
recommended_action: resolve_buyer_follow_up_event_record_gaps
human_operator_confirmation_required
next_action.action: confirm_human_operator_follow_up

## Pending Follow-Up Completion Example

If human_operator_confirmed is True but follow_up_completed is False, the event record becomes:

event_status: pending_follow_up_completion
recommended_action: resolve_buyer_follow_up_event_record_gaps
follow_up_completion_required
next_action.action: complete_follow_up_before_recording

## Blocked Follow-Up Message Example

If the source buyer follow-up message is blocked, the event record becomes:

event_status: blocked
recommended_action: resolve_buyer_follow_up_event_record_gaps
source_follow_up_message.message_status: blocked
valid_follow_up_message_required
next_action.action: resolve_buyer_follow_up_event_record_gaps

## Relationship to Buyer Follow-Up Message

The buyer follow-up message drafts human-operated follow-up language based on the follow-up tracker.

The buyer follow-up event record captures whether a human-operated follow-up action was confirmed, completed, and recorded.

The buyer follow-up message answers:

What human-reviewed follow-up message should be prepared next?

The buyer follow-up event record answers:

Was a follow-up message sent by a human operator, and what follow-up metadata should be preserved?

## Relationship to Future Assessment Scope Call Package

The buyer follow-up event record does not schedule a scope call.

A future assessment scope call package may use:

buyer follow-up event record
buyer response summary
commercial next action
recipient status
send reference
follow-up outcome
scope call agenda
evidence boundary
operator-approved scheduling language

## Relationship to Future Delivery Ledger

The buyer follow-up event record is a local object.

A future delivery ledger may persist follow-up events with:

event_id
recorded_at
source message hash
operator identity
recipient identity
send policy snapshot
operator review snapshot
buyer response summary
commercial next action
follow-up outcome
audit notes
immutable chain hash

## Commercial Boundary

The buyer follow-up event record does not create a binding quote, binding sales contract, invoice, legal agreement, payment request, signed proposal, CRM opportunity, calendar invite, scope call, or production onboarding commitment.

The record only captures follow-up metadata after a human-operated follow-up action.

## Compliance Boundary

The Assessment Factory Lite Buyer Follow-Up Event Record does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It creates a deterministic follow-up event record for a bounded paid-assessment conversation.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Buyer Follow-Up Event Record does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, live integrations, buyer delivery, send actions, email delivery, follow-up sending, CRM creation, calendar scheduling, scope call scheduling, or operator approval.

It does not perform automated follow-up.

It records a human-operated follow-up event only after a valid follow-up message exists, human confirmation is present, and follow-up completion is true.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or summarize buyer follow-up events, but AI must not override deterministic delivery checks, evidence boundaries, approval requirements, operator notes, boundary notices, commercial terms, blocked follow-up behavior, follow-up event status, send policy, or operator approval gates without human-approved policy changes.
