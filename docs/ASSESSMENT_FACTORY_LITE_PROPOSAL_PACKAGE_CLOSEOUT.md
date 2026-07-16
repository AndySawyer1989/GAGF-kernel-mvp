# Assessment Factory Lite Proposal Package Closeout

## Release

Release:

2.0.0

Release name:

assessment-factory-lite-proposal-package

Sprint:

4.9

Status:

complete

## Purpose

The Assessment Factory Lite Proposal Package release turns the commercial offer layer into a proposal-ready package.

This release adds a deterministic proposal builder, a proposal API endpoint, proposal documentation, a proposal HTML presentation view, a proposal HTML endpoint, proposal HTML documentation, and a formal proposal package release marker.

The product can now move from buyer interest to paid-assessment offer to proposal-ready artifact.

## What This Release Adds

Release 2.0.0 adds:

proposal builder service
proposal builder endpoint
proposal builder documentation
proposal HTML view service
proposal HTML view endpoint
proposal HTML view documentation
proposal package release marker
proposal package closeout documentation

## Product Meaning

Assessment Factory Lite now has a proposal package layer.

The commercial offer layer answers:

Can buyer interest become a bounded paid-assessment offer?

The proposal package layer answers:

Can that offer become a structured proposal-ready artifact with scope, evidence boundary, deliverables, timeline, commercial terms placeholder, approvals, controls, exclusions, and a presentation view?

## Completed Proposal Package Chain

The completed proposal package chain is:

Commercial Offer Release
→ Proposal Builder
→ Proposal Builder Endpoint
→ Proposal Builder Documentation
→ Proposal HTML View
→ Proposal HTML Endpoint
→ Proposal HTML Documentation
→ Proposal Package Release Marker

## Proposal Builder

The proposal builder answers:

What should the proposal contain?

Service:

AssessmentFactoryLiteProposalBuilderService

Endpoint:

POST /products/assessment-factory-lite/proposal

Proposal type:

assessment_factory_lite_paid_assessment_proposal

Object release:

assessment-factory-lite-commercial-offer

Object version:

1.9.0

Proposal stage:

proposal_ready_artifact

Purpose:

Create a deterministic proposal-ready artifact from a paid-assessment offer or buyer context.

## Proposal HTML View

The proposal HTML view answers:

How should the operator present the proposal?

Service:

AssessmentFactoryLiteProposalHTMLService

Endpoint:

POST /products/assessment-factory-lite/proposal/html

View type:

assessment_factory_lite_paid_assessment_proposal_html_view

Object release:

assessment-factory-lite-commercial-offer

Object version:

1.9.0

View stage:

proposal_ready_presentation

Purpose:

Turn the proposal-ready artifact into a presentation-ready HTML screen with buyer context, problem statement, proposed scope, evidence boundary, deliverables, timeline, commercial terms, approvals, risk controls, excluded scope, and next action.

## Release Marker

The system version endpoint now reports:

version:

2.0.0

release:

assessment-factory-lite-proposal-package

sprint:

4.9

status:

complete

Endpoint:

GET /version

## Preserved Object Contracts

Release 2.0.0 updates the system release marker only.

The proposal object contracts remain on the commercial offer release that created them:

proposal builder: 1.9.0 / assessment-factory-lite-commercial-offer
proposal HTML view: 1.9.0 / assessment-factory-lite-commercial-offer

The commercial offer object contracts remain preserved:

assessment offer builder: 1.8.0 / assessment-factory-lite-buyer-conversion
assessment offer HTML view: 1.8.0 / assessment-factory-lite-buyer-conversion

The buyer conversion object contracts remain preserved:

buyer walkthrough script: 1.7.0 / assessment-factory-lite-demo-delivery-packaging
buyer walkthrough HTML view: 1.7.0 / assessment-factory-lite-demo-delivery-packaging

The delivery package object contracts remain preserved:

delivery manifest: 1.6.0 / assessment-factory-lite-demo-styling-export
operator runbook: 1.6.0 / assessment-factory-lite-demo-styling-export
delivery readiness: 1.6.0 / assessment-factory-lite-demo-styling-export

Older internal object contracts also remain preserved:

UI view object: 1.1.0 / assessment-factory-lite-demo-package
HTML screen object: 1.2.0 / assessment-factory-lite-demo-ui
scenario menu object: 1.4.0 / assessment-factory-lite-demo-loader
style token object: 1.5.0 / assessment-factory-lite-demo-usability
buyer export polish object: 1.5.0 / assessment-factory-lite-demo-usability

## Proposal Package Content

The proposal package includes:

buyer context
problem statement
proposed scope
evidence boundary
deliverables
timeline
commercial terms placeholder
excluded scope
assumptions
approval requirements
proposal risk controls
source offer
next action
proposal HTML presentation view

## Buyer Context

Default primary buyer:

operations_leader

Default secondary buyers:

it_manager
workflow_owner
founder_operator

