from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_version_endpoint_reports_architectural_diversity_release_complete():
    response = client.get("/version")

    assert response.status_code == 200

    assert response.json() == {
        "version": "0.7.0",
        "release": "architectural-diversity-diagnostics",
        "sprint": "3.6",
        "status": "complete",
    }