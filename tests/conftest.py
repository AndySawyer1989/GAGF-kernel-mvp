import pytest

from backend.app.gagf.governance_assessment_auth import AssessmentActorContext


@pytest.fixture
def legacy_api_test_identity(monkeypatch):
    """Test-only identity for explicitly opted-in legacy API tests."""
    from backend.app.main import app

    async def verify_test_identity(request):
        return AssessmentActorContext(
            tenant_id="tenant-api-regression",
            actor_id="legacy-api-test-actor",
            roles=("assessment:read", "assessment:execute"),
        )

    monkeypatch.setattr(
        app.state,
        "assessment_identity_verifier",
        verify_test_identity,
        raising=False,
    )
