# Assessment Factory Lite Proposal HTML View

## Purpose

The Assessment Factory Lite Proposal HTML View renders the proposal-ready artifact as a presentation-ready HTML screen.

It gives the Operator Workstation a structured view for presenting the proposal after the paid-assessment offer has been converted into a proposal-ready artifact.

The view presents buyer context, problem statement, proposed scope, evidence boundary, deliverables, timeline, commercial terms placeholder, approval requirements, proposal risk controls, excluded scope, and next action.

## Capability Chain

Assessment Factory Lite Demo Package
→ Commercial Offer Release
→ Proposal Builder Service
→ Proposal Builder Endpoint
→ Proposal HTML View Service
→ Proposal HTML View Endpoint
→ Proposal Presentation View
→ Operator Review
→ Buyer Proposal Discussion

## Service

### AssessmentFactoryLiteProposalHTMLService

File:

backend/app/gagf/assessment_factory_lite_proposal_html_service.py

Purpose:

Render the Assessment Factory Lite proposal-ready artifact as HTML.

The service can render from an existing proposal object, an existing offer object, or buyer_context.

## Endpoint

### Proposal HTML Endpoint

POST /products/assessment-factory-lite/proposal/html

Purpose:

Returns the Assessment Factory Lite proposal HTML view.

The Operator Workstation can use this endpoint to fetch a proposal presentation screen.

## Request Contract

The request body may include:

proposal
offer
buyer_context

## Proposal Input

The proposal object may be supplied when the operator wants to render a previously generated proposal-ready artifact.

If proposal is supplied, the HTML renderer uses it directly.

## Offer Input

The offer object may be supplied when the operator wants to build a proposal from an existing paid-assessment offer and immediately render it as HTML.

If proposal is not supplied and offer is supplied, the proposal builder converts the offer into proposal data before rendering HTML.

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

If proposal and offer are not supplied, the service builds a proposal from buyer_context.

## Response Contract

The proposal HTML view response includes:

status
view_type
package_name
release
version
view_stage
html
source_proposal
view_sections
operator_message
recommended_action

## View Type

The view_type value is:

assessment_factory_lite_paid_assessment_proposal_html_view

## Release Marker

The proposal HTML view object belongs to:

release:

assessment-factory-lite-commercial-offer

version:

1.9.0

## View Stage

The view_stage value is:

proposal_ready_presentation

## Recommended Action

The recommended_action value is:

present_proposal_html_view

## View Sections

The proposal HTML view includes:

proposal_header
buyer_context
problem_statement
proposed_scope
evidence_boundary
deliverables
timeline
commercial_terms_placeholder
approval_requirements
proposal_risk_controls
excluded_scope
next_action

## HTML Document Structure

The HTML output includes:

doctype declaration
html lang attribute
page title
body data-view attribute
proposal header
buyer context card
problem statement card
proposed scope card
evidence boundary card
deliverables card
timeline card
commercial terms placeholder card
approval requirements card
proposal risk controls card
excluded scope card
next action card

The body data-view value is:

assessment-factory-lite-paid-assessment-proposal-html-view

The page title is:

Assessment Factory Lite Proposal

## Proposal Header

The proposal header displays:

Proposal-Ready Artifact
version
proposal title
proposal type
proposal stage

Default proposal title:

Assessment Factory Lite Proposal for approval and handoff workflow

Default proposal type:

assessment_factory_lite_paid_assessment_proposal

Default proposal stage:

proposal_ready_artifact

## Buyer Context Section

The buyer context section displays:

primary buyer
secondary buyers
buyer pain
best fit context

Default primary buyer:

operations_leader

Default secondary buyers:

it_manager
workflow_owner
founder_operator

Default buyer pain:

approval delays, ownership gaps, handoff delays, and workflow drag

## Problem Statement Section

The problem statement section displays:

workflow area
statement
default friction hypothesis
buyer value

Default workflow area:

approval and handoff workflow

Default friction hypothesis:

approval_delay

Purpose:

Explain the workflow friction hypothesis and why a bounded assessment is useful.

## Proposed Scope Section

The proposed scope section displays:

