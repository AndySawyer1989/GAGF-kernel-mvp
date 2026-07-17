# Assessment Factory Lite Buyer Follow-Up Tracker

## Purpose

The Assessment Factory Lite Buyer Follow-Up Tracker creates a deterministic follow-up tracker after a recorded human-operated buyer delivery event.

It does not send a follow-up message.

It does not create an automated email, CRM record, calendar event, invoice, contract, payment request, production onboarding action, or compliance certification.

It tracks buyer response status, follow-up schedule, commercial next action, follow-up checklist, blockers, boundary notices, audit notes, and next action.

## Capability Chain

Assessment Factory Lite Buyer Delivery Event Record
→ Buyer Follow-Up Tracker Service
→ Buyer Follow-Up Tracker Endpoint
→ Buyer Response Tracking
→ Future Buyer Follow-Up Message
→ Future Assessment Scope Call Package

## Service

### AssessmentFactoryLiteBuyerFollowUpTrackerService

File:

backend/app/gagf/assessment_factory_lite_buyer_follow_up_tracker_service.py

Purpose:

Build a buyer follow-up tracker from a recorded buyer delivery event.

The service can build the tracker from an existing event_record, buyer delivery message, buyer delivery package, proposal export package, Markdown export, formal proposal document, proposal-ready artifact, paid-assessment offer, buyer_context, operator_approval, message_context, event_context, or follow_up_context.

## Endpoint

### Buyer Follow-Up Tracker Endpoint

POST /products/assessment-factory-lite/buyer-follow-up-tracker

Purpose:

Returns a buyer follow-up tracker object.

The Operator Workstation can use this endpoint to track buyer response status after a recorded human-operated delivery event.

## Request Contract

The request body may include:

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

## Event Record Input

The event_record object may be supplied when the operator wants to create a follow-up tracker from a previously recorded buyer delivery event.

If event_record is supplied, the tracker service uses it directly.

## Message Input

The message object may be supplied when the operator wants the service chain to build a delivery event record from an existing buyer delivery message and then create the tracker.

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

The operator_approval object may be supplied when the operator wants the service chain to generate a send-ready buyer delivery message and recorded delivery event before creating the tracker.

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

## Response Contract

The buyer follow-up tracker response includes:

status
tracker_type
package_name
release
version
tracker_stage
tracker_status
tracker_id
created_at
source_event_record
buyer_response
follow_up_schedule
commercial_next_action
follow_up_checklist
follow_up_blockers
boundary_notices
audit_notes
next_action
operator_message
recommended_action

## Tracker Type

The tracker_type value is:

assessment_factory_lite_buyer_follow_up_tracker

## Release Marker

The buyer follow-up tracker object belongs to:

release:

assessment-factory-lite-proposal-export-package

version:

2.1.0

## Tracker Stage

The tracker_stage value is:

buyer_follow_up_tracker

## Tracker Status Values

The tracker_status value can be:

active
response_received
blocked

## Active Status

active means:

The source buyer delivery event record is recorded.
No buyer response has been recorded yet.
The tracker is waiting for buyer response.
A follow-up may be prepared after the due date.

Default active recommended action:

review_buyer_follow_up_tracker

## Response-Received Status

response_received means:

The source buyer delivery event record is recorded.
A buyer response status has been recorded as interested, questions, or declined.
The operator should review the response and choose the next commercial step.

Default response-received recommended action:

review_buyer_follow_up_tracker

## Blocked Status

blocked means:

The source buyer delivery event record is not recorded.

A follow-up tracker cannot become active until a recorded delivery event exists.

Default blocked recommended action:

resolve_buyer_follow_up_tracker_gaps

## Tracker ID

Default tracker_id:

buyer-follow-up-tracker-draft-001

Custom tracker_id example:

buyer-follow-up-tracker-001

## Created At

created_at may be supplied by follow_up_context.

Example:

2026-07-17T12:15:00+00:00

If created_at is not supplied, the service generates a UTC timestamp.

## Source Event Record

The source_event_record section preserves buyer delivery event identity.

Default recorded values:

event_type: assessment_factory_lite_buyer_delivery_event_record
event_stage: buyer_delivery_event_record
event_status: recorded
event_id: buyer-delivery-event-001
recorded_at: 2026-07-17T12:00:00+00:00
release: assessment-factory-lite-proposal-export-package
version: 2.1.0
recommended_action: review_buyer_delivery_event_record

