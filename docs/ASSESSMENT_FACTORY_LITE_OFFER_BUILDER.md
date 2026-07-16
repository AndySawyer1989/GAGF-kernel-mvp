# Assessment Factory Lite Assessment Offer Builder

## Purpose

The Assessment Factory Lite Assessment Offer Builder documents how the buyer walkthrough converts into a bounded paid-assessment offer.

It gives the operator a deterministic offer structure with a target buyer, problem statement, safe evidence request, assessment scope, excluded scope, deliverable, recommended price band, buyer commitment, qualification questions, risk controls, and next action.

This layer turns demo interest into a concrete assessment conversation without claiming production readiness, compliance certification, or binding pricing.

## Capability Chain

Assessment Factory Lite Demo Package
→ Buyer Conversion Release
→ Buyer Walkthrough Script
→ Assessment Offer Builder Service
→ Assessment Offer Builder Endpoint
→ Paid Assessment Offer
→ Safe Evidence Request
→ Bounded Scope
→ Buyer Summary Deliverable
→ Operator-Approved Price Band
→ Assessment Conversation

## Service

### AssessmentFactoryLiteOfferBuilderService

File:

backend/app/gagf/assessment_factory_lite_offer_builder_service.py

Purpose:

Build a bounded paid-assessment offer for Assessment Factory Lite.

The service returns a deterministic assessment offer that can be reviewed by the operator before presenting it to a buyer.

## Endpoint

### Assessment Offer Endpoint

POST /products/assessment-factory-lite/assessment-offer

Purpose:

Returns a bounded paid-assessment offer.

The endpoint accepts optional buyer_context and walkthrough_script inputs.

The Operator Workstation can use this endpoint to generate a target buyer profile, problem statement, safe evidence request, assessment scope, deliverable, recommended price band, buyer commitment, qualification questions, risk controls, next action, and intake boundary.

## Request Contract

The request body may include:

buyer_context
walkthrough_script

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

## Walkthrough Script Input

The walkthrough_script object may be supplied when the operator wants to build an offer from a known buyer walkthrough.

If walkthrough_script is not supplied, the service builds the offer from the default buyer walkthrough script.

## Response Contract

The assessment offer response includes:

status
offer_type
package_name
release
version
offer_stage
target_buyer
problem_statement
safe_evidence_request
assessment_scope
excluded_scope
deliverable
recommended_price_band
buyer_commitment
qualification_questions
risk_controls
next_action
source_script
demo_boundary
operator_message
recommended_action

## Offer Type

The offer_type value is:

assessment_factory_lite_paid_assessment_offer

## Release Marker

The assessment offer object belongs to:

release:

assessment-factory-lite-buyer-conversion

version:

1.8.0

## Offer Stage

The offer_stage value is:

paid_assessment_conversion

## Recommended Action

The recommended_action value is:

present_paid_assessment_offer

## Target Buyer

The default target buyer is:

operations_leader

Secondary buyers:

it_manager
workflow_owner
founder_operator

Default buyer pain:

approval delays, ownership gaps, handoff delays, and workflow drag

Best fit context:

A team that feels operational delay but needs clearer evidence before choosing an intervention.

## Problem Statement

The default workflow area is:

approval and handoff workflow

Default friction hypothesis:

approval_delay

Problem statement purpose:

Identify the highest-friction constraint, explain its operational impact, and recommend a focused test.

Buyer value:

Move from suspected workflow drag to traceable evidence and a small intervention candidate.

## Safe Evidence Request

The safe evidence request type is:

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

## Assessment Scope

The assessment scope type is:

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

Success definition:

Buyer receives one clear friction finding, one evidence-backed intervention recommendation, and one practical next test.

## Excluded Scope

The assessment offer explicitly excludes:

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

## Deliverable

The deliverable type is:

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

Buyer value:

A concise evidence-backed summary that can be reviewed with operations, IT, or workflow owners.

## Recommended Price Band

Default currency:

USD

Default low price:

500

Default high price:

2500

Pricing model:

fixed_fee_discovery_assessment

Pricing note:

Final pricing is operator-approved and should not be treated as an automated binding quote.

## Buyer Commitment

The buyer commitment type is:

small_bounded_assessment

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

## Qualification Questions

The offer builder reuses buyer walkthrough questions for offer qualification.

Question types:

workflow_similarity
evidence_source
first_test
buyer_value

All four default buyer walkthrough questions are used for the offer.

## Workflow Similarity Question

Purpose:

Connect the demo to the buyer's real workflow.

Used for offer:

true

## Evidence Source Question

Purpose:

Identify possible assessment inputs.

Used for offer:

true

## First Test Question

Purpose:

Move toward a focused assessment or pilot.

Used for offer:

true

## Buyer Value Question

Purpose:

Identify stakeholders and buying path.

Used for offer:

true

## Risk Controls

The risk controls are:

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

## Next Action

Default action:

schedule_paid_assessment_conversation

Default recommended message:

Based on the demo, the next step is a small bounded assessment focused on one workflow and safe non-sensitive evidence.

Operator instruction:

Confirm buyer interest, define the workflow boundary, confirm safe evidence sources, and approve final price before sending the offer.

## Source Script

The source_script field preserves the source buyer walkthrough script identity.

Default source script values:

script_type: assessment_factory_lite_buyer_walkthrough_script
script_stage: buyer_demo_conversion
recommended_action: use_buyer_walkthrough_script

## Custom Buyer Context

The offer builder supports custom buyer context.

Example custom fields:

primary_buyer: founder_operator
workflow_area: security review workflow
duration: 5_to_7_business_days
price_low: 1500
price_high: 3500

When custom context is provided, the offer updates target buyer, workflow area, duration, and price band.

## Demo and Assessment Intake Boundary

The assessment offer uses a demo and assessment intake boundary.

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

## Relationship to Buyer Walkthrough Script

The buyer walkthrough script explains the demo.

The assessment offer builder converts buyer interest into a bounded paid-assessment offer.

The walkthrough asks:

Where does this resemble your workflow?

The offer builder answers:

What assessment could we safely propose next?

## Relationship to Buyer Conversion Release

The buyer conversion release made the demo presentable.

The assessment offer builder makes the demo commercially actionable.

It is the first step from buyer demo conversion into paid assessment packaging.

## Relationship to Future Proposal Builder

The assessment offer builder is not yet a full proposal generator.

A future proposal builder may turn the offer into a polished proposal, PDF, statement of work, or sales document.

This service only creates the deterministic offer structure.

## Commercial Boundary

The assessment offer builder does not create a binding quote.

The recommended price band is an operator-reviewed estimate.

The operator must approve the final price before presenting it to a buyer.

The service does not process payments, create contracts, or commit to legal terms.

## Compliance Boundary

The Assessment Factory Lite Assessment Offer Builder does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides a deterministic paid-assessment offer structure for safe, bounded, non-sensitive evidence review.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Assessment Offer Builder does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, or live integrations.

It helps the operator convert demo interest into a bounded assessment offer while preserving evidence boundaries.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt offer language, but AI must not override deterministic assessment boundaries or commercial terms without human-approved policy changes.
