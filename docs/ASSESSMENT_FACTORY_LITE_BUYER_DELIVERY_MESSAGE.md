# Assessment Factory Lite Buyer Delivery Message

## Purpose

The Assessment Factory Lite Buyer Delivery Message creates an operator-reviewed buyer-facing message draft from a buyer delivery package.

It does not send anything to a buyer.

It does not create a contract, invoice, signed proposal, payment request, production onboarding plan, or compliance certification.

It creates a deterministic message draft that the operator can review before any buyer-facing delivery.

## Capability Chain

Assessment Factory Lite Buyer Delivery Package
→ Buyer Delivery Message Service
→ Buyer Delivery Message Endpoint
→ Operator Review
→ Future Human-Operated Send Workflow
→ Future Delivery Event Record

## Service

### AssessmentFactoryLiteBuyerDeliveryMessageService

File:

backend/app/gagf/assessment_factory_lite_buyer_delivery_message_service.py

Purpose:

Build an operator-reviewed buyer delivery message draft.

The service can build the message from an existing buyer delivery package, proposal export package, Markdown export, formal proposal document, proposal-ready artifact, paid-assessment offer, buyer_context, operator_approval, or message_context.

## Endpoint

### Buyer Delivery Message Endpoint

POST /products/assessment-factory-lite/buyer-delivery-message

Purpose:

Returns a buyer delivery message draft.

The Operator Workstation can use this endpoint to prepare a buyer-facing delivery message after reviewing delivery package readiness.

## Request Contract

The request body may include:

delivery_package
export_package
export
document
proposal
offer
buyer_context
operator_approval
message_context

## Delivery Package Input

The delivery_package object may be supplied when the operator wants to build a message from a previously generated buyer delivery package.

If delivery_package is supplied, the message service uses it directly.

## Export Package Input

The export_package object may be supplied when the operator wants the service chain to build a buyer delivery package from an existing proposal export package and then generate the message draft.

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

The operator_approval object may be supplied when the operator wants to generate a send-ready draft.

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

Default recipient_role:

operations_leader

Default sender_name:

Assessment Factory Lite Operator

Default delivery_channel:

email_draft

## Response Contract

The buyer delivery message response includes:

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
source_delivery_package
delivery_summary
attachments
operator_review
boundary_notices
send_policy
next_action
operator_message
recommended_action

## Message Type

The message_type value is:

assessment_factory_lite_buyer_delivery_message

## Release Marker

The buyer delivery message object belongs to:

release:

assessment-factory-lite-proposal-export-package

version:

2.1.0

## Message Stage

The message_stage value is:

buyer_delivery_message_draft

## Message Status Values

The message_status value can be:

draft_ready
send_ready_draft
blocked

## Draft-Ready Status

draft_ready means:

The buyer delivery package is review_ready.
The proposal export package is ready.
The delivery message can be drafted.
The message cannot be sent yet because operator approvals are incomplete.

Default draft-ready value:

message_status: draft_ready

Default recommended action:

review_buyer_delivery_message

## Send-Ready Draft Status

send_ready_draft means:

The buyer delivery package is send_ready.
The required operator approvals are complete.
The message draft can move to final human review before sending.

Default send-ready next action:

review_and_send_buyer_delivery_message

## Blocked Status

blocked means:

The buyer delivery package is blocked, or one or more export, readiness, approval, or delivery checks failed.

Default blocked recommended action:

resolve_buyer_delivery_message_gaps

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

## Subject

Default subject format:

Assessment Factory Lite Proposal Package Ready for Review - assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf

The subject uses the delivery package PDF filename from the delivery manifest.

## Message Body

The message body includes:

greeting
proposal package introduction
Primary proposal artifact
Primary proposal artifact
primary proposal artifact
bounded paid-assessment workflow framing
non-binding boundary
review or send-ready action language
operator signature

## Default Draft-Ready Body Behavior

When the delivery package is review_ready, the message body states:

This draft still requires operator approval before it can be sent as buyer-facing material.

## Send-Ready Body Behavior

When the delivery package is send_ready, the message body asks the buyer to review the proposal package and confirm whether they want to discuss the bounded assessment scope and next steps.

## Non-Binding Message Boundary

The message body states that the package is non-binding and does not create a contract, invoice, compliance certification, or production onboarding commitment.

## Source Delivery Package

The source_delivery_package section preserves buyer delivery package identity.

Default values:

delivery_type: assessment_factory_lite_buyer_delivery_package
delivery_stage: buyer_delivery_package
delivery_status: review_ready
release: assessment-factory-lite-proposal-export-package
version: 2.1.0
recommended_action: review_buyer_delivery_package

## Delivery Summary

The delivery_summary section includes:

send_ready
review_ready
blocked
blocker_count
delivery_blockers

Default review-ready values:

send_ready: False
review_ready: True
blocked: False
blocker_count: 4

Default delivery blockers:

buyer_language_approved
commercial_terms_approved
evidence_boundary_approved
scope_approved

## Attachments

The attachments section includes:

