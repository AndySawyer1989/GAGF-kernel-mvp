from dataclasses import FrozenInstanceError

import pytest

from backend.app.gagf.tenant_public_response_gate import (
    TenantPublicResponseRejectedError,
)
from backend.app.gagf.tenant_recorded_public_response_gate import (
    TENANT_RECORDED_PUBLIC_RESPONSE_GATE_ID,
    TENANT_RECORDED_PUBLIC_RESPONSE_GATE_VERSION,
    TenantRecordedPublicResponseGate,
)


def safe_response():
    return {
        "api_id": "tenant-api",
        "api_version": "1.0.0",
        "tenant_id": "tenant-alpha",
        "execution": {
            "view_id": (
                "tenant-public-scientific-execution-view"
            ),
            "public_artifact_id": "a" * 64,
            "view_hash": "b" * 64,
        },
    }


def test_recorded_gate_has_stable_identity():
    assert TENANT_RECORDED_PUBLIC_RESPONSE_GATE_ID == (
        "tenant-recorded-public-response-boundary-gate"
    )
    assert (
        TENANT_RECORDED_PUBLIC_RESPONSE_GATE_VERSION
        == "0.1.0"
    )


def test_safe_response_is_released_and_recorded(
    tmp_path,
):
    gate = TenantRecordedPublicResponseGate(
        database_path=tmp_path / "boundary-audit.db"
    )

    result = gate.release(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        response=safe_response(),
    )

    assert result["api_id"] == "tenant-api"
    assert result["boundary_audit"]["valid"] is True

    record = result["boundary_audit_record"]

    assert record["tenant_id"] == "tenant-alpha"
    assert record["response_kind"] == "evaluation"
    assert record["released"] is True
    assert record["audit_valid"] is True
    assert record["violation_count"] == 0
    assert record["sequence_number"] == 1


def test_released_record_references_boundary_audit(
    tmp_path,
):
    gate = TenantRecordedPublicResponseGate(
        database_path=tmp_path / "boundary-audit.db"
    )

    result = gate.release(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        response=safe_response(),
    )

    assert (
        result["boundary_audit_record"][
            "boundary_audit_hash"
        ]
        == result["boundary_audit"]["audit_hash"]
    )


def test_multiple_releases_form_ledger_chain(
    tmp_path,
):
    gate = TenantRecordedPublicResponseGate(
        database_path=tmp_path / "boundary-audit.db"
    )

    first = gate.release(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        response=safe_response(),
    )
    second = gate.release(
        tenant_id="tenant-alpha",
        response_kind="checkpoint-read",
        response=safe_response(),
    )

    assert (
        first["boundary_audit_record"][
            "sequence_number"
        ]
        == 1
    )
    assert (
        second["boundary_audit_record"][
            "sequence_number"
        ]
        == 2
    )
    assert (
        second["boundary_audit_record"][
            "previous_record_hash"
        ]
        == first["boundary_audit_record"][
            "record_hash"
        ]
    )

    verification = gate.verify_ledger()

    assert verification.valid is True
    assert verification.record_count == 2


def test_blocked_response_is_recorded(
    tmp_path,
):
    gate = TenantRecordedPublicResponseGate(
        database_path=tmp_path / "boundary-audit.db"
    )

    unsafe_response = {
        "credential_id": "credential-secret",
    }

    with pytest.raises(
        TenantPublicResponseRejectedError
    ):
        gate.release(
            tenant_id="tenant-alpha",
            response_kind="evaluation",
            response=unsafe_response,
        )

    records = gate.audit_ledger.list_records()

    assert len(records) == 1

    record = records[0]

    assert record.tenant_id == "tenant-alpha"
    assert record.response_kind == "evaluation"
    assert record.released is False
    assert record.audit_valid is False
    assert record.violation_count == 1


