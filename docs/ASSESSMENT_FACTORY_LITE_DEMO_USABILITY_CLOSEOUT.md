# Assessment Factory Lite Demo Usability Closeout

## Purpose

This document closes out Release 1.5.0 for the Assessment Factory Lite Demo Usability layer.

It records the completed scenario menu, scenario menu endpoint, sample loader integration, visible HTML menu rendering, operator actions, demo-only boundary, excluded scope, and recommended next implementation track.

## Release Marker

Release:

1.5.0

Release name:

assessment-factory-lite-demo-usability

Sprint:

4.4

Status:

complete

## Release Meaning

Release 1.5.0 marks the first usability-focused layer for the Assessment Factory Lite Demo Package.

The release makes the visible Operator Workstation screen easier to use by rendering scenario choices directly in the demo screen.

The operator no longer needs to remember scenario names or manually construct sample_scenario payloads.

## Completed Capability Chain

The completed chain is:

Assessment Factory Lite Demo Package
→ Demo Sample Rows Service
→ Demo Sample Rows API
→ Demo Scenario Menu Service
→ Demo Scenario Menu Endpoint
→ Demo Scenario Menu Documentation
→ HTML Screen Scenario Menu Integration
→ Demo Screen Usability Release Marker

## Completed Services

The completed services include:

AssessmentFactoryLiteDemoSampleRowsService
AssessmentFactoryLiteDemoScenarioMenuService
AssessmentFactoryLiteDemoUIHTMLService

## Completed Endpoints

The completed usability endpoints include:

GET /products/assessment-factory-lite/demo-samples/rows

GET /products/assessment-factory-lite/demo-samples/rows/{scenario}

GET /products/assessment-factory-lite/demo-scenario-menu

POST /products/assessment-factory-lite/demo-ui/html

## Scenario Menu Endpoint

GET /products/assessment-factory-lite/demo-scenario-menu

Purpose:

Returns UI-ready scenario menu items for the Operator Workstation.

The endpoint returns:

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

## Scenario Menu Contract

The scenario menu has menu_type:

assessment_factory_lite_demo_scenario_menu

The scenario menu belongs to the loader release:

assessment-factory-lite-demo-loader

The scenario menu object version remains:

1.4.0

The system release marker is now:

1.5.0

This preserves the distinction between internal object contracts and system release markers.

## Scenario Menu Items

The scenario menu currently exposes three primary choices:

standard
invalid
empty

Each item includes:

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

## Standard Scenario Menu Item

Scenario:

standard

Label:

Approval Delay and Blocked Work

Recommended use:

buyer_demo_default

UI action:

load_standard_demo_scenario

HTML payload:

sample_scenario standard

Expected intervention:

streamline_approval_path

## Invalid Scenario Menu Item

Scenario:

invalid

Label:

Unsafe Data Boundary Test

Recommended use:

boundary_rejection_demo

UI action:

load_invalid_boundary_test_scenario

HTML payload:

sample_scenario invalid

Expected intervention:

repair_sample_csv_before_demo

## Empty Scenario Menu Item

Scenario:

empty

Label:

Empty Demo Starting State

Recommended use:

initial_empty_state

UI action:

load_empty_demo_scenario

HTML payload:

sample_scenario empty

Expected intervention:

add_demo_rows

## Aliases

The menu preserves scenario aliases:

standard maps to standard
valid maps to standard
approval_delay maps to standard
invalid maps to invalid
unsafe maps to invalid
empty maps to empty
blank maps to empty

## HTML Screen Scenario Menu Integration

The HTML screen now includes a visible section titled:

Demo Scenario Menu

The screen renders scenario cards with:

data-scenario
label
description
recommended use
row count
expected intervention
UI action
HTML payload

The rendered payload text includes:

HTML payload: sample_scenario=standard
HTML payload: sample_scenario=invalid
HTML payload: sample_scenario=empty

## Sample Loader Integration

The HTML screen also preserves the Sample Data Loader section.

When a scenario is loaded, the screen displays:

scenario label
scenario
rows loaded
boundary
action

The loaded sample section includes:

data-sample-scenario

## Direct Rows Compatibility

The HTML screen still supports direct rows.

