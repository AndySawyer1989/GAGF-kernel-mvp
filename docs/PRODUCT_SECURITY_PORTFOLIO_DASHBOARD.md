# Product Security Portfolio Dashboard

## Purpose

The Product Security Portfolio Dashboard converts a product security portfolio classification result into an operator-ready dashboard summary.

It helps the Operator Workstation display product security posture, Zero Trust burden, productization tracks, highest-risk products, and recommended operator action.

## Dashboard Flow

Product Profiles or Portfolio Result
→ Product Security Portfolio Classification
→ Product Security Portfolio Dashboard Summary
→ Tier Distribution
→ ZTA Distribution
→ Productization Tracks
→ Risk Summary
→ Highest-Risk Summary
→ Dashboard Cards
→ Operator Message
→ Recommended Action

## Service

### ProductSecurityPortfolioDashboardService

File:

backend/app/gagf/product_security_portfolio_dashboard_service.py

Purpose:

portfolio classification result
→ dashboard-ready product security summary
→ tier distribution
→ ZTA distribution
→ productization tracks
→ highest-risk product summary
→ operator recommendation

## Endpoint

### Product Security Portfolio Dashboard Endpoint

POST /products/security-portfolio/dashboard

Purpose:

Builds a dashboard-ready summary from either product profiles or an existing portfolio classification result.

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
      "product_name": "FIP Secure",
      "product_category": "secure_enterprise",
      "targets_federal": true,
      "requires_air_gap": true,
      "requires_on_prem": true
    }
  ]
}

In this mode, the endpoint first runs ProductSecurityPortfolioService and then builds the dashboard summary.

### Mode 2 — Existing Portfolio Result

The endpoint may receive portfolio_result.

Example:

{
  "portfolio_result": {
    "status": "ok",
    "classification_type": "product_security_portfolio",
    "product_count": 2,
    "tier_counts": {
      "tier_1_standard_commercial": 1,
      "tier_2_enterprise_secure": 0,
      "tier_3_regulated_sensitive": 0,
      "tier_4_federal_critical": 1
    },
    "zta_counts": {
      "zta_required": 1,
      "zta_recommended": 0,
      "zta_not_required": 1
    }
  }
}

In this mode, the endpoint builds the dashboard summary directly from the supplied portfolio result.

## Output Contract

The dashboard returns:

status
summary_type
product_count
portfolio_recommendation
operator_message
recommended_action
tier_distribution
zta_distribution
productization_tracks
risk_summary
highest_risk_summary
dashboard_cards

## Summary Type

The summary_type value is:

product_security_portfolio_dashboard

## Tier Distribution

tier_distribution converts internal tier keys into dashboard-friendly labels.

The dashboard returns:

standard_commercial
enterprise_secure
regulated_sensitive
federal_critical

These map to:

tier_1_standard_commercial
tier_2_enterprise_secure
tier_3_regulated_sensitive
tier_4_federal_critical

## ZTA Distribution

zta_distribution summarizes Zero Trust Architecture burden across the portfolio.

The dashboard returns:

required
recommended
not_required

Interpretation:

required counts products that require ZTA, usually Tier 3 and Tier 4.

recommended counts products where ZTA readiness should be reviewed, usually Tier 2.

not_required counts products that do not require ZTA, usually Tier 1.

## Productization Tracks

productization_tracks separates products into operational tracks.

The dashboard returns:

fast_productization
enterprise_ready
regulated_boundary
hardened_federal
zta_planning

## Track Interpretation

fast_productization means the product is a good candidate for faster demo, pilot, or early revenue packaging.

enterprise_ready means the product can move toward enterprise packaging with enterprise security readiness.

regulated_boundary means the product needs a regulated compliance boundary before productization.

hardened_federal means the product needs hardened federal, on-prem, air-gapped, or critical infrastructure planning before productization.

zta_planning means the product must complete Zero Trust planning before productization.

## Risk Summary

risk_summary includes:

highest_security_tier
highest_risk_product_count
regulated_or_federal_product_count
requires_hardened_track
requires_regulated_track

## Highest-Risk Summary

highest_risk_summary includes:

highest_security_tier
highest_risk_products
regulated_or_federal_products
fastest_productization_candidates

## Dashboard Cards

dashboard_cards provide compact cards for UI display.

Current cards include:

Products Classified
Federal / Critical Products
Regulated / Sensitive Products
ZTA Required
Fast Productization Candidates

Each card includes:

label
value
status

Card status may be:

ok
attention_required

## Operator Message

operator_message gives the operator a plain-language interpretation of the portfolio security state.

Possible messages include:

Add product profiles to classify portfolio security posture.

Portfolio is ready for standard commercial productization.

Prioritize enterprise products while reviewing ZTA readiness.

Separate regulated products into a compliance-ready track.

Separate federal or critical products into a hardened track.

## Recommended Action

recommended_action gives the Operator Workstation a compact action key.

Possible values include:

add_product_profiles
package_standard_commercial_product
package_enterprise_product_with_zta_review
define_regulated_compliance_boundary
define_federal_hardened_product_track
review_product_security_portfolio

## Product Strategy Meaning

The dashboard makes the product portfolio usable for product planning.

It shows which products can move fast and which products must be separated into secure tracks.

The dashboard supports this product rule:

Do not burden every product with Tier 4 controls.

The dashboard also supports this security rule:

Do not productize regulated, HIPAA-sensitive, FedRAMP High-aligned, air-gapped, or federal products before defining the correct security boundary.

## Example Product Tracks

Assessment Factory Lite:

fast_productization

FIP Governance Diagnostics SaaS:

enterprise_ready

FIP Healthcare Readiness Diagnostic:

regulated_boundary

FIP Secure:

hardened_federal

ESY secure runtime:

hardened_federal

## Relationship to Product Security Portfolio Classification

Product Security Portfolio Classification produces the deterministic portfolio result.

Product Security Portfolio Dashboard converts that result into an operator-ready dashboard format.

Portfolio classification answers:

How should the portfolio be classified?

Portfolio dashboard answers:

How should the operator understand and act on the portfolio classification?

## Relationship to ZTA Control Mapping

ZTA Control Mapping identifies which products require Zero Trust Architecture.

The portfolio dashboard summarizes the total ZTA burden across the portfolio.

This allows the operator to see whether the portfolio is light enough for fast productization or heavy enough to require regulated, federal, or hardened planning.

## Compliance Boundary

The Product Security Portfolio Dashboard does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It displays security posture, Zero Trust burden, and productization guidance.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

The Product Security Portfolio Dashboard does not autonomously approve products for launch.

It provides deterministic dashboard guidance from product security classifications.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain dashboard recommendations later, but AI must not override deterministic product security classification or dashboard guidance without human-approved policy changes.
