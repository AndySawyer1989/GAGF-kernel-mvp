# Assessment Factory Lite Buyer Follow-Up Message

## Purpose

The Assessment Factory Lite Buyer Follow-Up Message creates a human-operated buyer follow-up message draft from a buyer follow-up tracker.

It does not send a follow-up message.

It does not create an automated email, CRM record, calendar event, invoice, contract, payment request, production onboarding action, or compliance certification.

It creates a deterministic follow-up message draft for operator review.

## Capability Chain

Assessment Factory Lite Buyer Follow-Up Tracker
→ Buyer Follow-Up Message Service
→ Buyer Follow-Up Message Endpoint
→ Operator Review
→ Future Buyer Follow-Up Event Record
→ Future Assessment Scope Call Package

## Service

### AssessmentFactoryLiteBuyerFollowUpMessageService

File:

backend/app/gagf/assessment_factory_lite_buyer_follow_up_message_service.py

Purpose:

Build a human-operated buyer follow-up message draft from a buyer follow-up tracker.

The service can build the message from an existing tracker, delivery event record, buyer delivery message, buyer delivery package, proposal export package, Markdown export, formal proposal document, proposal-ready artifact, paid-assessment offer, buyer_context, operator_approval, message_context, event_context, follow_up_context, or follow_up_message_context.

## Endpoint

### Buyer Follow-Up Message Endpoint

POST /products/assessment-factory-lite/buyer-follow-up-message

Purpose:

Returns a buyer follow-up message draft.

The Operator Workstation can use this endpoint to prepare no-response follow-up drafts and response-based reply drafts.

## Request Contract

The request body may include:

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

## Tracker Input

The tracker object may be supplied when the operator wants to create a follow-up message from a previously generated buyer follow-up tracker.

If tracker is supplied, the message service uses it directly.

## Event Record Input

The event_record object may be supplied when the operator wants the service chain to build a tracker from a delivery event record and then create the follow-up message.

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

The operator_approval object may be supplied when the operator wants the service chain to generate a send-ready buyer delivery message, recorded delivery event, and follow-up tracker before creating the follow-up message.

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

Default recipient_role:

operations_leader

Default sender_name:

Assessment Factory Lite Operator

Default delivery_channel:

email_draft

## Response Contract

The buyer follow-up message response includes:

status
message_type
package_name
release
version
message_stage
message_status
delivery_channel
recipient
sender
subject
message_body
source_follow_up_tracker
buyer_response_summary
commercial_next_action
follow_up_schedule
operator_review
boundary_notices
send_policy
next_action
operator_message
recommended_action

## Message Type

The message_type value is:

assessment_factory_lite_buyer_follow_up_message

## Release Marker

The buyer follow-up message object belongs to:

release:

assessment-factory-lite-proposal-export-package

version:

2.1.0

## Message Stage

The message_stage value is:

buyer_follow_up_message_draft

## Message Status Values

The message_status value can be:

draft_ready
response_reply_draft_ready
blocked

## Draft-Ready Status

draft_ready means:

The buyer follow-up tracker is active.
No buyer response has been recorded.
The service created a no-response follow-up draft.
The draft requires operator review before sending.

Default draft-ready recommended action:

review_buyer_follow_up_message

## Response-Reply Draft-Ready Status

response_reply_draft_ready means:

The buyer follow-up tracker has response_received status.
The buyer response is classified as interested, questions, or declined.
The service created a response-based reply draft.
The draft requires operator review before sending.

Default response-reply recommended action:

review_buyer_follow_up_message

## Blocked Status

blocked means:

The buyer follow-up tracker is not active or response_received.

A follow-up message draft cannot proceed until the tracker is valid.

Default blocked recommended action:

resolve_buyer_follow_up_message_gaps

## Recipient

The recipient section includes:

recipient_type
recipient_role
email_required
email_status

Default values:

recipient_type: buyer_role
recipient_role: operations_leader
email_required: True
email_status: operator_to_provide

Custom recipient example:

recipient_role: founder_operator

## Sender

The sender section includes:

sender_type
sender_name
signature_required

Default values:

sender_type: operator
sender_name: Assessment Factory Lite Operator
signature_required: True

Custom sender example:

sender_name: Andy Sawyer

## Delivery Channel

Default delivery channel:

email_draft

Meaning:

The service creates a draft message object only.

It does not send email.

It does not create a Gmail draft.

It does not create a CRM record.

It does not notify a buyer.

## Subject Behavior

Default no-response subject:

