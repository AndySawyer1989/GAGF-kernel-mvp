import pytest

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)

pytestmark = pytest.mark.usefixtures("legacy_api_test_identity")


def test_dashboard_includes_latest_evidence_source():
    response = client.get("/dashboard")

    assert response.status_code == 200

    data = response.json()

    assert "latest_evidence_source" in data






