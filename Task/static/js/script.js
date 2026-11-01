// Show notification toasts; Bootstrap hides each one after its data-bs-delay
document.querySelectorAll('.toast').forEach(function (element) {
    bootstrap.Toast.getOrCreateInstance(element).show();
});

// Light / dark theme toggle, remembered across visits
var themeToggle = document.getElementById('theme-toggle');
if (themeToggle) {
    themeToggle.addEventListener('click', function () {
        var root = document.documentElement;
        var next = root.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-bs-theme', next);
        localStorage.setItem('theme', next);
    });
}
