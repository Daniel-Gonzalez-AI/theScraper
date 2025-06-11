function toggleDarkMode() {
    document.documentElement.classList.toggle('dark');
    const mode = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    localStorage.setItem('color-mode', mode);
    document.getElementById('mode-toggle').innerText = mode === 'dark' ? 'Light Mode' : 'Dark Mode';
}

document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('color-mode');
    if (saved === 'dark') {
        document.documentElement.classList.add('dark');
    }
    const btn = document.getElementById('mode-toggle');
    if (btn) {
        btn.innerText = document.documentElement.classList.contains('dark') ? 'Light Mode' : 'Dark Mode';
        btn.addEventListener('click', toggleDarkMode);
    }
});
