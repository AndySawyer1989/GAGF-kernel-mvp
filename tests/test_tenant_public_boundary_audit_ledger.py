import json
import sqlite3
from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.tenant_public_boundary_audit_ledger import (
    TENANT_PUBLIC_BOUNDARY_AUDIT_GENESIS_HASH,
    TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_ID,
    TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_VERSION,
    TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_SCHEMA_VERSION,
    TenantPublicBoundaryAuditIntegrityError,
    TenantPublicBoundaryAuditLedger,
)
from backend.app.gagf.tenant_public_boundary_auditor import (
    TenantPublicBoundaryAuditor,
)


def safe_audit():
    return TenantPublicBoundaryAuditor().audit(
        response={
            "tenant_id": "tenant-alpha",
            "public_artifact_id": "a" * 64,
            "view_hash": "b" * 64,
        }
    )


def rejected_audit():
    return TenantPublicBoundaryAuditor().audit(
        response={
            "credential_id": "credential-secret",
        }
    )


def test_ledger_has_stable_identity():
    assert TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_ID == (
        "tenant-public-boundary-audit-ledger"
    )
    assert TENANT_PUBLIC_BOUNDARY_AUDIT_LEDGER_VERSION == (
        "0.1.0"
    )
    assert (
        TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_SCHEMA_VERSION
        == "1.0.0"
    )
    assert TENANT_PUBLIC_BOUNDARY_AUDIT_GENESIS_HASH == (
        "0" * 64
    )


def test_first_record_uses_genesis_hash(tmp_path):
    ledger = TenantPublicBoundaryAuditLedger(
        tmp_path / "boundary-audit.db"
    )

    record = ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )

    assert record.sequence_number == 1
    assert record.previous_record_hash == (
        TENANT_PUBLIC_BOUNDARY_AUDIT_GENESIS_HASH
    )
    assert record.verify() is True


def test_records_form_hash_chain(tmp_path):
    ledger = TenantPublicBoundaryAuditLedger(
        tmp_path / "boundary-audit.db"
    )

    first = ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )
    second = ledger.append(
        tenant_id="tenant-alpha",
        response_kind="checkpoint-read",
        released=True,
        audit=safe_audit(),
    )

    assert second.sequence_number == 2
    assert second.previous_record_hash == (
        first.record_hash
    )
    assert ledger.verify_chain().valid is True


def test_rejected_response_can_be_recorded(tmp_path):
    ledger = TenantPublicBoundaryAuditLedger(
        tmp_path / "boundary-audit.db"
    )

    record = ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=False,
        audit=rejected_audit(),
    )

    assert record.released is False
    assert record.audit_valid is False
    assert record.violation_count == 1
    assert record.verify() is True


def test_invalid_audit_cannot_be_recorded_as_released(
    tmp_path,
):
    ledger = TenantPublicBoundaryAuditLedger(
        tmp_path / "boundary-audit.db"
    )

    with pytest.raises(
        TenantPublicBoundaryAuditIntegrityError,
        match="cannot be recorded as released",
    ):
        ledger.append(
            tenant_id="tenant-alpha",
            response_kind="evaluation",
            released=True,
            audit=rejected_audit(),
        )


def test_tampered_audit_is_rejected(tmp_path):
    ledger = TenantPublicBoundaryAuditLedger(
        tmp_path / "boundary-audit.db"
    )

    audit = safe_audit()
    tampered = replace(
        audit,
        valid=False,
    )

    with pytest.raises(
        TenantPublicBoundaryAuditIntegrityError,
        match="verification failed",
    ):
        ledger.append(
            tenant_id="tenant-alpha",
            response_kind="evaluation",
            released=False,
            audit=tampered,
        )


def test_records_can_be_retrieved(tmp_path):
    ledger = TenantPublicBoundaryAuditLedger(
        tmp_path / "boundary-audit.db"
    )

    created = ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )

    retrieved = ledger.get(1)

    assert retrieved == created
    assert ledger.get(999) is None


def test_records_can_be_filtered_by_tenant(tmp_path):
    ledger = TenantPublicBoundaryAuditLedger(
        tmp_path / "boundary-audit.db"
    )

    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )
    ledger.append(
        tenant_id="tenant-beta",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )

    alpha_records = ledger.list_records(
        tenant_id="tenant-alpha"
    )

    assert len(alpha_records) == 1
    assert alpha_records[0].tenant_id == (
        "tenant-alpha"
    )


def test_chain_verification_detects_tampering(tmp_path):
    database_path = tmp_path / "boundary-audit.db"
    ledger = TenantPublicBoundaryAuditLedger(
        database_path
    )

    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT record_json
            FROM tenant_public_boundary_audit_records
            WHERE sequence_number = 1
            """
        ).fetchone()

        payload = json.loads(row[0])
        payload["tenant_id"] = "tenant-beta"

        connection.execute(
            """
            UPDATE tenant_public_boundary_audit_records
            SET record_json = ?
            WHERE sequence_number = 1
            """,
            (json.dumps(payload),),
        )
        connection.commit()

    verification = ledger.verify_chain()

    assert verification.valid is False
    assert verification.failure_sequence_number == 1


def test_empty_ledger_verifies(tmp_path):
    ledger = TenantPublicBoundaryAuditLedger(
        tmp_path / "boundary-audit.db"
    )

    verification = ledger.verify_chain()

    assert verification.valid is True
    assert verification.record_count == 0
    assert verification.last_sequence_number == 0
    assert verification.last_record_hash == (
        TENANT_PUBLIC_BOUNDARY_AUDIT_GENESIS_HASH
    )


def test_record_is_immutable(tmp_path):
    ledger = TenantPublicBoundaryAuditLedger(
        tmp_path / "boundary-audit.db"
    )

    record = ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
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
def test_empty_identity_fields_are_rejected(
    tmp_path,
    tenant_id,
    response_kind,
):
    ledger = TenantPublicBoundaryAuditLedger(
        tmp_path / "boundary-audit.db"
    )

    with pytest.raises(ValueError):
        ledger.append(
            tenant_id=tenant_id,
            response_kind=response_kind,
            released=True,
            audit=safe_audit(),
        )
