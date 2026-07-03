function showImportResult(fileName, data) {
    const card = document.getElementById('import_result_card');
    const title = document.getElementById('import_result_title');

    card.style.display = 'block';

    if (data.status === "ingested") {
        title.textContent = "✓ Import Successful";
        title.className = "result-title success";

        document.getElementById('result_file').textContent = fileName;
        document.getElementById('result_events').textContent = data.events_normalized;
        document.getElementById('result_snapshot_status').textContent = data.snapshot_status;
        document.getElementById('result_strategy').textContent = data.selected_strategy;
        document.getElementById('result_kernel_decision').textContent = data.kernel_decision;
        document.getElementById('result_reason').textContent = data.reason.join(", ");
    } else {
        title.textContent = "✕ Import Failed";
        title.className = "result-title error";

        document.getElementById('result_file').textContent = fileName;
        document.getElementById('result_events').textContent = "0";
        document.getElementById('result_snapshot_status').textContent = "N/A";
        document.getElementById('result_strategy').textContent = "N/A";
        document.getElementById('result_kernel_decision').textContent = "N/A";
        document.getElementById('result_reason').textContent =
            JSON.stringify(data.errors || data);
    }
}

async function uploadCSV() {
    const fileInput = document.getElementById('csv_file');
    const statusBox = document.getElementById('upload_status');

    if (!fileInput.files.length) {
        statusBox.textContent = "Please choose a CSV file first.";
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

    showImportResult(fileName, data);

    if (data.status === "ingested") {
        statusBox.textContent = "Import complete.";

        addActivity(`${fileName} imported`);
        addActivity(`${data.events_normalized} events normalized`);
        addActivity(`Snapshot ${data.snapshot_status}`);
        addActivity(`Kernel selected strategy: ${data.selected_strategy}`);

        await refreshConsole();
    } else {
        statusBox.textContent = "Import failed.";
        addActivity(`${fileName} import failed`);
    }
}