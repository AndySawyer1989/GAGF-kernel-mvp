from backend.app.main import app


def test_main_application_registers_assessment_router():
    paths = {route.path for route in app.routes}

    assert "/api/v1/governance-assessments/execute" in paths
    assert (
        "/api/v1/governance-assessments/"
        "{tenant_id}/{client_id}/{engagement_id}/"
        "{assessment_id}"
    ) in paths


def test_main_application_exposes_assessment_service():
    assert app.state.governance_assessment_service is not None
    assert app.state.governance_assessment_repository is not None


def test_main_application_registration_flag_is_set():
    assert (
        app.state.governance_assessment_api_registered
        is True
    )
