const JIRA_EXAMPLE_PAYLOAD = `{
  "events": [
    {
      "id": "jira-ui-001",
      "key": "FIP-101",
      "issue_type": "Story",
      "status": "Blocked",
      "priority": "Medium",
      "blocked": true,
      "created": "2026-07-07T12:00:00Z",
      "updated": "2026-07-07T12:30:00Z"
    },
    {
      "id": "jira-ui-002",
      "key": "FIP-202",
      "issue_type": "Bug",
      "status": "Open",
      "priority": "Critical",
      "created": "2026-07-07T13:00:00Z",
      "updated": "2026-07-07T13:15:00Z"
    }
  ]
}`;


function setJiraIngestEnabled(isEnabled) {
    const ingestButton = document.getElementById('jira_ingest_button');

    if (!ingestButton) {
        return;
    }

    ingestButton.disabled = !isEnabled;
}


function formatJiraErrors(errors) {
    if (Array.isArray(errors)) {
        return errors.join(", ");
    }

    return JSON.stringify(errors);
}


function showJiraValidationResult(isValid, errors) {
    const card = document.getElementById('jira_validation_card');
    const title = document.getElementById('jira_validation_title');
    const status = document.getElementById('jira_validation_status');
    const errorCount = document.getElementById('jira_validation_error_count');
    const details = document.getElementById('jira_validation_details');

    if (card) {
        card.classList.remove('hidden');
    }

    if (!title || !status || !errorCount || !details) {
        return;
    }

    if (isValid) {
        title.textContent = "✓ Jira Payload Validation Passed";
        title.className = "result-title success";

        status.textContent = "Valid";
        errorCount.textContent = "0";
        details.textContent = "Payload is valid and ready for ingestion.";
        return;
    }

    title.textContent = "✕ Jira Payload Validation Failed";
    title.className = "result-title error";

    status.textContent = "Invalid";
    errorCount.textContent = errors.length;
    details.textContent = errors.join(", ");
}


function getJiraPayloadValidationErrors(payload) {
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

        if (!event.key) {
            errors.push(`event_${index}_missing_key`);
        }

        if (!event.status) {
            errors.push(`event_${index}_missing_status`);
        }

        if (!event.created && !event.updated) {
            errors.push(`event_${index}_missing_timestamp`);
        }
    });

    return errors;
}


function validateJiraPayload() {
    const input = document.getElementById('jira_json_input');
    const statusBox = document.getElementById('jira_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        const errors = ["invalid_json"];

        setJiraIngestEnabled(false);
        showJiraValidationResult(false, errors);

        statusBox.textContent = "Payload validation failed: invalid JSON.";
        statusBox.className = "error";

        addActivity("[Jira] Payload validation failed: invalid JSON");
        return false;
    }

    const errors = getJiraPayloadValidationErrors(payload);

    if (errors.length > 0) {
        setJiraIngestEnabled(false);
        showJiraValidationResult(false, errors);

        statusBox.textContent = `Payload validation failed: ${errors.join(", ")}.`;
        statusBox.className = "error";

        addActivity("[Jira] Payload validation failed");
        return false;
    }

    setJiraIngestEnabled(true);
    showJiraValidationResult(true, []);

    statusBox.textContent = "Payload validation passed. Ingest is now enabled.";
    statusBox.className = "success";

    addActivity("[Jira] Payload validation passed");

    return true;
}


function resetJiraExamplePayload() {
    const input = document.getElementById('jira_json_input');
    const statusBox = document.getElementById('jira_ingest_status');

    input.value = JIRA_EXAMPLE_PAYLOAD;
    setJiraIngestEnabled(false);
    showJiraValidationResult(false, ["payload_reset_requires_validation"]);

    statusBox.textContent = "Example Jira payload restored. Validate before ingesting.";
    statusBox.className = "success";

    addActivity("[Jira] Example payload restored");
}


function clearJiraPayload() {
    const input = document.getElementById('jira_json_input');
    const statusBox = document.getElementById('jira_ingest_status');

    input.value = "";
    setJiraIngestEnabled(false);
    showJiraValidationResult(false, ["payload_cleared"]);

    statusBox.textContent = "Jira payload cleared. Validate before ingesting.";
    statusBox.className = "success";

    addActivity("[Jira] Payload cleared");
}


