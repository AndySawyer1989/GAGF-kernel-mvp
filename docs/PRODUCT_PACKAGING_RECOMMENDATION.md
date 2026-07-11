# Product Packaging Recommendation

## Purpose

Product Packaging Recommendation converts product security portfolio dashboard output into an actionable packaging decision.

It recommends which product should be packaged first, which products belong in demo, enterprise, regulated, or hardened tracks, and which security blockers must be handled before productization.

This layer helps the FIP/GAGF roadmap move from platform engineering into practical demo, pilot, and early-revenue planning.

## Recommendation Flow

Product Profiles or Portfolio Dashboard
→ Product Security Portfolio Classification
→ Product Security Portfolio Dashboard
→ Product Packaging Recommendation
→ First Packaging Candidate
→ Primary Packaging Track
→ Candidate Track Lists
→ Security Blockers
→ Packaging Recommendation
→ Operator Message
→ Next Action

## Service

### ProductPackagingRecommendationService

File:

backend/app/gagf/product_packaging_recommendation_service.py

Purpose:

portfolio dashboard result
→ choose first packaging candidate
→ separate demo, enterprise, regulated, and hardened tracks
→ identify security blockers
→ recommend product packaging action

## Endpoint

### Product Packaging Recommendation Endpoint

POST /products/packaging/recommendation

Purpose:

Builds a product packaging recommendation from either product profiles or an existing portfolio dashboard.

## Input Modes

The endpoint supports two input modes.

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

In this mode, the endpoint first runs ProductSecurityPortfolioService, then ProductSecurityPortfolioDashboardService, then ProductPackagingRecommendationService.

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

In this mode, the endpoint builds the packaging recommendation directly from the supplied dashboard result.

## Output Contract

The recommendation returns:

status
recommendation_type
first_packaging_candidate
primary_packaging_track
demo_candidates
enterprise_candidates
regulated_candidates
hardened_candidates
zta_planning_candidates
security_blockers
packaging_recommendation
operator_message
next_action

## Recommendation Type

The recommendation_type value is:

product_packaging_recommendation

## First Packaging Candidate

first_packaging_candidate identifies the product that should be packaged first.

It includes:

product_name
track
reason

Example:

{
  "product_name": "assessment_factory_lite",
  "track": "fast_productization",
  "reason": "lowest_security_burden"
}

## Candidate Selection Order

The service selects the first packaging candidate in this order:

fast_productization
enterprise_ready
regulated_boundary
hardened_federal
none

This means the platform prefers the lowest-security-burden candidate first, unless no fast candidate exists.

## Primary Packaging Track

primary_packaging_track converts the selected candidate track into a product packaging path.

Possible values include:

demo_or_early_revenue
enterprise_pilot
regulated_readiness_package
federal_hardened_package
none

## Candidate Lists

The service preserves all major candidate tracks.

demo_candidates:

Products that can move fastest toward demo, pilot, or early revenue.

enterprise_candidates:

Products that can move toward enterprise pilot packaging with security readiness review.

regulated_candidates:

Products that require regulated compliance boundary definition before packaging.

hardened_candidates:

Products that require hardened federal, on-prem, air-gapped, or critical infrastructure security planning.

zta_planning_candidates:

Products that must complete Zero Trust planning before productization.

## Security Blockers

security_blockers lists security or compliance concerns that block unrestricted productization.

Possible blockers include:

federal_hardened_track_required
regulated_compliance_boundary_required
zta_required_for_some_products
hardened_products_not_fast_packaging_candidates
regulated_products_need_boundary_definition

## Packaging Recommendation

packaging_recommendation gives a compact recommendation key.

Possible values include:

package_fast_demo_or_assessment_product_first
package_enterprise_pilot_with_security_readiness
define_regulated_boundary_before_product_packaging
define_hardened_federal_track_before_product_packaging
add_or_refine_product_candidates
review_packaging_path

## Next Action

next_action gives the Operator Workstation a compact action key.

Possible values include:

build_demo_package
build_enterprise_pilot_package
define_compliance_boundary
define_hardened_security_boundary
add_product_candidates
review_product_packaging

## Operator Message

operator_message gives a plain-language explanation of what to do next.

Example:

Package assessment_factory_lite first as the fastest demo or early-revenue candidate.

## Current Strategic Result

Using the current product security portfolio example, the first packaging candidate is:

assessment_factory_lite

Track:

fast_productization

Primary packaging track:

demo_or_early_revenue

Next action:

build_demo_package

This means Assessment Factory Lite is currently the best first product to package for demo, pilot, or early revenue because it has the lowest security burden.

## Product Track Interpretation

Assessment Factory Lite:

demo_or_early_revenue

FIP Governance Diagnostics SaaS:

enterprise_pilot

FIP Healthcare Readiness Diagnostic:

regulated_readiness_package

FIP Secure:

federal_hardened_package

ESY secure runtime:

federal_hardened_package

## Product Strategy Meaning

Product Packaging Recommendation adds product decision intelligence to the roadmap.

The platform is no longer only classifying architecture and security posture.

It can now recommend what to package first.

This supports a practical sequencing rule:

Package low-risk demo or assessment products first.

Prepare enterprise products with security readiness review.

Do not package regulated products before defining compliance boundaries.

Do not package federal, FedRAMP High-aligned, on-prem, air-gapped, or critical infrastructure products before defining a hardened security track.

## Relationship to Product Security Portfolio Dashboard

Product Security Portfolio Dashboard shows the portfolio security posture.

Product Packaging Recommendation converts that dashboard into a concrete packaging decision.

Portfolio dashboard answers:

What does the product security portfolio look like?

Product packaging recommendation answers:

What should we package first?

## Relationship to ZTA Control Mapping

ZTA Control Mapping identifies which products require Zero Trust Architecture.

Product Packaging Recommendation treats ZTA-heavy products as security-sensitive packaging candidates.

Products requiring ZTA may still be valuable, but they should not be treated as fast low-burden demo products unless their security boundary is already defined.

## Compliance Boundary

Product Packaging Recommendation does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It recommends product packaging sequence and identifies security blockers.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

Product Packaging Recommendation does not autonomously approve products for launch.

It provides deterministic packaging guidance.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain packaging recommendations later, but AI must not override deterministic product packaging guidance without human-approved policy changes.
