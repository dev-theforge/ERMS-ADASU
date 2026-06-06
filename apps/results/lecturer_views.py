import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from apps.accounts.decorators import lecturer_required
from apps.accounts.models import CourseAssignment, StudentProfile, Semester, Course, Enrollment
from apps.notifications.models import Notification
from apps.audit.models import AuditLog
from .models import Result, ResultUploadLog
from .services import process_single_course_csv, process_csv_upload, compute_semester_gpa, compute_student_cgpa


@lecturer_required
def lecturer_dashboard(request):
    lecturer = request.user.lecturer_profile
    current_sem = Semester.objects.filter(is_current=True).first()
    assignments = CourseAssignment.objects.filter(lecturer=lecturer).select_related('course', 'semester__session')
    if current_sem:
        current_assignments = assignments.filter(semester=current_sem)
    else:
        current_assignments = assignments.none()

    course_stats = []
    for ca in current_assignments:
        results = Result.objects.filter(course=ca.course, semester=ca.semester)
        total = results.count()
        submitted = results.filter(status__in=['submitted', 'approved', 'published']).count()
        course_stats.append({'assignment': ca, 'total_entered': total, 'submitted': submitted})

    return render(request, 'lecturer/dashboard.html', {
        'lecturer': lecturer,
        'current_semester': current_sem,
        'course_stats': course_stats,
        'all_assignments': assignments.order_by('-semester__session__start_date')[:20],
    })


@lecturer_required
def lecturer_courses(request):
    lecturer = request.user.lecturer_profile
    semester_id = request.GET.get('semester')
    semesters = Semester.objects.order_by('-session__start_date')
    assignments = CourseAssignment.objects.filter(lecturer=lecturer).select_related('course__department', 'semester__session')
    if semester_id:
        assignments = assignments.filter(semester_id=semester_id)
    return render(request, 'lecturer/courses.html', {
        'assignments': assignments, 'semesters': semesters, 'selected': semester_id
    })


@lecturer_required
def lecturer_enter_scores(request, course_id, semester_id):
    lecturer = request.user.lecturer_profile
    course = get_object_or_404(Course, pk=course_id)
    semester = get_object_or_404(Semester, pk=semester_id)
    assignment = get_object_or_404(CourseAssignment, lecturer=lecturer, course=course, semester=semester)

    enrolled = Enrollment.objects.filter(course=course, semester=semester).select_related('student__user')
    existing_results = {r.student_id: r for r in Result.objects.filter(course=course, semester=semester)}

    if request.method == 'POST':
        updated = 0
        for enrollment in enrolled:
            student = enrollment.student
            score_key = f'score_{student.pk}'
            score_val = request.POST.get(score_key, '').strip()
            if not score_val:
                continue
            try:
                score = float(score_val)
                if not (0 <= score <= 100):
                    messages.error(request, f"Score for {student.matric_number} must be 0–100.")
                    continue
            except ValueError:
                messages.error(request, f"Invalid score for {student.matric_number}.")
                continue

            if student.pk in existing_results:
                result = existing_results[student.pk]
                if result.status in ['published', 'approved']:
                    continue  # Skip locked results
                result.score = score
                result.lecturer = lecturer
                result.save()
            else:
                Result.objects.create(student=student, course=course, semester=semester, lecturer=lecturer, score=score)
            updated += 1

        AuditLog.log(request.user, f'Entered {updated} scores for {course.code} / {semester}')
        messages.success(request, f"{updated} score(s) saved as draft.")
        return redirect('lecturer:enter_scores', course_id=course_id, semester_id=semester_id)

    rows = []
    for enrollment in enrolled:
        result = existing_results.get(enrollment.student.pk)
        rows.append({'student': enrollment.student, 'result': result})

    return render(request, 'lecturer/enter_scores.html', {
        'course': course, 'semester': semester, 'rows': rows
    })


