# Assessment Factory Lite Demo Scenario Menu

## Purpose

The Assessment Factory Lite Demo Scenario Menu provides a structured menu of available demo scenarios for the Operator Workstation.

It allows the UI to fetch scenario choices instead of hardcoding labels, descriptions, recommended uses, UI actions, or HTML payloads.

## Capability Chain

Assessment Factory Lite Demo Package
→ Demo Sample Rows Service
→ Scenario Menu Service
→ Scenario Menu Endpoint
→ Operator Workstation Scenario Menu
→ sample_scenario HTML payload
→ Visible HTML Demo Screen

## Service

### AssessmentFactoryLiteDemoScenarioMenuService

File:

backend/app/gagf/assessment_factory_lite_demo_scenario_menu_service.py

Purpose:

Build a UI-ready scenario menu for the Assessment Factory Lite demo.

The service reads deterministic sample row scenario metadata and produces menu items that the Operator Workstation can render.

## Endpoint

### Scenario Menu Endpoint

GET /products/assessment-factory-lite/demo-scenario-menu

Purpose:

Returns the available Assessment Factory Lite demo scenarios as a UI-ready menu.

## Response Contract

The scenario menu response includes:

status
menu_type
package_name
release
version
default_scenario
menu_items
aliases
operator_message
recommended_action

## Menu Type

The menu_type value is:

assessment_factory_lite_demo_scenario_menu

## Release Marker

The scenario menu belongs to:

release:

assessment-factory-lite-demo-loader

version:

1.4.0

## Default Scenario

The default_scenario is:

standard

This means the Operator Workstation should use the standard scenario as the default buyer demo scenario.

## Menu Items

The menu_items list contains the primary visible scenario choices.

Current menu item order:

standard
invalid
empty

## Menu Item Fields

Each menu item includes:

scenario
label
description
recommended_use
is_valid_sample
row_count
expected_top_friction_label
expected_intervention
ui_action
html_payload

## HTML Payload

Each menu item includes an html_payload field.

The html_payload can be sent directly to:

POST /products/assessment-factory-lite/demo-ui/html

Example:

{
  "sample_scenario": "standard"
}

This lets the Operator Workstation render a selected scenario without manually constructing rows.

## Standard Menu Item

Scenario:

standard

Label:

Approval Delay and Blocked Work

Description:

Load valid synthetic workflow rows showing approval delay and blocked work.

Recommended use:

buyer_demo_default

Expected sample validity:

true

Row count:

3

Expected top friction label:

approval_delay

Expected intervention:

streamline_approval_path

UI action:

load_standard_demo_scenario

HTML payload:

sample_scenario standard

## Invalid Menu Item

Scenario:

invalid

Label:

Unsafe Data Boundary Test

Description:

Load intentionally invalid rows to demonstrate boundary rejection behavior.

Recommended use:

boundary_rejection_demo

Expected sample validity:

false

Row count:

1

Expected top friction label:

none

Expected intervention:

repair_sample_csv_before_demo

UI action:

load_invalid_boundary_test_scenario

HTML payload:

sample_scenario invalid

## Empty Menu Item

Scenario:

empty

Label:

Empty Demo Starting State

Description:

Initialize the demo screen before sample rows are loaded.

Recommended use:

initial_empty_state

Expected sample validity:

true

Row count:

0

Expected top friction label:

none

Expected intervention:

add_demo_rows

UI action:

load_empty_demo_scenario

HTML payload:

sample_scenario empty

## Aliases

The menu includes aliases so the UI and operator workflows can normalize alternate scenario names.

Aliases:

standard maps to standard
valid maps to standard
approval_delay maps to standard
invalid maps to invalid
unsafe maps to invalid
empty maps to empty
blank maps to empty

## Operator Workstation Use

The Operator Workstation can fetch:

GET /products/assessment-factory-lite/demo-scenario-menu

Then it can render buttons or cards:

Load Standard Demo
Load Invalid Boundary Test
Start Empty Demo

Each button can use the menu item's html_payload.

## Standard Button Behavior

When the operator chooses the standard menu item, the UI can call:

POST /products/assessment-factory-lite/demo-ui/html

with:

sample_scenario standard

The screen should render the Approval Delay and Blocked Work scenario.

## Invalid Button Behavior

When the operator chooses the invalid menu item, the UI can call:

POST /products/assessment-factory-lite/demo-ui/html

with:

sample_scenario invalid

The screen should render the Unsafe Data Boundary Test and show rejected diagnostics.

## Empty Button Behavior

When the operator chooses the empty menu item, the UI can call:

POST /products/assessment-factory-lite/demo-ui/html

with:

sample_scenario empty

The screen should render the Empty Demo Starting State.

## Relationship to Sample Rows API

The scenario menu does not replace the sample rows API.

The sample rows API returns rows.

The scenario menu returns UI-ready choices.

Related endpoints:

GET /products/assessment-factory-lite/demo-samples/rows

GET /products/assessment-factory-lite/demo-samples/rows/{scenario}

GET /products/assessment-factory-lite/demo-scenario-menu

## Relationship to HTML Screen

The scenario menu is designed to feed the HTML screen endpoint.

The selected menu item's html_payload can be passed directly into:

POST /products/assessment-factory-lite/demo-ui/html

This creates the flow:

menu item
→ html_payload
→ sample_scenario
→ sample rows loader
→ UI view
→ HTML screen

## Demo-Only Boundary

The scenario menu remains demo-only.

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

frontend browser JavaScript
persistent menu preferences
user authentication
tenant-specific scenario menus
production customer data
regulated data processing
federal data processing
live customer integrations
PDF generation
formal compliance certification

## Compliance Boundary

The Assessment Factory Lite Demo Scenario Menu does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It exposes deterministic synthetic scenario choices for a demo-only workflow.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Demo Scenario Menu does not autonomously approve production launch, production data use, customer deployment, certification claims, or live integrations.

It provides deterministic scenario choices for demo initialization.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain menu items, but AI must not override deterministic scenario boundaries without human-approved policy changes.
