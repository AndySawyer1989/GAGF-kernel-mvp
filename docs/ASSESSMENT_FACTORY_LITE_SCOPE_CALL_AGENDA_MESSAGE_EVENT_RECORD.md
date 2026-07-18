# Assessment Factory Lite Scope Call Agenda Message Event Record

## Release

Release:

assessment-factory-lite-scope-call-conversion

Version:

2.3.0

Story:

US-276 — Assessment Factory Lite Scope Call Agenda Message Event Record Documentation

## Purpose

The Assessment Factory Lite Scope Call Agenda Message Event Record captures a human-operated buyer communication action after a scope-call agenda message has been prepared.

The event record proves that the agenda message action was controlled by a human operator.

It records the agenda message action without sending email automatically.

It records the agenda message action without creating a calendar invite.

It records the agenda message action without scheduling a meeting.

It records the agenda message action without starting paid assessment work.

It preserves the commercial, evidence, scheduling, and human-approval boundaries of the scope-call conversion layer.

## Endpoint

POST /products/assessment-factory-lite/scope-call-agenda-message-event-record

## Service

AssessmentFactoryLiteScopeCallAgendaMessageEventRecordService

Service file:

backend/app/gagf/assessment_factory_lite_scope_call_agenda_message_event_record_service.py

Endpoint file:

backend/app/main.py

## Event Type

assessment_factory_lite_scope_call_agenda_message_event_record

## Event Stage

scope_call_agenda_message_event_record

## Source Message

The event record is generated from a scope-call agenda message.

Expected source message:

assessment_factory_lite_scope_call_agenda_message

Source message release:

assessment-factory-lite-scope-call-conversion

Source message version:

2.3.0

The source message must be draft_ready before the event can be recorded.

## Output Release

The event record uses the scope-call conversion object contract:

release: assessment-factory-lite-scope-call-conversion
version: 2.3.0

This preserves the same conversion-layer contract as the scope-call agenda message.

## Supported Inputs

The service accepts either a source scope_call_agenda_message directly or enough upstream context to build one.

Supported input keys include:

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

## Scope Call Message Event Context

The scope_call_message_event_context records the human-operated action.

Supported context fields include:

event_id
recorded_at
human_operator_confirmed
agenda_message_sent
recipient_confirmed
email_status
delivery_channel

Default event_id:

scope-call-agenda-message-event-draft-001

## Core Output Fields

The scope call agenda message event record returns:

status
event_type
package_name
release
version
event_stage
event_status
event_id
recorded_at
source_scope_call_agenda_message
message_channel
recipient_status
message_summary
send_policy_snapshot
operator_review_snapshot
scope_call_package_summary
agenda_summary
commercial_next_action
scheduling_boundary
commercial_boundary
evidence_boundary
event_checklist
event_blockers
boundary_notices
audit_notes
next_action
operator_message
recommended_action

## Event Statuses

The service supports four event statuses.

recorded:

The source message is draft_ready, a human operator confirmed the action, and the agenda message was completed.

pending_human_confirmation:

The source message is draft_ready, but human operator confirmation is missing.

pending_agenda_message_completion:

The source message is draft_ready and human confirmation exists, but the agenda message action is not complete.

blocked:

The source message is not draft_ready.

## Recorded Conditions

The event becomes recorded when:

message_draft_ready is true
human_operator_confirmed is true
agenda_message_sent is true
recipient_confirmed is true
automated_send_not_used is true
calendar_invite_not_created is true
automatic_scheduling_not_used is true

## Pending Human Confirmation Conditions

The event becomes pending_human_confirmation when:

source message is draft_ready
human_operator_confirmed is false or missing

## Pending Completion Conditions

The event becomes pending_agenda_message_completion when:

source message is draft_ready
human_operator_confirmed is true
agenda_message_sent is false or missing

## Blocked Conditions

The event becomes blocked when:

source agenda message is blocked
scope-call package is not ready
buyer is not interested
commercial action does not support scope-call preparation
upstream proposal export package is invalid
agenda message cannot be drafted

## Source Scope Call Agenda Message Summary

The source_scope_call_agenda_message summary includes:

message_type
message_stage
message_status
release
version
delivery_channel
subject
recommended_action

This preserves traceability to the source agenda message without copying the entire message artifact.

## Message Channel

The message_channel object includes:

delivery_channel
automated_send_used
calendar_invite_created
automatic_scheduling_used
human_operated

Required boundary values:

automated_send_used: false
calendar_invite_created: false
automatic_scheduling_used: false
human_operated: true

## Recipient Status

The recipient_status object includes:

recipient_type
recipient_role
email_required
email_status
recipient_confirmed

The recipient confirmation is supplied by the human-operated event context.

## Message Summary

The message_summary object includes:

subject
body_available
body_character_count
agenda_item_count
non_binding_notice_included
no_calendar_invite_notice_included
human_operator_notice_included

