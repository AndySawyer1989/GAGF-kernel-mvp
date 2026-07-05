const GITHUB_EXAMPLE_PAYLOAD = `{
  "events": [
    {
      "id": "gh-ui-001",
      "event_name": "pull_request",
      "action": "opened",
      "created_at": "2026-07-03T18:00:00Z"
    },
    {
      "id": "gh-ui-002",
      "event_name": "push",
      "action": "created",
      "created_at": "2026-07-03T18:05:00Z"
    }
  ]
}`;

function resetGitHubExamplePayload() {
    const input = document.getElementById('github_json_input');
    const statusBox = document.getElementById('github_ingest_status');

    input.value = GITHUB_EXAMPLE_PAYLOAD;

    statusBox.textContent = "Example GitHub payload restored.";
    statusBox.className = "success";

    addActivity("GitHub example payload restored");
}

function clearGitHubPayload() {
    const input = document.getElementById('github_json_input');
    const statusBox = document.getElementById('github_ingest_status');

    input.value = "";

    statusBox.textContent = "GitHub payload cleared.";
    statusBox.className = "success";

    addActivity("GitHub payload cleared");
}

function formatGitHubPayload() {
    const input = document.getElementById('github_json_input');
    const statusBox = document.getElementById('github_ingest_status');

    try {
        const payload = JSON.parse(input.value);
        input.value = JSON.stringify(payload, null, 2);

        statusBox.textContent = "GitHub payload formatted.";
        statusBox.className = "success";

        addActivity("GitHub payload formatted");
    } catch (error) {
        statusBox.textContent = "Cannot format invalid JSON.";
        statusBox.className = "error";

        addActivity("GitHub payload format failed: invalid JSON");
    }
}

function showGitHubIngestionResult(data) {
    const card = document.getElementById('github_result_card');
    const title = document.getElementById('github_result_title');

    card.style.display = 'block';

    if (data.status === "ingested") {
        title.textContent = "✓ GitHub Ingestion Successful";
        title.className = "result-title success";

        document.getElementById('github_result_source').textContent =
            data.source_system || "github";

        document.getElementById('github_result_events').textContent =
            data.events_normalized;

        document.getElementById('github_result_snapshot_status').textContent =
            data.snapshot_status;

        document.getElementById('github_result_strategy').textContent =
            data.selected_strategy;

        document.getElementById('github_result_kernel_decision').textContent =
            data.kernel_decision;

        document.getElementById('github_result_reason').textContent =
            data.reason.join(", ");
    } else {
        title.textContent = "✕ GitHub Ingestion Failed";
        title.className = "result-title error";

        document.getElementById('github_result_source').textContent = "github";
        document.getElementById('github_result_events').textContent = "0";
        document.getElementById('github_result_snapshot_status').textContent = "N/A";
        document.getElementById('github_result_strategy').textContent = "N/A";
        document.getElementById('github_result_kernel_decision').textContent = "N/A";
        document.getElementById('github_result_reason').textContent =
            JSON.stringify(data.errors || data);
    }
}


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

        showGitHubIngestionResult({
            status: "failed",
            errors: ["invalid_json"],
        });

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

    showGitHubIngestionResult(data);

    if (data.status === "ingested") {
        statusBox.textContent =
            `GitHub ingest complete: ${data.events_normalized} events processed.`;

        statusBox.className = "success";

        addActivity("GitHub evidence ingested");
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