## Buyer Response

The buyer_response section includes:

response_status
response_received
response_received_at
response_summary
buyer_questions
buyer_objections

## No Response State

Default no-response values:

response_status: no_response
response_received: False
response_received_at: empty string
response_summary: empty string
buyer_questions: []
buyer_objections: []

## Interested Response State

Interested response values may include:

response_status: interested
response_received: True
response_received_at: 2026-07-18T09:00:00+00:00
response_summary: Buyer wants to schedule a scope call.
buyer_questions: Can we start next week?
buyer_objections: []

Commercial next action:

schedule_assessment_scope_call

## Questions Response State

Questions response values may include:

response_status: questions
response_received: True
response_summary: Buyer has questions before approving next step.

Commercial next action:

answer_buyer_questions

## Declined Response State

Declined response values may include:

response_status: declined
response_received: True
response_summary: Buyer declined the assessment offer.

Commercial next action:

close_or_nurture_lead

## Follow-Up Schedule

The follow_up_schedule section includes:

follow_up_required
follow_up_due_at
follow_up_channel
follow_up_owner
reminder_status

Default values:

follow_up_required: True
follow_up_due_at: created_at plus three days
follow_up_channel: email
follow_up_owner: operator
reminder_status: pending

Example due date:

2026-07-20T12:15:00+00:00

## Commercial Next Action

The commercial_next_action section maps buyer response status to an operator action.

## No Response Commercial Action

If buyer_response_status is no_response, commercial_next_action is:

action: send_follow_up_if_no_response

description:

No buyer response recorded. Prepare a human-operated follow-up message after the due date.

## Interested Commercial Action

If buyer_response_status is interested, commercial_next_action is:

action: schedule_assessment_scope_call

description:

Buyer expressed interest. Schedule a scope call for the bounded paid assessment.

## Questions Commercial Action

If buyer_response_status is questions, commercial_next_action is:

action: answer_buyer_questions

description:

Buyer responded with questions. Prepare answers while preserving commercial and evidence boundaries.

## Declined Commercial Action

If buyer_response_status is declined, commercial_next_action is:

action: close_or_nurture_lead

description:

Buyer declined. Close the opportunity or preserve a light nurture note for later.

## Blocked Commercial Action

If tracker_status is blocked, commercial_next_action is:

action: resolve_delivery_event_before_follow_up

description:

Resolve delivery event record gaps before creating a buyer follow-up tracker.

## Follow-Up Checklist

The follow_up_checklist section includes:

delivery_event_recorded
recipient_confirmed
delivery_completed
follow_up_owner_assigned
buyer_response_classified

## Delivery Event Recorded Check

Purpose:

Buyer delivery event must be recorded.

Default recorded passed value:

True

## Recipient Confirmed Check

Purpose:

Recipient must be confirmed.

Default recorded passed value:

True

## Delivery Completed Check

Purpose:

Delivery must be completed.

Default recorded passed value:

True

## Follow-Up Owner Assigned Check

Purpose:

Follow-up owner must be assigned.

Default value:

operator

Default passed value:

True

## Buyer Response Classified Check

Purpose:

Buyer response status must be classified.

Allowed response statuses:

no_response
interested
questions
declined

Default passed value:

True

## Follow-Up Blockers

The follow_up_blockers list includes failed follow-up checklist items.

Default recorded blockers:

[]

Blocked tracker blockers may include:

delivery_event_recorded
recipient_confirmed
delivery_completed

## Boundary Notices

The buyer follow-up tracker preserves boundary notices from the delivery event and source chain.

Required boundary concepts include:

commercial_boundary
evidence_boundary
pdf_boundary
constitutional_boundary

## Audit Notes

The audit_notes section preserves supplied audit notes and adds deterministic tracker notes.

Active tracker audit notes include:

buyer_follow_up_tracker_active
automated_follow_up_not_performed

Response-received audit note:

buyer_response_recorded

Blocked tracker audit note:

recorded_delivery_event_required

Every tracker includes:

automated_follow_up_not_performed

## Active Next Action

When tracker_status is active, next_action includes:

action: monitor_for_buyer_response

operator_instruction:

