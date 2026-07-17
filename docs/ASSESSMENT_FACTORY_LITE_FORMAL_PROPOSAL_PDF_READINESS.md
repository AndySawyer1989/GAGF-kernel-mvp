# Assessment Factory Lite Formal Proposal PDF Readiness

## Purpose

The Assessment Factory Lite Formal Proposal PDF Readiness layer checks whether a formal proposal Markdown export is safe and complete enough for future PDF generation.

It does not generate a PDF.

It verifies that the Markdown export includes the required proposal sections, commercial boundaries, evidence boundaries, approval requirements, operator notes, and boundary notice before any buyer-facing PDF can be produced.

## Capability Chain

Assessment Factory Lite Proposal Package
→ Formal Proposal Document Service
→ Formal Proposal Markdown Export Service
→ Formal Proposal PDF Readiness Service
→ Formal Proposal PDF Readiness Endpoint
→ Operator Review
→ Future PDF Export

## Service

### AssessmentFactoryLiteFormalProposalPDFReadinessService

File:

backend/app/gagf/assessment_factory_lite_formal_proposal_pdf_readiness_service.py

Purpose:

Check whether a formal proposal Markdown export is ready for future PDF generation.

The service can check an existing Markdown export or build one from a formal proposal document, proposal-ready artifact, paid-assessment offer, or buyer_context.

## Endpoint

### Formal Proposal PDF Readiness Endpoint

POST /products/assessment-factory-lite/proposal/document/pdf-readiness

Purpose:

Returns a PDF readiness result for a formal proposal Markdown export.

The Operator Workstation can use this endpoint to decide whether the Markdown proposal export is safe enough to move toward PDF generation.

## Request Contract

The request body may include:

export
document
proposal
offer
buyer_context

## Export Input

The export object may be supplied when the operator wants to check an existing Markdown export.

If export is supplied, the PDF readiness service checks it directly.

## Document Input

The document object may be supplied when the operator wants to build a Markdown export from a formal proposal document and then check PDF readiness.

## Proposal Input

The proposal object may be supplied when the operator wants to build a formal proposal document from a proposal-ready artifact, render Markdown, and then check PDF readiness.

## Offer Input

The offer object may be supplied when the operator wants to build a proposal from a paid-assessment offer, build a formal proposal document, render Markdown, and then check PDF readiness.

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

If export, document, proposal, and offer are not supplied, the readiness service builds the proposal, formal document, and Markdown export from buyer_context before checking readiness.

## Response Contract

The PDF readiness response includes:

status
readiness_type
package_name
release
version
readiness_stage
source_export
required_sections
checks
passed_checks
failed_checks
readiness_score
ready_for_pdf
recommendation
blocking_issues
operator_message
recommended_action

## Readiness Type

The readiness_type value is:

assessment_factory_lite_formal_proposal_pdf_readiness

## Release Marker

The PDF readiness object belongs to:

release:

assessment-factory-lite-proposal-package

version:

2.0.0

## Readiness Stage

The readiness_stage value is:

formal_proposal_pdf_readiness_check

## Source Export Contract

The source_export section preserves Markdown export identity.

Default source export values:

export_type: assessment_factory_lite_formal_proposal_markdown_export
export_stage: formal_proposal_markdown_export
format: markdown
filename: assessment-factory-lite-proposal-approval-and-handoff-workflow.md
release: assessment-factory-lite-proposal-package
version: 2.0.0
recommended_action: review_formal_proposal_markdown_export

## Required Sections

The readiness service requires these proposal export sections:

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

## Required Markdown Headings

The readiness service checks for these Markdown headings:

## Proposal Metadata
## Buyer Summary
## Problem Statement
## Assessment Scope
## Evidence Boundary
## Deliverables
## Timeline
## Commercial Terms
## Assumptions
## Approval Requirements
## Exclusions
## Operator Notes
## Next Action
## Boundary Notice

## Readiness Checks

The readiness service runs nine checks.

## Check 1 — export_contract_present

Purpose:

Verify the export object identifies itself as a formal proposal Markdown export.

Required value:

assessment_factory_lite_formal_proposal_markdown_export

Failure meaning:

The input may not be the correct export object.

## Check 2 — export_format_is_markdown

Purpose:

Verify the source export format is Markdown before future PDF conversion.

Required value:

markdown

Failure meaning:

The source export is not in the expected Markdown format.

## Check 3 — filename_present

Purpose:

Verify the Markdown filename is present and ends with .md.

Default filename:

assessment-factory-lite-proposal-approval-and-handoff-workflow.md

Failure meaning:

The future PDF filename cannot be derived safely.

## Check 4 — required_sections_present

Purpose:

Verify all required Markdown headings are present.

Required headings include:

Proposal Metadata
Buyer Summary
Problem Statement
Assessment Scope
Evidence Boundary
Deliverables
Timeline
Commercial Terms
Assumptions
Approval Requirements
Exclusions
Operator Notes
Next Action
Boundary Notice

Failure meaning:

The Markdown export is missing one or more required proposal sections.

## Check 5 — commercial_terms_present

Purpose:

Verify commercial terms are visible, non-binding, and operator-finalized.

Required content includes:

## Commercial Terms
Binding quote: False
operator_to_finalize