Following Up on the Assessment Factory Lite Proposal Package

Interested response subject:

Next Step: Assessment Factory Lite Scope Call

Questions response subject:

Re: Assessment Factory Lite Proposal Questions

Declined response subject:

Thank You for Reviewing Assessment Factory Lite

## Message Body

The message body includes:

greeting
follow-up purpose
buyer response handling
non-binding boundary
commercial next action
operator signature

## No-Response Body Behavior

When buyer_response_status is no_response, the message body follows up on the Assessment Factory Lite proposal package.

It references the tracked follow-up due date.

It asks whether the buyer would like to discuss the bounded assessment scope and next steps.

The body includes:

tracked due date of 2026-07-20T12:15:00+00:00
bounded assessment scope and next steps
Current commercial next action: send_follow_up_if_no_response.

## Interested Response Body Behavior

When buyer_response_status is interested, the message body thanks the buyer for interest and recommends scheduling a bounded assessment scope call.

The body includes:

Thank you for your interest
schedule a bounded assessment scope call
workflow scope
evidence boundaries
timing
commercial terms
Current commercial next action: schedule_assessment_scope_call.

## Questions Response Body Behavior

When buyer_response_status is questions, the message body acknowledges the buyer questions.

The body includes:

I received your questions
preserving the approved commercial, evidence, and scope boundaries
Current commercial next action: answer_buyer_questions.

## Declined Response Body Behavior

When buyer_response_status is declined, the message body thanks the buyer for reviewing the proposal package and leaves the door open for a future bounded assessment conversation.

The body includes:

Thank you for reviewing the Assessment Factory Lite proposal package
future bounded assessment conversation
Current commercial next action: close_or_nurture_lead.

## Non-Binding Message Boundary

The message body states that the follow-up is non-binding and does not create a contract, invoice, payment request, compliance certification, or production onboarding commitment.

## Source Follow-Up Tracker

The source_follow_up_tracker section preserves tracker identity.

Default values:

tracker_type: assessment_factory_lite_buyer_follow_up_tracker
tracker_stage: buyer_follow_up_tracker
tracker_status: active
tracker_id: buyer-follow-up-tracker-001
created_at: 2026-07-17T12:15:00+00:00
release: assessment-factory-lite-proposal-export-package
version: 2.1.0
recommended_action: review_buyer_follow_up_tracker

## Buyer Response Summary

The buyer_response_summary section preserves:

response_status
response_received
response_received_at
response_summary
buyer_questions
buyer_objections

Default no-response values:

response_status: no_response
response_received: False
response_received_at: empty string
response_summary: empty string
buyer_questions: []
buyer_objections: []

Interested response values:

response_status: interested
response_received: True
response_received_at: 2026-07-18T09:00:00+00:00
response_summary: Buyer wants to schedule a scope call.
buyer_questions: Can we start next week?
buyer_objections: []

## Commercial Next Action

The commercial_next_action section is copied from the buyer follow-up tracker.

Supported actions include:

send_follow_up_if_no_response
schedule_assessment_scope_call
answer_buyer_questions
close_or_nurture_lead
resolve_delivery_event_before_follow_up

## Follow-Up Schedule

The follow_up_schedule section is copied from the buyer follow-up tracker.

Default values include:

follow_up_required: True
follow_up_due_at: 2026-07-20T12:15:00+00:00
follow_up_channel: email
follow_up_owner: operator
reminder_status: pending

## Operator Review

The operator_review section includes:

tracker_status
follow_up_blockers
review_required
human_operator_required
approved_for_sending

Default values:

tracker_status: active
follow_up_blockers: []
review_required: True
human_operator_required: True
approved_for_sending: False

## Send Policy

The send_policy section includes:

send_allowed
send_blocked_reason
automated_send_allowed
requires_human_operator
send_rule

Default draft-ready values:

send_allowed: False
send_blocked_reason: Human operator review and approval are required before follow-up sending.
automated_send_allowed: False
requires_human_operator: True

Send rule:

Buyer follow-up messages are draft-only and must be reviewed, approved, and sent by a human operator.

## Automated Follow-Up Boundary

Automated follow-up sending is never allowed by this message service.

The service only creates a follow-up message draft.

Human operator review is always required before follow-up delivery.

## Draft-Ready Next Action

When message_status is draft_ready, next_action includes:

action: review_no_response_follow_up_draft

operator_instruction:

Review the no-response follow-up draft, verify due date and recipient details, and send only through a human-operated channel.

future_action:

record_buyer_follow_up_event

