# Assessment Factory Lite Buyer Walkthrough Script

## Purpose

The Assessment Factory Lite Buyer Walkthrough Script documents the buyer-facing talk track for presenting the demo.

It helps the operator explain the product clearly, frame the buyer problem, walk through sample scenarios, explain the top friction finding, describe the recommended intervention, preserve the demo-only boundary, answer objections, and close toward a paid assessment conversation.

This document turns the technical demo package into a repeatable buyer communication artifact.

## Capability Chain

Assessment Factory Lite Demo Package
→ Delivery Packaging Release
→ Buyer Walkthrough Script Service
→ Buyer Walkthrough Script Endpoint
→ Opening Script
→ Problem Frame
→ Scenario Script
→ Finding Script
→ Intervention Script
→ Boundary Script
→ Buyer Questions
→ Close Script
→ Objection Responses
→ Buyer Demo Conversion

## Service

### AssessmentFactoryLiteBuyerWalkthroughScriptService

File:

backend/app/gagf/assessment_factory_lite_buyer_walkthrough_script_service.py

Purpose:

Build the buyer-facing walkthrough script for Assessment Factory Lite.

The service returns deterministic buyer-facing language for presenting the demo.

## Endpoint

### Buyer Walkthrough Script Endpoint

GET /products/assessment-factory-lite/buyer-walkthrough/script

Purpose:

Returns the Assessment Factory Lite buyer walkthrough script.

The Operator Workstation can use this endpoint to fetch the opening script, problem frame, scenario explanations, finding explanation, intervention explanation, boundary explanation, buyer questions, close script, objection responses, success criteria, and demo-only boundary.

## Response Contract

The buyer walkthrough script response includes:

status
script_type
package_name
release
version
script_stage
script_summary
opening_script
problem_frame
scenario_script
finding_script
intervention_script
boundary_script
buyer_questions
close_script
objection_responses
success_criteria
demo_boundary
operator_message
recommended_action

## Script Type

The script_type value is:

assessment_factory_lite_buyer_walkthrough_script

## Release Marker

The buyer walkthrough script object belongs to:

release:

assessment-factory-lite-demo-delivery-packaging

version:

1.7.0

## Script Stage

The script_stage value is:

buyer_demo_conversion

## Recommended Action

The recommended_action value is:

use_buyer_walkthrough_script

## Script Summary

The script summary defines the buyer-demo purpose.

Primary operator:

founder_operator

Target audience:

operations_leader
it_manager
workflow_owner
early_buyer

Delivery mode:

guided_buyer_walkthrough

Estimated duration:

10_to_20_minutes

Conversion goal:

move_from_demo_interest_to_paid_assessment_conversation

Positioning:

Assessment Factory Lite shows where work gets stuck, why it creates drag, and what small operational test to try first.

## Opening Script

Section:

opening

Title:

Open with operational friction

Operator script:

This is a sample-data-only demo of Assessment Factory Lite. The goal is to show how workflow evidence can reveal where work gets stuck, explain the top source of drag, and suggest a focused intervention to test first.

Buyer takeaway:

The buyer should understand that the product diagnoses workflow drag without needing production data for the demo.

Duration:

1_to_2_minutes

## Problem Frame

Section:

problem_frame

Title:

Frame the buyer problem

Operator script:

Most teams feel delays before they can prove them. Work waits on approvals, ownership, dependencies, or unclear handoffs. Assessment Factory Lite turns those workflow signals into a clear friction finding.

Buyer takeaway:

The demo is about making hidden operational drag visible.

Proof point:

sample workflow events become a ranked friction finding

## Scenario Script

The buyer walkthrough script includes three scenario explanations:

standard
invalid
empty

## Standard Scenario Script

Scenario:

standard

Label:

Approval Delay and Blocked Work

When to use:

default_buyer_demo

Operator script:

I will start with the standard scenario. It uses synthetic workflow rows showing approval delay and blocked work. This lets us demonstrate the diagnostic flow safely.

Buyer takeaway:

Approval delay can be detected from workflow evidence.

Expected friction:

approval_delay

## Invalid Scenario Script

Scenario:

invalid

Label:

Unsafe Data Boundary Test

When to use:

trust_and_safety_explanation

Operator script:

This scenario intentionally contains unsafe sample rows. The system rejects them before producing buyer-facing findings.

Buyer takeaway:

The demo protects the sample-data-only boundary.

Expected friction:

none

## Empty Scenario Script

Scenario:

empty

Label:

Empty Demo Starting State

When to use:

screen_initialization_explanation

Operator script:

This scenario shows the empty starting state before sample rows are loaded.

Buyer takeaway:

The operator can show the demo state before evidence is added.

Expected friction:

none

## Finding Script

Section:

finding

Title:

Explain the top friction finding

Operator script:

In this sample scenario, the top friction point is approval delay. That means the workflow is not mainly blocked by execution effort; it is slowed by waiting for a required decision or approval path.

Buyer takeaway:

The buyer should see that the product identifies the constraint, not just the symptoms.

Example finding:

Approval delays are creating workflow drag.

Evidence link:

synthetic approval and blocked-work events

## Intervention Script

Section:

intervention

Title:

Explain the recommended intervention

Operator script:

The recommended intervention is to streamline the approval path. That does not mean removing accountability. It means testing a narrow improvement such as clearer ownership, faster routing, or a smaller approval threshold.

