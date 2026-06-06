from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    # Mark all as read on viewing
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
    from django.core.paginator import Paginator
    paginator = Paginator(notifications, 20)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'notifications/list.html', {'page_obj': page})


@login_required
def mark_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, recipient=request.user)
    n.is_read = True
    n.read_at = timezone.now()
    n.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    return redirect(n.action_url or 'notifications:list')


@login_required
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
    return redirect('notifications:list')