@lecturer_required
def lecturer_upload_csv(request, course_id=None, semester_id=None):
    lecturer = request.user.lecturer_profile
    semesters = Semester.objects.order_by('-session__start_date')
    courses = CourseAssignment.objects.filter(lecturer=lecturer).select_related('course')
    current_sem = Semester.objects.filter(is_current=True).first()

    if request.method == 'POST':
        upload_type = request.POST.get('upload_type', 'single')
        sem_id = request.POST.get('semester')
        semester = get_object_or_404(Semester, pk=sem_id)
        csv_file = request.FILES.get('csv_file')

        if not csv_file:
            messages.error(request, "No file uploaded.")
            return redirect('lecturer:upload_csv')

        if upload_type == 'single':
            c_id = request.POST.get('course')
            course = get_object_or_404(Course, pk=c_id)
            get_object_or_404(CourseAssignment, lecturer=lecturer, course=course, semester=semester)
            created, errors, stats = process_single_course_csv(lecturer, semester, course, csv_file)
        else:
            created, errors, stats = process_csv_upload(lecturer, semester, csv_file, multi_course=True)

        ResultUploadLog.objects.create(
            lecturer=lecturer, semester=semester,
            file_name=csv_file.name,
            total_rows=stats['total'],
            successful_rows=stats['success'],
            failed_rows=stats['failed'],
            errors=errors,
        )
        messages.success(request, f"Upload complete: {stats['success']} successful, {stats['failed']} failed.")
        if errors:
            for e in errors[:10]:
                messages.warning(request, e)
        return redirect('lecturer:dashboard')

    return render(request, 'lecturer/upload_csv.html', {
        'semesters': semesters, 'courses': courses, 'current_sem': current_sem
    })


@lecturer_required
def download_csv_template(request, template_type):
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    if template_type == 'single':
        response['Content-Disposition'] = 'attachment; filename="single_course_template.csv"'
        writer.writerow(['matric_no', 'score'])
        writer.writerow(['ADU/2021/0001', '75'])
        writer.writerow(['ADU/2021/0002', '68'])
    else:
        response['Content-Disposition'] = 'attachment; filename="multi_course_template.csv"'
        writer.writerow(['course_code', 'matric_no', 'score'])
        writer.writerow(['CSC101', 'ADU/2021/0001', '75'])
        writer.writerow(['MTH101', 'ADU/2021/0002', '82'])
    return response


@lecturer_required
def submit_results(request, course_id, semester_id):
    lecturer = request.user.lecturer_profile
    course = get_object_or_404(Course, pk=course_id)
    semester = get_object_or_404(Semester, pk=semester_id)
    get_object_or_404(CourseAssignment, lecturer=lecturer, course=course, semester=semester)

    drafts = Result.objects.filter(course=course, semester=semester, status='draft', lecturer=lecturer)
    count = drafts.update(status='submitted', submitted_at=timezone.now())
    # Notify admins
    from apps.accounts.models import CustomUser
    for admin in CustomUser.objects.filter(role='admin', status='active'):
        Notification.notify(admin, 'result_submitted', 'Results Submitted for Approval',
                            f'{lecturer.title} {lecturer.user.get_full_name()} has submitted {count} results for {course.code} — {semester}.')
    AuditLog.log(request.user, f'Submitted {count} results for {course.code}/{semester}')
    messages.success(request, f"{count} result(s) submitted for approval.")
    return redirect('lecturer:enter_scores', course_id=course_id, semester_id=semester_id)


@lecturer_required
def lecturer_approve_results(request):
    """Admin reviews and approves submitted results."""
    from apps.accounts.decorators import admin_required
    return redirect('admin_panel:dashboard')


@lecturer_required
def course_statistics(request, course_id, semester_id):
    lecturer = request.user.lecturer_profile
    course = get_object_or_404(Course, pk=course_id)
    semester = get_object_or_404(Semester, pk=semester_id)
    results = Result.objects.filter(course=course, semester=semester).select_related('student__user')
    total = results.count()
    published = results.filter(status='published')

    grade_dist = {}
    for r in published:
        grade_dist[r.grade] = grade_dist.get(r.grade, 0) + 1

    pass_count = published.filter(grade__in=['A','B','C','D','E']).count()
    fail_count = published.filter(grade='F').count()
    avg_score = sum(float(r.score) for r in published) / published.count() if published.count() else 0

    return render(request, 'lecturer/course_stats.html', {
        'course': course, 'semester': semester,
        'results': results, 'total': total,
        'grade_dist': grade_dist, 'pass_count': pass_count,
        'fail_count': fail_count, 'avg_score': round(avg_score, 2),
    })