If rows are provided directly, no canned sample scenario is loaded.

In that case:

sample_rows_result is null

The screen displays:

No canned sample scenario was loaded. Rows may have been provided directly.

## Menu Toggle

The HTML service supports:

include_scenario_menu

Default:

true

If include_scenario_menu is false, the screen renders without the scenario menu.

The screen then displays:

Scenario menu was not included for this render.

## Operator Workstation Meaning

The Operator Workstation can now render a real scenario chooser.

Recommended UI actions:

Load Standard Demo
Load Invalid Boundary Test
Start Empty Demo

The operator can select a scenario and send the scenario item's html_payload into:

POST /products/assessment-factory-lite/demo-ui/html

## Buyer Demo Meaning

Release 1.5.0 makes the buyer-facing demo easier to operate during live walkthroughs.

The operator can show:

what scenario is available
what each scenario demonstrates
which scenario is safe and valid
which scenario intentionally tests boundary rejection
what intervention is expected
how the selected scenario drives the visible demo screen

## Product Strategy Meaning

Assessment Factory Lite is now closer to a usable demo product.

The demo can be operated through scenario choices instead of raw data entry.

This supports:

founder-led demos
early buyer discovery calls
operations leader walkthroughs
IT manager walkthroughs
internal product review
repeatable demo rehearsals

## Technical Meaning

Release 1.5.0 proves that the visible demo screen can render both:

scenario choices
selected scenario output

This creates a clearer product loop:

operator chooses scenario
→ scenario menu provides html_payload
→ HTML endpoint receives sample_scenario
→ sample rows load
→ diagnostics run
→ UI view builds
→ HTML screen renders

## Internal Contract Boundaries

System release marker:

1.5.0
assessment-factory-lite-demo-usability

Scenario menu object contract:

1.4.0
assessment-factory-lite-demo-loader

HTML screen object contract:

1.2.0
assessment-factory-lite-demo-ui

UI view object contract:

1.1.0
assessment-factory-lite-demo-package

These should not be collapsed unless the object contracts themselves change.

## Demo-Only Boundary

The usability layer remains demo-only.

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

This release explicitly excludes:

production_customer_data_processing
regulated_data_processing
federal_data_processing
fedramp_or_hipaa_certification_claims
autonomous_remediation
live_customer_integrations
production_customer_deployment
formal_security_authorization
third_party_audit_claims
persistent_file_upload_storage
interactive_browser_javascript
frontend_state_management
authentication_and_authorization
PDF_generation
customer_tenant_storage
real_design_system_css

## Recommended Next Implementation Track

The recommended next implementation track is:

Assessment Factory Lite Buyer-Facing Styling and Export Polish

Recommended next stories:

US-187 Assessment Factory Lite Demo Screen Style Token Service
US-188 Assessment Factory Lite Demo Screen Style Token Endpoint
US-189 Assessment Factory Lite Demo Screen Style Token Documentation
US-190 Assessment Factory Lite Demo HTML Style Integration
US-191 Assessment Factory Lite Demo Buyer Export Polish Service
US-192 Assessment Factory Lite Demo Buyer Export Polish Endpoint
US-193 Assessment Factory Lite Demo Buyer Export Polish Documentation
US-194 Assessment Factory Lite Demo Styling and Export Release Marker

## Why Styling Comes Next

The core demo flow now works.

The next product risk is not the diagnostic chain.

The next product risk is presentation quality.

Buyer-facing styling and export polish should make the demo feel more like a product and less like a raw technical artifact.

## Compliance Boundary

The Assessment Factory Lite Demo Usability layer does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It provides deterministic scenario selection and screen rendering for a demo-only workflow.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Demo Usability layer does not autonomously approve production launch, production data use, customer deployment, certification claims, or live integrations.

It provides deterministic scenario choices and demo screen rendering.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain scenario choices, but AI must not override deterministic scenario boundaries without human-approved policy changes.

## Closeout Statement

Release 1.5.0 completes the first usability layer for the Assessment Factory Lite Demo Package.

The project now has a safe, deterministic, sample-data-only visible demo screen with scenario choices, scenario payloads, sample loading, diagnostics, export preview, safety warnings, and operator actions.
