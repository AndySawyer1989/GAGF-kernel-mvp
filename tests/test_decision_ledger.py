import sqlite3

from backend.app.gagf.decision_ledger import DecisionLedger
from backend.app.gagf.schemas import DecisionMeta, ArbitrationResult


def test_decision_ledger_saves_and_loads_tenant_owned_decision(tmp_path):
    db_path = tmp_path / "decision-ledger.db"

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE gagf_state_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO gagf_state_snapshots (
                snapshot_id,
                tenant_id
            )
            VALUES (?, ?)
            """,
            ("snapshot-001", "tenant-a"),
        )

    ledger = DecisionLedger(db_path)

    decision = ArbitrationResult(
        snapshot_id="snapshot-001",
        active_strategy="Normal",
        strategy_proposal="continue",
        kernel_decision="transition_to_probe",
        selected_strategy="Probe",
        reason=["uncertainty_high"],
        decision_meta=DecisionMeta(
            is_override_triggered=False,
            hysteresis_buffer_active=False,
            policy_version="0.1",
            policy_id="gagf_default_kernel_policy",
        ),
    )

    decision_id = ledger.save_decision(
        decision,
        tenant_id="tenant-a",
        evidence=["evt-001", "evt-002"],
    )

    loaded = ledger.get_decision(
        decision_id,
        tenant_id="tenant-a",
    )

    assert loaded is not None
    assert loaded["tenant_id"] == "tenant-a"
    assert loaded["snapshot_id"] == "snapshot-001"
    assert ledger.get_decision(
        decision_id,
        tenant_id="tenant-b",
    ) is None
