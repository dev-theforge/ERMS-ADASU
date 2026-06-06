from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import admin_required, student_required
from apps.accounts.models import CustomUser
from apps.results.models import Result
from apps.notifications.models import Notification
from apps.audit.models import AuditLog
from .models import Complaint, ComplaintComment


@student_required
def submit_complaint(request):
    student = request.user.student_profile
    published_results = Result.objects.filter(student=student, status='published').select_related('course', 'semester__session')

    if request.method == 'POST':
        result_id = request.POST.get('result')
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        result = get_object_or_404(Result, pk=result_id, student=student, status='published')

        if not subject or not description:
            messages.error(request, "Subject and description are required.")
        else:
            complaint = Complaint.objects.create(
                student=student, result=result, subject=subject, description=description
            )
            for admin in CustomUser.objects.filter(role='admin', status='active'):
                Notification.notify(admin, 'complaint_update', 'New Complaint Filed',
                                    f'{student.user.get_full_name()} filed a complaint about {result.course.code}.')
            AuditLog.log(request.user, f'Submitted complaint #{complaint.pk}')
            messages.success(request, "Complaint submitted successfully. You will be notified of updates.")
            return redirect('complaints:my_complaints')

    return render(request, 'complaints/submit.html', {'results': published_results})


@student_required
def my_complaints(request):
    student = request.user.student_profile
    complaints = Complaint.objects.filter(student=student).select_related('result__course', 'result__semester__session').order_by('-created_at')
    return render(request, 'complaints/my_complaints.html', {'complaints': complaints})


@student_required
def complaint_detail(request, pk):
    student = request.user.student_profile
    complaint = get_object_or_404(Complaint, pk=pk, student=student)
    comments = complaint.comments.select_related('author').all()
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            ComplaintComment.objects.create(complaint=complaint, author=request.user, content=content)
            messages.success(request, "Comment added.")
        return redirect('complaints:detail', pk=pk)
    return render(request, 'complaints/detail.html', {'complaint': complaint, 'comments': comments})


# ─── ADMIN COMPLAINT VIEWS ─────────────────────────────────────────────────

@admin_required
def admin_complaints(request):
    status_filter = request.GET.get('status', '')
    complaints = Complaint.objects.select_related('student__user', 'result__course', 'result__semester__session', 'reviewed_by').order_by('-created_at')
    if status_filter:
        complaints = complaints.filter(status=status_filter)

    from django.core.paginator import Paginator
    paginator = Paginator(complaints, 25)
    page = paginator.get_page(request.GET.get('page', 1))

    stats = {
        'total': Complaint.objects.count(),
        'pending': Complaint.objects.filter(status='pending').count(),
        'under_review': Complaint.objects.filter(status='under_review').count(),
        'resolved': Complaint.objects.filter(status='resolved').count(),
    }
    return render(request, 'complaints/admin_complaints.html', {
        'page_obj': page, 'stats': stats, 'status_filter': status_filter
    })


@admin_required
def admin_complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    comments = complaint.comments.select_related('author').all()

    if request.method == 'POST':
        action = request.POST.get('action')
        response_text = request.POST.get('admin_response', '').strip()
        new_status = request.POST.get('status', complaint.status)

        if action == 'update':
            complaint.status = new_status
            if response_text:
                complaint.admin_response = response_text
            complaint.reviewed_by = request.user
            if new_status == 'resolved':
                complaint.resolved_at = timezone.now()
            complaint.save()

            Notification.notify(
                complaint.student.user, 'complaint_update',
                f'Complaint Update: {complaint.get_status_display()}',
                f'Your complaint "{complaint.subject}" has been updated to: {complaint.get_status_display()}. {response_text}'
            )
            AuditLog.log(request.user, f'Updated complaint #{pk} to {new_status}')
            messages.success(request, "Complaint updated.")

        comment_text = request.POST.get('comment', '').strip()
        if comment_text:
            ComplaintComment.objects.create(complaint=complaint, author=request.user, content=comment_text)

        return redirect('complaints:admin_detail', pk=pk)

    return render(request, 'complaints/admin_detail.html', {'complaint': complaint, 'comments': comments})
