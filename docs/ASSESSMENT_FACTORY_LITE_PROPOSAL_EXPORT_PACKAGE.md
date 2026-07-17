# Assessment Factory Lite Proposal Export Package

## Purpose

The Assessment Factory Lite Proposal Export Package bundles the formal proposal export artifacts into one guarded package object.

It combines the Markdown export summary, PDF readiness result, PDF export object summary, operator approval gate, export manifest, boundary notices, blocking issues, and next action.

The package is designed for operator review before preparing buyer delivery.

## Capability Chain

Assessment Factory Lite Proposal Package
→ Formal Proposal Document
→ Formal Proposal Markdown Export
→ Formal Proposal PDF Readiness
→ Formal Proposal PDF Export Object
→ Proposal Export Package
→ Operator Review
→ Future Buyer Delivery Package

## Service

### AssessmentFactoryLiteProposalExportPackageService

File:

backend/app/gagf/assessment_factory_lite_proposal_export_package_service.py

Purpose:

Bundle proposal export artifacts into one guarded package object.

The service can build the package from an existing Markdown export, formal proposal document, proposal-ready artifact, paid-assessment offer, buyer_context, or operator_approval object.

## Endpoint

### Proposal Export Package Endpoint

POST /products/assessment-factory-lite/proposal/export-package

Purpose:

Returns a bundled proposal export package.

The Operator Workstation can use this endpoint to review Markdown export status, PDF readiness, PDF export object status, approval gates, export manifest, boundary notices, blocking issues, and next action in one response.

## Request Contract

The request body may include:

export
document
proposal
offer
buyer_context
operator_approval

## Export Input

The export object may be supplied when the operator wants to package an existing Markdown export.

If export is supplied, the service uses it directly as the Markdown export input.

## Document Input

The document object may be supplied when the operator wants the service chain to build the Markdown export from a formal proposal document.

## Proposal Input

The proposal object may be supplied when the operator wants the service chain to build a formal proposal document from a proposal-ready artifact, render Markdown, check readiness, build PDF export object, and package the result.

## Offer Input

The offer object may be supplied when the operator wants to start from a paid-assessment offer.

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

If export, document, proposal, and offer are not supplied, the service builds the proposal, document, Markdown export, PDF readiness result, PDF export object, and package from buyer_context.

## Operator Approval Input

The operator_approval object may be supplied when the operator wants to attach approval metadata to the PDF export object and package.

If operator_approval is not supplied, the package preserves the default operator approval gate.

## Response Contract

The proposal export package response includes:

status
package_type
package_name
release
version
package_stage
package_status
markdown_export
pdf_readiness
pdf_export
export_manifest
operator_approval
boundary_notices
package_contents
blocking_issues
next_action
operator_message
recommended_action

## Package Type

The package_type value is:

assessment_factory_lite_proposal_export_package

## Release Marker

The package belongs to:

release:

assessment-factory-lite-proposal-package

version:

2.0.0

## Package Stage

The package_stage value is:

proposal_export_package

## Package Status

The package_status value is:

ready

or:

blocked

## Ready Package

A ready package means:

Markdown export exists
PDF readiness passes
PDF export object is created
Blocking issues are empty
Boundary notices are present
Operator approval gate is present

Default ready values include:

package_status: ready
recommended_action: review_proposal_export_package

## Blocked Package

A blocked package means one or more readiness checks failed.

Default blocked values include:

package_status: blocked
recommended_action: resolve_proposal_export_package_gaps

Blocked packages preserve the blocking issues and return a blocked PDF export summary.

## Markdown Export Summary

The markdown_export section includes:

export_type
export_stage
format
filename
release
version
recommended_action
section_count
markdown_present

Default values:

export_type: assessment_factory_lite_formal_proposal_markdown_export
export_stage: formal_proposal_markdown_export
format: markdown
filename: assessment-factory-lite-proposal-approval-and-handoff-workflow.md
release: assessment-factory-lite-proposal-package
version: 2.0.0
recommended_action: review_formal_proposal_markdown_export
section_count: 14
markdown_present: True

## PDF Readiness Summary

The pdf_readiness section includes:

readiness_type
readiness_stage
passed_checks
failed_checks
readiness_score
ready_for_pdf
blocking_issues
recommended_action

Default passing values:

readiness_type: assessment_factory_lite_formal_proposal_pdf_readiness
readiness_stage: formal_proposal_pdf_readiness_check
passed_checks: 9
failed_checks: 0
readiness_score: 1.0
ready_for_pdf: True
blocking_issues: []
recommended_action: prepare_formal_proposal_pdf_export

## PDF Export Summary

The pdf_export section includes:

status
export_type
export_stage
format
content_type
filename
source_markdown_filename
recommended_action

Default successful values:

status: ok
export_type: assessment_factory_lite_formal_proposal_pdf_export
export_stage: formal_proposal_pdf_export
format: pdf
content_type: application/pdf
filename: assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf
source_markdown_filename: assessment-factory-lite-proposal-approval-and-handoff-workflow.md
recommended_action: review_formal_proposal_pdf_export

## Export Manifest

The export_manifest section includes:

