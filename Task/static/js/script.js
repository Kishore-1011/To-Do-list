// Show a notification toast; Bootstrap hides it after its data-bs-delay
function showToast(text, variant) {
    var area = document.getElementById('toast-area');
    if (!area) {
        return;
    }
    var toast = document.createElement('div');
    toast.className = 'toast align-items-center border-0 text-bg-' + (variant || 'secondary');
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.setAttribute('aria-atomic', 'true');
    toast.dataset.bsDelay = '3000';

    var row = document.createElement('div');
    row.className = 'd-flex';
    var body = document.createElement('div');
    body.className = 'toast-body';
    body.textContent = text;
    var close = document.createElement('button');
    close.type = 'button';
    close.className = 'btn-close btn-close-white me-2 m-auto';
    close.setAttribute('data-bs-dismiss', 'toast');
    close.setAttribute('aria-label', 'Close');

    row.appendChild(body);
    row.appendChild(close);
    toast.appendChild(row);
    area.appendChild(toast);
    toast.addEventListener('hidden.bs.toast', function () { toast.remove(); });
    bootstrap.Toast.getOrCreateInstance(toast).show();
}

// Show notifications sent by the server
document.querySelectorAll('#toast-area .toast').forEach(function (element) {
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

// Filter dropdowns apply as soon as they change (search applies on Enter)
document.querySelectorAll('form[data-auto-submit] select').forEach(function (select) {
    select.addEventListener('change', function () { select.form.requestSubmit(); });
});
