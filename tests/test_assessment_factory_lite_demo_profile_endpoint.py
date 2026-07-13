from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def build_portfolio_profiles():
    return [
        {
            "product_name": "Assessment Factory Lite",
            "product_category": "demo",
            "is_public_demo": True,
        },
        {
            "product_name": "FIP Governance Diagnostics SaaS",
            "product_category": "governance_diagnostics",
            "targets_enterprise": True,
            "handles_customer_data": True,
        },
        {
            "product_name": "FIP Healthcare Readiness Diagnostic",
            "product_category": "compliance",
            "targets_healthcare": True,
            "handles_health_data": True,
        },
        {
            "product_name": "FIP Secure",
            "product_category": "secure_enterprise",
            "targets_federal": True,
            "requires_air_gap": True,
            "requires_on_prem": True,
        },
    ]


def test_assessment_factory_lite_demo_profile_endpoint_builds_from_profiles():
    response = client.post(
        "/products/assessment-factory-lite/demo-profile",
        json={"product_profiles": build_portfolio_profiles()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["profile_type"] == "assessment_factory_lite_demo_profile"
    assert payload["selected_product"] == "assessment_factory_lite"
    assert payload["package_name"] == "Assessment Factory Lite Demo Package"
    assert payload["selected_track"] == "fast_productization"
    assert payload["is_assessment_factory_lite"] is True


def test_assessment_factory_lite_demo_profile_endpoint_marks_demo_ready():
    response = client.post(
        "/products/assessment-factory-lite/demo-profile",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["demo_readiness"] == {
        "ready_for_demo_package": True,
        "decision": "go",
        "reason": "fast_demo_candidate_available",
        "requires_customer_data": False,
        "requires_regulated_data": False,
        "requires_federal_data": False,
        "requires_production_access": False,
    }


def test_assessment_factory_lite_demo_profile_endpoint_sets_demo_boundary():
    response = client.post(
        "/products/assessment-factory-lite/demo-profile",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["demo_boundary"]["boundary_type"] == (
        "demo_only_sample_data"
    )
    assert "sample_csv" in payload["demo_boundary"]["allowed_data"]
    assert "synthetic_workflow_events" in (
        payload["demo_boundary"]["allowed_data"]
    )
    assert "regulated_data" in payload["demo_boundary"]["prohibited_data"]
    assert "federal_data" in payload["demo_boundary"]["prohibited_data"]
    assert payload["demo_boundary"]["certification_claims_allowed"] is False


def test_assessment_factory_lite_demo_profile_endpoint_sets_workflow_and_sections():
    response = client.post(
        "/products/assessment-factory-lite/demo-profile",
        json={"product_profiles": build_portfolio_profiles()},
    )

    payload = response.json()

    assert payload["demo_workflow"] == [
        "load_demo_profile",
        "upload_sample_csv",
        "run_governance_diagnostics",
        "review_governance_drag_summary",
        "review_top_friction_points",
        "display_recommended_intervention",
        "export_demo_summary",
    ]
    assert "governance_drag_summary" in payload["dashboard_sections"]
    assert "recommended_intervention" in payload["dashboard_sections"]
    assert "executive_summary" in payload["report_sections"]
    assert "compliance_disclaimer" in payload["report_sections"]


def test_assessment_factory_lite_demo_profile_endpoint_accepts_existing_checkpoint():
    checkpoint_response = client.post(
        "/products/packaging/checkpoint",
        json={"product_profiles": build_portfolio_profiles()},
    )

    assert checkpoint_response.status_code == 200

    response = client.post(
        "/products/assessment-factory-lite/demo-profile",
        json={"checkpoint": checkpoint_response.json()},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["recommended_action"] == (
        "build_assessment_factory_lite_demo"
    )
    assert payload["operator_message"] == (
        "Assessment Factory Lite Demo Package is ready to configure as a "
        "demo-only sample-data package."
    )


def test_assessment_factory_lite_demo_profile_endpoint_route_exists():
    actual_routes = {route.path for route in app.routes}

    assert "/products/assessment-factory-lite/demo-profile" in actual_routes



