# Assessment Factory Lite Demo Diagnostics

## Purpose

The Assessment Factory Lite Demo Diagnostics Runner converts validated synthetic demo rows into a demo-ready governance diagnostic result.

It produces a governance drag summary, top friction points, recommended intervention, export-ready summary, operator message, and recommended action.

This is the first Assessment Factory Lite layer that turns safe sample data into visible demo value.

## Diagnostics Flow

Sample CSV Rows
→ Dataset Contract Validation
→ Demo Diagnostics Runner
→ Governance Drag Summary
→ Top Friction Points
→ Recommended Intervention
→ Export-Ready Summary
→ Operator Message
→ Recommended Action

## Service

### AssessmentFactoryLiteDemoDiagnosticsService

File:

backend/app/gagf/assessment_factory_lite_demo_diagnostics_service.py

Purpose:

validated demo rows
→ governance drag summary
→ top friction points
→ recommended intervention
→ demo diagnostic result
→ export-ready summary

## Endpoint

### Demo Diagnostics Run Endpoint

POST /products/assessment-factory-lite/demo-diagnostics/run

Purpose:

Runs Assessment Factory Lite demo diagnostics against demo-only synthetic workflow rows.

## Input Contract

The endpoint expects:

rows

Each row should follow the Assessment Factory Lite Dataset Contract.

Required fields:

event_id
case_id
event_type
actor
team
timestamp
severity
description

Optional fields:

expected_state
observed_state
duration_minutes
constraint_label
contains_real_customer_data
contains_regulated_data
contains_federal_data

## Valid Input Example

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
    },
    {
      "event_id": "evt-002",
      "case_id": "case-001",
      "event_type": "approval_delayed",
      "actor": "approver",
      "team": "operations",
      "timestamp": "2026-01-01T13:00:00Z",
      "severity": "high",
      "description": "Synthetic approval delayed.",
      "constraint_label": "approval_delay",
      "duration_minutes": 240
    }
  ]
}

## Output Contract

The diagnostics runner returns:

status
diagnostic_type
row_count
validation
governance_drag_summary
top_friction_points
recommended_intervention
export_ready_summary
operator_message
recommended_action

## Diagnostic Type

The diagnostic_type value is:

assessment_factory_lite_demo_diagnostics

## Dataset Validation

Before diagnostics run, the service validates rows with:

AssessmentFactoryLiteDatasetContractService

If validation succeeds, diagnostics continue.

If validation fails, diagnostics are rejected.

## Valid Diagnostics Result

For valid rows, status is:

ok

For valid rows, recommended_action is:

export_demo_summary

The valid result includes:

validation
governance_drag_summary
top_friction_points
recommended_intervention
export_ready_summary

## Rejected Diagnostics Result

For invalid rows, status is:

rejected

Rejected rows return:

dataset_validation_failed

The rejected result includes:

recommended_action:

repair_sample_csv_before_demo

recommended_intervention:

repair_sample_csv_before_demo

export_ready_summary:

is_export_ready false

This prevents invalid or unsafe data from entering the demo diagnostic layer.

## Governance Drag Summary

governance_drag_summary includes:

total_events
drag_event_count
critical_or_high_event_count
total_delay_minutes
event_type_counts
severity_counts
governance_drag_score
drag_level

## Drag Event Types

The runner treats these event types as governance drag events:

approval_delayed
work_blocked
dependency_wait
handoff_delayed
ownership_gap
environment_failure
escalation

## Governance Drag Score

governance_drag_score combines:

drag event ratio
high or critical severity ratio
delay factor

The score is deterministic and rounded.

## Drag Levels

drag_level may be:

none
low
moderate
high
critical

## Top Friction Points

top_friction_points identifies the highest-priority friction labels.

Each friction point includes:

friction_label
event_count
case_count
total_delay_minutes
high_or_critical_count
priority_score

The service uses constraint_label when present.

If constraint_label is missing, it falls back to event_type.

## Priority Score

priority_score uses:

event_count
high_or_critical_count
total_delay_minutes

Higher scores indicate stronger demo friction.

The list is sorted by priority_score, total_delay_minutes, and event_count.

## Recommended Intervention

recommended_intervention translates the top friction point into a demo action.

Possible intervention types include:

streamline_approval_path
clarify_ownership_and_handoffs
stabilize_operational_path
review_top_constraint
continue_monitoring
add_demo_rows
repair_sample_csv_before_demo

## Approval Friction

If the top friction label contains approval, the service recommends:

streamline_approval_path

Reason:

approval_friction_detected

## Handoff or Dependency Friction

If the top friction label is work_blocked, dependency_wait, or handoff_delayed, the service recommends:

clarify_ownership_and_handoffs

Reason:

handoff_or_dependency_friction_detected

## Operational Instability

If the top friction label is environment_failure or escalation, the service recommends:

stabilize_operational_path

Reason:

operational_instability_detected

## Empty Rows Behavior

If rows is empty or missing, diagnostics return status ok.

The service recommends:

add_demo_rows

Reason:

no_demo_rows_available

This allows the Operator Workstation to initialize diagnostics before a sample CSV is uploaded.

## Export-Ready Summary

export_ready_summary prepares the result for a future report/export object.

It includes:

is_export_ready
report_sections
executive_summary
top_friction_label
recommended_intervention_type
compliance_disclaimer

## Report Sections

report_sections include:

executive_summary
sample_data_boundary
governance_drag_findings
top_constraints
recommended_intervention
next_steps
compliance_disclaimer

## Compliance Disclaimer

The export-ready summary includes a compliance disclaimer.

It states that demo output is based only on synthetic sample data and does not certify FedRAMP High, HIPAA compliance, SOC 2, or production readiness.

## Operator Message

For successful diagnostics, operator_message states:

Assessment Factory Lite demo diagnostics completed using demo-only synthetic workflow events.

For rejected diagnostics, operator_message states that diagnostics cannot run until the sample CSV passes the demo-only dataset contract.

## Recommended Actions

Successful diagnostics:

export_demo_summary

Rejected diagnostics:

repair_sample_csv_before_demo

Empty rows:

add_demo_rows

## Relationship to Dataset Contract

The Dataset Contract decides whether rows are safe.

The Demo Diagnostics Runner decides what the safe rows show.

Dataset Contract answers:

Can these rows be accepted?

Demo Diagnostics answers:

What governance drag and friction do these rows demonstrate?

## Relationship to Future Export Summary

The next implementation layer should convert the diagnostics result into a clean export object.

The export service should use:

governance_drag_summary
top_friction_points
recommended_intervention
export_ready_summary
compliance_disclaimer

## Demo-Only Boundary

The diagnostics runner must only process demo-only synthetic data.

Allowed data:

sample_csv
synthetic_workflow_events
mock_approval_events
mock_delay_events
approval_or_delay_examples

Prohibited data:

real customer data
regulated data
federal data
production customer data
customer secrets
live security telemetry

## Compliance Boundary

The Assessment Factory Lite Demo Diagnostics Runner does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It produces a demo diagnostic result from synthetic sample data only.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Demo Diagnostics Runner does not autonomously approve production launch, production data use, or customer deployment.

It provides deterministic demo diagnostic output.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain diagnostics later, but AI must not override deterministic diagnostics or demo-only boundaries without human-approved policy changes.
