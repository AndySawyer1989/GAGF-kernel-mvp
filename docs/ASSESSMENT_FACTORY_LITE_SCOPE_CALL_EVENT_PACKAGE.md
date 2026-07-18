# Assessment Factory Lite Scope Call Event Package

## Release

Release:

assessment-factory-lite-scope-call-conversion

Version:

2.3.0

Story:

US-280 — Assessment Factory Lite Scope Call Event Package Documentation

## Purpose

The Assessment Factory Lite Scope Call Event Package is a governed readiness object.

It is created after the scope-call agenda message event has been recorded.

It determines whether the workflow is ready to move toward a human-operated scope call event record.

It does not schedule the call.

It does not create a calendar invite.

It does not send email.

It does not authorize paid assessment work.

It does not execute a contract.

It does not start production onboarding.

It preserves deterministic GAGF governance, human approval, commercial boundaries, scheduling boundaries, and evidence boundaries.

## Endpoint

POST /products/assessment-factory-lite/scope-call-event-package

## Service

AssessmentFactoryLiteScopeCallEventPackageService

Service file:

backend/app/gagf/assessment_factory_lite_scope_call_event_package_service.py

Endpoint file:

backend/app/main.py

## Event Type

assessment_factory_lite_scope_call_event_package

## Package Stage

scope_call_event_package

## Output Release

The package uses the scope-call conversion contract:

release: assessment-factory-lite-scope-call-conversion
version: 2.3.0

The package preserves the current system release marker:

version: 2.3.0
release: assessment-factory-lite-scope-call-conversion
sprint: 5.0
status: complete

## Source Object

The package is built from a scope-call agenda message event record.

Expected source object:

assessment_factory_lite_scope_call_agenda_message_event_record

Expected source event stage:

scope_call_agenda_message_event_record

Expected source status for readiness:

recorded

If the source event record is not recorded, the scope-call event package cannot become ready_for_scope_call.

## Supported Inputs

The service accepts either a source scope_call_agenda_message_event_record directly or enough upstream context to build one.

Supported input keys include:

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

## Scope Call Event Context

The scope_call_event_context provides package identity and preparation metadata.

Supported fields include:

scope_call_id
prepared_at
operator_approved
human_operator_confirmed

Default scope_call_id:

scope-call-event-package-draft-001

Default prepared_at:

not_recorded

## Core Output Fields

The scope-call event package returns:

status
event_type
package_name
release
version
package_stage
package_status
scope_call_id
prepared_at
source_scope_call_agenda_message_event_record
buyer_readiness
agenda_confirmation
human_approval
readiness_checklist
readiness_blockers
readiness_score
scope_call_package_summary
agenda_summary
message_channel
recipient_status
commercial_next_action
scheduling_boundary
commercial_boundary
evidence_boundary
governance_boundary
boundary_notices
audit_notes
next_action
operator_message
recommended_action

## Package Statuses

The service supports five package statuses.

ready_for_scope_call:

The agenda message event was recorded, the buyer is ready, the recipient was confirmed, the human operator approved readiness, and all readiness checklist boundaries pass.

pending_agenda_message_event:

The source agenda message event is not yet recorded.

pending_buyer_confirmation:

The source event is recorded, but buyer readiness is not confirmed.

pending_human_approval:

The source event is recorded and buyer readiness is present, but package-level human operator approval is missing.

blocked:

The source event is blocked or another readiness boundary failed.

## Ready Conditions

The package becomes ready_for_scope_call when:

agenda_message_event_recorded is true
agenda_ready is true
buyer_ready_for_scope_call is true
recipient_confirmed is true
human_operator_approved is true
automated_send_not_used is true
calendar_invite_not_created is true
automatic_scheduling_not_used is true
paid_assessment_not_authorized is true
contract_not_executed is true
scope_call_not_scheduled_by_system is true

## Pending Agenda Message Event Conditions

The package becomes pending_agenda_message_event when:

source agenda message event record is not recorded
agenda message event is pending human confirmation
agenda message event is pending agenda message completion

## Pending Buyer Confirmation Conditions

The package becomes pending_buyer_confirmation when:

buyer_response_status is not interested
buyer_ready_for_scope_call is false
buyer interest requires additional confirmation

## Pending Human Approval Conditions

The package becomes pending_human_approval when:

operator_approved is false
approval_status is operator_review_required
human operator readiness confirmation is missing

## Blocked Conditions

The package becomes blocked when:

source agenda message event record is blocked
upstream proposal export is invalid
source scope-call package is blocked
commercial or evidence boundaries fail
readiness blockers remain after deterministic evaluation

## Source Event Record Summary

The source_scope_call_agenda_message_event_record object includes:

event_type
event_stage
event_status
release
version
event_id
recorded_at
recommended_action

This preserves traceability without copying the full upstream event record.

## Buyer Readiness

The buyer_readiness object includes:

buyer_response_status
buyer_interested
buyer_questions
buyer_questions_count
buyer_ready_for_scope_call
source_recipient_confirmed

The ready-path buyer_response_status is:

interested

Buyer questions may exist without blocking the package if buyer readiness is still confirmed.

## Agenda Confirmation

The agenda_confirmation object includes:

agenda_message_event_recorded
agenda_message_sent
recipient_confirmed
agenda_item_count
agenda_items_required
agenda_ready

The agenda is ready only when the agenda message event was recorded, the agenda message was sent or confirmed by the operator, and the recipient was confirmed.

## Human Approval

The human_approval object includes:

approval_status
operator_approved
human_operator_required
scope_call_execution_approved
automatic_scheduling_approved
paid_assessment_approved
contract_execution_approved

