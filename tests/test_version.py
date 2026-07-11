from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_version_endpoint_reports_product_security_portfolio_release_complete():
    response = client.get("/version")

    assert response.status_code == 200

    assert response.json() == {
        "version": "0.8.0",
        "release": "product-security-portfolio",
        "sprint": "3.7",
        "status": "complete",
    }
