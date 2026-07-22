from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.gagf.scientific_calculation_contract import (
    LEGACY_METRIC_CONFIDENCE_CONTRACT,
)

from backend.app.gagf.scientific_authority_api import (
    SCIENTIFIC_AUTHORITY_API_ID,
    SCIENTIFIC_AUTHORITY_API_VERSION,
    ScientificAuthorityApiPaths,
    create_scientific_authority_router,
)
from backend.app.gagf.scientific_calculation_contract import (
    LEGACY_METRIC_CONFIDENCE_CONTRACT,
)


def build_client(tmp_path) -> TestClient:
    app = FastAPI()

    app.include_router(
        create_scientific_authority_router(
            paths=ScientificAuthorityApiPaths(
                authority_database_path=(
                    tmp_path / "authority.db"
                ),
                audit_database_path=(
                    tmp_path / "audit.db"
                ),
                checkpoint_database_path=(
                    tmp_path / "checkpoint.db"
                ),
                journal_database_path=(
                    tmp_path / "journal.db"
                ),
            )
        )
    )

    return TestClient(app)


def complete_evidence_payload() -> dict:
    return {
        "deterministic_replay_verified": True,
        "canonical_input_binding_verified": True,
        "calculation_version_frozen": True,
        "regression_suite_passed": True,
        "validation_report_present": True,
        "constitutional_approval_present": True,
    }


def incomplete_evidence_payload() -> dict:
    return {
        "deterministic_replay_verified": False,
        "canonical_input_binding_verified": False,
        "calculation_version_frozen": False,
        "regression_suite_passed": False,
        "validation_report_present": False,
        "constitutional_approval_present": False,
    }


def evaluation_payload(
    *,
    calculation_id="evidence-confidence",
    requested_authority="ADVISORY",
    evidence=None,
) -> dict:
    if evidence is None:
        evidence = complete_evidence_payload()

    return {
        "calculation_id": calculation_id,
        "requested_authority": requested_authority,
        "evidence": evidence,
    }


def test_api_has_stable_identity():
    assert SCIENTIFIC_AUTHORITY_API_ID == (
        "scientific-authority-api"
    )
    assert SCIENTIFIC_AUTHORITY_API_VERSION == "0.1.0"


