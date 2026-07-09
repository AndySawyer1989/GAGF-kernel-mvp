async function loadDecisionsTable() {
    const response = await fetch('/decisions');
    const decisions = await response.json();

    const tableBody = document.getElementById('decisions_table_body');
    tableBody.innerHTML = "";

    if (!decisions.length) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5">No decisions found.</td>
            </tr>
        `;
        return;
    }

    decisions.slice(0, 5).forEach(decision => {
        const decisionMeta = JSON.parse(decision.decision_meta_json);
        const createdAt = new Date(decision.created_at).toLocaleTimeString();

        const row = document.createElement('tr');

        row.innerHTML = `
            <td>${decision.decision_id.slice(0, 8)}...</td>
            <td>${decision.selected_strategy}</td>
            <td>${decision.kernel_decision}</td>
            <td>${decisionMeta.is_override_triggered ? "Yes" : "No"}</td>
            <td>${createdAt}</td>
        `;

        tableBody.appendChild(row);
    });
}