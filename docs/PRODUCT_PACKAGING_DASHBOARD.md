# Product Packaging Dashboard

## Purpose

The Product Packaging Dashboard converts a product packaging recommendation into an operator-ready dashboard summary.

It helps the Operator Workstation display the first packaging candidate, packaging track, candidate counts, security blockers, dashboard cards, operator message, and recommended action.

This layer makes product packaging guidance visible and actionable.

## Dashboard Flow

Product Profiles, Portfolio Dashboard, or Packaging Recommendation
→ Product Packaging Recommendation
→ Product Packaging Dashboard Summary
→ First Candidate Card
→ Packaging Track Summary
→ Candidate Summary
→ Blocker Summary
→ Dashboard Cards
→ Operator Message
→ Recommended Action

## Service

### ProductPackagingDashboardService

File:

backend/app/gagf/product_packaging_dashboard_service.py

Purpose:

packaging recommendation
→ dashboard-ready packaging summary
→ first candidate card
→ packaging track summary
→ blocker summary
→ operator guidance

## Endpoint

### Product Packaging Dashboard Endpoint

POST /products/packaging/dashboard

Purpose:

Builds a dashboard-ready product packaging summary from product profiles, an existing portfolio dashboard, or an existing packaging recommendation.

## Input Modes

The endpoint supports three input modes.

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

### Mode 2 — Existing Portfolio Dashboard

The endpoint may receive portfolio_dashboard.

Example:

{
  "portfolio_dashboard": {
    "status": "ok",
    "summary_type": "product_security_portfolio_dashboard",
    "productization_tracks": {
      "fast_productization": [
        "assessment_factory_lite"
      ],
      "enterprise_ready": [
        "fip_governance_diagnostics_saas"
      ],
      "regulated_boundary": [
        "fip_healthcare_readiness_diagnostic"
      ],
      "hardened_federal": [
        "fip_secure"
      ],
      "zta_planning": []
    },
    "risk_summary": {
      "highest_security_tier": "tier_4_federal_critical",
      "highest_risk_product_count": 1,
      "regulated_or_federal_product_count": 2,
      "requires_hardened_track": true,
      "requires_regulated_track": true
    },
    "zta_distribution": {
      "required": 2,
      "recommended": 1,
      "not_required": 1
    }
  }
}

In this mode, the endpoint runs:

ProductPackagingRecommendationService
→ ProductPackagingDashboardService

### Mode 3 — Existing Packaging Recommendation

The endpoint may receive packaging_recommendation.

Example:

{
  "packaging_recommendation": {
    "status": "ok",
    "recommendation_type": "product_packaging_recommendation",
    "first_packaging_candidate": {
      "product_name": "assessment_factory_lite",
      "track": "fast_productization",
      "reason": "lowest_security_burden"
    },
    "primary_packaging_track": "demo_or_early_revenue",
    "demo_candidates": [
      "assessment_factory_lite"
    ],
    "enterprise_candidates": [
      "fip_governance_diagnostics_saas"
    ],
    "regulated_candidates": [
      "fip_healthcare_readiness_diagnostic"
    ],
    "hardened_candidates": [
      "fip_secure"
    ],
    "security_blockers": [
      "federal_hardened_track_required",
      "regulated_compliance_boundary_required",
      "zta_required_for_some_products",
      "hardened_products_not_fast_packaging_candidates",
      "regulated_products_need_boundary_definition"
    ],
    "packaging_recommendation": "package_fast_demo_or_assessment_product_first",
    "operator_message": "Package assessment_factory_lite first as the fastest demo or early-revenue candidate.",
    "next_action": "build_demo_package"
  }
}

In this mode, the endpoint runs:

ProductPackagingDashboardService

## Output Contract

The dashboard returns:

status
summary_type
first_candidate_card
packaging_track_summary
candidate_summary
blocker_summary
operator_message
recommended_action
packaging_recommendation
dashboard_cards

## Summary Type

