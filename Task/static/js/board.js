// Kanban board: drag cards between columns and save the new status
(function () {
    var board = document.querySelector('.board');
    if (!board || typeof Sortable === 'undefined') {
        return;
    }

    var urlTemplate = board.dataset.statusUrlTemplate;   // e.g. /tasks/0/status/
    var csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]').value;
    var labels = {};
    document.querySelectorAll('.board-column').forEach(function (column) {
        var list = column.querySelector('.board-list');
        labels[list.dataset.status] = column.querySelector('h2').textContent.trim();
    });

    function statusUrl(taskId) {
        return urlTemplate.replace('/0/', '/' + taskId + '/');
    }

    function refreshCounts() {
        document.querySelectorAll('.board-list').forEach(function (list) {
            var count = document.querySelector('[data-count-for="' + list.dataset.status + '"]');
            count.textContent = list.children.length;
        });
    }

    function saveStatus(event) {
        var card = event.item;
        var newStatus = event.to.dataset.status;
        var body = new URLSearchParams({status: newStatus});

        card.classList.add('is-saving');
        fetch(statusUrl(card.dataset.taskId), {
            method: 'POST',
            headers: {'X-CSRFToken': csrfToken, 'Accept': 'application/json'},
            body: body,
            credentials: 'same-origin'
        }).then(function (response) {
            if (!response.ok) {
                throw new Error('Request failed');
            }
            return response.json();
        }).then(function (data) {
            card.classList.toggle('is-completed', data.status === 'completed');
            card.classList.toggle('is-overdue', data.due_state === 'overdue');
            showToast(card.dataset.taskLabel + ' moved to ' + data.status_label + '.', 'success');
        }).catch(function () {
            // Put the card back where it came from
            var reference = event.from.children[event.oldIndex] || null;
            event.from.insertBefore(card, reference);
            refreshCounts();
            showToast('Could not move ' + card.dataset.taskLabel + '. Please try again.', 'danger');
        }).finally(function () {
            card.classList.remove('is-saving');
        });
    }

    document.querySelectorAll('.board-list').forEach(function (list) {
        Sortable.create(list, {
            group: 'tasks',
            animation: 150,
            ghostClass: 'board-ghost',
            dragClass: 'board-dragging',
            filter: '.dropdown, .dropdown-menu',
            preventOnFilter: false,
            delayOnTouchOnly: true,
            delay: 150,
            onEnd: function (event) {
                refreshCounts();
                if (event.from !== event.to) {
                    saveStatus(event);
                }
            }
        });
    });
})();
