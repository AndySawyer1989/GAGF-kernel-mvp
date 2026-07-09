const ENTRA_EXAMPLE_PAYLOAD = `{
  "events": [
    {
      "id": "entra-ui-001",
      "activityDisplayName": "User sign-in failed",
      "createdDateTime": "2026-07-08T12:00:00Z",
      "status": {
        "errorCode": 50126,
        "failureReason": "Invalid username or password failure"
      }
    },
    {
      "id": "entra-ui-002",
      "activityDisplayName": "User sign-in",
      "createdDateTime": "2026-07-08T12:05:00Z",
      "conditionalAccessStatus": "success",
      "riskState": "none",
      "riskLevelAggregated": "none",
      "status": {
        "errorCode": 0
      }
    }
  ]
}`;


function setEntraIngestEnabled(isEnabled) {
    const ingestButton = document.getElementById('entra_ingest_button');

    if (!ingestButton) {
        return;
    }

    ingestButton.disabled = !isEnabled;
}


function formatEntraErrors(errors) {
    if (Array.isArray(errors)) {
        return errors.join(", ");
    }

    return JSON.stringify(errors);
}


function showEntraValidationResult(isValid, errors) {
    const card = document.getElementById('entra_validation_card');
    const title = document.getElementById('entra_validation_title');
    const status = document.getElementById('entra_validation_status');
    const errorCount = document.getElementById('entra_validation_error_count');
    const details = document.getElementById('entra_validation_details');

    if (card) {
        card.classList.remove('hidden');
    }

    if (!title || !status || !errorCount || !details) {
        return;
    }

    if (isValid) {
        title.textContent = "✓ Entra ID Payload Validation Passed";
        title.className = "result-title success";

        status.textContent = "Valid";
        errorCount.textContent = "0";
        details.textContent = "Payload is valid and ready for ingestion.";
        return;
    }

    title.textContent = "✕ Entra ID Payload Validation Failed";
    title.className = "result-title error";

    status.textContent = "Invalid";
    errorCount.textContent = errors.length;
    details.textContent = errors.join(", ");
}


function getEntraPayloadValidationErrors(payload) {
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

        if (!event.activityDisplayName) {
            errors.push(`event_${index}_missing_activityDisplayName`);
        }

        if (!event.createdDateTime) {
            errors.push(`event_${index}_missing_createdDateTime`);
        }
    });

    return errors;
}


function validateEntraPayload() {
    const input = document.getElementById('entra_json_input');
    const statusBox = document.getElementById('entra_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        const errors = ["invalid_json"];

        setEntraIngestEnabled(false);
        showEntraValidationResult(false, errors);

        statusBox.textContent = "Payload validation failed: invalid JSON.";
        statusBox.className = "error";

        addActivity("[Entra ID] Payload validation failed: invalid JSON");
        return false;
    }

    const errors = getEntraPayloadValidationErrors(payload);

    if (errors.length > 0) {
        setEntraIngestEnabled(false);
        showEntraValidationResult(false, errors);

        statusBox.textContent = `Payload validation failed: ${errors.join(", ")}.`;
        statusBox.className = "error";

        addActivity("[Entra ID] Payload validation failed");
        return false;
    }

    setEntraIngestEnabled(true);
    showEntraValidationResult(true, []);

    statusBox.textContent = "Payload validation passed. Ingest is now enabled.";
    statusBox.className = "success";

    addActivity("[Entra ID] Payload validation passed");

    return true;
}


function resetEntraExamplePayload() {
    const input = document.getElementById('entra_json_input');
    const statusBox = document.getElementById('entra_ingest_status');

    input.value = ENTRA_EXAMPLE_PAYLOAD;
    setEntraIngestEnabled(false);
    showEntraValidationResult(false, ["payload_reset_requires_validation"]);

    statusBox.textContent = "Example Entra ID payload restored. Validate before ingesting.";
    statusBox.className = "success";

    addActivity("[Entra ID] Example payload restored");
}


function clearEntraPayload() {
    const input = document.getElementById('entra_json_input');
    const statusBox = document.getElementById('entra_ingest_status');

    input.value = "";
    setEntraIngestEnabled(false);
    showEntraValidationResult(false, ["payload_cleared"]);

    statusBox.textContent = "Entra ID payload cleared. Validate before ingesting.";
    statusBox.className = "success";

    addActivity("[Entra ID] Payload cleared");
}


