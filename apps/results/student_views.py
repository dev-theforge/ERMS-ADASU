from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from apps.accounts.decorators import student_required
from apps.accounts.models import Semester, AcademicSession
from apps.notifications.models import Notification
from apps.complaints.models import Complaint
from .models import Result, SemesterGPA, StudentCGPA
from .pdf_generator import generate_result_slip, generate_transcript


@student_required
def student_dashboard(request):
    student = request.user.student_profile
    current_sem = Semester.objects.filter(is_current=True).first()
    cgpa_obj = getattr(student, 'cgpa_record', None)
    current_gpa = None
    if current_sem:
        gpa_obj = SemesterGPA.objects.filter(student=student, semester=current_sem).first()
        current_gpa = gpa_obj.gpa if gpa_obj else None

    recent_results = Result.objects.filter(student=student, status='published').select_related('course', 'semester__session').order_by('-semester__session__start_date')[:6]
    complaints = Complaint.objects.filter(student=student).order_by('-created_at')[:5]
    notifications = Notification.objects.filter(recipient=request.user, is_read=False)[:5]
    enrolled = student.enrollments.filter(semester=current_sem).select_related('course') if current_sem else []

    return render(request, 'student/dashboard.html', {
        'student': student,
        'current_gpa': current_gpa,
        'cgpa': cgpa_obj,
        'recent_results': recent_results,
        'complaints': complaints,
        'notifications': notifications,
        'enrolled_courses': enrolled,
        'current_semester': current_sem,
    })


@student_required
def student_results(request):
    student = request.user.student_profile
    semester_id = request.GET.get('semester')
    session_id = request.GET.get('session')
    semesters = Semester.objects.order_by('-session__start_date', 'semester_type')
    sessions = AcademicSession.objects.order_by('-start_date')

    results = Result.objects.filter(student=student, status='published').select_related('course__department', 'semester__session')
    if semester_id:
        results = results.filter(semester_id=semester_id)
    if session_id:
        results = results.filter(semester__session_id=session_id)

    gpa_records = SemesterGPA.objects.filter(student=student).select_related('semester__session').order_by('-semester__session__start_date')
    cgpa_obj = getattr(student, 'cgpa_record', None)

    return render(request, 'student/results.html', {
        'student': student, 'results': results, 'semesters': semesters,
        'sessions': sessions, 'gpa_records': gpa_records, 'cgpa': cgpa_obj,
        'selected_semester': semester_id, 'selected_session': session_id,
    })


@student_required
def download_result_slip(request, semester_id):
    student = request.user.student_profile
    semester = get_object_or_404(Semester, pk=semester_id)
    results = Result.objects.filter(student=student, semester=semester, status='published').select_related('course')
    gpa_obj = SemesterGPA.objects.filter(student=student, semester=semester).first()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="result_slip_{student.matric_number}_{semester.pk}.pdf"'
    generate_result_slip(response, student, semester, results, gpa_obj)
    return response


@student_required
def download_transcript(request):
    student = request.user.student_profile
    cgpa_obj = getattr(student, 'cgpa_record', None)
    gpa_records = SemesterGPA.objects.filter(student=student).select_related('semester__session').order_by('semester__session__start_date')
    all_results = Result.objects.filter(student=student, status='published').select_related('course', 'semester__session').order_by('semester__session__start_date', 'course__code')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transcript_{student.matric_number}.pdf"'
    generate_transcript(response, student, all_results, gpa_records, cgpa_obj)
    return response


@student_required
def academic_history(request):
    student = request.user.student_profile
    gpa_records = SemesterGPA.objects.filter(student=student).select_related('semester__session').order_by('semester__session__start_date')
    cgpa_obj = getattr(student, 'cgpa_record', None)
    sessions_data = {}
    for gpa in gpa_records:
        sess = str(gpa.semester.session)
        if sess not in sessions_data:
            sessions_data[sess] = []
        results = Result.objects.filter(student=student, semester=gpa.semester, status='published').select_related('course')
        sessions_data[sess].append({'semester': gpa.semester, 'gpa': gpa, 'results': results})

    return render(request, 'student/academic_history.html', {
        'student': student,
        'sessions_data': sessions_data,
        'gpa_records': gpa_records,
        'cgpa': cgpa_obj,
    })