proposal_markdown_export
proposal_pdf_export_object
proposal_export_manifest

## Proposal Markdown Export Attachment

Default values:

attachment: proposal_markdown_export
filename: assessment-factory-lite-proposal-approval-and-handoff-workflow.md
format: markdown
ready: True
buyer_facing: False
attachment_status: operator_review_required

## Proposal PDF Export Object Attachment

Default values:

attachment: proposal_pdf_export_object
filename: assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf
format: pdf
ready: True
buyer_facing: False
attachment_status: operator_review_required

## Proposal Export Manifest Attachment

Default values:

attachment: proposal_export_manifest
format: json
ready: True
buyer_facing: False
attachment_status: operator_review_required

## Operator Review

The operator_review section includes:

approval_status
scope_approved
evidence_boundary_approved
commercial_terms_approved
buyer_language_approved
delivery_blockers
review_required

Default review-ready values:

approval_status: operator_review_required
scope_approved: False
evidence_boundary_approved: False
commercial_terms_approved: False
buyer_language_approved: False
review_required: True

## Send Policy

The send_policy section includes:

send_allowed
send_blocked_reason
send_rule
automated_send_allowed
requires_human_operator

Default draft-ready values:

send_allowed: False
send_blocked_reason: Operator approval and delivery readiness are required before sending.
automated_send_allowed: False
requires_human_operator: True

Send rule:

Buyer delivery is allowed only when export package is ready and scope, evidence boundary, commercial terms, and buyer language are operator-approved.

## Automated Send Boundary

Automated sending is never allowed by this message service.

The service only creates a message draft.

Human operator review is always required before delivery.

## Draft-Ready Next Action

When message_status is draft_ready, next_action includes:

action: complete_operator_approval_before_sending

operator_instruction:

Complete operator approvals before sending this buyer delivery message draft.

future_action:

review_and_send_buyer_delivery_message

## Send-Ready Draft Next Action

When message_status is send_ready_draft, next_action includes:

action: review_and_send_buyer_delivery_message

operator_instruction:

Review the buyer delivery message, verify recipient details, confirm approved attachments, and send only through an approved human-operated channel.

future_action:

record_buyer_delivery_event

## Blocked Next Action

When message_status is blocked, next_action includes:

action: resolve_buyer_delivery_message_gaps

operator_instruction:

Resolve delivery package blockers before preparing a buyer-facing message.

future_action:

rerun_buyer_delivery_message

## Draft-Ready Operator Message

Assessment Factory Lite buyer delivery message draft is ready for operator review but not approved for sending.

## Send-Ready Operator Message

Assessment Factory Lite buyer delivery message draft is ready for final human review and sending.

## Blocked Operator Message

Assessment Factory Lite buyer delivery message is blocked because delivery package requirements are not satisfied.

## Full Operator Approval Example

A send-ready draft requires:

approval_status: operator_approved
scope_approved: True
evidence_boundary_approved: True
commercial_terms_approved: True
buyer_language_approved: True

Expected result:

message_status: send_ready_draft
delivery_summary.send_ready: True
operator_review.review_required: False
send_policy.send_allowed: True
send_policy.send_blocked_reason: empty string

## Failed Delivery Package Example

If the Markdown export changes:

Binding quote: False

to:

Binding quote: True

Then the delivery message becomes blocked.

Expected blocked values include:

message_status: blocked
recommended_action: resolve_buyer_delivery_message_gaps
delivery_summary.blocked: True
commercial_terms_present
send_policy.send_allowed: False

## Relationship to Buyer Delivery Package

The buyer delivery package determines whether delivery is review_ready, send_ready, or blocked.

The buyer delivery message creates the message draft based on that delivery status.

The buyer delivery package answers:

Can the export artifacts move toward buyer delivery, and what approvals are still missing?

The buyer delivery message answers:

What should the operator-reviewed buyer delivery message draft say?

## Relationship to Future Send Workflow

The buyer delivery message service does not send email, upload files, create a portal link, create a CRM record, or notify a buyer.

A future send workflow may use:

buyer delivery message
buyer delivery package
operator approval record
approved attachments
recipient email
send channel
delivery log

## Commercial Boundary

The buyer delivery message does not create a binding quote, binding sales contract, invoice, legal agreement, payment request, signed proposal, or production onboarding commitment.

The message remains non-binding until the operator approves final scope, price, payment terms, proposal expiration, evidence boundaries, exclusions, buyer-facing language, recipient details, and send channel.

## Compliance Boundary

The Assessment Factory Lite Buyer Delivery Message does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It creates a deterministic buyer delivery message draft for a bounded paid-assessment conversation.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Buyer Delivery Message does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, live integrations, buyer delivery, send actions, email delivery, or operator approval.

It helps the operator prepare buyer delivery language before any human-operated send workflow.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt buyer delivery language, but AI must not override deterministic delivery checks, evidence boundaries, approval requirements, operator notes, boundary notices, commercial terms, blocked delivery behavior, send policy, or operator approval gates without human-approved policy changes.

