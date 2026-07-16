# Assessment Factory Lite Proposal Builder

## Purpose

The Assessment Factory Lite Proposal Builder turns a paid-assessment offer into a proposal-ready artifact.

It does not create a binding contract, binding quote, statement of work, invoice, or production onboarding plan.

It creates a structured proposal draft that the operator can review before generating a formal proposal document.

## Capability Chain

Assessment Factory Lite Demo Package
→ Buyer Conversion Release
→ Commercial Offer Release
→ Assessment Offer Builder
→ Proposal Builder Service
→ Proposal Builder Endpoint
→ Proposal-Ready Artifact
→ Operator Review
→ Future Formal Proposal

## Service

### AssessmentFactoryLiteProposalBuilderService

File:

backend/app/gagf/assessment_factory_lite_proposal_builder_service.py

Purpose:

Build a proposal-ready artifact from an Assessment Factory Lite paid-assessment offer.

The service can build a proposal from an existing offer object or from buyer_context.

## Endpoint

### Proposal Builder Endpoint

POST /products/assessment-factory-lite/proposal

Purpose:

Returns a proposal-ready artifact for Assessment Factory Lite.

The Operator Workstation can use this endpoint to prepare a proposal draft after the paid-assessment offer has been generated.

## Request Contract

The request body may include:

offer
buyer_context

## Offer Input

The offer object may be supplied when the operator wants to build a proposal from a previously generated paid-assessment offer.

If offer is not supplied, the proposal builder creates a source offer from the AssessmentFactoryLiteOfferBuilderService.

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

If buyer_context is supplied, the proposal reflects the custom buyer, workflow area, duration, evidence request, deliverable format, and price band.

## Response Contract

The proposal builder response includes:

status
proposal_type
package_name
release
version
proposal_stage
proposal_title
buyer_context
problem_statement
proposed_scope
evidence_boundary
deliverables
timeline
commercial_terms_placeholder
excluded_scope
assumptions
approval_requirements
proposal_risk_controls
source_offer
next_action
operator_message
recommended_action

## Proposal Type

The proposal_type value is:

assessment_factory_lite_paid_assessment_proposal

## Release Marker

The proposal builder object belongs to:

release:

assessment-factory-lite-commercial-offer

version:

1.9.0

## Proposal Stage

The proposal_stage value is:

proposal_ready_artifact

## Recommended Action

The recommended_action value is:

review_proposal_ready_artifact

## Proposal Title

The default proposal title is generated from the workflow area.

Default title:

Assessment Factory Lite Proposal for approval and handoff workflow

Custom buyer context example:

workflow_area: security review workflow

Expected custom title:

Assessment Factory Lite Proposal for security review workflow

## Buyer Context Section

The buyer_context section includes:

primary_buyer
secondary_buyers
buyer_pain
best_fit_context

Default primary buyer:

operations_leader

Default secondary buyers:

it_manager
workflow_owner
founder_operator

Default buyer pain:

approval delays, ownership gaps, handoff delays, and workflow drag

## Problem Statement Section

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

## Proposed Scope Section

The proposed_scope section includes:

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

## Evidence Boundary Section

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

false

binding_price_quote_allowed:

false

Collection rule:

Collect the minimum safe evidence needed to diagnose one workflow.

## Deliverables Section

The proposal builder returns two default deliverables.

### Assessment Summary

Deliverable:

assessment_summary

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

### Recommended Next Test

Deliverable:

recommended_next_test

Format:

short_action_plan

Sections:

top_constraint
recommended_intervention
next_test
owner_or_stakeholder

Buyer value:

A practical next-step plan that the buyer can review with operations, IT, or workflow owners.

## Timeline Section

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

## Commercial Terms Placeholder

The commercial_terms_placeholder section includes:

pricing_model
currency
recommended_price_band
payment_terms
proposal_expiration
pricing_note
binding_quote

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

false

Pricing note:

Final pricing is operator-approved and should not be treated as an automated binding quote.

## Excluded Scope

The proposal preserves the commercial offer excluded scope.

Excluded items include:

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

## Assumptions

The default assumptions are:

