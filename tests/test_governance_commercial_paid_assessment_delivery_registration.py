from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.governance_assessment_api_registration import (
    register_governance_assessment_api,
)


BASE = (
    "/api/v1/governance-paid-assessments/"
    "tenant-alpha/client-acme/engagement-001/assessment-001"
)


def route_paths(app: FastAPI) -> tuple[str, ...]:
    return tuple(
        path
        for route in app.routes
        if (path := getattr(route, "path", None)) is not None
    )


def actor_headers(
    *,
    tenant_id: str = "tenant-alpha",
    roles: str = "assessment:read",
) -> dict[str, str]:
    return {
        "X-Tenant-ID": tenant_id,
        "X-Actor-ID": "actor-001",
        "X-Actor-Roles": roles,
    }


def approval_payload() -> dict[str, object]:
    return {
        "approval_id": "delivery-approval-001",
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "report_id": "report-001",
        "approved_by": "Human Reviewer",
        "approved_at": "2026-09-02T20:00:00+00:00",
        "scope_approved": True,
        "evidence_boundary_approved": True,
        "buyer_language_approved": True,
        "delivery_approved": True,
    }


def confirmation_payload() -> dict[str, object]:
    return {
        "delivery_event_id": "delivery-event-001",
        "tenant_id": "tenant-alpha",
        "client_id": "client-acme",
        "engagement_id": "engagement-001",
        "assessment_id": "assessment-001",
        "report_id": "report-001",
        "delivered_by": "Authorized Human Deliverer",
        "delivered_at": "2026-09-02T20:15:00+00:00",
        "delivery_method": "email",
        "delivery_reference": "customer-message-001",
        "delivery_completed": True,
    }


def build_registered_app(tmp_path) -> FastAPI:
    app = FastAPI()

    register_governance_assessment_api(
        app=app,
        database_path=(
            tmp_path
            / "assessment.sqlite3"
        ),
    )

    return app


def test_registration_adds_all_commercial_delivery_routes(
    tmp_path,
) -> None:
    app = build_registered_app(tmp_path)
    paths = app.openapi()["paths"]

    assert (
        "/api/v1/governance-paid-assessments/"
        "{tenant_id}/{client_id}/{engagement_id}/{assessment_id}/"
        "delivery-readiness"
    ) in paths

    assert (
        "/api/v1/governance-paid-assessments/"
        "{tenant_id}/{client_id}/{engagement_id}/{assessment_id}/"
        "delivery-approval"
    ) in paths

    assert (
        "/api/v1/governance-paid-assessments/"
        "{tenant_id}/{client_id}/{engagement_id}/{assessment_id}/"
        "delivery-recording"
    ) in paths


def test_registration_exposes_delivery_services_on_app_state(
    tmp_path,
) -> None:
    app = build_registered_app(tmp_path)

    assert (
        app.state
        .governance_commercial_paid_assessment_delivery_readiness_service
        is not None
    )
    assert (
        app.state
        .governance_commercial_paid_assessment_delivery_approval_service
        is not None
    )
    assert (
        app.state
        .governance_commercial_paid_assessment_delivery_recording_service
        is not None
    )


def test_registered_readiness_reuses_paid_execution_service(
    tmp_path,
) -> None:
    app = build_registered_app(tmp_path)

    paid_execution_service = (
        app.state
        .governance_commercial_paid_assessment_service
    )

    readiness_service = (
        app.state
        .governance_commercial_paid_assessment_delivery_readiness_service
    )

    assert (
        readiness_service.execution_service
        is paid_execution_service
    )


def test_registered_delivery_readiness_requires_authentication(
    tmp_path,
) -> None:
    app = build_registered_app(tmp_path)
    client = TestClient(app)

    response = client.get(
        BASE + "/delivery-readiness"
    )

    assert response.status_code == 401


def test_registered_delivery_approval_requires_authentication(
    tmp_path,
) -> None:
    app = build_registered_app(tmp_path)
    client = TestClient(app)

    response = client.post(
        BASE + "/delivery-approval",
        json=approval_payload(),
    )

    assert response.status_code == 401


def test_registered_delivery_recording_requires_authentication(
    tmp_path,
) -> None:
    app = build_registered_app(tmp_path)
    client = TestClient(app)

    response = client.post(
        BASE + "/delivery-recording",
        json=confirmation_payload(),
    )

    assert response.status_code == 401


def test_authenticated_readiness_reaches_governed_service_layer(
    tmp_path,
) -> None:
    app = build_registered_app(tmp_path)
    client = TestClient(app)

    response = client.get(
        BASE + "/delivery-readiness",
        headers=actor_headers(),
    )

    # No PA015 operator-result snapshot exists in this fresh test
    # repository. A 404 therefore proves authentication succeeded and
    # the registered route delegated into the governed readiness service.
    assert response.status_code == 404
    assert "snapshot" in response.json()["detail"].lower()
