from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import admin_required
from .models import Feedback
from django.db.models import Avg, Count


@login_required
def submit_feedback(request):
    if request.method == 'POST':
        Feedback.objects.create(
            author=request.user,
            category=request.POST.get('category', 'general'),
            subject=request.POST.get('subject', '').strip(),
            message=request.POST.get('message', '').strip(),
            rating=request.POST.get('rating') or None,
        )
        messages.success(request, "Thank you for your feedback!")
        return redirect('feedback:submit')
    return render(request, 'feedback/submit.html', {'categories': Feedback.Category.choices})


@admin_required
def feedback_report(request):
    feedbacks = Feedback.objects.select_related('author').order_by('-created_at')
    stats = {
        'total': feedbacks.count(),
        'avg_rating': feedbacks.aggregate(avg=Avg('rating'))['avg'],
        'by_category': feedbacks.values('category').annotate(count=Count('id')).order_by('-count'),
        'by_rating': feedbacks.values('rating').annotate(count=Count('id')).order_by('-rating'),
    }
    from django.core.paginator import Paginator
    page = Paginator(feedbacks, 25).get_page(request.GET.get('page', 1))
    return render(request, 'feedback/report.html', {'page_obj': page, 'stats': stats})