Default buyer pain:

approval delays, ownership gaps, handoff delays, and workflow drag

Best fit context:

A team that feels operational delay but needs clearer evidence before choosing an intervention.

## Problem Statement

Default workflow area:

approval and handoff workflow

Default friction hypothesis:

approval_delay

Purpose:

Explain the workflow friction hypothesis and why a bounded assessment is useful.

## Proposed Scope

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

Scope boundary:

This proposal covers one bounded workflow assessment using safe, non-sensitive evidence only.

## Evidence Boundary

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

The proposal package includes two default deliverables:

assessment_summary
recommended_next_test

## Assessment Summary

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

## Recommended Next Test

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

Default pricing model:

fixed_fee_discovery_assessment

Default currency:

USD

Default recommended price band:

USD 500 - 2500

Default payment terms:

operator_to_define

Default proposal expiration:

operator_to_define

Binding quote:

False

Pricing note:

Final pricing is operator-approved and should not be treated as an automated binding quote.

## Excluded Scope

The proposal package excludes:

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

## Assumptions

Default assumptions:

buyer_selects_one_workflow_for_assessment
buyer_provides_safe_non_sensitive_evidence_only
operator_reviews_evidence_boundary_before_analysis
assessment_output_is_reviewed_before_buyer_delivery
final_price_and_terms_are_operator_approved

## Approval Requirements

The proposal package includes three approval requirements:

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

## Proposal Risk Controls

The proposal package includes four risk controls:

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

## Source Offer

The proposal preserves key paid-assessment offer identity:

offer_type: assessment_factory_lite_paid_assessment_offer
offer_stage: paid_assessment_conversion
release: assessment-factory-lite-buyer-conversion
version: 1.8.0
recommended_action: present_paid_assessment_offer

## Next Action

Default action:

review_and_prepare_proposal

Operator instruction:

Review the proposal-ready artifact, confirm evidence boundary, approve commercial terms, and decide whether to generate a formal proposal document.

Future action:

generate_formal_proposal

## Proposal HTML Presentation View

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

The body data-view value is:

assessment-factory-lite-paid-assessment-proposal-html-view

The page title is:

Assessment Factory Lite Proposal

## Custom Buyer Context

The proposal builder and proposal HTML endpoint support custom buyer context.

Example custom fields:

primary_buyer: founder_operator
workflow_area: security review workflow
duration: 5_to_7_business_days
price_low: 1500
price_high: 3500

Expected custom values:

founder_operator
security review workflow
5_to_7_business_days
USD 1500 - 3500

## HTML Safety

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

## What Is Complete

The following proposal package components are complete:

proposal builder service
proposal builder endpoint
proposal builder documentation
proposal HTML view service
proposal HTML view endpoint
proposal HTML view documentation
proposal package release marker

## What Is Not Complete

The following remain future work:

proposal package closeout endpoint
formal proposal document generator
proposal PDF export
statement of work generator
terms and conditions workflow
payment processing
lead capture workflow
CRM integration
customer portal
production onboarding
real customer evidence intake
access control for proposal assets
signed proposal approval workflow
buyer signature workflow

## Product Readiness Meaning

Release 2.0.0 does not mean Assessment Factory Lite is production SaaS-ready.

It means the product can now move from buyer demo interest into a paid-assessment offer and then into a proposal-ready artifact.

The proposal remains non-binding until the operator approves final pricing, scope, evidence boundaries, terms, and buyer-facing language.

## Recommended Next Product Direction

The recommended next product direction is:

Formal Proposal Document Generator

Reason:

The proposal package is now structured and presentable.

The next bottleneck is turning the proposal-ready artifact into a formal document that can be shared outside the Operator Workstation.

## Suggested Next Story

US-230 — Assessment Factory Lite Formal Proposal Document Service

Purpose:

Create a deterministic formal proposal document object from the proposal-ready artifact.

The proposal document should include title, buyer summary, problem statement, assessment scope, evidence boundary, deliverables, timeline, commercial terms placeholders, assumptions, approvals, exclusions, operator notes, and next action.

## Commercial Boundary

The proposal package does not create a binding quote, binding sales contract, invoice, or legal agreement.

The recommended price band remains operator-approved and non-binding.

The operator must approve final scope, price, payment terms, proposal expiration, evidence boundaries, and buyer-facing language before sending a formal proposal to a buyer.

## Compliance Boundary

The Assessment Factory Lite Proposal Package release does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides deterministic proposal package structure for a bounded paid-assessment conversation.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Proposal Package release does not autonomously approve production launch, production data use, customer deployment, certification claims, binding price quotes, legal commitments, sales contracts, or live integrations.

It helps the operator convert a commercial offer into a proposal-ready package while preserving evidence boundaries.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt proposal language, but AI must not override deterministic assessment boundaries, evidence boundaries, approval requirements, or commercial terms without human-approved policy changes.