Required boundary values:

human_operator_required: true
scope_call_execution_approved: false
automatic_scheduling_approved: false
paid_assessment_approved: false
contract_execution_approved: false

The package can approve readiness without approving execution.

## Readiness Checklist

The readiness_checklist includes:

agenda_message_event_recorded
agenda_ready
buyer_ready_for_scope_call
recipient_confirmed
human_operator_approved
automated_send_not_used
calendar_invite_not_created
automatic_scheduling_not_used
paid_assessment_not_authorized
contract_not_executed
scope_call_not_scheduled_by_system

## Readiness Blockers

The readiness_blockers list contains any readiness checklist item that is not true.

Common blockers include:

agenda_message_event_recorded
agenda_ready
buyer_ready_for_scope_call
recipient_confirmed
human_operator_approved

## Readiness Score

The readiness_score object includes:

passed
total
score
ready

For a ready package:

passed: 11
total: 11
score: 1.0
ready: true

The readiness score is advisory evidence for the operator, but deterministic package_status remains authoritative.

## Scope Call Package Summary

The package carries forward:

scope_call_package_summary

This preserves package readiness context from the prior scope-call package layer.

## Agenda Summary

The package carries forward:

agenda_summary

This preserves agenda item count, required agenda status, and agenda owner from the prior agenda message layer.

## Message Channel

The package carries forward:

message_channel

Required boundary values include:

automated_send_used: false
calendar_invite_created: false
automatic_scheduling_used: false
human_operated: true

## Recipient Status

The package carries forward:

recipient_status

The recipient confirmation supports buyer readiness and scope-call preparation.

## Commercial Next Action

When ready_for_scope_call:

action: prepare_human_operated_scope_call
allowed_next_stage: scope_call_event_record
automatic_execution_allowed: false
human_operator_required: true

When not ready:

action: resolve_scope_call_event_package_gaps
allowed_next_stage: scope_call_event_package_review
automatic_execution_allowed: false
human_operator_required: true

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

contract_created
contract_executed
invoice_created
payment_requested
paid_assessment_authorized
production_onboarding_authorized
scope_call_is_non_binding

Required values:

contract_created: false
contract_executed: false
invoice_created: false
payment_requested: false
paid_assessment_authorized: false
production_onboarding_authorized: false
scope_call_is_non_binding: true

## Evidence Boundary

Allowed evidence examples include:

non_sensitive_sample_workflow_data
redacted_operational_examples
operator_approved_buyer_context

Excluded evidence examples include:

regulated_production_data
secrets
credentials
unapproved_personal_data
unapproved_customer_records

Evidence review is required before paid assessment authorization.

## Governance Boundary

The governance_boundary object includes:

deterministic_status_required
gagf_kernel_authoritative
ai_override_allowed
human_boundary_required
release_marker_preserved

Required values:

deterministic_status_required: true
gagf_kernel_authoritative: true
ai_override_allowed: false
human_boundary_required: true
release_marker_preserved: true

## Boundary Notices

The package emits these boundary notices:

scope_call_event_package_does_not_schedule_call
scope_call_event_package_does_not_create_calendar_invite
scope_call_event_package_does_not_authorize_paid_assessment
scope_call_event_package_does_not_execute_contract
scope_call_event_package_requires_human_operator

## Audit Notes

All package statuses include:

scope_call_event_package_built
automatic_scheduling_not_performed
calendar_invite_not_created
paid_assessment_not_authorized
contract_not_executed

When ready_for_scope_call, audit notes include:

scope_call_event_package_ready

When pending_agenda_message_event, audit notes include:

scope_call_event_package_pending_agenda_message_event

When pending_buyer_confirmation, audit notes include:

scope_call_event_package_pending_buyer_confirmation

When pending_human_approval, audit notes include:

scope_call_event_package_pending_human_approval

When blocked, audit notes include:

scope_call_event_package_blocked

## Next Action

When ready_for_scope_call:

action: prepare_scope_call_event_record
future_action: build_scope_call_event_record

When pending_agenda_message_event:

action: record_scope_call_agenda_message_event
future_action: rerun_scope_call_event_package

When pending_buyer_confirmation:

action: confirm_buyer_scope_call_readiness
future_action: rerun_scope_call_event_package

When pending_human_approval:

action: confirm_human_operator_approval
future_action: rerun_scope_call_event_package

When blocked:

action: resolve_scope_call_event_package_gaps
future_action: rerun_scope_call_event_package

## Recommended Action

When ready_for_scope_call:

prepare_scope_call_event_record

When not ready:

resolve_scope_call_event_package_gaps

## Human Operator Boundary

The package is a readiness object only.

It requires a human operator.

It may confirm readiness for a scope-call event record.

It does not execute the scope call.

It does not schedule the call.

It does not send automated communication.

It does not create a calendar invite.

It does not approve paid work.

It does not execute a contract.

## GAGF Meaning

The package represents the GAGF pattern:

Evidence → Readiness → Boundary Check → Human Approval → Governed Next Action

The object is not a generic DTO.

It is a deterministic governance checkpoint.

It proves the workflow can move toward a human-operated scope call event only when readiness conditions pass.

## Product Meaning

This package moves Assessment Factory Lite from buyer communication tracking into governed pre-engagement readiness.

It is the final readiness layer before recording the actual human-operated scope call event.

It keeps the product commercially useful without overclaiming automation, contract authority, or paid assessment authorization.

## Next Story

US-281 — Assessment Factory Lite Scope Call Event Package Release Marker
