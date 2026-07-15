# Assessment Factory Lite Delivery Manifest

## Purpose

The Assessment Factory Lite Delivery Manifest documents the contents of the demo delivery package.

It gives the operator one clear view of what is included, which endpoints are part of the package, which documents support delivery, which assets are buyer-facing, which inputs and outputs are expected, and which boundaries must be preserved.

The manifest supports repeatable demo delivery for discovery calls and early buyer walkthroughs.

## Capability Chain

Assessment Factory Lite Demo Package
→ Styling and Export Release
→ Delivery Manifest Service
→ Delivery Manifest Endpoint
→ Package Contents
→ Operator Assets
→ Buyer Demo Assets
→ Delivery Inputs
→ Delivery Outputs
→ Readiness Inputs
→ Demo Delivery Packaging

## Service

### AssessmentFactoryLiteDeliveryManifestService

File:

backend/app/gagf/assessment_factory_lite_delivery_manifest_service.py

Purpose:

Build the delivery manifest for the Assessment Factory Lite demo package.

The service returns a deterministic package manifest for operator packaging.

## Endpoint

### Delivery Manifest Endpoint

GET /products/assessment-factory-lite/delivery/manifest

Purpose:

Returns the Assessment Factory Lite demo delivery manifest.

The Operator Workstation can use this endpoint to fetch package contents, included routes, included docs, operator assets, buyer demo assets, delivery inputs, delivery outputs, excluded scope, demo boundary, and readiness inputs.

## Response Contract

The delivery manifest response includes:

status
manifest_type
package_name
release
version
delivery_stage
package_summary
included_capabilities
included_endpoints
included_documents
operator_assets
buyer_demo_assets
delivery_inputs
delivery_outputs
excluded_scope
demo_boundary
readiness_inputs
operator_message
recommended_action

## Manifest Type

The manifest_type value is:

assessment_factory_lite_demo_delivery_manifest

## Release Marker

The delivery manifest object belongs to:

release:

assessment-factory-lite-demo-styling-export

version:

1.6.0

## Delivery Stage

The delivery_stage value is:

demo_delivery_packaging

## Recommended Action

The recommended_action value is:

prepare_demo_delivery_package

## Package Summary

The package summary explains the delivery purpose.

Purpose:

Package the Assessment Factory Lite demo into a repeatable delivery unit for discovery calls and early buyer walkthroughs.

Primary audience:

founder_operator
operations_leader
it_manager
workflow_owner

Delivery mode:

sample_data_only_demo

Commercial use:

early_buyer_discovery_and_paid_assessment_setup

Positioning:

A sample-data-only operational friction diagnostic demo that shows where work gets stuck and what to test first.

## Included Capabilities

The delivery manifest includes these capabilities:

sample_rows
scenario_menu
dataset_contract_validation
demo_diagnostics
styled_html_screen
buyer_export_polish

## Sample Rows Capability

Capability:

sample_rows

Purpose:

Provides canned synthetic workflow rows.

Status:

included

## Scenario Menu Capability

Capability:

scenario_menu

Purpose:

Provides UI-ready scenario choices.

Status:

included

## Dataset Contract Validation Capability

Capability:

dataset_contract_validation

Purpose:

Rejects unsafe or invalid demo rows.

Status:

included

## Demo Diagnostics Capability

Capability:

demo_diagnostics

Purpose:

Finds friction in accepted sample rows.

Status:

included

## Styled HTML Screen Capability

Capability:

styled_html_screen

Purpose:

Renders the Operator Workstation demo screen.

Status:

included

## Buyer Export Polish Capability

Capability:

buyer_export_polish

Purpose:

Creates buyer-facing findings and next steps.

Status:

included

## Included Endpoints

The delivery package includes these endpoints:

GET /products/assessment-factory-lite/demo-samples/rows

GET /products/assessment-factory-lite/demo-samples/rows/{scenario}

GET /products/assessment-factory-lite/demo-scenario-menu

GET /products/assessment-factory-lite/demo-style-tokens

POST /products/assessment-factory-lite/demo-ui/html

POST /products/assessment-factory-lite/buyer-export/polish

GET /products/assessment-factory-lite/delivery/manifest

## Included Documents

The delivery package includes these supporting documents:

ASSESSMENT_FACTORY_LITE_DEMO_PACKAGE_CLOSEOUT.md
ASSESSMENT_FACTORY_LITE_DEMO_SCREEN_CLOSEOUT.md
ASSESSMENT_FACTORY_LITE_DEMO_LOADER_CLOSEOUT.md
ASSESSMENT_FACTORY_LITE_DEMO_USABILITY_CLOSEOUT.md
ASSESSMENT_FACTORY_LITE_DEMO_STYLING_EXPORT_CLOSEOUT.md
ASSESSMENT_FACTORY_LITE_DEMO_SAMPLE_ROWS.md
ASSESSMENT_FACTORY_LITE_DEMO_SCENARIO_MENU.md
ASSESSMENT_FACTORY_LITE_DEMO_STYLE_TOKENS.md
ASSESSMENT_FACTORY_LITE_BUYER_EXPORT_POLISH.md

