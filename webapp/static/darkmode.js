function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const mode = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
    localStorage.setItem('color-mode', mode);
    document.getElementById('mode-toggle').innerText = mode === 'dark' ? 'Light Mode' : 'Dark Mode';
}

document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('color-mode');
    if (saved === 'dark') {
        document.body.classList.add('dark-mode');
    }
    const btn = document.getElementById('mode-toggle');
    if (btn) {
        btn.innerText = document.body.classList.contains('dark-mode') ? 'Light Mode' : 'Dark Mode';
        btn.addEventListener('click', toggleDarkMode);
    }
});
