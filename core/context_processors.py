from .models import Notification, User


def wellness_context(request):
    """Global template context for wellness application navigation and stats."""
    context = {
        'ROLES': User.Role,
        'unread_notifications_count': 0,
    }
    if request.user.is_authenticated:
        context['unread_notifications_count'] = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    return context