function formatJiraPayload() {
    const input = document.getElementById('jira_json_input');
    const statusBox = document.getElementById('jira_ingest_status');

    try {
        const payload = JSON.parse(input.value);
        input.value = JSON.stringify(payload, null, 2);
        setJiraIngestEnabled(false);
        showJiraValidationResult(false, ["payload_formatted_requires_validation"]);

        statusBox.textContent = "Jira payload formatted. Validate before ingesting.";
        statusBox.className = "success";

        addActivity("[Jira] Payload formatted");
    } catch (error) {
        setJiraIngestEnabled(false);
        showJiraValidationResult(false, ["invalid_json"]);

        statusBox.textContent = "Cannot format invalid JSON.";
        statusBox.className = "error";

        addActivity("[Jira] Payload format failed: invalid JSON");
    }
}


function showJiraIngestionResult(data) {
    const card = document.getElementById('jira_result_card');
    const title = document.getElementById('jira_result_title');

    card.classList.remove('hidden');

    if (data.status === "ingested") {
        title.textContent = "✓ Jira Ingestion Successful";
        title.className = "result-title success";

        document.getElementById('jira_result_source').textContent =
            data.source_system || "jira";

        document.getElementById('jira_result_events').textContent =
            data.events_normalized;

        document.getElementById('jira_result_snapshot_status').textContent =
            data.snapshot_status;

        document.getElementById('jira_result_strategy').textContent =
            data.selected_strategy;

        document.getElementById('jira_result_kernel_decision').textContent =
            data.kernel_decision;

        document.getElementById('jira_result_reason').textContent =
            formatJiraErrors(data.reason);
    } else {
        title.textContent = "✕ Jira Ingestion Failed";
        title.className = "result-title error";

        document.getElementById('jira_result_source').textContent = "jira";
        document.getElementById('jira_result_events').textContent = "0";
        document.getElementById('jira_result_snapshot_status').textContent = "N/A";
        document.getElementById('jira_result_strategy').textContent = "N/A";
        document.getElementById('jira_result_kernel_decision').textContent = "N/A";
        document.getElementById('jira_result_reason').textContent =
            formatJiraErrors(data.errors || data);
    }
}


async function ingestJiraEvidence() {
    const input = document.getElementById('jira_json_input');
    const statusBox = document.getElementById('jira_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        const errors = ["invalid_json"];

        setJiraIngestEnabled(false);
        showJiraValidationResult(false, errors);

        statusBox.textContent = "Invalid JSON. Please check the payload.";
        statusBox.className = "error";

        addActivity("[Jira] Evidence import failed: invalid JSON");

        showJiraIngestionResult({
            status: "failed",
            errors: errors,
        });

        return;
    }

    statusBox.textContent = "Ingesting Jira evidence...";
    statusBox.className = "";

    const response = await fetch('/ingest/jira', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    const data = await response.json();

    showJiraIngestionResult(data);

    if (data.status === "ingested") {
        setJiraIngestEnabled(false);

        statusBox.textContent =
            `Jira ingest complete: ${data.events_normalized} events processed. Validate again before the next ingest.`;

        statusBox.className = "success";

        addActivity("[Jira] Evidence ingested");
        addActivity(`[Jira] ${data.events_normalized} events normalized`);
        addActivity(`[Jira] Snapshot ${data.snapshot_status}`);
        addActivity(`[Kernel] Strategy selected: ${data.selected_strategy}`);

        await refreshConsole();
    } else {
        setJiraIngestEnabled(false);

        statusBox.textContent = "Jira ingest failed.";
        statusBox.className = "error";

        addActivity("[Jira] Evidence import failed");
    }
}


document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('jira_json_input');

    if (!input) {
        return;
    }

    input.addEventListener('input', () => {
        setJiraIngestEnabled(false);
        showJiraValidationResult(false, ["payload_changed_requires_validation"]);

        const statusBox = document.getElementById('jira_ingest_status');

        if (statusBox) {
            statusBox.textContent = "Payload changed. Validate before ingesting.";
            statusBox.className = "";
        }
    });
});