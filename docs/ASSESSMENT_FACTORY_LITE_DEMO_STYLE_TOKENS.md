# Assessment Factory Lite Demo Style Tokens

## Purpose

The Assessment Factory Lite Demo Style Tokens layer defines deterministic buyer-facing visual tokens for the demo screen.

It gives the Operator Workstation a consistent visual identity using the project's orange, white, gold, and purple palette.

The style token layer prepares the demo for buyer-facing polish without introducing frontend JavaScript, persistent styling preferences, tenant-specific themes, or production branding controls.

## Capability Chain

Assessment Factory Lite Demo Package
→ Demo Usability Layer
→ Style Token Service
→ Style Token Endpoint
→ Buyer-Facing Palette
→ Typography Tokens
→ Layout Tokens
→ Component Tokens
→ Accessibility Tokens
→ HTML Style Integration

## Service

### AssessmentFactoryLiteDemoStyleTokenService

File:

backend/app/gagf/assessment_factory_lite_demo_style_token_service.py

Purpose:

Build deterministic style tokens for the Assessment Factory Lite demo.

The service returns stable visual tokens for buyer-facing screen polish.

## Endpoint

### Style Token Endpoint

GET /products/assessment-factory-lite/demo-style-tokens

Purpose:

Returns deterministic style tokens for the Assessment Factory Lite demo screen.

The Operator Workstation can fetch this endpoint before rendering or styling the visible demo screen.

## Response Contract

The style token response includes:

status
token_type
package_name
release
version
brand_identity
color_tokens
typography_tokens
spacing_tokens
layout_tokens
component_tokens
accessibility_tokens
demo_boundary
operator_message
recommended_action

## Token Type

The token_type value is:

assessment_factory_lite_demo_style_tokens

## Release Marker

The style token object belongs to:

release:

assessment-factory-lite-demo-usability

version:

1.5.0

## Recommended Action

The recommended_action value is:

apply_demo_style_tokens_to_html_screen

## Brand Identity

The brand identity defines the demo's visual purpose.

style_name:

assessment_factory_lite_buyer_demo

visual_intent:

clean_efficient_trustworthy_operator_screen

primary_audience:

operations_leaders_and_it_managers

tone:

practical_clear_confident

identity_colors:

orange
white
gold
purple

## Color Tokens

The color token set includes:

background
surface
surface_alt
text_primary
text_secondary
brand_orange
brand_gold
brand_purple
border_subtle
success
warning
danger
info

Core color values:

background #FFFFFF
surface #FFF8EF
surface_alt #F7F2FF
brand_orange #F97316
brand_gold #D6A21E
brand_purple #6D28D9
success #166534
warning #B45309
danger #B91C1C
info #1D4ED8

## Typography Tokens

The typography token set includes:

font_family
display_size
heading_size
body_size
caption_size
display_weight
heading_weight
body_weight
line_height

The font stack includes:

Inter
ui-sans-serif
system-ui
-apple-system
BlinkMacSystemFont
Segoe UI
sans-serif

Core typography values:

display_size 2.25rem
heading_size 1.35rem
body_size 1rem
caption_size 0.875rem
display_weight 750
heading_weight 700
body_weight 450
line_height 1.55

## Spacing Tokens

The spacing token set includes:

space_xs 0.25rem
space_sm 0.5rem
space_md 1rem
space_lg 1.5rem
space_xl 2rem
space_2xl 3rem

## Layout Tokens

The layout token set includes:

screen_max_width
screen_padding
section_gap
card_grid_min
card_grid_gap
header_radius
card_radius

Core layout values:

screen_max_width 1180px
screen_padding 2rem
section_gap 1.5rem
card_grid_min 260px
card_grid_gap 1rem
header_radius 1.25rem
card_radius 1rem

## Component Tokens

The component token set includes:

header_gradient
header_text_color
card_background
card_border
card_shadow
warning_background
warning_border
scenario_card_background
scenario_card_border
sample_loader_background
sample_loader_border

The header gradient includes:

#F97316
#D6A21E
#6D28D9

Core component values:

header_text_color #FFFFFF
card_background #FFFFFF
warning_background #FFF7ED
scenario_card_background #F7F2FF
sample_loader_background #FFF8EF
card_shadow 0 10px 28px rgba(36, 26, 18, 0.08)

## Accessibility Tokens

The accessibility token set includes:

minimum_contrast_goal
focus_outline
focus_offset
reduced_motion_safe
color_alone_required

Core accessibility values:

minimum_contrast_goal WCAG_AA
focus_outline 3px solid #6D28D9
focus_offset 3px
reduced_motion_safe true
color_alone_required false

## Operator Workstation Use

The Operator Workstation can call:

GET /products/assessment-factory-lite/demo-style-tokens

Then it can use the returned tokens to style:

demo header
scenario menu
sample loader
warning strip
operator cards
export preview
operator actions

## HTML Screen Use

The next integration step should apply these tokens to:

POST /products/assessment-factory-lite/demo-ui/html

The HTML renderer should embed deterministic CSS generated from the style tokens.

The result should make the visible demo screen feel more like a buyer-facing product and less like raw diagnostic output.

## Product Strategy Meaning

The style token layer starts the buyer-facing polish track.

The diagnostic flow already works.

The scenario menu already works.

The sample loader already works.

The next product risk is presentation quality.

The style token layer gives the project a stable visual foundation before export polish.

## Design Identity

The visual direction should remain:

clean
efficient
intuitive
operator-friendly
buyer-readable
practical
trustworthy

The identity colors should remain:

orange
white
gold
purple

## Demo-Only Boundary

The style token layer remains demo-only.

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

This story does not add:

frontend browser JavaScript
tenant-specific themes
persistent style preferences
user authentication
production branding management
PDF generation
interactive export builder
customer design system integration
formal accessibility certification
third-party design audit
regulated data processing
federal data processing
production customer deployment

## Compliance Boundary

The Assessment Factory Lite Demo Style Tokens layer does not certify products as FedRAMP High, HIPAA compliant, SOC 2 audited, WCAG certified, or production-ready.

It provides deterministic visual tokens for a demo-only workflow.

Formal compliance still requires policies, implementation, evidence collection, audits, authorization boundaries, accessibility review, and third-party review where applicable.

## Constitutional Boundary

The Assessment Factory Lite Demo Style Tokens layer does not autonomously approve production launch, production data use, customer deployment, certification claims, or live integrations.

It provides deterministic visual tokens for buyer-facing demo polish.

The deterministic GAGF Kernel remains the authoritative decision and verification layer.

AI may later explain style token choices, but AI must not override deterministic demo-only boundaries without human-approved policy changes.
