const SENTINELONE_EXAMPLE_PAYLOAD = `{
  "events": [
    {
      "id": "s1-ui-001",
      "eventType": "threat_detected",
      "threatName": "Suspicious PowerShell",
      "classification": "malware",
      "confidenceLevel": "high",
      "mitigationStatus": "not_mitigated",
      "incidentStatus": "unresolved",
      "createdAt": "2026-07-08T12:00:00Z"
    },
    {
      "id": "s1-ui-002",
      "eventType": "agent_online",
      "agentName": "workstation-001",
      "createdAt": "2026-07-08T12:05:00Z"
    }
  ]
}`;


function setSentinelOneIngestEnabled(isEnabled) {
    const ingestButton = document.getElementById('sentinelone_ingest_button');

    if (!ingestButton) {
        return;
    }

    ingestButton.disabled = !isEnabled;
}


function formatSentinelOneErrors(errors) {
    if (Array.isArray(errors)) {
        return errors.join(", ");
    }

    return JSON.stringify(errors);
}


function showSentinelOneValidationResult(isValid, errors) {
    const card = document.getElementById('sentinelone_validation_card');
    const title = document.getElementById('sentinelone_validation_title');
    const status = document.getElementById('sentinelone_validation_status');
    const errorCount = document.getElementById('sentinelone_validation_error_count');
    const details = document.getElementById('sentinelone_validation_details');

    if (card) {
        card.classList.remove('hidden');
    }

    if (!title || !status || !errorCount || !details) {
        return;
    }

    if (isValid) {
        title.textContent = "✓ SentinelOne Payload Validation Passed";
        title.className = "result-title success";

        status.textContent = "Valid";
        errorCount.textContent = "0";
        details.textContent = "Payload is valid and ready for ingestion.";
        return;
    }

    title.textContent = "✕ SentinelOne Payload Validation Failed";
    title.className = "result-title error";

    status.textContent = "Invalid";
    errorCount.textContent = errors.length;
    details.textContent = errors.join(", ");
}


function getSentinelOnePayloadValidationErrors(payload) {
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

        if (!event.eventType) {
            errors.push(`event_${index}_missing_eventType`);
        }

        if (!event.createdAt) {
            errors.push(`event_${index}_missing_createdAt`);
        }
    });

    return errors;
}


function validateSentinelOnePayload() {
    const input = document.getElementById('sentinelone_json_input');
    const statusBox = document.getElementById('sentinelone_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        const errors = ["invalid_json"];

        setSentinelOneIngestEnabled(false);
        showSentinelOneValidationResult(false, errors);

        statusBox.textContent = "Payload validation failed: invalid JSON.";
        statusBox.className = "error";

        addActivity("[SentinelOne] Payload validation failed: invalid JSON");
        return false;
    }

    const errors = getSentinelOnePayloadValidationErrors(payload);

    if (errors.length > 0) {
        setSentinelOneIngestEnabled(false);
        showSentinelOneValidationResult(false, errors);

        statusBox.textContent = `Payload validation failed: ${errors.join(", ")}.`;
        statusBox.className = "error";

        addActivity("[SentinelOne] Payload validation failed");
        return false;
    }

    setSentinelOneIngestEnabled(true);
    showSentinelOneValidationResult(true, []);

    statusBox.textContent = "Payload validation passed. Ingest is now enabled.";
    statusBox.className = "success";

    addActivity("[SentinelOne] Payload validation passed");

    return true;
}


function resetSentinelOneExamplePayload() {
    const input = document.getElementById('sentinelone_json_input');
    const statusBox = document.getElementById('sentinelone_ingest_status');

    input.value = SENTINELONE_EXAMPLE_PAYLOAD;
    setSentinelOneIngestEnabled(false);
    showSentinelOneValidationResult(false, ["payload_reset_requires_validation"]);

    statusBox.textContent = "Example SentinelOne payload restored. Validate before ingesting.";
    statusBox.className = "success";

    addActivity("[SentinelOne] Example payload restored");
}


function clearSentinelOnePayload() {
    const input = document.getElementById('sentinelone_json_input');
    const statusBox = document.getElementById('sentinelone_ingest_status');

    input.value = "";
    setSentinelOneIngestEnabled(false);
    showSentinelOneValidationResult(false, ["payload_cleared"]);

    statusBox.textContent = "SentinelOne payload cleared. Validate before ingesting.";
    statusBox.className = "success";

    addActivity("[SentinelOne] Payload cleared");
}