Buyer takeaway:

The product moves from diagnosis to a practical next test.

Recommended intervention:

streamline_approval_path

Buyer value:

reduce waiting time and make approval ownership clearer

## Boundary Script

Section:

boundary

Title:

Explain the demo-only boundary

Operator script:

This demo uses synthetic sample data only. We should not upload real customer data, regulated data, federal data, secrets, or live security telemetry into this demo path.

Buyer takeaway:

The buyer should trust that the demo does not require sensitive data.

Allowed data:

sample_csv
synthetic_workflow_events
mock_approval_events
mock_delay_events

Prohibited data:

real_customer_data
regulated_data
federal_data
production_customer_data
customer_secrets
live_security_telemetry

## Buyer Questions

The script includes four buyer questions:

workflow_similarity
evidence_source
first_test
buyer_value

## Workflow Similarity Question

Question type:

workflow_similarity

Question:

Which part of this sample workflow most resembles where your team gets stuck?

Purpose:

connect the demo to the buyer's real workflow

## Evidence Source Question

Question type:

evidence_source

Question:

What safe, non-sensitive workflow evidence could we inspect first?

Purpose:

identify possible assessment inputs

## First Test Question

Question type:

first_test

Question:

If approval delay is the issue, what is the smallest approval-path test worth trying?

Purpose:

move toward a focused assessment or pilot

## Buyer Value Question

Question type:

buyer_value

Question:

If we could show your top workflow constraint clearly, who would need to see that result?

Purpose:

identify stakeholders and buying path

## Close Script

Section:

close

Title:

Close with the assessment offer

Operator script:

The next step would not be a big deployment. It would be a small, bounded assessment using safe evidence to identify one or two high-friction workflow constraints and recommend a focused test.

Buyer takeaway:

The buyer should understand the next step as low-risk, bounded, and evidence-driven.

Call to action:

schedule_paid_assessment_conversation

## Objection Responses

The script includes responses to four expected buyer objections:

we_do_not_want_to_upload_sensitive_data
we_already_know_where_the_problem_is
this_looks_like_project_management
is_this_production_ready

## Sensitive Data Objection

Objection:

we_do_not_want_to_upload_sensitive_data

Response:

That is the right concern. This demo is sample-data-only, and a real assessment should start by defining safe evidence boundaries before any data is reviewed.

## Known Problem Objection

Objection:

we_already_know_where_the_problem_is

Response:

That may be true. The value here is turning that belief into traceable evidence, ranking the constraint, and choosing the smallest useful intervention.

## Project Management Objection

Objection:

this_looks_like_project_management

Response:

Project management tracks work. Assessment Factory Lite focuses on governance friction: approvals, ownership gaps, handoffs, dependencies, and decision delays.

## Production Ready Objection

Objection:

is_this_production_ready

Response:

This package is a sample-data-only buyer demo. Production use, regulated data, compliance claims, and live integrations are outside this demo boundary.

## Success Criteria

The buyer walkthrough script success criteria are:

buyer_understands_sample_data_only_boundary
buyer_understands_operational_friction_problem
buyer_understands_standard_scenario
buyer_understands_top_friction_finding
buyer_understands_recommended_intervention
buyer_identifies_workflow_similarity
buyer_can_name_possible_safe_evidence_source
operator_can_transition_to_assessment_offer

## Relationship to Operator Runbook

The operator runbook explains how to deliver the demo.

The buyer walkthrough script explains what to say during the buyer-facing parts of the demo.

The runbook is operational.

The buyer walkthrough script is communicative and commercial.

## Relationship to Delivery Readiness

The delivery readiness service verifies whether the demo package is ready.

The buyer walkthrough script assumes the package is ready and helps the operator communicate the value clearly.

Readiness answers:

Can we deliver the demo?

The buyer walkthrough script answers:

How do we explain the demo to a buyer?

## Relationship to Assessment Offer

The buyer walkthrough script is designed to move from demo interest to a paid assessment conversation.

It does not promise production deployment.

It closes toward a small, bounded assessment using safe evidence.

## Demo-Only Boundary

The buyer walkthrough script remains demo-only.

Allowed data:

sample_csv
synthetic_workflow_events
mock_approval_events
mock_delay_events

Prohibited data:

real_customer_data
regulated_data
federal_data
production_customer_data
customer_secrets
live_security_telemetry

certification_claims_allowed:

false

## Excluded Scope

The buyer walkthrough script explicitly excludes:

production_customer_data_processing
regulated_data_processing
federal_data_processing
fedramp_or_hipaa_certification_claims
soc_2_audit_claims
wcag_certification_claims
autonomous_remediation
live_customer_integrations
production_customer_deployment
formal_security_authorization
third_party_audit_claims
persistent_file_upload_storage
customer_tenant_storage
pdf_generation
payment_processing
live_customer_remediation
production_workflow_changes
guaranteed_operational_outcomes
binding_consulting_commitments

## Compliance Boundary

The Assessment Factory Lite Buyer Walkthrough Script does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides deterministic buyer-facing language for a demo-only workflow.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Buyer Walkthrough Script does not autonomously approve production launch, production data use, customer deployment, certification claims, or live integrations.

It helps the operator communicate a deterministic sample-data-only demo while preserving evidence boundaries.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain or adapt the walkthrough language, but AI must not override deterministic demo boundaries without human-approved policy changes.
