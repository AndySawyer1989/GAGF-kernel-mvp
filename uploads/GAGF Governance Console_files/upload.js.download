function showImportResult(result) {
    const card = document.getElementById('import_result_card');
    const title = document.getElementById('import_result_title');

    if (!card || !title) {
        return;
    }

    card.classList.remove('hidden');

    if (result.status === "ingested" || result.status === "imported") {
        title.textContent = "✓ Import Successful";
        title.className = "result-title success";

        document.getElementById('result_file').textContent =
            result.file || "uploaded_csv";

        document.getElementById('result_events').textContent =
            result.events_normalized || result.events_imported || 0;

        document.getElementById('result_snapshot_status').textContent =
            result.snapshot_status || "N/A";

        document.getElementById('result_strategy').textContent =
            result.selected_strategy || "N/A";

        document.getElementById('result_kernel_decision').textContent =
            result.kernel_decision || "N/A";

        document.getElementById('result_reason').textContent =
            Array.isArray(result.reason)
                ? result.reason.join(", ")
                : JSON.stringify(result.reason || []);
    } else {
        title.textContent = "✕ Import Failed";
        title.className = "result-title error";

        document.getElementById('result_file').textContent =
            result.file || "uploaded_csv";

        document.getElementById('result_events').textContent = "0";
        document.getElementById('result_snapshot_status').textContent = "N/A";
        document.getElementById('result_strategy').textContent = "N/A";
        document.getElementById('result_kernel_decision').textContent = "N/A";
        document.getElementById('result_reason').textContent =
            JSON.stringify(result.errors || result);
    }
}


async function uploadCSV() {
    const fileInput = document.getElementById('csv_file');
    const statusBox = document.getElementById('upload_status');

    if (!fileInput.files.length) {
        statusBox.textContent = "Please choose a CSV file first.";
        addActivity("[CSV] Upload blocked: no file selected");
        return;
    }

    const fileName = fileInput.files[0].name;

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    statusBox.textContent = "Uploading and processing CSV...";

    const response = await fetch('/upload-csv', {
        method: 'POST',
        body: formData
    });

    const data = await response.json();

    data.file = data.file || fileName;

    showImportResult(data);

    if (data.status === "ingested" || data.status === "imported") {
        const eventsProcessed =
            data.events_normalized || data.events_imported || 0;

        statusBox.textContent = "Import complete.";
        statusBox.className = "success";

        addActivity(`[CSV] ${fileName} imported`);
        addActivity(`[CSV] ${eventsProcessed} events normalized`);
        addActivity(`[CSV] Snapshot ${data.snapshot_status}`);
        addActivity(`[Kernel] Strategy selected: ${data.selected_strategy}`);

        await refreshConsole();
    } else {
        statusBox.textContent = "Import failed.";
        statusBox.className = "error";

        addActivity(`[CSV] ${fileName} import failed`);
    }
}