# Assessment Factory Lite Formal Proposal Markdown Export

## Purpose

The Assessment Factory Lite Formal Proposal Markdown Export converts a formal proposal document object into a deterministic Markdown proposal export.

The export is designed to be reviewed by the operator before it is used as buyer-facing material.

It is not a binding quote, sales contract, invoice, legal agreement, production onboarding plan, or compliance certification.

## Capability Chain

Assessment Factory Lite Proposal Package
→ Formal Proposal Document Service
→ Formal Proposal Document Endpoint
→ Markdown Export Service
→ Markdown Export Endpoint
→ Operator Review
→ Future PDF or DOCX Export

## Service

### AssessmentFactoryLiteFormalProposalMarkdownExportService

File:

backend/app/gagf/assessment_factory_lite_formal_proposal_markdown_export_service.py

Purpose:

Render a formal proposal document object as deterministic Markdown.

The service can export Markdown from an existing formal proposal document, an existing proposal-ready artifact, an existing paid-assessment offer, or buyer_context.

## Endpoint

### Formal Proposal Markdown Export Endpoint

POST /products/assessment-factory-lite/proposal/document/markdown

Purpose:

Returns a deterministic Markdown proposal export object.

The Operator Workstation can use this endpoint to review a Markdown proposal before PDF, DOCX, or buyer-facing export generation.

## Request Contract

The request body may include:

document
proposal
offer
buyer_context

## Document Input

The document object may be supplied when the operator wants to export Markdown from a previously generated formal proposal document.

If document is supplied, the Markdown export service uses it directly.

## Proposal Input

The proposal object may be supplied when the operator wants to build a formal proposal document from a proposal-ready artifact and then render Markdown.

If document is not supplied and proposal is supplied, the formal proposal document service converts the proposal into a formal document before Markdown export.

## Offer Input

The offer object may be supplied when the operator wants to build a proposal from a paid-assessment offer, convert it into a formal proposal document, and then render Markdown.

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

If document, proposal, and offer are not supplied, the export service builds the proposal and formal document from buyer_context before rendering Markdown.

## Response Contract

The Markdown export response includes:

status
export_type
package_name
release
version
export_stage
format
filename
markdown
source_document
export_sections
operator_message
recommended_action

## Export Type

The export_type value is:

assessment_factory_lite_formal_proposal_markdown_export

## Release Marker

The Markdown export object belongs to:

release:

assessment-factory-lite-proposal-package

version:

2.0.0

## Export Stage

The export_stage value is:

formal_proposal_markdown_export

## Format

The format value is:

markdown

## Recommended Action

The recommended_action value is:

review_formal_proposal_markdown_export

## Filename Behavior

The default filename is:

assessment-factory-lite-proposal-approval-and-handoff-workflow.md

The filename is generated from the formal proposal document title.

The filename generator removes the leading Formal prefix, removes the Assessment Factory Lite Proposal for prefix, lowercases the workflow area, replaces spaces and underscores with hyphens, removes unsafe characters, collapses empty parts, and appends the .md extension.

Custom buyer context example:

workflow_area: security review workflow

Expected custom filename:

assessment-factory-lite-proposal-security-review-workflow.md

Fallback filename:

assessment-factory-lite-proposal-workflow.md

## Source Document Contract

The source_document section preserves formal proposal document identity.

Default source document values:

document_type: assessment_factory_lite_formal_proposal_document
document_stage: formal_proposal_document_draft
release: assessment-factory-lite-proposal-package
version: 2.0.0
recommended_action: review_formal_proposal_document

## Export Sections

The Markdown export includes these sections:

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

## Generated Markdown Structure

The generated Markdown starts with the formal proposal document title as an H1 heading.

Default title:

# Formal Assessment Factory Lite Proposal for approval and handoff workflow

Custom title example:

# Formal Assessment Factory Lite Proposal for security review workflow

## Proposal Metadata Section

The Proposal Metadata section includes:

Document type
Package
Release
Version
Stage
Recommended action

Default values include:

assessment_factory_lite_formal_proposal_document
Assessment Factory Lite Demo Package
assessment-factory-lite-proposal-package
2.0.0
formal_proposal_document_draft
review_formal_proposal_document

## Buyer Summary Section

The Buyer Summary section includes:

Primary buyer
Secondary buyers
Buyer pain
Best fit context
Summary

Default buyer values include:

operations_leader
it_manager
workflow_owner
founder_operator
approval delays, ownership gaps, handoff delays, and workflow drag

## Problem Statement Section

The Problem Statement section includes:

Workflow area
Default friction hypothesis
Buyer value
Statement

Default values include:

approval and handoff workflow
approval_delay

## Assessment Scope Section

The Assessment Scope section includes:

Scope type
Workflow area
Duration
Scope boundary
Included Work
Success Definition

Default values include:

bounded_friction_assessment
approval and handoff workflow
3_to_5_business_days
review_safe_workflow_evidence
validate_sample_or_redacted_rows
identify_top_friction_point
summarize_governance_drag
recommend_one_focused_intervention
prepare_buyer_summary

## Evidence Boundary Section

The Evidence Boundary section includes:

Request type
Requested sources
Allowed formats
Allowed data
Prohibited data
Certification claims allowed
Binding price quote allowed
Collection rule

Default request type:

safe_non_sensitive_workflow_evidence

