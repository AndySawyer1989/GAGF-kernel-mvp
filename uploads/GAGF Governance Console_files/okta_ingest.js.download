const OKTA_EXAMPLE_PAYLOAD = `{
  "events": [
    {
      "uuid": "okta-ui-001",
      "eventType": "user.authentication.failed",
      "published": "2026-07-08T12:00:00Z",
      "outcome": {
        "result": "FAILURE"
      }
    },
    {
      "uuid": "okta-ui-002",
      "eventType": "user.session.start",
      "published": "2026-07-08T12:05:00Z",
      "outcome": {
        "result": "SUCCESS"
      }
    }
  ]
}`;


function setOktaIngestEnabled(isEnabled) {
    const ingestButton = document.getElementById('okta_ingest_button');

    if (!ingestButton) {
        return;
    }

    ingestButton.disabled = !isEnabled;
}


function formatOktaErrors(errors) {
    if (Array.isArray(errors)) {
        return errors.join(", ");
    }

    return JSON.stringify(errors);
}


function showOktaValidationResult(isValid, errors) {
    const card = document.getElementById('okta_validation_card');
    const title = document.getElementById('okta_validation_title');
    const status = document.getElementById('okta_validation_status');
    const errorCount = document.getElementById('okta_validation_error_count');
    const details = document.getElementById('okta_validation_details');

    if (card) {
        card.classList.remove('hidden');
    }

    if (!title || !status || !errorCount || !details) {
        return;
    }

    if (isValid) {
        title.textContent = "✓ Okta Payload Validation Passed";
        title.className = "result-title success";

        status.textContent = "Valid";
        errorCount.textContent = "0";
        details.textContent = "Payload is valid and ready for ingestion.";
        return;
    }

    title.textContent = "✕ Okta Payload Validation Failed";
    title.className = "result-title error";

    status.textContent = "Invalid";
    errorCount.textContent = errors.length;
    details.textContent = errors.join(", ");
}


function getOktaPayloadValidationErrors(payload) {
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

        if (!event.uuid) {
            errors.push(`event_${index}_missing_uuid`);
        }

        if (!event.eventType) {
            errors.push(`event_${index}_missing_eventType`);
        }

        if (!event.published) {
            errors.push(`event_${index}_missing_published`);
        }
    });

    return errors;
}


function validateOktaPayload() {
    const input = document.getElementById('okta_json_input');
    const statusBox = document.getElementById('okta_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        const errors = ["invalid_json"];

        setOktaIngestEnabled(false);
        showOktaValidationResult(false, errors);

        statusBox.textContent = "Payload validation failed: invalid JSON.";
        statusBox.className = "error";

        addActivity("[Okta] Payload validation failed: invalid JSON");
        return false;
    }

    const errors = getOktaPayloadValidationErrors(payload);

    if (errors.length > 0) {
        setOktaIngestEnabled(false);
        showOktaValidationResult(false, errors);

        statusBox.textContent = `Payload validation failed: ${errors.join(", ")}.`;
        statusBox.className = "error";

        addActivity("[Okta] Payload validation failed");
        return false;
    }

    setOktaIngestEnabled(true);
    showOktaValidationResult(true, []);

    statusBox.textContent = "Payload validation passed. Ingest is now enabled.";
    statusBox.className = "success";

    addActivity("[Okta] Payload validation passed");

    return true;
}


function resetOktaExamplePayload() {
    const input = document.getElementById('okta_json_input');
    const statusBox = document.getElementById('okta_ingest_status');

    input.value = OKTA_EXAMPLE_PAYLOAD;
    setOktaIngestEnabled(false);
    showOktaValidationResult(false, ["payload_reset_requires_validation"]);

    statusBox.textContent = "Example Okta payload restored. Validate before ingesting.";
    statusBox.className = "success";

    addActivity("[Okta] Example payload restored");
}


function clearOktaPayload() {
    const input = document.getElementById('okta_json_input');
    const statusBox = document.getElementById('okta_ingest_status');

    input.value = "";
    setOktaIngestEnabled(false);
    showOktaValidationResult(false, ["payload_cleared"]);

    statusBox.textContent = "Okta payload cleared. Validate before ingesting.";
    statusBox.className = "success";

    addActivity("[Okta] Payload cleared");
}


