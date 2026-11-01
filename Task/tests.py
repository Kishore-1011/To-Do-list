from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import TaskForm
from .models import Task

PASSWORD = 'Str0ng-pass-2026'


def make_task(user, **kwargs):
    defaults = {'name': 'Sample task', 'category': 'H'}
    defaults.update(kwargs)
    return Task.objects.create(user=user, **defaults)


class TaskModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('asha', password=PASSWORD)
        self.today = timezone.localdate()

    def test_task_numbers_count_up_per_user(self):
        other = User.objects.create_user('bob', password=PASSWORD)
        first = make_task(self.user)
        second = make_task(self.user)
        others_first = make_task(other)
        self.assertEqual((first.task_number, second.task_number), (1, 2))
        self.assertEqual(others_first.task_number, 1)

    def test_defaults(self):
        task = make_task(self.user)
        self.assertEqual(task.status, Task.Status.TODO)
        self.assertEqual(task.priority, Task.Priority.MEDIUM)
        self.assertIsNone(task.completed_at)

    def test_completed_at_is_set_and_cleared(self):
        task = make_task(self.user)
        task.status = Task.Status.COMPLETED
        task.save()
        self.assertIsNotNone(task.completed_at)
        task.status = Task.Status.IN_PROGRESS
        task.save()
        self.assertIsNone(task.completed_at)

    def test_due_states(self):
        cases = [
            (self.today - timedelta(days=1), 'overdue'),
            (self.today, 'today'),
            (self.today + timedelta(days=Task.DUE_SOON_DAYS), 'soon'),
            (self.today + timedelta(days=Task.DUE_SOON_DAYS + 1), ''),
            (None, ''),
        ]
        for due_date, expected in cases:
            with self.subTest(due_date=due_date):
                self.assertEqual(make_task(self.user, due_date=due_date).due_state, expected)

    def test_completed_task_is_never_overdue(self):
        task = make_task(self.user, due_date=self.today - timedelta(days=3), status=Task.Status.COMPLETED)
        self.assertEqual(task.due_state, '')


