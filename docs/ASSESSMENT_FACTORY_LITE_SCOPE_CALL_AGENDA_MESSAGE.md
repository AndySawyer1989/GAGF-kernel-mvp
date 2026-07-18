# Assessment Factory Lite Scope Call Agenda Message

## Release

Release:

assessment-factory-lite-scope-call-conversion

Version:

2.3.0

Story:

US-272 — Assessment Factory Lite Scope Call Agenda Message Documentation

## Purpose

The Assessment Factory Lite Scope Call Agenda Message prepares a human-reviewable buyer-facing agenda message after an assessment scope call package is ready.

The message helps the operator move from buyer interest to a bounded scope-call conversation.

The message does not send email.

The message does not schedule a meeting.

The message does not create a calendar invite.

The message does not start paid assessment work.

The message does not create a contract, invoice, payment request, or production onboarding commitment.

## Endpoint

POST /products/assessment-factory-lite/scope-call-agenda-message

## Service

AssessmentFactoryLiteScopeCallAgendaMessageService

Service file:

backend/app/gagf/assessment_factory_lite_scope_call_agenda_message_service.py

Endpoint file:

backend/app/main.py

## Message Type

assessment_factory_lite_scope_call_agenda_message

## Message Stage

scope_call_agenda_message_draft

## Source Package

The message is generated from an Assessment Factory Lite assessment scope call package.

Expected source package:

assessment_factory_lite_assessment_scope_call_package

Source package release:

assessment-factory-lite-buyer-delivery-follow-up

Source package version:

2.2.0

The source scope call package must be ready before the agenda message can become draft_ready.

## Output Release

The scope call agenda message uses its own object contract:

release: assessment-factory-lite-scope-call-conversion
version: 2.3.0

This preserves layered object versioning.

The source scope call package remains on release assessment-factory-lite-buyer-delivery-follow-up and version 2.2.0.

## Supported Inputs

The service accepts either a ready scope_call_package directly or enough upstream context to build one.

Supported input keys include:

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

## Scope Call Message Context

The scope_call_message_context may customize message-facing metadata.

Supported context fields include:

recipient_role
email_status
sender_name
subject
delivery_channel

Default recipient_role:

operations_leader

Default email_status:

operator_to_provide

Default sender_name:

Assessment Factory Lite Operator

Default subject:

Assessment Factory Lite Scope Call Agenda

Default delivery_channel:

email_draft

## Core Output Fields

The scope call agenda message returns:

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
source_scope_call_package
agenda_summary
buyer_response_summary
commercial_next_action
evidence_boundary
commercial_boundary
scheduling_boundary
operator_review
send_policy
boundary_notices
audit_notes
next_action
operator_message
recommended_action

## Message Status

The service supports two message statuses.

draft_ready:

The source scope call package is ready.

blocked:

The source scope call package is not ready.

## Draft Ready Conditions

The message becomes draft_ready when the source assessment scope call package has:

package_status: ready

The ready path normally requires:

buyer response is interested
commercial next action supports schedule_assessment_scope_call
follow-up event was recorded
source delivery event was recorded
required scope-call checklist items are satisfied

## Blocked Conditions

The message becomes blocked when the source assessment scope call package is not ready.

Common blockers include:

follow-up event not recorded
buyer not interested
commercial action does not support scope-call preparation
scope-call agenda unavailable
operator review required but not satisfied
upstream proposal export package invalid
delivery package blocked
delivery event missing
follow-up tracker blocked
follow-up message blocked

## Agenda Summary

The agenda_summary includes:

agenda_item_count
agenda_items
all_items_required
agenda_owner

Default agenda items:

confirm workflow scope
confirm evidence sources
confirm evidence boundaries
confirm timeline and deliverables
confirm commercial terms
confirm next approval step

## Message Body

The draft_ready message body includes:

thank-you language
scope-call agenda
workflow scope confirmation
evidence source confirmation
evidence boundary reminder
timeline and deliverables confirmation
commercial terms confirmation
next approval step confirmation
regulated data warning
secrets and credentials warning
personal data warning
customer records warning
non-binding commercial boundary
no contract boundary
no invoice boundary
no payment request boundary
no calendar invite boundary
no paid assessment start boundary
no production onboarding boundary
human operator scheduling requirement
current commercial next action

## Blocked Message Body

The blocked message body explains that the agenda message is not ready because the source scope-call package is not ready.

It instructs the operator to resolve package blockers before preparing buyer-facing scope-call agenda language.

