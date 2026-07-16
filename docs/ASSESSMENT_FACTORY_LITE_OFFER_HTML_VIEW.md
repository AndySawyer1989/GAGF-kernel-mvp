# Assessment Factory Lite Assessment Offer HTML View

## Purpose

The Assessment Factory Lite Assessment Offer HTML View documents the presentation-ready paid-assessment offer screen.

It turns the bounded assessment offer into structured HTML that the Operator Workstation can render after a buyer expresses interest in the demo.

The view helps the operator present the target buyer, problem statement, safe evidence request, assessment scope, deliverable, recommended price band, buyer commitment, qualification questions, risk controls, next action, demo boundary, and excluded scope.

## Capability Chain

Assessment Factory Lite Demo Package
→ Buyer Conversion Release
→ Assessment Offer Builder Service
→ Assessment Offer Builder Endpoint
→ Assessment Offer HTML View Service
→ Assessment Offer HTML View Endpoint
→ Presentation-Ready Paid Assessment Offer
→ Operator Review
→ Buyer Assessment Conversation

## Service

### AssessmentFactoryLiteOfferHTMLService

File:

backend/app/gagf/assessment_factory_lite_offer_html_service.py

Purpose:

Render the Assessment Factory Lite paid-assessment offer as HTML.

The service returns presentation-ready HTML plus the source offer and view section contract.

## Endpoint

### Assessment Offer HTML Endpoint

POST /products/assessment-factory-lite/assessment-offer/html

Purpose:

Returns the Assessment Factory Lite paid-assessment offer HTML view.

The Operator Workstation can use this endpoint to fetch a presentation-ready offer screen.

## Request Contract

The request body may include:

offer
buyer_context

## Offer Input

The offer object may be supplied when the operator wants to render a previously generated paid-assessment offer.

If offer is not supplied, the service builds an offer from the default offer builder.

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

If buyer_context is supplied, the generated HTML view reflects the custom buyer, workflow area, duration, and price band.

## Response Contract

The assessment offer HTML view response includes:

status
view_type
package_name
release
version
view_stage
html
source_offer
view_sections
operator_message
recommended_action

## View Type

The view_type value is:

assessment_factory_lite_paid_assessment_offer_html_view

## Release Marker

The assessment offer HTML view object belongs to:

release:

assessment-factory-lite-buyer-conversion

version:

1.8.0

## View Stage

The view_stage value is:

paid_assessment_conversion

## Recommended Action

The recommended_action value is:

present_paid_assessment_offer_html_view

## View Sections

The HTML view includes these sections:

offer_header
target_buyer
problem_statement
safe_evidence_request
assessment_scope
deliverable
recommended_price_band
buyer_commitment
qualification_questions
risk_controls
next_action
demo_boundary
excluded_scope

## HTML Document Structure

The HTML output includes:

doctype declaration
html lang attribute
page title
body data-view attribute
offer header
target buyer card
problem statement card
safe evidence request card
assessment scope card
deliverable card
recommended price band card
buyer commitment card
qualification questions card
risk controls card
next action card
demo and assessment intake boundary panel
excluded scope panel

The body data-view value is:

assessment-factory-lite-paid-assessment-offer-html-view

The page title is:

Assessment Factory Lite Paid Assessment Offer

## Offer Header

The offer header identifies the view as a paid assessment offer.

It displays:

Paid Assessment Offer
version
Assessment Factory Lite Demo Package
paid_assessment_conversion
assessment_factory_lite_paid_assessment_offer

## Target Buyer Section

The target buyer section displays:

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
problem statement
default friction hypothesis
buyer value

Default workflow area:

approval and handoff workflow

Default friction hypothesis:

approval_delay

Purpose:

Explain the highest-friction constraint and why a focused assessment is useful.

## Safe Evidence Request Section

The safe evidence request section displays:

request type
requested sources
allowed format
prohibited data
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

Prohibited data:

real_customer_secrets
regulated_health_data
federal_sensitive_data
credentials
live_security_telemetry

Collection rule:

Collect the minimum safe evidence needed to diagnose one workflow.

## Assessment Scope Section

The assessment scope section displays:

scope type
workflow area
duration
included work
success definition

Scope type:

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

## Deliverable Section

The deliverable section displays:

deliverable type
format
sections
buyer value

Deliverable type:

assessment_factory_lite_buyer_summary

Default format:

markdown_or_pdf_ready_summary

Deliverable sections:

executive_summary
evidence_boundary
workflow_friction_finding
top_constraint
recommended_intervention
next_test
excluded_scope

## Recommended Price Band Section