def test_contracts_endpoint_lists_registry_contracts(tmp_path):
    client = build_client(tmp_path)

    response = client.get(
        "/scientific-authority/contracts"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["api_id"] == "scientific-authority-api"
    assert body["api_version"] == "0.1.0"
    assert len(body["contracts"]) >= 3
    assert any(
        contract["calculation_id"]
        == "evidence-confidence"
        for contract in body["contracts"]
    )


def test_allowed_evaluation_returns_complete_cycle(tmp_path):
    client = build_client(tmp_path)

    response = client.post(
        "/scientific-authority/evaluate",
        json=evaluation_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["pipeline_result"]["decision_allowed"] is True
    assert body["pipeline_result"]["checkpoint_valid"] is True
    assert body["execution_receipt"]["decision_allowed"] is True
    assert len(
        body["execution_receipt"]["receipt_hash"]
    ) == 64
    assert body["resumed"] is False


def test_denied_evaluation_is_still_persisted(tmp_path):
    client = build_client(tmp_path)

    response = client.post(
        "/scientific-authority/evaluate",
        json=evaluation_payload(
            calculation_id=(
                LEGACY_METRIC_CONFIDENCE_CONTRACT.calculation_id
            ),
        ),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["pipeline_result"]["decision_allowed"] is False
    assert body["pipeline_result"]["checkpoint_valid"] is True
    assert body["execution_receipt"]["decision_allowed"] is False
    assert len(body["execution_receipt"]["receipt_hash"]) == 64

def test_incomplete_evidence_produces_denial(tmp_path):
    client = build_client(tmp_path)

    response = client.post(
        "/scientific-authority/evaluate",
        json=evaluation_payload(
            evidence=incomplete_evidence_payload(),
        ),
    )

    assert response.status_code == 200
    assert (
        response.json()["pipeline_result"]["decision_allowed"]
        is False
    )


def test_unknown_contract_returns_404(tmp_path):
    client = build_client(tmp_path)

    response = client.post(
        "/scientific-authority/evaluate",
        json=evaluation_payload(
            calculation_id="unknown-calculation",
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Scientific calculation contract was not found."
    )


def test_invalid_authority_returns_422(tmp_path):
    client = build_client(tmp_path)

    response = client.post(
        "/scientific-authority/evaluate",
        json=evaluation_payload(
            requested_authority="NOT_A_REAL_AUTHORITY",
        ),
    )

    assert response.status_code == 422


def test_identical_evaluation_resumes_existing_cycle(tmp_path):
    client = build_client(tmp_path)
    payload = evaluation_payload()

    first = client.post(
        "/scientific-authority/evaluate",
        json=payload,
    )
    second = client.post(
        "/scientific-authority/evaluate",
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 200

    first_body = first.json()
    second_body = second.json()

    assert first_body["execution_id"] == (
        second_body["execution_id"]
    )
    assert first_body["resumed"] is False
    assert second_body["resumed"] is True
    assert (
        first_body["execution_receipt"]["receipt_hash"]
        == second_body["execution_receipt"]["receipt_hash"]
    )


def test_authority_receipt_can_be_retrieved(tmp_path):
    client = build_client(tmp_path)

    evaluation = client.post(
        "/scientific-authority/evaluate",
        json=evaluation_payload(),
    ).json()

    receipt_hash = (
        evaluation["pipeline_result"]
        ["authority_receipt_hash"]
    )

    response = client.get(
        f"/scientific-authority/receipts/{receipt_hash}"
    )

    assert response.status_code == 200
    assert (
        response.json()["receipt"]["receipt_hash"]
        == receipt_hash
    )
    assert response.json()["sequence_number"] == 1


def test_unknown_authority_receipt_returns_404(tmp_path):
    client = build_client(tmp_path)

    response = client.get(
        "/scientific-authority/receipts/"
        + ("0" * 64)
    )

    assert response.status_code == 404


def test_checkpoint_can_be_retrieved(tmp_path):
    client = build_client(tmp_path)

    evaluation = client.post(
        "/scientific-authority/evaluate",
        json=evaluation_payload(),
    ).json()

    checkpoint_hash = (
        evaluation["pipeline_result"]["checkpoint_hash"]
    )

    response = client.get(
        "/scientific-authority/checkpoints/"
        + checkpoint_hash
    )

    assert response.status_code == 200
    assert (
        response.json()["checkpoint"]["checkpoint_hash"]
        == checkpoint_hash
    )


def test_checkpoint_can_be_replay_verified(tmp_path):
    client = build_client(tmp_path)

    evaluation = client.post(
        "/scientific-authority/evaluate",
        json=evaluation_payload(),
    ).json()

    checkpoint_hash = (
        evaluation["pipeline_result"]["checkpoint_hash"]
    )

    response = client.post(
        "/scientific-authority/checkpoints/"
        + checkpoint_hash
        + "/verify"
    )

    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["errors"] == []


def test_unknown_checkpoint_returns_404(tmp_path):
    client = build_client(tmp_path)

    response = client.get(
        "/scientific-authority/checkpoints/"
        + ("0" * 64)
    )

    assert response.status_code == 404


def test_unknown_checkpoint_verification_returns_404(
    tmp_path,
):
    client = build_client(tmp_path)

    response = client.post(
        "/scientific-authority/checkpoints/"
        + ("0" * 64)
        + "/verify"
    )

    assert response.status_code == 404


def test_execution_journal_can_be_retrieved(tmp_path):
    client = build_client(tmp_path)

    evaluation = client.post(
        "/scientific-authority/evaluate",
        json=evaluation_payload(),
    ).json()

    execution_id = evaluation["execution_id"]

    response = client.get(
        f"/scientific-authority/executions/{execution_id}"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["execution"]["execution_id"] == execution_id
    assert body["execution"]["state"] == "COMPLETED"
    assert len(body["transitions"]) == 5
    assert body["transitions"][0]["state"] == "STARTED"
    assert body["transitions"][-1]["state"] == "COMPLETED"


def test_unknown_execution_returns_404(tmp_path):
    client = build_client(tmp_path)

    response = client.get(
        "/scientific-authority/executions/"
        + ("0" * 64)
    )

    assert response.status_code == 404