buyer_selects_one_workflow_for_assessment
buyer_provides_safe_non_sensitive_evidence_only
operator_reviews_evidence_boundary_before_analysis
assessment_output_is_reviewed_before_buyer_delivery
final_price_and_terms_are_operator_approved

## Approval Requirements

The proposal includes three approval requirements.

### Evidence Boundary Approval

Approval:

evidence_boundary_approval

Required by:

operator

Purpose:

Confirm proposed evidence is safe for assessment intake.

Required:

true

### Commercial Terms Approval

Approval:

commercial_terms_approval

Required by:

operator

Purpose:

Confirm final price, scope, and payment terms.

Required:

true

### Buyer Scope Acknowledgement

Approval:

buyer_scope_acknowledgement

Required by:

buyer

Purpose:

Confirm workflow boundary and excluded scope.

Required:

true

## Proposal Risk Controls

The proposal includes four risk controls.

### Non-Binding Proposal Until Operator Approval

Control:

non_binding_proposal_until_operator_approval

Purpose:

Prevent automated commitment to pricing or terms.

Required:

true

### Safe Evidence Boundary Required

Control:

safe_evidence_boundary_required

Purpose:

Prevent regulated, federal, secret, or live telemetry intake.

Required:

true

### Excluded Scope Must Be Visible

Control:

excluded_scope_must_be_visible

Purpose:

Make production, compliance, and legal exclusions clear.

Required:

true

### Human Review Before Sending

Control:

human_review_before_sending

Purpose:

Ensure proposal language is reviewed before buyer delivery.

Required:

true

## Source Offer Section

The source_offer section preserves key paid-assessment offer identity.

Default source offer values:

offer_type: assessment_factory_lite_paid_assessment_offer
offer_stage: paid_assessment_conversion
release: assessment-factory-lite-buyer-conversion
version: 1.8.0
recommended_action: present_paid_assessment_offer

## Next Action

The next_action section includes:

action
operator_instruction
future_action

Default action:

review_and_prepare_proposal

Operator instruction:

Review the proposal-ready artifact, confirm evidence boundary, approve commercial terms, and decide whether to generate a formal proposal document.

Future action:

generate_formal_proposal

## Custom Buyer Context Example

The endpoint supports custom buyer context.

Example custom buyer context:

primary_buyer: founder_operator
workflow_area: security review workflow
duration: 5_to_7_business_days
price_low: 1500
price_high: 3500

Expected custom values:

proposal title: Assessment Factory Lite Proposal for security review workflow
primary buyer: founder_operator
workflow area: security review workflow
duration: 5_to_7_business_days
recommended price band: 1500 to 3500

## Relationship to Assessment Offer Builder

The assessment offer builder creates the bounded paid-assessment offer.

The proposal builder converts that offer into a proposal-ready artifact.

The offer builder answers:

What paid assessment should we offer?

The proposal builder answers:

How should that offer be structured as a reviewable proposal draft?

## Relationship to Proposal HTML View

The proposal builder returns structured proposal data.

A future proposal HTML view may render the proposal into a buyer-facing proposal screen.

The proposal builder should remain deterministic and reusable by future document, HTML, and PDF exporters.

## Relationship to Formal Proposal Documents

The proposal-ready artifact is not yet a formal proposal document.

A future formal proposal generator may create a polished proposal, PDF, statement of work draft, or sales document.

This service only creates the deterministic proposal structure.

## Commercial Boundary

The proposal builder does not create a binding quote, binding sales contract, invoice, or legal agreement.

The recommended price band remains operator-approved and non-binding.

The operator must approve final scope, price, payment terms, proposal expiration, and evidence boundaries before sending a formal proposal to a buyer.

## Compliance Boundary

The Assessment Factory Lite Proposal Builder does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides deterministic proposal structure for a bounded paid-assessment conversation.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Proposal Builder does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, or live integrations.

It helps the operator convert a commercial offer into a proposal-ready artifact while preserving evidence boundaries.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt proposal language, but AI must not override deterministic assessment boundaries, evidence boundaries, approval requirements, or commercial terms without human-approved policy changes.
