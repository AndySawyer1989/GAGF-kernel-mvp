from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_sprint_3_4_release_marker_is_complete():
    response = client.get("/version")

    assert response.status_code == 200

    data = response.json()

    assert data["version"] == "0.5.0"
    assert data["release"] == "evidence-intelligence"
    assert data["sprint"] == "3.4"
    assert data["status"] == "complete"


def test_sprint_3_4_evidence_intelligence_endpoints_are_available():
    expected_routes = {
        "/evidence/quality",
        "/evidence/agreement",
        "/evidence/conflicts",
        "/evidence/diagnostics",
        "/evidence/confidence",
        "/snapshot-diagnostics",
        "/snapshot-diagnostics/summary",
        "/snapshot-diagnostics/risk",
    }

    actual_routes = {route.path for route in app.routes}

    assert expected_routes.issubset(actual_routes)
