# Assessment Factory Lite Operator Runbook

## Purpose

The Assessment Factory Lite Operator Runbook documents how to deliver the demo in a repeatable live walkthrough.

It gives the operator a clear procedure for preparing the demo, explaining the product, loading scenarios, showing findings, presenting buyer-facing export copy, protecting the demo-only data boundary, and asking follow-up questions.

The runbook supports discovery calls, early buyer walkthroughs, and repeatable founder-led demos.

## Capability Chain

Assessment Factory Lite Demo Package
→ Delivery Manifest
→ Operator Runbook Service
→ Operator Runbook Endpoint
→ Pre-Demo Checklist
→ Live Demo Sequence
→ Scenario Talking Points
→ Safety Rules
→ Stop Conditions
→ Buyer Follow-Up
→ Success Criteria
→ Demo Delivery Packaging

## Service

### AssessmentFactoryLiteOperatorRunbookService

File:

backend/app/gagf/assessment_factory_lite_operator_runbook_service.py

Purpose:

Build the live-demo operator runbook for Assessment Factory Lite.

The service returns a deterministic runbook for repeatable demo delivery.

## Endpoint

### Operator Runbook Endpoint

GET /products/assessment-factory-lite/delivery/runbook

Purpose:

Returns the Assessment Factory Lite live-demo operator runbook.

The Operator Workstation can use this endpoint to fetch the pre-demo checklist, live demo sequence, scenario talking points, safety rules, stop conditions, buyer follow-up prompts, success criteria, and demo-only boundary.

## Response Contract

The operator runbook response includes:

status
runbook_type
package_name
release
version
runbook_stage
runbook_summary
pre_demo_checklist
live_demo_sequence
scenario_talking_points
operator_safety_rules
stop_conditions
buyer_follow_up
success_criteria
demo_boundary
operator_message
recommended_action

## Runbook Type

The runbook_type value is:

assessment_factory_lite_demo_operator_runbook

## Release Marker

The operator runbook object belongs to:

release:

assessment-factory-lite-demo-styling-export

version:

1.6.0

## Runbook Stage

The runbook_stage value is:

demo_delivery_packaging

## Recommended Action

The recommended_action value is:

use_operator_runbook_for_demo_delivery

## Runbook Summary

The runbook summary defines the demo purpose and audience.

Primary operator:

founder_operator

Target audience:

operations_leader
it_manager
workflow_owner
early_buyer

Delivery mode:

live_walkthrough

Estimated duration:

10_to_20_minutes

Positioning:

Show how FIP identifies operational friction, explains the top constraint, recommends a focused intervention, and presents buyer-ready findings.

## Pre-Demo Checklist

The pre-demo checklist verifies that the operator has everything needed before the walkthrough.

Required checks:

version_endpoint_ready
delivery_manifest_available
scenario_menu_available
styled_html_screen_available
buyer_export_polish_available
demo_boundary_visible

## Version Endpoint Ready Check

Check:

version_endpoint_ready

Instruction:

Confirm the system version endpoint responds successfully.

Expected:

1.6.0 assessment-factory-lite-demo-styling-export

Required:

true

## Delivery Manifest Available Check

Check:

delivery_manifest_available

Instruction:

Open the delivery manifest before the walkthrough.

Expected:

delivery manifest returns status ok

Required:

true

## Scenario Menu Available Check

Check:

scenario_menu_available

Instruction:

Confirm the scenario menu shows standard, invalid, and empty choices.

Expected:

three primary scenarios are visible

Required:

true

## Styled HTML Screen Available Check

Check:

styled_html_screen_available

Instruction:

Render the standard scenario in the HTML screen.

Expected:

styled screen includes Demo Scenario Menu and Sample Data Loader

Required:

true

## Buyer Export Polish Available Check

Check:

buyer_export_polish_available

Instruction:

Generate polished buyer export copy from the standard sample rows.

Expected:

buyer export polish returns present_polished_buyer_export

Required:

true

## Demo Boundary Visible Check

Check:

demo_boundary_visible

Instruction:

Confirm the demo-only sample-data boundary is visible.

Expected:

real customer, regulated, and federal data are prohibited

Required:

true

## Live Demo Sequence

The live demo sequence has seven steps:

1. Open with the problem
2. Show the scenario menu
3. Load the standard demo
4. Explain the finding
5. Show buyer export polish
6. Show boundary protection
7. Close with next evidence question

## Step 1: Open With the Problem

Operator action:

Explain that the demo identifies where work gets stuck.

Buyer message:

This demo shows how workflow evidence can reveal operational drag and suggest what to test first.

Endpoint or asset:

delivery_manifest

## Step 2: Show the Scenario Menu

Operator action:

Show the standard, invalid, and empty scenario choices.

Buyer message:

The demo uses synthetic scenarios so we can show the workflow without touching real customer data.

Endpoint or asset:

GET /products/assessment-factory-lite/demo-scenario-menu

## Step 3: Load the Standard Demo

Operator action:

Render the standard sample_scenario in the HTML screen.

Buyer message:

The standard scenario demonstrates approval delay and blocked work.

Endpoint or asset:

POST /products/assessment-factory-lite/demo-ui/html

## Step 4: Explain the Finding

Operator action:

Point to the top friction finding and recommended intervention.

Buyer message:

The system turns sample workflow events into a clear friction finding and a focused next step.

Endpoint or asset:

styled_html_screen

## Step 5: Show Buyer Export Polish

Operator action:

Show the polished buyer-facing export summary.

Buyer message:

This turns the diagnostic output into language that is easier for a buyer or manager to act on.

Endpoint or asset:

POST /products/assessment-factory-lite/buyer-export/polish

