const SERVICENOW_EXAMPLE_PAYLOAD = `{
  "events": [
    {
      "sys_id": "sn-ui-001",
      "table": "incident",
      "category": "security",
      "state": "new",
      "opened_at": "2026-07-06T12:00:00Z",
      "sys_created_on": "2026-07-06T12:01:00Z"
    },
    {
      "sys_id": "sn-ui-002",
      "table": "change_request",
      "state": "authorize",
      "opened_at": "2026-07-06T13:00:00Z",
      "sys_created_on": "2026-07-06T13:01:00Z"
    }
  ]
}`;


function setServiceNowIngestEnabled(isEnabled) {
    const ingestButton = document.getElementById('servicenow_ingest_button');

    if (!ingestButton) {
        return;
    }

    ingestButton.disabled = !isEnabled;
}


function formatServiceNowErrors(errors) {
    if (Array.isArray(errors)) {
        return errors.join(", ");
    }

    return JSON.stringify(errors);
}


function showServiceNowValidationResult(isValid, errors) {
    const card = document.getElementById('servicenow_validation_card');
    const title = document.getElementById('servicenow_validation_title');
    const status = document.getElementById('servicenow_validation_status');
    const errorCount = document.getElementById('servicenow_validation_error_count');
    const details = document.getElementById('servicenow_validation_details');

    if (card) {
        card.classList.remove('hidden');
    }

    if (!title || !status || !errorCount || !details) {
        return;
    }

    if (isValid) {
        title.textContent = "✓ ServiceNow Payload Validation Passed";
        title.className = "result-title success";

        status.textContent = "Valid";
        errorCount.textContent = "0";
        details.textContent = "Payload is valid and ready for ingestion.";
        return;
    }

    title.textContent = "✕ ServiceNow Payload Validation Failed";
    title.className = "result-title error";

    status.textContent = "Invalid";
    errorCount.textContent = errors.length;
    details.textContent = errors.join(", ");
}


function getServiceNowPayloadValidationErrors(payload) {
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

        if (!event.sys_id) {
            errors.push(`event_${index}_missing_sys_id`);
        }

        if (!event.table) {
            errors.push(`event_${index}_missing_table`);
        }

        if (!event.opened_at && !event.sys_created_on) {
            errors.push(`event_${index}_missing_timestamp`);
        }
    });

    return errors;
}


function validateServiceNowPayload() {
    const input = document.getElementById('servicenow_json_input');
    const statusBox = document.getElementById('servicenow_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        const errors = ["invalid_json"];

        setServiceNowIngestEnabled(false);
        showServiceNowValidationResult(false, errors);

        statusBox.textContent = "Payload validation failed: invalid JSON.";
        statusBox.className = "error";

        addActivity("ServiceNow payload validation failed: invalid JSON");
        return false;
    }

    const errors = getServiceNowPayloadValidationErrors(payload);

    if (errors.length > 0) {
        setServiceNowIngestEnabled(false);
        showServiceNowValidationResult(false, errors);

        statusBox.textContent = `Payload validation failed: ${errors.join(", ")}.`;
        statusBox.className = "error";

        addActivity("ServiceNow payload validation failed");
        return false;
    }

    setServiceNowIngestEnabled(true);
    showServiceNowValidationResult(true, []);

    statusBox.textContent = "Payload validation passed. Ingest is now enabled.";
    statusBox.className = "success";

    addActivity("ServiceNow payload validation passed");

    return true;
}


function resetServiceNowExamplePayload() {
    const input = document.getElementById('servicenow_json_input');
    const statusBox = document.getElementById('servicenow_ingest_status');

    input.value = SERVICENOW_EXAMPLE_PAYLOAD;
    setServiceNowIngestEnabled(false);
    showServiceNowValidationResult(false, ["payload_reset_requires_validation"]);

    statusBox.textContent = "Example ServiceNow payload restored. Validate before ingesting.";
    statusBox.className = "success";

    addActivity("ServiceNow example payload restored");
}


function clearServiceNowPayload() {
    const input = document.getElementById('servicenow_json_input');
    const statusBox = document.getElementById('servicenow_ingest_status');

    input.value = "";
    setServiceNowIngestEnabled(false);
    showServiceNowValidationResult(false, ["payload_cleared"]);

    statusBox.textContent = "ServiceNow payload cleared. Validate before ingesting.";
    statusBox.className = "success";

    addActivity("ServiceNow payload cleared");
}


