// Show a notification toast; Bootstrap hides it after its data-bs-delay
function showToast(text, variant) {
    var area = document.getElementById('toast-area');
    if (!area) {
        return;
    }
    var toast = document.createElement('div');
    toast.className = 'toast app-toast align-items-center border-0';
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.setAttribute('aria-atomic', 'true');
    toast.dataset.bsDelay = '3000';

    var row = document.createElement('div');
    row.className = 'd-flex align-items-center';
    var body = document.createElement('div');
    body.className = 'toast-body d-flex align-items-center gap-2';
    var icon = document.createElement('i');
    icon.className = variant === 'danger' ? 'bi bi-x-circle-fill text-danger' : 'bi bi-check-circle-fill text-success';
    body.appendChild(icon);
    body.appendChild(document.createTextNode(text));
    var close = document.createElement('button');
    close.type = 'button';
    close.className = 'btn-close me-2 m-auto';
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

// Filter dropdowns apply as soon as they change
document.querySelectorAll('form[data-auto-submit] select').forEach(function (select) {
    select.addEventListener('change', function () { select.form.requestSubmit(); });
});

// Press "/" anywhere to jump to search
var searchInput = document.getElementById('app-search-input');
if (searchInput) {
    document.addEventListener('keydown', function (event) {
        var tag = (event.target.tagName || '').toLowerCase();
        var typing = tag === 'input' || tag === 'textarea' || tag === 'select' || event.target.isContentEditable;
        if (event.key === '/' && !typing) {
            event.preventDefault();
            searchInput.focus();
        }
    });
}