## Step 6: Show Boundary Protection

Operator action:

Demonstrate or explain the invalid boundary test.

Buyer message:

Unsafe rows are rejected before buyer-facing findings are generated.

Endpoint or asset:

invalid_boundary_test

## Step 7: Close With Next Evidence Question

Operator action:

Ask whether the sample friction resembles the buyer's workflow.

Buyer message:

If this resembles your workflow, the next step is deciding what safe evidence we would collect first.

Endpoint or asset:

buyer_follow_up

## Scenario Talking Points

The runbook includes talking points for:

standard
invalid
empty

## Standard Scenario Talking Point

Scenario:

standard

Label:

Approval Delay and Blocked Work

When to use:

default buyer demo

Operator talk track:

Use this scenario to show the core value: finding approval drag and recommending a focused intervention.

Expected message:

Approval delays are creating workflow drag.

Recommended intervention:

streamline_approval_path

## Invalid Scenario Talking Point

Scenario:

invalid

Label:

Unsafe Data Boundary Test

When to use:

trust and safety explanation

Operator talk track:

Use this scenario to show that unsafe or non-demo data is blocked before findings are presented.

Expected message:

Sample data needs repair before buyer presentation.

Recommended intervention:

repair_sample_csv_before_demo

## Empty Scenario Talking Point

Scenario:

empty

Label:

Empty Demo Starting State

When to use:

screen initialization explanation

Operator talk track:

Use this scenario to show the starting state before demo rows are loaded.

Expected message:

Add synthetic sample rows before running the demo.

Recommended intervention:

add_demo_rows

## Operator Safety Rules

The operator safety rules are:

use_sample_data_only
avoid_certification_claims
do_not_overstate_automation
preserve_traceability
ask_for_workflow_similarity

## Use Sample Data Only Rule

Rule:

use_sample_data_only

Instruction:

Do not use real customer, regulated, federal, or secret data.

Severity:

critical

## Avoid Certification Claims Rule

Rule:

avoid_certification_claims

Instruction:

Do not claim FedRAMP High, HIPAA, SOC 2, WCAG, or production readiness.

Severity:

critical

## Do Not Overstate Automation Rule

Rule:

do_not_overstate_automation

Instruction:

Do not say the demo autonomously remediates customer workflows.

Severity:

high

## Preserve Traceability Rule

Rule:

preserve_traceability

Instruction:

Keep polished buyer language tied to the source export summary.

Severity:

high

## Ask for Workflow Similarity Rule

Rule:

ask_for_workflow_similarity

Instruction:

Ask whether the sample scenario resembles the buyer's real workflow before proposing next evidence collection.

Severity:

medium

## Stop Conditions

The stop conditions are:

buyer_requests_real_data_upload
regulated_or_federal_data_is_offered
certification_claim_requested
unsafe_sample_rows_detected

## Buyer Requests Real Data Upload Stop Condition

Condition:

buyer_requests_real_data_upload

Operator response:

Pause and explain that this demo is sample-data-only.

Required action:

do_not_accept_real_customer_data

## Regulated or Federal Data Is Offered Stop Condition

Condition:

regulated_or_federal_data_is_offered

Operator response:

Stop the demo data flow and restate the prohibited data boundary.

Required action:

reject_regulated_or_federal_data

## Certification Claim Requested Stop Condition

Condition:

certification_claim_requested

Operator response:

Clarify that this demo does not make compliance certification claims.

Required action:

avoid_certification_claim

## Unsafe Sample Rows Detected Stop Condition

Condition:

unsafe_sample_rows_detected

Operator response:

Use the invalid scenario behavior to show boundary rejection.

Required action:

repair_sample_csv_before_demo

## Buyer Follow-Up

The runbook includes three buyer follow-up prompts:

workflow_similarity_question
evidence_source_question
first_intervention_question

## Workflow Similarity Question

Prompt:

Which part of this sample workflow most resembles where your team gets stuck?

Purpose:

connect demo finding to buyer context

## Evidence Source Question

Prompt:

What safe, non-sensitive workflow evidence could we inspect first?

Purpose:

identify possible assessment inputs

## First Intervention Question

Prompt:

If approval delay is the issue, what is the smallest approval-path test worth trying?

Purpose:

move toward a paid assessment or pilot

## Success Criteria

The runbook success criteria are:

operator_can_explain_problem_in_plain_language
scenario_menu_is_visible
standard_demo_renders_successfully
buyer_understands_top_friction_point
buyer_export_polish_is_presented
demo_boundary_is_explained
buyer_identifies_possible_real_workflow_parallel
no_real_customer_data_is_used

## Relationship to Delivery Manifest

The delivery manifest answers:

What is included in the package?

The operator runbook answers:

How should the operator deliver the demo?

The runbook depends on the delivery manifest but does not replace it.

## Relationship to Delivery Readiness

The runbook defines the procedure.

The future delivery readiness service should verify that the package is ready before the operator uses the runbook live.

## Relationship to Buyer Demo

The operator runbook helps the founder or operator make the demo understandable to a buyer.

It keeps the walkthrough focused on:

the problem
the scenario
the finding
the recommended intervention
the safety boundary
the next evidence question

## Demo-Only Boundary

The operator runbook remains demo-only.

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

The runbook explicitly excludes:

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

## Compliance Boundary

The Assessment Factory Lite Operator Runbook does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides deterministic operating instructions for a demo-only workflow.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Operator Runbook does not autonomously approve production launch, production data use, customer deployment, certification claims, or live integrations.

It guides demo delivery while preserving deterministic evidence, traceability, and sample-data boundaries.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain the runbook, but AI must not override deterministic runbook boundaries without human-approved policy changes.
