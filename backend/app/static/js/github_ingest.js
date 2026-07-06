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


function setGitHubIngestEnabled(isEnabled) {
    const ingestButton = document.getElementById('github_ingest_button');

    if (!ingestButton) {
        return;
    }

    ingestButton.disabled = !isEnabled;
}


function showGitHubValidationResult(isValid, errors) {
    const card = document.getElementById('github_validation_card');
    const title = document.getElementById('github_validation_title');
    const status = document.getElementById('github_validation_status');
    const errorCount = document.getElementById('github_validation_error_count');
    const details = document.getElementById('github_validation_details');

    if (card) {
        card.classList.remove('hidden');
    }

    if (!title || !status || !errorCount || !details) {
        return;
    }

    if (isValid) {
        title.textContent = "✓ GitHub Payload Validation Passed";
        title.className = "result-title success";

        status.textContent = "Valid";
        errorCount.textContent = "0";
        details.textContent = "Payload is valid and ready for ingestion.";
        return;
    }

    title.textContent = "✕ GitHub Payload Validation Failed";
    title.className = "result-title error";

    status.textContent = "Invalid";
    errorCount.textContent = errors.length;
    details.textContent = errors.join(", ");
}


function formatGitHubErrors(errors) {
    if (Array.isArray(errors)) {
        return errors.join(", ");
    }

    return JSON.stringify(errors);
}


function resetGitHubExamplePayload() {
    const input = document.getElementById('github_json_input');
    const statusBox = document.getElementById('github_ingest_status');

    input.value = GITHUB_EXAMPLE_PAYLOAD;
    setGitHubIngestEnabled(false);
    showGitHubValidationResult(false, ["payload_reset_requires_validation"]);

    statusBox.textContent = "Example GitHub payload restored. Validate before ingesting.";
    statusBox.className = "success";

    addActivity("GitHub example payload restored");
}


function clearGitHubPayload() {
    const input = document.getElementById('github_json_input');
    const statusBox = document.getElementById('github_ingest_status');

    input.value = "";
    setGitHubIngestEnabled(false);
    showGitHubValidationResult(false, ["payload_cleared"]);

    statusBox.textContent = "GitHub payload cleared. Validate before ingesting.";
    statusBox.className = "success";

    addActivity("GitHub payload cleared");
}


function formatGitHubPayload() {
    const input = document.getElementById('github_json_input');
    const statusBox = document.getElementById('github_ingest_status');

    try {
        const payload = JSON.parse(input.value);
        input.value = JSON.stringify(payload, null, 2);
        setGitHubIngestEnabled(false);
        showGitHubValidationResult(false, ["payload_formatted_requires_validation"]);

        statusBox.textContent = "GitHub payload formatted. Validate before ingesting.";
        statusBox.className = "success";

        addActivity("GitHub payload formatted");
    } catch (error) {
        setGitHubIngestEnabled(false);
        showGitHubValidationResult(false, ["invalid_json"]);

        statusBox.textContent = "Cannot format invalid JSON.";
        statusBox.className = "error";

        addActivity("GitHub payload format failed: invalid JSON");
    }
}


function getGitHubPayloadValidationErrors(payload) {
    const errors = [];

    if (!Object.prototype.hasOwnProperty.call(payload, "events")) {
        errors.push("missing_events_field");
        return errors;
    }

    if (!Array.isArray(payload.events)) {
        errors.push("events_must_be_a_list");
        return errors;
    }

    if (payload.events.length === 0) {
        errors.push("events_list_is_empty");
        return errors;
    }

    payload.events.forEach((event, index) => {
        if (typeof event !== "object" || event === null || Array.isArray(event)) {
            errors.push(`event_${index}_must_be_an_object`);
            return;
        }

        if (!event.id) {
            errors.push(`event_${index}_missing_id`);
        }

        if (!event.event_name) {
            errors.push(`event_${index}_missing_event_name`);
        }

        if (!event.created_at) {
            errors.push(`event_${index}_missing_created_at`);
        }
    });

    return errors;
}


function validateGitHubPayload() {
    const input = document.getElementById('github_json_input');
    const statusBox = document.getElementById('github_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        const errors = ["invalid_json"];

        setGitHubIngestEnabled(false);
        showGitHubValidationResult(false, errors);

        statusBox.textContent = "Payload validation failed: invalid JSON.";
        statusBox.className = "error";

        addActivity("GitHub payload validation failed: invalid JSON");
        return false;
    }

    const errors = getGitHubPayloadValidationErrors(payload);

    if (errors.length > 0) {
        setGitHubIngestEnabled(false);
        showGitHubValidationResult(false, errors);

        statusBox.textContent = `Payload validation failed: ${errors.join(", ")}.`;
        statusBox.className = "error";

        addActivity("GitHub payload validation failed");
        return false;
    }

    setGitHubIngestEnabled(true);
    showGitHubValidationResult(true, []);

    statusBox.textContent = "Payload validation passed. Ingest is now enabled.";
    statusBox.className = "success";

    addActivity("GitHub payload validation passed");

    return true;
}


function showGitHubIngestionResult(data) {
    const card = document.getElementById('github_result_card');
    const title = document.getElementById('github_result_title');

    card.classList.remove('hidden');

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
            formatGitHubErrors(data.reason);
    } else {
        title.textContent = "✕ GitHub Ingestion Failed";
        title.className = "result-title error";

        document.getElementById('github_result_source').textContent = "github";
        document.getElementById('github_result_events').textContent = "0";
        document.getElementById('github_result_snapshot_status').textContent = "N/A";
        document.getElementById('github_result_strategy').textContent = "N/A";
        document.getElementById('github_result_kernel_decision').textContent = "N/A";
        document.getElementById('github_result_reason').textContent =
            formatGitHubErrors(data.errors || data);
    }
}


async function ingestGitHubEvidence() {
    const input = document.getElementById('github_json_input');
    const statusBox = document.getElementById('github_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        const errors = ["invalid_json"];

        setGitHubIngestEnabled(false);
        showGitHubValidationResult(false, errors);

        statusBox.textContent = "Invalid JSON. Please check the payload.";
        statusBox.className = "error";

        addActivity("GitHub evidence import failed: invalid JSON");

        showGitHubIngestionResult({
            status: "failed",
            errors: errors,
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
        setGitHubIngestEnabled(false);

        statusBox.textContent =
            `GitHub ingest complete: ${data.events_normalized} events processed. Validate again before the next ingest.`;

        statusBox.className = "success";

        addActivity("GitHub evidence ingested");
        addActivity(`${data.events_normalized} GitHub events normalized`);
        addActivity(`GitHub snapshot ${data.snapshot_status}`);
        addActivity(`Kernel selected strategy: ${data.selected_strategy}`);

        await refreshConsole();
    } else {
        setGitHubIngestEnabled(false);

        statusBox.textContent = "GitHub ingest failed.";
        statusBox.className = "error";

        addActivity("GitHub evidence import failed");
    }
}


document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('github_json_input');

    if (!input) {
        return;
    }

    input.addEventListener('input', () => {
        setGitHubIngestEnabled(false);
        showGitHubValidationResult(false, ["payload_changed_requires_validation"]);

        const statusBox = document.getElementById('github_ingest_status');

        if (statusBox) {
            statusBox.textContent = "Payload changed. Validate before ingesting.";
            statusBox.className = "";
        }
    });
});