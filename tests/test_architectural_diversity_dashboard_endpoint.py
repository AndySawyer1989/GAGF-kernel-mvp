from fastapi.testclient import TestClient

from backend.app.gagf.architectural_diversity_dashboard_service import (
    ArchitecturalDiversityDashboardService,
)
from backend.app.main import app


client = TestClient(app)


def fake_dashboard_summary():
    return {
        "status": "ok",
        "summary_type": "product_security_portfolio_dashboard",
        "platform_architecture_status": "platform_architecture_balanced",
        "architecture_posture": "mixed_resilience_architecture",
        "concentration_risk": "moderate",
        "operator_message": (
            "Architecture is balanced with manageable concentration risk."
        ),
        "recommended_action": "monitor_architecture_concentration",
        "scorecards": [
            {
                "label": "product security portfolio Index",
                "metric": "product_security_portfolio_index",
                "value": 0.5682,
                "interpretation": "moderate_diversity",
            },
            {
                "label": "Complexity Resilience Ratio",
                "metric": "complexity_resilience_ratio",
                "value": 0.6637,
                "interpretation": "moderate_resilience",
            },
            {
                "label": "Mononal Risk Score",
                "metric": "mononal_risk_score",
                "value": 0.4318,
                "interpretation": "moderate_mononal_risk",
            },
        ],
        "component_summary": {
            "component_count": 11,
            "kernel_component_count": 4,
            "source_component_count": 7,
            "dominant_component_type": "connector",
            "component_type_counts": {
                "kernel": 1,
                "ledger": 2,
                "worker": 1,
                "connector": 7,
            },
            "subsystem_counts": {
                "decision": 2,
                "security": 2,
                "identity": 2,
            },
            "authority_zone_counts": {
                "kernel": 1,
                "ledger": 2,
                "source_connector": 7,
            },
            "redundancy_group_counts": {
                "kernel-core": 1,
                "security_sources": 2,
                "identity_sources": 2,
            },
        },
        "risk_summary": {
            "architecture_posture": "mixed_resilience_architecture",
            "concentration_risk": "moderate",
            "mononal_risk_score": 0.4318,
            "platform_architecture_status": "platform_architecture_balanced",
            "highest_attention_area": "none",
        },
    }


def test_product_security_portfolio_dashboard_endpoint_exists(monkeypatch):
    monkeypatch.setattr(
        ArchitecturalDiversityDashboardService,
        "get_summary",
        lambda self: fake_dashboard_summary(),
    )

    response = client.get("/governance/architecture/dashboard")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_product_security_portfolio_dashboard_endpoint_returns_summary_header(
    monkeypatch,
):
    monkeypatch.setattr(
        ArchitecturalDiversityDashboardService,
        "get_summary",
        lambda self: fake_dashboard_summary(),
    )

    payload = client.get("/governance/architecture/dashboard").json()

    assert payload["summary_type"] == "product_security_portfolio_dashboard"
    assert payload["platform_architecture_status"] == (
        "platform_architecture_balanced"
    )
    assert payload["architecture_posture"] == "mixed_resilience_architecture"
    assert payload["concentration_risk"] == "moderate"


def test_product_security_portfolio_dashboard_endpoint_returns_operator_guidance(
    monkeypatch,
):
    monkeypatch.setattr(
        ArchitecturalDiversityDashboardService,
        "get_summary",
        lambda self: fake_dashboard_summary(),
    )

    payload = client.get("/governance/architecture/dashboard").json()

    assert payload["operator_message"] == (
        "Architecture is balanced with manageable concentration risk."
    )
    assert payload["recommended_action"] == (
        "monitor_architecture_concentration"
    )


def test_product_security_portfolio_dashboard_endpoint_returns_scorecards(
    monkeypatch,
):
    monkeypatch.setattr(
        ArchitecturalDiversityDashboardService,
        "get_summary",
        lambda self: fake_dashboard_summary(),
    )

    payload = client.get("/governance/architecture/dashboard").json()

    assert len(payload["scorecards"]) == 3

    metrics = {
        scorecard["metric"]
        for scorecard in payload["scorecards"]
    }

    assert metrics == {
        "product_security_portfolio_index",
        "complexity_resilience_ratio",
        "mononal_risk_score",
    }


def test_product_security_portfolio_dashboard_endpoint_returns_component_and_risk_summary(
    monkeypatch,
):
    monkeypatch.setattr(
        ArchitecturalDiversityDashboardService,
        "get_summary",
        lambda self: fake_dashboard_summary(),
    )

    payload = client.get("/governance/architecture/dashboard").json()

    assert payload["component_summary"]["component_count"] == 11
    assert payload["component_summary"]["kernel_component_count"] == 4
    assert payload["component_summary"]["source_component_count"] == 7
    assert payload["component_summary"]["dominant_component_type"] == (
        "connector"
    )

    assert payload["risk_summary"]["platform_architecture_status"] == (
        "platform_architecture_balanced"
    )
    assert payload["risk_summary"]["mononal_risk_score"] == 0.4318


def test_product_security_portfolio_dashboard_endpoint_preserves_release_marker():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": "1.7.0",
        "release": "assessment-factory-lite-demo-delivery-packaging",
        "sprint": "4.6",
        "status": "complete",
    }










