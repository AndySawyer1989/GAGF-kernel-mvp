from backend.app.gagf.decision_ledger import DecisionLedger
from backend.app.gagf.schemas import DecisionMeta, ArbitrationResult

ledger = DecisionLedger()

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
        policy_id="gagf_default_kernel_policy"
    )
)

decision_id = ledger.save_decision(
    decision,
    evidence=["evt-001", "evt-002"]
)

print("Saved Decision:", decision_id)

loaded = ledger.get_decision(decision_id)

print()
print("Loaded Record")
print("----------------")
print(loaded)

