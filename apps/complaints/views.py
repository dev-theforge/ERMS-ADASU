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


# ─────────────────────────────────────────────────────────────────────────────
# STUDENT VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@student_required
def submit_complaint(request):
    student          = request.user.student_profile
    published_results = Result.objects.filter(
        student=student, status='published'
    ).select_related('course', 'semester__session').order_by(
        '-semester__session__start_date', 'course__code'
    )

    if request.method == 'POST':
        result_id   = request.POST.get('result')
        subject     = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()

        if not result_id or not subject or not description:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'complaints/submit.html', {'results': published_results})

        result = get_object_or_404(Result, pk=result_id, student=student, status='published')

        complaint = Complaint.objects.create(
            student=student,
            result=result,
            subject=subject,
            description=description,
        )

        # Notify all active administrators
        admins = CustomUser.objects.filter(role='admin', status='active')
        for admin in admins:
            Notification.notify(
                recipient=admin,
                ntype='complaint_update',
                title=f'New Complaint Filed — {result.course.code}',
                message=(
                    f'A new complaint has been filed by {student.user.get_full_name()} '
                    f'({student.matric_number}) regarding their result in '
                    f'{result.course.code} — {result.course.title} '
                    f'for {result.semester}.\n\n'
                    f'Subject: {subject}\n\n'
                    f'Log in to the admin panel to review and respond.'
                ),
                url='/complaints/admin/',
            )

        AuditLog.log(request.user, f'Submitted complaint #{complaint.pk} for {result.course.code}')
        messages.success(
            request,
            "Your complaint has been submitted successfully. "
            "You will be notified by email when the administrator responds."
        )
        return redirect('complaints:my_complaints')

    return render(request, 'complaints/submit.html', {'results': published_results})


@student_required
def my_complaints(request):
    student    = request.user.student_profile
    complaints = Complaint.objects.filter(student=student).select_related(
        'result__course', 'result__semester__session'
    ).order_by('-created_at')
    return render(request, 'complaints/my_complaints.html', {'complaints': complaints})


@student_required
def complaint_detail(request, pk):
    student   = request.user.student_profile
    complaint = get_object_or_404(Complaint, pk=pk, student=student)
    comments  = complaint.comments.select_related('author').all()

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            ComplaintComment.objects.create(
                complaint=complaint,
                author=request.user,
                content=content,
            )
            messages.success(request, "Comment added.")
        return redirect('complaints:detail', pk=pk)

    return render(request, 'complaints/detail.html', {
        'complaint': complaint,
        'comments':  comments,
    })


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
def admin_complaints(request):
    status_filter = request.GET.get('status', '')
    complaints    = Complaint.objects.select_related(
        'student__user', 'result__course', 'result__semester__session', 'reviewed_by'
    ).order_by('-created_at')

    if status_filter:
        complaints = complaints.filter(status=status_filter)

    from django.core.paginator import Paginator
    paginator = Paginator(complaints, 25)
    page      = paginator.get_page(request.GET.get('page', 1))

    stats = {
        'total':        Complaint.objects.count(),
        'pending':      Complaint.objects.filter(status='pending').count(),
        'under_review': Complaint.objects.filter(status='under_review').count(),
        'resolved':     Complaint.objects.filter(status='resolved').count(),
        'rejected':     Complaint.objects.filter(status='rejected').count(),
    }

    return render(request, 'complaints/admin_complaints.html', {
        'page_obj':     page,
        'stats':        stats,
        'status_filter': status_filter,
    })


@admin_required
def admin_complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    comments  = complaint.comments.select_related('author').all()

    if request.method == 'POST':
        action          = request.POST.get('action', '')
        response_text   = request.POST.get('admin_response', '').strip()
        new_status      = request.POST.get('status', complaint.status)
        comment_text    = request.POST.get('comment', '').strip()

        # ── Update complaint status and response ──────────────────────
        if action == 'update':
            old_status        = complaint.status
            complaint.status  = new_status
            if response_text:
                complaint.admin_response = response_text
            complaint.reviewed_by = request.user
            if new_status == 'resolved' and not complaint.resolved_at:
                complaint.resolved_at = timezone.now()
            complaint.save()

            # Build email message based on the new status
            status_label = complaint.get_status_display()
            course_code  = complaint.result.course.code
            course_title = complaint.result.course.title
            semester     = complaint.result.semester

            if new_status == 'resolved':
                email_title = f'Complaint Resolved — {course_code}'
                email_msg = (
                    f'Your complaint regarding {course_code} — {course_title} '
                    f'for {semester} has been reviewed and resolved.\n\n'
                )
                if response_text:
                    email_msg += f'Administrator\'s Response:\n{response_text}\n\n'
                email_msg += (
                    'If you have further concerns, please log in to the ERMS portal '
                    'to submit a new complaint or contact the Academic Affairs office.'
                )

            elif new_status == 'rejected':
                email_title = f'Complaint Not Upheld — {course_code}'
                email_msg = (
                    f'Your complaint regarding {course_code} — {course_title} '
                    f'for {semester} has been reviewed.\n\n'
                    f'After careful review, the complaint has not been upheld.\n\n'
                )
                if response_text:
                    email_msg += f'Administrator\'s Response:\n{response_text}\n\n'
                email_msg += (
                    'If you believe this decision is incorrect, please contact '
                    'the Academic Affairs office directly.'
                )

            elif new_status == 'under_review':
                email_title = f'Complaint Under Review — {course_code}'
                email_msg = (
                    f'Your complaint regarding {course_code} — {course_title} '
                    f'for {semester} is now being actively reviewed by the administrator.\n\n'
                    f'You will receive another notification once a decision has been made. '
                    f'You can track the status by logging into the ERMS portal.'
                )

            else:
                email_title = f'Complaint Update — {course_code}'
                email_msg = (
                    f'Your complaint regarding {course_code} — {course_title} '
                    f'for {semester} has been updated to: {status_label}.\n\n'
                )
                if response_text:
                    email_msg += f'Administrator\'s note:\n{response_text}'

            # Send notification (triggers both email and SMS)
            Notification.notify(
                recipient=complaint.student.user,
                ntype='complaint_update',
                title=email_title,
                message=email_msg,
                url=f'/complaints/{complaint.pk}/',
            )

            AuditLog.log(
                request.user,
                f'Updated complaint #{pk} from {old_status} to {new_status}'
            )
            messages.success(request, f"Complaint updated to '{status_label}'. Student has been notified by email.")

        # ── Add internal comment ──────────────────────────────────────
        if comment_text:
            ComplaintComment.objects.create(
                complaint=complaint,
                author=request.user,
                content=comment_text,
            )
            messages.info(request, "Comment added.")

        return redirect('complaints:admin_detail', pk=pk)

    return render(request, 'complaints/admin_detail.html', {
        'complaint': complaint,
        'comments':  comments,
    })
