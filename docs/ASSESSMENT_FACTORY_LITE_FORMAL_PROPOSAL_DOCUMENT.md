# Assessment Factory Lite Formal Proposal Document

## Purpose

The Assessment Factory Lite Formal Proposal Document turns a proposal-ready artifact into a formal proposal document draft.

It does not create a binding quote, binding sales contract, invoice, legal agreement, production onboarding plan, or compliance certification.

It creates a structured document object that the operator can review before exporting or sending a buyer-facing proposal.

## Capability Chain

Assessment Factory Lite Demo Package
→ Proposal Package Release
→ Proposal Builder Service
→ Formal Proposal Document Service
→ Formal Proposal Document Endpoint
→ Formal Proposal Document Draft
→ Operator Review
→ Future Buyer-Facing Export

## Service

### AssessmentFactoryLiteFormalProposalDocumentService

File:

backend/app/gagf/assessment_factory_lite_formal_proposal_document_service.py

Purpose:

Build a formal proposal document object from an Assessment Factory Lite proposal-ready artifact.

The service can build a formal proposal document from an existing proposal object, an existing offer object, or buyer_context.

## Endpoint

### Formal Proposal Document Endpoint

POST /products/assessment-factory-lite/proposal/document

Purpose:

Returns a formal proposal document draft object.

The Operator Workstation can use this endpoint to prepare a structured proposal document before export or buyer delivery.

## Request Contract

The request body may include:

proposal
offer
buyer_context

## Proposal Input

The proposal object may be supplied when the operator wants to build a formal proposal document from a previously generated proposal-ready artifact.

If proposal is supplied, the document service uses it directly.

## Offer Input

The offer object may be supplied when the operator wants to build a proposal from a paid-assessment offer and then convert it into a formal proposal document.

If proposal is not supplied and offer is supplied, the proposal builder converts the offer into proposal data before the formal document is created.

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

If proposal and offer are not supplied, the document service builds a proposal from buyer_context and then converts it into a formal proposal document draft.

## Response Contract

The formal proposal document response includes:

status
document_type
package_name
release
version
document_stage
document_title
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
source_proposal
document_sections
next_action
operator_message
recommended_action

## Document Type

The document_type value is:

assessment_factory_lite_formal_proposal_document

## Release Marker

The formal proposal document object belongs to:

release:

assessment-factory-lite-proposal-package

version:

2.0.0

## Document Stage

The document_stage value is:

formal_proposal_document_draft

## Recommended Action

The recommended_action value is:

review_formal_proposal_document

## Document Title

The default document title is:

Formal Assessment Factory Lite Proposal for approval and handoff workflow

Custom buyer context example:

workflow_area: security review workflow

Expected custom title:

Formal Assessment Factory Lite Proposal for security review workflow

## Document Sections

The formal proposal document includes these sections:

document_title
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

## Buyer Summary

The buyer_summary section includes:

primary_buyer
secondary_buyers
buyer_pain
best_fit_context
summary

Default primary buyer:

operations_leader

Default secondary buyers:

it_manager
workflow_owner
founder_operator

Default buyer pain:

approval delays, ownership gaps, handoff delays, and workflow drag

Default buyer summary:

This proposal is prepared for operations_leader to assess friction in the approval and handoff workflow.

## Problem Statement

The problem_statement section includes:

workflow_area
statement
default_friction_hypothesis
buyer_value

Default workflow area:

approval and handoff workflow

Default friction hypothesis:

approval_delay

Purpose:

Explain the workflow friction hypothesis and why a bounded assessment is useful.

## Assessment Scope

The assessment_scope section includes:

scope_type
workflow_area
duration
included_work
success_definition
scope_boundary

Default scope type:

bounded_friction_assessment

Default duration:

3_to_5_business_days

Included work:

review_safe_workflow_evidence
validate_sample_or_redacted_rows
identify_top_friction_point
summarize_governance_drag
recommend_one_focused_intervention
prepare_buyer_summary

Scope boundary:

This proposal covers one bounded workflow assessment using safe, non-sensitive evidence only.

## Evidence Boundary

The evidence_boundary section includes:

request_type
requested_sources
allowed_format
allowed_data
prohibited_data
collection_rule
certification_claims_allowed
binding_price_quote_allowed

Request type:

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

certification_claims_allowed:

False

binding_price_quote_allowed:

False

Collection rule:

Collect the minimum safe evidence needed to diagnose one workflow.

## Deliverables

The formal proposal document preserves the proposal deliverables.

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

Buyer value:

A concise evidence-backed summary that can be reviewed with operations, IT, or workflow owners.

## Recommended Next Test Deliverable

Format:

short_action_plan

Sections:

top_constraint
recommended_intervention
next_test
owner_or_stakeholder

Buyer value:

A practical next-step plan that the buyer can review with operations, IT, or workflow owners.

## Timeline

The timeline section includes:

estimated_duration
phases

Default estimated duration:

3_to_5_business_days

Default phases:

intake
evidence_review
diagnostic_summary
recommendation_review