## Response-Reply Draft-Ready Next Action

When message_status is response_reply_draft_ready, next_action includes:

action: review_buyer_response_reply

operator_instruction:

Review the response-based follow-up draft, verify buyer response context, and send only through a human-operated channel.

future_action:

record_buyer_follow_up_event

## Blocked Next Action

When message_status is blocked, next_action includes:

action: resolve_buyer_follow_up_message_gaps

operator_instruction:

Resolve follow-up tracker gaps before preparing a buyer follow-up message draft.

future_action:

rerun_buyer_follow_up_message

## Draft-Ready Operator Message

Assessment Factory Lite buyer follow-up no-response draft is ready for operator review.

## Response-Reply Operator Message

Assessment Factory Lite buyer follow-up response reply draft is ready for operator review.

## Blocked Operator Message

Assessment Factory Lite buyer follow-up message is blocked because the follow-up tracker is not active or response-received.

## Full No-Response Draft Example

A no-response draft requires:

tracker_status: active
buyer_response.response_status: no_response

Expected result:

message_status: draft_ready
recommended_action: review_buyer_follow_up_message
subject: Following Up on the Assessment Factory Lite Proposal Package
commercial_next_action.action: send_follow_up_if_no_response
send_policy.send_allowed: False

## Interested Response Reply Example

An interested response reply requires:

tracker_status: response_received
buyer_response.response_status: interested

Expected result:

message_status: response_reply_draft_ready
subject: Next Step: Assessment Factory Lite Scope Call
commercial_next_action.action: schedule_assessment_scope_call
next_action.action: review_buyer_response_reply

## Questions Response Reply Example

A questions response reply requires:

tracker_status: response_received
buyer_response.response_status: questions

Expected result:

message_status: response_reply_draft_ready
subject: Re: Assessment Factory Lite Proposal Questions
commercial_next_action.action: answer_buyer_questions

## Declined Response Reply Example

A declined response reply requires:

tracker_status: response_received
buyer_response.response_status: declined

Expected result:

message_status: response_reply_draft_ready
subject: Thank You for Reviewing Assessment Factory Lite
commercial_next_action.action: close_or_nurture_lead

## Blocked Tracker Example

If the source buyer follow-up tracker is blocked, the follow-up message becomes:

message_status: blocked
recommended_action: resolve_buyer_follow_up_message_gaps
source_follow_up_tracker.tracker_status: blocked
send_policy.send_allowed: False
send_blocked_reason: Follow-up tracker must be active or response-received before drafting can proceed.
next_action.action: resolve_buyer_follow_up_message_gaps

## Relationship to Buyer Follow-Up Tracker

The buyer follow-up tracker tracks buyer response status, follow-up schedule, and commercial next action.

The buyer follow-up message drafts human-operated follow-up language based on that tracker.

The buyer follow-up tracker answers:

Did the buyer respond, when should the operator follow up, and what commercial action comes next?

The buyer follow-up message answers:

What human-reviewed follow-up message should be prepared next?

## Relationship to Future Buyer Follow-Up Event Record

The buyer follow-up message does not record that the follow-up was sent.

A future buyer follow-up event record may use:

buyer follow-up message
recipient confirmation
human operator confirmation
follow-up delivery completion
send channel
send reference
follow-up outcome
audit notes

## Relationship to Future Assessment Scope Call Package

The buyer follow-up message does not schedule a scope call.

A future assessment scope call package may use:

interested buyer response
buyer follow-up tracker
buyer follow-up message
scope call agenda
evidence boundary
commercial next action
operator-approved scheduling language

## Commercial Boundary

The buyer follow-up message does not create a binding quote, binding sales contract, invoice, legal agreement, payment request, signed proposal, CRM opportunity, calendar invite, or production onboarding commitment.

The message only drafts follow-up language for operator review.

## Compliance Boundary

The Assessment Factory Lite Buyer Follow-Up Message does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It creates a deterministic follow-up message draft for a bounded paid-assessment conversation.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Buyer Follow-Up Message does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, live integrations, buyer delivery, send actions, email delivery, follow-up sending, CRM creation, calendar scheduling, scope call scheduling, or operator approval.

It does not perform automated follow-up.

It drafts a human-operated follow-up message only after a valid follow-up tracker exists.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt buyer follow-up language, but AI must not override deterministic delivery checks, evidence boundaries, approval requirements, operator notes, boundary notices, commercial terms, blocked follow-up behavior, follow-up message status, send policy, or operator approval gates without human-approved policy changes.