## Operator Assets

The operator assets are:

scenario_menu
sample_loader
styled_html_screen
buyer_export_polish

## Scenario Menu Operator Asset

Asset:

scenario_menu

Purpose:

Let the operator choose standard, invalid, or empty scenarios.

Required:

true

## Sample Loader Operator Asset

Asset:

sample_loader

Purpose:

Load canned sample rows into the visible demo screen.

Required:

true

## Styled HTML Screen Operator Asset

Asset:

styled_html_screen

Purpose:

Show a buyer-readable Operator Workstation screen.

Required:

true

## Buyer Export Polish Operator Asset

Asset:

buyer_export_polish

Purpose:

Present clearer buyer-facing findings and next steps.

Required:

true

## Buyer Demo Assets

The buyer demo assets are:

standard_demo_scenario
invalid_boundary_test
empty_starting_state
polished_buyer_export

## Standard Demo Scenario

Asset:

standard_demo_scenario

Label:

Approval Delay and Blocked Work

Buyer value:

Shows how approval delays create workflow drag.

## Invalid Boundary Test

Asset:

invalid_boundary_test

Label:

Unsafe Data Boundary Test

Buyer value:

Shows that unsafe rows are rejected before findings are shown.

## Empty Starting State

Asset:

empty_starting_state

Label:

Empty Demo Starting State

Buyer value:

Shows the screen before sample rows are loaded.

## Polished Buyer Export

Asset:

polished_buyer_export

Label:

Buyer-Facing Export Preview

Buyer value:

Shows findings, intervention, next steps, and safety boundary.

## Delivery Inputs

The manifest identifies these delivery inputs:

sample_scenario
synthetic_rows
diagnostics_result
export_summary
include_scenario_menu
include_style_tokens

## Delivery Outputs

The manifest identifies these delivery outputs:

scenario_menu
sample_rows_result
styled_html
buyer_headline
buyer_summary
key_findings
recommended_intervention
next_steps
trust_and_boundary_note

## Readiness Inputs

The delivery manifest provides readiness inputs for future delivery checks:

sample_rows_available
scenario_menu_available
styled_html_available
buyer_export_polish_available
demo_boundary_visible

## Sample Rows Available Check

Check:

sample_rows_available

Required:

true

Reason:

The demo needs canned rows for repeatable walkthroughs.

## Scenario Menu Available Check

Check:

scenario_menu_available

Required:

true

Reason:

The operator needs visible scenario choices.

## Styled HTML Available Check

Check:

styled_html_available

Required:

true

Reason:

The buyer needs a polished visible screen.

## Buyer Export Polish Available Check

Check:

buyer_export_polish_available

Required:

true

Reason:

The buyer needs clear findings and next steps.

## Demo Boundary Visible Check

Check:

demo_boundary_visible

Required:

true

Reason:

The operator must keep the demo inside sample-data-only limits.

## Relationship to Delivery Readiness

The delivery manifest does not decide readiness by itself.

It defines what later delivery readiness checks should inspect.

The future readiness service should verify that required package assets are available and that the demo boundary is visible.

## Relationship to Operator Runbook

The delivery manifest defines what is in the package.

The future operator runbook should explain how to run the package during a live demo.

The manifest answers:

What is included?

The runbook answers:

How should the operator use it?

## Relationship to Buyer Demo

The delivery manifest helps make the buyer demo repeatable.

It identifies the scenario choices, visible screen, polished export, and safety boundary that should be available before a demo is delivered.

## Demo-Only Boundary

The delivery manifest remains demo-only.

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

The manifest explicitly excludes:

production_customer_data_processing
regulated_data_processing
federal_data_processing
fedramp_or_hipaa_certification_claims
soc_2_audit_claims
wcag_certification_claims
autonomous_remediation
live_customer_integrations
production_customer_deployment
formal_security_authorization
third_party_audit_claims
persistent_file_upload_storage
customer_tenant_storage
pdf_generation
payment_processing

## Compliance Boundary

The Assessment Factory Lite Delivery Manifest does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides deterministic package inventory for a demo-only workflow.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Delivery Manifest does not autonomously approve production launch, production data use, customer deployment, certification claims, or live integrations.

It documents what is included in the demo package and what remains excluded.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain delivery package contents, but AI must not override deterministic package boundaries without human-approved policy changes.