function formatOktaPayload() {
    const input = document.getElementById('okta_json_input');
    const statusBox = document.getElementById('okta_ingest_status');

    try {
        const payload = JSON.parse(input.value);
        input.value = JSON.stringify(payload, null, 2);
        setOktaIngestEnabled(false);
        showOktaValidationResult(false, ["payload_formatted_requires_validation"]);

        statusBox.textContent = "Okta payload formatted. Validate before ingesting.";
        statusBox.className = "success";

        addActivity("[Okta] Payload formatted");
    } catch (error) {
        setOktaIngestEnabled(false);
        showOktaValidationResult(false, ["invalid_json"]);

        statusBox.textContent = "Cannot format invalid JSON.";
        statusBox.className = "error";

        addActivity("[Okta] Payload format failed: invalid JSON");
    }
}


function showOktaIngestionResult(data) {
    const card = document.getElementById('okta_result_card');
    const title = document.getElementById('okta_result_title');

    card.classList.remove('hidden');

    if (data.status === "ingested") {
        title.textContent = "✓ Okta Ingestion Successful";
        title.className = "result-title success";

        document.getElementById('okta_result_source').textContent =
            data.source_system || "okta";

        document.getElementById('okta_result_events').textContent =
            data.events_normalized;

        document.getElementById('okta_result_snapshot_status').textContent =
            data.snapshot_status;

        document.getElementById('okta_result_strategy').textContent =
            data.selected_strategy;

        document.getElementById('okta_result_kernel_decision').textContent =
            data.kernel_decision;

        document.getElementById('okta_result_reason').textContent =
            formatOktaErrors(data.reason);
    } else {
        title.textContent = "✕ Okta Ingestion Failed";
        title.className = "result-title error";

        document.getElementById('okta_result_source').textContent = "okta";
        document.getElementById('okta_result_events').textContent = "0";
        document.getElementById('okta_result_snapshot_status').textContent = "N/A";
        document.getElementById('okta_result_strategy').textContent = "N/A";
        document.getElementById('okta_result_kernel_decision').textContent = "N/A";
        document.getElementById('okta_result_reason').textContent =
            formatOktaErrors(data.errors || data);
    }
}


async function ingestOktaEvidence() {
    const input = document.getElementById('okta_json_input');
    const statusBox = document.getElementById('okta_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        const errors = ["invalid_json"];

        setOktaIngestEnabled(false);
        showOktaValidationResult(false, errors);

        statusBox.textContent = "Invalid JSON. Please check the payload.";
        statusBox.className = "error";

        addActivity("[Okta] Evidence import failed: invalid JSON");

        showOktaIngestionResult({
            status: "failed",
            errors: errors,
        });

        return;
    }

    statusBox.textContent = "Ingesting Okta evidence...";
    statusBox.className = "";

    const response = await fetch('/ingest/okta', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    const data = await response.json();

    showOktaIngestionResult(data);

    if (data.status === "ingested") {
        setOktaIngestEnabled(false);

        statusBox.textContent =
            `Okta ingest complete: ${data.events_normalized} events processed. Validate again before the next ingest.`;

        statusBox.className = "success";

        addActivity("[Okta] Evidence ingested");
        addActivity(`[Okta] ${data.events_normalized} events normalized`);
        addActivity(`[Okta] Snapshot ${data.snapshot_status}`);
        addActivity(`[Kernel] Strategy selected: ${data.selected_strategy}`);

        await refreshConsole();
    } else {
        setOktaIngestEnabled(false);

        statusBox.textContent = "Okta ingest failed.";
        statusBox.className = "error";

        addActivity("[Okta] Evidence import failed");
    }
}


document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('okta_json_input');

    if (!input) {
        return;
    }

    input.addEventListener('input', () => {
        setOktaIngestEnabled(false);
        showOktaValidationResult(false, ["payload_changed_requires_validation"]);

        const statusBox = document.getElementById('okta_ingest_status');

        if (statusBox) {
            statusBox.textContent = "Payload changed. Validate before ingesting.";
            statusBox.className = "";
        }
    });
});