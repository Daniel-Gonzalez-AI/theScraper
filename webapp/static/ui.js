// UI interactions for spinner and log dropdown
function setupSpinner() {
    const form = document.querySelector('form[action*="scrape_selected"]');
    if (!form) return;
    form.addEventListener('submit', () => {
        const overlay = document.getElementById('spinner-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
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

document.addEventListener('DOMContentLoaded', () => {
    setupSpinner();
    setupLogToggle();
});

