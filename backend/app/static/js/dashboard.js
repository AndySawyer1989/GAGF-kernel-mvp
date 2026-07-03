async function loadDashboard() {
    const response = await fetch('/dashboard');
    const data = await response.json();

    document.getElementById('kernel_status').textContent = data.kernel_status;
    document.getElementById('snapshot_count').textContent = data.snapshot_count;
    document.getElementById('decision_count').textContent = data.decision_count;

    if (data.latest_decision) {
        document.getElementById('latest_strategy').textContent =
            data.latest_decision.selected_strategy;

        document.getElementById('decision_strategy').textContent =
            data.latest_decision.selected_strategy;

        document.getElementById('decision_kernel').textContent =
            data.latest_decision.kernel_decision;

        document.getElementById('decision_reason').textContent =
            data.latest_decision.reason.join(", ");

        document.getElementById('decision_policy').textContent =
            data.latest_decision.decision_meta.policy_version;

        document.getElementById('decision_override').textContent =
            data.latest_decision.decision_meta.is_override_triggered ? "Yes" : "No";
    } else {
        document.getElementById('latest_strategy').textContent = "None";
        document.getElementById('decision_strategy').textContent = "None";
        document.getElementById('decision_kernel').textContent = "None";
        document.getElementById('decision_reason').textContent = "None";
        document.getElementById('decision_policy').textContent = "None";
        document.getElementById('decision_override').textContent = "None";
    }

    if (data.latest_snapshot) {
        document.getElementById('risk_index').textContent =
            data.latest_snapshot.adaptive_state.risk_index;

        document.getElementById('uncertainty').textContent =
            data.latest_snapshot.adaptive_state.uncertainty;
    } else {
        document.getElementById('risk_index').textContent = "None";
        document.getElementById('uncertainty').textContent = "None";
    }

    const refreshTime = new Date().toLocaleTimeString();
    document.getElementById('refresh_status').textContent =
        `Last refreshed at ${refreshTime}`;
}