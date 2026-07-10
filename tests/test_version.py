from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_version_endpoint_reports_sprint_3_5_complete():
    response = client.get("/version")

    assert response.status_code == 200

    assert response.json() == {
        "version": "0.6.0",
        "release": "governance-diagnostic-chain",
        "sprint": "3.5",
        "status": "complete",
    }