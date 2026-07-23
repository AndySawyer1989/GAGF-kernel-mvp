from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.tenant_boundary_audit_query import (
    TENANT_BOUNDARY_AUDIT_QUERY_SERVICE_ID,
    TENANT_BOUNDARY_AUDIT_QUERY_SERVICE_VERSION,
    TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_ID,
    TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_SCHEMA_VERSION,
    TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_VERSION,
    TenantBoundaryAuditEvidenceQueryService,
)
from backend.app.gagf.tenant_public_boundary_audit_ledger import (
    TenantPublicBoundaryAuditLedger,
)
from backend.app.gagf.tenant_public_boundary_auditor import (
    TenantPublicBoundaryAuditor,
)


def safe_audit(*, tenant_id="tenant-alpha"):
    return TenantPublicBoundaryAuditor().audit(
        response={
            "tenant_id": tenant_id,
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


def build_system(tmp_path):
    database_path = tmp_path / "boundary-audit.db"

    ledger = TenantPublicBoundaryAuditLedger(
        database_path
    )
    service = TenantBoundaryAuditEvidenceQueryService(
        database_path=database_path
    )

    return ledger, service


def collect_keys(value):
    keys = set()

    if isinstance(value, dict):
        keys.update(value.keys())

        for child in value.values():
            keys.update(collect_keys(child))

    elif isinstance(value, list):
        for child in value:
            keys.update(collect_keys(child))

    return keys


def collect_strings(value):
    strings = set()

    if isinstance(value, str):
        strings.add(value)

    elif isinstance(value, dict):
        for child in value.values():
            strings.update(collect_strings(child))

    elif isinstance(value, list):
        for child in value:
            strings.update(collect_strings(child))

    return strings


def test_query_service_has_stable_identity():
    assert TENANT_BOUNDARY_AUDIT_QUERY_SERVICE_ID == (
        "tenant-boundary-audit-evidence-query-service"
    )
    assert TENANT_BOUNDARY_AUDIT_QUERY_SERVICE_VERSION == (
        "0.1.0"
    )
    assert TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_ID == (
        "tenant-public-boundary-audit-record"
    )
    assert TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_VERSION == (
        "0.1.0"
    )
    assert (
        TENANT_PUBLIC_BOUNDARY_AUDIT_RECORD_SCHEMA_VERSION
        == "1.0.0"
    )


def test_empty_tenant_query_returns_empty_result(
    tmp_path,
):
    _, service = build_system(tmp_path)

    result = service.list_for_tenant(
        tenant_id="tenant-alpha"
    )

    assert result.tenant_id == "tenant-alpha"
    assert result.record_count == 0
    assert result.records == ()
    assert result.verify() is True


def test_tenant_can_list_own_records(tmp_path):
    ledger, service = build_system(tmp_path)

    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )
    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="checkpoint-read",
        released=True,
        audit=safe_audit(),
    )

    result = service.list_for_tenant(
        tenant_id="tenant-alpha"
    )

    assert result.record_count == 2
    assert [
        record.response_kind
        for record in result.records
    ] == [
        "evaluation",
        "checkpoint-read",
    ]
    assert [
        record.tenant_sequence_number
        for record in result.records
    ] == [1, 2]
    assert result.verify() is True


def test_cross_tenant_records_are_excluded(tmp_path):
    ledger, service = build_system(tmp_path)

    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(
            tenant_id="tenant-alpha"
        ),
    )
    ledger.append(
        tenant_id="tenant-beta",
        response_kind="execution-read",
        released=True,
        audit=safe_audit(
            tenant_id="tenant-beta"
        ),
    )

    alpha = service.list_for_tenant(
        tenant_id="tenant-alpha"
    )
    beta = service.list_for_tenant(
        tenant_id="tenant-beta"
    )

    assert alpha.record_count == 1
    assert beta.record_count == 1

    assert alpha.records[0].tenant_id == (
        "tenant-alpha"
    )
    assert beta.records[0].tenant_id == (
        "tenant-beta"
    )


def test_tenant_sequence_does_not_reveal_global_order(
    tmp_path,
):
    ledger, service = build_system(tmp_path)

    ledger.append(
        tenant_id="tenant-beta",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(
            tenant_id="tenant-beta"
        ),
    )
    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(
            tenant_id="tenant-alpha"
        ),
    )
    ledger.append(
        tenant_id="tenant-beta",
        response_kind="checkpoint-read",
        released=True,
        audit=safe_audit(
            tenant_id="tenant-beta"
        ),
    )
    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="execution-read",
        released=True,
        audit=safe_audit(
            tenant_id="tenant-alpha"
        ),
    )

    alpha = service.list_for_tenant(
        tenant_id="tenant-alpha"
    )

    assert [
        record.tenant_sequence_number
        for record in alpha.records
    ] == [1, 2]