The summary_type value is:

product_packaging_dashboard

## First Candidate Card

first_candidate_card describes the product that should be packaged first.

It includes:

product_name
track
reason
is_available
display_label

Example:

{
  "product_name": "assessment_factory_lite",
  "track": "fast_productization",
  "reason": "lowest_security_burden",
  "is_available": true,
  "display_label": "assessment_factory_lite — Fast Productization"
}

## Packaging Track Summary

packaging_track_summary summarizes the recommended product packaging path.

It includes:

primary_packaging_track
recommendation_type
is_demo_or_revenue_candidate
requires_enterprise_review
requires_regulated_boundary
requires_hardened_boundary

## Primary Packaging Tracks

Possible primary_packaging_track values include:

demo_or_early_revenue
enterprise_pilot
regulated_readiness_package
federal_hardened_package
none

## Candidate Summary

candidate_summary counts and lists products in each packaging category.

It includes:

demo_candidate_count
enterprise_candidate_count
regulated_candidate_count
hardened_candidate_count
zta_planning_candidate_count
demo_candidates
enterprise_candidates
regulated_candidates
hardened_candidates
zta_planning_candidates

## Blocker Summary

blocker_summary summarizes security and compliance blockers.

It includes:

blocker_count
security_blockers
has_federal_blocker
has_regulated_blocker
has_zta_blocker
has_packaging_blocker

## Security Blockers

Possible security_blockers include:

federal_hardened_track_required
regulated_compliance_boundary_required
zta_required_for_some_products
hardened_products_not_fast_packaging_candidates
regulated_products_need_boundary_definition

## Dashboard Cards

dashboard_cards provide compact UI cards for the Operator Workstation.

Current cards include:

First Packaging Candidate
Primary Packaging Track
Demo Candidates
Security Blockers
Next Action

Each card includes:

label
value
status

Card status may be:

ok
attention_required

## Operator Guidance

operator_message provides a plain-language explanation of the packaging recommendation.

recommended_action provides a compact action key for the Operator Workstation.

For the current portfolio example:

operator_message:

Package assessment_factory_lite first as the fastest demo or early-revenue candidate.

recommended_action:

build_demo_package

## Product Strategy Meaning

The Product Packaging Dashboard makes the roadmap operational.

It converts product security and packaging logic into a dashboard-ready decision.

It supports this product sequencing rule:

Package low-risk demo or assessment products first.

Prepare enterprise products as pilots with security readiness review.

Define regulated compliance boundaries before packaging HIPAA-sensitive or regulated products.

Define hardened security boundaries before packaging FedRAMP High-aligned, federal, on-prem, air-gapped, or critical infrastructure products.

## Current Strategic Result

Using the current portfolio example:

First packaging candidate:

assessment_factory_lite

Primary packaging track:

demo_or_early_revenue

Recommended action:

build_demo_package

Security blockers remain for:

fip_healthcare_readiness_diagnostic
fip_secure

This means Assessment Factory Lite can move first while regulated and hardened products remain protected behind their correct security boundaries.

## Relationship to Product Packaging Recommendation

Product Packaging Recommendation selects the candidate and action.

Product Packaging Dashboard displays that recommendation in operator-ready form.

Recommendation answers:

What should we package first?

Dashboard answers:

How should the operator see and act on that recommendation?

## Relationship to Product Security Portfolio

Product Security Portfolio Classification identifies product security tiers and ZTA requirements.

Product Packaging Dashboard consumes those results indirectly through the portfolio dashboard and packaging recommendation layers.

This keeps packaging decisions grounded in deterministic security classification.

## Compliance Boundary

The Product Packaging Dashboard does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It displays packaging guidance and security blockers.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

The Product Packaging Dashboard does not autonomously approve products for launch.

It provides deterministic dashboard guidance from product security and packaging classifications.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain packaging dashboard recommendations later, but AI must not override deterministic product packaging guidance without human-approved policy changes.
