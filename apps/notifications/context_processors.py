from .models import Notification


def unread_notifications(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        recent = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
        return {'unread_count': count, 'recent_notifications': recent}
    return {'unread_count': 0, 'recent_notifications': []}
