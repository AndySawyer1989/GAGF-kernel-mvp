# Assessment Factory Lite Demo UI View

## Purpose

The Assessment Factory Lite Demo UI View defines the Operator Workstation rendering contract for the demo package.

It combines the demo profile, dataset contract, diagnostics result, export summary, UI sections, cards, operator actions, warnings, source payloads, and demo-only data boundary into one view object.

This view lets the Operator Workstation render the full Assessment Factory Lite demo path from one API call.

## UI View Flow

Rows, Checkpoint, Diagnostics Result, or Export Summary
→ Assessment Factory Lite Demo UI View Service
→ Demo Profile
→ Dataset Contract
→ Diagnostics Result
→ Export Summary
→ UI Sections
→ Cards
→ Operator Actions
→ Warnings
→ Data Boundary
→ Source Payloads

## Service

### AssessmentFactoryLiteDemoUIViewService

File:

backend/app/gagf/assessment_factory_lite_demo_ui_view_service.py

Purpose:

demo profile + dataset contract + diagnostics + export summary
→ unified UI view contract
→ cards
→ panels
→ sections
→ operator actions
→ demo-only warnings

## Endpoint

### Demo UI View Endpoint

POST /products/assessment-factory-lite/demo-ui/view

Purpose:

Builds the Operator Workstation demo UI view for the Assessment Factory Lite Demo Package.

## Input Modes

The endpoint may receive:

checkpoint
rows
diagnostics_result
export_summary

## Rows Input

If rows are provided, the service runs diagnostics and export summary generation.

Rows must follow the Assessment Factory Lite dataset contract.

## Diagnostics Result Input

If diagnostics_result is provided, the service uses it instead of rerunning diagnostics.

## Export Summary Input

If export_summary is provided, the service uses it instead of rebuilding the export summary.

## Empty Payload Behavior

If no rows, diagnostics_result, or export_summary is provided, the view still renders.

The diagnostics result is built from an empty rows list.

The operator action becomes:

add_synthetic_sample_rows

## Output Contract

The UI view returns:

status
view_type
package_name
release
version
ui_sections
cards
operator_actions
warnings
data_boundary
source_payloads
operator_message
recommended_action

## View Type

The view_type value is:

assessment_factory_lite_demo_ui_view

## Package Name

The package_name value is:

Assessment Factory Lite Demo Package

## Release

The release value is:

assessment-factory-lite-demo-package

## Version

The version value is:

1.1.0

## Recommended Action

The recommended_action value is:

render_assessment_factory_lite_demo_view

## UI Sections

ui_sections defines the Operator Workstation layout.

Sections include:

demo_readiness
sample_data_boundary
dataset_contract
dataset_validation
governance_drag_summary
top_friction_points
recommended_intervention
export_summary_preview
next_steps
compliance_disclaimer

## Cards

cards defines the card-level UI contract.

Each card includes:

card_id
title
status
summary
primary_value
action

## Demo Readiness Card

Card id:

demo_readiness_card

Purpose:

Shows whether the demo profile is ready.

The card uses:

demo_readiness
ready_for_demo_package
decision
reason
recommended_action

## Sample Data Boundary Card

Card id:

sample_data_boundary_card

Purpose:

Shows that the demo-only sample-data boundary is enforced.

The primary value is:

demo_only_sample_data

The action is:

enforce_sample_data_boundary

## Dataset Contract Card

Card id:

dataset_contract_card

Purpose:

Shows that the sample CSV contract is available.

The primary value is:

assessment_factory_lite_sample_csv

The action is:

show_dataset_contract

## Dataset Validation Card

Card id:

dataset_validation_card

Purpose:

Shows whether sample rows passed validation.

Possible statuses:

passed
failed

If validation passed, the action is:

run_demo_diagnostics

If validation failed, the action is:

repair_sample_csv_before_demo

## Governance Drag Summary Card

Card id:

governance_drag_summary_card

Purpose:

Displays the synthetic workflow governance drag score and drag level.

The card uses:

governance_drag_score
drag_level

The action is:

review_governance_drag_summary

## Top Friction Points Card

Card id:

top_friction_points_card

Purpose:

Displays the highest priority friction point.

The card uses:

top_friction_points
friction_label

The action is:

review_top_friction_points

## Recommended Intervention Card

Card id:

recommended_intervention_card

Purpose:

Displays the recommended intervention from the export summary.

The card uses:

recommended_intervention
intervention_type
priority
reason

The action is:

review_recommended_intervention

## Export Summary Preview Card

Card id:

export_summary_preview_card

Purpose:

Displays the executive summary preview and report title.

The card uses:

executive_summary
report_title
recommended_action

## Operator Actions

operator_actions define what the Operator Workstation should show next.

For valid rows, actions include:

review_demo_readiness
review_sample_data_boundary
review_governance_drag_summary
review_top_friction_points
review_recommended_intervention
review_demo_export_summary

For invalid rows, actions include:

repair_sample_csv_before_demo
rerun_dataset_validation
rerun_demo_diagnostics

For empty rows, actions include:

add_synthetic_sample_rows
rerun_demo_diagnostics
generate_demo_export_summary

## Warnings

warnings define high-visibility operator notices.

Warning types include:

demo_only_boundary
no_certification_claims

## Demo-Only Boundary Warning

The demo_only_boundary warning tells the operator to use synthetic sample data only.

It prohibits:

real customer data
regulated data
federal data
secret data
live telemetry data

## No Certification Claims Warning

The no_certification_claims warning states that the demo does not certify:

FedRAMP High
HIPAA compliance
SOC 2
production readiness
customer deployment readiness

## Data Boundary

data_boundary preserves the sample-data-only constraint.

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

## Source Payloads

source_payloads preserve the underlying deterministic source objects.

The source payloads include:

profile
dataset_contract
diagnostics_result
export_summary

These objects allow the UI to render a summary while preserving traceable source context.

## Operator Message

The operator_message states:

Assessment Factory Lite demo UI view is ready for the Operator Workstation using demo-only synthetic data.

## Relationship to Demo Export Summary

Demo Export Summary produces the buyer-facing report object.

Demo UI View packages that report object with view sections, cards, operator actions, and warnings.

Demo Export Summary answers:

What should the buyer-facing report say?

Demo UI View answers:

How should the Operator Workstation render the demo flow?

## Relationship to Operator Workstation

The Operator Workstation should call:

POST /products/assessment-factory-lite/demo-ui/view

The UI should render:

demo readiness card
sample data boundary card
dataset contract card
dataset validation card
governance drag summary card
top friction points card
recommended intervention card
export summary preview card

## Demo-Only Boundary

The UI view must preserve the sample-data-only demo boundary.

It must not encourage upload of real customer data, regulated data, federal data, production customer data, customer secrets, or live security telemetry.

## Compliance Boundary

The Assessment Factory Lite Demo UI View does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It renders a demo-only Operator Workstation view from synthetic sample data and deterministic demo outputs.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Demo UI View does not autonomously approve production launch, production data use, customer deployment, certification claims, or live integrations.

It provides deterministic UI rendering guidance.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain UI view results later, but AI must not override deterministic UI boundaries without human-approved policy changes.
