import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from apps.accounts.decorators import lecturer_required
from apps.accounts.models import (
    CourseAssignment, StudentProfile, Semester, Course, Enrollment, CustomUser
)
from apps.notifications.models import Notification
from apps.audit.models import AuditLog
from .models import Result, ResultUploadLog
from .services import (
    process_single_course_csv,
    process_multi_course_csv,
)


@lecturer_required
def lecturer_dashboard(request):
    lecturer    = request.user.lecturer_profile
    current_sem = Semester.objects.filter(is_current=True).first()
    assignments = CourseAssignment.objects.filter(
        lecturer=lecturer
    ).select_related('course', 'semester__session').order_by(
        '-semester__session__start_date', 'course__code'
    )
    current_assignments = assignments.filter(semester=current_sem) if current_sem else assignments.none()

    course_stats = []
    for ca in current_assignments:
        all_results = Result.objects.filter(course=ca.course, semester=ca.semester)
        submitted   = all_results.filter(status__in=['submitted', 'approved', 'published']).count()
        course_stats.append({
            'assignment':    ca,
            'total_entered': all_results.count(),
            'submitted':     submitted,
        })

    return render(request, 'lecturer/dashboard.html', {
        'lecturer':        lecturer,
        'current_semester': current_sem,
        'course_stats':    course_stats,
        'all_assignments': assignments[:20],
    })


@lecturer_required
def lecturer_courses(request):
    lecturer    = request.user.lecturer_profile
    semester_id = request.GET.get('semester')
    semesters   = Semester.objects.select_related('session').order_by('-session__start_date')
    assignments = CourseAssignment.objects.filter(
        lecturer=lecturer
    ).select_related('course__department', 'semester__session')

    if semester_id:
        assignments = assignments.filter(semester_id=semester_id)

    return render(request, 'lecturer/courses.html', {
        'assignments': assignments,
        'semesters':   semesters,
        'selected':    semester_id,
    })


@lecturer_required
def lecturer_enter_scores(request, course_id, semester_id):
    lecturer = request.user.lecturer_profile
    course   = get_object_or_404(Course, pk=course_id)
    semester = get_object_or_404(Semester, pk=semester_id)
    get_object_or_404(CourseAssignment, lecturer=lecturer, course=course, semester=semester)

    enrolled         = Enrollment.objects.filter(
        course=course, semester=semester
    ).select_related('student__user')
    existing_results = {
        r.student_id: r
        for r in Result.objects.filter(course=course, semester=semester)
    }

    if request.method == 'POST':
        saved = 0
        for enrollment in enrolled:
            student   = enrollment.student
            score_raw = request.POST.get(f'score_{student.pk}', '').strip()
            if not score_raw:
                continue
            try:
                score = float(score_raw)
                if not (0 <= score <= 100):
                    messages.error(
                        request,
                        f"Score for {student.matric_number} must be between 0 and 100."
                    )
                    continue
            except ValueError:
                messages.error(request, f"Invalid score for {student.matric_number}.")
                continue

            if student.pk in existing_results:
                result = existing_results[student.pk]
                if result.status in ('published', 'approved'):
                    continue        # locked — skip silently
                result.score    = score
                result.lecturer = lecturer
                result.save()
            else:
                Result.objects.create(
                    student=student, course=course, semester=semester,
                    lecturer=lecturer, score=score, status='draft',
                )
            saved += 1

        AuditLog.log(request.user, f'Entered {saved} scores for {course.code}/{semester}')
        messages.success(request, f"{saved} score(s) saved as Draft.")
        return redirect('lecturer:enter_scores', course_id=course_id, semester_id=semester_id)

    rows = [
        {'student': e.student, 'result': existing_results.get(e.student.pk)}
        for e in enrolled
    ]
    return render(request, 'lecturer/enter_scores.html', {
        'course': course, 'semester': semester, 'rows': rows
    })


