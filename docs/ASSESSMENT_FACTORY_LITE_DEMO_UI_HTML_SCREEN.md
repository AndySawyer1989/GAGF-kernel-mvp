# Assessment Factory Lite Demo UI HTML Screen

## Purpose

The Assessment Factory Lite Demo UI HTML Screen renders the Operator Workstation demo view into deterministic HTML.

It converts the Assessment Factory Lite Demo UI View into a visible screen containing the HTML shell, demo cards, safety warnings, buyer-facing export preview, operator actions, and demo-only data boundary messaging.

This screen is the first visible Operator Workstation rendering layer for the Assessment Factory Lite Demo Package.

## HTML Screen Flow

Rows, Checkpoint, Diagnostics Result, Export Summary, or UI View
→ Assessment Factory Lite Demo UI View
→ Assessment Factory Lite Demo UI HTML Service
→ Deterministic HTML Shell
→ Demo Safety Warnings
→ Operator Demo Cards
→ Buyer-Facing Export Preview
→ Operator Actions
→ Display-Ready HTML Screen

## Service

### AssessmentFactoryLiteDemoUIHTMLService

File:

backend/app/gagf/assessment_factory_lite_demo_ui_html_service.py

Purpose:

demo UI view contract
→ Operator Workstation HTML screen
→ demo cards
→ warnings
→ sample data boundary
→ buyer-facing preview layout

## Endpoint

### Demo UI HTML Endpoint

POST /products/assessment-factory-lite/demo-ui/html

Purpose:

Renders the Assessment Factory Lite Operator Workstation demo screen as deterministic HTML.

## Input Modes

The endpoint may receive:

checkpoint
rows
diagnostics_result
export_summary
ui_view

## Rows Input

If rows are provided, the service builds the UI view from rows, then renders HTML.

Rows must follow the Assessment Factory Lite dataset contract.

## Checkpoint Input

If checkpoint is provided, the service can build the profile portion of the UI view from the checkpoint.

## Diagnostics Result Input

If diagnostics_result is provided, the service can use it instead of rerunning diagnostics.

## Export Summary Input

If export_summary is provided, the service can use it instead of rebuilding the export summary.

## UI View Input

If ui_view is provided, the HTML service renders directly from that UI view.

This prevents unnecessary recomputation when the Operator Workstation already has a view object.

## Output Contract

The HTML endpoint returns:

status
screen_type
package_name
release
version
html
ui_view
operator_message
recommended_action

## Screen Type

The screen_type value is:

assessment_factory_lite_demo_ui_html_screen

## Package Name

The package_name value is:

Assessment Factory Lite Demo Package

## Release

The release value is:

assessment-factory-lite-demo-ui

## Version

The version value is:

1.2.0

## Recommended Action

The recommended_action value is:

display_assessment_factory_lite_demo_screen

## HTML Shell

The rendered HTML includes:

doctype declaration
html language attribute
head element
meta charset
viewport metadata
title
body data-screen attribute
main screen container

The body data-screen value is:

assessment-factory-lite-demo-ui-html-screen

## Page Title

The HTML title is:

Assessment Factory Lite Demo

## Header

The screen header includes:

FIP/GAGF Operator Workstation
Assessment Factory Lite Demo
Sample-data-only buyer demo path
release
version

## Demo Safety Warnings

The HTML screen renders warnings from the UI view.

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

## Operator Demo Cards

The HTML screen renders one article per UI card.

Rendered card ids include:

demo_readiness_card
sample_data_boundary_card
dataset_contract_card
dataset_validation_card
governance_drag_summary_card
top_friction_points_card
recommended_intervention_card
export_summary_preview_card

## Card Fields

Each rendered card displays:

card_id
title
status
summary
primary_value
action

## Export Preview

The Buyer-Facing Export Preview section displays:

executive_summary
compliance_disclaimer

The executive summary comes from the export summary source payload.

The compliance disclaimer states that the demo is based only on synthetic sample data and does not certify FedRAMP High, HIPAA compliance, SOC 2, production readiness, or customer deployment readiness.

## Operator Actions

The HTML screen renders operator actions as an ordered list.

For valid rows, actions may include:

review_demo_readiness
review_sample_data_boundary
review_governance_drag_summary
review_top_friction_points
review_recommended_intervention
review_demo_export_summary

For invalid rows, actions may include:

repair_sample_csv_before_demo
rerun_dataset_validation
rerun_demo_diagnostics

For empty rows, actions may include:

add_synthetic_sample_rows
rerun_demo_diagnostics
generate_demo_export_summary

## Invalid Rows Behavior

If rows fail dataset validation, the UI view source payload records a rejected diagnostics result.

The rendered HTML includes repair guidance such as:

repair_sample_csv_before_demo

This keeps invalid or unsafe rows from being presented as valid demo findings.

## HTML Escaping

The HTML service escapes rendered card fields, warning messages, operator actions, executive summary text, and compliance disclaimer text.

This protects the deterministic HTML screen from rendering untrusted raw text.

## Source UI View

The response preserves the source UI view under:

ui_view

This allows the Operator Workstation to display the HTML while preserving the deterministic source object.

The UI view includes:

profile
dataset_contract
diagnostics_result
export_summary

## Relationship to UI View Endpoint

The UI View Endpoint returns the structured view contract.

The HTML Endpoint renders that contract into display-ready HTML.

UI View answers:

What should the Operator Workstation display?

HTML Screen answers:

How can that view be rendered as a visible screen?

## Relationship to Operator Workstation

The Operator Workstation can call:

POST /products/assessment-factory-lite/demo-ui/html

The returned html field can be displayed in an Operator Workstation preview panel or screen route.

## Demo-Only Boundary

The HTML screen must preserve the sample-data-only demo boundary.

It must not encourage upload of real customer data, regulated data, federal data, production customer data, customer secrets, or live security telemetry.

## Compliance Boundary

The Assessment Factory Lite Demo UI HTML Screen does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It renders a demo-only Operator Workstation screen from synthetic sample data and deterministic demo outputs.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Demo UI HTML Screen does not autonomously approve production launch, production data use, customer deployment, certification claims, or live integrations.

It provides deterministic HTML rendering guidance.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain HTML screen results later, but AI must not override deterministic UI or demo-only boundaries without human-approved policy changes.
