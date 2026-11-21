import sqlite3
from types import SimpleNamespace

import pytest

from backend.app.gagf.decision_ledger import DecisionLedger


def build_decision(snapshot_id):
    return SimpleNamespace(
        snapshot_id=snapshot_id,
        active_strategy="Normal",
        strategy_proposal="continue",
        kernel_decision="transition_to_probe",
        selected_strategy="Probe",
        reason=["uncertainty_high"],
        decision_meta=SimpleNamespace(
            model_dump=lambda: {
                "is_override_triggered": False,
                "hysteresis_buffer_active": False,
                "policy_version": "0.1",
                "policy_id": "gagf_default_kernel_policy",
            }
        ),
    )


def create_snapshot_table(db_path, snapshots):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE gagf_state_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO gagf_state_snapshots (
                snapshot_id,
                tenant_id
            )
            VALUES (?, ?)
            """,
            snapshots,
        )


def test_decisions_are_scoped_to_tenant(tmp_path):
    db_path = tmp_path / "decision-isolation.db"

    create_snapshot_table(
        db_path,
        [
            ("snapshot-a", "tenant-a"),
            ("snapshot-b", "tenant-b"),
        ],
    )

    ledger = DecisionLedger(db_path)

    decision_a = ledger.save_decision(
        build_decision("snapshot-a"),
        tenant_id="tenant-a",
        evidence=["event-a"],
    )

    decision_b = ledger.save_decision(
        build_decision("snapshot-b"),
        tenant_id="tenant-b",
        evidence=["event-b"],
    )

    assert ledger.get_decision(
        decision_a,
        tenant_id="tenant-a",
    ) is not None

    assert ledger.get_decision(
        decision_a,
        tenant_id="tenant-b",
    ) is None

    assert ledger.get_decision(
        decision_b,
        tenant_id="tenant-a",
    ) is None

    assert {
        row["decision_id"]
        for row in ledger.list_decisions(tenant_id="tenant-a")
    } == {decision_a}

    assert {
        row["decision_id"]
        for row in ledger.list_decisions(tenant_id="tenant-b")
    } == {decision_b}


def test_decision_write_rejects_snapshot_owned_by_another_tenant(tmp_path):
    db_path = tmp_path / "decision-owner-mismatch.db"

    create_snapshot_table(
        db_path,
        [("snapshot-a", "tenant-a")],
    )

    ledger = DecisionLedger(db_path)

    with pytest.raises(
        ValueError,
        match="does not match snapshot owner",
    ):
        ledger.save_decision(
            build_decision("snapshot-a"),
            tenant_id="tenant-b",
        )

    assert ledger.list_decisions(tenant_id="tenant-a") == []
    assert ledger.list_decisions(tenant_id="tenant-b") == []


def test_decision_write_rejects_unknown_snapshot(tmp_path):
    db_path = tmp_path / "decision-unknown-snapshot.db"

    create_snapshot_table(db_path, [])

    ledger = DecisionLedger(db_path)

    with pytest.raises(
        ValueError,
        match="snapshot does not exist",
    ):
        ledger.save_decision(
            build_decision("missing-snapshot"),
            tenant_id="tenant-a",
        )


def test_legacy_decision_migration_backfills_only_known_owners(tmp_path):
    db_path = tmp_path / "decision-migration.db"

    create_snapshot_table(
        db_path,
        [("known-snapshot", "tenant-a")],
    )

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE gagf_decision_records (
                decision_id TEXT PRIMARY KEY,
                snapshot_id TEXT,
                active_strategy TEXT,
                strategy_proposal TEXT,
                kernel_decision TEXT NOT NULL,
                selected_strategy TEXT,
                reason_json TEXT NOT NULL,
                decision_meta_json TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        conn.executemany(
            """
            INSERT INTO gagf_decision_records (
                decision_id,
                snapshot_id,
                kernel_decision,
                reason_json,
                decision_meta_json,
                evidence_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "known-decision",
                    "known-snapshot",
                    "continue",
                    "[]",
                    "{}",
                    "[]",
                    "2026-01-01T00:00:00+00:00",
                ),
                (
                    "unknown-decision",
                    "missing-snapshot",
                    "continue",
                    "[]",
                    "{}",
                    "[]",
                    "2026-01-02T00:00:00+00:00",
                ),
            ],
        )

    ledger = DecisionLedger(db_path)

    known = ledger.get_decision(
        "known-decision",
        tenant_id="tenant-a",
    )

    unknown = ledger.get_decision(
        "unknown-decision",
        tenant_id="tenant-a",
    )

    assert known is not None
    assert known["tenant_id"] == "tenant-a"
    assert unknown is None

    with sqlite3.connect(db_path) as conn:
        unknown_owner = conn.execute(
            """
            SELECT tenant_id
            FROM gagf_decision_records
            WHERE decision_id = 'unknown-decision'
            """
        ).fetchone()[0]

    assert unknown_owner is None

    # Reinitialization must not change the migrated ownership.
    DecisionLedger(db_path)

    assert ledger.get_decision(
        "known-decision",
        tenant_id="tenant-a",
    ) is not None


@pytest.mark.parametrize("tenant_id", ["", " ", None])
def test_decision_reads_reject_empty_tenant(tmp_path, tenant_id):
    db_path = tmp_path / "decision-empty-tenant.db"
    create_snapshot_table(db_path, [])

    ledger = DecisionLedger(db_path)

    with pytest.raises(ValueError, match="tenant_id is required"):
        ledger.list_decisions(tenant_id=tenant_id)


def test_decision_reads_require_explicit_tenant(tmp_path):
    db_path = tmp_path / "decision-required-tenant.db"
    create_snapshot_table(db_path, [])

    ledger = DecisionLedger(db_path)

    with pytest.raises(TypeError):
        ledger.list_decisions()

    with pytest.raises(TypeError):
        ledger.get_decision("decision-a")
