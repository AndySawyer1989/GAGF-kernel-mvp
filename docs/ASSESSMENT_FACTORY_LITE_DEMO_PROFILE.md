# Assessment Factory Lite Demo Profile

## Purpose

The Assessment Factory Lite Demo Profile converts the product packaging checkpoint into an operator-ready demo configuration.

It defines the demo-only sample-data boundary, demo readiness state, allowed inputs, demo workflow, dashboard sections, report sections, success criteria, excluded scope, and recommended operator action.

This profile is the first concrete product package after the Product Packaging Checkpoint release.

## Demo Profile Flow

Product Profiles, Portfolio Dashboard, Packaging Recommendation, Packaging Dashboard, or Packaging Checkpoint
→ Product Packaging Checkpoint
→ Assessment Factory Lite Demo Profile
→ Demo Readiness
→ Sample-Data Boundary
→ Demo Inputs
→ Demo Workflow
→ Dashboard Sections
→ Report Sections
→ Success Criteria
→ Excluded Scope
→ Operator Message
→ Recommended Action

## Service

### AssessmentFactoryLiteDemoProfileService

File:

backend/app/gagf/assessment_factory_lite_demo_profile_service.py

Purpose:

demo package checkpoint
→ demo product profile
→ sample-data boundary
→ demo workflow
→ report sections
→ success criteria
→ operator-ready demo configuration

## Endpoint

### Assessment Factory Lite Demo Profile Endpoint

POST /products/assessment-factory-lite/demo-profile

Purpose:

Builds the Assessment Factory Lite demo profile from product profiles, portfolio dashboard, packaging recommendation, packaging dashboard, or packaging checkpoint input.

## Input Modes

The endpoint supports five input modes.

### Mode 1 — Product Profiles

The endpoint may receive product_profiles.

Example:

{
  "product_profiles": [
    {
      "product_name": "Assessment Factory Lite",
      "product_category": "demo",
      "is_public_demo": true
    },
    {
      "product_name": "FIP Governance Diagnostics SaaS",
      "product_category": "governance_diagnostics",
      "targets_enterprise": true,
      "handles_customer_data": true
    },
    {
      "product_name": "FIP Healthcare Readiness Diagnostic",
      "product_category": "compliance",
      "targets_healthcare": true,
      "handles_health_data": true
    },
    {
      "product_name": "FIP Secure",
      "product_category": "secure_enterprise",
      "targets_federal": true,
      "requires_air_gap": true,
      "requires_on_prem": true
    }
  ]
}

In this mode, the endpoint runs:

ProductSecurityPortfolioService
→ ProductSecurityPortfolioDashboardService
→ ProductPackagingRecommendationService
→ ProductPackagingDashboardService
→ ProductPackagingCheckpointService
→ AssessmentFactoryLiteDemoProfileService

### Mode 2 — Existing Portfolio Dashboard

The endpoint may receive portfolio_dashboard.

In this mode, the endpoint runs:

ProductPackagingRecommendationService
→ ProductPackagingDashboardService
→ ProductPackagingCheckpointService
→ AssessmentFactoryLiteDemoProfileService

### Mode 3 — Existing Packaging Recommendation

The endpoint may receive packaging_recommendation.

In this mode, the endpoint runs:

ProductPackagingDashboardService
→ ProductPackagingCheckpointService
→ AssessmentFactoryLiteDemoProfileService

### Mode 4 — Existing Packaging Dashboard

The endpoint may receive packaging_dashboard.

In this mode, the endpoint runs:

ProductPackagingCheckpointService
→ AssessmentFactoryLiteDemoProfileService

### Mode 5 — Existing Checkpoint

The endpoint may receive checkpoint.

In this mode, the endpoint runs:

AssessmentFactoryLiteDemoProfileService

## Output Contract

The demo profile returns:

status
profile_type
selected_product
package_name
selected_track
is_assessment_factory_lite
demo_readiness
demo_boundary
demo_inputs
demo_workflow
dashboard_sections
report_sections
success_criteria
excluded_scope
operator_message
recommended_action

## Profile Type

The profile_type value is:

assessment_factory_lite_demo_profile

## Selected Product

The selected product should be:

assessment_factory_lite

## Package Name

The package name should be:

Assessment Factory Lite Demo Package

## Selected Track

The selected track should be:

fast_productization

## Demo Readiness

demo_readiness determines whether the profile is ready to become a demo package.

For the current go path, demo_readiness includes:

ready_for_demo_package:

true

decision:

go

reason:

fast_demo_candidate_available

requires_customer_data:

false

requires_regulated_data:

false

requires_federal_data:

false

requires_production_access:

false

## Demo Boundary

demo_boundary defines the sample-data-only demo boundary.

boundary_type:

demo_only_sample_data

Allowed data:

sample_csv
synthetic_workflow_events
mock_approval_events
mock_delay_events

Allowed runtime:

local_demo
operator_workstation
non_production_environment

Prohibited data:

regulated_data
federal_data
production_customer_data
customer_secrets
live_security_telemetry

certification_claims_allowed:

false

## Demo Inputs

demo_inputs define the input contract for the demo package.

Current inputs include:

sample_csv

Description:

Synthetic workflow event CSV.

Required:

true

approval_or_delay_examples

Description:

Example approval, delay, blocked, or handoff events.

Required:

true

demo_context

Description:

Plain-language scenario context for the operator.

Required:

false

## Demo Workflow

demo_workflow defines the operator path for the demo.

Current workflow:

load_demo_profile
upload_sample_csv
run_governance_diagnostics
review_governance_drag_summary
review_top_friction_points
display_recommended_intervention
export_demo_summary

## Dashboard Sections

dashboard_sections define what the Operator Workstation should display.

Current sections:

demo_readiness_card
sample_data_boundary_card
governance_drag_summary
top_friction_points
recommended_intervention
demo_export_status

## Report Sections

report_sections define the demo summary/report structure.

Current sections:

executive_summary
sample_data_boundary
governance_drag_findings
top_constraints
recommended_intervention
next_steps
compliance_disclaimer

## Success Criteria

success_criteria define how the demo profile is validated.

Current criteria:

demo_profile_loads
sample_csv_boundary_is_enforced
governance_diagnostics_run
friction_summary_is_displayed
recommended_intervention_is_displayed
demo_summary_can_be_exported
no_regulated_or_federal_data_required

## Excluded Scope

excluded_scope prevents the demo package from expanding into risky product territory too early.

Current excluded scope:

production_customer_data_processing
regulated_data_processing
federal_data_processing
fedramp_or_hipaa_certification_claims
autonomous_remediation
live_customer_integrations

## Operator Message

When the checkpoint selects Assessment Factory Lite with a go decision, the operator message is:

Assessment Factory Lite Demo Package is ready to configure as a demo-only sample-data package.

## Recommended Action

When the checkpoint selects Assessment Factory Lite with a go decision, the recommended action is:

build_assessment_factory_lite_demo

## Strategic Meaning

Assessment Factory Lite Demo Profile turns the product checkpoint into the first buildable demo package.

It confirms that the first product package should be:

Assessment Factory Lite Demo Package

The package is constrained to:

sample data
synthetic workflow events
mock approval events
mock delay events
local or non-production demo runtime

This allows the product to move toward demo or early revenue without exposing regulated data, federal data, production customer data, live security telemetry, or certification claims.

## Relationship to Product Packaging Checkpoint

Product Packaging Checkpoint decides whether a product can move forward.

Assessment Factory Lite Demo Profile converts that decision into a concrete demo configuration.

Checkpoint answers:

Should this product move forward?

Demo profile answers:

How should the demo package be configured safely?

## Relationship to Future Demo Dataset Contract

The next implementation layer should define the sample CSV demo dataset contract.

The profile already identifies required inputs:

sample_csv
synthetic_workflow_events
mock_approval_events
mock_delay_events
approval_or_delay_examples

The dataset contract should define required fields, allowed event types, validation rules, and failure modes.

## Compliance Boundary

The Assessment Factory Lite Demo Profile does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It defines a safe demo-only product profile.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Demo Profile does not autonomously approve production launch.

It provides deterministic demo configuration guidance.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain demo profile results later, but AI must not override deterministic demo profile boundaries without human-approved policy changes.
