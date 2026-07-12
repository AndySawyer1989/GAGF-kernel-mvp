from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_version_endpoint_reports_product_security_portfolio_release_complete():
    response = client.get("/version")

    assert response.status_code == 200

    assert response.json() == {
        "version": "1.1.0",
        "release": "assessment-factory-lite-demo-package",
        "sprint": "4.0",
        "status": "complete",
    }



