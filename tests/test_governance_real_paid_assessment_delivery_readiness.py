from copy import deepcopy

import pytest

from scripts.run_real_paid_assessment import main as run_operator_main
from tests.test_run_real_paid_assessment import (
    build_operator_files,
)
from backend.app.gagf.governance_real_paid_assessment_delivery_readiness import (
    GovernanceRealPaidAssessmentDeliveryReadinessService,
    RealPaidAssessmentDeliveryReadinessError,
    READY_FOR_DELIVERY_APPROVAL_REVIEW,
)


SERVICE = GovernanceRealPaidAssessmentDeliveryReadinessService()


def run_real_operator(tmp_path, monkeypatch, capsys):
    files = build_operator_files(tmp_path)

    output_path = tmp_path / "operator-result.json"

    argv = [
        "run_real_paid_assessment",
        "--database",
        str(files["database"]),
        "--intake-json",
        str(files["intake"]),
        "--authorization-json",
        str(files["authorization"]),
        "--contract-event-json",
        str(files["contract_event"]),
        "--request-json",
        str(files["request"]),
        "--evidence-approvals-json",
        str(files["approvals"]),
        "--output-json",
        str(output_path),
    ]

    monkeypatch.setattr(
        "sys.argv",
        argv,
    )

    exit_code = run_operator_main()

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert output_path.exists()

    import json

    payload = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    return files, payload


def test_rehydrates_completed_execution_and_persisted_report(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, payload = run_real_operator(
        tmp_path,
        monkeypatch,
        capsys,
    )

    result = SERVICE.verify(
        database_path=files["database"],
        operator_payload=payload,
    )

    assert result.delivery_readiness_status == (
        READY_FOR_DELIVERY_APPROVAL_REVIEW
    )
    assert result.repository_chain_valid is True
    assert result.artifact_count == 10

    assert (
        result.execution_result.hierarchy_key
        == payload["result"]["execution_result"]["hierarchy_key"]
    )

    assert (
        result.execution_result.report_id
        == payload["result"]["execution_result"]["report_id"]
    )

    assert (
        result.report_package.report_id
        == result.execution_result.report_id
    )

    assert (
        result.report_package.hierarchy_key
        == result.execution_result.hierarchy_key
    )

    assert (
        result.report_package.manifest.package_hash
        == payload["result"]["execution_result"]["report_package_hash"]
    )

    serialized = result.to_dict()

    assert serialized[
        "ready_for_delivery_approval_review"
    ] is True

    assert serialized["boundaries"][
        "delivery_readiness_is_not_delivery_approval"
    ] is True

    assert serialized["boundaries"][
        "delivery_readiness_is_not_approved_for_human_delivery"
    ] is True

    assert serialized["boundaries"][
        "pa003_remains_delivery_envelope_authority"
    ] is True


def test_readiness_does_not_mutate_repository(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, payload = run_real_operator(
        tmp_path,
        monkeypatch,
        capsys,
    )

    database_bytes_before = files["database"].read_bytes()

    SERVICE.verify(
        database_path=files["database"],
        operator_payload=payload,
    )

    database_bytes_after = files["database"].read_bytes()

    assert database_bytes_after == database_bytes_before


def test_operator_failure_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, payload = run_real_operator(
        tmp_path,
        monkeypatch,
        capsys,
    )

    tampered = deepcopy(payload)
    tampered["operator_run_passed"] = False

    with pytest.raises(
        RealPaidAssessmentDeliveryReadinessError,
        match="operator result is not successful",
    ):
        SERVICE.verify(
            database_path=files["database"],
            operator_payload=tampered,
        )


def test_recovery_hierarchy_mismatch_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, payload = run_real_operator(
        tmp_path,
        monkeypatch,
        capsys,
    )

    tampered = deepcopy(payload)
    tampered["result"]["hierarchy_key"] = (
        "tenant-x/client-x/engagement-x/assessment-x"
    )

    with pytest.raises(
        RealPaidAssessmentDeliveryReadinessError,
        match="recovery hierarchy does not match execution result",
    ):
        SERVICE.verify(
            database_path=files["database"],
            operator_payload=tampered,
        )


def test_report_package_hash_mismatch_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, payload = run_real_operator(
        tmp_path,
        monkeypatch,
        capsys,
    )

    tampered = deepcopy(payload)

    tampered["result"]["execution_result"][
        "report_package_hash"
    ] = "a" * 64

    with pytest.raises(
        RealPaidAssessmentDeliveryReadinessError,
        match="persisted report package hash does not match execution",
    ):
        SERVICE.verify(
            database_path=files["database"],
            operator_payload=tampered,
        )


def test_demonstration_hash_mismatch_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, payload = run_real_operator(
        tmp_path,
        monkeypatch,
        capsys,
    )

    tampered = deepcopy(payload)

    tampered["result"]["execution_result"][
        "demonstration_hash"
    ] = "b" * 64

    with pytest.raises(
        RealPaidAssessmentDeliveryReadinessError,
        match="demonstration hash does not match persisted manifest",
    ):
        SERVICE.verify(
            database_path=files["database"],
            operator_payload=tampered,
        )


def test_execution_artifact_count_mismatch_is_rejected(
    tmp_path,
    monkeypatch,
    capsys,
):
    files, payload = run_real_operator(
        tmp_path,
        monkeypatch,
        capsys,
    )

    tampered = deepcopy(payload)

    tampered["result"]["execution_result"][
        "artifact_count"
    ] = 9

    with pytest.raises(
        RealPaidAssessmentDeliveryReadinessError,
        match="serialized execution artifact_count is invalid",
    ):
        SERVICE.verify(
            database_path=files["database"],
            operator_payload=tampered,
        )


def test_missing_database_is_rejected(
    tmp_path,
):
    missing = tmp_path / "missing.sqlite"

    with pytest.raises(
        RealPaidAssessmentDeliveryReadinessError,
        match="assessment database does not exist",
    ):
        SERVICE.verify(
            database_path=missing,
            operator_payload={
                "operator_run_passed": True,
            },
        )