The blocked body also preserves the same non-binding and non-scheduling boundaries.

## Recipient Contract

The recipient object includes:

recipient_type
recipient_role
email_required
email_status

Default recipient:

recipient_type: buyer_role
recipient_role: operations_leader
email_required: true
email_status: operator_to_provide

## Sender Contract

The sender object includes:

sender_type
sender_name
signature_required

Default sender:

sender_type: operator
sender_name: Assessment Factory Lite Operator
signature_required: true

## Source Scope Call Package Contract

The source_scope_call_package summary includes:

package_type
package_stage
package_status
package_id
created_at
release
version
recommended_action

This preserves traceability without copying the entire upstream package into the message artifact.

## Operator Review

The operator_review object includes:

package_status
package_blockers
review_required
human_operator_required
approved_for_sending
approved_for_scheduling
message_ready

The message is never automatically approved for sending.

The message is never automatically approved for scheduling.

Human operator review is always required.

## Send Policy

The send_policy object includes:

send_allowed
send_blocked_reason
automated_send_allowed
calendar_invite_allowed
automatic_scheduling_allowed
requires_human_operator
send_rule

Required values:

send_allowed: false
automated_send_allowed: false
calendar_invite_allowed: false
automatic_scheduling_allowed: false
requires_human_operator: true

## Draft Ready Send Rule

When draft_ready, the send rule states that scope-call agenda messages are draft-only and must be reviewed, approved, and sent by a human operator.

## Blocked Send Rule

When blocked, the send policy states that the scope-call package must be ready before agenda message drafting can proceed.

## Audit Notes

When draft_ready, audit notes include:

scope_call_agenda_message_draft_ready
automated_scope_call_sending_not_performed
automatic_scheduling_not_performed

When blocked, audit notes include:

scope_call_agenda_message_blocked
automated_scope_call_sending_not_performed
automatic_scheduling_not_performed

## Next Action

When draft_ready:

action: review_scope_call_agenda_message
future_action: record_scope_call_agenda_message_event

When blocked:

action: resolve_scope_call_agenda_message_gaps
future_action: rerun_scope_call_agenda_message

## Recommended Action

When draft_ready:

review_scope_call_agenda_message

When blocked:

resolve_scope_call_agenda_message_gaps

## Human Operator Boundary

The scope call agenda message is a draft artifact.

A human operator must review it before any buyer-facing action.

A human operator must approve the final message.

A human operator must send the message.

A human operator must schedule any actual meeting outside the automatic service.

## Scheduling Boundary

The scope call agenda message does not schedule the scope call.

The scope call agenda message does not create a calendar invite.

The scope call agenda message does not reserve time.

The scope call agenda message does not confirm buyer availability.

The message may reference scheduling, but only as a human-operated next step.

## Commercial Boundary

The scope call agenda message is non-binding.

It is not a quote.

It is not a contract.

It is not an invoice.

It is not a payment request.

It is not a signed proposal.

It is not a statement of work.

It is not paid assessment authorization.

It is not production onboarding.

## Evidence Boundary

The message tells the buyer not to share:

regulated production data
secrets
credentials
unapproved personal data
unapproved customer records

Allowed evidence examples include:

non-sensitive sample workflow data
redacted operational examples
operator-approved buyer-provided context

## Compliance Boundary

The message does not certify any compliance state.

It does not certify FedRAMP High.

It does not certify HIPAA compliance.

It does not certify SOC 2 readiness.

It does not certify WCAG accessibility.

It does not certify production readiness.

## GAGF Boundary

The deterministic GAGF Kernel remains authoritative.

AI may assist with drafting or summarization in future versions.

AI must not override deterministic scope-call readiness, evidence boundaries, scheduling boundaries, send policy, commercial terms, or operator approval gates without human-approved policy changes.

## Route Preservation

The endpoint must preserve the current system release marker.

The current system version endpoint remains:

version: 2.2.0
release: assessment-factory-lite-buyer-delivery-follow-up
sprint: 5.0
status: complete

The new message object may use version 2.3.0 without changing the system release marker until a later release-marker story.

## Product Meaning

This story starts the scope-call conversion layer.

Assessment Factory Lite can now prepare a scope-call agenda message after buyer interest has been recorded.

This turns buyer follow-up into a practical next commercial step while preserving human approval.

## Next Story

US-273 — Assessment Factory Lite Scope Call Agenda Message Release Marker