function formatSentinelOnePayload() {
    const input = document.getElementById('sentinelone_json_input');
    const statusBox = document.getElementById('sentinelone_ingest_status');

    try {
        const payload = JSON.parse(input.value);
        input.value = JSON.stringify(payload, null, 2);
        setSentinelOneIngestEnabled(false);
        showSentinelOneValidationResult(false, ["payload_formatted_requires_validation"]);

        statusBox.textContent = "SentinelOne payload formatted. Validate before ingesting.";
        statusBox.className = "success";

        addActivity("[SentinelOne] Payload formatted");
    } catch (error) {
        setSentinelOneIngestEnabled(false);
        showSentinelOneValidationResult(false, ["invalid_json"]);

        statusBox.textContent = "Cannot format invalid JSON.";
        statusBox.className = "error";

        addActivity("[SentinelOne] Payload format failed: invalid JSON");
    }
}


function showSentinelOneIngestionResult(data) {
    const card = document.getElementById('sentinelone_result_card');
    const title = document.getElementById('sentinelone_result_title');

    card.classList.remove('hidden');

    if (data.status === "ingested") {
        title.textContent = "✓ SentinelOne Ingestion Successful";
        title.className = "result-title success";

        document.getElementById('sentinelone_result_source').textContent =
            data.source_system || "sentinelone";

        document.getElementById('sentinelone_result_events').textContent =
            data.events_normalized;

        document.getElementById('sentinelone_result_snapshot_status').textContent =
            data.snapshot_status;

        document.getElementById('sentinelone_result_strategy').textContent =
            data.selected_strategy;

        document.getElementById('sentinelone_result_kernel_decision').textContent =
            data.kernel_decision;

        document.getElementById('sentinelone_result_reason').textContent =
            formatSentinelOneErrors(data.reason);
    } else {
        title.textContent = "✕ SentinelOne Ingestion Failed";
        title.className = "result-title error";

        document.getElementById('sentinelone_result_source').textContent = "sentinelone";
        document.getElementById('sentinelone_result_events').textContent = "0";
        document.getElementById('sentinelone_result_snapshot_status').textContent = "N/A";
        document.getElementById('sentinelone_result_strategy').textContent = "N/A";
        document.getElementById('sentinelone_result_kernel_decision').textContent = "N/A";
        document.getElementById('sentinelone_result_reason').textContent =
            formatSentinelOneErrors(data.errors || data);
    }
}


async function ingestSentinelOneEvidence() {
    const input = document.getElementById('sentinelone_json_input');
    const statusBox = document.getElementById('sentinelone_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        const errors = ["invalid_json"];

        setSentinelOneIngestEnabled(false);
        showSentinelOneValidationResult(false, errors);

        statusBox.textContent = "Invalid JSON. Please check the payload.";
        statusBox.className = "error";

        addActivity("[SentinelOne] Evidence import failed: invalid JSON");

        showSentinelOneIngestionResult({
            status: "failed",
            errors: errors,
        });

        return;
    }

    statusBox.textContent = "Ingesting SentinelOne evidence...";
    statusBox.className = "";

    const response = await fetch('/ingest/sentinelone', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    const data = await response.json();

    showSentinelOneIngestionResult(data);

    if (data.status === "ingested") {
        setSentinelOneIngestEnabled(false);

        statusBox.textContent =
            `SentinelOne ingest complete: ${data.events_normalized} events processed. Validate again before the next ingest.`;

        statusBox.className = "success";

        addActivity("[SentinelOne] Evidence ingested");
        addActivity(`[SentinelOne] ${data.events_normalized} events normalized`);
        addActivity(`[SentinelOne] Snapshot ${data.snapshot_status}`);
        addActivity(`[Kernel] Strategy selected: ${data.selected_strategy}`);

        await refreshConsole();
    } else {
        setSentinelOneIngestEnabled(false);

        statusBox.textContent = "SentinelOne ingest failed.";
        statusBox.className = "error";

        addActivity("[SentinelOne] Evidence import failed");
    }
}


document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('sentinelone_json_input');

    if (!input) {
        return;
    }

    input.addEventListener('input', () => {
        setSentinelOneIngestEnabled(false);
        showSentinelOneValidationResult(false, ["payload_changed_requires_validation"]);

        const statusBox = document.getElementById('sentinelone_ingest_status');

        if (statusBox) {
            statusBox.textContent = "Payload changed. Validate before ingesting.";
            statusBox.className = "";
        }
    });
});