Monitor for buyer response and prepare follow-up after the due date if no response is recorded.

future_action:

prepare_buyer_follow_up_message

## Response-Received Next Action

When tracker_status is response_received, next_action includes:

action: review_buyer_response

operator_instruction:

Review buyer response, update commercial next action, and prepare the next human-operated step.

future_action:

prepare_assessment_scope_call_or_response

## Blocked Next Action

When tracker_status is blocked, next_action includes:

action: resolve_buyer_follow_up_tracker_gaps

operator_instruction:

Resolve delivery event, recipient, or completion gaps before tracking buyer follow-up.

future_action:

rerun_buyer_follow_up_tracker

## Active Operator Message

Assessment Factory Lite buyer follow-up tracker is active and waiting for buyer response.

## Response-Received Operator Message

Assessment Factory Lite buyer follow-up tracker has recorded a buyer response for operator review.

## Blocked Operator Message

Assessment Factory Lite buyer follow-up tracker is blocked because the delivery event is not recorded.

## Full Active Tracker Example

An active tracker requires:

event_status: recorded
recipient_confirmed: True
delivery_completed: True
buyer_response_status: no_response

Expected result:

tracker_status: active
recommended_action: review_buyer_follow_up_tracker
buyer_follow_up_tracker_active
automated_follow_up_not_performed
next_action.action: monitor_for_buyer_response

## Interested Response Example

If buyer_response_status is interested, the tracker becomes:

tracker_status: response_received
buyer_response.response_status: interested
buyer_response.response_received: True
commercial_next_action.action: schedule_assessment_scope_call
buyer_response_recorded

## Questions Response Example

If buyer_response_status is questions, the tracker becomes:

tracker_status: response_received
buyer_response.response_status: questions
commercial_next_action.action: answer_buyer_questions

## Declined Response Example

If buyer_response_status is declined, the tracker becomes:

tracker_status: response_received
buyer_response.response_status: declined
commercial_next_action.action: close_or_nurture_lead

## Blocked Delivery Event Example

If the source buyer delivery event record is blocked, the tracker becomes:

tracker_status: blocked
recommended_action: resolve_buyer_follow_up_tracker_gaps
source_event_record.event_status: blocked
delivery_event_recorded
recipient_confirmed
recorded_delivery_event_required
next_action.action: resolve_buyer_follow_up_tracker_gaps

## Relationship to Buyer Delivery Event Record

The buyer delivery event record captures whether a human-operated delivery action was confirmed, completed, and recorded.

The buyer follow-up tracker tracks what happens after that delivery event.

The buyer delivery event record answers:

Was a send-ready message delivered by a human operator, and what delivery metadata should be preserved?

The buyer follow-up tracker answers:

Did the buyer respond, when should the operator follow up, and what commercial action comes next?

## Relationship to Future Buyer Follow-Up Message

The buyer follow-up tracker does not create the follow-up message yet.

A future buyer follow-up message service may use:

buyer follow-up tracker
buyer response status
follow-up due date
commercial next action
buyer questions
buyer objections
operator-approved follow-up language

## Relationship to Future Assessment Scope Call Package

The buyer follow-up tracker does not schedule a scope call yet.

A future assessment scope call package may use:

buyer follow-up tracker
interested buyer response
scope call notes
proposed agenda
evidence boundary
commercial next action
operator-approved scheduling language

## Commercial Boundary

The buyer follow-up tracker does not create a binding quote, binding sales contract, invoice, legal agreement, payment request, signed proposal, CRM opportunity, or production onboarding commitment.

The tracker only records follow-up readiness, response state, and next commercial action.

## Compliance Boundary

The Assessment Factory Lite Buyer Follow-Up Tracker does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It creates a deterministic follow-up tracker for a bounded paid-assessment conversation.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Buyer Follow-Up Tracker does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, live integrations, buyer delivery, send actions, email delivery, follow-up sending, CRM creation, calendar scheduling, or operator approval.

It does not perform automated follow-up.

It tracks a human-operated follow-up process only after a recorded delivery event.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or summarize buyer follow-up status, but AI must not override deterministic delivery checks, evidence boundaries, approval requirements, operator notes, boundary notices, commercial terms, blocked follow-up behavior, follow-up status, or operator approval gates without human-approved policy changes.
