# Assessment Factory Lite Demo Export Summary

## Purpose

The Assessment Factory Lite Demo Export Summary converts demo diagnostics into a clean buyer-facing report object.

It packages the executive summary, sample-data boundary, governance drag findings, top constraints, recommended intervention, next steps, compliance disclaimer, export metadata, operator message, and recommended action.

This is the first Assessment Factory Lite layer designed to support a polished demo walkthrough.

## Export Flow

Sample Rows or Existing Diagnostics Result
→ Demo Diagnostics
→ Export Summary Service
→ Executive Summary
→ Sample Data Boundary
→ Governance Drag Findings
→ Top Constraints
→ Recommended Intervention
→ Next Steps
→ Compliance Disclaimer
→ Export Metadata

## Service

### AssessmentFactoryLiteDemoExportService

File:

backend/app/gagf/assessment_factory_lite_demo_export_service.py

Purpose:

demo diagnostics result
→ clean report/export object
→ executive summary
→ findings
→ top constraints
→ recommended intervention
→ next steps
→ compliance disclaimer

## Endpoint

### Demo Export Summary Endpoint

POST /products/assessment-factory-lite/demo-export/summary

Purpose:

Builds an Assessment Factory Lite demo export summary from raw synthetic rows or an existing diagnostics result.

## Input Mode 1 - Rows

The endpoint may receive:

rows

In this mode, the export service runs demo diagnostics first and then builds the export summary.

Example:

{
  "rows": [
    {
      "event_id": "evt-001",
      "case_id": "case-001",
      "event_type": "approval_requested",
      "actor": "requester",
      "team": "operations",
      "timestamp": "2026-01-01T09:00:00Z",
      "severity": "medium",
      "description": "Synthetic approval request submitted.",
      "constraint_label": "approval_required",
      "duration_minutes": 0
    }
  ]
}

## Input Mode 2 - Diagnostics Result

The endpoint may receive:

diagnostics_result

In this mode, the export service uses the existing diagnostics result and converts it into an export summary.

## Empty Payload Behavior

If no rows or diagnostics_result is provided, the service treats rows as an empty list.

The result remains deterministic and recommends:

add_demo_rows

## Output Contract

The export summary returns:

status
export_type
package_name
source_diagnostic_type
row_count
report_title
executive_summary
sample_data_boundary
governance_drag_findings
top_constraints
recommended_intervention
next_steps
compliance_disclaimer
export_metadata
operator_message
recommended_action

## Export Type

The export_type value is:

assessment_factory_lite_demo_export_summary

## Package Name

The package_name value is:

Assessment Factory Lite Demo Package

## Report Title

The report_title value is:

Assessment Factory Lite Demo Summary

## Successful Export Result

For valid demo rows or a valid diagnostics result, status is:

ok

The recommended_action is:

review_demo_export_summary

## Rejected Export Result

If diagnostics are rejected because dataset validation failed, status is:

rejected

The recommended_action is:

repair_sample_csv_before_demo

The rejected export includes:

dataset_validation_failed

The next steps include:

repair_sample_csv_before_demo
rerun_dataset_validation
rerun_demo_diagnostics

## Executive Summary

executive_summary provides a plain-language summary of the demo result.

It describes:

total synthetic workflow events analyzed
governance drag events found
demo drag level
synthetic delay minutes observed

If no rows are present, it tells the operator to add synthetic demo rows.

## Sample Data Boundary

sample_data_boundary preserves the demo-only boundary.

The boundary_type is:

demo_only_sample_data

Allowed data includes:

sample_csv
synthetic_workflow_events
mock_approval_events
mock_delay_events

Prohibited data includes:

real_customer_data
regulated_data
federal_data
production_customer_data
customer_secrets
live_security_telemetry

certification_claims_allowed is false.

## Governance Drag Findings

governance_drag_findings includes:

available
total_events
drag_event_count
critical_or_high_event_count
total_delay_minutes
governance_drag_score
drag_level

If validation failed, governance_drag_findings has:

available false
reason dataset_validation_failed

## Top Constraints

top_constraints converts top friction points into ranked report constraints.

Each top constraint includes:

rank
constraint_label
event_count
case_count
total_delay_minutes
priority_score

## Recommended Intervention

recommended_intervention includes:

intervention_type
priority
target_friction_label
reason

Example intervention types include:

streamline_approval_path
clarify_ownership_and_handoffs
stabilize_operational_path
review_top_constraint
continue_monitoring
add_demo_rows
repair_sample_csv_before_demo

## Next Steps

next_steps turns the intervention into operator actions.

For normal successful exports, next_steps include:

review_governance_drag_summary
review_top_constraints
review_recommended_intervention
prepare_buyer_demo_walkthrough

For empty rows, next_steps include:

add_synthetic_sample_rows
rerun_demo_diagnostics
generate_demo_export_summary

For rejected diagnostics, next_steps include:

repair_sample_csv_before_demo
rerun_dataset_validation
rerun_demo_diagnostics

## Compliance Disclaimer

compliance_disclaimer states that the export is based only on synthetic sample data.

It also states that the export does not certify:

FedRAMP High
HIPAA compliance
SOC 2
production readiness
customer deployment readiness

## Export Metadata

export_metadata includes:

is_export_ready
source_status
validation_status
demo_only
report_sections

report_sections include:

executive_summary
sample_data_boundary
governance_drag_findings
top_constraints
recommended_intervention
next_steps
compliance_disclaimer

## Operator Message

For successful exports, operator_message states:

Assessment Factory Lite demo export summary is ready for review using synthetic sample data only.

For rejected exports, operator_message states that the export cannot be generated until the sample CSV passes the demo-only dataset contract.

## Relationship to Demo Diagnostics

Demo Diagnostics produces the analytical result.

Demo Export Summary packages that result into a buyer-facing report object.

Demo Diagnostics answers:

What did the synthetic workflow rows show?

Demo Export Summary answers:

How should the result be presented in the demo?

## Relationship to Operator Workstation

The Operator Workstation can call:

POST /products/assessment-factory-lite/demo-export/summary

The UI can display:

executive_summary
governance_drag_findings
top_constraints
recommended_intervention
next_steps
compliance_disclaimer

## Demo-Only Boundary

The export summary must only represent demo-only synthetic data.

It must not claim production readiness, customer deployment readiness, FedRAMP authorization, HIPAA compliance, SOC 2 audit status, or formal certification.

Allowed data:

sample_csv
synthetic_workflow_events
mock_approval_events
mock_delay_events

Prohibited data:

real customer data
regulated data
federal data
production customer data
customer secrets
live security telemetry

## Compliance Boundary

The Assessment Factory Lite Demo Export Summary does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It creates a buyer-facing demo report object from synthetic sample data only.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Demo Export Summary does not autonomously approve production launch, production data use, or customer deployment.

It provides deterministic demo export guidance.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain export summaries later, but AI must not override deterministic export boundaries without human-approved policy changes.
