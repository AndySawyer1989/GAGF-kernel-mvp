# Assessment Factory Lite Buyer Export Polish

## Purpose

The Assessment Factory Lite Buyer Export Polish layer converts raw demo export output into clearer buyer-facing language.

It improves the way findings, recommendations, next steps, and trust boundaries are presented during a live demo.

The polish layer does not change the underlying evidence, diagnostics, or deterministic decision path.

It only creates clearer presentation copy from accepted demo-only data.

## Capability Chain

Assessment Factory Lite Demo Package
→ Demo Diagnostics
→ Demo Export Summary
→ Buyer Export Polish Service
→ Buyer Export Polish Endpoint
→ Buyer-Facing Headline
→ Buyer-Facing Summary
→ Key Findings
→ Recommended Intervention
→ Next Steps
→ Trust and Boundary Note

## Service

### AssessmentFactoryLiteBuyerExportPolishService

File:

backend/app/gagf/assessment_factory_lite_buyer_export_polish_service.py

Purpose:

Build buyer-facing polished export copy for the Assessment Factory Lite demo.

The service accepts an existing export summary, diagnostics result, or raw sample rows.

## Endpoint

### Buyer Export Polish Endpoint

POST /products/assessment-factory-lite/buyer-export/polish

Purpose:

Returns a polished buyer-facing export summary for the Assessment Factory Lite demo.

## Accepted Inputs

The endpoint accepts:

rows
diagnostics_result
export_summary

## Input Mode 1: Rows

If rows are provided, the polish service builds the export summary first.

Flow:

rows
→ dataset validation
→ diagnostics
→ export summary
→ buyer export polish

## Input Mode 2: Diagnostics Result

If diagnostics_result is provided, the polish service builds the export summary from diagnostics.

Flow:

diagnostics_result
→ export summary
→ buyer export polish

## Input Mode 3: Export Summary

If export_summary is provided, the polish service uses it directly.

Flow:

export_summary
→ buyer export polish

## Response Contract

The successful polish response includes:

status
polish_type
package_name
release
version
buyer_headline
buyer_summary
key_findings
recommended_intervention
next_steps
trust_and_boundary_note
source_export_summary
operator_message
recommended_action

## Polish Type

The polish_type value is:

assessment_factory_lite_buyer_export_polish

## Release Marker

The buyer export polish object belongs to:

release:

assessment-factory-lite-demo-usability

version:

1.5.0

## Recommended Action

For successful polish output, recommended_action is:

present_polished_buyer_export

## Buyer Headline

buyer_headline provides a short buyer-facing statement about the workflow.

Example:

Operational drag is slowing work in the demo workflow.

The headline should be plain language and suitable for a buyer walkthrough.

## Buyer Summary

buyer_summary translates the export summary into buyer-facing language.

It should explain that the polished view turns demo diagnostics into findings and next steps.

The summary must remain tied to synthetic demo data.

## Key Findings

key_findings is a list of buyer-readable findings.

Each finding may include:

finding_type
rank
title
summary
severity
friction_label

## Standard Finding Behavior

For the standard sample scenario, the first key finding should identify approval delay.

Expected title:

Approval delays are creating workflow drag

Expected friction label:

approval_delay

## No Major Constraint Behavior

If no major constraint is found, the service returns a no-major-constraint finding.

Expected finding_type:

no_major_constraint

Expected friction label:

none

## Recommended Intervention

recommended_intervention provides a buyer-facing recommended action.

It includes:

intervention_type
title
summary
buyer_value
action

## Standard Recommended Intervention

For the standard sample scenario, expected intervention_type is:

streamline_approval_path

Expected title:

Streamline the approval path

Expected buyer value:

Reduce waiting time and make approval ownership clearer.

## Next Steps

next_steps provides short buyer-facing follow-up actions.

For standard accepted demo rows, the polished next steps are:

Review the top friction point with the workflow owner.
Choose one narrow intervention to test first.
Use the demo output to decide what evidence should be collected next.

## Trust and Boundary Note

trust_and_boundary_note explains the demo-only boundary.

It includes:

boundary_type
summary
allowed_data
prohibited_data
certification_claims_allowed

The boundary_type is:

demo_only_sample_data

## Rejected Input Behavior

If the source export summary is rejected, the polish result is also rejected.

Rejected status:

rejected

Rejected buyer_headline:

Sample data needs repair before buyer presentation.

Rejected recommended_action:

repair_sample_csv_before_demo

## Rejected Key Finding

Rejected unsafe data produces a key finding with:

finding_type:

sample_data_boundary_failure

title:

Unsafe or invalid sample rows detected

severity:

high

## Rejected Recommended Intervention

Rejected unsafe data produces:

title:

Repair the demo sample data

action:

repair_sample_csv_before_demo

## Rejected Next Steps

Rejected unsafe data should guide the operator to:

Replace unsafe rows with synthetic demo rows.
Run dataset contract validation again.
Regenerate the polished buyer export after validation passes.

## Relationship to Dataset Contract

The buyer export polish layer does not bypass dataset validation.

Unsafe rows must be rejected before buyer-facing findings are generated.

This protects the demo from presenting real, regulated, federal, or otherwise unsafe customer data.

## Relationship to Diagnostics

The buyer export polish layer does not replace diagnostics.

Diagnostics produce evidence-based findings.

Polish translates those findings into clearer buyer-facing language.

## Relationship to Export Summary

The buyer export polish layer does not replace the source export summary.

It preserves the source export summary under:

source_export_summary

This keeps the polished copy traceable to the underlying deterministic export.

## Operator Workstation Use

The Operator Workstation can call:

POST /products/assessment-factory-lite/buyer-export/polish

with rows, diagnostics_result, or export_summary.

The returned copy can be displayed in a buyer-facing export preview.

## Buyer Demo Use

During a buyer walkthrough, the polished export can help explain:

what friction was found
why it matters
what intervention is recommended
what the buyer should do next
what the demo-only data boundary means

## Product Strategy Meaning

The buyer export polish layer improves presentation quality without weakening deterministic governance.

It helps Assessment Factory Lite feel more like a product and less like raw backend output.

This supports:

founder-led demos
early buyer discovery calls
operations leader walkthroughs
IT manager walkthroughs
repeatable sales demos
executive summary previews

## Demo-Only Boundary

The buyer export polish layer remains demo-only.

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

This story does not add:

PDF generation
persistent export storage
customer tenant storage
production customer data processing
regulated data processing
federal data processing
FedRAMP High certification claims
HIPAA certification claims
SOC 2 audit claims
WCAG certification claims
autonomous remediation
live customer integrations
formal security authorization
third-party audit claims
interactive export builder
frontend browser JavaScript

## Compliance Boundary

The Assessment Factory Lite Buyer Export Polish layer does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides deterministic buyer-facing copy for a demo-only workflow.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Buyer Export Polish layer does not autonomously approve production launch, production data use, customer deployment, certification claims, or live integrations.

It presents deterministic demo findings in clearer buyer-facing language.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later assist with explanation, but AI must not override deterministic evidence, sample-data boundaries, or human-approved policy changes.
