# Assessment Factory Lite Demo Screen Sample Loader

## Purpose

The Assessment Factory Lite Demo Screen Sample Loader documents how canned sample scenarios are loaded directly into the visible HTML demo screen.

It allows the Operator Workstation to render the demo screen from a scenario name instead of manually posting raw JSON rows.

This completes the first usability bridge between canned demo data and the visible Operator Workstation screen.

## Sample Loader Flow

sample_scenario
→ AssessmentFactoryLiteDemoSampleRowsService
→ canned sample rows
→ AssessmentFactoryLiteDemoUIViewService
→ AssessmentFactoryLiteDemoUIHTMLService
→ Sample Data Loader section
→ visible HTML demo screen

## Services

### AssessmentFactoryLiteDemoSampleRowsService

Purpose:

Provides canned synthetic demo rows.

### AssessmentFactoryLiteDemoUIViewService

Purpose:

Builds the structured Operator Workstation UI view.

### AssessmentFactoryLiteDemoUIHTMLService

Purpose:

Renders the UI view and sample loader state as deterministic HTML.

## Endpoint

### Demo UI HTML Endpoint

POST /products/assessment-factory-lite/demo-ui/html

Purpose:

Renders the Assessment Factory Lite Operator Workstation demo screen.

The endpoint now accepts:

sample_scenario

## New Input

sample_scenario allows the screen to load canned rows by scenario name.

Example payload:

{
  "sample_scenario": "standard"
}

## Supported Scenarios

Supported scenarios include:

standard
valid
approval_delay
invalid
unsafe
empty
blank

## Standard Scenario Render

sample_scenario:

standard

The standard scenario loads valid canned rows.

Scenario label:

Approval Delay and Blocked Work

Expected behavior:

sample_rows_result status ok
sample_rows_result scenario standard
sample_rows_result row_count 3
sample_rows_result is_valid_sample true
diagnostics_result status ok
HTML includes Sample Data Loader
HTML includes data-sample-scenario="standard"
HTML includes Approval Delay and Blocked Work

Expected diagnostic meaning:

top_friction_label approval_delay
recommended_intervention streamline_approval_path

## Invalid Scenario Render

sample_scenario:

invalid

The invalid scenario loads an unsafe sample row for boundary rejection testing.

Scenario label:

Unsafe Data Boundary Example

Expected behavior:

sample_rows_result status ok
sample_rows_result scenario invalid
sample_rows_result is_valid_sample false
diagnostics_result status rejected
HTML includes Unsafe Data Boundary Example
HTML includes repair_sample_csv_before_demo

Expected validation errors:

invalid_event_type
invalid_severity
real_customer_data_not_allowed

## Empty Scenario Render

sample_scenario:

empty

The empty scenario initializes the screen without rows.

Scenario label:

Empty Demo Starting State

Expected behavior:

sample_rows_result status ok
sample_rows_result scenario empty
sample_rows_result row_count 0
diagnostics_result row_count 0
HTML includes Empty Demo Starting State
HTML includes add_synthetic_sample_rows

## Sample Loader Section

The HTML screen renders a sample loader section.

The section title is:

Sample Data Loader

The rendered sample loader article includes:

data-sample-scenario
scenario label
scenario
rows loaded
boundary
action

## Sample Rows Result

The HTML response now includes:

sample_rows_result

If a sample scenario is loaded, sample_rows_result contains the scenario payload from AssessmentFactoryLiteDemoSampleRowsService.

If direct rows are provided instead of sample_scenario, sample_rows_result is null.

## Direct Rows Fallback

If rows are provided directly, the HTML screen still renders.

In that case, no canned scenario is loaded.

The sample loader section displays:

No canned sample scenario was loaded. Rows may have been provided directly.

This preserves backward compatibility with direct row input.

## Input Priority

The HTML service only loads sample_scenario when:

ui_view is not provided
rows is not provided
sample_scenario is provided

If ui_view is provided, the service renders the supplied UI view.

If rows are provided, the service uses the rows directly.

This prevents accidental replacement of explicit input with canned sample data.

## Output Contract Additions

The HTML response includes:

sample_rows_result

The full response includes:

status
screen_type
package_name
release
version
sample_rows_result
html
ui_view
operator_message
recommended_action

## HTML Rendering Additions

The rendered HTML now includes:

Sample Data Loader

When a scenario is loaded, the HTML includes:

data-sample-scenario
scenario label
rows loaded
boundary
action

## Relationship to Sample Rows Endpoint

The sample rows endpoint returns canned sample rows directly.

GET /products/assessment-factory-lite/demo-samples/rows

GET /products/assessment-factory-lite/demo-samples/rows/{scenario}

The HTML endpoint can now use those same scenarios indirectly through sample_scenario.

## Relationship to HTML Screen

Before this integration, the HTML screen required rows, diagnostics_result, export_summary, or ui_view.

After this integration, the HTML screen can start from:

sample_scenario

This makes demo rendering easier for the Operator Workstation.

## Operator Workstation Meaning

The Operator Workstation can now provide simple buttons such as:

Load Standard Demo
Load Invalid Boundary Test
Start Empty Demo

Those buttons can call:

POST /products/assessment-factory-lite/demo-ui/html

with:

sample_scenario standard
sample_scenario invalid
sample_scenario empty

## Demo-Only Boundary

The sample loader remains demo-only.

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

## Compliance Boundary

The Assessment Factory Lite Demo Screen Sample Loader does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It loads synthetic sample scenarios for a demo-only workflow.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Demo Screen Sample Loader does not autonomously approve production launch, production data use, customer deployment, certification claims, or live integrations.

It provides deterministic sample scenario loading for demo initialization.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain sample loader results later, but AI must not override deterministic sample loading or demo-only boundaries without human-approved policy changes.