def test_public_view_excludes_global_ledger_fields(
    tmp_path,
):
    ledger, service = build_system(tmp_path)

    internal = ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )

    result = service.list_for_tenant(
        tenant_id="tenant-alpha"
    ).to_dict()

    keys = collect_keys(result)
    strings = collect_strings(result)

    forbidden_keys = {
        "sequence_number",
        "previous_record_hash",
        "record_hash",
        "boundary_audit_hash",
        "ledger_id",
        "ledger_version",
    }

    forbidden_values = {
        internal.record_hash,
        internal.previous_record_hash,
        internal.boundary_audit_hash,
    }

    assert forbidden_keys.isdisjoint(keys)
    assert forbidden_values.isdisjoint(strings)


def test_public_record_id_is_deterministic(tmp_path):
    ledger, service = build_system(tmp_path)

    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )

    first = service.list_for_tenant(
        tenant_id="tenant-alpha"
    )
    second = service.list_for_tenant(
        tenant_id="tenant-alpha"
    )

    assert (
        first.records[0].public_record_id
        == second.records[0].public_record_id
    )
    assert len(
        first.records[0].public_record_id
    ) == 64


def test_cross_tenant_public_ids_are_distinct(
    tmp_path,
):
    ledger, service = build_system(tmp_path)

    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(
            tenant_id="tenant-alpha"
        ),
    )
    ledger.append(
        tenant_id="tenant-beta",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(
            tenant_id="tenant-beta"
        ),
    )

    alpha = service.list_for_tenant(
        tenant_id="tenant-alpha"
    )
    beta = service.list_for_tenant(
        tenant_id="tenant-beta"
    )

    assert (
        alpha.records[0].public_record_id
        != beta.records[0].public_record_id
    )


def test_tenant_can_resolve_own_public_record(
    tmp_path,
):
    ledger, service = build_system(tmp_path)

    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )

    listed = service.list_for_tenant(
        tenant_id="tenant-alpha"
    ).records[0]

    resolved = service.get_for_tenant(
        tenant_id="tenant-alpha",
        public_record_id=(
            listed.public_record_id
        ),
    )

    assert resolved == listed
    assert resolved.verify() is True


def test_other_tenant_cannot_resolve_public_record(
    tmp_path,
):
    ledger, service = build_system(tmp_path)

    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )

    public_record_id = service.list_for_tenant(
        tenant_id="tenant-alpha"
    ).records[0].public_record_id

    assert service.get_for_tenant(
        tenant_id="tenant-beta",
        public_record_id=public_record_id,
    ) is None


def test_unknown_public_record_returns_none(tmp_path):
    _, service = build_system(tmp_path)

    assert service.get_for_tenant(
        tenant_id="tenant-alpha",
        public_record_id="f" * 64,
    ) is None


def test_rejected_release_evidence_is_visible(
    tmp_path,
):
    ledger, service = build_system(tmp_path)

    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=False,
        audit=rejected_audit(),
    )

    record = service.list_for_tenant(
        tenant_id="tenant-alpha"
    ).records[0]

    assert record.released is False
    assert record.audit_valid is False
    assert record.violation_count == 1
    assert record.verify() is True


def test_tampered_public_record_fails_verification(
    tmp_path,
):
    ledger, service = build_system(tmp_path)

    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )

    record = service.list_for_tenant(
        tenant_id="tenant-alpha"
    ).records[0]

    tampered = replace(
        record,
        response_kind="changed",
    )

    assert record.verify() is True
    assert tampered.verify() is False


def test_tampered_query_result_fails_verification(
    tmp_path,
):
    ledger, service = build_system(tmp_path)

    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )

    result = service.list_for_tenant(
        tenant_id="tenant-alpha"
    )

    tampered = replace(
        result,
        record_count=999,
    )

    assert result.verify() is True
    assert tampered.verify() is False


def test_public_record_is_immutable(tmp_path):
    ledger, service = build_system(tmp_path)

    ledger.append(
        tenant_id="tenant-alpha",
        response_kind="evaluation",
        released=True,
        audit=safe_audit(),
    )

    record = service.list_for_tenant(
        tenant_id="tenant-alpha"
    ).records[0]

    with pytest.raises(FrozenInstanceError):
        record.tenant_id = "tenant-beta"


@pytest.mark.parametrize(
    "tenant_id",
    [
        "",
        "   ",
    ],
)
def test_empty_tenant_id_is_rejected(
    tmp_path,
    tenant_id,
):
    _, service = build_system(tmp_path)

    with pytest.raises(ValueError):
        service.list_for_tenant(
            tenant_id=tenant_id
        )


@pytest.mark.parametrize(
    "public_record_id",
    [
        "",
        "   ",
    ],
)
def test_empty_public_record_id_is_rejected(
    tmp_path,
    public_record_id,
):
    _, service = build_system(tmp_path)

    with pytest.raises(ValueError):
        service.get_for_tenant(
            tenant_id="tenant-alpha",
            public_record_id=public_record_id,
        )