function formatServiceNowPayload() {
    const input = document.getElementById('servicenow_json_input');
    const statusBox = document.getElementById('servicenow_ingest_status');

    try {
        const payload = JSON.parse(input.value);
        input.value = JSON.stringify(payload, null, 2);
        setServiceNowIngestEnabled(false);
        showServiceNowValidationResult(false, ["payload_formatted_requires_validation"]);

        statusBox.textContent = "ServiceNow payload formatted. Validate before ingesting.";
        statusBox.className = "success";

        addActivity("ServiceNow payload formatted");
    } catch (error) {
        setServiceNowIngestEnabled(false);
        showServiceNowValidationResult(false, ["invalid_json"]);

        statusBox.textContent = "Cannot format invalid JSON.";
        statusBox.className = "error";

        addActivity("ServiceNow payload format failed: invalid JSON");
    }
}


function showServiceNowIngestionResult(data) {
    const card = document.getElementById('servicenow_result_card');
    const title = document.getElementById('servicenow_result_title');

    card.classList.remove('hidden');

    if (data.status === "ingested") {
        title.textContent = "✓ ServiceNow Ingestion Successful";
        title.className = "result-title success";

        document.getElementById('servicenow_result_source').textContent =
            data.source_system || "servicenow";

        document.getElementById('servicenow_result_events').textContent =
            data.events_normalized;

        document.getElementById('servicenow_result_snapshot_status').textContent =
            data.snapshot_status;

        document.getElementById('servicenow_result_strategy').textContent =
            data.selected_strategy;

        document.getElementById('servicenow_result_kernel_decision').textContent =
            data.kernel_decision;

        document.getElementById('servicenow_result_reason').textContent =
            formatServiceNowErrors(data.reason);
    } else {
        title.textContent = "✕ ServiceNow Ingestion Failed";
        title.className = "result-title error";

        document.getElementById('servicenow_result_source').textContent = "servicenow";
        document.getElementById('servicenow_result_events').textContent = "0";
        document.getElementById('servicenow_result_snapshot_status').textContent = "N/A";
        document.getElementById('servicenow_result_strategy').textContent = "N/A";
        document.getElementById('servicenow_result_kernel_decision').textContent = "N/A";
        document.getElementById('servicenow_result_reason').textContent =
            formatServiceNowErrors(data.errors || data);
    }
}


async function ingestServiceNowEvidence() {
    const input = document.getElementById('servicenow_json_input');
    const statusBox = document.getElementById('servicenow_ingest_status');

    let payload;

    try {
        payload = JSON.parse(input.value);
    } catch (error) {
        const errors = ["invalid_json"];

        setServiceNowIngestEnabled(false);
        showServiceNowValidationResult(false, errors);

        statusBox.textContent = "Invalid JSON. Please check the payload.";
        statusBox.className = "error";

        addActivity("ServiceNow evidence import failed: invalid JSON");

        showServiceNowIngestionResult({
            status: "failed",
            errors: errors,
        });

        return;
    }

    statusBox.textContent = "Ingesting ServiceNow evidence...";
    statusBox.className = "";

    const response = await fetch('/ingest/servicenow', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    const data = await response.json();

    showServiceNowIngestionResult(data);

    if (data.status === "ingested") {
        setServiceNowIngestEnabled(false);

        statusBox.textContent =
            `ServiceNow ingest complete: ${data.events_normalized} events processed. Validate again before the next ingest.`;

        statusBox.className = "success";

        addActivity("ServiceNow evidence ingested");
        addActivity(`${data.events_normalized} ServiceNow events normalized`);
        addActivity(`ServiceNow snapshot ${data.snapshot_status}`);
        addActivity(`Kernel selected strategy: ${data.selected_strategy}`);

        await refreshConsole();
    } else {
        setServiceNowIngestEnabled(false);

        statusBox.textContent = "ServiceNow ingest failed.";
        statusBox.className = "error";

        addActivity("ServiceNow evidence import failed");
    }
}


document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('servicenow_json_input');

    if (!input) {
        return;
    }

    input.addEventListener('input', () => {
        setServiceNowIngestEnabled(false);
        showServiceNowValidationResult(false, ["payload_changed_requires_validation"]);

        const statusBox = document.getElementById('servicenow_ingest_status');

        if (statusBox) {
            statusBox.textContent = "Payload changed. Validate before ingesting.";
            statusBox.className = "";
        }
    });
});