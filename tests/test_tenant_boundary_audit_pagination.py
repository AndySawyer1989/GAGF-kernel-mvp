from dataclasses import FrozenInstanceError, replace

import pytest

from backend.app.gagf.tenant_boundary_audit_pagination import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    TENANT_BOUNDARY_AUDIT_PAGINATION_SERVICE_ID,
    TENANT_BOUNDARY_AUDIT_PAGINATION_SERVICE_VERSION,
    TenantBoundaryAuditCursorError,
    TenantBoundaryAuditPaginationService,
)
from backend.app.gagf.tenant_public_boundary_audit_ledger import (
    TenantPublicBoundaryAuditLedger,
)
from backend.app.gagf.tenant_public_boundary_auditor import (
    TenantPublicBoundaryAuditor,
)


def safe_audit(*, tenant_id):
    return TenantPublicBoundaryAuditor().audit(
        response={
            "tenant_id": tenant_id,
            "public_artifact_id": "a" * 64,
            "view_hash": "b" * 64,
        }
    )


def build_system(tmp_path):
    database_path = tmp_path / "boundary-audit.db"

    return (
        TenantPublicBoundaryAuditLedger(
            database_path
        ),
        TenantBoundaryAuditPaginationService(
            database_path=database_path
        ),
    )


def append_records(
    ledger,
    *,
    tenant_id="tenant-alpha",
    count=5,
):
    for index in range(count):
        ledger.append(
            tenant_id=tenant_id,
            response_kind=f"response-{index + 1}",
            released=True,
            audit=safe_audit(
                tenant_id=tenant_id
            ),
        )


def test_pagination_service_has_stable_identity():
    assert (
        TENANT_BOUNDARY_AUDIT_PAGINATION_SERVICE_ID
        == "tenant-boundary-audit-pagination-service"
    )
    assert (
        TENANT_BOUNDARY_AUDIT_PAGINATION_SERVICE_VERSION
        == "0.1.0"
    )
    assert DEFAULT_PAGE_SIZE == 25
    assert MAX_PAGE_SIZE == 100


def test_empty_ledger_returns_empty_page(tmp_path):
    _, service = build_system(tmp_path)

    page = service.list_page(
        tenant_id="tenant-alpha"
    )

    assert page.returned_count == 0
    assert page.records == ()
    assert page.next_cursor is None
    assert page.has_more is False
    assert page.verify() is True


def test_first_page_is_bounded(tmp_path):
    ledger, service = build_system(tmp_path)
    append_records(ledger, count=5)

    page = service.list_page(
        tenant_id="tenant-alpha",
        page_size=2,
    )

    assert page.returned_count == 2
    assert [
        record.tenant_sequence_number
        for record in page.records
    ] == [1, 2]
    assert page.has_more is True
    assert page.next_cursor is not None
    assert page.verify() is True


def test_cursor_returns_next_page(tmp_path):
    ledger, service = build_system(tmp_path)
    append_records(ledger, count=5)

    first = service.list_page(
        tenant_id="tenant-alpha",
        page_size=2,
    )
    second = service.list_page(
        tenant_id="tenant-alpha",
        page_size=2,
        cursor=first.next_cursor,
    )

    assert [
        record.tenant_sequence_number
        for record in second.records
    ] == [3, 4]
    assert second.has_more is True


def test_final_page_has_no_cursor(tmp_path):
    ledger, service = build_system(tmp_path)
    append_records(ledger, count=5)

    first = service.list_page(
        tenant_id="tenant-alpha",
        page_size=2,
    )
    second = service.list_page(
        tenant_id="tenant-alpha",
        page_size=2,
        cursor=first.next_cursor,
    )
    third = service.list_page(
        tenant_id="tenant-alpha",
        page_size=2,
        cursor=second.next_cursor,
    )

    assert [
        record.tenant_sequence_number
        for record in third.records
    ] == [5]
    assert third.has_more is False
    assert third.next_cursor is None


def test_cursor_is_tenant_bound(tmp_path):
    ledger, service = build_system(tmp_path)

    append_records(
        ledger,
        tenant_id="tenant-alpha",
        count=3,
    )
    append_records(
        ledger,
        tenant_id="tenant-beta",
        count=3,
    )

    alpha = service.list_page(
        tenant_id="tenant-alpha",
        page_size=1,
    )

    with pytest.raises(
        TenantBoundaryAuditCursorError,
        match="verification failed",
    ):
        service.list_page(
            tenant_id="tenant-beta",
            page_size=1,
            cursor=alpha.next_cursor,
        )


def test_cross_tenant_records_are_excluded(tmp_path):
    ledger, service = build_system(tmp_path)

    append_records(
        ledger,
        tenant_id="tenant-alpha",
        count=2,
    )
    append_records(
        ledger,
        tenant_id="tenant-beta",
        count=2,
    )

    page = service.list_page(
        tenant_id="tenant-alpha",
        page_size=10,
    )

    assert page.returned_count == 2
    assert all(
        record.tenant_id == "tenant-alpha"
        for record in page.records
    )


def test_cursor_does_not_contain_tenant_id(tmp_path):
    ledger, service = build_system(tmp_path)
    append_records(ledger, count=3)

    page = service.list_page(
        tenant_id="tenant-alpha",
        page_size=1,
    )

    assert "tenant-alpha" not in page.next_cursor


def test_tampered_cursor_is_rejected(tmp_path):
    ledger, service = build_system(tmp_path)
    append_records(ledger, count=3)

    page = service.list_page(
        tenant_id="tenant-alpha",
        page_size=1,
    )

    tampered = (
        "f" * 64
        + page.next_cursor[64:]
    )

    with pytest.raises(
        TenantBoundaryAuditCursorError,
        match="verification failed",
    ):
        service.list_page(
            tenant_id="tenant-alpha",
            page_size=1,
            cursor=tampered,
        )


@pytest.mark.parametrize(
    "cursor",
    [
        "",
        "   ",
        "invalid",
        "hash.not-a-number",
        ("a" * 64) + ".0",
    ],
)
def test_invalid_cursor_is_rejected(
    tmp_path,
    cursor,
):
    _, service = build_system(tmp_path)

    with pytest.raises(
        TenantBoundaryAuditCursorError
    ):
        service.list_page(
            tenant_id="tenant-alpha",
            cursor=cursor,
        )


@pytest.mark.parametrize(
    "page_size",
    [
        0,
        -1,
        MAX_PAGE_SIZE + 1,
    ],
)
def test_invalid_page_size_is_rejected(
    tmp_path,
    page_size,
):
    _, service = build_system(tmp_path)

    with pytest.raises(ValueError):
        service.list_page(
            tenant_id="tenant-alpha",
            page_size=page_size,
        )


@pytest.mark.parametrize(
    "tenant_id",
    [
        "",
        "   ",
    ],
)
def test_empty_tenant_is_rejected(
    tmp_path,
    tenant_id,
):
    _, service = build_system(tmp_path)

    with pytest.raises(ValueError):
        service.list_page(
            tenant_id=tenant_id
        )


def test_page_hash_detects_tampering(tmp_path):
    ledger, service = build_system(tmp_path)
    append_records(ledger, count=2)

    page = service.list_page(
        tenant_id="tenant-alpha",
        page_size=1,
    )

    tampered = replace(
        page,
        returned_count=99,
    )

    assert page.verify() is True
    assert tampered.verify() is False


def test_page_is_immutable(tmp_path):
    _, service = build_system(tmp_path)

    page = service.list_page(
        tenant_id="tenant-alpha"
    )

    with pytest.raises(FrozenInstanceError):
        page.tenant_id = "tenant-beta"
