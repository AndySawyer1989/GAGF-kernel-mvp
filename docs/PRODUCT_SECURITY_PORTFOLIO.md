# Product Security Portfolio Classification

## Purpose

Product Security Portfolio Classification evaluates multiple FIP/GAGF product profiles together.

It classifies each product by security tier, maps Zero Trust Architecture requirements, counts products by risk tier, identifies the highest-risk products, identifies the fastest productization candidates, and recommends a portfolio-level product strategy.

This helps separate products that can move quickly toward demos or revenue from products that require enterprise, regulated, federal, or hardened security tracks.

## Portfolio Classification Flow

Product Profiles
→ Product Security Tier Classification
→ ZTA Control Mapping
→ Tier Counts
→ ZTA Counts
→ Highest-Risk Products
→ Regulated or Federal Products
→ Fastest Productization Candidates
→ Portfolio Recommendation

## Service

### ProductSecurityPortfolioService

File:

backend/app/gagf/product_security_portfolio_service.py

Purpose:

multiple product profiles
→ classify each product
→ map ZTA controls
→ count products by tier
→ identify highest-risk products
→ recommend productization priority

## Endpoint

### Product Security Portfolio Endpoint

POST /products/security-portfolio

Purpose:

Classifies a list of product profiles into a portfolio-level security and productization plan.

## Input Contract

The endpoint accepts a list of product profiles.

Example input:

[
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

## Product Profile Fields

Supported product profile fields include:

product_name
product_category
handles_customer_data
handles_sensitive_data
handles_security_telemetry
handles_health_data
targets_enterprise
targets_healthcare
targets_federal
requires_air_gap
requires_on_prem
is_public_demo
is_internal_only

## Output Contract

The portfolio service returns:

status
classification_type
product_count
tier_counts
zta_counts
highest_security_tier
highest_risk_products
regulated_or_federal_products
fastest_productization_candidates
portfolio_recommendation
products

## Product Result Contract

Each product result includes:

product_name
product_category
security_tier
security_tier_label
compliance_alignment
required_controls
deployment_models
evidence_requirements
tier_recommended_next_action
zta_required
zta_requirement_level
zta_recommended_next_action
zta_controls
portfolio_priority
classification_reason

## Tier Counts

The tier_counts object tracks how many products belong to each security tier:

tier_1_standard_commercial
tier_2_enterprise_secure
tier_3_regulated_sensitive
tier_4_federal_critical

## ZTA Counts

The zta_counts object tracks Zero Trust requirements across the portfolio:

zta_required
zta_recommended
zta_not_required

Interpretation:

zta_required counts Tier 3 and Tier 4 products.

zta_recommended counts Tier 2 products.

zta_not_required counts Tier 1 products.

## Highest Security Tier

highest_security_tier identifies the highest security burden present in the portfolio.

Possible values include:

none
tier_1_standard_commercial
tier_2_enterprise_secure
tier_3_regulated_sensitive
tier_4_federal_critical

If any Tier 4 product exists, the highest security tier is tier_4_federal_critical.

If no Tier 4 product exists but a Tier 3 product exists, the highest security tier is tier_3_regulated_sensitive.

## Highest-Risk Products

highest_risk_products lists the products that belong to the highest security tier in the portfolio.

Example:

If FIP Secure is the only Tier 4 product, highest_risk_products returns:

fip_secure

## Regulated or Federal Products

regulated_or_federal_products lists products classified as:

tier_3_regulated_sensitive
tier_4_federal_critical

These products require separate compliance, data-boundary, and security planning.

Examples:

fip_healthcare_readiness_diagnostic
fip_secure

## Fastest Productization Candidates

fastest_productization_candidates lists products classified as:

tier_1_standard_commercial
tier_2_enterprise_secure

These products are usually better candidates for faster demos, commercial pilots, or early revenue packaging.

Examples:

assessment_factory_lite
fip_governance_diagnostics_saas

## Portfolio Recommendation

The service may recommend:

add_product_profiles_to_classify_portfolio
prioritize_standard_commercial_productization
prioritize_enterprise_products_with_zta_readiness_review
separate_regulated_products_into_compliance_ready_track
separate_federal_critical_products_into_hardened_track

## Recommendation Logic

If the portfolio is empty, the service recommends:

add_product_profiles_to_classify_portfolio

If any Tier 4 product exists, the service recommends:

separate_federal_critical_products_into_hardened_track

If no Tier 4 product exists but any Tier 3 product exists, the service recommends:

separate_regulated_products_into_compliance_ready_track

If no Tier 4 or Tier 3 product exists but any Tier 2 product exists, the service recommends:

prioritize_enterprise_products_with_zta_readiness_review

If only Tier 1 products exist, the service recommends:

prioritize_standard_commercial_productization

## Product Priority

Each product receives a portfolio_priority.

Possible values include:

fast_productization_candidate
enterprise_ready_productization_candidate
define_compliance_boundary_before_productization
harden_before_productization
complete_zta_plan_before_productization

## Product Strategy Meaning

Product Security Portfolio Classification turns the FIP/GAGF roadmap into a product-planning system.

It helps answer:

Which products can move toward demos fastest?

Which products are enterprise-ready candidates?

Which products need SOC 2 readiness?

Which products need HIPAA-sensitive boundaries?

Which products need FedRAMP High, on-prem, air-gapped, or critical infrastructure planning?

Which products should be separated into hardened tracks?

## Current Product Examples

Assessment Factory Lite:

tier_1_standard_commercial
fast_productization_candidate

FIP Governance Diagnostics SaaS:

tier_2_enterprise_secure
enterprise_ready_productization_candidate

FIP Healthcare Readiness Diagnostic:

tier_3_regulated_sensitive
define_compliance_boundary_before_productization

FIP Secure:

tier_4_federal_critical
harden_before_productization

ESY secure runtime:

tier_4_federal_critical
harden_before_productization

Personal Friction Assistant:

tier_1_standard_commercial or tier_2_enterprise_secure depending on customer data scope

Game Adaptive Intelligence API:

tier_1_standard_commercial or tier_2_enterprise_secure depending on customer data scope

## Productization Checkpoint

Product Security Portfolio Classification is a product checkpoint.

When this layer is complete, the platform can begin separating:

fast demo products
enterprise commercial products
regulated products
federal or hardened products

This supports a practical development rule:

Do not burden every product with Tier 4 controls.

Do not expose sensitive or regulated products before defining the correct security and compliance boundary.

## Relationship to Product Security Tiering

Product Security Tiering classifies one product.

Product Security Portfolio Classification classifies many products and produces portfolio-level planning outputs.

Product Security Tiering answers:

What tier is this product?

Product Security Portfolio Classification answers:

How should this whole product portfolio be prioritized and separated?

## Relationship to ZTA Control Mapping

ZTA Control Mapping maps one product tier to Zero Trust controls.

Product Security Portfolio Classification applies ZTA mapping across many products.

ZTA Control Mapping answers:

Does this product require Zero Trust controls?

Product Security Portfolio Classification answers:

How many products require ZTA, and which products should be hardened first?

## Compliance Boundary

Product Security Portfolio Classification does not certify products as FedRAMP High, HIPAA compliant, or SOC 2 audited.

It classifies security posture, Zero Trust requirements, and productization priority.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, and third-party review where applicable.

## Constitutional Boundary

Product Security Portfolio Classification does not autonomously approve products for launch.

It provides deterministic portfolio classification and productization guidance.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may explain portfolio recommendations later, but AI must not override deterministic product security classification without human-approved policy changes.