@lecturer_required
def lecturer_upload_csv(request, course_id=None, semester_id=None):
    lecturer    = request.user.lecturer_profile
    semesters   = Semester.objects.select_related('session').order_by('-session__start_date')
    courses     = CourseAssignment.objects.filter(
        lecturer=lecturer
    ).select_related('course', 'semester__session')
    current_sem = Semester.objects.filter(is_current=True).first()

    if request.method == 'POST':
        upload_type = request.POST.get('upload_type', 'single')
        sem_id      = request.POST.get('semester')
        semester    = get_object_or_404(Semester, pk=sem_id)
        csv_file    = request.FILES.get('csv_file')

        if not csv_file:
            messages.error(request, "Please select a CSV file to upload.")
            return redirect('lecturer:upload_csv')

        if not csv_file.name.lower().endswith('.csv'):
            messages.error(request, "Only .csv files are accepted.")
            return redirect('lecturer:upload_csv')

        if upload_type == 'single':
            c_id   = request.POST.get('course')
            course = get_object_or_404(Course, pk=c_id)
            get_object_or_404(CourseAssignment, lecturer=lecturer, course=course, semester=semester)
            created, errors, stats = process_single_course_csv(
                lecturer, semester, course, csv_file
            )
        else:
            created, errors, stats = process_multi_course_csv(
                lecturer, semester, csv_file
            )

        ResultUploadLog.objects.create(
            lecturer=lecturer,
            semester=semester,
            file_name=csv_file.name,
            total_rows=stats['total'],
            successful_rows=stats['success'],
            failed_rows=stats['failed'],
            errors=errors,
        )

        if stats['success'] > 0:
            messages.success(
                request,
                f"Upload complete: {stats['success']} score(s) saved, "
                f"{stats['failed']} row(s) failed."
            )
        else:
            messages.error(
                request,
                f"Upload failed: 0 scores saved. {stats['failed']} row(s) had errors."
            )

        for err in errors[:10]:
            messages.warning(request, err)
        if len(errors) > 10:
            messages.warning(request, f"... and {len(errors) - 10} more errors. Check upload log.")

        return redirect('lecturer:dashboard')

    return render(request, 'lecturer/upload_csv.html', {
        'semesters':   semesters,
        'courses':     courses,
        'current_sem': current_sem,
    })


@lecturer_required
def download_csv_template(request, template_type):
    response = HttpResponse(content_type='text/csv')
    writer   = csv.writer(response)

    if template_type == 'single':
        response['Content-Disposition'] = 'attachment; filename="single_course_template.csv"'
        writer.writerow(['matric_no', 'score'])
        writer.writerow(['ADU/2021/0001', '75'])
        writer.writerow(['ADU/2021/0002', '68'])
        writer.writerow(['ADU/2021/0003', '82'])
        writer.writerow(['ADU/2021/0004', '55'])
        writer.writerow(['ADU/2021/0005', '91'])
    else:
        response['Content-Disposition'] = 'attachment; filename="multi_course_template.csv"'
        writer.writerow(['course_code', 'matric_no', 'score'])
        writer.writerow(['CSC101', 'ADU/2021/0001', '75'])
        writer.writerow(['CSC101', 'ADU/2021/0002', '68'])
        writer.writerow(['MTH101', 'ADU/2021/0001', '82'])
        writer.writerow(['MTH101', 'ADU/2021/0002', '90'])

    return response


@lecturer_required
def submit_results(request, course_id, semester_id):
    lecturer = request.user.lecturer_profile
    course   = get_object_or_404(Course, pk=course_id)
    semester = get_object_or_404(Semester, pk=semester_id)
    get_object_or_404(CourseAssignment, lecturer=lecturer, course=course, semester=semester)

    drafts = Result.objects.filter(
        course=course, semester=semester, status='draft', lecturer=lecturer
    )
    count = drafts.update(status='submitted', submitted_at=timezone.now())

    if count == 0:
        messages.warning(request, "No draft results found to submit.")
        return redirect('lecturer:enter_scores', course_id=course_id, semester_id=semester_id)

    # Notify all active administrators
    admins = CustomUser.objects.filter(role='admin', status='active')
    for admin in admins:
        Notification.notify(
            recipient=admin,
            ntype='result_submitted',
            title=f'Results Submitted for Approval — {course.code}',
            message=(
                f'{lecturer.title} {lecturer.user.get_full_name()} has submitted '
                f'{count} result(s) for {course.code} — {course.title} '
                f'({semester}) for your approval.\n\n'
                f'Log in to the admin panel to review and approve.'
            ),
            url='/admin-panel/approve-results/',
        )

    AuditLog.log(
        request.user,
        f'Submitted {count} results for {course.code}/{semester} for approval'
    )
    messages.success(request, f"{count} result(s) submitted for admin approval.")
    return redirect('lecturer:enter_scores', course_id=course_id, semester_id=semester_id)


@lecturer_required
def course_statistics(request, course_id, semester_id):
    lecturer = request.user.lecturer_profile
    course   = get_object_or_404(Course, pk=course_id)
    semester = get_object_or_404(Semester, pk=semester_id)
    results  = Result.objects.filter(
        course=course, semester=semester
    ).select_related('student__user')

    published = results.filter(status='published')
    total     = results.count()

    grade_dist  = {}
    for r in published:
        grade_dist[r.grade] = grade_dist.get(r.grade, 0) + 1

    published_count = published.count()
    pass_count  = published.filter(grade__in=['A', 'B', 'C', 'D', 'E']).count()
    fail_count  = published.filter(grade='F').count()
    avg_score   = (
        sum(float(r.score) for r in published) / published_count
        if published_count else 0
    )

    return render(request, 'lecturer/course_stats.html', {
        'course':     course,
        'semester':   semester,
        'results':    results,
        'total':      total,
        'grade_dist': grade_dist,
        'pass_count': pass_count,
        'fail_count': fail_count,
        'avg_score':  round(avg_score, 2),
    })