package_manifest_type
markdown_filename
pdf_filename
markdown_export_type
pdf_export_type
pdf_export_status
readiness_score
ready_for_pdf
release
version
generated_by

Default values:

package_manifest_type: proposal_export_package_manifest
markdown_filename: assessment-factory-lite-proposal-approval-and-handoff-workflow.md
pdf_filename: assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf
markdown_export_type: assessment_factory_lite_formal_proposal_markdown_export
pdf_export_type: assessment_factory_lite_formal_proposal_pdf_export
pdf_export_status: ok
readiness_score: 1.0
ready_for_pdf: True
release: assessment-factory-lite-proposal-package
version: 2.0.0
generated_by: AssessmentFactoryLiteProposalExportPackageService

## Operator Approval Gate

The operator_approval section preserves the approval gate from the PDF export object.

Default values:

approval_status: operator_review_required
scope_approved: False
evidence_boundary_approved: False
commercial_terms_approved: False
buyer_language_approved: False

Default approval note:

PDF export object is generated for review only. Operator must approve scope, evidence boundary, commercial terms, and buyer-facing language before sending.

## Boundary Notices

The boundary_notices section includes:

commercial_boundary
evidence_boundary
pdf_boundary
constitutional_boundary

Every boundary notice is required.

## Commercial Boundary Notice

Message:

Proposal export package is non-binding until final scope, price, payment terms, and buyer-facing language are approved.

Required:

True

## Evidence Boundary Notice

Message:

Proposal export package must use safe, non-sensitive evidence only unless a future approved policy expands the boundary.

Required:

True

## PDF Boundary Notice

Message:

This PDF export object is a draft artifact. It does not create a binding quote, sales contract, invoice, legal agreement, production onboarding plan, or compliance certification.

Required:

True

## Constitutional Boundary Notice

Message:

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

Required:

True

## Package Contents

The package_contents section includes:

formal_proposal_markdown_export
formal_proposal_pdf_readiness
formal_proposal_pdf_export_object
operator_approval_gate
export_manifest
boundary_notices
blocking_issues
next_action

## Blocking Issues

The blocking_issues list is empty when package_status is ready.

Default ready value:

blocking_issues: []

A blocked package includes failed readiness check names.

Example blocking issue:

commercial_terms_present

## Ready Next Action

When the package is ready, next_action includes:

action: review_and_prepare_buyer_delivery_package

operator_instruction:

Review Markdown export, PDF export object, approval gate, manifest, and boundary notices before preparing buyer delivery.

future_action:

prepare_buyer_delivery_package

## Blocked Next Action

When the package is blocked, next_action includes:

action: resolve_export_package_gaps

operator_instruction:

Resolve readiness or boundary gaps before preparing buyer delivery.

future_action:

rerun_proposal_export_package

## Ready Operator Message

Assessment Factory Lite proposal export package is ready for operator review.

## Blocked Operator Message

Assessment Factory Lite proposal export package is blocked because one or more readiness checks failed.

## Blocked Commercial Terms Example

If the Markdown export changes:

Binding quote: False

to:

Binding quote: True

Then the package becomes blocked.

Expected blocked values:

package_status: blocked
recommended_action: resolve_proposal_export_package_gaps
blocking_issues: commercial_terms_present
pdf_readiness.ready_for_pdf: False
pdf_readiness.failed_checks: 1
pdf_export.status: blocked
pdf_export.export_stage: formal_proposal_pdf_export_blocked

## Relationship to Markdown Export

The Markdown export is the human-readable proposal content source.

The proposal export package summarizes the Markdown export and confirms Markdown content is present.

The Markdown summary includes:

format: markdown
section_count: 14
markdown_present: True

## Relationship to PDF Readiness

The PDF readiness result determines whether the package is ready or blocked.

If ready_for_pdf is True, the package can include a successful PDF export object.

If ready_for_pdf is False, the package is blocked and carries the failed checks forward.

## Relationship to PDF Export Object

The PDF export object is the guarded PDF draft representation.

The package does not create a binary PDF file.

It includes a PDF export object summary that can later feed buyer delivery packaging or binary PDF generation.

## Relationship to Buyer Delivery

The proposal export package is the bridge between proposal generation and buyer delivery.

It does not send anything to the buyer.

A future buyer delivery package may include:

Markdown export
PDF export object
actual generated PDF
operator approval record
delivery manifest
evidence boundary metadata
commercial boundary notice
buyer-facing message

## Commercial Boundary

The proposal export package does not create a binding quote, binding sales contract, invoice, legal agreement, or payment request.

The package remains non-binding until the operator approves final scope, price, payment terms, proposal expiration, evidence boundaries, exclusions, and buyer-facing language.

## Compliance Boundary

The Assessment Factory Lite Proposal Export Package does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It creates a deterministic export package for a bounded paid-assessment conversation.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Proposal Export Package does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, live integrations, buyer delivery, or operator approval.

It helps the operator review proposal export artifacts before buyer delivery.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt proposal package language, but AI must not override deterministic readiness checks, evidence boundaries, approval requirements, operator notes, boundary notices, commercial terms, blocked package behavior, or operator approval gates without human-approved policy changes.
