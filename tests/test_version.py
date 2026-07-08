from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_version_endpoint_reports_sprint_3_3_complete():
    response = client.get("/version")

    assert response.status_code == 200

    data = response.json()

    assert data["version"] == "0.4.0"
    assert data["release"] == "evidence-expansion"
    assert data["sprint"] == "3.3"
    assert data["status"] == "complete"