class TaskFormTests(TestCase):
    def test_description_and_due_date_are_optional(self):
        form = TaskForm(data={'name': 'Pay rent', 'category': 'H', 'priority': 2, 'status': 'todo'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_required_fields(self):
        form = TaskForm(data={})
        self.assertFalse(form.is_valid())
        self.assertTrue({'name', 'category', 'priority', 'status'} <= set(form.errors))

    def test_invalid_fields_are_marked_for_bootstrap(self):
        form = TaskForm(data={})
        form.is_valid()
        self.assertIn('is-invalid', form.fields['name'].widget.attrs['class'])


class AuthViewTests(TestCase):
    def test_register_logs_in_and_redirects(self):
        response = self.client.post(reverse('register'), {
            'username': 'asha', 'password1': PASSWORD, 'password2': PASSWORD,
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), User.objects.get(username='asha').id)

    def test_register_shows_errors(self):
        response = self.client.post(reverse('register'), {
            'username': 'asha', 'password1': 'abc', 'password2': 'abd',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'invalid-feedback')

    def test_login_follows_safe_next_only(self):
        User.objects.create_user('asha', password=PASSWORD)
        response = self.client.post(reverse('my-login'), {
            'username': 'asha', 'password': PASSWORD, 'next': reverse('board'),
        })
        self.assertRedirects(response, reverse('board'))

        self.client.logout()
        response = self.client.post(reverse('my-login'), {
            'username': 'asha', 'password': PASSWORD, 'next': 'https://evil.example.com/',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_wrong_password_shows_message(self):
        User.objects.create_user('asha', password=PASSWORD)
        response = self.client.post(reverse('my-login'), {'username': 'asha', 'password': 'wrong'})
        self.assertContains(response, 'Please enter a correct username and password')

    def test_logout_requires_post(self):
        User.objects.create_user('asha', password=PASSWORD)
        self.client.login(username='asha', password=PASSWORD)
        self.assertEqual(self.client.get(reverse('user-logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('user-logout')), reverse('my-login'))

    def test_pages_require_login(self):
        for name in ['dashboard', 'board', 'create-task']:
            with self.subTest(page=name):
                url = reverse(name)
                self.assertRedirects(self.client.get(url), f"{reverse('my-login')}?next={url}")


class TaskViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('asha', password=PASSWORD)
        self.client.login(username='asha', password=PASSWORD)
        self.today = timezone.localdate()

    def test_create_task(self):
        response = self.client.post(reverse('create-task'), {
            'name': 'Write report', 'category': 'O', 'priority': 3, 'status': 'todo',
            'due_date': self.today.isoformat(), 'description': '',
        })
        self.assertRedirects(response, reverse('dashboard'))
        task = Task.objects.get()
        self.assertEqual((task.user, task.priority, task.due_date), (self.user, 3, self.today))

    def test_create_from_board_column_preselects_status(self):
        response = self.client.get(reverse('create-task') + '?status=on_hold')
        self.assertEqual(response.context['form'].initial['status'], 'on_hold')

    def test_update_task_and_return_to_next(self):
        task = make_task(self.user)
        response = self.client.post(reverse('update-task', args=[task.id]), {
            'name': 'Renamed', 'category': 'S', 'priority': 1, 'status': 'in_progress',
            'next': reverse('board'),
        })
        self.assertRedirects(response, reverse('board'))
        task.refresh_from_db()
        self.assertEqual((task.name, task.status), ('Renamed', 'in_progress'))

    def test_unsafe_next_is_not_rendered(self):
        task = make_task(self.user)
        response = self.client.get(reverse('update-task', args=[task.id]) + '?next=javascript:alert(1)')
        self.assertNotContains(response, 'javascript:alert')

    def test_delete_needs_confirmation(self):
        task = make_task(self.user)
        response = self.client.get(reverse('delete-task', args=[task.id]))
        self.assertContains(response, 'Delete this task?')
        self.assertTrue(Task.objects.filter(id=task.id).exists())
        self.client.post(reverse('delete-task', args=[task.id]))
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_toggle_complete(self):
        task = make_task(self.user)
        url = reverse('toggle-complete', args=[task.id])
        self.assertEqual(self.client.get(url).status_code, 405)

        self.client.post(url)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.COMPLETED)

        self.client.post(url)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.TODO)

    def test_status_update_returns_json_for_board(self):
        task = make_task(self.user)
        response = self.client.post(reverse('update-status', args=[task.id]), {'status': 'completed'},
                                    HTTP_ACCEPT='application/json')
        self.assertEqual(response.json()['status_label'], 'Completed')
        task.refresh_from_db()
        self.assertIsNotNone(task.completed_at)

    def test_status_update_rejects_invalid_status(self):
        task = make_task(self.user)
        response = self.client.post(reverse('update-status', args=[task.id]), {'status': 'done-ish'},
                                    HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 400)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.TODO)

    def test_status_update_form_post_redirects_back(self):
        task = make_task(self.user)
        response = self.client.post(reverse('update-status', args=[task.id]),
                                    {'status': 'on_hold', 'next': reverse('board')})
        self.assertRedirects(response, reverse('board'))

    def test_xss_in_task_name_is_escaped(self):
        make_task(self.user, name='<script>alert(1)</script>')
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('asha', password=PASSWORD)
        self.client.login(username='asha', password=PASSWORD)
        today = timezone.localdate()
        self.overdue = make_task(self.user, name='Write report', category='O', priority=3,
                                 due_date=today - timedelta(days=2))
        self.today_task = make_task(self.user, name='Call bank', category='H', due_date=today)
        self.later = make_task(self.user, name='Read chapter', category='S', priority=1,
                               due_date=today + timedelta(days=10))
        self.done = make_task(self.user, name='Pay bill', category='H', status=Task.Status.COMPLETED,
                              due_date=today - timedelta(days=5))

    def names(self, **params):
        response = self.client.get(reverse('dashboard'), params)
        return [task.name for task in response.context['records']]

    def test_stats(self):
        stats = self.client.get(reverse('dashboard')).context['stats']
        self.assertEqual(stats, {'total': 4, 'open': 3, 'completed': 1, 'overdue': 1, 'percent_done': 25})

    def test_due_badges_shown(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Overdue ·')
        self.assertContains(response, 'Due today')

    def test_filters(self):
        self.assertEqual(self.names(status='overdue'), ['Write report'])
        self.assertEqual(self.names(status='completed'), ['Pay bill'])
        self.assertEqual(len(self.names(status='open')), 3)
        self.assertEqual(self.names(priority='3'), ['Write report'])
        self.assertEqual(set(self.names(category='H')), {'Call bank', 'Pay bill'})
        self.assertEqual(self.names(q='chapter'), ['Read chapter'])

    def test_default_sort_is_due_date_with_completed_last(self):
        self.assertEqual(self.names(), ['Write report', 'Call bank', 'Read chapter', 'Pay bill'])

    def test_sort_by_priority(self):
        self.assertEqual(self.names(sort='priority')[0], 'Write report')

    def test_unknown_filter_values_are_ignored(self):
        self.assertEqual(len(self.names(status='zzz', priority='9', category='Q', sort='evil')), 4)

    def test_board_groups_by_status(self):
        columns = self.client.get(reverse('board')).context['columns']
        self.assertEqual([c['status'] for c in columns], ['todo', 'in_progress', 'on_hold', 'completed'])
        self.assertEqual(len(columns[0]['tasks']), 3)
        self.assertEqual([t.name for t in columns[3]['tasks']], ['Pay bill'])

    def test_board_category_filter(self):
        columns = self.client.get(reverse('board'), {'category': 'O'}).context['columns']
        self.assertEqual([t.name for c in columns for t in c['tasks']], ['Write report'])


class OwnershipTests(TestCase):
    """Users can never see or change each other's tasks."""

    def setUp(self):
        alice = User.objects.create_user('alice', password=PASSWORD)
        User.objects.create_user('bob', password=PASSWORD)
        self.task = make_task(alice, name='Alice private task')
        self.client.login(username='bob', password=PASSWORD)

    def test_other_users_get_404(self):
        urls = [
            ('get', reverse('update-task', args=[self.task.id])),
            ('post', reverse('update-task', args=[self.task.id])),
            ('get', reverse('delete-task', args=[self.task.id])),
            ('post', reverse('delete-task', args=[self.task.id])),
            ('post', reverse('toggle-complete', args=[self.task.id])),
            ('post', reverse('update-status', args=[self.task.id])),
        ]
        for method, url in urls:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, {'status': 'completed', 'name': 'HACKED'})
                self.assertEqual(response.status_code, 404)
        self.task.refresh_from_db()
        self.assertEqual((self.task.name, self.task.status), ('Alice private task', Task.Status.TODO))

    def test_other_users_tasks_not_listed(self):
        self.assertNotContains(self.client.get(reverse('dashboard')), 'Alice private task')
        self.assertNotContains(self.client.get(reverse('board')), 'Alice private task')

    def test_post_without_csrf_token_is_blocked(self):
        self.client.handler.enforce_csrf_checks = True
        self.client.login(username='alice', password=PASSWORD)
        response = self.client.post(reverse('toggle-complete', args=[self.task.id]))
        self.assertEqual(response.status_code, 403)
