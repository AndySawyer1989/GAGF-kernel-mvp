# Assessment Factory Lite Demo Sample Rows

## Purpose

The Assessment Factory Lite Demo Sample Rows layer provides deterministic canned sample rows for the Assessment Factory Lite demo.

It lets the Operator Workstation load standard valid rows, invalid boundary-test rows, or an empty starting state without manually posting JSON.

This starts the sample data loader track for the visible demo screen.

## Sample Rows Flow

Operator Workstation
→ Sample Rows Endpoint
→ Scenario Selection
→ Deterministic Sample Rows
→ Dataset Contract Validation
→ Demo Diagnostics
→ Demo Export Summary
→ Demo UI View
→ Demo HTML Screen

## Service

### AssessmentFactoryLiteDemoSampleRowsService

File:

backend/app/gagf/assessment_factory_lite_demo_sample_rows_service.py

Purpose:

canned synthetic rows
→ valid sample rows
→ invalid sample rows
→ empty sample profile
→ loader-ready demo scenarios

## Endpoints

### Default Sample Rows Endpoint

GET /products/assessment-factory-lite/demo-samples/rows

Purpose:

Returns the default standard Assessment Factory Lite demo sample rows.

### Scenario Sample Rows Endpoint

GET /products/assessment-factory-lite/demo-samples/rows/{scenario}

Purpose:

Returns sample rows for a named canned demo scenario.

## Output Contract

The sample rows response returns:

status
sample_type
scenario
scenario_label
boundary_type
is_valid_sample
rows
row_count
expected_demo_outcome
operator_message
recommended_action

## Sample Type

The sample_type value is:

assessment_factory_lite_demo_sample_rows

## Boundary Type

The boundary_type value is:

demo_only_sample_data

## Available Scenarios

Available scenarios include:

standard
valid
approval_delay
invalid
unsafe
empty
blank

## Standard Scenario

Scenario names:

standard
valid
approval_delay

Scenario label:

Approval Delay and Blocked Work

Purpose:

Provides valid synthetic workflow rows that demonstrate approval delay and blocked work.

The standard scenario includes:

approval_requested
approval_delayed
work_blocked

The standard scenario is valid sample data.

is_valid_sample:

true

recommended_action:

load_sample_rows_into_demo

## Standard Scenario Expected Outcome

The standard scenario expected_demo_outcome is:

validation_status:

passed

top_friction_label:

approval_delay

recommended_intervention:

streamline_approval_path

recommended_action:

run_demo_diagnostics

## Standard Scenario Rows

The standard scenario contains synthetic rows with:

event_id
case_id
event_type
actor
team
timestamp
severity
description
constraint_label
duration_minutes

The rows are synthetic and do not contain real customer data, regulated data, federal data, customer secrets, or live security telemetry.

## Invalid Scenario

Scenario names:

invalid
unsafe

Scenario label:

Unsafe Data Boundary Example

Purpose:

Provides an intentionally invalid row for testing dataset boundary rejection.

The invalid scenario contains:

real_customer_incident
urgent
contains_real_customer_data true

The invalid scenario is not valid sample data.

is_valid_sample:

false

recommended_action:

test_sample_data_boundary_rejection

## Invalid Scenario Expected Outcome

The invalid scenario expected_demo_outcome is:

validation_status:

failed

top_friction_label:

none

recommended_intervention:

repair_sample_csv_before_demo

recommended_action:

repair_sample_csv_before_demo

## Invalid Scenario Rejection

The invalid scenario should be rejected by the dataset contract.

Expected error types include:

invalid_event_type
invalid_severity
real_customer_data_not_allowed

This confirms that unsafe rows cannot enter valid diagnostics as trusted demo findings.

## Empty Scenario

Scenario names:

empty
blank

Scenario label:

Empty Demo Starting State

Purpose:

Provides an empty row set for initializing the demo screen before sample data is loaded.

The empty scenario is valid as an initialization state.

is_valid_sample:

true

row_count:

0

recommended_action:

initialize_empty_demo_screen

## Empty Scenario Expected Outcome

The empty scenario expected_demo_outcome is:

validation_status:

passed

top_friction_label:

none

recommended_intervention:

add_demo_rows

recommended_action:

add_synthetic_sample_rows

## Unknown Scenario Behavior

If an unknown scenario is requested, the service returns:

status:

not_found

rows:

empty list

row_count:

0

available_scenarios

recommended_action:

choose_available_sample_scenario

This allows the Operator Workstation to show available scenario choices instead of failing silently.

## Dataset Contract Relationship

The sample rows service provides canned rows.

The dataset contract validates whether those rows are acceptable.

Sample Rows answers:

Which canned rows should be loaded?

Dataset Contract answers:

Are these rows safe and valid?

## Diagnostics Relationship

The standard scenario should run through diagnostics and produce:

top friction label:

approval_delay

recommended intervention:

streamline_approval_path

The invalid scenario should not produce valid diagnostics until repaired.

The empty scenario should recommend adding synthetic rows.

## Operator Workstation Relationship

The Operator Workstation can call:

GET /products/assessment-factory-lite/demo-samples/rows

or:

GET /products/assessment-factory-lite/demo-samples/rows/{scenario}

The returned rows can be passed into:

POST /products/assessment-factory-lite/demo-ui/html

This supports loading a visible demo screen without manually pasting JSON.

## Demo-Only Boundary

The sample rows layer must remain demo-only.

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

The Assessment Factory Lite Demo Sample Rows layer does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It provides synthetic sample rows for a demo-only workflow.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Demo Sample Rows layer does not autonomously approve production launch, production data use, customer deployment, certification claims, or live integrations.

It provides deterministic sample data for demo initialization.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain sample scenarios later, but AI must not override deterministic sample data boundaries without human-approved policy changes.
