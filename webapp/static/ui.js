// UI interactions for spinner and log dropdown
function setupSpinner() {
    const form = document.querySelector('form[action*="scrape_selected"]');
    if (!form) return;
    form.addEventListener('submit', () => {
        const overlay = document.getElementById('spinner-overlay');
        const statusEl = document.getElementById('spinner-status');
        if (overlay) {
            overlay.style.display = 'flex';
            if (statusEl) statusEl.textContent = 'Starting...';
        }
    });
}

function setupLogToggle() {
    const toggleBtn = document.getElementById('toggle-log');
    const logContainer = document.getElementById('log-container');
    const latest = document.getElementById('latest-log');
    if (!toggleBtn || !logContainer) return;
    toggleBtn.addEventListener('click', () => {
        const hidden = logContainer.classList.toggle('hidden');
        if (hidden) {
            toggleBtn.textContent = 'Show Logs';
            if (latest) latest.style.display = 'block';
        } else {
            toggleBtn.textContent = 'Hide Logs';
            if (latest) latest.style.display = 'none';
        }
    });
}

function setupLogStream() {
    const logLines = [];
    const pre = document.getElementById('log-lines');
    const latest = document.getElementById('latest-log');
    const statusEl = document.getElementById('spinner-status');
    if (!pre) return;

    const source = new EventSource('/logs_stream');
    source.onmessage = (e) => {
        logLines.push(e.data);
        if (logLines.length > 10) logLines.shift();
        pre.textContent = logLines.join('\n');
        if (latest) {
            latest.textContent = logLines[logLines.length - 1];
        }
        if (statusEl) {
            statusEl.textContent = parseStatus(logLines[logLines.length - 1]);
        }
    };
}

function parseStatus(logLine) {
    const msg = logLine.split(' - ').slice(2).join(' - ');
    if (msg.includes('Starting link discovery')) return 'Discovering links...';
    if (msg.includes('Found') && msg.includes('links')) return msg;
    if (msg.includes('Starting scraping')) return 'Starting scraping...';
    if (msg.includes('Scraping content from')) return 'Scraping pages...';
    if (msg.includes('Saved content from')) return 'Saving page...';
    if (msg.includes('completed')) return 'Completed.';
    return msg;
}

document.addEventListener('DOMContentLoaded', () => {
    setupSpinner();
    setupLogToggle();
    setupLogStream();
});