These fields confirm that the source message included the required commercial, scheduling, and human-operator boundaries.

## Policy Snapshots

The event record snapshots the source message policy objects.

send_policy_snapshot preserves:

send_allowed
send_blocked_reason
automated_send_allowed
calendar_invite_allowed
automatic_scheduling_allowed
requires_human_operator
send_rule

operator_review_snapshot preserves:

package_status
package_blockers
review_required
human_operator_required
approved_for_sending
approved_for_scheduling
message_ready

## Scope Call Package Summary

The event record preserves the source scope-call package summary through:

scope_call_package_summary

The summary should show whether the source package was ready.

## Agenda Summary

The event record preserves agenda metadata through:

agenda_summary

The agenda summary includes agenda item count, agenda items, all-items-required status, and agenda owner.

## Commercial Next Action

The event record carries forward:

commercial_next_action

The expected ready-path commercial action is:

schedule_assessment_scope_call

The event record does not perform scheduling.

## Event Checklist

The event_checklist includes:

message_draft_ready
human_operator_confirmed
agenda_message_sent
recipient_confirmed
automated_send_not_used
calendar_invite_not_created
automatic_scheduling_not_used

## Event Blockers

The event_blockers list includes any checklist fields that are not true.

Common blockers include:

message_draft_ready
human_operator_confirmed
agenda_message_sent
recipient_confirmed

## Audit Notes

When recorded, audit notes include:

scope_call_agenda_message_event_recorded
human_operator_confirmed_agenda_message_action
automated_scope_call_sending_not_performed
automatic_scheduling_not_performed

When pending_human_confirmation, audit notes include:

scope_call_agenda_message_event_pending_human_confirmation
automated_scope_call_sending_not_performed
automatic_scheduling_not_performed

When pending_agenda_message_completion, audit notes include:

scope_call_agenda_message_event_pending_completion
automated_scope_call_sending_not_performed
automatic_scheduling_not_performed

When blocked, audit notes include:

scope_call_agenda_message_event_blocked
automated_scope_call_sending_not_performed
automatic_scheduling_not_performed

## Next Action

When recorded:

action: prepare_scope_call_event_record
future_action: build_scope_call_event_record

When pending_human_confirmation:

action: confirm_scope_call_agenda_message_event
future_action: rerun_scope_call_agenda_message_event_record

When pending_agenda_message_completion:

action: complete_scope_call_agenda_message_action
future_action: rerun_scope_call_agenda_message_event_record

When blocked:

action: resolve_scope_call_agenda_message_event_gaps
future_action: rerun_scope_call_agenda_message_event_record

## Recommended Action

When recorded:

prepare_scope_call_event_record

When not recorded:

resolve_scope_call_agenda_message_event_gaps

## Human Operator Boundary

The event record is a human-operated evidence artifact.

It records that a human operator controlled the buyer-facing agenda message action.

It does not approve automatic sending.

It does not approve automatic scheduling.

It does not approve paid assessment start.

It does not approve production onboarding.

## Send Boundary

The event record must preserve that automated sending was not used.

The source scope-call agenda message remains draft-only until reviewed and sent by a human operator.

The event record can record a human-operated send action, but it must not perform the send action itself.

## Scheduling Boundary

The event record must preserve that no calendar invite was created automatically.

The event record must preserve that automatic scheduling was not used.

The event record can support a later scope-call event record, but it does not schedule the scope call.

## Commercial Boundary

The event record is not a contract.

It is not a contract.

It is not an invoice.

It is not a payment request.

It is not a statement of work.

It is not paid assessment authorization.

It is not production onboarding.

It records only the human-operated agenda message action.

## Evidence Boundary

Allowed evidence examples include:

non-sensitive sample workflow data
redacted operational examples
operator-approved buyer-provided context

Excluded evidence examples include:

regulated production data
secrets
credentials
unapproved personal data
unapproved customer records

## Compliance Boundary

The event record does not certify any compliance state.

It does not certify FedRAMP High.

It does not certify HIPAA compliance.

It does not certify SOC 2 readiness.

It does not certify WCAG accessibility.

It does not certify production readiness.

## GAGF Boundary

The deterministic GAGF Kernel remains authoritative.

AI may assist with summarizing the event in future versions.

AI must not override deterministic event status, send policy, scheduling boundaries, commercial terms, evidence boundaries, or operator approval gates without human-approved policy changes.

## Route Preservation

The endpoint must preserve the current system release marker.

The current system version endpoint remains:

version: 2.3.0
release: assessment-factory-lite-scope-call-conversion
sprint: 5.0
status: complete

## Product Meaning

This story gives Assessment Factory Lite an evidence record for human-operated scope-call agenda communication.

The product can now move from agenda message drafting to recorded agenda-message action.

This keeps the commercial workflow auditable without pretending the system automatically sent email or scheduled a meeting.

## Next Story

US-277 — Assessment Factory Lite Scope Call Agenda Message Event Record Release Marker

