from types import SimpleNamespace

import pytest

from backend.app.gagf.snapshot_ledger import SnapshotLedger


def build_snapshot(snapshot_id, tenant_id, work_item_id="test-work-item"):
    return SimpleNamespace(
        snapshot_id=snapshot_id,
        tenant_id=tenant_id,
        work_item_id=work_item_id,
        status="VALID",
        adaptive_state=SimpleNamespace(
            model_dump=lambda: {"risk_index": 0.25}
        ),
        evidence_confidence=SimpleNamespace(
            model_dump=lambda: {"score": 0.95}
        ),
        timestamp_quality_distribution={
            "SOURCE_OCCURRED_AT": 1
        },
        evidence=["event-001"],
    )


def test_snapshot_reads_are_scoped_to_tenant(tmp_path):
    ledger = SnapshotLedger(tmp_path / "tenant-isolation.db")

    ledger.save_snapshot(build_snapshot("snapshot-a", "tenant-a"))
    ledger.save_snapshot(build_snapshot("snapshot-b", "tenant-b"))

    assert ledger.get_snapshot(
        "snapshot-a",
        tenant_id="tenant-a",
    ) is not None

    assert ledger.get_snapshot(
        "snapshot-a",
        tenant_id="tenant-b",
    ) is None

    assert ledger.get_snapshot(
        "snapshot-b",
        tenant_id="tenant-a",
    ) is None


def test_snapshot_listing_only_returns_requested_tenant(tmp_path):
    ledger = SnapshotLedger(tmp_path / "tenant-list.db")

    ledger.save_snapshot(build_snapshot("snapshot-a1", "tenant-a"))
    ledger.save_snapshot(build_snapshot("snapshot-a2", "tenant-a"))
    ledger.save_snapshot(build_snapshot("snapshot-b1", "tenant-b"))

    tenant_a_snapshots = ledger.list_snapshots(tenant_id="tenant-a")
    tenant_b_snapshots = ledger.list_snapshots(tenant_id="tenant-b")

    assert {row["snapshot_id"] for row in tenant_a_snapshots} == {
        "snapshot-a1",
        "snapshot-a2",
    }

    assert {row["snapshot_id"] for row in tenant_b_snapshots} == {
        "snapshot-b1",
    }


def test_duplicate_snapshot_id_cannot_transfer_ownership(tmp_path):
    ledger = SnapshotLedger(tmp_path / "ownership.db")

    original = build_snapshot("shared-id", "tenant-a", "original-work")
    ledger.save_snapshot(original)

    replacement = build_snapshot(
        "shared-id",
        "tenant-b",
        "replacement-work",
    )

    with pytest.raises(Exception):
        ledger.save_snapshot(replacement)

    original_record = ledger.get_snapshot(
        "shared-id",
        tenant_id="tenant-a",
    )

    assert original_record is not None
    assert original_record["tenant_id"] == "tenant-a"
    assert original_record["work_item_id"] == "original-work"

    assert ledger.get_snapshot(
        "shared-id",
        tenant_id="tenant-b",
    ) is None


@pytest.mark.parametrize(
    "tenant_id",
    ["", " ", None],
)
def test_snapshot_write_rejects_empty_tenant(tmp_path, tenant_id):
    ledger = SnapshotLedger(tmp_path / "empty-tenant.db")

    snapshot = build_snapshot("invalid-snapshot", tenant_id)

    with pytest.raises(ValueError, match="tenant_id is required"):
        ledger.save_snapshot(snapshot)


@pytest.mark.parametrize(
    "tenant_id",
    ["", " ", None],
)
def test_snapshot_reads_reject_empty_tenant(tmp_path, tenant_id):
    ledger = SnapshotLedger(tmp_path / "empty-read-tenant.db")

    with pytest.raises(ValueError, match="tenant_id is required"):
        ledger.list_snapshots(tenant_id=tenant_id)


def test_snapshot_lookup_requires_explicit_tenant(tmp_path):
    ledger = SnapshotLedger(tmp_path / "required-tenant.db")

    with pytest.raises(TypeError):
        ledger.list_snapshots()

    with pytest.raises(TypeError):
        ledger.get_snapshot("snapshot-a")
