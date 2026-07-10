from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_version_endpoint_reports_sprint_3_4_complete():
    response = client.get("/version")

    assert response.status_code == 200

    assert response.json() == {
        "version": "0.5.0",
        "release": "evidence-intelligence",
        "sprint": "3.4",
        "status": "complete",
    }