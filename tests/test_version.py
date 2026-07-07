from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_version_endpoint_reports_sprint_3_2_complete():
    response = client.get("/version")

    assert response.status_code == 200

    data = response.json()

    assert data["version"] == "0.3.0"
    assert data["release"] == "operator-workstation"
    assert data["sprint"] == "3.2"
    assert data["status"] == "complete"