function formatEntraPayload() {
    const input = document.getElementById('entra_json_input');
    const statusBox = document.getElementById('entra_ingest_status');

    try {
        const payload = JSON.parse(input.value);
        input.value = JSON.stringify(payload, null, 2);
        setEntraIngestEnabled(false);
        showEntraValidationResult(false, ["payload_formatted_requires_validation"]);

        statusBox.textContent = "Entra ID payload formatted. Validate before ingesting.";
        statusBox.className = "success";

        addActivity("[Entra ID] Payload formatted");
    } catch (error) {
        setEntraIngestEnabled(false);
        showEntraValidationResult(false, ["invalid_json"]);

        statusBox.textContent = "Cannot format invalid JSON.";
        statusBox.className = "error";

        addActivity("[Entra ID] Payload format failed: invalid JSON");
    }
}


function showEntraIngestionResult(data) {
    const card = document.getElementById('entra_result_card');
    const title = document.getElementById('entra_result_title');

    card.classList.remove('hidden');

    if (data.status === "ingested") {
        title.textContent = "✓ Entra ID Ingestion Successful";
        title.className = "result-title success";

        document.getElementById('entra_result_source').textContent =
            data.source_system || "entra";

        document.getElementById('entra_result_events').textContent =
            data.events_normalized;

        document.getElementById('entra_result_snapshot_status').textContent =
            data.snapshot_status;

        document.getElementById('entra_result_strategy').textContent =
            data.selected_strategy;

        document.getElementById('entra_result_kernel_decision').textContent =
            data.kernel_decision;

        document.getElementById('entra_result_reason').textContent =
            formatEntraErrors(data.reason);
    } else {
        title.textContent = "✕ Entra ID Ingestion Failed";
        title.className = "result-title error";

        document.getElementById('entra_result_source').textContent = "entra";
        document.getElementById('entra_result_events').textContent = "0";
        document.getElementById('entra_result_snapshot_status').textContent = "N/A";
        document.getElementById('entra_result_strategy').textContent = "N/A";
        document.getElementById('entra_result_kernel_decision').textContent = "N/A";
        document.getElementById('entra_result_reason').textContent =
            formatEntraErrors(data.errors || data);
    }
}


async function ingestEntraEvidence() {
    const input = document.getElementById('entra_json_input');
    const statusBox = document.getElementById('entra_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        const errors = ["invalid_json"];

        setEntraIngestEnabled(false);
        showEntraValidationResult(false, errors);

        statusBox.textContent = "Invalid JSON. Please check the payload.";
        statusBox.className = "error";

        addActivity("[Entra ID] Evidence import failed: invalid JSON");

        showEntraIngestionResult({
            status: "failed",
            errors: errors,
        });

        return;
    }

    statusBox.textContent = "Ingesting Entra ID evidence...";
    statusBox.className = "";

    const response = await fetch('/ingest/entra', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    const data = await response.json();

    showEntraIngestionResult(data);

    if (data.status === "ingested") {
        setEntraIngestEnabled(false);

        statusBox.textContent =
            `Entra ID ingest complete: ${data.events_normalized} events processed. Validate again before the next ingest.`;

        statusBox.className = "success";

        addActivity("[Entra ID] Evidence ingested");
        addActivity(`[Entra ID] ${data.events_normalized} events normalized`);
        addActivity(`[Entra ID] Snapshot ${data.snapshot_status}`);
        addActivity(`[Kernel] Strategy selected: ${data.selected_strategy}`);

        await refreshConsole();
    } else {
        setEntraIngestEnabled(false);

        statusBox.textContent = "Entra ID ingest failed.";
        statusBox.className = "error";

        addActivity("[Entra ID] Evidence import failed");
    }
}


document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('entra_json_input');

    if (!input) {
        return;
    }

    input.addEventListener('input', () => {
        setEntraIngestEnabled(false);
        showEntraValidationResult(false, ["payload_changed_requires_validation"]);

        const statusBox = document.getElementById('entra_ingest_status');

        if (statusBox) {
            statusBox.textContent = "Payload changed. Validate before ingesting.";
            statusBox.className = "";
        }
    });
});