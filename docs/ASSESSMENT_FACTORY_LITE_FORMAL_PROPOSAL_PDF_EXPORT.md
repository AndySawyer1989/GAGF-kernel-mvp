# Assessment Factory Lite Formal Proposal PDF Export

## Purpose

The Assessment Factory Lite Formal Proposal PDF Export layer creates a guarded PDF export object from a PDF-ready Markdown proposal export.

It does not directly create a binary PDF file yet.

It creates a deterministic PDF export object that records the intended PDF filename, source Markdown filename, readiness summary, operator approval gate, PDF document model, export manifest, and boundary notice.

## Capability Chain

Assessment Factory Lite Proposal Package
→ Formal Proposal Document Service
→ Formal Proposal Markdown Export Service
→ Formal Proposal PDF Readiness Service
→ Formal Proposal PDF Export Service
→ Formal Proposal PDF Export Endpoint
→ Operator Review
→ Future Binary PDF Generation

## Service

### AssessmentFactoryLiteFormalProposalPDFExportService

File:

backend/app/gagf/assessment_factory_lite_formal_proposal_pdf_export_service.py

Purpose:

Build a guarded PDF export object from a PDF-ready Markdown proposal export.

The service checks PDF readiness before creating an export object.

If readiness fails, the service returns a blocked export response.

## Endpoint

### Formal Proposal PDF Export Endpoint

POST /products/assessment-factory-lite/proposal/document/pdf

Purpose:

Returns a guarded PDF export object for the formal proposal package.

The endpoint can receive an existing Markdown export, formal proposal document, proposal-ready artifact, paid-assessment offer, buyer_context, or operator_approval object.

## Request Contract

The request body may include:

export
document
proposal
offer
buyer_context
operator_approval

## Export Input

The export object may be supplied when the operator wants to create a PDF export object from an existing Markdown export.

If export is supplied, the PDF export service checks its PDF readiness before creating the export object.

## Document Input

The document object may be supplied when the operator wants to build a Markdown export from a formal proposal document and then create a guarded PDF export object.

## Proposal Input

The proposal object may be supplied when the operator wants to build a formal proposal document from a proposal-ready artifact, render Markdown, check readiness, and then create a guarded PDF export object.

## Offer Input

The offer object may be supplied when the operator wants to build a proposal from a paid-assessment offer, build a formal document, render Markdown, check readiness, and then create a guarded PDF export object.

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

If export, document, proposal, and offer are not supplied, the export service builds the proposal, formal document, Markdown export, readiness result, and PDF export object from buyer_context.

## Operator Approval Input

The operator_approval object may be supplied when the operator wants to attach explicit approval metadata to the export object.

If operator_approval is not supplied, the service uses the default approval gate.

## Response Contract

A successful PDF export response includes:

status
export_type
package_name
release
version
export_stage
format
content_type
filename
source_markdown_filename
readiness
operator_approval
pdf_document
export_manifest
boundary_notice
operator_message
recommended_action

## Export Type

The export_type value is:

assessment_factory_lite_formal_proposal_pdf_export

## Release Marker

The PDF export object belongs to:

release:

assessment-factory-lite-proposal-package

version:

2.0.0

## Export Stage

A successful export uses:

formal_proposal_pdf_export

A blocked export uses:

formal_proposal_pdf_export_blocked

## Format

The format value is:

pdf

## Content Type

The content_type value is:

application/pdf

## Recommended Action

A successful export uses:

review_formal_proposal_pdf_export

A blocked export uses:

resolve_formal_proposal_pdf_readiness_gaps

## Filename Behavior

The default Markdown filename is:

assessment-factory-lite-proposal-approval-and-handoff-workflow.md

The default PDF filename is:

assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf

The PDF filename is derived from the Markdown filename.

If the Markdown filename ends with .md, the service replaces .md with .pdf.

Custom buyer context example:

workflow_area: security review workflow

Expected custom Markdown filename:

assessment-factory-lite-proposal-security-review-workflow.md

Expected custom PDF filename:

assessment-factory-lite-proposal-security-review-workflow.pdf

Fallback PDF filename:

assessment-factory-lite-proposal-workflow.pdf

## Readiness Gate

The PDF export service calls the PDF readiness service before creating a successful export object.

The PDF export service requires:

ready_for_pdf: True
readiness_score: 1.0
failed_checks: 0
blocking_issues: []

If readiness fails, PDF export is blocked.

## Readiness Summary

The readiness section includes:

readiness_type
readiness_stage
passed_checks
failed_checks
readiness_score
ready_for_pdf
blocking_issues
recommended_action

Default passing readiness values:

readiness_type: assessment_factory_lite_formal_proposal_pdf_readiness
readiness_stage: formal_proposal_pdf_readiness_check
passed_checks: 9
failed_checks: 0
readiness_score: 1.0
ready_for_pdf: True
blocking_issues: []
recommended_action: prepare_formal_proposal_pdf_export

## Blocked Export Behavior

If readiness fails, the service returns:

status: blocked
export_type: assessment_factory_lite_formal_proposal_pdf_export
release: assessment-factory-lite-proposal-package
version: 2.0.0
export_stage: formal_proposal_pdf_export_blocked
format: pdf
content_type: application/pdf
readiness
blocking_issues
boundary_notice
operator_message
recommended_action: resolve_formal_proposal_pdf_readiness_gaps

## Blocked Commercial Terms Example

If the Markdown export changes:

Binding quote: False

to:

Binding quote: True

Then the PDF export service blocks the export.

Expected blocked values:

status: blocked
failed_checks: 1
readiness_score: 0.89
blocking_issues: commercial_terms_present
recommended_action: resolve_formal_proposal_pdf_readiness_gaps

## Default Operator Approval Gate

If no operator_approval object is supplied, the PDF export service returns:

approval_status: operator_review_required
scope_approved: False
evidence_boundary_approved: False
commercial_terms_approved: False
buyer_language_approved: False

Approval note:

PDF export object is generated for review only. Operator must approve scope, evidence boundary, commercial terms, and buyer-facing language before sending.

## Operator Approval Meaning

The operator approval gate prevents a generated PDF export object from being treated as buyer-approved or send-ready.

The default approval gate requires review of:

scope
evidence boundary
commercial terms
buyer-facing language

## PDF Document Model

The pdf_document section includes:

document_kind
filename
render_source
render_status
page_model
required_sections
watermark
footer_notice

Default document kind:

buyer_facing_pdf_proposal_draft

Default render source:

formal_proposal_markdown_export

Default render status:

pdf_export_object_ready

Default page model:

markdown_sections_to_pdf_pages

Default watermark:

Draft - Operator Review Required

Default footer notice:

Non-binding proposal draft. Final scope, price, and terms require operator approval.

## Required Sections

The PDF document model preserves required sections from the readiness layer.

Required sections include:

proposal_metadata
buyer_summary
problem_statement
assessment_scope
evidence_boundary
deliverables
timeline
commercial_terms
assumptions
approval_requirements
exclusions
operator_notes
next_action
boundary_notice

## Export Manifest

The export_manifest section includes:

pdf_filename
source_markdown_filename
source_export_type
source_export_stage
source_release
source_version
readiness_score
ready_for_pdf
generated_by

Default generated_by value:

AssessmentFactoryLiteFormalProposalPDFExportService

## Boundary Notice

The boundary_notice section includes:

non_binding
operator_review_required
not_a_contract
not_an_invoice
not_a_compliance_certification
not_production_onboarding
message
constitutional_rule

Default boolean values:

non_binding: True
operator_review_required: True
not_a_contract: True
not_an_invoice: True
not_a_compliance_certification: True
not_production_onboarding: True

Default message:

This PDF export object is a draft artifact. It does not create a binding quote, sales contract, invoice, legal agreement, production onboarding plan, or compliance certification.

Default constitutional rule:

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

## Successful Export Result

A default successful export should return:

status: ok
export_stage: formal_proposal_pdf_export
format: pdf
content_type: application/pdf
filename: assessment-factory-lite-proposal-approval-and-handoff-workflow.pdf
source_markdown_filename: assessment-factory-lite-proposal-approval-and-handoff-workflow.md
recommended_action: review_formal_proposal_pdf_export

## Custom Buyer Context Example

Example buyer_context:

primary_buyer: founder_operator
workflow_area: security review workflow
duration: 5_to_7_business_days
price_low: 1500
price_high: 3500

Expected values:

status: ok
filename: assessment-factory-lite-proposal-security-review-workflow.pdf
source_markdown_filename: assessment-factory-lite-proposal-security-review-workflow.md
ready_for_pdf: True
readiness_score: 1.0

## Relationship to PDF Readiness

The PDF readiness service decides whether Markdown is safe and complete enough for PDF generation.

The PDF export service creates a guarded PDF export object only after readiness passes.

The PDF readiness service answers:

Is this Markdown proposal safe and complete enough to move toward PDF generation?

The PDF export service answers:

What PDF export object should be created after readiness passes?

## Relationship to Future Binary PDF Generation

The current PDF export object is not a binary PDF file.

It is a deterministic export manifest and document model for future binary PDF generation.

A future binary PDF generator may use:

filename
source_markdown_filename
pdf_document
export_manifest
boundary_notice
operator_approval
readiness

## Commercial Boundary

The PDF export service does not create a binding quote, binding sales contract, invoice, legal agreement, or payment request.

The generated PDF export object is a draft artifact.

The recommended price band remains operator-approved and non-binding.

The operator must approve final scope, price, payment terms, proposal expiration, evidence boundaries, exclusions, and buyer-facing language before sending a proposal to a buyer.

## Compliance Boundary

The Assessment Factory Lite Formal Proposal PDF Export layer does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It creates a guarded PDF export object for a bounded paid-assessment conversation.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Formal Proposal PDF Export layer does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, live integrations, buyer delivery, or operator approval.

It helps the operator create a guarded PDF export object after PDF readiness passes.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt PDF proposal language, but AI must not override deterministic readiness checks, evidence boundaries, approval requirements, operator notes, boundary notices, commercial terms, blocked export behavior, or operator approval gates without human-approved policy changes.
