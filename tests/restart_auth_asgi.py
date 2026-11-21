"""Test-only authenticated ASGI entry point for restart-persistence probes."""

import hmac
import os

from fastapi import HTTPException

from backend.app.main import app
from backend.app.gagf.governance_assessment_auth import AssessmentActorContext


TOKEN_ENV = "GAGF_TEST_RESTART_BEARER_TOKEN"
TENANT_ENV = "GAGF_TEST_RESTART_TENANT_ID"

expected_token = os.environ.get(TOKEN_ENV, "")
expected_tenant = os.environ.get(TENANT_ENV, "")

if not expected_token or not expected_tenant:
    raise RuntimeError(
        "Restart test authentication requires explicit test credentials"
    )


async def verify_restart_test_identity(request):
    authorization = request.headers.get("authorization", "")

    expected_authorization = f"Bearer {expected_token}"

    if not hmac.compare_digest(
        authorization.encode("utf-8"),
        expected_authorization.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=401,
            detail="restart_test_credentials_required",
        )

    return AssessmentActorContext(
        tenant_id=expected_tenant,
        actor_id="release-restart-test-actor",
        roles=("assessment:admin",),
    )


app.state.assessment_identity_verifier = verify_restart_test_identity
