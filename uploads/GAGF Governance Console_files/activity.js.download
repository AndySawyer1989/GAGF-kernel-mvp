function addActivity(message) {
    const timeline = document.getElementById('activity_timeline');
    const now = new Date().toLocaleTimeString();

    const item = document.createElement('div');
    item.className = 'activity-item';

    item.innerHTML = `
        <div class="activity-time">${now}</div>
        <div class="activity-text">${message}</div>
    `;

    if (timeline.textContent.includes("No activity loaded yet")) {
        timeline.innerHTML = "";
    }

    timeline.prepend(item);
}