Failure meaning:

The export may contain unsafe commercial terms or may be missing required commercial boundaries.

## Check 6 — evidence_boundary_present

Purpose:

Verify the evidence boundary is visible before PDF export.

Required content includes:

## Evidence Boundary
safe_non_sensitive_workflow_evidence
Certification claims allowed: False

Failure meaning:

The export may not clearly prevent unsafe evidence intake or certification claims.

## Check 7 — approval_requirements_present

Purpose:

Verify approval requirements are visible before PDF export.

Required content includes:

## Approval Requirements
evidence_boundary_approval
commercial_terms_approval
buyer_scope_acknowledgement

Failure meaning:

The export may not clearly identify who must approve evidence, terms, and buyer scope.

## Check 8 — operator_notes_present

Purpose:

Verify operator review notes are visible before PDF export.

Required content includes:

## Operator Notes
review_scope_before_sending
review_evidence_boundary_before_sending
review_terms_before_sending

Failure meaning:

The export may be missing required operator review prompts.

## Check 9 — boundary_notice_present

Purpose:

Verify the boundary notice is visible before PDF export.

Required content includes:

## Boundary Notice
not a binding quote, sales contract, invoice
GAGF Kernel remains the authoritative decision

Failure meaning:

The export may not clearly state that it is non-binding and that the deterministic GAGF Kernel remains authoritative.

## Passing Result

A default valid export should return:

passed_checks: 9
failed_checks: 0
readiness_score: 1.0
ready_for_pdf: True
blocking_issues: []

Recommended action:

prepare_formal_proposal_pdf_export

Recommendation:

Markdown export is ready for operator-reviewed PDF generation.

Operator message:

Assessment Factory Lite formal proposal Markdown export passed PDF readiness checks.

## Failing Result

If one or more checks fail, the response returns:

ready_for_pdf: False
recommended_action: resolve_formal_proposal_pdf_readiness_gaps

Recommendation:

Markdown export is not ready for PDF generation. Resolve blocking readiness issues before creating a buyer-facing PDF.

Operator message:

Assessment Factory Lite formal proposal Markdown export has blocking PDF readiness gaps.

## Readiness Score Logic

The readiness_score is calculated as:

passed checks divided by total checks

The score is rounded to two decimal places.

There are nine total checks.

A perfect readiness score is:

1.0

A passing PDF readiness decision requires:

readiness_score == 1.0

This means every readiness check must pass.

## Blocking Issues

The blocking_issues list includes the check names that failed.

Example blocking issues:

required_sections_present
commercial_terms_present
evidence_boundary_present
approval_requirements_present
operator_notes_present
boundary_notice_present

## Missing Boundary Notice Example

If the Markdown export is missing the Boundary Notice heading, the readiness service should block PDF generation.

Expected failed checks:

required_sections_present
boundary_notice_present

Expected readiness score:

0.78

Expected recommended action:

resolve_formal_proposal_pdf_readiness_gaps

## Binding Quote Language Example

If the Markdown export changes Binding quote: False to Binding quote: True, the readiness service should block PDF generation.

Expected failed check:

commercial_terms_present

Expected readiness score:

0.89

Expected recommended action:

resolve_formal_proposal_pdf_readiness_gaps

## Custom Buyer Context Example

Example buyer_context:

primary_buyer: founder_operator
workflow_area: security review workflow
duration: 5_to_7_business_days
price_low: 1500
price_high: 3500

Expected source export filename:

assessment-factory-lite-proposal-security-review-workflow.md

Expected readiness:

ready_for_pdf: True
readiness_score: 1.0

## Relationship to Markdown Export

The Markdown export service creates the proposal Markdown content.

The PDF readiness service validates that Markdown content before PDF generation.

The Markdown export service answers:

What should the Markdown proposal contain?

The PDF readiness service answers:

Is this Markdown proposal safe and complete enough to move toward PDF generation?

## Relationship to Future PDF Export

The PDF readiness layer is a gate before actual PDF export.

A future PDF export service should only generate a buyer-facing PDF when:

ready_for_pdf is True
readiness_score is 1.0
blocking_issues is empty
recommended_action is prepare_formal_proposal_pdf_export

## Future PDF Export Inputs

A future PDF export service may use:

filename
markdown
source_document
source_export
required_sections
readiness result
operator approval metadata
evidence boundary metadata

## Commercial Boundary

The PDF readiness service does not create a binding quote, binding sales contract, invoice, legal agreement, or payment request.

It only checks whether the Markdown export includes the required non-binding commercial terms and operator-finalized status.

The recommended price band remains operator-approved and non-binding.

The operator must approve final scope, price, payment terms, proposal expiration, evidence boundaries, exclusions, and buyer-facing language before sending a proposal to a buyer.

## Compliance Boundary

The Assessment Factory Lite Formal Proposal PDF Readiness layer does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides a deterministic readiness gate before future PDF generation.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Formal Proposal PDF Readiness layer does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, live integrations, or buyer delivery.

It helps the operator verify that a Markdown proposal export is complete and bounded before future PDF generation.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt proposal language, but AI must not override deterministic readiness checks, evidence boundaries, approval requirements, operator notes, boundary notices, commercial terms, or PDF-readiness gates without human-approved policy changes.