## Intake Phase

Description:

Confirm workflow boundary and safe evidence sources.

## Evidence Review Phase

Description:

Review sample, sanitized, or redacted workflow evidence.

## Diagnostic Summary Phase

Description:

Identify the top friction point and governance drag.

## Recommendation Review Phase

Description:

Review recommended intervention and next test.

## Commercial Terms

The commercial_terms section includes:

pricing_model
currency
recommended_price_band
payment_terms
proposal_expiration
pricing_note
binding_quote
terms_status

Default pricing model:

fixed_fee_discovery_assessment

Default currency:

USD

Default recommended price band:

low: 500
high: 2500

Default payment terms:

operator_to_define

Default proposal expiration:

operator_to_define

Binding quote:

False

Terms status:

operator_to_finalize

Pricing note:

Final pricing is operator-approved and should not be treated as an automated binding quote.

## Assumptions

The assumptions section includes:

buyer_selects_one_workflow_for_assessment
buyer_provides_safe_non_sensitive_evidence_only
operator_reviews_evidence_boundary_before_analysis
assessment_output_is_reviewed_before_buyer_delivery
final_price_and_terms_are_operator_approved

## Approval Requirements

The formal proposal document preserves three approval requirements:

evidence_boundary_approval
commercial_terms_approval
buyer_scope_acknowledgement

## Evidence Boundary Approval

Required by:

operator

Purpose:

Confirm proposed evidence is safe for assessment intake.

Required:

True

## Commercial Terms Approval

Required by:

operator

Purpose:

Confirm final price, scope, and payment terms.

Required:

True

## Buyer Scope Acknowledgement

Required by:

buyer

Purpose:

Confirm workflow boundary and excluded scope.

Required:

True

## Exclusions

The formal proposal document preserves proposal exclusions and adds document-level exclusions.

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

## Operator Notes

The operator_notes section includes:

review_scope_before_sending
review_evidence_boundary_before_sending
review_terms_before_sending

## Review Scope Before Sending

Message:

Confirm the workflow boundary, included work, and excluded scope before sharing with a buyer.

Required:

True

## Review Evidence Boundary Before Sending

Message:

Confirm only safe, non-sensitive evidence is requested.

Required:

True

## Review Terms Before Sending

Message:

Finalize payment terms, proposal expiration, and pricing before buyer delivery.

Required:

True

## Source Proposal

The source_proposal section preserves proposal identity.

Default source proposal values:

proposal_type: assessment_factory_lite_paid_assessment_proposal
proposal_stage: proposal_ready_artifact
release: assessment-factory-lite-commercial-offer
version: 1.9.0
recommended_action: review_proposal_ready_artifact

## Next Action

The next_action section includes:

action
operator_instruction
future_action

Default action:

review_and_finalize_formal_proposal_document

Operator instruction:

Review the formal proposal document draft, finalize commercial terms, confirm evidence boundaries, and decide whether to export a buyer-facing document.

Future action:

export_formal_proposal_document

## Custom Buyer Context Example

The endpoint supports custom buyer context.

Example custom buyer context:

primary_buyer: founder_operator
workflow_area: security review workflow
duration: 5_to_7_business_days
price_low: 1500
price_high: 3500

Expected custom values:

document title: Formal Assessment Factory Lite Proposal for security review workflow
primary buyer: founder_operator
workflow area: security review workflow
duration: 5_to_7_business_days
recommended price band: 1500 to 3500

## Relationship to Proposal Builder

The proposal builder creates the deterministic proposal-ready artifact.

The formal proposal document service converts that artifact into a structured formal document draft.

The proposal builder answers:

What should the proposal contain?

The formal proposal document service answers:

How should that proposal be organized as a formal document object?

## Relationship to Proposal HTML View

The proposal HTML view presents the proposal-ready artifact inside the Operator Workstation.

The formal proposal document object prepares the structure for a future buyer-facing export.

The HTML view is for presentation.

The formal document object is for document generation.

## Relationship to Future Export Services

The formal proposal document is not yet a PDF, DOCX, signed proposal, invoice, or statement of work.

A future export service may convert the formal proposal document object into a PDF, DOCX, markdown document, statement of work draft, or buyer-facing sales document.

## Commercial Boundary

The formal proposal document service does not create a binding quote, binding sales contract, invoice, legal agreement, or payment request.

The recommended price band remains operator-approved and non-binding.

The operator must approve final scope, price, payment terms, proposal expiration, evidence boundaries, and buyer-facing language before sending a formal proposal to a buyer.

## Compliance Boundary

The Assessment Factory Lite Formal Proposal Document does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides a deterministic formal proposal document draft for a bounded paid-assessment conversation.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Formal Proposal Document does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, or live integrations.

It helps the operator convert a proposal-ready artifact into a formal proposal document draft while preserving evidence boundaries.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt formal proposal language, but AI must not override deterministic assessment boundaries, evidence boundaries, approval requirements, exclusions, operator notes, or commercial terms without human-approved policy changes.
