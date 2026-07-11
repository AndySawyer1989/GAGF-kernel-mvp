# Assessment Factory Lite Dataset Contract

## Purpose

The Assessment Factory Lite Dataset Contract defines the safe sample CSV boundary for the Assessment Factory Lite Demo Package.

It specifies required fields, optional fields, allowed event types, allowed severity values, validation rules, failure modes, sample rows, excluded scope, and API endpoints.

This contract prevents the demo package from accepting real customer data, regulated data, federal data, live security telemetry, customer secrets, or certification claims.

## Dataset Contract Flow

Assessment Factory Lite Demo Profile
→ Dataset Contract
→ Required Fields
→ Optional Fields
→ Allowed Event Types
→ Allowed Severity Values
→ Validation Rules
→ Failure Modes
→ Sample Rows
→ Demo-Only Boundary
→ Dataset Validation Result

## Service

### AssessmentFactoryLiteDatasetContractService

File:

backend/app/gagf/assessment_factory_lite_dataset_contract_service.py

Purpose:

sample_csv
→ required fields
→ allowed event types
→ validation rules
→ failure modes
→ demo dataset boundary

## Endpoints

### Dataset Contract Endpoint

GET /products/assessment-factory-lite/dataset-contract

Purpose:

Returns the Assessment Factory Lite sample CSV dataset contract.

### Dataset Validation Endpoint

POST /products/assessment-factory-lite/dataset-contract/validate

Purpose:

Validates sample CSV rows against the Assessment Factory Lite demo-only dataset boundary.

## Contract Output

The dataset contract returns:

status
contract_type
dataset_name
boundary_type
required_fields
optional_fields
allowed_event_types
allowed_severity_values
validation_rules
failure_modes
sample_rows
excluded_scope
operator_message
recommended_action

## Contract Type

The contract_type value is:

assessment_factory_lite_demo_dataset_contract

## Dataset Name

The dataset_name value is:

assessment_factory_lite_sample_csv

## Boundary Type

The boundary_type value is:

demo_only_sample_data

## Required Fields

The required_fields list defines fields that every demo row must include.

Required field names:

event_id
case_id
event_type
actor
team
timestamp
severity
description

## Required Field Meanings

event_id:

Unique synthetic event identifier.

case_id:

Synthetic workflow or request identifier.

event_type:

Demo workflow event type.

actor:

Synthetic actor or role responsible for event.

team:

Synthetic team or function name.

timestamp:

Synthetic event timestamp.

severity:

Demo severity rating.

description:

Plain-language demo event description.

## Optional Fields

The optional_fields list may include:

expected_state
observed_state
duration_minutes
constraint_label
contains_real_customer_data
contains_regulated_data
contains_federal_data

## Optional Field Rules

contains_real_customer_data:

Must be false or omitted.

contains_regulated_data:

Must be false or omitted.

contains_federal_data:

Must be false or omitted.

## Allowed Event Types

The allowed_event_types list includes:

approval_requested
approval_delayed
approval_granted
approval_rejected
work_blocked
dependency_wait
handoff_delayed
ownership_gap
environment_failure
escalation

## Allowed Severity Values

The allowed_severity_values list includes:

low
medium
high
critical

## Validation Rules

The validation_rules list includes:

all_required_fields_must_be_present
event_type_must_be_allowed
severity_must_be_allowed
dataset_must_be_demo_only
real_customer_data_is_not_allowed
regulated_data_is_not_allowed
federal_data_is_not_allowed
certification_claims_are_not_allowed

## Failure Modes

The failure_modes list includes:

missing_required_fields

Action:

repair_sample_csv_before_demo

invalid_event_type

Action:

map_event_to_allowed_demo_event_type

invalid_severity

Action:

map_severity_to_allowed_value

real_customer_data_not_allowed

Action:

remove_real_customer_data_or_use_synthetic_data

regulated_data_not_allowed

Action:

remove_regulated_data_from_demo_dataset

federal_data_not_allowed

Action:

remove_federal_data_from_demo_dataset

## Sample Rows

The contract includes sample rows using synthetic workflow events.

Example event types include:

approval_requested
approval_delayed

Example constraint labels include:

approval_required
approval_delay

The sample rows are synthetic and must not contain real customer data, regulated data, federal data, customer secrets, or live security telemetry.

## Validation Input

The validation endpoint expects:

rows

Example shape:

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
      "description": "Synthetic approval request submitted."
    }
  ]
}

## Validation Output

The validation endpoint returns:

status
validation_type
row_count
is_valid
error_count
errors
accepted_boundary
recommended_action

## Validation Type

The validation_type value is:

assessment_factory_lite_dataset_validation

## Valid Dataset Result

If rows are valid, the validation result includes:

is_valid:

true

error_count:

0

errors:

empty list

accepted_boundary:

demo_only_sample_data

recommended_action:

run_demo_diagnostics

## Invalid Dataset Result

If rows are invalid, the validation result includes:

is_valid:

false

accepted_boundary:

none

recommended_action:

repair_sample_csv_before_demo

The errors list identifies row number, error type, and relevant fields or values.

## Error Types

Possible error_type values include:

missing_required_fields
invalid_event_type
invalid_severity
real_customer_data_not_allowed
regulated_data_not_allowed
federal_data_not_allowed

## Empty Rows Behavior

If rows is missing or empty, the validator returns a valid empty result.

This allows the Operator Workstation to initialize the validator before a file is uploaded.

## Excluded Scope

The dataset contract excludes:

production_customer_data
regulated_data
federal_data
live_security_telemetry
customer_secrets
fedramp_or_hipaa_certification_claims

## Demo-Only Boundary

The dataset contract is limited to demo-only sample data.

Allowed data should be:

sample_csv
synthetic_workflow_events
mock_approval_events
mock_delay_events
approval_or_delay_examples

The dataset must not include:

real customer data
regulated data
federal data
production customer data
live security telemetry
customer secrets

## Operator Message

The contract operator message is:

Assessment Factory Lite sample CSV contract is ready for demo-only synthetic workflow events.

## Recommended Action

The contract recommended action is:

build_sample_csv_validator

If validation succeeds, the validation recommended action is:

run_demo_diagnostics

If validation fails, the validation recommended action is:

repair_sample_csv_before_demo

## Relationship to Assessment Factory Lite Demo Profile

The Assessment Factory Lite Demo Profile defines that the demo package requires sample CSV input and synthetic workflow events.

The Dataset Contract defines exactly what that CSV-like input must contain.

Demo Profile answers:

What demo package configuration is allowed?

Dataset Contract answers:

What sample rows are valid for that demo package?

## Relationship to Future Demo Diagnostics Runner

The next implementation layer should use the dataset validation result before running demo diagnostics.

A valid dataset can proceed to:

run_demo_diagnostics

An invalid dataset must stop and return:

repair_sample_csv_before_demo

## Compliance Boundary

The Assessment Factory Lite Dataset Contract does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It defines and validates a safe demo-only sample dataset.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Dataset Contract does not autonomously approve production data use.

It provides deterministic demo dataset validation.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain dataset validation errors later, but AI must not override deterministic dataset validation or demo-only boundaries without human-approved policy changes.
