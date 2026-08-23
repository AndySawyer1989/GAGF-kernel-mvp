import json

import pytest

from backend.app.gagf.governance_assessment_isolation import (
    CommercialHierarchyContext,
)
from backend.app.gagf.governance_assessment_repository import (
    GovernanceAssessmentRepository,
)
from backend.app.gagf.governance_paid_assessment_closeout import (
    PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_paid_assessment_lifecycle_persistence import (
    CLIENT_RESPONSE_ARTIFACT_TYPE,
)
from backend.app.gagf.governance_real_paid_assessment_closeout import (
    GovernanceRealPaidAssessmentCloseoutService,
    RealPaidAssessmentCloseoutError,
)
from tests.test_record_real_paid_assessment_client_response import (
    build_cli_inputs as build_response_cli_inputs,
    run_cli as run_response_cli,
)


SERVICE = GovernanceRealPaidAssessmentCloseoutService()


def build_client_response_result(
    tmp_path,
    monkeypatch,
    capsys,
):
    inputs = build_response_cli_inputs(
        tmp_path,
        monkeypatch,
        capsys,
    )

    output = tmp_path / "client-response-recorded.json"

    exit_code = run_response_cli(
        database=inputs["files"]["database"],
        acknowledged=inputs["acknowledged_path"],
        response=inputs["response_path"],
        output=output,
        monkeypatch=monkeypatch,
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert output.exists()

    payload = json.loads(
        output.read_text(
            encoding="utf-8"
        )
    )

    assert payload["client_response_recording_passed"] is True
    assert payload["client_response_recorded"] is True

    return inputs["files"], payload


def build_closeout_payload(
    client_response_payload,
):
    result = client_response_payload["result"]["client_response"]

    return {
        "tenant_id": result["tenant_id"],
        "client_id": result["client_id"],
        "engagement_id": result["engagement_id"],
        "assessment_id": result["assessment_id"],
        "report_id": result["report_id"],
        "closed_by": "Assessment Operator",
        "closeout_reason": (
            "Client response was recorded and administrative "
            "assessment processing is complete."
        ),
        "administrative_closeout_confirmed": True,
    }


def build_context(
    client_response_payload,
):
    result = client_response_payload["result"]["client_response"]

    return CommercialHierarchyContext(
        tenant_id=result["tenant_id"],
        client_id=result["client_id"],
        engagement_id=result["engagement_id"],
        assessment_id=result["assessment_id"],
    )


def test_real_client_response_records_exactly_one_administrative_closeout(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, client_response_payload = build_client_response_result(
        tmp_path,
        monkeypatch,
        capsys,
    )

    closeout_payload = build_closeout_payload(
        client_response_payload
    )

    context = build_context(
        client_response_payload
    )

    repository = GovernanceAssessmentRepository(
        files["database"]
    )

    client_responses = repository.list_artifacts(
        context=context,
        artifact_type=CLIENT_RESPONSE_ARTIFACT_TYPE,
    )

    before = repository.list_artifacts(
        context=context,
        artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    )

    assert len(client_responses) == 1
    assert len(before) == 0

    result = SERVICE.record(
        database_path=files["database"],
        client_response_payload=client_response_payload,
        closeout_payload=closeout_payload,
    )

    assert result.closeout_status == "assessment_closed"

    after = repository.list_artifacts(
        context=context,
        artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    )

    assert len(after) == 1

    assert (
        result.client_response_artifact_id
        == client_responses[0].artifact_id
    )

    assert (
        result.client_response_artifact_hash
        == client_responses[0].artifact_hash
    )

    assert (
        result.closeout_artifact_id
        == after[0].artifact_id
    )

    assert (
        result.closeout_artifact_hash
        == after[0].artifact_hash
    )

    assert (
        after[0].payload["closeout_status"]
        == "assessment_closed"
    )

    assert (
        after[0].payload["client_response_artifact_id"]
        == client_responses[0].artifact_id
    )

    assert (
        after[0].payload["client_response_artifact_hash"]
        == client_responses[0].artifact_hash
    )

    assert repository.verify_chain(
        context=context
    ) is True

    payload = result.to_dict()

    assert payload["administrative_closeout_recorded"] is True

    assert payload["boundaries"][
        "pa010_remains_closeout_authority"
    ] is True

    assert payload["boundaries"][
        "closeout_is_not_intervention_authorization"
    ] is True


def test_exact_closeout_retry_does_not_duplicate_artifact(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, client_response_payload = build_client_response_result(
        tmp_path,
        monkeypatch,
        capsys,
    )

    closeout_payload = build_closeout_payload(
        client_response_payload
    )

    context = build_context(
        client_response_payload
    )

    repository = GovernanceAssessmentRepository(
        files["database"]
    )

    first = SERVICE.record(
        database_path=files["database"],
        client_response_payload=client_response_payload,
        closeout_payload=closeout_payload,
    )

    after_first = repository.list_artifacts(
        context=context,
        artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    )

    assert len(after_first) == 1

    second = SERVICE.record(
        database_path=files["database"],
        client_response_payload=client_response_payload,
        closeout_payload=closeout_payload,
    )

    after_second = repository.list_artifacts(
        context=context,
        artifact_type=PAID_ASSESSMENT_CLOSEOUT_ARTIFACT_TYPE,
    )

    assert len(after_second) == 1

    assert (
        second.closeout_artifact_id
        == first.closeout_artifact_id
    )

    assert (
        second.closeout_artifact_hash
        == first.closeout_artifact_hash
    )

    assert repository.verify_chain(
        context=context
    ) is True


def test_closeout_hierarchy_mismatch_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, client_response_payload = build_client_response_result(
        tmp_path,
        monkeypatch,
        capsys,
    )

    closeout_payload = build_closeout_payload(
        client_response_payload
    )

    closeout_payload["assessment_id"] = "wrong-assessment"

    with pytest.raises(
        RealPaidAssessmentCloseoutError,
        match=(
            "assessment_id does not match PILOT-010 "
            "client-response lineage"
        ),
    ):
        SERVICE.record(
            database_path=files["database"],
            client_response_payload=client_response_payload,
            closeout_payload=closeout_payload,
        )


def test_closeout_report_mismatch_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, client_response_payload = build_client_response_result(
        tmp_path,
        monkeypatch,
        capsys,
    )

    closeout_payload = build_closeout_payload(
        client_response_payload
    )

    closeout_payload["report_id"] = "wrong-report"

    with pytest.raises(
        RealPaidAssessmentCloseoutError,
        match=(
            "report_id does not match PILOT-010 "
            "client-response lineage"
        ),
    ):
        SERVICE.record(
            database_path=files["database"],
            client_response_payload=client_response_payload,
            closeout_payload=closeout_payload,
        )


def test_tampered_pilot010_response_hash_is_rejected_against_repository(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, client_response_payload = build_client_response_result(
        tmp_path,
        monkeypatch,
        capsys,
    )

    client_response_payload["result"]["client_response"][
        "response_hash"
    ] = "0" * 64

    closeout_payload = build_closeout_payload(
        client_response_payload
    )

    with pytest.raises(
        RealPaidAssessmentCloseoutError,
        match=(
            "serialized PILOT-010 response_hash does not match "
            "durable client-response artifact"
        ),
    ):
        SERVICE.record(
            database_path=files["database"],
            client_response_payload=client_response_payload,
            closeout_payload=closeout_payload,
        )


def test_unsuccessful_pilot010_wrapper_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, client_response_payload = build_client_response_result(
        tmp_path,
        monkeypatch,
        capsys,
    )

    client_response_payload[
        "client_response_recording_passed"
    ] = False

    closeout_payload = build_closeout_payload(
        client_response_payload
    )

    with pytest.raises(
        RealPaidAssessmentCloseoutError,
        match=(
            "PILOT-010 client response recording "
            "is not successful"
        ),
    ):
        SERVICE.record(
            database_path=files["database"],
            client_response_payload=client_response_payload,
            closeout_payload=closeout_payload,
        )


def test_closeout_requires_explicit_administrative_confirmation(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, client_response_payload = build_client_response_result(
        tmp_path,
        monkeypatch,
        capsys,
    )

    closeout_payload = build_closeout_payload(
        client_response_payload
    )

    closeout_payload[
        "administrative_closeout_confirmed"
    ] = False

    with pytest.raises(
        RealPaidAssessmentCloseoutError,
        match="administrative_closeout_confirmed must be true",
    ):
        SERVICE.record(
            database_path=files["database"],
            client_response_payload=client_response_payload,
            closeout_payload=closeout_payload,
        )


def test_closeout_does_not_create_intervention_or_outcome_authority(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, client_response_payload = build_client_response_result(
        tmp_path,
        monkeypatch,
        capsys,
    )

    closeout_payload = build_closeout_payload(
        client_response_payload
    )

    result = SERVICE.record(
        database_path=files["database"],
        client_response_payload=client_response_payload,
        closeout_payload=closeout_payload,
    )

    payload = result.to_dict()

    serialized = json.dumps(
        payload
    )

    assert '"intervention_authorized"' not in serialized
    assert '"intervention_executed"' not in serialized
    assert '"recommendation_implemented"' not in serialized
    assert '"remediation_success"' not in serialized
    assert '"roi_verified"' not in serialized
    assert '"customer_outcome_verified"' not in serialized

    boundaries = payload["boundaries"]

    assert boundaries[
        "closeout_is_not_recommendation_implementation"
    ] is True

    assert boundaries[
        "closeout_is_not_intervention_request"
    ] is True

    assert boundaries[
        "closeout_is_not_intervention_authorization"
    ] is True

    assert boundaries[
        "closeout_is_not_execution"
    ] is True

    assert boundaries[
        "closeout_is_not_causation"
    ] is True

    assert boundaries[
        "closeout_is_not_roi_verification"
    ] is True

    assert boundaries[
        "closeout_is_not_remediation_success"
    ] is True

    assert boundaries[
        "closeout_is_not_customer_outcome"
    ] is True