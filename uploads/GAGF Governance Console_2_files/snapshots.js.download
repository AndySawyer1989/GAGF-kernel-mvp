async function loadSnapshotsTable() {
    const response = await fetch('/snapshots');
    const snapshots = await response.json();

    const tableBody = document.getElementById('snapshots_table_body');
    tableBody.innerHTML = "";

    if (!snapshots.length) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5">No snapshots found.</td>
            </tr>
        `;
        return;
    }

    snapshots.slice(0, 5).forEach(snapshot => {
        const adaptiveState = JSON.parse(snapshot.adaptive_state_json);
        const createdAt = new Date(snapshot.created_at).toLocaleTimeString();

        const row = document.createElement('tr');

        row.innerHTML = `
            <td>${snapshot.snapshot_id.slice(0, 8)}...</td>
            <td>${snapshot.status}</td>
            <td>${adaptiveState.risk_index}</td>
            <td>${adaptiveState.uncertainty}</td>
            <td>${createdAt}</td>
        `;

        tableBody.appendChild(row);
    });
}