The recommended price band section displays:

currency
low price
high price
pricing model
pricing note

Default price band:

USD 500 - 2500

Pricing model:

fixed_fee_discovery_assessment

Pricing note:

Final pricing is operator-approved and should not be treated as an automated binding quote.

## Buyer Commitment Section

The buyer commitment section displays what each side provides.

Buyer provides:

one_workflow_to_assess
safe_non_sensitive_evidence
workflow_owner_contact
review_time_for_findings

Operator provides:

evidence_boundary_review
friction_diagnostic_summary
recommended_intervention
next_test_summary

## Qualification Questions Section

The qualification questions section renders buyer walkthrough questions used for the offer.

Question types:

workflow_similarity
evidence_source
first_test
buyer_value

These questions connect the demo to the buyer's workflow, evidence source, first test, and stakeholder path.

## Risk Controls Section

The risk controls section displays:

sample_or_redacted_data_only
operator_price_approval
excluded_scope_visibility
human_review_before_delivery

## Sample or Redacted Data Only Control

Purpose:

Keep assessment intake within safe evidence boundaries.

Required:

true

## Operator Price Approval Control

Purpose:

Prevent automated binding pricing commitments.

Required:

true

## Excluded Scope Visibility Control

Purpose:

Make production, compliance, and regulated-data exclusions explicit.

Required:

true

## Human Review Before Delivery Control

Purpose:

Ensure the buyer summary is reviewed before presentation.

Required:

true

## Next Action Section

The next action section displays:

action
recommended message
operator instruction

Default action:

schedule_paid_assessment_conversation

Default recommended message:

Based on the demo, the next step is a small bounded assessment focused on one workflow and safe non-sensitive evidence.

Operator instruction:

Confirm buyer interest, define the workflow boundary, confirm safe evidence sources, and approve final price before sending the offer.

## Demo and Assessment Intake Boundary Section

The boundary section displays:

boundary type
allowed data
prohibited data
certification claims allowed
binding price quote allowed

Boundary type:

demo_and_assessment_intake_boundary

Allowed data:

sample_csv
synthetic_workflow_events
sanitized_csv
redacted_workflow_export
manual_workflow_summary

Prohibited data:

real_customer_secrets
regulated_health_data
federal_sensitive_data
production_customer_data_without_review
credentials
live_security_telemetry

certification_claims_allowed:

false

binding_price_quote_allowed:

false

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

## Custom Context Example

The endpoint supports custom buyer context.

Example custom buyer context:

primary_buyer: founder_operator
workflow_area: security review workflow
price_low: 1500
price_high: 3500

Expected rendered values:

founder_operator
security review workflow
USD 1500 - 3500

## Styling

The HTML view uses simple inline CSS variables and cards.

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

The view uses cards, pills, boundary panels, and a prominent price style.

The price style class is:

afl-price

## Escaping and Safety

The HTML renderer escapes dynamic offer values.

This protects the offer view from rendering raw unsafe markup when custom buyer context or custom offer content is passed into the renderer.

Escaped values include:

package name
offer stage
offer type
buyer fields
workflow area
problem statement
safe evidence values
scope values
deliverable values
price values
qualification questions
risk controls
next action values
boundary values
excluded scope values

## Relationship to Assessment Offer Builder

The assessment offer builder creates the deterministic offer structure.

The assessment offer HTML view turns that offer into a presentation-ready screen.

The offer builder answers:

What should we offer?

The HTML view answers:

How should the operator present the offer?

## Relationship to Buyer Conversion Release

The buyer conversion release made the demo presentable.

The assessment offer HTML view makes the paid-assessment offer presentable.

It is a bridge from buyer interest to a commercial assessment conversation.

## Relationship to Future Proposal Builder

The assessment offer HTML view is not a full proposal generator.

A future proposal builder may turn the offer into a formal proposal, PDF, statement of work, or sales document.

This view only presents the deterministic offer structure for operator review and buyer discussion.

## Commercial Boundary

The assessment offer HTML view does not create a binding quote.

The recommended price band is an operator-reviewed estimate.

The operator must approve the final price before presenting it to a buyer.

The view does not process payments, create contracts, or commit to legal terms.

## Compliance Boundary

The Assessment Factory Lite Assessment Offer HTML View does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides a deterministic presentation view for a bounded paid-assessment offer.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Assessment Offer HTML View does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, or live integrations.

It helps the operator present a bounded assessment offer while preserving evidence boundaries.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt offer presentation language, but AI must not override deterministic assessment boundaries or commercial terms without human-approved policy changes.

