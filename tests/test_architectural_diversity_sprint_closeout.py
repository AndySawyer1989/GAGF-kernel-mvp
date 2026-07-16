from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)

DOC_PATH = Path("docs/ARCHITECTURAL_DIVERSITY_DIAGNOSTICS.md")


def test_architectural_diversity_sprint_closeout_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "2.0.0",
        "release": "assessment-factory-lite-proposal-package",
        "sprint": "4.9",
        "status": "complete",
    }


def test_architectural_diversity_sprint_closeout_routes_exist():
    actual_routes = {route.path for route in app.routes}

    assert "/governance/architecture/diversity" in actual_routes
    assert "/governance/architecture/platform" in actual_routes
    assert "/governance/architecture/dashboard" in actual_routes


def test_architectural_diversity_sprint_closeout_platform_contract():
    response = client.get("/governance/architecture/platform")

    assert response.status_code == 200

    payload = response.json()

    required_fields = {
        "status",
        "component_origin",
        "source_count",
        "kernel_component_count",
        "source_component_count",
        "component_count",
        "architectural_diversity_index",
        "complexity_resilience_ratio",
        "mononal_risk_score",
        "architecture_posture",
        "concentration_risk",
        "platform_architecture_status",
        "dominant_component_type",
        "component_type_counts",
        "subsystem_counts",
        "authority_zone_counts",
        "redundancy_group_counts",
        "diversity_breakdown",
        "component_diagnostics",
        "components",
    }

    assert required_fields.issubset(payload.keys())
    assert payload["status"] == "ok"
    assert payload["component_origin"] == "platform_telemetry"
    assert payload["kernel_component_count"] == 4
    assert payload["component_count"] == len(payload["components"])
    assert payload["component_count"] == len(payload["component_diagnostics"])


def test_architectural_diversity_sprint_closeout_dashboard_contract():
    response = client.get("/governance/architecture/dashboard")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["summary_type"] == "architectural_diversity_dashboard"

    required_fields = {
        "platform_architecture_status",
        "architecture_posture",
        "concentration_risk",
        "operator_message",
        "recommended_action",
        "scorecards",
        "component_summary",
        "risk_summary",
    }

    assert required_fields.issubset(payload.keys())
    assert len(payload["scorecards"]) == 3


def test_architectural_diversity_sprint_closeout_platform_round_trips_to_manual_endpoint():
    platform_payload = client.get(
        "/governance/architecture/platform"
    ).json()

    manual_response = client.post(
        "/governance/architecture/diversity",
        json=platform_payload["components"],
    )

    assert manual_response.status_code == 200

    manual_payload = manual_response.json()

    assert manual_payload["architectural_diversity_index"] == (
        platform_payload["architectural_diversity_index"]
    )
    assert manual_payload["complexity_resilience_ratio"] == (
        platform_payload["complexity_resilience_ratio"]
    )
    assert manual_payload["mononal_risk_score"] == (
        platform_payload["mononal_risk_score"]
    )
    assert manual_payload["architecture_posture"] == (
        platform_payload["architecture_posture"]
    )
    assert manual_payload["concentration_risk"] == (
        platform_payload["concentration_risk"]
    )


def test_architectural_diversity_sprint_closeout_dashboard_aligns_with_platform():
    platform_payload = client.get(
        "/governance/architecture/platform"
    ).json()
    dashboard_payload = client.get(
        "/governance/architecture/dashboard"
    ).json()

    assert dashboard_payload["platform_architecture_status"] == (
        platform_payload["platform_architecture_status"]
    )
    assert dashboard_payload["architecture_posture"] == (
        platform_payload["architecture_posture"]
    )
    assert dashboard_payload["concentration_risk"] == (
        platform_payload["concentration_risk"]
    )

    component_summary = dashboard_payload["component_summary"]

    assert component_summary["component_count"] == (
        platform_payload["component_count"]
    )
    assert component_summary["kernel_component_count"] == (
        platform_payload["kernel_component_count"]
    )
    assert component_summary["source_component_count"] == (
        platform_payload["source_component_count"]
    )


def test_architectural_diversity_sprint_closeout_documentation_mentions_release_surface():
    content = DOC_PATH.read_text(encoding="utf-8")

    assert "ArchitecturalDiversityDiagnosticService" in content
    assert "ArchitecturalDiversityTelemetryAdapter" in content
    assert "ArchitecturalDiversityPlatformService" in content
    assert "ArchitecturalDiversityDashboardService" in content
    assert "POST /governance/architecture/diversity" in content
    assert "GET /governance/architecture/platform" in content
    assert "GET /governance/architecture/dashboard" in content













