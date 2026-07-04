async function ingestGitHubEvidence() {
    const input = document.getElementById('github_json_input');
    const statusBox = document.getElementById('github_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        statusBox.textContent = "Invalid JSON. Please check the payload.";
        statusBox.className = "error";
        addActivity("GitHub evidence import failed: invalid JSON");
        return;
    }

    statusBox.textContent = "Ingesting GitHub evidence...";
    statusBox.className = "";

    const response = await fetch('/ingest/github', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (data.status === "ingested") {
        statusBox.textContent = `GitHub ingest complete: ${data.events_normalized} events processed.`;
        statusBox.className = "success";

        addActivity(`GitHub evidence ingested`);
        addActivity(`${data.events_normalized} GitHub events normalized`);
        addActivity(`GitHub snapshot ${data.snapshot_status}`);
        addActivity(`Kernel selected strategy: ${data.selected_strategy}`);

        await refreshConsole();
    } else {
        statusBox.textContent = "GitHub ingest failed.";
        statusBox.className = "error";
        addActivity("GitHub evidence import failed");
    }
}