scope type
workflow area
duration
included work
scope boundary
success definition

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

The evidence boundary section displays:

request type
requested sources
allowed formats
allowed data
prohibited data
certification claims allowed
binding price quote allowed
collection rule

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

## Deliverables Section

The deliverables section displays each proposal deliverable as a card.

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

## Timeline Section

The timeline section displays:

estimated duration
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

## Commercial Terms Placeholder Section

The commercial terms placeholder section displays:

recommended price band
pricing model
payment terms
proposal expiration
binding quote
pricing note

Default price band:

USD 500 - 2500

Default pricing model:

fixed_fee_discovery_assessment

Default payment terms:

operator_to_define

Default proposal expiration:

operator_to_define

Binding quote:

False

Pricing note:

Final pricing is operator-approved and should not be treated as an automated binding quote.

## Approval Requirements Section

The approval requirements section displays:

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

## Proposal Risk Controls Section

The proposal risk controls section displays:

non_binding_proposal_until_operator_approval
safe_evidence_boundary_required
excluded_scope_must_be_visible
human_review_before_sending

## Non-Binding Proposal Until Operator Approval

Purpose:

Prevent automated commitment to pricing or terms.

Required:

True

## Safe Evidence Boundary Required

Purpose:

Prevent regulated, federal, secret, or live telemetry intake.

Required:

True

## Excluded Scope Must Be Visible

Purpose:

Make production, compliance, and legal exclusions clear.

Required:

True

## Human Review Before Sending

Purpose:

Ensure proposal language is reviewed before buyer delivery.

Required:

True

## Excluded Scope Section

The excluded scope section displays:

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

## Next Action Section

The next action section displays:

action
operator instruction
future action

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

Expected rendered values:

founder_operator
security review workflow
5_to_7_business_days
USD 1500 - 3500

## Styling

The HTML view uses inline CSS variables and reusable card styles.

Core style tokens include:

afl-brand-orange
afl-brand-gold
afl-brand-purple
afl-surface
afl-surface-alt
afl-text-primary
afl-text-secondary
afl-border-subtle
afl-card-radius
afl-font-family

The proposal HTML view uses:

afl-proposal-header
afl-card
afl-pill
afl-boundary
afl-price
afl-phase

## Escaping and Safety

The proposal HTML renderer escapes dynamic proposal values.

This helps prevent raw unsafe markup from rendering if custom buyer context, custom offer content, or custom proposal content is passed into the renderer.

Escaped values include:

proposal title
proposal type
proposal stage
buyer fields
workflow area
problem statement
scope values
evidence boundary values
deliverable values
timeline phase values
commercial terms values
approval values
risk control values
excluded scope values
next action values

## Relationship to Proposal Builder

The proposal builder creates the deterministic proposal-ready artifact.

The proposal HTML view turns that artifact into a presentation-ready screen.

The proposal builder answers:

What should the proposal contain?

The proposal HTML view answers:

How should the operator present the proposal?

## Relationship to Offer HTML View

The offer HTML view presents the paid-assessment offer.

The proposal HTML view presents the proposal-ready artifact.

The offer view supports the buyer conversation before proposal review.

The proposal view supports the buyer conversation after proposal structure exists.

## Relationship to Future Formal Proposal Documents

The proposal HTML view is not a formal proposal document.

A future formal proposal generator may create a polished proposal, PDF, statement of work draft, or sales document.

This view only presents the deterministic proposal structure for operator review and buyer discussion.

## Commercial Boundary

The proposal HTML view does not create a binding quote, binding sales contract, invoice, or legal agreement.

The recommended price band remains operator-approved and non-binding.

The operator must approve final scope, price, payment terms, proposal expiration, evidence boundaries, and buyer-facing language before sending a formal proposal to a buyer.

## Compliance Boundary

The Assessment Factory Lite Proposal HTML View does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides a deterministic presentation view for a bounded paid-assessment proposal.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Proposal HTML View does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, or live integrations.

It helps the operator present a proposal-ready artifact while preserving evidence boundaries.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt proposal presentation language, but AI must not override deterministic assessment boundaries, evidence boundaries, approval requirements, or commercial terms without human-approved policy changes.