def test_blocked_response_does_not_store_secret(
    tmp_path,
):
    gate = TenantRecordedPublicResponseGate(
        database_path=tmp_path / "boundary-audit.db"
    )

    with pytest.raises(
        TenantPublicResponseRejectedError
    ):
        gate.release(
            tenant_id="tenant-alpha",
            response_kind="evaluation",
            response={
                "credential_id": (
                    "credential-super-secret"
                ),
            },
        )

    serialized = str(
        gate.audit_ledger.list_records()[0].to_dict()
    )

    assert "credential-super-secret" not in serialized


def test_error_detail_is_released_and_recorded(
    tmp_path,
):
    gate = TenantRecordedPublicResponseGate(
        database_path=tmp_path / "boundary-audit.db"
    )

    result = gate.release_error_detail(
        tenant_id="tenant-alpha",
        response_kind="authorization-denial",
        detail={
            "message": "Request denied.",
            "view_id": (
                "tenant-public-scientific-authorization-view"
            ),
            "decision": {
                "allowed": False,
                "reasons": [
                    "Role not permitted.",
                ],
            },
            "view_hash": "a" * 64,
        },
    )

    assert result["message"] == "Request denied."
    assert result["boundary_audit"]["valid"] is True
    assert (
        result["boundary_audit_record"][
            "response_kind"
        ]
        == "authorization-denial"
    )
    assert (
        result["boundary_audit_record"]["released"]
        is True
    )


def test_ledger_record_can_be_omitted_from_response(
    tmp_path,
):
    gate = TenantRecordedPublicResponseGate(
        database_path=tmp_path / "boundary-audit.db"
    )

    result = gate.release(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        response=safe_response(),
        include_ledger_record=False,
    )

    assert "boundary_audit_record" not in result
    assert len(gate.audit_ledger.list_records()) == 1


def test_boundary_audit_can_be_omitted_but_recorded(
    tmp_path,
):
    gate = TenantRecordedPublicResponseGate(
        database_path=tmp_path / "boundary-audit.db"
    )

    result = gate.release(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        response=safe_response(),
        include_boundary_audit=False,
    )

    assert "boundary_audit" not in result
    assert (
        result["boundary_audit_record"][
            "audit_valid"
        ]
        is True
    )


def test_cross_tenant_records_remain_distinct(
    tmp_path,
):
    gate = TenantRecordedPublicResponseGate(
        database_path=tmp_path / "boundary-audit.db"
    )

    gate.release(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        response=safe_response(),
    )
    gate.release(
        tenant_id="tenant-beta",
        response_kind="evaluation",
        response={
            **safe_response(),
            "tenant_id": "tenant-beta",
        },
    )

    alpha = gate.audit_ledger.list_records(
        tenant_id="tenant-alpha"
    )
    beta = gate.audit_ledger.list_records(
        tenant_id="tenant-beta"
    )

    assert len(alpha) == 1
    assert len(beta) == 1
    assert alpha[0].tenant_id != beta[0].tenant_id


def test_recorded_response_is_immutable(
    tmp_path,
):
    gate = TenantRecordedPublicResponseGate(
        database_path=tmp_path / "boundary-audit.db"
    )

    envelope = gate.release(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        response=safe_response(),
    )

    record = gate.audit_ledger.get(
        envelope["boundary_audit_record"][
            "sequence_number"
        ]
    )

    with pytest.raises(FrozenInstanceError):
        record.tenant_id = "tenant-beta"


@pytest.mark.parametrize(
    ("tenant_id", "response_kind"),
    [
        ("", "evaluation"),
        ("   ", "evaluation"),
        ("tenant-alpha", ""),
        ("tenant-alpha", "   "),
    ],
)
def test_empty_record_identity_is_rejected(
    tmp_path,
    tenant_id,
    response_kind,
):
    gate = TenantRecordedPublicResponseGate(
        database_path=tmp_path / "boundary-audit.db"
    )

    with pytest.raises(ValueError):
        gate.release(
            tenant_id=tenant_id,
            response_kind=response_kind,
            response=safe_response(),
        )
