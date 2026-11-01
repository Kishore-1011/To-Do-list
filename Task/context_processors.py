from django.db.models import Count, Q
from django.utils import timezone

from .models import Task


def sidebar(request):
    """Task counts shown in the app sidebar on every logged-in page."""
    if not request.user.is_authenticated:
        return {}

    today = timezone.localdate()
    is_open = ~Q(status=Task.Status.COMPLETED)
    counts = Task.objects.filter(user=request.user).aggregate(
        open=Count('id', filter=is_open),
        today=Count('id', filter=is_open & Q(due_date__lte=today)),
        upcoming=Count('id', filter=is_open & Q(due_date__gt=today)),
        completed=Count('id', filter=Q(status=Task.Status.COMPLETED)),
        home=Count('id', filter=is_open & Q(category='H')),
        school=Count('id', filter=is_open & Q(category='S')),
        office=Count('id', filter=is_open & Q(category='O')),
    )
    categories = [
        {'code': 'H', 'label': 'Home', 'style': 'home', 'total': counts['home']},
        {'code': 'S', 'label': 'School', 'style': 'school', 'total': counts['school']},
        {'code': 'O', 'label': 'Office', 'style': 'office', 'total': counts['office']},
    ]
    return {'sidebar_counts': counts, 'sidebar_categories': categories}
