from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_version_endpoint_reports_product_security_portfolio_release_complete():
    response = client.get("/version")

    assert response.status_code == 200

    assert response.json() == {
        "version": "1.9.0",
        "release": "assessment-factory-lite-commercial-offer",
        "sprint": "4.8",
        "status": "complete",
    }