Default requested sources:

sanitized_workflow_export
approval_timestamps
handoff_log
blocked_work_items

Allowed formats:

sanitized_csv
synthetic_sample
redacted_export
manual_summary

Allowed data:

sample_csv
synthetic_workflow_events
sanitized_csv
redacted_workflow_export
manual_workflow_summary

Prohibited data:

credentials
federal_sensitive_data
live_security_telemetry
production_customer_data_without_review
real_customer_secrets
regulated_health_data

Certification claims allowed:

False

Binding price quote allowed:

False

## Deliverables Section

The Deliverables section includes each deliverable as a Markdown subsection.

Default deliverables:

assessment_summary
recommended_next_test

## Assessment Summary Deliverable

Format:

markdown_or_pdf_ready_summary

Sections:

executive_summary
evidence_boundary
workflow_friction_finding
top_constraint
recommended_intervention
next_test
excluded_scope

## Recommended Next Test Deliverable

Format:

short_action_plan

Sections:

top_constraint
recommended_intervention
next_test
owner_or_stakeholder

## Timeline Section

The Timeline section includes:

Estimated duration
Timeline phase subsections

Default estimated duration:

3_to_5_business_days

Default phases:

intake
evidence_review
diagnostic_summary
recommendation_review

## Commercial Terms Section

The Commercial Terms section includes:

Pricing model
Currency
Recommended price band
Payment terms
Proposal expiration
Binding quote
Terms status
Pricing note

Default values:

fixed_fee_discovery_assessment
USD
USD 500 - 2500
operator_to_define
False
operator_to_finalize

Pricing note:

Final pricing is operator-approved and should not be treated as an automated binding quote.

## Assumptions Section

The Assumptions section includes:

buyer_selects_one_workflow_for_assessment
buyer_provides_safe_non_sensitive_evidence_only
operator_reviews_evidence_boundary_before_analysis
assessment_output_is_reviewed_before_buyer_delivery
final_price_and_terms_are_operator_approved

## Approval Requirements Section

The Approval Requirements section includes:

evidence_boundary_approval
commercial_terms_approval
buyer_scope_acknowledgement

Each approval includes required_by, purpose, and required.

## Exclusions Section

The Exclusions section includes proposal and document-level exclusions.

Default exclusions include:

production_customer_data_processing
regulated_data_processing
federal_data_processing
live_system_integration
autonomous_remediation
security_certification
compliance_audit
soc_2_audit_claims
fedramp_or_hipaa_certification_claims
payment_processing
customer_portal_access
persistent_customer_storage
guaranteed_operational_outcomes
binding_legal_or_compliance_advice
binding_price_quote
binding_sales_contract
production_service_commitment
legal_or_compliance_certification

## Operator Notes Section

The Operator Notes section includes:

review_scope_before_sending
review_evidence_boundary_before_sending
review_terms_before_sending

These notes require operator review before the Markdown export is used as buyer-facing material.

## Next Action Section

The Next Action section includes:

action
operator_instruction
future_action

Default action:

review_and_finalize_formal_proposal_document

Default future action:

export_formal_proposal_document

## Boundary Notice Section

The Boundary Notice section states that the Markdown export is not a binding quote, sales contract, invoice, legal agreement, production onboarding plan, or compliance certification.

It also states that the operator must review scope, pricing, evidence boundaries, commercial terms, exclusions, and buyer-facing language before use.

It also preserves this constitutional rule:

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

## Custom Buyer Context Example

Example custom buyer context:

primary_buyer: founder_operator
workflow_area: security review workflow
duration: 5_to_7_business_days
price_low: 1500
price_high: 3500

Expected Markdown values:

# Formal Assessment Factory Lite Proposal for security review workflow
Primary buyer: founder_operator
Workflow area: security review workflow
Duration: 5_to_7_business_days
Recommended price band: USD 1500 - 3500

Expected filename:

assessment-factory-lite-proposal-security-review-workflow.md

## Relationship to Formal Proposal Document

The formal proposal document service creates a structured document object.

The Markdown export service renders that document object into Markdown.

The document service answers:

What should the formal proposal document contain?

The Markdown export service answers:

How should the formal proposal document be rendered as Markdown?

## Relationship to Future PDF and DOCX Exports

The Markdown export is a bridge format.

A future PDF export service can convert the Markdown export into a buyer-facing PDF.

A future DOCX export service can convert the Markdown export into an editable proposal document.

A future proposal package exporter can combine Markdown, PDF, DOCX, operator notes, evidence boundary metadata, and approval records.

## Commercial Boundary

The Markdown export service does not create a binding quote, binding sales contract, invoice, legal agreement, or payment request.

The recommended price band remains operator-approved and non-binding.

The operator must approve final scope, price, payment terms, proposal expiration, evidence boundaries, exclusions, and buyer-facing language before sending a proposal to a buyer.

## Compliance Boundary

The Assessment Factory Lite Formal Proposal Markdown Export does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides a deterministic Markdown export for a bounded paid-assessment conversation.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Formal Proposal Markdown Export does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, or live integrations.

It helps the operator convert a formal proposal document draft into a Markdown export while preserving evidence boundaries.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt Markdown proposal language, but AI must not override deterministic assessment boundaries, evidence boundaries, approval requirements, exclusions, operator notes, boundary notices, or commercial terms without human-approved policy changes.
