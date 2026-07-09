async function refreshConsole() {
    await loadDashboard();
    await loadSnapshotsTable();
    await loadDecisionsTable();
}

refreshConsole();

setInterval(() => {
    refreshConsole();
}, 5000);